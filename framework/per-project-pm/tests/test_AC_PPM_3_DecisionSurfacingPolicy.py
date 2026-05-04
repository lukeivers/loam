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

"""AC.PPM.3 — DecisionSurfacingPolicy Pydantic model + defaults.

Per parent plan §5 + cycle-2 plan §4 Surface #4:
  - default max_questions_per_turn = 1
  - default onboarding_mode = False
  - default require_owner_response = True
  - default cool_down_seconds = 0
  - reject max_questions_per_turn < 1
  - reject cool_down_seconds < 0
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.per_project_pm.contract import DecisionSurfacingPolicy


def test_defaults_correct() -> None:
    policy = DecisionSurfacingPolicy()
    assert policy.onboarding_mode is False
    assert policy.max_questions_per_turn == 1
    assert policy.cool_down_seconds == 0
    assert policy.require_owner_response is True


def test_reject_max_questions_per_turn_zero() -> None:
    with pytest.raises(ValidationError) as excinfo:
        DecisionSurfacingPolicy(max_questions_per_turn=0)
    assert "max_questions_per_turn" in str(excinfo.value)


def test_reject_max_questions_per_turn_negative() -> None:
    with pytest.raises(ValidationError) as excinfo:
        DecisionSurfacingPolicy(max_questions_per_turn=-1)
    assert "max_questions_per_turn" in str(excinfo.value)


def test_reject_cool_down_seconds_negative() -> None:
    with pytest.raises(ValidationError) as excinfo:
        DecisionSurfacingPolicy(cool_down_seconds=-1)
    assert "cool_down_seconds" in str(excinfo.value)


def test_accept_post_onboarding_batch_size() -> None:
    """Operator-tunable post-onboarding batch (max_questions_per_turn=N)."""
    policy = DecisionSurfacingPolicy(max_questions_per_turn=3)
    assert policy.max_questions_per_turn == 3


def test_policy_is_frozen() -> None:
    """frozen=True; tuning happens via re-construction at contract load."""
    policy = DecisionSurfacingPolicy()
    with pytest.raises(ValidationError):
        policy.max_questions_per_turn = 5  # type: ignore[misc]


def test_reject_unknown_field() -> None:
    """extra='forbid' rejects typos."""
    with pytest.raises(ValidationError):
        DecisionSurfacingPolicy(typo_field=True)
