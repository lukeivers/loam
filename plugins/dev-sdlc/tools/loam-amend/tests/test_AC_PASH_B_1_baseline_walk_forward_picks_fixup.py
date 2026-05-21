"""AC.PASH.B.1 — BASELINE walk-forward picks latest `chore(amend-fixup):` commit.

Per amendment #142 Scope B (closes FIDRAFT 336). A fresh persona/agent
following the plan-author SKILLs authoring an amendment that follows
a fixup-bearing seal picks the latest `chore(amend-fixup):` commit as
BASELINE (not the bare seal commit).

The walk-forward discipline is SKILL-prose-only (no production helper
per D-PASH.BASELINE-WALK + plan-doc §3 / §8). This test verifies the
discipline produces the expected output on a synthetic git fixture by
implementing the prescription locally + asserting the BASELINE
selection matches.

Plan: docs/plans/amendment-142-plan-author-skill-hygiene-merged.md §4
AC.PASH.B.1; outcome-altitude: false.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _select_baseline_per_skill_prescription(
    repo: Path, predecessor_seal_sha: str
) -> str:
    """Implement the Scope B walk-forward discipline locally.

    Mirrors the SKILL-prose prescription from amendment #142 Scope B:
    walk forward from the predecessor seal commit; if any
    `chore(amend-fixup):` commits exist between that seal and current
    HEAD, return the latest such fixup SHA; else return the seal SHA.

    Implementation note: kept local to this test (NOT promoted to a
    `loam_amend` production helper per D-PASH.BASELINE-WALK — the
    prescription is discipline-only).
    """
    # Walk commits in chronological order from <seal>..HEAD.
    proc = subprocess.run(
        [
            "git",
            "log",
            "--reverse",
            "--format=%H %s",
            f"{predecessor_seal_sha}..HEAD",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    latest_fixup: str | None = None
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition(" ")
        if subject.startswith("chore(amend-fixup):"):
            latest_fixup = sha
    return latest_fixup if latest_fixup else predecessor_seal_sha


def test_AC_PASH_B_1_walk_forward_picks_latest_fixup(
    scratch_repo: Path,
) -> None:
    """When a `chore(amend-fixup):` commit exists between predecessor
    seal and HEAD, BASELINE walks forward to the fixup."""
    repo = scratch_repo
    # Seed a synthetic seal commit `S`.
    (repo / "stub.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore(seals): seed seal commit S")
    seal_sha = _git(repo, "rev-parse", "HEAD")

    # Land an unrelated docs commit on top.
    (repo / "stub.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs: an unrelated commit")

    # Now land a corrective fixup commit `F` (the post-seal cleanup
    # pattern that triggered #139's stale-BASELINE failure).
    (repo / "stub.py").write_text("x = 3\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        "chore(amend-fixup): orphan-file cleanup post-seal",
    )
    fixup_sha = _git(repo, "rev-parse", "HEAD")

    # Walk-forward discipline should pick F, not S.
    chosen = _select_baseline_per_skill_prescription(repo, seal_sha)
    assert chosen == fixup_sha, (
        f"walk-forward picked {chosen!r}; expected fixup {fixup_sha!r} "
        f"(not the bare seal {seal_sha!r}). Amendment #142 Scope B "
        "regression."
    )


def test_AC_PASH_B_1_walk_forward_picks_LATEST_fixup_when_multiple(
    scratch_repo: Path,
) -> None:
    """When MULTIPLE fixups exist, BASELINE walks forward to the
    LATEST (not the earliest)."""
    repo = scratch_repo
    (repo / "stub.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore(seals): seed seal S")
    seal_sha = _git(repo, "rev-parse", "HEAD")

    # First fixup.
    (repo / "stub.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore(amend-fixup): first fixup")
    first_fixup = _git(repo, "rev-parse", "HEAD")

    # Second fixup (the latest).
    (repo / "stub.py").write_text("x = 3\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore(amend-fixup): second fixup")
    second_fixup = _git(repo, "rev-parse", "HEAD")

    chosen = _select_baseline_per_skill_prescription(repo, seal_sha)
    assert chosen == second_fixup, (
        f"walk-forward picked {chosen!r}; expected latest fixup "
        f"{second_fixup!r} (not the earlier {first_fixup!r})."
    )
    assert chosen != first_fixup


def test_AC_PASH_B_1_skill_prose_carries_walk_forward_prescription() -> None:
    """The four plan-author SKILLs each carry the walk-forward
    prescription string (verifies the SKILL-prose surface a fresh
    agent would read)."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    surfaces = [
        "plugins/dev-sdlc/skills/plan-docs-author/SKILL.md",
        "plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md",
        "plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md",
    ]
    for rel in surfaces:
        text = (repo_root / rel).read_text(encoding="utf-8")
        # The prescription must mention BOTH "walk forward" (the
        # discipline name) AND `chore(amend-fixup):` (the predicate)
        # in the same surface.
        assert (
            "walk forward" in text.lower() or "walk-forward" in text.lower()
        ), (
            f"SKILL {rel} missing the walk-forward prescription "
            "(amendment #142 Scope B regression)."
        )
        assert "chore(amend-fixup)" in text, (
            f"SKILL {rel} missing the `chore(amend-fixup):` predicate "
            "in the walk-forward prescription."
        )
