import logging
import re
from datetime import datetime

from chatbot.dataset import DatasetManager
from chatbot.query_engine import QueryEngine
from chatbot.retriever import DataRetriever
from chatbot.generator import AnswerGenerator
from chatbot.memory import ConversationMemory
from chatbot.planner import Planner
from chatbot.executer import Executor


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def pretty_section(raw):
    """
    Convert raw section slug → human-readable title.
    e.g. "aged_and_community_care"              → "Aged and Community Care"
         "hospitals_&_hospitals_in_the_home"    → "Hospitals & Hospitals in the Home"
    """
    if not raw or raw == "Unselected":
        return raw
    return raw.replace("_", " ").title()


def pretty_date(raw):
    """
    Convert ISO date string → readable format.
    e.g. "2026-02-03T18:04:00.000Z" → "3 Feb 2026"
    """
    if not raw:
        return raw
    raw_str = str(raw).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw_str, fmt)
            return dt.strftime("%-d %b %Y")
        except ValueError:
            continue
    return raw_str  # fallback: return as-is if unparseable


def pretty_rank(raw):
    """
    Convert rank float/int → clean integer string.
    e.g. 9.0 → "9"
    """
    if raw is None:
        return None
    try:
        return str(int(float(raw)))
    except (ValueError, TypeError):
        return str(raw)


