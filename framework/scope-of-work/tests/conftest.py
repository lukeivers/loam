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

"""Shared pytest fixtures for the scope-of-work test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `src` importable as a package even when pytest runs from the
# scope-of-work root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loam.scope_of_work.runtime import ScopeRuntime  # noqa: E402
from loam.scope_of_work.spec import (  # noqa: E402
    Budget,
    BudgetExhaustionPolicy,
    Observer,
    ParentClosePolicy,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)


@pytest.fixture
async def runtime(tmp_path):
    db = tmp_path / "scope.db"
    pending = tmp_path / "pending"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=pending)
    yield rt
    rt.close()


def make_spec(
    *,
    goal: str = "test scope",
    budget: Budget | None = None,
    reversibility=ReversibilityClass.fully_reversible,
    triggers=(),
    success_criteria=(SuccessCriterion(criterion_id="c1", description="done"),),
    observers=(),
    parent_close_policy=ParentClosePolicy.TERMINATE,
    owner_persona: str | None = None,
    expected_duration_seconds: float | None = None,
):
    return ScopeSpec(
        goal=goal,
        constraints=("no real spending", "synthetic data only"),
        budget=budget or Budget(tokens=1000, money_cents=500, time_seconds=3600),
        reversibility_class=reversibility,
        success_criteria=tuple(success_criteria),
        observers=tuple(observers),
        escalation_triggers=tuple(triggers),
        owner_persona=owner_persona,
        parent_close_policy=parent_close_policy,
        expected_duration_seconds=expected_duration_seconds,
    )
