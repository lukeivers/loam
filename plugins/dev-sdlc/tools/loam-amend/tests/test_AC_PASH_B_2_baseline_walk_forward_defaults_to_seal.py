"""AC.PASH.B.2 — BASELINE walk-forward defaults to seal when no fixup.

Per amendment #142 Scope B (closes FIDRAFT 336). When NO
`chore(amend-fixup):` commits exist between the predecessor seal and
current HEAD, BASELINE defaults to the seal commit itself (no
regression vs the pre-fix discipline — the walk-forward must NOT
arbitrarily pick a non-fixup commit just because something landed
after the seal).

Plan: docs/plans/amendment-142-plan-author-skill-hygiene-merged.md §4
AC.PASH.B.2; outcome-altitude: false.
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
    """Mirror of the Scope B walk-forward discipline (see AC.PASH.B.1)."""
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


def test_AC_PASH_B_2_defaults_to_seal_when_no_fixups(
    scratch_repo: Path,
) -> None:
    """No fixup → BASELINE is the seal commit itself."""
    repo = scratch_repo
    (repo / "stub.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore(seals): seed seal S")
    seal_sha = _git(repo, "rev-parse", "HEAD")

    # Land a `docs:` commit on top (NOT a fixup — should be ignored).
    (repo / "stub.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs: README touch unrelated to S")
    docs_sha = _git(repo, "rev-parse", "HEAD")

    chosen = _select_baseline_per_skill_prescription(repo, seal_sha)
    assert chosen == seal_sha, (
        f"walk-forward picked {chosen!r}; expected seal {seal_sha!r}. "
        f"Unrelated `docs:` commit ({docs_sha!r}) must NOT be picked."
    )
    assert chosen != docs_sha


def test_AC_PASH_B_2_defaults_to_seal_when_HEAD_equals_seal(
    scratch_repo: Path,
) -> None:
    """When HEAD == predecessor seal (no intervening commits at all),
    BASELINE is the seal commit (degenerate case but must not crash)."""
    repo = scratch_repo
    (repo / "stub.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore(seals): seed seal S")
    seal_sha = _git(repo, "rev-parse", "HEAD")

    chosen = _select_baseline_per_skill_prescription(repo, seal_sha)
    assert chosen == seal_sha


def test_AC_PASH_B_2_feat_commits_not_picked() -> None:
    """`feat(...):` commits between seal and HEAD must NOT be picked
    (only `chore(amend-fixup):` is the predicate)."""
    # This is a unit-level invariant on the prescription's predicate.
    # Verify the test helper does NOT match a `feat(...)` subject.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=repo, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "t@t.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "t"], cwd=repo, check=True
        )

        (repo / "s.py").write_text("x = 1\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "chore(seals): seed")
        seal = _git(repo, "rev-parse", "HEAD")

        # A `feat(...)` commit between seal and HEAD must NOT be picked.
        (repo / "s.py").write_text("x = 2\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(
            repo,
            "commit",
            "-q",
            "-m",
            "feat(comp): real source-edit work",
        )

        chosen = _select_baseline_per_skill_prescription(repo, seal)
        assert chosen == seal, (
            "`feat(...):` commit must NOT be picked as fixup."
        )
