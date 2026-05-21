"""AC.DTCO.1 — dirty-tree validation gate fires BEFORE any plan-doc
/ manifest file move.

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope B: F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE).

Pre-amendment-#138 the T1.4 plan-doc archive step ran BEFORE the
dirty-tree validation gate (see amendment #134's docstring at
canonical line 656-658 — "archive plan-doc + manifest BEFORE the
dirty-tree check, so the moved files are part of the expected-
writes set"). When the gate halted, ``git mv`` had already moved
the plan-doc + manifest into ``docs/plans/sealed/`` and the
operator had to manually move them back. Amendment #138 reorders
so the gate halt leaves the working tree pristine.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)


def _write_plan_doc(plan_path: Path) -> None:
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "# Fixture plan doc\n\n## §14. Method-decision register\n\n"
        "placeholder.\n",
        encoding="utf-8",
    )


def test_AC_DTCO_1_halt_leaves_plan_doc_at_original_location(
    sealed_repo, monkeypatch
):
    """A dirty-tree halt during seal leaves the plan-doc + manifest at
    their pre-seal locations (docs/plans/<slug>.md), NOT moved into
    docs/plans/sealed/. Pre-amendment-#138 this was reversed."""
    repo = sealed_repo
    monkeypatch.chdir(repo)
    plan_path = repo / "docs" / "plans" / "dtco-1-fixture.md"
    _write_plan_doc(plan_path)
    _git(repo, "add", "--", "docs/plans/dtco-1-fixture.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=2005,
        slug="dtco-1-fixture",
        seal_description="DTCO-1",
    )
    _make_amendment_commit(repo, "alpha", payload="dtco1")

    # Land an unrelated dirty file (untracked).
    dirty_file = repo / "unrelated-dirt.txt"
    dirty_file.write_text("intentionally untracked\n", encoding="utf-8")

    rc = cli_main(
        ["seal", "--scoped-sweep", "--plan-doc", str(plan_path),
         str(manifest_path)]
    )
    assert rc == 3, "seal must halt with exit 3 on dirty working tree"

    # Plan-doc + manifest still at original locations.
    assert plan_path.exists(), (
        "plan-doc must still be at docs/plans/<slug>.md after a "
        "dirty-tree halt (pre-amendment-#138 it was moved to "
        "docs/plans/sealed/ and the operator had to git-mv it back)"
    )
    assert manifest_path.exists(), (
        "manifest must still be at docs/plans/ after a dirty-tree halt"
    )
    sealed_plan = repo / "docs" / "plans" / "sealed" / plan_path.name
    sealed_manifest = (
        repo / "docs" / "plans" / "sealed" / manifest_path.name
    )
    assert not sealed_plan.exists(), (
        f"plan-doc must NOT have been moved to {sealed_plan} on halt"
    )
    assert not sealed_manifest.exists(), (
        f"manifest must NOT have been moved to {sealed_manifest} on halt"
    )
