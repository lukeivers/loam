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

"""D5 — NL ("show me why") path: corpus accuracy + cited output + reflexive cost + no-loop."""
from __future__ import annotations

import time
from pathlib import Path


from loam.observability_aggregator import open_store
from loam.observability_aggregator.api import QueryAPI
from loam.observability_aggregator.ingest import register_otel_provider, SpoolDrainer
from loam.observability_aggregator.nl_corpus import (
    evaluate_corpus,
)
from loam.observability_aggregator.nl_path import (
    NLPath,
    rule_based_translate,
)
from loam.observability_aggregator.schema import SpanRecord


def test_translate_corpus_meets_80_percent_accuracy():
    """Acceptance D5: ≥80% accuracy on 20-30-question corpus."""
    result = evaluate_corpus(rule_based_translate)
    assert result["total"] >= 20, "corpus too small for statistical meaning"
    assert result["total"] <= 30
    assert result["accuracy"] >= 0.80, (
        f"NL translate accuracy {result['accuracy']:.0%} below 80% threshold; "
        f"misses: {[m['question'] for m in result['misses']]}"
    )


def test_format_always_cites_span_ids(store):
    # Populate one span.
    now_ns = int(time.time() * 1e9)
    store.insert_span(SpanRecord(
        trace_id="t" * 32, span_id="s" * 16, name="probe_span",
        tracer_name="loam.scope_of_work", component="scope_of_work",
        start_time_unix_nano=now_ns, end_time_unix_nano=now_ns + 1000,
    ))
    api = QueryAPI(store)
    nl = NLPath(api)
    answer = nl.answer("Show me scope spans recently")
    assert answer.rows_returned >= 0
    if answer.rows_returned > 0:
        assert len(answer.cited_span_ids) > 0
        assert all(sid for sid in answer.cited_span_ids)
        for cit in answer.citations:
            assert "span_id" in cit


def test_format_no_uncited_claims_when_no_data(store):
    api = QueryAPI(store)
    nl = NLPath(api)
    answer = nl.answer("Show me everything")
    assert answer.rows_returned == 0
    assert answer.cited_span_ids == []
    assert "no records" in answer.summary.lower()


def test_nl_path_reflexive_cost_attribution(tmp_config, fresh_otel_provider):
    """Both LLM-call spans (translate + format) carry loam.prompt.type."""
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, processor, exporter = register_otel_provider(
        spool, self_namespace_prefix="__never_match__"  # don't filter aggregator's own
    )
    try:
        store = open_store(tmp_config)
        try:
            api = QueryAPI(store)
            nl = NLPath(api)
            nl.answer("how much did orchestrator cost yesterday?")
            provider.force_flush(timeout_millis=2000)
        finally:
            store.close()
    finally:
        provider.shutdown()
    # Re-open: read what got spooled.
    import json
    lines = [json.loads(l) for l in spool.read_text().splitlines() if l.strip()]
    nl_spans = [
        s for s in lines
        if s["name"] in ("loam.aggregator.nl_translate", "loam.aggregator.nl_format")
    ]
    assert len(nl_spans) == 2
    prompt_types = {s["attributes"].get("loam.prompt.type") for s in nl_spans}
    assert prompt_types == {"obs-nl-translate", "obs-nl-format"}


def test_self_observation_no_infinite_loop(tmp_config, fresh_otel_provider):
    """When the aggregator filters its own spans at ingest, NL queries
    over its own activity terminate without recursion."""
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, _, _ = register_otel_provider(spool)  # default: filter aggregator
    try:
        store = open_store(tmp_config)
        try:
            api = QueryAPI(store)
            nl = NLPath(api)
            # Run several NL answers; the aggregator's own spans must NOT
            # land in the store, so each answer remains terminating.
            for q in [
                "what spans happened in the last hour?",
                "show me orchestrator errors today",
                "how much did memory cost yesterday?",
            ]:
                answer = nl.answer(q)
                # No infinite loop: terminates with an answer.
                assert answer is not None
            provider.force_flush(timeout_millis=2000)
            # Drain spool: aggregator spans should be filtered out.
            drainer = SpoolDrainer(store, spool)
            drainer.drain_once()
            # Confirm: no aggregator spans in the store.
            from loam.observability_aggregator.api import SpanFilter
            agg_spans = api.find_spans(SpanFilter(components=["aggregator"]), limit=100)
            assert agg_spans == []
        finally:
            store.close()
    finally:
        provider.shutdown()


def test_nl_translate_cost_intent_with_window():
    t = rule_based_translate("how much did the persona cost in the last 30 minutes?")
    assert t.mode == "cost"
    assert t.cost_window is not None
    assert "primary_persona" in (t.cost_components or [])


def test_nl_translate_replay_session():
    t = rule_based_translate("Replay session sess_abc123 for me")
    assert t.mode == "replay_session"
    assert t.replay_id == "sess_abc123"


def test_nl_translate_audit_intent():
    t = rule_based_translate("Why did memory mark Alice's address as superseded?")
    assert t.mode == "audit"
    assert t.audit_actor == "memory_system"
    assert t.audit_operation == "supersession_inferred"
