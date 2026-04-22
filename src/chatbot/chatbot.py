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

        # remove whitespace around IDs
        self.df[self.id_col] = self.df[self.id_col].astype(str).str.strip()

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

        import re

        # find any number that looks like an item id
        match = re.search(r"\b[A-Za-z]?\d{8,}\b", question)

        if not match:
            return None

        possible_id = match.group()

        # check if it exists in dataset
        if possible_id in self.df[self.id_col].astype(str).values:
            return possible_id

        return "INVALID_ITEM"
    # =====================================================
    # TWO ITEMS DETECTION
    # =====================================================
    def extract_two_items(self, question):

        import re

        ids = re.findall(r"\b\d{8,}\b", question)

        if len(ids) >= 2:
            return ids[0], ids[1]

        return None, None

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

    # =====================================================
    # CHECK IF SECTION EXISTS IN QUESTION
    # =====================================================
    def section_exists(self, question):

        q = question.lower()

        for section in self.sections:

            readable = section.replace("_", " ")

            # exact match of section name
            if readable in q or section in q:
                return True

        # explicit unselected case
        if "unselected" in q:
            return True

        return False

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
        # Invalid item ID check
        if item_id == "INVALID_ITEM":
            return {
                "type": "error",
                "data": "Item ID does not exist in dataset."
            }

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
        # WHY NOT IN SECTION
        # =====================================================

        if item_id and "not" in q:

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            actual_section = None

            # Detect the actual section from dataset
            for sec in self.sections:
                col = f"{sec}_answer"

                if col in self.df.columns:
                    if str(row[col]).strip().lower() == "yes":
                        actual_section = sec
                        break

            # Detect the section mentioned in the question
            mentioned_section = self.extract_section_from_question(question)

            # Fetch dataset reasons
            actual_reason = None
            not_reason = None

            if actual_section:
                reason_col = f"{actual_section}_reason"
                if reason_col in self.df.columns:
                    actual_reason = row.get(reason_col)

            if mentioned_section:
                reason_col = f"{mentioned_section}_reason"
                if reason_col in self.df.columns:
                    not_reason = row.get(reason_col)

            return {
                "type": "section_negation",
                "data": {
                    "Item ID": item_id,
                    "Actual Section": actual_section,
                    "Actual Reason": actual_reason,
                    "Not Section": mentioned_section,
                    "Not Reason": not_reason
                }
            }

        # =====================================================
        # INVALID SECTION IN QUESTION
        # =====================================================

        if item_id and ("why" in q or "placed" in q) and self.extract_section_from_question(question):
            if self.section_exists(question) is False:

                row = self.get_item_row(item_id)

                actual_section = "Unknown"

                if row is not None:
                    for sec in self.sections:
                        col = f"{sec}_answer"
                        if col in self.df.columns:
                            if str(row[col]).strip().lower() == "yes":
                                actual_section = sec
                                break

                return {
                    "type": "invalid_section_query",
                    "data": {
                        "Item ID": item_id,
                        "Actual Section": actual_section,
                        "Message": "The section mentioned in the question does not exist in the dataset."
                    }
                }
        # =====================================================
        # RANK EXPLANATION
        # =====================================================

        if item_id and "rank" in q and "why" in q:

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            rank = row[self.rank_col]

            return {
                "type": "rank_explanation",
                "data": {
                    "Item ID": item_id,
                    "Rank": int(rank),
                    "Explanation": f"This item received rank {rank} based on the dataset ranking."
                }
            }

        # =====================================================
        # WHY ITEM NOT SELECTED (UNSELECTED REASONING)
        # =====================================================

        if item_id and ("not selected" in q or "unselected" in q):

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            # check if item actually belongs to a section
            selected_section = None

            for sec in self.sections:
                answer_col = f"{sec}_answer"

                if answer_col in self.df.columns:
                    if str(row[answer_col]).strip().lower() == "yes":
                        selected_section = sec
                        break

            # if item was selected, don't run this logic
            if selected_section:
                return {
                    "type": "item_explanation",
                    "data": {
                        "Item ID": item_id,
                        "Section": selected_section,
                        "Explanation": "This item was selected for a section, so it is not unselected."
                    }
                }

            # collect reasons for all sections
            section_reasons = []

            for sec in self.sections:

                reason_col = f"{sec}_reason"

                if reason_col in self.df.columns:
                    reason = row.get(reason_col)

                    if pd.notna(reason):
                        section_reasons.append({
                            "Section": sec,
                            "Reason": reason
                        })

            return {
                "type": "unselected_reasoning",
                "data": {
                    "Item ID": item_id,
                    "Section_Reasons": section_reasons
                }
            }

        # =====================================================
        # ITEM EXPLANATION (WHY)
        # =====================================================

        if item_id and ("why" in q or "reason" in q) and "rank" not in q:

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
                section_found = "Unselected"

            # --- NEW: allow LLM explanation ---
            if reason:

                prompt = f"""
                Explain why the following news item belongs in this section.

                Headline: {row[self.text_col]}
                Section: {section_found}
                Dataset reason: {reason}

                Explain in simple terms.
                """

                response = self.model.generate_content(prompt)

                explanation = response.text

            else:
                explanation = "No explanation available."

            return {
                "type": "item_explanation",
                "data": {
                    "Item ID": item_id,
                    "Section": section_found,
                    "Explanation": explanation
                }
            }


        # =====================================================
        # SENTIMENT
        # =====================================================
        if item_id and any(x in q for x in ["sentiment", "opinion", "tone", "feeling"]):
            return analyze_sentiment(
                self.df,
                self.model,
                self.id_col,
                self.text_col,
                item_id
            )


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
                            relevant_text = row.get(text_col) or ""

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
        # LIST ITEMS IN SECTION
        # =====================================================

        if "items" in q and ("list" in q or "show" in q or "what" in q):

            section = self.extract_section_from_question(question)

            # UNSELECTED ITEMS
            if section == "unselected":

                unselected_items = []

                for _, row in self.df.iterrows():

                    matched = False

                    for sec in self.sections:
                        col = f"{sec}_answer"

                        if col in self.df.columns:
                            if str(row[col]).strip().lower() == "yes":
                                matched = True
                                break

                    if not matched:
                        unselected_items.append(str(row[self.id_col]))

                return {
                    "type": "section_item_list",
                    "data": {
                        "Section": "Unselected",
                        "Count": len(unselected_items),
                        "Items": unselected_items
                    }
                }

            # ITEMS IN SPECIFIC SECTION
            if section:

                answer_col = f"{section}_answer"

                if answer_col in self.df.columns:
                    section_items = self.df[
                        self.df[answer_col].astype(str).str.lower() == "yes"
                        ][self.id_col].astype(str).tolist()

                    return {
                        "type": "section_item_list",
                        "data": {
                            "Section": section,
                            "Count": len(section_items),
                            "Items": section_items
                        }
                    }


        # =====================================================
        # ITEM COUNT (DYNAMIC)
        # =====================================================

        if any(x in q for x in ["how many", "total", "count", "number of items"]):

            section = self.extract_section_from_question(question)

            # dataset total queries
            if "dataset" in q or "total" in q:
                return {
                    "type": "section_count",
                    "data": {
                        "Section": "Total",
                        "Count": len(self.df)
                    }
                }

            # invalid section query
            if section is None and "in" in q:
                return {
                    "type": "error",
                    "data": "Section does not exist in dataset."
                }

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
        # ITEM COMPARISON (RANK)
        # =====================================================

        item1, item2 = self.extract_two_items(question)

        if item1 and item2 and "rank" in q:

            row1 = self.get_item_row(item1)
            row2 = self.get_item_row(item2)

            if row1 is None or row2 is None:
                return {"type": "error", "data": "One of the items not found"}

            rank1 = row1[self.rank_col]
            rank2 = row2[self.rank_col]

            better = item1 if rank1 < rank2 else item2

            return {
                "type": "rank_comparison",
                "data": {
                    "Item1": item1,
                    "Rank1": int(rank1),
                    "Item2": item2,
                    "Rank2": int(rank2),
                    "Higher Ranked": better
                }
            }

        # =====================================================
        # SECTION COMPARISON
        # =====================================================

        if item_id and "instead of" in q:

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            actual_section = None

            for sec in self.sections:

                col = f"{sec}_answer"

                if col in self.df.columns:
                    if str(row[col]).strip().lower() == "yes":
                        actual_section = sec
                        break

            mentioned_section = self.extract_section_from_question(question)

            return {
                "type": "section_comparison",
                "data": {
                    "Item ID": item_id,
                    "Actual Section": actual_section,
                    "Compared Section": mentioned_section,
                    "Explanation": f"The item was classified under {actual_section} according to dataset labels."
                }
            }


        # =====================================================
        # ITEM RANK LOOKUP
        # =====================================================

        if item_id and "rank" in q:

            row = self.get_item_row(item_id)

            if row is None:
                return {"type": "error", "data": "Item not found"}

            rank_value = "Unranked"

            if self.rank_col and pd.notna(row.get(self.rank_col)):
                try:
                    rank_value = int(float(row[self.rank_col]))
                except:
                    pass

            return {
                "type": "item_rank",
                "data": {
                    "Item ID": item_id,
                    "Rank": rank_value
                }
            }

        # =====================================================
        # RANKING
        # =====================================================
        if "ranking" in intents:

            section = self.extract_section_from_question(question)

            # If a specific section is asked
            if section and section != "unselected":

                answer_col = f"{section}_answer"

                if answer_col in self.df.columns:

                    section_df = self.df[
                        self.df[answer_col].astype(str).str.lower() == "yes"
                        ]

                    if not section_df.empty:

                        # highest ranked item
                        if any(x in q for x in ["highest", "top", "best"]):
                            section_df = section_df.sort_values(self.rank_col, ascending=True)
                            row = section_df.iloc[0]

                        # lowest ranked item
                        elif any(x in q for x in ["lowest", "bottom", "worst", "least"]):
                            section_df = section_df.sort_values(self.rank_col, ascending=False)
                            row = section_df.iloc[0]

                        else:
                            section_df = section_df.sort_values(self.rank_col)
                            row = section_df.iloc[0]

                        return {
                            "type": "ranking",
                            "data": [{
                                "Section": section,
                                "Item ID": str(row[self.id_col]),
                                "Rank": int(row[self.rank_col])
                            }]
                        }
            # Otherwise return ranking for all sections
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