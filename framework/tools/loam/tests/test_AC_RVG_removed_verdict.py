"""AC.RVG.{1,2,3} — `check_acs_verified` accepts REMOVED as a
non-failure verdict.

Per `feedback_locked_design_not_license_for_bad_outcomes` (and ODD §4
re-extension), an AC can be legitimately struck mid-build when
empirical reality contradicts the plan. The §status verdict matrix
records `REMOVED` alongside a reference to the build-time decision
that struck it. The v0.6.0 `check_acs_verified` parser recognised
only `GREEN` as a pass token; v0.8.3 adds REMOVED recognition.

This module covers three new ACs:

- **AC.RVG.1** — REMOVED counts as a non-failure verdict alongside
  GREEN. (Two surface-form tests cover the canonical table-row form
  and the prose em-dash form.)
- **AC.RVG.2** — REMOVED-marker recognition is robust across the
  observed surface forms.
- **AC.RVG.3** — Missing-verdict (no GREEN AND no REMOVED) still
  returns RED — the fix doesn't open the gate to silently-skipped ACs.

AC.RVG.4 is the outcome-altitude dogfood probe verified via real CLI
invocation; that lives in `docs/experiments/v0-8-3-hard-smoke.md`,
not in this test module.

Backward-compat (all-GREEN plan-docs continue to pass) is verified by
the existing `test_AC_V060_2_pre_publish_gates.py` +
`test_AC_SDPD_plan_doc_flag.py` suites continuing to pass unmodified.
"""

from __future__ import annotations

from pathlib import Path

from loam_cli.release import gates


# --------------------------------------------------------------------
# AC.RVG.1 + AC.RVG.2 — REMOVED recognised in canonical surface forms
# --------------------------------------------------------------------


def test_acs_verified_green_when_status_marks_ac_removed_table_form(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """The canonical REMOVED form (live in the paper-publish plan-doc):
    a markdown table row with ``REMOVED`` in the Verdict cell and a
    build-time-decision reference in the Evidence cell. The gate
    counts the AC as verified.
    """
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Append a third §4-declared AC + a §status table-row matrix that
    # mirrors the live paper-publish plan-doc shape. The fixture's
    # default §status is a bullet-list form for AC.V060.{1,2}; we
    # add a table-row form for AC.V060.3 alongside.
    body = body.replace(
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n",
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n"
        "### AC.V060.3 — Stale capability\n\nWill be REMOVED mid-build.\n\n",
    )
    body += (
        "\n### AC verdict matrix\n\n"
        "| AC | Verdict | Evidence |\n"
        "|---|---|---|\n"
        "| AC.V060.3 | REMOVED | Build-time D-FOO.5.2 Path C — "
        "stale capability dropped; ship without. |\n"
    )
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is True, (
        f"expected GREEN with REMOVED recognition; got: {r.message}"
    )
    # The GREEN success message reports the total §4-declared AC
    # count (REMOVED + GREEN combined).
    assert "3 AC" in r.message
    # The new success message names BOTH recognised verdicts.
    assert "GREEN" in r.message
    assert "REMOVED" in r.message


def test_acs_verified_green_when_status_marks_ac_removed_em_dash_form(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """The prose em-dash form: ``AC.X.1 — REMOVED at build per
    D-FOO.5.2``. Plan-docs that don't use a verdict-matrix table may
    instead carry an inline prose verdict for each AC. The gate
    counts the AC as verified.
    """
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Add AC.V060.3 to §4 + a prose-form REMOVED verdict in §status.
    body = body.replace(
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n",
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n"
        "### AC.V060.3 — Stale capability\n\nWill be REMOVED mid-build.\n\n",
    )
    body = body.replace(
        "- AC.V060.2: GREEN\n",
        "- AC.V060.2: GREEN\n"
        "- AC.V060.3 — REMOVED at build per D-FOO.5.2 "
        "(stale capability dropped; ship without)\n",
    )
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is True, (
        f"expected GREEN with REMOVED prose-form recognition; "
        f"got: {r.message}"
    )
    assert "3 AC" in r.message


# --------------------------------------------------------------------
# AC.RVG.3 — missing-verdict still RED (regression)
# --------------------------------------------------------------------


def test_acs_verified_red_when_status_omits_ac_entirely(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """An AC declared in §4 with NEITHER GREEN nor REMOVED within
    240 chars in §status is still flagged as missing. The v0.8.3
    fix is narrow: REMOVED is the only added verdict; other tokens
    (or no token at all) still RED.
    """
    plan_path = (
        staged_repo
        / "docs"
        / "plans"
        / f"{fixture_slug}-release-process.md"
    )
    body = plan_path.read_text(encoding="utf-8")
    # Add AC.V060.3 to §4 but leave §status untouched — no verdict
    # line for the new AC, so it has neither GREEN nor REMOVED near it.
    body = body.replace(
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n",
        "### AC.V060.2 — Gates\n\nDoes another thing.\n\n"
        "### AC.V060.3 — Stale capability\n\nNo verdict in status.\n\n",
    )
    plan_path.write_text(body, encoding="utf-8")
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is False
    # The missing-list names the AC with no verdict.
    assert "AC.V060.3" in r.message
    # The corrective hint mentions BOTH recognised verdicts so the
    # operator knows REMOVED is an option for legitimate strikes.
    assert "GREEN" in r.message
    assert "REMOVED" in r.message


# --------------------------------------------------------------------
# Regression — all-GREEN plan-docs continue to pass unmodified
# --------------------------------------------------------------------


def test_acs_verified_green_when_all_acs_green_regression(
    staged_repo: Path, fixture_version: str
) -> None:
    """Regression: a plan-doc with all-GREEN verdicts (the v0.6.0
    default shape — no REMOVED ACs) continues to pass after the
    v0.8.3 fix. The verdict-loop tries GREEN first; the REMOVED
    fall-through is only reached when GREEN doesn't match.
    """
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is True
    # New success message names both verdicts even when none are
    # REMOVED — the message describes the recognised set, not the
    # actual mix.
    assert "GREEN" in r.message
    assert "REMOVED" in r.message
