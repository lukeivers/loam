"""AC.SDG.1 — the guard-floor registry resolves to every shared-doc guard.

Plan: ``docs/plans/shared-doc-guard-floor-coverage.md`` §3 / §4.

Every constant-anchored content-guard on a file-level universal-admitted
doc (the 8 tests across 6 docs enumerated Tier-0 in the plan §3) is
covered by the live ``docs/plans/guard-floor.yaml`` floor, and none of the
class-12 registrations is stale (each resolves to >=1 tracked test).
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.guard_floor import discover_guard_floor
from loam_amend.shared_doc_coverage import _is_floored

REPO_ROOT = Path(__file__).resolve().parents[5]

# The Tier-0 enumeration (plan §3). If a shared-doc guard is added or moved,
# the coverage meta-check (AC.SDC.*) — not this fixed list — is the anti-rot
# guard; this list pins the specific set the registration was authored for.
SHARED_DOC_GUARDS = [
    "plugins/dev-sdlc/tests/test_AC_KDOC_1_methodology_rewrite.py",
    "plugins/dev-sdlc/tests/test_AC_KDOC_3_verified_rename.py",
    "plugins/dev-sdlc/tests/test_AC_KDOC_5_adapter_tables_relocated.py",
    "plugins/dev-sdlc/tests/test_AC_MSLB_1_line_budget_admits_cap_bias_checklist.py",
    "framework/primary-persona/tests/test_AC_RVL_8_cap_bias_checklist_line.py",
    "plugins/dev-sdlc/tests/test_AC_CH0_2_value_prop_po_labels.py",
    "plugins/dev-sdlc/tests/test_AC_CH0_1_charter_genesis.py",
    "framework/tools/capability-refresh/tests/test_AC_CLP_CUR_1_2_reference_surface.py",
    "framework/hands-off-lifecycle/tests/test_AC_OGP_3_claudedev_references_lean_grounding.py",
    "framework/primary-persona/tests/test_AC_NTU_7_implementation_tier_picker.py",
]


def test_every_shared_doc_guard_is_floored() -> None:
    floor = discover_guard_floor(REPO_ROOT)
    uncovered = [g for g in SHARED_DOC_GUARDS if not _is_floored(g, floor)]
    assert not uncovered, f"shared-doc guards not covered by the floor: {uncovered}"


def test_no_stale_registry_pattern() -> None:
    floor = discover_guard_floor(REPO_ROOT)
    assert floor.stale_patterns == [], (
        "guard-floor.yaml has stale (zero-match) patterns: "
        f"{floor.stale_patterns}"
    )
