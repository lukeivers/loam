"""D7 — observability emission tests.

Covers:
- Every memory operation emits a structured OTel span.
- Token rows are written with prompt_name, model, counts.
- Audit log is append-only, JSONL, reconstructible.
- Per-prompt cost is queryable without a consumer present.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import observability


@pytest.fixture
def emitter(tmp_path) -> observability.Emitter:
    return observability.Emitter(sink_dir=tmp_path)


def test_span_round_trip(emitter: observability.Emitter) -> None:
    with emitter.span(
        "memory.ingest",
        attributes={"name": "test-ep", "scope_id": "s1"},
    ) as span:
        span.set_attr("episode_uuid", "abc-123")
        span.set_payload(inputs={"body": "hello"}, outputs={"nodes": 2})

    spans = emitter.read_spans()
    assert len(spans) == 1
    rec = spans[0]
    assert rec["name"] == "memory.ingest"
    assert rec["status"] == "OK"
    assert rec["attributes"]["episode_uuid"] == "abc-123"
    assert rec["attributes"]["scope_id"] == "s1"
    assert "inputs" in rec["attributes"]
    assert rec["start_time_unix_nano"] <= rec["end_time_unix_nano"]


def test_span_on_error_records_exception(emitter: observability.Emitter) -> None:
    with pytest.raises(ValueError):
        with emitter.span("memory.search", attributes={"query": "q"}):
            raise ValueError("boom")
    spans = emitter.read_spans()
    assert spans[0]["status"] == "ERROR"
    assert "ValueError" in spans[0]["error"]


def test_token_row_then_cost_attribution(emitter: observability.Emitter) -> None:
    observability.record_llm_usage(
        prompt_name="extract_nodes.extract_text",
        model="claude-haiku-4-5",
        input_tokens=1000,
        output_tokens=200,
        call_count=1,
        scope_id="s1",
        emitter=emitter,
    )
    observability.record_llm_usage(
        prompt_name="dedupe_edges.resolve_edge",
        model="claude-haiku-4-5",
        input_tokens=5000,
        output_tokens=400,
        call_count=5,
        scope_id="s1",
        emitter=emitter,
    )

    rows = emitter.read_tokens()
    assert len(rows) == 2

    cost = emitter.per_prompt_cost(input_usd_per_mtok=1.0, output_usd_per_mtok=5.0)
    assert "extract_nodes.extract_text" in cost
    assert "dedupe_edges.resolve_edge" in cost
    # (1000/1M * 1.0) + (200/1M * 5.0) = 0.001 + 0.001 = 0.002
    assert cost["extract_nodes.extract_text"]["estimated_usd"] == pytest.approx(0.002)


def test_audit_entry_durable(emitter: observability.Emitter) -> None:
    observability.record_audit(
        operation="memory.ingest.discarded",
        actor="memory-system",
        scope_id="s1",
        rationale="ephemeral class matched",
        extras={"rule": "cpu-readings"},
        emitter=emitter,
    )
    audit = emitter.read_audit()
    assert len(audit) == 1
    assert audit[0]["operation"] == "memory.ingest.discarded"
    assert audit[0]["extras"]["rule"] == "cpu-readings"


def test_sampled_operation_reconstructible(emitter: observability.Emitter) -> None:
    """v1.1 R11 A1 correction: a sampled operation must be
    reconstructible from its emissions alone — no consumer required.
    """
    with emitter.span(
        "memory.ingest",
        attributes={"name": "test-ep", "scope_id": "s1", "body_chars": 42},
    ) as span:
        span.set_attr("episode_uuid", "ep-001")
        observability.record_llm_usage(
            prompt_name="extract_nodes.extract_text",
            model="claude-haiku-4-5",
            input_tokens=500,
            output_tokens=100,
            trace_id=span.trace_id,
            span_id=span.span_id,
            emitter=emitter,
        )
        observability.record_audit(
            operation="memory.ingest.ok",
            actor="memory-system",
            scope_id="s1",
            subject_uuid="ep-001",
            rationale="normal ingest",
            emitter=emitter,
        )

    spans = emitter.read_spans()
    tokens = emitter.read_tokens()
    audit = emitter.read_audit()
    assert len(spans) == 1
    assert len(tokens) == 1
    assert len(audit) == 1

    # Reconstruction: pick one span, pull its trace_id, find the
    # token rows and audit entries referencing the same episode_uuid.
    target_span = spans[0]
    ep_uuid = target_span["attributes"]["episode_uuid"]
    # Token rows carry trace_id; audit entries reference subject_uuid.
    tok_for_trace = [t for t in tokens if t["trace_id"] == target_span["trace_id"]]
    aud_for_subject = [a for a in audit if a["subject_uuid"] == ep_uuid]
    assert tok_for_trace and aud_for_subject
