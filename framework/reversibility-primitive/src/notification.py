"""Rollback-failure notifications via OneOnOneChannel (R23).

Subclass the sealed `OneOnOneChannel` to inherit the group-rejection
guard. Rollback failures are Tier 1 — one-on-one only; no group
channels and no queue (fail-closed on dispatch).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from primary_persona.introduction import OneOnOneChannel


@dataclass(frozen=True)
class ReversibilityChannel(OneOnOneChannel):
    """Subclass of the sealed OneOnOneChannel — inherits is_group=False.

    Nominal subclass so tests can tell reversibility channels apart
    from safety / degradation / introduction channels.
    """

    pass


@dataclass(frozen=True)
class RollbackNotification:
    """One rollback-related payload."""

    kind: str  # "rollback_failed" | "rollback_succeeded" | "cascade_invoked"
    text: str
    scope_id: str | None = None


@dataclass
class RollbackNotifier:
    """Dispatches rollback-failure notifications via one-on-one channels.

    R23: no group-channel paths. The constructor refuses any channel
    declaring `is_group=True` (inherits OneOnOneChannel's own guard
    at construction; the check here is belt-and-braces so tests that
    construct a notifier directly cannot slip a group channel in).
    """

    channels: Sequence[OneOnOneChannel]

    def __post_init__(self) -> None:
        for ch in self.channels:
            if ch.is_group:
                raise ValueError(
                    f"channel {ch.name!r} declares is_group=True; "
                    "rollback notifications are one-on-one only (R23)."
                )

    def has_active_channel(self) -> bool:
        return any(c.is_active for c in self.channels)

    async def send(self, notification: RollbackNotification) -> bool:
        active = [c for c in self.channels if c.is_active]
        if not active:
            return False
        ch = active[0]
        try:
            await ch.send(notification.text)
        except Exception:
            return False
        return True


def render_rollback_failure_text(
    *, scope_id: str, handle: str | None, reason: str, narrative: str
) -> str:
    lines = [
        "[Rollback failed — Tier 1]",
        f"Scope: {scope_id}",
        f"Handler: {handle or '<unregistered>'}",
        f"Reason: {reason}",
    ]
    if narrative:
        lines.append(f"Narrative: {narrative}")
    lines.append("")
    lines.append("Manual recovery may be required — inspect the event log.")
    return "\n".join(lines)
