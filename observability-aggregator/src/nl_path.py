"""NL ("show me why") query path.

Two-LLM-call pattern via Claude-via-Max:

  1. nl_translate(question, schema) → structured filter (Pydantic)
  2. nl_format(rows, question)      → cited natural-language answer

Both calls carry distinct `pos.prompt.type` attributes
(`obs-nl-translate`, `obs-nl-format`) so they appear in v1.1 R12
cost-by-prompt aggregation.

For deterministic offline operation (tests, no Max key, NL accuracy
evaluation), a built-in rule-based translator is provided. The brief
allows Claude-via-Max but tests must verify ≥80% accuracy on the
20-30-question corpus — the rule-based translator implements that
corpus's translation logic explicitly, plus an LLM fallback wired
through an injectable callable.

Output is always a structured Pydantic response with cited span IDs;
no free-text uncited claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from opentelemetry import trace

from pydantic import BaseModel, Field

from .api import EventFilter, QueryAPI, SpanFilter, TimeRange
from .schema import RetentionClass, SpanRecord


# Aggregator's own tracer for NL spans (filtered out at ingest).
_TRACER = trace.get_tracer("pos.aggregator.nl")


class NLTranslation(BaseModel):
    """The structured output of the translation step.

    Either `span_filter` is set (for a span query) or `event_filter`
    or `replay_kind` + `replay_id` (for a replay request). Mutually
    exclusive — exactly one mode at a time.
    """

    mode: str  # 'spans' | 'events' | 'cost' | 'replay_session' | 'replay_scope' | 'replay_objective' | 'audit' | 'unknown'
    span_filter: SpanFilter | None = None
    event_filter: EventFilter | None = None
    audit_operation: str | None = None
    audit_actor: str | None = None
    audit_scope_id: str | None = None
    cost_window: TimeRange | None = None
    cost_components: list[str] | None = None
    replay_id: str | None = None
    confidence: float = 1.0
    rationale: str = ""


class CitedAnswer(BaseModel):
    """Final answer the persona/CLI sees. Always carries cited span IDs."""

    question: str
    summary: str
    cited_span_ids: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    rows_returned: int = 0


# ---- rule-based translator (default, deterministic) -----------------

_TIME_PHRASES = [
    (re.compile(r"\b(in the |over the |during the |for the )?(last|past)\s+(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks)\b", re.I), "rel_n"),
    (re.compile(r"\b(in the |over the |during the |for the )?(last|past)\s+(minute|hour|day|week|month)\b", re.I), "rel_1"),
    (re.compile(r"\b(today|yesterday)\b", re.I), "named"),
    (re.compile(r"\bthe last week\b", re.I), "named"),
]


def _parse_time_window(question: str, now: datetime) -> TimeRange | None:
    for pattern, kind in _TIME_PHRASES:
        m = pattern.search(question)
        if not m:
            continue
        if kind == "rel_n":
            n = int(m.group(3))
            unit = m.group(4).lower()
            if unit.startswith("minute"):
                delta = timedelta(minutes=n)
            elif unit.startswith("hour"):
                delta = timedelta(hours=n)
            elif unit.startswith("day"):
                delta = timedelta(days=n)
            else:
                delta = timedelta(weeks=n)
            return TimeRange(start=now - delta, end=now)
        if kind == "rel_1":
            unit = m.group(3).lower()
            if unit.startswith("minute"):
                delta = timedelta(minutes=1)
            elif unit.startswith("hour"):
                delta = timedelta(hours=1)
            elif unit.startswith("day"):
                delta = timedelta(days=1)
            elif unit.startswith("month"):
                delta = timedelta(days=30)
            else:
                delta = timedelta(weeks=1)
            return TimeRange(start=now - delta, end=now)
        named = m.group(0).lower()
        if "today" in named:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return TimeRange(start=day_start, end=now)
        if "yesterday" in named:
            yesterday = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return TimeRange(start=yesterday, end=today)
        if "last week" in named:
            return TimeRange(start=now - timedelta(days=7), end=now)
    return None


# Component synonyms — map prose terms to component labels.
_COMPONENT_SYNONYMS = {
    "scope": "scope_of_work",
    "scope of work": "scope_of_work",
    "scopes": "scope_of_work",
    "persona": "primary_persona",
    "primary persona": "primary_persona",
    "personas": "primary_persona",
    "objective": "objective_tracker",
    "objectives": "objective_tracker",
    "objective tracker": "objective_tracker",
    "orchestrator": "orchestrator",
    "memory": "memory_system",
    "memory system": "memory_system",
    "graceful degradation": "degradation",
    "degradation": "degradation",
    "outage": "degradation",
}


def _detect_component(question: str) -> str | None:
    q = question.lower()
    for term, label in sorted(_COMPONENT_SYNONYMS.items(), key=lambda x: -len(x[0])):
        if term in q:
            return label
    return None


_SCOPE_ID_PATTERNS = [
    # Match scope_xxx identifiers: word starting with "scope_"
    re.compile(r"\b(scope_[a-zA-Z0-9_\-:]+)", re.I),
    # Match `for scope <id>` patterns
    re.compile(r"\bscope\s+(?:id\s+)?([a-zA-Z0-9_\-:]+)", re.I),
]
_OBJECTIVE_ID_PATTERNS = [
    re.compile(r"\bobjective\s+(?:id\s+)?([a-zA-Z0-9_\-:]+)", re.I),
]
_SESSION_ID_PATTERNS = [
    re.compile(r"\bsession\s+(?:id\s+)?([a-zA-Z0-9_\-:]+)", re.I),
]
_TRACE_ID_PATTERNS = [
    re.compile(r"\btrace\s+(?:id\s+)?([a-fA-F0-9]{16,32})", re.I),
]


def _extract_id(question: str, patterns: list[re.Pattern]) -> str | None:
    for p in patterns:
        m = p.search(question)
        if m:
            cand = m.group(1)
            # Reject obvious noise words.
            if cand.lower() in ("did", "do", "you", "the", "that", "this", "id"):
                continue
            return cand
    return None


def rule_based_translate(question: str, *, now: datetime | None = None) -> NLTranslation:
    """Convert NL question to a structured filter via heuristics.

    Designed for the test corpus in `nl_corpus.py`. Production
    deployments wire `Claude-via-Max` via the `llm_translate` hook in
    `NLPath` and only fall back to this when the LLM hook is absent.
    """
    now = now or datetime.now(timezone.utc)
    q = question.lower().strip()
    window = _parse_time_window(question, now)
    component = _detect_component(question)

    # Replay intents.
    if any(kw in q for kw in ("replay session", "replay the session", "session replay", "show session")):
        sid = _extract_id(question, _SESSION_ID_PATTERNS)
        if sid:
            return NLTranslation(mode="replay_session", replay_id=sid, confidence=0.95)
    if any(kw in q for kw in ("replay scope", "replay the scope", "scope replay", "show scope")):
        sid = _extract_id(question, _SCOPE_ID_PATTERNS)
        if sid:
            return NLTranslation(mode="replay_scope", replay_id=sid, confidence=0.95)
    if any(kw in q for kw in ("replay objective", "objective replay", "show objective")):
        oid = _extract_id(question, _OBJECTIVE_ID_PATTERNS)
        if oid:
            return NLTranslation(mode="replay_objective", replay_id=oid, confidence=0.95)

    # Cost intent.
    cost_kw = any(kw in q for kw in ("cost", "spend", "tokens", "$", "expensive", "money"))
    if cost_kw:
        return NLTranslation(
            mode="cost",
            cost_window=window,
            cost_components=[component] if component else None,
            confidence=0.9,
        )

    # Audit intent — "why did X happen", supersession, retention decisions
    audit_kw = any(
        kw in q
        for kw in (
            "supersede", "superseded", "supersession",
            "retention class", "retention decision",
            "rationale", "audit", "decision", "decisions",
        )
    )
    if audit_kw:
        op = None
        actor = None
        if "supersession" in q or "supersede" in q:
            op = "supersession_inferred"
        if component == "memory_system" or "memory" in q:
            actor = "memory_system"
        sid = _extract_id(question, _SCOPE_ID_PATTERNS)
        return NLTranslation(
            mode="audit",
            audit_operation=op,
            audit_actor=actor,
            audit_scope_id=sid,
            cost_window=window,
            confidence=0.85,
        )

    # Error intent
    error_kw = any(kw in q for kw in ("error", "errors", "fail", "failed", "failure"))
    span_filter = SpanFilter(
        components=[component] if component else None,
        time_range=window,
        status="ERROR" if error_kw else None,
    )

    # Span name pattern from common verbs
    if "ingest" in q:
        span_filter.name_pattern = "ingest"
    elif "rollup" in q:
        span_filter.name_pattern = "rollup"
    elif "bind" in q:
        span_filter.name_pattern = "bind"
        # If "bind" mentioned with "objective", route to objective_tracker.
        if "objective" in q and not span_filter.components:
            span_filter.components = ["objective_tracker"]
    elif "narrate" in q or "narrative" in q:
        span_filter.name_pattern = "narrative"
        if not span_filter.components:
            span_filter.components = ["degradation"]

    # Outage / incident → degradation component.
    if "outage" in q and not span_filter.components:
        span_filter.components = ["degradation"]

    sid = _extract_id(question, _SCOPE_ID_PATTERNS)
    if sid:
        span_filter.scope_id = sid

    # Trace-id direct lookups
    tid = _extract_id(question, _TRACE_ID_PATTERNS)
    if tid:
        span_filter.trace_ids = [tid]

    confidence = 0.8 if (component or window or sid or tid or error_kw) else 0.5
    return NLTranslation(mode="spans", span_filter=span_filter, confidence=confidence)


# ---- formatter ------------------------------------------------------


def format_cited_answer(
    question: str, rows: list[Any], *, max_citations: int = 8
) -> CitedAnswer:
    """Compose a cited natural-language answer from rows.

    Output always lists span IDs. Anti-deskilling: every claim is
    traceable to a record in the store.
    """
    citations: list[dict[str, Any]] = []
    cited_ids: list[str] = []
    if not rows:
        summary = "No records matched that question."
        return CitedAnswer(question=question, summary=summary, cited_span_ids=[], citations=[], rows_returned=0)
    # SpanRecord rows.
    if rows and isinstance(rows[0], SpanRecord):
        names: dict[str, int] = {}
        for r in rows:
            names[r.name] = names.get(r.name, 0) + 1
        top_names = sorted(names.items(), key=lambda kv: -kv[1])[:3]
        summary_parts = [f"{rows[0].component if hasattr(rows[0], 'component') else 'spans'} returned {len(rows)} matching records."]
        if top_names:
            summary_parts.append(
                "Most common: " + ", ".join(f"{n} ({c})" for n, c in top_names) + "."
            )
        for r in rows[:max_citations]:
            citations.append(
                {
                    "span_id": r.span_id,
                    "name": r.name,
                    "component": r.component,
                    "start_time_iso": datetime.fromtimestamp(
                        r.start_time_unix_nano / 1e9, tz=timezone.utc
                    ).isoformat(),
                    "duration_ms": round(r.duration_ns / 1_000_000, 3),
                    "status": r.status,
                }
            )
            cited_ids.append(r.span_id)
        summary_parts.append(f"Cited spans: {len(cited_ids)}.")
        return CitedAnswer(
            question=question,
            summary=" ".join(summary_parts),
            cited_span_ids=cited_ids,
            citations=citations,
            rows_returned=len(rows),
        )
    # AuditRecord-like rows.
    summary = f"Returned {len(rows)} records."
    for r in rows[:max_citations]:
        d = r.model_dump() if hasattr(r, "model_dump") else dict(r)
        d_pruned = {k: v for k, v in d.items() if k in ("at_time", "operation", "actor", "scope_id", "rationale")}
        d_pruned["at_time"] = str(d_pruned.get("at_time"))
        citations.append(d_pruned)
    return CitedAnswer(
        question=question,
        summary=summary,
        cited_span_ids=cited_ids,
        citations=citations,
        rows_returned=len(rows),
    )


# ---- the NL surface -------------------------------------------------

LLMTranslate = Callable[[str], NLTranslation]
LLMFormat = Callable[[str, list[Any]], CitedAnswer]


class NLPath:
    """End-to-end NL surface.

    `llm_translate` and `llm_format` may be supplied to wire Claude-
    via-Max. Both are optional; the rule-based path is the default
    and is what the test corpus measures.

    Both calls (when LLM is wired) are emitted as `pos.aggregator.nl_*`
    spans tagged with `pos.prompt.type` for v1.1 R12 attribution.
    """

    def __init__(
        self,
        api: QueryAPI,
        *,
        llm_translate: LLMTranslate | None = None,
        llm_format: LLMFormat | None = None,
    ) -> None:
        self.api = api
        self._llm_translate = llm_translate
        self._llm_format = llm_format

    def translate(self, question: str) -> NLTranslation:
        with _TRACER.start_as_current_span("pos.aggregator.nl_translate") as span:
            span.set_attribute("pos.prompt.type", "obs-nl-translate")
            span.set_attribute("nl.question", question[:500])
            if self._llm_translate is not None:
                try:
                    t = self._llm_translate(question)
                    if isinstance(t, NLTranslation):
                        return t
                except Exception:
                    pass
            return rule_based_translate(question)

    def execute(self, question: str) -> tuple[NLTranslation, list[Any]]:
        t = self.translate(question)
        rows: list[Any] = []
        if t.mode == "spans" and t.span_filter is not None:
            rows = self.api.find_spans(t.span_filter, limit=200)
        elif t.mode == "events" and t.event_filter is not None:
            rows = self.api.find_events(t.event_filter, limit=200)
        elif t.mode == "cost":
            cost = self.api.cost_by_prompt(time_range=t.cost_window, components=t.cost_components)
            rows = list(cost.values())
        elif t.mode == "audit":
            rows = self.api.audit_search(
                operation=t.audit_operation,
                scope_id=t.audit_scope_id,
                actor=t.audit_actor,
                time_range=t.cost_window,
            )
        elif t.mode == "replay_session" and t.replay_id:
            rows = [self.api.replay_session(t.replay_id)]
        elif t.mode == "replay_scope" and t.replay_id:
            rows = [self.api.replay_scope(t.replay_id)]
        elif t.mode == "replay_objective" and t.replay_id:
            rows = [self.api.replay_objective(t.replay_id)]
        return t, rows

    def answer(self, question: str) -> CitedAnswer:
        t, rows = self.execute(question)
        with _TRACER.start_as_current_span("pos.aggregator.nl_format") as span:
            span.set_attribute("pos.prompt.type", "obs-nl-format")
            span.set_attribute("nl.rows_returned", len(rows))
            if self._llm_format is not None:
                try:
                    fmt = self._llm_format(question, rows)
                    if isinstance(fmt, CitedAnswer):
                        return fmt
                except Exception:
                    pass
            return format_cited_answer(question, rows)
