import asyncio
import json
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


class Planner:

    def __init__(self, api_key=None):
        # api_key ignored — auth via Claude subscription (claude auth login)
        pass

    def _run(self, prompt):
        """Run a single-turn query via Agent SDK and return the result text."""

        result_text = ""

        async def _query():
            nonlocal result_text
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    allowed_tools=[],
                    permission_mode="dontAsk",
                ),
            ):
                if isinstance(message, ResultMessage):
                    result_text = message.result or ""

        asyncio.run(_query())
        return result_text

    def plan(self, question, context="", sections=""):

        prompt = f"""
You are a query planner for a dataset reasoning chatbot.

Conversation Context:
{context}

User Question:
{question}

Convert the user question into a structured query plan.

Valid dataset sections:
{sections}

Only use valid sections.
Do not invent section names.

Available operations:

item_rank → item ranking
item_section → item placement section
item_details → item information
item_field → specific item field
selected_reason → why item was selected
other_section_reasons → why not placed elsewhere
unselected_reasons → why item was unselected
highest_ranked → highest ranked items
lowest_ranked → lowest ranked items
highest_ranked_section → highest ranked item in section
lowest_ranked_section → lowest ranked item in section
top_ranked_items → top ranked items
filter_items → dynamic filtering

Rules:
- item IDs → fill item_id
- section names → fill section
- item details/info/about item → item_details
- item properties/headline/score/page/date/outlet/etc → item_field
- placement questions → item_field with field "ordering section"
- why selected → selected_reason
- why not elsewhere → other_section_reasons
- why unselected → unselected_reasons
- filtering/above/below/contains/search/find → filter_items
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

        text = self._run(prompt).strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except Exception:
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