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

"""SafetyController — the composed runtime the workspace bootstrap wires.

Composition (proposal §3.1, §3.2):
  - AlwaysAskList            — Pydantic-validated YAML
  - DangerousOpGate          — stricter gate composed on the ask gate
  - SafetyStore              — SQLite persistence
  - KillEngine               — three-level kill dispatcher
  - SafetyNotifier           — dispatch via OneOnOneChannel

The workspace bootstrap constructs the controller once, then:
  1. Registers the controller's IPC methods on the shared `IPCServer`.
  2. Wraps the IPC handler for `activate_scope` so `check_gates(...)`
     fires before forwarding to the orchestrator.

The orchestrator object is NOT amended. The IPC-wrap is consumption of
the sealed `IPCServer.register()` surface (A15).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

from loam.orchestrator.ipc import ApplicationError
from loam.scope_of_work import ScopeRuntime, ScopeSpec

from . import observability as obs
from .ask_list import AlwaysAskList, parse_duration_spec
from .config import SafetyConfig
from .dangerous_op import DangerousOpGate, _extract_action_classes
from .events import (
    AskDecisionRecord,
    iso_now,
    structural_hash,
)
from .kill import KillEngine
from .notification import (
    SafetyNotification,
    SafetyNotifier,
    render_ask_gate_text,
    render_dangerous_op_text,
)
from .store import SafetyStore


# IPC application error codes (proposal §4.3 + §4.4).
IPC_ASK_GATE_PENDING = -32040
IPC_DANGEROUS_OP_GATE_BLOCKED = -32041
IPC_SYSTEM_KILL_ACTIVE = -32042
IPC_SAFETY_CHANNEL_UNAVAILABLE = -32043


class GateOutcome(str, Enum):
    pass_ = "pass"
    block = "block"


@dataclass(frozen=True)
class GateRefusal:
    """Why a gate blocked. Carried as IPC `data` on the application error
    response so a caller can render it without parsing the message."""

    code: int
    reason: str
    spec_hash: str
    action_classes: tuple[str, ...]
    scope_id: str | None = None
    trigger_reasons: tuple[str, ...] = ()


@dataclass
class SafetyController:
    """Composed safety runtime — wired by the workspace bootstrap."""

    scope_runtime: ScopeRuntime
    orchestrator: Any  # duck-typed pos_orchestrator.Orchestrator
    store: SafetyStore
    ask_list: AlwaysAskList
    config: SafetyConfig
    notifier: SafetyNotifier
    # Injected; default constructed in __post_init__ if omitted.
    kill_engine: KillEngine | None = None
    dangerous_op_gate: DangerousOpGate | None = None
    # Primary persona's LLM-mediated render hook (optional — outside
    # the gate itself). Passed the plain-text ask; returns adapted text.
    persona_render: Callable[[str], Awaitable[str]] | None = None

    def __post_init__(self) -> None:
        if self.kill_engine is None:
            self.kill_engine = KillEngine(
                scope_runtime=self.scope_runtime,
                store=self.store,
                orchestrator=self.orchestrator,
            )
        if self.dangerous_op_gate is None:
            self.dangerous_op_gate = DangerousOpGate(
                ask_list=self.ask_list,
                store=self.store,
                money_threshold_cents=self.config.money_threshold_cents,
            )

    # ---- bootstrap check for system-kill state ----------------------

    def is_system_kill_active(self) -> bool:
        return self.store.active_system_kill() is not None

    def refuse_if_system_killed(self, *, scope_id: str) -> None:
        """Called by the activation-path wrap on every activate_scope.
        Raises ApplicationError if a system kill is active and not
        cleared."""
        if self.is_system_kill_active():
            obs.system_kill_block_activation(scope_id=scope_id)
            raise ApplicationError(
                IPC_SYSTEM_KILL_ACTIVE,
                "system kill active — run `pos safety clear-system-kill` to resume",
                data={"scope_id": scope_id},
            )

    # ---- gate composition -------------------------------------------

    async def check_gates(self, spec: ScopeSpec, *, scope_id: str | None = None) -> None:
        """Fire the ask gate and the dangerous-op gate against a spec.

        On BLOCK, raises `ApplicationError` with the matching IPC code.
        On PASS, returns None — the caller proceeds to activate.

        Both gates are deterministic — pure function of the spec + the
        decision store. No LLM inference inside this method.
        """
        spec_hash = structural_hash(spec)
        classes = _extract_action_classes(spec.constraints)
        ask_set = self.ask_list.all_action_classes()
        dangerous_set = self.ask_list.dangerous_op_values()

        ask_hit = [c for c in classes if c in ask_set]
        # Dangerous-op gate runs irrespective of ask-hit (reversibility
        # + money can fire it without any action_class entry).
        assert self.dangerous_op_gate is not None
        op_decision = self.dangerous_op_gate.classify(spec)

        # First gate: ask list. Block if any ask-matched class lacks an
        # approval for this spec_hash.
        if ask_hit:
            approval = self.store.find_active_approval(spec_hash)
            outcome = GateOutcome.block if approval is None else GateOutcome.pass_
            obs.ask_gate_fired(
                scope_id=scope_id,
                spec_hash=spec_hash,
                action_classes=list(ask_hit),
                outcome=outcome.value,
            )
            if approval is None:
                await self._dispatch_ask_notification(
                    spec=spec, scope_id=scope_id, ask_hit=list(ask_hit)
                )
                if not self.notifier.has_active_channel():
                    # Fail-closed (ruling #5) — no queue, scope stays proposed.
                    raise ApplicationError(
                        IPC_SAFETY_CHANNEL_UNAVAILABLE,
                        "no active OneOnOneChannel — gate remains BLOCKED",
                        data=GateRefusal(
                            code=IPC_SAFETY_CHANNEL_UNAVAILABLE,
                            reason="channel_unavailable",
                            spec_hash=spec_hash,
                            action_classes=tuple(ask_hit),
                            scope_id=scope_id,
                        ).__dict__,
                    )
                raise ApplicationError(
                    IPC_ASK_GATE_PENDING,
                    f"ask gate pending approval for {ask_hit}",
                    data=GateRefusal(
                        code=IPC_ASK_GATE_PENDING,
                        reason="ask_gate_pending",
                        spec_hash=spec_hash,
                        action_classes=tuple(ask_hit),
                        scope_id=scope_id,
                    ).__dict__,
                )

        # Second gate: dangerous op.
        if op_decision.fired:
            outcome = (
                GateOutcome.block if op_decision.blocked else GateOutcome.pass_
            )
            obs.dangerous_op_gate_fired(
                scope_id=scope_id,
                spec_hash=spec_hash,
                reasons=list(op_decision.reasons),
                outcome=outcome.value,
            )
            if op_decision.blocked:
                await self._dispatch_dangerous_op_notification(
                    spec=spec,
                    scope_id=scope_id,
                    op_decision=op_decision,
                )
                if not self.notifier.has_active_channel():
                    raise ApplicationError(
                        IPC_SAFETY_CHANNEL_UNAVAILABLE,
                        "no active OneOnOneChannel — dangerous-op gate remains BLOCKED",
                        data=GateRefusal(
                            code=IPC_SAFETY_CHANNEL_UNAVAILABLE,
                            reason="channel_unavailable",
                            spec_hash=spec_hash,
                            action_classes=op_decision.action_classes,
                            scope_id=scope_id,
                            trigger_reasons=op_decision.reasons,
                        ).__dict__,
                    )
                raise ApplicationError(
                    IPC_DANGEROUS_OP_GATE_BLOCKED,
                    f"dangerous op blocked: {op_decision.reasons}",
                    data=GateRefusal(
                        code=IPC_DANGEROUS_OP_GATE_BLOCKED,
                        reason="dangerous_op_gate_blocked",
                        spec_hash=spec_hash,
                        action_classes=op_decision.action_classes,
                        scope_id=scope_id,
                        trigger_reasons=op_decision.reasons,
                    ).__dict__,
                )

    # ---- ask-decide IPC surface -------------------------------------

    def record_ask_decision(
        self,
        *,
        scope_spec_hash: str,
        decision: str,
        action_classes: list[str] | tuple[str, ...],
        scope_id: str | None = None,
        decided_by: str = "user",
        reasoning: str | None = None,
        now: datetime | None = None,
    ) -> AskDecisionRecord:
        """Persist a user decision. `decision` must be one of approved /
        refused. Expiry is the longest timeout across the matched
        action_classes on the ask list (fail-safe: sets the earliest
        expiry, not the latest, so an approval cannot outlive the
        tightest category timeout)."""
        now = now or datetime.now(timezone.utc)
        if decision not in ("approved", "refused"):
            raise ValueError(f"decision must be approved|refused, got {decision!r}")

        expires_at: str | None = None
        if decision == "approved":
            minutes = _earliest_timeout_minutes(self.ask_list, action_classes)
            if minutes is not None:
                expires_at = (now + timedelta(minutes=minutes)).isoformat()

        record = AskDecisionRecord(
            scope_id=scope_id,
            scope_spec_hash=scope_spec_hash,
            action_classes=tuple(action_classes),
            state=decision,  # type: ignore[arg-type]
            decided_at=now.isoformat(),
            expires_at=expires_at,
            decided_by=decided_by,
            reasoning=reasoning,
        )
        self.store.record_decision(record)
        obs.ask_decision_recorded(
            spec_hash=scope_spec_hash,
            state=decision,
            action_classes=list(action_classes),
        )
        return record

    # ---- helpers ----------------------------------------------------

    async def _dispatch_ask_notification(
        self, *, spec: ScopeSpec, scope_id: str | None, ask_hit: list[str]
    ) -> None:
        descriptions = {
            ac: (self.ask_list.entry_for(ac).description if self.ask_list.entry_for(ac) else "")
            for ac in ask_hit
        }
        timeout_hint = "4h"  # informational — stored expiry comes from the
        # earliest category timeout at record_ask_decision time.
        entry = self.ask_list.entry_for(ask_hit[0]) if ask_hit else None
        if entry is not None:
            timeout_hint = entry.timeout
        text = render_ask_gate_text(
            scope_id=scope_id,
            goal=spec.goal,
            action_classes=ask_hit,
            descriptions=descriptions,
            timeout_hint=timeout_hint,
        )
        if self.persona_render is not None:
            try:
                text = await self.persona_render(text)
            except Exception as e:
                # Amendment #19 (site 5): persona-render failure is
                # surfaced to OTel; the un-rendered text is still a
                # valid safety notification and the fail-closed
                # "notifications must go out regardless of LLM
                # availability" invariant is preserved.
                obs.persona_render_failed(
                    kind="ask_gate",
                    exception_class=type(e).__name__,
                )
        await self.notifier.send(
            SafetyNotification(kind="ask_gate", text=text, scope_id=scope_id)
        )

    async def _dispatch_dangerous_op_notification(
        self, *, spec: ScopeSpec, scope_id: str | None, op_decision: Any
    ) -> None:
        text = render_dangerous_op_text(
            scope_id=scope_id,
            goal=spec.goal,
            reasons=list(op_decision.reasons),
            money_cents=spec.budget.money_cents,
            reversibility_class=spec.reversibility_class.value,
        )
        if self.persona_render is not None:
            try:
                text = await self.persona_render(text)
            except Exception as e:
                # Amendment #19 (site 6): see site 5 comment — OTel
                # surface + fail-closed preserved.
                obs.persona_render_failed(
                    kind="dangerous_op",
                    exception_class=type(e).__name__,
                )
        await self.notifier.send(
            SafetyNotification(kind="dangerous_op", text=text, scope_id=scope_id)
        )


def _earliest_timeout_minutes(
    ask_list: AlwaysAskList,
    action_classes: list[str] | tuple[str, ...],
) -> int | None:
    """Return the smallest timeout in minutes across matched entries,
    or None if no class matched."""
    mins: list[int] = []
    for ac in action_classes:
        entry = ask_list.entry_for(ac)
        if entry is not None:
            mins.append(parse_duration_spec(entry.timeout))
    return min(mins) if mins else None
