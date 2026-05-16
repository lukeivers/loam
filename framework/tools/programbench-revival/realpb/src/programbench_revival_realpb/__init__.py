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

"""ProgramBench-revival (REAL public ProgramBench) — the real-benchmark
measurement harness.

Plan: docs/plans/programbench-revival-real-pb.md (AC.RPB.1..7).

Does the real sealed v0.11.0 hands-off loop (the loam arm) MATERIALLY
OUTPERFORM a bare ``claude -p`` baseline (the no-harness floor arm) at
executing the REAL public ProgramBench task set (the real linux/amd64
``programbench/<owner>_1776_<repo>.<sha>:task`` images + the real
HuggingFace ``ProgramBench-Tests`` blobs, scored by the REAL upstream
``programbench eval`` as the deterministic GRADED floor signal) — that
signal GROUNDED by the INDEPENDENT held-out adversarial tool-grounded
judge, PROVABLY NOT the loop's own intake.py AC.B.4b judge.

"loam does not materially beat the baseline on the real benchmark" is
a FIRST-CLASS plan-success outcome (AC.RPB.7) — reported straight,
NEVER retried to green, NEVER the FROZEN margin weakened.

REUSE (Lens 1 — does NOT re-implement, does NOT re-derive):
  * v2's ``programbench_revival.arms`` (run_baseline_arm /
    run_loam_arm — both arm drivers, isolation + env correct) read
    only.
  * v2's ``programbench_revival.scorer.independent_judge`` (composing
    the proven ``_independent_judge`` shape via
    ``spawn_isolated_claude``) read only.
  * the existing pos3 ``programbench-derivative`` real-PB PLUMBING
    (instance-id map, ``programbench eval`` invocation form,
    ``submission.tar.gz`` packaging, HF blob resolution, the proven
    amd64-emulation runnability) read only.

FIX (the two named v2 defects — F2 §10.1 / §10.2):
  1. TASK-SOURCE MISDIAGNOSIS — the task set IS the REAL public
     ProgramBench (digest-pinned real ``:task`` images + real HF
     blobs, scored by the REAL upstream ``programbench eval``), NOT a
     hand-curated substitute. The builder live-re-verified the host
     is real-PB-runnable (NOT inherited from v2's record).
  2. BINARY-VERDICT-RULE DEGENERACY (the v2 task-#44 / PB3 defect) —
     the real upstream signal is GRADED (``score = n_resolved /
     len(test_results)``, ``compile_failed`` ⇒ 0). The verdict rule
     is re-authored over a FROZEN per-task floor threshold over the
     graded score PLUS a FROZEN ``k_min >= 2`` small-k floor on the
     baseline-miss denominator that FORCES verdict (c) indeterminate
     (machine-stated reason) whenever the baseline-miss count is
     ``< k_min`` — a degenerate / near-degenerate denominator can
     NEVER read as a determinate loss or win.

NO Anthropic API key — real ``claude`` binary, default Sonnet; every
``claude`` spawn (both arms + the independent judge) routes through
the sealed ``loam_spawn_isolation.spawn_isolated_claude`` surface
(reused via the v2 arms/scorer modules).
"""

from .loader import RealPBTask, RealPBTaskSet, load_frozen_realpb_set
from .verdict import (
    THREE_VALUED,
    FROZEN_FAILURE_TAXONOMY,
    FROZEN_MARGIN_TEXT,
    K_MIN,
    RealPBArmDisposition,
    classify_realpb_failure,
    compute_realpb_verdict,
    realpb_frozen_pass,
)

__all__ = [
    "RealPBTask",
    "RealPBTaskSet",
    "load_frozen_realpb_set",
    "THREE_VALUED",
    "FROZEN_FAILURE_TAXONOMY",
    "FROZEN_MARGIN_TEXT",
    "K_MIN",
    "RealPBArmDisposition",
    "classify_realpb_failure",
    "compute_realpb_verdict",
    "realpb_frozen_pass",
]
