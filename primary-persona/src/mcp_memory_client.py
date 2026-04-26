"""Live MCP memory-client adapter (amendment #48 / D1 / D5 / D9).

Constructs a ``MemoryClient``-Protocol-conforming object backed by a
streamable-HTTP MCP client speaking to the workspace's local
memory-graphiti FastMCP service. The URL is read from
``<workspace>/.mcp.json`` (authored by amendment #47's
``write_mcp_json`` writer); no other discovery surface is used.

Per the locked plan (§6 D1), this module exposes:

  - :class:`LiveMCPMemoryClient` — Protocol-shape adapter.
  - :func:`build_live_mcp_memory_client` — factory used by the
    persona's ``_default_memory_client_factory`` to lift the
    pre-#48 ``return None`` to a live client.

Per-call MCP handshake: each ``search`` / ``add_episode`` opens
``streamablehttp_client(url)`` → ``ClientSession.initialize()`` →
``call_tool("search" | "add_episode", arguments)`` and closes the
session. No connection pooling (plan §9 explicit out-of-scope).

Fail-direction (AC.M.1 vs AC.M.3 vs AC.M.10):

  - ``build_live_mcp_memory_client`` returns ``None`` when the
    workspace's ``.mcp.json`` is missing / malformed / lacks the
    ``memory-graphiti`` entry. Callers (the persona's session-start
    factory) then leave the contributor unregistered — the
    ``_default_memory_client_factory`` already swallows ``None``
    and proceeds with the AC46.2 graceful-empty turn-payload shape.
  - When the live client is constructed but the per-call MCP round
    trip fails (service down, timeout, protocol error), the call
    raises. The retrieval-time call site (``build_memory_retrieval_
    contributor`` in ``memory_consumer.py``) is fail-closed per
    AC-D7.7 — the exception turns into an empty retrieval block.
    The write-time call site (``cli_memory_write`` in
    ``stop_emitter.py``) catches and logs to the workspace-local
    diagnostic log (AC.M.10).

Per ODD §2.5 every code path traces back to AC.M.1 / AC.M.3 / AC.M.10.
The ``return None`` branches in ``build_live_mcp_memory_client`` are
explicitly AC.M.3-backed (graceful-empty when the substrate is not
ready).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .memory_consumer import MemoryClient


# ---- public constants -----------------------------------------------


MCP_JSON_FILENAME = ".mcp.json"
MEMORY_GRAPHITI_SERVER_NAME = "memory-graphiti"


# ---- URL discovery (AC.M.1 / AC.M.3) --------------------------------


def _read_memory_graphiti_url(workspace_root: Path) -> str | None:
    """Return the streamable-HTTP URL for the workspace's
    memory-graphiti MCP service, or ``None`` when the substrate is
    not present or recognisable.

    AC.M.3 graceful-empty: every malformed-substrate branch lands
    here. The caller (``build_live_mcp_memory_client``) treats
    ``None`` as "do not construct a live client".
    """
    path = Path(workspace_root) / MCP_JSON_FILENAME
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return None
    entry = servers.get(MEMORY_GRAPHITI_SERVER_NAME)
    if not isinstance(entry, dict):
        return None
    url = entry.get("url")
    if not isinstance(url, str) or not url.strip():
        return None
    return url


# ---- live client adapter (AC.M.1) -----------------------------------


class LiveMCPMemoryClient:
    """``MemoryClient`` Protocol adapter backed by streamable-HTTP MCP.

    Per-call session lifecycle: each :meth:`search` / :meth:`add_episode`
    opens a fresh streamable-HTTP transport + ``ClientSession``, runs
    one tool call, and closes. The MCP package handles framing;
    we own the JSON-shape contract that AC.M.1 measures.

    The Protocol is defined in
    ``primary_persona.memory_consumer.MemoryClient`` (sealed since
    amendment #33). This adapter satisfies it duck-typed; the
    Protocol's ``...`` method bodies tolerate any sync/async return
    that yields the documented dict shape.
    """

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    async def search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
        center_node_uuid: str | None,
    ) -> dict[str, Any]:
        """Issue ``search`` against the live memory-graphiti service.

        AC.M.1 + AC-D7.4: returns the documented ``{"query": str,
        "results": list}`` shape verbatim. Raises on transport / MCP
        protocol failure; the contributor at the call site is
        responsible for fail-closed semantics (AC-D7.7 / AC.M.3).
        """
        arguments: dict[str, Any] = {
            "query": query,
            "num_results": num_results,
        }
        if group_ids is not None:
            arguments["group_ids"] = group_ids
        if center_node_uuid is not None:
            arguments["center_node_uuid"] = center_node_uuid
        return await self._call_tool("search", arguments)

    async def add_episode(
        self,
        *,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        source: str,
        group_id: str,
    ) -> dict[str, Any]:
        """Issue ``add_episode`` against the live memory-graphiti
        service.

        AC.M.1 + AC.M.6 + AC-D7.4: returns the documented
        ``{"episode_uuid", "nodes_extracted", "edges_extracted"}``
        dict shape. ``reference_time`` is serialised via
        ``isoformat()`` to match the FastMCP wrapper's
        ``datetime.fromisoformat`` parse path.
        """
        arguments: dict[str, Any] = {
            "name": name,
            "body": body,
            "source_description": source_description,
            "reference_time": reference_time.isoformat(),
            "source": source,
            "group_id": group_id,
        }
        return await self._call_tool("add_episode", arguments)

    async def _call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Open a streamable-HTTP MCP session, call ``tool_name``,
        close. Returns the tool's structured-content dict.

        Imports are lazy so this module's import-time surface stays
        cheap (mcp pulls anyio / httpx / pydantic-settings, etc.) —
        consumers that fail-soft never pay the cost.
        """
        # Lazy import: keep import-time surface narrow.
        from mcp.client.session import ClientSession  # noqa: WPS433
        from mcp.client.streamable_http import (  # noqa: WPS433
            streamable_http_client,
        )

        async with streamable_http_client(self._url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
        return _extract_structured_content(result)


def _extract_structured_content(result: Any) -> dict[str, Any]:
    """Pull a ``dict`` payload out of an MCP ``CallToolResult``.

    FastMCP encodes ``_impl_*`` dict returns as ``structuredContent``
    on the response. When ``structuredContent`` is absent (older
    servers, or a manual-content response) we fall back to parsing
    the first textual content as JSON. Either path raises on
    unexpected shape — the surrounding fail-soft contract (AC.M.3 /
    AC.M.10) absorbs the exception at the consumer's boundary.
    """
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    content = getattr(result, "content", None)
    if isinstance(content, list):
        for item in content:
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
    raise ValueError(
        "mcp-tool-result-missing-structured-content"
    )


# ---- factory entry point (D1) ---------------------------------------


def build_live_mcp_memory_client(
    workspace_root: Path,
) -> MemoryClient | None:
    """Return a live MCP memory-client, or ``None`` when the
    workspace's substrate is not ready.

    AC.M.1: when ``<workspace>/.mcp.json`` exists and carries a
    well-formed ``memory-graphiti`` entry, the returned object
    satisfies the ``MemoryClient`` Protocol against the live
    service.

    AC.M.3 graceful-empty: every malformed-substrate branch
    returns ``None``. The persona's session-start factory then
    leaves the memory-retrieval contributor unregistered, and the
    turn payload omits the retrieval block — pre-#48 production
    behaviour preserved.

    Per ODD §2.5 the only branches in this function are the
    AC.M.3-backed ``return None`` branches (delegated to
    ``_read_memory_graphiti_url``) and the success-path
    instantiation.
    """
    url = _read_memory_graphiti_url(Path(workspace_root))
    if url is None:
        return None
    return LiveMCPMemoryClient(url)
