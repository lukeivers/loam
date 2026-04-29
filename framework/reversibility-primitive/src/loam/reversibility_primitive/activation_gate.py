"""Activation-gate — class dispatch for the reversibility wrap.

Decision matrix (R6–R12):

| class             | binding? | safety-approval? | outcome                         |
|-------------------|----------|------------------|---------------------------------|
| fully_reversible  | *        | *                | PASS (binding_redundant if set) |
| compensatable     | yes      | *                | PASS                            |
| compensatable     | no       | *                | REFUSE -32050                   |
| irreversible      | yes      | *                | PASS (safety still runs)        |
| irreversible      | no       | yes              | PASS                            |
| irreversible      | no       | no / unknown     | REFUSE -32050 (fail-closed)     |

The outcome is deterministic — no LLM inside the gate. The refusal is
raised as `ApplicationError(-32050)` BEFORE safety's wrap or the
orchestrator's `orig_activate` can run (wrap composition in
`ipc_wiring.py`).
"""

from __future__ import annotations

from typing import Any, Callable

from loam.orchestrator.ipc import ApplicationError
from loam.safety_layer.events import structural_hash  # ruling #4
from loam.scope_of_work import ReversibilityClass, ScopeSpec

from . import observability as obs
from .store import ReversibilityStore


IPC_REVERSIBILITY_MISSING_COMPENSATION = -32050


# safety_approval_resolver: callable (spec_hash) -> Any | None.
# `None` means "no approval recorded" — the gate treats unknown as
# fail-closed (R12).
SafetyApprovalResolver = Callable[[str], Any]


class ActivationGate:
    """Pure class-dispatch gate over ScopeSpec.reversibility_class.

    Constructed once; the IPC wrap calls `gate.check(spec, scope_id)`
    on every activation. Raises ApplicationError on refusal; returns
    None on pass.
    """

    def __init__(
        self,
        *,
        store: ReversibilityStore,
        safety_approval_resolver: SafetyApprovalResolver | None = None,
    ) -> None:
        self._store = store
        # None means "safety resolver not injected" — R12 fail-closed
        # posture applies.
        self._resolver = safety_approval_resolver

    def check(self, spec: ScopeSpec, *, scope_id: str) -> None:
        cls = spec.reversibility_class
        binding = self._store.get_binding(scope_id)

        if cls == ReversibilityClass.fully_reversible:
            # R6: always pass. Emit audit-only `binding_redundant` when
            # a binding exists (Eve-inference #5; kept per proposal §4.1).
            if binding is not None:
                obs.binding_redundant(scope_id=scope_id, handle=binding.handle)
            obs.activation_passed(
                scope_id=scope_id,
                reversibility_class=cls.value,
                path="fully_reversible",
            )
            return

        if cls == ReversibilityClass.compensatable:
            if binding is None:
                self._refuse(
                    scope_id=scope_id,
                    cls=cls,
                    reason="compensatable_no_binding",
                )
            obs.activation_passed(
                scope_id=scope_id,
                reversibility_class=cls.value,
                path="binding_present",
            )
            return

        # irreversible
        if binding is not None:
            # R9: binding present is sufficient for reversibility's
            # refusal to step aside. Safety's wrap still independently
            # fires on the irreversible class.
            obs.activation_passed(
                scope_id=scope_id,
                reversibility_class=cls.value,
                path="binding_present",
            )
            return

        # irreversible + no binding → check safety approval (R11).
        # R12: if resolver absent, treat as "no approval" and refuse.
        if self._resolver is None:
            self._refuse(
                scope_id=scope_id,
                cls=cls,
                reason="irreversible_no_binding_no_safety_resolver",
            )
        spec_hash = structural_hash(spec)
        approval = self._resolver(spec_hash)
        if approval is None:
            self._refuse(
                scope_id=scope_id,
                cls=cls,
                reason="irreversible_no_binding_no_approval",
            )
        obs.activation_passed(
            scope_id=scope_id,
            reversibility_class=cls.value,
            path="safety_approved",
        )

    def _refuse(
        self, *, scope_id: str, cls: ReversibilityClass, reason: str
    ) -> None:
        obs.activation_refused(
            scope_id=scope_id,
            reversibility_class=cls.value,
            reason=reason,
            code=IPC_REVERSIBILITY_MISSING_COMPENSATION,
        )
        raise ApplicationError(
            IPC_REVERSIBILITY_MISSING_COMPENSATION,
            (
                f"scope {scope_id!r} ({cls.value}) has no compensation "
                f"binding and no active safety approval"
            ),
            data={
                "scope_id": scope_id,
                "reversibility_class": cls.value,
                "reason": reason,
            },
        )
