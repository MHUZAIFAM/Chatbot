import pandas as pd


class DatasetManager:

    def __init__(self, path: str):

        print("Loading dataset...")

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

        print("Detected Sections:", self.sections)
        print("Dataset Ready")


    # =====================================================
    # COLUMN DETECTION
    # =====================================================

    def detect_column(self, possible_names):

        for col in self.columns:
            for name in possible_names:
                if name.lower() in col.lower():
                    return col

        return None