import pandas as pd


def analyze_sentiment(df, model, id_col, text_col, item_id):

    row = df[df[id_col].astype(str) == str(item_id)]

    if row.empty:
        return {"type": "sentiment", "data": "Item not found"}

    row = row.iloc[0]

    text = None

    for col in ["Full Text", "Headline", text_col]:

        if col and col in df.columns:
            val = row.get(col)

            if pd.notna(val):
                text = str(val)
                break

    if not text:
        return {"type": "sentiment", "data": "No text available"}

    try:

        prompt = f"""
Analyze the sentiment of the following news text.
Respond with ONLY one word: Positive, Negative, or Neutral.

Text:
{text}
"""

        response = model.generate_content(prompt)

        sentiment = response.text.strip()

        return {
            "type": "sentiment",
            "data": {
                "Item ID": str(row[id_col]).replace(".0", ""),
                "Sentiment": sentiment
            }
        }

    except Exception as e:

        return {
            "type": "sentiment",
            "data": str(e)
        }