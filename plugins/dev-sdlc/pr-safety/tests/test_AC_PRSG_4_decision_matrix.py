"""AC.PRSG.4 — per-band gating engine (3-band × 4-shape × 3-profile decision matrix).

Decision-matrix coverage per plan-doc §6 — 13 cells + 6 mixed-touch
pre-emption rules. Every cell tested.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)
from loam_pr_safety import (
    CandidateAC,
    ClassificationResult,
    GateAction,
    Hunk,
    TouchedAC,
    decide,
)


# ---- helpers ---------------------------------------------------------


def _verified_ac(ac_id: str = "AC.V.1") -> BandedAC:
    return BandedAC(
        ac_id=ac_id,
        text="A verified AC.",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["tests/test_x.py::test_y", "src/x.py:10"],
            repo_sha="abc1234",
        ),
        backing_files=["src/x.py"],
    )


def _plausible_ac(ac_id: str = "AC.P.1") -> BandedAC:
    return BandedAC(
        ac_id=ac_id,
        text="A plausible AC.",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["src/y.py:20-30"],
        ),
        backing_files=["src/y.py"],
    )


def _hypothesised_ac(ac_id: str = "AC.H.1") -> BandedAC:
    return BandedAC(
        ac_id=ac_id,
        text="A hypothesised AC.",
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(
            kind="inference",
            rationale="Inferred from source patterns.",
        ),
        backing_files=["src/z.py"],
    )


def _touched(ac: BandedAC, *, kind: str = "citation_line") -> TouchedAC:
    return TouchedAC(
        ac=ac,
        touch_kind=kind,
        touched_hunks=[
            Hunk(old_start=1, old_lines=1, new_start=1, new_lines=1)
        ],
    )


def _novel_one() -> CandidateAC:
    return CandidateAC(
        file_path=Path("src/new.py"),
        hunks=[Hunk(old_start=1, old_lines=0, new_start=1, new_lines=5)],
    )


# ---- 13-cell coverage ------------------------------------------------


# Cells 1-3: VERIFIED-touched, all profiles → HARD_BLOCK + req_ratification=True.

def test_cell_1_verified_production_stake():
    cls = ClassificationResult(touched_acs=[_touched(_verified_ac())])
    d = decide(cls, safety_profile="production-stake")
    assert d.action is GateAction.HARD_BLOCK
    assert d.requires_ratification is True


def test_cell_2_verified_dev():
    cls = ClassificationResult(touched_acs=[_touched(_verified_ac())])
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.HARD_BLOCK
    assert d.requires_ratification is True


def test_cell_3_verified_research():
    cls = ClassificationResult(touched_acs=[_touched(_verified_ac())])
    d = decide(cls, safety_profile="research")
    assert d.action is GateAction.HARD_BLOCK
    assert d.requires_ratification is True


# Cells 4-6: PLAUSIBLE-touched (no VERIFIED) → SURFACE_DECISION; req per profile.

def test_cell_4_plausible_production_stake():
    cls = ClassificationResult(touched_acs=[_touched(_plausible_ac())])
    d = decide(cls, safety_profile="production-stake")
    assert d.action is GateAction.SURFACE_DECISION
    assert d.requires_ratification is True
    assert len(d.pm_batch_pairs) == 1


def test_cell_5_plausible_dev_default():
    cls = ClassificationResult(touched_acs=[_touched(_plausible_ac())])
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.SURFACE_DECISION
    assert d.requires_ratification is False
    assert len(d.pm_batch_pairs) == 1


def test_cell_5b_plausible_dev_with_require_ratification():
    cls = ClassificationResult(touched_acs=[_touched(_plausible_ac())])
    d = decide(
        cls,
        safety_profile="dev",
        require_ratification=True,
    )
    assert d.action is GateAction.SURFACE_DECISION
    assert d.requires_ratification is True


def test_cell_6_plausible_research():
    cls = ClassificationResult(touched_acs=[_touched(_plausible_ac())])
    d = decide(cls, safety_profile="research")
    assert d.action is GateAction.SURFACE_DECISION
    assert d.requires_ratification is False


# Cells 7-9: HYPOTHESISED-touched → DOCS_ONLY; never blocks.

def test_cell_7_hypothesised_production_stake():
    cls = ClassificationResult(
        touched_acs=[_touched(_hypothesised_ac(), kind="backing_file")]
    )
    d = decide(cls, safety_profile="production-stake")
    assert d.action is GateAction.DOCS_ONLY
    assert d.requires_ratification is False


def test_cell_8_hypothesised_dev():
    cls = ClassificationResult(
        touched_acs=[_touched(_hypothesised_ac(), kind="backing_file")]
    )
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.DOCS_ONLY
    assert d.requires_ratification is False


def test_cell_9_hypothesised_research():
    cls = ClassificationResult(
        touched_acs=[_touched(_hypothesised_ac(), kind="backing_file")]
    )
    d = decide(cls, safety_profile="research")
    assert d.action is GateAction.DOCS_ONLY


# Cells 10-12: novel-only → SURFACE_DECISION; req per profile.

def test_cell_10_novel_production_stake():
    cls = ClassificationResult(novel=[_novel_one()], untouched=False)
    d = decide(cls, safety_profile="production-stake")
    assert d.action is GateAction.SURFACE_DECISION
    assert d.requires_ratification is True


def test_cell_11_novel_dev():
    cls = ClassificationResult(novel=[_novel_one()], untouched=False)
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.SURFACE_DECISION
    assert d.requires_ratification is False


def test_cell_12_novel_research():
    cls = ClassificationResult(novel=[_novel_one()], untouched=False)
    d = decide(cls, safety_profile="research")
    assert d.action is GateAction.SURFACE_DECISION


# Cell 13: untouched → PASS.

def test_cell_13_untouched_pass():
    cls = ClassificationResult(untouched=True)
    for profile in ("production-stake", "dev", "research"):
        d = decide(cls, safety_profile=profile)
        assert d.action is GateAction.PASS
        assert d.requires_ratification is False


# ---- 6 mixed-touch pre-emption rules ---------------------------------


def test_mixed_verified_plus_plausible_pre_empt():
    """VERIFIED + PLAUSIBLE → HARD_BLOCK."""
    cls = ClassificationResult(
        touched_acs=[
            _touched(_verified_ac()),
            _touched(_plausible_ac()),
        ]
    )
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.HARD_BLOCK


def test_mixed_verified_plus_hypothesised_pre_empt():
    cls = ClassificationResult(
        touched_acs=[
            _touched(_verified_ac()),
            _touched(_hypothesised_ac(), kind="backing_file"),
        ]
    )
    d = decide(cls, safety_profile="research")
    assert d.action is GateAction.HARD_BLOCK


def test_mixed_verified_plus_novel_pre_empt():
    cls = ClassificationResult(
        touched_acs=[_touched(_verified_ac())],
        novel=[_novel_one()],
        untouched=False,
    )
    d = decide(cls, safety_profile="production-stake")
    assert d.action is GateAction.HARD_BLOCK


def test_mixed_plausible_plus_hypothesised_pre_empt():
    """PLAUSIBLE + HYPOTHESISED → SURFACE_DECISION."""
    cls = ClassificationResult(
        touched_acs=[
            _touched(_plausible_ac()),
            _touched(_hypothesised_ac(), kind="backing_file"),
        ]
    )
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.SURFACE_DECISION


def test_mixed_plausible_plus_novel_pre_empt():
    """PLAUSIBLE + novel → SURFACE_DECISION (consolidated batch)."""
    cls = ClassificationResult(
        touched_acs=[_touched(_plausible_ac())],
        novel=[_novel_one()],
        untouched=False,
    )
    d = decide(cls, safety_profile="production-stake")
    assert d.action is GateAction.SURFACE_DECISION
    # Plausible question + novel question = 2 PM batch entries.
    assert len(d.pm_batch_pairs) == 2


def test_mixed_hypothesised_plus_novel_pre_empt():
    """HYPOTHESISED + novel → SURFACE_DECISION (novel pre-empts DOCS_ONLY)."""
    cls = ClassificationResult(
        touched_acs=[_touched(_hypothesised_ac(), kind="backing_file")],
        novel=[_novel_one()],
        untouched=False,
    )
    d = decide(cls, safety_profile="dev")
    assert d.action is GateAction.SURFACE_DECISION


# ---- Additional invariant tests --------------------------------------


def test_decision_carries_safety_profile():
    cls = ClassificationResult(untouched=True)
    d = decide(cls, safety_profile="production-stake")
    assert d.safety_profile == "production-stake"


def test_decision_pass_has_empty_pm_batch():
    cls = ClassificationResult(untouched=True)
    d = decide(cls, safety_profile="dev")
    assert d.pm_batch_pairs == []


def test_decision_audit_payload_populated():
    cls = ClassificationResult(touched_acs=[_touched(_verified_ac("AC.X.1"))])
    d = decide(cls, safety_profile="dev")
    assert d.audit_payload["decision"] == GateAction.HARD_BLOCK.value
    assert "AC.X.1" in d.audit_payload["verified_ac_ids"]
