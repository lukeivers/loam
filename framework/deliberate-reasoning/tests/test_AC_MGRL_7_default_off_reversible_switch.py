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

"""AC.MGRL.7 — the slice ships default-OFF: enabling the deliberate layer is
an explicit, reversible opt-in, and with it off the harness is unchanged.

Pins: (a) the default is OFF (no config, no env => disabled); (b) the env
var is the explicit reversible switch (on and back off); (c) an explicit
TurnConfig flag overrides the env var both ways.
"""

from __future__ import annotations

import pytest

from loam.deliberate_reasoning.turn import (
    ENABLE_ENV_VAR,
    TurnConfig,
    _enabled_from_env,
)


def test_AC_MGRL_7_default_is_off(monkeypatch):
    monkeypatch.delenv(ENABLE_ENV_VAR, raising=False)
    assert TurnConfig().is_enabled() is False
    assert _enabled_from_env() is False


def test_AC_MGRL_7_env_var_is_reversible_switch(monkeypatch):
    monkeypatch.setenv(ENABLE_ENV_VAR, "1")
    assert TurnConfig().is_enabled() is True
    # Reversible: clearing it returns to OFF.
    monkeypatch.setenv(ENABLE_ENV_VAR, "0")
    assert TurnConfig().is_enabled() is False
    monkeypatch.delenv(ENABLE_ENV_VAR, raising=False)
    assert TurnConfig().is_enabled() is False


def test_AC_MGRL_7_explicit_flag_overrides_env_both_ways(monkeypatch):
    monkeypatch.setenv(ENABLE_ENV_VAR, "1")
    assert TurnConfig(enabled=False).is_enabled() is False  # explicit off wins
    monkeypatch.delenv(ENABLE_ENV_VAR, raising=False)
    assert TurnConfig(enabled=True).is_enabled() is True  # explicit on wins


@pytest.mark.parametrize("token", ["1", "true", "on", "yes", "TRUE", "On"])
def test_AC_MGRL_7_enabling_tokens(monkeypatch, token):
    monkeypatch.setenv(ENABLE_ENV_VAR, token)
    assert _enabled_from_env() is True


@pytest.mark.parametrize("token", ["", "0", "false", "off", "no", "maybe"])
def test_AC_MGRL_7_non_enabling_tokens(monkeypatch, token):
    monkeypatch.setenv(ENABLE_ENV_VAR, token)
    assert _enabled_from_env() is False
