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

"""PROVE step for slice P1.2 (.loam/ workspace layout).

Outcome-altitude ACs (cold-walk: the production entry point
``establish_loam_layout`` is invoked against a brand-new temp workspace
with NO pre-arranged state — see AC-LOAM-LAYOUT-1..4 in
``docs/plans/loam-layout-slice-plan.md``).
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.loam_layout import (
    DECLARED_DIRS,
    establish_loam_layout,
)


# ---- AC-LOAM-LAYOUT-1 (outcome-altitude) -----------------------------
def test_AC_LOAM_LAYOUT_1_fresh_workspace_gets_complete_layout(tmp_path: Path):
    """Establishing against a fresh (empty) workspace produces the
    complete declared ``.loam/`` structure — invoked with no pre-seeded
    ``.loam/`` (cold-walk)."""
    result = establish_loam_layout(tmp_path)
    loam = tmp_path / ".loam"

    assert loam.is_dir()
    assert (loam / "README.md").is_file()
    for name in DECLARED_DIRS:
        assert (loam / name).is_dir(), f"declared dir {name!r} missing"
    # The four homes + migrations + README were all newly created.
    assert result.changed
    assert "README.md" in result.created
    for name in DECLARED_DIRS:
        assert name in result.created


# ---- AC-LOAM-LAYOUT-2 (outcome-altitude) -----------------------------
def test_AC_LOAM_LAYOUT_2_layout_is_self_describing(tmp_path: Path):
    """``.loam/README.md`` names every declared dir + its purpose and
    states the boundary rule (user-state only; no framework code)."""
    establish_loam_layout(tmp_path)
    readme = (tmp_path / ".loam" / "README.md").read_text(encoding="utf-8")

    for name in DECLARED_DIRS:
        assert name in readme, f"declared dir {name!r} not documented in README"
    assert "memory/" in readme
    # The boundary rule is stated.
    assert "USER-STATE ONLY" in readme
    assert "No framework code" in readme


# ---- AC-LOAM-LAYOUT-3 ------------------------------------------------
def test_AC_LOAM_LAYOUT_3_boundary_additive_existing_memory_untouched(
    tmp_path: Path,
):
    """An existing ``memory/`` tree (live FBM store) is detected and left
    byte-for-byte intact; nothing the helper does removes user-state."""
    loam = tmp_path / ".loam"
    mem = loam / "memory" / "episodes" / "ws"
    mem.mkdir(parents=True)
    episode = mem / "episode-0001.json"
    episode.write_text('{"fact": "ZEPHYR"}', encoding="utf-8")
    index = loam / "memory" / "search-index.sqlite"
    index.write_bytes(b"\x00fake-index\x00")
    index_bytes_before = index.read_bytes()

    result = establish_loam_layout(tmp_path)

    assert result.memory_preexisting is True
    assert "memory" in result.existing
    assert "memory" not in result.created
    # Live state byte-identical.
    assert episode.read_text(encoding="utf-8") == '{"fact": "ZEPHYR"}'
    assert index.read_bytes() == index_bytes_before


# ---- AC-LOAM-LAYOUT-4 ------------------------------------------------
def test_AC_LOAM_LAYOUT_4_idempotent_second_run_is_noop(tmp_path: Path):
    """A second establish run creates nothing and overwrites nothing —
    fail-safe over an existing tree."""
    first = establish_loam_layout(tmp_path)
    assert first.changed

    # Annotate the README + drop a file in a home; the second run must
    # not clobber either.
    readme = tmp_path / ".loam" / "README.md"
    readme.write_text("OPERATOR ANNOTATED", encoding="utf-8")
    seeded = tmp_path / ".loam" / "user-model" / "model.yaml"
    seeded.write_text("openness: open", encoding="utf-8")

    second = establish_loam_layout(tmp_path)

    assert second.created == [], "second run must create nothing"
    assert second.changed is False
    assert readme.read_text(encoding="utf-8") == "OPERATOR ANNOTATED"
    assert seeded.read_text(encoding="utf-8") == "openness: open"
