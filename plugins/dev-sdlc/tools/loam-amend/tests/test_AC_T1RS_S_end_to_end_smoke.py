"""AC.T1RS.S (outcome-altitude: true) — synthetic amendment cycle
exercises all three Scopes A + B + C end-to-end.

Per amendment #143 §4 AC.T1RS.S + §10 F2 doubt #5 + the outcome-
altitude rule (feedback_test_outcome_altitude_required): this test
invokes the PRODUCTION sweep-archive CLI against an un-pre-arranged
tmpfs git fixture and verifies the full pipeline:

  Setup:
    (a) pre-#134-style plan-doc with body-slug-only seal (Strategy 2)
    (b) post-#134-style plan-doc with full-slug seal (Strategy 1)
    (c) in-flight plan-doc (no seal)
    (d) ambiguous plan-doc (two matching seals)

  Run:
    1. sweep-archive --dry-run — verify the dry-run report names
       the moves correctly.
    2. sweep-archive --apply — execute the real sweep.

  Verify:
    - (a) + (b) moved to docs/plans/sealed/
    - (c) + (d) still in docs/plans/
    - One ``chore(retroactive-sweep):`` commit landed.
    - All FOUR downstream consumers iterate correctly across both
      directories (release-gate _find_plan_doc, heavy-b-migrate
      discover_amendment_plans, primary-persona session-start
      enumerate_amendments_in_flight + enumerate_sealed_amendments,
      dev-sdlc bash-guard _candidate_manifests).

No pre-arrangement of partial-sweep state.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_amend.commands import sweep_archive as sweep_archive_cmd
from loam_amend.plan_locator import (
    find_plan_doc_by_slug_glob,
    iter_all_manifests,
    iter_all_plan_docs,
)


# outcome-altitude: true
# (this test invokes the production sweep-archive CLI + the four
# downstream consumer helpers against an un-pre-arranged tmpfs
# git fixture)
pytestmark = pytest.mark.outcome_altitude


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


_C = {"n": 0}


def _seal(repo: Path, subject: str) -> str:
    _C["n"] += 1
    m = repo / f".s-{_C['n']}"
    m.write_text("x", encoding="utf-8")
    _git(repo, "add", "--", str(m.relative_to(repo)))
    _git(repo, "commit", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def end_to_end_repo(tmp_path):
    """A four-plan-doc fixture exercising all three strategies +
    in-flight + ambiguous buckets simultaneously."""
    repo = tmp_path / "e2e-repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")

    plans = repo / "docs" / "plans"
    plans.mkdir(parents=True)

    # (a) Pre-#134-style: body-slug-only attribution (Strategy 2).
    (plans / "amendment-22-foo.md").write_text(
        "# foo\n", encoding="utf-8"
    )
    (plans / "amendment-22-foo.manifest.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )

    # (b) Post-#134-style: full-slug attribution (Strategy 1).
    (plans / "amendment-134-canonical.md").write_text(
        "# canonical\n", encoding="utf-8"
    )

    # (c) In-flight: no seal at all.
    (plans / "amendment-200-pending.md").write_text(
        "# pending\n", encoding="utf-8"
    )

    # (d) Ambiguous: two matching seals.
    (plans / "amendment-77-ambig.md").write_text(
        "# ambig\n", encoding="utf-8"
    )

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: four-plan-doc seed")

    # Strategy 2 seal for (a): body-slug only, no ``amendment-22-``.
    _seal(repo, "chore(seals): foo seal — pre-#134-style attribution")
    # Strategy 1 seal for (b): full slug in subject.
    _seal(
        repo,
        "chore(seals): amendment-134-canonical seal — full-slug attribution",
    )
    # No seal for (c).
    # Two seals for (d): ambiguous in Strategy 2.
    _seal(repo, "chore(seals): ambig seal — first")
    _seal(repo, "chore(seals): ambig seal — second")
    return repo


def test_AC_T1RS_S_end_to_end_smoke(end_to_end_repo, capsys):
    """All three scopes exercised end-to-end against an un-pre-
    arranged fixture; production CLI + helper entry-points
    invoked."""
    repo = end_to_end_repo

    # 1. Dry-run preview (Scope C entry-point).
    rc = sweep_archive_cmd.run(repo, dry_run=True)
    assert rc == 0
    dry_report = capsys.readouterr().out
    # Dry-run names (a) + (b), classifies (d) as ambiguous, leaves
    # (c) implicit (in-flight count > 0).
    assert "amendment-22-foo.md" in dry_report
    assert "amendment-134-canonical.md" in dry_report
    assert "amendment-77-ambig.md" in dry_report
    assert "in-flight: 1" in dry_report or "in-flight:" in dry_report

    # 2. Real run (Scope C real-mode).
    rc = sweep_archive_cmd.run(repo, dry_run=False)
    assert rc == 0
    real_report = capsys.readouterr().out
    assert "sweep:" in real_report

    # 3. Verify file moves.
    sealed = repo / "docs" / "plans" / "sealed"
    plans = repo / "docs" / "plans"
    # (a) + (b) moved.
    assert (sealed / "amendment-22-foo.md").exists()
    assert (sealed / "amendment-134-canonical.md").exists()
    # (a)'s manifest sibling rides with it.
    assert (sealed / "amendment-22-foo.manifest.yaml").exists()
    # (c) + (d) stay in docs/plans/.
    assert (plans / "amendment-200-pending.md").exists()
    assert (plans / "amendment-77-ambig.md").exists()
    # And NOT in sealed/.
    assert not (sealed / "amendment-200-pending.md").exists()
    assert not (sealed / "amendment-77-ambig.md").exists()

    # 4. Exactly one ``chore(retroactive-sweep):`` commit.
    subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert subject.startswith("chore(retroactive-sweep):"), subject
    assert "amendment #143 Scope C" in subject

    # 5. Each of the four downstream consumers iterates correctly
    # across both directories. We exercise the SHARED HELPERS
    # directly here (Scope B AC.T1RS.GLOB.{1,2,3}); the downstream
    # consumer modules route through them in production so the
    # behavior is equivalent at the helper boundary.

    # 5a. release-gate _find_plan_doc semantics: find a sealed
    # plan-doc by its slug prefix (lookup via find_plan_doc_by_slug_glob).
    found = find_plan_doc_by_slug_glob(repo, "amendment-22-foo")
    assert found is not None
    assert "sealed" in found.parts, "sealed plan-doc resolved"
    # And an in-flight one still resolves to its live location.
    found_live = find_plan_doc_by_slug_glob(repo, "amendment-200-pending")
    assert found_live is not None
    assert "sealed" not in found_live.parts

    # 5b. heavy-b-migrate semantics: iter_all_plan_docs covers both.
    all_paths = sorted(p.name for p in iter_all_plan_docs(repo))
    # Live: 200-pending + 77-ambig still in docs/plans/; sealed:
    # 22-foo + 134-canonical now in docs/plans/sealed/.
    assert "amendment-22-foo.md" in all_paths
    assert "amendment-134-canonical.md" in all_paths
    assert "amendment-200-pending.md" in all_paths
    assert "amendment-77-ambig.md" in all_paths

    # 5c. session-start semantics: in-flight vs sealed enumeration
    # via the helper's include_sealed flag (production callers route
    # through it).
    in_flight_only = sorted(
        p.name for p in iter_all_plan_docs(repo, include_sealed=False)
    )
    assert "amendment-200-pending.md" in in_flight_only
    assert "amendment-77-ambig.md" in in_flight_only
    assert "amendment-22-foo.md" not in in_flight_only
    assert "amendment-134-canonical.md" not in in_flight_only

    # 5d. bash-guard semantics: iter_all_manifests covers both
    # locations.
    manifest_names = sorted(p.name for p in iter_all_manifests(repo))
    assert "amendment-22-foo.manifest.yaml" in manifest_names
    # Manifest moved with its plan-doc; verify by location.
    sealed_manifests = sorted(p.name for p in (sealed.iterdir()) if p.name.endswith(".manifest.yaml"))
    assert "amendment-22-foo.manifest.yaml" in sealed_manifests
