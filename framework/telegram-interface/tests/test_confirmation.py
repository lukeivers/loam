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

"""Telegram-originated extra-confirmation gate — TG18, TG19.

TG18: Tier-A/B request from Telegram → extra explicit-confirmation
      yes/no from Telegram required before execution.
TG19: confirmation timeout (30 minutes default) refuses the request;
      owner is notified of the refusal.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from loam.telegram_interface.adapter import ChannelEvent, TelegramAdapter
from loam.telegram_interface.allowlist import AccessFile, AuthorityClass, Identity
from loam.telegram_interface.availability import (
    AvailabilityProbe,
    AvailabilityState,
    ProbeResult,
)
from loam.telegram_interface.confirmation import (
    DEFAULT_CONFIRMATION_TIMEOUT_S,
    ConfirmationGate,
    ConfirmationOutcome,
)


async def _ok() -> ProbeResult:
    return ProbeResult(available=True, latency_ms=1.0)


async def _available_probe() -> AvailabilityProbe:
    probe = AvailabilityProbe(getme_probe=_ok, mcp_tool_probe=None)
    probe._state = AvailabilityState.available
    probe._last_result = ProbeResult(available=True)
    return probe


@pytest.mark.asyncio
async def test_tg18_tier_ab_confirmation_requires_yes_from_telegram(
    tmp_access_with_owner: AccessFile,
) -> None:
    """TG18 — the confirmation prompt is sent to the same identity
    and a `yes <request_id>` answer from Telegram resolves the
    confirmation."""
    probe = await _available_probe()
    sent: list[str] = []

    class FakeMcp:
        async def invoke(self, tool, args):
            sent.append(args["text"])
            return {}

    from loam.telegram_interface.mcp_client import McpReplyClient

    fake = FakeMcp()
    mcp = McpReplyClient(invoke_tool=fake.invoke)
    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        mcp_client=mcp,
    )
    owner = tmp_access_with_owner.owner()
    assert owner is not None

    # Kick off confirmation in background.
    task = asyncio.create_task(
        adapter.request_tier_ab_confirmation(
            action_name="delete_file",
            action_summary="remove /tmp/something.txt",
            identity=owner,
        )
    )
    # Wait long enough for the prompt to be emitted.
    await asyncio.sleep(0.05)
    assert len(sent) == 1
    prompt = sent[0]
    assert "extra confirmation required" in prompt
    assert "delete_file" in prompt
    # Extract the request_id from the prompt.
    import re
    m = re.search(r"`yes ([a-f0-9]{8})`", prompt)
    assert m is not None
    request_id = m.group(1)

    # Inbound "yes <id>" via the adapter resolves the gate.
    await adapter.on_inbound(
        meta={
            "chat_id": owner.user_id,
            "message_id": "77",
            "user": "luke",
            "user_id": owner.user_id,
            "ts": "2026-04-22T13:00:00Z",
        },
        content=f"yes {request_id}",
    )
    outcome = await asyncio.wait_for(task, timeout=1.0)
    assert outcome == ConfirmationOutcome.approved


@pytest.mark.asyncio
async def test_tg19_confirmation_timeout_refuses_and_notifies_owner(
    tmp_access_with_owner: AccessFile,
) -> None:
    """TG19 — if no answer arrives within the timeout, the request is
    refused and the owner is notified."""
    probe = await _available_probe()
    sent: list[str] = []

    class FakeMcp:
        async def invoke(self, tool, args):
            sent.append(args["text"])
            return {}

    from loam.telegram_interface.mcp_client import McpReplyClient

    fake = FakeMcp()
    mcp = McpReplyClient(invoke_tool=fake.invoke)

    notified: list[str] = []

    async def notify(msg: str) -> None:
        notified.append(msg)

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        mcp_client=mcp,
        confirmation=ConfirmationGate(timeout_s=0.05),  # short timeout for test
        owner_notify=notify,
    )
    owner = tmp_access_with_owner.owner()
    assert owner is not None

    outcome = await adapter.request_tier_ab_confirmation(
        action_name="publish_post",
        action_summary="send draft to medium.com",
        identity=owner,
    )
    assert outcome == ConfirmationOutcome.timeout
    assert any("timed out" in msg for msg in notified)


def test_default_confirmation_timeout_is_30_minutes() -> None:
    """Design-intent: Eve's inference #2 (30 minutes) held."""
    assert DEFAULT_CONFIRMATION_TIMEOUT_S == 30 * 60