class ChatbotAgent:

    def __init__(self, dataset_path, api_key):

        # -------------------------------------------------
        # Core Components
        # -------------------------------------------------

        self.dataset_manager = DatasetManager(dataset_path)

        self.query_engine = QueryEngine(self.dataset_manager)

        self.retriever = DataRetriever(self.dataset_manager)

        self.generator = AnswerGenerator(api_key)

        self.memory = ConversationMemory()

        self.planner = Planner(api_key)

        self.executor = Executor(self.query_engine)

    # -------------------------------------------------
    # Main Chat Function
    # -------------------------------------------------

    def ask(self, question):

        print("ASK FUNCTION TRIGGERED")
        print("QUESTION:", question)

        q_lower = question.lower()

        # -------------------------------------------------
        # AGGREGATE / STATS GUARD  (pre-planner)
        # Questions asking for counts / totals are not
        # supported — block them before the planner runs.
        # -------------------------------------------------

        _AGGREGATE_PATTERNS = [
            r"\bhow many\b",
            r"\bcount\b",
            r"\btotal number\b",
            r"\bnumber of\b",
            r"\bhow much\b",
            r"\bwhat is the size\b",
            r"\bdataset size\b",
            r"\bhow large\b",
        ]

        _AGGREGATE_KEYWORDS = [
            "how many sections",
            "how many items",
            "how many ranked",
            "how many unranked",
            "how many unselected",
            "how many selected",
            "how many articles",
            "how many records",
            "how many rows",
            "total items",
            "total sections",
            "total articles",
            "total records",
            "number of sections",
            "number of items",
            "number of ranked",
            "number of unranked",
            "number of unselected",
            "number of selected",
            "number of articles",
            "items per section",
            "articles per section",
            "ranked per section",
            "unranked per section",
        ]

        _is_aggregate = (
            any(re.search(p, q_lower) for p in _AGGREGATE_PATTERNS)
            or any(kw in q_lower for kw in _AGGREGATE_KEYWORDS)
        )

        if _is_aggregate:
            answer = (
                "This chatbot focuses on article reasoning, "
                "ranking, placement, and filtering."
            )
            self.memory.add(question, answer)
            return answer

        # -------------------------------------------------
        # DETERMINISTIC REFERENCE RESOLUTION
        # -------------------------------------------------

        if self.memory.last_item:

            reference_phrases = [
                "this item",
                "that item",
                "this article",
                "that article",
                "tell me about it",
                "tell me about this",
                "where was it placed",
                "why was it placed there",
                "why was it selected"
            ]

            if any(p in q_lower for p in reference_phrases):

                item_id_ref = str(self.memory.last_item)

                replacements = {
                    "this item": item_id_ref,
                    "that item": item_id_ref,
                    "this article": item_id_ref,
                    "that article": item_id_ref,
                    "it": item_id_ref
                }

                for old, new in replacements.items():

                    question = re.sub(
                        rf"\b{re.escape(old)}\b",
                        new,
                        question,
                        flags=re.IGNORECASE
                    )

        # -------------------------------------------------
        # Planner
        # -------------------------------------------------

        context = self.memory.summary()

        sections = ", ".join(
            self.dataset_manager.sections
        )

        plan = self.planner.plan(
            question=question,
            context=context,
            sections=sections
        )

        logging.info(f"PLANNER OUTPUT: {plan}")

        operation = plan.get("operation")

        item_id = plan.get("item_id")

        # -------------------------------------------------
        # RANKING WHY GUARD
        # "Why was it ranked 9th?" / "Why is it at position X?"
        # → fetch Ordering_Reason, not section reason.
        # Must be checked BEFORE the generic "why" handler.
        # -------------------------------------------------

        _RANK_WHY_PATTERNS = [
            r"\branked\b",
            r"\branking\b",
            r"\bposition\b",
            r"\bordered\b",
            r"\bordering\b",
            r"\brank\s*\d+\b",
            r"#\s*\d+",
            r"\b\d+(?:st|nd|rd|th)\b",  # "9th", "1st", "2nd"
        ]

        _is_rank_why = (
            q_lower.startswith("why")
            and item_id
            and any(re.search(p, q_lower) for p in _RANK_WHY_PATTERNS)
        )

        if _is_rank_why:
            # Override: fetch Ordering_Reason for this item
            plan["operation"] = "item_field"
            plan["field"] = "ordering reason"
            operation = "item_field"

        # -------------------------------------------------
        # Follow-up WHY handling (placement / selection)
        # -------------------------------------------------

        elif (
                q_lower.startswith("why")
                and item_id
                and operation not in [
                    "selected_reason",
                    "other_section_reasons",
                    "unselected_reasons"
                ]
        ):
            plan["operation"] = "selected_reason"
            operation = "selected_reason"

        # -------------------------------------------------
        # Execute
        # -------------------------------------------------

        result = self.executor.execute(plan)

        # -------------------------------------------------
        # Update conversational state
        # -------------------------------------------------

        if plan.get("item_id"):
            self.memory.last_item = plan.get("item_id")

        if plan.get("section"):
            self.memory.last_section = plan.get("section")

        if plan.get("operation"):
            self.memory.last_operation = plan.get("operation")

        # -------------------------------------------------
        # Unsupported Questions
        # -------------------------------------------------

        if operation == "unknown":
            answer = (
                "This chatbot focuses on article reasoning, "
                "ranking, placement, and filtering."
            )

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # Retrieval + Generator Fallback
        # -------------------------------------------------

        if result is None:
            retrieved = self.retriever.retrieve(question)

            generated = self.generator.generate(
                question=question,
                retrieved_items=retrieved,
                memory=context
            )

            answer = generated.get("answer", str(generated))

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # ITEM DETAILS
        # -------------------------------------------------

        if operation == "item_details":

            lines = []

            def add(label, value):
                if value is not None and value != "":
                    lines.append(f"<b>{label}:</b> {value}")

            add("Item ID",      result.get("Item ID"))
            add("Headline",     result.get("Headline"))
            add("Media Outlet", result.get("Media Outlet"))
            add("Date",         pretty_date(result.get("Date")))
            add("Page",         result.get("Page"))
            add("Rank",         pretty_rank(result.get("Rank")))
            add("Score",        result.get("Score"))
            add("Section",      pretty_section(result.get("Section")))
            add("Reason",       result.get("Reason"))

            answer = "<br>".join(lines)

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # ITEM FIELD
        # -------------------------------------------------

        if operation == "item_field":

            field = str(plan.get("field", "")).lower().strip()

            # Apply pretty formatters for known field types
            if field in ("date", "publication date"):
                answer = pretty_date(result)
            elif field in ("rank", "ranking"):
                answer = pretty_rank(result)
            elif field in ("ordering section", "section"):
                answer = pretty_section(str(result))
            else:
                answer = str(result)

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # ITEM RANK
        # -------------------------------------------------

        if operation == "item_rank":

            answer = f"Item {item_id} is ranked #{pretty_rank(result)}."

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # ITEM SECTION
        # -------------------------------------------------

        if operation == "item_section":

            answer = f"Item {item_id} was placed in {pretty_section(result)}."

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # REASONING RESPONSES
        # -------------------------------------------------

        if operation in [
            "selected_reason",
            "other_section_reasons",
            "unselected_reasons"
        ]:

            answer = str(result)

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # FILTER RESULTS
        # -------------------------------------------------

        if operation == "filter_items":

            if not result:

                answer = "No matching items found."

                self.memory.add(question, answer)

                return answer

            lines = []

            for item in result:

                lines.append(
                    f"""
                    <div style='margin-bottom:16px'>
                    <b>{item.get("Headline", "Untitled")}</b><br>
                    Item ID: {item.get("Item ID")}<br>
                    Score: {item.get("Score")}<br>
                    Rank: {pretty_rank(item.get("Rank"))}<br>
                    Section: {pretty_section(item.get("Section"))}
                    </div>
                    """
                )

            answer = "".join(lines)

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # RANKING RESULTS
        # -------------------------------------------------

        if operation in [
            "highest_ranked",
            "lowest_ranked",
            "top_ranked_items",
            "highest_ranked_section",
            "lowest_ranked_section"
        ]:

            if isinstance(result, list):

                lines = []

                for item in result:

                    lines.append(
                        f"""
                        <div style='margin-bottom:16px'>
                        <b>{item.get("Headline", "Untitled")}</b><br>
                        Item ID: {item.get("Item ID")}<br>
                        Rank: {pretty_rank(item.get("Rank"))}<br>
                        Score: {item.get("Score")}<br>
                        Section: {pretty_section(item.get("Section"))}
                        </div>
                        """
                    )

                answer = "".join(lines)

            else:

                answer = str(result)

            self.memory.add(question, answer)

            return answer

        # -------------------------------------------------
        # FINAL FALLBACK
        # -------------------------------------------------

        answer = str(result)

        self.memory.add(question, answer)

        return answer