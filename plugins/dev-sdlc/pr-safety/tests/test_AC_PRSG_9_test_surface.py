"""AC.PRSG.9 — component-level test surface.

Meta-test: verifies all per-AC test files are present and the
integration tests are present.
"""

from __future__ import annotations

from pathlib import Path


_TESTS_DIR = Path(__file__).resolve().parent


def test_all_per_ac_test_files_present():
    """One per-AC test file per AC.PRSG.{1..9} exists."""
    expected = {
        "test_AC_PRSG_1_component_scaffold.py",
        "test_AC_PRSG_2_contract_reader.py",
        "test_AC_PRSG_3_diff_classifier.py",
        "test_AC_PRSG_4_decision_matrix.py",
        "test_AC_PRSG_5_override_flow.py",
        "test_AC_PRSG_6_cli_invocable.py",
        "test_AC_PRSG_7_audit_log_entries.py",
        "test_AC_PRSG_8_production_stake_integration.py",
        "test_AC_PRSG_9_test_surface.py",
    }
    actual = {p.name for p in _TESTS_DIR.glob("test_AC_PRSG_*.py")}
    missing = expected - actual
    assert not missing, f"missing per-AC test files: {missing}"


def test_integration_tests_present():
    """Integration test files per plan-doc §4 AC.PRSG.9 + §7.

    File names use the ``_d2``/``_d5``/``_d6`` suffix to disambiguate
    from the odd-extractor's identically-named test files at
    pytest collection time (rootdir conftest collects across the
    whole dev-sdlc plugin tree).
    """
    expected = {
        "test_full_gate_against_fixture.py",
        "test_audit_log_entries_d6.py",
        "test_cross_session_state_d5.py",
        "test_steady_state_idempotent_d2.py",
        "test_classifier_accuracy.py",
        "test_decision_matrix_coverage.py",
        "test_override_flow.py",
    }
    actual = {p.name for p in _TESTS_DIR.glob("test_*.py")}
    missing = expected - actual
    assert not missing, f"missing integration test files: {missing}"
