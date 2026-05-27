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
    if not raw or raw == "Unselected":
        return raw
    return raw.replace("_", " ").title()


def pretty_date(raw):
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
    if raw is None:
        return None
    if str(raw).lower() == "unranked":
        return "Unranked"
    try:
        return str(int(float(raw)))
    except (ValueError, TypeError):
        return str(raw)


def make_card(label, badge, reason, relevant_text, briefing_sentence):
    """Shared plain-text response for both selected and exclusion reasons."""

    parts = []

    # Section label + badge (badge is HTML span, only used for exclusions)
    parts.append(f"<b>{label}</b>{badge}")

    # Reason
    parts.append(reason)

    # Key article text
    if relevant_text:
        parts.append(f'<i style="color:#8a8a8a;">"{relevant_text}"</i>')

    # Briefing context sentence
    if briefing_sentence:
        parts.append(briefing_sentence)

    return "<br><br>".join(parts)


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

    def ask(self, question):

        print("ASK FUNCTION TRIGGERED")
        print("QUESTION:", question)

        q_lower = question.lower()

        # ── AGGREGATE / STATS GUARD ────────────────────────────

        _AGG_PATTERNS = [
            r"\bhow many\b", r"\bcount\b", r"\btotal number\b",
            r"\bnumber of\b", r"\bhow much\b", r"\bwhat is the size\b",
            r"\bdataset size\b", r"\bhow large\b",
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

        # ── UPDATE STATE ───────────────────────────────────────

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

            if not isinstance(result, dict):
                answer = str(result)
                self.memory.add(question, answer)
                return answer

            section_slug  = result.get("section", "")
            reason        = result.get("reason", "")
            relevant_text = result.get("relevant_text")
            label         = pretty_section(section_slug)

            briefing_rule     = self.dataset_manager.section_prompts.get(section_slug, "")
            briefing_sentence = ""

            if briefing_rule:
                synth = self.generator.synthesise_exclusions([{
                    "section":       section_slug,
                    "section_label": label,
                    "reason":        reason,
                    "relevant_text": relevant_text or "",
                    "briefing_rule": briefing_rule,
                }], mode="inclusion")
                briefing_sentence = synth.get(section_slug, "")

            answer = make_card(
                label=label,
                badge="",
                reason=reason,
                relevant_text=relevant_text,
                briefing_sentence=briefing_sentence,
            )

            self.memory.add(question, answer)
            return answer

        # ── OTHER SECTION REASONS / UNSELECTED REASONS ─────────

        if operation in ["other_section_reasons", "unselected_reasons"]:

            if not result:
                answer = "No section reasoning found for this item."
                self.memory.add(question, answer)
                return answer

            section_prompts = self.dataset_manager.section_prompts

            normalised = []
            for entry in result:
                if isinstance(entry, dict):
                    normalised.append(entry)
                else:
                    section_slug, reason = entry
                    normalised.append({
                        "section":       section_slug,
                        "reason":        reason,
                        "relevant_text": None,
                        "relevance":     "",
                    })

            # Batch synthesise all sections in one API call
            synth_input = []
            for entry in normalised:
                slug = entry["section"]
                synth_input.append({
                    "section":       slug,
                    "section_label": pretty_section(slug),
                    "reason":        entry["reason"],
                    "relevant_text": entry.get("relevant_text") or "",
                    "briefing_rule": section_prompts.get(slug, ""),
                })

            synthesised = self.generator.synthesise_exclusions(synth_input, mode="exclusion")

            cards = []

            for entry in normalised:

                section_slug  = entry["section"]
                reason        = entry["reason"]
                relevant_text = entry.get("relevant_text")
                relevance     = str(entry.get("relevance") or "").strip()
                label         = pretty_section(section_slug)

                briefing_sentence = synthesised.get(section_slug, "")

                # Relevance badge
                rel_lower = relevance.lower()
                if rel_lower == "not relevant":
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

                cards.append(make_card(
                    label=label,
                    badge=badge,
                    reason=reason,
                    relevant_text=relevant_text,
                    briefing_sentence=briefing_sentence,
                ))

            answer = "<br><br><br>".join(cards)
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