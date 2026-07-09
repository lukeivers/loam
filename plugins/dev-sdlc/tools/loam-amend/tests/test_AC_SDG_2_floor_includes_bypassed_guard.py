"""AC.SDG.2 (outcome-altitude) — the seal sweep now runs the bypassed guard.

Plan: ``docs/plans/shared-doc-guard-floor-coverage.md`` §4.

The production floor-discovery entry point, invoked against the real repo
with no pre-set state, returns a floor whose ``sweep_targets`` include BOTH
the exact guard the v1.11.0 recall seal bypassed
(``test_AC_KDOC_1_methodology_rewrite.py`` — odd-methodology.md's line-count
guard) AND the cross-component ``test_AC_RVL_8_cap_bias_checklist_line.py``
(the same shared doc, guarded from a DIFFERENT component). A guard-floor
sweep — which runs at every seal — now executes them regardless of which
component seals.
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.guard_floor import discover_guard_floor

REPO_ROOT = Path(__file__).resolve().parents[5]

BYPASSED_GUARD = "plugins/dev-sdlc/tests/test_AC_KDOC_1_methodology_rewrite.py"
CROSS_COMPONENT_GUARD = (
    "framework/primary-persona/tests/test_AC_RVL_8_cap_bias_checklist_line.py"
)


def test_floor_sweep_includes_the_bypassed_and_cross_component_guards() -> None:
    floor = discover_guard_floor(REPO_ROOT)
    sweep = {str(t) for t in floor.sweep_targets}
    assert BYPASSED_GUARD in sweep, (
        "the odd-methodology.md line-count guard the v1.11.0 recall seal "
        "bypassed is still not in the guard-floor sweep"
    )
    assert CROSS_COMPONENT_GUARD in sweep, (
        "the cross-component RVL_8 guard on the shared methodology doc is "
        "not in the guard-floor sweep"
    )
