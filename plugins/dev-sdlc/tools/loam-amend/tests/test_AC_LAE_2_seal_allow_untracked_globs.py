"""AC.LAE.2 — ``loam amend seal --allow-untracked-globs <pattern>``.

Plan: ``docs/plans/v0-1-2-loam-amend-ergonomics.md`` AC.LAE.2.
Per v0.1.2 item 6 (loam-amend ergonomics sweep). Patterns admit
dirty paths via ``fnmatch.fnmatchcase`` for the seal-step
dirty-tree pre-flight; admitted patterns are NOT staged or
committed.
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.commands.seal import _working_tree_dirty


def _git_init(repo: Path) -> None:
    import subprocess

    subprocess.run(
        ["git", "init", "-q", "-b", "main"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "loam amend test"],
        cwd=repo,
        check=True,
    )
    (repo / "README.md").write_text("seed\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True
    )


def test_single_literal_pattern_admits_path(tmp_path: Path) -> None:
    """Untracked file matching the exact pattern is admitted."""
    repo = tmp_path
    _git_init(repo)
    (repo / "FUTURE_IDEAS_DRAFT.md").write_text("dirt\n")

    dirty = _working_tree_dirty(repo, set())
    assert any("FUTURE_IDEAS_DRAFT.md" in d for d in dirty), (
        "control: file should be dirty without admission"
    )

    dirty_admitted = _working_tree_dirty(
        repo, set(), allow_untracked_globs=("FUTURE_IDEAS_DRAFT.md",)
    )
    assert dirty_admitted == [], (
        f"file should be admitted via literal pattern: {dirty_admitted}"
    )


def test_glob_pattern_admits_modified_files(tmp_path: Path) -> None:
    """Glob pattern admits modified-tracked files (M state).

    Note: untracked-directory state surfaces as ``?? <dir>/`` in
    porcelain output, so glob admit-set tests use modified-tracked
    files (where porcelain reports per-file paths) — this matches
    the real-world workflow case (dirty FIDRAFT post-commit).
    """
    import subprocess

    repo = tmp_path
    _git_init(repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "drift1.md").write_text("seed\n")
    (repo / "docs" / "drift2.md").write_text("seed\n")
    subprocess.run(
        ["git", "add", "docs/drift1.md", "docs/drift2.md"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "seed docs"], cwd=repo, check=True
    )

    # Now modify both — porcelain reports each as `M docs/drift{1,2}.md`.
    (repo / "docs" / "drift1.md").write_text("dirt\n")
    (repo / "docs" / "drift2.md").write_text("dirt\n")

    dirty = _working_tree_dirty(
        repo, set(), allow_untracked_globs=("docs/*.md",)
    )
    assert dirty == [], (
        f"glob pattern should admit both docs/*.md modified files: {dirty}"
    )


def test_multiple_flags_compose(tmp_path: Path) -> None:
    """Multiple --allow-untracked-globs flags admit their union (literal patterns).

    Two literal patterns at the repo root — both admitted individually,
    porcelain reports each as a separate ``??`` line.
    """
    repo = tmp_path
    _git_init(repo)
    (repo / "FIDRAFT.md").write_text("dirt\n")
    (repo / "scratch.md").write_text("dirt\n")

    dirty = _working_tree_dirty(
        repo,
        set(),
        allow_untracked_globs=(
            "FIDRAFT.md",
            "scratch.md",
        ),
    )
    assert dirty == [], (
        f"both literal patterns should admit; remaining: {dirty}"
    )


def test_non_matching_dirt_still_aborts(tmp_path: Path) -> None:
    """Dirt not matching any admit pattern is still surfaced."""
    repo = tmp_path
    _git_init(repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "FUTURE_IDEAS_DRAFT.md").write_text("dirt\n")
    (repo / "secret.env").write_text("API_KEY=...\n")

    dirty = _working_tree_dirty(
        repo,
        set(),
        allow_untracked_globs=("docs/FUTURE_IDEAS_DRAFT.md",),
    )
    # The admitted path drops out; the unrelated dirt persists.
    assert any("secret.env" in d for d in dirty), (
        f"non-admitted dirt should remain: {dirty}"
    )
    assert not any("FUTURE_IDEAS_DRAFT.md" in d for d in dirty), (
        f"admitted path should drop: {dirty}"
    )
