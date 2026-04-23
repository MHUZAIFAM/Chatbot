import json
import google.generativeai as genai


class AnswerGenerator:

    def __init__(self, api_key):

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            "models/gemini-pro-latest"
        )

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

        response = self.model.generate_content(prompt)

        text = response.text.strip()

        # Remove markdown code blocks if Gemini adds them
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        # Try parsing JSON
        try:
            return json.loads(text)

        except Exception:

            # fallback if Gemini returns plain text
            return {
                "answer": text
            }