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

"""Token rotation + failure modes — TG20, TG21, TG22.

TG20: on 401 the adapter loud-escalates and routes subsequent messages
      to the fallback until the token is updated.
TG21: on 429 the adapter returns the error to the caller with
      rate-limit classification (grammY handles retry-after at the
      plugin layer; direct-Bot-API path records the 429 and defers).
TG22: on 403 the adapter flags the identity `blocked_at` and does not
      attempt to re-send to that identity until cleared.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.telegram_interface import (
    IPC_TELEGRAM_BLOCKED_BY_USER,
    IPC_TELEGRAM_RATE_LIMITED,
    IPC_TELEGRAM_TOKEN_INVALID,
)
from loam.telegram_interface.adapter import TelegramAdapter
from loam.telegram_interface.allowlist import AccessFile
from loam.telegram_interface.availability import (
    AvailabilityProbe,
    AvailabilityState,
    FailureClass,
    ProbeResult,
)
from loam.telegram_interface.bot_api import BotApiClient, BotApiError


async def _ok() -> ProbeResult:
    return ProbeResult(available=True, latency_ms=1.0)


async def _available_probe() -> AvailabilityProbe:
    probe = AvailabilityProbe(getme_probe=_ok, mcp_tool_probe=None)
    probe._state = AvailabilityState.available
    probe._last_result = ProbeResult(available=True)
    return probe


def _err_transport(error: BotApiError):
    async def fn(method: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise error
    return fn


# TG20 ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_tg20_401_flips_probe_and_routes_to_fallback(
    tmp_access_with_owner: AccessFile, tmp_path: Path
) -> None:
    """TG20 — a 401 from the Bot API flips the probe to unavailable
    and subsequent sends route to fallback until the token is
    rotated. Error-code IPC_TELEGRAM_TOKEN_INVALID (-32102)."""
    probe = await _available_probe()
    err = BotApiError(
        code=IPC_TELEGRAM_TOKEN_INVALID,
        message="Unauthorized",
        failure_class=FailureClass.token_invalid,
    )
    bot = BotApiClient(transport=_err_transport(err))

    in_session: list[str] = []

    async def in_sess(t: str) -> None:
        in_session.append(t)

    attn = tmp_path / "attention.md"
    import loam.telegram_interface.fallback as fb
    fb.DEFAULT_ATTENTION_PATH = attn

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        bot_api=bot,
        in_session_send=in_sess,
    )
    # First send — transport raises 401 → fallback + flip.
    await adapter._default_send("escalation")
    assert probe.current is False
    assert probe.last_failure_class == FailureClass.token_invalid

    # Second send — cached flag is unavailable → straight to fallback.
    await adapter._default_send("another escalation")
    assert any("token_invalid" in msg for msg in in_session)


# TG21 ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_tg21_429_flagged_as_rate_limited(
    tmp_access_with_owner: AccessFile, tmp_path: Path
) -> None:
    """TG21 — a 429 response from the Bot API is classified as
    rate_limited; adapter routes to fallback and records the
    failure class for the loud-escalation timer."""
    probe = await _available_probe()
    err = BotApiError(
        code=IPC_TELEGRAM_RATE_LIMITED,
        message="Too Many Requests",
        failure_class=FailureClass.rate_limited,
    )
    bot = BotApiClient(transport=_err_transport(err))

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        bot_api=bot,
        in_session_send=lambda t: _noop(),
    )
    attn = tmp_path / "attention.md"
    import loam.telegram_interface.fallback as fb
    fb.DEFAULT_ATTENTION_PATH = attn

    await adapter._default_send("rate-limited content")
    assert probe.last_failure_class == FailureClass.rate_limited


async def _noop() -> None:
    return None


# TG22 ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_tg22_403_marks_identity_blocked(
    tmp_access_with_owner: AccessFile, tmp_path: Path
) -> None:
    """TG22 — a 403 (user blocked the bot) to a specific chat_id
    flags that identity `blocked_at`; subsequent messages to that
    identity do not retry over the Bot API until the block is
    cleared."""
    probe = await _available_probe()
    err = BotApiError(
        code=IPC_TELEGRAM_BLOCKED_BY_USER,
        message="Forbidden: bot was blocked",
        failure_class=FailureClass.blocked_by_user,
    )
    bot = BotApiClient(transport=_err_transport(err))

    attn = tmp_path / "attention.md"
    import loam.telegram_interface.fallback as fb
    fb.DEFAULT_ATTENTION_PATH = attn

    adapter = TelegramAdapter(
        availability=probe,
        access=tmp_access_with_owner,
        bot_api=bot,
        in_session_send=lambda t: _noop(),
    )
    await adapter._default_send("ping")
    identity = tmp_access_with_owner.lookup("111111")
    assert identity is not None
    assert identity.blocked_at is not None
