"""Repo discovery + universal-path constants.

The canonical tree root is resolved by walking up from the CWD until a
``.git`` entry is found. This matches how the seal-diff tests themselves
resolve ``REPO_ROOT``.
"""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Return the enclosing repo root for *start* (default CWD)."""
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"no .git found at or above {cur}")
