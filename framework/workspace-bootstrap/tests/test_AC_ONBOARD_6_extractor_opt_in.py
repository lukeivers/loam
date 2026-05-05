# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.6 — Q4 extractor opt-in (Y / Defer / Never).

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.6: three branches; on Y
fires `loam odd-extract <root>`; manifest field writes per branch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import run_onboarding


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


@pytest.mark.parametrize(
    "answer,expected_field",
    [
        ("1", "yes"),
        ("2", "deferred"),
        ("3", "never"),
    ],
)
def test_extractor_branches_persist_field(
    tmp_path: Path, answer: str, expected_field: str
) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    # Use a no-op extractor command so Y branch doesn't try to launch
    # the real extractor (subprocess /bin/true is a clean no-op).
    answers = ["y", "3", "2", answer, "2", "2"]
    run_onboarding(
        tmp_path,
        answerer=_scripted(answers),
        extractor_cmd=["/usr/bin/true"],
    )
    manifest = load_manifest(bootstrap)
    assert manifest.extractor_opt_in == expected_field


def test_y_branch_invokes_subprocess(
    tmp_path: Path
) -> None:
    """On Q4=Y the activation runs the injected extractor command."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    # Marker file written by the injected command proves the
    # subprocess executed.
    marker = tmp_path / "extractor-fired"
    cmd = ["/bin/sh", "-c", f"touch {marker!s}"]
    answers = ["y", "3", "2", "1", "2", "2"]
    run_onboarding(
        tmp_path,
        answerer=_scripted(answers),
        extractor_cmd=cmd,
    )
    assert marker.exists(), "extractor subprocess did not fire on Q4=Y"
