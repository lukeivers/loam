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

"""AC.UM.OVR.1/.2/.3 — explicit-override (D-N4.3).

AC.UM.OVR.1: a stated preference hard-sets the cell + persists in the
seed-writer's format.
AC.UM.OVR.2: the write bumps confidence to ``high`` and marks the cell
``locked`` (forward-compatible with "never silently override").
AC.UM.OVR.3: the override survives a re-read (round-trips through the
read-path).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _seed(tmp_path: Path) -> Path:
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        render_interaction_model() + "\n", encoding="utf-8"
    )
    return tmp_path


def test_AC_UM_OVR_1_stated_preference_sets_cell(tmp_path: Path) -> None:
    """An override hard-sets the named cell + persists it."""
    home = _seed(tmp_path)
    r = im.apply_override(
        area="harness-mechanics",
        axis="technical-exposure",
        value="deep",
        claude_home=home,
    )
    assert r.ok
    reread = im.load_interaction_model(home)
    assert reread.cell("harness-mechanics", "technical-exposure").value == "deep"


def test_AC_UM_OVR_2_confidence_bumps_and_locks(tmp_path: Path) -> None:
    """The override sets confidence=high + locked=true in the file."""
    home = _seed(tmp_path)
    im.apply_override(
        area="code-and-builds",
        axis="autonomy",
        value="act",
        claude_home=home,
    )
    cell = im.load_interaction_model(home).cell("code-and-builds", "autonomy")
    assert cell.value == "act"
    assert cell.confidence == "high"
    assert cell.locked is True
    # The lock marker is recorded IN THE FILE (forward-compat with AIM-4).
    raw = (home / "INTERACTION-MODEL.md").read_text()
    assert "locked: true" in raw


def test_AC_UM_OVR_3_override_survives_reread_others_intact(
    tmp_path: Path,
) -> None:
    """A subsequent read injects the overridden value; other cells intact."""
    home = _seed(tmp_path)
    im.apply_override(
        area="their-domain-work",
        axis="technical-exposure",
        value="deep",
        claude_home=home,
    )
    model = im.load_interaction_model(home)
    # The overridden cell reads back as the new value.
    block = im.render_injection(model, "their-domain-work")
    assert "full technical depth" in block
    # An untouched area still carries its seeded prior (others intact).
    assert model.cell("ops-and-money", "autonomy").value == "surface"


def test_AC_UM_OVR_rejects_bad_input(tmp_path: Path) -> None:
    """A bad area / axis / value is rejected — the file is untouched
    (an override can never corrupt the matrix)."""
    home = _seed(tmp_path)
    before = (home / "INTERACTION-MODEL.md").read_text()
    assert not im.apply_override(
        area="not-an-area", axis="autonomy", value="act", claude_home=home
    ).ok
    assert not im.apply_override(
        area="code-and-builds", axis="bogus-axis", value="x", claude_home=home
    ).ok
    assert not im.apply_override(
        area="code-and-builds",
        axis="technical-exposure",
        value="ultra-deep",
        claude_home=home,
    ).ok
    after = (home / "INTERACTION-MODEL.md").read_text()
    assert before == after  # file byte-for-byte untouched


def test_AC_UM_OVR_seeds_minimal_matrix_pre_seed(tmp_path: Path) -> None:
    """An override on a machine with NO matrix file yet (pre-N3-seed) still
    honours the stated preference by seeding a minimal matrix."""
    home = tmp_path  # no INTERACTION-MODEL.md written
    r = im.apply_override(
        area="code-and-builds",
        axis="technical-exposure",
        value="deep",
        claude_home=home,
    )
    assert r.ok
    assert (home / "INTERACTION-MODEL.md").is_file()
    assert (
        im.load_interaction_model(home)
        .cell("code-and-builds", "technical-exposure")
        .value
        == "deep"
    )
