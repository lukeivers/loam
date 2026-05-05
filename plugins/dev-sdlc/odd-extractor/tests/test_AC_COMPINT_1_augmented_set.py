"""AC.COMPINT.1 — Augmented-set Pydantic shape.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.1:

- Additive ``Objective.source`` Literal field with default
  ``"extracted"`` (round-trip safe).
- New :class:`AugmentedObjectiveSet` container with no-duplicate-
  ``objective_id`` ``model_validator``.
- Default ``source`` on legacy objectives; explicit ``source`` on
  new instances.
"""

from __future__ import annotations

import datetime as _dt

import pytest
from pydantic import ValidationError

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
)


def _make_obj(idx: int, *, source: str = "extracted") -> Objective:
    return Objective(
        objective_id=f"O.dispute-flow.{idx}",
        text=(
            "Operators file refund disputes against merchant portals "
            f"at scale (variant {idx})."
        ),
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        source=source,  # type: ignore[arg-type]
        evidence=ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
        ),
    )


def test_objective_source_defaults_to_extracted_on_legacy_construction() -> None:
    """Legacy v0.2.3 callers omit ``source``; default is ``extracted``."""
    legacy = Objective(
        objective_id="O.dispute-flow.99",
        text="Operators file refund disputes against merchant portals at scale.",
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
        ),
    )
    assert legacy.source == "extracted"


def test_objective_source_accepts_added_by_user_and_flagged_by_persona() -> None:
    a = _make_obj(1, source="added_by_user")
    b = _make_obj(2, source="flagged_by_persona")
    assert a.source == "added_by_user"
    assert b.source == "flagged_by_persona"


def test_objective_source_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        Objective(
            objective_id="O.dispute-flow.42",
            text="Operators file refund disputes against merchant portals.",
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="dispute-flow",
            source="bogus-source",  # type: ignore[arg-type]
            evidence=ObjectiveEvidence(
                readme_excerpts=["File refunds at scale"],
            ),
        )


def test_augmented_set_round_trip() -> None:
    objs = [_make_obj(1), _make_obj(2, source="added_by_user")]
    aug = AugmentedObjectiveSet(
        extraction_id="repo-id-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path="/tmp/audit-log",
        objectives=objs,
    )
    payload = aug.model_dump(mode="json")
    round_tripped = AugmentedObjectiveSet.model_validate(payload)
    assert len(round_tripped.objectives) == 2
    assert round_tripped.objectives[1].source == "added_by_user"


def test_augmented_set_rejects_duplicate_objective_id() -> None:
    objs = [_make_obj(1), _make_obj(1)]
    with pytest.raises(ValidationError):
        AugmentedObjectiveSet(
            extraction_id="repo-id-1",
            augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
            interview_audit_path="/tmp/audit-log",
            objectives=objs,
        )


def test_augmented_set_requires_non_empty_extraction_id() -> None:
    with pytest.raises(ValidationError):
        AugmentedObjectiveSet(
            extraction_id="",
            augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
            interview_audit_path="/tmp/audit-log",
            objectives=[],
        )


def test_augmented_set_schema_version_is_one() -> None:
    aug = AugmentedObjectiveSet(
        extraction_id="repo-id-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path="/tmp/audit-log",
        objectives=[],
    )
    assert aug.schema_version == 1
