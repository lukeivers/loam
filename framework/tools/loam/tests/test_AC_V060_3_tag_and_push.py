"""AC.V060.3 — Tag + push action against a local fake remote.

Verifies (a) annotated tag created at the seal commit with the
roadmap-derived objective in the message, (b) `git push` invoked
correctly against the `origin` remote, (c) re-running on an
already-published version produces a no-op + clear diagnostic.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import runner


@pytest.fixture
def repo_with_local_remote(staged_repo: Path, tmp_path: Path) -> Path:
    """Wire `staged_repo` to a bare local 'origin' remote so
    `git push origin main` succeeds without network."""
    bare = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
        check=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(bare)],
        cwd=staged_repo,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-q", "origin", "main"],
        cwd=staged_repo,
        check=True,
    )
    return staged_repo


def test_publish_creates_annotated_tag_at_seal_commit(
    repo_with_local_remote: Path, fixture_version: str
) -> None:
    out = runner.run(
        repo_with_local_remote,
        fixture_version,
        dry_run=False,
        create_release=False,
    )
    assert out.rc == 0
    # Tag should now exist locally.
    proc = subprocess.run(
        ["git", "tag", "-l", fixture_version],
        cwd=repo_with_local_remote,
        capture_output=True,
        text=True,
        check=True,
    )
    assert fixture_version in proc.stdout
    # Tag is annotated → `git cat-file -t <tag>` returns 'tag' (not 'commit').
    proc = subprocess.run(
        ["git", "cat-file", "-t", fixture_version],
        cwd=repo_with_local_remote,
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout.strip() == "tag"
    # Tag message includes the version + the objective sentence from §2.
    proc = subprocess.run(
        ["git", "tag", "-l", "--format=%(contents)", fixture_version],
        cwd=repo_with_local_remote,
        capture_output=True,
        text=True,
        check=True,
    )
    assert fixture_version in proc.stdout
    assert "next outcome shape" in proc.stdout


def test_publish_pushes_branch_and_tag(
    repo_with_local_remote: Path, fixture_version: str
) -> None:
    out = runner.run(
        repo_with_local_remote,
        fixture_version,
        dry_run=False,
        create_release=False,
    )
    assert out.tag_pushed is True
    assert out.branch_pushed is True
    # Tag should now appear on the remote (the bare repo).
    proc = subprocess.run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{fixture_version}"],
        cwd=repo_with_local_remote,
        capture_output=True,
        text=True,
        check=True,
    )
    assert fixture_version in proc.stdout


def test_re_run_is_idempotent_no_op(
    repo_with_local_remote: Path, fixture_version: str, capsys
) -> None:
    """First run publishes; second run sees the tag on remote +
    surfaces the 'already on origin remote' message + rc=0."""
    runner.run(
        repo_with_local_remote, fixture_version, dry_run=False
    )
    capsys.readouterr()  # drop first-run output
    out2 = runner.run(
        repo_with_local_remote, fixture_version, dry_run=False
    )
    captured = capsys.readouterr()
    assert out2.rc == 0
    assert out2.idempotent_noop is True
    assert out2.tag_created is False
    assert out2.tag_pushed is False
    assert (
        f"{fixture_version} already on origin remote" in captured.out
    )


def test_dry_run_skips_tag_creation_and_push(
    repo_with_local_remote: Path, fixture_version: str
) -> None:
    out = runner.run(
        repo_with_local_remote, fixture_version, dry_run=True
    )
    assert out.rc == 0
    assert out.tag_created is False
    assert out.tag_pushed is False
    # Tag should NOT exist locally after a dry-run.
    proc = subprocess.run(
        ["git", "tag", "-l", fixture_version],
        cwd=repo_with_local_remote,
        capture_output=True,
        text=True,
        check=True,
    )
    assert fixture_version not in proc.stdout.split()


def test_red_gate_aborts_publish_no_tag_no_push(
    repo_with_local_remote: Path, fixture_version: str, fixture_slug: str
) -> None:
    """When any pre-publish gate RED, the runner aborts BEFORE
    creating the tag or pushing anything."""
    # Force gate 4 (clean-tree) RED.
    (repo_with_local_remote / "scratch.txt").write_text(
        "dirty\n", encoding="utf-8"
    )
    out = runner.run(
        repo_with_local_remote, fixture_version, dry_run=False
    )
    assert out.rc == 1
    assert out.tag_created is False
    assert out.tag_pushed is False
    # Tag should NOT exist locally.
    proc = subprocess.run(
        ["git", "tag", "-l", fixture_version],
        cwd=repo_with_local_remote,
        capture_output=True,
        text=True,
        check=True,
    )
    assert fixture_version not in proc.stdout.split()
