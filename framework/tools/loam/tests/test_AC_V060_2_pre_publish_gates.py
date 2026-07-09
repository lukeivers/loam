"""AC.V060.2 — Per-gate pre-publish verification.

Six gates, six test pairs (one passing, one failing per gate). Per
the AC's "each gate failure surfaces a specific corrective hint
(not a generic error)" requirement, each RED test asserts the
hint contains gate-specific guidance (not just a boolean).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import gates


# --------------------------------------------------------------------
# Gate 1 — HARD smoke GREEN
# --------------------------------------------------------------------


def test_hard_smoke_green_when_writeup_exists_and_contains_token(
    staged_repo: Path, fixture_version: str
) -> None:
    r = gates.check_hard_smoke(staged_repo, fixture_version)
    assert r.ok is True
    assert "GREEN" in r.message


def test_hard_smoke_red_when_writeup_missing(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    (
        staged_repo
        / "docs"
        / "experiments"
        / f"{fixture_slug}-hard-smoke.md"
    ).unlink()
    r = gates.check_hard_smoke(staged_repo, fixture_version)
    assert r.ok is False
    # Specific corrective hint — names the missing path + the
    # memory rule + the corrective action.
    assert "missing HARD smoke" in r.message
    assert "feedback_hard_smoke_per_minor_before_publish" in r.message


def test_hard_smoke_red_when_writeup_lacks_green_token(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    smoke_path = (
        staged_repo
        / "docs"
        / "experiments"
        / f"{fixture_slug}-hard-smoke.md"
    )
    smoke_path.write_text(
        "# smoke writeup\n\nVerdict: YELLOW. Smoke flapping.\n",
        encoding="utf-8",
    )
    r = gates.check_hard_smoke(staged_repo, fixture_version)
    assert r.ok is False
    assert "GREEN verdict token" in r.message


# --------------------------------------------------------------------
# Gate 2 — ACs verified per plan-doc
# --------------------------------------------------------------------


def test_acs_verified_green_when_status_marks_each_ac_green(
    staged_repo: Path, fixture_version: str
) -> None:
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is True
    assert "GREEN" in r.message


def test_acs_verified_red_when_plan_doc_missing(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    ).unlink()
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is False
    assert "no plan-doc found" in r.message
    assert "feedback_plan_before_code" in r.message


def test_acs_verified_red_when_status_omits_an_ac(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Drop the AC.V060.2 GREEN line — verdict matrix is incomplete.
    body = body.replace("- AC.V060.2: GREEN\n", "")
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is False
    assert "AC.V060.2" in r.message


# AC.READYP.1 / AC.READYP.3 — Section-scoped scan: cross-reference AC IDs
# in §6 (out-of-scope), §8 (dependencies), and §13 (§status itself) must
# NOT be treated as in-scope ACs requiring §status verdicts. Closes the
# v0.7.1 publish-time defect captured at FUTURE_IDEAS_DRAFT.md line 232.


def test_acs_verified_ignores_cross_references_in_other_sections(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """Cross-reference AC IDs in §6 / §8 / §13 must NOT be flagged
    as missing-from-§status. The fixed parser scopes its AC-ID
    scan to §4 only.
    """
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Append §6 + §8 sections containing cross-reference AC IDs to
    # other versions' ACs. These are NOT in-scope for v0.6.0 — they
    # explain dependencies + out-of-scope follow-ons. Without the
    # AC.READYP.1 fix, the parser would flag AC.OTHER.1 + AC.OTHER.2
    # + AC.OTHER.3 as missing-from-§status.
    body += (
        "\n## §6 Out of scope\n\n"
        "Reference to **AC.OTHER.1** as an out-of-scope follow-on.\n"
        "\n## §8 Dependencies\n\n"
        "Cross-reference to **AC.OTHER.2** as a predecessor.\n"
    )
    plan_path.write_text(body, encoding="utf-8")
    # The §status section already mentions AC.OTHER.3 via a cross-
    # reference (the verdict matrix can name predecessor ACs without
    # owning them). Re-author §status to include such a reference.
    body = plan_path.read_text(encoding="utf-8")
    body = body.replace(
        "- AC.V060.2: GREEN\n",
        "- AC.V060.2: GREEN\n"
        "- (cross-ref AC.OTHER.3 — predecessor, no GREEN required)\n",
    )
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is True, (
        f"expected GREEN; cross-references in §6/§8/§13 must not "
        f"trigger missing-from-§status. Got: {r.message}"
    )
    # The gate's GREEN message reports only the §4-declared ACs.
    assert "2 AC" in r.message  # the two AC.V060.* in §4


def test_acs_verified_red_names_only_section_4_acs_when_status_incomplete(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """Negative case: §4 declares two ACs; §status omits one of them
    AND §6/§8 contain cross-reference AC IDs to other-version ACs.
    Gate returns RED naming ONLY the missing §4 AC — the cross-
    references are silent (not RED-flagged, not absent-flagged).
    """
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Append §6 + §8 with cross-reference AC IDs.
    body += (
        "\n## §6 Out of scope\n\n"
        "Reference to **AC.OTHER.1**.\n"
        "\n## §8 Dependencies\n\n"
        "Reference to **AC.OTHER.2**.\n"
    )
    # Drop the §4-declared AC.V060.2 verdict from §status.
    body = body.replace("- AC.V060.2: GREEN\n", "")
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is False
    # The §4-declared AC.V060.2 is RED-flagged.
    assert "AC.V060.2" in r.message
    # The cross-reference AC.OTHER.* IDs are NOT in the missing-list
    # (they were never in-scope; they're not declared in §4).
    assert "AC.OTHER.1" not in r.message
    assert "AC.OTHER.2" not in r.message


def test_acs_verified_red_when_section_4_heading_absent(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """Missing §4 heading returns RED with corrective hint naming the
    §4 — Acceptance criteria convention. No fall-back to whole-doc
    scan (per D-READYP.1.b — that would silently re-introduce the
    pre-fix defect).
    """
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Strip the §4 heading. Replace with a different heading so the
    # rest of the doc still parses; the AC declarations under it
    # remain but are no longer in a §4 section.
    body = body.replace("## §4 Acceptance criteria", "## Acceptance criteria")
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is False
    assert "§4" in r.message
    assert "Acceptance criteria" in r.message


# --------------------------------------------------------------------
# Gate 3 — STATE.md SHIPPED
# --------------------------------------------------------------------


def test_state_shipped_green_when_state_marks_version(
    staged_repo: Path, fixture_version: str
) -> None:
    r = gates.check_state_shipped(staged_repo, fixture_version)
    assert r.ok is True


def test_state_shipped_red_when_state_omits_version(
    staged_repo: Path, fixture_version: str
) -> None:
    state_path = staged_repo / "docs" / "STATE.md"
    body = state_path.read_text(encoding="utf-8")
    # Drop the version's SHIPPED line.
    body = body.replace(
        f"{fixture_version} SHIPPED 2026-05-09 — release-process work.\n",
        "",
    )
    state_path.write_text(body, encoding="utf-8")
    r = gates.check_state_shipped(staged_repo, fixture_version)
    assert r.ok is False
    assert "does not mark" in r.message
    assert fixture_version in r.message


# --------------------------------------------------------------------
# Gate 4 — clean tree
# --------------------------------------------------------------------


def test_clean_tree_green_when_no_uncommitted_changes(
    staged_repo: Path, fixture_version: str
) -> None:
    r = gates.check_clean_tree(staged_repo, fixture_version)
    assert r.ok is True


def test_clean_tree_red_when_dirty(
    staged_repo: Path, fixture_version: str
) -> None:
    (staged_repo / "scratch.txt").write_text("dirty\n", encoding="utf-8")
    r = gates.check_clean_tree(staged_repo, fixture_version)
    assert r.ok is False
    assert "uncommitted changes" in r.message
    assert "scratch.txt" in r.message


# --------------------------------------------------------------------
# Gate 5 — branch == main
# --------------------------------------------------------------------


def test_branch_main_green_on_main(
    staged_repo: Path, fixture_version: str
) -> None:
    r = gates.check_branch_main(staged_repo, fixture_version)
    assert r.ok is True


def test_branch_main_red_off_main(
    staged_repo: Path, fixture_version: str
) -> None:
    subprocess.run(
        ["git", "switch", "-c", "feature/foo"],
        cwd=staged_repo,
        check=True,
        capture_output=True,
    )
    r = gates.check_branch_main(staged_repo, fixture_version)
    assert r.ok is False
    assert "feature/foo" in r.message
    assert "main" in r.message


# --------------------------------------------------------------------
# Gate 6 — seal commit reachable
# --------------------------------------------------------------------


def test_seal_reachable_green_when_seal_in_history(
    staged_repo: Path, fixture_version: str
) -> None:
    r = gates.check_seal_commit_reachable(staged_repo, fixture_version)
    assert r.ok is True
    assert "reachable" in r.message


def test_seal_reachable_red_when_roadmap_omits_seal(
    staged_repo: Path, fixture_version: str
) -> None:
    roadmap_path = staged_repo / "docs" / "release-roadmap.md"
    body = roadmap_path.read_text(encoding="utf-8")
    # Strip the "seal `<sha>`" token from the version's row only.
    new_body = []
    for line in body.splitlines(keepends=True):
        if line.startswith(f"| {fixture_version} "):
            line = line.replace(
                "; seal `" + line.split("seal `")[1].split("`")[0] + "`",
                "",
            )
        new_body.append(line)
    roadmap_path.write_text("".join(new_body), encoding="utf-8")
    # Need a clean tree for this gate test (gate 6 doesn't depend
    # on clean tree, but let's keep state tidy).
    subprocess.run(
        ["git", "add", "docs/release-roadmap.md"],
        cwd=staged_repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "drop seal"],
        cwd=staged_repo,
        check=True,
    )
    r = gates.check_seal_commit_reachable(staged_repo, fixture_version)
    assert r.ok is False
    # Post-Class-D rewire: gate 6 resolves the tag target via ancestor-
    # dominance and defers the no-seal DETAIL to the seal-dominance gate;
    # the RED behavior on a seal-less row is preserved. The seal-dominance
    # gate carries the "names no seal SHA" wording.
    assert "does not resolve to a single tag target" in r.message
    dom = gates.check_seal_dominance(staged_repo, fixture_version)
    assert dom.ok is False
    assert "no seal SHA" in dom.message


def test_seal_reachable_red_when_seal_unreachable(
    staged_repo: Path, fixture_version: str
) -> None:
    """A seal SHA that's syntactically valid but not in HEAD's
    ancestry should fail the reachability check with the
    'NOT reachable' corrective hint."""
    roadmap_path = staged_repo / "docs" / "release-roadmap.md"
    body = roadmap_path.read_text(encoding="utf-8")
    # Replace the version's seal SHA with an unreachable hex blob.
    # `0123456abcd` is 11 hex chars — gate's regex accepts 7-40, but
    # this SHA isn't an actual commit so reachability fails.
    import re
    new_body = re.sub(
        r"(\| " + re.escape(fixture_version) + r" .*?seal `)([0-9a-f]+)(`)",
        r"\g<1>0123456abcd\g<3>",
        body,
        count=1,
        flags=re.DOTALL,
    )
    roadmap_path.write_text(new_body, encoding="utf-8")
    subprocess.run(
        ["git", "add", "docs/release-roadmap.md"],
        cwd=staged_repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "swap seal sha"],
        cwd=staged_repo,
        check=True,
    )
    r = gates.check_seal_commit_reachable(staged_repo, fixture_version)
    assert r.ok is False
    assert "NOT reachable" in r.message


# --------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------


def test_run_all_returns_six_results_in_declaration_order(
    staged_repo: Path, fixture_version: str
) -> None:
    # The migration-declared gate (AC.MIG-GATE.*, P1.3) appended a seventh
    # gate; the substrate-audit gate (AC.SOL-GATE.*, N2) appended an eighth;
    # the boundary-respected gate (AC.BLOCK-ENFORCE.*, N1) appended a ninth.
    # The 2026-07-08 release-seal near-miss audit appended a tenth
    # (seal-dominance, AC.DOM.5) + an eleventh (deterministic-cut,
    # AC.CUT.1). run_all now returns eleven verdicts in declaration order.
    rs = gates.run_all(staged_repo, fixture_version)
    assert len(rs) == 11
    names = [r.name for r in rs]
    assert names == [
        "hard-smoke",
        "acs-verified",
        "state-shipped",
        "clean-tree",
        "branch-main",
        "seal-reachable",
        "migration-declared",
        "substrate-audit",
        "boundary-respected",
        "seal-dominance",
        "deterministic-cut",
    ]


def test_run_all_does_not_short_circuit_on_first_red(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """When two gates RED, both verdicts surface in the report (no
    short-circuit). Operators see the full state in one pass."""
    # Force gate 1 RED (smoke missing) AND gate 4 RED (dirty tree).
    (
        staged_repo
        / "docs"
        / "experiments"
        / f"{fixture_slug}-hard-smoke.md"
    ).unlink()
    (staged_repo / "scratch.txt").write_text("dirty\n", encoding="utf-8")
    rs = gates.run_all(staged_repo, fixture_version)
    by_name = {r.name: r for r in rs}
    assert by_name["hard-smoke"].ok is False
    assert by_name["clean-tree"].ok is False
    # Gates 2 / 3 / 5 / 6 should still pass — the run_all walked all six.
    assert by_name["acs-verified"].ok is True
    assert by_name["branch-main"].ok is True


def test_format_report_marks_green_and_red_inline(
    staged_repo: Path, fixture_version: str
) -> None:
    rs = gates.run_all(staged_repo, fixture_version)
    out = gates.format_report(rs)
    assert "[GREEN]" in out
    # Format string includes the gate name + message.
    for r in rs:
        assert r.name in out
