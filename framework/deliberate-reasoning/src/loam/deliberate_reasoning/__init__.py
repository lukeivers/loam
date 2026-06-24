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

"""loam-deliberate-reasoning — a gated, evidence-bound deliberate-reasoning
layer over the inference engine (slice 1).

Implements docs/plans/metacognitive-gate-reentrant-loop-slice1.md:
the metacognitive **gate** (D-MGRL.1, D-MGRL.4) + the **evidence-bound
re-entrant loop** with a no-degradation guard (D-MGRL.2), default-OFF and
gated (D-MGRL.5). The pre-registered experiment harness (D-MGRL.3) lives
under ``experiment/``.

Slice 3 (situation triggers + live-wiring) extends this with the STRUCTURAL
situation-signal substrate (``signals``), the live PreToolUse wiring adapter
(``wiring``), and the default-OFF option-(ii) self-assessment escalation seam
(``escalation``). The slice-1 ``gate``/``loop``/``turn`` spine is composed-with,
unchanged in shape.

Public surface:

- ``gate`` — :func:`evaluate_gate`, :class:`GateDecision`, :class:`GateSignals`,
  :class:`Trigger` (now driven by the structural signals).
- ``loop`` — :func:`run_deliberate_loop`, :class:`LoopResult`.
- ``turn`` — :func:`process_turn` (the production entry-point) and
  :class:`TurnConfig` (the default-OFF switch, AC.MGRL.7 / AC.WIRE.2).
- ``signals`` (slice 3) — :func:`detect_situation_signals`,
  :class:`PendingAction`, :class:`ToolResultRing`, :class:`SituationSignal`
  (the structural floor; AC.TRIG.*).
- ``wiring`` (slice 3) — :func:`evaluate_pretooluse`, :func:`run_pretooluse_hook`
  (the live about-to-act path; AC.WIRE.1/.2/.3/.OA).
- ``escalation`` (slice 3) — :func:`make_self_assessment_escalation`,
  :func:`escalation_enabled` (the default-OFF option-(ii) seam; AC.WIRE.4).
"""

from __future__ import annotations

from .gate import GateDecision, GateSignals, Trigger, evaluate_gate
from .loop import LoopResult, run_deliberate_loop
from .turn import TurnConfig, TurnResult, process_turn
from .signals import (
    PendingAction,
    SituationSignal,
    ResultClass,
    ToolCallRecord,
    ToolResultRing,
    detect_situation_signals,
)
from .wiring import (
    WireOutcome,
    WireResult,
    evaluate_pretooluse,
    run_pretooluse_hook,
)
from .escalation import (
    ESCALATION_ENV_VAR,
    SelfAssessment,
    escalation_enabled,
    make_self_assessment_escalation,
)

__all__ = [
    # slice-1 spine (composed-with, unchanged in shape)
    "GateDecision",
    "GateSignals",
    "Trigger",
    "evaluate_gate",
    "LoopResult",
    "run_deliberate_loop",
    "TurnConfig",
    "TurnResult",
    "process_turn",
    # slice-3 situation-signal substrate (AC.TRIG.*)
    "PendingAction",
    "SituationSignal",
    "ResultClass",
    "ToolCallRecord",
    "ToolResultRing",
    "detect_situation_signals",
    # slice-3 live-wiring (AC.WIRE.1/.2/.3/.OA)
    "WireOutcome",
    "WireResult",
    "evaluate_pretooluse",
    "run_pretooluse_hook",
    # slice-3 option-(ii) escalation seam (AC.WIRE.4)
    "ESCALATION_ENV_VAR",
    "SelfAssessment",
    "escalation_enabled",
    "make_self_assessment_escalation",
]
