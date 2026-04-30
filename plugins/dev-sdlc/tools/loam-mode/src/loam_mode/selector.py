"""Mode-aware corpus selector (sub-plan B's data-side dependency).

``select_corpus(manifest, workspace_root, mode)`` returns the sorted
list of workspace-relative paths that should auto-load for the given
mode. ``"user"`` → always-loaded only; ``"dev"`` → always-loaded ∪
dev-only.

Sub-plan B's mechanism (the SessionStart hook + CLAUDE.md fragment
delivery) consumes this function's output. F owns the data; B owns
the routing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal

from loam_mode.manifest import Manifest, expand_entry


Mode = Literal["user", "dev"]


def select_corpus(
    manifest: Manifest,
    workspace_root: Path,
    mode: Mode,
    candidate_paths: Iterable[str] | None = None,
) -> list[str]:
    """Return the sorted list of paths for ``mode``.

    ``candidate_paths`` lets callers pass a pre-walked tree to avoid
    re-walking; without it, each glob entry walks the tree itself.
    """
    if mode not in ("user", "dev"):
        raise ValueError(f"mode must be 'user' or 'dev'; got {mode!r}")
    candidate_set = (
        list(candidate_paths) if candidate_paths is not None else None
    )
    selected: set[str] = set()
    for entry in manifest.always_loaded:
        selected.update(
            expand_entry(entry, workspace_root, candidate_set)
        )
    if mode == "dev":
        for entry in manifest.dev_only:
            selected.update(
                expand_entry(entry, workspace_root, candidate_set)
            )
    return sorted(selected)
