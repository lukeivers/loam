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

"""Shared fixtures for cost-governance tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.primary_persona.introduction import ChannelKind
from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeRuntime,
    ScopeSpec,
    SuccessCriterion,
)

from loam.cost_governance import (
    CostChannel,
    CostConfig,
    CostController,
    CostLedger,
    CostNotifier,
    CostStore,
    RollingCeiling,
    SessionCeiling,
)


def make_fake_channel(*, name: str = "cost-telegram", active: bool = True):
    received: list[str] = []

    async def _send(text: str) -> None:
        received.append(text)

    ch = CostChannel(
        kind=ChannelKind.personal_telegram,
        name=name,
        send=_send,
        is_group=False,
        is_active=active,
    )
    return ch, received


def make_spec(
    *,
    goal: str = "test scope",
    constraints: tuple[str, ...] = (),
    time_seconds: int | None = 60,
    tokens: int | None = None,
    money_cents: int | None = None,
    reversibility: ReversibilityClass = ReversibilityClass.fully_reversible,
) -> ScopeSpec:
    return ScopeSpec(
        goal=goal,
        constraints=constraints,
        budget=Budget(
            time_seconds=time_seconds,
            tokens=tokens,
            money_cents=money_cents,
        ),
        reversibility_class=reversibility,
        success_criteria=(
            SuccessCriterion(criterion_id="done", description="it runs"),
        ),
        observers=(),
        escalation_triggers=(),
    )


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
def store(tmp_path: Path) -> CostStore:
    st = CostStore(tmp_path / "cost.sqlite")
    yield st
    st.close()


def build_config(
    *,
    session_money: int | None = None,
    session_tokens: int | None = None,
    session_time: int | None = None,
    daily_money: int | None = None,
    hourly_money: int | None = None,
    warning_fraction: float = 0.8,
) -> CostConfig:
    return CostConfig(
        session=SessionCeiling(
            time_seconds=session_time,
            tokens=session_tokens,
            money_cents=session_money,
        ),
        rolling=[
            RollingCeiling(
                window_kind="daily",
                duration_seconds=24 * 60 * 60,
                money_cents=daily_money,
            ),
            RollingCeiling(
                window_kind="hourly",
                duration_seconds=60 * 60,
                money_cents=hourly_money,
            ),
        ],
        warning_fraction=warning_fraction,
    )


@pytest.fixture
def ledger(store: CostStore) -> CostLedger:
    config = build_config()
    return CostLedger(store=store, config=config)
