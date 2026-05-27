from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json


class AnswerGenerator:

    def __init__(self, api_key):

        load_dotenv()

        self.client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        self.model = "claude-sonnet-4-20250514"


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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print("\n===== GENERATOR TOKEN USAGE =====")
        print("Input Tokens:", response.usage.input_tokens)
        print("Output Tokens:", response.usage.output_tokens)
        print("==================================\n")

        text = response.content[0].text.strip()

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
        """
        Synthesises one "According to the briefing," sentence per section.

        mode="exclusion" — what the section requires that the article lacks
        mode="inclusion" — what the section requires that the article satisfies

        Returns { section_slug: sentence }
        """

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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print("\n===== SYNTHESISER TOKEN USAGE =====")
        print("Input Tokens: ", response.usage.input_tokens)
        print("Output Tokens:", response.usage.output_tokens)
        print("===================================\n")

        text = response.content[0].text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except Exception:
            return {e["section"]: e["reason"] for e in entries}