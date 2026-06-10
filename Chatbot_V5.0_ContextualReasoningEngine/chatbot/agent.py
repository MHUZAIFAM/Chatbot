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

        # ── HYPOTHETICAL PLACEMENT OVERRIDE ───────────────────
        # "if I were to place this in X, what changes are needed?"
        # User is asking what the guideline would need to say — always
        # generates a refinement, regardless of actual placement.

        _HYPOTHETICAL_KW = [
            "if i were to place", "if i place", "if we place",
            "if i wanted to place", "if i want to place",
            "what changes", "what would need to change",
            "what necessary changes", "necessary changes to the",
            "changes to the selection prompt", "changes to the guideline",
            "changes to the section prompt", "what would the guideline",
            "how would the guideline", "to include this in",
            "to place this in", "to put this in",
        ]
        _is_hypothetical_q = (
            item_id
            and any(kw in q_lower for kw in _HYPOTHETICAL_KW)
        )

        if _is_hypothetical_q:
            plan["operation"] = "hypothetical_placement"
            operation         = "hypothetical_placement"

        # ── PLACEMENT AUDIT OVERRIDE ───────────────────────────
        # Catch audit questions before the generic "why" handler grabs them.

        _AUDIT_KW = [
            "placed correctly", "placement correct", "correctly placed",
            "correctly unselected", "should it be", "shouldn't it be",
            "should it have been", "placed in wrong", "wrong section",
            "placed incorrectly", "incorrect placement", "should be in",
            "shouldnt it be", "should this be in",
            "where should this", "where should it", "where does this belong",
            "where does it belong", "what section should", "which section should",
            "what section does", "which section does",
        ]
        _is_audit_q = (
            item_id
            and any(kw in q_lower for kw in _AUDIT_KW)
        )

        if _is_audit_q:
            plan["operation"] = "item_placement_audit"
            operation         = "item_placement_audit"

        # ── UNSELECTED REASONS OVERRIDE ───────────────────────
        # "why wasn't it placed in any section?" → unselected_reasons
        # Must check BEFORE lead/similar guard since both contain "why wasn't"

        _UNSELECTED_KW = [
            "any section", "any of the sections", "not placed in any",
            "wasn't placed in any", "wasnt placed in any",
            "not selected", "why unselected", "why was it unselected",
            "why wasn't it selected", "wasnt it selected",
        ]
        _is_unselected_q = (
            item_id
            and any(kw in q_lower for kw in _UNSELECTED_KW)
        )

        if _is_unselected_q:
            plan["operation"] = "unselected_reasons"
            operation         = "unselected_reasons"

        # ── LEAD / SIMILAR OVERRIDE ────────────────────────────
        # Tightened: only fire on explicitly lead/similar vocabulary,
        # NOT on "why wasn't" which can belong to unselected questions.

        _LEAD_SIMILAR_KW = [
            "lead article", "similar article", "not a lead", "not lead",
            "why lead", "why similar", "why not lead", "why was it lead",
            "why was it similar", "is it lead", "is it similar",
            "lead item", "similar item",
        ]
        _is_lead_similar_q = (
            not _is_unselected_q  # don't override unselected detection
            and item_id
            and any(kw in q_lower for kw in _LEAD_SIMILAR_KW)
        )

        if _is_lead_similar_q:
            plan["operation"] = "item_type_reason"
            operation         = "item_type_reason"

        # ── RANKING WHY GUARD ──────────────────────────────────

        _RANK_WHY_PATTERNS = [
            r"\branked\b", r"\branking\b", r"\bposition\b",
            r"\bordered\b", r"\bordering\b",
            r"\brank\s*\d+\b", r"#\s*\d+",
            r"\b\d+(?:st|nd|rd|th)\b",
        ]
        _is_rank_why = (
            not _is_lead_similar_q
            and not _is_unselected_q
            and q_lower.startswith("why")
            and item_id
            and any(re.search(p, q_lower) for p in _RANK_WHY_PATTERNS)
        )

        if _is_rank_why:
            plan["operation"] = "item_field"
            plan["field"]     = "ordering reason"
            operation         = "item_field"

        elif (
            not _is_lead_similar_q
            and not _is_unselected_q
            and q_lower.startswith("why")
            and item_id
            and operation not in [
                "selected_reason",
                "other_section_reasons",
                "unselected_reasons",
                "item_type_reason",
                "item_placement_audit",
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

        # ── ITEM TYPE REASON (lead / similar) ──────────────────

        if operation == "item_type_reason":

            if not result or not isinstance(result, dict):
                answer = "Could not determine lead/similar reasoning for this item."
                self.memory.add(question, answer)
                return answer

            item_type      = result.get("item_type", "")
            is_lead        = result.get("is_lead", "")
            media_type     = result.get("media_type", "")
            outlet         = result.get("outlet", "")
            media_priority = result.get("media_priority")
            outlet_priority= result.get("outlet_priority")
            outlet_tier    = result.get("outlet_tier", "")
            rank           = result.get("rank")
            lead_item      = result.get("lead_item")
            lead_id        = result.get("lead_id", "")

            is_lead_item = item_type.lower() == "lead"

            # ── Fix: user asked "why wasn't X lead?" but X IS the lead ──
            # Find similar items that point to this item as their lead
            if is_lead_item and (
                "not" in q_lower or "wasn't" in q_lower or "wasnt" in q_lower
            ):
                similar_items = self.query_engine.get_similar_items(item_id)
                if similar_items:
                    similar_list = ", ".join(similar_items[:5])
                    answer = (
                        f"Item {item_id} is actually the <b>Lead</b> article. "
                        f"The following item(s) are marked as Similar to it: <b>{similar_list}</b>."
                    )
                else:
                    answer = (
                        f"Item {item_id} is the <b>Lead</b> article — "
                        f"there are no Similar items linked to it in this dataset."
                    )
                self.memory.add(question, answer)
                return answer

            # ── Build general statement ───────────────────────────
            if is_lead_item:
                statement = (
                    f"Item {item_id} is the <b>Lead</b> article. "
                    f"It is a {media_type} item from {outlet}"
                    + (f", holding media type priority {media_priority}" if media_priority else "")
                    + (f" and outlet priority {outlet_priority}" if outlet_priority else "")
                    + " according to the ordering guidelines."
                )
            else:
                if lead_item:
                    l_media = lead_item.get("media_type", "")
                    l_outlet = lead_item.get("outlet", "")
                    l_mp = lead_item.get("media_priority")
                    l_op = lead_item.get("outlet_priority")

                    if media_priority and l_mp and media_priority != l_mp:
                        reason_text = (
                            f"the lead item is a {l_media} "
                            f"(media type priority {l_mp}) "
                            f"while this item is a {media_type} "
                            f"(media type priority {media_priority}). "
                            f"Lower numbers mean higher priority."
                        )
                    elif outlet_priority and l_op and outlet_priority != l_op:
                        reason_text = (
                            f"both are {media_type} items, but the lead item is from "
                            f"{l_outlet} (outlet priority {l_op}) while this item is "
                            f"from {outlet} (outlet priority {outlet_priority}). "
                            f"Lower numbers mean higher priority."
                        )
                    else:
                        reason_text = (
                            f"the lead item ({lead_id}) ranked higher based on "
                            f"media type, outlet priority, date, or page number."
                        )

                    statement = (
                        f"Item {item_id} is <b>Similar</b> to item {lead_id} "
                        f"because {reason_text}"
                    )
                else:
                    statement = (
                        f"Item {item_id} is marked as <b>Similar</b> "
                        f"with lead article {lead_id}."
                    )

            # ── Build collapsible details box ─────────────────────
            def detail_row(label, this_val, lead_val=None):
                lead_cell = f"<td style='padding:8px 16px;'>{lead_val}</td>" if lead_val is not None else ""
                return (
                    f"<tr style='border-bottom:1px solid rgba(255,255,255,0.06);'>"
                    f"<td style='padding:8px 16px;color:#f0f0f0;font-weight:600;white-space:nowrap;'>{label}</td>"
                    f"<td style='padding:8px 16px;'>{this_val}</td>"
                    f"{lead_cell}"
                    f"</tr>"
                )

            # Fetch lead item rank
            lead_rank_val = ""
            if not is_lead_item and lead_item:
                lead_row_df = self.query_engine.df[
                    self.query_engine.df[self.query_engine.id_col].astype(str) == str(lead_id)
                ]
                if not lead_row_df.empty:
                    lr_rank = lead_row_df.iloc[0].get(self.query_engine.rank_col)
                    lead_rank_val = str(int(float(lr_rank))) if lr_rank and str(lr_rank) != "nan" else "Unranked"

            def media_label(raw_type, priority):
                if priority:
                    return f"{raw_type}&nbsp;&nbsp;<span style='color:#6b7280;font-size:11px;'>priority {priority}</span>"
                return str(raw_type)

            def outlet_label(priority, tier):
                if priority and tier:
                    return f"{priority}&nbsp;&nbsp;<span style='color:#6b7280;font-size:11px;'>({tier})</span>"
                return str(priority or "Unknown")

            if is_lead_item:
                header = (
                    f"<tr style='border-bottom:1px solid rgba(255,255,255,0.1);'>"
                    f"<th style='padding:8px 16px;text-align:left;color:#f0f0f0;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>Field</th>"
                    f"<th style='padding:8px 16px;text-align:left;color:#f0f0f0;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>{item_id}</th>"
                    f"</tr>"
                )
                rows = (
                    detail_row("Item Type",       item_type)
                    + detail_row("Is Lead",       is_lead)
                    + detail_row("Media Type",    media_label(media_type, media_priority))
                    + detail_row("Media Outlet",  outlet)
                    + detail_row("Outlet Priority", outlet_label(outlet_priority, outlet_tier))
                    + detail_row("Rank",          str(rank) if rank else "Unranked")
                )
            else:
                l = lead_item or {}
                header = (
                    f"<tr style='border-bottom:1px solid rgba(255,255,255,0.1);'>"
                    f"<th style='padding:8px 16px;text-align:left;color:#f0f0f0;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>Field</th>"
                    f"<th style='padding:8px 16px;text-align:left;color:#f0f0f0;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>{item_id}</th>"
                    f"<th style='padding:8px 16px;text-align:left;color:#f0f0f0;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>{lead_id}</th>"
                    f"</tr>"
                )
                rows = (
                    detail_row("Item Type",      item_type,   "Lead")
                    + detail_row("Is Lead",      is_lead,     "TRUE")
                    + detail_row("Media Type",
                                 media_label(media_type, media_priority),
                                 media_label(l.get("media_type",""), l.get("media_priority","")))
                    + detail_row("Media Outlet", outlet,      l.get("outlet",""))
                    + detail_row("Outlet Priority",
                                 outlet_label(outlet_priority, outlet_tier),
                                 outlet_label(l.get("outlet_priority",""), l.get("outlet_tier","")))
                    + detail_row("Rank",
                                 str(rank) if rank else "Unranked",
                                 lead_rank_val or "Unranked")
                )

            collapsible = (
                f"<br><br>"
                f"<details style='border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;'>"
                f"<summary style='padding:10px 16px;cursor:pointer;user-select:none;list-style:none;color:#8a8a8a;font-size:13px;outline:none;'>"
                f"Details"
                f"</summary>"
                f"<div style='border-top:1px solid rgba(255,255,255,0.08);'>"
                f"<table style='width:100%;border-collapse:collapse;font-size:13.5px;color:#c8c8c8;'>"
                f"{header}{rows}"
                f"</table>"
                f"</div>"
                f"</details>"
            )

            answer = statement + collapsible
            self.memory.add(question, answer)
            return answer

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

        # ── HYPOTHETICAL PLACEMENT ─────────────────────────────

        if operation == "hypothetical_placement":

            if not result or not isinstance(result, dict):
                answer = "Could not retrieve item context."
                self.memory.add(question, answer)
                return answer

            # Detect target section from question
            actual_section = result.get("current_section", "Unselected")
            target_section = None
            for slug in self.dataset_manager.sections:
                pretty = pretty_section(slug).lower()
                if pretty in q_lower or slug.lower().replace("_", " ") in q_lower:
                    target_section = slug
                    break

            if not target_section:
                answer = "Please specify which section you'd like to place this item in."
                self.memory.add(question, answer)
                return answer

            # Generate what the guideline would need to say
            refined = self.generator.hypothetical_refinement(
                item_context=result,
                target_section=target_section,
                target_rule=self.dataset_manager.section_prompts.get(target_section, ""),
                all_section_names=self.dataset_manager.sections,
            )

            def md_to_html(text):
                import re as _re
                text = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
                lines = text.split("\n")
                out = []
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("- "):
                        out.append(f"<div style='display:flex;gap:8px;margin:2px 0;padding-left:8px;'><span style='color:#6366f1;flex-shrink:0;'>•</span><span>{stripped[2:]}</span></div>")
                    elif stripped.startswith("### "):
                        out.append(f"<div style='color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;margin-top:10px;margin-bottom:4px;'>{stripped[4:]}</div>")
                    elif stripped == "":
                        out.append("<div style='height:6px;'></div>")
                    else:
                        out.append(f"<div style='margin:3px 0;'>{stripped}</div>")
                return "".join(out)

            intro = (
                f"To place this item in <b>{pretty_section(target_section)}</b>, "
                f"the section guideline would need the following changes:"
            )

            refined_html = md_to_html(refined)

            ref_rows = (
                f"<tr style='border-bottom:1px solid rgba(255,255,255,0.06);'>"
                f"<td style='padding:8px 16px;color:#f0f0f0;font-weight:600;white-space:nowrap;vertical-align:top;'>Section</td>"
                f"<td style='padding:8px 16px;color:#c8c8c8;'>{pretty_section(target_section)}</td></tr>"
                f"<tr><td style='padding:8px 16px;color:#f0f0f0;font-weight:600;vertical-align:top;'>Revised Guideline</td>"
                f"<td style='padding:8px 16px;color:#c8c8c8;'><div style='line-height:1.7;'>{refined_html}</div></td></tr>"
            )

            card = (
                f"<br><br>"
                f"<details style='border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;' open>"
                f"<summary style='padding:10px 16px;cursor:pointer;user-select:none;list-style:none;color:#8a8a8a;font-size:13px;outline:none;'>Hypothetical Guideline Change</summary>"
                f"<div style='border-top:1px solid rgba(255,255,255,0.08);'>"
                f"<table style='width:100%;border-collapse:collapse;font-size:13.5px;'>{ref_rows}</table>"
                f"</div></details>"
            )

            answer = intro + card
            self.memory.add(question, answer)
            return answer

        # ── ITEM PLACEMENT AUDIT ────────────────────────────────

        if operation == "item_placement_audit":

            if not result or not isinstance(result, dict):
                answer = "Could not retrieve item context for audit."
                self.memory.add(question, answer)
                return answer

            # Check if user specified a claimed section in the question
            # e.g. "was it correctly placed in Accidents?" or "placed in Road Safety?"
            actual_section  = result.get("current_section", "Unselected")
            claimed_section = actual_section  # default to actual

            section_slugs = self.dataset_manager.sections
            for slug in section_slugs:
                pretty = pretty_section(slug).lower()
                if pretty in q_lower or slug.lower().replace("_", " ") in q_lower:
                    claimed_section = slug
                    break

            # Run the AI audit against the CLAIMED section
            audit = self.generator.audit_placement(
                item_context=result,
                current_section=claimed_section,
                actual_section=actual_section,
                all_section_prompts=self.dataset_manager.section_prompts,
            )

            decision          = audit.get("decision", "")
            correct           = audit.get("correct")
            columns_used      = audit.get("columns_used", [])
            guideline_used    = audit.get("guideline_used", "")
            suggested_section = audit.get("suggested_section")
            suggested_reason  = audit.get("suggested_section_reason")
            refinement_needed = audit.get("refinement_needed", False)
            refined_rule      = audit.get("refined_rule")
            refined_section   = audit.get("refined_rule_section")
            current_section   = claimed_section

            # Correctness badge
            user_asked_wrong_section = (not correct) and (claimed_section != actual_section)
            genuinely_misplaced      = (not correct) and (claimed_section == actual_section)

            if correct is True:
                verdict_badge = "<span style='color:#34d399;font-weight:600;'>Correctly Placed</span>"
            elif user_asked_wrong_section:
                # Item IS correctly placed — user just asked about the wrong section
                verdict_badge = "<span style='color:#34d399;font-weight:600;'>Correctly Placed</span>"
            elif genuinely_misplaced:
                verdict_badge = "<span style='color:#ef4444;font-weight:600;'>Incorrectly Placed</span>"
            else:
                verdict_badge = "<span style='color:#f59e0b;font-weight:600;'>Uncertain</span>"

            # Pretty-print any raw section slugs in the AI decision text
            pretty_decision = decision
            for slug in self.dataset_manager.sections:
                pretty_decision = pretty_decision.replace(slug, pretty_section(slug))

            # Decision (plain text)
            decision_html = f"{verdict_badge}<br><br>{pretty_decision}"
            if not correct:
                if user_asked_wrong_section:
                    decision_html += (
                        f"<br><br>The item is correctly placed in "
                        f"<b>{pretty_section(actual_section)}</b> — "
                        f"{pretty_section(claimed_section)} is not the right section for this item."
                    )
                elif suggested_section:
                    decision_html += (
                        f"<br><br>It should be placed in "
                        f"<b>{pretty_section(suggested_section)}</b>. "
                        f"{suggested_reason or ''}"
                    )
                else:
                    # Genuinely misplaced but belongs nowhere — should be Unselected
                    decision_html += (
                        f"<br><br>This item does not qualify for any section under the current briefing rules "
                        f"and should be <b>Unselected</b>."
                    )

            # Shared card row helper
            def audit_row(label, value):
                return (
                    f"<tr style='border-bottom:1px solid rgba(255,255,255,0.06);'>"
                    f"<td style='padding:8px 16px;color:#f0f0f0;font-weight:600;white-space:nowrap;vertical-align:top;'>{label}</td>"
                    f"<td style='padding:8px 16px;color:#c8c8c8;'>{value}</td>"
                    f"</tr>"
                )

            # Details card
            actual_section_display = result.get("current_section", "Unselected")
            details_rows = (
                audit_row("Actual Section",    pretty_section(actual_section_display))
                + audit_row("Evaluated Against", pretty_section(current_section))
                + audit_row("Placement",       "Correct" if correct else ("Incorrect" if correct is False else "Uncertain"))
                + audit_row("Columns Examined", ", ".join(columns_used) if columns_used else "N/A")
                + audit_row("Guideline Applied", guideline_used or "N/A")
            )
            if suggested_section:
                details_rows += audit_row("Should Be In", f"<b>{pretty_section(suggested_section)}</b>")
            elif not correct and not user_asked_wrong_section:
                details_rows += audit_row("Should Be In", "<b>Unselected</b>")

            details_card = (
                f"<br><br>"
                f"<details style='border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;'>"
                f"<summary style='padding:10px 16px;cursor:pointer;user-select:none;list-style:none;color:#8a8a8a;font-size:13px;outline:none;'>Details</summary>"
                f"<div style='border-top:1px solid rgba(255,255,255,0.08);'>"
                f"<table style='width:100%;border-collapse:collapse;font-size:13.5px;'>{details_rows}</table>"
                f"</div></details>"
            )

            # Refinement card — always shown
            if refinement_needed and refined_rule:
                # Convert markdown to HTML for proper rendering
                def md_to_html(text):
                    import re as _re
                    # **bold**
                    text = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
                    # Lines starting with - → bullet
                    lines = text.split("\n")
                    out = []
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith("- "):
                            out.append(f"<div style='display:flex;gap:8px;margin:2px 0;padding-left:8px;'><span style='color:#6366f1;flex-shrink:0;'>•</span><span>{stripped[2:]}</span></div>")
                        elif stripped.startswith("### "):
                            out.append(f"<div style='color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;margin-top:10px;margin-bottom:4px;'>{stripped[4:]}</div>")
                        elif stripped == "":
                            out.append("<div style='height:6px;'></div>")
                        else:
                            out.append(f"<div style='margin:3px 0;'>{stripped}</div>")
                    return "".join(out)

                refined_html = md_to_html(refined_rule)
                ref_rows = (
                    audit_row("Section", pretty_section(refined_section or ""))
                    + audit_row("Status", "<span style='color:#f59e0b;font-weight:600;'>Refinement Suggested</span>")
                    + audit_row("Refined Rule", f"<div style='line-height:1.7;'>{refined_html}</div>")
                )
                ref_content = (
                    f"<table style='width:100%;border-collapse:collapse;font-size:13.5px;'>{ref_rows}</table>"
                )
            else:
                ref_content = (
                    f"<div style='padding:12px 16px;color:#6b7280;font-size:13.5px;'>"
                    f"The current guidelines are appropriate for this item. No refinement needed.</div>"
                )

            refinement_card = (
                f"<br>"
                f"<details style='border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;'>"
                f"<summary style='padding:10px 16px;cursor:pointer;user-select:none;list-style:none;color:#8a8a8a;font-size:13px;outline:none;'>Guideline Refinement</summary>"
                f"<div style='border-top:1px solid rgba(255,255,255,0.08);'>{ref_content}</div>"
                f"</details>"
            )

            answer = decision_html + details_card + refinement_card
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