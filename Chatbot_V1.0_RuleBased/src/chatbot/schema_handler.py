def handle_schema(sections):

    return {
        "type": "schema",
        "data": {
            "Sections": sections,
            "Total_Sections": len(sections)
        }
    }


def handle_schema_count(sections):

    return {
        "type": "schema_count",
        "data": {
            "Total_Sections": len(sections)
        }
    }