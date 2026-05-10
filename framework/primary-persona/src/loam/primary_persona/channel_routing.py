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

"""Channel-routing policy decision (v0.7.0 AC.NTU.2).

This module is the runtime-routing policy layer that the persona's
reply surface consults to decide whether a terminal-reply is allowed
or should be routed elsewhere (currently: Telegram, when the workspace
has opted into Telegram as primary channel).

The slot is the workspace-bootstrap manifest's ``primary_channel``
field (added at v0.7.0 alongside the existing
``channel_preference``); this module reads the slot + the reply
context and emits a single binary decision.

Per AC.NTU.2 (d) the four cells covered:

  1. ``primary_channel = 'telegram'``, reply target = telegram
     → ``False`` (allow; this IS the routed channel).
  2. ``primary_channel = 'telegram'``, reply target = terminal,
     reply kind = ``'user-reply'``
     → ``True`` (block; user replies must route through Telegram
     when the workspace is Telegram-routed).
  3. ``primary_channel = 'telegram'``, reply target = terminal,
     reply kind = ``'diagnostic'``
     → ``False`` (allow; diagnostics stay in terminal regardless of
     primary channel).
  4. ``primary_channel = 'terminal'`` (or ``None``)
     → ``False`` (allow; current behavior preserved as no-op).

The module is purely a policy function — it does not invoke any IO,
does not write files, does not block any process. Callers (the
persona's reply-emit path; future Stop-hook integration) consult the
function and act on the result.

Per the v0.7.0 plan-doc D-NTU.2.c (builder-time decision documented
in the build report): full Stop-hook integration is deferred — the
slot + this policy function deliver the AC.NTU.2 surface without
attempting Stop-hook-level mechanical enforcement (Claude Code
``decision: 'block'`` blocks turn-completion but does not redirect
the reply, so a Stop-hook block alone wouldn't move the reply to
Telegram). The persona reads this policy at reply-emit time + routes
accordingly. Stop-hook contributor wiring (audit-log emission +
future enforcement) is a candidate follow-on amendment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ---------------------------------------------------------------------------
# Decision input + result types


# Reply-target = where the reply would go if the policy doesn't block.
ReplyTarget = Literal["telegram", "terminal"]

# Reply-kind = the semantic class of the reply. Diagnostics (logs,
# error surfaces, tool-output) are never blocked from terminal even
# under Telegram routing — they're not user-facing communication.
ReplyKind = Literal["user-reply", "diagnostic"]

# Primary-channel = the workspace manifest slot value. None = unset
# (treated as "terminal" for behavior-preservation purposes; callers
# may distinguish None vs explicit "terminal" if they care, but the
# policy decision is identical).
PrimaryChannel = Literal["telegram", "terminal"] | None


@dataclass(frozen=True)
class ChannelDecision:
    """The policy decision for a single reply emit.

    ``block_terminal_reply`` is the binary answer the caller acts on.
    ``reason`` is a short human-readable explanation suitable for
    audit-log emission + diagnostic surfaces.
    """

    block_terminal_reply: bool
    reason: str


# ---------------------------------------------------------------------------
# Policy function (the AC's four-cell surface)


def decide(
    *,
    primary_channel: PrimaryChannel,
    reply_target: ReplyTarget,
    reply_kind: ReplyKind,
) -> ChannelDecision:
    """Decide whether to block a terminal-reply per AC.NTU.2.

    Returns a :class:`ChannelDecision` carrying the binary block flag
    + a short reason string. The function is total — every legal
    combination of inputs returns a defined decision.

    Cells covered (AC.NTU.2 (d)):

    +------------------------+-----------+--------------+----------------+
    | primary_channel        | target    | kind         | block?         |
    +========================+===========+==============+================+
    | telegram               | telegram  | (any)        | False (allow)  |
    +------------------------+-----------+--------------+----------------+
    | telegram               | terminal  | user-reply   | True  (block)  |
    +------------------------+-----------+--------------+----------------+
    | telegram               | terminal  | diagnostic   | False (allow)  |
    +------------------------+-----------+--------------+----------------+
    | terminal | None        | (any)     | (any)        | False (allow)  |
    +------------------------+-----------+--------------+----------------+
    """
    # Cell 4: terminal (or unset) — no-op; preserves current behavior.
    if primary_channel != "telegram":
        return ChannelDecision(
            block_terminal_reply=False,
            reason="primary_channel is not telegram; no routing constraint",
        )

    # primary_channel == "telegram" from here.

    # Cell 1: target IS the routed channel — trivially allowed.
    if reply_target == "telegram":
        return ChannelDecision(
            block_terminal_reply=False,
            reason="reply target matches primary_channel (telegram)",
        )

    # primary_channel == "telegram", reply_target == "terminal".

    # Cell 3: diagnostics always stay in terminal.
    if reply_kind == "diagnostic":
        return ChannelDecision(
            block_terminal_reply=False,
            reason=(
                "diagnostic reply allowed in terminal regardless of "
                "primary_channel (diagnostics are not user-facing "
                "communication)"
            ),
        )

    # Cell 2: user-reply attempting terminal under telegram routing.
    return ChannelDecision(
        block_terminal_reply=True,
        reason=(
            "primary_channel = telegram; user-reply attempted via "
            "terminal — route through telegram instead"
        ),
    )


__all__ = [
    "ChannelDecision",
    "PrimaryChannel",
    "ReplyKind",
    "ReplyTarget",
    "decide",
]
