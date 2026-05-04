"""Workspace ``safety_profile`` reader for loam-pr-safety.

Per AC.PRSG.8 — composes on
:func:`loam.workspace_bootstrap.load_manifest` (v0.1.6 Cycle 1).
Production-stake demands ``requires_ratification=True`` on every
SURFACE-DECISION; dev / research default to proceed-with-warning.

Per F2 RF gap §10.8 — no caching. Cycle 1 gate is one-shot
(invoked-on-demand); manifest reads are microseconds. Hooks (Cycle 2)
fire at most tens-per-day; still negligible.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap import load_manifest
from loam.workspace_bootstrap.manifest import (
    DEFAULT_SAFETY_PROFILE,
    LEGAL_SAFETY_PROFILES,
)


def read_safety_profile(workspace_root: Path) -> str:
    """Read ``safety_profile`` from the workspace manifest.

    Resolution order:
      1. ``<workspace_root>/loam.yaml`` — the canonical location.
      2. Manifest absent → :data:`DEFAULT_SAFETY_PROFILE` (= ``dev``).
      3. Manifest present but malformed → re-raises the underlying
         ``MissingConfigError`` (caller halts).

    Returns one of :data:`LEGAL_SAFETY_PROFILES`.
    """
    manifest_path = (
        workspace_root.expanduser().resolve() / "loam.yaml"
    )
    if not manifest_path.exists():
        return DEFAULT_SAFETY_PROFILE
    manifest = load_manifest(manifest_path)
    return manifest.safety_profile


def is_production_stake(workspace_root: Path) -> bool:
    """Return ``True`` iff the workspace's ``safety_profile`` is
    ``production-stake``.

    Per AC.PRSG.8 — the strict floor flag. Used by
    :func:`loam_pr_safety.gate.decide` to flip
    ``requires_ratification`` to ``True`` on SURFACE-DECISION
    actions.
    """
    return read_safety_profile(workspace_root) == "production-stake"


__all__ = [
    "DEFAULT_SAFETY_PROFILE",
    "LEGAL_SAFETY_PROFILES",
    "is_production_stake",
    "read_safety_profile",
]
