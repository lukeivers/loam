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
    assert "no seal SHA" in r.message


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
    rs = gates.run_all(staged_repo, fixture_version)
    assert len(rs) == 6
    names = [r.name for r in rs]
    assert names == [
        "hard-smoke",
        "acs-verified",
        "state-shipped",
        "clean-tree",
        "branch-main",
        "seal-reachable",
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
