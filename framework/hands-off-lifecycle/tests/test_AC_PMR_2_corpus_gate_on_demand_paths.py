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

"""AC.PMR.2 — corpus_inline_session_start.py `_ON_DEMAND` tuple
points at post-M6b.0 plugin-relative ODD doc paths.

Per post-M6 partition realignment plan §4 AC.PMR.2: the SessionStart
corpus inline hook's on-demand pointer block now references the
plugin-relative ODD doc locations (post-M6b.0 the long-form ODD docs
MOVED to ``plugins/dev-sdlc/docs/`` per AC.OSS-M6b0.5).

This test exercises BOTH branches:
  - Constant-shape: ``_ON_DEMAND[:2]`` carries the plugin-relative
    paths.
  - End-to-end: SessionStart envelope drives ``main()`` against a
    fixture workspace where the plugin docs exist on disk; the
    rendered on-demand block lists both plugin-relative paths.

Closes the today's-session diagnostic where the gate reported
``corpus_gate_state: partial`` with ``missing_corpus_paths: docs/odd-
methodology.md, docs/odd-in-loam.md`` — the path-list now matches
the post-M6b.0 location.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
HOOK_SCRIPT = HOOKS_DIR / "corpus_inline_session_start.py"


def test_AC_PMR_2_on_demand_constant_points_at_plugin_paths() -> None:
    """The `_ON_DEMAND` tuple carries the post-M6b.0 plugin-relative
    ODD-doc paths. C2-prime amendment §11 D-Q.ABC-prime.2 STRIPPED
    the prior third entry (``docs/rebuild/FUTURE_IDEAS.md``) — the
    AC.PMR.2 intent ("on-demand pointer block lists plugin paths")
    is preserved; only the FUTURE_IDEAS pointer was retired (no
    public counterpart). ODD §4 in-band rebaseline per
    `feedback_loose_AC_text_fix_AC_not_implementation`.
    """
    sys.path.insert(0, str(HOOKS_DIR))
    try:
        import corpus_inline_session_start as mod  # type: ignore[import-not-found]
    finally:
        try:
            sys.path.remove(str(HOOKS_DIR))
        except ValueError:
            pass
    assert mod._ON_DEMAND == (
        "plugins/dev-sdlc/docs/odd-methodology.md",
        "plugins/dev-sdlc/docs/odd-in-loam.md",
    )


def _make_dev_mode_workspace_with_plugin_docs(tmp_path: Path) -> Path:
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
    (rebuild_dir / "FUTURE_IDEAS.md").write_text(
        "# FUTURE_IDEAS\n", encoding="utf-8"
    )
    plugin_docs = tmp_path / "plugins" / "dev-sdlc" / "docs"
    plugin_docs.mkdir(parents=True, exist_ok=True)
    (plugin_docs / "odd-methodology.md").write_text(
        "# ODD methodology\n", encoding="utf-8"
    )
    (plugin_docs / "odd-in-loam.md").write_text(
        "# ODD in loam\n", encoding="utf-8"
    )
    return tmp_path


def _run_hook(workspace: Path) -> tuple[str, int]:
    envelope = json.dumps(
        {
            "session_id": "sess-pmr-2",
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


def test_AC_PMR_2_e2e_on_demand_block_lists_plugin_paths(
    tmp_path: Path,
) -> None:
    """End-to-end: SessionStart envelope through `main()` against a
    fixture workspace where the plugin docs exist on disk; the
    rendered on-demand block lists both plugin-relative paths."""
    workspace = _make_dev_mode_workspace_with_plugin_docs(tmp_path)
    stdout, rc = _run_hook(workspace)
    assert rc == 0, f"hook exit {rc}; stdout={stdout!r}"
    block_idx = stdout.index("=== pos-v2 on-demand corpus")
    block = stdout[block_idx:]
    assert "- plugins/dev-sdlc/docs/odd-methodology.md" in block
    assert "- plugins/dev-sdlc/docs/odd-in-loam.md" in block
    # FUTURE_IDEAS.md pointer STRIPPED at C2-prime per §11 D-Q.ABC-
    # prime.2 — no public counterpart, so the on-demand block no
    # longer references it. AC.PMR.2 intent preserved.
    assert "- docs/rebuild/FUTURE_IDEAS.md" not in block
    # Pre-realignment paths must NOT appear (they would mislead the
    # reader if both shapes were emitted).
    assert "- docs/odd-methodology.md\n" not in block
    assert "- docs/odd-in-loam.md\n" not in block
