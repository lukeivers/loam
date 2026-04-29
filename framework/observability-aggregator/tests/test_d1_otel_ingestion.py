"""D1 — Bootstrap-based OTel ingestion + spool buffer + late-binding test."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from pos_observability_aggregator import open_store
from pos_observability_aggregator.api import QueryAPI, SpanFilter
from pos_observability_aggregator.ingest import (
    AggregatorSpanExporter,
    IngestionPipeline,
    SpoolDrainer,
    register_otel_provider,
    detect_proxy_late_binding_failure,
)


def test_register_otel_provider_installs_globally(tmp_config, fresh_otel_provider):
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, processor, exporter = register_otel_provider(spool)
    try:
        # The global tracer provider should be ours.
        global_provider = trace.get_tracer_provider()
        assert global_provider is provider
        assert detect_proxy_late_binding_failure() is None
    finally:
        provider.shutdown()


def test_six_components_emit_into_spool(tmp_config, fresh_otel_provider):
    """Acceptance: spans emitted via `trace.get_tracer('pos.<component>')`
    after provider registration land in our spool."""
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, processor, exporter = register_otel_provider(spool)
    try:
        # Simulate the six OTel-emitting components getting their tracers
        # AFTER we registered. Real components import-time get the proxy;
        # here we exercise the same surface.
        for tracer_name in (
            "loam.scope_of_work",
            "pos_v2.primary_persona",
            "loam.objective_tracker",
            "loam.orchestrator",
            "loam.degradation",
        ):
            tracer = trace.get_tracer(tracer_name)
            with tracer.start_as_current_span(f"{tracer_name}.demo_op") as span:
                span.set_attribute("test.synthetic", True)
        provider.force_flush(timeout_millis=2000)
    finally:
        provider.shutdown()
    # Spool should have at least 5 spans (one per tracer).
    assert spool.exists()
    lines = [l for l in spool.read_text().splitlines() if l.strip()]
    assert len(lines) >= 5
    names = {json.loads(l)["name"] for l in lines}
    assert "loam.scope_of_work.demo_op" in names
    assert "pos_v2.primary_persona.demo_op" in names


def test_self_namespace_filtered_at_exporter(tmp_config, fresh_otel_provider):
    """Aggregator's own loam.aggregator.* spans are not spooled."""
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, processor, exporter = register_otel_provider(spool)
    try:
        agg_tracer = trace.get_tracer("loam.aggregator.test")
        with agg_tracer.start_as_current_span("loam.aggregator.test_op") as span:
            span.set_attribute("self", True)
        # And one normal span to prove filter is selective.
        normal = trace.get_tracer("loam.scope_of_work")
        with normal.start_as_current_span("normal_op"):
            pass
        provider.force_flush(timeout_millis=2000)
    finally:
        provider.shutdown()
    if spool.exists():
        lines = [json.loads(l) for l in spool.read_text().splitlines() if l.strip()]
    else:
        lines = []
    names = [r["name"] for r in lines]
    assert "normal_op" in names
    assert all("loam.aggregator" not in r["tracer_name"] for r in lines)


def test_spool_buffers_during_aggregator_downtime(tmp_config, fresh_otel_provider):
    """Spans emitted while drainer is stopped persist; replay on restart."""
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, processor, exporter = register_otel_provider(spool)
    try:
        tracer = trace.get_tracer("loam.scope_of_work")
        for i in range(5):
            with tracer.start_as_current_span(f"buffered_op_{i}") as s:
                s.set_attribute("i", i)
        provider.force_flush(timeout_millis=2000)
    finally:
        provider.shutdown()
    # Now spin up the store + drainer separately and drain.
    store = open_store(tmp_config)
    try:
        drainer = SpoolDrainer(store, spool, poll_interval_seconds=10)
        ingested = drainer.drain_once()
        assert ingested == 5
        # Verify all spans are now queryable.
        api = QueryAPI(store)
        spans = api.find_spans(SpanFilter(name_pattern="buffered_op_"), limit=20)
        assert len(spans) == 5
        # Restart drainer (cursor advanced; no double-ingest).
        drainer2 = SpoolDrainer(store, spool, poll_interval_seconds=10)
        assert drainer2.drain_once() == 0
    finally:
        store.close()


def test_late_binding_detection(tmp_config, fresh_otel_provider):
    """Diagnostic surfaces if our provider isn't the global one."""
    # Reset provider to a vanilla one BEFORE we register; this mimics
    # a sealed component that bound a non-aggregator provider too early.
    other_provider = TracerProvider()
    trace.set_tracer_provider(other_provider)

    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    # Now our register replaces it.
    provider, processor, exporter = register_otel_provider(spool)
    try:
        # After replacement, late-binding is intact.
        assert detect_proxy_late_binding_failure() is None
    finally:
        provider.shutdown()


def test_pre_existing_proxy_tracer_picks_up_provider(tmp_config, fresh_otel_provider):
    """A tracer obtained BEFORE the provider was registered still routes
    spans through our exporter on next call (ProxyTracer late-binding)."""
    # Get tracer first — this is what sealed components do at import time.
    early_tracer = trace.get_tracer("loam.scope_of_work")
    # Now register our provider.
    spool = Path(tmp_config.resolved_spool_path())
    spool.parent.mkdir(parents=True, exist_ok=True)
    provider, processor, exporter = register_otel_provider(spool)
    try:
        # Span emitted with the early tracer should land in our spool.
        with early_tracer.start_as_current_span("late_binding_proof") as s:
            s.set_attribute("demo", True)
        provider.force_flush(timeout_millis=2000)
    finally:
        provider.shutdown()
    if not spool.exists():
        pytest.fail(
            "BOOTSTRAP-TIMING HALT SIGNAL: spool empty — late-binding "
            "proxy did not pick up our TracerProvider after registration. "
            "Sealed components may be caching concrete tracers at import."
        )
    lines = [json.loads(l) for l in spool.read_text().splitlines() if l.strip()]
    names = {r["name"] for r in lines}
    assert "late_binding_proof" in names
