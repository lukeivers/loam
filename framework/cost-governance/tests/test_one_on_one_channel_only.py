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

"""C25: Throttle notifications use OneOnOneChannel; is_group=True rejected."""

from __future__ import annotations

import pytest

from loam.primary_persona.introduction import ChannelKind

from loam.cost_governance import CostChannel, CostNotifier


def test_C25_cost_channel_refuses_is_group_true() -> None:
    async def _send(text: str) -> None: ...

    with pytest.raises(ValueError):
        CostChannel(
            kind=ChannelKind.personal_telegram,
            name="bad",
            send=_send,
            is_group=True,
        )


def test_C25_cost_notifier_refuses_group_channel_via_base_injection() -> None:
    """Base-class guard fires at channel construction, but the notifier
    also guards to catch mis-constructed channels. We simulate via a
    frozen dataclass that lies about is_group after construction (which
    Python permits with object.__setattr__).
    """
    async def _send(text: str) -> None: ...

    ch = CostChannel(
        kind=ChannelKind.personal_telegram,
        name="ok",
        send=_send,
        is_group=False,
    )
    # Force-flip to simulate a post-construction tamper.
    object.__setattr__(ch, "is_group", True)
    with pytest.raises(ValueError):
        CostNotifier(channels=[ch])
