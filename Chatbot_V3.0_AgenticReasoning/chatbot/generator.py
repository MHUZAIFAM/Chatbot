import json
from google import genai


class AnswerGenerator:

    def __init__(self, api_key):

        self.client = genai.Client(api_key=api_key)

        self.model = "gemini-2.5-flash"


    # =====================================================
    # GENERATE ANSWER
    # =====================================================

    def generate(self, question, data, memory_summary):

        prompt = f"""
You are a senior data analyst working for a media monitoring and research company.

Your job is to analyze dataset records and answer the user's question clearly.

Dataset Records:
{data}

Conversation Summary:
{memory_summary}

User Question:
{question}

Instructions:

- Use ONLY the dataset records provided.
- Do NOT invent information.
- If the dataset does not contain the answer, say so.
- Provide a clear natural language answer.

Return JSON ONLY in this format:

{{ "answer": "" }}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)

        except Exception:
            return {"answer": text}