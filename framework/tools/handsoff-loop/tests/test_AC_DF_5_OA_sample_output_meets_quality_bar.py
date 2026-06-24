"""AC.DF.5 (outcome-altitude: true) — a candidate design's sample-output
rendering reaches the named quality bar.

Invoking the candidate-design generation on a real ask with NO
pre-arranged state produces, for at least one candidate, a sample-output
rendering that satisfies a checkable quality rubric derived from the
accounting-back-office demo (>= N named output sections, a populated
tabular result, a plain-language summary, a review-queue-equivalent) —
verified by ``design_rubric_check``, a check the generator never saw
(the generation prompt NEVER carries the rubric).

This is the owner's "demo quality is a real build target" ruling made
into a falsifiable AC. The provenance of the rubric (the accounting
demo whose output shape it generalises:
pos3 .../response-paper/assets/demo/raw-outputs — month_end_summary's
summary_text, a reconciliation's matched/unpaid/unmatched rows, a
review_queue's items) is named HERE, never in pipeline source (AC.GEN.2).

Live path is env-gated (BFI_REAL_CLAUDE=1): a real `claude -p` dispatch
through the production entry point, no pre-arranged state. The
non-live test pins the held-out property of the check itself (the
rubric is genuinely independent of the generator).

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.generative import (  # noqa: E402
    SAMPLE_RUBRIC_MIN_SECTIONS,
    _CANDIDATE_PROMPT,
    design_rubric_check,
    generate_candidate_designs,
)
from handsoff_loop.grounding import GroundingOutcome  # noqa: E402
from handsoff_loop.request_intent import RequestIntent  # noqa: E402

# A real, off-vertical ask — no pre-arranged state, no domain shortcut.
LIVE_DF_ASK = (
    "I run a small community tool library and I waste hours every week "
    "turning the paper sign-out sheet into a record of who has which "
    "tool, what is overdue, and what needs a reminder — can you make me "
    "something that does that"
)


def test_rubric_is_independent_of_the_generator():
    # AC.DF.5's check is genuinely held-out: the generation prompt never
    # carries the rubric's pass condition, so a passing candidate is
    # checked by something the generator never saw.
    prompt = _CANDIDATE_PROMPT
    assert "design_rubric_check" not in prompt
    assert "SAMPLE_RUBRIC_MIN_SECTIONS" not in prompt
    # The structural rubric's pass tokens are not spelled into the prompt
    # as a literal checklist the generator could overfit to.
    assert ">= 3 named sections" not in prompt


def test_rubric_rejects_a_stub_sample_output():
    # A terse bullet-stub (the SAL-DF-1 failure mode) does NOT pass.
    ok, reason = design_rubric_check({"plan": "a tool"})
    assert ok is False and "section" in reason
    # Sections but no table / summary / review surface also fails.
    ok2, _ = design_rubric_check(
        {"a": "x", "b": "y", "c": "z"})
    assert ok2 is False


def test_rubric_accepts_a_demo_grade_sample_output():
    # A rendering with the demo's structure passes (>= N sections, a
    # populated table, a plain-language summary, a review surface).
    demo_grade = {
        "summary": ("Checked 84 sign-outs: 71 returned on time, 9 are "
                    "out, 4 are overdue and need a reminder."),
        "status_table": [
            {"tool": "drill", "borrower": "A. Lee", "status": "out"},
            {"tool": "ladder", "borrower": "M. Ortiz", "status": "overdue"}],
        "review_queue": [
            {"tool": "saw", "why": "no clear borrower on the sheet"}],
    }
    ok, reason = design_rubric_check(demo_grade)
    assert ok is True, reason
    assert SAMPLE_RUBRIC_MIN_SECTIONS == 3


@pytest.mark.skipif(
    os.environ.get("BFI_REAL_CLAUDE") != "1",
    reason="live candidate-design generation; set BFI_REAL_CLAUDE=1")
def test_live_candidate_sample_output_meets_the_bar():
    # Outcome-altitude: the production entry point on a real ask, no
    # pre-arranged state, real `claude -p` dispatch.
    intent = RequestIntent(
        ask=LIVE_DF_ASK, inferred_intent=LIVE_DF_ASK,
        objective="objective: " + LIVE_DF_ASK)
    grounding = GroundingOutcome(
        grounded=False, objective=intent.objective, summary="",
        norms=[], expert_gate_flags=[], record_path="",
        ungrounded_reason="grounding skipped for the DF.5 live probe")

    candidates = generate_candidate_designs(intent, grounding, n=3)

    assert len(candidates) >= 2, "the design-first stage needs a choice"
    # At least one candidate's sample-output rendering reaches the bar,
    # checked by the held-out rubric the generator never saw.
    results = [design_rubric_check(c.sample_output) for c in candidates]
    assert any(ok for ok, _ in results), (
        "no candidate sample-output met the demo-grade rubric: "
        + "; ".join(reason for _, reason in results))
