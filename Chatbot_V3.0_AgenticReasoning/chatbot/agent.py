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

        return " ".join(
            word.upper() if len(word) <= 2 else word.capitalize()
            for word in sec.replace("_", " ").split()
        )

    # =====================================================
    # MAIN ASK FUNCTION
    # =====================================================

    def ask(self, question):

        print("ASK FUNCTION TRIGGERED", flush=True)
        print("QUESTION:", question, flush=True)


        # 1️⃣ Planner decides what tool to use
        plan = self.planner.plan(question)
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

        # =====================================
        # FOLLOW-UP WHY HANDLING
        # =====================================
        q = question.lower().strip()

        if q.startswith("why"):

            # recover last item if planner missed it
            if not item_id and hasattr(self.memory, "last_item"):
                item_id = self.memory.last_item
                plan["item_id"] = item_id

            if item_id:
                if self.query_engine.is_unselected(item_id):
                    plan["operation"] = "unselected_reasons"
                else:
                    plan["operation"] = "selected_reason"

            operation = plan.get("operation")

        # 3️⃣ Execute tool if planner selected one
        if operation and operation != "unknown":

            result = self.executor.execute(plan)

            if result is not None:

                if isinstance(result, dict):

                    lines = []

                    for k, v in result.items():

                        section_name = self.format_section(k)

                        if v is None:
                            lines.append(f"{section_name}: No ranked items")
                        else:
                            lines.append(f"{section_name}: {v}")

                    answer = "\n".join(lines)

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
                                    f"🔹 {sec_name}\n{reason}\n"
                                )

                            # CASE 2: ranked items
                            elif isinstance(item, dict) and "Item ID" in item:

                                rank = item.get("Rank")

                                if rank is None:
                                    formatted.append(f"{item['Item ID']} | Unranked")
                                else:
                                    formatted.append(f"{item['Item ID']} | Rank {rank}")

                            else:
                                formatted.append(str(item))

                        answer = "Reasons:\n\n" + "\n".join(formatted)

                else:
                    answer = str(result)

                # ✅ IMPORTANT: stop execution here
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