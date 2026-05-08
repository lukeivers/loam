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

"""R23: RollbackNotifier rejects group channels at construction.

The sealed `OneOnOneChannel.__post_init__` already enforces
`is_group=False`; the notifier check here is belt-and-braces so tests
constructing a notifier directly cannot slip a group channel in via a
third-party subclass that bypassed `__post_init__`.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel

from loam.reversibility_primitive import RollbackNotifier


def test_R23_group_channel_rejected_at_oneononechannel() -> None:
    """The sealed channel itself rejects is_group=True."""

    async def send(text: str) -> None:
        pass

    with pytest.raises(ValueError):
        OneOnOneChannel(
            kind=ChannelKind.personal_telegram,
            name="group-bad",
            send=send,
            is_group=True,
        )


def test_R23_notifier_rejects_forced_group_channel() -> None:
    """If somehow a channel with is_group=True reaches the notifier,
    the notifier refuses it too (defence-in-depth)."""

    async def send(text: str) -> None:
        pass

    # Bypass the post_init by forging a frozen dataclass directly.

    class _ForgedChannel(OneOnOneChannel):
        def __post_init__(self) -> None:  # override to skip guard
            pass

    ch = _ForgedChannel(
        kind=ChannelKind.personal_telegram,
        name="forged-group",
        send=send,
        is_group=True,
    )
    with pytest.raises(ValueError):
        RollbackNotifier(channels=[ch])
