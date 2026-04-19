"""NL-path evaluation corpus — 25 representative "show me why" questions.

Each entry has the question and an expected `ground_truth` describing
what the translator should produce. The harness in tests/ measures
both translate-accuracy (does the structured filter match expected
intent) and format-correctness (does the cited answer cite span IDs).

Per the brief: ≥80% translate accuracy required. Per Eve-flagged
inference: 20-30 question corpus is the target size; 25 lands in
the middle.

Ground truth shape:
  {
    "mode": "spans|cost|audit|replay_*",
    "expects": {
      "component": "...",   # if applicable
      "scope_id": "...",    # if applicable
      "objective_id": "...",
      "session_id": "...",
      "trace_id": "...",
      "name_pattern": "...",
      "status": "ERROR" | "OK" | None,
      "has_time_window": True | False,
    }
  }
"""

CORPUS = [
    # 1. Cost intent — generic
    {
        "q": "What was my total LLM cost in the last 7 days?",
        "ground_truth": {"mode": "cost", "expects": {"has_time_window": True}},
    },
    # 2. Cost intent — by component
    {
        "q": "How much did the memory system spend on tokens yesterday?",
        "ground_truth": {"mode": "cost", "expects": {"component": "memory_system", "has_time_window": True}},
    },
    # 3. Cost intent — most expensive
    {
        "q": "Which prompts were most expensive last week?",
        "ground_truth": {"mode": "cost", "expects": {"has_time_window": True}},
    },
    # 4. Audit intent — supersession
    {
        "q": "Why did memory mark Alice's address as superseded?",
        "ground_truth": {"mode": "audit", "expects": {"actor": "memory_system", "operation": "supersession_inferred"}},
    },
    # 5. Audit intent — retention class
    {
        "q": "Show me the audit decisions about retention class today.",
        "ground_truth": {"mode": "audit", "expects": {"has_time_window": True}},
    },
    # 6. Replay session
    {
        "q": "Replay session abc123 for me.",
        "ground_truth": {"mode": "replay_session", "expects": {"session_id": "abc123"}},
    },
    # 7. Replay scope
    {
        "q": "Replay scope scope_42 please.",
        "ground_truth": {"mode": "replay_scope", "expects": {"scope_id": "scope_42"}},
    },
    # 8. Replay objective
    {
        "q": "Show objective obj_99 — what scopes ran under it?",
        "ground_truth": {"mode": "replay_objective", "expects": {"objective_id": "obj_99"}},
    },
    # 9. Spans — error filter
    {
        "q": "Show me all the orchestrator errors today.",
        "ground_truth": {"mode": "spans", "expects": {"component": "orchestrator", "status": "ERROR", "has_time_window": True}},
    },
    # 10. Spans — by component, time window
    {
        "q": "What did graceful degradation do in the last hour?",
        "ground_truth": {"mode": "spans", "expects": {"component": "degradation", "has_time_window": True}},
    },
    # 11. Spans — primary persona
    {
        "q": "Show me primary persona spans from today.",
        "ground_truth": {"mode": "spans", "expects": {"component": "primary_persona", "has_time_window": True}},
    },
    # 12. Spans — by name pattern
    {
        "q": "Find all the ingest spans from yesterday.",
        "ground_truth": {"mode": "spans", "expects": {"name_pattern": "ingest", "has_time_window": True}},
    },
    # 13. Spans — bind events
    {
        "q": "Show me all the bind events for objectives last week.",
        "ground_truth": {"mode": "spans", "expects": {"name_pattern": "bind", "has_time_window": True}},
    },
    # 14. Spans — narrative
    {
        "q": "Show me the narrative spans during the outage.",
        "ground_truth": {"mode": "spans", "expects": {"component": "degradation", "name_pattern": "narrative"}},
    },
    # 15. Spans — failures
    {
        "q": "What memory ingests failed in the last 24 hours?",
        "ground_truth": {"mode": "spans", "expects": {"component": "memory_system", "name_pattern": "ingest", "status": "ERROR", "has_time_window": True}},
    },
    # 16. Audit — generic
    {
        "q": "Audit search for scope_55 — what decisions were made?",
        "ground_truth": {"mode": "audit", "expects": {"scope_id": "scope_55"}},
    },
    # 17. Spans — rollup
    {
        "q": "Show me the rollup spans from the past day.",
        "ground_truth": {"mode": "spans", "expects": {"name_pattern": "rollup", "has_time_window": True}},
    },
    # 18. Cost — explicit money word
    {
        "q": "How much money did we spend on the orchestrator today?",
        "ground_truth": {"mode": "cost", "expects": {"component": "orchestrator", "has_time_window": True}},
    },
    # 19. Cost — tokens explicit
    {
        "q": "Tokens used by the persona in the last 30 minutes?",
        "ground_truth": {"mode": "cost", "expects": {"component": "primary_persona", "has_time_window": True}},
    },
    # 20. Spans — objective tracker errors
    {
        "q": "Any objective tracker errors today?",
        "ground_truth": {"mode": "spans", "expects": {"component": "objective_tracker", "status": "ERROR", "has_time_window": True}},
    },
    # 21. Trace lookup
    {
        "q": "Show me trace abc123def456abc1 in full.",
        "ground_truth": {"mode": "spans", "expects": {"trace_id": "abc123def456abc1"}},
    },
    # 22. Generic question, no specifics
    {
        "q": "What happened recently?",
        "ground_truth": {"mode": "spans", "expects": {}},
    },
    # 23. Replay scope — different phrasing
    {
        "q": "Replay scope my_scope_id for me.",
        "ground_truth": {"mode": "replay_scope", "expects": {"scope_id": "my_scope_id"}},
    },
    # 24. Audit — supersession with time
    {
        "q": "Why was that record superseded yesterday?",
        "ground_truth": {"mode": "audit", "expects": {"operation": "supersession_inferred", "has_time_window": True}},
    },
    # 25. Spans — degradation outage
    {
        "q": "Show me what happened during the outage in the last hour.",
        "ground_truth": {"mode": "spans", "expects": {"component": "degradation", "has_time_window": True}},
    },
]


