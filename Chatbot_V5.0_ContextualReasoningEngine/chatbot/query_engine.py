import pandas as pd

FIELD_MAP = {

    # -------------------------
    # Headline / Title
    # -------------------------
    "headline": "Headline",
    "title": "Headline",
    "article title": "Headline",

    # -------------------------
    # URL / Links
    # -------------------------
    "url": "WebURL",
    "web url": "WebURL",
    "link": "WebURL",
    "article link": "WebURL",
    "website": "WebURL",
    "webpage": "WebURL",

    # -------------------------
    # Date / Page
    # -------------------------
    "date": "Date",
    "publication date": "Date",
    "page": "Page Number",
    "page number": "Page Number",

    # -------------------------
    # Ranking
    # -------------------------
    "rank": "Rank",
    "ranking": "Rank",
    "score": "Score",

    # -------------------------
    # Media Metadata
    # -------------------------
    "media outlet": "Media Outlet",
    "outlet": "Media Outlet",
    "publisher": "Media Outlet",
    "publication": "Media Outlet",
    "source": "Media Outlet",

    "media type": "Media Item Type",
    "item type": "Media Item Type",

    # -------------------------
    # Article Content
    # -------------------------
    "full text": "Full Text",
    "article text": "Full Text",
    "text": "Full Text",

    "summary": "Summary",
    "article summary": "Summary",


    # -------------------------
    # Story Grouping
    # -------------------------
    "story id": "story_id",
    "story title": "story_title",
    "story summary": "story_summary",

    # -------------------------
    # Clustering
    # -------------------------
    "sub cluster id": "Sub_Cluster_ID",
    "sub cluster title": "Sub_Cluster_Title",

    # -------------------------
    # Ordering
    # -------------------------
    "ordering section": "Ordering_Section",
    "ordering reason": "Ordering_Reason",

    # -------------------------
    # Lead Article
    # -------------------------
    "is lead": "Is_Lead",
    "lead article": "Is_Lead",
    "leading item": "Is_Lead",
    "lead item": "Is_Lead",
}

class QueryEngine:

    def __init__(self, dataset_manager):

        self.dataset = dataset_manager
        self.df = dataset_manager.df

        self.id_col = dataset_manager.id_col
        self.rank_col = dataset_manager.rank_col
        self.score_col = dataset_manager.score_col

        self.sections = dataset_manager.sections

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

    def other_section_reasons(self, item_id, section=None):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return []

        row = row.iloc[0]

        selected_section = self.item_section(item_id)

        reasons = []

        for sec in self.sections:

            # skip the section where the item was actually placed
            if sec == selected_section:
                continue

            # if planner requested a specific section, filter
            if section and sec != section:
                continue

            col = f"{sec}_reason"

            if col in self.df.columns:

                reason = row[col]

                if isinstance(reason, str) and reason.strip():

                    relevant_text = None
                    text_col = f"{sec}_relevant_text"
                    if text_col in self.df.columns:
                        val = row[text_col]
                        if isinstance(val, str) and val.strip() and val.lower() != "nan":
                            relevant_text = val.strip()

                    relevance = None
                    rel_col = f"{sec}_relevance"
                    if rel_col in self.df.columns:
                        val = row[rel_col]
                        if isinstance(val, str) and val.strip():
                            relevance = val.strip()

                    reasons.append({
                        "section":       sec,
                        "reason":        reason,
                        "relevant_text": relevant_text,
                        "relevance":     relevance,
                    })

        return reasons

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
            self.df[col].astype(str).str.strip().str.lower().isin(["yes", "true", "1"]) &
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
            self.df[col].astype(str).str.strip().str.lower().isin(["yes", "true", "1"]) &
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

        if pd.isna(rank):
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

                if val in ["yes", "true", "1"]:
                    return sec

        return "Unselected"



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

                    relevant_text = None
                    text_col = f"{sec}_relevant_text"
                    if text_col in self.df.columns:
                        val = row[text_col]
                        if isinstance(val, str) and val.strip() and val.lower() != "nan":
                            relevant_text = val.strip()

                    relevance = None
                    rel_col = f"{sec}_relevance"
                    if rel_col in self.df.columns:
                        val = row[rel_col]
                        if isinstance(val, str) and val.strip():
                            relevance = val.strip()

                    reasons.append({
                        "section":       sec,
                        "reason":        reason,
                        "relevant_text": relevant_text,
                        "relevance":     relevance,
                    })

        return reasons


    def item_details(self, item_id):

        row = self.df[
            self.df[self.id_col].astype(str) == str(item_id)
            ]

        if row.empty:
            return None

        row = row.iloc[0]

        section = self.item_section(item_id)
        rank = self.item_rank(item_id)

        reason = None

        if section and section != "Unselected":

            col = f"{section}_reason"

            if col in self.df.columns:
                reason = row[col]

        return {
            "Item ID": str(item_id),
            "Headline": row.get("Headline"),
            "Date": row.get("Date"),
            "Media Outlet": row.get("Media Outlet"),
            "Page": row.get("Page Number"),
            "Rank": rank,
            "Score": row.get("Score"),
            "Section": section,
            "Reason": reason
        }


    def item_field(self, item_id, field):

        if not field:
            return None

        field = field.lower().replace("_", " ").strip()

        column = FIELD_MAP.get(field)

        if column is None:
            return None

        # fallback search
        if column not in self.df.columns:
            for col in self.df.columns:
                if column.lower() in col.lower():
                    column = col
                    break

        if column is None:
            return None

        row = self.df[
            self.df[self.id_col].astype(str) == str(item_id)
            ]

        if row.empty:
            return None

        value = row.iloc[0][column]

        if pd.isna(value):
            return "Not available in the dataset"

        return value


    # =====================================================
    # GENERIC FILTER ENGINE
    # =====================================================

    def filter_items(
            self,
            section=None,
            filters=None,
            sort_by=None,
            ascending=False,
            limit=10
    ):

        df = self.df.copy()

        # -----------------------------------
        # SECTION FILTER
        # -----------------------------------
        if section:

            col = f"{section}_answer"

            if col in df.columns:

                df = df[
                    df[col]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .isin(["yes", "true", "1"])
                ]

        # -----------------------------------
        # APPLY FILTERS
        # -----------------------------------
        if filters:

            for f in filters:

                field = f.get("field")
                operator = f.get("operator")
                value = f.get("value")

                if field not in df.columns:
                    continue

                # numeric conversion if possible
                try:
                    value = float(value)
                    df[field] = pd.to_numeric(df[field], errors="coerce")
                except:
                    pass

                if operator == ">":
                    df = df[df[field] > value]

                elif operator == "<":
                    df = df[df[field] < value]

                elif operator == ">=":
                    df = df[df[field] >= value]

                elif operator == "<=":
                    df = df[df[field] <= value]

                elif operator == "==":
                    df = df[df[field] == value]

                elif operator == "contains":

                    df = df[
                        df[field]
                        .astype(str)
                        .str.contains(str(value), case=False, na=False)
                    ]

        # -----------------------------------
        # SORTING
        # -----------------------------------
        if sort_by and sort_by in df.columns:

            df = df.sort_values(
                sort_by,
                ascending=ascending
            )

        # -----------------------------------
        # LIMIT
        # -----------------------------------
        df = df.head(limit)

        # -----------------------------------
        # FORMAT RESULTS
        # -----------------------------------
        results = []

        for _, row in df.iterrows():

            results.append({
                "Item ID": str(row[self.id_col]),
                "Headline": row.get("Headline"),
                "Score": row.get("Score"),
                "Section": self.item_section(row[self.id_col])
            })

        return results