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

"""AC.MPF.5 — TurnAggregator writes with group_id=workspace_slug.

Outcome (per locked plan §4 AC.MPF.5): the persona's write path
invokes ``add_episode`` with ``group_id`` equal to the workspace_slug
exactly. This is the regression-prevention check for the
write/read group_id convention alignment Fix #5: write-side adopts
``workspace_slug``; the persona's read-side already queries with
``group_ids=[workspace_slug]`` — the two paths agree by construction.

Convention documented in ``memory_consumer.py`` module docstring.

(The orphan ``pos-v2_default`` data the diagnostic surfaced was
written by a verification path that bypassed the persona surface;
this test pins the persona's invariant so a future write-path
addition can't drift.)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from loam.primary_persona.memory_consumer import TurnAggregator


class _RecordingMemoryClient:
    """FakeMemoryClient that records every ``add_episode`` invocation."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"name": kwargs["name"]}

    async def search(self, **kwargs: Any) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


@pytest.mark.asyncio
async def test_AC_MPF_5_close_turn_writes_with_workspace_slug_group_id() -> None:
    client = _RecordingMemoryClient()
    aggregator = TurnAggregator(
        memory_client=client, workspace_slug="my-workspace-slug"
    )
    task = aggregator.close_turn(
        turn_id="t1",
        user_message="hello",
        persona_reply="hi back",
        reference_time=datetime.now(timezone.utc),
    )
    await task
    assert len(client.calls) == 1
    call = client.calls[0]
    # The load-bearing invariant: group_id matches workspace_slug.
    assert call["group_id"] == "my-workspace-slug"
    # Other invariants the dispatch's "no other source change for Fix
    # #5" decision rests on: name carries turn_id; body contains both
    # user message + persona reply.
    assert call["name"] == "turn/t1"
    assert "hello" in call["body"]
    assert "hi back" in call["body"]


@pytest.mark.asyncio
async def test_AC_MPF_5_group_id_does_not_drift_to_default_scope_id() -> None:
    """Regression-prevention: confirm ``group_id`` is NOT
    "pos-v2_default" (memory-system's mock-scope fallback per
    memory.yml:72) — that's the orphan-data group_id the diagnostic
    surfaced. The persona's write path must use the workspace-slug
    surface exclusively.
    """
    client = _RecordingMemoryClient()
    aggregator = TurnAggregator(
        memory_client=client, workspace_slug="pos3"
    )
    await aggregator.close_turn(
        turn_id="t1",
        user_message="u",
        persona_reply="r",
    )
    assert client.calls[0]["group_id"] != "pos-v2_default"
    assert client.calls[0]["group_id"] == "pos3"


@pytest.mark.asyncio
async def test_AC_MPF_5_group_id_matches_resolve_workspace_slug() -> None:
    """When the workspace_slug is computed via
    ``resolve_workspace_slug``, the value flows through to
    ``add_episode`` unchanged.
    """
    from pathlib import Path

    from loam.primary_persona.memory_consumer import resolve_workspace_slug

    slug = resolve_workspace_slug(Path("/Users/luke/MyProject"))
    client = _RecordingMemoryClient()
    aggregator = TurnAggregator(memory_client=client, workspace_slug=slug)
    await aggregator.close_turn(
        turn_id="t1", user_message="u", persona_reply="r"
    )
    assert client.calls[0]["group_id"] == slug
    assert client.calls[0]["group_id"] == "myproject"
