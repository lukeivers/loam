"""AC-D7.3 — interactive turn is not blocked on the memory write.

Outcome (from amendment #33 plan §4 AC-D7.3): given a fake memory
boundary whose ``add_episode`` blocks for a configurable duration
(simulating the empirical 113 s), the user's next turn may begin
without waiting for the prior turn's memory write to complete.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from loam.primary_persona.context_composer import ComposedContextPayload
from loam.primary_persona.memory_consumer import (
    TurnAggregator,
    register_memory_retrieval,
    resolve_workspace_slug,
)
from loam.primary_persona.session_start_gate import compose_session_fields

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


@pytest.mark.asyncio
async def test_D7_3_next_turn_proceeds_while_write_pending(tmp_path: Path) -> None:
    """Turn 1's ``add_episode`` blocks indefinitely; turn 2's
    ``on_user_prompt_submit`` must still return promptly."""
    workspace_root = tmp_path / "latency-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    # Hold: the ``add_episode`` coroutine blocks on this event until
    # the test releases it at the end. This simulates the 113 s
    # empirical cost without actually waiting.
    hold = asyncio.Event()
    client = FakeMemoryClient(add_episode_hold=hold)

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )
    composer.on_session_start(workspace_root)

    agg = TurnAggregator(memory_client=client, workspace_slug=slug)

    # Turn 1: user message + reply. Close the turn — write is
    # scheduled via asyncio.create_task; we do NOT await it.
    write_task = agg.close_turn(
        turn_id="turn-1",
        user_message="start something long",
        persona_reply="on it",
    )

    # At least one tick so the create_task scheduler reaches the
    # blocking await inside add_episode. Asyncio's create_task is
    # scheduled for the next tick but not yet running.
    await asyncio.sleep(0)
    assert len(client.add_episode_calls) == 1
    assert not write_task.done(), (
        "the write must still be pending — the hold event is unset"
    )

    # Turn 2: fire UserPromptSubmit while the turn-1 write is
    # outstanding. This MUST return promptly (AC-D7.3).
    t0 = time.monotonic()
    turn_2_payload = composer.on_user_prompt_submit(prompt="turn 2 question")
    elapsed = time.monotonic() - t0

    assert turn_2_payload is not None
    # Generous budget — the test proves "well under 1 s" for a
    # retrieval path against an unblocked FakeMemoryClient.search
    # while an add_episode is still held.
    assert elapsed < 1.0, (
        f"on_user_prompt_submit took {elapsed:.3f}s while a prior "
        f"write was pending; AC-D7.3 requires non-blocking"
    )

    # The held task is still pending — the interactive path did not
    # wait on it.
    assert not write_task.done()

    # Release the hold so the task can complete cleanly before the
    # test loop tears down.
    hold.set()
    await write_task
