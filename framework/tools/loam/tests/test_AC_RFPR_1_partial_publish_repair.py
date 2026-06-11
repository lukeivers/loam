"""AC.RFPR.1 — Partial-publish repair (release-flow-partial-publish-repair).

With the tag on origin and no GitHub Release, a re-run with
``--release`` ends with the Release created carrying generated notes,
instead of short-circuiting at "already on origin; nothing to do".
A ``--dry-run`` against the same state reports the would-create-Release
without creating it.

Fixture: the v1.5.0 live-incident shape — a prior no-``--release``
publish pushed the tag; the GitHub Release was never created. ``gh``
is faked at the ``subprocess.run`` seam (halt trigger 4: no test may
reach the real ``gh`` binary or a real remote).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import runner


class FakeGh:
    """Stateful fake for the ``gh`` CLI at the subprocess seam.

    Routes ``gh release view`` / ``gh release create`` against an
    in-memory release set; passes every non-``gh`` invocation through
    to the real ``subprocess.run`` (git keeps working).
    """

    def __init__(self) -> None:
        self.releases: set[str] = set()
        self.invocations: list[list[str]] = []
        self.fail_create = False
        self._real_run = subprocess.run

    def run(self, args, *posargs, **kwargs):
        if not (isinstance(args, list) and args and args[0] == "gh"):
            return self._real_run(args, *posargs, **kwargs)
        self.invocations.append(list(args))
        if args[1:3] == ["release", "view"]:
            tag = args[3]
            rc = 0 if tag in self.releases else 1
            return subprocess.CompletedProcess(
                args=args,
                returncode=rc,
                stdout="" if rc else tag,
                stderr="" if rc == 0 else "release not found",
            )
        if args[1:3] == ["release", "create"]:
            if self.fail_create:
                raise subprocess.CalledProcessError(1, args)
            self.releases.add(args[3])
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr=""
            )
        raise AssertionError(f"unexpected gh invocation: {args}")

    def creates(self) -> list[list[str]]:
        return [
            inv for inv in self.invocations
            if inv[1:3] == ["release", "create"]
        ]


@pytest.fixture
def fake_gh(monkeypatch) -> FakeGh:
    gh = FakeGh()
    monkeypatch.setattr("loam_cli.release.runner.subprocess.run", gh.run)
    monkeypatch.setattr(
        "loam_cli.release.runner.shutil.which", lambda _: "/usr/bin/gh"
    )
    return gh


@pytest.fixture
def tag_only_repo(staged_repo: Path, fixture_version: str, tmp_path: Path) -> Path:
    """Wire a local bare 'origin' + publish WITHOUT ``--release`` so
    the tag is on origin but no GitHub Release exists — the
    partial-publish state under repair."""
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
    out = runner.run(
        staged_repo, fixture_version, dry_run=False, create_release=False
    )
    assert out.rc == 0 and out.tag_pushed
    return staged_repo


def test_rerun_with_release_creates_missing_release(
    tag_only_repo: Path, fixture_version: str, fake_gh: FakeGh, capsys
) -> None:
    """AC.RFPR.1: tag on origin + Release absent + ``--release`` →
    the re-run creates the missing Release with a notes body."""
    out = runner.run(
        tag_only_repo, fixture_version, dry_run=False, create_release=True
    )
    assert out.rc == 0
    assert out.gh_release_created is True
    creates = fake_gh.creates()
    assert len(creates) == 1
    cmd = creates[0]
    assert cmd[1:4] == ["release", "create", fixture_version]
    notes_body = cmd[cmd.index("--notes") + 1]
    assert fixture_version in notes_body
    assert "Outcome shape" in notes_body
    assert fixture_version in fake_gh.releases
    captured = capsys.readouterr()
    assert "nothing to do" not in captured.out


def test_dry_run_reports_would_create_without_creating(
    tag_only_repo: Path, fixture_version: str, fake_gh: FakeGh, capsys
) -> None:
    """AC.RFPR.1 dry-run variant: the same state under ``--dry-run``
    reports the would-create-Release and performs no create."""
    out = runner.run(
        tag_only_repo, fixture_version, dry_run=True, create_release=True
    )
    assert out.rc == 0
    assert out.gh_release_created is False
    assert fake_gh.creates() == []
    assert fixture_version not in fake_gh.releases
    captured = capsys.readouterr()
    assert "would create" in captured.out.lower()
