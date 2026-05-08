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

"""ScopeRuntime — the public orchestrator.

Composes the EventStore, projector, trigger evaluator, pyee emitter,
and OTel tracer behind one public API. Per-scope `asyncio.Lock`
serialises mutations; cross-process coordination is event-log polling
(see `poll_external_events`).

The legal-transition table lives in `policies.py`; the public read
model in `projection_view.py`.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Sequence

from pyee.asyncio import AsyncIOEventEmitter

from . import observability as obs
from .events import (
    BudgetDebited,
    BudgetExtended,
    BudgetRefunded,
    ChildLinked,
    ExtensionRejected,
    ExtensionRequested,
    ObserverAdded,
    ObserverRemoved,
    ParentCloseRequested,
    ScopeCreated,
    ScopeEvent,
    StateTransitioned,
    SuccessCriterionEvaluated,
    TriggerFired,
)
from .policies import is_legal, is_terminal
from .projection import (
    ScopeProjectionData,
    project,
    projection_to_state_row,
)
from .projection_view import ScopeProjection, public_projection
from .spec import (
    BudgetAxis,
    BudgetExhaustionPolicy,
    Observer,
    ParentClosePolicy,
    ScopeSpec,
    ScopeState,
)
from .store import EventStore
from .triggers import (
    evaluate_trigger,
    remaining_for_axis,
)


class ScopeRuntime:
    """Orchestrates scope lifecycle on top of an EventStore."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        pending_extension_dir: str | Path | None = None,
        cross_process_poll_interval: float = 0.25,
    ) -> None:
        self._store = EventStore(db_path)
        self._emitter = AsyncIOEventEmitter()
        self._scope_locks: dict[str, asyncio.Lock] = {}
        self._scope_locks_lock = asyncio.Lock()
        self._invoke_spans: dict[str, Any] = {}
        self._registered_callbacks: dict[str, Callable[..., Awaitable[None]]] = {}
        self._pending_extension_dir = (
            Path(pending_extension_dir)
            if pending_extension_dir is not None
            else Path(self._store.path).parent / "pending_extensions"
        )
        self._pending_extension_dir.mkdir(parents=True, exist_ok=True)
        self._poll_interval = cross_process_poll_interval

    @property
    def store(self) -> EventStore:
        return self._store

    @property
    def emitter(self) -> AsyncIOEventEmitter:
        return self._emitter

    def close(self) -> None:
        self._store.close()

    # -- helpers -------------------------------------------------------

    async def _lock_for(self, scope_id: str) -> asyncio.Lock:
        async with self._scope_locks_lock:
            lock = self._scope_locks.get(scope_id)
            if lock is None:
                lock = asyncio.Lock()
                self._scope_locks[scope_id] = lock
            return lock

    def _append(self, event: ScopeEvent) -> Any:
        scope_span = self._invoke_spans.get(event.scope_id)
        trace_id, span_id = obs.span_ids(scope_span)
        if trace_id and not event.otel_trace_id:
            event = event.model_copy(
                update={"otel_trace_id": trace_id, "otel_span_id": span_id}
            )
        return self._store.append(event).event

    def _project(self, scope_id: str) -> ScopeProjectionData:
        return project(scope_id, self._store.events_for(scope_id))

    def _persist(self, proj: ScopeProjectionData) -> None:
        self._store.upsert_state(projection_to_state_row(proj))

    def _public(self, proj: ScopeProjectionData) -> ScopeProjection:
        return public_projection(proj)

    def _fan_out(self, scope_id: str, event: ScopeEvent) -> None:
        self._emitter.emit(f"scope:{scope_id}", event)
        self._emitter.emit("*", event)

    # -- pyee fan-out --------------------------------------------------

    def subscribe(self, scope_id: str, callback: Callable[[ScopeEvent], Any]) -> None:
        self._emitter.on(f"scope:{scope_id}", callback)

    def subscribe_all(self, callback: Callable[[ScopeEvent], Any]) -> None:
        self._emitter.on("*", callback)

    def register_callback(
        self, handle: str, fn: Callable[..., Awaitable[None]]
    ) -> None:
        self._registered_callbacks[handle] = fn

    # ------------------------------------------------------------------
    # Public API: lifecycle
    # ------------------------------------------------------------------

    async def create(
        self,
        spec: ScopeSpec,
        *,
        scope_id: str | None = None,
        parent_scope_id: str | None = None,
    ) -> ScopeProjection:
        sid = scope_id or f"scope-{uuid.uuid4()}"
        async with await self._lock_for(sid):
            ev = self._append(
                ScopeCreated(
                    scope_id=sid,
                    goal=spec.goal,
                    constraints=spec.constraints,
                    budget=spec.budget,
                    reversibility_class=spec.reversibility_class,
                    success_criteria=spec.success_criteria,
                    observers=spec.observers,
                    escalation_triggers=spec.escalation_triggers,
                    owner_persona=spec.owner_persona,
                    parent_close_policy=spec.parent_close_policy,
                    parent_scope_id=parent_scope_id,
                    expected_duration_seconds=spec.expected_duration_seconds,
                )
            )
            self._fan_out(sid, ev)
            if parent_scope_id:
                ev2 = self._append(
                    ChildLinked(scope_id=parent_scope_id, child_scope_id=sid)
                )
                self._fan_out(parent_scope_id, ev2)
                self._persist(self._project(parent_scope_id))
            proj = self._project(sid)
            self._persist(proj)
            return self._public(proj)

    async def start(self, scope_id: str) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            await self._transition(self._project(scope_id), ScopeState.active)
            return self._public(self._project(scope_id))

    async def pause(self, scope_id: str, reason: str | None = None) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            await self._transition(
                self._project(scope_id), ScopeState.paused, pause_reason=reason
            )
            return self._public(self._project(scope_id))

    async def resume(self, scope_id: str) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            await self._transition(self._project(scope_id), ScopeState.active)
            return self._public(self._project(scope_id))

    async def complete(
        self,
        scope_id: str,
        *,
        evaluations: Sequence[tuple[str, str, str | None]] | None = None,
    ) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            for crit_id, result, note in (evaluations or []):
                ev = SuccessCriterionEvaluated(
                    scope_id=scope_id,
                    criterion_id=crit_id,
                    result=result,  # type: ignore[arg-type]
                    note=note,
                )
                ap = self._append(ev)
                self._fan_out(scope_id, ap)
                await self._evaluate_triggers(self._project(scope_id), ap)
            await self._transition(self._project(scope_id), ScopeState.completed)
            return self._public(self._project(scope_id))

    async def fail(self, scope_id: str, reason: str) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            await self._transition(
                self._project(scope_id), ScopeState.failed, reason=reason
            )
            return self._public(self._project(scope_id))

    async def cancel(
        self, scope_id: str, reason: str | None = None
    ) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            proj = self._project(scope_id)
            children = tuple(proj.children)
            await self._transition(proj, ScopeState.cancelled, reason=reason)
        await self._cascade_to_children(scope_id, children, reason=reason)
        return self._public(self._project(scope_id))

    # ------------------------------------------------------------------
    # Public API: budget
    # ------------------------------------------------------------------

    async def debit(
        self,
        scope_id: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        money_cents: int = 0,
        prompt_name: str | None = None,
        model: str | None = None,
        call_id: str | None = None,
    ) -> ScopeProjection:
        cid = call_id or f"call-{uuid.uuid4()}"
        async with await self._lock_for(scope_id):
            ap = self._append(
                BudgetDebited(
                    scope_id=scope_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    money_cents=money_cents,
                    prompt_name=prompt_name,
                    model=model,
                    call_id=cid,
                )
            )
            if model:
                obs.emit_chat_span(
                    model=model,
                    prompt_name=prompt_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    scope_id=scope_id,
                    parent_span=self._invoke_spans.get(scope_id),
                )
            self._fan_out(scope_id, ap)
            proj = self._project(scope_id)
            self._persist(proj)
            await self._evaluate_triggers(proj, ap)
            await self._enforce_budget_exhaustion(proj)
            return self._public(self._project(scope_id))

    async def refund(
        self,
        scope_id: str,
        call_id: str,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        money_cents: int | None = None,
        reason: str | None = None,
    ) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            proj = self._project(scope_id)
            prior = proj.debits_by_call.get(call_id)
            if prior is None:
                raise KeyError(
                    f"refund: no prior debit with call_id={call_id!r} on {scope_id}"
                )
            ip, op_, mc = prior
            ap = self._append(
                BudgetRefunded(
                    scope_id=scope_id,
                    call_id=call_id,
                    input_tokens=ip if input_tokens is None else input_tokens,
                    output_tokens=op_ if output_tokens is None else output_tokens,
                    money_cents=mc if money_cents is None else money_cents,
                    reason=reason,
                )
            )
            self._fan_out(scope_id, ap)
            self._persist(self._project(scope_id))
            return self._public(self._project(scope_id))

    async def extend(
        self, scope_id: str, axis: BudgetAxis, amount: int
    ) -> ScopeProjection:
        if amount < 0:
            raise ValueError("extend amount must be non-negative")
        async with await self._lock_for(scope_id):
            ap = self._append(
                BudgetExtended(scope_id=scope_id, axis=axis, amount=amount)
            )
            self._fan_out(scope_id, ap)
            proj = self._project(scope_id)
            self._persist(proj)
            if (
                proj.state == ScopeState.paused
                and proj.pending_extension_axis is None
                and proj.pause_reason
                and "pending_extension_request" in (proj.pause_reason or "")
            ):
                self._clear_pending_file(scope_id)
                await self._transition(proj, ScopeState.active)
            return self._public(self._project(scope_id))

    async def reject(self, scope_id: str) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            proj = self._project(scope_id)
            axis = proj.pending_extension_axis
            if axis is None:
                raise RuntimeError(
                    f"reject: no pending extension on scope {scope_id!r}"
                )
            ap = self._append(ExtensionRejected(scope_id=scope_id, axis=axis))
            self._fan_out(scope_id, ap)
            proj = self._project(scope_id)
            target = (
                ScopeState.completed
                if proj.success_criteria_met
                else ScopeState.cancelled
            )
            self._clear_pending_file(scope_id)
            await self._transition(proj, target, reason="extension_rejected")
            return self._public(self._project(scope_id))

    # ------------------------------------------------------------------
    # Public API: observers and success criteria
    # ------------------------------------------------------------------

    async def add_observer(
        self, scope_id: str, observer: Observer
    ) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            ap = self._append(ObserverAdded(scope_id=scope_id, observer=observer))
            self._fan_out(scope_id, ap)
            self._persist(self._project(scope_id))
            if (
                observer.callback_handle
                and observer.callback_handle in self._registered_callbacks
            ):
                self._emitter.on(
                    f"scope:{scope_id}",
                    self._registered_callbacks[observer.callback_handle],
                )
            return self._public(self._project(scope_id))

    async def remove_observer(
        self, scope_id: str, observer_id: str
    ) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            ap = self._append(
                ObserverRemoved(scope_id=scope_id, observer_id=observer_id)
            )
            self._fan_out(scope_id, ap)
            self._persist(self._project(scope_id))
            return self._public(self._project(scope_id))

    async def evaluate_success_criterion(
        self,
        scope_id: str,
        *,
        criterion_id: str,
        result: str,
        note: str | None = None,
    ) -> ScopeProjection:
        async with await self._lock_for(scope_id):
            ap = self._append(
                SuccessCriterionEvaluated(
                    scope_id=scope_id,
                    criterion_id=criterion_id,
                    result=result,  # type: ignore[arg-type]
                    note=note,
                )
            )
            self._fan_out(scope_id, ap)
            proj = self._project(scope_id)
            self._persist(proj)
            await self._evaluate_triggers(proj, ap)
            return self._public(self._project(scope_id))

    # ------------------------------------------------------------------
    # Public API: queries
    # ------------------------------------------------------------------

    def get(self, scope_id: str) -> ScopeProjection | None:
        events = self._store.events_for(scope_id)
        if not events:
            return None
        return self._public(project(scope_id, events))

    def list(
        self,
        *,
        states: Sequence[ScopeState] | None = None,
        parent_scope_id: str | None = None,
        owner_persona: str | None = None,
        include_pending_extension: bool | None = None,
        stuck: bool | None = None,
    ) -> list[ScopeProjection]:
        """Filterable enumeration — the data surface the background-
        work-monitor component polls (STATE.md rule #7, brief D3).

        Filters:
        - `states`: restrict to these lifecycle states.
        - `parent_scope_id`: restrict to children of this scope.
        - `owner_persona`: restrict to scopes owned by this persona.
        - `include_pending_extension`: True = only paused-awaiting-
          extension scopes; False = exclude them; None = no filter.
        - `stuck`: True = only stuck scopes (D0 + D3); False = only
          non-stuck; None = no filter. Stuck rule: scope declared
          `expected_duration_seconds`, is non-terminal, has had no
          state transitions after initial activation, and wall-clock
          elapsed exceeds 2× expected.
        """
        rows = self._store.list_states(
            states=[s.value for s in states] if states else None,
            parent_scope_id=parent_scope_id,
            owner_persona=owner_persona,
        )
        out: list[ScopeProjection] = []
        for r in rows:
            if include_pending_extension is True and not r.get("pending_extension_axis"):
                continue
            if include_pending_extension is False and r.get("pending_extension_axis"):
                continue
            public = self._public(self._project(r["scope_id"]))
            if stuck is True and not public.is_stuck:
                continue
            if stuck is False and public.is_stuck:
                continue
            out.append(public)
        return out

    def per_prompt_costs(self) -> list[dict[str, Any]]:
        return self._store.per_prompt_costs()

    def snapshot(self, target_path: str | Path) -> Path:
        return self._store.snapshot_to(target_path)

    def pending_extension_path(self, scope_id: str) -> Path:
        return self._pending_extension_dir / f"{scope_id}.json"

    async def poll_external_events(self, last_event_id: int = 0) -> int:
        """Drain new events from the store; fan them via pyee. Returns
        the new last_event_id. Cross-process callers loop on this."""
        new_events = self._store.events_since(last_event_id)
        for ev in new_events:
            self._fan_out(ev.scope_id, ev)
        return new_events[-1].event_id if new_events else last_event_id

    # ------------------------------------------------------------------
    # Internals: transition + trigger orchestration
    # ------------------------------------------------------------------

    async def _transition(
        self,
        proj: ScopeProjectionData,
        to_state: ScopeState,
        *,
        reason: str | None = None,
        pause_reason: str | None = None,
    ) -> None:
        if to_state == proj.state:
            return
        if not is_legal(proj.state, to_state):
            raise RuntimeError(
                f"Illegal transition {proj.state.value} → {to_state.value} "
                f"on {proj.scope_id}"
            )
        if (
            to_state == ScopeState.active
            and proj.scope_id not in self._invoke_spans
        ):
            self._invoke_spans[proj.scope_id] = obs.start_invoke_scope_span(
                scope_id=proj.scope_id,
                parent_scope_id=proj.parent_scope_id,
                owner_persona=proj.owner_persona,
                goal=proj.goal,
                reversibility_class=proj.reversibility_class.value,
            )

        ap = self._append(
            StateTransitioned(
                scope_id=proj.scope_id,
                from_state=proj.state,
                to_state=to_state,
                reason=reason,
                pause_reason=pause_reason,
            )
        )
        span = self._invoke_spans.get(proj.scope_id)
        obs.add_span_event(
            span,
            "scope.state_changed",
            {
                "from": proj.state.value,
                "to": to_state.value,
                "reason": reason or "",
                "pause_reason": pause_reason or "",
            },
        )
        if is_terminal(to_state) or to_state == ScopeState.escalated:
            obs.set_span_attrs(
                span,
                **{
                    "loam.scope.budget.tokens.remaining": (
                        remaining_for_axis(proj, BudgetAxis.tokens)
                    ),
                    "loam.scope.budget.money.remaining_cents": (
                        remaining_for_axis(proj, BudgetAxis.money)
                    ),
                    "loam.scope.budget.time.remaining_seconds": (
                        remaining_for_axis(proj, BudgetAxis.time)
                    ),
                    "loam.scope.success_criteria.met": len(proj.success_criteria_met),
                    "loam.scope.success_criteria.total": len(proj.success_criteria_ids),
                },
            )
            if to_state == ScopeState.failed:
                obs.fail_span(span, reason or "failed")
        if is_terminal(to_state):
            obs.end_span(self._invoke_spans.pop(proj.scope_id, None))

        self._fan_out(proj.scope_id, ap)
        new_proj = self._project(proj.scope_id)
        self._persist(new_proj)
        await self._evaluate_triggers(new_proj, ap)

    async def _evaluate_triggers(
        self, proj: ScopeProjectionData, event: Any
    ) -> None:
        if not proj.triggers:
            return
        for tr in proj.triggers:
            fires, value = evaluate_trigger(tr, proj, event)
            if not fires:
                continue
            ap = self._append(
                TriggerFired(
                    scope_id=proj.scope_id,
                    trigger_id=tr.trigger_id,
                    trigger_kind=tr.kind,
                    triggering_value=value,
                    reason=tr.reason_on_fire or None,
                )
            )
            obs.add_span_event(
                self._invoke_spans.get(proj.scope_id),
                "scope.trigger_fired",
                {"trigger_id": tr.trigger_id, "trigger_kind": tr.kind},
            )
            self._fan_out(proj.scope_id, ap)
            proj = self._project(proj.scope_id)
            self._persist(proj)
            if proj.state == ScopeState.active:
                await self._transition(
                    proj,
                    ScopeState.escalated,
                    reason=f"trigger:{tr.trigger_id}",
                )
                proj = self._project(proj.scope_id)

    async def _enforce_budget_exhaustion(
        self, proj: ScopeProjectionData
    ) -> None:
        if is_terminal(proj.state):
            return
        spec_event = next(
            (e for e in self._store.events_for(proj.scope_id)
             if isinstance(e, ScopeCreated)),
            None,
        )
        if spec_event is None:
            return
        budget = spec_event.budget
        for axis in (BudgetAxis.tokens, BudgetAxis.money, BudgetAxis.time):
            cap = budget.cap_for(axis)
            if cap is None:
                continue
            remaining = remaining_for_axis(proj, axis)
            if remaining is None or remaining > 0:
                continue
            if proj.pending_extension_axis == axis:
                continue
            await self._apply_exhaustion_policy(
                proj, axis, budget.policy_for(axis), remaining, cap
            )
            proj = self._project(proj.scope_id)

    async def _apply_exhaustion_policy(
        self,
        proj: ScopeProjectionData,
        axis: BudgetAxis,
        policy: BudgetExhaustionPolicy,
        remaining: int,
        cap: int,
    ) -> None:
        if policy == BudgetExhaustionPolicy.request_extension:
            self._fan_out(
                proj.scope_id,
                self._append(
                    ExtensionRequested(
                        scope_id=proj.scope_id,
                        axis=axis,
                        remaining=remaining,
                        cap=cap,
                        reason=f"{axis.value}_budget_exhausted",
                    )
                ),
            )
            self._write_pending_file(proj.scope_id, axis, remaining, cap)
            await self._transition(
                proj,
                ScopeState.paused,
                pause_reason=f"pending_extension_request:{axis.value}",
            )
        elif policy == BudgetExhaustionPolicy.halt_and_signal:
            await self._transition(
                proj, ScopeState.escalated, reason=f"{axis.value}_budget_exhausted"
            )
        elif policy == BudgetExhaustionPolicy.throttle:
            await self._transition(
                proj,
                ScopeState.paused,
                pause_reason=f"throttled:{axis.value}_budget_exhausted",
            )

    async def _cascade_to_children(
        self,
        parent_scope_id: str,
        children: Iterable[str],
        *,
        reason: str | None,
    ) -> None:
        for child in children:
            try:
                child_proj = self._project(child)
            except Exception:
                continue
            if is_terminal(child_proj.state):
                continue
            policy = ParentClosePolicy(child_proj.parent_close_policy)
            if policy == ParentClosePolicy.TERMINATE:
                await self.cancel(child, reason=reason or "parent_terminated")
            elif policy == ParentClosePolicy.ABANDON:
                continue
            elif policy == ParentClosePolicy.REQUEST_CANCEL:
                async with await self._lock_for(child):
                    ap = self._append(
                        ParentCloseRequested(
                            scope_id=child, parent_scope_id=parent_scope_id
                        )
                    )
                    self._fan_out(child, ap)

    # -- pending-extension human-readable surface ---------------------

    def _write_pending_file(
        self, scope_id: str, axis: BudgetAxis, remaining: int, cap: int
    ) -> None:
        self.pending_extension_path(scope_id).write_text(
            json.dumps(
                {
                    "scope_id": scope_id,
                    "axis": axis.value,
                    "remaining": remaining,
                    "cap": cap,
                    "requested_at": datetime.now(timezone.utc).isoformat(),
                    "respond_via": [
                        f"runtime.extend({scope_id!r}, BudgetAxis.{axis.value}, <amount>)",
                        f"runtime.reject({scope_id!r})",
                    ],
                },
                indent=2,
            )
        )

    def _clear_pending_file(self, scope_id: str) -> None:
        try:
            self.pending_extension_path(scope_id).unlink()
        except FileNotFoundError:
            pass
