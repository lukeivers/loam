"""AC.PRSI.8 — Install ergonomics CLI: loam pr-safety install <surface>
+ --all + --force + --dry-run; conflict-halt with exit code 6."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# We invoke the CLI in-process via the loam_cli builder; conftest's
# subprocess invocation tests the entry-point chain end-to-end.


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    return repo


def _setup_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


def _run_cli(*args: str) -> tuple[int, str, str]:
    """Run `loam pr-safety <args>` as a subprocess + return (rc, out, err)."""
    proc = subprocess.run(
        [sys.executable, "-m", "loam_cli", "pr-safety", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.returncode, proc.stdout, proc.stderr)


def _run_cli_via_entry(*args: str) -> tuple[int, str, str]:
    """Run via the installed `loam` entry script."""
    proc = subprocess.run(
        ["loam", "pr-safety", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.returncode, proc.stdout, proc.stderr)


def test_install_pre_commit_via_cli(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    rc, out, err = _run_cli_via_entry(
        "install",
        "pre-commit",
        str(repo),
        "--workspace-root",
        str(ws),
    )
    assert rc == 0, f"unexpected rc={rc}; out={out!r}; err={err!r}"
    assert "[install:pre-commit]" in out or "[install:pre-commit]" in err
    assert (repo / ".git" / "hooks" / "pre-commit").exists()


def test_install_all_via_cli(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    rc, out, err = _run_cli_via_entry(
        "install", "all", str(repo), "--workspace-root", str(ws)
    )
    assert rc == 0
    # All 6 surfaces created.
    assert (repo / ".git" / "hooks" / "pre-commit").exists()
    assert (repo / ".git" / "hooks" / "pre-push").exists()
    assert (repo / ".github" / "workflows" / "loam-pr-safety.yml").exists()
    assert (repo / ".gitlab-ci.yml").exists()
    assert (repo / ".circleci" / "config.yml").exists()
    assert (repo / ".github" / "pull_request_template.md").exists()


def test_install_dry_run_via_cli(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    rc, out, err = _run_cli_via_entry(
        "install",
        "pre-commit",
        str(repo),
        "--workspace-root",
        str(ws),
        "--dry-run",
    )
    assert rc == 0
    assert not (repo / ".git" / "hooks" / "pre-commit").exists()


def test_install_conflict_exits_6(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("#!/bin/sh\necho lol\n", encoding="utf-8")

    rc, out, err = _run_cli_via_entry(
        "install", "pre-commit", str(repo), "--workspace-root", str(ws)
    )
    assert rc == 6, f"expected exit code 6 (install conflict); got {rc}; err={err!r}"


def test_install_force_via_cli(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("#!/bin/sh\necho old\n", encoding="utf-8")

    rc, out, err = _run_cli_via_entry(
        "install",
        "pre-commit",
        str(repo),
        "--workspace-root",
        str(ws),
        "--force",
    )
    assert rc == 0
    # New content is loam-managed.
    assert "loam-pr-safety:managed:" in target.read_text()


def test_install_ci_github_actions_via_cli(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    rc, out, err = _run_cli_via_entry(
        "install",
        "ci",
        "github-actions",
        str(repo),
        "--workspace-root",
        str(ws),
    )
    assert rc == 0
    assert (repo / ".github" / "workflows" / "loam-pr-safety.yml").exists()


def test_install_all_aggregates_conflicts(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    # Plant a non-loam pre-commit hook only.
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("#!/bin/sh\necho lol\n", encoding="utf-8")

    rc, out, err = _run_cli_via_entry(
        "install", "all", str(repo), "--workspace-root", str(ws)
    )
    # Exit 6 because at least one conflict.
    assert rc == 6
    # Other surfaces still installed.
    assert (repo / ".github" / "workflows" / "loam-pr-safety.yml").exists()
    assert (repo / ".gitlab-ci.yml").exists()
