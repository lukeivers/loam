"""AC.OREK.7 — Component-level test surface.

This test asserts the structural test-surface requirement: every
AC.OREK.{1..7} family has at least one explicit test file, and the
integration tests named in the plan-doc §4 exist.

It is intentionally meta — it does not duplicate the assertions of
the per-AC tests; it ensures the surface itself is in place.
"""

from __future__ import annotations

from pathlib import Path


_TESTS_DIR = Path(__file__).resolve().parent


def test_per_ac_test_files_exist() -> None:
    """One test file per AC.OREK.1..7."""
    expected = [
        "test_AC_OREK_1_component_scaffold.py",
        "test_AC_OREK_2_cli_invocable.py",
        "test_AC_OREK_3_four_stage_workflow.py",
        "test_AC_OREK_4_language_adapter_registry.py",
        "test_AC_OREK_5_dry_run_estimate.py",
        "test_AC_OREK_6_budget_envelope.py",
        "test_AC_OREK_7_test_surface.py",
    ]
    for fname in expected:
        assert (_TESTS_DIR / fname).exists(), f"missing {fname}"


def test_integration_test_files_exist() -> None:
    """Integration tests — v0.2.3 Cycle 3 surface (legacy
    test_full_workflow_dry_run + test_steady_state_idempotent
    retired with v0.1.9 PR-safety reframe per master plan §6.2)."""
    expected = [
        "test_audit_log_entries.py",
        "test_cross_session_state.py",
        "test_v0_2_3_release_soft_smoke.py",
    ]
    for fname in expected:
        assert (_TESTS_DIR / fname).exists(), f"missing {fname}"


def test_scaffold_invariants_test_present() -> None:
    """Sub-tree scaffold-invariants test (mirror of dev-sdlc's
    seal-fence test, scoped to the odd-extractor sub-tree). Renamed
    from test_no_sealed_amendments.py to a unique basename so
    pytest collection at the dev-sdlc level doesn't double-import
    (the parent dev-sdlc tests directory carries its own seal-test
    with that basename — pytest doesn't allow same basename in
    different rootdirs without unique conftest scopes)."""
    assert (_TESTS_DIR / "test_odd_extractor_scaffold_invariants.py").exists()
