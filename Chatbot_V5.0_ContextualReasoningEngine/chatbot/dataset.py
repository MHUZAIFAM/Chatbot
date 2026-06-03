import json
import os
import pandas as pd


class DatasetManager:

    def __init__(self, path: str, section_prompts_path: str = None):

        print("Loading dataset...")

        # Support both CSV and Excel
        if path.endswith(".xlsx") or path.endswith(".xlsm"):
            self.df = pd.read_excel(path)
        else:
            self.df = pd.read_csv(path)

        print("Dataset rows:", len(self.df))

        # Clean column names
        self.df.columns = self.df.columns.str.strip()

        # Remove duplicates
        self.df = self.df.drop_duplicates().reset_index(drop=True)

        # Store all column names
        self.columns = self.df.columns.tolist()

        # ================================
        # CORE IDENTIFICATION COLUMNS
        # ================================

        self.id_col = self.detect_column(["item id"])
        self.media_item_id_col = self.detect_column(["mediaitemid"])
        self.media_outlet_col = self.detect_column(["media outlet"])
        self.headline_col = self.detect_column(["headline"])
        self.full_text_col = self.detect_column(["full text"])
        self.summary_col = self.detect_column(["summary"])

        # ================================
        # METADATA COLUMNS
        # ================================

        self.date_col = self.detect_column(["date"])
        self.page_col = self.detect_column(["page"])
        self.wordcount_col = self.detect_column(["wordcount"])

        # ================================
        # RANKING / ORDERING COLUMNS
        # ================================

        self.rank_col = self.detect_column(["rank"])
        self.score_col = self.detect_column(["score"])
        self.order_col = self.detect_column(["order"])

        self.ordering_section_col = self.detect_column(["ordering_section"])
        self.ordering_reason_col = self.detect_column(["ordering_reason"])
        self.ordering_relevant_text_col = self.detect_column(["ordering_relevant_text"])

        # ================================
        # LEAD / SIMILAR COLUMNS
        # ================================

        self.item_type_col      = self.detect_column(["item_type"])
        self.is_lead_col        = self.detect_column(["is_lead"])
        self.lead_article_id_col = self.detect_column(["lead_article_id"])

        # ================================
        # VALIDATION
        # ================================

        if not self.id_col:
            raise ValueError("Item ID column could not be detected.")

        if not self.rank_col:
            print("Warning: Rank column not detected.")

        # ================================
        # CONVERT NUMERIC COLUMNS
        # ================================

        if self.rank_col:
            self.df[self.rank_col] = pd.to_numeric(
                self.df[self.rank_col],
                errors="coerce"
            )

        if self.score_col:
            self.df[self.score_col] = pd.to_numeric(
                self.df[self.score_col],
                errors="coerce"
            )

        # ================================
        # SECTION DETECTION
        # ================================

        self.sections = [
            col.replace("_answer", "")
            for col in self.columns
            if col.endswith("_answer")
        ]

        # ================================
        # SECTION REASON / TEXT COLUMNS
        # ================================

        self.section_reason_cols = [
            col for col in self.columns if col.endswith("_reason")
        ]

        self.section_text_cols = [
            col for col in self.columns if col.endswith("_relevant_text")
        ]

        # ================================
        # SECTION PROMPTS / BRIEFING RULES
        # ================================

        self.section_prompts = {}

        if section_prompts_path:
            try:
                with open(section_prompts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.section_prompts = data.get("sections", {})
                print(f"Loaded section prompts for: {list(self.section_prompts.keys())}")
            except Exception as e:
                print(f"Warning: Could not load section prompts: {e}")

        # ================================
        # ORDERING GUIDELINES
        # ================================

        self.ordering_guidelines = {}

        ordering_path = None
        if section_prompts_path:
            ordering_path = os.path.join(os.path.dirname(section_prompts_path), "ordering_guidelines.json")

        if ordering_path and os.path.exists(ordering_path):
            try:
                with open(ordering_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.ordering_guidelines = data.get("ordering_guidelines", {})
                print(f"Loaded ordering guidelines.")
            except Exception as e:
                print(f"Warning: Could not load ordering guidelines: {e}")

        # ================================
        # SECTION PROMPT COVERAGE CHECK
        # ================================

        if self.section_prompts:
            prompt_keys  = set(self.section_prompts.keys())
            dataset_keys = set(self.sections)

            matched   = dataset_keys & prompt_keys
            missing   = dataset_keys - prompt_keys   # in dataset but not in JSON
            extra     = prompt_keys  - dataset_keys  # in JSON but not in dataset

            print(f"\n── Section Prompt Coverage ──────────────────")
            print(f"  ✔  Matched  ({len(matched)}): {sorted(matched) or '—'}")
            if missing:
                print(f"  ✘  Missing from JSON ({len(missing)}): {sorted(missing)}")
                print(f"     ↳ These sections have no briefing rule — exclusion cards will omit the rule block.")
            if extra:
                print(f"  ⚠  Extra in JSON ({len(extra)}): {sorted(extra)}")
                print(f"     ↳ These keys exist in the JSON but don't match any dataset section.")
            print(f"─────────────────────────────────────────────\n")

        print("Detected Sections:", self.sections)
        print("Dataset Ready")


    # =====================================================
    # COLUMN DETECTION
    # =====================================================

    def detect_column(self, possible_names):

        # exact match first
        for col in self.columns:
            for name in possible_names:
                if col.lower() == name.lower():
                    return col

        # fallback partial match
        for col in self.columns:
            for name in possible_names:
                if name.lower() in col.lower():
                    return col

        return None