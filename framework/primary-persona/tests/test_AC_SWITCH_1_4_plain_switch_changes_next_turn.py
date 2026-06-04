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

"""AC.SWITCH.1 / .2 / .3 / .4 — the plain-language switch path.

AC.SWITCH.1: a plain-language switch ("just show me what's on my plate" /
"I think in projects") persists the choice such that the NEXT turn's
resolver returns the switched-to lens-set.

AC.SWITCH.2: the switch write does NOT mutate the #34 taxonomy — AIM_AREAS
unchanged, apply_override's area-gate unchanged, the seed-writer untouched.
The written matrix round-trips through the live load_interaction_model
reader.

AC.SWITCH.3: the switch confirmation carries ZERO internal vocabulary — no
axis names, cell values, slugs, paths, or enums; a plain acknowledgement.

AC.SWITCH.4: an overridden lens cell is honoured OVER the
technical-exposure-derived default (explicit-statement-wins precedence).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im
from loam.primary_persona.keep_pace import lens_choice as lc
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _seed_plain_exposure(tmp_path: Path) -> Path:
    # A plain-exposure user whose DERIVED default would be on-my-plate.
    matrix = render_interaction_model()
    matrix += (
        "\n## default\n"
        "technical-exposure: { value: plain, confidence: high, "
        "evidence: [], locked: true }\n"
    )
    (tmp_path / "INTERACTION-MODEL.md").write_text(matrix, encoding="utf-8")
    return tmp_path


def test_AC_SWITCH_1_plain_switch_changes_next_resolve(tmp_path: Path) -> None:
    home = _seed_plain_exposure(tmp_path)
    # Pre-switch: the plain-exposure user defaults to on-my-plate.
    assert lc.resolve_lens_set(claude_home=home) == (lc.LENS_PLATE,)

    # The user states a plain-language preference change.
    result = lc.apply_lens_switch(
        preference_text="actually, I think in projects", claude_home=home
    )
    assert result.ok

    # The NEXT resolve returns the switched-to set.
    assert lc.resolve_lens_set(claude_home=home) == (lc.LENS_PROJECTS,)


def test_AC_SWITCH_1_explicit_lens_argument_path(tmp_path: Path) -> None:
    # The switch also accepts an explicit lens name (the persona already
    # mapped the ask). Both paths persist the same cell.
    home = _seed_plain_exposure(tmp_path)
    result = lc.apply_lens_switch(lens=lc.LENS_STREAMS, claude_home=home)
    assert result.ok
    assert lc.LENS_STREAMS in lc.resolve_lens_set(claude_home=home)


def test_AC_SWITCH_2_no_taxonomy_mutation_roundtrips(tmp_path: Path) -> None:
    home = _seed_plain_exposure(tmp_path)
    lc.apply_lens_switch(lens=lc.LENS_PROJECTS, claude_home=home)

    # The written cell round-trips through the LIVE reader.
    model = im.load_interaction_model(home)
    cell = model.cell(lc.LENS_CHOICE_AREA, lc.LENS_CHOICE_AXIS)
    assert cell is not None
    assert cell.value == lc.LENS_PROJECTS

    # The #34 taxonomy is NOT widened by the switch.
    assert "work-tracking" not in im.AIM_AREAS
    assert "preferred-lens" not in im.AIM_AXES
    # apply_override STILL rejects the work-tracking area (the gate is
    # unchanged — the writer never routed through it).
    rej = im.apply_override(
        area=lc.LENS_CHOICE_AREA,
        axis=lc.LENS_CHOICE_AXIS,
        value=lc.LENS_PROJECTS,
        claude_home=tmp_path / "other",
    )
    assert not rej.ok


def test_AC_SWITCH_2_writer_does_not_call_apply_override() -> None:
    # Static guard: the writer path must not route through apply_override
    # (which would reject the work-tracking area). The cell is persisted by
    # re-emitting render_matrix directly.
    src = Path(lc.__file__).read_text(encoding="utf-8")
    # The fence guard targets a CALL to apply_override (and an import of
    # it), not the docstring that explains WHY the writer avoids it.
    assert "apply_override(" not in src, (
        "lens_choice CALLS apply_override — it rejects the work-tracking "
        "area (D-WMS6.4 fence breach)"
    )
    assert "import apply_override" not in src
    assert "render_matrix" in src, (
        "the writer must re-emit via render_matrix (the fence-respecting "
        "WMS-scoped path)"
    )


def test_AC_SWITCH_3_confirmation_zero_internal_vocab(tmp_path: Path) -> None:
    home = _seed_plain_exposure(tmp_path)
    result = lc.apply_lens_switch(
        preference_text="just show me what's on my plate", claude_home=home
    )
    msg = result.confirmation
    assert msg  # there IS a plain confirmation
    lowered = msg.lower()
    # NO internal vocabulary leaks into the user-facing confirmation.
    for forbidden in (
        "work-tracking",
        "preferred-lens",
        "aim_areas",
        "cell",
        "axis",
        "matrix",
        "interaction-model",
        "render_matrix",
        ".md",
        "claude_home",
        "lens_choice",
        "trigger",
        "contributor",
    ):
        assert forbidden not in lowered, (
            f"switch confirmation leaked internal vocab {forbidden!r}: {msg!r}"
        )


def test_AC_SWITCH_4_explicit_pick_sticky_over_derived_default(
    tmp_path: Path,
) -> None:
    # A plain-exposure user whose DERIVED default is on-my-plate, but who
    # has explicitly picked projects: the explicit pick wins.
    home = _seed_plain_exposure(tmp_path)
    lc.apply_lens_switch(lens=lc.LENS_PROJECTS, claude_home=home)
    # The exposure-derived default would be on-my-plate; the explicit pick
    # is honoured over it (the stated-preference-is-sticky outcome).
    assert lc.resolve_lens_set(claude_home=home) == (lc.LENS_PROJECTS,)
