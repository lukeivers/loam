"""AC.SE.5 — workspace-mode partition is honoured by the corpus-load hook.

Per the locked plan-doc §4 AC.SE.5: when the workspace-mode bit is
``"normal-use"`` the corpus-load sentinel hook still writes a
sentinel, BUT its ``corpus_paths_required`` reflects the NORMAL-USE
always-loaded set (smaller — DEV-MODE-only paths excluded). When
``"dev-mode"``, the required set is the full DEV-MODE always-loaded
set. This ensures A2/A3/A4 gates that consult the sentinel produce
mode-correct decisions without each gate re-computing the partition.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from corpus_load_sentinel import (  # noqa: E402
    compute_corpus_paths_required,
    write_corpus_load_sentinel,
)


def _seed_minimal_workspace(workspace_root: Path) -> None:
    """Copy enough of the canonical workspace into ``workspace_root``
    to make the dev-mode-manifest resolvable + the always-loaded /
    dev-only files exist, so AC.SE.5 can verify the mode-aware
    required set."""
    # Real manifest copied verbatim — one file. Post-M6b.0 the
    # manifest lives at plugins/dev-sdlc/dev-mode-manifest.yaml; the
    # in-test mirror writes to BOTH possible locations so the
    # corpus-load partition mechanism resolves regardless of which
    # path the loam-mode probe-and-prefer logic prefers in the
    # synthetic workspace.
    src_manifest = (
        REPO_ROOT
        / "plugins"
        / "dev-sdlc"
        / "dev-mode-manifest.yaml"
    )
    target_manifest = (
        workspace_root
        / "plugins"
        / "dev-sdlc"
        / "dev-mode-manifest.yaml"
    )
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_manifest, target_manifest)
    # Also seed the legacy docs/rebuild/ location for tests that may
    # still reference it through downstream code that hasn't yet
    # been updated; both paths resolve to the same byte-content.
    legacy_target = (
        workspace_root
        / "docs"
        / "rebuild"
        / "dev-mode-manifest.yaml"
    )
    legacy_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_manifest, legacy_target)

    # Stub each top-level always-loaded surface with a sentinel file
    # so existence checks resolve. CLAUDE.md + CLAUDE.dev.md +
    # README.md + first-run-inventory.yaml at root.
    for name in ("CLAUDE.md", "CLAUDE.dev.md", "README.md", "first-run-inventory.yaml"):
        (workspace_root / name).write_text("stub", encoding="utf-8")
    # Top-level dirs the manifest names.
    for d in (
        "cost-governance",
        "graceful-degradation",
        "hands-off-lifecycle",
        "memory-system",
        "objective-tracker",
        "observability-aggregator",
        "orchestrator",
        "primary-persona",
        "reversibility-primitive",
        "safety-layer",
        "scope-of-work",
        "self-correction",
        "self-upgrade",
        "telegram-interface",
        "workspace-bootstrap",
        "docs",
        "tools",
        "data",
    ):
        (workspace_root / d).mkdir(parents=True, exist_ok=True)


def test_AC_SE_5_normal_use_required_set_excludes_dev_only(
    tmp_path: Path,
) -> None:
    """In ``normal-use`` mode, ``corpus_paths_required`` does not
    contain ``CLAUDE.dev.md`` (the dev-only file)."""
    _seed_minimal_workspace(tmp_path)
    paths = compute_corpus_paths_required(tmp_path, "normal-use")
    assert "CLAUDE.dev.md" not in paths


def test_AC_SE_5_dev_mode_required_set_includes_dev_only(
    tmp_path: Path,
) -> None:
    """In ``dev-mode``, ``corpus_paths_required`` includes
    ``CLAUDE.dev.md``."""
    _seed_minimal_workspace(tmp_path)
    paths = compute_corpus_paths_required(tmp_path, "dev-mode")
    assert "CLAUDE.dev.md" in paths


def test_AC_SE_5_normal_use_writes_sentinel_with_mode_correct_required(
    tmp_path: Path,
) -> None:
    """End-to-end: write_corpus_load_sentinel in normal-use mode
    writes a sentinel whose corpus_paths_required excludes dev-only
    paths."""
    _seed_minimal_workspace(tmp_path)
    write_corpus_load_sentinel(
        tmp_path, session_id="normal-1", mode="normal-use"
    )
    on_disk = json.loads(
        (tmp_path / "workspace" / ".pos" / "session-state" / "normal-1.json").read_text()
    )
    assert "CLAUDE.dev.md" not in on_disk["corpus_paths_required"]


def test_AC_SE_5_dev_mode_writes_sentinel_with_mode_correct_required(
    tmp_path: Path,
) -> None:
    """End-to-end: dev-mode sentinel includes dev-only paths."""
    _seed_minimal_workspace(tmp_path)
    write_corpus_load_sentinel(
        tmp_path, session_id="dev-1", mode="dev-mode"
    )
    on_disk = json.loads(
        (tmp_path / "workspace" / ".pos" / "session-state" / "dev-1.json").read_text()
    )
    assert "CLAUDE.dev.md" in on_disk["corpus_paths_required"]


def test_AC_SE_5_writes_sentinel_even_when_manifest_missing(
    tmp_path: Path,
) -> None:
    """AC.SE.5 explicit clause: 'still writes a sentinel' even on
    fail-soft (missing manifest). The state field surfaces the
    degradation."""
    # No _seed_minimal_workspace — manifest is absent.
    result = write_corpus_load_sentinel(
        tmp_path, session_id="degraded", mode="normal-use"
    )
    assert result.wrote is True
    on_disk = json.loads(
        (tmp_path / "workspace" / ".pos" / "session-state" / "degraded.json").read_text()
    )
    # Manifest unreadable → empty required-set → state = missing.
    assert on_disk["state"] == "missing"
    assert on_disk["corpus_paths_required"] == []
