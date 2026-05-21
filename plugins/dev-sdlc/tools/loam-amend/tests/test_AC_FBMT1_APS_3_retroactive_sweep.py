"""AC.FBMT1.APS.3 — retroactive one-shot sweep moves sealed plan-docs.

Runs the retroactive sweep against a tmpfs git repo with a mix of
sealed + in-flight plan-docs; asserts only sealed plan-docs moved;
asserts in-flight ones remain in ``docs/plans/``.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.APS family + §6 step 8.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_amend.plan_archive import sweep_sealed_plan_docs


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


_SEAL_COUNTER = {"n": 0}


def _commit_seal(repo: Path, slug: str) -> str:
    """Create a fake seal commit that mentions ``slug`` in its
    message. Used to set up the test fixture. Each invocation
    creates a uniquely-named marker file so distinct seal commits
    can land for the same slug (testing the ambiguous case)."""
    _SEAL_COUNTER["n"] += 1
    nonce = _SEAL_COUNTER["n"]
    marker = repo / f".{slug}-marker-{nonce}"
    marker.write_text(f"seal marker {nonce}\n", encoding="utf-8")
    _git(repo, "add", "--", str(marker.relative_to(repo)))
    _git(
        repo,
        "commit",
        "-m",
        f"chore(seals): {slug} sealed at fixture {nonce}\n\n"
        f"Plan: docs/plans/{slug}.md\n",
    )
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo_with_mixed_plans(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")

    plans = repo / "docs" / "plans"
    plans.mkdir(parents=True)
    # Three plan-docs:
    #   - sealed-one: has a matching seal commit (one).
    #   - sealed-two: has a matching seal commit (one). Has a
    #     sibling manifest.
    #   - in-flight: no matching seal commit.
    for slug in ("sealed-one", "sealed-two", "in-flight"):
        (plans / f"{slug}.md").write_text(
            f"# {slug}\n", encoding="utf-8"
        )
    (plans / "sealed-two.manifest.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-docs seeded")

    # Seal sealed-one + sealed-two (each gets its own seal commit).
    _commit_seal(repo, "sealed-one")
    _commit_seal(repo, "sealed-two")
    # in-flight has no seal commit — that's the test.
    return repo


def test_AC_FBMT1_APS_3_sealed_plan_docs_moved_inflight_preserved(
    repo_with_mixed_plans,
):
    """Sealed plan-docs land under docs/plans/sealed/; in-flight
    stays in docs/plans/."""
    repo = repo_with_mixed_plans
    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _new in result.moved}
    assert "sealed-one.md" in moved_names
    assert "sealed-two.md" in moved_names
    # Manifest sibling moved too.
    assert "sealed-two.manifest.yaml" in moved_names
    # in-flight stays.
    assert "in-flight.md" not in moved_names
    assert (repo / "docs" / "plans" / "in-flight.md").exists()
    assert not (repo / "docs" / "plans" / "sealed-one.md").exists()
    assert (repo / "docs" / "plans" / "sealed" / "sealed-one.md").exists()
    assert (repo / "docs" / "plans" / "sealed" / "sealed-two.md").exists()
    assert (
        repo / "docs" / "plans" / "sealed" / "sealed-two.manifest.yaml"
    ).exists()


def test_AC_FBMT1_APS_3_dry_run_does_not_move(repo_with_mixed_plans):
    """``dry_run=True`` returns the would-be moves without
    executing them — used by a higher-level caller that wants to
    preview before committing."""
    repo = repo_with_mixed_plans
    result = sweep_sealed_plan_docs(repo, dry_run=True)
    # Result lists the would-be moves.
    assert len(result.moved) >= 2
    # Files are still at their original locations.
    assert (repo / "docs" / "plans" / "sealed-one.md").exists()
    assert (repo / "docs" / "plans" / "sealed-two.md").exists()
    assert not (
        repo / "docs" / "plans" / "sealed" / "sealed-one.md"
    ).exists()


def test_AC_FBMT1_APS_3_ambiguous_plan_doc_left_in_place(tmp_path):
    """A plan-doc whose slug matches MULTIPLE seal commits is
    left in place for manual triage (§8 halt trigger #5)."""
    repo = tmp_path / "repo-amb"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")

    plans = repo / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "ambiguous-slug.md").write_text(
        "# ambiguous\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture")
    # Two seal commits mentioning the slug — ambiguous.
    _commit_seal(repo, "ambiguous-slug")
    _commit_seal(repo, "ambiguous-slug")

    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _ in result.moved}
    assert "ambiguous-slug.md" not in moved_names
    ambig_names = {p.name for p in result.ambiguous}
    assert "ambiguous-slug.md" in ambig_names
    # The file is still in docs/plans/.
    assert (repo / "docs" / "plans" / "ambiguous-slug.md").exists()
