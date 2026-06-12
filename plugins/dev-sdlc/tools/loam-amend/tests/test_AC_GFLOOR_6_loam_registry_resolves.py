"""AC.GFLOOR.6 — the loam repo's registry covers the inventoried
guard classes and never rots silently between seals.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4: the loam repo's
``docs/plans/guard-floor.yaml`` covers the 11 guard classes of the
2026-06-12 guard-breach inventory (classes 1-2 — fence +
cross-cutting tests — are convention-discovered per AC.GFLOOR.1;
classes 3-11 are registry patterns); every registry pattern resolves
to ≥1 tracked file at HEAD. Seal-time enforcement is AC.GFLOOR.3;
this LIVE test catches staleness between seals (the floor guards its
own registry).
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.guard_floor import REGISTRY_RELPATH, discover_guard_floor
from loam_amend.paths import find_repo_root


def _loam_repo_root() -> Path:
    return find_repo_root(Path(__file__).parent)


def test_AC_GFLOOR_6_every_registry_pattern_resolves() -> None:
    repo_root = _loam_repo_root()
    assert (repo_root / REGISTRY_RELPATH).exists(), (
        "loam's guard-floor registry is missing — the floor would "
        "silently lose its sweep-class members"
    )
    floor = discover_guard_floor(repo_root)
    assert floor.registry_present
    assert floor.stale_patterns == [], (
        "stale guard-floor registry pattern(s) — a guard moved or "
        f"was renamed; update {REGISTRY_RELPATH}: "
        f"{floor.stale_patterns}"
    )


def test_AC_GFLOOR_6_floor_covers_the_inventoried_classes() -> None:
    """Classes 3-11 of the inventory each resolve to a known live
    member; classes 1-2 (fence/cross-cutting) are convention-
    discovered and non-empty."""
    repo_root = _loam_repo_root()
    floor = discover_guard_floor(repo_root)

    sweep = {str(p) for p in floor.sweep_targets}
    expected_members = {
        # class 3 — banned-stem sweep (PB retirement)
        "plugins/dev-sdlc/tests/test_AC_PBRET_5_programbench_retirement_sweep.py",
        # class 4 — capability-schema-marker sweep
        "framework/primary-persona/tests/test_AC_alpha_8_no_capability_content_outside_admitted_paths.py",
        # class 5 — manifest conformance sweep
        "plugins/dev-sdlc/tools/loam-amend/tests/test_AC_DPS1_dev_pattern_simplifications_1.py",
        # class 6 — decision-claim guard (live ledger replay)
        "framework/hands-off-lifecycle/tests/test_AC_DCG_OA_live_ledger_gate_replay.py",
        # class 7 — claim-language guard (live repo replay)
        "framework/hands-off-lifecycle/tests/test_AC_CLG_OA_live_repo_replay.py",
        # class 8 — version lockstep sweep
        "plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py",
        # class 9 — dev-mode manifest roots
        "plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py",
        # class 10 — protection-matrix catalogue suite (dir target)
        "framework/protection-matrix/tests",
        # class 11 — fence-integrity guards
        "framework/tools/loam-spawn-isolation/tests/test_AC_PROMO_6_fence_integrity.py",
        "framework/tools/handsoff-loop/tests/test_AC_TPI_5_marker_guard_regression.py",
    }
    missing = expected_members - sweep
    assert not missing, (
        "guard-floor registry no longer covers these inventoried "
        f"class members: {sorted(missing)}"
    )

    # Classes 1-2: convention-discovered fence + cross-cutting tests.
    fence = {str(p) for p in floor.fence_targets}
    assert (
        "framework/hands-off-lifecycle/tests/test_cross_cutting.py" in fence
    )
    # The historically-missed tree shapes are now floor members.
    assert (
        "framework/tools/loam/tests/test_no_sealed_amendments.py" in fence
    )
    assert "plugins/dev-sdlc/tests/test_no_sealed_amendments.py" in fence
    # Archived sealed history is excluded.
    assert not any(t.startswith("docs/archive/") for t in fence)
