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

"""Fallback delivery — in-session stdout and ``~/.loam/attention.md``.

When Telegram is unavailable, a dropped message is forbidden (rule 8
of the research plan constraints). This module implements the two
fallback surfaces:

- In-session: the caller supplies an ``in_session_send`` callable. If
  not provided, in-session delivery is skipped (out-of-session case).
- ``attention.md``: durable surface (hands-off-lifecycle §Q7). Append-
  only; the supervisor and session-start hook already read from this
  path. The adapter writes a single framed entry per fallback event.

Both surfaces receive a framing preamble that names the degraded
state. The framing distinguishes the fallback from a normal message
so the user can tell something is off.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

from . import observability as obs


DEFAULT_ATTENTION_PATH = Path("~/.loam/attention.md").expanduser()


def fallback_preamble(reason: str) -> str:
    return f"[telegram-unavailable: {reason}] delivered via fallback."


async def write_fallback(
    *,
    text: str,
    reason: str,
    attention_path: Path | None = None,
    in_session_send: Callable[[str], Awaitable[None]] | None = None,
    identity: str | None = None,
) -> list[str]:
    """Deliver `text` to every available fallback surface.

    Returns the list of surfaces that accepted the message. Never
    returns an empty list — if both surfaces fail, raises. A dropped
    message is a halt-signal.
    """
    surfaces: list[str] = []
    framed = f"{fallback_preamble(reason)}\n{text}"

    # In-session first (more immediate if user is active).
    if in_session_send is not None:
        try:
            await in_session_send(framed)
            surfaces.append("in_session")
        except Exception:  # noqa: BLE001 — fallback must be robust
            obs.outbound_failed(
                path="in_session_fallback",
                chat_id=None,
                error_class="in_session_send_raised",
                error_code=-1,
            )

    # attention.md always — durable.
    path = Path(attention_path or DEFAULT_ATTENTION_PATH).expanduser()
    try:
        _append_attention(path, text=text, reason=reason, identity=identity)
        surfaces.append("attention_md")
    except Exception:  # noqa: BLE001
        obs.outbound_failed(
            path="attention_md",
            chat_id=None,
            error_class="attention_md_write_failed",
            error_code=-2,
        )

    if not surfaces:
        raise RuntimeError(
            f"both fallback surfaces failed; message dropped (reason={reason!r})"
        )

    obs.fallback_triggered(reason=reason, surfaces=surfaces)
    return surfaces


def _append_attention(
    path: Path, *, text: str, reason: str, identity: str | None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    header = (
        f"\n\n## telegram-fallback @ {now}\n"
        f"reason: {reason}\n"
        + (f"identity: {identity}\n" if identity else "")
        + "message:\n"
    )
    body = "\n".join("  " + ln for ln in text.splitlines())
    with path.open("a") as f:
        f.write(header + body + "\n")
