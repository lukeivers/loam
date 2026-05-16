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

"""ProgramBench-revival REAL-public-PB runner — AC.RPB.1..7 end to
end.

Freeze (already done: tasks.json content-hash-pinned + per-task floor
theta + the frozen pass rule + the FROZEN-RATIFIED margin + the
k_min>=2 small-k floor in verdict.py) -> run BOTH arms per task under
a CLOSED channel with IDENTICAL single-prompt input (REUSED v2
arms.py read-only, Lens 1) -> package each arm's work dir into the
upstream submission.tar.gz shape -> run the REAL upstream
`programbench eval` under amd64 emulation (REUSED real-PB plumbing
read-only, D-RPB-7) for the GRADED positive-real-outcome floor signal
-> the INDEPENDENT held-out judge (REUSED v2 scorer.py read-only,
composing the proven _independent_judge via spawn_isolated_claude —
PROVABLY NOT the loop's own judge) grounded in the real *.eval.json +
the frozen theta -> frozen pass rule (judge FAITHFUL AND graded score
>= theta AND held-out binding) -> classify every non-pass into the
frozen four-class taxonomy -> compute the three-valued verdict from
the numbers WITH the k_min small-k floor -> preserve per-(arm,task)
evidence incl. the REAL *.eval.json -> write the verdict report.

Cost + WALL-CLOCK ceiling (D-RPB-4): a measured-USD AND measured-
wall-clock ceiling halts the run and surfaces the PARTIAL-but-DEFINITE
picture (never silently truncates / downscopes / fakes completion —
§8.6). "loam does not materially beat the baseline on the real
benchmark" / "indeterminate" are FIRST-CLASS plan-success outcomes.

NO Anthropic API key — real `claude` binary, default Sonnet; every
`claude` spawn (both arms + the independent judge) routes through the
sealed loam_spawn_isolation.spawn_isolated_claude surface via the
REUSED v2 arms/scorer modules (the un-isolated-spawn hard-error
guard, the Telegram-death #5 vector).
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# --- REUSE the v2 surviving spine read-only (Lens 1 / D-RPB-7): the
# arm drivers + the independent judge live in the sibling v2 package
# `programbench_revival` (NOT re-authored here). Reach its src on
# sys.path; do NOT modify it.
_REALPB_PKG_ROOT = Path(__file__).resolve().parents[2]      # realpb/
_V2_SRC = _REALPB_PKG_ROOT.parent / "src"                   # v2 src/
if str(_V2_SRC) not in sys.path:
    sys.path.insert(0, str(_V2_SRC))

from programbench_revival.arms import (  # noqa: E402
    run_baseline_arm,
    run_loam_arm,
)
from programbench_revival.scorer import independent_judge  # noqa: E402

from .loader import (  # noqa: E402
    RealPBTaskSet,
    load_frozen_realpb_set,
)
from .upstream_eval import (  # noqa: E402
    package_submission,
    run_upstream_eval,
)
from .verdict import (  # noqa: E402
    RealPBArmDisposition,
    classify_realpb_failure,
    compute_realpb_verdict,
    realpb_frozen_pass,
)

PKG_ROOT = _REALPB_PKG_ROOT
EVIDENCE_DIR = PKG_ROOT / ".run_evidence"
TASKS_DIR = PKG_ROOT / "tasks"
STRUCTURAL_FLOOR = TASKS_DIR / "realpb_structural_floor.py"


@dataclass
class CostWallCeiling:
    """D-RPB-4 — measured-USD AND measured-wall-clock ceiling;
    partial-but-definite on hit (§8.6 — never silently truncates)."""

    usd: float
    wall_s: float
    spent_usd: float = 0.0
    started_monotonic: float = 0.0

    def add_cost(self, c: float | None) -> None:
        if c:
            self.spent_usd += c

    def elapsed_s(self) -> float:
        return time.monotonic() - self.started_monotonic

    def exceeded(self) -> tuple[bool, str]:
        if self.spent_usd >= self.usd:
            return True, (
                f"measured dollar ceiling reached "
                f"(${self.spent_usd:.4f} >= ${self.usd:.2f})"
            )
        if self.elapsed_s() >= self.wall_s:
            return True, (
                f"measured wall-clock ceiling reached "
                f"({self.elapsed_s():.0f}s >= {self.wall_s:.0f}s)"
            )
        return False, ""


def _score_arm_realpb(
    *,
    task,
    arm: str,
    work_dir: Path,
    transcript: str,
    agent_wall_s: float,
    cost: float | None,
    transcript_path: Path,
    run_dir: Path,
    upstream_eval_dir: Path | None,
    eval_timeout: int,
) -> RealPBArmDisposition:
    """Package the arm's submission, run the REAL upstream
    `programbench eval` (the GRADED positive-real-outcome floor),
    independent-judge it GROUNDED in the real *.eval.json + the frozen
    theta, apply the frozen pass rule over the graded score, classify
    a non-pass into the frozen taxonomy. The agent NEVER saw the
    upstream test suite / scoring command (ground-truth isolation,
    AC.RPB.1)."""
    sub_tar = run_dir / task.instance_id / "submission.tar.gz"
    produced = package_submission(Path(work_dir), sub_tar)

    if not produced:
        # No submission at all — did-not-produce-output. We still run
        # the real eval form for evidence completeness, but an empty
        # work dir compiles_failed / scores 0.0 by construction.
        ue = run_upstream_eval(
            instance_id=task.instance_id,
            filter_regex=task.filter_regex,
            submission_tar=sub_tar,
            run_dir=run_dir,
            upstream_eval_dir=upstream_eval_dir,
            timeout=eval_timeout,
        )
        ue.produced_submission = False
    else:
        ue = run_upstream_eval(
            instance_id=task.instance_id,
            filter_regex=task.filter_regex,
            submission_tar=sub_tar,
            run_dir=run_dir,
            upstream_eval_dir=upstream_eval_dir,
            timeout=eval_timeout,
        )

    # held-out anti-overfit binding: the REAL upstream test suite
    # includes the held-out behavioural branches the agent never saw
    # (the agent only ever received the plain-language statement —
    # AC.RPB.1 ground-truth isolation). The graded upstream score IS
    # measured over those unseen branches, so a non-zero score that
    # clears theta inherently survived the unseen-branch binding;
    # held_out_clean is True unless the upstream eval itself errored
    # in a way that means the held-out signal is unavailable.
    held_out_clean = ue.error_code is None or (
        ue.n_tests > 0 and ue.error_code not in (
            "eval_json_absent",
        )
    )

    judge = independent_judge(
        statement=task.statement,
        arm=arm,
        floor_cmd=[
            "REAL-upstream-programbench-eval",
            task.instance_id,
            f"graded-score={ue.score}",
            f"n_resolved={ue.n_resolved}/{ue.n_tests}",
            f"error_code={ue.error_code}",
            f"frozen-floor-theta={task.floor_theta}",
        ],
        floor_exit=(0 if ue.score >= task.floor_theta else 1),
        held_out_exit=(0 if held_out_clean else 1),
        transcript_tail=(
            transcript
            + "\n[REAL upstream programbench eval result]\n"
            + json.dumps({
                "instance_id": ue.instance_id,
                "graded_score": ue.score,
                "n_resolved": ue.n_resolved,
                "n_tests": ue.n_tests,
                "error_code": ue.error_code,
                "frozen_floor_theta": task.floor_theta,
                "eval_emulation_wall_clock_s":
                    ue.eval_emulation_wall_clock_s,
            }, indent=2)
            + "\n[upstream eval stdout tail]\n"
            + ue.raw_stdout_tail
        ),
    )
    judge_tag = judge["tag"]

    passed = realpb_frozen_pass(
        judge_tag=judge_tag,
        upstream_score=ue.score,
        floor_theta=task.floor_theta,
        held_out_clean=held_out_clean,
    )
    failure_class = ""
    if not passed:
        failure_class = classify_realpb_failure(
            produced_submission=ue.produced_submission,
            judge_tag=judge_tag,
            upstream_score=ue.score,
            upstream_error_code=ue.error_code,
            floor_theta=task.floor_theta,
        )
    return RealPBArmDisposition(
        task_id=task.id,
        instance_id=task.instance_id,
        arm=arm,
        passed=passed,
        judge_tag=judge_tag,
        judge_reason=judge["reason"],
        upstream_score=ue.score,
        upstream_n_resolved=ue.n_resolved,
        upstream_n_tests=ue.n_tests,
        upstream_error_code=ue.error_code,
        floor_theta=task.floor_theta,
        held_out_clean=held_out_clean,
        failure_class=failure_class,
        cost_usd=cost,
        agent_wall_clock_s=round(agent_wall_s, 2),
        eval_emulation_wall_clock_s=ue.eval_emulation_wall_clock_s,
        transcript_path=str(transcript_path),
        eval_json_path=ue.eval_json_path,
    )


def run_realpb_experiment(
    *,
    cost_ceiling_usd: float,
    wall_ceiling_s: float,
    task_set: RealPBTaskSet | None = None,
    baseline_timeout: int = 1800,
    loam_timeout: int = 3600,
    eval_timeout: int = 5400,
    upstream_eval_dir: Path | None = None,
) -> dict:
    """Run the full REAL-public-ProgramBench experiment to a DEFINITE
    three-valued verdict.

    Honours the D-RPB-4 measured cost + wall-clock ceiling: on hit,
    HALT and surface the PARTIAL-but-DEFINITE picture (the verdict is
    computed over the tasks that completed; the report names the
    truncation — §8.6, never silently truncates / downscopes). Any
    polarity (material-beat / no-material-beat / indeterminate, incl.
    the k_min-forced indeterminate) is a first-class plan-success
    outcome.
    """
    ts = task_set or load_frozen_realpb_set()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ceiling = CostWallCeiling(
        usd=cost_ceiling_usd, wall_s=wall_ceiling_s,
        started_monotonic=time.monotonic(),
    )

    baseline_disp: list[RealPBArmDisposition] = []
    loam_disp: list[RealPBArmDisposition] = []
    completed: list[str] = []
    halted = False
    halt_reason = ""
    t_start = time.monotonic()

    for task in ts.tasks:
        hit, why = ceiling.exceeded()
        if hit:
            halted = True
            halt_reason = why
            break

        tdir = EVIDENCE_DIR / task.id
        tdir.mkdir(parents=True, exist_ok=True)
        run_dir = tdir / "eval_run"

        # --- Baseline arm (no-harness floor) — REUSED v2 arms.py.
        b_wd = tdir / "baseline_work"
        b_tr, b_dt, b_cost = run_baseline_arm(
            statement=task.statement,
            setup_files=task.setup_files,
            work_dir=b_wd,
            timeout=baseline_timeout,
        )
        b_tr_path = tdir / "baseline.transcript"
        b_tr_path.write_text(b_tr, encoding="utf-8")
        ceiling.add_cost(b_cost)
        b_d = _score_arm_realpb(
            task=task, arm="baseline", work_dir=b_wd,
            transcript=b_tr, agent_wall_s=b_dt, cost=b_cost,
            transcript_path=b_tr_path,
            run_dir=run_dir / "baseline",
            upstream_eval_dir=upstream_eval_dir,
            eval_timeout=eval_timeout,
        )
        baseline_disp.append(b_d)

        # --- Loam arm (the REAL sealed loop) — REUSED v2 arms.py.
        # The loop's frozen check_argv is the lightweight STRUCTURAL
        # floor (loop-internal done-signal); the REAL upstream eval +
        # the independent judge are the EXTERNAL scoring authority
        # (ground-truth isolation, AC.RPB.1 / AC.RPB.3 / AC.RPB.4).
        l_wd = tdir / "loam_work"
        l_ad = tdir / "loam_artifacts"
        l_tr, l_dt, l_cost = run_loam_arm(
            task_id=task.id,
            statement=task.statement,
            setup_files=task.setup_files,
            floor_check_argv=[sys.executable, str(STRUCTURAL_FLOOR)],
            held_out_argv=[sys.executable, str(STRUCTURAL_FLOOR)],
            work_dir=l_wd,
            artifact_dir=l_ad,
            timeout=loam_timeout,
        )
        l_tr_path = tdir / "loam.transcript"
        l_tr_path.write_text(l_tr, encoding="utf-8")
        ceiling.add_cost(l_cost)
        l_d = _score_arm_realpb(
            task=task, arm="loam", work_dir=l_wd,
            transcript=l_tr, agent_wall_s=l_dt, cost=l_cost,
            transcript_path=l_tr_path,
            run_dir=run_dir / "loam",
            upstream_eval_dir=upstream_eval_dir,
            eval_timeout=eval_timeout,
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

    verdict = compute_realpb_verdict(
        baseline_disp, loam_disp, k_min=ts.k_min,
    )
    result = {
        "task_set_id": ts.task_set_id,
        "is_real_public_programbench": ts.is_real_public_programbench,
        "task_set_sha256": ts.content_sha256,
        "hf_dataset": ts.hf_dataset,
        "hf_revision_snapshot": ts.hf_revision_snapshot,
        "upstream_eval": ts.upstream_eval,
        "frozen_pass_rule": ts.frozen_pass_rule,
        "frozen_floor_theta_default": ts.frozen_floor_theta_default,
        "frozen_k_min": ts.k_min,
        "frozen_failure_taxonomy":
            list(ts.frozen_failure_taxonomy),
        "tasks_total": len(ts.tasks),
        "tasks_completed": completed,
        "halted_on_ceiling": halted,
        "halt_reason": halt_reason,
        "cost_ceiling_usd": cost_ceiling_usd,
        "wall_ceiling_s": wall_ceiling_s,
        "measured_spent_usd": round(ceiling.spent_usd, 4),
        "measured_total_wall_clock_s":
            round(time.monotonic() - t_start, 1),
        "baseline_dispositions":
            [d.as_record() for d in baseline_disp],
        "loam_dispositions": [d.as_record() for d in loam_disp],
        "verdict": verdict.as_record(),
        "v2_substitute_relationship": (
            "This is the REAL public ProgramBench measurement. It is "
            "a DIFFERENT, HARDER artefact than the v2 6-task "
            "substitute (slug `programbench-revival-v2`, task_set_id "
            "`programbench-revival-v2-honest-scope-6task`). The v2 "
            "substitute result MUST NOT be cited as a real-PB result; "
            "it remains a valid honest-scope record FOR ITS TIME, "
            "preserved un-extended. This cycle supersedes ONLY v2's "
            "task-source decision (the host-block premise is "
            "Tier-0-refuted by the builder's own live recheck), NOT "
            "v2's invariant spine."
        ),
        "scoring_authority": (
            "INDEPENDENT held-out adversarial tool-grounded judge "
            "(programbench_revival.scorer.independent_judge, composing "
            "the proven _independent_judge shape via "
            "spawn_isolated_claude), GROUNDED in the REAL upstream "
            "`programbench eval` *.eval.json graded score + the "
            "frozen per-task floor theta — PROVABLY NOT the loop's "
            "own handsoff_loop.intake._judge_faithful AC.B.4b judge "
            "(never imported / never called by this harness)."
        ),
    }
    (EVIDENCE_DIR / "verdict.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        prog="programbench-revival-real-pb")
    ap.add_argument("--cost-ceiling-usd", type=float, required=True)
    ap.add_argument("--wall-ceiling-s", type=float, required=True)
    ap.add_argument("--baseline-timeout", type=int, default=1800)
    ap.add_argument("--loam-timeout", type=int, default=3600)
    ap.add_argument("--eval-timeout", type=int, default=5400)
    a = ap.parse_args()
    out = run_realpb_experiment(
        cost_ceiling_usd=a.cost_ceiling_usd,
        wall_ceiling_s=a.wall_ceiling_s,
        baseline_timeout=a.baseline_timeout,
        loam_timeout=a.loam_timeout,
        eval_timeout=a.eval_timeout,
    )
    print(json.dumps(out, indent=2))
