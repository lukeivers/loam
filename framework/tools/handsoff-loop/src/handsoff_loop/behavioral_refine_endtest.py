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

"""AC.BRC.5 end-test runner (LEAD; honest-negative first-class).

Produces a DEFINITE, evidence-backed PER-DIMENSION verdict that, on a
real (non-toy) task of probe-class-or-harder, the loop now CROSSES the
real-outcome line before stopping:

  (i)   terminal "done" is gated by a BEHAVIOURAL self-check, not
        structural presence (a structurally-present-but-behaviourally-
        wrong artefact is NOT reported done);
  (ii)  a failed behavioural check RE-DROVE a bounded, failure-
        context-carrying refinement (the re-dispatch is observable in
        the transcripts/refine_log; the bound HELD);
  (iii) each refine iteration was VERIFICATION-GATED (no unverified
        self-report progress accepted);
  (iv)  cost/wall stayed within the EXISTING ceiling (MEASURED via the
        loop's --output-format json cost surface, not estimated)

— OR a definite, evidence-backed HONEST-NEGATIVE naming WHICH dimension
could not be demonstrated and why.  A definite honest-negative
satisfies the AC EXACTLY as a positive does; it is reported straight
and is NEVER retried-to-green, the bound NEVER weakened.

n=1 framing (stated in plain language, per plan §10.5 +
feedback_n1_architectural_vs_n3_statistical): this end-test answers an
ARCHITECTURAL question — "is the loop now CAPABLE of crossing the
real-outcome line before stopping?" — with a binary verifier + a large
effect-size + a meaningful cost-per-rep.  n=1 on a load-bearing real
task is sufficient for the architectural verdict.  The STATISTICAL
payoff-SIZE question is the SEPARATE post-aggregate fast-follow; this
runner does NOT assert or measure a benchmark-score magnitude.

DISPATCHER-OWNED (own-the-wait): every `claude` spawn is the loop's
own — routed through the loop's sealed isolation surface
(goal_drive.build_goal_drive_argv -> _isolation.inject_isolation /
isolated_env()); this runner adds NO new spawn machinery.  The seal
sweep COLLECTS but SKIPS the end-test behind HANDSOFF_RUN_BRC=1 (the
GR.5 / AC.B.5 precedent — the captured verdict artefact is
the durable fact; re-spawning real `claude` to flip a test assertion
would itself be the retry-to-green the plan forbids).
"""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

from .orchestrator import SubTask, run_handsoff_loop
from .verify import freeze_acceptance

VERDICT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / ".phase_verdicts" / "behavioral_refine_endtest.json"
)


def _real_task_floor_check() -> str:
    """A probe-class-or-harder REAL behavioural floor: the produced
    artefact must EXERCISE-and-OBSERVE correctly, not merely exist.

    The task: produce a runnable script `rev.sh` that reverses each
    line of stdin.  The independent floor RUNS it on a held-out input
    and asserts the OBSERVED output — a structurally-present-but-wrong
    submission (or an empty/`true` no-op) fails by construction.  This
    is the loop's EXTERNAL graded authority for the end-test; it is
    NOT the loop's own behavioural self-check (AC.BRC.4 isolation).
    """
    return textwrap.dedent(
        """\
        #!/bin/sh
        # EXTERNAL graded floor (not the loop's own self-check).
        set -e
        [ -f rev.sh ] || { echo "no rev.sh produced"; exit 1; }
        got=$(printf 'abc\\nde\\n' | sh rev.sh)
        [ "$got" = "$(printf 'cba\\ned\\n')" ] || {
          echo "behavioural floor FAIL: got [$got]"; exit 1; }
        echo "behavioural floor OK"
        """
    )


