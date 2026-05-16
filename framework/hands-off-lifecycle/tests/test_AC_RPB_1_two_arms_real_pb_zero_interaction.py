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
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.RPB.1 — two arms, isolated, identically tasked on the SAME real
public ProgramBench subset, zero-interaction parity, no simulated
user (REUSED v2 invariant, real-PB-bound).

Deterministic structural assertion (no real claude spawn): the two
arm drivers are the REUSED v2 arms.py (baseline = ONE bare claude -p
via the mandated isolation surface; loam = the REAL handsoff-loop CLI
--frozen, closed channel); each arm receives ONLY the plain-language
statement; neither arm ever sees the upstream test suite / scoring
command (ground-truth isolation); no simulated/scripted user is wired.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
V2 = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(REALPB / "src"))
sys.path.insert(0, str(V2 / "src"))


def test_AC_RPB_1_two_arms_real_pb_zero_interaction_no_sim_user() -> None:
    # the runner REUSES v2's arm drivers read-only (Lens 1 / D-RPB-7)
    from programbench_revival_realpb import runner
    from programbench_revival.arms import (
        run_baseline_arm,
        run_loam_arm,
    )

    assert runner.run_baseline_arm is run_baseline_arm
    assert runner.run_loam_arm is run_loam_arm

    # baseline arm = ONE bare claude -p through the mandated isolation
    # surface (no hand-rolled subprocess.run(["claude",...]))
    arms_src = inspect.getsource(sys.modules[
        "programbench_revival.arms"])
    assert "spawn_isolated_claude" in arms_src
    assert "ONE bare ``claude -p``" in arms_src

    # the ONLY thing an arm receives is the plain-language statement
    # under a CLOSED no-answer channel (zero-interaction parity)
    assert "There is NO channel to ask them anything" in arms_src
    assert "closed channel" in arms_src.lower()

    # loam arm = the REAL handsoff-loop CLI --frozen (no mock, no
    # cooperative-user simulation — the v2 D-PBR-6 / D-RPB-6 removal)
    assert "handsoff_loop.cli" in arms_src
    assert "cooperative-user simulation is NOT used" in arms_src

    # each (arm,task) is environment-isolated (the reused v2 arms.py
    # wipes + recreates a fresh per-(arm,task) work dir) and the
    # scoring command is NEVER passed to the arm (ground-truth
    # isolation) — assert the real invariant, not exact prose:
    runner_src = inspect.getsource(runner)
    assert "ground-truth isolation" in runner_src
    # the runner states the agent never sees the upstream
    # suite/scoring command (wording may line-wrap — assert the
    # property, normalised over whitespace)
    norm = " ".join(runner_src.split())
    assert "agent NEVER saw the upstream test suite" in norm or \
        "NEVER saw the upstream test suite / scoring command" in norm
    # the reused v2 arms.py wipes the work dir fresh per (arm,task)
    assert "shutil.rmtree(work_dir)" in arms_src
    # the arm directive carries ONLY the user statement — the frozen
    # check / ground-truth is never put in the arm's prompt
    assert "NO frozen check" in arms_src
    assert "NO ground-truth" in arms_src

    # the loop's frozen check is the lightweight STRUCTURAL floor; the
    # REAL upstream eval + the independent judge are the EXTERNAL
    # scoring authority (the agent never sees them)
    assert runner.STRUCTURAL_FLOOR.name == \
        "realpb_structural_floor.py"
    floor_src = runner.STRUCTURAL_FLOOR.read_text()
    floor_norm = " ".join(floor_src.split())
    assert "NOT the scoring authority" in floor_norm
    assert "never seen by either arm" in floor_norm.lower()
    # the structural floor is loop-internal only; the REAL upstream
    # eval + the independent judge are the EXTERNAL authority
    assert "REAL upstream programbench eval" in floor_norm
    assert "EXTERNAL scoring authority" in floor_norm
