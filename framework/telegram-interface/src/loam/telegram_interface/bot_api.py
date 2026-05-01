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

"""Direct Telegram Bot API fallback for out-of-session callers.

Orchestrator processes, cron jobs, and any caller that is NOT inside a
Claude Code MCP session cannot invoke the plugin's MCP tools. The
direct Bot API path is used in that case. Token is read from
``~/.claude/channels/telegram/.env``; target ``chat_id`` is resolved
from the allowlist (the owner is the first entry or the ``owner``-
authority-class identity in ``pos_identities``).

Only the `sendMessage` and `getMe` endpoints are implemented here —
the minimal surface needed for (a) out-of-session system-initiated
messages, (b) the availability probe, and (c) the round-trip verify
at the end of the setup walkthrough.

Pure stdlib transport (``urllib.request``). The `httpx` dependency
listed in the brief's permitted-deps is available but the retry/
timeout discipline here is simple enough that stdlib is cleaner.
"""

from __future__ import annotations

import asyncio
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import (
    IPC_TELEGRAM_BLOCKED_BY_USER,
    IPC_TELEGRAM_RATE_LIMITED,
    IPC_TELEGRAM_SEND_FAILED,
    IPC_TELEGRAM_TOKEN_INVALID,
)
from . import observability as obs
from .availability import FailureClass, ProbeResult


DEFAULT_ENV_PATH = Path("~/.claude/channels/telegram/.env").expanduser()
API_BASE = "https://api.telegram.org"
DEFAULT_TIMEOUT_S = 5.0


class BotApiError(Exception):
    def __init__(self, *, code: int, message: str, failure_class: FailureClass):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.failure_class = failure_class


def load_token(env_path: Path | None = None) -> str | None:
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return os.environ["TELEGRAM_BOT_TOKEN"]
    p = Path(env_path or DEFAULT_ENV_PATH).expanduser()
    if not p.exists():
        return None
    try:
        for line in p.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or not line or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "TELEGRAM_BOT_TOKEN":
                return value.strip().strip('"').strip("'") or None
    except OSError:
        return None
    return None


@dataclass
class BotApiClient:
    env_path: Path | None = None
    timeout_s: float = DEFAULT_TIMEOUT_S
    # Injection seam for tests. Real transport is urllib.
    transport: Any | None = None

    def _token(self) -> str:
        tok = load_token(self.env_path)
        if not tok:
            raise BotApiError(
                code=IPC_TELEGRAM_TOKEN_INVALID,
                message="TELEGRAM_BOT_TOKEN not configured",
                failure_class=FailureClass.token_missing,
            )
        return tok

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        parse_mode: str | None = None,
        reply_to: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode
        if reply_to is not None:
            payload["reply_to_message_id"] = reply_to
        try:
            resp = await self._post("sendMessage", payload)
        except BotApiError as e:
            obs.outbound_failed(
                path="bot_api",
                chat_id=chat_id,
                error_class=e.failure_class.value,
                error_code=e.code,
            )
            raise
        obs.outbound_sent(
            path="bot_api",
            chat_id=chat_id,
            identity=None,
            bytes_sent=len(text.encode("utf-8")),
        )
        return resp

    async def get_me(self) -> ProbeResult:
        started = time.perf_counter()
        try:
            await self._post("getMe", {})
        except BotApiError as e:
            return ProbeResult(
                available=False,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                failure_class=e.failure_class,
                detail=e.message,
            )
        return ProbeResult(
            available=True,
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )

    async def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.transport is not None:
            return await self.transport(method, payload)
        token = self._token()
        url = f"{API_BASE}/bot{token}/{method}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        loop = asyncio.get_running_loop()
        ctx = ssl.create_default_context()

        def _do() -> dict[str, Any]:
            try:
                with urllib.request.urlopen(
                    req, timeout=self.timeout_s, context=ctx
                ) as resp:
                    body = resp.read().decode("utf-8")
                    parsed = json.loads(body)
                    if not parsed.get("ok"):
                        raise _classify_error(parsed)
                    return parsed.get("result", {})
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode("utf-8")
                    parsed = json.loads(body) if body else {}
                except Exception:
                    parsed = {}
                raise _classify_http_error(e.code, parsed)
            except urllib.error.URLError as e:
                raise BotApiError(
                    code=IPC_TELEGRAM_SEND_FAILED,
                    message=f"transport: {e.reason}",
                    failure_class=FailureClass.api_unreachable,
                )

        return await loop.run_in_executor(None, _do)


def _classify_http_error(status: int, parsed: dict[str, Any]) -> BotApiError:
    description = parsed.get("description") or f"HTTP {status}"
    if status == 401:
        return BotApiError(
            code=IPC_TELEGRAM_TOKEN_INVALID,
            message=description,
            failure_class=FailureClass.token_invalid,
        )
    if status == 403:
        return BotApiError(
            code=IPC_TELEGRAM_BLOCKED_BY_USER,
            message=description,
            failure_class=FailureClass.blocked_by_user,
        )
    if status == 429:
        return BotApiError(
            code=IPC_TELEGRAM_RATE_LIMITED,
            message=description,
            failure_class=FailureClass.rate_limited,
        )
    return BotApiError(
        code=IPC_TELEGRAM_SEND_FAILED,
        message=description,
        failure_class=FailureClass.api_unreachable,
    )


def _classify_error(parsed: dict[str, Any]) -> BotApiError:
    code = int(parsed.get("error_code") or 0)
    return _classify_http_error(code, parsed)
