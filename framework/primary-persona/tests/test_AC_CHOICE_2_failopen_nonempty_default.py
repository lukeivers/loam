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

"""AC.CHOICE.2 — fail-open to a NON-EMPTY exposure-derived default.

Plan §6 AC.CHOICE.2 / RF #3 / §8 #3 (the anti-regression floor): given a
#34 matrix with NO work-tracking/preferred-lens cell (an un-seeded or
fresh user), the resolver returns a non-empty SENSIBLE default lens-set
derived from the existing technical-exposure cell per D-WMS6.5 —
plain -> on-my-plate, open -> work-streams, deep -> the broad set —
NEVER an empty set, NEVER nothing surfaced.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import lens_choice as lc
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _seed_exposure(tmp_path: Path, area: str, exposure: str) -> Path:
    """Seed a matrix then hard-set one area's technical-exposure cell,
    WITHOUT any work-tracking/preferred-lens cell (the un-chosen case)."""
    matrix = render_interaction_model()
    matrix += (
        f"\n## {area}\n"
        f"technical-exposure: {{ value: {exposure}, confidence: high, "
        "evidence: [], locked: true }\n"
    )
    (tmp_path / "INTERACTION-MODEL.md").write_text(matrix, encoding="utf-8")
    return tmp_path


def test_AC_CHOICE_2_no_cell_no_file_nonempty_default(tmp_path: Path) -> None:
    # No matrix file at all (a fresh machine). The resolver must NOT
    # return empty — the un-seeded user keeps a per-turn surface.
    chosen = lc.resolve_lens_set(claude_home=tmp_path)
    assert chosen, "un-seeded user resolved to an EMPTY lens-set (regression)"


def test_AC_CHOICE_2_plain_exposure_defaults_to_plate(tmp_path: Path) -> None:
    # A plain-exposure (non-tech, meet-them-simply) user with NO explicit
    # lens choice gets the simplest actionable view (D-WMS6.5).
    home = _seed_exposure(tmp_path, "default", "plain")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert chosen == (lc.LENS_PLATE,)


def test_AC_CHOICE_2_open_exposure_defaults_to_streams(tmp_path: Path) -> None:
    # An open-exposure (engaged) user defaults to the architecture's
    # broadest openness default (D-WMS6.5).
    home = _seed_exposure(tmp_path, "default", "open")
    chosen = lc.resolve_lens_set(claude_home=home)
    assert lc.LENS_STREAMS in chosen


def test_AC_CHOICE_2_default_set_never_empty_for_any_exposure(
    tmp_path: Path,
) -> None:
    for exposure in ("plain", "open", "deep"):
        home = _seed_exposure(tmp_path, "default", exposure)
        chosen = lc.resolve_lens_set(claude_home=home)
        assert chosen, f"exposure {exposure!r} resolved to an EMPTY set"
