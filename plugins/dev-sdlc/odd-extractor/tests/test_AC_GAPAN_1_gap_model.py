"""AC.GAPAN.1 — Gap Pydantic shape.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.1:

- ``gap_id`` regex ``^G\\.(BACKING|ORPHAN)\\.[a-z0-9_-]+$``.
- ``category`` Literal {objective_without_verified_backing,
  implementation_orphan}.
- ``confidence`` Literal {STRONG, WEAK}.
- ``objective_id: str | None`` — set for category-a, None for category-b.
- ``evidence_rows`` list (empty allowed for empty-backing category-a).
- ``rationale`` ≥20 chars.
- ``negative_alignment_evidence: list[EvidenceRowRef] | None`` default None.
- model_validator enforces category/objective_id invariants both directions.
- Round-trip via model_dump / model_validate.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import (
    EvidenceRowRef,
    Gap,
)


def _row() -> EvidenceRowRef:
    return EvidenceRowRef(
        evidence_row_id="route:src/foo.js:42",
        kind="route",
        path="src/foo.js",
        line_range=(42, 47),
        confidence="WEAK",
        language="jsts",
    )


def test_category_a_gap_round_trip() -> None:
    g = Gap(
        gap_id="G.BACKING.o-dispute-1",
        category="objective_without_verified_backing",
        confidence="STRONG",
        objective_id="O.dispute.1",
        evidence_rows=[],
        rationale="Objective O.dispute.1 has empty backing-map entry; STRONG gap.",
    )
    payload = g.model_dump(mode="json")
    g2 = Gap.model_validate(payload)
    assert g2.gap_id == g.gap_id
    assert g2.category == "objective_without_verified_backing"
    assert g2.confidence == "STRONG"
    assert g2.objective_id == "O.dispute.1"
    assert g2.negative_alignment_evidence is None


def test_category_b_gap_round_trip() -> None:
    g = Gap(
        gap_id="G.ORPHAN.src-orphan-route-js",
        category="implementation_orphan",
        confidence="WEAK",
        objective_id=None,
        evidence_rows=[_row()],
        rationale="Implementation orphan cluster at src/orphan-route.js (1 row).",
    )
    payload = g.model_dump(mode="json")
    g2 = Gap.model_validate(payload)
    assert g2.gap_id == g.gap_id
    assert g2.category == "implementation_orphan"
    assert g2.objective_id is None


def test_category_a_requires_objective_id() -> None:
    with pytest.raises(ValidationError) as exc:
        Gap(
            gap_id="G.BACKING.o-dispute-1",
            category="objective_without_verified_backing",
            confidence="STRONG",
            objective_id=None,
            rationale="Objective O.dispute.1 has empty backing-map entry; STRONG gap.",
        )
    assert "objective_id" in str(exc.value).lower()


def test_category_b_forbids_objective_id() -> None:
    with pytest.raises(ValidationError) as exc:
        Gap(
            gap_id="G.ORPHAN.foo",
            category="implementation_orphan",
            confidence="STRONG",
            objective_id="O.dispute.1",
            rationale="Implementation orphan must not carry objective_id.",
        )
    assert "objective_id" in str(exc.value).lower()


def test_rationale_min_length() -> None:
    with pytest.raises(ValidationError) as exc:
        Gap(
            gap_id="G.BACKING.o-x-1",
            category="objective_without_verified_backing",
            confidence="STRONG",
            objective_id="O.x.1",
            rationale="too short",  # < 20 chars
        )
    assert "rationale" in str(exc.value).lower()


def test_gap_id_regex_must_match() -> None:
    with pytest.raises(ValidationError) as exc:
        Gap(
            gap_id="badformat",
            category="objective_without_verified_backing",
            confidence="STRONG",
            objective_id="O.x.1",
            rationale="Test that gap_id regex is enforced strictly.",
        )
    assert "gap_id" in str(exc.value).lower()


def test_gap_id_regex_rejects_uppercase_in_slug() -> None:
    with pytest.raises(ValidationError):
        Gap(
            gap_id="G.BACKING.UPPERCASE",
            category="objective_without_verified_backing",
            confidence="STRONG",
            objective_id="O.x.1",
            rationale="Test that gap_id regex enforces lowercase slug part.",
        )


def test_negative_alignment_evidence_field_round_trip_when_populated() -> None:
    """Forward-compat shape works when v0.2.6+ would populate it."""
    g = Gap(
        gap_id="G.BACKING.o-x-1",
        category="objective_without_verified_backing",
        confidence="STRONG",
        objective_id="O.x.1",
        rationale="Forward-compat field carries v0.2.6+ negative-alignment evidence.",
        negative_alignment_evidence=[_row()],
    )
    payload = g.model_dump(mode="json")
    g2 = Gap.model_validate(payload)
    assert g2.negative_alignment_evidence is not None
    assert len(g2.negative_alignment_evidence) == 1
