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

"""CR23 — all user-facing notifications use CorrectionChannel (OneOnOneChannel subclass).

Group-channel refusal is inherited from the base class; the notifier
rejects any channel declaring is_group=True as belt-and-braces.
"""

from __future__ import annotations

import pytest
from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel

from loam.self_correction import CorrectionChannel, CorrectionNotifier


def test_CR23_correction_channel_subclasses_one_on_one() -> None:
    assert issubclass(CorrectionChannel, OneOnOneChannel)


def test_CR23_group_channel_refused_at_construction() -> None:
    async def _noop(_text: str) -> None:
        return None

    with pytest.raises(ValueError):
        CorrectionChannel(
            kind=ChannelKind.personal_telegram,
            name="group-chan",
            send=_noop,
            is_group=True,  # refused
        )


def test_CR23_notifier_rejects_group_channel() -> None:
    async def _noop(_text: str) -> None:
        return None

    # Pass a mis-shaped channel directly (base class would have blocked
    # at construction, but the notifier's belt-and-braces check still
    # runs — simulate via monkey).
    ch = OneOnOneChannel.__new__(OneOnOneChannel)
    object.__setattr__(ch, "kind", ChannelKind.personal_telegram)
    object.__setattr__(ch, "name", "bad")
    object.__setattr__(ch, "send", _noop)
    object.__setattr__(ch, "is_group", True)
    object.__setattr__(ch, "is_active", True)

    with pytest.raises(ValueError):
        CorrectionNotifier(channels=[ch])


async def test_CR23_notifier_delivers_via_active_channel() -> None:
    inbox: list[str] = []

    async def _send(text: str) -> None:
        inbox.append(text)

    ch = CorrectionChannel(
        kind=ChannelKind.personal_telegram,
        name="ok-chan",
        send=_send,
        is_group=False,
        is_active=True,
    )
    notifier = CorrectionNotifier(channels=[ch])
    from loam.self_correction.notification import CorrectionNotification

    await notifier.send(
        CorrectionNotification(
            kind="cost_refusal", text="hello", episode_id="ep-1"
        )
    )
    assert inbox == ["hello"]
