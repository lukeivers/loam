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

"""Transport routing — TG7–TG11.

TG7: MCP plugin `reply` invoked when plugin available and session has
     `--channels`.
TG8: direct Bot API used when no MCP session but token is configured.
TG9: nine named failure classes → fallback (in-session + attention.md)
     with framing preamble.
TG10: inbound `<channel source=telegram>` events pass through the
      allowlist and arrive at the handler with identity context.
TG11: on recovery from outage the adapter resumes normal routing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.telegram_interface.adapter import (
    ChannelEvent,
    TelegramAdapter,
)
from loam.telegram_interface.allowlist import AccessFile, AuthorityClass
from loam.telegram_interface.availability import (
    AvailabilityProbe,
    FailureClass,
    ProbeResult,
)
from loam.telegram_interface.bot_api import BotApiClient, BotApiError
from loam.telegram_interface.fallback import fallback_preamble
from loam.telegram_interface.mcp_client import McpReplyClient


# ---- helpers ---------------------------------------------------


class FakeMcp:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def invoke(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool, args))
        return {"message_id": "42"}


async def _getme_ok() -> ProbeResult:
    return ProbeResult(available=True, latency_ms=10.0)


async def _getme_fail() -> ProbeResult:
    return ProbeResult(
        available=False,
        latency_ms=100.0,
        failure_class=FailureClass.api_unreachable,
        detail="mock offline",
    )


async def _mcp_connected() -> bool:
    return True


async def _mcp_not_connected() -> bool:
    return False


async def _make_probe(available: bool, tool_connected: bool = True) -> AvailabilityProbe:
    probe = AvailabilityProbe(
        getme_probe=_getme_ok if available else _getme_fail,
        mcp_tool_probe=_mcp_connected if tool_connected else _mcp_not_connected,
        cache_dir=Path("/tmp/nonexistent-telegram-cache"),  # will force unavailable
    )
    # Bypass filesystem probe for this test by directly setting state.
    if available:
        probe._state = probe.state.__class__.available
        from loam.telegram_interface.availability import AvailabilityState, ProbeResult as PR
        probe._state = AvailabilityState.available
        probe._last_result = PR(available=True, latency_ms=10.0)
    else:
        from loam.telegram_interface.availability import AvailabilityState, ProbeResult as PR
        probe._state = AvailabilityState.unavailable
        probe._last_result = PR(
            available=False,
            failure_class=FailureClass.api_unreachable,
            detail="mock",
        )
    return probe


# ---- tests -----------------------------------------------------


@pytest.mark.asyncio
async def test_tg7_mcp_reply_invoked_when_available(tmp_access_with_owner: AccessFile) -> None:
    """TG7 — with Telegram available and an MCP client wired, the
    adapter's `send` invokes the plugin's `reply` tool."""
    probe = await _make_probe(available=True)
    fake = FakeMcp()
    mcp = McpReplyClient(invoke_tool=fake.invoke)
    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        mcp_client=mcp,
    )
    channel = adapter.build_channel()
    await channel.send("hello from eve")
    assert len(fake.calls) == 1
    assert fake.calls[0][0] == "reply"
    assert fake.calls[0][1]["chat_id"] == "111111"
    assert fake.calls[0][1]["text"] == "hello from eve"


@pytest.mark.asyncio
async def test_tg8_direct_bot_api_when_no_mcp(tmp_access_with_owner: AccessFile) -> None:
    """TG8 — with no MCP client (out-of-session) but Telegram
    available, the adapter sends via the direct Bot API."""
    probe = await _make_probe(available=True)

    calls: list[tuple[str, dict[str, Any]]] = []

    async def transport(method: str, payload: dict[str, Any]) -> dict[str, Any]:
        calls.append((method, payload))
        return {"message_id": 42}

    bot = BotApiClient(transport=transport)
    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        bot_api=bot,
    )
    channel = adapter.build_channel()
    await channel.send("morning briefing")
    assert calls == [("sendMessage", {"chat_id": "111111", "text": "morning briefing"})]


@pytest.mark.asyncio
async def test_tg9_fallback_when_unavailable_with_framing(tmp_access_with_owner: AccessFile, tmp_path: Path) -> None:
    """TG9 — with Telegram unavailable, outbound routes to in-session
    + attention.md; framing preamble names the degraded state."""
    probe = await _make_probe(available=False)

    in_session: list[str] = []

    async def in_sess(text: str) -> None:
        in_session.append(text)

    attention = tmp_path / "attention.md"

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        in_session_send=in_sess,
    )
    # Patch fallback path.
    import loam.telegram_interface.fallback as fb
    original = fb.DEFAULT_ATTENTION_PATH
    fb.DEFAULT_ATTENTION_PATH = attention
    try:
        channel = adapter.build_channel()
        await channel.send("escalation!")
    finally:
        fb.DEFAULT_ATTENTION_PATH = original

    assert len(in_session) == 1
    assert fallback_preamble("api_unreachable") in in_session[0]
    assert "escalation!" in in_session[0]
    # attention.md got a framed entry.
    content = attention.read_text()
    assert "telegram-fallback" in content
    assert "api_unreachable" in content
    assert "escalation!" in content


@pytest.mark.asyncio
async def test_tg10_inbound_routes_through_allowlist(tmp_access_with_owner: AccessFile) -> None:
    """TG10 — inbound `<channel>` events pass through the allowlist
    and arrive at the handler with identity context attached."""
    probe = await _make_probe(available=True)
    captured: list[ChannelEvent] = []

    async def handler(event: ChannelEvent) -> None:
        captured.append(event)

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        on_user_message=handler,
    )

    await adapter.on_inbound(
        meta={
            "chat_id": "111111",
            "message_id": "55",
            "user": "luke",
            "user_id": "111111",
            "ts": "2026-04-22T12:00:00Z",
        },
        content="hi eve",
    )
    assert len(captured) == 1
    ev = captured[0]
    assert ev.user_id == "111111"
    assert ev.identity is not None
    assert ev.identity.display_name == "Luke"
    assert ev.authority_class == AuthorityClass.OWNER


@pytest.mark.asyncio
async def test_tg11_recovery_resumes_normal_routing(tmp_access_with_owner: AccessFile) -> None:
    """TG11 — on recovery from outage, the adapter resumes normal
    routing without restart. We simulate outage then recovery by
    flipping the probe state."""
    from loam.telegram_interface.availability import AvailabilityState, ProbeResult

    probe = await _make_probe(available=False)
    fake = FakeMcp()
    mcp = McpReplyClient(invoke_tool=fake.invoke)
    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        mcp_client=mcp,
        in_session_send=lambda t: _noop(),
    )
    # First send during outage → fallback.
    await adapter._default_send("message-1")
    assert len(fake.calls) == 0

    # Recovery: flip probe to available.
    probe._state = AvailabilityState.available
    probe._last_result = ProbeResult(available=True, latency_ms=5.0)

    await adapter._default_send("message-2")
    assert len(fake.calls) == 1
    assert fake.calls[0][1]["text"] == "message-2"


async def _noop() -> None:
    return None
