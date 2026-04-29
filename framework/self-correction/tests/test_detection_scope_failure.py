"""CR1, CR2 — scope-failure detection with gate-refusal exclusion."""

from __future__ import annotations

import pytest
from loam.scope_of_work.events import StateTransitioned
from loam.scope_of_work.spec import ScopeState

from loam.self_correction import (
    GATE_REFUSAL_REASON_PATTERN,
    TriggerSource,
    build_trigger_from_state_transitioned,
)


def _mkfail(reason: str):
    return StateTransitioned(
        scope_id="scope-123",
        from_state=ScopeState.active,
        to_state=ScopeState.failed,
        reason=reason,
    )


def test_CR1_scope_failure_fires_trigger() -> None:
    ev = _mkfail("timeout exceeded")
    trigger = build_trigger_from_state_transitioned(event=ev)
    assert trigger is not None
    assert trigger.source == TriggerSource.scope_failure
    assert trigger.scope_id == "scope-123"
    assert trigger.failure_class_hint == "timeout exceeded"
    # Dedup key populated deterministically.
    assert trigger.dedup_key is not None
    assert len(trigger.dedup_key) == 64  # sha256 hex


@pytest.mark.parametrize(
    "reason",
    [
        "safety-gate/ask-refused",
        "cost-ceiling/session_exceeded",
        "reversibility-gate/compensatable_no_binding",
    ],
)
def test_CR2_gate_refusal_reasons_are_excluded(reason: str) -> None:
    ev = _mkfail(reason)
    trigger = build_trigger_from_state_transitioned(event=ev)
    assert trigger is None, (
        f"gate-refusal reason {reason!r} must not fire a trigger"
    )


def test_CR2_exclusion_pattern_is_prefix_anchored() -> None:
    # Regex must be anchored at start — a reason mentioning "safety-gate/"
    # mid-string should still fire.
    assert GATE_REFUSAL_REASON_PATTERN.match("safety-gate/x") is not None
    assert GATE_REFUSAL_REASON_PATTERN.match("cost-ceiling/x") is not None
    assert GATE_REFUSAL_REASON_PATTERN.match("reversibility-gate/x") is not None
    assert GATE_REFUSAL_REASON_PATTERN.match("prefix safety-gate/x") is None


def test_CR1_non_failed_transitions_do_not_fire() -> None:
    ev = StateTransitioned(
        scope_id="scope-1",
        from_state=ScopeState.active,
        to_state=ScopeState.completed,
    )
    assert build_trigger_from_state_transitioned(event=ev) is None
