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

"""AC D8.5 — Shared-composer contract (D7 sibling consumer).

Outcome (from amendment plan §4 D8.5): a ``ComposedContextPayload``
primitive is exposed at the persona-layer surface with two entry
points (``on_session_start``, ``on_user_prompt_submit``) and a
registration surface for ``additionalContext`` contributors. The
primitive refuses at construction when the serialised payload
produced by any entry point would exceed 10,000 characters. A
synthetic turn-level contributor registered in the test fixture and
invoked via ``on_user_prompt_submit`` has its contribution observable
in the returned turn-payload — the registration-and-invocation path
is exercised end-to-end without any D7 amendment being present.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from loam.primary_persona.context_composer import (
    ADDITIONAL_CONTEXT_CAP,
    AdditionalContextCapExceededError,
    ComposedContextPayload,
    SessionPayload,
    TriggerKind,
    TurnPayload,
)
from loam.primary_persona.session_start_gate import compose_session_fields


def _seed(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "## Session-start discipline\n\n- `docs/odd-methodology.md`\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("x")


def test_D8_5_two_entry_points_and_registration_surface(tmp_path: Path) -> None:
    """The primitive exposes ``on_session_start``,
    ``on_user_prompt_submit``, and a ``register`` surface."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    assert hasattr(composer, "on_session_start")
    assert hasattr(composer, "on_user_prompt_submit")
    assert hasattr(composer, "register")

    # The two entry points return the declared payload shapes.
    session = composer.on_session_start(tmp_path)
    assert isinstance(session, SessionPayload)
    turn = composer.on_user_prompt_submit(prompt="hi")
    assert isinstance(turn, TurnPayload)


def test_D8_5_construction_refuses_over_cap_session(tmp_path: Path) -> None:
    """``SessionPayload`` refuses at construction when the serialised
    payload would exceed 10,000 characters. Structural (not advisory).

    Pydantic wraps the underlying ``AdditionalContextCapExceededError``
    inside a ``ValidationError`` (both are ``ValueError`` subclasses)
    — the structural refusal surfaces as either form depending on the
    construction path. We accept both.
    """
    overflow_text = "x" * (ADDITIONAL_CONTEXT_CAP + 1)
    with pytest.raises((AdditionalContextCapExceededError, ValidationError)):
        SessionPayload(additional_context_text=overflow_text)


def test_D8_5_construction_refuses_over_cap_turn(tmp_path: Path) -> None:
    """``TurnPayload`` refuses at construction when the serialised
    payload would exceed 10,000 characters."""
    overflow_text = "x" * (ADDITIONAL_CONTEXT_CAP + 1)
    with pytest.raises((AdditionalContextCapExceededError, ValidationError)):
        TurnPayload(additional_context_text=overflow_text)


def test_D8_5_synthetic_turn_contributor_round_trip(tmp_path: Path) -> None:
    """A synthetic turn-level contributor registered in the test
    fixture and invoked via ``on_user_prompt_submit`` has its
    contribution observable in the returned turn-payload. Exercises
    the registration-and-invocation path end-to-end without any D7
    amendment being present."""
    _seed(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)

    received_contexts: list[dict[str, Any]] = []

    def synthetic(ctx: dict[str, Any]) -> str:
        received_contexts.append(ctx)
        return f"synthetic-out/{ctx.get('prompt')}"

    composer.register(
        name="synthetic",
        trigger_kind=TriggerKind.turn,
        fn=synthetic,
    )
    composer.on_session_start(tmp_path)
    turn = composer.on_user_prompt_submit(prompt="round-trip")

    # The contributor was invoked with the turn context.
    assert len(received_contexts) == 1
    assert received_contexts[0]["prompt"] == "round-trip"

    # The output is observable in the turn payload's contributor
    # outputs AND its serialised additionalContext text.
    names_outputs = dict(turn.contributor_outputs)
    assert names_outputs["synthetic"] == "synthetic-out/round-trip"
    assert "synthetic-out/round-trip" in turn.additional_context_text
