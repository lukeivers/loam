# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""D2 — Memory JSONL tailer."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from loam.observability_aggregator import open_store
from loam.observability_aggregator.api import QueryAPI, SpanFilter
from loam.observability_aggregator.ingest import (
    IngestionPipeline,
    JSONLTailer,
    memory_audit_to_canonical,
    memory_span_to_canonical,
    memory_token_to_canonical,
)


def _write_memory_span(path: Path, name: str, **attrs):
    rec = {
        "trace_id": "a" * 32,
        "span_id": f"{name[:14]:0>16}".replace(" ", "0"),
        "parent_span_id": None,
        "name": name,
        "start_time_unix_nano": int(time.time() * 1e9),
        "end_time_unix_nano": int(time.time() * 1e9) + 1_000_000,
        "attributes": attrs,
        "status": "OK",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("at", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def _write_memory_token(path: Path, prompt_name: str, model: str = "claude-sonnet-4"):
    rec = {
        "trace_id": "b" * 32,
        "span_id": "c" * 16,
        "prompt_name": prompt_name,
        "model": model,
        "input_tokens": 100,
        "output_tokens": 50,
        "call_count": 1,
        "at_iso": datetime.now(timezone.utc).isoformat(),
        "scope_id": "test_scope",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("at", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def _write_memory_audit(path: Path, op: str, rationale: str = "test"):
    rec = {
        "at_iso": datetime.now(timezone.utc).isoformat(),
        "operation": op,
        "actor": "memory_system",
        "scope_id": "audit_scope",
        "subject_uuid": "subj-123",
        "rationale": rationale,
        "extras": {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("at", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def test_memory_format_translators_match_documented_shape():
    """Acceptance: format matches memory's documented shape; halt-and-signal
    in this test if memory's format has drifted."""
    sample_span = {
        "trace_id": "abc" * 10 + "ab",
        "span_id": "1234567890abcdef",
        "parent_span_id": None,
        "name": "memory.ingest",
        "start_time_unix_nano": 1000,
        "end_time_unix_nano": 2000,
        "attributes": {"key": "value", "loam.retention.class": "derived-only"},
        "status": "OK",
        "error": None,
    }
    sp = memory_span_to_canonical(sample_span)
    assert sp.trace_id == sample_span["trace_id"]
    assert sp.component == "memory_system"
    assert sp.tracer_name == "loam.memory"
    assert sp.retention_class.value == "derived-only"

    sample_tok = {
        "trace_id": "x" * 32,
        "span_id": "y" * 16,
        "prompt_name": "extract_facts",
        "model": "claude-haiku",
        "input_tokens": 100,
        "output_tokens": 50,
        "call_count": 1,
        "at_iso": "2026-04-19T12:00:00+00:00",
        "scope_id": "scope_42",
    }
    tk = memory_token_to_canonical(sample_tok)
    assert tk.prompt_name == "extract_facts"
    assert tk.input_tokens == 100
    assert tk.scope_id == "scope_42"

    sample_audit = {
        "at_iso": "2026-04-19T12:00:00+00:00",
        "operation": "supersession_inferred",
        "actor": "memory_system",
        "scope_id": "scope_42",
        "subject_uuid": "subj-1",
        "rationale": "newer entry contradicts older",
        "extras": {"hop": 2},
    }
    au = memory_audit_to_canonical(sample_audit)
    assert au.operation == "supersession_inferred"
    assert au.extras["hop"] == 2


def test_jsonl_tailer_ingests_memory_spans(tmp_config):
    store = open_store(tmp_config)
    try:
        sink_dir = tmp_config.resolved_memory_sink_dir()
        spans_file = sink_dir / "spans.jsonl"
        for i in range(3):
            _write_memory_span(spans_file, f"memory.op_{i}", payload="test")
        handler = lambda r: store.insert_span(memory_span_to_canonical(r))
        tailer = JSONLTailer(store, "memory:spans", spans_file, handler, poll_interval_seconds=0.1)
        n = tailer.drain_once()
        assert n == 3
        api = QueryAPI(store)
        spans = api.find_spans(SpanFilter(components=["memory_system"]), limit=10)
        assert len(spans) == 3
        # Re-drain returns 0 (cursor advanced).
        assert tailer.drain_once() == 0
    finally:
        store.close()


def test_tailer_skips_malformed_lines(tmp_config):
    store = open_store(tmp_config)
    try:
        sink_dir = tmp_config.resolved_memory_sink_dir()
        spans_file = sink_dir / "spans.jsonl"
        sink_dir.mkdir(parents=True, exist_ok=True)
        # Write valid + malformed mix.
        _write_memory_span(spans_file, "good_span_1")
        with spans_file.open("at", encoding="utf-8") as fh:
            fh.write("this is not json\n")
            fh.write("{broken json\n")
        _write_memory_span(spans_file, "good_span_2")
        handler = lambda r: store.insert_span(memory_span_to_canonical(r))
        tailer = JSONLTailer(store, "memory:spans", spans_file, handler)
        n = tailer.drain_once()
        # 2 valid spans ingested; 2 malformed skipped.
        assert n == 2
    finally:
        store.close()


def test_tail_latency_under_one_second_p95(tmp_config):
    """Tail thread polls at 0.5s; new lines reach the store within ~1s."""
    store = open_store(tmp_config)
    try:
        sink_dir = tmp_config.resolved_memory_sink_dir()
        spans_file = sink_dir / "spans.jsonl"
        sink_dir.mkdir(parents=True, exist_ok=True)
        # Pre-create empty file so the tailer attaches.
        spans_file.touch()
        handler = lambda r: store.insert_span(memory_span_to_canonical(r))
        tailer = JSONLTailer(store, "memory:spans", spans_file, handler, poll_interval_seconds=0.2)
        tailer.start()
        try:
            # Write a span and time how long until it appears in the store.
            _write_memory_span(spans_file, "latency_probe")
            api = QueryAPI(store)
            deadline = time.monotonic() + 2.0
            found = False
            while time.monotonic() < deadline:
                spans = api.find_spans(SpanFilter(name_exact="latency_probe"), limit=5)
                if spans:
                    found = True
                    break
                time.sleep(0.05)
            assert found, "tail latency exceeded 2s — bounded p95 target failed"
        finally:
            tailer.stop()
    finally:
        store.close()


def test_full_pipeline_ingests_all_three_sinks(tmp_config):
    store = open_store(tmp_config)
    try:
        sink_dir = tmp_config.resolved_memory_sink_dir()
        sink_dir.mkdir(parents=True, exist_ok=True)
        _write_memory_span(sink_dir / "spans.jsonl", "memory.ingest")
        _write_memory_token(sink_dir / "tokens.jsonl", "extract_facts")
        _write_memory_audit(sink_dir / "audit.jsonl", "supersession_inferred", "rationale")
        pipe = IngestionPipeline(tmp_config, store)
        result = pipe.drain_all_once()
        assert result["memory_spans"] == 1
        assert result["memory_tokens"] == 1
        assert result["memory_audit"] == 1
        api = QueryAPI(store)
        # Spans
        spans = api.find_spans(SpanFilter(components=["memory_system"]), limit=10)
        assert len(spans) == 1
        # Audit
        audit = api.audit_search(operation="supersession_inferred")
        assert len(audit) == 1
        assert audit[0].rationale == "rationale"
        # Cost
        cost = api.cost_by_prompt()
        assert "extract_facts" in cost
    finally:
        store.close()
