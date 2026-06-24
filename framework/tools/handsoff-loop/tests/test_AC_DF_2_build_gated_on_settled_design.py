"""AC.DF.2 — the build loop does NOT start until the user settles on a
design.

When a ``choose_design_fn`` is provided and returns None (declined /
abandoned), NO acceptance gate is frozen and NO build sub-task
dispatches — the run terminates with a distinct ``design-not-chosen``
terminal. When a choice IS returned, the build proceeds on exactly the
chosen design.

Outcome, not method: asserts the freeze+build is gated on a settled
design; does not prescribe the choice UI (a test double here, a
numbered terminal prompt / channel reply in production — all pass).

Drives the production entry point ``run_build_from_intent`` with the
two live legs (understanding, research) doubled so the test pins the
ORCHESTRATION outcome without a real model dispatch; the freeze and
convergence are the real sealed code.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop import build_from_intent as bfi  # noqa: E402
from handsoff_loop.build_from_intent import (  # noqa: E402
    ChosenDesign,
    run_build_from_intent,
)
from handsoff_loop.generative import (  # noqa: E402
    CandidateDesign,
    GeneratedDesign,
    GateCriterion,
)
from handsoff_loop.grounding import GroundingOutcome  # noqa: E402
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _design(slug, *, gate="done when the result is clean"):
    return GeneratedDesign(
        objective=f"objective for {slug}",
        tool_plan=f"A {slug} tool.",
        data_shape="in/out files",
        gate_plain=gate,
        gate_criteria=[GateCriterion(criterion="works", traceable_to="")],
        # An always-passing self-contained gate so convergence reaches a
        # real honest terminal cheaply (no model dispatch in the build).
        gate_files={"check.py": "import sys; sys.exit(0)\n"},
        check_command="python3 {gate_dir}/check.py {work_dir}",
        held_out_command="",
        sub_tasks=[{"name": slug, "brief": f"build {slug}",
                    "tighter_acceptance": "ok"}],
        judge_scope="sample only",
    )


def _candidate(slug, form_factor):
    return CandidateDesign(
        form_factor=form_factor, tool_plan=f"A {slug} tool.",
        data_shape="in/out", gate_plain="done when clean",
        sample_output={
            "summary": "Processed everything; nothing needs review here.",
            "rows": [{"id": 1}, {"id": 2}],
            "review_queue": []})


def _patch_front_legs(monkeypatch):
    """Double the live legs (understanding, research, candidate gen, and
    the chosen-direction buildable-design gen) so the orchestration runs
    without a real model dispatch; the freeze + convergence are real."""
    intent = RequestIntent(ask="tidy the list",
                           inferred_intent="tidy the list",
                           objective="objective: tidy the list")
    monkeypatch.setattr(bfi, "understand_request",
                        lambda ask, model="sonnet": intent)
    monkeypatch.setattr(
        bfi, "research_domain",
        lambda objective, *, workspace_dir, model="sonnet":
        GroundingOutcome(grounded=False, objective=objective, summary="",
                         norms=[], expert_gate_flags=[], record_path="",
                         ungrounded_reason="no grounding this run"))
    cands = [_candidate("cli", "one-shot CLI"),
             _candidate("queue", "interactive review-queue app")]
    monkeypatch.setattr(
        bfi, "generate_candidate_designs",
        lambda intent, grounding, *, n=3, answers=None, model="sonnet":
        cands)
    # The chosen direction drives a single-design generation (mocked):
    # echo the chosen direction brief into the tool_plan so the test can
    # assert the chosen direction survived into the buildable design.
    def _gen(intent, grounding, *, answers=None, model="sonnet"):
        brief = (answers or {}).get("Chosen design direction to build", "")
        return _design("built-" + ("queue" if "review-queue" in brief
                                    else "cli"))
    monkeypatch.setattr(bfi, "generate_design", _gen)
    return cands


def test_decline_freezes_nothing_and_builds_nothing(tmp_path, monkeypatch):
    _patch_front_legs(monkeypatch)
    convergence_ran = {"called": False}
    monkeypatch.setattr(
        bfi, "run_to_convergence",
        lambda **kw: convergence_ran.__setitem__("called", True))

    result = run_build_from_intent(
        "tidy the list", workspace_dir=tmp_path,
        choose_design_fn=lambda candidates: None,  # user declines
        say=lambda _l: None)

    assert result.terminal == "design-not-chosen"
    assert result.convergence is None
    assert convergence_ran["called"] is False, (
        "build dispatched despite a declined design")
    # No acceptance gate was frozen.
    run_dir = Path(result.run_dir)
    assert not (run_dir / "_frozen").exists(), (
        "a gate was frozen despite no settled design")
    # The candidates were still surfaced for the (declined) choice.
    assert len(result.candidates) >= 2


def test_choice_proceeds_the_build_on_the_chosen_design(tmp_path,
                                                        monkeypatch):
    cands = _patch_front_legs(monkeypatch)
    chosen_seen = {}

    def _choose(candidates):
        chosen_seen["count"] = len(candidates)
        return ChosenDesign(index=1)  # pick the review-queue app

    result = run_build_from_intent(
        "tidy the list", workspace_dir=tmp_path,
        choose_design_fn=_choose, say=lambda _l: None)

    assert chosen_seen["count"] == len(cands)
    # The build proceeded (a real freeze + convergence ran) on the
    # chosen design — an honest terminal, not design-not-chosen.
    assert result.terminal in ("done", "honest-negative")
    assert result.design is not None
    # The chosen direction (candidate index 1, the review-queue app)
    # conditioned the buildable design generation.
    assert "queue" in result.design.tool_plan
    # The gate was frozen for the chosen design.
    assert (Path(result.run_dir) / "_frozen").exists()
