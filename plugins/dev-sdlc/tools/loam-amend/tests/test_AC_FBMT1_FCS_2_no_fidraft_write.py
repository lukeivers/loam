"""AC.FBMT1.FCS.2 — FIDRAFT cleanup hook never writes FIDRAFT.

Test captures the SHA + mtime of ``docs/FUTURE_IDEAS_DRAFT.md``
before sealing; asserts they are unchanged after the hook fires.
The cleanup hook is owner-gated by design — it surfaces only.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.FCS family.
"""

from __future__ import annotations

import hashlib
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


def test_AC_FBMT1_FCS_2_hook_never_writes_fidraft(sealed_repo):
    """SHA + mtime of FIDRAFT are unchanged after the seal hook
    fires — the hook is read-only by design."""
    repo = sealed_repo
    fidraft = repo / "docs" / "FUTURE_IDEAS_DRAFT.md"
    fidraft.parent.mkdir(parents=True, exist_ok=True)
    fidraft.write_text(
        "# FUTURE_IDEAS_DRAFT\n\n"
        "- Entry that strongly overlaps the plan slug below: "
        "the snowboard-ergonomics-test draft.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/FUTURE_IDEAS_DRAFT.md")
    _git(repo, "commit", "-q", "-m", "fixture: FIDRAFT")

    pre_sha = hashlib.sha256(fidraft.read_bytes()).hexdigest()
    pre_mtime = fidraft.stat().st_mtime

    plan_path = repo / "docs" / "plans" / "snowboard-ergonomics-test.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/snowboard-ergonomics-test.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1001,
        slug="snowboard-ergonomics-test",
        seal_description="FCS-2",
    )
    _make_amendment_commit(repo, "alpha", payload="fcs2")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    post_sha = hashlib.sha256(fidraft.read_bytes()).hexdigest()
    post_mtime = fidraft.stat().st_mtime

    assert pre_sha == post_sha, (
        "FIDRAFT content changed after seal hook fired"
    )
    assert pre_mtime == post_mtime, (
        "FIDRAFT mtime changed after seal hook fired"
    )
