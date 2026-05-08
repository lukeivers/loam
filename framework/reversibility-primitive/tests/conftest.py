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

"""Shared fixtures for the reversibility primitive tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.introduction import ChannelKind
from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeRuntime,
    ScopeSpec,
    SuccessCriterion,
)

from loam.reversibility_primitive import (
    ReversibilityChannel,
    ReversibilityController,
    ReversibilityStore,
    RollbackNotifier,
)


def make_fake_channel(*, name: str = "test-telegram", active: bool = True):
    received: list[str] = []

    async def _send(text: str) -> None:
        received.append(text)

    ch = ReversibilityChannel(
        kind=ChannelKind.personal_telegram,
        name=name,
        send=_send,
        is_group=False,
        is_active=active,
    )
    return ch, received


@pytest.fixture
def scope_runtime(tmp_path: Path) -> ScopeRuntime:
    rt = ScopeRuntime(
        tmp_path / "scope.sqlite", pending_extension_dir=tmp_path / "pe"
    )
    yield rt
    try:
        rt.close()
    except Exception:
        pass


@pytest.fixture
def store(tmp_path: Path) -> ReversibilityStore:
    st = ReversibilityStore(tmp_path / "reversibility.sqlite")
    yield st
    st.close()


@pytest.fixture
def active_channel():
    return make_fake_channel(name="rev-telegram-active", active=True)


@pytest.fixture
def notifier(active_channel) -> RollbackNotifier:
    ch, _ = active_channel
    return RollbackNotifier(channels=[ch])


@pytest.fixture
def controller(
    store: ReversibilityStore,
    scope_runtime: ScopeRuntime,
    notifier: RollbackNotifier,
) -> ReversibilityController:
    return ReversibilityController(
        store=store,
        scope_runtime=scope_runtime,
        notifier=notifier,
        # No safety_approval_resolver → fail-closed on irreversible +
        # no binding. Tests that want a resolver override explicitly.
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
        budget=Budget(time_seconds=60, money_cents=money_cents),
        reversibility_class=reversibility,
        success_criteria=(
            SuccessCriterion(criterion_id="done", description="it runs"),
        ),
        observers=(),
        escalation_triggers=(),
    )
