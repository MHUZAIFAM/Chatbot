import re

from .dataset import DatasetManager
from .query_engine import QueryEngine
from .retriever import DataRetriever
from .generator import AnswerGenerator
from .memory import ConversationMemory
from .planner import Planner
from .executer import Executor


import logging
logging.basicConfig(level=logging.INFO)

class ChatbotAgent:

    def __init__(self, dataset_path, api_key):

        # Load dataset
        self.dataset = DatasetManager(dataset_path)

        # Query engine
        self.query_engine = QueryEngine(self.dataset)

        # Retriever
        self.retriever = DataRetriever(self.dataset)

        # LLM generator
        self.generator = AnswerGenerator(api_key)

        # Memory
        self.memory = ConversationMemory()

        # Planner
        self.planner = Planner(api_key)

        # Executor
        self.executor = Executor(self.query_engine)


    # =====================================================
    # ITEM ID DETECTION
    # =====================================================

    def extract_item_id(self, question):

        match = re.search(r"[A-Za-z]*\d{6,}", question)

        if match:
            return match.group()

        return None


    # =====================================================
    # SECTION DETECTION
    # =====================================================

    def extract_section(self, question):

        q = question.lower()

        for sec in self.dataset.sections:

            # dataset format
            dataset_name = sec.lower()

            # readable format
            readable = sec.replace("_", " ").lower()

            # alternative format (& → and)
            readable_alt = readable.replace("&", "and")

            if dataset_name in q or readable in q or readable_alt in q:
                return sec

        return None

    # =====================================================
    # SECTION FORMATTER
    # =====================================================

    def format_section(self, sec):
        return sec.replace("_", " ").title()

    # =====================================================
    # MAIN ASK FUNCTION
    # =====================================================

    def ask(self, question):

        print("ASK FUNCTION TRIGGERED", flush=True)
        print("QUESTION:", question, flush=True)


        # 1️⃣ Planner decides what tool to use
        sections = ", ".join(self.dataset.sections)

        plan = self.planner.plan(
            question,
            context=self.memory.summary(),
            sections=sections
        )
        logging.info(f"PLANNER OUTPUT: {plan}")

        if not plan:
            plan = {"operation": "unknown", "section": None, "item_id": None}

        operation = plan.get("operation")
        section = plan.get("section")
        item_id = plan.get("item_id")

        # 2️⃣ fallback extraction if planner missed it
        if not section:
            section = self.extract_section(question)

        # recover previous section from conversation
        if not section and hasattr(self.memory, "last_section"):
            section = self.memory.last_section

        if not item_id:
            item_id = self.extract_item_id(question)

        # normalize section name
        if section:
            section = section.lower().replace(" ", "_")

        plan["section"] = section
        plan["item_id"] = item_id

        # store last section in memory
        if section:
            self.memory.last_section = section
        # store last item
        if item_id:
            self.memory.last_item = item_id

        # FOLLOW-UP WHY HANDLING
        q = question.lower().strip()

        if q.startswith("why"):

            # recover last item if planner missed it
            if not item_id and hasattr(self.memory, "last_item"):
                item_id = self.memory.last_item
                plan["item_id"] = item_id

            # only override if planner didn't already choose a reason operation
            if item_id and operation not in [
                "selected_reason",
                "other_section_reasons",
                "unselected_reasons"
            ]:

                if self.query_engine.is_unselected(item_id):
                    plan["operation"] = "unselected_reasons"
                else:
                    plan["operation"] = "selected_reason"

            operation = plan.get("operation")

        # 3️⃣ Execute tool if planner selected one
        if operation and operation != "unknown":

            result = self.executor.execute(plan)
            answer = None

            if result is not None:

                if isinstance(result, dict):

                    # -------------------------------------------------
                    # ITEM DETAILS
                    # -------------------------------------------------
                    if operation == "item_details":

                        section = result.get("Section")
                        rank = result.get("Rank")
                        reason = result.get("Reason")

                        section_name = (
                            self.format_section(section)
                            if section and section != "Unselected"
                            else "Unselected"
                        )

                        rank_text = "Unranked" if rank in [None, "Unranked"] else rank

                        # Clean date
                        date = result.get("Date")
                        if date:
                            date = str(date).split("T")[0]
                        else:
                            date = "Unknown"

                        # Clean page
                        page = result.get("Page")
                        if page in [None, "None"]:
                            page = "Unknown"

                        answer = (
                            f"<b>Item ID:</b> {result['Item ID']}<br>"
                            f"<b>Date:</b> {date}<br>"
                            f"<b>Page:</b> {page}<br>"
                            f"<b>Rank:</b> {rank_text}<br>"
                            f"<b>Section:</b> {section_name}"
                        )

                        if section != "Unselected" and reason:
                            answer += f"<br><b>Section Reason:</b> {reason}"

                    # -------------------------------------------------
                    # GENERIC DICT FORMAT
                    # -------------------------------------------------
                    else:

                        lines = []

                        for k, v in result.items():

                            section_name = self.format_section(k)

                            if v is None:
                                lines.append(f"{section_name}: No ranked items")
                            else:
                                lines.append(f"• {section_name}: {v} items")

                        answer = "\n".join(lines)

                elif operation == "list_sections":

                    sections = [f"• {self.format_section(s)}" for s in result]

                    answer = "The sections present in this dataset are:\n" + "\n".join(sections)

                elif isinstance(result, list):

                    if not result:
                        answer = "No items found."

                    else:

                        formatted = []

                        for item in result:

                            # CASE 1: section rejection reasons
                            if isinstance(item, tuple) and len(item) == 2:

                                sec, reason = item
                                sec_name = self.format_section(sec)

                                formatted.append(
                                    f"• <b>{sec_name}</b><br>{reason}"
                                )

                            # CASE 2: ranked items
                            elif isinstance(item, dict) and "Item ID" in item:
                                
                                rank = item.get("Rank")

                                q_lower = question.lower()

                                # ranked only
                                if "ranked" in q_lower and rank is None:
                                    continue

                                # unranked only
                                if "unranked" in q_lower and rank is not None:
                                    continue

                                if rank is None:
                                    formatted.append(
                                        f"• <b>Item {item['Item ID']}</b> — Unranked"
                                    )
                                else:
                                    formatted.append(
                                        f"• <b>Item {item['Item ID']}</b> — Rank {rank}"
                                    )
                            else:
                                formatted.append(str(item))

                        if operation in ["other_section_reasons", "unselected_reasons"]:

                            answer = "<b>Reasons</b><br><br>" + "<br><br>".join(formatted)

                        else:

                            answer = "\n".join(formatted)

                            if section:

                                section_name = self.format_section(section)

                                if "ranked" in question.lower():
                                    header = f"<b>Ranked items in {section_name}</b><br><br>"

                                elif "unranked" in question.lower():
                                    header = f"<b>Unranked items in {section_name}</b><br><br>"

                                else:
                                    header = f"<b>Items in {section_name}</b><br><br>"

                                answer = header + answer

                elif operation == "item_rank":

                    if result == "Unranked":
                        answer = f"Item {item_id} was unranked."
                    else:
                        answer = f"Item {item_id} was ranked {result}."

                elif operation == "item_section":

                    section_name = self.format_section(result)

                    answer = f"Item {item_id} was placed in {section_name}."

                elif isinstance(result, int):

                    if operation == "count_items":

                        answer = f"There are {result} items in the dataset."


                    elif operation == "count_sections":

                        answer = f"There are {result} sections in this dataset."


                    elif operation == "count_ranked_items":

                        answer = f"There are a total of {result} ranked items in this dataset."


                    elif operation == "count_unranked_items":

                        answer = f"There are {result} unranked items in this dataset."


                    elif operation == "count_unselected_items":

                        answer = f"There are {result} unselected items in this dataset."



                    else:

                        answer = str(result)

                # ✅ IMPORTANT: stop execution here
                if answer is None:
                    answer = str(result)

                self.memory.add(question, answer)
                return answer

        # 4️⃣ Fallback → LLM reasoning with dataset
        if not item_id:
            item_id = self.extract_item_id(question)

        # recover item from memory
        if not item_id and hasattr(self.memory, "last_item"):
            item_id = self.memory.last_item

        section = self.extract_section(question)

        data = self.retriever.retrieve(item_id=item_id, section=section)

        context = self.memory.summary()

        result = self.generator.generate(question, data, context)

        answer = result.get("answer", "No answer generated.")

        self.memory.add(question, answer)

        return answer