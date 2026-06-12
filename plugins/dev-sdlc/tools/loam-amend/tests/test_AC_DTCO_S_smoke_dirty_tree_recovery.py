"""AC.DTCO.S — outcome-altitude smoke: synthetic seal cycle with an
intentionally-dirty working tree halts cleanly; post-halt working
tree has the plan-doc still at ``docs/plans/<slug>.md`` (NOT at
``docs/plans/sealed/<slug>.md``).

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope B: F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE).

``outcome-altitude: true`` — invokes the production seal entry-point
against a workspace with an unrelated dirty file. Asserts exit 3
AND filesystem state shows the plan-doc at its pre-seal location.

Pre-amendment-#138, the same scenario halted with exit 3 but left
the plan-doc + manifest moved into ``docs/plans/sealed/`` (the
operator had to ``git mv`` them back manually). Post-amendment, no
recovery work is needed.
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


def test_AC_DTCO_S_dirty_tree_halt_leaves_working_tree_pristine(
    sealed_repo, monkeypatch
):
    """End-to-end smoke: dirty file → seal halts at gate → plan-doc
    + manifest at pre-seal locations → no manual recovery needed.

    The pre-amendment-#138 failure mode this prevents: operator
    invoked ``loam amend seal``, hit a dirty-tree halt, found the
    plan-doc had been moved to ``docs/plans/sealed/<slug>.md`` and
    the manifest to ``docs/plans/sealed/<slug>.manifest.yaml``,
    needed two ``git mv`` commands to restore the pre-seal state
    before re-invoking. Now the halt leaves nothing to undo."""
    repo = sealed_repo
    monkeypatch.chdir(repo)
    plan_path = repo / "docs" / "plans" / "dtco-s-fixture.md"
    _write_plan_doc(plan_path)
    _git(repo, "add", "--", "docs/plans/dtco-s-fixture.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=2006,
        slug="dtco-s-fixture",
        seal_description="DTCO-S",
    )
    _make_amendment_commit(repo, "alpha", payload="dtco-s")

    # Snapshot the post-amendment HEAD — the seal must NOT advance.
    pre_seal_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    # Untracked dirt that the seal step has no admission for.
    dirty_file = repo / "unrelated-dirt.txt"
    dirty_file.write_text("intentionally untracked\n", encoding="utf-8")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path),
         str(manifest_path)]
    )

    # (1) Exit 3 (dirty-working-tree).
    assert rc == 3, (
        f"seal must halt with exit 3 on dirty working tree; got {rc}"
    )

    # (2) Plan-doc + manifest at original locations (NOT in sealed/).
    assert plan_path.exists()
    assert manifest_path.exists()
    sealed_plan = repo / "docs" / "plans" / "sealed" / plan_path.name
    sealed_manifest = (
        repo / "docs" / "plans" / "sealed" / manifest_path.name
    )
    assert not sealed_plan.exists(), (
        "AC.DTCO.S outcome-altitude check: plan-doc must NOT have "
        "been moved to docs/plans/sealed/ on halt"
    )
    assert not sealed_manifest.exists(), (
        "AC.DTCO.S outcome-altitude check: manifest must NOT have "
        "been moved to docs/plans/sealed/ on halt"
    )

    # (3) HEAD unchanged — no seal commit landed.
    post_halt_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert post_halt_sha == pre_seal_sha, (
        f"seal must not have advanced HEAD on halt; pre={pre_seal_sha} "
        f"post={post_halt_sha}"
    )

    # (4) Working-tree state for plan-doc + manifest: NEITHER staged
    # nor moved. The only dirty entries should be the untracked
    # ``unrelated-dirt.txt``.
    porcelain = _git(repo, "status", "--porcelain").stdout
    lines_with_plan_doc = [
        line for line in porcelain.splitlines()
        if "dtco-s-fixture" in line and "sealed/" in line
    ]
    assert not lines_with_plan_doc, (
        f"no rename-into-sealed/ should be staged on halt; "
        f"got porcelain lines:\n{porcelain}"
    )
