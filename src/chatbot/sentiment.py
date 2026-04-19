import pandas as pd


def analyze_sentiment(df, model, id_col, text_col, item_id):

    row = df[df[id_col].astype(str) == str(item_id)]

    if row.empty:
        return {"type": "sentiment", "data": "Item not found"}

    row = row.iloc[0]

    text = None

    # Try to find usable text
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

Classify it as:
Positive, Negative, or Neutral.

Respond ONLY in this format:

Sentiment: Positive/Negative/Neutral
Explanation: <one short sentence explaining why>

Text:
{text}
"""

        response = model.generate_content(prompt)

        result = response.text.strip()

        sentiment = "Unknown"
        explanation = ""

        # Parse Gemini response safely
        for line in result.split("\n"):

            line = line.strip()

            if line.lower().startswith("sentiment"):
                sentiment = line.split(":", 1)[1].strip()

            if line.lower().startswith("explanation"):
                explanation = line.split(":", 1)[1].strip()

        return {
            "type": "sentiment",
            "data": {
                "Item ID": str(row[id_col]).replace(".0", ""),
                "Sentiment": sentiment,
                "Explanation": explanation
            }
        }

    except Exception as e:

        return {
            "type": "sentiment",
            "data": str(e)
        }