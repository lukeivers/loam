"""AC.FBMT1.FCS.4 — --skip-fidraft-cleanup bypasses the hook.

The cleanup hook is skippable via a flag for emergency seals where
the operator wants to bypass.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.FCS family.
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


def test_AC_FBMT1_FCS_4_skip_flag_suppresses_surface(sealed_repo, capsys):
    """With ``--skip-fidraft-cleanup``, the hook does not fire —
    no FIDRAFT cleanup surface appears in seal output even when a
    matching FIDRAFT entry exists."""
    repo = sealed_repo
    fidraft = repo / "docs" / "FUTURE_IDEAS_DRAFT.md"
    fidraft.parent.mkdir(parents=True, exist_ok=True)
    fidraft.write_text(
        "- **Snowboard ergonomics entry.** would match strongly if "
        "the hook fired.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/FUTURE_IDEAS_DRAFT.md")
    _git(repo, "commit", "-q", "-m", "fixture: FIDRAFT")

    plan_path = repo / "docs" / "plans" / "snowboard-ergonomics-skip.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/snowboard-ergonomics-skip.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1003,
        slug="snowboard-ergonomics-skip",
        seal_description="FCS-4",
    )
    _make_amendment_commit(repo, "alpha", payload="fcs4")

    capsys.readouterr()
    rc = cli_main(
        [
            "seal",
            "--plan-doc",
            str(plan_path),
            "--skip-fidraft-cleanup",
            str(manifest_path),
        ]
    )
    assert rc == 0

    out = capsys.readouterr().out
    assert "FIDRAFT cleanup surface" not in out, (
        "the cleanup surface fired despite --skip-fidraft-cleanup"
    )


def test_AC_FBMT1_FCS_4_default_keeps_surface_firing(sealed_repo, capsys):
    """Without the flag, the surface fires (regression check —
    confirms the flag is the differentiator)."""
    repo = sealed_repo
    fidraft = repo / "docs" / "FUTURE_IDEAS_DRAFT.md"
    fidraft.parent.mkdir(parents=True, exist_ok=True)
    fidraft.write_text(
        "- A FIDRAFT entry that won't match anything strong.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/FUTURE_IDEAS_DRAFT.md")
    _git(repo, "commit", "-q", "-m", "fixture: FIDRAFT")

    plan_path = repo / "docs" / "plans" / "fcs4-default.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/fcs4-default.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1004,
        slug="fcs4-default",
        seal_description="FCS-4-default",
    )
    _make_amendment_commit(repo, "alpha", payload="fcs4d")

    capsys.readouterr()
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    out = capsys.readouterr().out
    assert "FIDRAFT cleanup surface" in out
