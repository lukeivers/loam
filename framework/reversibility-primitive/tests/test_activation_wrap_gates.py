"""R6–R12: activation-gate enforcement matrix.

class × binding-presence × safety-approval grid.
"""

from __future__ import annotations

import pytest
from loam.orchestrator.ipc import ApplicationError

from loam.reversibility_primitive import (
    ActivationGate,
    CompensationPathBinding,
    IPC_REVERSIBILITY_MISSING_COMPENSATION,
    ReversibilityStore,
)
from loam.scope_of_work import ReversibilityClass

from .conftest import make_spec


def _gate(store: ReversibilityStore, resolver=None) -> ActivationGate:
    return ActivationGate(store=store, safety_approval_resolver=resolver)


def _bind(store: ReversibilityStore, scope_id: str) -> None:
    store.upsert_binding(
        CompensationPathBinding(
            scope_id=scope_id, handle="h", idempotency_key="k"
        )
    )


def test_R6_fully_reversible_always_passes(store: ReversibilityStore) -> None:
    """R6: fully_reversible passes regardless of binding presence."""
    spec = make_spec(reversibility=ReversibilityClass.fully_reversible)
    # No binding, no resolver.
    _gate(store).check(spec, scope_id="s-fr-1")
    # Binding present — still passes (emits binding_redundant audit).
    _bind(store, "s-fr-2")
    _gate(store).check(spec, scope_id="s-fr-2")


def test_R7_compensatable_no_binding_refuses(
    store: ReversibilityStore,
) -> None:
    """R7: compensatable + no binding → ApplicationError(-32050)."""
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    with pytest.raises(ApplicationError) as exc:
        _gate(store).check(spec, scope_id="s-c-1")
    assert exc.value.code == IPC_REVERSIBILITY_MISSING_COMPENSATION


def test_R8_compensatable_with_binding_passes(
    store: ReversibilityStore,
) -> None:
    """R8: compensatable + binding → gate passes."""
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    _bind(store, "s-c-2")
    _gate(store).check(spec, scope_id="s-c-2")


def test_R9_irreversible_with_binding_passes(
    store: ReversibilityStore,
) -> None:
    """R9: irreversible + binding → gate passes; safety still fires
    independently (safety wrap composition is covered separately)."""
    spec = make_spec(reversibility=ReversibilityClass.irreversible)
    _bind(store, "s-i-1")
    _gate(store).check(spec, scope_id="s-i-1")


def test_R10_irreversible_no_binding_no_approval_refuses(
    store: ReversibilityStore,
) -> None:
    """R10: irreversible, no binding, no approval → refuse -32050."""
    spec = make_spec(reversibility=ReversibilityClass.irreversible)
    # Resolver returns None → no approval.
    gate = _gate(store, resolver=lambda h: None)
    with pytest.raises(ApplicationError) as exc:
        gate.check(spec, scope_id="s-i-2")
    assert exc.value.code == IPC_REVERSIBILITY_MISSING_COMPENSATION


def test_R11_irreversible_no_binding_with_approval_passes(
    store: ReversibilityStore,
) -> None:
    """R11: irreversible, no binding, active safety approval → pass.
    The approval is peek-resolved via structural_hash."""
    spec = make_spec(reversibility=ReversibilityClass.irreversible)
    # Sentinel approval — any truthy object counts.
    approval = object()
    gate = _gate(store, resolver=lambda h: approval)
    gate.check(spec, scope_id="s-i-3")


def test_R12_irreversible_no_binding_no_resolver_refuses(
    store: ReversibilityStore,
) -> None:
    """R12: resolver not injected → fail-closed, stricter refusal."""
    spec = make_spec(reversibility=ReversibilityClass.irreversible)
    gate = _gate(store, resolver=None)
    with pytest.raises(ApplicationError) as exc:
        gate.check(spec, scope_id="s-i-4")
    assert exc.value.code == IPC_REVERSIBILITY_MISSING_COMPENSATION
    # Refusal reason identifies the fail-closed path explicitly.
    assert "no_safety_resolver" in (exc.value.data or {}).get("reason", "")
