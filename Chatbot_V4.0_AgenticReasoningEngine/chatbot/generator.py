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