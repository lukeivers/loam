"""D6 — Replay (Reading A) — read-only playback round-trip."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from pos_observability_aggregator.api import QueryAPI
from pos_observability_aggregator.schema import (
    AuditRecord,
    EventRecord,
    SpanRecord,
)


def _span(span_id, name, *, attrs, tracer="pos.scope_of_work", comp="scope_of_work", offset_ns=0):
    now_ns = int(time.time() * 1e9) + offset_ns
    return SpanRecord(
        trace_id="t" * 32, span_id=span_id, name=name,
        tracer_name=tracer, component=comp,
        start_time_unix_nano=now_ns, end_time_unix_nano=now_ns + 1_000_000,
        attributes=attrs,
    )


def test_replay_session_returns_ordered_spans_and_events(store):
    # Two spans tied by pos.session.id == "sess_1".
    store.insert_span(_span("a" * 16, "first", attrs={"pos.session.id": "sess_1"}, offset_ns=0))
    store.insert_span(_span("b" * 16, "second", attrs={"pos.session.id": "sess_1"}, offset_ns=10_000_000))
    # An event on the first span.
    store.insert_event(EventRecord(
        span_id="a" * 16, trace_id="t" * 32, name="state_changed",
        time_unix_nano=int(time.time() * 1e9), attributes={"to": "active"},
    ))
    api = QueryAPI(store)
    rep = api.replay_session("sess_1")
    assert rep.session_id == "sess_1"
    assert len(rep.spans) == 2
    assert rep.spans[0].name == "first"
    assert rep.spans[1].name == "second"
    assert len(rep.events) >= 1


def test_replay_scope_returns_decision_chain(store):
    # Three spans bound to pos.scope.id == "scope_42".
    for i, n in enumerate(["invoke_scope", "child_op", "another_child"]):
        store.insert_span(_span(f"{i:016x}", n, attrs={"pos.scope.id": "scope_42"}, offset_ns=i * 1_000_000))
    # State transition events.
    store.insert_event(EventRecord(
        span_id="0" * 16, trace_id="t" * 32, name="pos.scope.state_changed",
        time_unix_nano=int(time.time() * 1e9), attributes={"to": "active"},
    ))
    # Audit entry tied to scope.
    store.insert_audit(AuditRecord(
        at_time=datetime.now(timezone.utc), operation="bind_refused",
        actor="orchestrator", scope_id="scope_42", rationale="why",
    ))
    api = QueryAPI(store)
    rep = api.replay_scope("scope_42")
    assert rep.scope_id == "scope_42"
    assert rep.root_span is not None
    assert rep.root_span.name == "invoke_scope"
    assert len(rep.spans) == 3
    assert len(rep.state_transitions) == 1
    assert len(rep.audit_entries) == 1


def test_replay_objective_returns_bound_scopes(store):
    # bind_scope spans linking objective_id -> scope_ids
    store.insert_span(_span("a" * 16, "bind_scope", attrs={
        "pos.objective.id": "obj_99", "pos.scope.id": "scope_a",
    }, tracer="pos.objective_tracker", comp="objective_tracker"))
    store.insert_span(_span("b" * 16, "bind_scope", attrs={
        "pos.objective.id": "obj_99", "pos.scope.id": "scope_b",
    }, tracer="pos.objective_tracker", comp="objective_tracker"))
    # Activity inside each scope.
    store.insert_span(_span("c" * 16, "scope_work", attrs={"pos.scope.id": "scope_a"}))
    store.insert_span(_span("d" * 16, "scope_work", attrs={"pos.scope.id": "scope_b"}))
    api = QueryAPI(store)
    rep = api.replay_objective("obj_99")
    assert rep.objective_id == "obj_99"
    assert len(rep.scope_replays) == 2
    scope_ids = {sr.scope_id for sr in rep.scope_replays}
    assert scope_ids == {"scope_a", "scope_b"}


def test_replay_round_trip_preserves_input_ordering(store):
    """Round-trip: input ordering preserved in replay output."""
    # Insert in scrambled order; replay must return ordered.
    spans = [
        _span("3" * 16, "third", attrs={"pos.session.id": "sx"}, offset_ns=2_000_000),
        _span("1" * 16, "first", attrs={"pos.session.id": "sx"}, offset_ns=0),
        _span("2" * 16, "second", attrs={"pos.session.id": "sx"}, offset_ns=1_000_000),
    ]
    for s in spans:
        store.insert_span(s)
    api = QueryAPI(store)
    rep = api.replay_session("sx")
    assert [s.name for s in rep.spans] == ["first", "second", "third"]
