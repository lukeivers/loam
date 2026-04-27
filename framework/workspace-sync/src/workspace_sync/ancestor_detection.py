"""α.1 — Content-vs-canonical-history ancestor detection.

Pre-resolver pass that walks canonical's git history per conflicted
path looking for an ancestor commit whose blob byte-content matches
the workspace's installed sha256. When a match is found, the
conflict is fast-path resolved as ``inferred-accept-canonical``
with confidence 1.0 and the resolver is NOT invoked — the workspace
content is just behind canonical, not edited.

Empirically 97.8% of pos3's 46-conflict live-test would skip via
this pass (research note `nn-ancestor-detection-empirical-
skippability-2026-04-27.md`). For the milestone live-test alone the
single non-skippable path was ``.claude/settings.json``; α.1 closes
the cost gap that halted that run.

Walk parameters (D-1 LOCKED 2026-04-27):
  - depth cap 200 (workspace-tunable; pos3's max ancestor-match was
    13 commits; 200 is generous)
  - sibling cache `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`
    keyed by (path, workspace_sha256), invalidates on canonical-ref
    SHA advance
  - sha256 of file bytes (matches `conflict_detection.py`'s existing
    `_sha256_bytes` shape)
  - decline-on-shallow: when `git log` returns FEWER than depth_cap
    commits AND no match found, the helper declines (the resolver
    runs as today)

No new third-party deps (Hard Constraint #3): stdlib + `git` binary
+ Pydantic + PyYAML.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_DEPTH_CAP = 200


class AncestorMatch(BaseModel):
    """Result of a successful ancestor-walk match."""

    model_config = ConfigDict(extra="forbid")

    commit_sha: str  # full SHA (40 hex chars)
    walk_depth: int  # 0-indexed position in the walk where the match landed

    @property
    def short_sha(self) -> str:
        return self.commit_sha[:7]


class AncestorCacheEntry(BaseModel):
    """Per-conflict cache entry."""

    model_config = ConfigDict(extra="forbid")

    path: str
    workspace_sha256: str
    ancestor_sha: str | None  # None on miss; full SHA on hit
    walk_depth: int  # how many commits walked (or 0 if cache-hit-from-prior-run-with-no-match)
    walk_short: bool  # True when git log returned fewer than depth_cap commits


class AncestorCache(BaseModel):
    """Workspace-local ancestor-walk cache.

    Sibling file at `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`.
    Invalidated wholesale when `canonical_ref_sha` differs from the
    current canonical-HEAD (so a canonical advance does not produce
    stale fast-path verdicts).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    canonical_ref_sha: str  # the resolved canonical-HEAD SHA at write-time
    entries: dict[str, AncestorCacheEntry] = Field(default_factory=dict)

    def key(self, path: str, workspace_sha256: str) -> str:
        return f"{path}|{workspace_sha256}"

    def get(
        self, path: str, workspace_sha256: str
    ) -> AncestorCacheEntry | None:
        return self.entries.get(self.key(path, workspace_sha256))

    def put(self, entry: AncestorCacheEntry) -> None:
        self.entries[self.key(entry.path, entry.workspace_sha256)] = entry


def cache_path(workspace_root: Path, ref: str) -> Path:
    """Return the absolute cache file path for a workspace + ref.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/sync/``.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "sync" / ref / "ancestor-cache.yaml"


def load_cache(
    workspace_root: Path, ref: str, current_canonical_sha: str
) -> AncestorCache:
    """Load the cache, returning an empty (fresh) cache when stale.

    Stale = file missing OR file's `canonical_ref_sha` differs from
    `current_canonical_sha`. Stale cache is treated as empty so any
    fast-path verdicts from a prior canonical SHA are discarded
    (D-1 LOCKED).
    """
    p = cache_path(workspace_root, ref)
    if not p.exists():
        return AncestorCache(canonical_ref_sha=current_canonical_sha)
    try:
        raw = yaml.safe_load(p.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return AncestorCache(canonical_ref_sha=current_canonical_sha)
    if not isinstance(raw, dict):
        return AncestorCache(canonical_ref_sha=current_canonical_sha)
    try:
        cache = AncestorCache.model_validate(raw)
    except Exception:  # noqa: BLE001 — defensive; malformed cache treated as empty
        return AncestorCache(canonical_ref_sha=current_canonical_sha)
    if cache.canonical_ref_sha != current_canonical_sha:
        # Canonical ref advanced; cache is wholesale invalidated.
        return AncestorCache(canonical_ref_sha=current_canonical_sha)
    return cache


def save_cache(cache: AncestorCache, workspace_root: Path, ref: str) -> None:
    """Persist the cache to its sibling YAML."""
    p = cache_path(workspace_root, ref)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = cache.model_dump(mode="json")
    p.write_text(yaml.safe_dump(payload, default_flow_style=False, sort_keys=False))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_log_paths(
    canonical_path: Path, ref: str, conflict_path: str, depth_cap: int
) -> list[str]:
    """Return up to depth_cap ancestor commits that touched <conflict_path>.

    Uses ``git log --all --follow --format=%H -- <path>`` so we
    walk renames + every branch reachable from the local repo.
    Result is the full chronological list, newest-first; we slice
    to depth_cap.
    """
    completed = subprocess.run(  # noqa: S603 — argv constructed
        [
            "git",
            "-C",
            str(canonical_path),
            "log",
            "--all",
            "--follow",
            "--format=%H",
            "--",
            conflict_path,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        # git log failed (path not tracked, etc.); return empty.
        return []
    commits = [ln.strip() for ln in completed.stdout.splitlines() if ln.strip()]
    return commits[:depth_cap]


def _git_show_bytes(
    canonical_path: Path, commit: str, conflict_path: str
) -> bytes | None:
    """Return raw bytes of <commit>:<path>; None on failure."""
    completed = subprocess.run(  # noqa: S603 — argv constructed
        [
            "git",
            "-C",
            str(canonical_path),
            "show",
            f"{commit}:{conflict_path}",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def walk_ancestors(
    *,
    canonical_path: Path,
    ref: str,
    conflict_path: str,
    target_sha256: str,
    depth_cap: int = DEFAULT_DEPTH_CAP,
) -> tuple[AncestorMatch | None, int, bool]:
    """Walk canonical's git history for <conflict_path> looking for a sha256 match.

    Returns ``(match, walk_depth, walk_short)`` where:
      - ``match`` is the AncestorMatch or None (no match within cap).
      - ``walk_depth`` is the number of commits inspected (0 to depth_cap).
      - ``walk_short`` is True when ``git log`` returned FEWER than
        depth_cap commits AND no match was found — the canonical
        history is shallow / pruned for this path. Caller treats
        walk_short=True as decline-on-shallow per D-1 LOCKED.

    The walk is byte-content sha256 comparison (matches
    ``conflict_detection._sha256_bytes``). First match wins.

    The ``ref`` argument is recorded by the caller for cache-keying;
    not used by the walk itself (``--all`` + ``--follow`` covers
    all branches reachable from the canonical repo).
    """
    commits = _git_log_paths(canonical_path, ref, conflict_path, depth_cap)
    walk_depth = 0
    walk_short = len(commits) < depth_cap
    for commit in commits:
        walk_depth += 1
        blob = _git_show_bytes(canonical_path, commit, conflict_path)
        if blob is None:
            continue
        if _sha256_bytes(blob) == target_sha256:
            return AncestorMatch(commit_sha=commit, walk_depth=walk_depth), walk_depth, walk_short
    return None, walk_depth, walk_short
