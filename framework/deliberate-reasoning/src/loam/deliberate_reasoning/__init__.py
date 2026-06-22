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

Public surface:

- ``gate`` — :func:`evaluate_gate`, :class:`GateDecision`, :class:`Trigger`.
- ``loop`` — :func:`run_deliberate_loop`, :class:`LoopResult`.
- ``turn`` — :func:`process_turn` (the production entry-point AC.MGRL.OA
  fires through) and :class:`TurnConfig` (the default-OFF switch, AC.MGRL.7).
"""

from __future__ import annotations

from .gate import GateDecision, Trigger, evaluate_gate
from .loop import LoopResult, run_deliberate_loop
from .turn import TurnConfig, TurnResult, process_turn

__all__ = [
    "GateDecision",
    "Trigger",
    "evaluate_gate",
    "LoopResult",
    "run_deliberate_loop",
    "TurnConfig",
    "TurnResult",
    "process_turn",
]
