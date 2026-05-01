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

"""Amendment #36 — AC36.3 — Re-running first-run on a workspace with
an existing persona directory is a no-op.

Plan §4 AC36.3 outcomes:

- Re-run does NOT overwrite ``contract.yaml`` or ``prompt.md``.
- Re-run does NOT regenerate the directory tree.
- Re-run does NOT modify ``is_starter`` regardless of its current value.
- Re-run does NOT raise — first-run completes successfully.

Behaviour holds whether ``is_starter`` is currently True (an earlier
first-run completed but elicitation hasn't run) or False (the user
has completed elicitation or hand-edited the contract).

Maps to v1.0 line 152 (low-friction; no surprise overwrites) +
v1.2 R16 (workspace-supplied content remains workspace-owned) →
AC.PO.1.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import yaml

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    _install_persona_directory,
    run_first_run_scaffold,
)


def _scaffold_fresh(tmp_path: Path, suffix: str = "") -> Path:
    workspace = tmp_path / f"ws-rerun{suffix}"
    workspace.mkdir()
    pos_root = tmp_path / f".pos{suffix}"
    agents = tmp_path / f"LaunchAgents{suffix}"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace


def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _snapshot(persona_dir: Path) -> dict[str, tuple[float, str]]:
    """Return mtime + content-hash for each file in the persona dir."""
    out: dict[str, tuple[float, str]] = {}
    for f in persona_dir.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(persona_dir))
            out[rel] = (f.stat().st_mtime, _hash(f))
    return out


def test_AC36_3_re_install_is_noop_with_is_starter_true(tmp_path: Path) -> None:
    """The persona-dir installer is idempotent: a second call leaves
    contract.yaml + prompt.md mtimes + content hashes unchanged."""
    workspace = _scaffold_fresh(tmp_path)
    persona_dir = workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE

    pre = _snapshot(persona_dir)
    # Sleep briefly so any spurious write would alter mtime detectably.
    time.sleep(0.05)
    installed, returned_dir = _install_persona_directory(
        workspace_root=workspace,
        handle=DEFAULT_PERSONA_HANDLE,
    )
    post = _snapshot(persona_dir)

    assert installed is False, "second install reported writing — must be idempotent"
    assert returned_dir == persona_dir.resolve()
    assert pre == post, "persona-dir contents/mtimes changed on re-install"


def test_AC36_3_re_install_is_noop_with_is_starter_false(tmp_path: Path) -> None:
    """If the user has completed elicitation (``is_starter: false``),
    a re-install must not flip the field back to true and must not
    overwrite the contract."""
    workspace = _scaffold_fresh(tmp_path)
    persona_dir = workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
    contract_path = persona_dir / "contract.yaml"

    # Simulate elicitation completion by flipping the flag on disk.
    parsed = yaml.safe_load(contract_path.read_text())
    parsed["is_starter"] = False
    parsed["given_name"] = "Iris"
    contract_path.write_text(
        yaml.safe_dump(parsed, sort_keys=False, default_flow_style=False)
    )

    pre = _snapshot(persona_dir)
    time.sleep(0.05)
    installed, _ = _install_persona_directory(
        workspace_root=workspace,
        handle=DEFAULT_PERSONA_HANDLE,
    )
    post = _snapshot(persona_dir)

    assert installed is False
    assert pre == post

    # Re-read contract — flag must still be False, given_name still Iris.
    re_read = yaml.safe_load(contract_path.read_text())
    assert re_read["is_starter"] is False
    assert re_read["given_name"] == "Iris"


def test_AC36_3_full_scaffold_re_run_does_not_raise(tmp_path: Path) -> None:
    """Re-running ``run_first_run_scaffold`` against a fully-scaffolded
    workspace returns the ``already_scaffolded`` short-circuit and
    leaves the persona directory unchanged."""
    workspace = _scaffold_fresh(tmp_path)
    persona_dir = workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
    pre = _snapshot(persona_dir)
    time.sleep(0.05)

    # Re-run the full scaffold against the same pos_root + workspace.
    result = run_first_run_scaffold(
        pos_root=tmp_path / ".pos",
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=workspace,
    )
    assert result.ran is False
    assert result.reason == "already_scaffolded"

    post = _snapshot(persona_dir)
    assert pre == post
