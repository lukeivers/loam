# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LD.SKIP-FRAMEWORK.3 — bootstrapped Rails workspace → primary "rails".

Per v0.2.1 corrective F2 plan-doc §2 AC.LD.SKIP-FRAMEWORK.3: a workspace
mirroring the documented `loam init` post-state but with a Rails app at
the root (Gemfile + config/application.rb) and JS tooling under
framework/ (cloned canonical's archived JS) MUST detect as `rails`,
NOT `mixed`. Inverse-case sibling to AC.LD.SKIP-FRAMEWORK.2.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.language_detection import detect_language


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "fresh-user-onboarding"
    / "synthetic-bootstrapped-rails"
)


def test_bootstrapped_rails_primary_is_rails() -> None:
    """Root Rails + framework/ JS fixtures → primary `rails`.

    The fixture mirrors the post-`loam init` shape with a Rails app
    at the workspace root. Pre-fix this returned `mixed` (because
    framework/package.json was treated as a root-level signal);
    post-fix returns `rails`.
    """
    detection = detect_language(FIXTURE)

    assert detection.primary == "rails"


def test_bootstrapped_rails_signals_exclude_framework_js() -> None:
    """Detection signals exclude JS noise from framework/."""
    detection = detect_language(FIXTURE)

    assert "Gemfile" in detection.signals
    assert "config/application.rb" in detection.signals
    assert "package.json" not in detection.signals
    assert "tsconfig.json" not in detection.signals


def test_bootstrapped_rails_fixture_layout_is_realistic() -> None:
    """Sanity check: fixture must materially exercise the skip path.

    Plan-doc §4 halt trigger: fixture's framework/ contents must
    materially exercise the detection path (i.e., contain a
    package.json + tsconfig.json that WOULD trigger ts detection if
    framework/ were not skipped).
    """
    assert (FIXTURE / "Gemfile").is_file()
    assert (FIXTURE / "config" / "application.rb").is_file()
    assert (FIXTURE / "framework").is_dir()
    assert (FIXTURE / "framework" / "package.json").is_file()
    assert (FIXTURE / "framework" / "tsconfig.json").is_file()
