"""AC.V060.6 — Post-ship review + next-scope decision.

Verifies the post-publish output includes a "Next-scope proposal"
block naming objective + class + fence + named ACs (or queue
excerpt). Also verifies the major-release eval branches correctly
on pre-1.0 vs post-1.0 versions.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import post_ship, runner


def test_proposal_carries_next_objective_class_and_fence(
    staged_repo: Path, fixture_version: str
) -> None:
    """AC.NSWP.1 — walker reads v0.10.0 §4 candidate-queue structure
    and surfaces the top-priority candidate's slug + title + class +
    slug-fence pointer. Conftest fixture's roadmap §4 carries
    `### Candidate 1 — `fixture-candidate` — Fixture next-scope target`
    + `**Slug:** `fixture-candidate`. **Class:** MINOR (FIXTURE).`."""
    p = post_ship.build_proposal(staged_repo, fixture_version)
    assert p.next_objective != ""
    assert "fixture-candidate" in p.next_objective
    assert "Fixture next-scope target" in p.next_objective
    assert "MINOR" in p.next_class
    assert "FIXTURE" in p.next_class
    assert "fixture-candidate" in p.next_ac_or_fence


def test_proposal_handles_missing_roadmap_with_placeholders(
    staged_repo: Path, fixture_version: str
) -> None:
    (staged_repo / "docs" / "release-roadmap.md").unlink()
    # Re-commit so working tree stays clean for downstream tests.
    subprocess.run(
        ["git", "add", "-A"], cwd=staged_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "drop roadmap"],
        cwd=staged_repo,
        check=True,
    )
    p = post_ship.build_proposal(staged_repo, fixture_version)
    assert "(roadmap not found)" in p.next_objective


def test_proposal_handles_empty_candidate_queue(
    staged_repo: Path, fixture_version: str
) -> None:
    """AC.NSWP.2 — when §4 exists but contains zero `### Candidate N`
    headings (genuinely empty queue between MINORs), the walker
    emits an explicit "queue empty — author next candidate" message
    instead of the misleading legacy "(no entries in §4)" placeholder.
    """
    roadmap = staged_repo / "docs" / "release-roadmap.md"
    body = roadmap.read_text(encoding="utf-8")
    # Strip the candidate heading + class line from the conftest
    # fixture, leaving §4 with only its heading + prose body.
    empty_body = body.replace(
        "### Candidate 1 — `fixture-candidate` — Fixture next-scope target\n\n"
        "**Slug:** `fixture-candidate`. **Class:** MINOR (FIXTURE).\n\n"
        "Some prose about the next candidate.\n",
        "Queue currently empty between MINORs.\n",
    )
    roadmap.write_text(empty_body, encoding="utf-8")
    subprocess.run(
        ["git", "add", "docs/release-roadmap.md"],
        cwd=staged_repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "empty candidate queue"],
        cwd=staged_repo,
        check=True,
    )
    p = post_ship.build_proposal(staged_repo, fixture_version)
    # Empty-queue case: explicit operator-readable message naming
    # the action ("author next candidate"), NOT the legacy
    # "(no entries in §4)" placeholder.
    assert "queue empty" in p.next_objective.lower()
    assert "author next candidate" in p.next_objective.lower()
    assert "(no entries in §4)" not in p.next_objective
    # Same message in class hint and fence (all three placeholder
    # fields conflated for the empty-queue branch).
    assert "queue empty" in p.next_class.lower()
    assert "queue empty" in p.next_ac_or_fence.lower()


def test_pre_1_0_major_eval_returns_pre_1_0(staged_repo: Path) -> None:
    p = post_ship.build_proposal(staged_repo, "v0.6.0")
    assert p.major_eval == "pre-1.0"
    assert "never cuts major" in p.major_eval_detail


def test_post_1_0_major_eval_returns_review_needed(
    staged_repo: Path,
) -> None:
    p = post_ship.build_proposal(staged_repo, "v1.5.0")
    assert p.major_eval == "post-1.0-review-needed"
    assert "Operator review" in p.major_eval_detail


def test_format_proposal_renders_full_block(
    staged_repo: Path, fixture_version: str
) -> None:
    p = post_ship.build_proposal(staged_repo, fixture_version)
    rendered = post_ship.format_proposal(p)
    assert "== Next-scope proposal ==" in rendered
    assert "Next objective:" in rendered
    assert "Class hint:" in rendered
    assert "Major-release eval:" in rendered
    assert "FUTURE_IDEAS_DRAFT.md" in rendered


def test_runner_emits_proposal_on_successful_publish(
    staged_repo: Path, fixture_version: str, tmp_path: Path, capsys
) -> None:
    """Full integration: a successful publish run prints the proposal
    block to stdout post-publish."""
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
        staged_repo, fixture_version, dry_run=False
    )
    assert out.rc == 0
    captured = capsys.readouterr()
    assert "== Next-scope proposal ==" in captured.out
    assert out.proposal is not None


def test_runner_emits_proposal_on_dry_run(
    staged_repo: Path, fixture_version: str, capsys
) -> None:
    """Even on dry-run, the proposal block surfaces — operator may
    be reading the dry-run output to plan the next cycle."""
    out = runner.run(
        staged_repo, fixture_version, dry_run=True
    )
    assert out.rc == 0
    captured = capsys.readouterr()
    assert "== Next-scope proposal ==" in captured.out
