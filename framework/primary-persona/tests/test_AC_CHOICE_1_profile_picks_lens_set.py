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

"""AC.CHOICE.1 — a stated preference picks the lens-set.

Plan §6 AC.CHOICE.1: given a #34 matrix carrying a
``work-tracking`` / ``preferred-lens`` cell with a recognised value, the
resolver returns the lens-set that value maps to (a projects-preference
-> the projects lens; a plate-preference -> on-my-plate; a streams/broad
preference -> work-streams). The cell-read mechanism + the value->set map
are the builder's call; this test pins only the OUTCOME (the stated
preference selects the lens-set).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import lens_choice as lc
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _seed_with_lens(tmp_path: Path, value: str) -> Path:
    """Write a seeded matrix carrying a work-tracking/preferred-lens cell.

    The seed-writer does NOT emit the work-tracking area (it is not in
    AIM_AREAS) — the resolver reads a forward-compat cell exactly as
    intake.py reads work-tracking/intake-aggressiveness. We append a
    ``## work-tracking`` section in the live matrix line-shape so the
    read path exercises the production parser, not a stub."""
    matrix = render_interaction_model()
    matrix += (
        "\n## work-tracking\n"
        f"preferred-lens: {{ value: {value}, confidence: high, "
        "evidence: [], locked: true }}\n"
    )
    (tmp_path / "INTERACTION-MODEL.md").write_text(matrix, encoding="utf-8")
    return tmp_path


def test_AC_CHOICE_1_plate_preference_picks_plate(tmp_path: Path) -> None:
    home = _seed_with_lens(tmp_path, "on-my-plate")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert lc.LENS_PLATE in chosen
    assert chosen == (lc.LENS_PLATE,)


def test_AC_CHOICE_1_projects_preference_picks_projects(tmp_path: Path) -> None:
    home = _seed_with_lens(tmp_path, "projects")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert chosen == (lc.LENS_PROJECTS,)


def test_AC_CHOICE_1_streams_preference_picks_streams(tmp_path: Path) -> None:
    home = _seed_with_lens(tmp_path, "work-streams")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert chosen == (lc.LENS_STREAMS,)


def test_AC_CHOICE_1_plain_simplest_alias_picks_plate(tmp_path: Path) -> None:
    # A plain "simplest" alias resolves to the on-my-plate lens (the
    # simplest actionable view) — the value-vocabulary stays small + plain.
    home = _seed_with_lens(tmp_path, "simplest")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert chosen == (lc.LENS_PLATE,)


def test_AC_CHOICE_1_multi_select_set_expressible(tmp_path: Path) -> None:
    # A power user picks a LARGER set (the "add" case expressed as
    # "choose a larger set" — D-WMS6.3): a comma-list of lens names
    # resolves to the set, never a single name.
    home = _seed_with_lens(tmp_path, "projects+work-streams")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert lc.LENS_PROJECTS in chosen
    assert lc.LENS_STREAMS in chosen
    assert len(chosen) == 2
