"""AC.V060.4 — Optional GitHub Release with auto-generated notes.

Verifies (a) generated notes contain version objective sentence,
(b) AC verdict matrix, (c) commit log section. Integration test
(mocked `gh` invocation) verifies the command shape.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import notes, runner


def test_generated_notes_contain_outcome_shape_section(
    staged_repo: Path, fixture_version: str
) -> None:
    body = notes.generate_notes(staged_repo, fixture_version)
    assert "Outcome shape" in body
    assert fixture_version in body


def test_generated_notes_contain_ac_verdict_matrix(
    staged_repo: Path, fixture_version: str
) -> None:
    body = notes.generate_notes(staged_repo, fixture_version)
    assert "AC verdicts" in body
    # The fixture's status section names AC.V060.1 + AC.V060.2.
    assert "AC.V060.1" in body
    assert "AC.V060.2" in body


def test_generated_notes_contain_commit_log_section(
    staged_repo: Path, fixture_version: str
) -> None:
    body = notes.generate_notes(staged_repo, fixture_version)
    assert "## Commits" in body


def test_generated_notes_handle_missing_plan_doc_gracefully(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """A missing plan-doc → notes still render with placeholder text;
    no exception."""
    (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    ).unlink()
    body = notes.generate_notes(staged_repo, fixture_version)
    assert "unavailable: no plan-doc" in body
    assert fixture_version in body


def test_release_flag_invokes_gh_release_create(
    staged_repo: Path, fixture_version: str, monkeypatch, tmp_path: Path
) -> None:
    """With `--release`, the runner invokes `gh release create <tag>`
    after the tag + push action. We monkeypatch subprocess.run to
    capture the gh invocation without reaching the real gh binary."""
    # Wire a local bare remote (re-using the gate-3 fixture pattern).
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
    # Capture gh invocations.
    captured: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(args, *posargs, **kwargs):
        if isinstance(args, list) and args and args[0] == "gh":
            captured.append(list(args))
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr=""
            )
        return real_run(args, *posargs, **kwargs)

    monkeypatch.setattr(
        "loam_cli.release.runner.subprocess.run", fake_run
    )
    # Also patch shutil.which so the runner doesn't FileNotFoundError on
    # missing gh binary in CI / venv.
    monkeypatch.setattr(
        "loam_cli.release.runner.shutil.which", lambda _: "/usr/bin/gh"
    )
    out = runner.run(
        staged_repo, fixture_version, dry_run=False, create_release=True
    )
    assert out.rc == 0
    assert out.gh_release_created is True
    assert len(captured) == 1
    cmd = captured[0]
    assert cmd[0] == "gh"
    assert cmd[1:4] == ["release", "create", fixture_version]
    # Notes payload includes the version + outcome heading.
    notes_idx = cmd.index("--notes") + 1
    assert fixture_version in cmd[notes_idx]
    assert "Outcome shape" in cmd[notes_idx]
