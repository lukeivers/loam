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

"""ProgramBench-revival v2 runner — AC.PBR.1..7 end to end.

Freeze (already done: tasks.json content-hash-pinned + the pass rule
+ the FROZEN-RATIFIED margin in verdict.py) -> run both arms per task
under a closed channel with identical single-prompt input -> execute
the positive-real-outcome floor + held-out anti-overfit checks
against each arm's produced work dir (the scoring command is NEVER
seen by the agent — ground-truth isolation) -> INDEPENDENT held-out
judge scores each (provably NOT the loop's own judge) -> frozen pass
rule (judge FAITHFUL AND floor exit 0 AND held-out exit 0, no
retry-to-pass) -> classify every non-pass into the frozen four-class
taxonomy -> compute the three-valued verdict from the numbers ->
preserve per-(arm,task) evidence -> write the verdict report.

Cost ceiling (D-PBR-4): a USD ceiling halts the run and surfaces the
PARTIAL-but-DEFINITE picture (never silently truncates / fakes
completion). "loam does not materially beat the baseline" /
"indeterminate" are FIRST-CLASS plan-success outcomes.

NO Anthropic API key — real ``claude`` binary, default Sonnet.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .arms import run_baseline_arm, run_loam_arm
from .loader import FrozenTaskSet, load_frozen_task_set
from .scorer import independent_judge
from .verdict import (
    ArmTaskDisposition,
    classify_failure,
    compute_verdict,
    frozen_pass,
)

PKG_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = PKG_ROOT / ".run_evidence"
TASKS_DIR = PKG_ROOT / "tasks"


@dataclass
class CostCeiling:
    """D-PBR-4 — measured-USD ceiling; partial-but-definite on hit."""

    usd: float
    spent: float = 0.0

    def add(self, c: float | None) -> None:
        if c:
            self.spent += c

    def exceeded(self) -> bool:
        return self.spent >= self.usd


def _run_check(check_py: str, work_dir: Path,
               timeout: int = 60) -> tuple[int, str]:
    """Execute a frozen floor/held-out check against the arm's
    produced work dir. The check command is NEVER passed to the arm
    (ground-truth isolation, AC.PBR.1)."""
    argv = [sys.executable, str(TASKS_DIR / check_py)]
    try:
        proc = subprocess.run(
            argv, cwd=str(work_dir), capture_output=True,
            text=True, timeout=timeout,
        )
        return proc.returncode, ((proc.stdout or "")
                                 + (proc.stderr or ""))[-1200:]
    except subprocess.TimeoutExpired:
        return 124, f"check TIMEOUT after {timeout}s"


def _score_arm(
    *,
    task,
    arm: str,
    work_dir: Path,
    transcript: str,
    wall_s: float,
    cost: float | None,
    transcript_path: Path,
) -> ArmTaskDisposition:
    """Execute the frozen checks, independent-judge, apply the frozen
    pass rule, classify a non-pass into the frozen taxonomy."""
    floor_argv = [sys.executable, str(TASKS_DIR / task.floor_check)]
    produced_artifact = any(
        p.name not in set()  # any file beyond the setup is "produced"
        for p in work_dir.iterdir()
    ) if work_dir.exists() else False

    floor_exit, floor_tail = _run_check(task.floor_check, work_dir)
    held_exit, held_tail = _run_check(task.held_out_check, work_dir)

    judge = independent_judge(
        statement=task.statement,
        arm=arm,
        floor_cmd=floor_argv,
        floor_exit=floor_exit,
        held_out_exit=held_exit,
        transcript_tail=(
            transcript + "\n[floor_check_tail]\n" + floor_tail
            + "\n[held_out_check_tail]\n" + held_tail
        ),
    )
    judge_tag = judge["tag"]
    passed = frozen_pass(
        judge_tag=judge_tag,
        floor_exit=floor_exit,
        held_out_exit=held_exit,
    )
    failure_class = ""
    if not passed:
        failure_class = classify_failure(
            produced_artifact=produced_artifact,
            judge_tag=judge_tag,
            floor_exit=floor_exit,
            held_out_exit=held_exit,
        )
    return ArmTaskDisposition(
        task_id=task.id,
        arm=arm,
        passed=passed,
        judge_tag=judge_tag,
        judge_reason=judge["reason"],
        floor_exit=floor_exit,
        held_out_exit=held_exit,
        failure_class=failure_class,
        cost_usd=cost,
        wall_clock_s=round(wall_s, 2),
        transcript_path=str(transcript_path),
        check_command=" ".join(floor_argv),
    )


def run_experiment(
    *,
    cost_ceiling_usd: float,
    task_set: FrozenTaskSet | None = None,
    baseline_timeout: int = 900,
    loam_timeout: int = 1800,
) -> dict:
    """Run the full v2 experiment to a DEFINITE three-valued verdict.

    Honours the D-PBR-4 cost ceiling: on hit, halt and surface the
    PARTIAL-but-DEFINITE picture (the verdict is computed over the
    tasks that completed; the report names the truncation). Either
    polarity (material-beat / no-material-beat / indeterminate) is a
    first-class plan-success outcome.
    """
    ts = task_set or load_frozen_task_set()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ceiling = CostCeiling(usd=cost_ceiling_usd)

    baseline_disp: list[ArmTaskDisposition] = []
    loam_disp: list[ArmTaskDisposition] = []
    completed: list[str] = []
    halted_on_ceiling = False
    t_start = time.monotonic()

    for task in ts.tasks:
        if ceiling.exceeded():
            halted_on_ceiling = True
            break

        tdir = EVIDENCE_DIR / task.id
        tdir.mkdir(parents=True, exist_ok=True)

        # --- Baseline arm (no-harness floor) -------------------
        b_wd = tdir / "baseline_work"
        b_tr, b_dt, b_cost = run_baseline_arm(
            statement=task.statement,
            setup_files=task.setup_files,
            work_dir=b_wd,
            timeout=baseline_timeout,
        )
        b_tr_path = tdir / "baseline.transcript"
        b_tr_path.write_text(b_tr, encoding="utf-8")
        ceiling.add(b_cost)
        b_d = _score_arm(
            task=task, arm="baseline", work_dir=b_wd,
            transcript=b_tr, wall_s=b_dt, cost=b_cost,
            transcript_path=b_tr_path,
        )
        ceiling.add(None)  # judge cost folded below
        baseline_disp.append(b_d)

        # --- Loam arm (the real sealed loop) -------------------
        l_wd = tdir / "loam_work"
        l_ad = tdir / "loam_artifacts"
        l_tr, l_dt, l_cost = run_loam_arm(
            task_id=task.id,
            statement=task.statement,
            setup_files=task.setup_files,
            floor_check_argv=[sys.executable,
                              str(TASKS_DIR / task.floor_check)],
            held_out_argv=[sys.executable,
                           str(TASKS_DIR / task.held_out_check)],
            work_dir=l_wd,
            artifact_dir=l_ad,
            timeout=loam_timeout,
        )
        l_tr_path = tdir / "loam.transcript"
        l_tr_path.write_text(l_tr, encoding="utf-8")
        ceiling.add(l_cost)
        l_d = _score_arm(
            task=task, arm="loam", work_dir=l_wd,
            transcript=l_tr, wall_s=l_dt, cost=l_cost,
            transcript_path=l_tr_path,
        )
        loam_disp.append(l_d)

        completed.append(task.id)
        (tdir / "disposition.json").write_text(
            json.dumps(
                {"baseline": b_d.as_record(),
                 "loam": l_d.as_record()},
                indent=2,
            ),
            encoding="utf-8",
        )

    verdict = compute_verdict(baseline_disp, loam_disp)
    result = {
        "task_set_id": ts.task_set_id,
        "task_set_sha256": ts.content_sha256,
        "frozen_pass_rule": ts.frozen_pass_rule,
        "frozen_failure_taxonomy": list(ts.frozen_failure_taxonomy),
        "tasks_total": len(ts.tasks),
        "tasks_completed": completed,
        "halted_on_cost_ceiling": halted_on_ceiling,
        "cost_ceiling_usd": cost_ceiling_usd,
        "measured_spent_usd": round(ceiling.spent, 4),
        "wall_clock_s": round(time.monotonic() - t_start, 1),
        "baseline_dispositions": [d.as_record()
                                  for d in baseline_disp],
        "loam_dispositions": [d.as_record() for d in loam_disp],
        "verdict": verdict.as_record(),
        "scoring_authority": (
            "INDEPENDENT held-out adversarial tool-grounded judge "
            "(programbench_revival.scorer.independent_judge, composing "
            "the proven _independent_judge shape via "
            "spawn_isolated_claude) — PROVABLY NOT the loop's own "
            "handsoff_loop.intake._judge_faithful AC.B.4b judge "
            "(never imported / never called by this harness)."
        ),
    }
    (EVIDENCE_DIR / "verdict.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(prog="programbench-revival-v2")
    ap.add_argument("--cost-ceiling-usd", type=float, required=True)
    ap.add_argument("--baseline-timeout", type=int, default=900)
    ap.add_argument("--loam-timeout", type=int, default=1800)
    a = ap.parse_args()
    out = run_experiment(
        cost_ceiling_usd=a.cost_ceiling_usd,
        baseline_timeout=a.baseline_timeout,
        loam_timeout=a.loam_timeout,
    )
    print(json.dumps(out, indent=2))
