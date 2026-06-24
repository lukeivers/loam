"""AC.DF.4 — non-interactive runs are byte-behaviour-preserved (no
regression).

A run with NO design-choice surface (``choose_design_fn=None``, the
standing-hands-off path the sealed S6 proof + smoke use) reaches the
same terminal set and the same freeze->build->verdict spine as before
this slice — the design-first stage degrades to the UNCHANGED single-
design path (it does NOT generate candidates, does NOT call the choice
gate), and the sealed AC.REQ.* / AC.GEN.* / AC.PRG.* / AC.CVG.* suites
stay green (the full-suite green run is the broader proof; this file
pins the specific non-regression: the None path is byte-identical to
the pre-slice planning leg).

Outcome, not method: asserts no behavioural regression on the
non-interactive path.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop import build_from_intent as bfi  # noqa: E402
from handsoff_loop.build_from_intent import run_build_from_intent  # noqa: E402
from handsoff_loop.generative import (  # noqa: E402
    GateCriterion,
    GeneratedDesign,
)
from handsoff_loop.grounding import GroundingOutcome  # noqa: E402
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _design():
    return GeneratedDesign(
        objective="obj", tool_plan="A tool.", data_shape="in/out",
        gate_plain="Done when it runs.",
        gate_criteria=[GateCriterion(criterion="works", traceable_to="")],
        gate_files={"check.py": "import sys; sys.exit(0)\n"},
        check_command="python3 {gate_dir}/check.py {work_dir}",
        held_out_command="",
        sub_tasks=[{"name": "t", "brief": "build it",
                    "tighter_acceptance": "ok"}],
        judge_scope="sample only")


def _patch_front(monkeypatch, *, calls):
    intent = RequestIntent(ask="x", inferred_intent="x", objective="obj")
    monkeypatch.setattr(bfi, "understand_request",
                        lambda ask, model="sonnet": intent)
    monkeypatch.setattr(
        bfi, "research_domain",
        lambda objective, *, workspace_dir, model="sonnet":
        GroundingOutcome(grounded=False, objective=objective, summary="",
                         norms=[], expert_gate_flags=[], record_path="",
                         ungrounded_reason="none"))

    def _gen_design(intent, grounding, *, answers=None, model="sonnet"):
        calls.append("generate_design")
        return _design()

    def _gen_candidates(intent, grounding, *, n=3, answers=None,
                        model="sonnet"):
        calls.append("generate_candidate_designs")
        return []

    monkeypatch.setattr(bfi, "generate_design", _gen_design)
    monkeypatch.setattr(bfi, "generate_candidate_designs", _gen_candidates)


def test_none_choose_fn_uses_the_single_design_path_only(tmp_path,
                                                         monkeypatch):
    calls: list[str] = []
    _patch_front(monkeypatch, calls=calls)

    result = run_build_from_intent(
        "x", workspace_dir=tmp_path, choose_design_fn=None,
        say=lambda _l: None)

    # The non-interactive path runs the UNCHANGED single-design leg and
    # NEVER the candidate generation / choice gate (byte-preserved spine).
    assert "generate_design" in calls
    assert "generate_candidate_designs" not in calls
    # ...and reaches an honest terminal exactly as the sealed spine.
    assert result.terminal in ("done", "honest-negative")
    assert result.design is not None
    # No candidates surface on the non-interactive path.
    assert result.candidates == []


def test_none_choose_fn_freezes_and_builds_like_before(tmp_path,
                                                       monkeypatch):
    _patch_front(monkeypatch, calls=[])
    result = run_build_from_intent(
        "x", workspace_dir=tmp_path, say=lambda _l: None)  # default None
    # The freeze->build->verdict spine ran: a frozen gate exists and a
    # convergence result is present (the same spine as pre-slice).
    assert (Path(result.run_dir) / "_frozen" / "bfi-gate.frozen").exists()
    assert result.convergence is not None
