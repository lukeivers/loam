"""AC.COMPINT.10 — Resumability across ``/clear`` + restart.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.10:

- Mid-interview interrupt → re-invoking reads state.yaml +
  decision-queue.yaml + audit-log; reconstructs from PM's crash-safe
  surface.
- Augmented set updated AFTER each ``record_response`` (per-response,
  not per batch end) → partial state durable.
- Already-answered questions are no longer in the FIFO queue
  (consume-on-surface contract).
- Mid-LLM-judge interrupt re-runs LLM call (heuristic priors cached
  via audit-log; LLM call fresh).

The full PM crash-safety surface is provided by v0.1.7 itself; this
test exercises the consumer-side resume logic — that we don't re-ask
already-answered questions when the run is restarted.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    load_augmented_objectives,
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


def _baseline(ext_dir: Path, objs: list[Objective]) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )


class _KillAfter:
    """Response producer that raises after N answers — simulates kill -TERM."""

    def __init__(self, answers: list[str], kill_after: int) -> None:
        self.answers = answers
        self.kill_after = kill_after
        self.calls = 0

    def __call__(self, sq) -> str:
        if self.calls >= self.kill_after:
            raise RuntimeError("simulated kill -TERM")
        ans = self.answers[self.calls]
        self.calls += 1
        return ans


def test_per_response_durability_writes_after_each_record(tmp_path: Path) -> None:
    """After each record_response, the augmented set on disk reflects
    the latest mutation. (Implementation detail; structural guarantee.)
    """
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = _baseline(ext_dir, [_make_objective(1), _make_objective(2)])

    # Use a kill-after-1 producer; this raises on the 2nd surface.
    producer = _KillAfter(
        answers=["3 not relevant to the project", "1", "no"],
        kill_after=1,
    )

    try:
        run_interview(
            workspace_root=tmp_path,
            extraction_dir_=ext_dir,
            extraction_id="repo-1",
            pm=pm,
            augmented_set_in=aug,
            flagged_missing=[],
            response_producer=producer,
        )
    except RuntimeError:
        pass  # expected — simulated kill

    # After 1st answer (flag-out), the augmented set on disk should
    # have 1 objective (the second; first was removed).
    on_disk = load_augmented_objectives(ext_dir)
    assert on_disk is not None
    ids = {o.objective_id for o in on_disk.objectives}
    assert "O.dispute-flow.1" not in ids


def test_resume_does_not_re_ask_already_answered_objective(tmp_path: Path) -> None:
    """Run 1 answers Q1 only (kill); run 2 sees Q1 in audit-log + skip."""
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm1 = StubPM(audit_root=ext_dir / "audit-log")
    aug = _baseline(ext_dir, [_make_objective(1), _make_objective(2)])

    producer = _KillAfter(
        answers=["1", "1", "no"],
        kill_after=1,
    )

    try:
        run_interview(
            workspace_root=tmp_path,
            extraction_dir_=ext_dir,
            extraction_id="repo-1",
            pm=pm1,
            augmented_set_in=aug,
            flagged_missing=[],
            response_producer=producer,
        )
    except RuntimeError:
        pass

    # After kill: O.dispute-flow.1 was confirmed (audit-logged); the
    # augmented-objectives.yaml was written with it.

    # Run 2 — fresh PM (the real PM persists the FIFO queue but our
    # stub is in-memory; the resume defence is in the consumer's
    # audit-log scan so the consumer should NOT re-enqueue Q1).
    pm2 = StubPM(audit_root=ext_dir / "audit-log")
    answers_2 = iter(["1", "no"])  # only Q2 + free-form

    def producer2(sq):
        return next(answers_2)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm2,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer2,
    )

    # Re-enqueued plan should NOT include O.dispute-flow.1 — it was
    # already confirmed in the prior run.
    confirms_re_enqueued = [
        prov for _, prov in pm2.enqueued
        if prov and prov.startswith("completeness_interview:confirm_existing:")
    ]
    assert "completeness_interview:confirm_existing:O.dispute-flow.1" not in confirms_re_enqueued
    # O.dispute-flow.2 SHOULD still be enqueued.
    assert "completeness_interview:confirm_existing:O.dispute-flow.2" in confirms_re_enqueued
    assert len(result.objectives) == 2


def test_resume_treats_existing_augmented_yaml_as_baseline(tmp_path: Path) -> None:
    """If an augmented-objectives.yaml exists with a free-form-added
    objective, restarting the interview preserves it."""
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm1 = StubPM(audit_root=ext_dir / "audit-log")
    aug = _baseline(ext_dir, [_make_objective(1)])

    free_text = (
        "the system continues to serve queued requests for at least "
        "60 seconds after a graceful shutdown signal"
    )
    answers = iter(["1", free_text])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm1,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer,
    )

    on_disk = load_augmented_objectives(ext_dir)
    assert on_disk is not None
    assert any(o.source == "added_by_user" for o in on_disk.objectives)

    # Run 2 — empty FIFO; should NOT lose the user-added objective.
    pm2 = StubPM(audit_root=ext_dir / "audit-log")
    answers_2 = iter([])  # nothing should be asked

    def producer2(sq):
        # Should never be called; queue is empty after resume.
        raise AssertionError("Should not be asked anything on resume")

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id="repo-1",
        pm=pm2,
        augmented_set_in=aug,
        flagged_missing=[],
        response_producer=producer2,
    )

    # The user-added objective survives.
    assert any(o.source == "added_by_user" for o in result.objectives)


def test_resume_preserves_extraction_id_match_check(tmp_path: Path) -> None:
    """If the on-disk augmented set has a different extraction_id,
    resume falls back to the input baseline (no cross-extraction leak)."""
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")

    # Plant a stale augmented set with a different extraction_id.
    stale = AugmentedObjectiveSet(
        extraction_id="DIFFERENT-REPO",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=[_make_objective(99)],
    )
    from loam_odd_extractor import save_augmented_objectives
    save_augmented_objectives(stale, ext_dir)

    aug = _baseline(ext_dir, [_make_objective(1)])
    answers = iter(["1", "no"])

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
    # Stale O.dispute-flow.99 must NOT be in the result.
    ids = {o.objective_id for o in result.objectives}
    assert "O.dispute-flow.99" not in ids
    assert "O.dispute-flow.1" in ids
