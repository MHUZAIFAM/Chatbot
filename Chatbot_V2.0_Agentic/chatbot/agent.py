import re

from .dataset import DatasetManager
from .query_engine import QueryEngine
from .retriever import DataRetriever
from .generator import AnswerGenerator
from .memory import ConversationMemory


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
    # DETERMINISTIC ANSWERS
    # =====================================================

    def try_deterministic(self, question):

        q = question.lower()
        item_id = self.extract_item_id(question)
        section = self.extract_section(question)

        # MEMORY SECTION RESOLUTION
        if not section:

            last_question, last_answer = self.memory.last()

            if last_question:
                prev_section = self.extract_section(last_question)

                if prev_section:
                    section = prev_section

        # FOLLOW-UP WHY QUESTION
        if "why" in q:
            last_question, last_answer = self.memory.last()

            if last_question:

                last_item = self.extract_item_id(last_question)

                if last_item:

                    reasons = self.query_engine.unselected_reasons(last_item)

                    if reasons:

                        lines = []
                        lines.append(f"Item {last_item} was not selected for the following reasons:")
                        lines.append("")

                        for sec, reason in reasons:
                            readable = self.format_section(sec)
                            lines.append(f"- {readable}: {reason}")

                        return "\n".join(lines)


        # TOTAL RANKED ITEMS
        if "how many ranked items" in q or "total ranked items" in q:
            return f"There are {self.query_engine.count_ranked_items()} ranked items in the dataset."

        # RANKED ITEMS IN SECTION
        if section and "ranked" in q and "how many" in q:
            count = self.query_engine.count_ranked_items_in_section(section)

            readable = self.format_section(section)

            return f"There are {count} ranked items in the {readable} section."

        # HIGHEST RANKED PER SECTION
        if "highest ranked" in q and any(x in q for x in ["per section", "each section", "of each section"]):

            lines = []
            lines.append("Highest ranked item in each section:")
            lines.append("")

            for sec in self.dataset.sections:

                item = self.query_engine.highest_ranked_section(sec)

                if item:
                    readable = self.format_section(sec)

                    lines.append(
                        f"- Item ID: {item['Item ID']} - Rank: {item['Rank']} ({readable})"
                    )

            return "\n".join(lines)

        # LOWEST RANKED PER SECTION
        if "lowest ranked" in q and any(x in q for x in ["per section", "each section", "of each section"]):

            lines = []
            lines.append("Lowest ranked item in each section:")
            lines.append("")

            for sec in self.dataset.sections:

                item = self.query_engine.lowest_ranked_section(sec)

                if item:
                    readable = self.format_section(sec)

                    lines.append(
                        f"- Item ID: {item['Item ID']} - Rank: {item['Rank']} ({readable})"
                    )

            return "\n".join(lines)

        # HIGHEST RANKED IN SECTION
        if any(x in q for x in ["highest ranked", "top ranked", "highest ranking"]) and section \
                and not any(x in q for x in ["per section", "each section", "of each section"]):

            item = self.query_engine.highest_ranked_section(section)

            if item:
                readable = self.format_section(section)

                return f"The highest ranked item in {readable} is {item['Item ID']} with rank {item['Rank']}."

        # LOWEST RANKED IN SECTION
        if any(x in q for x in ["lowest ranked", "lowest ranking"]) and section \
                and not any(x in q for x in ["per section", "each section", "of each section"]):
            item = self.query_engine.lowest_ranked_section(section)

            if item:
                readable = self.format_section(section)

                return f"The lowest ranked item in {readable} is {item['Item ID']} with rank {item['Rank']}."

        # UNRANKED ITEMS IN SECTION
        if section and "unranked" in q:

            items = self.query_engine.items_in_section(section)

            readable = self.format_section(section)

            unranked = [i for i in items if i["Rank"] is None]

            if not unranked:
                return f"There are no unranked items in the {readable} section."

            lines = []
            lines.append(f"Unranked items in {readable}:")
            lines.append("")

            for item in unranked:
                lines.append(f"- {item['Item ID']}")

            return "\n".join(lines)

        # RANKED ITEMS IN SECTION
        if section and "ranked" in q and "items" in q:

            items = self.query_engine.items_in_section(section)

            readable = self.format_section(section)

            ranked = [i for i in items if i["Rank"] is not None]

            if not ranked:
                return f"There are no ranked items in the {readable} section."

            lines = []
            lines.append(f"Ranked items in {readable}:")
            lines.append("")

            for item in ranked:
                lines.append(f"- {item['Item ID']} (Rank {item['Rank']})")

            return "\n".join(lines)

        # LIST ALL RANKED ITEMS
        if "ranked items" in q and any(x in q for x in ["list", "show", "display", "what"]):
            items = self.query_engine.all_ranked_items()

            lines = []
            lines.append("Ranked items in the dataset:")
            lines.append("")

            for item in items:
                section = self.format_section(item["Section"])
                rank = int(item["Rank"])

                lines.append(f"- Item ID: {item['Item ID']} (Rank {rank}, {section})")

            return "\n".join(lines)

        # LIST ITEMS IN SECTION
        if section and any(x in q for x in ["list", "show", "display"]) and "items" in q:
            items = self.query_engine.items_in_section(section)

            readable = self.format_section(section)

            if not items:
                return f"No items were found in the {readable} section."

            lines = []
            lines.append(f"Items in {readable}:")
            lines.append("")

            for item in items:

                if item["Rank"] is not None:
                    lines.append(f"- {item['Item ID']} (Rank {item['Rank']})")
                else:
                    lines.append(f"- {item['Item ID']} (Unranked)")

            return "\n".join(lines)

        # WHY WAS ITEM UNSELECTED
        if item_id and "why" in q and "unselected" in q:

            reasons = self.query_engine.unselected_reasons(item_id)

            if not reasons:
                return f"No explanation available for why item {item_id} was unselected."

            lines = []
            lines.append(f"Item {item_id} was not selected for the following reasons:")
            lines.append("")

            for sec, reason in reasons:
                readable = self.format_section(sec)

                lines.append(f"- {readable}: {reason}")

            return "\n".join(lines)

        # WAS ITEM UNSELECTED
        if item_id and "unselected" in q:

            if self.query_engine.is_unselected(item_id):
                return f"Yes, item {item_id} was an unselected item."
            else:
                return f"No, item {item_id} was selected and ranked."

        # RANKED ITEMS PER SECTION
        if "ranked" in q and any(x in q for x in ["per section", "each section", "by section"]):
            lines = []
            lines.append(f"Total Ranked Items: {self.query_engine.count_ranked_items()}")
            lines.append("Ranked Items per Section")
            lines.append("")

            for sec in self.dataset.sections:
                count = self.query_engine.count_ranked_items_in_section(sec)

                readable = self.format_section(sec)

                lines.append(f"{readable}: {count} ranked items")

            return "\n".join(lines)


        # ITEMS PER SECTION
        if "items per section" in q or "items in each section" in q:

            counts = self.query_engine.items_per_section()

            lines = []
            lines.append(f"Total Number of Items: {self.query_engine.count_items()}")
            lines.append("")
            lines.append("Items per Section:")
            lines.append("")

            for sec, count in counts.items():
                readable = self.format_section(sec)

                lines.append(f"- {readable}: {count} items")

            unselected = self.query_engine.count_unselected_items()

            lines.append("")
            lines.append(f"- Unselected Items: {unselected} items")

            return "\n".join(lines)

        # ITEM PLACEMENT (SECTION)
        if item_id and ("placed" in q or "section" in q):

            section = self.query_engine.get_item_section(item_id)

            if section:
                readable = self.format_section(section)
                return f"Item {item_id} was placed in the '{readable}' section."

            else:
                return f"Item {item_id} was not placed in any section and thus Unselected."


        # COUNT UNSELECTED ITEMS
        if "how many" in q and "unselected" in q:
            return f"There are {self.query_engine.count_unselected_items()} unselected items in the dataset."

        # COUNT ITEMS
        if "how many items" in q or "total items" in q:
            return f"There are {self.query_engine.count_items()} items in the dataset."

        # COUNT SECTIONS
        if "how many sections" in q:
            return f"There are {self.query_engine.count_sections()} sections."

        # LIST SECTIONS
        if "sections" in q and ("what" in q or "list" in q):

            sections = self.query_engine.list_sections()

            formatted = [self.format_section(sec) for sec in sections]

            bullet_list = "\n".join([f"- {s}" for s in formatted])

            return f"The dataset contains the following sections:\n\n{bullet_list}"

        return None


    # =====================================================
    # MAIN ASK FUNCTION
    # =====================================================

    def ask(self, question):

        # 1️⃣ deterministic first
        answer = self.try_deterministic(question)

        if answer:
            self.memory.add(question, answer)
            return answer


        # 2️⃣ extract structure
        item_id = self.extract_item_id(question)
        section = self.extract_section(question)


        # 3️⃣ retrieve dataset slice
        data = self.retriever.retrieve(
            item_id=item_id,
            section=section
        )


        # 4️⃣ memory context
        context = self.memory.summary()


        # 5️⃣ generate answer
        result = self.generator.generate(
            question,
            data,
            context
        )

        answer = result.get("answer", "No answer generated.")

        self.memory.add(question, answer)

        return answer
