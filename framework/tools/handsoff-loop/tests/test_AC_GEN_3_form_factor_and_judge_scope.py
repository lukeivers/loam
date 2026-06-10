"""AC.GEN.3 — form-factor at the confirm + judge-scope honesty (S3).

  * the confirm surfaces the form-factor decision (clickable app /
    command tool / service) in plain language (built on the S1 confirm
    surface);
  * the verdict states judge-scope honestly — what the gate did and
    did not verify, in words a non-technical user understands, for
    BOTH polarities; a negative verdict is reported straight, never
    softened.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.generative import (  # noqa: E402
    GateCriterion,
    GeneratedDesign,
    render_verdict,
)
from handsoff_loop.request_intent import (  # noqa: E402
    RequestIntent,
    build_confirm_text,
)


def _design(judge_scope="It checks the tool on the prepared sample "
                        "and held-out files; it does not check every "
                        "real file you might have.",
            flags=None):
    return GeneratedDesign(
        objective="obj", tool_plan="plan", data_shape="shape",
        gate_plain="done when it works",
        gate_criteria=[GateCriterion(criterion="works")],
        gate_files={"check.py": "pass"},
        check_command="python3 {gate_dir}/check.py",
        held_out_command="", sub_tasks=[{"name": "t", "brief": "b",
                                         "tighter_acceptance": "a"}],
        judge_scope=judge_scope,
        expert_gate_flags=list(flags or []),
    )


def test_confirm_surfaces_form_factor_in_plain_language():
    intent = RequestIntent(
        ask="a thing for the roster",
        inferred_intent="You want the roster sorted out.",
        objective="sort the roster",
        form_factor="cli",
        form_factor_plain="You'll get a small command you run on the "
                          "roster file, and it writes the fixed list "
                          "next to it.",
    )
    confirm = build_confirm_text(intent)
    assert "small command you run" in confirm


def test_positive_verdict_states_what_was_and_was_not_checked():
    v = render_verdict(_design(), reached_done=True, stop_reason="done")
    assert "Done" in v
    assert "did not check every real file" not in v  # not invented
    assert "does not check every real file" in v
    assert "What was checked, honestly" in v


def test_negative_verdict_reported_straight_never_softened():
    v = render_verdict(_design(), reached_done=False,
                       stop_reason="attempt-bound",
                       evidence_tail="3 rows mismatched")
    assert v.startswith("Not done")
    assert "attempt-bound" in v
    assert "not\nretried" in v or "not retried" in v.replace("\n", " ")
    assert "3 rows mismatched" in v


def test_expert_gate_flags_surface_in_the_verdict():
    v = render_verdict(
        _design(flags=["Whether partial rows count needs an expert."]),
        reached_done=True, stop_reason="done")
    assert "human expert" in v
    assert "partial rows count" in v


def test_empty_judge_scope_gets_the_honest_default_never_silence():
    v = render_verdict(_design(judge_scope=""), reached_done=True,
                       stop_reason="done")
    assert "did not verify behavior on other inputs" in v
