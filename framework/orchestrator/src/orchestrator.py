"""Orchestrator — the long-lived asyncio process (D1 + D5 + D7 + D8).

Composes:
  - LocalStateStore          (~/.loam/orchestrator.sqlite)
  - IPCServer                (Unix-domain-socket JSON-RPC)
  - ScopeRuntime             (scope-of-work; Phase 1)
  - ObjectiveTracker         (objective-tracker; Phase 1)
  - BackgroundWorkMonitor    (primary-persona; Phase 1)

Workspace bootstrap is loaded by the workspace-bootstrap framework's
``WorkspaceBootstrapPyContribution`` adapter, NOT by _startup. See
docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md
(amendment #7). The orchestrator's own startup no longer has a
fail-closed branch tied to a workspace Python file — the fail-closed
point moved to missing ``~/.loam/bootstrap.yaml``, which the framework
refuses on with ``MissingConfigError`` (-32080).

Runtime contract:
  - `await Orchestrator(config).run()` runs until SIGTERM/SIGINT,
    then performs a graceful flush and returns cleanly with exit
    code 0 (the caller invokes sys.exit).
  - On crash inside the event loop, the span records the exception
    and the wrapper exits non-zero. launchd auto-restart follows
    per D2.

Enforcement posture:
  - activate_scope runs the full dispatch sequence per brief §D5:
    verify scope pending → bind_scope → start; failures emit a
    `bind_refused` local event, an OTel span event, and a 409 return
    to the IPC caller.
  - pause_activation(reason) / resume_activation() are thin hooks.
    No degradation policy is implemented here — the graceful-
    degradation component (separate Phase 2) calls these.

File size rationale: per STATE.md rule #9 the 200-line rule is
suspended for new-pOS code; cohesion-first. The orchestrator is the
single composition point, so keeping lifecycle + dispatch + IPC
wiring co-located reads more cleanly than splitting them.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable

from objective_tracker import ObjectiveTracker
from objective_tracker.errors import OrphanRootError, UnresolvedObjectiveError
from primary_persona import BackgroundWorkMonitor
from scope_of_work import ScopeRuntime
from scope_of_work.spec import ScopeState

from . import observability as obs
from .config import OrchestratorConfig
from .errors import BindRefused, ScopeNotPending
from .ipc import ApplicationError, IPCServer
from .local_state import LocalStateStore


_LOGGER = logging.getLogger(__name__)


_SCOPE_NOT_PENDING_CODE = -32020
_BIND_REFUSED_CODE = 409
_PAUSED_CODE = -32030


# ---------------------------------------------------------------------
# Public type — recent-corrections provider (wired through to the
# primary-persona compaction module when restoration fires).
# ---------------------------------------------------------------------


RecentCorrectionsProvider = Callable[[int], list[dict[str, Any]]]


class Orchestrator:
    """The long-lived asyncio process."""

    def __init__(
        self,
        config: OrchestratorConfig,
        *,
        recent_corrections_provider: RecentCorrectionsProvider | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.config = config
        self.config.ensure_dirs()
        self._clock = clock or time.monotonic
        self._started_at_monotonic = 0.0
        self._started_at_iso: str | None = None
        self._stop_event = asyncio.Event()
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._tick_id = 0
        self._process_span: Any | None = None

        # Phase 1 primitives
        self.scope_runtime: ScopeRuntime | None = None
        self.objective_tracker: ObjectiveTracker | None = None
        self.monitor: BackgroundWorkMonitor | None = None

        # Local state + IPC
        self.local_state = LocalStateStore(self.config.local_sqlite_path)
        self.ipc_server: IPCServer | None = None

        # Pause hook state
        self._paused = False
        self._paused_reason: str | None = None

        # Awareness cache (for 100ms-hard-ceiling with cache fallback)
        self._awareness_cache: dict[str, Any] | None = None
        self._awareness_cache_at: float | None = None
        self._awareness_lock = asyncio.Lock()

        # Recent corrections provider for compaction restoration
        self._recent_corrections_provider = recent_corrections_provider

        # Loaded persona (optional — not required for all IPC methods,
        # but required for compaction-restore).
        self.loaded_persona: Any | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def run(self) -> int:
        """Main entry point. Runs the orchestrator until SIGTERM/SIGINT
        and returns a suggested exit code."""
        exit_code = 0
        self._process_span = obs.process_start_span(
            **{
                "pos.orchestrator.workspace": self.config.workspace_label,
                "pos.orchestrator.root_dir": str(self.config.root_dir),
                "pos.orchestrator.pid": os.getpid(),
            }
        )
        try:
            await self._startup()
            self._install_signal_handlers()
            await self._stop_event.wait()
        except Exception as e:
            self.local_state.append(
                "process_crashed",
                {"message": str(e), "type": type(e).__name__},
            )
            obs.emit_event(
                self._process_span,
                "pos.orchestrator.crashed",
                {"message": str(e), "type": type(e).__name__},
            )
            exit_code = 1
        finally:
            await self._shutdown(clean=(exit_code == 0))
        return exit_code

    async def _startup(self) -> None:
        """Construct everything; register IPC methods; start monitor;
        invoke workspace bootstrap; write process_started."""
        self._started_at_monotonic = self._clock()
        from datetime import datetime, timezone

        self._started_at_iso = datetime.now(timezone.utc).isoformat()

        # Phase 1 primitives
        self.scope_runtime = ScopeRuntime(
            self.config.scope_of_work_db,
            pending_extension_dir=self.config.pending_extension_dir,
        )
        self.objective_tracker = ObjectiveTracker(self.config.objective_tracker_db)
        # Wire objective-tracker to scope-of-work emitter so
        # ScopeSuccessCriterion auto-evaluates per the Phase 1
        # integration pattern.
        self.objective_tracker.subscribe_scope_emitter(self.scope_runtime.emitter)

        # Primary-persona monitor — hosted IN this process.
        self.monitor = BackgroundWorkMonitor(runtime=self.scope_runtime)
        await self.monitor.start()

        # IPC
        assert self.config.socket_path is not None
        self.ipc_server = IPCServer(
            self.config.socket_path, socket_mode=self.config.socket_mode
        )
        self._register_ipc_methods(self.ipc_server)
        await self.ipc_server.start()

        # Workspace bootstrap is run by
        # workspace_bootstrap.adapters.workspace_bootstrap_py as a
        # late-phase contribution (amendment #7). The orchestrator no
        # longer self-loads bootstrap.py — see
        # docs/rebuild/components/orchestrator-bootstrap-unification.

        # Heartbeat task
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(), name="orchestrator-heartbeat"
        )

        # Lifecycle event.
        self.local_state.append(
            "process_started",
            {
                "pid": os.getpid(),
                "started_at": self._started_at_iso,
                "workspace": self.config.workspace_label,
            },
        )
        obs.emit_event(
            self._process_span,
            "pos.orchestrator.started",
            {
                "pid": os.getpid(),
                "workspace": self.config.workspace_label,
            },
        )

    async def _shutdown(self, *, clean: bool) -> None:
        # Stop heartbeat first so it doesn't race the flush.
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                # Expected flow on cancel — bare pass per tightened CDC 2.
                pass
            except Exception as e:
                # Amendment #26 — teardown CDC 2: _process_span is live
                # through line 257; surface the exception via
                # span.add_event.
                obs.emit_event(
                    self._process_span,
                    "pos.orchestrator.heartbeat_stop_exception",
                    {"exception_class": type(e).__name__},
                )
            self._heartbeat_task = None

        if self.monitor is not None:
            try:
                await asyncio.wait_for(
                    self.monitor.stop(), timeout=self.config.sigterm_grace_seconds
                )
            except asyncio.TimeoutError as e:
                # Amendment #26 — teardown CDC 2: sigterm_grace timeout
                # is a distinct operational signal from broad-Exception,
                # not expected-flow. Emit on _process_span (live here).
                obs.emit_event(
                    self._process_span,
                    "pos.orchestrator.monitor_stop_timeout",
                    {
                        "exception_class": type(e).__name__,
                        "grace_seconds": self.config.sigterm_grace_seconds,
                    },
                )
            except Exception as e:
                obs.emit_event(
                    self._process_span,
                    "pos.orchestrator.monitor_stop_exception",
                    {"exception_class": type(e).__name__},
                )

        if self.ipc_server is not None:
            try:
                await self.ipc_server.stop()
            except Exception as e:
                # Amendment #26 — teardown CDC 2: emit on _process_span.
                obs.emit_event(
                    self._process_span,
                    "pos.orchestrator.ipc_server_stop_exception",
                    {"exception_class": type(e).__name__},
                )
            self.ipc_server = None

        if self.scope_runtime is not None:
            try:
                self.scope_runtime.close()
            except Exception as e:
                # Amendment #26 — teardown CDC 2: emit on _process_span.
                obs.emit_event(
                    self._process_span,
                    "pos.orchestrator.scope_runtime_close_exception",
                    {"exception_class": type(e).__name__},
                )

        if clean:
            self.local_state.append(
                "process_stopped", {"pid": os.getpid(), "reason": "sigterm"}
            )
            obs.emit_event(
                self._process_span, "pos.orchestrator.stopped", {"pid": os.getpid()}
            )

        obs.end_span(self._process_span)
        self._process_span = None

        # NB: we do NOT close self.local_state here. The orchestrator's
        # run() return is followed by process exit in production (OS
        # reclaims the handle); in tests, callers query local_state
        # after shutdown. Use orch.close() for explicit cleanup.

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self._signal_handler)
            except NotImplementedError:
                # Windows or environment that can't add signal handlers.
                pass

    def _signal_handler(self) -> None:
        self._stop_event.set()

    # Test hook — set the event directly.
    def request_stop(self) -> None:
        self._stop_event.set()

    def close(self) -> None:
        """Explicit close — releases the local_state handle. Tests
        call this after they're done querying; production code relies
        on OS process exit."""
        try:
            self.local_state.close()
        except Exception:
            # Amendment #26 — teardown CDC 2: _process_span is already
            # ended by the time close() runs; logger.debug is the
            # tightened-CDC fallback when no span is in scope.
            _LOGGER.debug(
                "orchestrator_close_local_state_failed", exc_info=True
            )

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        interval = self.config.heartbeat_interval_seconds
        while not self._stop_event.is_set():
            try:
                self._tick_id += 1
                uptime = self._clock() - self._started_at_monotonic
                self.local_state.append(
                    "heartbeat",
                    {"tick_id": self._tick_id, "uptime_seconds": round(uptime, 3)},
                )
                obs.emit_event(
                    self._process_span,
                    "pos.orchestrator.heartbeat",
                    {"tick_id": self._tick_id, "uptime_seconds": round(uptime, 3)},
                )
            except Exception:
                # Never kill the loop on a heartbeat write error.
                pass
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    # ------------------------------------------------------------------
    # Dispatch-layer — bind_scope enforcement (D5)
    # ------------------------------------------------------------------

    async def activate_scope(
        self,
        scope_id: str,
        objective_id: str,
    ) -> dict[str, Any]:
        """Dispatch-layer activation.

        Sequence per brief §D5:
          1. Verify scope exists and is pending.
          2. tracker.bind_scope(scope_id, objective_id).
          3. On success: scope_runtime.start(scope_id).
          4. Emit `pos.orchestrator.scope_activated` span event.

        Raises:
          ScopeNotPending, BindRefused, or a degraded-mode error when
          paused.
        """
        assert self.scope_runtime is not None
        assert self.objective_tracker is not None

        if self._paused:
            raise ApplicationError(
                _PAUSED_CODE,
                f"activation paused: {self._paused_reason or 'unknown'}",
            )

        with obs.operation_span(
            "pos.orchestrator.activate_scope",
            **{
                "pos.scope.id": scope_id,
                "pos.objective.id": objective_id,
            },
        ) as span:
            proj = self.scope_runtime.get(scope_id)
            if proj is None:
                raise ScopeNotPending(scope_id, "<not-found>")
            # Scope-of-work uses `proposed` as the pre-active state;
            # the brief calls it "pending" in prose — same semantics.
            if proj.state != ScopeState.proposed:
                raise ScopeNotPending(scope_id, proj.state.value)

            try:
                binding = await self.objective_tracker.bind_scope(
                    scope_id, objective_id
                )
            except (UnresolvedObjectiveError, OrphanRootError) as e:
                cause_kind = type(e).__name__
                cause_message = str(e)
                event = self.local_state.append(
                    "bind_refused",
                    {
                        "scope_id": scope_id,
                        "objective_id": objective_id,
                        "cause_kind": cause_kind,
                        "cause_message": cause_message,
                    },
                )
                obs.emit_event(
                    span,
                    "pos.orchestrator.bind_refused",
                    {
                        "scope_id": scope_id,
                        "objective_id": objective_id,
                        "cause_kind": cause_kind,
                    },
                )
                raise BindRefused(
                    scope_id=scope_id,
                    objective_id=objective_id,
                    cause_kind=cause_kind,
                    cause_message=cause_message,
                    event_id=event.event_id,
                )

            await self.scope_runtime.start(scope_id)
            self.local_state.append(
                "scope_activated",
                {
                    "scope_id": scope_id,
                    "objective_id": objective_id,
                    "bound_event_id": binding.get("bound_event_id"),
                },
            )
            obs.emit_event(
                span,
                "pos.orchestrator.scope_activated",
                {
                    "scope_id": scope_id,
                    "objective_id": objective_id,
                    "bound_event_id": str(binding.get("bound_event_id")),
                },
            )
            return {
                "scope_id": scope_id,
                "objective_id": objective_id,
                "binding": binding,
            }

    # ------------------------------------------------------------------
    # Amendment #52 (A8 R1) — activate_scope_with_spec + record_dispatch_close
    # ------------------------------------------------------------------
    #
    # The persona-side dispatch wrapper (primary-persona/src/
    # dispatch_wrapper.py) cannot drive the cost/safety/reversibility
    # gate chain through `activate_scope` alone: that IPC takes only
    # ids, and the production cost-governance `spec_resolver` returns
    # None for any scope not constructed in-process by the orchestrator
    # runtime (verified empirically at amendment authoring — see
    # `.scratch/claude-output/A8-halt-surface-2026-04-26.md`).
    #
    # `activate_scope_with_spec` accepts a JSON-encoded `ScopeSpec`,
    # registers it with the in-process `ScopeRuntime` so the in-memory
    # CostLedger subscriber sees `ScopeCreated`, then routes through
    # the existing wrapped IPC chain so the gate verdict fires
    # identically to a direct `activate_scope` call.
    #
    # `record_dispatch_close` is the close-emission surface paired with
    # `activate_scope_with_spec`: emit `BudgetDebited` for the agent-
    # reported tokens and transition the scope to a terminal state.

    async def activate_scope_with_spec(
        self,
        scope_id: str,
        objective_id: str,
        spec_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Activate a scope from a caller-supplied ScopeSpec payload.

        Sequence:
          1. Decode `spec_payload` into a `ScopeSpec` (Pydantic
             validation; malformed payload raises `ValidationError`).
          2. If `scope_id` is not yet registered in the runtime,
             call `scope_runtime.create(spec, scope_id=...)` to
             register it in-process so the in-memory subscribers
             (notably the cost-governance ledger) see ScopeCreated.
             If the scope is already registered (idempotent retry),
             skip the create and proceed.
          3. Delegate to `self.activate_scope(scope_id, objective_id)`
             so the existing dispatch sequence (verify pending →
             bind_scope → start) fires unchanged.

        Returns the `activate_scope` result dict augmented with
        `scope_id` echoed back. Wrap-chain firing happens on the IPC
        path (see `_register_ipc_methods.activate_scope_with_spec`) —
        this Python surface is the unwrapped path used by tests.
        """
        from scope_of_work import ScopeSpec

        assert self.scope_runtime is not None
        spec = ScopeSpec.model_validate(spec_payload)
        existing = self.scope_runtime.get(scope_id)
        if existing is None:
            await self.scope_runtime.create(spec, scope_id=scope_id)
        result = await self.activate_scope(scope_id, objective_id)
        return {**result, "scope_id": scope_id}

    async def record_dispatch_close(
        self,
        scope_id: str,
        *,
        terminal_state: str,
        debited_tokens: int = 0,
    ) -> dict[str, Any]:
        """Emit BudgetDebited (if tokens > 0) and transition the scope
        to a terminal state.

        The persona-side wrapper calls this once per dispatch close
        with the agent-reported `total_tokens` and the terminal state
        ("completed" | "failed" | "cancelled").
        """
        assert self.scope_runtime is not None
        if terminal_state not in ("completed", "failed", "cancelled"):
            raise ApplicationError(
                -32602,
                "terminal_state must be 'completed' | 'failed' | 'cancelled'",
            )
        if debited_tokens > 0:
            await self.scope_runtime.debit(
                scope_id, output_tokens=int(debited_tokens)
            )
        if terminal_state == "completed":
            await self.scope_runtime.complete(scope_id)
        elif terminal_state == "failed":
            await self.scope_runtime.fail(scope_id, reason="dispatch_failed")
        else:  # cancelled
            await self.scope_runtime.cancel(
                scope_id, reason="dispatch_cancelled"
            )
        return {
            "scope_id": scope_id,
            "terminal_state": terminal_state,
            "debited_tokens": int(debited_tokens),
        }

    # ------------------------------------------------------------------
    # Pause / resume hooks for graceful-degradation component
    # ------------------------------------------------------------------

    def pause_activation(self, reason: str) -> None:
        self._paused = True
        self._paused_reason = reason
        self.local_state.append("pause_activation", {"reason": reason})
        obs.emit_event(
            self._process_span,
            "pos.orchestrator.pause_activation",
            {"reason": reason},
        )

    def resume_activation(self) -> None:
        prior = self._paused_reason
        self._paused = False
        self._paused_reason = None
        self.local_state.append(
            "resume_activation", {"prior_reason": prior}
        )
        obs.emit_event(
            self._process_span,
            "pos.orchestrator.resume_activation",
            {"prior_reason": prior},
        )

    @property
    def is_paused(self) -> bool:
        return self._paused

    # ------------------------------------------------------------------
    # Compaction integration (D8)
    # ------------------------------------------------------------------

    def set_compaction_flag(self, session_id: str | None = None) -> int:
        """Called via IPC from the session's PreCompact hook."""
        event = self.local_state.set_compaction_flag(session_id=session_id)
        obs.emit_event(
            self._process_span,
            "pos.orchestrator.compaction_flag_set",
            {"session_id": session_id or ""},
        )
        return event.event_id

    def compaction_flag_pending(self) -> bool:
        return self.local_state.compaction_flag_pending()

    async def consume_compaction(
        self,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Called on the next post-compaction UserPromptSubmit.

        Returns the survival payload (five-item canonical list) and
        clears the flag. Returns None if no flag is pending.
        """
        if not self.compaction_flag_pending():
            return None
        from primary_persona.compaction import (
            build_survival_payload,
        )

        if self.loaded_persona is None:
            raise ApplicationError(
                -32031,
                "compaction restore requested but no persona loaded on orchestrator",
            )
        assert self.scope_runtime is not None
        payload = build_survival_payload(
            persona=self.loaded_persona,
            runtime=self.scope_runtime,
            recent_corrections_provider=self._recent_corrections_provider,
        )
        self.local_state.clear_compaction_flag()
        obs.emit_event(
            self._process_span,
            "pos.orchestrator.compaction_restored",
            {"session_id": session_id or ""},
        )
        return payload.to_dict()

    def set_loaded_persona(self, persona: Any) -> None:
        """Workspace bootstrap wires the loaded persona here so
        compaction restoration has access to contract + authority
        boundary."""
        self.loaded_persona = persona

    def set_recent_corrections_provider(
        self, provider: RecentCorrectionsProvider
    ) -> None:
        self._recent_corrections_provider = provider

    # ------------------------------------------------------------------
    # Awareness (D4) — 100ms hard ceiling with cache fallback
    # ------------------------------------------------------------------

    async def get_awareness(self, turn_id: str) -> dict[str, Any]:
        """Return an awareness block for this turn.

        Contract:
          - If the live pull completes within
            config.awareness_pull_timeout_ms, return it and refresh
            the cache.
          - Otherwise return the last cached block with
            `stale: true` and a `cache_age_ms` value.
          - If no cache is available and the live pull times out,
            return an empty block marked stale (no block is worse
            than a slightly-stale block, but an empty block preserves
            shape so the session never blocks).
        """
        assert self.monitor is not None
        timeout_s = self.config.awareness_pull_timeout_ms / 1000.0

        def _build_sync() -> dict[str, Any]:
            block = self.monitor.on_user_prompt(turn_id=turn_id)  # type: ignore[union-attr]
            return block.to_dict()

        # Run the monitor snapshot in a worker thread so the asyncio
        # timeout is honoured even when the snapshot is a slow sync
        # call. In normal operation the snapshot is fast (<1ms); we
        # pay the thread-hop cost for the 100ms-ceiling guarantee.
        try:
            fresh = await asyncio.wait_for(
                asyncio.to_thread(_build_sync), timeout=timeout_s
            )
        except asyncio.TimeoutError:
            return self._stale_awareness(turn_id, reason="timeout")
        except Exception as e:
            # Graceful fallback on unexpected monitor failure.
            stale = self._stale_awareness(turn_id, reason=f"error:{type(e).__name__}")
            return stale

        async with self._awareness_lock:
            self._awareness_cache = fresh
            self._awareness_cache_at = self._clock()
        fresh_marked = dict(fresh)
        fresh_marked["stale"] = False
        fresh_marked["cache_age_ms"] = 0
        return fresh_marked

    def _stale_awareness(self, turn_id: str, *, reason: str) -> dict[str, Any]:
        cached = self._awareness_cache
        if cached is None:
            from datetime import datetime, timezone

            return {
                "turn_id": turn_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "active": [],
                "pending_decision": [],
                "stuck": [],
                "recently_finished": [],
                "escalated": [],
                "failed": [],
                "stale": True,
                "stale_reason": f"no_cache:{reason}",
                "cache_age_ms": 0,
            }
        age_ms = 0
        if self._awareness_cache_at is not None:
            age_ms = int((self._clock() - self._awareness_cache_at) * 1000)
        out = dict(cached)
        out["turn_id"] = turn_id
        out["stale"] = True
        out["stale_reason"] = reason
        out["cache_age_ms"] = age_ms
        return out

    # ------------------------------------------------------------------
    # IPC method registration
    # ------------------------------------------------------------------

    def _register_ipc_methods(self, server: IPCServer) -> None:
        async def ping(params: dict[str, Any]) -> dict[str, Any]:
            return {"pong": True, "ts": time.time()}

        async def status(params: dict[str, Any]) -> dict[str, Any]:
            uptime = self._clock() - self._started_at_monotonic
            return {
                "started_at": self._started_at_iso,
                "uptime_seconds": round(uptime, 3),
                "pid": os.getpid(),
                "tick_id": self._tick_id,
                "paused": self._paused,
                "paused_reason": self._paused_reason,
                "compaction_flag_pending": self.compaction_flag_pending(),
            }

        async def awareness(params: dict[str, Any]) -> dict[str, Any]:
            turn_id = str(params.get("turn_id") or f"turn-{uuid.uuid4()}")
            return await self.get_awareness(turn_id)

        async def activate_scope(params: dict[str, Any]) -> dict[str, Any]:
            scope_id = params.get("scope_id")
            objective_id = params.get("objective_id")
            if not isinstance(scope_id, str) or not isinstance(objective_id, str):
                raise ApplicationError(
                    -32602, "scope_id and objective_id (strings) are required"
                )
            try:
                return await self.activate_scope(scope_id, objective_id)
            except ScopeNotPending as e:
                raise ApplicationError(
                    _SCOPE_NOT_PENDING_CODE,
                    str(e),
                    data={"scope_id": e.scope_id, "state": e.current_state},
                )
            except BindRefused as e:
                raise ApplicationError(
                    _BIND_REFUSED_CODE,
                    str(e),
                    data={
                        "scope_id": e.scope_id,
                        "objective_id": e.objective_id,
                        "cause_kind": e.cause_kind,
                        "event_id": e.event_id,
                    },
                )

        async def activate_scope_with_spec(params: dict[str, Any]) -> Any:
            """Amendment #52 (A8 R1): activate a scope from a caller-
            supplied ScopeSpec payload, then route through the
            wrap-chain `activate_scope` handler so cost / safety /
            reversibility gates fire identically to a direct
            `activate_scope` call.
            """
            from pydantic import ValidationError as _PydValidationError
            from scope_of_work import ScopeSpec

            scope_id = params.get("scope_id")
            objective_id = params.get("objective_id")
            spec_payload = params.get("spec")
            if not isinstance(scope_id, str) or not isinstance(
                objective_id, str
            ):
                raise ApplicationError(
                    -32602,
                    "scope_id and objective_id (strings) are required",
                )
            if not isinstance(spec_payload, dict):
                raise ApplicationError(
                    -32602, "spec (object) is required"
                )
            try:
                spec = ScopeSpec.model_validate(spec_payload)
            except _PydValidationError as e:
                raise ApplicationError(
                    -32602, f"spec validation failed: {e}"
                )
            assert self.scope_runtime is not None
            existing = self.scope_runtime.get(scope_id)
            if existing is None:
                await self.scope_runtime.create(spec, scope_id=scope_id)
            wrapped = server._handlers.get("activate_scope")
            if wrapped is None:
                raise ApplicationError(
                    -32601, "activate_scope not registered on orchestrator"
                )
            return await wrapped(
                {"scope_id": scope_id, "objective_id": objective_id}
            )

        async def record_dispatch_close(params: dict[str, Any]) -> Any:
            """Amendment #52 (A8 R1): emit BudgetDebited and transition
            the scope to a terminal state."""
            scope_id = params.get("scope_id")
            terminal_state = params.get("terminal_state")
            debited_tokens = params.get("debited_tokens", 0)
            if not isinstance(scope_id, str):
                raise ApplicationError(-32602, "scope_id (string) is required")
            if terminal_state not in ("completed", "failed", "cancelled"):
                raise ApplicationError(
                    -32602,
                    "terminal_state must be 'completed' | 'failed' | "
                    "'cancelled'",
                )
            if not isinstance(debited_tokens, int) or debited_tokens < 0:
                raise ApplicationError(
                    -32602, "debited_tokens must be a non-negative integer"
                )
            return await self.record_dispatch_close(
                scope_id,
                terminal_state=terminal_state,
                debited_tokens=debited_tokens,
            )

        async def pause(params: dict[str, Any]) -> dict[str, Any]:
            reason = str(params.get("reason") or "unspecified")
            self.pause_activation(reason)
            return {"paused": True, "reason": reason}

        async def resume(params: dict[str, Any]) -> dict[str, Any]:
            self.resume_activation()
            return {"paused": False}

        async def mark_precompact(params: dict[str, Any]) -> dict[str, Any]:
            session_id = params.get("session_id")
            event_id = self.set_compaction_flag(
                str(session_id) if session_id is not None else None
            )
            return {"flag_event_id": event_id, "pending": True}

        async def consume_compaction(params: dict[str, Any]) -> dict[str, Any] | None:
            session_id = params.get("session_id")
            payload = await self.consume_compaction(
                session_id=str(session_id) if session_id is not None else None
            )
            return payload or {"pending": False}

        async def local_event_count(params: dict[str, Any]) -> dict[str, Any]:
            event_type = params.get("event_type")
            n = self.local_state.count(event_type if isinstance(event_type, str) else None)
            return {"count": n}

        server.register("ping", ping)
        server.register("status", status)
        server.register("awareness", awareness)
        server.register("activate_scope", activate_scope)
        # Amendment #52 (A8 R1) — paired IPC methods for the persona-
        # side dispatch wrapper. activate_scope_with_spec composes onto
        # the existing activate_scope wrap chain (registered above);
        # record_dispatch_close drives BudgetDebited + terminal-state
        # transition.
        server.register("activate_scope_with_spec", activate_scope_with_spec)
        server.register("record_dispatch_close", record_dispatch_close)
        server.register("pause", pause)
        server.register("resume", resume)
        server.register("mark_precompact", mark_precompact)
        server.register("consume_compaction", consume_compaction)
        server.register("local_event_count", local_event_count)

    # ------------------------------------------------------------------
    # Test helpers — programmatic run instead of signal-driven.
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def running(self) -> AsyncIterator[Orchestrator]:
        """Context manager for tests — yields a running orchestrator;
        requests stop + awaits clean shutdown on exit."""
        self._process_span = obs.process_start_span(
            **{
                "pos.orchestrator.workspace": self.config.workspace_label,
                "pos.orchestrator.root_dir": str(self.config.root_dir),
                "pos.orchestrator.pid": os.getpid(),
            }
        )
        try:
            await self._startup()
            yield self
        finally:
            self.request_stop()
            await self._shutdown(clean=True)
