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

"""AC-FBM-STATE-LENS-1 (Slice D / D1) — the production composer registers
the GROUND-TRUTH project-state turn contributor, and a composed turn surfaces a
STATE block naming a registered project + its derived status.

This is the wiring + surfacing AC: it proves (a) the production (client-None)
branch of ``build_session_composer`` registers a ``project-state`` turn
contributor, and (b) when a turn is composed, the rendered turn payload carries
a STATE block whose text names a registered project + its derived status — the
ground-truth status now reaching the turn-start lens, which was the missing edge.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import TriggerKind
from loam.primary_persona.keep_pace.project_state import (
    render_project_state_block,
    register_project_state_contributor,
)
from loam.primary_persona.session_start_emitter import build_session_composer


def test_production_composer_registers_project_state_contributor(
    tmp_path: Path,
) -> None:
    """The production (client-None) branch registers exactly one
    ``project-state`` turn contributor."""
    ws = tmp_path / "myws"
    ws.mkdir()

    composer = build_session_composer(
        ws,
        memory_client_factory=lambda _root: None,  # production client-None branch
        register_tracker=False,
    )

    turn_contribs = composer.contributors(trigger_kind=TriggerKind.turn)
    names = [c.name for c in turn_contribs]
    assert "project-state" in names, (
        "the production composer must register a turn-level project-state "
        f"contributor; registered turn contributors: {names}"
    )
    assert names.count("project-state") == 1, "no double-register"


def test_composed_turn_surfaces_state_block(tmp_path: Path) -> None:
    """A composed turn payload carries a STATE block naming a registered
    project + its derived status.

    Uses a FIXTURE derivation injected via the contributor's ``names`` +
    ``render_project_state_block``'s ``derive`` override so the test is
    hermetic (no live repos): a single registered project ``demo`` with a
    ``alpha = built (merged)`` row must appear in the rendered turn text.
    """
    from loam_cli.audit.probe import Liveness
    from loam_cli.audit.record import ComponentState, StateOfLoam

    ws = tmp_path / "myws"
    ws.mkdir()

    # A composer with ONLY the project-state contributor, scoped to a fixture
    # project name, deriving a fixture record (no live repo).
    from loam.primary_persona.context_composer import ComposedContextPayload
    from loam.primary_persona.session_start_emitter import compose_session_fields

    composer = ComposedContextPayload(session_builder=compose_session_fields)

    fixture = StateOfLoam(
        head_sha="abc123def456",
        components=(
            ComponentState(
                name="alpha",
                liveness=Liveness.MERGED,
                kind="component",
                evidence="fixture",
            ),
        ),
    )

    # Register a contributor that derives the fixture record for the fixture
    # project name (bypasses the live registry path).
    def _fn(context: dict) -> str:  # noqa: ARG001
        return render_project_state_block(
            names=("demo",), derive=lambda _n: fixture
        )

    composer.register(
        name="project-state", trigger_kind=TriggerKind.turn, fn=_fn
    )

    composer.on_session_start(ws)
    payload = composer.on_user_prompt_submit(prompt="what's the status of demo")
    text = payload.additional_context_text.lower()

    assert "demo" in text, f"the STATE block must name the project; got:\n{text}"
    assert "alpha" in text, f"the STATE block must name the module; got:\n{text}"
    assert "built" in text, (
        f"the STATE block must carry the derived status; got:\n{text}"
    )
