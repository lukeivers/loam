"""Self-correction notifications via OneOnOneChannel subclass (CR23).

Subclass the sealed `OneOnOneChannel` to inherit the group-channel
refusal guard. User-facing correction notifications — depth-cap and
same-class-cascade escalations (CR15, CR16), cost-refusal bubbles
(CR19) — flow exclusively through this channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from loam.primary_persona.introduction import OneOnOneChannel


@dataclass(frozen=True)
class CorrectionChannel(OneOnOneChannel):
    """Subclass of the sealed OneOnOneChannel — inherits is_group=False.

    Nominal subclass so tests can tell correction channels apart from
    cost / safety / reversibility channels. The post-init on the base
    class enforces `is_group=False` at construction.
    """

    pass


@dataclass(frozen=True)
class CorrectionNotification:
    """One escalation payload."""

    kind: str  # "cascade_depth" | "cascade_same_class" | "cost_refusal"
    text: str
    episode_id: str | None = None
    failure_class: str | None = None


@dataclass
class CorrectionNotifier:
    """Dispatches correction-escalation notifications via one-on-one channels.

    Constructor refuses any channel declaring `is_group=True` — inherits
    the base class guard; the belt-and-braces check here catches tests
    that build a notifier directly with a mis-shaped channel.
    """

    channels: Sequence[OneOnOneChannel]

    def __post_init__(self) -> None:
        for ch in self.channels:
            if ch.is_group:
                raise ValueError(
                    f"channel {ch.name!r} declares is_group=True; "
                    "self-correction notifications are one-on-one only "
                    "(CR23)."
                )

    def has_active_channel(self) -> bool:
        return any(c.is_active for c in self.channels)

    async def send(self, notification: CorrectionNotification) -> bool:
        active = [c for c in self.channels if c.is_active]
        if not active:
            return False
        ch = active[0]
        try:
            await ch.send(notification.text)
        except Exception:
            return False
        return True


def render_cascade_depth_text(
    *, episode_id: str, failure_class: str, depth: int, cap: int
) -> str:
    return (
        "[Self-correction escalation — Tier 1]\n"
        f"Episode: {episode_id}\n"
        f"Failure class: {failure_class}\n"
        f"Depth cap reached ({depth}/{cap}). Refusing to open a "
        f"further correction; escalating to the primary persona."
    )


def render_cascade_same_class_text(
    *, failure_class: str, count: int, window_seconds: int
) -> str:
    return (
        "[Self-correction escalation — Tier 1]\n"
        f"Failure class: {failure_class}\n"
        f"Same-class cascade: {count} corrections within "
        f"{window_seconds}s. Refusing to open another; escalating."
    )


def render_cost_refusal_text(
    *, episode_id: str, code: int, message: str
) -> str:
    return (
        "[Self-correction escalation — Tier 1]\n"
        f"Episode: {episode_id}\n"
        f"Cost ceiling refused correction scope "
        f"(code {code}): {message}\n"
        f"Correction has NOT been attempted. Resolve the ceiling "
        f"(cost.adjust_ceiling) or accept the original failure."
    )
