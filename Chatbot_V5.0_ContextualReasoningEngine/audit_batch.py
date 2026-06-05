"""
Batch Placement Audit Script
Chatbot V5.0 — BriefingAwareReasoning

Reads Full_Enriched_Dataset.csv and section_prompts.json,
runs the AI audit on every PLACED item, and outputs a CSV
flagging any misplacements with suggested corrections and
guideline refinements.

Usage:
    python audit_batch.py \
        --dataset  Data/Full_Enriched_Dataset.csv \
        --prompts  Data/section_prompts.json \
        --output   audit_results.csv \
        [--delay   1.5]   # seconds between API calls (default 1.0)
"""

import argparse
import json
import time
import re
from datetime import datetime

import pandas as pd
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
import asyncio


# ── helpers ──────────────────────────────────────────────────────────────────

def pretty_section(slug):
    if not slug or slug == "Unselected":
        return slug or "Unselected"
    return slug.replace("_", " ").title()


def detect_sections(df):
    return [
        col.replace("_answer", "")
        for col in df.columns
        if col.endswith("_answer")
    ]


def item_section(row, sections):
    for sec in sections:
        col = f"{sec}_answer"
        if col in row.index:
            val = str(row[col]).strip().lower()
            if val in ("yes", "true", "1"):
                return sec
    return "Unselected"


# ── agent SDK runner ──────────────────────────────────────────────────────────

def run_prompt(prompt_text):
    result_text = ""

    async def _q():
        nonlocal result_text
        async for msg in query(
            prompt=prompt_text,
            options=ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="dontAsk",
            ),
        ):
            if isinstance(msg, ResultMessage):
                result_text = msg.result or ""

    asyncio.run(_q())
    return result_text


# ── audit one item ────────────────────────────────────────────────────────────

def audit_item(row, current_section, sections_text, all_section_names):
    headline   = str(row.get("Headline", "") or "")
    outlet     = str(row.get("Media Outlet", "") or "")
    media_type = str(row.get("Media Item Type", "") or "")
    date       = str(row.get("Date", "") or "")
    state      = str(row.get("state", "") or "")
    wordcount  = str(row.get("wordCount", "") or "")
    summary    = str(row.get("Summary", "") or "")[:500]
    full_text  = str(row.get("Full Text", "") or "")[:1500]

    prompt = f"""
You are an independent media briefing auditor. Your job is to read a news article and decide which section it belongs in — WITHOUT being influenced by where it was previously placed.

ARTICLE DETAILS:
- Headline: {headline}
- Media Outlet: {outlet}
- Media Item Type: {media_type}
- Date: {date}
- State: {state}
- Word Count: {wordcount}
- Summary: {summary}
- Full Text (excerpt): {full_text}

PLACEMENT TO EVALUATE: "{current_section}"

BRIEFING RULES FOR ALL SECTIONS:
{sections_text}

YOUR TASK:
STEP 1: Read the article carefully. Identify the PRIMARY topic and any secondary topics.
STEP 2: Evaluate EACH section's inclusion and exclusion rules independently and strictly.
STEP 3: Decide which section this article belongs in (or Unselected).
STEP 4: Compare your verdict to the claimed placement "{current_section}". If they match: correct=true. If not: correct=false.
STEP 5: If wrong, set refinement_needed=true and refined_rule_section to the section slug that needs updating.

CRITICAL:
1. Do NOT default to correct just because there is some connection to the section.
2. Be strict — a passing mention does not qualify.
3. Your verdict must come from your own reading, not from the claimed placement.

Return ONLY valid JSON:
{{
  "my_verdict_section": "slug or null",
  "decision": "one sentence",
  "correct": true,
  "guideline_used": "rule text",
  "suggested_section": null,
  "refinement_needed": false,
  "refined_rule_section": null
}}
No markdown, no preamble.
"""

    text = run_prompt(prompt).strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {
            "my_verdict_section": None,
            "decision": text[:200],
            "correct": None,
            "guideline_used": "",
            "suggested_section": None,
            "refinement_needed": False,
            "refined_rule_section": None,
        }


