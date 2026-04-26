"""Clause-(h) canonical-as-source pull adapter.

Today self-upgrade expects a pre-unpacked staging tree at
``--staging-dir``. This module adds a parallel ``--canonical <path>``
mode that resolves the manifest + staging tree from a local canonical
git working tree without rebuilding ``execute_upgrade``'s pipeline:
the canonical tree IS the staging shape, so ``staging_dir`` resolves
directly to ``canonical_path``.

Argparse-side: ``--canonical`` and ``--staging-dir`` are mutually
exclusive (one of the two is required). When ``--canonical`` is
present and ``--manifest`` is absent, the manifest path is derived
from the tag against
``<canonical_path>/self-upgrade/manifests/<tag>.yaml`` by default.

A future amendment will compose ``--canonical <git-url>`` to fetch a
remote into a tmp worktree; the local-path form here is the minimum
surface needed for the canonical-as-released-from case.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .manifest import Manifest, load_manifest


@dataclass(frozen=True)
class StagingResolution:
    """Resolved (staging_dir, manifest) tuple for canonical-pull mode."""

    staging_dir: Path
    manifest: Manifest
    manifest_path: Path


class CanonicalPullError(Exception):
    """Raised on malformed/missing canonical inputs."""


def default_manifest_path(canonical_path: Path, tag: str) -> Path:
    """Return the conventional manifest location inside canonical."""
    return canonical_path / "self-upgrade" / "manifests" / f"{tag}.yaml"


def resolve_canonical_to_staging(
    canonical_path: Path,
    *,
    tag: str,
    manifest_path: Path | None = None,
) -> StagingResolution:
    """Validate canonical_path and resolve to (staging_dir, manifest).

    For local-canonical pulls, ``staging_dir == canonical_path``: the
    canonical tree itself is the unpacked staging shape
    ``execute_upgrade`` already expects.

    Raises:
        CanonicalPullError: ``canonical_path`` does not exist, is not
            a directory, lacks a ``.git`` subdirectory (not a git
            working tree), or the resolved manifest path does not
            exist.
    """
    if not canonical_path.exists():
        raise CanonicalPullError(
            f"canonical path does not exist: {canonical_path}"
        )
    if not canonical_path.is_dir():
        raise CanonicalPullError(
            f"canonical path must be a directory: {canonical_path}"
        )
    git_marker = canonical_path / ".git"
    if not git_marker.exists():
        raise CanonicalPullError(
            f"canonical path is not a git working tree (no .git): "
            f"{canonical_path}"
        )

    resolved_manifest_path = (
        manifest_path
        if manifest_path is not None
        else default_manifest_path(canonical_path, tag)
    )
    if not resolved_manifest_path.exists():
        raise CanonicalPullError(
            f"manifest not found at expected location: "
            f"{resolved_manifest_path}"
        )

    manifest = load_manifest(resolved_manifest_path)
    if manifest.release_tag != tag:
        raise CanonicalPullError(
            f"manifest at {resolved_manifest_path} has release_tag="
            f"{manifest.release_tag!r}; CLI tag={tag!r} disagrees"
        )

    # Local-canonical: the canonical tree IS the staging tree.
    return StagingResolution(
        staging_dir=canonical_path,
        manifest=manifest,
        manifest_path=resolved_manifest_path,
    )
