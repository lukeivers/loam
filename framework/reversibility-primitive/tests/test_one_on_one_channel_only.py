"""R23: RollbackNotifier rejects group channels at construction.

The sealed `OneOnOneChannel.__post_init__` already enforces
`is_group=False`; the notifier check here is belt-and-braces so tests
constructing a notifier directly cannot slip a group channel in via a
third-party subclass that bypassed `__post_init__`.
"""

from __future__ import annotations

import pytest

from primary_persona.introduction import ChannelKind, OneOnOneChannel

from reversibility_primitive import RollbackNotifier


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
    import dataclasses

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
