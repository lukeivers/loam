"""URL-form canonical cache (β.1).

When ``canonical_source:`` in sync-config.yaml is a URL (per
``sync_config.canonical_source_kind``), pos-sync clones the
canonical working tree to a workspace-shared cache at
``~/.loam/canonical-cache/<repo-id>/`` and runs ``git fetch
--all --tags`` on every invocation (always-fetch policy per
D-β.1 LOCKED).

The cache directory is a normal git working tree (NOT a bare
repo) so the existing ``resolve_canonical()`` flow keeps working
unchanged. Disk cost is small (pos-v2 is ~15 MB at HEAD); a
workspace-shared cache avoids per-workspace duplicates when an
operator has multiple workspaces against the same canonical.

URL trust model (β.1): pos-sync trusts the ``canonical_source``
the operator set. β.1 does NOT pin fingerprints or verify the
remote out-of-band; future amendments may add fingerprint pinning
if empirical demand surfaces.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class CanonicalCacheError(Exception):
    """Raised on cache-clone or cache-fetch failure."""


def derive_repo_id(url: str) -> str:
    """Sanitise a URL into a ``host/owner/repo`` slug.

    Examples (all return ``github.com/lukeivers/pos-v2``):

    - ``https://github.com/lukeivers/pos-v2``
    - ``https://github.com/lukeivers/pos-v2.git``
    - ``git@github.com:lukeivers/pos-v2.git``
    - ``http://github.com/lukeivers/pos-v2``

    Algorithm:

    1. Strip leading ``https://`` / ``http://`` / ``git@``.
    2. Replace the first ``:`` (in ``git@host:owner/repo``) with ``/``.
    3. Strip trailing ``.git``.
    4. Strip trailing ``/``.

    The result is forward-slash-joined, safe as a POSIX path
    component, and stable across the two equivalent-form URLs the
    operator might paste.
    """
    s = url
    for prefix in ("https://", "http://", "git@"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    # git@host:owner/repo → host/owner/repo
    if ":" in s and "/" in s:
        # Only replace the first ':' to keep colons in path-style refs
        # (rare but possible). git@-form has a single leading colon
        # before the first slash.
        head, _, rest = s.partition(":")
        if "/" not in head:
            s = f"{head}/{rest}"
    if s.endswith(".git"):
        s = s[: -len(".git")]
    s = s.rstrip("/")
    if not s:
        raise CanonicalCacheError(
            f"derive_repo_id: empty slug after sanitising {url!r}"
        )
    return s


def cache_root() -> Path:
    """Return ``~/.loam/canonical-cache/`` (the workspace-shared cache root)."""
    return Path.home() / ".loam" / "canonical-cache"


def _git(args: list[str], *, cwd: Path | None = None) -> None:
    """Invoke ``git <args>`` and raise on non-zero exit."""
    try:
        completed = subprocess.run(  # noqa: S603 — argv constructed
            ["git", *args],
            cwd=str(cwd) if cwd is not None else None,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
    except OSError as exc:
        raise CanonicalCacheError(
            f"git {' '.join(args)} failed (subprocess spawn): {exc}"
        ) from exc
    if completed.returncode != 0:
        raise CanonicalCacheError(
            f"git {' '.join(args)} failed (exit "
            f"{completed.returncode}): {completed.stderr.strip()!r}"
        )


def ensure_cache_clone(url: str, ref: str = "HEAD") -> Path:
    """Ensure ``~/.loam/canonical-cache/<repo-id>/`` exists + is up-to-date.

    Per D-β.1 LOCKED:

    - Clone-or-fetch: if the cache directory does not exist, ``git
      clone <url> <cache_dir>``. The leaf directory MUST be the
      clone target; parents are created idempotently.
    - Always-fetch: on every invocation, ``git -C <cache_dir>
      fetch --all --tags`` so symbolic refs (``HEAD``, branch names)
      and tags resolve against the latest remote state.

    Returns the absolute path to the cache directory (a normal git
    working tree). The caller hands this Path to ``resolve_canonical``
    which already knows how to ``git rev-parse <ref>`` against a
    working tree.

    The ``ref`` parameter is accepted for symmetry with
    ``resolve_canonical``; β.1 does not consume it directly here
    (the fetch is unconditional `--all --tags`). It is reserved for
    future amendments that may want to fetch only a specific ref.
    """
    cache_dir = cache_root() / derive_repo_id(url)

    if not cache_dir.exists():
        # Ensure parent exists; git clone creates the leaf.
        cache_dir.parent.mkdir(parents=True, exist_ok=True)
        _git(["clone", url, str(cache_dir)])
    else:
        if not (cache_dir / ".git").exists():
            raise CanonicalCacheError(
                f"cache_dir {cache_dir} exists but is not a git working "
                "tree (missing .git/). Remove it and re-run, or move "
                "it aside."
            )

    # Always-fetch (D-β.1 LOCKED).
    _git(["fetch", "--all", "--tags"], cwd=cache_dir)

    return cache_dir
