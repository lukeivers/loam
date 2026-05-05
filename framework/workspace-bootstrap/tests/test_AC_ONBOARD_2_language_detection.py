# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.2 — Project-language auto-detection.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.2 + §7: depth-bounded walk
returns rails / ruby / ts / js / mixed / unknown per the file-signal
matrix.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.language_detection import (
    DETECTION_FILES,
    MAX_WALK_DEPTH,
    LanguageDetection,
    detect_language,
)


FIXTURES = Path(__file__).parent / "fixtures" / "fresh-user-onboarding"


@pytest.mark.parametrize(
    "fixture_dir,expected_primary",
    [
        ("synthetic-rails", "rails"),
        ("synthetic-jsts", "ts"),
        ("synthetic-mixed", "mixed"),
        ("synthetic-unknown", "unknown"),
    ],
)
def test_detect_language_returns_expected_primary(
    fixture_dir: str, expected_primary: str
) -> None:
    """Each canonical fixture produces its expected primary language."""
    detection = detect_language(FIXTURES / fixture_dir)
    assert detection.primary == expected_primary


def test_signals_include_gemfile_for_rails() -> None:
    detection = detect_language(FIXTURES / "synthetic-rails")
    assert "Gemfile" in detection.signals
    assert "config/application.rb" in detection.signals


def test_signals_include_package_json_and_tsconfig_for_ts() -> None:
    detection = detect_language(FIXTURES / "synthetic-jsts")
    assert "package.json" in detection.signals
    assert "tsconfig.json" in detection.signals


def test_ruby_without_rails(tmp_path: Path) -> None:
    """Gemfile alone (no config/application.rb) → ruby."""
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    detection = detect_language(tmp_path)
    assert detection.primary == "ruby"


def test_js_without_typescript(tmp_path: Path) -> None:
    """package.json alone (no tsconfig.json) → js."""
    (tmp_path / "package.json").write_text("{}\n")
    detection = detect_language(tmp_path)
    assert detection.primary == "js"


def test_depth_bound_respected(tmp_path: Path) -> None:
    """Files deeper than MAX_WALK_DEPTH are NOT detected (depth bound)."""
    deep_path = tmp_path
    for level in range(MAX_WALK_DEPTH + 2):
        deep_path = deep_path / f"level{level}"
        deep_path.mkdir()
    (deep_path / "Gemfile").write_text("source 'rubygems'\n")
    detection = detect_language(tmp_path)
    assert detection.primary == "unknown"


def test_node_modules_not_walked(tmp_path: Path) -> None:
    """node_modules/ directory is skipped (otherwise package.jsons
    inside dependencies would falsely trigger js detection)."""
    nm = tmp_path / "node_modules" / "some-pkg"
    nm.mkdir(parents=True)
    (nm / "package.json").write_text("{}\n")
    detection = detect_language(tmp_path)
    assert detection.primary == "unknown"


def test_detection_files_pinned() -> None:
    """The DETECTION_FILES frozenset contains the AC.ONBOARD.2 names."""
    expected_subset = {
        "Gemfile",
        "Gemfile.lock",
        "config/application.rb",
        "package.json",
        "tsconfig.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
    }
    assert expected_subset.issubset(DETECTION_FILES)


def test_returns_language_detection_dataclass() -> None:
    """Return type is the structured dataclass per the AC."""
    detection = detect_language(FIXTURES / "synthetic-rails")
    assert isinstance(detection, LanguageDetection)
    assert isinstance(detection.signals, tuple)
    assert detection.primary in {"rails", "ruby", "ts", "js", "mixed", "unknown"}