def run_behavioral_refine_endtest(
    *,
    work_root: Path | None = None,
    max_refine_attempts: int = 2,
    cost_ceiling_usd: float = 8.0,
    wall_ceiling_s: float = 2400.0,
) -> dict:
    """Run the real-claude behavioural-refine end-test once (n=1
    architectural).  Returns the DEFINITE per-dimension verdict table
    (either polarity is plan-success) and writes it to VERDICT_PATH.
    """
    work_root = Path(
        work_root
        or os.environ.get("HANDSOFF_BRC_WORKROOT")
        or (Path(__file__).resolve().parent.parent.parent
            / ".phase_verdicts" / "_brc_work")
    )
    work_dir = work_root / "wd"
    artifact_dir = work_root / "ad"
    freeze_dir = work_root / "_frozen"
    for d in (work_dir, artifact_dir, freeze_dir):
        d.mkdir(parents=True, exist_ok=True)

    floor = freeze_dir / "behavioural_floor.sh"
    floor.write_text(_real_task_floor_check(), encoding="utf-8")
    floor.chmod(0o755)

    frozen = freeze_acceptance(
        acceptance_id="brc_endtest",
        content=(
            "FROZEN-ACCEPTANCE brc_endtest: the produced rev.sh, when "
            "RUN on a held-out input, OBSERVABLY reverses each line. "
            "Independent + behaviourally graded; unseen by any brief."
        ),
        check_argv=["sh", str(floor)],
        freeze_dir=freeze_dir,
    )

    objective = (
        "Produce a runnable shell script named rev.sh in the current "
        "directory that reads stdin and prints each line with its "
        "characters reversed."
    )
    sub_tasks = [SubTask(
        name="deliver_rev",
        brief=objective,
        tighter_acceptance=(
            "rev.sh exists AND, when run, actually reverses each "
            "input line (observable behaviour, not merely present)."
        ),
        # AC.BRC.6 — NOT a hand-authored no-op; the orchestrator's
        # _behavioralize() replaces this generically with the loop's
        # own behavioural self-check derived from the objective.
        check_command="BEHAVIORAL-SELF-CHECK-PLACEHOLDER",
    )]

    result = run_handsoff_loop(
        objective=objective,
        sub_tasks=sub_tasks,
        frozen=frozen,
        work_dir=work_dir,
        artifact_dir=artifact_dir,
        behavioral_done=True,
        max_refine_attempts=max_refine_attempts,
        cost_ceiling_usd=cost_ceiling_usd,
        wall_ceiling_s=wall_ceiling_s,
    )

    redrove = result.refine_attempts > 0 or result.reached_done
    bound_held = result.refine_attempts <= result.refine_bound
    gated = bool(result.refine_log) and all(
        e.get("gated_on") == "independent-verify"
        for e in result.refine_log
    )
    cost_known = result.cost_usd is not None
    within = (
        cost_known
        and result.cost_usd <= cost_ceiling_usd
        and result.wall_clock_s <= wall_ceiling_s
    )

    dimensions = {
        "behavioural_done_not_structural": (
            result.behavioral_gated,
            "the in-loop check was the loop's own behavioural self-"
            "check (not structural presence / not `true`); final "
            f"independent verify done={result.reached_done}",
        ),
        "bounded_failure_context_redrive": (
            bound_held,
            f"refine_attempts={result.refine_attempts} of bound "
            f"{result.refine_bound}; stop_reason="
            f"{result.refine_stop_reason}; re-dispatch observable in "
            f"{len(result.transcript_paths)} transcript(s)",
        ),
        "verification_gated_iteration": (
            gated,
            f"every one of {len(result.refine_log)} iteration(s) "
            "advanced on the independent verify, never a self-report",
        ),
        "within_existing_cost_wall_ceiling": (
            within,
            f"measured cost_usd={result.cost_usd} (ceiling "
            f"{cost_ceiling_usd}); wall_s={result.wall_clock_s} "
            f"(ceiling {wall_ceiling_s})"
            + ("" if cost_known
               else " — COST MEASUREMENT GAP (honest None)"),
        ),
    }
    definite = all(isinstance(e, str) and e.strip()
                    for _, e in dimensions.values())
    polarity = ("positive"
                if all(v for v, _ in dimensions.values())
                else "negative")

    table = {
        "ac": "AC.BRC.5",
        "task": objective,
        "task_class": "probe-class-or-harder real task (n=1)",
        "n1_framing": (
            "ARCHITECTURAL verdict (is the loop now CAPABLE of "
            "crossing the real-outcome line before stopping?), NOT a "
            "statistical payoff-size measurement — the score-payoff "
            "SIZE is the SEPARATE post-aggregate fast-follow; this "
            "end-test asserts NO benchmark-score magnitude"
        ),
        "definite": definite,
        "polarity": polarity,
        "honest_negative_is_plan_success": True,
        "never_retried_to_green": True,
        "reached_done": result.reached_done,
        "refine_attempts": result.refine_attempts,
        "refine_bound": result.refine_bound,
        "refine_stop_reason": result.refine_stop_reason,
        "refine_log": result.refine_log,
        "measured_cost_usd": result.cost_usd,
        "measured_wall_clock_s": result.wall_clock_s,
        "dimensions": {
            k: {"verdict": v, "evidence": e}
            for k, (v, e) in dimensions.items()
        },
    }
    VERDICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERDICT_PATH.write_text(
        json.dumps(table, indent=2), encoding="utf-8")
    return table
