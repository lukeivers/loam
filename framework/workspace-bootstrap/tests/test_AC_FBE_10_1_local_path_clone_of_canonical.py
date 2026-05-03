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

"""AC.FBE.10.2 — local-path clones of canonical materialise framework-only.

FBE.10 closes BLOCKER-FBE9.1 (surfaced by FBE.9 stranger-flow smoke):
``bootstrap_new_workspace``'s local-path branch took the source path
directly to ``_clone_canonical`` without the ``framework-only``
materialisation step that ``_resolve_url_to_clone_source`` runs for
URL-form. When ``local_path`` is a stranger's ``git clone
<canonical-url>`` of canonical (the typical post-FBE.9
cwd-default-when-git-tree pattern), ``framework-only`` exists only as
``refs/remotes/origin/framework-only`` on ``local_path`` — and the
downstream ``_clone_canonical`` checkout step then fails with
``fatal: 'origin/framework-only' is not a commit``.

This test reproduces that exact case (clone-of-canonical → bootstrap
against the clone) and verifies the post-FBE.10 fix produces a
working workspace.
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


def test_AC_FBE_10_1_local_path_clone_of_canonical_materialises_framework_only(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """A bootstrap against a stranger's clone-of-canonical succeeds.

    AC.FBE.10.2: the case the FBE.9 stranger-flow smoke uncovered
    (``loam init <ws>`` from inside a cloned loam tree, with the cwd
    auto-resolved as ``--from``) must work end-to-end. Pre-FBE.10:
    raises ``CloneFailedError`` at the ``git checkout -B framework-only
    origin/framework-only`` step. Post-FBE.10: completes cleanly with
    the workspace's framework subdir checked out on ``framework-only``.
    """
    # Step 1: build fixture canonical. This produces a git working
    # tree with `framework-only` as a LOCAL branch (per
    # `make_fixture_canonical(publish_framework_only=True)` default).
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # Step 2: clone the fixture canonical into a "stranger-clone"
    # path. After the clone, `framework-only` exists ONLY as
    # `refs/remotes/origin/framework-only` on the stranger-clone —
    # NOT as a local branch — exactly mirroring the post-FBE.9
    # cwd-default-when-git-tree case (a stranger ran
    # `git clone <canonical-url>`).
    stranger_clone = tmp_path / "stranger-clone"
    _git(
        ["clone", str(canonical), str(stranger_clone)],
        cwd=tmp_path,
    )

    # Verify the bug pre-condition: `framework-only` is NOT a local
    # branch on the stranger-clone (only `pos-v2`, the default).
    local_branches = _git(
        ["branch", "--list", "framework-only"], cwd=stranger_clone
    )
    assert local_branches.strip() == "", (
        "fixture pre-condition: stranger-clone must not have "
        "framework-only as a local branch (only as a remote-tracking "
        f"ref); got: {local_branches!r}"
    )
    # Sanity: confirm the remote-tracking ref is present (so the
    # materialisation step has something to point at).
    remote_branches = _git(
        ["branch", "-r", "--list", "origin/framework-only"],
        cwd=stranger_clone,
    )
    assert "origin/framework-only" in remote_branches, (
        "fixture pre-condition: stranger-clone must have "
        "origin/framework-only as a remote-tracking ref; got: "
        f"{remote_branches!r}"
    )

    # Step 3: bootstrap against the stranger-clone (the post-FBE.9
    # cwd-default-when-git-tree case). Pre-FBE.10: raises
    # CloneFailedError. Post-FBE.10: returns BootstrapResult cleanly.
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

    # Step 5: framework subdir is checked out on `framework-only`
    # (the synthetic branch the bootstrap MUST land on per AC.SFR.1).
    framework_branch = _git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=result.framework_dir
    )
    assert framework_branch == "framework-only", (
        "AC.FBE.10.2: workspace's framework subdir must be checked "
        "out on framework-only post-bootstrap; got: "
        f"{framework_branch!r}"
    )
