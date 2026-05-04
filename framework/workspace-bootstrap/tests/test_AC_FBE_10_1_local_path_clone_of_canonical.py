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

"""AC.WBM2M.2 — local-path clones of canonical land on ``main``.

Successor to AC.FBE.10.2 (now superseded by the OSS dev-architecture
migration, 2026-05-04). Pre-migration the bootstrap targeted the
synthesis-only ``framework-only`` branch, which was a non-default
branch on canonical and therefore exposed the FBE.10 BLOCKER (a
stranger's local clone of canonical carried ``framework-only`` only as
``refs/remotes/origin/framework-only``, not as a local branch).

Post-migration the bootstrap targets canonical's default branch
``main``, which IS a local branch on any stranger-clone (because
``git clone`` propagates the source's default branch as a local ref
automatically). The materialise helper is a defensive no-op on this
typical case but stays for symmetry with cache-clone scenarios.

This test reproduces a stranger's clone-of-canonical → bootstrap-
against-the-clone flow (the post-FBE.9 cwd-default-when-git-tree
pattern: stranger clones loam, cd's in, runs ``loam init <ws>`` with
no ``--from``) and verifies the post-migration bootstrap lands a
working workspace on ``main``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam.workspace_bootstrap.new_workspace import bootstrap_new_workspace


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(  # noqa: S603 — argv constructed
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")


def test_AC_WBM2M_2_local_path_clone_of_canonical_lands_on_main(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """A bootstrap against a stranger's clone-of-canonical succeeds.

    AC.WBM2M.2: the case the FBE.9 stranger-flow smoke uncovered
    (``loam init <ws>`` from inside a cloned loam tree, with the cwd
    auto-resolved as ``--from``) must work end-to-end. Post-OSS-dev-
    architecture-migration: completes cleanly with the workspace's
    framework subdir checked out on ``main``.
    """
    # Step 1: build fixture canonical. This produces a git working
    # tree on ``main`` (per the post-migration `make_fixture_canonical`
    # default).
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # Step 2: clone the fixture canonical into a "stranger-clone"
    # path. After the clone, ``main`` IS a local branch on the
    # stranger-clone (canonical's default branch is propagated by
    # ``git clone`` automatically).
    stranger_clone = tmp_path / "stranger-clone"
    _git(
        ["clone", str(canonical), str(stranger_clone)],
        cwd=tmp_path,
    )

    # Sanity: confirm ``main`` is a local branch on the stranger-clone
    # (no materialise step needed; the helper is defensive).
    local_branches = _git(
        ["branch", "--list", "main"], cwd=stranger_clone
    )
    assert "main" in local_branches, (
        "fixture pre-condition: stranger-clone must have main as a "
        f"local branch (canonical's default); got: {local_branches!r}"
    )

    # Step 3: bootstrap against the stranger-clone (the post-FBE.9
    # cwd-default-when-git-tree case).
    new_ws = tmp_path / "ws"
    result = bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(stranger_clone),
    )

    # Step 4: workspace shape correct (mirrors AC.D.4.* surface).
    assert result.framework_dir.is_dir()
    assert (result.framework_dir / ".git").exists()
    assert result.workspace_state_dir.is_dir()
    assert result.sync_config_path.exists()
    assert result.claude_dir.is_dir()
    assert (result.claude_dir / "settings.json").exists()

    # Step 5: framework subdir is checked out on ``main`` (the
    # canonical default branch the bootstrap MUST land on per
    # AC.WBM2M.2).
    framework_branch = _git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=result.framework_dir
    )
    assert framework_branch == "main", (
        "AC.WBM2M.2: workspace's framework subdir must be checked "
        "out on main post-bootstrap; got: "
        f"{framework_branch!r}"
    )
