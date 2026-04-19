"""D4 — Structured Pydantic query API."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from pos_observability_aggregator import open_store
from pos_observability_aggregator.api import (
    EventFilter,
    QueryAPI,
    SpanFilter,
    TimeRange,
)
from pos_observability_aggregator.schema import (
    AuditRecord,
    EventRecord,
    SpanRecord,
    TokenRecord,
)


def _span(span_id: str, name: str, *, scope_id=None, status="OK", attrs=None, comp="scope_of_work", tracer="pos.scope_of_work"):
    now_ns = int(time.time() * 1e9)
    a = dict(attrs or {})
    if scope_id:
        a["pos.scope.id"] = scope_id
    return SpanRecord(
        trace_id="t" * 32,
        span_id=span_id,
        name=name,
        tracer_name=tracer,
        component=comp,
        start_time_unix_nano=now_ns,
        end_time_unix_nano=now_ns + 5_000_000,
        status=status,
        attributes=a,
    )


def test_find_spans_by_component(store):
    store.insert_span(_span("a" * 16, "op_a"))
    store.insert_span(_span("b" * 16, "op_b", comp="orchestrator", tracer="pos.orchestrator"))
    api = QueryAPI(store)
    res = api.find_spans(SpanFilter(components=["scope_of_work"]))
    assert {s.span_id for s in res} == {"a" * 16}
    res = api.find_spans(SpanFilter(components=["orchestrator"]))
    assert {s.span_id for s in res} == {"b" * 16}


def test_find_spans_by_status(store):
    store.insert_span(_span("a" * 16, "ok_op", status="OK"))
    store.insert_span(_span("b" * 16, "err_op", status="ERROR"))
    api = QueryAPI(store)
    errs = api.find_spans(SpanFilter(status="ERROR"))
    assert {s.name for s in errs} == {"err_op"}


def test_find_spans_by_scope_id_via_attr(store):
    store.insert_span(_span("a" * 16, "in_scope", scope_id="scope_1"))
    store.insert_span(_span("b" * 16, "out_of_scope", scope_id="scope_2"))
    api = QueryAPI(store)
    res = api.find_spans(SpanFilter(scope_id="scope_1"))
    assert {s.name for s in res} == {"in_scope"}


def test_find_spans_by_time_range(store):
    now = int(time.time() * 1e9)
    s_old = SpanRecord(
        trace_id="t" * 32, span_id="a" * 16, name="old", tracer_name="pos.scope_of_work",
        component="scope_of_work",
        start_time_unix_nano=now - 86_400_000_000_000,
        end_time_unix_nano=now - 86_400_000_000_000 + 1000,
    )
    s_new = SpanRecord(
        trace_id="t" * 32, span_id="b" * 16, name="new", tracer_name="pos.scope_of_work",
        component="scope_of_work",
        start_time_unix_nano=now, end_time_unix_nano=now + 1000,
    )
    store.insert_span(s_old)
    store.insert_span(s_new)
    api = QueryAPI(store)
    res = api.find_spans(
        SpanFilter(time_range=TimeRange(start=datetime.now(timezone.utc) - timedelta(hours=1)))
    )
    assert {s.name for s in res} == {"new"}


def test_get_span_and_get_trace(store):
    store.insert_span(_span("a" * 16, "op_a"))
    store.insert_span(_span("b" * 16, "op_b"))
    api = QueryAPI(store)
    one = api.get_span("a" * 16)
    assert one is not None and one.name == "op_a"
    none = api.get_span("z" * 16)
    assert none is None
    trace = api.get_trace("t" * 32)
    assert len(trace) == 2


def test_cost_by_prompt_aggregates_across_components(store):
    # Add tokens from memory + orchestrator-namespaced prompts.
    now = datetime.now(timezone.utc)
    store.insert_token(TokenRecord(
        prompt_name="extract_facts", model="claude-haiku",
        input_tokens=100, output_tokens=50, call_count=1,
        at_time=now, component="memory_system",
    ))
    store.insert_token(TokenRecord(
        prompt_name="extract_facts", model="claude-haiku",
        input_tokens=200, output_tokens=80, call_count=2,
        at_time=now, component="memory_system",
    ))
    store.insert_token(TokenRecord(
        prompt_name="narrative", model="claude-sonnet",
        input_tokens=500, output_tokens=300, call_count=1,
        at_time=now, component="degradation",
    ))
    api = QueryAPI(store)
    cost = api.cost_by_prompt()
    assert "extract_facts" in cost
    assert cost["extract_facts"].input_tokens == 300
    assert cost["extract_facts"].output_tokens == 130
    assert cost["extract_facts"].call_count == 3
    assert cost["narrative"].input_tokens == 500


def test_cost_by_prompt_with_pricing(store):
    store.insert_token(TokenRecord(
        prompt_name="big_prompt", model="claude-opus",
        input_tokens=1_000_000, output_tokens=500_000, call_count=1,
        at_time=datetime.now(timezone.utc),
    ))
    api = QueryAPI(store)
    cost = api.cost_by_prompt(pricing={"claude-opus": (15.0, 75.0)})
    # 1M @ $15 + 0.5M @ $75 = $15 + $37.5 = $52.5
    assert abs(cost["big_prompt"].estimated_usd - 52.5) < 0.01


def test_audit_search_by_operation(store):
    now = datetime.now(timezone.utc)
    store.insert_audit(AuditRecord(
        at_time=now, operation="supersession_inferred",
        actor="memory_system", scope_id="scope_1", rationale="r1",
    ))
    store.insert_audit(AuditRecord(
        at_time=now, operation="retention_class_decided",
        actor="memory_system", scope_id="scope_1", rationale="r2",
    ))
    api = QueryAPI(store)
    res = api.audit_search(operation="supersession_inferred")
    assert len(res) == 1
    res = api.audit_search(scope_id="scope_1")
    assert len(res) == 2
