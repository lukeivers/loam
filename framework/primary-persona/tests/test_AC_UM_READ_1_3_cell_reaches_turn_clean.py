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

"""AC.UM.READ.1 + AC.UM.READ.3 — the per-area cell reaches the turn as a
clean, plain behavioural directive (no raw file, no mechanism leak).

AC.UM.READ.1: given a seeded matrix + an area, the read-path emits an
``additionalContext`` directive carrying that area's technical-exposure +
autonomy cell values in plain language.

AC.UM.READ.3: the injected directive carries NO raw file content, NO
mechanism narration, NO SHAs/paths/axis-jargon — it passes the KP9
Layer-1 lint (the syntactic-leak floor that survives unconditionally).
"""

from __future__ import annotations

import sys
from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im
from loam.workspace_bootstrap.seed_writer import render_interaction_model


# Make the KP9 draft_gate importable for the no-leak assertion (the gate
# lives in the hands-off-lifecycle hook home; the test reaches it the same
# best-effort way the live wiring does).
_HOOKS_KP = (
    Path(__file__).resolve().parents[3]
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "keep_pace"
)
sys.path.insert(0, str(_HOOKS_KP))
import draft_gate  # noqa: E402


def _seeded_model() -> im.InteractionModel:
    return im.parse_matrix(render_interaction_model())


def test_AC_UM_READ_1_cell_values_reach_the_directive() -> None:
    """The injected directive carries the area's exposure + autonomy cell."""
    model = _seeded_model()
    # ops-and-money: seeded open exposure + surface autonomy (the cautious
    # floor). Both axes' directives must be present.
    block = im.render_injection(model, "ops-and-money")
    assert block, "ops-and-money produced no injection"
    # The exposure directive (open) and the cautious autonomy directive
    # (surface) are both present, in plain language.
    assert "substance is always on the table" in block  # open exposure
    assert "surface the plan" in block  # surface autonomy


def test_AC_UM_READ_1_distinct_areas_distinct_cells() -> None:
    """A different area's cell yields a distinguishable directive."""
    model = _seeded_model()
    # Override one area so it differs from the seeded prior, then confirm
    # the injection reflects the per-area value (not a global constant).
    model.areas.setdefault("code-and-builds", {})
    model.areas["code-and-builds"]["technical-exposure"] = im.Cell(
        value="deep", confidence="high", locked=True
    )
    deep_block = im.render_injection(model, "code-and-builds")
    prior_block = im.render_injection(model, "default")
    assert "full technical depth" in deep_block
    assert "full technical depth" not in prior_block


def test_AC_UM_READ_3_every_area_injection_passes_kp9_lint() -> None:
    """Every seeded-area injection passes the KP9 Layer-1 lint — no
    path/SHA/AC-ID/jargon leak in the user-visible directive."""
    model = _seeded_model()
    for area in im.AIM_AREAS:
        block = im.render_injection(model, area)
        if not block:
            continue
        result = draft_gate.gate(block)
        assert result.passed(), (
            f"area {area!r} injection leaked: "
            f"{result.model_facing_report()}"
        )


def test_AC_UM_READ_3_no_axis_jargon_or_raw_file() -> None:
    """The directive never surfaces the axis name, the value token, or the
    matrix file mechanism."""
    model = _seeded_model()
    block = im.render_injection(model, "harness-mechanics")
    low = block.lower()
    # No axis jargon.
    assert "technical-exposure" not in low
    assert "autonomy" not in low
    # No mechanism narration.
    assert "cell" not in low
    assert "matrix" not in low
    assert "interaction-model.md" not in low
