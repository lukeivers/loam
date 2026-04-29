"""KillEngine — three-level kill dispatcher.

All three kill surfaces (CLI, persona phrase, IPC) land in
`issue_kill(level, reason, source, ...)` so the audit shape is
identical regardless of entry point.

Sealed surfaces consumed (no amendment):
  - ScopeRuntime.cancel(scope_id, reason)    — emits scope.cancelled + cascades
  - ScopeRuntime.list(...)                    — active-scope enumeration
  - Orchestrator.pause_activation(reason)     — session-kill + system-kill
  - Orchestrator.request_stop()               — system-kill clean exit
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Literal

from loam.scope_of_work import ScopeRuntime, ScopeState

from . import observability as obs
from .events import KillEventRecord, KillLevel, iso_now
from .store import SafetyStore


KillSource = Literal["cli", "persona", "ipc"]


@dataclass
class KillEngine:
    """Three-level kill dispatcher. Holds references to the sealed
    surfaces but does not mutate any of them."""

    scope_runtime: ScopeRuntime
    store: SafetyStore
    orchestrator: Any  # pos_orchestrator.Orchestrator — duck-typed to avoid circular import
    # In-memory two-step-confirm nonce table for system-kill.
    _system_kill_nonces: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._system_kill_nonces = {}

    # ---- scope kill -------------------------------------------------

    async def kill_scope(
        self, *, scope_id: str, reason: str, source: KillSource
    ) -> KillEventRecord:
        """Cancel a single scope. TERMINATE-policy children cascade per
        scope-of-work's internal behaviour — the cascade is not a
        separate safety-layer call."""
        try:
            proj = await self.scope_runtime.cancel(scope_id, reason=reason)
        except Exception as e:
            # Scope-of-work raises on unknown ids / already-terminal
            # scopes. We preserve the reason and still record an event.
            record = KillEventRecord(
                level=KillLevel.scope,
                reason=f"{reason} (cancel-raise:{type(e).__name__})",
                source=source,
                scope_id=scope_id,
                issued_at=iso_now(),
                cancelled_scope_ids=(),
            )
            self.store.record_kill(record)
            obs.scope_kill(scope_id=scope_id, reason=record.reason, source=source)
            raise

        record = KillEventRecord(
            level=KillLevel.scope,
            reason=reason,
            source=source,
            scope_id=scope_id,
            issued_at=iso_now(),
            cancelled_scope_ids=(scope_id,),
        )
        self.store.record_kill(record)
        obs.scope_kill(scope_id=scope_id, reason=reason, source=source)
        return record

    # ---- session kill -----------------------------------------------

    async def kill_session(
        self, *, reason: str, source: KillSource
    ) -> KillEventRecord:
        """Pause activation, cancel every non-terminal scope.

        Amendment #19 (site 1): a pause_activation failure is surfaced
        via ``obs.pause_activation_failed`` + suffixed into the audit
        record's ``reason`` field. The kill continues — a user-issued
        session kill is not blocked by a transient pause failure
        (fail-safe direction preserved)."""
        # Pause first so new scopes cannot activate while we iterate.
        pause_failure_class: str | None = None
        try:
            self.orchestrator.pause_activation(f"safety:session_kill:{reason}")
        except Exception as e:
            pause_failure_class = type(e).__name__
            obs.pause_activation_failed(
                level="session",
                reason=reason,
                source=source,
                exception_class=pause_failure_class,
            )

        active_ids = await self._list_non_terminal_scope_ids()
        cancelled: list[str] = []
        for sid in active_ids:
            try:
                await self.scope_runtime.cancel(sid, reason=f"safety:session_kill:{reason}")
                cancelled.append(sid)
            except Exception:
                # A scope that went terminal between list() and cancel()
                # is not a kill failure — record and continue. Amendment
                # #19 research doc §3.1 records why this line is NOT
                # widened in this amendment (not in classifier's 8-finding
                # set; deliberate intentional-silence case named in
                # comment above).
                continue

        audit_reason = (
            f"{reason} (pause_failed:{pause_failure_class})"
            if pause_failure_class
            else reason
        )
        record = KillEventRecord(
            level=KillLevel.session,
            reason=audit_reason,
            source=source,
            scope_id=None,
            issued_at=iso_now(),
            cancelled_scope_ids=tuple(cancelled),
        )
        self.store.record_kill(record)
        obs.session_kill(
            reason=reason, source=source, cancelled_count=len(cancelled)
        )
        return record

    # ---- system kill ------------------------------------------------

    def request_system_kill_nonce(self) -> str:
        """Step 1 of the two-step system-kill. Issues a nonce that step 2
        must present. Nonces are single-use and do not expire by time in
        this implementation — system kills are rare and the safety layer
        is single-process, so a stale nonce sitting in memory is
        acceptable. Eve-inference #8 (proposal §8): the builder adopted
        the two-step nonce pattern as described; an alternative like a
        confirm-token parameter on a single IPC call would collapse
        step-1/step-2 into one round-trip but lose the independent
        client-side proof-of-intent — keeping the two-call pattern."""
        import time

        nonce = secrets.token_hex(16)
        self._system_kill_nonces[nonce] = time.monotonic()
        return nonce

    def _check_nonce(self, nonce: str) -> bool:
        return self._system_kill_nonces.pop(nonce, None) is not None

    async def kill_system(
        self, *, reason: str, source: KillSource, nonce: str | None = None
    ) -> KillEventRecord:
        """Step 2 of the two-step system-kill. Requires `nonce` on the
        IPC surface; CLI uses `--yes-really`; persona uses an
        LLM-mediated confirm that the workspace's primary-persona layer
        resolves to this call with a nonce obtained from
        `request_system_kill_nonce`."""
        if source == "ipc":
            if nonce is None or not self._check_nonce(nonce):
                raise ValueError(
                    "kill_system requires a valid nonce obtained from "
                    "request_system_kill_nonce (two-step confirm)."
                )

        # Pause activation so nothing new starts.
        # Amendment #19 (site 2): surface pause failure to OTel +
        # suffix the audit reason; kill still proceeds (fail-safe).
        pause_failure_class: str | None = None
        try:
            self.orchestrator.pause_activation(f"safety:system_kill:{reason}")
        except Exception as e:
            pause_failure_class = type(e).__name__
            obs.pause_activation_failed(
                level="system",
                reason=reason,
                source=source,
                exception_class=pause_failure_class,
            )

        active_ids = await self._list_non_terminal_scope_ids()
        cancelled: list[str] = []
        failed: list[str] = []
        for sid in active_ids:
            try:
                await self.scope_runtime.cancel(sid, reason=f"safety:system_kill:{reason}")
                cancelled.append(sid)
            except Exception as e:
                # Amendment #19 (site 3): callers previously inferred
                # from cancelled_scope_ids alone which scopes were
                # killed — a failing cancel was silently dropped.
                # Record the failed id + emit a per-scope span so the
                # observable-surface carries the signal.
                failed.append(sid)
                obs.scope_cancel_failed_during_kill(
                    level="system",
                    scope_id=sid,
                    reason=reason,
                    exception_class=type(e).__name__,
                )

        # Record the terminal system-kill state BEFORE the stop request —
        # if stop races the DB write we prefer the state row to exist
        # so the next bootstrap sees it (A4).
        self.store.record_system_kill(reason=reason, source=source)

        audit_reason = (
            f"{reason} (pause_failed:{pause_failure_class})"
            if pause_failure_class
            else reason
        )
        record = KillEventRecord(
            level=KillLevel.system,
            reason=audit_reason,
            source=source,
            scope_id=None,
            issued_at=iso_now(),
            cancelled_scope_ids=tuple(cancelled),
            failed_scope_ids=tuple(failed),
        )
        self.store.record_kill(record)
        obs.system_kill(
            reason=reason, source=source, cancelled_count=len(cancelled)
        )

        # Clean exit: trigger orchestrator's stop event.
        # Amendment #19 (site 4): state row + audit already landed;
        # a request_stop failure is surfaced via OTel — the contract
        # "returns a KillEventRecord on issued system-kill" is
        # preserved, and the next bootstrap still reads the persisted
        # terminal state.
        try:
            self.orchestrator.request_stop()
        except Exception as e:
            obs.request_stop_failed(
                reason=reason, exception_class=type(e).__name__,
            )
        return record

    # ---- helpers ----------------------------------------------------

    async def _list_non_terminal_scope_ids(self) -> list[str]:
        # scope_runtime.list() supports `states=` keyword filter. We
        # enumerate non-terminal states explicitly.
        projections = self.scope_runtime.list(
            states=[ScopeState.active, ScopeState.paused, ScopeState.proposed]
        )
        return [p.scope_id for p in projections]
