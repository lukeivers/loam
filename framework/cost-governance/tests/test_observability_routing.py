"""C24: OTel spans flow through `trace.get_tracer("loam.cost_governance")`.
The component does not construct its own TracerProvider.
"""

from __future__ import annotations

import ast
import pathlib

import loam.cost_governance as cg
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry import trace

from loam.cost_governance import CostLedger, CostStore, observability as obs

from .conftest import build_config, make_spec


def test_C24_spans_emitted_via_shared_tracer(tmp_path) -> None:
    """Install an aggregator-style provider and confirm our emissions
    land on it via the shared trace.get_tracer handle.
    """
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    store = CostStore(tmp_path / "cost.sqlite")
    try:
        ledger = CostLedger(store=store, config=build_config(session_money=10_000))
        spec = make_spec(money_cents=50)
        ledger.reserve_or_refuse(spec, scope_id="s1")
        provider.force_flush()
        spans = exporter.get_finished_spans()
        names = [s.name for s in spans]
        assert "loam.cost.reservation_created" in names
    finally:
        store.close()


def test_C24_no_tracer_provider_constructed_in_cost_governance() -> None:
    """Static check: no file inside cost_governance.* constructs a
    TracerProvider. (A1 correction held.)
    """
    pkg_dir = pathlib.Path(cg.__file__).parent
    offenders: list[str] = []
    for src in pkg_dir.rglob("*.py"):
        text = src.read_text()
        if "TracerProvider(" in text:
            offenders.append(str(src))
    assert offenders == [], (
        f"files construct TracerProvider (violates A1): {offenders}"
    )
