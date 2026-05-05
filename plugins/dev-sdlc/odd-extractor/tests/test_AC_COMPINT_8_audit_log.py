"""AC.COMPINT.8 — Audit-log event_kinds.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.8:

- 7 new event_kinds: completeness_interview_start, objective_confirmed,
  objective_adjusted, objective_flagged_out_of_scope,
  objective_added_by_user, objective_flagged_by_persona,
  completeness_interview_end.
- Structured payloads via existing ``estimate`` field (no schema bump).
- Start payload: extraction_id + objective_count_pre +
  flagged_missing_count.
- Per-objective: objective_id + response_audit_path + response_text_hash
  (loose — tests check audit-path presence).
- End: extraction_id + objective_count_post + added/removed/adjusted.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    FlaggedMissing,
    Objective,
    ObjectiveEvidence,
    run_interview,
)
from loam_odd_extractor.observability import (
    COMPLETENESS_INTERVIEW_EVENT_KINDS,
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


def _read_audit_entries(audit_dir: Path) -> list[dict]:
    out: list[dict] = []
    if not audit_dir.exists():
        return out
    for f in sorted(audit_dir.iterdir()):
        if f.is_file() and f.name.endswith(".yaml"):
            payload = yaml.safe_load(f.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                out.append(payload)
    return out


def test_event_kinds_constant_is_seven_kinds() -> None:
    assert len(COMPLETENESS_INTERVIEW_EVENT_KINDS) == 7
    expected = {
        "completeness_interview_start",
        "objective_confirmed",
        "objective_adjusted",
        "objective_flagged_out_of_scope",
        "objective_added_by_user",
        "objective_flagged_by_persona",
        "completeness_interview_end",
    }
    assert set(COMPLETENESS_INTERVIEW_EVENT_KINDS) == expected


def test_start_event_payload_present(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=[_make_objective(1)],
    )
    answers = iter(["1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )
    entries = _read_audit_entries(ext_dir / "audit-log")
    starts = [e for e in entries if e["event_kind"] == "completeness_interview_start"]
    assert len(starts) == 1
    est = starts[0]["estimate"]
    assert est["extraction_id"] == "repo-1"
    assert est["objective_count_pre"] == 1
    assert est["flagged_missing_count"] == 0


def test_end_event_payload_present_with_counts(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=[_make_objective(1), _make_objective(2)],
    )

    answers = iter(["1", "1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )
    entries = _read_audit_entries(ext_dir / "audit-log")
    ends = [e for e in entries if e["event_kind"] == "completeness_interview_end"]
    assert len(ends) == 1
    est = ends[0]["estimate"]
    assert est["objective_count_post"] == 2
    assert est["confirmed_count"] == 2
    assert est["added_count"] == 0
    assert est["removed_count"] == 0


def test_full_action_set_emits_each_event_kind(tmp_path: Path) -> None:
    """Exercise confirm + adjust + flag-out + flagged-by-persona + added-by-user paths."""
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=[
            _make_objective(1),  # confirm
            _make_objective(2),  # adjust
            _make_objective(3),  # flag-out
        ],
    )
    flagged = [
        FlaggedMissing(
            candidate_text="Audit trail identifies who initiated each dispute filing for SOC-2.",
            reasoning="No audit-domain objective.",
            evidence_refs=["survey:Q5"],
            priority="high",
            domain="audit",
        )
    ]
    adjust = "2 the operators file refund disputes against merchant portals at MASSIVE scale"
    flag_out = "3 not relevant to product"
    free_form = (
        "the system continues to serve queued requests for at least "
        "60 seconds after a graceful shutdown signal"
    )
    answers = iter(["1", adjust, flag_out, "1", free_form])

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

    entries = _read_audit_entries(ext_dir / "audit-log")
    seen = {e["event_kind"] for e in entries}
    # All 7 event_kinds should be present at least once across this run.
    for kind in COMPLETENESS_INTERVIEW_EVENT_KINDS:
        assert kind in seen, f"missing event_kind {kind}; saw {seen}"


def test_per_objective_event_carries_objective_id_and_audit_ref(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=[_make_objective(1)],
    )
    answers = iter(["1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )
    entries = _read_audit_entries(ext_dir / "audit-log")
    confirmed = [e for e in entries if e["event_kind"] == "objective_confirmed"]
    assert len(confirmed) >= 1
    est = confirmed[0]["estimate"]
    assert est.get("objective_id") == "O.dispute-flow.1"
    assert "response_audit_path" in est
