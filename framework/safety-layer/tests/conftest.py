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

"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeRuntime,
    ScopeSpec,
    SuccessCriterion,
)

from loam.safety_layer import (
    AlwaysAskList,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    SafetyConfig,
    SafetyController,
    SafetyNotifier,
    SafetyStore,
)

from .fakes import FakeOrchestrator, make_fake_channel


@pytest.fixture
def scope_runtime(tmp_path: Path) -> ScopeRuntime:
    rt = ScopeRuntime(tmp_path / "scope.sqlite", pending_extension_dir=tmp_path / "pe")
    yield rt
    try:
        rt.close()
    except Exception:
        pass


@pytest.fixture
def safety_store(tmp_path: Path) -> SafetyStore:
    store = SafetyStore(tmp_path / "safety.sqlite")
    yield store
    store.close()


@pytest.fixture
def default_ask_list() -> AlwaysAskList:
    return AlwaysAskList(
        version=1,
        framework_floor=DEFAULT_FRAMEWORK_FLOOR,
        workspace_additions=(),
        dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
    )


@pytest.fixture
def default_config() -> SafetyConfig:
    return SafetyConfig()


@pytest.fixture
def fake_orchestrator() -> FakeOrchestrator:
    return FakeOrchestrator()


@pytest.fixture
def active_channel():
    ch, received = make_fake_channel(name="telegram-active", active=True)
    return ch, received


@pytest.fixture
def inactive_channel():
    ch, received = make_fake_channel(name="telegram-down", active=False)
    return ch, received


@pytest.fixture
def controller(
    scope_runtime: ScopeRuntime,
    safety_store: SafetyStore,
    default_ask_list: AlwaysAskList,
    default_config: SafetyConfig,
    fake_orchestrator: FakeOrchestrator,
    active_channel,
) -> SafetyController:
    ch, _ = active_channel
    notifier = SafetyNotifier(channels=[ch])
    return SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=fake_orchestrator,
        store=safety_store,
        ask_list=default_ask_list,
        config=default_config,
        notifier=notifier,
    )


def make_spec(
    *,
    goal: str = "test scope",
    constraints: tuple[str, ...] = (),
    money_cents: int | None = None,
    reversibility: ReversibilityClass = ReversibilityClass.fully_reversible,
) -> ScopeSpec:
    return ScopeSpec(
        goal=goal,
        constraints=constraints,
        budget=Budget(
            time_seconds=60,
            money_cents=money_cents,
        ),
        reversibility_class=reversibility,
        success_criteria=(
            SuccessCriterion(criterion_id="done", description="it runs"),
        ),
        observers=(),
        escalation_triggers=(),
    )
