"""AC.RFPR.4 — Idempotency + dry-run safety preserved.

A re-run against a fully published version (tag AND Release both
present) remains a no-op — no duplicate Release attempt, no spurious
mutation. A ``--dry-run`` invocation that reaches the already-on-origin
branch performs no repository mutation (no Release create, no backfill
commit, no push) while still reporting state.

The dry-run half also closes the pre-existing latent defect the plan
folded in per D-RFPR.4: the already-on-origin branch called
``apply_backfill(..., dry_run=False)`` + ``_commit_and_push_backfill``
even under ``--dry-run`` (runner.py:286 pre-fix) — a dry-run could
commit AND push backfill edits.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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
def tag_only_repo(staged_repo: Path, fixture_version: str, tmp_path: Path) -> Path:
    """Tag on origin via a prior no-release publish."""
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
    assert out.rc == 0
    return staged_repo


def _git_state(repo: Path) -> tuple[str, str, str]:
    """(HEAD sha, porcelain status, remote refs) snapshot for
    mutation comparison."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout
    remote = subprocess.run(
        ["git", "ls-remote", "origin"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout
    return head, status, remote


def test_fully_published_rerun_is_noop(
    tag_only_repo: Path, fixture_version: str, fake_gh: FakeGh
) -> None:
    """Tag AND Release both present → re-run with ``--release`` stays
    an idempotent no-op: no duplicate Release attempt, no mutation."""
    fake_gh.releases.add(fixture_version)  # fully published
    before = _git_state(tag_only_repo)
    out = runner.run(
        tag_only_repo, fixture_version, dry_run=False, create_release=True
    )
    assert out.rc == 0
    assert out.idempotent_noop is True
    assert out.gh_release_created is False
    assert fake_gh.creates() == []
    assert _git_state(tag_only_repo) == before


def test_dry_run_on_already_on_origin_branch_mutates_nothing(
    tag_only_repo: Path, fixture_version: str, fake_gh: FakeGh, capsys
) -> None:
    """``--dry-run`` reaching the already-on-origin branch performs
    zero repository mutation — no Release create, no backfill commit,
    no push — while still reporting state (D-RFPR.4)."""
    # Re-introduce a pending backfill edit so the branch WOULD mutate
    # if dry-run were ignored (the pre-fix runner.py:286 behavior):
    # a canonical SHIPPED-LOCAL trailing claim for the version.
    state_md = tag_only_repo / "docs" / "STATE.md"
    state_md.write_text(
        "# State\n\n"
        f"- **2026-05-10** — **{fixture_version} PATCH SHIPPED LOCAL** — "
        f"fixture row. {fixture_version} SHIPPED LOCAL — owner gates "
        "publish.\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "docs/STATE.md"], cwd=tag_only_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "reset STATE.md to pre-backfill shape"],
        cwd=tag_only_repo,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-q", "origin", "main"], cwd=tag_only_repo, check=True
    )
    state_before = state_md.read_text(encoding="utf-8")
    before = _git_state(tag_only_repo)
    out = runner.run(
        tag_only_repo, fixture_version, dry_run=True, create_release=True
    )
    captured = capsys.readouterr()
    assert out.rc == 0
    assert out.gh_release_created is False
    assert out.backfill_committed is False
    assert out.backfill_pushed is False
    assert fake_gh.creates() == []
    assert state_md.read_text(encoding="utf-8") == state_before
    assert _git_state(tag_only_repo) == before
    # Still reports state (backfill preview + Release half).
    assert captured.out.strip() != ""
