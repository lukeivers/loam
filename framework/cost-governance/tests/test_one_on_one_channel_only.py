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
