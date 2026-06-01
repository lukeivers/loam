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

"""Work-visibility refresh-hook LOGIC (AC.WVS-FRESH.1 / .2).

The importable, testable core of the work-visibility refresh hook. The
thin stdlib shim at ``hooks/work_visibility_hook.py`` imports ``run`` /
``main`` from here so the hook entry-point is exercised in-process by
the AC suite (and the shim stays import-light for the pre-venv hook
spawn).

Persona-owned, lifecycle-driven refresh (AC.WVS-FRESH.2): registered on
the work-state-change / reinject-carrier events (SessionStart /
PreCompact / UserPromptSubmit / PostToolUse), Claude Code spawns the
shim with a JSON envelope on stdin; ``run`` regenerates the always-
openable status file (presenter (a)) and emits the live in-context
block (presenter (c)) as ``additionalContext`` — off the SHARED
aggregator.

Fail-closed (the statusline.py contract): any unhandled exception →
empty ``additionalContext`` + exit 0. Never raises out of a hook.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _resolve_workspace_root(envelope: dict[str, Any]) -> Path | None:
    """Resolve the workspace root from a hook stdin envelope.

    Prefer ``workspace.project_dir`` (the statusline precedent), fall
    back to top-level ``cwd``. Returns None when neither is present.
    """
    workspace = envelope.get("workspace")
    if isinstance(workspace, dict):
        project_dir = workspace.get("project_dir")
        if isinstance(project_dir, str) and project_dir:
            return Path(project_dir)
    cwd = envelope.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd)
    return None


def run(envelope: dict[str, Any]) -> dict[str, Any]:
    """Execute the refresh + return the Claude-Code hook output dict.

    Regenerates the status file (a) and produces the in-context block
    (c), both off the shared aggregator. On any failure returns an
    empty-additionalContext dict (fail-closed; AC.WVS-FRESH.2 + the
    fail-soft envelope mirroring AC.WVS-AGG.2 at the host boundary).
    """
    try:
        workspace_root = _resolve_workspace_root(envelope)
        if workspace_root is None:
            return {"hookSpecificOutput": {"additionalContext": ""}}

        from .work_visibility_presenters import (
            in_context_block,
            regenerate_status_file,
        )

        # (a) refresh the always-openable artifact.
        try:
            regenerate_status_file(workspace_root)
        except Exception:
            # A file-write failure must not block the in-context leg or
            # the host event (the aggregator already fails soft per
            # source — AC.WVS-AGG.2; this guards the write itself).
            pass

        # (c) the live in-context block.
        block = in_context_block(workspace_root)
        return {"hookSpecificOutput": {"additionalContext": block}}
    except Exception:
        return {"hookSpecificOutput": {"additionalContext": ""}}


def main() -> int:
    """CLI entry-point: read stdin envelope, run, print output, exit 0.

    Always exits 0 (fail-closed). Prints the hook output dict as JSON.
    """
    try:
        raw = sys.stdin.read()
        envelope = json.loads(raw) if raw.strip() else {}
        if not isinstance(envelope, dict):
            envelope = {}
    except Exception:
        envelope = {}
    output = run(envelope)
    try:
        sys.stdout.write(json.dumps(output))
    except Exception:
        pass
    return 0
