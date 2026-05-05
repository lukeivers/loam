"""AC.PRSI.10 — Component-level test surface inventory.

Updated v0.2.3 Cycle 3: AC.PRSG.* tests retired in favor of AC.PRGATE.*
(objective-altitude reframe per master plan §6.2).
"""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def test_per_ac_prsi_test_files_exist() -> None:
    expected = [
        "test_AC_PRSI_1_pre_commit_installer.py",
        "test_AC_PRSI_2_pre_push_installer.py",
        "test_AC_PRSI_3_hook_script_semantics.py",
        "test_AC_PRSI_4_github_actions_template.py",
        "test_AC_PRSI_5_gitlab_ci_template.py",
        "test_AC_PRSI_6_circleci_template.py",
        "test_AC_PRSI_8_install_ergonomics.py",
        "test_AC_PRSI_10_test_surface.py",
    ]
    for fname in expected:
        assert (_ROOT / fname).exists(), f"missing AC.PRSI test: {fname}"


def test_per_ac_prgate_test_files_exist() -> None:
    """v0.2.3 Cycle 3 — objective-altitude AC tests."""
    expected = [
        "test_AC_PRGATE_1_contract_reader.py",
        "test_AC_PRGATE_2_classifier.py",
        "test_AC_PRGATE_3_decision_matrix.py",
        "test_AC_PRGATE_4_override_flow.py",
        "test_AC_PRGATE_5_pr_description_template.py",
        "test_AC_PRGATE_6_audit_log.py",
    ]
    for fname in expected:
        assert (_ROOT / fname).exists(), f"missing AC.PRGATE test: {fname}"
