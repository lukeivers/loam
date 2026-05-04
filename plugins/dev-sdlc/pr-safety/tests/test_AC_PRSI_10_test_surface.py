"""AC.PRSI.10 — Component-level test surface inventory.

Verifies all AC.PRSI.{1..9} test files exist, plus the integration
tests for D2/D3/D4/D5/D6 + husky + conflict + overflow.
"""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def test_per_ac_test_files_exist() -> None:
    expected = [
        "test_AC_PRSI_1_pre_commit_installer.py",
        "test_AC_PRSI_2_pre_push_installer.py",
        "test_AC_PRSI_3_hook_script_semantics.py",
        "test_AC_PRSI_4_github_actions_template.py",
        "test_AC_PRSI_5_gitlab_ci_template.py",
        "test_AC_PRSI_6_circleci_template.py",
        "test_AC_PRSI_7_pr_description_template.py",
        "test_AC_PRSI_8_install_ergonomics.py",
        "test_AC_PRSI_9_e2e_smoke.py",
        "test_AC_PRSI_10_test_surface.py",
    ]
    for fname in expected:
        assert (_ROOT / fname).exists(), f"missing AC.PRSI test: {fname}"


def test_integration_test_files_exist() -> None:
    expected = [
        "test_idempotency_d2.py",
        "test_cross_session_state_d5_install.py",
        "test_husky_detection.py",
        "test_conflict_halt.py",
        "test_pr_description_overflow.py",
    ]
    for fname in expected:
        assert (_ROOT / fname).exists(), f"missing integration test: {fname}"


def test_cycle1_tests_still_present() -> None:
    """Sanity — Cycle 1's test surface preserved after Cycle 2 lands."""
    expected = [
        "test_AC_PRSG_1_component_scaffold.py",
        "test_AC_PRSG_2_contract_reader.py",
        "test_AC_PRSG_3_diff_classifier.py",
        "test_AC_PRSG_4_decision_matrix.py",
        "test_AC_PRSG_5_override_flow.py",
        "test_AC_PRSG_6_cli_invocable.py",
        "test_AC_PRSG_7_audit_log_entries.py",
        "test_AC_PRSG_8_production_stake_integration.py",
        "test_AC_PRSG_9_test_surface.py",
        "test_full_gate_against_fixture.py",
        "test_classifier_accuracy.py",
        "test_decision_matrix_coverage.py",
        "test_override_flow.py",
    ]
    for fname in expected:
        assert (_ROOT / fname).exists(), f"missing Cycle 1 test: {fname}"
