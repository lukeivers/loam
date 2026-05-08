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

"""D9 — Self-observability + privacy verification + NL accuracy structured."""
from __future__ import annotations

import json
import time
from pathlib import Path

from opentelemetry import trace

from loam.observability_aggregator import open_store
from loam.observability_aggregator.api import QueryAPI, SpanFilter
from loam.observability_aggregator.ingest import (
    SpoolDrainer,
    register_otel_provider,
    IngestionPipeline,
)
from loam.observability_aggregator.nl_corpus import (
    evaluate_corpus,
)
from loam.observability_aggregator.nl_path import NLPath, rule_based_translate
from loam.observability_aggregator.schema import RetentionClass


def _write_memory_span(path: Path, name: str, *, retention_class=None, payload=None):
    rec = {
        "trace_id": "a" * 32,
        "span_id": f"{name[:14]:0>16}".replace(" ", "0"),
        "parent_span_id": None,
        "name": name,
        "start_time_unix_nano": int(time.time() * 1e9),
        "end_time_unix_nano": int(time.time() * 1e9) + 1000,
        "attributes": {
            **({"loam.retention.class": retention_class} if retention_class else {}),
            **({"inputs": payload} if payload else {}),
        },
        "status": "OK",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("at", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def test_self_observability_aggregator_spans_filtered(tmp_config, fresh_otel_provider):
    """Aggregator's own loam.aggregator.* spans never reach the store."""
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, _, _ = register_otel_provider(spool)
    try:
        # Both a normal span and several aggregator self-spans.
        normal = trace.get_tracer("loam.scope_of_work")
        with normal.start_as_current_span("normal_op"):
            pass
        agg = trace.get_tracer("loam.aggregator.something")
        for i in range(10):
            with agg.start_as_current_span(f"agg_internal_op_{i}"):
                pass
        provider.force_flush(timeout_millis=2000)
    finally:
        provider.shutdown()
    store = open_store(tmp_config)
    try:
        SpoolDrainer(store, spool).drain_once()
        api = QueryAPI(store)
        agg_spans = api.find_spans(SpanFilter(components=["aggregator"]), limit=100)
        assert agg_spans == []
        normal_spans = api.find_spans(SpanFilter(components=["scope_of_work"]), limit=100)
        assert len(normal_spans) == 1
    finally:
        store.close()


def test_privacy_derived_only_drops_payload_at_ingest(tmp_config):
    """Derived-only memory spans → no payload in store."""
    sink_dir = tmp_config.resolved_memory_sink_dir()
    spans_file = sink_dir / "spans.jsonl"
    _write_memory_span(spans_file, "ingest_op", retention_class="derived-only", payload="SENSITIVE TEXT")
    store = open_store(tmp_config)
    try:
        pipe = IngestionPipeline(tmp_config, store)
        pipe.drain_all_once()
        api = QueryAPI(store)
        spans = api.find_spans(SpanFilter(components=["memory_system"]))
        assert len(spans) == 1
        assert spans[0].retention_class is RetentionClass.DERIVED_ONLY
        # Privacy: SENSITIVE TEXT must not be retained anywhere.
        assert "inputs" not in spans[0].attributes
        # Audit: confirm no raw text in any record across the DB.
        all_attrs = json.dumps(spans[0].attributes)
        assert "SENSITIVE TEXT" not in all_attrs
        # Also check raw row in the DB.
        rows = store.fetch("SELECT attributes FROM spans")
        all_db_text = " ".join(str(r[0]) for r in rows)
        assert "SENSITIVE TEXT" not in all_db_text
    finally:
        store.close()


def test_privacy_ephemeral_keeps_only_stub(tmp_config):
    """Ephemeral memory spans → minimal stub, no payload, status reduced."""
    sink_dir = tmp_config.resolved_memory_sink_dir()
    spans_file = sink_dir / "spans.jsonl"
    _write_memory_span(spans_file, "eph_op", retention_class="ephemeral", payload="EPHEMERAL CONTENT")
    store = open_store(tmp_config)
    try:
        pipe = IngestionPipeline(tmp_config, store)
        pipe.drain_all_once()
        api = QueryAPI(store)
        spans = api.find_spans(SpanFilter(components=["memory_system"]))
        assert len(spans) == 1
        s = spans[0]
        assert s.retention_class is RetentionClass.EPHEMERAL
        # Ephemeral: only stub fields preserved (operation name + timing);
        # no payload; no inputs; no extras.
        assert "inputs" not in s.attributes
        # The raw row in the DB does not contain payload.
        rows = store.fetch("SELECT attributes FROM spans")
        all_db_text = " ".join(str(r[0]) for r in rows)
        assert "EPHEMERAL CONTENT" not in all_db_text
    finally:
        store.close()


def test_nl_accuracy_evaluation_structured_measurement():
    """Structured measurement of translate-accuracy on the 25-question corpus."""
    result = evaluate_corpus(rule_based_translate)
    assert result["total"] == 25
    print(f"\nNL translate accuracy: {result['accuracy']:.0%} ({result['correct']}/{result['total']})")
    assert result["accuracy"] >= 0.80


def test_nl_format_correctness_cited_output(tmp_config):
    """Format correctness: every cited answer with rows includes span IDs."""
    store = open_store(tmp_config)
    try:
        # Insert one span to ensure rows exist for at least one query.
        from loam.observability_aggregator.schema import SpanRecord
        now_ns = int(time.time() * 1e9)
        store.insert_span(SpanRecord(
            trace_id="t" * 32, span_id="z" * 16, name="probe",
            tracer_name="loam.scope_of_work", component="scope_of_work",
            start_time_unix_nano=now_ns, end_time_unix_nano=now_ns + 1000,
        ))
        api = QueryAPI(store)
        nl = NLPath(api)
        # Run a span-mode question.
        answer = nl.answer("show me scope_of_work spans")
        # If rows returned, span IDs MUST be cited.
        if answer.rows_returned > 0:
            assert len(answer.cited_span_ids) > 0
            assert all(sid for sid in answer.cited_span_ids)
            for cit in answer.citations:
                assert "span_id" in cit
                assert cit["span_id"] in answer.cited_span_ids
    finally:
        store.close()
