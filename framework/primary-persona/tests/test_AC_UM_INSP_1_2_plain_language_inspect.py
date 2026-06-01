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

"""AC.UM.INSP.1/.2 — plain-language inspect.

AC.UM.INSP.1: inspect renders the per-area stance as PROSE, never the raw
matrix or axis-jargon (design §5 — the highest-risk leak surface).
AC.UM.INSP.2: inspect is truthful to the file — reading the live matrix,
so an inspect after an override reflects the override.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im
from loam.workspace_bootstrap.seed_writer import render_interaction_model


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


def test_AC_UM_INSP_1_renders_prose_not_raw_file() -> None:
    """Inspect renders prose — no axis name, no value token, no raw
    matrix line, no file mechanism."""
    prose = im.render_inspect(_seeded_model(), "ops-and-money")
    assert prose
    low = prose.lower()
    # No axis jargon / value tokens / file mechanism.
    for leak in (
        "technical-exposure",
        "autonomy",
        "confidence",
        "evidence",
        "{ value",
        "interaction-model.md",
        "matrix",
    ):
        assert leak not in low, f"inspect leaked {leak!r}: {prose!r}"


def test_AC_UM_INSP_1_passes_kp9_lint() -> None:
    """The inspect prose passes the KP9 Layer-1 lint (no path/SHA/jargon
    leak) for every area + the all-areas render."""
    model = _seeded_model()
    for area in list(im.AIM_AREAS) + [None]:  # type: ignore[list-item]
        prose = im.render_inspect(model, area)
        result = draft_gate.gate(prose)
        assert result.passed(), (
            f"inspect for {area!r} leaked: {result.model_facing_report()}"
        )


def test_AC_UM_INSP_2_reflects_override(tmp_path: Path) -> None:
    """An inspect after an override reflects the new value — proving it
    reads the live file, not a guess."""
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        render_interaction_model() + "\n", encoding="utf-8"
    )
    im.apply_override(
        area="code-and-builds",
        axis="technical-exposure",
        value="deep",
        claude_home=tmp_path,
    )
    model = im.load_interaction_model(tmp_path)
    prose = im.render_inspect(model, "code-and-builds")
    # The deep-exposure prose description is present (the override is
    # reflected); the open-prior description is not.
    assert "full technical depth" in prose
    assert "introduce technical terms as they come up" not in prose


def test_AC_UM_INSP_2_per_area_distinct() -> None:
    """Inspect is per-area: a cautious-autonomy area reads differently from
    a recommend-autonomy area."""
    model = _seeded_model()
    money = im.render_inspect(model, "ops-and-money")  # surface autonomy
    builds = im.render_inspect(model, "code-and-builds")  # recommend autonomy
    assert "before any consequence-bearing move" in money
    assert "before any consequence-bearing move" not in builds
