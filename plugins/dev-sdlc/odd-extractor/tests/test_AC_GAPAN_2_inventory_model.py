"""AC.GAPAN.2 — GapInventory container Pydantic.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.2:

- Container with schema_version: int = 1.
- extraction_id, analyzed_at, audit_path, gaps, summary fields.
- Nested GapSummary with category_a_count, category_b_count,
  strong_count, weak_count, total.
- model_validator enforces no duplicate gap_id AND summary aggregate
  match.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import (
    Gap,
    GapInventory,
    GapSummary,
)


def _gap(gap_id: str, category: str = "objective_without_verified_backing", confidence: str = "STRONG") -> Gap:
    return Gap(
        gap_id=gap_id,
        category=category,
        confidence=confidence,
        objective_id=("O.x.1" if category == "objective_without_verified_backing" else None),
        rationale="Round-trip rationale text long enough to satisfy minimum length.",
    )


def test_round_trip_empty() -> None:
    inv = GapInventory(
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
    )
    payload = inv.model_dump(mode="json")
    inv2 = GapInventory.model_validate(payload)
    assert inv2.extraction_id == "repo-1"
    assert inv2.gaps == []
    assert inv2.summary.total == 0


def test_round_trip_with_gaps() -> None:
    g1 = _gap("G.BACKING.o-1", "objective_without_verified_backing", "STRONG")
    g2 = _gap("G.ORPHAN.src-foo-js", "implementation_orphan", "WEAK")
    inv = GapInventory(
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
        gaps=[g1, g2],
        summary=GapSummary(
            category_a_count=1,
            category_b_count=1,
            strong_count=1,
            weak_count=1,
            total=2,
        ),
    )
    inv2 = GapInventory.model_validate(inv.model_dump(mode="json"))
    assert inv2.summary.total == 2
    assert {g.gap_id for g in inv2.gaps} == {"G.BACKING.o-1", "G.ORPHAN.src-foo-js"}


def test_duplicate_gap_id_rejected() -> None:
    g1 = _gap("G.BACKING.dup")
    g2 = _gap("G.BACKING.dup")
    with pytest.raises(ValidationError) as exc:
        GapInventory(
            extraction_id="repo-1",
            analyzed_at="2026-05-04T16:00:00+00:00",
            audit_path="/tmp/audit",
            gaps=[g1, g2],
            summary=GapSummary(
                category_a_count=2, category_b_count=0,
                strong_count=2, weak_count=0, total=2,
            ),
        )
    assert "duplicate" in str(exc.value).lower()


def test_summary_mismatch_rejected() -> None:
    g1 = _gap("G.BACKING.o-1", "objective_without_verified_backing", "STRONG")
    with pytest.raises(ValidationError) as exc:
        GapInventory(
            extraction_id="repo-1",
            analyzed_at="2026-05-04T16:00:00+00:00",
            audit_path="/tmp/audit",
            gaps=[g1],
            # Wrong: total=2 but only 1 gap.
            summary=GapSummary(
                category_a_count=1, category_b_count=1,
                strong_count=1, weak_count=1, total=2,
            ),
        )
    assert "summary mismatch" in str(exc.value).lower()


def test_schema_version_pinned_to_one() -> None:
    """schema_version Literal[1] — non-1 values fail validation."""
    inv = GapInventory(
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
    )
    payload = inv.model_dump(mode="json")
    payload["schema_version"] = 2
    with pytest.raises(ValidationError):
        GapInventory.model_validate(payload)


def test_extra_fields_forbidden() -> None:
    payload = {
        "schema_version": 1,
        "extraction_id": "repo-1",
        "analyzed_at": "2026-05-04T16:00:00+00:00",
        "audit_path": "/tmp/audit",
        "gaps": [],
        "summary": {
            "category_a_count": 0, "category_b_count": 0,
            "strong_count": 0, "weak_count": 0, "total": 0,
        },
        "spurious_field": "rejected",
    }
    with pytest.raises(ValidationError):
        GapInventory.model_validate(payload)