def generate_refinement(section_slug, original_rule, article_context,
                        correct_section, wrong_section, all_section_names):
    section_names_list = "\n".join(
        f"- {s.replace('_', ' ').title()}" for s in all_section_names
    )
    category   = section_slug.replace("_", " ").title()
    headline   = article_context.get("Headline", "")
    summary    = str(article_context.get("Summary", ""))[:400]
    full_text  = str(article_context.get("Full Text", ""))[:1000]
    correct_label = (correct_section or "").replace("_", " ").title()
    wrong_label   = wrong_section.replace("_", " ").title()

    prompt = f"""
You are a Senior QA Analyst. An article was incorrectly placed in "{wrong_label}" when it should have been in "{correct_label}".

Original guideline for "{category}" that failed to prevent this:
---
{original_rule}
---

Misplaced article:
- Headline: {headline}
- Summary: {summary}
- Full Text excerpt: {full_text}

Rewrite the FULL refined criteria for "{category}" using this EXACT format:

**{category}**
[One-sentence overview.]

**Include coverage on the following:**
1. [Specific keywords/entities/people]
- [Entity A]

2. [Primary subject matter]
- [Sub-topic A]

3. [Secondary subject matter]
- [Sub-topic A]

**Exclusions:**
1. Prioritize [Section A] over [Section B] when coverage involves [nuance]
- [Sub-item A]

2. [Entities/keywords to exclude with reason]
- [Entity A]

3. [Subject matter to exclude with reason]
- [Sub-item A]

Rules:
- Use original descriptions verbatim where possible
- List every person/entity individually — no "..." or "etc."
- Redirection syntax: "Prioritize [A] over [B] when coverage involves [nuance]"
- No introductory or concluding remarks

Sibling sections:
{section_names_list}

Output the refined criteria only.
"""
    return run_prompt(prompt).strip()


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="Data/Full_Enriched_Dataset.csv")
    parser.add_argument("--prompts", default="Data/section_prompts.json")
    parser.add_argument("--output",  default="audit_results.csv")
    parser.add_argument("--delay",   type=float, default=1.0)
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Batch Placement Audit")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Load dataset
    df = pd.read_csv(args.dataset)
    print(f"Dataset loaded: {len(df)} rows")

    # Load section prompts
    with open(args.prompts, "r", encoding="utf-8") as f:
        prompts_data = json.load(f)
    section_prompts = prompts_data.get("sections", {})

    sections = detect_sections(df)
    print(f"Sections detected: {sections}\n")

    sections_text = "\n\n".join([
        f"SECTION: {slug}\n{rule}"
        for slug, rule in section_prompts.items()
    ])

    # Build audit list: placed items + unselected items
    placed_rows     = []
    unselected_rows = []
    for _, row in df.iterrows():
        sec = item_section(row, sections)
        if sec != "Unselected":
            placed_rows.append((row, sec))
        else:
            unselected_rows.append((row, "Unselected"))

    all_rows = placed_rows + unselected_rows
    print(f"Placed items to audit:     {len(placed_rows)}")
    print(f"Unselected items to audit: {len(unselected_rows)}")
    print(f"Total:                     {len(all_rows)}\n")

    results = []
    misplaced_count    = 0
    should_be_placed   = 0

    for i, (row, current_section) in enumerate(all_rows):
        item_id  = str(row.get("Item ID", row.get("MediaItemID", i)))
        headline = str(row.get("Headline", ""))[:80]
        label    = pretty_section(current_section)

        print(f"[{i+1}/{len(all_rows)}] {item_id} | {label} | {headline}")

        audit = audit_item(row, current_section, sections_text, sections)

        correct           = audit.get("correct")
        decision          = audit.get("decision", "")
        suggested         = audit.get("suggested_section")
        refinement_needed = audit.get("refinement_needed", False)
        refine_section    = audit.get("refined_rule_section")
        my_verdict        = audit.get("my_verdict_section")

        refined_rule = ""
        issue_type   = ""

        if current_section == "Unselected" and not correct and my_verdict and my_verdict != "null":
            # Unselected item that should have been placed
            issue_type = "Should Be Placed"
            should_be_placed += 1
            if refinement_needed and refine_section:
                print(f"  → Should be placed! Generating refinement for {refine_section}...")
                refined_rule = generate_refinement(
                    section_slug=refine_section,
                    original_rule=section_prompts.get(refine_section, ""),
                    article_context=row.to_dict(),
                    correct_section=my_verdict or suggested,
                    wrong_section="Unselected",
                    all_section_names=sections,
                )
            print(f"  ✘ SHOULD BE PLACED → {pretty_section(my_verdict or suggested)}")

        elif current_section != "Unselected" and not correct:
            # Placed item in wrong section
            issue_type = "Misplaced"
            misplaced_count += 1
            if refinement_needed and refine_section:
                print(f"  → Misplaced! Generating refinement for {refine_section}...")
                refined_rule = generate_refinement(
                    section_slug=refine_section,
                    original_rule=section_prompts.get(refine_section, ""),
                    article_context=row.to_dict(),
                    correct_section=my_verdict or suggested,
                    wrong_section=current_section,
                    all_section_names=sections,
                )
            print(f"  ✘ MISPLACED → should be {pretty_section(suggested or my_verdict)}")

        else:
            issue_type = ""
            print(f"  ✔ Correct")

        results.append({
            "Item ID":           item_id,
            "Headline":          str(row.get("Headline", ""))[:120],
            "Media Outlet":      str(row.get("Media Outlet", "")),
            "Media Type":        str(row.get("Media Item Type", "")),
            "Actual Section":    pretty_section(current_section),
            "AI Verdict":        pretty_section(my_verdict) if my_verdict and my_verdict != "null" else "Unselected",
            "Issue Type":        issue_type,
            "Correct":           "Yes" if not issue_type else "No",
            "Decision":          decision,
            "Suggested Section": pretty_section(suggested) if suggested else "",
            "Refinement Needed": "Yes" if refinement_needed else "No",
            "Refined Rule Section": pretty_section(refine_section) if refine_section else "",
            "Refined Rule":      refined_rule,
        })

        time.sleep(args.delay)

    # Save results
    out_df = pd.DataFrame(results)
    out_df.to_csv(args.output, index=False)

    print(f"\n{'='*60}")
    print(f"  AUDIT COMPLETE")
    print(f"  Total audited:          {len(all_rows)}")
    print(f"  Placed items:           {len(placed_rows)}")
    print(f"    - Correctly placed:   {len(placed_rows) - misplaced_count}")
    print(f"    - Misplaced:          {misplaced_count}")
    print(f"  Unselected items:       {len(unselected_rows)}")
    print(f"    - Correctly excluded: {len(unselected_rows) - should_be_placed}")
    print(f"    - Should be placed:   {should_be_placed}")
    print(f"  Total issues found:     {misplaced_count + should_be_placed}")
    print(f"  Results saved:          {args.output}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()