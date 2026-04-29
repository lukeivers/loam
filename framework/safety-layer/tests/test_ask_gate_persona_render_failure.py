"""Amendment #19 (sites 5, 6) — persona-render failure observability.

A persona_render failure during ask-gate / dangerous-op notification
dispatch is surfaced via the loam.safety.persona_render_failed OTel span
and the un-rendered text is still sent to the OneOnOneChannel. This
preserves the fail-closed "notifications must go out regardless of LLM
availability" invariant while giving operators observability into the
render failure (previously silently swallowed — classifier audit
2026-04-22, AC:none).
"""

from __future__ import annotations

import pytest

from loam.orchestrator.ipc import ApplicationError
from loam.scope_of_work import ReversibilityClass

from loam.safety_layer import (
    AlwaysAskList,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    SafetyConfig,
    SafetyController,
    SafetyNotifier,
    SafetyStore,
)

from .conftest import make_spec
from .fakes import FakeOrchestrator, make_fake_channel


async def _raising_persona_render(text: str) -> str:
    raise RuntimeError("persona-render-blew-up")


def _controller_with_raising_persona(scope_runtime, tmp_path):
    store = SafetyStore(tmp_path / "safety.sqlite")
    ask_list = AlwaysAskList(
        version=1,
        framework_floor=DEFAULT_FRAMEWORK_FLOOR,
        workspace_additions=(),
        dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
    )
    ch, received = make_fake_channel(name="telegram-active", active=True)
    notifier = SafetyNotifier(channels=[ch])
    ctrl = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=FakeOrchestrator(),
        store=store,
        ask_list=ask_list,
        config=SafetyConfig(),
        notifier=notifier,
        persona_render=_raising_persona_render,
    )
    return ctrl, received


@pytest.mark.asyncio
async def test_amendment_19_ask_gate_persona_render_failure_falls_back(
    scope_runtime, tmp_path
):
    """Site 5: persona_render raising during ask-gate dispatch does
    not prevent the notification from being sent. The un-rendered
    text reaches the channel."""
    ctrl, received = _controller_with_raising_persona(scope_runtime, tmp_path)
    spec = make_spec(
        constraints=("action_class=commit_external_funds",),
    )
    with pytest.raises(ApplicationError):
        await ctrl.check_gates(spec, scope_id="s-amend19-ask")

    # The notification landed on the channel despite the persona
    # render failure — fail-closed guarantee preserved.
    assert received, "notification must be sent when persona_render raises"
    # Un-rendered text contains the safety-gate preamble that
    # render_ask_gate_text produces.
    assert any("Safety gate" in m for m in received)


@pytest.mark.asyncio
async def test_amendment_19_dangerous_op_persona_render_failure_falls_back(
    scope_runtime, tmp_path
):
    """Site 6: persona_render raising during dangerous-op gate dispatch
    does not prevent the notification from being sent."""
    ctrl, received = _controller_with_raising_persona(scope_runtime, tmp_path)
    # Under the ask-gate floor, `send_communication_as_user_to_third_party`
    # triggers ask first. We use the money-threshold clause to fire the
    # dangerous-op gate cleanly without the ask gate intercepting.
    spec = make_spec(
        goal="paid op exceeding threshold",
        money_cents=1500,
        reversibility=ReversibilityClass.fully_reversible,
    )
    with pytest.raises(ApplicationError):
        await ctrl.check_gates(spec, scope_id="s-amend19-danger")

    assert received, "dangerous-op notification must be sent when persona_render raises"
