class DataRetriever:

    def __init__(self, dataset_manager):

        # reference dataset
        self.dataset = dataset_manager
        self.df = dataset_manager.df

        # key columns
        self.id_col = dataset_manager.id_col
        self.rank_col = dataset_manager.rank_col
        self.score_col = dataset_manager.score_col

        self.sections = dataset_manager.sections

        # useful context columns for reasoning
        self.reason_cols = dataset_manager.section_reason_cols
        self.text_cols = dataset_manager.section_text_cols

        self.ordering_section_col = dataset_manager.ordering_section_col
        self.ordering_reason_col = dataset_manager.ordering_reason_col
        self.ordering_relevant_text_col = dataset_manager.ordering_relevant_text_col


    # =====================================================
    # SAFE COLUMN SELECTION
    # =====================================================

    def get_safe_columns(self):

        cols = [
            self.id_col,
            self.rank_col,
            self.score_col,
            self.ordering_section_col,
            self.ordering_reason_col,
            self.ordering_relevant_text_col
        ]

        cols += self.reason_cols
        cols += self.text_cols

        # remove None values
        cols = [c for c in cols if c is not None]

        # keep only columns that exist in dataset
        cols = [c for c in cols if c in self.df.columns]

        return cols


    # =====================================================
    # MAIN RETRIEVAL FUNCTION
    # =====================================================

    def retrieve(self, item_id=None, section=None):

        data = self.df.copy()

        # --------------------------------
        # ITEM FILTER
        # --------------------------------
        if item_id:
            data = data[
                data[self.id_col].astype(str) == str(item_id)
                ]

        # --------------------------------
        # SECTION FILTER
        # --------------------------------
        if section:

            col = f"{section}_answer"

            if col in data.columns:
                data = data[
                    data[col].astype(str).str.lower() == "yes"
                    ]

        # --------------------------------
        # SAFE COLUMN SELECTION
        # --------------------------------
        safe_cols = self.get_safe_columns()

        data = data[safe_cols]

        # --------------------------------
        # LIMIT FOR LLM
        # --------------------------------
        data = data.head(25)

        return data.to_dict(orient="records")