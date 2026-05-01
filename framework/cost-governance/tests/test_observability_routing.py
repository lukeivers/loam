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
