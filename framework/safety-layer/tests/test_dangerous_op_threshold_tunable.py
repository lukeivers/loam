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

"""Dangerous-op threshold — A13 + ruling #1.

A13. Threshold is read from safety.yaml config with framework-default
     1000 cents and minimum floor of 1 cent. Workspace may tune above
     the floor.
Ruling #1. Tunable with floor (1 cent).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.safety_layer import (
    DEFAULT_MONEY_THRESHOLD_CENTS,
    MONEY_THRESHOLD_FLOOR_CENTS,
    SafetyConfig,
)


def test_A13_default_threshold_is_1000_cents():
    cfg = SafetyConfig()
    assert cfg.money_threshold_cents == DEFAULT_MONEY_THRESHOLD_CENTS == 1000


def test_A13_floor_is_one_cent():
    assert MONEY_THRESHOLD_FLOOR_CENTS == 1


def test_A13_below_floor_rejected():
    with pytest.raises(ValidationError):
        SafetyConfig(money_threshold_cents=0)
    with pytest.raises(ValidationError):
        SafetyConfig(money_threshold_cents=-10)


def test_A13_workspace_can_tune_above_floor():
    cfg = SafetyConfig(money_threshold_cents=5000)
    assert cfg.money_threshold_cents == 5000
    # All the way down to 1 cent is accepted.
    cfg_min = SafetyConfig(money_threshold_cents=1)
    assert cfg_min.money_threshold_cents == 1
