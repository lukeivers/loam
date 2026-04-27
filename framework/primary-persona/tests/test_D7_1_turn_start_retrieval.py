"""AC-D7.1 — turn-start retrieval lands in UserPromptSubmit
additionalContext.

Outcome (from amendment #33 plan §4 AC-D7.1): given the primary-
persona layer loaded against a workspace whose memory service is
reachable and has at least one prior episode under the workspace's
``group_id``, a UserPromptSubmit event for a user message causes the
layer's ``additionalContext`` output to include a memory-retrieval
block whose contents are the result of issuing a query against
memory-system with the workspace's ``group_id`` in its ``group_ids``
filter.
"""

from __future__ import annotations

from pathlib import Path

from src.context_composer import ComposedContextPayload
from src.memory_consumer import register_memory_retrieval, resolve_workspace_slug
from src.session_start_gate import compose_session_fields

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


def test_D7_1_turn_start_retrieval_reaches_additional_context(tmp_path: Path) -> None:
    """Seed memory with one episode under the workspace slug; fire
    ``on_user_prompt_submit``; assert the emitted additionalContext
    contains the retrieval block and the search call carried the
    workspace slug in ``group_ids``."""
    workspace_root = tmp_path / "my-demo-workspace"
    seed_baseline_workspace(workspace_root)

    slug = resolve_workspace_slug(workspace_root)

    # FakeMemoryClient returns one recorded edge — the "prior episode"
    # the AC's precondition demands.
    client = FakeMemoryClient(
        search_result={
            "query": "what did we decide about feature X?",
            "results": [
                {
                    "fact": "owner decided to ship feature X v1 this quarter",
                    "edge_uuid": "edge-1",
                    "valid_at": None,
                    "invalid_at": None,
                    "source_node_uuid": "n-1",
                    "target_node_uuid": "n-2",
                },
            ],
        }
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_memory_retrieval(
        composer,
        memory_client=client,
        workspace_slug=slug,
    )
    composer.on_session_start(workspace_root)
    turn = composer.on_user_prompt_submit(
        prompt="what did we decide about feature X?"
    )

    # The memory-retrieval contribution is in the turn payload.
    names = dict(turn.contributor_outputs)
    assert "memory-retrieval" in names
    assert "owner decided to ship feature X v1" in names["memory-retrieval"]

    # Same contribution surfaces in the serialised additionalContext.
    assert "owner decided to ship feature X v1" in turn.additional_context_text

    # The search call was issued with the workspace slug in
    # group_ids (the precondition for per-workspace retrieval).
    assert len(client.search_calls) == 1
    call = client.search_calls[0]
    assert call.group_ids == [slug]
    assert call.query == "what did we decide about feature X?"
