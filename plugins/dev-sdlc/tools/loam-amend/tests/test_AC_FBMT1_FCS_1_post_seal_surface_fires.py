"""AC.FBMT1.FCS.1 — post-seal FIDRAFT cleanup surface fires.

After ``loam amend seal`` completes successfully, a process reads
the just-sealed plan-doc, scans ``docs/FUTURE_IDEAS_DRAFT.md`` for
entries whose slug-overlap with the plan-doc's slug exceeds the
confidence threshold, and emits a structured surfacing payload (NOT
a file edit) asking the operator "did you mark this actioned?".

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.FCS family.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam_amend.cli import main as cli_main
from loam_amend.fidraft_cleanup import scan_fidraft

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


def test_AC_FBMT1_FCS_1_surface_fires_with_matching_fidraft_entry(
    sealed_repo, capsys
):
    """A seal whose plan-doc slug shares tokens with a FIDRAFT
    entry emits the cleanup surface naming that entry."""
    repo = sealed_repo
    # Author a FIDRAFT carrying an entry that names a unique
    # keyword shared with the plan-doc slug.
    fidraft = repo / "docs" / "FUTURE_IDEAS_DRAFT.md"
    fidraft.parent.mkdir(parents=True, exist_ok=True)
    fidraft.write_text(
        "# FUTURE_IDEAS_DRAFT.md — capture\n\n"
        "## Active drafts\n\n"
        "- **Unrelated entry.** Talks about gauntlet runners and "
        "obscure ergonomic flags. Nothing to do with the plan-doc.\n"
        "- **The quokka-platypus retrieval ranker draft.** Builds "
        "the supersession-marker quokka-platypus penalty machinery "
        "the seal-time hook should remind us to mark actioned.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/FUTURE_IDEAS_DRAFT.md")
    _git(repo, "commit", "-q", "-m", "fixture: FIDRAFT seed")

    # Plan-doc slug matches the FIDRAFT entry tokens.
    plan_path = repo / "docs" / "plans" / "quokka-platypus-supersession.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/quokka-platypus-supersession.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc for FCS.1")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1000,
        slug="quokka-platypus-supersession",
        seal_description="FCS-1",
    )
    _make_amendment_commit(repo, "alpha", payload="fcs1")

    capsys.readouterr()  # clear pre-seal noise
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # AC.FBMT1.FCS.1: surface text names the plan-doc slug and the
    # matching FIDRAFT entry.
    assert "FIDRAFT cleanup surface" in out
    assert "quokka-platypus-supersession" in out
    assert "quokka-platypus" in out  # at least one token from FIDRAFT entry shows up


def test_AC_FBMT1_FCS_1_scan_helper_returns_structured_payload(tmp_path):
    """The ``scan_fidraft`` helper returns a structured payload
    consumable by callers other than the seal CLI (smoke test +
    future programmatic consumers)."""
    fidraft = tmp_path / "FIDRAFT.md"
    fidraft.write_text(
        "- **Quokka platypus retrieval ranker.** Lengthy entry about "
        "the supersession marker.\n",
        encoding="utf-8",
    )
    surface = scan_fidraft(
        plan_slug="quokka-platypus-supersession-marker",
        fidraft_path=fidraft,
    )
    assert surface.plan_slug == "quokka-platypus-supersession-marker"
    assert len(surface.matches) == 1
    assert "Quokka platypus" in surface.matches[0].entry_text
    assert surface.matches[0].score >= 0.30  # above threshold
