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

"""AC-D7.5 — shared contributor registry is the composition surface.

Outcome (from amendment #33 plan §4 AC-D7.5): the primary-persona
layer exposes a single contributor registry for ``additionalContext``
contributions that accepts (a) a turn-level contributor (registered
by this amendment for memory retrieval) and (b) a session-level
contributor (registered by D8). Contributors are discovered and
invoked by trigger kind, not by persona memory of their existence.

The AC's truth does not depend on which sibling amendment introduced
the registry — the import from ``src.context_composer`` locates the
D8-owned registry here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    TriggerKind,
)
from loam.primary_persona.memory_consumer import register_memory_retrieval, resolve_workspace_slug
from loam.primary_persona.session_start_gate import compose_session_fields

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


def test_D7_5_session_level_and_turn_level_coexist(tmp_path: Path) -> None:
    """Register a session-level synthetic contributor and a
    turn-level (D7 memory-retrieval) contributor on one composer.
    Fire the turn entry point: only the turn contributor's output
    appears. Fire the session entry point: only the session
    contributor's output appears.
    """
    workspace_root = tmp_path / "registry-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    client = FakeMemoryClient(
        search_result={
            "query": "x",
            "results": [{"fact": "turn-level retrieval fact"}],
        }
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)

    # (a) session-level synthetic contributor — stand-in for any
    # session-level contributor (cost-governance, etc.). D8's own
    # corpus-load gate is wired via the session_builder, not via the
    # contributor registry — this test verifies the registry accepts
    # an additional session-level contributor alongside turn-level.
    def session_contrib(ctx: dict[str, Any]) -> str:
        return "session-level-marker"

    composer.register(
        name="synthetic-session",
        trigger_kind=TriggerKind.session,
        fn=session_contrib,
    )

    # (b) turn-level — D7's memory-retrieval contributor.
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )

    # Fire the session entry point.
    session_payload = composer.on_session_start(workspace_root)
    session_names = dict(session_payload.contributor_outputs)
    assert "synthetic-session" in session_names
    assert session_names["synthetic-session"] == "session-level-marker"
    # Turn-level contributor's output does NOT appear on session
    # start — the registry discriminates by trigger kind.
    assert "memory-retrieval" not in session_names

    # Fire the turn entry point.
    turn_payload = composer.on_user_prompt_submit(prompt="hello")
    turn_names = dict(turn_payload.contributor_outputs)
    assert "memory-retrieval" in turn_names
    assert "turn-level retrieval fact" in turn_names["memory-retrieval"]
    # Session-level contributor does NOT appear on turn start.
    assert "synthetic-session" not in turn_names


def test_D7_5_registry_is_invocation_driven_not_memory_driven(
    tmp_path: Path,
) -> None:
    """Contributors are invoked by walking the registry on trigger-
    fire, not by the persona holding memory of their existence. We
    demonstrate this by registering the turn contributor AFTER
    session-start has composed — the turn-start invocation still
    picks it up because the registry is the authority, not any
    cached state.
    """
    workspace_root = tmp_path / "registry-late-bind-ws"
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)

    client = FakeMemoryClient(
        search_result={
            "query": "x",
            "results": [{"fact": "late-bound retrieval"}],
        }
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    # Session first — no turn contributor yet.
    composer.on_session_start(workspace_root)

    # Register the turn-level contributor AFTER session composition.
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )

    turn_payload = composer.on_user_prompt_submit(prompt="anything")
    assert "memory-retrieval" in dict(turn_payload.contributor_outputs)
