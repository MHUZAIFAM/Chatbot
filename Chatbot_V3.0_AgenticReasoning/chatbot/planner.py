import json
import google.generativeai as genai

#=================================================
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json


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

unselected_items
→ return a list of items that were not selected for any section.

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

count_ranked_items_per_section
→ return the number of ranked items inside each section.

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

item_details
→ return full details about a specific item including:
Item ID, Date, Page, Section, Rank and selection reason.

count_items_in_section
→ return the number of items in a specific section.

item_field
→ return a specific dataset field for an item

ranked_items_per_section
→ returns all the ranked items in each section

section_with_most_items
→ return the section with the highest number of items

top_items_by_wordcount
→ return top items sorted by word count

average_wordcount_per_section
→ return average word count per section


Rules:

- If the question asks to COUNT items → use a counting operation.
- If the question asks to LIST or SHOW items inside a section → always use "items_in_section".
- If the question asks to LIST items in a section → use items_in_section.
- If the question mentions an item ID → fill "item_id".
- If the question mentions a section → fill "section".
- If no operation matches → return "unknown".
- If the user asks WHY an item was placed in a section → use "selected_reason".
- If the user asks why an item was not placed in other sections or asks why it was not placed elsewhere → use "other_section_reasons".
- If the item was unselected and the user asks WHY → use "unselected_reasons".
- If the question asks "how many ranked items in <section>" → use "count_ranked_items_in_section".
- If the user asks for details, information, or description about an item → use "item_details".
- If the user asks to LIST or SHOW unselected items → use "unselected_items".
- If the question asks "How many items in <section>" → use count_items_in_section
- If the user asks about a specific property of an item (headline, score, outlet, summary, word count, page, etc) use operation "item_field".
- If the user asks about section ordering, ordering section, where an item was placed, or which section it belongs to, use operation "item_field" and field "ordering section".
- If the question asks whether an item is leading, lead article, or Is_Lead → use operation "item_field".
- If question asks "highest number of articles" → use section_with_most_items
- If question asks "top by word count" → use top_items_by_wordcount

Reference Resolution Rules:

- The conversation context may contain previously discussed items.
- If the user uses pronouns like "it", "this item", "that item", or "there",
  resolve the reference using the conversation context.
- If the last discussed item ID appears in the context, reuse it.
- If the user asks whether an item should be placed in another section,
  use operation "other_section_reasons".
  
IMPORTANT:

- "number of articles" ALWAYS means TOTAL items, not ranked
- "top by word count" means sort using wordCount column, NOT rank
- "top ranked" ONLY refers to rank column

Return ONLY valid JSON:

{{
 "operation": "",
 "section": "",
 "item_id": "",
 "field": ""
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
                "field": None
            }