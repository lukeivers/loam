"""AC.SDC.2 (outcome-altitude) — a surface doc with an unfloored guard REDs
with a named, corrective violation.

Plan: ``docs/plans/shared-doc-guard-floor-coverage.md`` §4.

Given a floor that covers everything EXCEPT one shared-doc guard (the real
odd-methodology.md line-count guard), the meta-check returns a violation
naming the shared doc, the uncovered guard test, and a corrective registry
pattern that — when resolved — covers that guard. This is the registry-rot
catch: a new shared-doc guard that nobody floored is caught, not silently
skipped to the once-per-minor HARD smoke.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from loam_amend.guard_floor import GuardFloor, discover_guard_floor
from loam_amend.shared_doc_coverage import find_uncovered_shared_doc_guards

REPO_ROOT = Path(__file__).resolve().parents[5]

MISSING_GUARD = "plugins/dev-sdlc/tests/test_AC_KDOC_1_methodology_rewrite.py"
ODD = "plugins/dev-sdlc/docs/odd-methodology.md"


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def test_unfloored_shared_doc_guard_is_named_with_a_corrective_hint() -> None:
    # Real floor MINUS the KDOC_1 target — simulates a shared-doc guard that
    # was never registered (or whose registration was dropped).
    full = discover_guard_floor(REPO_ROOT)
    degraded = GuardFloor(
        fence_targets=list(full.fence_targets),
        sweep_targets=[t for t in full.sweep_targets if str(t) != MISSING_GUARD],
        registry_present=True,
    )

    violations = find_uncovered_shared_doc_guards(REPO_ROOT, degraded)
    match = [v for v in violations if v.guard_test == MISSING_GUARD]

    assert match, "removing a shared-doc guard from the floor did not RED the meta-check"
    v = match[0]
    # Names the shared doc.
    assert v.doc == ODD
    # The corrective hint is actually corrective: the suggested pattern,
    # resolved against tracked files, covers the missing guard.
    tracked = _tracked()
    resolved = [t for t in tracked if fnmatch.fnmatchcase(t, v.suggested_pattern)]
    assert MISSING_GUARD in resolved, (
        f"suggested pattern {v.suggested_pattern!r} does not resolve to the "
        f"missing guard {MISSING_GUARD}"
    )
