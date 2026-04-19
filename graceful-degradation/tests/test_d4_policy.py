"""D4 — Response-policy dispatch.

Acceptance (brief):
- Mode entering `open` triggers the correct policy; pause_activation
  called on the orchestrator for P1/P2.
- Per-scope metadata override at scope creation changes policy for
  that scope only.
- P3 fall-through marks scopes failed with recoverable state.
- P4 produces a per-scope user-decision surface via notification.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from graceful_degradation import DegradationConfig, DegradationMode
from graceful_degradation.policy import (
    Policy,
    PolicyDispatcher,
    build_defaults_from_config,
)

from .fakes import FakeOrchestrator, FakeScope, FakeScopeRuntime


def _make() -> tuple[FakeOrchestrator, FakeScopeRuntime, PolicyDispatcher]:
    orch = FakeOrchestrator()
    rt = FakeScopeRuntime()
    cfg = DegradationConfig()
    dispatcher = PolicyDispatcher(
        orchestrator=orch,
        scope_runtime=rt,
        defaults=build_defaults_from_config(cfg),
    )
    return orch, rt, dispatcher


async def test_p1_pause_all_triggers_orchestrator_hook() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("s1"))
    app = await dispatcher.apply(DegradationMode.down, "ep-1", signal="connection_error")
    assert orch.paused is True
    assert "claude_upstream_degraded" in orch.paused_reason
    assert app.policy == Policy.pause_all
    # P1 with LLM scope → pauses scope.
    assert len(app.paused_scope_ids) == 1


async def test_p2_pause_llm_only_skips_deterministic_scopes() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("llm-scope"))
    deterministic = FakeScope(
        "det-scope", constraints=("deterministic_only=true",)
    )
    rt.add_scope(deterministic)
    await dispatcher.apply(
        DegradationMode.rate_limited, "ep-2", signal="rate_limited"
    )
    # LLM scope paused; deterministic left alone.
    assert ("llm-scope", "degradation:ep-2") in rt.pause_calls
    assert "det-scope" not in [c[0] for c in rt.pause_calls]


async def test_p3_fall_through_to_fail_marks_scopes_failed() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(
        FakeScope("s1", constraints=("degradation_policy=fall_through_to_fail",))
    )
    app = await dispatcher.apply(
        DegradationMode.down, "ep-3", signal="connection_error"
    )
    # Per-scope override → fail instead of pause.
    assert "s1" in app.failed_scope_ids
    assert len(rt.fail_calls) == 1


async def test_p4_request_user_decision_pauses_scope() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(
        FakeScope(
            "s1", constraints=("degradation_policy=request_user_decision",)
        )
    )
    app = await dispatcher.apply(
        DegradationMode.down, "ep-4", signal="connection_error"
    )
    assert "s1" in app.paused_scope_ids
    # awaiting_user reason tag
    reason_tags = [c[1] for c in rt.pause_calls]
    assert any("awaiting_user" in r for r in reason_tags if r)


async def test_per_scope_override_is_scope_local_only() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("s1"))  # default P1
    rt.add_scope(
        FakeScope(
            "s2", constraints=("degradation_policy=fall_through_to_fail",)
        )
    )
    app = await dispatcher.apply(
        DegradationMode.down, "ep", signal="connection_error"
    )
    # s1 is paused (P1); s2 is failed (override)
    assert "s1" in app.paused_scope_ids
    assert "s2" in app.failed_scope_ids


async def test_release_calls_resume_on_each_scope_and_orchestrator() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("s1"))
    rt.add_scope(FakeScope("s2"))
    app = await dispatcher.apply(
        DegradationMode.down, "ep", signal="connection_error"
    )
    resumed = await dispatcher.release(
        mode=DegradationMode.down,
        episode_id="ep",
        paused_scope_ids=app.paused_scope_ids,
    )
    assert sorted(resumed) == sorted(app.paused_scope_ids)
    assert orch.paused is False
    assert orch.resume_calls == 1


async def test_p2_default_for_rate_limited() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("s1"))
    app = await dispatcher.apply(
        DegradationMode.rate_limited, "ep", signal="rate_limited"
    )
    assert app.policy == Policy.pause_llm_only


async def test_p1_default_for_down() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("s1"))
    app = await dispatcher.apply(
        DegradationMode.down, "ep", signal="connection_error"
    )
    assert app.policy == Policy.pause_all


async def test_p4_default_for_auth_broken() -> None:
    orch, rt, dispatcher = _make()
    rt.add_scope(FakeScope("s1"))
    app = await dispatcher.apply(
        DegradationMode.auth_broken, "ep", signal="auth_broken"
    )
    assert app.policy == Policy.request_user_decision
