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

"""AC.PBR.1 — two arms defined, isolated, identically tasked under a
closed (no-answer) channel (zero-interaction parity, D-PBR-6).

Outcome under test (not method): there are exactly two arms; both
receive the IDENTICAL single plain-language statement under a closed
channel (no simulated/scripted/stand-in user); each arm's per-task
run is environment-isolated (fresh work dir) and isolated from the
ground-truth check (the agent never sees the floor/held-out check).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "programbench-revival" / "src")
)


def test_AC_PBR_1_exactly_two_arms_identical_single_prompt() -> None:
    """The baseline driver and the loam driver each format the SAME
    single directive from the user's plain-language statement and
    nothing else (input parity); neither arm's directive carries the
    frozen check / ground-truth (ground-truth isolation)."""
    from programbench_revival import arms

    # exactly two arm entry points
    assert hasattr(arms, "run_baseline_arm")
    assert hasattr(arms, "run_loam_arm")

    stmt = "do the real thing the user asked for"
    directive = arms._ARM_DIRECTIVE.format(statement=stmt)
    # the single prompt carries ONLY the user's sentence + the
    # work-dir contract — no clarifying-question channel
    assert stmt in directive
    assert "NO channel to ask them anything" in directive
    assert "you will get no answer" in directive
    # ground-truth isolation: the directive must not mention the
    # floor/held-out check or any scoring command
    low = directive.lower()
    assert "floor_check" not in low
    assert "held_out" not in low
    assert "check command" not in low


def test_AC_PBR_1_loam_arm_drives_real_cli_closed_channel() -> None:
    """The loam arm drives the REAL handsoff-loop CLI with --frozen
    (no --from-intake live question; closed channel) and does NOT use
    the cooperative-user simulation (D-PBR-6 — removed as the
    loam-arm model)."""
    src = (ROOT / "framework" / "tools" / "programbench-revival"
           / "src" / "programbench_revival" / "arms.py").read_text()
    # invokes the real persona-invocable CLI module
    assert "handsoff_loop.cli" in src
    assert '"run"' in src and '"--frozen"' in src
    # closed channel: no cooperative-user / agrees-to-milestone sim
    assert "_cooperative_user" not in src
    assert "_agrees_to_milestone" not in src
    # the loop's done is decided by EXECUTING the frozen check
    # (check_argv = the task's real floor/held-out checks)
    assert "check_argv" in src and "held_out_argv" in src


def test_AC_PBR_1_per_task_environment_isolation() -> None:
    """Each arm's per-task run gets a FRESH work dir (no residual
    state across tasks/arms) — the runner gives every task its own
    evidence subdir and the arm drivers rmtree+recreate the work
    dir."""
    arms_src = (ROOT / "framework" / "tools" / "programbench-revival"
                / "src" / "programbench_revival"
                / "arms.py").read_text()
    assert "shutil.rmtree(work_dir)" in arms_src
    runner_src = (ROOT / "framework" / "tools"
                  / "programbench-revival" / "src"
                  / "programbench_revival" / "runner.py").read_text()
    # per-task evidence subdir keyed by task id (no cross-task state)
    assert "EVIDENCE_DIR / task.id" in runner_src
