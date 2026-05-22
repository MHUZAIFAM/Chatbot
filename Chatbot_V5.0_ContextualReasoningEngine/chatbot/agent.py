import logging
import re
from datetime import datetime

from chatbot.dataset import DatasetManager
from chatbot.query_engine import QueryEngine
from chatbot.retriever import DataRetriever
from chatbot.generator import AnswerGenerator
from chatbot.memory import ConversationMemory
from chatbot.planner import Planner
from chatbot.executer import Executor


# =============================================================
# DISPLAY HELPERS
# =============================================================

def pretty_section(raw):
    """
    'aged_and_community_care' → 'Aged and Community Care'
    'hospitals_&_hospitals_in_the_home' → 'Hospitals & Hospitals in the Home'
    """
    if not raw or raw == "Unselected":
        return raw
    return raw.replace("_", " ").title()


def pretty_date(raw):
    """
    '2026-02-03T18:04:00.000Z' → '3 Feb 2026'
    Falls back gracefully if format is unexpected.
    """
    if not raw:
        return raw
    raw_str = str(raw).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw_str, fmt)
            return dt.strftime("%-d %b %Y")
        except ValueError:
            continue
    return raw_str


def pretty_rank(raw):
    """
    9.0 → '9'  |  None → None  |  'Unranked' → 'Unranked'
    """
    if raw is None:
        return None
    if str(raw).lower() == "unranked":
        return "Unranked"
    try:
        return str(int(float(raw)))
    except (ValueError, TypeError):
        return str(raw)


# =============================================================
# AGENT
# =============================================================

