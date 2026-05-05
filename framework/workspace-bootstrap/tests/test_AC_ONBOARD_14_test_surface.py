# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.14 — Test-surface meta-test.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.14: validates the test-file
roster (15 per-AC files + 1 integration file). Catches accidental
deletion or renaming of AC tests.
"""

from __future__ import annotations

from pathlib import Path


TESTS_DIR = Path(__file__).parent

EXPECTED_PER_AC_TESTS = {
    "test_AC_ONBOARD_1_trigger_and_skip.py",
    "test_AC_ONBOARD_2_language_detection.py",
    "test_AC_ONBOARD_3_pm_sequencing.py",
    "test_AC_ONBOARD_4_channel_preference.py",
    "test_AC_ONBOARD_5_safety_profile.py",
    "test_AC_ONBOARD_6_extractor_opt_in.py",
    "test_AC_ONBOARD_7_watch_opt_in.py",
    "test_AC_ONBOARD_8_auto_skill_capture_opt_in.py",
    "test_AC_ONBOARD_9_completion_summary.py",
    "test_AC_ONBOARD_10_production_stake_default_flip.py",
    "test_AC_ONBOARD_11_audit_log.py",
    "test_AC_ONBOARD_12_fresh_user_smoke.py",
    "test_AC_ONBOARD_13_install_docs.py",
    "test_AC_ONBOARD_14_test_surface.py",
    "test_AC_ONBOARD_15_survey_as_default_source.py",
}

EXPECTED_INTEGRATION_TEST = "test_onboarding_integration.py"


def test_per_ac_test_files_present() -> None:
    """Every AC.ONBOARD.* has its own test file in this directory."""
    actual = {p.name for p in TESTS_DIR.iterdir() if p.name.startswith("test_AC_ONBOARD_")}
    missing = EXPECTED_PER_AC_TESTS - actual
    assert not missing, f"missing AC test files: {sorted(missing)}"


def test_integration_test_present() -> None:
    """Integration test file present per AC.ONBOARD.14."""
    integ = TESTS_DIR / EXPECTED_INTEGRATION_TEST
    assert integ.exists(), f"missing integration test: {EXPECTED_INTEGRATION_TEST!r}"


def test_test_count_meets_15_plus_1() -> None:
    """Roster: 15 per-AC + 1 integration test."""
    per_ac = [p.name for p in TESTS_DIR.iterdir() if p.name.startswith("test_AC_ONBOARD_")]
    assert len(per_ac) >= 15
    assert (TESTS_DIR / EXPECTED_INTEGRATION_TEST).exists()
