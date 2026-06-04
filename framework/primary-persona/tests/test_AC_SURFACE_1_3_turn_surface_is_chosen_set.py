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

"""AC.SURFACE.1 / .2 / .3 — the per-turn surface respects the choice.

AC.SURFACE.1: given a resolved lens-set, the per-turn surface registers
exactly the CHOSEN lens(es) as the turn blocks; a lens NOT in the resolved
set is NOT registered as a TriggerKind.turn contributor for that user.

AC.SURFACE.2: an un-chosen lens stays available on demand — its
render_*_block entry point still renders the correct view when invoked,
even though it is not a per-turn block (replace-not-delete, D-WMS6.3).

AC.SURFACE.3: for a given resolved set, the per-turn block COUNT is the
size of the chosen set — a single-lens choice yields ONE WMS lens block
where today three always-on blocks fire (the anti-bloat outcome).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    TriggerKind,
)
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.keep_pace import lens_choice as lc
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _seed_lens(tmp_path: Path, value: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    matrix = render_interaction_model()
    matrix += (
        "\n## work-tracking\n"
        f"preferred-lens: {{ value: {value}, confidence: high, "
        "evidence: [], locked: true }}\n"
    )
    (tmp_path / "INTERACTION-MODEL.md").write_text(matrix, encoding="utf-8")
    return tmp_path


def _turn_block_names(composer: ComposedContextPayload) -> set[str]:
    return {c.name for c in composer.contributors(TriggerKind.turn)}


def test_AC_SURFACE_1_only_chosen_lens_registered(tmp_path: Path) -> None:
    home = _seed_lens(tmp_path, "on-my-plate")
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer, claude_home=home)
    names = _turn_block_names(composer)
    # The chosen plate lens IS registered; the un-chosen always-on trio is NOT.
    assert lc.LENS_PLATE in names
    assert lc.LENS_STREAMS not in names
    assert lc.LENS_PROJECTS not in names
    assert lc.LENS_RELATIONAL not in names


def test_AC_SURFACE_1_projects_choice_registers_only_projects(
    tmp_path: Path,
) -> None:
    home = _seed_lens(tmp_path, "projects")
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer, claude_home=home)
    names = _turn_block_names(composer)
    assert names == {lc.LENS_PROJECTS}


def test_AC_SURFACE_3_block_count_equals_set_size(tmp_path: Path) -> None:
    # A single-lens choice -> exactly ONE WMS turn block (where today the
    # trio fires three). A two-lens choice -> exactly two.
    _seed_lens(tmp_path / "one", "on-my-plate")
    composer_one = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer_one, claude_home=tmp_path / "one")
    assert len(composer_one.contributors(TriggerKind.turn)) == 1

    _seed_lens(tmp_path / "two", "projects+work-streams")
    composer_two = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer_two, claude_home=tmp_path / "two")
    assert len(composer_two.contributors(TriggerKind.turn)) == 2


def test_AC_SURFACE_2_unchosen_lens_still_renders_on_demand(
    tmp_path: Path,
) -> None:
    # The user chose on-my-plate, so projects is NOT a per-turn block.
    # Its render_*_block entry point still renders correctly when invoked
    # (replace, not delete — D-WMS6.3 / AC.SURFACE.2).
    from _wms4_store import make_item
    from loam.primary_persona.keep_pace import projects as P

    home = _seed_lens(tmp_path, "on-my-plate")
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer, claude_home=home)
    assert lc.LENS_PROJECTS not in _turn_block_names(composer)

    # The on-demand projects entry point still works against an injected set.
    items = [
        make_item(
            "x",
            goal="advance the launch",
            status="active",
            belongs_to_project="cairn",
        )
    ]
    block = P.render_projects_block(items=items)
    assert block, "un-chosen projects lens failed to render on demand"
    assert "cairn" in block
