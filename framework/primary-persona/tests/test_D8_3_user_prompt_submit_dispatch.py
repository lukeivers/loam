"""AC D8.3 — UserPromptSubmit contributor dispatch.

Outcome (from amendment plan §4 D8.3): the shared composer exposes an
``on_user_prompt_submit`` entry point that accepts a user prompt +
resolved-component hint + optional memory-client handle and returns a
turn-payload object carrying the session-level sentinel plus a
registered-contributor collection. Invoking the entry point on a
process whose session-level payload was never composed is not
representable — the composer refuses at construction. The turn-payload
surface exposes a registration mechanism a sibling amendment (D7) can
bind a memory-retrieval contributor to without amending D8's scope.
D8 itself registers no turn-level contributor; the corpus baseline is
session-level only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    SessionPayloadMissingError,
    TriggerKind,
)
from loam.primary_persona.session_start_gate import compose_session_fields


def _seed(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "## Session-start discipline\n\n- `docs/odd-methodology.md`\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("x")


def test_D8_3_entry_point_accepts_prompt_and_component_and_memory_client(
    tmp_path: Path,
) -> None:
    """``on_user_prompt_submit`` accepts a prompt, optional resolved-
    component hint, and optional memory-client handle, and returns a
    turn payload."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    composer.on_session_start(tmp_path)

    class _FakeMemoryClient:
        pass

    turn = composer.on_user_prompt_submit(
        prompt="what's next?",
        resolved_component="primary-persona-loader",
        memory_client=_FakeMemoryClient(),
    )
    assert turn.prompt == "what's next?"
    assert turn.resolved_component == "primary-persona-loader"


def test_D8_3_turn_payload_carries_session_level_sentinel(
    tmp_path: Path,
) -> None:
    """Turn payload carries the session-level sentinel inherited from
    ``on_session_start``."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    session_payload = composer.on_session_start(tmp_path)
    turn = composer.on_user_prompt_submit(prompt="hi")

    assert turn.corpus_gate_state == session_payload.corpus_gate_state


def test_D8_3_refuses_at_construction_without_session_payload(
    tmp_path: Path,
) -> None:
    """Invoking ``on_user_prompt_submit`` on a composer whose session
    payload was never composed raises ``SessionPayloadMissingError``.
    Structural representation of the plan's "not representable"
    constraint."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    # Deliberately skip on_session_start.
    with pytest.raises(SessionPayloadMissingError):
        composer.on_user_prompt_submit(prompt="will fail")


def test_D8_3_registered_turn_contributor_observable_in_turn_payload(
    tmp_path: Path,
) -> None:
    """The turn-payload surface exposes a registration mechanism
    D7 can bind against without amending D8's scope. A synthetic
    turn-level contributor registered against the shared registry
    appears in the returned turn payload's contributor_outputs."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)

    def synthetic_memory_retrieval(ctx: dict[str, Any]) -> str:
        return f"retrieved:{ctx['prompt']}"

    composer.register(
        name="d7-memory-retrieval",
        trigger_kind=TriggerKind.turn,
        fn=synthetic_memory_retrieval,
    )
    composer.on_session_start(tmp_path)
    turn = composer.on_user_prompt_submit(prompt="hello")

    names = [name for name, _ in turn.contributor_outputs]
    assert "d7-memory-retrieval" in names
    # Output is observable in the turn's additionalContext text.
    assert "retrieved:hello" in turn.additional_context_text


def test_D8_3_d8_registers_no_turn_level_contributor(tmp_path: Path) -> None:
    """D8 itself registers no turn-level contributor; the corpus
    baseline is session-level only. A composer with no external
    registrations has an empty turn-level contributor set."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    composer.on_session_start(tmp_path)

    turn_contributors = composer.contributors(trigger_kind=TriggerKind.turn)
    assert turn_contributors == ()
