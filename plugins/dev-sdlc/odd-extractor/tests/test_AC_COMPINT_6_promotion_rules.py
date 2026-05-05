"""AC.COMPINT.6 — Promotion rules + interview-added defaults.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.6:

- Shape (b)(1) yes-add-as-PLAUSIBLE → ``source="flagged_by_persona"``,
  ``confidence=PLAUSIBLE``, ``survey_line_refs`` populated from
  audit-log entry.
- Shape (b)(2) yes-but-rewrite → ``source="added_by_user"``.
- Shape (a)(2) yes-but-adjust-text → in-place text update;
  ``source`` preserved.
- Shape (a)(3) no-flag-out-of-scope → removed from set.
- Shape (c) free-form-add → ``source="added_by_user"``,
  ``confidence=PLAUSIBLE``.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    FlaggedMissing,
    Objective,
    ObjectiveEvidence,
    run_interview,
)

from _compint_pm_stub import StubPM


def _make_objective(idx: int = 1) -> Objective:
    return Objective(
        objective_id=f"O.dispute-flow.{idx}",
        text=f"Operators file refund disputes against merchant portals (variant {idx}).",
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
        ),
    )


def _make_flagged() -> FlaggedMissing:
    return FlaggedMissing(
        candidate_text="Audit trail identifies who initiated each dispute filing for SOC-2 CC6.",
        reasoning="No audit-domain objective.",
        evidence_refs=["survey:Q5"],
        priority="high",
        domain="audit",
    )


def _baseline(ext_dir: Path, objs: list[Objective]) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )


def test_shape_b_1_yes_add_persists_with_flagged_by_persona_source(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = [_make_objective(1)]
    flagged = [_make_flagged()]
    aug = _baseline(ext_dir, objs)

    answers = iter(["1", "1", "no"])  # confirm O.1; add flagged; no-free-form

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    added = [o for o in result.objectives if o.source == "flagged_by_persona"]
    assert len(added) == 1
    a = added[0]
    assert a.confidence == ConfidenceBand.PLAUSIBLE
    assert a.evidence.survey_line_refs  # populated from audit-log


def test_shape_b_2_rewrite_records_source_added_by_user(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = [_make_objective(1)]
    flagged = [_make_flagged()]
    aug = _baseline(ext_dir, objs)

    rewrite_text = (
        "2 my own version: ensure every dispute action is reviewable "
        "by an authorised auditor and traceable to the initiating user"
    )
    answers = iter(["1", rewrite_text, "no"])

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    added = [o for o in result.objectives if o.source == "added_by_user"]
    assert len(added) == 1
    assert "reviewable" in added[0].text


def test_shape_a_2_adjust_text_preserves_source_extracted(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = [_make_objective(1)]
    aug = _baseline(ext_dir, objs)

    adjust_text = (
        "2 the operators file refund disputes against merchant portals "
        "ALL DAY LONG WITH GREAT EFFICIENCY"
    )
    answers = iter([adjust_text, "no"])

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )
    obj = next(o for o in result.objectives if o.objective_id == "O.dispute-flow.1")
    assert obj.source == "extracted"  # preserved
    assert "ALL DAY LONG" in obj.text


def test_shape_a_3_flag_out_of_scope_removes_objective(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = [_make_objective(1), _make_objective(2)]
    aug = _baseline(ext_dir, objs)

    answers = iter(["3 not relevant to the project", "1", "no"])

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )
    ids = {o.objective_id for o in result.objectives}
    assert "O.dispute-flow.1" not in ids
    assert "O.dispute-flow.2" in ids


def test_shape_c_free_form_add_records_source_added_by_user(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = [_make_objective(1)]
    aug = _baseline(ext_dir, objs)

    free_text = (
        "the system continues to serve queued requests for at least "
        "60 seconds after a graceful shutdown signal"
    )
    answers = iter(["1", free_text])

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )
    added = [o for o in result.objectives if o.source == "added_by_user"]
    assert len(added) == 1
    assert added[0].confidence == ConfidenceBand.PLAUSIBLE
    assert "graceful shutdown" in added[0].text


def test_added_objective_evidence_satisfies_PLAUSIBLE_invariant(tmp_path: Path) -> None:
    """Added objectives carry survey_line_refs (from audit-log entry)
    so the PLAUSIBLE invariant is structurally satisfied."""
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    objs = [_make_objective(1)]
    flagged = [_make_flagged()]
    aug = _baseline(ext_dir, objs)

    answers = iter(["1", "1", "no"])

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    for o in result.objectives:
        if o.source != "extracted":
            assert o.evidence.survey_line_refs, (
                f"Added objective {o.objective_id} must populate "
                "survey_line_refs from audit-log."
            )
