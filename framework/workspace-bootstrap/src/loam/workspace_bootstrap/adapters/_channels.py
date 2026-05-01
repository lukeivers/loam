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

"""Notification channel defaults.

Adapters that need a notification channel (safety, reversibility,
cost, self-correction) read one of:

  1. `host.channel_registry["<adapter_name>"]` — workspace-registered
     channel overrides the default.
  2. A no-op terminal channel with a captured-list `send` hook (used
     by tests and as a sensible default for headless workspaces).

The channel kind is `ChannelKind.terminal` for the default because the
one-on-one invariant (not a group channel) holds for a local shell
audience.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel


def default_send() -> Callable[[str], Coroutine[Any, Any, None]]:
    async def _send(text: str) -> None:
        # Default is silent. Workspaces that want a real channel
        # register one via host.channel_registry.
        return None

    return _send


def resolve_channel(host: Any, name: str, channel_cls: type, **extra: Any) -> Any:
    """Look up a channel in host.channel_registry or construct a default.

    `channel_cls` is the safety/reversibility/cost-specific subclass;
    the default construction provides kind+name+send+is_active and
    `extra` for subclass-specific fields (currently none).
    """
    existing = host.channel_registry.get(name)
    if existing is not None:
        return existing
    ch = channel_cls(
        kind=ChannelKind.terminal,
        name=name,
        send=default_send(),
        is_active=True,
        **extra,
    )
    host.channel_registry[name] = ch
    return ch
