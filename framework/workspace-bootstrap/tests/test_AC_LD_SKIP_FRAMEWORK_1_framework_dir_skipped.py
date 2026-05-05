# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LD.SKIP-FRAMEWORK.1 — _walk() skips framework/ subdirectory.

Per v0.2.1 corrective F2 plan-doc §2 AC.LD.SKIP-FRAMEWORK.1: signals
inside `framework/` (loam's harness scaffolding inside a bootstrapped
workspace) MUST NOT leak into project-language detection. The walker's
existing skip-set is extended with `framework`.

Smoke evidence (RED) prompting this AC: a user running
`loam init <workspace>` followed by `cd <workspace> && loam onboard`
sees Q1 = "I detected this is ruby" or "...both Ruby and JS/TS" because
the cloned canonical at <workspace>/framework/ carries archived Ruby
fixtures. Mental-model break on the install ritual's first question.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.language_detection import detect_language


def test_framework_gemfile_does_not_leak_signal(tmp_path: Path) -> None:
    """`framework/Gemfile` MUST NOT contribute a Ruby signal.

    Construct a workspace whose only language signal lives inside
    framework/. The walker must skip framework/ and report unknown.
    """
    framework_dir = tmp_path / "framework"
    framework_dir.mkdir()
    (framework_dir / "Gemfile").write_text("source 'https://rubygems.org'\n")

    detection = detect_language(tmp_path)

    assert detection.primary == "unknown"
    assert "Gemfile" not in detection.signals


def test_framework_package_json_does_not_leak_signal(tmp_path: Path) -> None:
    """`framework/package.json` MUST NOT contribute a JS signal.

    Inverse case to the Gemfile probe — same skip semantics; framework/
    contents are opaque regardless of the language they describe.
    """
    framework_dir = tmp_path / "framework"
    framework_dir.mkdir()
    (framework_dir / "package.json").write_text("{}\n")

    detection = detect_language(tmp_path)

    assert detection.primary == "unknown"
    assert "package.json" not in detection.signals


def test_framework_application_rb_does_not_leak_signal(tmp_path: Path) -> None:
    """`framework/config/application.rb` MUST NOT contribute a rails signal.

    Edge case: the special two-component `config/application.rb` lookup
    is anchored at depth-0; framework/config/application.rb sits at
    depth-2 and is unreachable because framework/ is skipped at depth-1.
    """
    framework_config = tmp_path / "framework" / "config"
    framework_config.mkdir(parents=True)
    (framework_config / "application.rb").write_text("module App; end\n")
    (tmp_path / "framework" / "Gemfile").write_text("source 'rubygems'\n")

    detection = detect_language(tmp_path)

    assert detection.primary == "unknown"
    assert "config/application.rb" not in detection.signals


def test_root_signals_dominate_when_framework_present(tmp_path: Path) -> None:
    """Root-level signals are detected; framework/ noise is filtered.

    Composes AC.LD.SKIP-FRAMEWORK.1 with the existing AC.ONBOARD.2
    detection rules — root-level package.json wins regardless of
    framework/ contents.
    """
    (tmp_path / "package.json").write_text("{}\n")
    framework_dir = tmp_path / "framework"
    framework_dir.mkdir()
    (framework_dir / "Gemfile").write_text("source 'rubygems'\n")
    (framework_dir / "Gemfile.lock").write_text("GEM\n")

    detection = detect_language(tmp_path)

    assert detection.primary == "js"
    assert "package.json" in detection.signals
    assert "Gemfile" not in detection.signals
    assert "Gemfile.lock" not in detection.signals
