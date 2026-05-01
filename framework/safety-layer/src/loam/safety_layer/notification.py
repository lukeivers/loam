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

"""Safety notifications via OneOnOneChannel.

Reuses the sealed `OneOnOneChannel` from primary_persona.introduction;
the `is_group=True` rejection is inherited at construction (A17). This
mirrors graceful-degradation's `DegradationChannel` pattern.

FAIL-CLOSED: unlike degradation, safety does NOT queue notifications.
If no active channel exists at dispatch time, `send()` returns False
and the caller (the gate) keeps the scope in `proposed` state. The
pending ask surfaces via `pos safety status`. This implements ruling #5
— no queue-and-fire; no auto-approve on channel loss; the user sees
the gap on next session startup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel

from . import observability as obs


@dataclass(frozen=True)
class SafetyChannel(OneOnOneChannel):
    """Subclass of the sealed OneOnOneChannel.

    Reuses the __post_init__ group-rejection guard — the one-on-one
    invariant is enforced by the sealed type, not re-implemented.
    """

    # No new fields; nominal subclass so tests can discriminate
    # safety channels from degradation / introduction channels.
    pass


@dataclass(frozen=True)
class SafetyNotification:
    """One safety notification payload."""

    kind: str  # "ask_gate" | "dangerous_op" | "kill" | "status"
    text: str
    scope_id: str | None = None


@dataclass
class SafetyNotifier:
    """Sends safety notifications via registered one-on-one channels.

    Fail-closed — no queue. If no active channel is reachable at send
    time, returns False; the caller must refuse to advance the scope
    past `proposed` (ruling #5). Tests and the CLI can register fake
    channels to drive the ask flow deterministically.
    """

    channels: Sequence[OneOnOneChannel]

    def __post_init__(self) -> None:
        for ch in self.channels:
            if ch.is_group:
                raise ValueError(
                    f"channel {ch.name!r} declares is_group=True; "
                    "safety notifications are one-on-one only (v1.2 R15)."
                )

    def has_active_channel(self) -> bool:
        return any(c.is_active for c in self.channels)

    async def send(self, notification: SafetyNotification) -> bool:
        """Dispatch. Returns True on delivery; False on no-active-channel
        or send failure. Safety does NOT queue — ruling #5.
        """
        active = [c for c in self.channels if c.is_active]
        if not active:
            obs.notification_dispatched(
                channel="<none>",
                outcome="unavailable_fail_closed",
                kind=notification.kind,
            )
            return False
        channel = active[0]
        try:
            await channel.send(notification.text)
        except Exception as e:  # noqa: BLE001
            obs.notification_dispatched(
                channel=channel.name,
                outcome=f"failed:{type(e).__name__}",
                kind=notification.kind,
            )
            return False
        obs.notification_dispatched(
            channel=channel.name,
            outcome="delivered",
            kind=notification.kind,
        )
        return True


# ---- template rendering (pure text, no LLM) ---------------------------


def render_ask_gate_text(
    *,
    scope_id: str | None,
    goal: str,
    action_classes: list[str],
    descriptions: dict[str, str],
    timeout_hint: str,
) -> str:
    """Plain-text ask-gate render.

    LLM has no presence here — the primary persona adapts tone at its
    own session layer when relaying the message. The gate is
    deterministic (proposal §5 "no LLM inference inside the gate").
    """
    lines = [
        "[Safety gate — approval required]",
        f"Scope: {scope_id or '<pending>'}",
        f"Goal: {goal}",
        "Categories:",
    ]
    for ac in action_classes:
        desc = descriptions.get(ac, "")
        lines.append(f"  - {ac}: {desc}" if desc else f"  - {ac}")
    lines.append("")
    lines.append("Reply with: approve / refuse")
    lines.append(f"Approval timeout: {timeout_hint}")
    return "\n".join(lines)


def render_dangerous_op_text(
    *,
    scope_id: str | None,
    goal: str,
    reasons: list[str],
    money_cents: int | None,
    reversibility_class: str,
) -> str:
    money_display = (
        f"${money_cents / 100:.2f}" if money_cents is not None and money_cents > 0 else "no money budget"
    )
    lines = [
        "[Safety gate — dangerous operation]",
        f"Scope: {scope_id or '<pending>'}",
        f"Goal: {goal}",
        f"Classification: {reversibility_class} + {', '.join(reasons) or 'n/a'}",
        f"Money budget: {money_display}",
        "",
        "Approve once        → one-shot approval, this scope only",
        "Approve + allowlist → add to workspace allowlist for bounded window",
        "Refuse              → scope cancels immediately; audit record written",
        "Refuse + denylist   → add to workspace denylist; scope cancels",
        "",
        "Reply with: approve / approve-allowlist / refuse / refuse-denylist",
    ]
    return "\n".join(lines)
