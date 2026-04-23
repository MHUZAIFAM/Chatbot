def detect_intents(question):
    q = question.lower()

    intents = set()

    # dataset related keywords
    dataset_terms = ["section", "sections", "dataset", "news"]

    # -------- SCHEMA COUNT ----------
    if "how many sections" in q:
        return ["schema_count"]

    # -------- SCHEMA ----------
    if (
            "section" in q
            and any(x in q for x in ["what", "which", "list", "show", "present"])
            and not any(x in q for x in ["rank", "highest", "lowest"])
    ):
        intents.add("schema")
    # -------- RANKING ----------
    if any(x in q for x in ["rank", "lowest", "highest"]):
        intents.add("ranking")

    # -------- SECTION COUNTS ----------
    if (
            any(x in q for x in [
                "items per section",
                "items in each section",
                "how many items in each section"
            ])
            and not any(x in q for x in ["rank", "lowest", "highest"])
    ):
        intents.add("section_counts")

    # -------- SENTIMENT ----------
    if "sentiment" in q:
        intents.add("sentiment")

    # -------- AGGREGATION ----------
    if "how many" in q or "count" in q:

        if "item" in q or "items" in q:

            # total items
            if "dataset" in q or "there" in q:
                intents.add("total_items")

            # section specific
            if "council mentions" in q or "council_mentions" in q:
                intents.add("count_council")

            if "other news" in q or "other_news" in q:
                intents.add("count_other")

            if "unselected" in q:
                intents.add("count_unselected")

            # generic items per section
            intents.add("aggregation")

    # -------- LISTING ----------
    if any(x in q for x in ["list", "show"]):
        intents.add("listing")

    # -------- EXPLAIN ----------
    if any(x in q for x in [
        "why",
        "reason",
        "tell me about",
        "about item",
        "explain item",
        "explain"
    ]):
        intents.add("explain")

    # -------- FALLBACK ----------
    if not intents:
        return ["unknown"]

    return list(intents)
