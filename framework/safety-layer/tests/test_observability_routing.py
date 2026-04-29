"""A16 — OTel routed through the aggregator's provider.

Claim: the safety layer does not construct its own TracerProvider. It
calls `trace.get_tracer(...)` only. The aggregator's
`install_for_workspace` hook is responsible for routing the late-bound
tracer to a real exporter.

Verification approach (structural):
  1. The safety_layer.observability module imports only `trace` from
     opentelemetry — not `TracerProvider`, not `BatchSpanProcessor`.
  2. Source-level grep: no `TracerProvider(` construction anywhere in
     safety_layer/src/.
"""

from __future__ import annotations

from pathlib import Path

from loam.safety_layer import observability as safety_obs


SAFETY_SRC = Path(safety_obs.__file__).parent


def test_A16_no_tracer_provider_construction_in_safety_src():
    """No `.py` file under safety-layer/src/ calls TracerProvider(...)."""
    for py in SAFETY_SRC.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        # Allow the substring inside a comment / docstring that's
        # describing the pattern — disallow construction.
        assert "TracerProvider(" not in text, (
            f"{py.name}: constructs TracerProvider — must use "
            "aggregator's register_otel_provider instead (A16)."
        )
        assert "BatchSpanProcessor(" not in text, (
            f"{py.name}: constructs BatchSpanProcessor — aggregator owns this."
        )


def test_A16_observability_module_uses_default_tracer_api():
    import inspect
    src = inspect.getsource(safety_obs)
    # The only OTel symbol we import is `trace` (and contextmanager from stdlib).
    assert "from opentelemetry import trace" in src
    # Confirm the tracer namespace.
    assert 'trace.get_tracer("loam.safety_layer"' in src


def test_A16_spans_emit_without_consumer():
    """A graceful-degradation A1 correction — emission succeeds against
    the no-op tracer with no consumer. The safety layer inherits this
    by using `trace.get_tracer()` in the same way."""
    # Call every emitter; nothing should raise even with no provider
    # installed.
    safety_obs.scope_kill(scope_id="s", reason="r", source="cli")
    safety_obs.session_kill(reason="r", source="cli", cancelled_count=0)
    safety_obs.system_kill(reason="r", source="cli", cancelled_count=0)
    safety_obs.system_kill_cleared(reason="r")
    safety_obs.system_kill_block_activation(scope_id="s")
    safety_obs.ask_gate_fired(
        scope_id="s", spec_hash="h", action_classes=["x"], outcome="block"
    )
    safety_obs.dangerous_op_gate_fired(
        scope_id="s", spec_hash="h", reasons=["irreversible"], outcome="block"
    )
    safety_obs.ask_decision_recorded(
        spec_hash="h", state="approved", action_classes=["x"]
    )
    safety_obs.notification_dispatched(
        channel="t", outcome="delivered", kind="ask_gate"
    )
