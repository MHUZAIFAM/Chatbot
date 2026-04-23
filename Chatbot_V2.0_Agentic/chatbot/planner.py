import json
import google.generativeai as genai


class Planner:

    def __init__(self, api_key):

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-pro-latest")

    def plan(self, question):

        prompt = f"""
You are a query planner for a dataset chatbot.

Your job is to convert the user question into a structured query plan.

Available operations:

count_items
count_sections
items_per_section
count_ranked_items
count_unranked_items
count_unselected_items
highest_ranked
lowest_ranked
highest_ranked_section
lowest_ranked_section
item_rank
item_section
list_sections

Return JSON only in this format:

{{
 "operation": "",
 "section": "",
 "item_id": ""
}}

User Question:
{question}
"""

        response = self.model.generate_content(prompt)

        text = response.text.strip()

        try:
            return json.loads(text)

        except:
            return {"operation": "unknown"}