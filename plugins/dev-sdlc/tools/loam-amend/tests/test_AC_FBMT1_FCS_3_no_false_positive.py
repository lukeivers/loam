"""AC.FBMT1.FCS.3 — zero false-positive when no FIDRAFT match.

Zero false-positive surfacing when the seal commit's plan-doc has
no FIDRAFT match (slug-overlap below threshold for every entry).
The hook still fires (so the operator knows it was checked) but
the surface text indicates no matches.

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


def test_AC_FBMT1_FCS_3_invented_slug_yields_no_match(sealed_repo, capsys):
    """A plan-doc slug crafted to share NO tokens with any FIDRAFT
    entry yields the no-match surface (not a false positive)."""
    repo = sealed_repo
    # FIDRAFT carries entries about retrieval / supersession /
    # ergonomics. Plan-doc slug uses unrelated single-purpose
    # tokens.
    fidraft = repo / "docs" / "FUTURE_IDEAS_DRAFT.md"
    fidraft.parent.mkdir(parents=True, exist_ok=True)
    fidraft.write_text(
        "# FIDRAFT\n\n"
        "- **Retrieval ranker work.** about supersession and "
        "encoding-context.\n"
        "- **Ergonomics ideas.** about workspace bootstrap and "
        "user-facing surfaces.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/FUTURE_IDEAS_DRAFT.md")
    _git(repo, "commit", "-q", "-m", "fixture: FIDRAFT")

    # Invented slug with no overlap to the FIDRAFT vocabulary.
    plan_path = (
        repo / "docs" / "plans" / "zzz-jabberwocky-vorpal-mimsy.md"
    )
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/zzz-jabberwocky-vorpal-mimsy.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1002,
        slug="zzz-jabberwocky-vorpal-mimsy",
        seal_description="FCS-3",
    )
    _make_amendment_commit(repo, "alpha", payload="fcs3")

    capsys.readouterr()
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    out = capsys.readouterr().out
    # The no-match surface fires; no false positive.
    assert "no matching entries above threshold" in out
    assert "zzz-jabberwocky-vorpal-mimsy" in out
    # Confirm no FIDRAFT entry token leaked into the surface text
    # (the surface should NOT name Retrieval/Ergonomics entries).
    surface_section = out.split("FIDRAFT cleanup surface", 1)[1]
    assert "Retrieval ranker" not in surface_section
    assert "Ergonomics ideas" not in surface_section
