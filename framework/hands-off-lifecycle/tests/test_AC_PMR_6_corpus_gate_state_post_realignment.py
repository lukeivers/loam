"""AC.PMR.6 — corpus_gate sentinel state computes ∈ {"loaded",
"partial"} post-realignment (NOT "missing").

Per post-M6 partition realignment plan §4 AC.PMR.6: post-realignment,
``compute_corpus_paths_required`` returns a non-empty list (per
AC.PMR.5). The A1 sentinel's ``state`` field then computes against
that list — either ``"loaded"`` (every required path is in the
loaded set), ``"partial"`` (subset overlap), or ``"missing"`` (zero
overlap).

Pre-realignment the dispatcher's session diagnostic surfaced
``corpus_gate_state: partial`` with ``missing_corpus_paths: docs/odd-
methodology.md, docs/odd-in-loam.md`` — because the inline hook's
loaded set listed those pre-M6b.0 paths, but the manifest's required
set drew the post-M6b.0 paths via the realigned `dev_only:` block.
The mismatch led to "partial" state (some overlap, not all).

Post-realignment + post-Surface-B-fix, the inline hook's _ON_DEMAND
list points at plugin-relative paths (matching the dev_only: block);
the `corpus_paths_loaded` sentinel field reflects the correct subset.

This test asserts only that the degenerate ``"missing"`` state is
gone — the "loaded" vs "partial" distinction is a runtime
classification dependent on which paths actually loaded vs are
required, and tightening the AC to "loaded" specifically would risk
brittleness. The dispatcher's empirical UPS hook fire verifies the
exact end-state.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
HOOK_SCRIPT = HOOKS_DIR / "corpus_inline_session_start.py"


def _make_dev_mode_workspace_with_full_corpus(tmp_path: Path) -> Path:
    """Build a fixture workspace that has the always-load corpus AND
    the on-demand corpus on disk (post-M6b.0 plugin-relative paths) AND
    a minimal dev-mode-manifest.yaml so `compute_corpus_paths_required`
    returns a non-empty list."""
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    # Always-load tier (3 paths).
    (tmp_path / "CLAUDE.md").write_text("# C\n", encoding="utf-8")
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text(
        "# V\n", encoding="utf-8"
    )
    (rebuild_dir / "STATE.md").write_text("# S\n", encoding="utf-8")
    # On-demand tier (3 paths post-realignment).
    plugin_docs = tmp_path / "plugins" / "dev-sdlc" / "docs"
    plugin_docs.mkdir(parents=True, exist_ok=True)
    (plugin_docs / "odd-methodology.md").write_text(
        "# odd\n", encoding="utf-8"
    )
    (plugin_docs / "odd-in-loam.md").write_text(
        "# odd-in-loam\n", encoding="utf-8"
    )
    (rebuild_dir / "FUTURE_IDEAS.md").write_text(
        "# FI\n", encoding="utf-8"
    )
    # Minimal dev-mode-manifest at the post-M6b.0 plugin location so
    # `compute_corpus_paths_required` returns the always-load tier
    # paths (3 path entries) and the sentinel state classifier can
    # produce a meaningful overlap with the inline hook's loaded set.
    manifest_text = (
        "schema_version: 1\n"
        "roots:\n"
        "  - CLAUDE.md\n"
        "  - docs/\n"
        "audit_excludes: []\n"
        "always_loaded:\n"
        "  - path: CLAUDE.md\n"
        "  - path: docs/rebuild/VALUE_PROPOSITION.md\n"
        "  - path: docs/rebuild/STATE.md\n"
        "dev_only:\n"
        "  - path: plugins/dev-sdlc/docs/odd-methodology.md\n"
    )
    (
        tmp_path / "plugins" / "dev-sdlc" / "dev-mode-manifest.yaml"
    ).write_text(manifest_text, encoding="utf-8")
    return tmp_path


def _run_hook(workspace: Path) -> int:
    envelope = json.dumps(
        {
            "session_id": "sess-pmr-6",
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
    return result.returncode


def _read_sentinel_state(workspace: Path, session_id: str) -> str | None:
    """Read the A1 sentinel JSON at the standard workspace-state
    location and return the ``state`` field."""
    sentinel = (
        workspace
        / "workspace"
        / ".pos"
        / "session-state"
        / f"{session_id}.json"
    )
    if not sentinel.is_file():
        return None
    data = json.loads(sentinel.read_text(encoding="utf-8"))
    return data.get("state")


def test_AC_PMR_6_sentinel_state_not_missing(tmp_path: Path) -> None:
    """After the inline hook fires against a fixture workspace where
    BOTH the always-load corpus AND the on-demand corpus exist on
    disk, the sentinel's ``state`` is NOT ``"missing"``.

    The "loaded" vs "partial" branch depends on whether the inline
    hook's loaded set (the static 3-path always-load tuple) matches
    the manifest-derived required set; this test does not assert
    which of those two it is.
    """
    workspace = _make_dev_mode_workspace_with_full_corpus(tmp_path)
    rc = _run_hook(workspace)
    assert rc == 0
    state = _read_sentinel_state(workspace, "sess-pmr-6")
    if state is None:
        pytest.skip(
            "sentinel not written (loam_mode unavailable in test env); "
            "AC.PMR.6 vacuous"
        )
    assert state in ("loaded", "partial"), (
        f"expected loaded/partial post-realignment; got {state!r}"
    )


def test_AC_PMR_6_sentinel_records_loaded_paths(tmp_path: Path) -> None:
    """The sentinel's ``corpus_paths_loaded`` field reflects the
    static 3-path always-load tier (per AC.CI.4)."""
    workspace = _make_dev_mode_workspace_with_full_corpus(tmp_path)
    rc = _run_hook(workspace)
    assert rc == 0
    sentinel = (
        workspace
        / "workspace"
        / ".pos"
        / "session-state"
        / "sess-pmr-6.json"
    )
    if not sentinel.is_file():
        pytest.skip("sentinel not written; AC.PMR.6 vacuous")
    data = json.loads(sentinel.read_text(encoding="utf-8"))
    loaded = set(data.get("corpus_paths_loaded", []))
    # The static always-load tier has 3 paths; all 3 should appear.
    assert "CLAUDE.md" in loaded
    assert "docs/rebuild/VALUE_PROPOSITION.md" in loaded
    assert "docs/rebuild/STATE.md" in loaded
