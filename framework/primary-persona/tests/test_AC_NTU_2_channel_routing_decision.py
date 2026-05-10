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

"""AC.NTU.2 — channel-routing policy decision (the four AC.NTU.2 (d) cells).

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.2 (d):

    tests cover the four cells:
      - slot=telegram + reply-target=telegram → pass
      - slot=telegram + reply-target=terminal + user-reply → halt
      - slot=telegram + reply-target=terminal + diagnostic → pass
      - slot=terminal → no-op

Per D-NTU.2.c (build-time decision documented in build report): full
Stop-hook integration is deferred — the slot + the policy function in
``primary_persona.channel_routing`` deliver the AC.NTU.2 surface
without attempting Stop-hook-level enforcement (Claude Code
``decision: 'block'`` blocks turn-completion but does not redirect
the reply, so a Stop-hook block alone wouldn't move the reply to
Telegram). The persona reads this policy at reply-emit time + routes
accordingly.
"""

from __future__ import annotations

from loam.primary_persona.channel_routing import (
    ChannelDecision,
    decide,
)


# ---- Cell 1: slot=telegram + reply-target=telegram → allow ----


def test_AC_NTU_2_cell_1_telegram_to_telegram_allows() -> None:
    """primary_channel=telegram + reply_target=telegram → allow
    (this IS the routed channel)."""
    d = decide(
        primary_channel="telegram",
        reply_target="telegram",
        reply_kind="user-reply",
    )
    assert d.block_terminal_reply is False
    assert "matches" in d.reason


def test_AC_NTU_2_cell_1_diagnostic_to_telegram_allows() -> None:
    """Cell-1 variant: kind=diagnostic also allows under
    primary_channel=telegram + target=telegram."""
    d = decide(
        primary_channel="telegram",
        reply_target="telegram",
        reply_kind="diagnostic",
    )
    assert d.block_terminal_reply is False


# ---- Cell 2: slot=telegram + reply-target=terminal + user-reply → block ----


def test_AC_NTU_2_cell_2_user_reply_via_terminal_blocked() -> None:
    """primary_channel=telegram + reply_target=terminal +
    reply_kind=user-reply → block."""
    d = decide(
        primary_channel="telegram",
        reply_target="terminal",
        reply_kind="user-reply",
    )
    assert d.block_terminal_reply is True
    # Reason names the routing constraint clearly.
    assert "telegram" in d.reason.lower()


# ---- Cell 3: slot=telegram + reply-target=terminal + diagnostic → allow ----


def test_AC_NTU_2_cell_3_diagnostic_via_terminal_allowed() -> None:
    """primary_channel=telegram + reply_target=terminal +
    reply_kind=diagnostic → allow (diagnostics never blocked)."""
    d = decide(
        primary_channel="telegram",
        reply_target="terminal",
        reply_kind="diagnostic",
    )
    assert d.block_terminal_reply is False
    assert "diagnostic" in d.reason.lower()


# ---- Cell 4: slot=terminal (or None) → no-op ----


def test_AC_NTU_2_cell_4_terminal_slot_no_op_user_reply() -> None:
    """primary_channel=terminal → no-op regardless of target/kind."""
    d = decide(
        primary_channel="terminal",
        reply_target="terminal",
        reply_kind="user-reply",
    )
    assert d.block_terminal_reply is False


def test_AC_NTU_2_cell_4_terminal_slot_no_op_telegram_target() -> None:
    """Cell-4 variant: even if reply_target=telegram under
    primary_channel=terminal, still no-op (caller decides what to do
    with the routing — this policy doesn't force terminal-routing)."""
    d = decide(
        primary_channel="terminal",
        reply_target="telegram",
        reply_kind="user-reply",
    )
    assert d.block_terminal_reply is False


def test_AC_NTU_2_cell_4_none_slot_treated_as_terminal_no_op() -> None:
    """primary_channel=None (fresh workspace pre-onboarding) →
    treated as terminal-equivalent for behavior preservation."""
    d = decide(
        primary_channel=None,
        reply_target="terminal",
        reply_kind="user-reply",
    )
    assert d.block_terminal_reply is False


# ---- Decision shape sanity ----


def test_AC_NTU_2_decision_is_frozen_dataclass() -> None:
    """ChannelDecision is a frozen dataclass with a binary block flag
    + a non-empty reason string."""
    d = decide(
        primary_channel="telegram",
        reply_target="terminal",
        reply_kind="user-reply",
    )
    assert isinstance(d, ChannelDecision)
    assert isinstance(d.block_terminal_reply, bool)
    assert isinstance(d.reason, str)
    assert len(d.reason) > 0
