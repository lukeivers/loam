"""Amendment #20 — S2 silent-except bundle new-behaviour tests (sites 9-10).

Research doc: docs/rebuild/plans/research/amendment-20-s2-silent-excepts-research.md.

Two new tests covering the two observability-aggregator silent-except sites:
  Site 9  — NLPath.translate LLM failure captured as llm_translate_failed event.
  Site 10 — NLPath.answer LLM failure captured as llm_format_failed event.
"""

from __future__ import annotations

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from loam.observability_aggregator import nl_path as nl_path_mod
from loam.observability_aggregator.api import QueryAPI
from loam.observability_aggregator.nl_path import NLPath, rule_based_translate


@pytest.fixture
def setup_nl_exporter(monkeypatch):
    """Install an in-memory OTel exporter and swap the nl_path tracer."""
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(
        nl_path_mod,
        "_TRACER",
        provider.get_tracer("loam.aggregator.nl", "0.1.0"),
    )
    yield exporter
    exporter.clear()


def test_S2_site9_nl_translate_surfaces_llm_failure_on_fallback(
    store, setup_nl_exporter
) -> None:
    """Site 9 — a raising llm_translate lands llm_translate_failed as a
    span event on the already-open loam.aggregator.nl_translate span;
    the function still falls back to rule_based_translate."""
    api = QueryAPI(store)

    def _raising_llm_translate(question: str):
        raise RuntimeError("translate boom")

    nl = NLPath(api, llm_translate=_raising_llm_translate)
    t = nl.translate("Show me scope spans recently")

    # Rule-based fall-through still produced a translation.
    assert t is not None
    expected = rule_based_translate("Show me scope spans recently")
    assert t.mode == expected.mode

    spans = setup_nl_exporter.get_finished_spans()
    translate_spans = [
        s for s in spans if s.name == "loam.aggregator.nl_translate"
    ]
    assert len(translate_spans) == 1
    events = translate_spans[0].events
    assert any(
        e.name == "llm_translate_failed"
        and dict(e.attributes or {}).get("exception.class") == "RuntimeError"
        and dict(e.attributes or {}).get("fallback") == "rule_based"
        for e in events
    )


def test_S2_site10_nl_answer_surfaces_llm_failure_on_fallback(
    store, setup_nl_exporter
) -> None:
    """Site 10 — a raising llm_format lands llm_format_failed as a span
    event on the loam.aggregator.nl_format span; the function still
    falls back to format_cited_answer."""
    api = QueryAPI(store)

    def _raising_llm_format(question: str, rows):
        raise RuntimeError("format boom")

    nl = NLPath(api, llm_format=_raising_llm_format)
    answer = nl.answer("Show me everything")

    # Rule-based fall-through still produced an answer.
    assert answer is not None
    assert answer.rows_returned == 0
    assert "no records" in answer.summary.lower()

    spans = setup_nl_exporter.get_finished_spans()
    fmt_spans = [s for s in spans if s.name == "loam.aggregator.nl_format"]
    assert len(fmt_spans) == 1
    events = fmt_spans[0].events
    assert any(
        e.name == "llm_format_failed"
        and dict(e.attributes or {}).get("exception.class") == "RuntimeError"
        and dict(e.attributes or {}).get("fallback") == "rule_based"
        for e in events
    )
