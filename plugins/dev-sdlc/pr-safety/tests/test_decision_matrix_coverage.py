"""Decision-matrix coverage — every cell of the 13-cell matrix +
6 mixed-touch pre-emption rules + edge cases (per plan-doc §6).

This file is the integration-level coverage test; per-cell unit tests
live in test_AC_PRSG_4_decision_matrix.py. This file asserts the
combined surface — running the full decision matrix on a synthetic
classification and verifying every (touch-shape, profile) combination
produces the correct (action, requires_ratification) pair.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


def _verified_touch():
    ac = BandedAC(
        ac_id="AC.V",
        text="V",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["src/x.py:10"],
            repo_sha="abc",
        ),
        backing_files=["src/x.py"],
    )
    return TouchedAC(
        ac=ac,
        touch_kind="citation_line",
        touched_hunks=[Hunk(old_start=10, old_lines=1, new_start=10, new_lines=1)],
    )


def _plausible_touch():
    ac = BandedAC(
        ac_id="AC.P",
        text="P",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(kind="source", citations=["src/y.py:20"]),
        backing_files=["src/y.py"],
    )
    return TouchedAC(
        ac=ac,
        touch_kind="citation_line",
        touched_hunks=[Hunk(old_start=20, old_lines=1, new_start=20, new_lines=1)],
    )


def _hypothesised_touch():
    ac = BandedAC(
        ac_id="AC.H",
        text="H",
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(kind="inference", rationale="r"),
        backing_files=["src/z.py"],
    )
    return TouchedAC(
        ac=ac,
        touch_kind="backing_file",
        touched_hunks=[Hunk(old_start=1, old_lines=0, new_start=1, new_lines=5)],
    )


def _novel():
    return CandidateAC(
        file_path=Path("src/new.py"),
        hunks=[Hunk(old_start=1, old_lines=0, new_start=1, new_lines=5)],
    )


# (touched, novel, profile, expected_action, expected_req)
DECISION_MATRIX_CASES = [
    # ---- VERIFIED-touched (cells 1-3) ----
    ([_verified_touch()], [], "production-stake", GateAction.HARD_BLOCK, True),
    ([_verified_touch()], [], "dev", GateAction.HARD_BLOCK, True),
    ([_verified_touch()], [], "research", GateAction.HARD_BLOCK, True),

    # ---- PLAUSIBLE-touched (cells 4-6) ----
    ([_plausible_touch()], [], "production-stake", GateAction.SURFACE_DECISION, True),
    ([_plausible_touch()], [], "dev", GateAction.SURFACE_DECISION, False),
    ([_plausible_touch()], [], "research", GateAction.SURFACE_DECISION, False),

    # ---- HYPOTHESISED-touched (cells 7-9) ----
    ([_hypothesised_touch()], [], "production-stake", GateAction.DOCS_ONLY, False),
    ([_hypothesised_touch()], [], "dev", GateAction.DOCS_ONLY, False),
    ([_hypothesised_touch()], [], "research", GateAction.DOCS_ONLY, False),

    # ---- Novel-only (cells 10-12) ----
    ([], [_novel()], "production-stake", GateAction.SURFACE_DECISION, True),
    ([], [_novel()], "dev", GateAction.SURFACE_DECISION, False),
    ([], [_novel()], "research", GateAction.SURFACE_DECISION, False),

    # ---- Untouched (cell 13) ----
    ([], [], "production-stake", GateAction.PASS, False),
    ([], [], "dev", GateAction.PASS, False),
    ([], [], "research", GateAction.PASS, False),

    # ---- Mixed: VERIFIED+PLAUSIBLE → HARD_BLOCK ----
    ([_verified_touch(), _plausible_touch()], [], "dev", GateAction.HARD_BLOCK, True),
    # ---- Mixed: VERIFIED+HYPOTHESISED → HARD_BLOCK ----
    ([_verified_touch(), _hypothesised_touch()], [], "research", GateAction.HARD_BLOCK, True),
    # ---- Mixed: VERIFIED+novel → HARD_BLOCK ----
    ([_verified_touch()], [_novel()], "production-stake", GateAction.HARD_BLOCK, True),
    # ---- Mixed: PLAUSIBLE+HYPOTHESISED → SURFACE_DECISION ----
    ([_plausible_touch(), _hypothesised_touch()], [], "dev", GateAction.SURFACE_DECISION, False),
    # ---- Mixed: PLAUSIBLE+novel → SURFACE_DECISION ----
    ([_plausible_touch()], [_novel()], "production-stake", GateAction.SURFACE_DECISION, True),
    # ---- Mixed: HYPOTHESISED+novel → SURFACE_DECISION ----
    ([_hypothesised_touch()], [_novel()], "dev", GateAction.SURFACE_DECISION, False),
]


@pytest.mark.parametrize(
    "touched, novel, profile, expected_action, expected_req",
    DECISION_MATRIX_CASES,
)
def test_decision_matrix_cell(
    touched, novel, profile, expected_action, expected_req
):
    cls = ClassificationResult(
        touched_acs=touched,
        novel=novel,
        untouched=(not touched and not novel),
    )
    d = decide(cls, safety_profile=profile)
    assert d.action is expected_action, (
        f"profile={profile} touched={[t.ac.ac_id for t in touched]} "
        f"novel={len(novel)} → expected {expected_action}, got {d.action}"
    )
    assert d.requires_ratification is expected_req, (
        f"profile={profile} → expected req_ratification={expected_req}, "
        f"got {d.requires_ratification}"
    )
