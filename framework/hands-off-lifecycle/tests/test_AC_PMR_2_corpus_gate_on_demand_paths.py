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
    """The `_ON_DEMAND` tuple's first two entries are the post-M6b.0
    plugin-relative paths."""
    sys.path.insert(0, str(HOOKS_DIR))
    try:
        import corpus_inline_session_start as mod  # type: ignore[import-not-found]
    finally:
        try:
            sys.path.remove(str(HOOKS_DIR))
        except ValueError:
            pass
    assert mod._ON_DEMAND[:2] == (
        "plugins/dev-sdlc/docs/odd-methodology.md",
        "plugins/dev-sdlc/docs/odd-in-loam.md",
    )
    # Third entry unchanged.
    assert mod._ON_DEMAND[2] == "docs/rebuild/FUTURE_IDEAS.md"


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
    assert "- docs/rebuild/FUTURE_IDEAS.md" in block
    # Pre-realignment paths must NOT appear (they would mislead the
    # reader if both shapes were emitted).
    assert "- docs/odd-methodology.md\n" not in block
    assert "- docs/odd-in-loam.md\n" not in block
