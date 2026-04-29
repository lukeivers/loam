"""Cost-governance throttle notifications via OneOnOneChannel (C25).

Subclass the sealed `OneOnOneChannel` to inherit the group-rejection
guard. Throttle warnings (80% threshold — ruling #2) are one-on-one
only; no group-channel escape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from loam.primary_persona.introduction import OneOnOneChannel


@dataclass(frozen=True)
class CostChannel(OneOnOneChannel):
    """Subclass of the sealed OneOnOneChannel — inherits is_group=False.

    Nominal subclass so tests can tell cost channels apart from
    safety / reversibility / introduction channels. The post-init on
    the base class enforces `is_group=False` at construction.
    """

    pass


@dataclass(frozen=True)
class CostNotification:
    """One throttle-warning payload."""

    kind: str  # "ceiling_warning"
    text: str
    scope_id: str | None = None
    ceiling_kind: str | None = None
    axis: str | None = None
    window_kind: str | None = None


@dataclass
class CostNotifier:
    """Dispatches cost-warning notifications via one-on-one channels.

    C25: no group-channel paths. The constructor refuses any channel
    declaring `is_group=True` (inherits the base class guard; the
    belt-and-braces check here catches tests that build a notifier
    directly with a mis-shaped channel).
    """

    channels: Sequence[OneOnOneChannel]

    def __post_init__(self) -> None:
        for ch in self.channels:
            if ch.is_group:
                raise ValueError(
                    f"channel {ch.name!r} declares is_group=True; "
                    "cost-warning notifications are one-on-one only (C25)."
                )

    def has_active_channel(self) -> bool:
        return any(c.is_active for c in self.channels)

    async def send(self, notification: CostNotification) -> bool:
        active = [c for c in self.channels if c.is_active]
        if not active:
            return False
        ch = active[0]
        try:
            await ch.send(notification.text)
        except Exception:
            return False
        return True


def render_ceiling_warning_text(
    *,
    scope_id: str,
    ceiling_kind: str,
    axis: str,
    window_kind: str | None,
    fraction: float,
    projected: int,
    ceiling: int,
) -> str:
    """Plain-text body for the throttle notification.

    Format is deliberately terse — Tier-2 one-liner shape; the user
    can pull detail from `pos cost status` if wanted.
    """
    scope = (
        f"{ceiling_kind}[{window_kind}]" if window_kind else ceiling_kind
    )
    pct = int(round(fraction * 100))
    return (
        f"[Cost warning — Tier 2]\n"
        f"Scope: {scope_id}\n"
        f"Ceiling: {scope}.{axis} at ~{pct}% ({projected}/{ceiling})\n"
        f"Activation would cross the warning threshold."
    )
