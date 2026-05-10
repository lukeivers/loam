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

"""AC.NTU.2 — workspace-bootstrap manifest slot for primary_channel.

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.2:

    (b) the manifest-loader exposes ``primary_channel`` to the
    persona's session-start path

This file covers (b) — the manifest-side surface. The runtime policy
function lives in ``framework/primary-persona`` (covered by
test_AC_NTU_2_channel_routing_decision.py); the survey question
extension covers (a).

Per D-NTU.2.a ruling: extend ``<workspace>/.pos/manifest.yaml`` with
the new ``primary_channel`` field. For pre-v0.7.0 workspaces with
only the legacy ``channel_preference`` set, the loader derives
``primary_channel`` (graceful migration: telegram→telegram;
cli→terminal; deferred→None).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.workspace_bootstrap.manifest import (
    LEGAL_PRIMARY_CHANNELS,
    load_manifest,
    write_onboarding_fields,
)


def _write_manifest(p: Path, body: dict) -> Path:
    base = {"version": 1, "contributions": []}
    base.update(body)
    p.write_text(yaml.safe_dump(base, sort_keys=False))
    return p


def test_AC_NTU_2_legal_primary_channels_includes_telegram_and_terminal() -> None:
    """The two legal values per the AC are ``telegram`` and ``terminal``."""
    assert "telegram" in LEGAL_PRIMARY_CHANNELS
    assert "terminal" in LEGAL_PRIMARY_CHANNELS
    assert len(LEGAL_PRIMARY_CHANNELS) == 2


def test_AC_NTU_2_load_with_explicit_primary_channel(tmp_path: Path) -> None:
    """An explicit ``primary_channel: telegram`` field loads + exposes
    the value on the Manifest dataclass.
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {"primary_channel": "telegram"})
    m = load_manifest(p)
    assert m.primary_channel == "telegram"


def test_AC_NTU_2_load_with_explicit_terminal_value(tmp_path: Path) -> None:
    """``primary_channel: terminal`` loads."""
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {"primary_channel": "terminal"})
    m = load_manifest(p)
    assert m.primary_channel == "terminal"


def test_AC_NTU_2_absent_field_is_none_on_fresh_workspace(tmp_path: Path) -> None:
    """Absent ``primary_channel`` AND absent ``channel_preference``
    -> ``None`` on the Manifest dataclass.
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {})
    m = load_manifest(p)
    assert m.primary_channel is None


def test_AC_NTU_2_migration_default_from_channel_preference_telegram(
    tmp_path: Path,
) -> None:
    """Pre-v0.7.0 workspace with ``channel_preference: telegram`` and
    no ``primary_channel`` -> migration default exposes
    ``primary_channel == 'telegram'``.
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {"channel_preference": "telegram"})
    m = load_manifest(p)
    assert m.channel_preference == "telegram"
    assert m.primary_channel == "telegram"


def test_AC_NTU_2_migration_default_from_channel_preference_cli(
    tmp_path: Path,
) -> None:
    """``channel_preference: cli`` (the legacy terminal-equivalent) ->
    migration default ``primary_channel = 'terminal'``.
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {"channel_preference": "cli"})
    m = load_manifest(p)
    assert m.primary_channel == "terminal"


def test_AC_NTU_2_migration_default_from_channel_preference_deferred(
    tmp_path: Path,
) -> None:
    """``channel_preference: deferred`` (the legacy unset-equivalent)
    -> migration leaves ``primary_channel`` as None (caller defaults
    to terminal at runtime).
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {"channel_preference": "deferred"})
    m = load_manifest(p)
    assert m.primary_channel is None


def test_AC_NTU_2_invalid_value_fails_closed(tmp_path: Path) -> None:
    """An illegal value (e.g. 'sms') raises MissingConfigError per the
    fail-closed pattern shared with safety_profile / channel_preference.
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {"primary_channel": "sms"})
    from loam.workspace_bootstrap.errors import MissingConfigError

    with pytest.raises(MissingConfigError):
        load_manifest(p)


def test_AC_NTU_2_write_onboarding_fields_writes_primary_channel(
    tmp_path: Path,
) -> None:
    """The ``write_onboarding_fields`` helper accepts + persists
    ``primary_channel``.
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {})
    write_onboarding_fields(p, primary_channel="telegram")
    raw = yaml.safe_load(p.read_text())
    assert raw["primary_channel"] == "telegram"
    # And reload returns the value.
    m = load_manifest(p)
    assert m.primary_channel == "telegram"


def test_AC_NTU_2_explicit_primary_channel_overrides_migration_default(
    tmp_path: Path,
) -> None:
    """When BOTH fields are set explicitly, the explicit primary_channel
    wins (no auto-derivation override).
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(
        p,
        {
            "channel_preference": "telegram",
            "primary_channel": "terminal",
        },
    )
    m = load_manifest(p)
    assert m.channel_preference == "telegram"
    assert m.primary_channel == "terminal"


def test_AC_NTU_2_write_onboarding_fields_rejects_invalid_value(
    tmp_path: Path,
) -> None:
    """write_onboarding_fields raises ValueError on illegal value
    (matches the pattern for channel_preference / safety_profile).
    """
    p = tmp_path / "bootstrap.yaml"
    _write_manifest(p, {})
    with pytest.raises(ValueError):
        write_onboarding_fields(p, primary_channel="sms")
