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

"""AC.PBR.4 / AC.PBR.5 / AC.PBR.6 — the frozen pass rule, the
FROZEN-RATIFIED materially-beats margin, the three-valued verdict
(computed, not asserted), and the four-class failure taxonomy.

Everything in this module is FROZEN BEFORE ANY RUN and is NOT moved
after runs begin (D-PBR-1 / D-PBR-5 / AC.PBR.4 contamination spine).
"loam does not materially beat the baseline" is a FIRST-CLASS
plan-success polarity (AC.PBR.7) — there is deliberately no
green-only path here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- AC.PBR.6 frozen four-class failure taxonomy (the
# false-success-class map). Every non-pass carries EXACTLY ONE. ----
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


@dataclass(frozen=True)
class FailureClass:
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


def classify_failure(
    *,
    produced_artifact: bool,
    judge_tag: str,
    floor_exit: int,
    held_out_exit: int | None,
) -> str:
    """Map a non-pass into EXACTLY ONE frozen taxonomy class
    (AC.PBR.6). The classification MECHANISM is the builder's call;
    the taxonomy is the frozen OUTCOME.

    Precedence (frozen): an honest refusal the judge named is
    HONEST-NEGATIVE-REFUSAL; nothing produced at all is
    DID-NOT-PRODUCE-OUTPUT; an artefact that exists but the floor /
    held-out check rejects as hollow (compiled-but-no-effect /
    empty-extraction / target-untouched / overfit) is
    PRODUCED-BUT-NO-REAL-EFFECT — the false-success class AC.PBR.2's
    floor is built to catch; an artefact that delivered a real but
    incorrect effect is PRODUCED-BUT-WRONG.
    """
    if judge_tag == "HONEST-NEGATIVE":
        return HONEST_NEGATIVE_REFUSAL
    if not produced_artifact:
        return DID_NOT_PRODUCE_OUTPUT
    # An artefact exists. The floor check distinguishes hollow
    # (no real effect / target untouched / vacuous) from a real but
    # wrong effect via its own FLOOR-FAIL reason; the held-out check
    # is the overfit/hardcoded (no-real-effect) signal.
    if held_out_exit is not None and held_out_exit != 0 and \
            floor_exit == 0:
        # floor passed but anti-overfit failed -> hollow/hardcoded:
        # nominally produced the right surface, no real generalisable
        # effect (the produced-but-no-real-effect false-success class)
        return PRODUCED_BUT_NO_REAL_EFFECT
    if judge_tag == "CHECKABLE-BUT-WRONG":
        # the judge found a proxy/plumbing pass without the real
        # outcome — the false-success class
        return PRODUCED_BUT_NO_REAL_EFFECT
    return PRODUCED_BUT_WRONG


def frozen_pass(
    *,
    judge_tag: str,
    floor_exit: int,
    held_out_exit: int | None,
) -> bool:
    """AC.PBR.4 frozen pass rule (the verify.py:213-215 both-must-pass
    spine, frozen with the task set, NO retry-to-pass).

    PASSED iff the independent judge tags FAITHFUL **and** the
    positive-real-outcome floor check exits 0 **and** the held-out
    anti-overfit check exits 0. Any leg failing ⇒ non-pass. The judge
    must be the INDEPENDENT held-out judge (AC.PBR.3) — this function
    is judge-source-agnostic by signature, but the run wiring
    (scorer.py) passes ONLY the independent judge's tag.
    """
    return (
        judge_tag == "FAITHFUL"
        and floor_exit == 0
        and (held_out_exit is None or held_out_exit == 0)
    )


@dataclass
class ArmTaskDisposition:
    """The definite per-(arm,task) disposition (AC.PBR.6 record)."""

    task_id: str
    arm: str
    passed: bool
    judge_tag: str
    judge_reason: str
    floor_exit: int
    held_out_exit: int | None
    failure_class: str  # "" iff passed
    cost_usd: float | None
    wall_clock_s: float
    transcript_path: str
    check_command: str

    def as_record(self) -> dict:
        return {
            "task_id": self.task_id,
            "arm": self.arm,
            "passed": self.passed,
            "judge_tag": self.judge_tag,
            "judge_reason": self.judge_reason,
            "floor_exit": self.floor_exit,
            "held_out_exit": self.held_out_exit,
            "failure_class": self.failure_class,
            "cost_usd": self.cost_usd,
            "wall_clock_s": self.wall_clock_s,
            "transcript_path": self.transcript_path,
            "check_command": self.check_command,
        }


@dataclass
class Verdict:
    """The computed three-valued verdict + the failure-signature map.

    The verdict is COMPUTED from the dispositions (AC.PBR.5), never
    asserted. ``all_tasks_pass_aspirational`` is the owner's
    documented aspirational/secondary metric — reported alongside but
    EXPLICITLY NOT the gate.
    """

    verdict: str
    baseline_pass_count: int
    loam_pass_count: int
    baseline_non_pass_tasks: list[str]
    loam_recovered_of_baseline_misses: list[str]
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
            "clear_majority_threshold": self.clear_majority_threshold,
            "clear_majority_cleared": self.clear_majority_cleared,
            "no_total_regression": self.no_total_regression,
            "all_tasks_pass_aspirational":
                self.all_tasks_pass_aspirational,
            "per_arm_failure_signature": self.per_arm_failure_signature,
            "reason": self.reason,
            "margin_text": self.margin_text,
        }


# FROZEN-RATIFIED D-PBR-1 margin text (owner Telegram 11447). The
# builder freezes EXACTLY this and does NOT move it after runs begin.
FROZEN_MARGIN_TEXT = (
    "loam MATERIALLY BEATS baseline IFF BOTH: (i) among the tasks the "
    "BASELINE arm is independently judged a NON-PASS on, the LOAM arm "
    "is independently judged a PASS on a CLEAR MAJORITY (strictly "
    ">50%) of them; AND (ii) loam's TOTAL independently-judged pass "
    "count does NOT regress below baseline's total. Otherwise loam "
    "does NOT materially beat baseline (a first-class plan-success "
    "outcome). If there are too few baseline non-passes to define a "
    "clear majority (0 baseline misses) OR the set is under-powered, "
    "the verdict is INDETERMINATE (a definite reportable finding "
    "naming why). 'Every task a pass' is a DOCUMENTED ASPIRATIONAL / "
    "SECONDARY metric, EXPLICITLY NOT the gate."
)


def compute_verdict(
    baseline: list[ArmTaskDisposition],
    loam: list[ArmTaskDisposition],
) -> Verdict:
    """AC.PBR.5 — compute the three-valued verdict from the numbers.

    Applies the FROZEN-RATIFIED D-PBR-1 margin EXACTLY. The verdict
    is computed, never asserted; "loam does not materially beat" is a
    first-class polarity; the all-tasks-pass metric is reported
    alongside but is NOT the gate.
    """
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
    # "clear majority" frozen numeric form: strictly >50% of the
    # baseline-miss subset (a paired definition over the baseline's
    # OWN misses — not a trivially-clearable absolute count).
    threshold = 0.5
    clear_majority = (
        n_miss > 0 and (len(recovered) / n_miss) > threshold
    )
    no_regression = len(l_pass) >= len(b_pass)

    def _sig(arm_disp: list[ArmTaskDisposition]) -> dict:
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
                 "explicitly NOT the v2 pass/fail gate (the gate is "
                 "the frozen (a)/(b)/(c) margin)."),
    }

    if n_miss == 0:
        verdict = "indeterminate"
        reason = (
            f"INDETERMINATE: the baseline arm passed all {len(all_ids)} "
            f"tasks (0 independently-judged non-passes), so there is no "
            f"baseline-miss subset over which to define a clear "
            f"majority. This is a definite, reportable finding: on this "
            f"non-subjective set bare claude -p already clears every "
            f"task, so the harness's distinctive value (translation-"
            f"burden absorption on under-specified intent) is not "
            f"measurable here — exactly the §10.5 expected-possible "
            f"result, NOT a loam failure and NOT a reason to re-pick "
            f"easier tasks."
        )
    elif clear_majority and no_regression:
        verdict = "loam-materially-beats-baseline"
        reason = (
            f"loam recovered {len(recovered)}/{n_miss} of the "
            f"baseline's independently-judged misses (>50% clear "
            f"majority) AND did not regress total pass count "
            f"({len(l_pass)} >= {len(b_pass)})."
        )
    else:
        verdict = "loam-does-not-materially-beat-baseline"
        why = []
        if not clear_majority:
            why.append(
                f"loam recovered only {len(recovered)}/{n_miss} of the "
                f"baseline's misses (not a >50% clear majority)"
            )
        if not no_regression:
            why.append(
                f"loam's total pass count regressed "
                f"({len(l_pass)} < {len(b_pass)})"
            )
        reason = (
            "loam does NOT materially beat the baseline on this set: "
            + "; ".join(why)
            + ". This is a FIRST-CLASS plan-success outcome, reported "
            "straight — NOT retried to green, the margin NOT weakened."
        )

    return Verdict(
        verdict=verdict,
        baseline_pass_count=len(b_pass),
        loam_pass_count=len(l_pass),
        baseline_non_pass_tasks=baseline_non_pass,
        loam_recovered_of_baseline_misses=recovered,
        clear_majority_threshold=threshold,
        clear_majority_cleared=clear_majority,
        no_total_regression=no_regression,
        all_tasks_pass_aspirational=aspirational,
        per_arm_failure_signature=per_arm_sig,
        reason=reason,
        margin_text=FROZEN_MARGIN_TEXT,
    )
