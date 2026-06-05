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

        self.ordering_guidelines = dataset_manager.ordering_guidelines

    def _get_outlet_priority(self, media_item_type, outlet):
        """
        Look up the outlet priority number from ordering_guidelines.
        Returns (priority_number, tier_label) or (None, None) if not found.
        """
        if not self.ordering_guidelines or not outlet:
            return None, None

        media_type_lower = str(media_item_type).lower()

        if "newspaper" in media_type_lower or "print" in media_type_lower:
            table = self.ordering_guidelines.get("print", {})
        elif "online" in media_type_lower:
            table = self.ordering_guidelines.get("online", {})
        elif "radio" in media_type_lower or "broadcast" in media_type_lower or "television" in media_type_lower:
            table = self.ordering_guidelines.get("broadcast", {})
        else:
            table = {}

        outlet_lower = str(outlet).lower()
        for key, priority in table.items():
            if key.lower() in outlet_lower or outlet_lower in key.lower():
                return priority, key

        return None, None

    def _get_media_type_priority(self, media_item_type):
        """Return numeric priority for media type (Print=1, Online=2, Broadcast=3)."""
        if not self.ordering_guidelines:
            return None
        media_type_priority = self.ordering_guidelines.get("media_type_priority", {})
        media_lower = str(media_item_type).lower()
        if "newspaper" in media_lower or "print" in media_lower:
            return media_type_priority.get("Print")
        elif "online" in media_lower:
            return media_type_priority.get("Online")
        elif "radio" in media_lower or "broadcast" in media_lower or "television" in media_lower:
            return media_type_priority.get("Broadcast")
        return None

    def get_similar_items(self, lead_item_id):
        """Return list of item IDs that are Similar and point to this lead_item_id."""
        ds = self.dataset
        if not ds.lead_article_id_col or not ds.item_type_col:
            return []

        mask = (
            (self.df[ds.lead_article_id_col].astype(str) == str(lead_item_id))
            & (self.df[ds.item_type_col].astype(str).str.lower() == "similar")
        )
        return self.df[mask][self.id_col].astype(str).tolist()

    def item_type_reason(self, item_id):
        """
        Returns a dict explaining why this item is Lead or Similar,
        including comparison with lead article if item is Similar.
        """
        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return None

        row = row.iloc[0]

        ds = self.dataset

        item_type      = str(row.get(ds.item_type_col, "")).strip() if ds.item_type_col else ""
        is_lead        = str(row.get(ds.is_lead_col, "")).strip() if ds.is_lead_col else ""
        lead_id        = str(row.get(ds.lead_article_id_col, "")).strip() if ds.lead_article_id_col else ""
        media_type     = str(row.get("Media Item Type", "")).strip()
        outlet         = str(row.get("Media Outlet", "")).strip()
        rank           = row.get(self.rank_col)
        section        = self.item_section(item_id)

        media_priority  = self._get_media_type_priority(media_type)
        outlet_priority, outlet_tier = self._get_outlet_priority(media_type, outlet)

        result = {
            "item_id":         str(item_id),
            "item_type":       item_type,
            "is_lead":         is_lead,
            "lead_id":         lead_id,
            "media_type":      media_type,
            "outlet":          outlet,
            "media_priority":  media_priority,
            "outlet_priority": outlet_priority,
            "outlet_tier":     outlet_tier,
            "rank":            int(rank) if rank and str(rank) != "nan" else None,
            "section":         section,
            "lead_item":       None,
        }

        # If similar, also fetch lead article details for comparison
        if item_type.lower() == "similar" and lead_id and lead_id != str(item_id):
            lead_row = self.df[self.df[self.id_col].astype(str) == lead_id]
            if not lead_row.empty:
                lr = lead_row.iloc[0]
                l_media_type = str(lr.get("Media Item Type", "")).strip()
                l_outlet     = str(lr.get("Media Outlet", "")).strip()
                l_priority   = self._get_media_type_priority(l_media_type)
                l_out_pri, l_out_tier = self._get_outlet_priority(l_media_type, l_outlet)
                result["lead_item"] = {
                    "item_id":         lead_id,
                    "media_type":      l_media_type,
                    "outlet":          l_outlet,
                    "media_priority":  l_priority,
                    "outlet_priority": l_out_pri,
                    "outlet_tier":     l_out_tier,
                }

        return result

    def selected_reason(self, item_id):

        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return None

        row = row.iloc[0]

        section = self.item_section(item_id)

        if section == "Unselected":
            return None

        col = f"{section}_reason"

        if col not in self.df.columns:
            return None

        reason = row[col]

        if not isinstance(reason, str) or not reason.strip():
            return None

        relevant_text = None
        text_col = f"{section}_relevant_text"
        if text_col in self.df.columns:
            val = row[text_col]
            if isinstance(val, str) and val.strip() and val.lower() != "nan":
                relevant_text = val.strip()

        return {
            "section":       section,
            "reason":        reason,
            "relevant_text": relevant_text,
        }

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
    def item_placement_audit(self, item_id):
        """
        Gather all context needed for the AI placement audit.
        Returns a dict with article fields + current reasons for all sections.
        """
        row = self.df[self.df[self.id_col].astype(str) == str(item_id)]

        if row.empty:
            return None

        row = row.iloc[0]
        ds = self.dataset

        # Core article fields
        context = {
            "item_id":         str(item_id),
            "Headline":        str(row.get("Headline", "") or ""),
            "Full Text":       str(row.get(ds.full_text_col, "") or "") if ds.full_text_col else "",
            "Summary":         str(row.get(ds.summary_col, "") or "") if ds.summary_col else "",
            "Media Outlet":    str(row.get(ds.media_outlet_col, "") or "") if ds.media_outlet_col else "",
            "Media Item Type": str(row.get("Media Item Type", "") or ""),
            "Date":            str(row.get(ds.date_col, "") or "") if ds.date_col else "",
            "State":           str(row.get("state", "") or ""),
            "wordCount":       str(row.get(ds.wordcount_col, "") or "") if ds.wordcount_col else "",
            "current_section": self.item_section(item_id),
        }

        return context