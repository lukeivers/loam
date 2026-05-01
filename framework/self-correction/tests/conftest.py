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

"""Shared fixtures for self-correction tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.introduction import ChannelKind
from loam.scope_of_work import ScopeRuntime

from loam.self_correction import (
    CorrectionChannel,
    CorrectionConfig,
    CorrectionNotifier,
    CorrectionStore,
    SelfCorrectionController,
)


@pytest.fixture
def store(tmp_path: Path) -> CorrectionStore:
    st = CorrectionStore(tmp_path / "correction.sqlite")
    yield st
    st.close()


@pytest.fixture
def config() -> CorrectionConfig:
    return CorrectionConfig(
        depth_cap=3,
        cascade_window_seconds=600,
        cascade_threshold=3,
        dedup_ttl_seconds=60,
        aggregator_poll_interval_seconds=30,
    )


def make_fake_channel(*, name: str = "correction-telegram", active: bool = True):
    received: list[str] = []

    async def _send(text: str) -> None:
        received.append(text)

    ch = CorrectionChannel(
        kind=ChannelKind.personal_telegram,
        name=name,
        send=_send,
        is_group=False,
        is_active=active,
    )
    return ch, received


@pytest.fixture
def channel_and_inbox():
    return make_fake_channel()


@pytest.fixture
def notifier(channel_and_inbox) -> CorrectionNotifier:
    ch, _ = channel_and_inbox
    return CorrectionNotifier(channels=[ch])


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
def controller(
    store: CorrectionStore, config: CorrectionConfig, notifier: CorrectionNotifier
) -> SelfCorrectionController:
    return SelfCorrectionController(
        store=store,
        config=config,
        notifier=notifier,
        allowed_user_report_callers=frozenset({"primary-persona", "eve"}),
    )
