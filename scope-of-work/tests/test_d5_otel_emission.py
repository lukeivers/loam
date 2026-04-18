"""D5 — OpenTelemetry emission with GenAI semantic conventions.

Acceptance (brief D5):
- Starting a scope produces an `invoke_scope` INTERNAL span covering
  active duration.
- LLM calls (recorded via debit API) produce child `chat {model}` spans
  following GenAI convention.
- State transitions produce span events on the scope's span.
- Budget remaining, reversibility class, and escalation reason appear
  as `pos.scope.*` attributes.
- Extension-request events appear as OTel events; no consumer is
  required for emission to succeed.
"""

from __future__ import annotations

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.runtime import ScopeRuntime
from src.spec import (
    Budget,
    BudgetAxis,
    BudgetThreshold,
    ReversibilityClass,
)
from tests.conftest import make_spec


@pytest.fixture(scope="module")
def otel_exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


@pytest.fixture
async def rt_with_otel(tmp_path, otel_exporter):
    otel_exporter.clear()
    db = tmp_path / "scope.db"
    pending = tmp_path / "pending"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=pending)
    yield rt, otel_exporter
    rt.close()


def _spans_named(exporter, name):
    return [s for s in exporter.get_finished_spans() if s.name == name]


async def test_starting_scope_produces_invoke_scope_span(rt_with_otel):
    rt, exporter = rt_with_otel
    proj = await rt.create(make_spec(goal="otel test", owner_persona="eve"))
    await rt.start(proj.scope_id)
    await rt.complete(proj.scope_id, evaluations=[("c1", "met", None)])

    spans = _spans_named(exporter, "invoke_scope")
    assert len(spans) >= 1
    span = spans[-1]
    attrs = dict(span.attributes)
    assert attrs["pos.scope.id"] == proj.scope_id
    assert attrs["gen_ai.agent.id"] == proj.scope_id
    assert attrs["gen_ai.agent.name"] == "eve"
    assert attrs["pos.scope.reversibility_class"] == "fully_reversible"


async def test_llm_call_produces_chat_span_with_genai_attrs(rt_with_otel):
    rt, exporter = rt_with_otel
    proj = await rt.create(make_spec())
    await rt.start(proj.scope_id)
    await rt.debit(
        proj.scope_id,
        input_tokens=100,
        output_tokens=50,
        prompt_name="extract_facts",
        model="claude-sonnet-4-5",
    )

    spans = _spans_named(exporter, "chat claude-sonnet-4-5")
    assert spans, "expected a chat span"
    attrs = dict(spans[-1].attributes)
    assert attrs["gen_ai.request.model"] == "claude-sonnet-4-5"
    assert attrs["gen_ai.usage.input_tokens"] == 100
    assert attrs["gen_ai.usage.output_tokens"] == 50
    assert attrs["pos.prompt.name"] == "extract_facts"
    assert attrs["pos.scope.id"] == proj.scope_id


async def test_state_transitions_recorded_as_span_events(rt_with_otel):
    rt, exporter = rt_with_otel
    proj = await rt.create(make_spec())
    await rt.start(proj.scope_id)
    await rt.pause(proj.scope_id, "rest")
    await rt.resume(proj.scope_id)
    await rt.complete(proj.scope_id, evaluations=[("c1", "met", None)])

    spans = _spans_named(exporter, "invoke_scope")
    span = spans[-1]
    event_names = [e.name for e in span.events]
    # We expect at least state_changed events for the transitions.
    assert event_names.count("scope.state_changed") >= 3


async def test_budget_attrs_on_terminal_span(rt_with_otel):
    rt, exporter = rt_with_otel
    proj = await rt.create(make_spec(budget=Budget(tokens=1000)))
    await rt.start(proj.scope_id)
    await rt.debit(proj.scope_id, input_tokens=200, output_tokens=100, model="claude-opus-4")
    await rt.complete(proj.scope_id, evaluations=[("c1", "met", None)])
    spans = _spans_named(exporter, "invoke_scope")
    attrs = dict(spans[-1].attributes)
    assert attrs.get("pos.scope.budget.tokens.remaining") == 700
    assert attrs.get("pos.scope.success_criteria.met") == 1


async def test_extension_request_does_not_require_consumer(rt_with_otel):
    """Even with no exporter wired (or with no consumer reading spans),
    emission must not raise. The default tracer is no-op when no
    provider is configured. We don't unset the provider here, but the
    invariant is: emission succeeds regardless of consumer presence."""
    rt, exporter = rt_with_otel
    proj = await rt.create(make_spec(budget=Budget(tokens=10)))
    await rt.start(proj.scope_id)
    p = await rt.debit(proj.scope_id, input_tokens=20)  # over budget
    # No raise; pause + extension event written.
    assert p.state.value == "paused"
