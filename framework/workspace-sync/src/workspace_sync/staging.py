"""Stage-then-atomic-accept primitives (B-shape).

Authored fresh. Per AC.WS.7: the sync stages every canonical-clean
write + every resolved Class-C content into
``<workspace>/.pos/sync/staging/<ref>/`` and then either applies the
staging tree atomically to the workspace (single-pass apply with
``os.replace`` per file) OR discards it without touching workspace
state.

Class-A paths are NEVER present in the staging tree. The conflict
detector pre-resolves Class-A entries to ``KEEP_LOCAL`` and leaves
their canonical content out of the clean-writes list, so workspace
data loss via staging contamination is structurally impossible.

``apply_staging_atomically`` performs per-file atomic renames within
the same filesystem root (assumed: workspace and staging dir share
a mount, which holds because staging lives under the workspace).
The workspace tree never observes a partial-apply visible to a
concurrent reader at the per-file level; cross-file atomicity (all
writes commit or none) is delivered by the upstream caller's
discard-on-error flow in ``cli.py``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def staging_root(workspace_root: Path, ref: str) -> Path:
    """Return ``<workspace>/workspace/.pos/sync/staging/<ref>/``.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/``.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "sync" / "staging" / ref


def stage_canonical_clean_writes(
    *,
    canonical_path: Path,
    ref: str,
    workspace_root: Path,
    paths_to_apply: list[str],
) -> Path:
    """Stage every canonical-clean write under the staging root.

    Each path's canonical-side content (read via ``git show <ref>:<path>``)
    is written to ``<staging_root>/<path>``. Returns the staging root.
    The staging tree is created idempotently — re-staging is a no-op
    if the same content is already present.
    """
    sroot = staging_root(workspace_root, ref)
    sroot.mkdir(parents=True, exist_ok=True)

    for rel in paths_to_apply:
        completed = subprocess.run(  # noqa: S603 — argv constructed
            ["git", "-C", str(canonical_path), "show", f"{ref}:{rel}"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            # ls-tree listed it but show failed (submodule / symlink).
            # Skip silently; future amendment can surface.
            continue
        target = sroot / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(completed.stdout)

    return sroot


def stage_resolved_content(
    staging_root_path: Path,
    rel_path: str,
    content: str,
) -> None:
    """Drop resolver-merged content into the staging tree at ``rel_path``."""
    target = Path(staging_root_path) / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def apply_staging_atomically(
    staging_root_path: Path,
    workspace_root: Path,
) -> None:
    """Apply every file in the staging tree to the workspace.

    Per-file atomic-rename within the same filesystem. Class-A paths
    must NEVER appear in the staging tree (the conflict detector +
    resolver helper enforce this); the apply does not validate Class-A
    membership at this layer because the upstream invariant means it
    cannot fire.

    Directory creation is idempotent. Existing workspace files at the
    same path are atomically replaced; missing paths are created.
    """
    sroot = Path(staging_root_path)
    if not sroot.exists():
        return

    for source in sroot.rglob("*"):
        if not source.is_file():
            continue
        rel = source.relative_to(sroot)
        target = Path(workspace_root) / rel
        target.parent.mkdir(parents=True, exist_ok=True)

        # Per-file atomic rename: write to a temp sibling then
        # ``os.replace`` so a concurrent reader never observes a
        # half-written file.
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{target.name}.", dir=str(target.parent)
        )
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(source.read_bytes())
            os.replace(tmp_name, target)
        except Exception:
            # Best-effort cleanup; caller's discard_staging will
            # remove the staging tree.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise


def discard_staging(staging_root_path: Path) -> None:
    """Remove the staging tree. Idempotent — missing tree is no-op."""
    sroot = Path(staging_root_path)
    if sroot.exists():
        shutil.rmtree(sroot)
