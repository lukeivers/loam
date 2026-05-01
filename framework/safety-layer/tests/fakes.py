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

"""Test fakes — in-memory channel, minimal orchestrator stub."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loam.primary_persona.introduction import ChannelKind

from loam.safety_layer.notification import SafetyChannel


def make_fake_channel(*, name: str = "test-telegram", active: bool = True):
    """Build a SafetyChannel that captures every send for assertion."""
    received: list[str] = []

    async def _send(text: str) -> None:
        received.append(text)

    ch = SafetyChannel(
        kind=ChannelKind.personal_telegram,
        name=name,
        send=_send,
        is_group=False,
        is_active=active,
    )
    return ch, received


@dataclass
class FakeOrchestrator:
    """Just enough of pos_orchestrator.Orchestrator for the kill engine.
    Captures paused/resumed state and stop-requested flag for assertion."""

    _paused: bool = False
    _paused_reason: str | None = None
    _stop_requested: bool = False
    pause_log: list[str] = field(default_factory=list)
    resume_log: list[str] = field(default_factory=list)

    def pause_activation(self, reason: str) -> None:
        self._paused = True
        self._paused_reason = reason
        self.pause_log.append(reason)

    def resume_activation(self) -> None:
        self.resume_log.append(self._paused_reason or "")
        self._paused = False
        self._paused_reason = None

    def request_stop(self) -> None:
        self._stop_requested = True

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested
