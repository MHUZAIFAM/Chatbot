import pandas as pd
import re
import json
import google.generativeai as genai

import pandas as pd

def handle_section_ranking(df, rank_col, id_col, sections, question):

    if not rank_col:
        return {"type": "ranking", "data": "No rank column found"}

    df = df.copy()
    df[rank_col] = pd.to_numeric(df[rank_col], errors="coerce")
    df = df.dropna(subset=[rank_col])

    q = question.lower()
    ascending = True

    if "lowest" in q or "worst" in q:
        ascending = False

    results = []

    for sec in sections:

        col = f"{sec}_answer"

        if col not in df.columns:
            continue

        df_sec = df[df[col].astype(str).str.lower() == "yes"]
        df_sec = df_sec.dropna(subset=[rank_col])

        if df_sec.empty:
            continue

        top = df_sec.sort_values(rank_col, ascending=ascending).iloc[0]

        results.append({
            "Section": sec,
            "Item ID": str(top[id_col]).replace(".0", ""),
            "Rank": int(top[rank_col])
        })

    return {
        "type": "ranking",
        "data": results
    }


