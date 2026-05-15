import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv


class Planner:

    def __init__(self, api_key):

        load_dotenv()

        self.client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        self.model = "claude-sonnet-4-20250514"

    def plan(self, question, context="", sections=""):

        prompt = f"""
You are a query planner for a dataset analysis chatbot.

Conversation Context:
{context}

User Question:
{question}

Your job is to convert the user question into a structured query plan.

The dataset contains items grouped into sections and ranked.
Valid dataset sections:
{sections}

Only use these sections if a section is required.
Do NOT invent new section names.

Sections depend on the dataset and should NOT be invented.
If the user mentions a section, extract it exactly as written.

Available operations:

count_items → total dataset items
count_sections → total sections
items_per_section → item counts per section

count_ranked_items → ranked item count
count_unranked_items → unranked item count
count_unselected_items → unselected item count

count_items_in_section → items in section
count_ranked_items_in_section → ranked items in section
count_ranked_items_per_section → ranked counts per section
unranked_items_per_section → unranked counts per section

highest_ranked → best ranked items
lowest_ranked → lowest ranked items
highest_ranked_section → best ranked in section
lowest_ranked_section → lowest ranked in section
top_ranked_items → top ranked items

section_with_most_items → section with most items
section_with_most_ranked → section with most ranked items
average_rank_per_section → average rank per section

list_sections → list sections
items_in_section → list items in section
ranked_items_per_section → ranked items grouped by section
unselected_items → list unselected items

item_rank → item rank
item_section → item section
item_details → item details
item_field → specific item field

selected_reason → why item selected
other_section_reasons → why not placed elsewhere
unselected_reasons → why item unselected

filter_items → dynamic filtering

Rules:

- count questions → counting operations
- list/show section items → items_in_section
- item IDs → fill item_id
- section names → fill section
- item details/info → item_details
- item properties/headline/score/page/etc → item_field
- placement/ordering section questions → item_field with field "ordering section"

- why selected → selected_reason
- why not elsewhere → other_section_reasons
- why unselected → unselected_reasons

- highest number of articles → section_with_most_items
- ranked item counts in section → count_ranked_items_in_section

- filtering/above/below/contains → filter_items

- "number of articles" means TOTAL items
- "top ranked" refers to rank column

- unknown intent → operation "unknown"

Return ONLY valid JSON:

{{
 "operation": "",
 "section": "",
 "item_id": "",
 "field": "",
 "filters": [],
 "sort_by": "",
 "ascending": false,
 "limit": 10
}}

"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print("\n===== PLANNER TOKEN USAGE =====")
        print("Input Tokens:", response.usage.input_tokens)
        print("Output Tokens:", response.usage.output_tokens)
        print("================================\n")

        text = response.content[0].text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)

        except:
            return {
                "operation": "unknown",
                "section": None,
                "item_id": None,
                "field": None,
                "filters": [],
                "sort_by": "",
                "ascending": False,
                "limit": 10
            }