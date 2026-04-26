import json
import google.generativeai as genai


class Planner:

    def __init__(self, api_key):

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-pro-latest")

    def plan(self, question):

        prompt = f"""
You are a query planner for a dataset analysis chatbot.

Your job is to convert the user question into a structured query plan.

The dataset contains items grouped into sections and ranked.

Sections depend on the dataset and should NOT be invented.
If the user mentions a section, extract it exactly as written.

Available operations:

count_items
→ return the total number of items in the dataset.

count_sections
→ return the total number of sections in the dataset.

items_per_section
→ return the number of items assigned to each section.

count_ranked_items
→ return the total number of ranked items (Rank is not null).

count_ranked_items_in_section
→ return the number of ranked items inside a specific section.

count_unranked_items
→ return the total number of unranked items (Rank is null).

count_unselected_items
→ return the number of items that were not selected for any section.

highest_ranked
→ return the highest ranked item(s) in the dataset (lowest numerical rank).

lowest_ranked
→ return the lowest ranked item(s) in the dataset (highest numerical rank).

highest_ranked_section
→ return the highest ranked item within a specific section.

lowest_ranked_section
→ return the lowest ranked item within a specific section.

item_rank
→ return the rank of a specific item using its item ID.

item_section
→ return the section where a specific item was placed.

list_sections
→ return all available sections in the dataset.

section_with_most_ranked
→ return the section that contains the most ranked items.

top_ranked_items
→ return the top ranked items sorted by rank.

average_rank_per_section
→ return the average rank of items within each section.

unranked_items_per_section
→ return the number of unranked items within each section.

items_in_section
→ return all items in a section along with their ranks.

selected_reason
→ return the dataset reason explaining why an item was placed in its selected section.

other_section_reasons
→ return the dataset reasons explaining why the item was NOT placed in other sections.

unselected_reasons
→ return the dataset reasons explaining why the item was not selected for any section.

Rules:

- If the question asks to COUNT items → use a counting operation.
- If the question asks to LIST or SHOW items inside a section → always use "items_in_section".
- If the question asks to LIST items in a section → use items_in_section.
- If the question mentions an item ID → fill "item_id".
- If the question mentions a section → fill "section".
- If no operation matches → return "unknown".
- If the user asks WHY an item was placed in a section → use "selected_reason".
- If the user asks WHY an item was NOT placed in another section → use "other_section_reasons".
- If the item was unselected and the user asks WHY → use "unselected_reasons".
- If the question asks "how many ranked items in <section>" → use "count_ranked_items_in_section".

Return ONLY valid JSON:

{{
 "operation": "",
 "section": "",
 "item_id": ""
}}

Examples:

Question: How many items are there in the dataset?
Answer:
{{
 "operation": "count_items",
 "section": "",
 "item_id": ""
}}

Question: How many sections exist?
Answer:
{{
 "operation": "count_sections",
 "section": "",
 "item_id": ""
}}

Question: Which section was item 1168180533 placed in?
Answer:
{{
 "operation": "item_section",
 "section": "",
 "item_id": "1168180533"
}}

Question: What is the highest ranked item in a section?
Answer:
{{
 "operation": "highest_ranked_section",
 "section": "<section>",
 "item_id": ""
}}

Question: How many ranked items are there in a section?
Answer:
{{
 "operation": "count_ranked_items_in_section",
 "section": "<section>",
 "item_id": ""
}}

Question: How many unranked items are there?
Answer:
{{
 "operation": "count_unranked_items",
 "section": "",
 "item_id": ""
}}

Question: How many unranked items are there in each section?
Answer:
{{
 "operation": "unranked_items_per_section",
 "section": "",
 "item_id": ""
}}

Question: How many unselected items are there?
Answer:
{{
 "operation": "count_unselected_items",
 "section": "",
 "item_id": ""
}}

Question: Which section has the most ranked items?
Answer:
{{
 "operation": "section_with_most_ranked",
 "section": "",
 "item_id": ""
}}

Question: What are the top ranked items?
Answer:
{{
 "operation": "top_ranked_items",
 "section": "",
 "item_id": ""
}}

Question: What is the average rank per section?
Answer:
{{
 "operation": "average_rank_per_section",
 "section": "",
 "item_id": ""
}}

Question: List all ranked items in a section
Answer:
{{
 "operation": "items_in_section",
 "section": "<section>",
 "item_id": ""
}}

Question: Show all items in a section
Answer:
{{
 "operation": "items_in_section",
 "section": "<section>",
 "item_id": ""
}}

Question: Why was item 1168242419 placed in Health Care Industry?
Answer:
{{
 "operation": "selected_reason",
 "section": "",
 "item_id": "1168242419"
}}

Question: Why wasn't item 1168242419 placed in Hospitals?
Answer:
{{
 "operation": "other_section_reasons",
 "section": "hospitals_&_hospitals_in_the_home",
 "item_id": "1168242419"
}}

Question: Why was item 1168210045 unselected?
Answer:
{{
 "operation": "unselected_reasons",
 "section": "",
 "item_id": "1168210045"
}}

User Question:
{question}
"""

        response = self.model.generate_content(prompt)

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)

        except:
            return {"operation": "unknown"}