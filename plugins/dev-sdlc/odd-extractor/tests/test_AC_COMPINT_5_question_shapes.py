"""AC.COMPINT.5 — Question-shape design (3 shapes).

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.5:

- Shape (a) confirm-existing — 4 numeric options.
- Shape (b) flag-missing-candidate — 4 numeric options.
- Shape (c) free-form-add — surfaced ONCE at end; free-text response.
- Numeric-prefix response parser handles each branch.
- Malformed → one re-ask cap; second malformed → defer.
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
    parse_response,
    render_confirm_existing,
    render_flag_missing_candidate,
    render_free_form_add,
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


# ---- Shape rendering ----------------------------------------------


def test_shape_a_confirm_existing_renders_four_numeric_options() -> None:
    text = render_confirm_existing(_make_objective(1))
    assert "(1)" in text
    assert "(2)" in text
    assert "(3)" in text
    assert "(4)" in text
    assert "yes-keep" in text
    assert "yes-but-adjust-text" in text
    assert "no-flag-out-of-scope" in text
    assert "skip" in text
    # Carries the objective_id + text.
    assert "O.dispute-flow.1" in text


def test_shape_b_flag_missing_candidate_renders_four_numeric_options() -> None:
    cand = FlaggedMissing(
        candidate_text="Audit trail identifies who initiated each dispute.",
        reasoning="No audit-domain objective.",
        evidence_refs=["survey:Q5"],
        priority="high",
        domain="audit",
    )
    text = render_flag_missing_candidate(cand)
    assert "(1)" in text
    assert "(2)" in text
    assert "(3)" in text
    assert "(4)" in text
    assert "yes-add-as-PLAUSIBLE" in text
    assert "yes-but-rewrite" in text
    assert "no-skip" in text
    assert "defer" in text
    assert "Audit trail" in text


def test_shape_c_free_form_add_renders_once() -> None:
    text = render_free_form_add()
    assert "missed" in text.lower() or "any objectives" in text.lower()


# ---- Response parser ----------------------------------------------


def test_parse_response_extracts_numeric_choice() -> None:
    p = parse_response("1")
    assert p.choice == 1
    assert p.free_text == ""


def test_parse_response_handles_paren_form() -> None:
    p = parse_response("(2) here is my replacement text that is at least twenty characters")
    assert p.choice == 2
    assert "replacement" in p.free_text


def test_parse_response_handles_dot_form() -> None:
    p = parse_response("3. flag this out of scope")
    assert p.choice == 3
    assert "flag this" in p.free_text


def test_parse_response_returns_none_choice_on_free_text() -> None:
    p = parse_response("the system should preserve audit logs across restarts")
    assert p.choice is None
    assert "audit logs" in p.free_text


def test_parse_response_handles_empty_input() -> None:
    p = parse_response("")
    assert p.choice is None
    assert p.free_text == ""


# ---- Malformed re-ask cap (integration via run_interview) ---------


def test_malformed_response_triggers_re_ask_then_defer(tmp_path: Path) -> None:
    """Two consecutive malformed responses → defer audit entry."""
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=[_make_objective(1)],
    )

    # First answer: garbage non-numeric. Second answer: also garbage.
    # Then for the free-form-add, answer "no".
    answers = iter(["whatever", "still nothing useful", "no"])

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

    # Audit-log dir should contain a deferred entry.
    audit_dir = ext_dir / "audit-log"
    assert audit_dir.exists()
    deferred_found = False
    for entry in audit_dir.iterdir():
        text = entry.read_text(encoding="utf-8")
        if "deferred" in text or "deferred_after_malformed_re_ask" in text:
            deferred_found = True
            break
    assert deferred_found, (
        "Expected a deferred-for-human-review audit entry after "
        "two consecutive malformed responses."
    )
