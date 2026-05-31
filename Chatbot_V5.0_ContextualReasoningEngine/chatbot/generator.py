import asyncio
import json
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


class AnswerGenerator:

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


    # =====================================================
    # GENERATE ANSWER
    # =====================================================

    def generate(self, question, retrieved_items, memory):
        safe_data = str(retrieved_items)[:8000]

        prompt = f"""
Answer using ONLY the dataset records provided.

Your job is to analyze dataset records and answer the user's question clearly.

Dataset Records:
{safe_data}

Conversation Summary:
{memory}

User Question:
{question}

Instructions:
- Use ONLY the dataset records provided.
- Do NOT invent information.
- If the dataset does not contain the answer, say so.

Return JSON ONLY in this format:

{{ "answer": "" }}
"""

        text = self._run(prompt).strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except Exception:
            return {"answer": text}


    # =====================================================
    # SYNTHESISE BRIEFING CONTEXT
    # =====================================================

    def synthesise_exclusions(self, entries, mode="exclusion"):

        sections_payload = []
        for e in entries:
            sections_payload.append({
                "section":       e["section"],
                "section_label": e["section_label"],
                "reason":        e["reason"],
                "relevant_text": e.get("relevant_text") or "",
                "briefing_rule": e.get("briefing_rule") or "",
            })

        if mode == "inclusion":
            instruction = (
                'For each section below, write ONE clear sentence (max 40 words) starting with '
                '"According to the briefing," that explains what criteria this section requires '
                'and why this article satisfies them, based on the briefing_rule provided.'
            )
        else:
            instruction = (
                'For each section below, write ONE clear sentence (max 40 words) starting with '
                '"According to the briefing," that explains what the section requires or explicitly '
                'excludes, based on the briefing_rule provided.'
            )

        prompt = f"""
You are helping explain briefing rules to a media analyst.

{instruction}

Rules:
- Start every sentence with "According to the briefing,"
- Focus on what the section requires or excludes, not on the article itself
- Write in plain English, no jargon
- Do not use em dashes
- Do not repeat the section name in the sentence

Sections:
{json.dumps(sections_payload, indent=2)}

Return ONLY valid JSON, one key per section slug:

{{
  "section_slug_1": "According to the briefing, ...",
  "section_slug_2": "According to the briefing, ..."
}}

No extra keys, no markdown, no preamble.
"""

        text = self._run(prompt).strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except Exception:
            return {e["section"]: e["reason"] for e in entries}