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

"""AC.OGP.2 — Lean grounding doc inlined into ``additionalContext``.

Per v0.2.2 sub-plan-doc §3 AC.OGP.2: the corpus-inline SessionStart
hook's ``_ALWAYS_LOAD`` tuple includes
``docs/odd-llm-grounding.lean.md``; on a DEV-MODE SessionStart fan-out,
the hook emits the lean grounding doc's literal byte content under
its per-file delimiter.

Mirrors the AC.CI.1 test pattern: synthetic DEV-MODE workspace; run
the hook; assert content + delimiter present in stdout.
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


def _make_dev_mode_workspace(tmp_path: Path) -> Path:
    """Set up a DEV-MODE workspace with all _ALWAYS_LOAD files present.

    Mirrors the AC.CI.1 fixture pattern; adds the lean grounding doc
    body so the hook has bytes to inline.
    """
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text(
        "# Workspace CLAUDE\n\nClaude is the model.\n",
        encoding="utf-8",
    )
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text(
        "# VALUE_PROPOSITION\n\nPrime objective text here.\n",
        encoding="utf-8",
    )
    (rebuild_dir / "STATE.md").write_text(
        "# STATE\n\nCurrent cycle status.\n",
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs"
    (docs_dir / "odd-llm-grounding.lean.md").write_text(
        "# ODD — LLM context prime (lean)\n\n"
        "Failure mode this prevents: implementation-altitude facts "
        "labeled as ACs (signature v0.1.8 drift).\n",
        encoding="utf-8",
    )
    return tmp_path


def _run_hook(workspace: Path, session_id: str = "sess-ogp-2") -> tuple[str, int]:
    envelope = json.dumps(
        {
            "session_id": session_id,
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


def test_AC_OGP_2_lean_grounding_emitted_in_always_load_block(
    tmp_path: Path,
) -> None:
    """DEV MODE; lean grounding doc present → stdout contains its
    delimiter and its content under the always-load block."""
    workspace = _make_dev_mode_workspace(tmp_path)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    assert "=== pos-v2 always-loaded corpus (DEV MODE) ===" in stdout
    assert "--- docs/odd-llm-grounding.lean.md ---" in stdout
    assert "ODD — LLM context prime (lean)" in stdout
    assert (
        "implementation-altitude facts labeled as ACs" in stdout
    ), (
        "AC.OGP.2: lean grounding doc body must reach stdout under "
        "its per-file delimiter."
    )


def test_AC_OGP_2_lean_grounding_missing_marker_when_absent(
    tmp_path: Path,
) -> None:
    """DEV MODE; lean grounding doc absent → ``[missing]`` slot at
    the lean grounding doc's delimiter; other always-load files
    still emit their content (fail-soft per AC.CI.7)."""
    workspace = _make_dev_mode_workspace(tmp_path)
    (workspace / "docs" / "odd-llm-grounding.lean.md").unlink()
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    # Other always-load content still emitted.
    assert "Claude is the model." in stdout
    assert "Prime objective text here." in stdout
    # Missing-file marker at the lean grounding doc's slot.
    lean_idx = stdout.index("--- docs/odd-llm-grounding.lean.md ---")
    rest = stdout[lean_idx:]
    assert "[missing]" in rest, (
        "AC.OGP.2 fail-soft: absent lean grounding doc emits "
        "[missing] marker per AC.CI.1 contract."
    )
