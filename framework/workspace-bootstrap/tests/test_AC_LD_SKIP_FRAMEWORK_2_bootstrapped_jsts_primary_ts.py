# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LD.SKIP-FRAMEWORK.2 — bootstrapped JS/TS workspace → primary "ts".

Per v0.2.1 corrective F2 plan-doc §2 AC.LD.SKIP-FRAMEWORK.2: a workspace
mirroring the documented `loam init` post-state (root-level package.json
+ tsconfig.json + framework/ containing Ruby Gemfile fixtures from the
cloned canonical) MUST detect as `ts`, NOT `mixed`.

This is the happy-path scenario that broke in Cycle 3 HARD smoke:
Probe 1 onboarding asked "Ruby or JS/TS — which is primary?" because
detection scoped framework/ alongside the user's app code.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.language_detection import detect_language


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "fresh-user-onboarding"
    / "synthetic-bootstrapped-jsts"
)


def test_bootstrapped_jsts_primary_is_ts() -> None:
    """Root JS/TS + framework/ Ruby fixtures → primary `ts`.

    The fixture mirrors the post-`loam init` shape: package.json +
    tsconfig.json at the workspace root, framework/Gemfile +
    framework/Gemfile.lock from the cloned canonical's archive.
    Pre-fix this returned `mixed`; post-fix returns `ts`.
    """
    detection = detect_language(FIXTURE)

    assert detection.primary == "ts"


def test_bootstrapped_jsts_signals_exclude_framework_gemfile() -> None:
    """Detection signals exclude Ruby noise from framework/.

    The walker's skip applies before signal collection; Gemfile +
    Gemfile.lock under framework/ never enter the signals set.
    """
    detection = detect_language(FIXTURE)

    assert "package.json" in detection.signals
    assert "tsconfig.json" in detection.signals
    assert "Gemfile" not in detection.signals
    assert "Gemfile.lock" not in detection.signals


def test_bootstrapped_jsts_fixture_layout_is_realistic() -> None:
    """Sanity check: fixture must materially exercise the skip path.

    Plan-doc §4 halt trigger: fixture's framework/ contents must
    materially exercise the detection path (i.e., contain a Ruby
    Gemfile that WOULD trigger Ruby detection if framework/ were not
    skipped). Without this assertion the test could pass trivially
    by mis-construction of the fixture.
    """
    assert (FIXTURE / "package.json").is_file()
    assert (FIXTURE / "tsconfig.json").is_file()
    assert (FIXTURE / "framework").is_dir()
    assert (FIXTURE / "framework" / "Gemfile").is_file()
    assert (FIXTURE / "framework" / "Gemfile.lock").is_file()
