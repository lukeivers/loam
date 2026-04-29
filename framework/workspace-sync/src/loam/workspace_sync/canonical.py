"""Canonical-as-source resolver (workspace-sync B-shape).

Salvaged from ``self-upgrade/src/self_upgrade/canonical.py`` with
the following scrub list (per workspace-sync plan §9.1):

  - Drop the manifest validator (``manifest.release_tag != tag``)
    — manifests do not exist under B; the canonical repo's git
    history IS the at-rest comparison source.
  - Drop ``default_manifest_path`` — no manifest under B.
  - Drop the ``Manifest`` import.
  - Rename function ``resolve_canonical_to_staging`` →
    ``resolve_canonical``; return type renamed
    ``StagingResolution`` → ``CanonicalResolution`` and field
    ``staging_dir`` → ``canonical_path``.
  - Rename parameter ``tag`` → ``ref``.
  - Add ``git rev-parse <ref>`` resolution so symbolic refs (HEAD,
    branch names, tags) collapse to a stable SHA the audit + state
    can key idempotency against (AC.WS.8).

Local-canonical mode only. ``--canonical <git-url>`` (remote fetch
into a tmp worktree) is explicitly out of scope (plan §7); future
amendment composes that on top.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CanonicalResolution:
    """Resolved (canonical_path, ref) pair for B-mode pull."""

    canonical_path: Path
    ref: str  # the resolved SHA (output of `git rev-parse <ref>`)


class CanonicalPullError(Exception):
    """Raised on malformed/missing canonical inputs."""


def _git_rev_parse(canonical_path: Path, ref: str) -> str:
    """Resolve ``ref`` against ``canonical_path``'s git tree.

    Returns the full SHA. Raises ``CanonicalPullError`` if the ref
    does not exist in the tree.
    """
    try:
        completed = subprocess.run(  # noqa: S603 — argv constructed
            ["git", "-C", str(canonical_path), "rev-parse", ref],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
    except OSError as exc:
        raise CanonicalPullError(
            f"git rev-parse {ref} failed (subprocess spawn): {exc}"
        ) from exc
    if completed.returncode != 0:
        raise CanonicalPullError(
            f"git rev-parse {ref!r} in {canonical_path} failed: "
            f"{completed.stderr.strip()!r}"
        )
    sha = completed.stdout.strip()
    if not sha:
        raise CanonicalPullError(
            f"git rev-parse {ref!r} returned empty SHA"
        )
    return sha


def resolve_canonical(
    canonical_path: Path,
    *,
    ref: str = "HEAD",
) -> CanonicalResolution:
    """Validate canonical_path and resolve ``ref`` to a stable SHA.

    For B-mode pulls, the canonical tree IS the at-rest comparison
    source: there is no copy step. The returned ``CanonicalResolution``
    carries the canonical path plus the resolved SHA.

    Raises:
        CanonicalPullError: ``canonical_path`` does not exist, is not
            a directory, lacks a ``.git`` subdirectory (not a git
            working tree), or ``ref`` does not resolve in that tree.
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

    resolved_sha = _git_rev_parse(canonical_path, ref)

    return CanonicalResolution(
        canonical_path=canonical_path,
        ref=resolved_sha,
    )
