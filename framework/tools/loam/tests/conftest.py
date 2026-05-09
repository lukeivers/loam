"""Shared fixtures for the loam-cli test suite (release-process specific).

The fixtures here scaffold a temporary repository tree resembling the
canonical loam layout (`docs/experiments/`, `docs/plans/`,
`docs/release-roadmap.md`, `docs/STATE.md`) so the per-gate tests
under `test_AC_V060_2_*` can verify each pre-publish gate against a
realistic pattern without depending on the live canonical state.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def scratch_repo(tmp_path: Path) -> Path:
    """Initialise a tiny throwaway git repo on `main` with one
    seed commit so reachability checks resolve.

    The repo lives at ``tmp_path/repo/`` so sibling directories
    (e.g., bare remotes) can co-exist under ``tmp_path/`` without
    appearing as untracked files inside the working tree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "release-test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "loam release test"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=repo,
        check=True,
    )
    (repo / "README.md").write_text("scratch\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "initial"],
        cwd=repo,
        check=True,
    )
    return repo


@pytest.fixture
def fixture_version() -> str:
    """The version literal every release-process gate test pair targets."""
    return "v0.6.0"


@pytest.fixture
def fixture_slug(fixture_version: str) -> str:
    return fixture_version.replace(".", "-")


@pytest.fixture
def staged_repo(
    scratch_repo: Path, fixture_version: str, fixture_slug: str
) -> Path:
    """Scaffold the canonical doc surface needed by every gate.

    Each gate's RED test mutates one of these files (or removes it)
    to force the failure mode under test; each gate's GREEN test
    relies on the as-staged shape.
    """
    docs = scratch_repo / "docs"
    (docs / "experiments").mkdir(parents=True)
    (docs / "plans").mkdir(parents=True)

    # HARD smoke writeup (gate 1).
    (docs / "experiments" / f"{fixture_slug}-hard-smoke.md").write_text(
        f"# {fixture_version} HARD smoke — rd-automation extraction\n\n"
        "**Verdict: GREEN.** Aggregate verdict for AC.V060.HS: ok.\n",
        encoding="utf-8",
    )

    # Plan-doc with §status backfill (gate 2).
    plan_body = (
        f"# {fixture_version} minor — release process\n\n"
        "## §4 Acceptance criteria\n\n"
        "### AC.V060.1 — CLI verb\n\nDoes a thing.\n\n"
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n"
        "## §13 §status\n\n"
        "AC verdict matrix:\n\n"
        "- AC.V060.1: GREEN\n"
        "- AC.V060.2: GREEN\n"
    )
    (docs / "plans" / f"{fixture_slug}-release-process.md").write_text(
        plan_body, encoding="utf-8"
    )

    # release-roadmap with §2 row (gate 6) + §4 mapped versions
    # (post-ship review block reads §4).
    roadmap_body = (
        "# Release Roadmap\n\n"
        "## §2 Shipped\n\n"
        "| Version | Objective sentence | Anchor |\n"
        "|---|---|---|\n"
        "| v0.5.1 | predecessor objective | seal `aaaaaaa` |\n"
        f"| {fixture_version} | next outcome shape | "
        "Single-cycle MINOR: apply `bbbbbbb`; seal `SEAL_PLACEHOLDER` |\n\n"
        "## §4 Mapped versions\n\n"
        "### v0.7.0 — next things land here\n\n"
        "Some prose about the next entry.\n"
    )
    (docs / "release-roadmap.md").write_text(
        roadmap_body, encoding="utf-8"
    )

    # STATE.md SHIPPED rollup (gate 3).
    (docs / "STATE.md").write_text(
        f"# State\n\nv0.5.1 SHIPPED 2026-05-09 — predecessor.\n"
        f"{fixture_version} SHIPPED 2026-05-09 — release-process work.\n",
        encoding="utf-8",
    )

    # FUTURE_IDEAS_DRAFT.md (post-ship review reads recent captures).
    (docs / "FUTURE_IDEAS_DRAFT.md").write_text(
        "# Future ideas\n\n- **Idea one** captured 2026-05-09.\n",
        encoding="utf-8",
    )

    # Stage + commit so HEAD has these files; then capture the seal SHA.
    subprocess.run(
        ["git", "add", "docs/"], cwd=scratch_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "scaffold docs"],
        cwd=scratch_repo,
        check=True,
    )
    seal = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=scratch_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    # Replace placeholder seal in roadmap with the real HEAD SHA, then
    # commit the substitution so HEAD reflects the final body shape.
    roadmap_path = docs / "release-roadmap.md"
    roadmap_path.write_text(
        roadmap_path.read_text(encoding="utf-8").replace(
            "SEAL_PLACEHOLDER", seal[:7]
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "docs/release-roadmap.md"],
        cwd=scratch_repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "backfill seal SHA"],
        cwd=scratch_repo,
        check=True,
    )
    return scratch_repo