def matches_ground_truth(translation, ground_truth: dict) -> bool:
    """Return True iff a translation satisfies the ground truth."""
    expected_mode = ground_truth.get("mode")
    if expected_mode and translation.mode != expected_mode:
        return False
    expects = ground_truth.get("expects", {})
    f = translation.span_filter
    if expected_mode == "spans":
        if not f:
            return False
        comp = expects.get("component")
        if comp:
            if not f.components or comp not in f.components:
                return False
        if expects.get("status") and f.status != expects["status"]:
            return False
        np_ = expects.get("name_pattern")
        if np_ and (f.name_pattern is None or np_ not in f.name_pattern):
            return False
        scope_id = expects.get("scope_id")
        if scope_id and f.scope_id != scope_id:
            return False
        tid = expects.get("trace_id")
        if tid and (not f.trace_ids or tid not in f.trace_ids):
            return False
        if expects.get("has_time_window") is True and f.time_range is None:
            return False
        return True
    if expected_mode == "cost":
        comp = expects.get("component")
        if comp:
            if not translation.cost_components or comp not in translation.cost_components:
                return False
        if expects.get("has_time_window") is True and translation.cost_window is None:
            return False
        return True
    if expected_mode == "audit":
        if expects.get("actor") and translation.audit_actor != expects["actor"]:
            return False
        if expects.get("operation") and translation.audit_operation != expects["operation"]:
            return False
        if expects.get("scope_id") and translation.audit_scope_id != expects["scope_id"]:
            return False
        return True
    if expected_mode in ("replay_session", "replay_scope", "replay_objective"):
        wanted = expects.get("session_id") or expects.get("scope_id") or expects.get("objective_id")
        if wanted and translation.replay_id != wanted:
            return False
        return True
    return False


def evaluate_corpus(translator) -> dict:
    """Apply `translator(question)` to each corpus item; return summary stats."""
    correct = 0
    misses = []
    for item in CORPUS:
        t = translator(item["q"])
        if matches_ground_truth(t, item["ground_truth"]):
            correct += 1
        else:
            misses.append({
                "question": item["q"],
                "expected": item["ground_truth"],
                "got_mode": t.mode,
                "got_filter": t.span_filter.model_dump() if t.span_filter else None,
                "got_cost_components": t.cost_components,
                "got_audit_actor": t.audit_actor,
                "got_audit_operation": t.audit_operation,
                "got_replay_id": t.replay_id,
            })
    return {
        "total": len(CORPUS),
        "correct": correct,
        "accuracy": correct / len(CORPUS),
        "misses": misses,
    }
