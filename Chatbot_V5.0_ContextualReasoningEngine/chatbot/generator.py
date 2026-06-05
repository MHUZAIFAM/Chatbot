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

    # =====================================================
    # PLACEMENT AUDIT
    # =====================================================

    def audit_placement(self, item_context, current_section, all_section_prompts, actual_section=None):
        """
        AI independent audit of whether an item was placed correctly.

        current_section: the section being evaluated (claimed by user or from dataset)
        actual_section:  the real section in the dataset (may differ from current_section)
        """

        sections_text = "\n\n".join([
            f"SECTION: {slug}\n{rule}"
            for slug, rule in all_section_prompts.items()
        ])

        # If user claimed a different section than actual, flag it
        if actual_section and actual_section != current_section:
            placement_context = (
                f'The user claims this item was placed in "{current_section}". '
                f'Its ACTUAL placement in the dataset is "{actual_section}". '
                f'Evaluate whether "{current_section}" would be correct — '
                f'regardless of where it actually sits.'
            )
        else:
            placement_context = (
                f'The CLAIMED placement to evaluate is: "{current_section}"'
            )

        prompt = f"""
You are an independent media briefing auditor. Your job is to read a news article and decide which section it belongs in — WITHOUT being influenced by where it was previously placed.

ARTICLE DETAILS:
- Headline: {item_context.get('Headline', '')}
- Media Outlet: {item_context.get('Media Outlet', '')}
- Media Item Type: {item_context.get('Media Item Type', '')}
- Date: {item_context.get('Date', '')}
- State: {item_context.get('State', '')}
- Word Count: {item_context.get('wordCount', '')}
- Summary: {item_context.get('Summary', '')[:500]}
- Full Text (excerpt): {str(item_context.get('Full Text', ''))[:1500]}

PLACEMENT TO EVALUATE:
{placement_context}

BRIEFING RULES FOR ALL SECTIONS:
{sections_text}

YOUR TASK — follow these steps in order:

STEP 1: Read the article carefully. Identify the PRIMARY topic and any secondary topics.

STEP 2: Go through EACH section's rules independently. For each section ask:
  - Does the article's PRIMARY content match the inclusion criteria?
  - Does the article trigger any exclusion criteria?
  - Be strict — a passing mention does not qualify. The content must be substantively about the criterion.

STEP 3: Based purely on your own reading, decide which section (if any) this article belongs in.

STEP 4: Evaluate the CLAIMED placement "{current_section}":
  - Does your verdict match the claimed placement?
  - If yes: correct = true
  - If no: correct = false — state where it should actually go and why

STEP 5: If the placement is wrong, set refinement_needed = true and set refined_rule_section to the slug of the section whose rule needs updating. Leave refined_rule as null — it will be generated separately.

If the placement is correct, set refinement_needed = false.

CRITICAL — avoid these two failure modes:
1. Do NOT default to "correct" just because the article has some connection to the claimed section. If a clearly better section exists, the placement is wrong.
2. Do NOT be swayed by question phrasing. If the question says "shouldn't it be in X?" that is NOT evidence it belongs in X. Evaluate purely on article content and rules. If X is wrong, say it is wrong — even if the user seems to expect it.

Your verdict must come from STEP 3 (your independent reading) — not from what the user implies.

Return ONLY valid JSON:

{{
  "my_verdict_section": "the section slug you determined, or null if Unselected",
  "decision": "One plain-English sentence explaining your verdict and whether it matches the claimed placement",
  "correct": true,
  "columns_used": ["Headline", "Full Text", "Summary"],
  "guideline_used": "The specific rule text that drove your decision",
  "suggested_section": null,
  "suggested_section_reason": null,
  "refinement_needed": false,
  "refined_rule": null,
  "refined_rule_section": null
}}

No markdown, no preamble, return raw JSON only.
"""

        text = self._run(prompt).strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except Exception:
            result = {
                "decision": text,
                "correct": None,
                "columns_used": [],
                "guideline_used": "",
                "suggested_section": None,
                "suggested_section_reason": None,
                "refinement_needed": False,
                "refined_rule": None,
                "refined_rule_section": None,
            }

        # If refinement needed, run second call with QA analyst prompt
        # Only fire when item is genuinely misplaced (claimed == actual but wrong)
        # Not when user simply asked about a hypothetical wrong section
        if (
            result.get("refinement_needed")
            and result.get("refined_rule_section")
            and current_section == actual_section  # genuinely misplaced
        ):
            refined_rule = self._generate_refined_rule(
                section_slug=result["refined_rule_section"],
                original_rule=all_section_prompts.get(result["refined_rule_section"], ""),
                article_context=item_context,
                correct_section=result.get("my_verdict_section") or result.get("suggested_section"),
                wrong_section=current_section,
                all_section_names=list(all_section_prompts.keys()),
            )
            result["refined_rule"] = refined_rule

        return result

    # =====================================================
    # GENERATE STRUCTURED REFINED RULE (QA ANALYST FORMAT)
    # =====================================================

    def _generate_refined_rule(
        self,
        section_slug,
        original_rule,
        article_context,
        correct_section,
        wrong_section,
        all_section_names,
    ):
        section_names_list = "\n".join(f"- {s.replace('_', ' ').title()}" for s in all_section_names)
        category    = section_slug.replace("_", " ").title()
        headline    = article_context.get("Headline", "")
        summary     = article_context.get("Summary", "")[:400]
        full_text   = str(article_context.get("Full Text", ""))[:1000]

        prompt = f"""
You are a Senior QA Analyst. An article was incorrectly placed in "{wrong_section.replace('_',' ').title()}" when it should have been in "{(correct_section or '').replace('_',' ').title()}".

The original guideline for "{category}" that failed to prevent this error:

---
{original_rule}
---

The article that was misplaced:
- Headline: {headline}
- Summary: {summary}
- Full Text excerpt: {full_text}

Your task: Rewrite the FULL refined criteria for "{category}" using the exact format below.
The refined version must be specific enough that this article would be correctly handled next time.
Do not change the intent of the original. Only add specificity, clarify boundaries, or strengthen redirects.

Use this EXACT format:

**{category}**
[A one-sentence overview of the section's identity / scope of content it should cover.]

**Include coverage on the following:**
1. [Specific keywords, entities, or people to include]
- [Entity A]
- [Entity B]

2. [Primary subject matter to include]
- [Sub-topic A]
- [Sub-topic B]

3. [Secondary subject matter to include]
- [Sub-topic A]
- [Sub-topic B]

**Exclusions:**
1. Prioritize [Section Name A] over [Section Name B] when coverage involves [specific nuance]
- [Sub-item A]
- [Sub-item B]

2. [Specific entities or keywords to exclude, with reason]
- [Entity A]

3. [Subject matter to exclude, with reason]
- [Sub-item A]

### Processing Rules
- Do not rewrite original descriptions — use them verbatim where possible
- Zero-Omission Policy: list every person, project, and entity individually — no "..." or "etc."
- Use exact redirection syntax: "Prioritize [Section A] over [Section B] when coverage involves [nuance]"
- No introductory or concluding remarks — output the refined criteria only

### Sibling Sections in This Briefing (for Redirects):
{section_names_list}

Output the refined criteria only. No preamble, no explanation.
"""
        return self._run(prompt).strip()