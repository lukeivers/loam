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

"""The live-wiring path (slice 3 — plan D-SIT.4, D-SIT.5; AC.WIRE.*).

This is the harness-side ADAPTER that fires the deliberate gate inside a live
primary-session turn. It composes with the EXISTING PreToolUse hook pattern
(``in_thread_work_budget_guard.py`` / ``wd_discipline_guard.py``): same
envelope (``tool_name`` + ``tool_input``), same fail-open contract (any error
-> allow), same override sentinel, default-OFF.

Separation (D-SIT.4): the framework owns the DECISION (``evaluate_gate`` +
``run_deliberate_loop``); this adapter owns the HARNESS ADAPTATION — reading
the envelope into a :class:`PendingAction`, calling the gate, and on a fire
surfacing the deliberate critique (warn) or blocking toward re-think (the
high-severity structural signals). It mirrors how ``intent_classifier`` (the
framework decision) is wired by ``intent_classifier_inbound.py`` (the hook
adapter).

The slice-1 gate->loop spine is UNCHANGED in shape; this module only feeds it
the structural envelope and translates its decision into the PreToolUse
warn/block contract.

NOTE ON LIVE ACTIVATION (plan scope / dispatch fence): registering this
adapter as a live PreToolUse hook in the workspace ``.claude/settings.json``
is a SEPARATE owner-gated step (the frame-kernel-hook precedent). This slice
ships + tests the adapter against SIMULATED PreToolUse envelopes; the pos3
session's settings/hooks are NOT touched here. The activation is noted as a
follow-on.

ACs:

- AC.WIRE.1 — the gate fires inside a live turn (envelope -> gate -> loop) and
  the loop's deliberate output affects the outcome; a safe turn produces none.
- AC.WIRE.2 — default-OFF + zero-collateral: with the layer off the adapter
  no-ops; a turn with no structural signal yields the allow/no-op outcome
  byte-for-byte (the live form of ``gain_on_unflagged == 0``).
- AC.WIRE.3 — composes with the existing safety guards without overriding
  them: a hard block already decided by a safety guard is not un-blocked by
  this adapter (the ``safety_guard_blocked`` short-circuit).
- AC.WIRE.OA — a real envelope carrying a genuine structural signal, run
  through this production entry-point with no seeded gate state, yields the
  escalation + loop intervention; normal envelopes yield zero fires.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from .gate import GateDecision, GateSignals, Trigger, evaluate_gate
from .loop import Critic, LoopResult, run_deliberate_loop
from .signals import PendingAction, ToolResultRing
from .turn import ENABLE_ENV_VAR, TurnConfig

# The high-severity structural signals on which the adapter BLOCKS toward
# re-think (exit 2 in the PreToolUse contract) rather than merely warning.
# An irreversible machine action and a high-blast-radius action are the cases
# where letting it run-then-rethink is itself the harm; the unbounded/repeat
# signals warn-and-surface (the persona can still proceed). The builder fixes
# this severity split; it is a method call within AC.WIRE.1's outcome.
_BLOCKING_TRIGGERS = frozenset(
    {Trigger.MACHINE_IRREVERSIBLE, Trigger.HIGH_BLAST_RADIUS}
)


class WireOutcome(str, Enum):
    """The PreToolUse-contract outcome class this adapter emits.

    Mirrors the existing guards' exit contract:

    - ``ALLOW`` — exit 0, no message (the zero-collateral no-op; AC.WIRE.2).
    - ``WARN``  — exit 0 + ``systemMessage`` (surface the deliberate critique;
      AC.WIRE.1).
    - ``BLOCK`` — exit 2 + stderr (block toward re-think on a high-severity
      structural signal; AC.WIRE.1).
    """

    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


@dataclass(frozen=True)
class WireResult:
    """The live-wiring adapter's structured result for one PreToolUse turn.

    ``outcome`` is the PreToolUse-contract class; ``decision`` is the gate's
    decision (None on the default-OFF / safety-guard-short-circuit path —
    the gate was never consulted); ``loop_result`` is present iff the
    deliberate loop ran; ``message`` is the warn/block surface text.
    """

    outcome: WireOutcome
    decision: GateDecision | None
    loop_result: LoopResult | None
    message: str


def _layer_enabled(config: TurnConfig | None) -> bool:
    cfg = config or TurnConfig()
    return cfg.is_enabled()


def _pending_action_from_envelope(envelope: dict) -> PendingAction | None:
    """Build the structural :class:`PendingAction` from the PreToolUse
    envelope (``tool_name`` + ``tool_input``) — the SAME envelope the existing
    guards read. Reads ONLY structural fields (tool name, command/pattern
    string structure, target path/size); never a prompt/draft (D-SIT.3).
    """

    tool_name = (
        envelope.get("tool_name") or envelope.get("toolName") or ""
    )
    tool_input = envelope.get("tool_input") or envelope.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    command = str(
        tool_input.get("command")
        or tool_input.get("cmd")
        or ""
    )
    pattern = str(tool_input.get("pattern") or "")
    target_path = str(
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("filePath")
        or tool_input.get("glob")
        or ""
    )
    try:
        size = int(tool_input.get("target_size_bytes") or 0)
    except (TypeError, ValueError):
        size = 0

    if not (tool_name or command or pattern or target_path):
        return None

    return PendingAction(
        tool_name=str(tool_name),
        command=command,
        pattern=pattern,
        target_path=target_path,
        target_size_bytes=size,
    )


def _surface_message(decision: GateDecision, loop_result: LoopResult | None) -> str:
    trigs = ", ".join(t.value for t in decision.triggers)
    base = (
        f"deliberate-reasoning: about-to-act gate fired ({trigs}). "
        "Stop and re-think this action before running it."
    )
    if loop_result is not None and loop_result.revised:
        return base + f" Deliberate revision available: {loop_result.final_answer}"
    return base


def evaluate_pretooluse(
    envelope: dict,
    *,
    critic: Critic,
    result_ring: ToolResultRing | None = None,
    config: TurnConfig | None = None,
    safety_guard_blocked: bool = False,
) -> WireResult:
    """The live about-to-act entry-point — envelope -> gate -> loop.

    Behaviour (the AC.WIRE.* outcomes):

    - **Layer disabled (default-OFF):** return ``ALLOW`` with no gate
      consultation and no loop call — the zero-collateral no-op (AC.WIRE.2).
    - **A safety guard already blocked this action:** return ``ALLOW`` from
      THIS adapter's perspective without consulting the gate — the deliberate
      gate is a sibling classifier and must NOT un-block a safety-guard block
      (AC.WIRE.3). The caller's existing block stands; this adapter adds
      nothing.
    - **Enabled, no structural signal:** return ``ALLOW`` — the gate fires on
      zero normal turns; the loop is never invoked (AC.WIRE.2 zero-collateral).
    - **Enabled, structural signal fires:** run the slice-1 deliberate loop on
      the pending action's surfaced critique; return ``WARN`` (surface the
      re-think) or ``BLOCK`` (high-severity structural signal) — the live
      deliberate intervention (AC.WIRE.1 / AC.WIRE.OA).

    Fail-open by construction: any internal error is caught by the caller's
    hook wrapper (``run_pretooluse_hook``) and degraded to ALLOW.
    """

    # Default-OFF: the gate is not consulted, the loop never runs (AC.WIRE.2).
    if not _layer_enabled(config):
        return WireResult(WireOutcome.ALLOW, decision=None, loop_result=None, message="")

    # Compose-not-override (AC.WIRE.3): a safety-guard block short-circuits the
    # deliberate gate entirely — no point re-thinking an already-blocked
    # action, and this adapter must never un-block it.
    if safety_guard_blocked:
        return WireResult(WireOutcome.ALLOW, decision=None, loop_result=None, message="")

    action = _pending_action_from_envelope(envelope)
    signals = GateSignals(pending_action=action, result_ring=result_ring)
    decision = evaluate_gate(signals)

    if not decision.escalate:
        # Zero-collateral: a structurally-safe turn is an ALLOW no-op, the
        # loop is never invoked (AC.WIRE.2).
        return WireResult(
            WireOutcome.ALLOW, decision=decision, loop_result=None, message=""
        )

    # A structural signal fired — engage the slice-1 deliberate loop. The
    # "draft" the loop critiques is the pending action's surfaced description
    # (the about-to-act surface); the prompt frames the re-think. The loop's
    # shape is UNCHANGED (composes-with, not rewrite).
    pending_desc = _pending_action_description(action)
    loop_result = run_deliberate_loop(
        draft=pending_desc,
        prompt="An about-to-act gate fired on this pending action; re-think it.",
        critic=critic,
    )

    blocking = any(t in _BLOCKING_TRIGGERS for t in decision.triggers)
    outcome = WireOutcome.BLOCK if blocking else WireOutcome.WARN
    return WireResult(
        outcome=outcome,
        decision=decision,
        loop_result=loop_result,
        message=_surface_message(decision, loop_result),
    )


def _pending_action_description(action: PendingAction | None) -> str:
    if action is None:
        return "(no pending action)"
    parts = [f"tool={action.tool_name}"]
    if action.command:
        parts.append(f"command={action.command}")
    if action.pattern:
        parts.append(f"pattern={action.pattern}")
    if action.target_path:
        parts.append(f"target={action.target_path}")
    return " ".join(parts)


# --------------------------------------------------------------------------
# The PreToolUse hook process contract (exit codes + streams), mirroring
# in_thread_work_budget_guard.py. The actual `.claude/hooks/` registration in
# the live workspace is a SEPARATE owner-gated step (NOT done in this slice);
# this function is the harness-runnable surface the registration would call,
# and the AC.WIRE.* tests drive it with simulated envelopes.
# --------------------------------------------------------------------------


def run_pretooluse_hook(
    envelope: dict,
    *,
    critic: Critic,
    result_ring: ToolResultRing | None = None,
    config: TurnConfig | None = None,
    safety_guard_blocked: bool = False,
) -> tuple[int, str, str]:
    """Translate :func:`evaluate_pretooluse` into the PreToolUse exit contract.

    Returns ``(exit_code, stdout, stderr)``:

    - ALLOW -> ``(0, "", "")`` (the silent no-op).
    - WARN  -> ``(0, json_systemMessage, "")``.
    - BLOCK -> ``(2, "", stderr_feedback)``.

    Fail-open: ANY exception degrades to ``(0, "", "")`` (allow) — the hook can
    never wedge the session (the existing guards' invariant; AC.WIRE.2/.3).
    """

    import json

    try:
        result = evaluate_pretooluse(
            envelope,
            critic=critic,
            result_ring=result_ring,
            config=config,
            safety_guard_blocked=safety_guard_blocked,
        )
    except Exception:  # noqa: BLE001 — fail-open invariant
        return (0, "", "")

    if result.outcome is WireOutcome.ALLOW:
        return (0, "", "")
    if result.outcome is WireOutcome.WARN:
        return (0, json.dumps({"systemMessage": result.message}), "")
    # BLOCK
    return (2, "", result.message)


__all__ = [
    "WireOutcome",
    "WireResult",
    "evaluate_pretooluse",
    "run_pretooluse_hook",
    "ENABLE_ENV_VAR",
]
