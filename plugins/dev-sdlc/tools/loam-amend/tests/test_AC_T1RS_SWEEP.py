"""AC.T1RS.SWEEP.{1,2} — ``loam amend sweep-archive`` CLI subcommand.

Per amendment #143 Scope C + §14 D-T1RS.LIVE-SWEEP-{TIMING,MECHANISM}:
the new CLI subcommand makes the retroactive sweep reproducible +
auditable. ``--dry-run`` previews; ``--apply`` performs the move +
creates one ``chore(retroactive-sweep):`` commit. ``--dry-run`` and
``--apply`` are mutually exclusive AND required (no implicit
default) so a bare invocation is a noisy no-op rather than a silent
real run.

ACs verified here:
- AC.T1RS.SWEEP.1 — sweep-archive --dry-run reports ``moved`` > 0
  when the fixture has cleanly-attributable plan-docs.
- AC.T1RS.SWEEP.2 — sweep-archive --apply produces exactly ONE
  corrective commit; commit subject + body follow the canonical
  D-T1RS.LIVE-SWEEP-MECHANISM convention.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_amend.commands import sweep_archive as sweep_archive_cmd


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


_MC = {"n": 0}


def _commit_seal_with_subject(repo: Path, subject: str) -> str:
    _MC["n"] += 1
    marker = repo / f".m-{_MC['n']}"
    marker.write_text("x", encoding="utf-8")
    _git(repo, "add", "--", str(marker.relative_to(repo)))
    _git(repo, "commit", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo_with_mixed_plans(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")

    plans = repo / "docs" / "plans"
    plans.mkdir(parents=True)
    # Mix: one narrow-clean, one body-slug, one in-flight, one
    # ambiguous.
    (plans / "amendment-10-narrow.md").write_text(
        "# narrow\n", encoding="utf-8"
    )
    (plans / "amendment-20-body.md").write_text(
        "# body\n", encoding="utf-8"
    )
    (plans / "amendment-30-untracked.md").write_text(
        "# untracked\n", encoding="utf-8"
    )
    (plans / "amendment-40-ambig.md").write_text(
        "# ambig\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-docs seeded")

    # narrow strategy seal for #10.
    _commit_seal_with_subject(
        repo, "chore(seals): amendment-10-narrow — narrow attribution"
    )
    # body strategy seal for #20 — only ``body`` mentioned, not full slug.
    _commit_seal_with_subject(
        repo, "chore(seals): body seal — fixture body-slug attribution"
    )
    # #30 has no seal commit (in-flight).
    # #40 has TWO seals attributing via body — ambiguous.
    _commit_seal_with_subject(
        repo, "chore(seals): ambig seal — first attribution"
    )
    _commit_seal_with_subject(
        repo, "chore(seals): ambig seal — second attribution"
    )
    return repo


def test_AC_T1RS_SWEEP_1_dry_run_reports_moves(
    repo_with_mixed_plans, capsys
):
    """``sweep-archive --dry-run`` reports moves WITHOUT modifying
    the tree."""
    repo = repo_with_mixed_plans
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    rc = sweep_archive_cmd.run(repo, dry_run=True)
    assert rc == 0
    out = capsys.readouterr().out
    # Both narrow and body strategies recovered a plan-doc.
    assert "dry-run:" in out
    assert "narrow" in out
    assert "body" in out
    # #10 + #20 named in the dry-run report.
    assert "amendment-10-narrow.md" in out
    assert "amendment-20-body.md" in out
    # Ambiguous bucket surfaces too.
    assert "ambiguous" in out

    # Tree NOT modified.
    head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head_before == head_after
    # Files still at original locations.
    assert (repo / "docs" / "plans" / "amendment-10-narrow.md").exists()
    assert (repo / "docs" / "plans" / "amendment-20-body.md").exists()
    sealed = repo / "docs" / "plans" / "sealed"
    # sealed/ may not even exist yet on dry-run.
    if sealed.exists():
        assert not (sealed / "amendment-10-narrow.md").exists()


def test_AC_T1RS_SWEEP_2_real_run_produces_one_corrective_commit(
    repo_with_mixed_plans,
):
    """``sweep-archive --apply`` moves the cleanly-attributable
    plan-docs + creates exactly ONE ``chore(retroactive-sweep):``
    commit. Ambiguous + in-flight stay in place."""
    repo = repo_with_mixed_plans
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    commit_count_before = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )

    rc = sweep_archive_cmd.run(repo, dry_run=False)
    assert rc == 0

    head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    commit_count_after = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )
    # Exactly one new commit.
    assert commit_count_after == commit_count_before + 1, (
        f"expected exactly one new commit, "
        f"got {commit_count_after - commit_count_before}"
    )
    assert head_before != head_after

    # Subject matches D-T1RS.LIVE-SWEEP-MECHANISM convention.
    subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert subject.startswith("chore(retroactive-sweep):"), (
        f"unexpected subject: {subject!r}"
    )
    assert "amendment #143 Scope C" in subject
    # Body groups by strategy.
    body = _git(repo, "log", "-1", "--format=%b").stdout
    assert "narrow" in body
    assert "body" in body
    assert "amendment-10-narrow.md" in body
    assert "amendment-20-body.md" in body
    # Ambiguous bucket named in body.
    assert "ambiguous" in body.lower()

    # Files moved.
    sealed = repo / "docs" / "plans" / "sealed"
    assert (sealed / "amendment-10-narrow.md").exists()
    assert (sealed / "amendment-20-body.md").exists()
    # In-flight + ambiguous stay in docs/plans/.
    assert (repo / "docs" / "plans" / "amendment-30-untracked.md").exists()
    assert (repo / "docs" / "plans" / "amendment-40-ambig.md").exists()
    assert not (sealed / "amendment-30-untracked.md").exists()
    assert not (sealed / "amendment-40-ambig.md").exists()


def test_AC_T1RS_SWEEP_2_no_op_when_nothing_to_move(tmp_path, capsys):
    """When the sweep finds nothing to move, no commit is created
    (avoids noise from empty commits)."""
    repo = tmp_path / "empty"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    (repo / "docs" / "plans").mkdir(parents=True)
    (repo / "docs" / "plans" / "in-flight.md").write_text(
        "# in flight\n", encoding="utf-8"
    )
    (repo / "README").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture")

    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    rc = sweep_archive_cmd.run(repo, dry_run=False)
    assert rc == 0
    head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head_before == head_after, (
        "no commit must be created when there's nothing to sweep"
    )
    out = capsys.readouterr().out
    assert "nothing to archive" in out


def test_AC_T1RS_SWEEP_cli_requires_flag(tmp_path):
    """The CLI surface requires ``--dry-run`` OR ``--apply``; a bare
    invocation should be rejected by argparse."""
    from loam_amend.cli import _build_parser

    parser = _build_parser()
    with pytest.raises(SystemExit):
        # No flag set — argparse should error on the required
        # mutually-exclusive group.
        parser.parse_args(["sweep-archive"])
