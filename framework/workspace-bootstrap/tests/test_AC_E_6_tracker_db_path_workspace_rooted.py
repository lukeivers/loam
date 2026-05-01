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

"""AC.E.6 — `tracker_db_path_for(workspace_root)` returns
`<workspace_root>/objective_tracker.sqlite`.

Sub-plan E (two-modes-and-multi-workspace, amendment #42) folds in
the path-mismatch fix between amendment #39 (the seed) and amendment
#40 (the tracker-context contributor on primary-persona). #39 wrote
the DB at ``pos_root/objective_tracker.sqlite`` while #40 reads at
``workspace_root/objective_tracker.sqlite`` — a latent bug that bites
the moment register_tracker_context goes live.

E aligns the seed-side resolver to the contributor-side: both now
take ``workspace_root``; both return the same workspace-rooted path.

This test asserts the seed-side ``tracker_db_path_for`` resolves to
the workspace-rooted location, and that the same path equals the
primary-persona contributor-side resolver's output for the same
workspace.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.tracker_context import (
    tracker_db_path_for as persona_tracker_db_path_for,
)

from loam.workspace_bootstrap.adapters.tracker_seed import (
    TRACKER_DB_FILENAME,
    tracker_db_path_for,
)


def test_AC_E_6_path_is_workspace_rooted(tmp_path: Path) -> None:
    """``tracker_db_path_for(workspace_root)`` returns
    ``<workspace_root>/workspace/objective_tracker.sqlite`` post-D.2
    (was ``<workspace_root>/objective_tracker.sqlite`` pre-D.2
    amendment #63).
    """
    workspace = tmp_path / "ws-1"
    workspace.mkdir()

    out = tracker_db_path_for(workspace)
    assert out == workspace / "workspace" / TRACKER_DB_FILENAME
    assert out.parent == workspace / "workspace"


def test_AC_E_6_path_matches_primary_persona_contributor(tmp_path: Path) -> None:
    """The seed-side resolver and amendment #40's contributor-side
    resolver return the SAME path for the same workspace_root. Single
    source of truth — both reads land on the same DB file."""
    workspace = tmp_path / "ws-parity"
    workspace.mkdir()

    seed_path = tracker_db_path_for(workspace)
    contributor_path = persona_tracker_db_path_for(workspace)
    assert seed_path == contributor_path


def test_AC_E_6_two_workspaces_yield_distinct_paths(tmp_path: Path) -> None:
    """Two distinct workspace roots resolve to two distinct DB paths.
    Workspace-locality is structural — two pos-v2 workspaces on one
    host cannot collide on the tracker DB."""
    ws_a = tmp_path / "ws-a"
    ws_b = tmp_path / "ws-b"
    ws_a.mkdir()
    ws_b.mkdir()

    path_a = tracker_db_path_for(ws_a)
    path_b = tracker_db_path_for(ws_b)
    assert path_a != path_b
    assert path_a.is_relative_to(ws_a)
    assert path_b.is_relative_to(ws_b)


def test_AC_E_6_accepts_string_argument(tmp_path: Path) -> None:
    """Argument may be ``str`` or ``Path``; behaviour identical."""
    workspace = tmp_path / "ws-str"
    workspace.mkdir()

    path_from_str = tracker_db_path_for(str(workspace))
    path_from_path = tracker_db_path_for(workspace)
    assert path_from_str == path_from_path
