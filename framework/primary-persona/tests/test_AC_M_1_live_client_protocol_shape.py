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

"""AC.M.1 — Live MCP client returns a usable MemoryClient.

Outcome (per locked plan §5 / §6 D1): when ``<workspace>/.mcp.json``
carries a well-formed ``memory-graphiti`` entry, the persona's
``build_live_mcp_memory_client(workspace_root)`` returns a non-None
adapter that satisfies the existing ``MemoryClient`` Protocol —
``await client.search(...)`` returns the documented
``{"query", "results"}`` shape and ``await client.add_episode(...)``
returns the documented ``{"episode_uuid", "nodes_extracted",
"edges_extracted"}`` shape.

Determinism: the live MCP service is not started inside the test;
instead we spin up an in-process FastMCP server bound to a free
local port, write a matching ``.mcp.json``, and exercise the live
adapter against that. This keeps the test hermetic but proves the
adapter speaks streamable-HTTP MCP correctly. Per ODD §2.5: the
test backs AC.M.1's "outcome shape" — not method.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_fake_memory_graphiti(port: int) -> threading.Thread:
    """Spin up an in-process FastMCP server emulating the
    memory-graphiti service surface (``search`` + ``add_episode``
    tools returning the documented dict shapes).
    """
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("fake-memory-graphiti", host="127.0.0.1", port=port)

    @server.tool()
    async def search(
        query: str,
        group_ids: list[str] | None = None,
        num_results: int = 10,
        center_node_uuid: str | None = None,
    ) -> dict[str, Any]:
        return {
            "query": query,
            "results": [
                {
                    "fact": f"echoed:{query}",
                    "edge_uuid": "edge-1",
                    "valid_at": None,
                    "invalid_at": None,
                    "source_node_uuid": "n1",
                    "target_node_uuid": "n2",
                }
            ],
        }

    @server.tool()
    async def add_episode(
        name: str,
        body: str,
        source_description: str = "synthetic",
        reference_time: str | None = None,
        source: str = "text",
        group_id: str = "default",
    ) -> dict[str, Any]:
        return {
            "episode_uuid": f"ep-{name}",
            "nodes_extracted": 0,
            "edges_extracted": 0,
        }

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(server.run_streamable_http_async())
        except Exception:
            pass

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    return th


def _wait_for_port(port: int, timeout: float = 5.0) -> None:
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"fake memory-graphiti did not bind to {port}")


def _seed_mcp_json(workspace_root: Path, port: int) -> None:
    (workspace_root / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "memory-graphiti": {
                        "type": "http",
                        "url": f"http://127.0.0.1:{port}/mcp",
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.fixture(scope="module")
def fake_memory_graphiti():
    port = _free_port()
    _start_fake_memory_graphiti(port)
    _wait_for_port(port)
    yield port


def test_AC_M_1_factory_returns_non_none_for_well_formed_mcp_json(
    tmp_path: Path, fake_memory_graphiti: int
) -> None:
    """When ``.mcp.json`` is present and well-formed, the factory
    returns a non-None client object."""
    from loam.primary_persona.mcp_memory_client import build_live_mcp_memory_client

    _seed_mcp_json(tmp_path, fake_memory_graphiti)
    client = build_live_mcp_memory_client(tmp_path)
    assert client is not None


def test_AC_M_1_factory_returns_none_when_mcp_json_missing(
    tmp_path: Path,
) -> None:
    """AC.M.3 graceful-empty: no .mcp.json → factory returns None."""
    from loam.primary_persona.mcp_memory_client import build_live_mcp_memory_client

    client = build_live_mcp_memory_client(tmp_path)
    assert client is None


def test_AC_M_1_factory_returns_none_when_mcp_json_malformed(
    tmp_path: Path,
) -> None:
    """AC.M.3 graceful-empty: malformed JSON → factory returns None."""
    from loam.primary_persona.mcp_memory_client import build_live_mcp_memory_client

    (tmp_path / ".mcp.json").write_text("not json", encoding="utf-8")
    client = build_live_mcp_memory_client(tmp_path)
    assert client is None


def test_AC_M_1_factory_returns_none_when_entry_missing(
    tmp_path: Path,
) -> None:
    """AC.M.3 graceful-empty: no memory-graphiti entry → None."""
    from loam.primary_persona.mcp_memory_client import build_live_mcp_memory_client

    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"other": {"type": "http", "url": "x"}}}),
        encoding="utf-8",
    )
    client = build_live_mcp_memory_client(tmp_path)
    assert client is None


def test_AC_M_1_search_returns_documented_shape(
    tmp_path: Path, fake_memory_graphiti: int
) -> None:
    """AC.M.1 outcome: ``await client.search(...)`` against the
    live service returns ``{"query": str, "results": list}``."""
    from loam.primary_persona.mcp_memory_client import build_live_mcp_memory_client

    _seed_mcp_json(tmp_path, fake_memory_graphiti)
    client = build_live_mcp_memory_client(tmp_path)
    assert client is not None
    result = asyncio.run(
        client.search(
            query="hello",
            group_ids=["test-slug"],
            num_results=5,
            center_node_uuid=None,
        )
    )
    assert isinstance(result, dict)
    assert result.get("query") == "hello"
    assert isinstance(result.get("results"), list)
    assert result["results"], "fake server seeded one result"
    assert result["results"][0]["fact"] == "echoed:hello"


def test_AC_M_1_add_episode_returns_documented_shape(
    tmp_path: Path, fake_memory_graphiti: int
) -> None:
    """AC.M.1 outcome: ``await client.add_episode(...)`` returns
    ``{"episode_uuid", "nodes_extracted", "edges_extracted"}``."""
    from loam.primary_persona.mcp_memory_client import build_live_mcp_memory_client

    _seed_mcp_json(tmp_path, fake_memory_graphiti)
    client = build_live_mcp_memory_client(tmp_path)
    assert client is not None
    result = asyncio.run(
        client.add_episode(
            name="turn/abc",
            body="[user]\nhi\n\n[persona]\nhello\n",
            source_description="primary-persona turn",
            reference_time=datetime.now(timezone.utc),
            source="message",
            group_id="test-slug",
        )
    )
    assert isinstance(result, dict)
    assert "episode_uuid" in result
    assert "nodes_extracted" in result
    assert "edges_extracted" in result
    assert result["episode_uuid"] == "ep-turn/abc"
