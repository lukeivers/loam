# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.NTU.2 (a) — onboarding survey extension writes ``primary_channel``.

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.2 (a):

    onboarding survey adds the channel-default question (or extends
    AC.ONBOARD.4 to cover both telegram + terminal explicitly with
    ``primary_channel`` semantics — D-NTU.2.b ruling)

D-NTU.2.b ruling at build-time: extend the existing AC.ONBOARD.4
question to drive both the legacy ``channel_preference`` field AND
the new ``primary_channel`` field from the same answer (telegram →
both telegram; CLI-only → channel_preference=cli +
primary_channel=terminal; Skip → both deferred/None).
"""

from __future__ import annotations

from pathlib import Path

import pytest

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
    "channel_answer,expected_pc",
    [
        ("1", "telegram"),  # Telegram → primary_channel = telegram
        ("2", "terminal"),  # CLI-only → primary_channel = terminal
        ("3", None),  # Skip-for-now → primary_channel = None (unset)
    ],
)
def test_AC_NTU_2_a_onboarding_writes_primary_channel(
    tmp_path: Path,
    channel_answer: str,
    expected_pc: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each Q2 branch writes the expected ``primary_channel`` value
    alongside the existing ``channel_preference`` field.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = _bootstrap(tmp_path)
    answers = ["y", channel_answer, "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.primary_channel == expected_pc


def test_AC_NTU_2_a_telegram_pick_sets_both_fields_to_telegram(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The telegram branch sets BOTH legacy + new fields to 'telegram'."""
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = _bootstrap(tmp_path)
    run_onboarding(
        tmp_path, answerer=_scripted(["y", "1", "2", "2", "2", "2"])
    )
    manifest = load_manifest(bootstrap)
    assert manifest.channel_preference == "telegram"
    assert manifest.primary_channel == "telegram"


def test_AC_NTU_2_a_cli_pick_sets_legacy_cli_and_primary_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI-only branch sets legacy=cli + primary_channel=terminal
    (the legacy 'cli' value maps to the new 'terminal' runtime slot).
    """
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = _bootstrap(tmp_path)
    run_onboarding(
        tmp_path, answerer=_scripted(["y", "2", "2", "2", "2", "2"])
    )
    manifest = load_manifest(bootstrap)
    assert manifest.channel_preference == "cli"
    assert manifest.primary_channel == "terminal"
