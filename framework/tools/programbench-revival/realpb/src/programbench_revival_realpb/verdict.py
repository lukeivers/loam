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

"""AC.RPB.4 / AC.RPB.5 / AC.RPB.6 — the frozen pass rule over the
GRADED upstream score, the FROZEN-RATIFIED materially-beats margin
PLUS the NEW ``k_min >= 2`` small-k floor (the named v2 task-#44
defect fix), the three-valued verdict (computed, not asserted), and
the four-class failure taxonomy.

Everything in this module is FROZEN BEFORE ANY RUN and is NOT moved
after runs begin (D-RPB-1 / D-RPB-2 / AC.RPB.4 contamination spine).
"loam does not materially beat the baseline on the real benchmark" is
a FIRST-CLASS plan-success polarity (AC.RPB.7) — there is deliberately
no green-only path here.

THE NAMED v2 DEFECT FIX (F2 §10.2 / AC.RPB.5 / D-RPB-1):
v2's ``programbench_revival.verdict.compute_verdict`` forced
``indeterminate`` ONLY when the baseline-miss count was EXACTLY 0.
That is the binary-verdict-rule degeneracy the v2 task-#44 / PB3
defect named: a near-degenerate denominator (1 baseline miss) could
read as a determinate loss/win. This real-PB module forces verdict
(c) ``indeterminate`` whenever the baseline-miss count is ``< k_min``
(``k_min >= 2``, frozen with the task set) with the machine-stated
reason ``baseline-miss-denominator < k_min`` — a degenerate OR
near-degenerate denominator can NEVER resolve to (a) or (b). v2's
module is left UNTOUCHED (the substitute record is preserved); this
is a NEW module, not a silent patch of the v2 one.

THE GRADED UPSTREAM FLOOR (F2 §10.2 / AC.RPB.2 / D-RPB-2):
the real upstream signal is GRADED (``score = n_resolved /
len(test_results)``; ``compile_failed`` => 0.0). The frozen per-task
pass rule is authored over the graded score (>= the frozen per-task
``theta``), NOT a binary judge tag alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- AC.RPB.6 frozen four-class failure taxonomy (the false-success-
# class map). Every non-pass carries EXACTLY ONE. REUSED v2 taxonomy,
# real-PB-bound. ----
DID_NOT_PRODUCE_OUTPUT = "did-not-produce-output"
PRODUCED_BUT_NO_REAL_EFFECT = "produced-but-no-real-effect"
PRODUCED_BUT_WRONG = "produced-but-wrong"
HONEST_NEGATIVE_REFUSAL = "honest-negative-refusal"

FROZEN_FAILURE_TAXONOMY = (
    DID_NOT_PRODUCE_OUTPUT,
    PRODUCED_BUT_NO_REAL_EFFECT,
    PRODUCED_BUT_WRONG,
    HONEST_NEGATIVE_REFUSAL,
)

THREE_VALUED = (
    "loam-materially-beats-baseline",
    "loam-does-not-materially-beat-baseline",
    "indeterminate",
)

# FROZEN small-k floor on the baseline-miss denominator (D-RPB-1).
# The authoritative value is carried in tasks.json (frozen with the
# task set + content-hash-pinned); this is the module-level default
# the test/run wiring asserts equals the task-set's pinned value.
K_MIN = 2

# FROZEN-RATIFIED D-PBR-1 margin text (owner Telegram 11447), REUSED
# verbatim from v2 (the margin SHAPE is not re-litigated — only the
# task source + the graded floor + the k_min small-k floor are the
# real-PB additions). The builder freezes EXACTLY this and does NOT
# move it after runs begin.
FROZEN_MARGIN_TEXT = (
    "loam MATERIALLY BEATS baseline IFF BOTH: (i) among the tasks the "
    "BASELINE arm is independently judged a NON-PASS on, the LOAM arm "
    "is independently judged a PASS on a CLEAR MAJORITY (strictly "
    ">50%) of them; AND (ii) loam's TOTAL independently-judged pass "
    "count does NOT regress below baseline's total. Otherwise loam "
    "does NOT materially beat baseline (a first-class plan-success "
    "outcome). The 'clear majority of the baseline's non-passes' "
    "computation is GATED by a FROZEN small-k floor k_min >= 2 on the "
    "baseline-miss denominator: if the count of tasks the baseline "
    "arm is independently judged a NON-PASS on is < k_min, the "
    "verdict is FORCED to INDETERMINATE with the machine-stated "
    "reason 'baseline-miss-denominator < k_min' (the named v2 "
    "task-#44 degenerate-denominator defect fix) — a degenerate or "
    "near-degenerate denominator can NEVER read as a determinate "
    "loss or win. 'Every task a pass' is a DOCUMENTED ASPIRATIONAL / "
    "SECONDARY metric, EXPLICITLY NOT the gate."
)


@dataclass(frozen=True)
class RealPBFailureClass:
    """One non-pass mapped to exactly one frozen taxonomy class."""

    task_id: str
    arm: str
    failure_class: str
    evidence: str

    def __post_init__(self) -> None:
        if self.failure_class not in FROZEN_FAILURE_TAXONOMY:
            raise ValueError(
                f"failure_class {self.failure_class!r} not in the "
                f"frozen taxonomy {FROZEN_FAILURE_TAXONOMY}"
            )


def classify_realpb_failure(
    *,
    produced_submission: bool,
    judge_tag: str,
    upstream_score: float,
    upstream_error_code: str | None,
    floor_theta: float,
) -> str:
    """Map a non-pass into EXACTLY ONE frozen taxonomy class
    (AC.RPB.6), real-PB-bound. The classification MECHANISM is the
    builder's call; the taxonomy is the frozen OUTCOME.

    Precedence (frozen):
      * an honest refusal the independent judge named is
        HONEST-NEGATIVE-REFUSAL (first-class, never retried-to-green);
      * no submission produced at all is DID-NOT-PRODUCE-OUTPUT;
      * a submission that the REAL upstream eval reports
        ``compile_failed`` (or any error_code) OR scores ~0 (below
        the frozen theta with a near-zero resolved fraction) is
        PRODUCED-BUT-NO-REAL-EFFECT — the false-success class the
        positive-real-outcome floor is built to catch (a friendly
        summary / hollow / non-compiling submission reporting done);
      * a real compiling submission that resolved a non-trivial slice
        but still did NOT clear the frozen ``theta`` is
        PRODUCED-BUT-WRONG (a real but insufficient effect).
    """
    if judge_tag == "HONEST-NEGATIVE":
        return HONEST_NEGATIVE_REFUSAL
    if not produced_submission:
        return DID_NOT_PRODUCE_OUTPUT
    if upstream_error_code or upstream_score <= 0.01:
        # compile_failed / hollow / vacuous: the false-success class
        # (nominally produced something, no real test-passing effect).
        return PRODUCED_BUT_NO_REAL_EFFECT
    if judge_tag == "CHECKABLE-BUT-WRONG":
        # the judge found a proxy/plumbing pass without the real
        # outcome despite a non-zero score — the false-success class.
        return PRODUCED_BUT_NO_REAL_EFFECT
    # a real compiling submission that delivered a real but
    # insufficient effect (0.01 < score < theta).
    return PRODUCED_BUT_WRONG


def realpb_frozen_pass(
    *,
    judge_tag: str,
    upstream_score: float,
    floor_theta: float,
    held_out_clean: bool,
) -> bool:
    """AC.RPB.4 frozen pass rule over the GRADED upstream score (the
    verify.py:213-215 both-must-pass spine, real-PB-bound, frozen with
    the task set, NO retry-to-pass).

    PASSED IFF the INDEPENDENT held-out judge tags FAITHFUL **and**
    the REAL upstream ``programbench eval`` graded score clears the
    frozen per-task positive-real-outcome floor ``theta`` **and** the
    held-out anti-overfit binding holds (the upstream held-out test
    branches — absent from every prompt — did not contradict; the
    agent provably never saw the upstream suite). Any leg failing =>
    non-pass. ``compile_failed`` / hollow drives ``upstream_score`` to
    0.0 < ``theta`` => non-pass by construction. The judge must be the
    INDEPENDENT held-out judge (AC.RPB.3) — this function is
    judge-source-agnostic by signature; the run wiring (scorer/runner)
    passes ONLY the independent judge's tag, never the loop's own.
    """
    return (
        judge_tag == "FAITHFUL"
        and upstream_score >= floor_theta
        and held_out_clean
    )


@dataclass
class RealPBArmDisposition:
    """The definite per-(arm,task) disposition (AC.RPB.6 record),
    grounded in the REAL upstream ``*.eval.json``."""

    task_id: str
    instance_id: str
    arm: str
    passed: bool
    judge_tag: str
    judge_reason: str
    upstream_score: float
    upstream_n_resolved: int
    upstream_n_tests: int
    upstream_error_code: str | None
    floor_theta: float
    held_out_clean: bool
    failure_class: str  # "" iff passed
    cost_usd: float | None
    agent_wall_clock_s: float
    eval_emulation_wall_clock_s: float
    transcript_path: str
    eval_json_path: str

    def as_record(self) -> dict:
        return {
            "task_id": self.task_id,
            "instance_id": self.instance_id,
            "arm": self.arm,
            "passed": self.passed,
            "judge_tag": self.judge_tag,
            "judge_reason": self.judge_reason,
            "upstream_score": self.upstream_score,
            "upstream_n_resolved": self.upstream_n_resolved,
            "upstream_n_tests": self.upstream_n_tests,
            "upstream_error_code": self.upstream_error_code,
            "floor_theta": self.floor_theta,
            "held_out_clean": self.held_out_clean,
            "failure_class": self.failure_class,
            "cost_usd": self.cost_usd,
            "agent_wall_clock_s": self.agent_wall_clock_s,
            "eval_emulation_wall_clock_s":
                self.eval_emulation_wall_clock_s,
            "transcript_path": self.transcript_path,
            "eval_json_path": self.eval_json_path,
        }


@dataclass
class RealPBVerdict:
    """The computed three-valued verdict + the failure-signature map.

    The verdict is COMPUTED from the dispositions (AC.RPB.5), never
    asserted. ``all_tasks_pass_aspirational`` is the owner's
    documented aspirational/secondary metric — reported alongside but
    EXPLICITLY NOT the gate. ``k_min`` + ``baseline_miss_below_k_min``
    are the named v2 task-#44 defect fix made observable.
    """

    verdict: str
    baseline_pass_count: int
    loam_pass_count: int
    baseline_non_pass_tasks: list[str]
    loam_recovered_of_baseline_misses: list[str]
    k_min: int
    baseline_miss_count: int
    baseline_miss_below_k_min: bool
    clear_majority_threshold: float
    clear_majority_cleared: bool
    no_total_regression: bool
    all_tasks_pass_aspirational: dict
    per_arm_failure_signature: dict
    reason: str = ""
    margin_text: str = field(default="")

    def as_record(self) -> dict:
        return {
            "verdict": self.verdict,
            "baseline_pass_count": self.baseline_pass_count,
            "loam_pass_count": self.loam_pass_count,
            "baseline_non_pass_tasks": self.baseline_non_pass_tasks,
            "loam_recovered_of_baseline_misses":
                self.loam_recovered_of_baseline_misses,
            "k_min": self.k_min,
            "baseline_miss_count": self.baseline_miss_count,
            "baseline_miss_below_k_min":
                self.baseline_miss_below_k_min,
            "clear_majority_threshold": self.clear_majority_threshold,
            "clear_majority_cleared": self.clear_majority_cleared,
            "no_total_regression": self.no_total_regression,
            "all_tasks_pass_aspirational":
                self.all_tasks_pass_aspirational,
            "per_arm_failure_signature":
                self.per_arm_failure_signature,
            "reason": self.reason,
            "margin_text": self.margin_text,
        }


def compute_realpb_verdict(
    baseline: list[RealPBArmDisposition],
    loam: list[RealPBArmDisposition],
    *,
    k_min: int,
) -> RealPBVerdict:
    """AC.RPB.5 — compute the three-valued verdict from the numbers,
    with the NEW frozen ``k_min >= 2`` small-k floor (the named v2
    task-#44 defect fix, D-RPB-1).

    Applies the FROZEN-RATIFIED D-PBR-1 margin EXACTLY + the k_min
    small-k floor. The verdict is computed, never asserted; "loam
    does not materially beat" is a first-class polarity; the
    all-tasks-pass metric is reported alongside but is NOT the gate.

    ORDER OF PRECEDENCE (frozen): the k_min small-k floor is checked
    FIRST — if the baseline-miss denominator is ``< k_min`` the
    verdict is FORCED to ``indeterminate`` with the machine-stated
    reason; a degenerate / near-degenerate denominator can NEVER
    resolve to (a) or (b). Only with ``>= k_min`` baseline misses is
    the clear-majority + no-regression margin even evaluated.
    """
    if k_min < 2:
        raise ValueError(
            f"k_min must be >= 2 (D-RPB-1 small-k floor invariant); "
            f"got {k_min}."
        )

    by_task_b = {d.task_id: d for d in baseline}
    by_task_l = {d.task_id: d for d in loam}
    all_ids = sorted(set(by_task_b) | set(by_task_l))

    b_pass = sorted(t for t in all_ids
                    if by_task_b.get(t) and by_task_b[t].passed)
    l_pass = sorted(t for t in all_ids
                    if by_task_l.get(t) and by_task_l[t].passed)

    baseline_non_pass = sorted(
        t for t in all_ids
        if not (by_task_b.get(t) and by_task_b[t].passed)
    )
    recovered = sorted(
        t for t in baseline_non_pass
        if by_task_l.get(t) and by_task_l[t].passed
    )

    n_miss = len(baseline_non_pass)
    below_k_min = n_miss < k_min

    threshold = 0.5
    clear_majority = (
        n_miss > 0 and (len(recovered) / n_miss) > threshold
    )
    no_regression = len(l_pass) >= len(b_pass)

    def _sig(arm_disp: list[RealPBArmDisposition]) -> dict:
        sig = {c: 0 for c in FROZEN_FAILURE_TAXONOMY}
        for d in arm_disp:
            if not d.passed and d.failure_class:
                sig[d.failure_class] = sig.get(d.failure_class, 0) + 1
        return sig

    per_arm_sig = {
        "baseline": _sig(baseline),
        "loam": _sig(loam),
    }

    aspirational = {
        "baseline_all_tasks_pass": len(b_pass) == len(all_ids)
        and len(all_ids) > 0,
        "loam_all_tasks_pass": len(l_pass) == len(all_ids)
        and len(all_ids) > 0,
        "note": ("DOCUMENTED ASPIRATIONAL / SECONDARY metric — "
                 "explicitly NOT the real-PB pass/fail gate (the gate "
                 "is the frozen (a)/(b)/(c) margin with the k_min "
                 "small-k floor)."),
    }

    # --- THE NAMED v2 TASK-#44 DEFECT FIX (D-RPB-1), checked FIRST.
    if below_k_min:
        verdict = "indeterminate"
        reason = (
            f"INDETERMINATE: baseline-miss-denominator < k_min "
            f"(baseline independently-judged non-passes = {n_miss}; "
            f"frozen k_min = {k_min}). The 'clear majority of the "
            f"baseline's non-passes' computation is UNDEFINED / "
            f"degenerate on a sub-k_min denominator, so the verdict "
            f"is FORCED to (c) indeterminate with this machine-stated "
            f"reason — a degenerate or near-degenerate denominator "
            f"can NEVER read as a determinate loss or win. This is "
            f"the named v2 task-#44 / PB3 defect being CORRECTLY "
            f"handled (v2 forced indeterminate only at exactly 0 "
            f"baseline misses; this real-PB rule forces it at "
            f"< k_min). A definite, reportable finding naming exactly "
            f"why — NOT a loam failure, NOT a reason to re-pick "
            f"easier tasks or shrink to a substitute."
        )
    elif clear_majority and no_regression:
        verdict = "loam-materially-beats-baseline"
        reason = (
            f"loam recovered {len(recovered)}/{n_miss} of the "
            f"baseline's independently-judged real-benchmark misses "
            f"(>50% clear majority, denominator {n_miss} >= k_min "
            f"{k_min}) AND did not regress total pass count "
            f"({len(l_pass)} >= {len(b_pass)})."
        )
    else:
        verdict = "loam-does-not-materially-beat-baseline"
        why = []
        if not clear_majority:
            why.append(
                f"loam recovered only {len(recovered)}/{n_miss} of "
                f"the baseline's real-benchmark misses (not a >50% "
                f"clear majority)"
            )
        if not no_regression:
            why.append(
                f"loam's total pass count regressed "
                f"({len(l_pass)} < {len(b_pass)})"
            )
        reason = (
            "loam does NOT materially beat the baseline on the REAL "
            "public ProgramBench subset (baseline-miss denominator "
            f"{n_miss} >= k_min {k_min}, so the margin is well-"
            "defined): "
            + "; ".join(why)
            + ". This is a FIRST-CLASS plan-success outcome, reported "
            "straight — NOT retried to green, the FROZEN margin NOT "
            "weakened."
        )

    return RealPBVerdict(
        verdict=verdict,
        baseline_pass_count=len(b_pass),
        loam_pass_count=len(l_pass),
        baseline_non_pass_tasks=baseline_non_pass,
        loam_recovered_of_baseline_misses=recovered,
        k_min=k_min,
        baseline_miss_count=n_miss,
        baseline_miss_below_k_min=below_k_min,
        clear_majority_threshold=threshold,
        clear_majority_cleared=clear_majority,
        no_total_regression=no_regression,
        all_tasks_pass_aspirational=aspirational,
        per_arm_failure_signature=per_arm_sig,
        reason=reason,
        margin_text=FROZEN_MARGIN_TEXT,
    )
