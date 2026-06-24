"""AC.DF.3 — the chosen design carries the user's tweaks into the
frozen build.

When the chosen design includes a user edit (a changed objective
sentence, an added/removed gate criterion, a changed output shape), the
frozen acceptance gate and the build briefs reflect the EDITED design,
not the original machine candidate.

Outcome, not method: asserts the edit propagates to the freeze; does
not prescribe the edit mechanism.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop import build_from_intent as bfi  # noqa: E402
from handsoff_loop.build_from_intent import (  # noqa: E402
    ChosenDesign,
    apply_design_tweaks,
    run_build_from_intent,
)
from handsoff_loop.generative import (  # noqa: E402
    CandidateDesign,
    GateCriterion,
    GeneratedDesign,
)
from handsoff_loop.grounding import GroundingOutcome  # noqa: E402
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _design():
    return GeneratedDesign(
        objective="original objective",
        tool_plan="A tool.",
        data_shape="in/out",
        gate_plain="Done when it runs once.",
        gate_criteria=[
            GateCriterion(criterion="keeps every row", traceable_to=""),
            GateCriterion(criterion="drops blank rows", traceable_to="")],
        gate_files={"check.py": "import sys; sys.exit(0)\n"},
        check_command="python3 {gate_dir}/check.py {work_dir}",
        held_out_command="",
        sub_tasks=[{"name": "t", "brief": "build it",
                    "tighter_acceptance": "ok"}],
        judge_scope="sample only")


def _candidate():
    return CandidateDesign(
        form_factor="one-shot CLI", tool_plan="A tool.",
        data_shape="in/out", gate_plain="Done when it runs once.",
        sample_output={"summary": "ok ok ok ok ok ok ok ok ok ok ok ok",
                       "rows": [{"id": 1}], "review_queue": []})


def test_changed_objective_propagates():
    edited = apply_design_tweaks(
        _design(), ChosenDesign(index=0, objective="edited objective"))
    assert edited.objective == "edited objective"
    # ...and untouched fields are preserved.
    assert edited.tool_plan == "A tool."


def test_added_and_removed_criteria_propagate():
    edited = apply_design_tweaks(
        _design(),
        ChosenDesign(index=0,
                     add_criteria=["emits a per-row audit line"],
                     remove_criteria=["drops blank"]))
    texts = [c.criterion for c in edited.gate_criteria]
    assert "emits a per-row audit line" in texts
    assert not any("drops blank" in t for t in texts)
    # The non-removed original criterion survives.
    assert any("keeps every row" in t for t in texts)


def test_changed_gate_plain_propagates():
    edited = apply_design_tweaks(
        _design(),
        ChosenDesign(index=0, gate_plain="Done when it emits an audit log."))
    assert edited.gate_plain == "Done when it emits an audit log."


def test_no_tweaks_returns_the_design_unchanged():
    base = _design()
    out = apply_design_tweaks(base, ChosenDesign(index=0))
    # No tweaks: the same design object back (the auto-pick path).
    assert out is base


def test_tweaks_reach_the_frozen_gate_end_to_end(tmp_path, monkeypatch):
    intent = RequestIntent(ask="x", inferred_intent="x", objective="obj")
    monkeypatch.setattr(bfi, "understand_request",
                        lambda ask, model="sonnet": intent)
    monkeypatch.setattr(
        bfi, "research_domain",
        lambda objective, *, workspace_dir, model="sonnet":
        GroundingOutcome(grounded=False, objective=objective, summary="",
                         norms=[], expert_gate_flags=[], record_path="",
                         ungrounded_reason="none"))
    monkeypatch.setattr(
        bfi, "generate_candidate_designs",
        lambda intent, grounding, *, n=3, answers=None, model="sonnet":
        [_candidate(),
         CandidateDesign(form_factor="scheduled normalizer",
                         tool_plan="A normalizer.", data_shape="in/out",
                         gate_plain="done when normalized",
                         sample_output={"summary": "x" * 40,
                                        "rows": [{"id": 1}],
                                        "review_queue": []})])
    # The chosen direction drives the buildable-design generation (mocked).
    monkeypatch.setattr(
        bfi, "generate_design",
        lambda intent, grounding, *, answers=None, model="sonnet": _design())

    result = run_build_from_intent(
        "x", workspace_dir=tmp_path, say=lambda _l: None,
        choose_design_fn=lambda candidates: ChosenDesign(
            index=0,
            objective="USER-EDITED objective",
            add_criteria=["a user-added criterion"]))

    assert result.design.objective == "USER-EDITED objective"
    assert any("user-added" in c.criterion
               for c in result.design.gate_criteria)
    # The frozen gate content reflects the edited design: the run's
    # frozen pin exists and the build proceeded on the edit.
    frozen = Path(result.run_dir) / "_frozen" / "bfi-gate.frozen"
    assert frozen.exists()
    # The run_summary records the edited objective (the gate was frozen
    # on the edited content, not the raw machine candidate).
    summary = json.loads(
        (Path(result.run_dir) / "run_summary.json").read_text())
    assert summary["design"]["objective"] == "USER-EDITED objective"
