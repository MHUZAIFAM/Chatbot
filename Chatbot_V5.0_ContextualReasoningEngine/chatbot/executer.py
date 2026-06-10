class Executor:

    def __init__(self, query_engine):

        self.qe = query_engine

    def execute(self, plan):

        op = plan.get("operation")
        section = plan.get("section")
        item_id = plan.get("item_id")

        # -------------------------------------------------
        # RANKING
        # -------------------------------------------------

        if op == "highest_ranked":
            return self.qe.highest_ranked()

        if op == "lowest_ranked":
            return self.qe.lowest_ranked()

        if op == "highest_ranked_section":
            return self.qe.highest_ranked_section(section)

        if op == "lowest_ranked_section":
            return self.qe.lowest_ranked_section(section)

        if op == "top_ranked_items":
            return self.qe.top_ranked_items()

        # -------------------------------------------------
        # ITEM ANALYSIS
        # -------------------------------------------------

        if op == "item_rank":
            return self.qe.item_rank(item_id)

        if op == "item_section":
            return self.qe.item_section(item_id)

        if op == "item_details":
            return self.qe.item_details(item_id)

        if op == "item_field":
            return self.qe.item_field(
                item_id,
                plan.get("field")
            )

        # -------------------------------------------------
        # REASONING
        # -------------------------------------------------

        if op == "selected_reason":
            return self.qe.selected_reason(item_id)

        if op == "item_type_reason":
            return self.qe.item_type_reason(item_id)

        if op == "item_placement_audit":
            return self.qe.item_placement_audit(item_id)

        if op == "hypothetical_placement":
            return self.qe.item_placement_audit(item_id)

        if op == "other_section_reasons":
            return self.qe.other_section_reasons(
                item_id,
                section
            )

        if op == "unselected_reasons":
            return self.qe.unselected_reasons(item_id)

        # -------------------------------------------------
        # FILTERING
        # -------------------------------------------------

        if op == "filter_items":

            return self.qe.filter_items(
                section=section,
                filters=plan.get("filters"),
                sort_by=plan.get("sort_by"),
                ascending=plan.get("ascending", False),
                limit=plan.get("limit", 10)
            )

        return None