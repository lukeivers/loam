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

"""Multi-identity allowlist — TG14, TG15, TG16, TG17.

TG14: owner-mediated identity addition flow; allowlist append
      populates `relationship` and `authority_class`.
TG15: inbound message from allowlisted non-owner identity arrives at
      handler with reduced-bound authority class in context.
TG16: Tier-A/B action requested by non-owner identity refuses; owner
      is notified via `owner_notify` callback.
TG17: unauthorised sender — plugin would reject at allowlist layer; if
      any message reaches pos-v2 without an entry, we drop and log
      (defence-in-depth).
"""

from __future__ import annotations

import pytest

from loam.telegram_interface.adapter import ChannelEvent, TelegramAdapter
from loam.telegram_interface.allowlist import AccessFile, AuthorityClass
from loam.telegram_interface.availability import (
    AvailabilityProbe,
    AvailabilityState,
    ProbeResult,
)
from loam.telegram_interface.confirmation import ConfirmationOutcome


async def _ok() -> ProbeResult:
    return ProbeResult(available=True, latency_ms=1.0)


async def _available_probe() -> AvailabilityProbe:
    probe = AvailabilityProbe(getme_probe=_ok, mcp_tool_probe=None)
    probe._state = AvailabilityState.available
    probe._last_result = ProbeResult(available=True)
    return probe


# TG14 --------------------------------------------------------


def test_tg14_owner_mediated_add_identity_flow(tmp_access_with_owner: AccessFile) -> None:
    """TG14 — owner-mediated add: the owner in-session creates the
    identity; the allowlist appends with `relationship` and
    `authority_class` populated by the owner at add-time."""
    tmp_access_with_owner.add_identity(
        user_id="222222",
        display_name="Spouse",
        relationship="spouse",
        authority_class=AuthorityClass.REDUCED_BOUND,
        actor="workspace_owner",
    )
    tmp_access_with_owner.save()

    identities = tmp_access_with_owner.identities()
    assert "222222" in identities
    spouse = identities["222222"]
    assert spouse.display_name == "Spouse"
    assert spouse.relationship == "spouse"
    assert spouse.authority_class == AuthorityClass.REDUCED_BOUND
    # Plugin's allowFrom also extended — the plugin drops messages
    # from unlisted IDs before pos-v2 ever sees them.
    assert "222222" in tmp_access_with_owner.allow_from


# TG15 --------------------------------------------------------


@pytest.mark.asyncio
async def test_tg15_inbound_from_spouse_carries_reduced_bound_context(
    tmp_access_with_spouse: AccessFile,
) -> None:
    """TG15 — inbound messages from allowlisted non-owner identity
    carry reduced-bound authority class in the handler context."""
    probe = await _available_probe()
    captured: list[ChannelEvent] = []

    async def handler(ev: ChannelEvent) -> None:
        captured.append(ev)

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_spouse,
        on_user_message=handler,
    )

    await adapter.on_inbound(
        meta={
            "chat_id": "222222",
            "message_id": "99",
            "user": "partner",
            "user_id": "222222",
            "ts": "2026-04-22T13:00:00Z",
        },
        content="remind me to pick up the kids",
    )
    assert len(captured) == 1
    ev = captured[0]
    assert ev.identity is not None
    assert ev.identity.display_name == "Partner"
    assert ev.authority_class == AuthorityClass.REDUCED_BOUND


# TG16 --------------------------------------------------------


@pytest.mark.asyncio
async def test_tg16_tier_ab_from_nonowner_refused_and_owner_notified(
    tmp_access_with_spouse: AccessFile,
) -> None:
    """TG16 — Tier-A/B action from non-owner identity → immediate
    nonowner_refused outcome; owner receives a notification via
    ``owner_notify``."""
    probe = await _available_probe()
    notified: list[str] = []

    async def notify(msg: str) -> None:
        notified.append(msg)

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_spouse,
        owner_notify=notify,
    )
    spouse = tmp_access_with_spouse.lookup("222222")
    assert spouse is not None

    outcome = await adapter.request_tier_ab_confirmation(
        action_name="publish_post",
        action_summary="publish draft to luke-ivers.com",
        identity=spouse,
    )
    assert outcome == ConfirmationOutcome.nonowner_refused
    assert len(notified) == 1
    assert "Partner" in notified[0]
    assert "Tier-A/B" in notified[0]


# TG17 --------------------------------------------------------


@pytest.mark.asyncio
async def test_tg17_unauthorised_sender_silently_dropped(
    tmp_access_with_owner: AccessFile,
) -> None:
    """TG17 — unauthorised Telegram sender slips past the plugin; the
    adapter drops and logs without routing to the handler. No
    handler invocation."""
    probe = await _available_probe()
    captured = []

    async def handler(ev: ChannelEvent) -> None:
        captured.append(ev)

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        on_user_message=handler,
    )
    # 999999 is not in pos_identities or allowFrom.
    await adapter.on_inbound(
        meta={
            "chat_id": "999999",
            "message_id": "1",
            "user": "unknown",
            "user_id": "999999",
            "ts": "2026-04-22T13:00:00Z",
        },
        content="add me to the allowlist",
    )
    assert captured == []
