"""Shared test helpers for the D7 memory-consumer AC suite.

Not a test module — pytest discovers tests by ``test_*`` prefix on
function names, so a module with no ``test_`` functions is inert.
The ``FakeMemoryClient`` below is the deterministic stub every AC
(D7.1–D7.7) binds against — it records calls and lets each test
configure its specific return shape without spinning up a live
memory-system.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable


@dataclass
class SearchCall:
    query: str
    group_ids: list[str] | None
    num_results: int
    center_node_uuid: str | None


@dataclass
class AddEpisodeCall:
    name: str
    body: str
    source_description: str
    reference_time: datetime
    source: str
    group_id: str


@dataclass
class FakeMemoryClient:
    """Protocol-compatible stub for ``MemoryClient`` in AC tests.

    Every method records its call for inspection. ``search_result``
    governs the ``search`` return shape; ``search_raises`` causes
    ``search`` to raise (AC-D7.7). ``add_episode_hold`` is an
    ``asyncio.Event`` — when set, ``add_episode`` blocks on it before
    returning (AC-D7.3).
    """

    search_calls: list[SearchCall] = field(default_factory=list)
    add_episode_calls: list[AddEpisodeCall] = field(default_factory=list)
    search_result: dict[str, Any] = field(
        default_factory=lambda: {"query": "", "results": []}
    )
    search_raises: BaseException | None = None
    add_episode_hold: asyncio.Event | None = None
    add_episode_raises: BaseException | None = None

    async def search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
        center_node_uuid: str | None,
    ) -> dict[str, Any]:
        self.search_calls.append(
            SearchCall(
                query=query,
                group_ids=group_ids,
                num_results=num_results,
                center_node_uuid=center_node_uuid,
            )
        )
        if self.search_raises is not None:
            raise self.search_raises
        return self.search_result

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
        self.add_episode_calls.append(
            AddEpisodeCall(
                name=name,
                body=body,
                source_description=source_description,
                reference_time=reference_time,
                source=source,
                group_id=group_id,
            )
        )
        if self.add_episode_hold is not None:
            # Block until the test releases the hold. Simulates the
            # empirical 113 s per-episode wall-time (AC-D7.3).
            await self.add_episode_hold.wait()
        if self.add_episode_raises is not None:
            raise self.add_episode_raises
        return {
            "episode_uuid": f"fake-{len(self.add_episode_calls)}",
            "nodes_extracted": 0,
            "edges_extracted": 0,
        }


def seed_baseline_workspace(root: Path) -> None:
    """Write a minimal workspace layout the D8 session-builder
    accepts — one baseline corpus file present, so the session-level
    sentinel lands at ``loaded`` and the composer will accept turns.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "## Session-start discipline\n\n- `docs/odd-methodology.md`\n"
    )
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "odd-methodology.md").write_text("x")
