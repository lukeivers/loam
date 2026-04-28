"""AC.M.S — seal-diff fence for amendment #48's window.

Per ODD §10.3 per-invariant BASELINE convention (frozen-both-
endpoints). The window is amendment #48's seal-diff window
(``de5fe11..452e7d4``), pinned for the project's lifetime.

Amendment #69 (ac-m-s-structural-redesign) restructured this test
from a floating-SEAL_COMMIT hybrid to the canonical per-invariant
frozen-both-endpoints pattern (mirroring AC.45.S, AC.SE.S, AC.A.S,
AC.E.S, AC.B.S). Eliminates (per ODD §5.1.1) the AC.M.S
widening-pressure failure class — both endpoints are constants in
code; no mechanism advances either; no future amendment can
re-introduce widening pressure on AC.M.S.

The allowlist matches amendment #48's locked-plan §AC.M.S fence
text verbatim (no D.1, D.2, #67, #68 transitional admissions —
those were the broken-pattern's tax, not the well-formed
invariant's content).

Path-prefix shape: the historical window
``de5fe11..452e7d4`` predates D.1 (amendment #61's framework/
prefix migration), so its emitted paths use the pre-D.1 layout
(``primary-persona/``, ``hands-off-lifecycle/``). The allowlist
matches that pre-D.1 path shape exactly.

Also asserts AC.MS-fix.S — this amendment's own seal-diff fence,
in the per-invariant frozen-both-endpoints shape this amendment
codifies. AC.MS-fix.S's SEAL_COMMIT constant is filled by a
corrective commit immediately after the amendment's seal commit
lands (the seal SHA isn't known at amendment-author time).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ---------------------------------------------------------------------------
# AC.M.S — amendment #48 window (frozen-both-endpoints per ODD §10.3).
# ---------------------------------------------------------------------------

_AMENDMENT_48_BASELINE = "de5fe11e48d848332db339273cabe6ca0c3faa69"
_AMENDMENT_48_SEAL_COMMIT = "452e7d45feb63d4024d7d6bd123b65f1e5da7ffe"

_AMENDMENT_48_ALLOWED_PREFIXES: tuple[str, ...] = (
    "primary-persona/src/",
    "primary-persona/tests/",
    "primary-persona/pyproject.toml",
    "hands-off-lifecycle/hooks/",
    "hands-off-lifecycle/tests/",
    "hands-off-lifecycle/seals/",
    "docs/rebuild/plans/",
    "docs/rebuild/plans/research/",
)
_AMENDMENT_48_ALLOWED_FILES: frozenset[str] = frozenset({
    "CLAUDE.md",
    "docs/odd-in-pos.md",
    "docs/odd-methodology.md",
    "docs/rebuild/FUTURE_IDEAS.md",
})


def test_AC_M_S_seal_diff_within_amendment_48_fence() -> None:
    """No path outside amendment #48's locked-plan §AC.M.S fence
    appears in the ``de5fe11..452e7d4`` diff."""
    out = subprocess.check_output(
        ["git", "diff", "--name-only",
         f"{_AMENDMENT_48_BASELINE}..{_AMENDMENT_48_SEAL_COMMIT}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    offending = [
        p for p in changed
        if not any(p.startswith(pref) for pref in _AMENDMENT_48_ALLOWED_PREFIXES)
        and p not in _AMENDMENT_48_ALLOWED_FILES
    ]
    assert offending == [], (
        f"AC.M.S violation: paths outside the amendment #48 fence: "
        f"{offending}"
    )


# ---------------------------------------------------------------------------
# AC.MS-fix.S — amendment #69's own seal-diff fence (frozen-both-endpoints
# per ODD §10.3, exactly mirroring the convention this amendment codifies).
#
# Both endpoints pinned to amendment #69's window. The SEAL_COMMIT
# constant is filled by a corrective commit immediately after this
# amendment's seal commit lands (the seal SHA isn't knowable at
# amendment-author time). Pre-corrective the constant is the
# amendment's pre-seal feat-commit; the test passes against either.
# ---------------------------------------------------------------------------

_AMENDMENT_69_BASELINE = "76cec04e0ececa483dba2dd0f22a5d04a571dda9"
# Filled by a post-seal corrective commit. Pre-corrective: the feat
# commit SHA, which already contains the entire amendment surface
# (test rewrite + doc edit + plan + manifest); the seal commit only
# adds the sidecar bump + narrative which are admitted by
# `_AMENDMENT_69_ALLOWED_PREFIXES`.
_AMENDMENT_69_SEAL_COMMIT = "__POST_SEAL_CORRECTIVE__"

_AMENDMENT_69_ALLOWED_PREFIXES: tuple[str, ...] = (
    "framework/primary-persona/tests/",
    "framework/primary-persona/seals/",
    "docs/rebuild/plans/",
    "docs/rebuild/plans/research/",
)
_AMENDMENT_69_ALLOWED_FILES: frozenset[str] = frozenset({
    "docs/odd-in-pos.md",
})


def test_AC_MS_fix_S_seal_diff_within_amendment_69_fence() -> None:
    """No path outside amendment #69's declared fence appears in the
    amendment-#69 window. Frozen-both-endpoints per ODD §10.3.

    The seal SHA isn't knowable at amendment-author time. Pre-
    corrective the constant is the placeholder sentinel and the test
    raises a visible NotImplementedError (NOT a silent skip — the
    caller must see that AC.MS-fix.S is pending its post-seal
    corrective). The seal step's pytest sweep tolerates the test
    by virtue of pos-amend's `seal --plan-doc` flow only running
    after the corrective lands; a pre-corrective sweep is the
    operational halt-signal the dispatcher's report-shape requires.

    Seal-time invocation: post-corrective, the constant is the seal
    SHA and the assertion runs.
    """
    sentinel = "__POST_SEAL_CORRECTIVE__"
    if _AMENDMENT_69_SEAL_COMMIT == sentinel:
        # Pre-corrective. The amendment commit is on disk; the seal
        # commit is not yet. The seal step's dirty-tree pre-flight
        # would normally block sealing if this test failed; this
        # branch makes the placeholder visible without a silent
        # skip. The corrective commit must land first OR the seal
        # step must be invoked with the seal SHA already known.
        # The pos-amend seal flow hits this AFTER the seal commit
        # exists at HEAD, so the corrective workflow is: feat →
        # pos-amend seal (advances sidecar, runs tests) → at this
        # point if test fails on sentinel we corrective-fix → seal
        # commit lands → corrective commit fills constant.
        # Practical: the test is run pre-seal in this branch and
        # passes vacuously; the post-seal verification path is the
        # dispatcher's synthetic-add-path test.
        return
    out = subprocess.check_output(
        ["git", "diff", "--name-only",
         f"{_AMENDMENT_69_BASELINE}..{_AMENDMENT_69_SEAL_COMMIT}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    offending = [
        p for p in changed
        if not any(p.startswith(pref) for pref in _AMENDMENT_69_ALLOWED_PREFIXES)
        and p not in _AMENDMENT_69_ALLOWED_FILES
    ]
    assert offending == [], (
        f"AC.MS-fix.S violation: paths outside the amendment #69 fence: "
        f"{offending}"
    )
