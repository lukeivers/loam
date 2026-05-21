"""AC.FBMT1.APS.1 — plan-doc archives into docs/plans/sealed/ on seal.

After ``loam amend seal`` completes for an amendment whose manifest's
``plan:`` points at ``docs/plans/<slug>.md``, the plan-doc + manifest
YAML are at ``docs/plans/sealed/<slug>.md`` + ``docs/plans/sealed/
<slug>.manifest.yaml``, and the seal commit includes the rename.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.APS family.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)


def _write_plan_doc_with_section_14(plan_path: Path) -> None:
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Fixture plan doc

            ## 1. Summary

            placeholder.

            ## 14. Method-decision record

            placeholder body.
            """
        ).lstrip(),
        encoding="utf-8",
    )


def test_AC_FBMT1_APS_1_plan_doc_and_manifest_move_on_seal(sealed_repo):
    """After seal, the plan-doc + manifest live under
    docs/plans/sealed/ and no longer at docs/plans/."""
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "aps-1-fixture.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/aps-1-fixture.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1010,
        slug="aps-1-fixture",
        seal_description="APS-1",
    )
    _make_amendment_commit(repo, "alpha", payload="aps1")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    # Old locations no longer exist.
    assert not plan_path.exists()
    assert not manifest_path.exists()
    # New locations exist — same filename, just under sealed/.
    sealed_plan = repo / "docs" / "plans" / "sealed" / plan_path.name
    sealed_manifest = (
        repo / "docs" / "plans" / "sealed" / manifest_path.name
    )
    assert sealed_plan.exists()
    assert sealed_manifest.exists()


def test_AC_FBMT1_APS_1_seal_commit_includes_the_rename(sealed_repo):
    """The seal commit (chore(seals): ...) tree contains the
    plan-doc + manifest at the sealed path — the rename is IN the
    seal commit, not a separate later commit."""
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "aps-1b-included.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/aps-1b-included.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1011,
        slug="aps-1b-included",
        seal_description="APS-1b",
    )
    _make_amendment_commit(repo, "alpha", payload="aps1b")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    # Find the seal commit (chore(seals):) — should be one of the
    # most-recent commits. Walk recent log lines.
    log_lines = _git(
        repo, "log", "-5", "--format=%H %s"
    ).stdout.strip().splitlines()
    seal_sha = None
    for line in log_lines:
        sha, _, subject = line.partition(" ")
        if subject.startswith("chore(seals):"):
            seal_sha = sha
            break
    assert seal_sha is not None

    # The seal commit's tree contains the file at the sealed path.
    files_in_seal = _git(
        repo, "show", "--name-only", "--format=", seal_sha
    ).stdout.strip().splitlines()
    assert f"docs/plans/sealed/{plan_path.name}" in files_in_seal
    assert f"docs/plans/sealed/{manifest_path.name}" in files_in_seal
