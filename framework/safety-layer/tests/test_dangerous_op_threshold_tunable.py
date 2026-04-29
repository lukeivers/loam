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
