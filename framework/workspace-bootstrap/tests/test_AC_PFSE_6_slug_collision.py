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

"""AC.PFSE.6 — two workspaces colliding on the same slug are detected at
install + bootstrap time, with a disambiguation knob available.

Verification surface (plan §5): a bootstrap against a colliding slug
raises the collision + the disambiguation path resolves it.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.slug_collision import (
    SlugCollision,
    detect_slug_collision,
    disambiguate_slug,
    taken_slugs_in,
)


def _write_plist(
    launch_agents: Path, slug: str, kind: str, workspace: Path
) -> None:
    (launch_agents / f"com.loam.{slug}.{kind}.plist").write_text(
        f"<key>WorkingDirectory</key>"
        f"<string>{workspace}/workspace</string>",
        encoding="utf-8",
    )


# ----- collision across two DIFFERENT workspaces with the same slug ---


def test_AC_PFSE_6_collision_detected(tmp_path: Path) -> None:
    la = tmp_path / "LaunchAgents"
    la.mkdir()
    ws_a = tmp_path / "loam"
    ws_a.mkdir()
    ws_b = tmp_path / "clones" / "loam"
    ws_b.mkdir(parents=True)
    _write_plist(la, "loam", "orchestrator", ws_a)

    collision = detect_slug_collision(ws_b, launch_agents_dir=la)
    assert isinstance(collision, SlugCollision)
    assert collision.slug == "loam"
    assert collision.other_workspace is not None
    assert collision.other_workspace.resolve() == ws_a.resolve()
    assert collision.plist_paths


# ----- a re-bootstrap of the SAME workspace is NOT a collision -----


def test_AC_PFSE_6_rebootstrap_not_a_collision(tmp_path: Path) -> None:
    la = tmp_path / "LaunchAgents"
    la.mkdir()
    ws = tmp_path / "loam"
    ws.mkdir()
    _write_plist(la, "loam", "orchestrator", ws)

    collision = detect_slug_collision(ws, launch_agents_dir=la)
    assert collision is None


# ----- no plists at all -> no collision -----


def test_AC_PFSE_6_no_plists_no_collision(tmp_path: Path) -> None:
    la = tmp_path / "LaunchAgents"
    la.mkdir()
    ws = tmp_path / "loam"
    ws.mkdir()
    assert detect_slug_collision(ws, launch_agents_dir=la) is None


# ----- missing LaunchAgents dir -> no collision (fail-soft) -----


def test_AC_PFSE_6_missing_dir_no_collision(tmp_path: Path) -> None:
    ws = tmp_path / "loam"
    ws.mkdir()
    assert (
        detect_slug_collision(
            ws, launch_agents_dir=tmp_path / "absent"
        )
        is None
    )


# ----- basename collision: pos-v2 and pos.v2 both -> pos-v2 -----


def test_AC_PFSE_6_sluggify_collision_detected(tmp_path: Path) -> None:
    la = tmp_path / "LaunchAgents"
    la.mkdir()
    ws_a = tmp_path / "a" / "pos-v2"
    ws_a.mkdir(parents=True)
    ws_b = tmp_path / "b" / "pos.v2"  # sluggifies to pos-v2 too
    ws_b.mkdir(parents=True)
    _write_plist(la, "pos-v2", "orchestrator", ws_a)

    collision = detect_slug_collision(ws_b, launch_agents_dir=la)
    assert collision is not None
    assert collision.slug == "pos-v2"


# ----- the disambiguation knob -----


def test_AC_PFSE_6_disambiguate_appends_suffix() -> None:
    assert disambiguate_slug("loam", taken_slugs={"loam"}) == "loam-2"
    assert (
        disambiguate_slug("loam", taken_slugs={"loam", "loam-2"})
        == "loam-3"
    )


def test_AC_PFSE_6_disambiguate_free_slug_unchanged() -> None:
    assert (
        disambiguate_slug("unique", taken_slugs={"loam"}) == "unique"
    )


# ----- taken_slugs_in reads the live host state -----


def test_AC_PFSE_6_taken_slugs_in(tmp_path: Path) -> None:
    la = tmp_path / "LaunchAgents"
    la.mkdir()
    _write_plist(la, "loam", "orchestrator", tmp_path / "a")
    _write_plist(la, "pos-v2", "memory-write-worker", tmp_path / "b")
    taken = taken_slugs_in(la)
    assert taken == {"loam", "pos-v2"}


# ----- end-to-end: detect collision, then disambiguate against host ----


def test_AC_PFSE_6_collision_then_disambiguate(tmp_path: Path) -> None:
    la = tmp_path / "LaunchAgents"
    la.mkdir()
    ws_a = tmp_path / "loam"
    ws_a.mkdir()
    ws_b = tmp_path / "clones" / "loam"
    ws_b.mkdir(parents=True)
    _write_plist(la, "loam", "orchestrator", ws_a)

    collision = detect_slug_collision(ws_b, launch_agents_dir=la)
    assert collision is not None
    resolved = disambiguate_slug(
        collision.slug, taken_slugs=taken_slugs_in(la)
    )
    assert resolved == "loam-2"
    assert resolved not in taken_slugs_in(la)
