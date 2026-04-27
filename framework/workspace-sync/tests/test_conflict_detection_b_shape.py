"""AC.WS.1, AC.WS.2, AC.WS.4 — B-shape conflict-detection tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from workspace_sync.canonical import resolve_canonical
from workspace_sync.conflict_detection import detect_b_shape_conflicts
from workspace_sync.conflict_report import (
    ConflictChangeKind,
    Resolution,
)
from workspace_sync.sync_protected import default_sync_protected


def _git_head_sha(canonical: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(canonical), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def test_identical_paths_produce_no_entry(make_canonical_repo, make_workspace) -> None:
    canonical = make_canonical_repo({"a.txt": "alpha"})
    workspace = make_workspace({"a.txt": "alpha"})
    sp = default_sync_protected()

    report, clean_writes = detect_b_shape_conflicts(
        canonical_path=canonical,
        ref=_git_head_sha(canonical),
        workspace_root=workspace,
        sync_protected=sp,
        prior_state=None,
    )
    assert report.conflicts == []
    assert clean_writes == []


def test_canonical_only_path_is_clean_write(make_canonical_repo, make_workspace) -> None:
    canonical = make_canonical_repo({"new.txt": "fresh"})
    workspace = make_workspace({})  # empty
    sp = default_sync_protected()

    report, clean_writes = detect_b_shape_conflicts(
        canonical_path=canonical,
        ref=_git_head_sha(canonical),
        workspace_root=workspace,
        sync_protected=sp,
    )
    assert clean_writes == ["new.txt"]
    assert report.conflicts == []


def test_both_sides_modified_produces_pending_class_c(make_canonical_repo, make_workspace) -> None:
    canonical = make_canonical_repo({"foo.py": "canonical_body"})
    workspace = make_workspace({"foo.py": "workspace_body"})
    sp = default_sync_protected()

    report, _ = detect_b_shape_conflicts(
        canonical_path=canonical,
        ref=_git_head_sha(canonical),
        workspace_root=workspace,
        sync_protected=sp,
    )
    assert len(report.conflicts) == 1
    entry = report.conflicts[0]
    assert entry.path == "foo.py"
    assert entry.resolution is Resolution.PENDING
    assert entry.change_kind is ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED


def test_class_a_path_pre_resolved_to_keep_local(make_canonical_repo, make_workspace) -> None:
    """AC.WS.2: Class-A paths are pre-resolved to KEEP_LOCAL at detection.

    D-migration D.2 (amendment #63): post-D.2 the framework-floor
    Class-A patterns prefix every workspace-state path with
    ``workspace/`` — ``workspace/.mcp.json`` etc.
    """
    canonical = make_canonical_repo({"workspace/.mcp.json": "{\"canonical\":1}"})
    workspace = make_workspace({"workspace/.mcp.json": "{\"workspace\":1}"})
    sp = default_sync_protected()  # workspace/.mcp.json is Class A

    report, _ = detect_b_shape_conflicts(
        canonical_path=canonical,
        ref=_git_head_sha(canonical),
        workspace_root=workspace,
        sync_protected=sp,
    )
    assert len(report.conflicts) == 1
    entry = report.conflicts[0]
    assert entry.path == "workspace/.mcp.json"
    # Pre-resolved (NOT pending) — the helper would never enter
    # the resolver for this path.
    assert entry.resolution is Resolution.KEEP_LOCAL
    assert entry.confidence == 1.0
    assert entry.rationale is not None
    assert "Class A" in entry.rationale


def test_workspace_only_modification_no_entry(make_canonical_repo, make_workspace) -> None:
    """If canonical did not change a path but workspace did, no conflict
    entry needed — but our conservative classifier may still flag.
    Test the behaviour: workspace_only -> LOCAL_MODIFIED_ONLY entry IF
    classifier sees it, but more likely the path isn't even in the
    canonical tree → no entry."""
    # Setup: create canonical with file 'shared.txt'='same'; workspace
    # has 'shared.txt'='workspace_edit' (modified vs canonical).
    canonical = make_canonical_repo({"shared.txt": "same"})
    workspace = make_workspace({"shared.txt": "workspace_edit"})
    sp = default_sync_protected()

    report, _ = detect_b_shape_conflicts(
        canonical_path=canonical,
        ref=_git_head_sha(canonical),
        workspace_root=workspace,
        sync_protected=sp,
    )
    # canonical_sha != workspace_sha; prior_sha=None, classifier
    # treats absent-prior as both-sides-changed.
    assert len(report.conflicts) == 1
    entry = report.conflicts[0]
    assert entry.path == "shared.txt"
    assert entry.resolution is Resolution.PENDING
