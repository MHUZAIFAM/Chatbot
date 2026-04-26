class QueryEngine:

    def __init__(self, dataset_manager):

        self.dataset = dataset_manager
        self.df = dataset_manager.df

        self.id_col = dataset_manager.id_col
        self.rank_col = dataset_manager.rank_col
        self.score_col = dataset_manager.score_col

        self.sections = dataset_manager.sections

    # =====================================================
    # DATASET LEVEL
    # =====================================================

    def count_items(self):

        return len(self.df)


    def count_sections(self):

        return len(self.sections)


    def list_sections(self):

        return self.sections


    # =====================================================
    # SECTION LEVEL
    # =====================================================

    def count_items_in_section(self, section):

        col = f"{section}_answer"

        if col not in self.df.columns:
            return None

        section_df = self.df[
            self.df[col].astype(str).str.lower() == "yes"
        ]

        return len(section_df)


    def items_per_section(self):

        counts = {}

        for sec in self.sections:

            col = f"{sec}_answer"

            if col in self.df.columns:

                count = len(
                    self.df[
                        self.df[col].astype(str).str.lower() == "yes"
                    ]
                )

                counts[sec] = count

        return counts

    def section_with_most_ranked(self):

        counts = {}

        for sec in self.sections:
            counts[sec] = self.count_ranked_items_in_section(sec)

        best_section = max(counts, key=counts.get)

        return {
            "Section": best_section,
            "Ranked Items": counts[best_section]
        }

    def top_ranked_items(self, n=3):

        ranked_df = self.df[self.df[self.rank_col].notna()]

        ranked_df = ranked_df.sort_values(self.rank_col)

        top = ranked_df.head(n)

        results = []

        for _, row in top.iterrows():
            item_id = str(row[self.id_col])
            rank = int(row[self.rank_col])
            section = self.item_section(item_id)

            results.append({
                "Item ID": item_id,
                "Rank": rank,
                "Section": section
            })

        return results

    def average_rank_per_section(self):

        averages = {}

        for sec in self.sections:

            col = f"{sec}_answer"

            if col not in self.df.columns:
                continue

            section_df = self.df[
                (self.df[col].astype(str).str.lower() == "yes") &
                (self.df[self.rank_col].notna())
                ]

            if section_df.empty:
                averages[sec] = None
            else:
                averages[sec] = float(section_df[self.rank_col].mean())

        return averages


    # =====================================================
    # RANKING COUNTS
    # =====================================================

    def count_ranked_items(self):

        ranked = self.df[self.df[self.rank_col].notna()]

        return len(ranked)


    def count_unranked_items(self):

        unranked = self.df[self.df[self.rank_col].isna()]

        return len(unranked)

    def unranked_items_per_section(self):

        counts = {}

        for sec in self.sections:
            counts[sec] = self.count_unranked_items_in_section(sec)

        return counts

    def selected_reason(self, item_id):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return None

        row = row.iloc[0]

        section = self.item_section(item_id)

        if section == "Unselected":
            return None

        col = f"{section}_reason"

        if col in self.df.columns:
            return row[col]

        return None

    def other_section_reasons(self, item_id):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return []

        row = row.iloc[0]

        selected = self.item_section(item_id)

        reasons = []

        for sec in self.sections:

            if sec == selected:
                continue

            col = f"{sec}_reason"

            if col in self.df.columns:

                reason = row[col]

                if isinstance(reason, str) and reason.strip():
                    reasons.append((sec, reason))

        return reasons


    def count_ranked_items_in_section(self, section):

        col = f"{section}_answer"

        if col not in self.df.columns:
            return None

        section_df = self.df[
            (self.df[col].astype(str).str.lower() == "yes") &
            (self.df[self.rank_col].notna())
        ]

        return len(section_df)


    # =====================================================
    # UNSELECTED ITEMS
    # =====================================================

    def count_unselected_items(self):

        selected_mask = None

        for sec in self.sections:

            col = f"{sec}_answer"

            if col in self.df.columns:

                mask = self.df[col].astype(str).str.lower() == "yes"

                if selected_mask is None:
                    selected_mask = mask
                else:
                    selected_mask = selected_mask | mask

        if selected_mask is None:
            return len(self.df)

        unselected = self.df[~selected_mask]

        return len(unselected)

    # =====================================================
    # HIGHEST RANKED ITEMS IN DATASET
    # =====================================================

    def highest_ranked(self):

        if self.rank_col not in self.df.columns:
            return []

        min_rank = self.df[self.rank_col].min()

        data = self.df[self.df[self.rank_col] == min_rank]

        results = []

        for _, row in data.iterrows():
            section = self.item_section(row[self.id_col])

            results.append({
                "Item ID": row[self.id_col],
                "Rank": row[self.rank_col],
                "Section": section
            })

        return results

    # =====================================================
    # LOWEST RANKED ITEMS IN DATASET
    # =====================================================

    def lowest_ranked(self):

        if self.rank_col not in self.df.columns:
            return []

        max_rank = self.df[self.rank_col].max()

        data = self.df[self.df[self.rank_col] == max_rank]

        results = []

        for _, row in data.iterrows():
            section = self.item_section(row[self.id_col])

            results.append({
                "Item ID": row[self.id_col],
                "Rank": row[self.rank_col],
                "Section": section
            })

        return results

    # =====================================================
    # HIGHEST RANKED PER SECTION
    # =====================================================

    def highest_ranked_section(self, section):

        col = f"{section}_answer"

        if col not in self.df.columns:
            return None

        section_df = self.df[
            (self.df[col].astype(str).str.lower() == "yes") &
            (self.df[self.rank_col].notna())
        ]

        if section_df.empty:
            return None

        row = section_df.sort_values(self.rank_col).iloc[0]

        return {
            "Section": section,
            "Item ID": str(row[self.id_col]),
            "Rank": int(row[self.rank_col])
        }


    # =====================================================
    # LOWEST RANKED PER SECTION
    # =====================================================

    def lowest_ranked_section(self, section):

        col = f"{section}_answer"

        if col not in self.df.columns:
            return None

        section_df = self.df[
            (self.df[col].astype(str).str.lower() == "yes") &
            (self.df[self.rank_col].notna())
        ]

        if section_df.empty:
            return None

        row = section_df.sort_values(self.rank_col, ascending=False).iloc[0]

        return {
            "Section": section,
            "Item ID": str(row[self.id_col]),
            "Rank": int(row[self.rank_col])
        }

    # =====================================================
    # COUNT UNRANKED ITEMS IN SECTION
    # =====================================================

    def count_unranked_items_in_section(self, section):

        col = f"{section}_answer"

        if col not in self.df.columns:
            return 0

        data = self.df[
            (self.df[col].astype(str).str.lower() == "yes") &
            (self.df[self.rank_col].isna())
            ]

        return len(data)


    # =====================================================
    # ITEM RANK LOOKUP
    # =====================================================

    def item_rank(self, item_id):

        row = self.df[
            self.df[self.id_col].astype(str) == str(item_id)
        ]

        if row.empty:
            return None

        row = row.iloc[0]

        rank = row.get(self.rank_col)

        if rank is None:
            return "Unranked"

        return int(rank)


    # =====================================================
    # ITEM SECTION LOOKUP
    # =====================================================

    def item_section(self, item_id):

        row = self.df[
            self.df[self.id_col].astype(str) == str(item_id)
        ]

        if row.empty:
            return None

        row = row.iloc[0]

        for sec in self.sections:

            col = f"{sec}_answer"

            if col in self.df.columns:

                val = str(row[col]).strip().lower()

                if val == "yes":
                    return sec

        return "Unselected"

    # =====================================================
    # ALL RANKED ITEMS IN DATASET
    # =====================================================

    def all_ranked_items(self):

        ranked_df = self.df[self.df[self.rank_col].notna()]

        results = []

        for _, row in ranked_df.iterrows():
            item_id = str(row[self.id_col])
            rank = int(row[self.rank_col])
            section = self.item_section(item_id)

            results.append({
                "Item ID": item_id,
                "Rank": rank,
                "Section": section
            })

        return results

    # =====================================================
    # GET ITEM SECTION
    # =====================================================
    def get_item_section(self, item_id):

        df = self.dataset.df

        row = df[df[self.dataset.id_col] == item_id]

        if row.empty:
            return None

        row = row.iloc[0]

        for sec in self.dataset.sections:

            col = f"{sec}_answer"

            if col in df.columns:

                val = str(row[col]).lower()

                if val in ["yes", "true", "1"]:
                    return sec

        return None

    def is_unselected(self, item_id):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return None

        row = row.iloc[0]

        for sec in self.sections:

            col = f"{sec}_answer"

            if col in self.df.columns:

                val = str(row[col]).lower()

                if val in ["yes", "true", "1"]:
                    return False  # item is selected

        return True  # item is unselected

    def unselected_reasons(self, item_id):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return []

        row = row.iloc[0]

        reasons = []

        for sec in self.sections:

            col = f"{sec}_reason"

            if col in self.df.columns:

                reason = row[col]

                if isinstance(reason, str) and reason.strip() and reason.lower() != "nan":
                    reasons.append((sec, reason))

        return reasons

    def items_in_section(self, section):

        col = f"{section}_answer"

        if col not in self.df.columns:
            return []

        data = self.df[
            self.df[col].astype(str).str.strip().str.lower().isin(["yes", "true", "1"])
        ]

        # keep only ranked items
        data = data[data[self.rank_col].notna()]

        results = []

        for _, row in data.iterrows():
            item_id = str(row[self.id_col])
            rank = int(row[self.rank_col])

            results.append({
                "Item ID": item_id,
                "Rank": rank
            })

        return results