"""CostLedger — the deterministic core of cost governance.

Composes the store + config + notifier. Exposes two hot paths:

  * `reserve_or_refuse(spec, scope_id)` — called from the innermost
    activation wrap. Runs the ceiling math deterministically, raises
    `ApplicationError(-32060/-32061/-32062)` on refusal, inserts a
    reservation on pass, emits the 80% warning when crossed.

  * Event subscription — `subscribe(scope_runtime)` wires the pyee
    emitter so `BudgetDebited` / `BudgetRefunded` / `StateTransitioned`
    events update the ledger in-place.

No LLM inference inside the gate or ledger (brief hard constraint).
Every refusal is a Pydantic-validated raise before `orig_activate` runs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Sequence

from pos_orchestrator.ipc import ApplicationError
from scope_of_work import ScopeRuntime, ScopeSpec
from scope_of_work.events import (
    BudgetDebited,
    BudgetRefunded,
    StateTransitioned,
)
from scope_of_work.spec import ScopeState

from . import observability as obs
from .config import CostConfig, RollingCeiling, SessionCeiling
from .notification import CostNotification, CostNotifier, render_ceiling_warning_text
from .spec import (
    IPC_COST_ROLLING_CEILING_EXCEEDED,
    IPC_COST_SCOPE_BUDGET_EXCEEDED,
    IPC_COST_SESSION_CEILING_EXCEEDED,
    CeilingAdjustment,
    Reservation,
    iso_now,
    unix_now,
)
from .store import CostStore


# Type alias: (scope_id) -> session_id mapping supplied by the wiring
# layer. Default behaviour uses the orchestrator process lifecycle as
# the session boundary (Eve-inference #3).
SessionResolver = Callable[[str], str]

# Notifier dispatch is async (OneOnOneChannel.send is awaitable); the
# ledger can fire it from a sync call via `asyncio.create_task` when
# inside a running loop, or defer it to a caller-supplied sink in
# non-loop contexts (tests).
DispatchFn = Callable[[CostNotification], Awaitable[None]]


TERMINAL_STATES = {
    ScopeState.completed,
    ScopeState.failed,
    ScopeState.cancelled,
    ScopeState.escalated,
}


@dataclass
class CeilingContext:
    """Computed once per activation — the math inputs."""

    session_id: str
    session_current_time: int
    session_current_tokens: int
    session_current_money: int


class CostLedger:
    """Core cost-governance runtime.

    The ledger holds a mutable in-memory copy of the config so
    `cost.adjust_ceiling` can update caps without a restart. The
    adjustment applies to NEW activations only (Eve-inference #4); it
    does NOT re-check active reservations.
    """

    def __init__(
        self,
        *,
        store: CostStore,
        config: CostConfig,
        notifier: CostNotifier | None = None,
        session_resolver: SessionResolver | None = None,
        dispatch_fn: DispatchFn | None = None,
    ) -> None:
        self.store = store
        self._config = config
        self.notifier = notifier
        # Default session = orchestrator process lifecycle (inference #3).
        self._default_session_id = f"session-{int(unix_now())}"
        self._session_resolver = session_resolver or (
            lambda _scope_id: self._default_session_id
        )
        self._dispatch = dispatch_fn
        # Track which ceilings have already warned on this session/window
        # so C14 — "fire once per crossing, not repeatedly per debit" —
        # holds when a scope activates at 85% and subsequent debits keep
        # it between 80-100%. Key: (ceiling_kind, axis, window_kind).
        self._warnings_fired: set[tuple[str, str, str | None]] = set()

    @property
    def config(self) -> CostConfig:
        return self._config

    @property
    def default_session_id(self) -> str:
        return self._default_session_id

    # -- reserve-or-refuse -------------------------------------------

    def reserve_or_refuse(
        self, spec: ScopeSpec, *, scope_id: str
    ) -> Reservation:
        """Gate check + reservation insert.

        Raises ApplicationError on refusal; returns the inserted
        Reservation on pass. This is the deterministic refusal
        enforced by the innermost wrap.

        Reservation math (per axis where the scope declared a cap):
            committed[axis] + active_reservations[axis] + declared[axis] > ceiling[axis]
                → refuse
        """
        session_id = self._session_resolver(scope_id)
        self.store.upsert_session_start(session_id)

        declared_time = spec.budget.time_seconds
        declared_tokens = spec.budget.tokens
        declared_money = spec.budget.money_cents

        # Active reservation totals for this session (in-flight).
        active_totals = self._sum_active_reservations(session_id=session_id)

        # Session rollup totals (committed spend so far).
        session_rollup = self.store.get_session_rollup(session_id)
        committed_time = session_rollup.total_time_seconds if session_rollup else 0
        committed_tokens = session_rollup.total_tokens if session_rollup else 0
        committed_money = session_rollup.total_money_cents if session_rollup else 0

        # --- session ceiling check ---
        self._check_axis(
            scope_id=scope_id,
            ceiling_kind="session",
            window_kind=None,
            axis="time",
            declared=declared_time,
            current=committed_time + active_totals[0],
            ceiling=self._config.session.time_seconds,
            refusal_code=IPC_COST_SESSION_CEILING_EXCEEDED,
        )
        self._check_axis(
            scope_id=scope_id,
            ceiling_kind="session",
            window_kind=None,
            axis="tokens",
            declared=declared_tokens,
            current=committed_tokens + active_totals[1],
            ceiling=self._config.session.tokens,
            refusal_code=IPC_COST_SESSION_CEILING_EXCEEDED,
        )
        self._check_axis(
            scope_id=scope_id,
            ceiling_kind="session",
            window_kind=None,
            axis="money",
            declared=declared_money,
            current=committed_money + active_totals[2],
            ceiling=self._config.session.money_cents,
            refusal_code=IPC_COST_SESSION_CEILING_EXCEEDED,
        )

        # --- rolling-window ceilings ---
        now = unix_now()
        for rc in self._config.rolling:
            since = now - float(rc.duration_seconds)
            win_time, win_tokens, win_money = self.store.sum_rolling_since(
                window_kind=rc.window_kind, since_unix=since
            )
            # Active in-flight across all sessions contributes to the
            # rolling window too (reservations are the best-available
            # proxy for "about to happen"). Keep it simple: add active
            # totals across all sessions to the window base.
            all_active = self._sum_active_reservations(session_id=None)
            self._check_axis(
                scope_id=scope_id,
                ceiling_kind="rolling",
                window_kind=rc.window_kind,
                axis="time",
                declared=declared_time,
                current=win_time + all_active[0],
                ceiling=rc.time_seconds,
                refusal_code=IPC_COST_ROLLING_CEILING_EXCEEDED,
            )
            self._check_axis(
                scope_id=scope_id,
                ceiling_kind="rolling",
                window_kind=rc.window_kind,
                axis="tokens",
                declared=declared_tokens,
                current=win_tokens + all_active[1],
                ceiling=rc.tokens,
                refusal_code=IPC_COST_ROLLING_CEILING_EXCEEDED,
            )
            self._check_axis(
                scope_id=scope_id,
                ceiling_kind="rolling",
                window_kind=rc.window_kind,
                axis="money",
                declared=declared_money,
                current=win_money + all_active[2],
                ceiling=rc.money_cents,
                refusal_code=IPC_COST_ROLLING_CEILING_EXCEEDED,
            )

        # --- gate passed: insert reservation ---
        reservation = Reservation(
            scope_id=scope_id,
            session_id=session_id,
            reserved_time_seconds=declared_time,
            reserved_tokens=declared_tokens,
            reserved_money_cents=declared_money,
        )
        self.store.insert_reservation(reservation)
        obs.reservation_created(
            scope_id=scope_id,
            session_id=session_id,
            reserved_time=declared_time,
            reserved_tokens=declared_tokens,
            reserved_money_cents=declared_money,
        )
        return reservation

    # -- gate helper --------------------------------------------------

    def _check_axis(
        self,
        *,
        scope_id: str,
        ceiling_kind: str,
        window_kind: str | None,
        axis: str,
        declared: int | None,
        current: int,
        ceiling: int | None,
        refusal_code: int,
    ) -> None:
        """Axis-scoped ceiling check + throttle warning.

        `None` declared → the scope did not declare this axis; the
        axis contributes zero. Honest declaration, not validation
        failure (C7).

        `None` ceiling → the operator has not set a cap on this axis;
        no check applies.

        Refusal raises `ApplicationError(refusal_code)` with structured
        data; caller bubbles up. Warning fires once per (kind,axis,
        window) when projected ≥ warning_fraction × ceiling.
        """
        if declared is None or ceiling is None:
            return

        projected = current + declared
        if projected > ceiling:
            obs.activation_refused(
                scope_id=scope_id,
                ceiling_kind=ceiling_kind,
                axis=axis,
                window_kind=window_kind,
                code=refusal_code,
                reason=f"projected {projected} > ceiling {ceiling}",
            )
            raise ApplicationError(
                refusal_code,
                (
                    f"cost ceiling exceeded on {ceiling_kind}"
                    f"{f'[{window_kind}]' if window_kind else ''}"
                    f".{axis}: projected={projected} > ceiling={ceiling}"
                ),
                data={
                    "scope_id": scope_id,
                    "ceiling_kind": ceiling_kind,
                    "axis": axis,
                    "window_kind": window_kind,
                    "projected": projected,
                    "ceiling": ceiling,
                },
            )

        # Warning band — fire once per (kind, axis, window) crossing.
        warn_cutoff = ceiling * self._config.warning_fraction
        if projected >= warn_cutoff:
            warn_key = (ceiling_kind, axis, window_kind)
            if warn_key not in self._warnings_fired:
                self._warnings_fired.add(warn_key)
                obs.ceiling_warning(
                    scope_id=scope_id,
                    ceiling_kind=ceiling_kind,
                    axis=axis,
                    window_kind=window_kind,
                    fraction=self._config.warning_fraction,
                    projected=projected,
                    ceiling=ceiling,
                )
                if self.notifier is not None or self._dispatch is not None:
                    text = render_ceiling_warning_text(
                        scope_id=scope_id,
                        ceiling_kind=ceiling_kind,
                        axis=axis,
                        window_kind=window_kind,
                        fraction=self._config.warning_fraction,
                        projected=projected,
                        ceiling=ceiling,
                    )
                    notif = CostNotification(
                        kind="ceiling_warning",
                        text=text,
                        scope_id=scope_id,
                        ceiling_kind=ceiling_kind,
                        axis=axis,
                        window_kind=window_kind,
                    )
                    self._fire_notification(notif)

    def _fire_notification(self, notif: CostNotification) -> None:
        """Dispatch a warning. Non-blocking — scheduled on the loop
        if one is running, otherwise left to the injected dispatch.
        """
        if self._dispatch is not None:
            # Test-injected dispatch — schedule on loop if running.
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._dispatch(notif))
            except RuntimeError:
                # No loop — best-effort; the dispatch is fire-and-forget.
                asyncio.run(self._dispatch(notif))
            return
        if self.notifier is None:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.notifier.send(notif))
        except RuntimeError:
            # Not inside a running loop; run synchronously.
            asyncio.run(self.notifier.send(notif))

    # -- active-reservations sum -------------------------------------

    def _sum_active_reservations(
        self, *, session_id: str | None
    ) -> tuple[int, int, int]:
        active = self.store.list_active_reservations(session_id=session_id)
        t = sum((r.reserved_time_seconds or 0) for r in active)
        k = sum((r.reserved_tokens or 0) for r in active)
        m = sum((r.reserved_money_cents or 0) for r in active)
        return t, k, m

    # -- pyee event handling -----------------------------------------

    def subscribe(self, scope_runtime: ScopeRuntime) -> None:
        """Wire pyee subscriptions on `*` (brief §6) so the ledger
        sees every BudgetDebited / BudgetRefunded / StateTransitioned
        event as the runtime emits it.
        """
        scope_runtime.emitter.on("*", self._on_event)

    def _on_event(self, event: Any) -> None:
        if isinstance(event, BudgetDebited):
            self._apply_debit(event, sign=+1)
        elif isinstance(event, BudgetRefunded):
            # Refund is a negative debit.
            self._apply_debit(event, sign=-1)
        elif isinstance(event, StateTransitioned):
            if event.to_state in TERMINAL_STATES:
                self._reconcile(event.scope_id)

    def _apply_debit(self, event: Any, *, sign: int) -> None:
        """Apply a debit or refund to reservation + session rollup.

        Time axis: a BudgetDebited event does not carry a time delta;
        scope-of-work's budget-debit path tracks tokens + money (see
        events.py). Time-seconds spent is accrued when the runtime
        emits BudgetExtended or on state transition — we do not read
        time from a debit event.
        """
        reservation = self.store.get_reservation(event.scope_id)
        if reservation is None:
            # Activation happened outside this ledger (test harness or
            # the wrap bypassed the gate); nothing to update.
            return

        total_tokens = int(getattr(event, "input_tokens", 0) or 0) + int(
            getattr(event, "output_tokens", 0) or 0
        )
        money = int(getattr(event, "money_cents", 0) or 0)

        self.store.apply_debit_to_reservation(
            scope_id=event.scope_id,
            time_delta=0,
            tokens_delta=sign * total_tokens,
            money_delta=sign * money,
        )
        self.store.apply_debit_to_session(
            session_id=reservation.session_id,
            time_delta=0,
            tokens_delta=sign * total_tokens,
            money_delta=sign * money,
        )

    def _reconcile(self, scope_id: str) -> None:
        reservation = self.store.get_reservation(scope_id)
        if reservation is None or reservation.state == "reconciled":
            return
        updated = self.store.reconcile_reservation(scope_id=scope_id)
        if updated is None:
            return
        obs.reservation_reconciled(
            scope_id=scope_id,
            actual_time=updated.actual_time_seconds,
            actual_tokens=updated.actual_tokens,
            actual_money_cents=updated.actual_money_cents,
        )

    # -- ceiling adjustment ------------------------------------------

    def adjust_ceiling(
        self,
        *,
        ceiling_kind: str,
        axis: str,
        new_value: int | None,
        reason: str,
        window_kind: str | None = None,
    ) -> CeilingAdjustment:
        """Audit-log and apply a ceiling adjustment. NEW activations
        only — active reservations are not re-checked (C22;
        Eve-inference #4 held).
        """
        adj = CeilingAdjustment(
            ceiling_kind=ceiling_kind,
            axis=axis,
            window_kind=window_kind,
            new_value=new_value,
            reason=reason,
        )
        adj = self.store.append_ceiling_adjustment(adj)

        # Update in-memory config.
        if ceiling_kind == "session":
            sc = self._config.session
            updated = sc.model_copy(update={self._axis_field(axis): new_value})
            self._config = self._config.model_copy(update={"session": updated})
        elif ceiling_kind == "rolling":
            if window_kind is None:
                raise ValueError("window_kind required for rolling adjustment")
            new_rolling: list[RollingCeiling] = []
            found = False
            for rc in self._config.rolling:
                if rc.window_kind == window_kind:
                    new_rc = rc.model_copy(
                        update={self._axis_field(axis): new_value}
                    )
                    new_rolling.append(new_rc)
                    found = True
                else:
                    new_rolling.append(rc)
            if not found:
                raise ValueError(
                    f"rolling window_kind {window_kind!r} not configured"
                )
            self._config = self._config.model_copy(
                update={"rolling": new_rolling}
            )

        # Reset the warning-fired set so an adjustment can re-arm the
        # warning — if the ceiling just moved, the crossing state
        # has changed.
        self._warnings_fired.clear()

        obs.ceiling_adjusted(
            ceiling_kind=ceiling_kind,
            axis=axis,
            window_kind=window_kind,
            new_value=new_value,
            reason=reason,
            audit_record_id=adj.audit_record_id,
        )
        return adj

    @staticmethod
    def _axis_field(axis: str) -> str:
        return {
            "time": "time_seconds",
            "tokens": "tokens",
            "money": "money_cents",
        }[axis]
