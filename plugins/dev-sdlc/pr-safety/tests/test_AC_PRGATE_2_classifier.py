"""AC.PRGATE.2 — Classifier consumes backing-map at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.PRGATE.2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_pr_safety import (
    BandedContract,
    ClassificationResult,
    Diff,
    DiffEntry,
    Hunk,
    NovelDiff,
    TouchedObjective,
    classify,
    read_contract,
)


def _make_diff(file_path: str, hunks: list[tuple[int, int]]) -> Diff:
    """Build a synthetic Diff: file_path with hunks
    [(new_start, new_lines), ...].
    """
    return Diff(
        from_sha="prior",
        to_sha="HEAD",
        entries=[
            DiffEntry(
                file_path=Path(file_path),
                hunks=[
                    Hunk(
                        old_start=ns,
                        old_lines=nl,
                        new_start=ns,
                        new_lines=nl,
                    )
                    for ns, nl in hunks
                ],
            )
        ],
    )


def test_hunk_inside_evidence_line_range_marks_evidence_line_touch(
    workspace_with_objectives,
):
    """Diff hunk overlapping a backing-row's line_range → TouchedObjective(touch_kind=evidence_line)."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    # O.auth.1 has backing row app/auth.py:10-25.
    diff = _make_diff("app/auth.py", [(15, 3)])  # within 10-25
    result = classify(diff, contract)
    assert isinstance(result, ClassificationResult)
    assert len(result.touched_objectives) == 1
    t = result.touched_objectives[0]
    assert t.objective.objective_id == "O.auth.1"
    assert t.touch_kind == "evidence_line"
    assert len(t.touched_evidence_rows) >= 1
    assert result.untouched is False


def test_unmapped_file_marks_novel_diff(workspace_with_objectives):
    """Diff in file not in any backing row → NovelDiff."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    diff = _make_diff("src/new-feature.py", [(1, 50)])
    result = classify(diff, contract)
    assert len(result.novel) == 1
    assert isinstance(result.novel[0], NovelDiff)
    assert str(result.novel[0].file_path) == "src/new-feature.py"
    assert result.touched_objectives == []


def test_no_overlap_marks_untouched(workspace_with_objectives):
    """Diff whose hunk doesn't overlap any backing row → untouched=True."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    # app/auth.py:10-25 is the backing row; hunk at 100 is far outside.
    diff = _make_diff("app/auth.py", [(100, 1)])
    result = classify(diff, contract)
    # File is mapped — so the hunk-on-uncovered-lines case is PASS
    # (not novel; not touched).
    assert result.touched_objectives == []
    assert result.novel == []
    assert result.untouched is True


def test_hunk_at_range_boundary_intersects(workspace_with_objectives):
    """Hunk exactly on the end of a line range counts as intersecting."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    # backing row 10-25; hunk at 25,1.
    diff = _make_diff("app/auth.py", [(25, 1)])
    result = classify(diff, contract)
    assert len(result.touched_objectives) == 1


def test_multiple_objectives_touched(workspace_with_objectives):
    """Diff hitting multiple files maps to multiple objectives."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    # Touch O.auth.1 (app/auth.py:10-25) AND O.orders.1 (app/models/order.rb:12-25).
    diff = Diff(
        from_sha="prior",
        to_sha="HEAD",
        entries=[
            DiffEntry(
                file_path=Path("app/auth.py"),
                hunks=[
                    Hunk(old_start=15, old_lines=3, new_start=15, new_lines=3)
                ],
            ),
            DiffEntry(
                file_path=Path("app/models/order.rb"),
                hunks=[
                    Hunk(old_start=12, old_lines=2, new_start=12, new_lines=2)
                ],
            ),
        ],
    )
    result = classify(diff, contract)
    objective_ids = {
        t.objective.objective_id for t in result.touched_objectives
    }
    assert objective_ids == {"O.auth.1", "O.orders.1"}


def test_pure_addition_hunk_intersects_new_side(workspace_with_objectives):
    """Pure-addition hunk (old_lines=0) still intersects on new-side."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    # Pure-addition at line 15 of app/auth.py (within 10-25).
    diff = Diff(
        from_sha="prior",
        to_sha="HEAD",
        entries=[
            DiffEntry(
                file_path=Path("app/auth.py"),
                hunks=[
                    Hunk(
                        old_start=15,
                        old_lines=0,
                        new_start=15,
                        new_lines=3,
                        added_lines=["new line 1", "new line 2", "new line 3"],
                    )
                ],
            )
        ],
    )
    result = classify(diff, contract)
    assert len(result.touched_objectives) == 1
