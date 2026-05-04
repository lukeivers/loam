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

"""AC.SFR.4 — `pos-sync` composition with canonical's main is unchanged
from D.3's invariant.

Single-framework restructure (amendment #67) + OSS dev-architecture
migration (2026-05-04). Post-migration the bootstrap targets
canonical's ``main`` branch directly; the test exercises the
ff-graph composition without the (now-archived) synthesis layer:

1. ``pos-new-workspace`` clones canonical's ``main``.
2. Canonical advances its ``main`` (a direct commit; pre-migration
   this advance went via the synthesis tool but post-migration the
   advance is just a normal commit).
3. From the workspace, ``pos-sync`` runs ``git fetch + git merge
   --ff-only`` against ``main``'s HEAD; the workspace's
   ``framework/`` fast-forwards.
4. After ``pos-sync``, every file under ``<workspace>/framework/<rel>``
   is byte-identical to canonical's ``main`` HEAD's ``<rel>``.
5. Files under ``<workspace>/workspace/`` are byte-identical pre/post
   sync (D.3's HC#6 structural promise carried forward).

The test composes:

- ``workspace_bootstrap.new_workspace.bootstrap_new_workspace`` — to
  produce the workspace.
- ``workspace_sync.cli.main`` — to run ``pos-sync`` against the
  workspace.

Pre-migration the test also imported
``loam.publish_framework_only.synthesise_framework_only`` to advance
the synthesis-only ``framework-only`` branch lockstep with each
``pos-v2`` commit. Post-migration that import is gone; canonical's
``main`` advances directly via a normal git commit.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters import tracker_seed
from loam.workspace_bootstrap.new_workspace import bootstrap_new_workspace


def _stub_tracker_seed_runner(**_kwargs):
    return tracker_seed.TrackerSeedResult(
        seeded=False,
        reason="skipped_test_stub",
        classification="user",
        root_id=None,
        descendants_seeded=(),
        value_prop_source=None,
    )


def _git(args: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.rstrip("\n")


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _snapshot_tree_sha(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root))] = _sha256(p)
    return out


def test_AC_SFR_4_pos_sync_fast_forwards_main(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The full bootstrap-then-sync flow over canonical's main.

    Steps:
      1. Construct fixture canonical on ``main``.
      2. ``pos-new-workspace`` produces a workspace tracking ``main``.
      3. Capture ``<workspace>/workspace/`` tree snapshot pre-sync.
      4. Advance canonical's ``main`` with a follow-on commit.
      5. From the workspace, ``pos-sync`` runs.
      6. Assert: workspace's framework/ HEAD equals canonical's main
         HEAD (``git fetch + git merge --ff-only`` succeeded).
      7. Assert: workspace files byte-equal post-sync to canonical's
         main HEAD's tree (HC#4 carry-forward).
      8. Assert: ``<workspace>/workspace/`` files byte-identical
         pre/post sync (HC#6 carry-forward).
    """
    pytest.importorskip("workspace_sync.cli")
    from loam.workspace_sync.cli import main as sync_cli_main  # noqa: PLC0415

    canonical = make_fixture_canonical(tmp_path / "canonical")
    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"

    # Step 2: bootstrap workspace.
    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )
    framework = new_ws / "framework"
    workspace_state_dir = new_ws / "workspace"

    # Sanity: workspace-side initial HEAD matches canonical's main
    # initial HEAD.
    initial_main_sha = _git(
        ["rev-parse", "refs/heads/main"], cwd=canonical
    )
    initial_ws_sha = _git(["rev-parse", "HEAD"], cwd=framework)
    assert initial_ws_sha == initial_main_sha

    # Step 3: snapshot workspace-state.
    pre_workspace_state = _snapshot_tree_sha(workspace_state_dir)
    assert pre_workspace_state, (
        "<workspace>/workspace/ must contain scaffolded state pre-sync"
    )

    # Step 4: advance canonical's main with a direct commit (post-
    # migration there is no synthesis layer; advances are normal
    # git commits on main).
    new_file = canonical / "framework" / "workspace-bootstrap" / "added.py"
    new_file.write_text("# new content for AC.SFR.4 sync\n")
    _git(["add", "-A"], cwd=canonical)
    _git(["commit", "-m", "advance main for AC.SFR.4"], cwd=canonical)
    advanced_main_sha = _git(["rev-parse", "refs/heads/main"], cwd=canonical)
    assert advanced_main_sha != initial_main_sha

    # Step 5: pos-sync from the workspace.
    rc = sync_cli_main(["--workspace", str(new_ws)])
    assert rc == 0, f"pos-sync exited non-zero: {rc}"

    # Step 6: workspace's framework/ now at canonical's main HEAD.
    post_ws_sha = _git(["rev-parse", "HEAD"], cwd=framework)
    assert post_ws_sha == advanced_main_sha, (
        f"AC.SFR.4: workspace HEAD post-sync should equal advanced "
        f"main ({advanced_main_sha!r}); got {post_ws_sha!r}"
    )

    # Step 7: workspace's framework/<rel> byte-equals canonical's
    # main HEAD's <rel>. The advance landed `framework/workspace-
    # bootstrap/added.py` on canonical's main → workspace lands it
    # DOUBLED at `<workspace>/framework/framework/workspace-
    # bootstrap/added.py` (post-migration doubling contract preserved
    # because canonical's main carries `framework/<comp>/` paths
    # verbatim).
    advanced_file = (
        framework / "framework" / "workspace-bootstrap" / "added.py"
    )
    assert advanced_file.exists(), (
        f"AC.SFR.4: advanced file should land at {advanced_file} "
        f"(doubled-component shape); not found"
    )
    assert advanced_file.read_text() == "# new content for AC.SFR.4 sync\n"

    # Step 8: workspace-state byte-identical pre/post sync (HC#6) for
    # files OTHER than pos-sync's own state-record at
    # `<workspace>/workspace/.pos/sync/state.yaml` — D.3 records its
    # own audit trail there. The structural promise is that pos-sync
    # does not mutate workspace files outside its declared state-record
    # surface.
    post_workspace_state = _snapshot_tree_sha(workspace_state_dir)

    def _strip_sync_state(d: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in d.items() if not k.startswith(".pos/sync/")}

    pre_minus_sync = _strip_sync_state(pre_workspace_state)
    post_minus_sync = _strip_sync_state(post_workspace_state)
    assert pre_minus_sync == post_minus_sync, (
        "AC.SFR.4 / HC#6: <workspace>/workspace/ files mutated by "
        "pos-sync outside its own state-record surface; D.3's "
        "structural-promise broken. "
        f"removed={set(pre_minus_sync) - set(post_minus_sync)!r} "
        f"added={set(post_minus_sync) - set(pre_minus_sync)!r}"
    )
