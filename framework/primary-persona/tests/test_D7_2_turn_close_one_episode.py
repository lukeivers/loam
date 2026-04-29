"""AC-D7.2 — turn-close writes exactly one aggregated episode per
user↔AI turn.

Outcome (from amendment #33 plan §4 AC-D7.2): given a completed
user↔AI turn, the primary-persona layer causes exactly one memory-
system episode to be persisted for that turn — not zero, not two,
not per-message, not per-state-event. A multi-turn fixture produces
one call per turn.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from loam.primary_persona.memory_consumer import TurnAggregator, resolve_workspace_slug

from _helpers_d7 import FakeMemoryClient


@pytest.mark.asyncio
async def test_D7_2_single_turn_writes_exactly_one_episode(tmp_path: Path) -> None:
    """One turn → one add_episode call with the workspace slug and a
    body containing both the user message and the persona reply."""
    workspace_root = tmp_path / "scratch-ws"
    slug = resolve_workspace_slug(workspace_root)
    client = FakeMemoryClient()
    agg = TurnAggregator(memory_client=client, workspace_slug=slug)

    task = agg.close_turn(
        turn_id="t1",
        user_message="Hey, please summarise the Q3 review notes.",
        persona_reply="Sure — the top three takeaways were ...",
    )
    # Await the task to let the write complete (production code
    # fire-and-forgets; AC-D7.3 verifies non-blocking).
    await task

    assert len(client.add_episode_calls) == 1
    call = client.add_episode_calls[0]
    assert call.group_id == slug
    # Body captures both the user message and the persona reply in a
    # single payload (AC-D7.2 structural membership check).
    assert "Q3 review notes" in call.body
    assert "top three takeaways" in call.body
    # Single episode, not per-message (so source is not "message-per
    # message" — the test asserts one call, not a structural source
    # type).


@pytest.mark.asyncio
async def test_D7_2_multi_turn_produces_one_call_per_turn(tmp_path: Path) -> None:
    """Three turns → three add_episode calls — not two, not six."""
    workspace_root = tmp_path / "multi-turn-ws"
    slug = resolve_workspace_slug(workspace_root)
    client = FakeMemoryClient()
    agg = TurnAggregator(memory_client=client, workspace_slug=slug)

    tasks = [
        agg.close_turn(
            turn_id=f"t{n}",
            user_message=f"user msg {n}",
            persona_reply=f"persona reply {n}",
        )
        for n in range(3)
    ]
    await asyncio.gather(*tasks)

    assert len(client.add_episode_calls) == 3
    # Every call carries the workspace slug.
    assert {call.group_id for call in client.add_episode_calls} == {slug}
    # Each turn's aggregated body pairs its own user message with its
    # own persona reply (AC-D7.2 aggregation semantics).
    for n, call in enumerate(client.add_episode_calls):
        assert f"user msg {n}" in call.body
        assert f"persona reply {n}" in call.body
