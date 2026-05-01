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

"""AC.CI.2 — on-demand-tier path-pointer block emitted (DEV MODE).

Per the locked plan-doc §4 AC.CI.2: on a DEV MODE session-start, the
hook ALSO emits a structured pointer block listing the workspace-
relative paths of every on-demand-tier corpus file. Entries are
workspace-relative paths only (no section-anchor extraction in this
hook). Missing on-demand files are silently omitted from the pointer
block (no ``[missing]`` marker — that's the always-load tier's
contract).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SCRIPT = (
    REPO_ROOT
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "corpus_inline_session_start.py"
)


def _make_dev_mode_workspace(
    tmp_path: Path, *, with_on_demand: bool = True
) -> Path:
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text("# C\n", encoding="utf-8")
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text("# V\n", encoding="utf-8")
    (rebuild_dir / "STATE.md").write_text("# S\n", encoding="utf-8")
    if with_on_demand:
        # Post-M6b.0 + AC.PMR.2: ODD docs MOVED to plugins/dev-sdlc/
        # docs/. The hook's _ON_DEMAND tuple now points at the plugin-
        # relative locations.
        plugin_docs_dir = tmp_path / "plugins" / "dev-sdlc" / "docs"
        plugin_docs_dir.mkdir(parents=True, exist_ok=True)
        (plugin_docs_dir / "odd-methodology.md").write_text(
            "# odd-methodology\n", encoding="utf-8"
        )
        (plugin_docs_dir / "odd-in-loam.md").write_text(
            "# odd-in-loam\n", encoding="utf-8"
        )
        (rebuild_dir / "FUTURE_IDEAS.md").write_text(
            "# FUTURE_IDEAS\n", encoding="utf-8"
        )
    return tmp_path


def _run_hook(workspace: Path) -> tuple[str, int]:
    envelope = json.dumps(
        {
            "session_id": "sess-on-demand",
            "workspace": {"project_dir": str(workspace)},
        }
    )
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout, result.returncode


def test_AC_CI_2_emits_on_demand_pointer_block(tmp_path: Path) -> None:
    """All on-demand files present → pointer block lists each file
    on its own line, prefixed with ``- ``."""
    workspace = _make_dev_mode_workspace(tmp_path, with_on_demand=True)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    assert "=== pos-v2 on-demand corpus" in stdout
    assert "- plugins/dev-sdlc/docs/odd-methodology.md" in stdout
    assert "- plugins/dev-sdlc/docs/odd-in-loam.md" in stdout
    assert "- docs/rebuild/FUTURE_IDEAS.md" in stdout


def test_AC_CI_2_omits_missing_on_demand_files(tmp_path: Path) -> None:
    """Missing on-demand files are NOT emitted with a ``[missing]``
    marker (that's the always-load tier's contract); they are
    silently omitted from the pointer block."""
    workspace = _make_dev_mode_workspace(tmp_path, with_on_demand=True)
    # Remove odd-methodology.md (post-M6b.0 plugin-relative path).
    (
        workspace / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"
    ).unlink()
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    # The pointer block exists.
    block_idx = stdout.index("=== pos-v2 on-demand corpus")
    block = stdout[block_idx:]
    # odd-methodology.md is omitted — no `- plugins/dev-sdlc/docs/odd-
    # methodology.md` line and NO `[missing]` marker for it.
    assert "- plugins/dev-sdlc/docs/odd-methodology.md" not in block
    assert "[missing]" not in block.split("=== pos-v2 on-demand corpus")[1]
    # Other on-demand files still listed.
    assert "- plugins/dev-sdlc/docs/odd-in-loam.md" in block
    assert "- docs/rebuild/FUTURE_IDEAS.md" in block


def test_AC_CI_2_pointer_entries_are_workspace_relative_paths(
    tmp_path: Path,
) -> None:
    """Pointer block entries are workspace-relative paths only — no
    section-anchor extraction (out-of-scope per plan §7)."""
    workspace = _make_dev_mode_workspace(tmp_path, with_on_demand=True)
    stdout, _rc = _run_hook(workspace)
    block_idx = stdout.index("=== pos-v2 on-demand corpus")
    block = stdout[block_idx:]
    # Each pointer entry starts with `- ` followed by a path-shaped
    # token; no `#` (section anchors) appear.
    pointer_lines = [
        line for line in block.splitlines()
        if line.startswith("- ")
    ]
    assert pointer_lines  # at least one
    for line in pointer_lines:
        assert "#" not in line, (
            f"Pointer entry should not contain a section anchor: {line!r}"
        )