class ChatbotAgent:

    def __init__(self, dataset_path, api_key, section_prompts_path=None):

        self.dataset_manager = DatasetManager(
            dataset_path,
            section_prompts_path=section_prompts_path
        )

        self.query_engine = QueryEngine(self.dataset_manager)
        self.retriever    = DataRetriever(self.dataset_manager)
        self.generator    = AnswerGenerator(api_key)
        self.memory       = ConversationMemory()
        self.planner      = Planner(api_key)
        self.executor     = Executor(self.query_engine)

    # ---------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ---------------------------------------------------------

    def ask(self, question):

        print("ASK FUNCTION TRIGGERED")
        print("QUESTION:", question)

        q_lower = question.lower()

        # ── AGGREGATE / STATS GUARD (pre-planner) ─────────────
        # Counting questions are outside this chatbot's scope.
        # Block them before wasting a planner API call.

        _AGG_PATTERNS = [
            r"\bhow many\b",
            r"\bcount\b",
            r"\btotal number\b",
            r"\bnumber of\b",
            r"\bhow much\b",
            r"\bwhat is the size\b",
            r"\bdataset size\b",
            r"\bhow large\b",
        ]
        _AGG_KEYWORDS = [
            "how many sections", "how many items", "how many ranked",
            "how many unranked", "how many unselected", "how many selected",
            "how many articles", "how many records", "how many rows",
            "total items", "total sections", "total articles", "total records",
            "number of sections", "number of items", "number of ranked",
            "number of unranked", "number of unselected", "number of selected",
            "number of articles", "items per section", "articles per section",
            "ranked per section", "unranked per section",
        ]

        if (
            any(re.search(p, q_lower) for p in _AGG_PATTERNS)
            or any(kw in q_lower for kw in _AGG_KEYWORDS)
        ):
            answer = (
                "This chatbot focuses on article reasoning, "
                "ranking, placement, and filtering."
            )
            self.memory.add(question, answer)
            return answer

        # ── REFERENCE RESOLUTION ───────────────────────────────
        # Replace "this item / that article / it" with last known item ID.

        if self.memory.last_item:
            ref_phrases = [
                "this item", "that item", "this article", "that article",
                "tell me about it", "tell me about this",
                "where was it placed", "why was it placed there",
                "why was it selected",
            ]
            if any(p in q_lower for p in ref_phrases):
                item_id_ref = str(self.memory.last_item)
                for old, new in {
                    "this item":    item_id_ref,
                    "that item":    item_id_ref,
                    "this article": item_id_ref,
                    "that article": item_id_ref,
                    "it":           item_id_ref,
                }.items():
                    question = re.sub(
                        rf"\b{re.escape(old)}\b",
                        new, question, flags=re.IGNORECASE
                    )

        # ── PLANNER ────────────────────────────────────────────

        context  = self.memory.summary()
        sections = ", ".join(self.dataset_manager.sections)

        plan = self.planner.plan(
            question=question,
            context=context,
            sections=sections
        )

        logging.info(f"PLANNER OUTPUT: {plan}")

        operation = plan.get("operation")
        item_id   = plan.get("item_id")

        # ── RANKING WHY GUARD ──────────────────────────────────
        # "Why was it ranked 9th?" → Ordering_Reason, not section reason.
        # Must fire BEFORE the generic "why" handler.

        _RANK_WHY_PATTERNS = [
            r"\branked\b", r"\branking\b", r"\bposition\b",
            r"\bordered\b", r"\bordering\b",
            r"\brank\s*\d+\b", r"#\s*\d+",
            r"\b\d+(?:st|nd|rd|th)\b",
        ]
        _is_rank_why = (
            q_lower.startswith("why")
            and item_id
            and any(re.search(p, q_lower) for p in _RANK_WHY_PATTERNS)
        )

        if _is_rank_why:
            plan["operation"] = "item_field"
            plan["field"]     = "ordering reason"
            operation         = "item_field"

        # ── GENERIC WHY HANDLER ────────────────────────────────
        elif (
            q_lower.startswith("why")
            and item_id
            and operation not in [
                "selected_reason",
                "other_section_reasons",
                "unselected_reasons",
            ]
        ):
            plan["operation"] = "selected_reason"
            operation         = "selected_reason"

        # ── EXECUTE ────────────────────────────────────────────

        result = self.executor.execute(plan)

        # ── UPDATE CONVERSATIONAL STATE ────────────────────────

        if plan.get("item_id"):
            self.memory.last_item = plan.get("item_id")
        if plan.get("section"):
            self.memory.last_section = plan.get("section")
        if plan.get("operation"):
            self.memory.last_operation = plan.get("operation")

        # ── UNSUPPORTED ────────────────────────────────────────

        if operation == "unknown":
            answer = (
                "This chatbot focuses on article reasoning, "
                "ranking, placement, and filtering."
            )
            self.memory.add(question, answer)
            return answer

        # ── RETRIEVAL + GENERATOR FALLBACK ─────────────────────

        if result is None:
            retrieved = self.retriever.retrieve(question)
            generated = self.generator.generate(
                question=question,
                retrieved_items=retrieved,
                memory=context
            )
            answer = generated.get("answer", str(generated))
            self.memory.add(question, answer)
            return answer

        # =======================================================
        # FORMAT RESPONSES
        # =======================================================

        # ── ITEM DETAILS ───────────────────────────────────────

        if operation == "item_details":
            lines = []

            def add(label, value):
                if value is not None and str(value).strip() not in ("", "nan"):
                    lines.append(f"<b>{label}:</b> {value}")

            add("Item ID",      result.get("Item ID"))
            add("Headline",     result.get("Headline"))
            add("Media Outlet", result.get("Media Outlet"))
            add("Date",         pretty_date(result.get("Date")))
            add("Page",         result.get("Page"))
            add("Rank",         pretty_rank(result.get("Rank")))
            add("Score",        result.get("Score"))
            add("Section",      pretty_section(result.get("Section")))
            add("Reason",       result.get("Reason"))

            answer = "<br>".join(lines)
            self.memory.add(question, answer)
            return answer

        # ── ITEM FIELD ─────────────────────────────────────────

        if operation == "item_field":
            field = str(plan.get("field", "")).lower().strip()

            if field in ("date", "publication date"):
                answer = pretty_date(result)
            elif field in ("rank", "ranking"):
                answer = pretty_rank(result)
            elif field in ("ordering section", "section"):
                # Ordering_Section column is only populated for ranked items.
                # For unselected/unranked items fall back to the logical section
                # derived from the _answer columns.
                raw = str(result).strip()
                if raw.lower() in ("not available in the dataset", "nan", "", "none"):
                    logical = self.query_engine.item_section(item_id)
                    answer = pretty_section(logical) if logical else "Unselected"
                else:
                    answer = pretty_section(raw)
            else:
                answer = str(result)

            self.memory.add(question, answer)
            return answer

        # ── ITEM RANK ──────────────────────────────────────────

        if operation == "item_rank":
            answer = f"Item {item_id} is ranked #{pretty_rank(result)}."
            self.memory.add(question, answer)
            return answer

        # ── ITEM SECTION ───────────────────────────────────────

        if operation == "item_section":
            if result == "Unselected" or not result:
                answer = f"Item {item_id} was not placed in any section."
            else:
                answer = f"Item {item_id} was placed in {pretty_section(result)}."
            self.memory.add(question, answer)
            return answer

        # ── SELECTED REASON ────────────────────────────────────

        if operation == "selected_reason":
            answer = str(result)
            self.memory.add(question, answer)
            return answer

        # ── OTHER SECTION REASONS / UNSELECTED REASONS ─────────

        if operation in ["other_section_reasons", "unselected_reasons"]:

            if not result:
                answer = "No section reasoning found for this item."
                self.memory.add(question, answer)
                return answer

            section_prompts = self.dataset_manager.section_prompts
            cards = []

            for entry in result:

                # Support both old tuple format and new dict format
                if isinstance(entry, dict):
                    section_slug  = entry["section"]
                    reason        = entry["reason"]
                    relevant_text = entry.get("relevant_text")
                    relevance     = str(entry.get("relevance") or "").strip()
                else:
                    section_slug, reason = entry
                    relevant_text = None
                    relevance     = ""

                label = pretty_section(section_slug)

                # Relevance colour badge
                rel_lower = relevance.lower()
                if rel_lower in ("not relevant",):
                    badge_color = "#ef4444"
                elif rel_lower == "low":
                    badge_color = "#f97316"
                elif rel_lower == "medium":
                    badge_color = "#f59e0b"
                elif rel_lower == "high":
                    badge_color = "#34d399"
                else:
                    badge_color = "#6b7280"

                badge = ""
                if relevance and rel_lower not in ("", "nan"):
                    badge = (
                        f"<span style='font-size:11px;font-weight:600;"
                        f"color:{badge_color};text-transform:uppercase;"
                        f"letter-spacing:0.05em;margin-left:8px;'>"
                        f"{relevance}</span>"
                    )

                # Briefing rule — extract "Do not include" block and render as bullets
                briefing_rule = section_prompts.get(section_slug, "")
                rule_html = ""
                if briefing_rule:
                    lower_rule = briefing_rule.lower()
                    do_not_idx = lower_rule.find("do not include")
                    excerpt = (
                        briefing_rule[do_not_idx:].strip()
                        if do_not_idx != -1
                        else briefing_rule.strip()
                    )

                    # Parse into lines, build bullet items
                    raw_lines = [l.strip() for l in excerpt.splitlines()]
                    bullet_items = []
                    for line in raw_lines:
                        if not line:
                            continue
                        # Header line e.g. "Do not include coverage of the following:"
                        if line.lower().startswith("do not include"):
                            bullet_items.append(
                                f"<div style='font-size:10px;text-transform:uppercase;"
                                f"letter-spacing:0.07em;color:#4b5563;font-weight:600;"
                                f"margin-bottom:6px;'>{line}</div>"
                            )
                        else:
                            # Split on → to style the redirect separately
                            if "→" in line:
                                rule_part, redirect = line.split("→", 1)
                                bullet_items.append(
                                    f"<div style='display:flex;gap:6px;margin-bottom:4px;'>"
                                    f"<span style='color:#4b5563;flex-shrink:0;'>•</span>"
                                    f"<span>{rule_part.strip()} "
                                    f"<span style='color:#6366f1;font-size:11px;'>"
                                    f"→ {redirect.strip()}</span></span></div>"
                                )
                            else:
                                bullet_items.append(
                                    f"<div style='display:flex;gap:6px;margin-bottom:4px;'>"
                                    f"<span style='color:#4b5563;flex-shrink:0;'>•</span>"
                                    f"<span>{line}</span></div>"
                                )

                    # Cap at 6 bullet items to avoid overwhelming the card
                    MAX_BULLETS = 6
                    shown   = bullet_items[:MAX_BULLETS + 1]  # +1 for header line
                    trimmed = len(bullet_items) > MAX_BULLETS + 1

                    rule_inner = "".join(shown)
                    if trimmed:
                        rule_inner += (
                            f"<div style='color:#4b5563;font-size:11px;"
                            f"margin-top:4px;'>…and more</div>"
                        )

                    rule_html = f"""
  <div style='margin-top:8px;padding:10px 12px;background:#0d1117;
              border-left:2px solid #374151;border-radius:4px;
              color:#8a8a8a;font-size:12.5px;line-height:1.6;'>
    {rule_inner}
  </div>"""

                # Key text from article
                text_html = ""
                if relevant_text:
                    text_html = f"""
  <div style='margin-top:8px;padding:8px 10px;background:#0d0d0d;
              border-left:2px solid #6366f1;border-radius:4px;
              color:#8a8a8a;font-size:12.5px;font-style:italic;line-height:1.55;'>
    "{relevant_text}"
  </div>"""

                card = f"""<div style='margin-bottom:18px;padding:12px 14px;
                                background:#161616;
                                border:1px solid rgba(255,255,255,0.08);
                                border-radius:10px;'>
  <div style='margin-bottom:6px;'>
    <b style='color:#f0f0f0;font-size:14px;'>{label}</b>{badge}
  </div>
  <div style='color:#c8c8c8;font-size:13.5px;line-height:1.6;'>
    {reason}
  </div>{text_html}{rule_html}
</div>"""

                cards.append(card)

            answer = "".join(cards)
            self.memory.add(question, answer)
            return answer

        # ── FILTER RESULTS ─────────────────────────────────────

        if operation == "filter_items":

            if not result:
                answer = "No matching items found."
                self.memory.add(question, answer)
                return answer

            lines = []
            for item in result:
                lines.append(
                    f"<div style='margin-bottom:16px'>"
                    f"<b>{item.get('Headline', 'Untitled')}</b><br>"
                    f"Item ID: {item.get('Item ID')}<br>"
                    f"Score: {item.get('Score')}<br>"
                    f"Rank: {pretty_rank(item.get('Rank'))}<br>"
                    f"Section: {pretty_section(item.get('Section'))}"
                    f"</div>"
                )
            answer = "".join(lines)
            self.memory.add(question, answer)
            return answer

        # ── RANKING RESULTS ────────────────────────────────────

        if operation in [
            "highest_ranked", "lowest_ranked", "top_ranked_items",
            "highest_ranked_section", "lowest_ranked_section",
        ]:
            if isinstance(result, list):
                lines = []
                for item in result:
                    lines.append(
                        f"<div style='margin-bottom:16px'>"
                        f"<b>{item.get('Headline', 'Untitled')}</b><br>"
                        f"Item ID: {item.get('Item ID')}<br>"
                        f"Rank: {pretty_rank(item.get('Rank'))}<br>"
                        f"Score: {item.get('Score')}<br>"
                        f"Section: {pretty_section(item.get('Section'))}"
                        f"</div>"
                    )
                answer = "".join(lines)
            else:
                answer = str(result)

            self.memory.add(question, answer)
            return answer

        # ── FINAL FALLBACK ─────────────────────────────────────

        answer = str(result)
        self.memory.add(question, answer)
        return answer