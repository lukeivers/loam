"""AC.PERSONA-PULL.3 — Composition with v0.2.3 ratification.

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.PERSONA-PULL.3:

- HYPOTHESISED objectives flagged in rationale prefix; not blocked
  from ranking.
- PLAUSIBLE / VERIFIED ranked normally.
- Ordering preserved.
"""

from __future__ import annotations

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    Gap,
    GapInventory,
    GapSummary,
    Objective,
    ObjectiveEvidence,
    score_candidates,
)
from loam_odd_extractor.bands import ConfidenceBand


def _make_objective(
    oid: str,
    *,
    band: ConfidenceBand,
) -> Objective:
    if band is ConfidenceBand.HYPOTHESISED:
        ev = ObjectiveEvidence(rationale="hypothesised — pattern-only inference")
    elif band is ConfidenceBand.VERIFIED:
        ev = ObjectiveEvidence(
            readme_excerpts=["Stated outcome"],
            test_name_refs=["test_outcome"],
            repo_sha="abc123",
        )
    else:  # PLAUSIBLE
        ev = ObjectiveEvidence(readme_excerpts=["Stated outcome plausible"])
    return Objective(
        objective_id=oid,
        text="Operators see audit trail outcomes for SOC-2 readiness review.",
        confidence=band,
        domain="security",
        source="extracted",
        evidence=ev,
    )


def _make_gap(oid: str, *, confidence: str = "STRONG") -> Gap:
    return Gap(
        gap_id=f"G.BACKING.{oid.lower().replace('.', '-')}",
        category="objective_without_verified_backing",
        confidence=confidence,
        objective_id=oid,
        evidence_rows=[],
        rationale=(
            f"Objective {oid} flagged as backing gap — empty backing-map "
            "entry; no implementation evidence rows are claimed by it."
        ),
    )


def test_hypothesised_flagged_in_rationale_prefix():
    obj_h = _make_objective("O.h.1", band=ConfidenceBand.HYPOTHESISED)
    obj_p = _make_objective("O.p.1", band=ConfidenceBand.PLAUSIBLE)
    obj_v = _make_objective("O.v.1", band=ConfidenceBand.VERIFIED)
    gap_h = _make_gap("O.h.1")
    gap_p = _make_gap("O.p.1")
    gap_v = _make_gap("O.v.1")

    aug = AugmentedObjectiveSet(
        extraction_id="rat-test",
        augmented_at="2026-05-04T00:00:00+00:00",
        interview_audit_path="/tmp",
        objectives=[obj_h, obj_p, obj_v],
    )
    inv = GapInventory(
        extraction_id="rat-test",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path="/tmp",
        gaps=[gap_h, gap_p, gap_v],
        summary=GapSummary(
            category_a_count=3, strong_count=3, total=3,
        ),
    )
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="rat-test",
        audit_path="/tmp",
    )
    by_id = {c.gap_id: c for c in rec.candidates}

    # HYPOTHESISED-derived candidate carries the prefix.
    h = by_id["G.BACKING.o-h-1"]
    assert "HYPOTHESISED" in h.rationale
    assert "ratify via interview" in h.rationale.lower()

    # PLAUSIBLE / VERIFIED do NOT carry the prefix.
    p = by_id["G.BACKING.o-p-1"]
    assert "ratify via interview" not in p.rationale.lower()
    v = by_id["G.BACKING.o-v-1"]
    assert "ratify via interview" not in v.rationale.lower()


def test_hypothesised_not_blocked_from_ranking():
    """All three bands surface — none filtered out."""
    obj_h = _make_objective("O.h.1", band=ConfidenceBand.HYPOTHESISED)
    obj_p = _make_objective("O.p.1", band=ConfidenceBand.PLAUSIBLE)
    aug = AugmentedObjectiveSet(
        extraction_id="rat-test",
        augmented_at="2026-05-04T00:00:00+00:00",
        interview_audit_path="/tmp",
        objectives=[obj_h, obj_p],
    )
    inv = GapInventory(
        extraction_id="rat-test",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path="/tmp",
        gaps=[_make_gap("O.h.1"), _make_gap("O.p.1")],
        summary=GapSummary(
            category_a_count=2, strong_count=2, total=2,
        ),
    )
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="rat-test",
        audit_path="/tmp",
    )
    assert len(rec.candidates) == 2  # both retained


def test_ordering_independent_of_band():
    """Same composite formula applies regardless of band — ordering follows
    score, not band classification."""
    obj_h = _make_objective("O.h.1", band=ConfidenceBand.HYPOTHESISED)
    obj_v = _make_objective("O.v.1", band=ConfidenceBand.VERIFIED)
    aug = AugmentedObjectiveSet(
        extraction_id="rat-test",
        augmented_at="2026-05-04T00:00:00+00:00",
        interview_audit_path="/tmp",
        objectives=[obj_h, obj_v],
    )
    # HYPOTHESISED gap STRONG (gc=1.0); VERIFIED gap WEAK (gc=0.5)
    inv = GapInventory(
        extraction_id="rat-test",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path="/tmp",
        gaps=[_make_gap("O.h.1", confidence="STRONG"), _make_gap("O.v.1", confidence="WEAK")],
        summary=GapSummary(
            category_a_count=2, strong_count=1, weak_count=1, total=2,
        ),
    )
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="rat-test",
        audit_path="/tmp",
    )
    # HYPOTHESISED-STRONG ranks above VERIFIED-WEAK by score.
    assert rec.candidates[0].gap_id == "G.BACKING.o-h-1"
    assert rec.candidates[1].gap_id == "G.BACKING.o-v-1"
