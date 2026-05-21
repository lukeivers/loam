"""AC.FBMT1.APS.2 — plan-doc content unchanged post-move (pre-§14-backfill).

The plan-doc's internal cross-references (other plan-docs, doc paths)
remain functional — the move does not break content. The body bytes
between the original (pre-seal) plan-doc and the moved (post-seal,
pre-§14-backfill) plan-doc are identical.

Note: the §14 SHA backfill step adds a ``### Commit SHAs`` subsection
to the moved plan-doc; the content-unchanged property is verified
between (a) the original committed plan-doc body and (b) the body of
the moved plan-doc at the seal commit (before the §14 backfill
commit lands).

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
            # Fixture plan doc — APS.2 content verification

            ## 1. Summary

            Plan-doc body content carrying internal references
            like [other](docs/plans/other-plan.md) and code
            spans (`code/path/here.py`) that must remain
            byte-identical post-move.

            ## 14. Method-decision record

            placeholder body.
            """
        ).lstrip(),
        encoding="utf-8",
    )


def test_AC_FBMT1_APS_2_plan_doc_content_byte_identical_at_seal_commit(
    sealed_repo,
):
    """The plan-doc at its post-move location in the SEAL COMMIT
    is byte-identical to the pre-seal plan-doc. The §14 backfill
    commit (which adds the SHA subsection) lands AFTER the seal
    commit; the seal commit's tree carries the unmodified content."""
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "aps-2-content.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/aps-2-content.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")
    pre_seal_content = plan_path.read_bytes()

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1020,
        slug="aps-2-content",
        seal_description="APS-2",
    )
    _make_amendment_commit(repo, "alpha", payload="aps2")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    # Find the seal commit (chore(seals):) and read the plan-doc
    # at that commit. The seal commit's tree carries the moved
    # plan-doc with body byte-identical to the pre-seal version.
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

    moved_at_seal = _git(
        repo, "show", f"{seal_sha}:docs/plans/sealed/aps-2-content.md"
    ).stdout.encode("utf-8")
    assert moved_at_seal == pre_seal_content, (
        "plan-doc content at seal commit differs from pre-seal"
    )


def test_AC_FBMT1_APS_2_internal_references_preserved(sealed_repo):
    """Internal references inside the plan-doc body (links to
    other plan-docs, code paths) are preserved — the move is
    rename-only, no path-rewriting."""
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "aps-2b-refs.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/aps-2b-refs.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1021,
        slug="aps-2b-refs",
        seal_description="APS-2b",
    )
    _make_amendment_commit(repo, "alpha", payload="aps2b")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    # The moved plan-doc in the working tree (post-§14 backfill)
    # carries the original internal references.
    moved_plan = repo / "docs" / "plans" / "sealed" / "aps-2b-refs.md"
    assert moved_plan.exists()
    text = moved_plan.read_text(encoding="utf-8")
    assert "[other](docs/plans/other-plan.md)" in text
    assert "`code/path/here.py`" in text
