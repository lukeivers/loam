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

"""Rollback runtime — invocation, FSM, idempotence, cascade.

FSM: `requested → in_progress → {succeeded | failed | degraded}`.
The `(scope_id, idempotency_key)` unique constraint in the store makes
the second call with the same key a cache hit — the handler does not
re-run (R14).

Cascade trigger: `subscribe_to_cascade(scope_runtime)` wires a pyee
subscription on the scope emitter; when a child scope transitions to
`failed` and that child has a registered binding, rollback is invoked
automatically with a cascade-generated idempotency_key.

Eve-inference #3 (proposal §8): the cascade filter on
`ParentClosePolicy=TERMINATE` is kept — per scope-of-work's own
`_cascade_to_children`, TERMINATE is the default and the policy that
drives the child to `cancelled`. We subscribe on `failed` (not
`cancelled`) per R18's wording: "when a child scope transitions to
failed." Children with ParentClosePolicy=TERMINATE whose failure
cascades are the primary cascade shape the primitive targets.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from loam.orchestrator.ipc import ApplicationError
from loam.scope_of_work import (
    ParentClosePolicy,
    ScopeRuntime,
)

from . import observability as obs
from .notification import (
    RollbackNotification,
    RollbackNotifier,
    render_rollback_failure_text,
)
from .spec import (
    CompensationPathBinding,
    RollbackContext,
    RollbackInvocationRecord,
    RollbackResult,
)
from .store import ReversibilityStore


# IPC application error codes — proposal §3.3.
IPC_REVERSIBILITY_MISSING_COMPENSATION = -32050
IPC_REVERSIBILITY_UNREGISTERED_HANDLE = -32051
IPC_REVERSIBILITY_NOT_ACTIVATED = -32052


HandlerFn = Callable[[RollbackContext], Awaitable[RollbackResult]]


@dataclass
class RollbackRuntime:
    """Runs compensation handlers and maintains the invocation FSM.

    Dependencies injected: the SQLite store, the handler registry, the
    scope runtime (for events/projection reads + driving the scope to
    `cancelled` on success), and the notifier.
    """

    store: ReversibilityStore
    handlers: dict[str, HandlerFn]
    scope_runtime: ScopeRuntime
    notifier: RollbackNotifier

    # ---- public IPC handler -------------------------------------------

    async def rollback(
        self,
        *,
        scope_id: str,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> RollbackInvocationRecord:
        """Main rollback entry — IPC-invoked or cascade-invoked.

        R17: raises `-32052 REVERSIBILITY_NOT_ACTIVATED` when the scope
        has no activation history (no events yet).
        """
        # R17: pre-activation refusal.
        events = self.scope_runtime.store.events_for(scope_id)
        if not self._scope_has_activated(events):
            raise ApplicationError(
                IPC_REVERSIBILITY_NOT_ACTIVATED,
                f"scope {scope_id!r} has not activated — nothing to unwind",
                data={"scope_id": scope_id},
            )

        binding = self.store.get_binding(scope_id)
        # Idempotency key: caller-supplied wins; otherwise use the
        # binding's key; otherwise synthesise one. This keeps the
        # caller's idempotence story intact even when the binding is
        # missing (e.g. cascade invoked against an unregistered scope).
        key = (
            idempotency_key
            if idempotency_key is not None
            else (binding.idempotency_key if binding else f"rb-{scope_id}-{uuid.uuid4()}")
        )

        # R14 — idempotent cache hit.
        prior = self.store.find_invocation(
            scope_id=scope_id, idempotency_key=key
        )
        if prior is not None and prior.state in ("succeeded", "failed", "degraded"):
            obs.rollback_idempotent_hit(
                scope_id=scope_id,
                idempotency_key=key,
                prior_outcome=prior.outcome or prior.state,
            )
            return prior

        # Persist requested state.
        invocation_id = f"rbi-{uuid.uuid4()}"
        obs.rollback_requested(
            scope_id=scope_id, idempotency_key=key, reason=reason or ""
        )
        self.store.insert_invocation(
            invocation_id=invocation_id,
            scope_id=scope_id,
            idempotency_key=key,
            reason=reason,
            handle=binding.handle if binding else None,
        )
        self.store.transition_invocation(
            scope_id=scope_id, idempotency_key=key, state="in_progress"
        )

        # No binding → we can't run a handler. Record failure and return.
        if binding is None:
            text = render_rollback_failure_text(
                scope_id=scope_id,
                handle=None,
                reason="no_binding_registered",
                narrative="rollback requested but no compensation binding exists",
            )
            await self.notifier.send(
                RollbackNotification(
                    kind="rollback_failed", text=text, scope_id=scope_id
                )
            )
            obs.rollback_failed(
                scope_id=scope_id,
                idempotency_key=key,
                handle=None,
                reason="no_binding_registered",
            )
            record = self.store.transition_invocation(
                scope_id=scope_id,
                idempotency_key=key,
                state="failed",
                outcome="failed",
                narrative="no binding registered for scope",
            )
            assert record is not None
            return record

        # Handle not registered → R-inferred: raise -32051 so the caller
        # sees the mismatch. This is an operational error (workspace
        # registered a binding with a handle name but did not register
        # the fn); treat as a loud failure rather than a silent
        # notification.
        fn = self.handlers.get(binding.handle)
        if fn is None:
            obs.rollback_failed(
                scope_id=scope_id,
                idempotency_key=key,
                handle=binding.handle,
                reason="unregistered_handle",
            )
            self.store.transition_invocation(
                scope_id=scope_id,
                idempotency_key=key,
                state="failed",
                outcome="failed",
                narrative=f"handler {binding.handle!r} not in registry",
            )
            raise ApplicationError(
                IPC_REVERSIBILITY_UNREGISTERED_HANDLE,
                f"binding references handle {binding.handle!r} not in registry",
                data={"scope_id": scope_id, "handle": binding.handle},
            )

        # Build the context.
        projection = self.scope_runtime.get(scope_id)
        # scope_spec is reconstructible from the projection but the
        # handler usually wants the original spec envelope; for now we
        # surface it as None when not easily reconstructed — handlers
        # read from projection.
        ctx = RollbackContext(
            scope_id=scope_id,
            scope_spec=None,
            events=tuple(events),
            projection=projection,
            idempotency_key=key,
            invocation_id=invocation_id,
        )

        # Invoke the handler with optional budget_seconds timeout.
        try:
            if binding.budget_seconds is not None:
                result = await asyncio.wait_for(
                    fn(ctx), timeout=float(binding.budget_seconds)
                )
            else:
                result = await fn(ctx)
        except asyncio.TimeoutError:
            await self._on_failure(
                scope_id=scope_id,
                key=key,
                handle=binding.handle,
                reason="handler_timeout",
                narrative=(
                    f"handler {binding.handle!r} exceeded "
                    f"budget_seconds={binding.budget_seconds}"
                ),
            )
            return self._must_fetch(scope_id, key)
        except Exception as exc:  # noqa: BLE001
            await self._on_failure(
                scope_id=scope_id,
                key=key,
                handle=binding.handle,
                reason=f"handler_raised:{type(exc).__name__}",
                narrative=str(exc),
            )
            return self._must_fetch(scope_id, key)

        # Pydantic guarantees .outcome is in the allowed set — no
        # unexpected strings reach here.
        if result.outcome == "succeeded":
            self.store.transition_invocation(
                scope_id=scope_id,
                idempotency_key=key,
                state="succeeded",
                outcome="succeeded",
                narrative=result.narrative,
            )
            # R15: drive the scope to cancelled.
            try:
                await self.scope_runtime.cancel(
                    scope_id, reason="rollback_invoked"
                )
            except Exception:
                # If the scope is already terminal, cancel raises. That
                # is not a rollback failure — rollback succeeded; the
                # scope-runtime state has simply already progressed.
                pass
            obs.rollback_succeeded(
                scope_id=scope_id,
                idempotency_key=key,
                handle=binding.handle,
            )
            return self._must_fetch(scope_id, key)
        elif result.outcome == "degraded":
            self.store.transition_invocation(
                scope_id=scope_id,
                idempotency_key=key,
                state="degraded",
                outcome="degraded",
                narrative=result.narrative,
            )
            obs.rollback_succeeded(
                scope_id=scope_id,
                idempotency_key=key,
                handle=binding.handle,
            )
            return self._must_fetch(scope_id, key)
        else:
            await self._on_failure(
                scope_id=scope_id,
                key=key,
                handle=binding.handle,
                reason="handler_returned_failed",
                narrative=result.narrative or "handler returned outcome=failed",
            )
            return self._must_fetch(scope_id, key)

    # ---- cascade subscription (R18) -----------------------------------

    def subscribe_to_cascade(self, runtime: ScopeRuntime) -> None:
        """Wire the pyee cascade subscription.

        Subscribe on `*` so we see every scope event; filter for
        `StateTransitioned(to=failed)` and `parent_close_policy=TERMINATE`.
        When a binding exists for the failed scope, invoke rollback
        with a generated idempotency_key keyed to the cascade event.
        """
        from loam.scope_of_work.events import StateTransitioned
        from loam.scope_of_work.spec import ScopeState

        async def _handler(event: Any) -> None:
            if not isinstance(event, StateTransitioned):
                return
            if event.to_state != ScopeState.failed:
                return
            scope_id = event.scope_id
            # Only cascade when binding exists — cascade on every
            # failure would be noise for scopes without handlers.
            binding = self.store.get_binding(scope_id)
            if binding is None:
                return
            # Filter on ParentClosePolicy=TERMINATE per brief §6 and
            # Eve-inference #3. Projection carries the public value.
            projection = runtime.get(scope_id)
            if projection is not None and (
                projection.parent_close_policy != ParentClosePolicy.TERMINATE
            ):
                return
            cascade_key = f"cascade-{scope_id}-{event.event_id or uuid.uuid4()}"
            obs.cascade_rollback_invoked(
                scope_id=scope_id,
                parent_scope_id=projection.parent_scope_id if projection else None,
                idempotency_key=cascade_key,
            )
            try:
                await self.rollback(
                    scope_id=scope_id,
                    reason="parent_cascade_failed",
                    idempotency_key=cascade_key,
                )
            except Exception:
                # Cascade invocations swallow exceptions — they are
                # background-triggered and the failure is already
                # recorded + notified via `_on_failure`.
                pass

        runtime.subscribe_all(_handler)

    # ---- helpers ------------------------------------------------------

    async def _on_failure(
        self,
        *,
        scope_id: str,
        key: str,
        handle: str | None,
        reason: str,
        narrative: str,
    ) -> None:
        text = render_rollback_failure_text(
            scope_id=scope_id,
            handle=handle,
            reason=reason,
            narrative=narrative,
        )
        await self.notifier.send(
            RollbackNotification(
                kind="rollback_failed", text=text, scope_id=scope_id
            )
        )
        obs.rollback_failed(
            scope_id=scope_id,
            idempotency_key=key,
            handle=handle,
            reason=reason,
        )
        self.store.transition_invocation(
            scope_id=scope_id,
            idempotency_key=key,
            state="failed",
            outcome="failed",
            narrative=narrative,
        )

    def _must_fetch(
        self, scope_id: str, key: str
    ) -> RollbackInvocationRecord:
        record = self.store.find_invocation(
            scope_id=scope_id, idempotency_key=key
        )
        assert record is not None, (
            f"rollback invocation for {scope_id}/{key} vanished"
        )
        return record

    @staticmethod
    def _scope_has_activated(events: list[Any]) -> bool:
        """True when the scope has at least one StateTransitioned event
        with to_state != proposed. The proposed-only case is pre-
        activation (R17)."""
        from loam.scope_of_work.events import StateTransitioned

        for ev in events:
            if isinstance(ev, StateTransitioned):
                # Any transition counts — paused / active / completed /
                # failed / cancelled / escalated all mean the scope
                # left `proposed`.
                if getattr(ev, "to_state", None) is not None:
                    return True
        return False
