"""AC-D7.7 — memory unavailable at retrieval does not fail the turn.

Outcome (from amendment #33 plan §4 AC-D7.7): given the memory
service unreachable (connection refused, HTTP 5xx, or a simulated
timeout) at turn-start retrieval, the ``UserPromptSubmit`` path still
emits a valid ``additionalContext`` payload and the turn proceeds.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.context_composer import ComposedContextPayload
from src.memory_consumer import register_memory_retrieval, resolve_workspace_slug
from src.session_start_gate import compose_session_fields

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


@pytest.mark.parametrize(
    "failure",
    [
        ConnectionRefusedError("connection refused"),
        RuntimeError("HTTP 503: memory sidecar unavailable"),
        asyncio.TimeoutError(),
        OSError("socket closed"),
    ],
)
def test_D7_7_any_boundary_failure_fails_closed(
    tmp_path: Path, failure: BaseException
) -> None:
    """Stub the memory boundary to raise on ``search``; fire
    ``on_user_prompt_submit``; assert no exception reaches the hook-
    level caller and the turn payload emits with an empty memory-
    retrieval contribution."""
    workspace_root = tmp_path / "fail-closed-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    client = FakeMemoryClient(search_raises=failure)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )
    composer.on_session_start(workspace_root)

    # Must NOT raise — this is the AC's primary assertion.
    turn = composer.on_user_prompt_submit(prompt="anything")

    # The memory-retrieval contribution is present but empty (fail-
    # closed per plan §3 constraint 8).
    outputs = dict(turn.contributor_outputs)
    assert outputs.get("memory-retrieval") == ""

    # The turn payload still emits — a valid additionalContext that
    # downstream consumers can read.
    assert turn.additional_context_text  # non-empty (session sentinel etc.)


def test_D7_7_awareness_path_unaffected_by_memory_failure(
    tmp_path: Path,
) -> None:
    """AC-D7.7 closing clause: the awareness-block path is
    unaffected. We stand in a synthetic awareness contributor
    alongside the failing memory contributor; the awareness output
    survives.
    """
    from typing import Any

    from src.context_composer import TriggerKind

    workspace_root = tmp_path / "awareness-survives-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    def awareness(ctx: dict[str, Any]) -> str:
        return "awareness-survives"

    client = FakeMemoryClient(search_raises=RuntimeError("boom"))
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    composer.register(
        name="awareness",
        trigger_kind=TriggerKind.turn,
        fn=awareness,
    )
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )
    composer.on_session_start(workspace_root)

    turn = composer.on_user_prompt_submit(prompt="hi")

    outputs = dict(turn.contributor_outputs)
    assert outputs.get("awareness") == "awareness-survives"
    assert outputs.get("memory-retrieval") == ""
    # Awareness output visible in serialised text.
    assert "awareness-survives" in turn.additional_context_text
