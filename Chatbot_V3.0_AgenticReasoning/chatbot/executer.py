class Executor:

    def __init__(self, query_engine):

        self.qe = query_engine

    def execute(self, plan):

        op = plan.get("operation")
        section = plan.get("section")
        item_id = plan.get("item_id")

        if op == "count_items":
            return self.qe.count_items()

        if op == "count_sections":
            return self.qe.count_sections()

        if op == "items_per_section":
            return self.qe.items_per_section()

        if op == "count_ranked_items":
            return self.qe.count_ranked_items()

        if op == "count_unranked_items":
            return self.qe.count_unranked_items()

        if op == "count_unselected_items":
            return self.qe.count_unselected_items()

        if op == "highest_ranked":
            return self.qe.highest_ranked()

        if op == "lowest_ranked":
            return self.qe.lowest_ranked()

        if op == "highest_ranked_section":
            return self.qe.highest_ranked_section(section)

        if op == "lowest_ranked_section":
            return self.qe.lowest_ranked_section(section)

        if op == "item_rank":
            return self.qe.item_rank(item_id)

        if op == "item_section":
            return self.qe.item_section(item_id)

        if op == "list_sections":
            return self.qe.list_sections()

        if op == "section_with_most_ranked":
            return self.qe.section_with_most_ranked()

        if op == "top_ranked_items":
            return self.qe.top_ranked_items()

        if op == "average_rank_per_section":
            return self.qe.average_rank_per_section()

        if op == "unranked_items_per_section":
            return self.qe.unranked_items_per_section()

        if op == "items_in_section":
            return self.qe.items_in_section(section)

        if op == "selected_reason":
            return self.qe.selected_reason(item_id)

        if op == "other_section_reasons":
            return self.qe.other_section_reasons(item_id)

        if op == "count_ranked_items_in_section":
            return self.qe.count_ranked_items_in_section(section)

        if op == "unselected_reasons":
            return self.qe.unselected_reasons(item_id)

        return None