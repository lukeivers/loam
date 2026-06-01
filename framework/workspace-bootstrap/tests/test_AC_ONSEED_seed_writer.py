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

"""AC.ONSEED.* — the verified result seeds into the two-tier home (N3).
Covers: lands in the correct homes / gate-9 clean (.1), interaction-model at
confidence:prior (.2), confirmed end-intent as an objective (.3), the seed is
the D-2 MINIMUM, not a full model (.4)."""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.seed_writer import (
    AIM_AREAS,
    render_interaction_model,
    seed_user_state,
)


def _seed(tmp_path: Path):
    home = tmp_path / ".claude"
    ws = tmp_path / "ws"
    ws.mkdir()
    res = seed_user_state(
        objective_slug="stop-manual-status-reports",
        objective_text="Help the user stop doing manual status reports",
        workspace_root=ws,
        global_home=home,
        last_touched="2026-05-31",
    )
    return home, ws, res


# ---- AC.ONSEED.1 — the seed lands in the correct homes. ----


def test_AC_ONSEED_1_seed_lands_only_under_the_global_home(tmp_path: Path):
    home, ws, res = _seed(tmp_path)
    # Both seed files land UNDER ~/.claude (the global home), nothing elsewhere.
    assert res.objectives_path == home / "OBJECTIVES.md"
    assert res.interaction_model_path == home / "INTERACTION-MODEL.md"
    assert res.objectives_path.exists()
    assert res.interaction_model_path.exists()
    # The workspace home was composed (the layout), but NO model seed landed.
    assert (ws / ".loam").is_dir()
    assert not any((ws / ".loam" / "user-model").glob("*.md"))


def test_AC_ONSEED_1_no_seed_file_carries_a_framework_path_segment(tmp_path: Path):
    """Gate-9 proxy: every seeded file is addressed relative to the home —
    none lands under a framework/ tree."""
    home, ws, res = _seed(tmp_path)
    for p in (res.objectives_path, res.interaction_model_path):
        assert "framework" not in p.parts
        assert ".claude" in p.parts


# ---- AC.ONSEED.2 — interaction-model at confidence: prior. ----


def test_AC_ONSEED_2_interaction_model_every_cell_at_confidence_prior(tmp_path: Path):
    home, ws, res = _seed(tmp_path)
    text = res.interaction_model_path.read_text()
    # Every cell carries confidence: prior; none has climbed to low/medium/high.
    assert "confidence: prior" in text
    assert "confidence: low" not in text
    assert "confidence: medium" not in text
    assert "confidence: high" not in text
    # The matrix seeds every declared area row.
    for area in AIM_AREAS:
        assert f"## {area}" in text


def test_AC_ONSEED_2_openness_biased_defaults_and_autonomy_floor():
    text = render_interaction_model()
    # technical-exposure defaults open (openness-biased), learning-appetite invite.
    assert "technical-exposure: { value: open" in text
    assert "learning-appetite: { value: invite" in text
    # The floor exception: ops-and-money autonomy floors at the cautious end.
    ops_block = text.split("## ops-and-money", 1)[1].split("##", 1)[0]
    assert "autonomy: { value: surface" in ops_block
    # A non-consequence area uses the open autonomy default (recommend).
    code_block = text.split("## code-and-builds", 1)[1].split("##", 1)[0]
    assert "autonomy: { value: recommend" in code_block


# ---- AC.ONSEED.3 — confirmed end-intent seeds as an objective. ----


def test_AC_ONSEED_3_objective_in_objectives_md_shape(tmp_path: Path):
    home, ws, res = _seed(tmp_path)
    text = res.objectives_path.read_text()
    assert "## stop-manual-status-reports" in text
    assert "status: active" in text  # confirmed -> active (the verify gate IS the owner-gate)
    assert "cadence:" in text
    assert "objective: Help the user stop doing manual status reports" in text


# ---- AC.ONSEED.4 — the seed is the MINIMUM useful prior. ----


def test_AC_ONSEED_4_workspace_model_homes_not_pre_filled(tmp_path: Path):
    home, ws, res = _seed(tmp_path)
    # The workspace model homes are NOT pre-populated with inferred content
    # (N4 fills them from evidence). The layout exists; the homes are empty.
    user_model = ws / ".loam" / "user-model"
    session_model = ws / ".loam" / "session-model"
    assert user_model.is_dir()
    assert session_model.is_dir()
    # Only the .gitkeep marker — no seeded model content.
    assert [p.name for p in user_model.iterdir()] in ([], [".gitkeep"])
    assert [p.name for p in session_model.iterdir()] in ([], [".gitkeep"])


def test_AC_ONSEED_4_only_two_global_seed_files(tmp_path: Path):
    home, ws, res = _seed(tmp_path)
    md_files = sorted(p.name for p in home.glob("*.md"))
    assert md_files == ["INTERACTION-MODEL.md", "OBJECTIVES.md"]
