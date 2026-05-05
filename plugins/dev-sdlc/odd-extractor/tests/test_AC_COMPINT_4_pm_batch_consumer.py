"""AC.COMPINT.4 — PM batch API consumer.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.4:

- Read-only consumption of the v0.1.7 PMRuntime surface; zero edits
  to ``framework/per-project-pm/``.
- ``surface_next_questions_batch(n=1)`` is the strict one-question-
  at-a-time mechanism — every call passes ``n=1``.
- Every enqueued decision carries provenance prefix
  ``completeness_interview:<kind>:<id>``.
- Every surfaced question gets a paired ``record_response`` call.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    FlaggedMissing,
    Objective,
    ObjectiveEvidence,
    run_interview,
)

from _compint_pm_stub import StubPM


def _objs(n: int = 2) -> list[Objective]:
    out: list[Objective] = []
    for i in range(1, n + 1):
        out.append(
            Objective(
                objective_id=f"O.dispute-flow.{i}",
                text=f"Operators file refund disputes against merchant portals (variant {i}).",
                confidence=ConfidenceBand.PLAUSIBLE,
                domain="dispute-flow",
                evidence=ObjectiveEvidence(
                    readme_excerpts=["File refunds at scale"],
                ),
            )
        )
    return out


def _flagged(n: int = 1) -> list[FlaggedMissing]:
    return [
        FlaggedMissing(
            candidate_text=(
                f"Audit trail identifies who initiated each dispute filing "
                f"(variant {i})."
            ),
            reasoning=f"Reasoning {i}",
            evidence_refs=["survey:Q5"],
            priority="high",
            domain="audit",
        )
        for i in range(1, n + 1)
    ]


def _aug(extraction_id: str, audit_path: str, objs: list[Objective]) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=audit_path,
        objectives=objs,
    )


def test_consumer_calls_surface_next_questions_batch_with_n1_each_time(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = _objs(2)
    flagged = _flagged(1)
    aug = _aug("repo-1", str(ext_dir / "audit-log"), objs)

    answers = iter(["1", "1", "1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    assert pm.surfaced_calls
    assert all(call == 1 for call in pm.surfaced_calls)


def test_consumer_enqueues_one_decision_per_objective_and_flagged(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = _objs(3)  # 3 confirm-existing
    flagged = _flagged(2)  # 2 flag-missing
    aug = _aug("repo-1", str(ext_dir / "audit-log"), objs)

    answers = iter(["1", "1", "1", "1", "1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    # 3 confirm + 2 flag + 1 free-form = 6 enqueues
    assert len(pm.enqueued) == 6


def test_consumer_provenance_carries_routing_prefix(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = _objs(1)
    flagged = _flagged(1)
    aug = _aug("repo-1", str(ext_dir / "audit-log"), objs)

    answers = iter(["1", "3", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    provenances = [p for _, p in pm.enqueued]
    assert any(
        p and p.startswith("completeness_interview:confirm_existing:")
        for p in provenances
    )
    assert any(
        p and p.startswith("completeness_interview:flag_missing:")
        for p in provenances
    )
    assert any(
        p and p.startswith("completeness_interview:free_form_add:")
        for p in provenances
    )


def test_consumer_records_response_for_every_surfaced_question(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = _objs(2)
    flagged = _flagged(1)
    aug = _aug("repo-1", str(ext_dir / "audit-log"), objs)

    answers = iter(["1", "1", "1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    # surfaced_calls == record count: every surfaced question recorded.
    # surfaced_calls includes the final empty-queue call which returns ();
    # only successful surfacings produce a record_response.
    successful_surfacings = sum(1 for _ in range(len(pm.surfaced_calls)) if True)  # noqa: F841
    # Better: equal to the number of surfaced questions = 2 obj + 1 flag + 1 free = 4.
    assert len(pm.recorded) == 4
