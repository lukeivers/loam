# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PSAFE.3 — `production-stake` profile non-tunable floors.

Per ``docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.PSAFE.3 + Decision P (RESOLVED YES): the production-stake
profile, when active, sets non-tunable floors:

  - ``audit_trail: on`` (SOC-2 floor — non-negotiable for Eric).
  - ``cost_governance.warning_fraction`` floored at 0.6 (tighter than
    the default 0.8).
  - ``always_ask`` extends the framework floor with
    ``production-data-mutation``, ``customer-record-edit``.

This test verifies the cost-governance floor (the cost-side surface
of AC.PSAFE.3); the manifest field acceptance is in AC.PSAFE.1; the
audit-trail + always-ask floor wiring lives consumer-side and is
covered by the smoke test (AC.PSAFE.6).

The cost-governance floor is the production-side surface this test
pins because workspace-bootstrap reads the manifest's safety_profile
and the cost-governance config layer applies the floor at runtime.
"""

from __future__ import annotations

from loam.cost_governance.config import (
    PRODUCTION_STAKE_WARNING_FRACTION_FLOOR,
    CostConfig,
    apply_safety_profile_floor,
)


def test_production_stake_floors_warning_fraction_above() -> None:
    """User config of 0.8 (default) is clamped to 0.6 under
    production-stake."""
    config = CostConfig(warning_fraction=0.8)
    floored = apply_safety_profile_floor(config, safety_profile="production-stake")
    assert floored.warning_fraction == PRODUCTION_STAKE_WARNING_FRACTION_FLOOR
    assert floored.warning_fraction == 0.6


def test_production_stake_does_not_raise_already_low_value() -> None:
    """User config of 0.5 (below the floor) is preserved — the floor
    only clamps DOWN, never UP. A user already running tighter than
    the floor is honored."""
    config = CostConfig(warning_fraction=0.5)
    floored = apply_safety_profile_floor(config, safety_profile="production-stake")
    assert floored.warning_fraction == 0.5


def test_dev_profile_is_no_op_passthrough() -> None:
    """`dev` profile applies no floor — user config is preserved."""
    config = CostConfig(warning_fraction=0.95)
    floored = apply_safety_profile_floor(config, safety_profile="dev")
    assert floored.warning_fraction == 0.95
    # Same object (or model_copy with no changes) — semantically
    # identical to the input.
    assert floored.warning_fraction == config.warning_fraction


def test_research_profile_is_no_op_passthrough() -> None:
    """`research` profile applies no floor — user config is preserved."""
    config = CostConfig(warning_fraction=0.95)
    floored = apply_safety_profile_floor(config, safety_profile="research")
    assert floored.warning_fraction == 0.95


def test_production_stake_floor_constant_pinned_at_0_6() -> None:
    """The floor value is 0.6 — pinned against accidental change.
    Decision P RESOLVED YES locks the SOC-2 floor non-tunably."""
    assert PRODUCTION_STAKE_WARNING_FRACTION_FLOOR == 0.6


def test_production_stake_floor_does_not_mutate_input_config() -> None:
    """`apply_safety_profile_floor` returns a new CostConfig; the
    input is not mutated. Pydantic's model_copy guarantees this."""
    config = CostConfig(warning_fraction=0.8)
    apply_safety_profile_floor(config, safety_profile="production-stake")
    # input untouched
    assert config.warning_fraction == 0.8
