"""AC-D7.6 — retrieval payload respects the persona layer's payload
cap.

Outcome (from amendment #33 plan §4 AC-D7.6): the combined
``UserPromptSubmit`` ``additionalContext`` output of the memory-
retrieval contributor plus the existing D3 awareness-block
contributor does not exceed the primary-persona layer's declared
cap (the composer's 10 000-char structural refusal per D8).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.context_composer import (
    ADDITIONAL_CONTEXT_CAP,
    ComposedContextPayload,
    TriggerKind,
)
from src.memory_consumer import (
    MEMORY_RETRIEVAL_CHAR_CAP,
    register_memory_retrieval,
    resolve_workspace_slug,
)
from src.session_start_gate import compose_session_fields

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


def test_D7_6_retrieval_contribution_soft_capped(tmp_path: Path) -> None:
    """Long retrieval payload (many facts, each long) trims at the
    contributor's soft cap — ensures the memory-retrieval share of
    the turn envelope stays bounded."""
    workspace_root = tmp_path / "cap-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    # Seed many long facts so the raw concatenation would exceed the
    # soft cap.
    many_long_facts = [
        {"fact": "x" * 500 + f"-fact-{n}"}
        for n in range(40)
    ]
    client = FakeMemoryClient(
        search_result={"query": "big question", "results": many_long_facts}
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )
    composer.on_session_start(workspace_root)
    turn = composer.on_user_prompt_submit(prompt="big question")

    memory_output = dict(turn.contributor_outputs).get("memory-retrieval", "")
    # Soft cap: memory-retrieval output alone stays within its
    # declared envelope.
    assert len(memory_output) <= MEMORY_RETRIEVAL_CHAR_CAP, (
        f"memory-retrieval output length {len(memory_output)} exceeds "
        f"declared soft cap {MEMORY_RETRIEVAL_CHAR_CAP}"
    )


def test_D7_6_combined_turn_payload_respects_structural_cap(
    tmp_path: Path,
) -> None:
    """Combined D3-style + memory-retrieval contributions still pass
    through the composer's structural 10 000-char refusal. The
    composer's Pydantic ``_cap_guard`` is the authoritative cap
    (per D8 AC-D8.5); this test demonstrates co-existence with a
    heavy synthetic awareness-sized contributor."""
    workspace_root = tmp_path / "combined-cap-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    # Synthetic D3-sized awareness contributor emitting up to ~4000
    # characters (close to the D3 monitor's 1000-token budget).
    def awareness_contrib(ctx: dict[str, Any]) -> str:
        # Mimic realistic awareness-block prose without spilling into
        # the composer's cap.
        return "awareness-row\n" * 250  # ~3500 chars

    # Memory-retrieval returns enough facts to press the soft cap.
    client = FakeMemoryClient(
        search_result={
            "query": "q",
            "results": [{"fact": "y" * 200 + f" -{n}"} for n in range(40)],
        }
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    composer.register(
        name="awareness-synthetic",
        trigger_kind=TriggerKind.turn,
        fn=awareness_contrib,
    )
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )
    composer.on_session_start(workspace_root)
    turn = composer.on_user_prompt_submit(prompt="pressure the cap")

    # Composer's structural cap is not breached — the TurnPayload
    # Pydantic validator would have raised otherwise.
    assert len(turn.additional_context_text) <= ADDITIONAL_CONTEXT_CAP
