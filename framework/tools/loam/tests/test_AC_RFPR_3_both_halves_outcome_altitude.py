"""AC.RFPR.3 (outcome-altitude) — Both-halves publish assertion.

A deliberately tag-only state run through the PRODUCTION release
entry-point (CLI dispatch with ``--release``, no pre-arranged
repair-specific state) ends with the Release existing, and the flow
reports the publish complete only when tag AND Release both exist;
a Release-half failure is reported as incomplete, never as success.

Production entry-point: the unified ``loam`` parser's ``release``
subcommand (entry-point discovery) → ``args.func(args)`` — the same
dispatch path a terminal invocation takes. The tag-only state arises
the production way: a prior publish without ``--release``.

D-RFPR.5 scope: the both-halves assertion applies to ``--release``
runs only; a deliberate no-``--release`` publish stays legitimately
tag-only (covered by the existing AC.V060.3 idempotency tests).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import loam_cli.cli as cli_mod
from loam_cli.release import runner

from tests.test_AC_RFPR_1_partial_publish_repair import FakeGh


@pytest.fixture
def fake_gh(monkeypatch) -> FakeGh:
    gh = FakeGh()
    monkeypatch.setattr("loam_cli.release.runner.subprocess.run", gh.run)
    monkeypatch.setattr(
        "loam_cli.release.runner.shutil.which", lambda _: "/usr/bin/gh"
    )
    return gh


@pytest.fixture
def repo_with_local_remote(staged_repo: Path, tmp_path: Path) -> Path:
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


def _dispatch_release(repo: Path, version: str, *extra: str) -> int:
    """Drive the production CLI surface: top-level ``loam`` parser →
    ``release`` subcommand → ``args.func``."""
    parser = cli_mod._build_parser()
    args = parser.parse_args(
        ["release", version, "--repo-root", str(repo), *extra]
    )
    return args.func(args)


def test_tag_only_state_ends_with_release_existing(
    repo_with_local_remote: Path, fixture_version: str, fake_gh: FakeGh, capsys
) -> None:
    """Outcome altitude: tag-only state (prior no-release publish) +
    production ``--release`` re-run → end-state has the Release; the
    flow reports the publish complete (both halves)."""
    rc0 = _dispatch_release(repo_with_local_remote, fixture_version)
    assert rc0 == 0
    capsys.readouterr()
    rc = _dispatch_release(
        repo_with_local_remote, fixture_version, "--release"
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert fixture_version in fake_gh.releases
    assert "publish complete" in captured.out.lower()


def test_release_half_failure_on_repair_path_reported_incomplete(
    repo_with_local_remote: Path, fixture_version: str, fake_gh: FakeGh, capsys
) -> None:
    """Failure-injection (repair path): the Release create fails →
    the flow reports INCOMPLETE + non-zero rc, never success."""
    rc0 = _dispatch_release(repo_with_local_remote, fixture_version)
    assert rc0 == 0
    capsys.readouterr()
    fake_gh.fail_create = True
    rc = _dispatch_release(
        repo_with_local_remote, fixture_version, "--release"
    )
    captured = capsys.readouterr()
    assert rc != 0
    assert fixture_version not in fake_gh.releases
    assert "incomplete" in captured.out.lower()
    assert "publish complete" not in captured.out.lower()


def test_release_half_failure_on_fresh_path_reported_incomplete(
    repo_with_local_remote: Path, fixture_version: str, fake_gh: FakeGh, capsys
) -> None:
    """Failure-injection (success path): a first-run ``--release``
    publish whose Release create fails reports INCOMPLETE + non-zero
    rc — the tag half alone is never reported as a complete publish."""
    fake_gh.fail_create = True
    rc = _dispatch_release(
        repo_with_local_remote, fixture_version, "--release"
    )
    captured = capsys.readouterr()
    assert rc != 0
    assert fixture_version not in fake_gh.releases
    assert "incomplete" in captured.out.lower()
    assert "publish complete" not in captured.out.lower()
