"""Resolve the git HEAD SHA for a target repo.

Per AC.JSTS.3 + AC.BANDS.2 — VERIFIED ACs require a non-null
``repo_sha`` so the test pin survives codebase drift. Mirror of
``lang/ruby/repo_sha.py`` (Cycle 3 Surface #7).

DRY surface (RF §10 #6): byte-identical to
``lang/ruby/repo_sha.resolve_repo_sha`` modulo docstrings; refactor
into ``lang/_common/`` deferred to Cycle 4b/5.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def resolve_repo_sha(repo_path: Path) -> str | None:
    """Return the repo's HEAD SHA, or ``None`` if it cannot be resolved.

    Returns ``None`` when:
    - ``repo_path`` is not inside a git repository.
    - The ``git`` binary is unavailable.
    - The ``git rev-parse HEAD`` invocation fails (detached state,
      bare repo, etc.).

    The 40-char hex SHA is returned verbatim with surrounding
    whitespace stripped.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    if not sha or not all(c in "0123456789abcdef" for c in sha.lower()):
        return None
    return sha
