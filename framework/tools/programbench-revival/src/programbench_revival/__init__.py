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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""ProgramBench-revival v2 — the measurement harness.

Plan: docs/plans/programbench-revival-v2.md (AC.PBR.1..7).

Does the real sealed v0.11.0 hands-off loop (the loam arm) MATERIALLY
OUTPERFORM a bare ``claude -p`` baseline (the no-harness floor arm) at
executing a frozen set of NON-SUBJECTIVE ProgramBench-class hands-off
tasks stated as a non-technical user would state them — scored by the
INDEPENDENT held-out adversarial tool-grounded judge, PROVABLY NOT the
loop's own intake.py AC.B.4b faithfulness judge.

"loam does not materially beat the baseline" is a FIRST-CLASS
plan-success outcome (AC.PBR.7) — reported straight, NEVER retried to
green, NEVER the margin weakened.

Composes (Lens 1 — does NOT re-implement):
  * ``handsoff_loop_goal_refine_reharden._independent_judge`` — the
    proven held-out adversarial tool-grounded scoring authority.
  * ``loam_spawn_isolation.spawn_isolated_claude`` — the MANDATED
    isolation surface for EVERY ``claude`` spawn (both arms + judge).
The independent judge + isolation surface are CONSUMED read-only.

NO Anthropic API key — real ``claude`` binary, default Sonnet.
"""

from .loader import FrozenTaskSet, load_frozen_task_set
from .verdict import (
    THREE_VALUED,
    FailureClass,
    compute_verdict,
    frozen_pass,
)

__all__ = [
    "FrozenTaskSet",
    "load_frozen_task_set",
    "compute_verdict",
    "frozen_pass",
    "FailureClass",
    "THREE_VALUED",
]
