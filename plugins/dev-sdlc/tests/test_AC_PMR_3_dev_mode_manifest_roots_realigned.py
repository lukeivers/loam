"""AC.PMR.3 + AC.PMR.4 — dev-mode-manifest.yaml `roots:` and
`always_loaded:` blocks point at post-M6b.0 paths.

Per post-M6 partition realignment plan §4 AC.PMR.3 + AC.PMR.4: the
``plugins/dev-sdlc/dev-mode-manifest.yaml`` ``roots:`` (lines 36-64
pre-realignment) and ``always_loaded:`` (lines 78-110 pre-realignment)
blocks reference 14 component dirs rebased to ``framework/<comp>/``,
plus the ``graceful-degradation/`` → ``framework/dormancy/`` rename,
plus the ``framework/workspace-sync/`` ADD (a missing component
admission), plus ``tools/`` → ``framework/tools/`` and
``first-run-inventory.yaml`` → ``framework/first-run-inventory.yaml``.

This test exercises three branches:
  - roots-resolution: every ``roots:`` entry resolves on disk.
  - always_loaded-expansion: every ``always_loaded:`` glob/path
    expands to a non-empty match-set against canonical workspace.
  - explicit rename + ADD: ``framework/dormancy/`` is in roots
    (NOT ``graceful-degradation/`` and NOT
    ``framework/graceful-degradation/``); ``framework/workspace-sync/``
    is in roots.

Closes M1c-corrective plan-doc §16 HSF#1 (broader dev-mode-manifest
staleness).
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "plugins" / "dev-sdlc" / "dev-mode-manifest.yaml"


def _load_manifest():
    if not MANIFEST_PATH.is_file():
        pytest.skip("dev-mode-manifest not at expected location")
    # Use loam_mode's manifest reader (the runtime consumer).
    import sys

    loam_mode_src = (
        REPO_ROOT
        / "plugins"
        / "dev-sdlc"
        / "tools"
        / "loam-mode"
        / "src"
    )
    if loam_mode_src.exists() and str(loam_mode_src) not in sys.path:
        sys.path.insert(0, str(loam_mode_src))
    from loam_mode.manifest import load_manifest  # type: ignore[import-not-found]

    return load_manifest(MANIFEST_PATH)


def test_AC_PMR_3_every_root_resolves_on_disk() -> None:
    """Every entry under `roots:` resolves to an existing on-disk
    path within the canonical workspace."""
    manifest = _load_manifest()
    for root in manifest.roots:
        # Strip trailing `/` for path-resolution; both files and dirs
        # are admissible roots.
        rel = root.rstrip("/")
        target = REPO_ROOT / rel
        assert target.exists(), (
            f"roots: entry {root!r} does not resolve at {target}"
        )


def test_AC_PMR_3_dormancy_renamed_not_graceful_degradation() -> None:
    """The `graceful-degradation/` → `framework/dormancy/` rename
    landed: the new path is in roots, the old name (with or without
    `framework/` prefix) is NOT."""
    manifest = _load_manifest()
    roots = set(manifest.roots)
    assert "framework/dormancy/" in roots
    # Old name in either form must be gone.
    assert "graceful-degradation/" not in roots
    assert "framework/graceful-degradation/" not in roots


def test_AC_PMR_3_workspace_sync_added() -> None:
    """`framework/workspace-sync/` is admitted in roots (it was
    missing from the original sub-plan F authoring)."""
    manifest = _load_manifest()
    roots = set(manifest.roots)
    assert "framework/workspace-sync/" in roots


def test_AC_PMR_3_no_top_level_component_refs_remain() -> None:
    """No top-level component refs (the pre-M6b.0 shape) remain in
    roots. The 15 components live at `framework/<comp>/` post-M6b.0.

    This is the negative-control: any top-level dir matching the 15
    component names is a stale ref and a regression.
    """
    manifest = _load_manifest()
    stale_top_level = {
        "cost-governance/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "workspace-bootstrap/",
        "workspace-sync/",  # never had a top-level admission, but defensive
        "tools/",
    }
    roots = set(manifest.roots)
    intersection = roots & stale_top_level
    assert intersection == set(), (
        f"stale top-level roots remain: {intersection}"
    )


def test_AC_PMR_4_every_always_loaded_glob_resolves() -> None:
    """Every glob/path entry under `always_loaded:` expands to a
    non-empty match-set against the canonical workspace tree.

    Path-shaped entries: existence check via the workspace tree.
    Glob-shaped entries: at least one matching file in the tree.
    """
    import sys

    loam_mode_src = (
        REPO_ROOT
        / "plugins"
        / "dev-sdlc"
        / "tools"
        / "loam-mode"
        / "src"
    )
    if loam_mode_src.exists() and str(loam_mode_src) not in sys.path:
        sys.path.insert(0, str(loam_mode_src))
    from loam_mode.manifest import expand_entry  # type: ignore[import-not-found]

    manifest = _load_manifest()
    for entry in manifest.always_loaded:
        matches = expand_entry(entry, REPO_ROOT)
        assert matches, (
            f"always_loaded entry expanded empty: "
            f"path={entry.path!r} glob={entry.glob!r}"
        )


def test_AC_PMR_4_first_run_inventory_rebased() -> None:
    """`first-run-inventory.yaml` MOVED to
    `framework/first-run-inventory.yaml` post-M6b.0; the
    always_loaded entry references the new location."""
    manifest = _load_manifest()
    paths = {e.path for e in manifest.always_loaded if e.path}
    assert "framework/first-run-inventory.yaml" in paths
    assert "first-run-inventory.yaml" not in paths


def test_AC_PMR_4_data_stays_top_level() -> None:
    """`data/**` glob STAYS top-level (workspace runtime telemetry,
    not a component source surface)."""
    manifest = _load_manifest()
    globs = {e.glob for e in manifest.always_loaded if e.glob}
    assert "data/**" in globs


def test_AC_PMR_4_workspace_sync_admitted() -> None:
    """`framework/workspace-sync/**` glob is in always_loaded."""
    manifest = _load_manifest()
    globs = {e.glob for e in manifest.always_loaded if e.glob}
    assert "framework/workspace-sync/**" in globs
