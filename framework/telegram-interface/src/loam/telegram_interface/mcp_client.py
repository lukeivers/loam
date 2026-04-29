"""Thin wrapper over the MCP `reply`/`react`/`edit_message` tools.

The plugin exposes these as MCP tools on the stdio transport inside a
Claude Code session launched with ``--channels``. Outside such a
session (orchestrator, cron), MCP is unreachable — callers must use
the direct Bot API via ``bot_api.py`` instead.

This module does not own an MCP stdio connection. It receives an
``invoke_tool`` callable that the orchestrator supplies from whatever
it is using to speak MCP on this host. Tests wire a fake. In the
in-session case (primary persona calling), the persona's own tool-
invocation path is what produces calls — this module is the Python-
side shape when the adapter needs to invoke the tool on the persona's
behalf.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable


InvokeToolFn = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class McpReplyClient:
    invoke_tool: InvokeToolFn

    async def reply(
        self,
        *,
        chat_id: str,
        text: str,
        reply_to: str | None = None,
        files: list[str] | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_to is not None:
            args["reply_to"] = reply_to
        if files:
            args["files"] = files
        if format is not None:
            args["format"] = format
        return await self.invoke_tool("reply", args)

    async def react(
        self, *, chat_id: str, message_id: str, emoji: str
    ) -> dict[str, Any]:
        return await self.invoke_tool(
            "react", {"chat_id": chat_id, "message_id": message_id, "emoji": emoji}
        )

    async def edit_message(
        self,
        *,
        chat_id: str,
        message_id: str,
        text: str,
        format: str | None = None,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if format is not None:
            args["format"] = format
        return await self.invoke_tool("edit_message", args)
