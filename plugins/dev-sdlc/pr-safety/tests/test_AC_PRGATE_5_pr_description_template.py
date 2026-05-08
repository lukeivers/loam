"""AC.PRGATE.5 — PR description template at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.PRGATE.5.

Template renders objective TEXT + band + backing rows path:line.
AC.* IDs DO NOT appear (regression guard against legacy leak).
"""

from __future__ import annotations

import re
from pathlib import Path


from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.spec import EvidenceRowRef, Objective, ObjectiveEvidence

from loam_pr_safety import (
    GateAction,
    GateDecision,
    Hunk,
    NovelDiff,
    TouchedObjective,
)
from loam_pr_safety.installers.pr_template import render_pr_description


def _decision_with_verified_touched() -> GateDecision:
    obj = Objective(
        objective_id="O.dispute-flow.1",
        text=(
            "Operators file refund disputes against DoorDash + Uber Eats "
            "merchant portals at scale, replacing manual portal clickwork."
        ),
        confidence=ConfidenceBand.VERIFIED,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            readme_excerpts=["Disputes are filed at scale"],
            test_name_refs=["tests/test_disputes.py::test_file_dispute"],
            repo_sha="abc1234567890def",
        ),
    )
    touched = TouchedObjective(
        objective=obj,
        touch_kind="evidence_line",
        touched_evidence_rows=[
            EvidenceRowRef(
                evidence_row_id="route:src/routes/disputeRoutes.js:42-58",
                kind="route",
                path="src/routes/disputeRoutes.js",
                line_range=[42, 58],
            )
        ],
        touched_hunks=[
            Hunk(old_start=45, old_lines=3, new_start=45, new_lines=3)
        ],
    )
    return GateDecision(
        action=GateAction.HARD_BLOCK,
        requires_ratification=True,
        touched_objectives=[touched],
        novel=[],
        safety_profile="dev",
        reason="HARD_BLOCK — diff touches VERIFIED objective.",
        pm_batch_pairs=[],
    )


def test_render_renders_objective_text_and_backing_rows(tmp_workspace):
    """Rendered PR description carries objective text + backing row path:line."""
    decision = _decision_with_verified_touched()
    md = render_pr_description(
        decision, workspace_root=tmp_workspace, repo_id="test-repo"
    )
    # Objective text appears.
    assert "operators file refund disputes" in md.lower()
    # Backing row path:line appears.
    assert "src/routes/disputeRoutes.js:42-58" in md
    # Band appears.
    assert "VERIFIED" in md
    # Domain appears.
    assert "dispute-flow" in md


def test_render_excludes_legacy_ac_ids(tmp_workspace):
    """No AC.* ID in rendered output (regression guard)."""
    decision = _decision_with_verified_touched()
    md = render_pr_description(
        decision, workspace_root=tmp_workspace, repo_id="test-repo"
    )
    # Match `AC.<UPPER>.<n>` pattern; objective IDs use O. prefix.
    assert not re.search(r"\bAC\.[A-Z]+\.[0-9]+", md), (
        f"Legacy AC.* ID found in rendered output: {md!r}"
    )


def test_render_includes_touched_objectives_section_header(tmp_workspace):
    """Section is "Touched objectives" not "ACs touched"."""
    decision = _decision_with_verified_touched()
    md = render_pr_description(
        decision, workspace_root=tmp_workspace, repo_id="test-repo"
    )
    assert "Touched objectives" in md
    assert "ACs touched" not in md


def test_render_with_novel_diff(tmp_workspace):
    """Novel diff section uses 'Novel diffs' header (not 'Novel candidates')."""
    decision = GateDecision(
        action=GateAction.SURFACE_DECISION,
        requires_ratification=False,
        touched_objectives=[],
        novel=[
            NovelDiff(
                file_path=Path("src/new-feature.ts"),
                hunks=[Hunk(old_start=1, old_lines=0, new_start=1, new_lines=20)],
            )
        ],
        safety_profile="dev",
        reason="novel hunks",
        pm_batch_pairs=[],
    )
    md = render_pr_description(
        decision, workspace_root=tmp_workspace, repo_id="test-repo"
    )
    assert "Novel diffs" in md
    assert "src/new-feature.ts" in md
    # Should not say 'Novel candidates' (legacy v0.1.9 phrasing).
    assert "Novel candidates" not in md


def test_render_overflow_truncation(tmp_workspace):
    """Many touched objectives → truncation kicks in."""
    # Build 100 touched objectives to force overflow.
    touched_list = []
    for i in range(100):
        obj = Objective(
            objective_id=f"O.test-domain.{i + 1}",
            text=(
                "Operators do something verifiable in the system that "
                "passes the implementation-rewrite test " * 5
            ),
            confidence=ConfidenceBand.VERIFIED,
            domain="test-domain",
            evidence=ObjectiveEvidence(
                readme_excerpts=["x" * 1000],
                test_name_refs=["tests/test.py::test_x"],
                repo_sha="abc1234567890def",
            ),
        )
        touched_list.append(
            TouchedObjective(
                objective=obj,
                touch_kind="evidence_line",
                touched_evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id=f"route:src/file{i}.py:1-{i}",
                        kind="route",
                        path=f"src/file{i}.py",
                        line_range=[1, max(1, i)],
                    )
                ],
                touched_hunks=[
                    Hunk(old_start=1, old_lines=1, new_start=1, new_lines=1)
                ],
            )
        )
    decision = GateDecision(
        action=GateAction.HARD_BLOCK,
        requires_ratification=True,
        touched_objectives=touched_list,
        novel=[],
        safety_profile="dev",
        reason="many touches",
        pm_batch_pairs=[],
    )
    md = render_pr_description(
        decision, workspace_root=tmp_workspace, repo_id="test-repo"
    )
    # Must stay under the 60K ceiling (with footer headroom).
    assert len(md) <= 60_000
