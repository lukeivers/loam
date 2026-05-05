"""AC.WATCH.9 — Component-level test surface.

Sanity checks: per-AC test files exist + integration tests exist.
The actual coverage for each AC lives in `test_AC_WATCH_<n>_*.py`;
this file verifies the file inventory.
"""

from __future__ import annotations

from pathlib import Path


_TESTS_DIR = Path(__file__).parent


_REQUIRED_PER_AC_TESTS = [
    "test_AC_WATCH_1_incremental_cli.py",
    "test_AC_WATCH_2_diff_classifier.py",
    "test_AC_WATCH_3_proposal_generation.py",
    "test_AC_WATCH_4_pm_ratification.py",
    "test_AC_WATCH_5_domain_batching.py",
    "test_AC_WATCH_6_scheduling_primitive.py",
    "test_AC_WATCH_7_production_stake.py",
    "test_AC_WATCH_8_audit_log.py",
]

_REQUIRED_INTEGRATION_TESTS = [
    "test_incremental_smoke.py",
    "test_incremental_idempotent.py",
    "test_incremental_cross_session.py",
    "test_diff_classifier_accuracy.py",
]


def test_per_ac_tests_exist() -> None:
    for name in _REQUIRED_PER_AC_TESTS:
        assert (_TESTS_DIR / name).exists(), f"missing: {name}"


def test_integration_tests_exist() -> None:
    for name in _REQUIRED_INTEGRATION_TESTS:
        assert (_TESTS_DIR / name).exists(), f"missing: {name}"


def test_helpers_module_exists() -> None:
    """`_incremental_helpers.py` is the shared fixture surface."""
    assert (_TESTS_DIR / "_incremental_helpers.py").exists()
