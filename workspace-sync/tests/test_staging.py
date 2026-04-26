"""AC.WS.7, AC.WS.12 — staging primitives tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from workspace_sync.staging import (
    apply_staging_atomically,
    discard_staging,
    stage_canonical_clean_writes,
    stage_resolved_content,
    staging_root,
)


def _git_head(canonical: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(canonical), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def test_staging_root_path(tmp_path: Path) -> None:
    p = staging_root(tmp_path, "abc123")
    assert p == tmp_path / ".pos" / "sync" / "staging" / "abc123"


def test_stage_canonical_clean_writes_copies_from_git(make_canonical_repo, make_workspace) -> None:
    canonical = make_canonical_repo({"a.py": "alpha", "b.py": "beta"})
    workspace = make_workspace({})
    ref = _git_head(canonical)

    sroot = stage_canonical_clean_writes(
        canonical_path=canonical,
        ref=ref,
        workspace_root=workspace,
        paths_to_apply=["a.py", "b.py"],
    )
    assert (sroot / "a.py").read_text() == "alpha"
    assert (sroot / "b.py").read_text() == "beta"


def test_stage_resolved_content_writes_to_staging(tmp_path: Path) -> None:
    sroot = staging_root(tmp_path, "ref")
    sroot.mkdir(parents=True)
    stage_resolved_content(sroot, "deep/path.py", "merged_content")
    assert (sroot / "deep" / "path.py").read_text() == "merged_content"


def test_apply_staging_atomically_writes_workspace_files(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    sroot = workspace / ".pos" / "sync" / "staging" / "ref"
    sroot.mkdir(parents=True)
    (sroot / "x.py").write_text("staged_x")
    (sroot / "sub").mkdir()
    (sroot / "sub" / "y.py").write_text("staged_y")

    apply_staging_atomically(sroot, workspace)

    assert (workspace / "x.py").read_text() == "staged_x"
    assert (workspace / "sub" / "y.py").read_text() == "staged_y"


def test_apply_staging_replaces_existing_files(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "x.py").write_text("old_content")

    sroot = workspace / ".pos" / "sync" / "staging" / "ref"
    sroot.mkdir(parents=True)
    (sroot / "x.py").write_text("new_content")

    apply_staging_atomically(sroot, workspace)
    assert (workspace / "x.py").read_text() == "new_content"


def test_discard_staging_removes_tree(tmp_path: Path) -> None:
    sroot = tmp_path / "staging"
    sroot.mkdir()
    (sroot / "x.py").write_text("y")
    discard_staging(sroot)
    assert not sroot.exists()


def test_discard_staging_idempotent_on_missing(tmp_path: Path) -> None:
    discard_staging(tmp_path / "nope")  # no raise
