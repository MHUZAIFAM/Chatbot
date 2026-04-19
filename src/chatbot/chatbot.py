import pandas as pd
import google.generativeai as genai

from .intents import detect_intents
from .ranking import handle_section_ranking
from .sentiment import analyze_sentiment


class NewsChatbot:

    # =====================================================
    # INIT
    # =====================================================
    def __init__(self, csv_path, api_key):

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-pro-latest")

        print("Loading dataset...")
        self.df = pd.read_csv(csv_path)
        self.df = self.df.drop_duplicates().reset_index(drop=True)

        self.columns = self.df.columns.tolist()

        # detect important columns
        self.id_col = "Item ID" if "Item ID" in self.df.columns else self.detect_column(["id", "item"])
        self.rank_col = self.detect_column(["rank", "position"])
        self.text_col = self.detect_column(["headline", "title", "name"])
        self.media_col = "Media Outlet"

        # normalize item ids
        if "Item ID" in self.df.columns:
            self.df["Item ID"] = (
                self.df["Item ID"]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
            )

        # detect sections
        self.sections = [
            col.replace("_answer", "")
            for col in self.df.columns
            if col.endswith("_answer")
        ]

        # memory
        self.item_memory = {}
        self.general_memory = []
        self.memory_limit = 5

        print("Detected Sections:", self.sections)
        print("Chatbot Ready ✅")

    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    def detect_column(self, possible_names):

        for col in self.df.columns:
            for name in possible_names:
                if name.lower() in col.lower():
                    return col
        return None

    # =====================================================
    # ITEM DETECTION
    # =====================================================
    def extract_item_id(self, question):

        if not self.id_col:
            return None

        q = question.lower()

        for item in self.df[self.id_col].astype(str):

            if item.lower() in q:
                return item

        return None

    # =====================================================
    # SECTION DETECTION FROM QUESTION
    # =====================================================

    def extract_section_from_question(self, question):

        q = question.lower()

        # check dataset sections
        for section in self.sections:

            readable = section.replace("_", " ")

            if section in q or readable in q:
                return section

        # detect unselected
        if "unselected" in q:
            return "unselected"

        return None

    def get_item_row(self, item_id):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return None

        return row.iloc[0]

    # =====================================================
    # SECTION ANALYSIS
    # =====================================================
    def analyze_sections(self):

        counts = {sec: 0 for sec in self.sections}
        unselected = 0

        for _, row in self.df.iterrows():

            matched = False

            for sec in self.sections:

                col = f"{sec}_answer"

                if col in self.df.columns:
                    if str(row[col]).strip().lower() == "yes":
                        counts[sec] += 1
                        matched = True

            if not matched:
                unselected += 1

        counts["Unselected Items"] = unselected

        return counts

    # =====================================================
    # MEMORY
    # =====================================================
    def get_last_item_from_memory(self):

        if not self.item_memory:
            return None

        return list(self.item_memory.keys())[-1]

    def update_item_memory(self, item_id, question):

        if item_id not in self.item_memory:
            self.item_memory[item_id] = []

        self.item_memory[item_id].append(question)

        if len(self.item_memory[item_id]) > self.memory_limit:
            self.item_memory[item_id] = self.item_memory[item_id][-self.memory_limit:]

    def update_general_memory(self, question):

        self.general_memory.append(question)

        if len(self.general_memory) > self.memory_limit:
            self.general_memory = self.general_memory[-self.memory_limit:]

    # =====================================================
    # MAIN ASK FUNCTION
        # =====================================================
    def ask(self, question):

        print("\nQUESTION:", question)

        item_id = self.extract_item_id(question)

        # memory context resolution
        q = question.lower()

        dataset_words = [
            "dataset",
            "sections",
            "how many",
            "count",
            "items per section",
            "list sections"
        ]

        # memory context resolution
        if not item_id:

            last_item = self.get_last_item_from_memory()

            if (
                    last_item
                    and any(x in q for x in ["why", "rank", "placed", "sentiment"])
                    and not any(x in q for x in dataset_words)
            ):
                item_id = last_item
        # -------------------------------
        # MEMORY UPDATE
        # -------------------------------
        if item_id:
            self.update_item_memory(item_id, question)
        else:
            self.update_general_memory(question)

        intents = detect_intents(question)
        q = question.lower()

        print("Item Memory:", self.item_memory)
        print("General Memory:", self.general_memory)

        # =====================================================
        # ITEM EXPLANATION (WHY)
        # =====================================================

        if item_id and ("why" in q or "reason" in q):

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            section_found = None
            reason = None

            for sec in self.sections:

                answer_col = f"{sec}_answer"
                reason_col = f"{sec}_reason"

                if answer_col in self.df.columns:

                    if str(row[answer_col]).strip().lower() == "yes":

                        section_found = sec

                        if reason_col in self.df.columns:
                            reason = row.get(reason_col)

                        break

            if not section_found:
                section_found = "Unknown"

            return {
                "type": "item_explanation",
                "data": {
                    "Item ID": item_id,
                    "Section": section_found,
                    "Reason": reason
                }
            }


        # =====================================================
        # ITEM DETAILS (Tell me about item)
        # =====================================================
        if item_id and ("explain" in intents or "about" in q):

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            section_found = "Unselected"
            rank_value = "Unranked"

            for sec in self.sections:

                answer_col = f"{sec}_answer"

                if answer_col in self.df.columns:
                    if str(row[answer_col]).strip().lower() == "yes":
                        section_found = sec
                        break

            if self.rank_col and pd.notna(row.get(self.rank_col)):
                try:
                    rank_value = int(float(row[self.rank_col]))
                except:
                    pass

            media = None

            if self.media_col and self.media_col in self.df.columns:
                media = row.get(self.media_col)

            relevant_text = None

            for sec in self.sections:

                answer_col = f"{sec}_answer"
                text_col = f"{sec}_relevant_text"

                if answer_col in self.df.columns:

                    if str(row[answer_col]).strip().lower() == "yes":

                        if text_col in self.df.columns:
                            relevant_text = row.get(text_col)

                        break
            return {
                "type": "item_details",
                "data": {
                    "Item ID": item_id,
                    "Section": section_found,
                    "Rank": rank_value,
                    "Media Outlet": media,
                    "Relevant Text": relevant_text
                }
            }


        # =====================================================
        # ITEM SECTION LOOKUP
        # =====================================================
        if item_id and ("section" in q or "placed" in q or "belongs" in q):

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            section_found = "Unselected"

            for sec in self.sections:

                col = f"{sec}_answer"

                if col in self.df.columns:
                    if str(row[col]).strip().lower() == "yes":
                        section_found = sec
                        break

            return {
                "type": "item_section",
                "data": {
                    "Item ID": item_id,
                    "Section": section_found
                }
            }


        # =====================================================
        # SCHEMA
        # =====================================================
        if "schema_count" in intents:
            return {
                "type": "schema_count",
                "data": {"Total_Sections": len(self.sections)}
            }

        if "schema" in intents:
            return {
                "type": "schema",
                "data": {
                    "Sections": self.sections,
                    "Total_Sections": len(self.sections)
                }
            }

        # =====================================================
        # ITEMS PER SECTION
        # =====================================================

        if any(x in q for x in ["per section", "each section", "by section"]):
            return {
                "type": "section_counts",
                "data": self.analyze_sections()
            }
        # =====================================================
        # ITEM COUNT (DYNAMIC)
        # =====================================================

        if any(x in q for x in ["how many", "total", "count", "number of items"]):

            section = self.extract_section_from_question(question)

            # TOTAL ITEMS
            if not section:
                return {
                    "type": "section_count",
                    "data": {
                        "Section": "Total",
                        "Count": len(self.df)
                    }
                }

            # UNSELECTED
            if section == "unselected":
                counts = self.analyze_sections()

                return {
                    "type": "section_count",
                    "data": {
                        "Section": "Unselected",
                        "Count": counts.get("Unselected Items", 0)
                    }
                }

            # SPECIFIC SECTION
            answer_col = f"{section}_answer"

            if answer_col in self.df.columns:
                count = len(
                    self.df[self.df[answer_col].astype(str).str.lower() == "yes"]
                )

                return {
                    "type": "section_count",
                    "data": {
                        "Section": section,
                        "Count": count
                    }
                }

        # =====================================================
        # DATASET GUARD
        # =====================================================
        dataset_terms = [
            "section", "sections",
            "dataset", "news",
            "item", "items",
            "row", "rows",
            "count"
        ]

        if (
                not item_id
                and "schema" not in intents
                and not any(term in q for term in dataset_terms)
                and "rank" not in q
                and "lowest" not in q
                and "highest" not in q
        ):
            return {
                "type": "error",
                "data": "Query not related to dataset."
            }

        # =====================================================
        # SENTIMENT
        # =====================================================
        if item_id and "sentiment" in q:
            return analyze_sentiment(
                self.df,
                self.model,
                self.id_col,
                self.text_col,
                item_id
            )

        # =====================================================
        # RANKING
        # =====================================================
        if "ranking" in intents:
            return handle_section_ranking(
                self.df,
                self.rank_col,
                self.id_col,
                self.sections,
                question
            )

        # =====================================================
        # AGGREGATION
        # =====================================================
        if "aggregation" in intents:
            return {
                "type": "aggregation",
                "data": self.analyze_sections()
            }

        return {
            "type": "error",
            "data": "Query not related to dataset."
        }