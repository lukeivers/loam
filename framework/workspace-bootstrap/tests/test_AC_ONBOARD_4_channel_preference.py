# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.4 — Q2 channel preference (Telegram / CLI / Skip).

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.4: three branches; manifest
field set; SetupWalkthrough invoked on telegram only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import run_onboarding


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def _bootstrap(tmp_path: Path) -> Path:
    p = tmp_path / "bootstrap.yaml"
    p.write_text("version: 1\ncontributions: []\n")
    return p


@pytest.mark.parametrize(
    "channel_answer,expected_field",
    [
        ("1", "telegram"),
        ("2", "cli"),
        ("3", "deferred"),
    ],
)
def test_channel_preference_branches_set_manifest_field(
    tmp_path: Path,
    channel_answer: str,
    expected_field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each Q2 branch writes the expected channel_preference value."""
    # Isolate the Telegram marker path so writing it doesn't pollute
    # the user's home directory during tests.
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = _bootstrap(tmp_path)
    answers = ["y", channel_answer, "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.channel_preference == expected_field


def test_telegram_branch_writes_setup_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On Q2=Telegram, the existing setup-walkthrough marker is written
    with status='offered' so the walkthrough resumes in the next session."""
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    _bootstrap(tmp_path)
    run_onboarding(
        tmp_path, answerer=_scripted(["y", "1", "2", "2", "2", "2"])
    )
    marker_path = fake_home / ".loam" / "telegram-setup-offered"
    assert marker_path.exists(), "telegram setup-walkthrough marker not written"
    import json

    payload = json.loads(marker_path.read_text())
    assert payload["status"] == "offered"


def test_cli_branch_writes_no_telegram_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Q2=CLI does NOT touch the telegram setup-walkthrough marker."""
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    _bootstrap(tmp_path)
    run_onboarding(
        tmp_path, answerer=_scripted(["y", "2", "2", "2", "2", "2"])
    )
    marker_path = fake_home / ".loam" / "telegram-setup-offered"
    assert not marker_path.exists(), "CLI branch must not write telegram marker"
