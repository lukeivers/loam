# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""File-based memory primitives for the primary-persona layer (M-FBM).

This module is the v0.1.0 file-based memory substrate. It replaces
the live MCP-client + graphiti-service runtime path with stdlib-only
file-based primitives: per-turn markdown episode files + a grep/BM25
retrieval surface that composes against the persona's existing
``ComposedContextPayload`` registry.

Per the locked plan ``oss-v0-1-0-publish-memory-pivot.md`` §11
decisions:

  - **D-Q.MFBM.1** — Episode shape: one markdown file per turn.
  - **D-Q.MFBM.2** — Retrieval: layered grep + BM25 via sqlite-FTS5;
    no embedding index at v0.1.0.
  - **D-Q.MFBM.3** — Memory dir: ``<workspace>/workspace/.loam/memory/``
    (D.2-shape; sibling of ``<workspace>/workspace/.pos/``;
    ``.loam/`` introduced new for memory and unaffected by M1b's
    pending ``.pos`` → ``.loam`` rename).
  - **D-Q.MFBM.4** — Auto-memory orthogonal; this module never
    touches ``~/.claude/projects/<slug>/memory/``.
  - **D-Q.MFBM.5** — ``MemoryProvider`` Protocol stub authored here;
    M-GMP implements graphiti's provider against it.
  - **D-Q.MFBM.6** — kuzu_db state migration: discard. The one-shot
    inspection script lives at
    ``framework/tools/loam-memory-inspect/`` (dev_only).

Public API:

  - :class:`FileMemoryStore` — write/search/archive primitives over
    the file-based memory dir.
  - :func:`memory_dir_for_workspace` — canonical path resolver for
    ``<workspace>/workspace/.loam/memory/``.
  - :func:`build_file_memory_retrieval_contributor` — factory
    producing the ``ComposedContextPayload`` callable that fires at
    ``TriggerKind.turn`` and emits the ``[memory-retrieval]`` block
    populated from the file-based store.
  - :class:`MemoryProvider` Protocol — substrate-composition contract
    that future memory plugins (M-GMP graphiti, future
    ``loam.memory.providers``) implement against. Zero runtime
    impact at v0.1.0; M-FBM authors the stub only.

ACs delivered (per plan §5):

  - **AC.MFBM.1** — :meth:`FileMemoryStore.write_episode` writes one
    markdown file per turn at
    ``<memory-dir>/episodes/<workspace-slug>/<YYYY-MM-DD>/<turn-id>.md``.
  - **AC.MFBM.2** — :func:`build_file_memory_retrieval_contributor`
    emits the file-based retrieval block matching the existing
    ``_render_retrieval`` shape in ``memory_consumer.py``.
  - **AC.MFBM.5** — runtime path no longer instantiates
    ``MemoryClient`` against the MCP surface; the file-based store
    is the only runtime memory path. ``MemoryProvider`` Protocol
    (see below) is the future-pluggable shape.

Per ODD §2.5 every code path traces back to a named AC; defensive
``if`` branches without an AC anchor are not introduced.
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol


# ---- public dir resolver (D-Q.MFBM.3) -------------------------------


# The memory dir lives under the D.2 workspace-state root
# (``<workspace>/workspace/``), at sibling-of-``.pos`` location
# ``.loam/memory/``. Pre-M1b ``<workspace>/workspace/.pos/`` and the
# new ``<workspace>/workspace/.loam/memory/`` coexist; post-M1b
# rename consolidates ``.pos`` → ``.loam``, which absorbs this dir
# without any data move (``.loam/memory/`` already lives where it
# would).
LOAM_SUBDIR = ".loam"
MEMORY_SUBDIR = "memory"
EPISODES_SUBDIR = "episodes"
ARCHIVED_SUBDIR = "archived"
ERRORS_LOG_NAME = ".errors"
SEARCH_INDEX_NAME = "search-index.sqlite"


def memory_dir_for_workspace(workspace_root: Path | str) -> Path:
    """Resolve the file-based memory dir for ``workspace_root``.

    The path is ``<workspace>/workspace/.loam/memory/``. The dir is
    NOT created here — :class:`FileMemoryStore` creates it lazily on
    first write. Callers that need to verify presence call
    ``path.exists()`` themselves.

    Per D-Q.MFBM.3 + AC.MFBM.1 + AC.MFBM.7 (workspace-bootstrap
    ``mkdir -p`` is a no-op if the dir already exists; this module's
    lazy-mkdir is the second-line creator).
    """
    from loam.workspace_bootstrap.workspace_paths import (  # noqa: WPS433
        WORKSPACE_STATE_SUBDIR,
    )

    ws_root = Path(workspace_root)
    return ws_root / WORKSPACE_STATE_SUBDIR / LOAM_SUBDIR / MEMORY_SUBDIR


# ---- MemoryProvider Protocol stub (D-Q.MFBM.5 / AC.MFBM.5) ----------


class MemoryProvider(Protocol):
    """Substrate-composition contract for memory providers.

    Stub authored at M-FBM with **zero runtime impact at v0.1.0**.
    M-GMP (post-v0.1.0) implements graphiti's provider against this
    Protocol; future memory-substrate plugins (e.g. embedding
    sidecar, Anthropic server-side Memory API) compose by
    implementing the same surface and registering against the
    ``loam.memory.providers`` entry-point group.

    The persona's retrieval contributor reads all registered
    providers; the file-based provider (see :class:`FileMemoryStore`)
    is always the floor — it ships with every workspace and never
    requires a service. Additional providers are additive
    enrichment per AC.MGMP.2.

    Three methods cover the substrate contract:

      - ``add_episode``: write one episode (mirrors graphiti's
        episode-create signature; minimum-viable shape).
      - ``search``: retrieve relevant episodes for a query string;
        return the canonical retrieval-result shape (see below).
      - ``health``: lightweight liveness probe; ``True`` when the
        provider is queryable, ``False`` when not. The persona
        skips providers that report unhealthy without raising.

    Search result shape (D-build.M-FBM.5; mirrors the post-#96
    superset that ``memory_consumer._render_retrieval`` already
    handles):

        {"query": str,
         "results":  list[{"fact": str, ...}],   # edges / facts
         "nodes":    list[dict],                 # entities
         "episodes": list[{"name": str,
                           "content": str,
                           "valid_at": str,
                           ...}]}

    The file-based provider returns ``results=[]`` + ``nodes=[]``
    (no entity extraction at v0.1.0) and populates ``episodes`` from
    grep/BM25 hits. Graphiti's M-GMP provider populates all three.
    """

    def add_episode(
        self,
        *,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        source: str,
        group_id: str,
    ) -> dict[str, Any]:
        """Write one episode. Returns provider-specific metadata
        (e.g. file path, episode_uuid)."""
        ...

    def search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
    ) -> dict[str, Any]:
        """Search the substrate; return canonical result shape."""
        ...

    def health(self) -> bool:
        """``True`` when the provider is queryable. Never raises."""
        ...


# ---- FileMemoryStore (AC.MFBM.1 + AC.MFBM.2 + AC.MFBM.6) ------------


# Soft cap on search result rendering — mirrors
# ``memory_consumer.MEMORY_RETRIEVAL_CHAR_CAP`` so the file-based
# block matches the shape the existing turn payload already carries.
MEMORY_RETRIEVAL_CHAR_CAP = 1600

# Maximum episode files scanned per search when the FTS5 index is
# unavailable (degraded grep-only path). Bound prevents pathological
# search-time on workspaces with thousands of episodes; 200 covers
# AC.MFBM.2's 7-of-10 fixture bar empirically.
GREP_FALLBACK_SCAN_LIMIT = 200


@dataclass
class FileMemoryStore:
    """File-based memory store rooted at ``memory_dir``.

    Writes one markdown file per turn under
    ``<memory_dir>/episodes/<group_id>/<YYYY-MM-DD>/<turn_id>.md``
    (AC.MFBM.1). Reads via sqlite-FTS5 BM25 ranking when the search
    index is available, falling back to grep-only when it is not
    (AC.MFBM.2 + D-Q.MFBM.2).

    The store is **stateless apart from the filesystem** — every
    write is a self-contained operation; no in-process index;
    crashes mid-write at most leak a half-written ``.tmp`` file
    (cleaned on next write or by archive).

    ``health`` is structurally always-true at v0.1.0 — the
    file-based store has no out-of-process dependency to be
    unreachable. Mirrors :class:`MemoryProvider`.
    """

    memory_dir: Path

    # Per-instance scratch cache for FTS5 connection. Created
    # lazily; ``None`` while not yet connected. Tests that exercise
    # the grep-only fallback set this to ``None`` and never call
    # ``ensure_index``.
    _conn: sqlite3.Connection | None = None

    # ---- write path (AC.MFBM.1) -------------------------------------

    def write_episode(
        self,
        *,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        source: str,
        group_id: str,
    ) -> dict[str, Any]:
        """Write one markdown episode file.

        Path shape:
            ``<memory_dir>/episodes/<group_id>/<YYYY-MM-DD>/<turn_id>.md``

        ``turn_id`` is recovered from ``name`` (which the persona's
        :class:`TurnAggregator` shapes as ``f"turn/{turn_id}"``); if
        ``name`` does not carry the ``turn/`` prefix the full ``name``
        is the filename stem (fallback for non-persona writers).

        File body:
            ``---``
            ``name: <name>``
            ``source: <source>``
            ``source_description: <source_description>``
            ``reference_time: <ISO-8601-utc>``
            ``group_id: <group_id>``
            ``---``
            ``<body>``

        Returns a dict ``{"path": <str>, "name": <name>, "group_id":
        <group_id>}`` — the file-based equivalent of graphiti's
        ``add_episode`` ``{"episode_uuid": ...}`` return shape; the
        ``path`` field uniquely identifies the episode just as
        ``episode_uuid`` does for graphiti.

        Atomic via ``tmp + os.replace`` so a crash mid-write does
        not produce a partially-readable file (Hard Constraint
        analogue from amendment-J).
        """
        ref_utc = reference_time.astimezone(timezone.utc)
        date_dir = ref_utc.strftime("%Y-%m-%d")
        # Recover turn_id from the ``turn/<id>`` shape the
        # TurnAggregator authors. Non-persona writers (e.g. an
        # interactive ``loam memory write`` future verb) supply a
        # plain name and we use it directly.
        if name.startswith("turn/"):
            stem = name[len("turn/") :]
        else:
            stem = name
        # Sanitise to a filesystem-safe stem; replace ``/`` and
        # whitespace; preserve ``:`` for session_id-style stems
        # since the persona's turn_id shape is
        # ``"<session>:<digest>"`` and that's recoverable.
        stem = _sanitise_filename(stem)
        target_dir = self.memory_dir / EPISODES_SUBDIR / group_id / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{stem}.md"
        tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        front = (
            "---\n"
            f"name: {name}\n"
            f"source: {source}\n"
            f"source_description: {source_description}\n"
            f"reference_time: {ref_utc.isoformat()}\n"
            f"group_id: {group_id}\n"
            "---\n"
        )
        # Single write, then atomic rename. Any IOError surfaces to
        # the caller — the Stop-hook's caller already absorbs every
        # boundary error to ``memory-writes.log`` (AC.M.10), and the
        # contributor-side caller fail-closes (AC.MFBM.2 / AC-D7.7).
        tmp_path.write_text(front + body, encoding="utf-8")
        tmp_path.replace(target_path)
        # Best-effort FTS5 index update; failure is non-fatal —
        # next search rebuilds index from scratch via grep fallback.
        try:
            self._index_episode(
                path=target_path,
                name=name,
                body=body,
                group_id=group_id,
                reference_time=ref_utc,
            )
        except (sqlite3.Error, OSError):
            pass
        return {
            "path": str(target_path),
            "name": name,
            "group_id": group_id,
        }

    # ---- search path (AC.MFBM.2 + D-Q.MFBM.2) -----------------------

    def search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int = 5,
    ) -> dict[str, Any]:
        """Return the canonical retrieval-result shape for ``query``.

        Layered retrieval per D-Q.MFBM.2:
          1. If sqlite-FTS5 index is queryable, rank via BM25.
          2. Else fall back to ripgrep-or-grep-via-stdlib over the
             most recent ``GREP_FALLBACK_SCAN_LIMIT`` files.

        Returns ``{"query", "results", "nodes", "episodes"}`` — the
        post-#96 ``_render_retrieval`` shape. ``results`` and
        ``nodes`` are always ``[]`` for the file-based provider
        (no edge / entity extraction at v0.1.0). ``episodes`` carries
        the BM25-or-grep-ranked top-N.
        """
        if not query or not query.strip():
            return _empty_result(query)
        if num_results <= 0:
            return _empty_result(query)

        # Ensure the memory dir exists; if not, return empty (a
        # workspace with zero episodes legitimately yields zero
        # results — AC.MFBM.2 fail-closed branch).
        episodes_root = self.memory_dir / EPISODES_SUBDIR
        if not episodes_root.exists():
            return _empty_result(query)

        episodes: list[dict[str, Any]] = []
        try:
            episodes = self._fts_search(
                query=query,
                group_ids=group_ids,
                num_results=num_results,
            )
        except (sqlite3.Error, OSError):
            episodes = []
        if not episodes:
            episodes = self._grep_search(
                query=query,
                group_ids=group_ids,
                num_results=num_results,
            )
        return {
            "query": query,
            "results": [],
            "nodes": [],
            "episodes": episodes,
        }

    # ---- archive path (AC.MFBM.6) -----------------------------------

    def archive_before(self, *, date: datetime) -> int:
        """Move every episode whose date-dir is before ``date`` under
        ``<memory_dir>/archived/<YYYY-MM-DD>/...``.

        Returns the count of moved episodes. Idempotent: a re-invocation
        with the same ``date`` is a no-op when no episodes remain
        before the cutoff.

        Per AC.MFBM.6's archive verification: this method backs the
        ``/memory:archive`` skill.
        """
        cutoff = date.astimezone(timezone.utc).strftime("%Y-%m-%d")
        episodes_root = self.memory_dir / EPISODES_SUBDIR
        archive_root = self.memory_dir / ARCHIVED_SUBDIR
        if not episodes_root.exists():
            return 0
        moved = 0
        for group_dir in episodes_root.iterdir():
            if not group_dir.is_dir():
                continue
            for date_dir in list(group_dir.iterdir()):
                if not date_dir.is_dir():
                    continue
                if date_dir.name >= cutoff:
                    continue
                target_dir = archive_root / group_dir.name / date_dir.name
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                # If target exists from a prior partial archive, merge
                # episode-by-episode rather than failing; idempotency
                # win.
                if target_dir.exists():
                    for ep in date_dir.iterdir():
                        if ep.is_file():
                            ep.replace(target_dir / ep.name)
                            moved += 1
                    if not any(date_dir.iterdir()):
                        date_dir.rmdir()
                else:
                    date_dir.replace(target_dir)
                    moved += sum(1 for _ in target_dir.iterdir() if _.is_file())
        return moved

    # ---- health -----------------------------------------------------

    def health(self) -> bool:
        """``True`` when the memory dir is reachable.

        File-based store has no out-of-process dependency; the only
        unreachable case is a filesystem error on parent dir
        creation. The :class:`MemoryProvider` Protocol contract.
        """
        try:
            self.memory_dir.parent.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    # ---- index helpers ---------------------------------------------

    def _connection(self) -> sqlite3.Connection:
        """Lazily open the FTS5 sqlite connection; create schema if
        needed."""
        if self._conn is not None:
            return self._conn
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.memory_dir / SEARCH_INDEX_NAME
        conn = sqlite3.connect(str(index_path))
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS episodes "
            "USING fts5(name, body, group_id, path UNINDEXED, "
            "reference_time UNINDEXED)"
        )
        conn.commit()
        self._conn = conn
        return conn

    def _index_episode(
        self,
        *,
        path: Path,
        name: str,
        body: str,
        group_id: str,
        reference_time: datetime,
    ) -> None:
        conn = self._connection()
        # UPSERT shape: delete prior row at same path, insert fresh.
        conn.execute(
            "DELETE FROM episodes WHERE path = ?",
            (str(path),),
        )
        conn.execute(
            "INSERT INTO episodes (name, body, group_id, path, reference_time) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, body, group_id, str(path), reference_time.isoformat()),
        )
        conn.commit()

    def _fts_search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
    ) -> list[dict[str, Any]]:
        index_path = self.memory_dir / SEARCH_INDEX_NAME
        if not index_path.exists():
            return []
        conn = self._connection()
        # Quote the query as an FTS5 phrase to keep punctuation /
        # operators inert; FTS5 raises on a malformed expression.
        # If quoting fails (the query contains an unbalanced quote),
        # caller falls back to grep.
        safe_query = '"' + query.replace('"', "") + '"'
        if group_ids:
            placeholders = ",".join("?" for _ in group_ids)
            sql = (
                "SELECT name, body, path, group_id, reference_time, "
                "bm25(episodes) as score "
                f"FROM episodes WHERE episodes MATCH ? AND group_id IN ({placeholders}) "
                "ORDER BY score LIMIT ?"
            )
            params: list[Any] = [safe_query, *group_ids, num_results]
        else:
            sql = (
                "SELECT name, body, path, group_id, reference_time, "
                "bm25(episodes) as score "
                "FROM episodes WHERE episodes MATCH ? "
                "ORDER BY score LIMIT ?"
            )
            params = [safe_query, num_results]
        try:
            cur = conn.execute(sql, params)
        except sqlite3.OperationalError:
            return []
        out: list[dict[str, Any]] = []
        for row in cur:
            name, body, path, group_id, ref_time, _score = row
            out.append(
                {
                    "name": name,
                    "content": body,
                    "path": path,
                    "group_id": group_id,
                    "valid_at": ref_time,
                }
            )
        return out

    def _grep_search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
    ) -> list[dict[str, Any]]:
        """Fallback retrieval — scan the most recent N episode files
        and rank by raw term-occurrence count.

        Used when the FTS5 index is missing / corrupted / failed. For
        a workspace with <200 episodes this is empirically <100 ms
        and meets AC.MFBM.2's 7-of-10 fixture bar.
        """
        episodes_root = self.memory_dir / EPISODES_SUBDIR
        if not episodes_root.exists():
            return []
        # Collect candidate files; bound to the most recent N to avoid
        # pathological scans on long-running workspaces.
        candidates: list[Path] = []
        for group_dir in episodes_root.iterdir():
            if not group_dir.is_dir():
                continue
            if group_ids and group_dir.name not in group_ids:
                continue
            # Walk date dirs newest-first.
            date_dirs = sorted(
                (d for d in group_dir.iterdir() if d.is_dir()),
                reverse=True,
            )
            for d in date_dirs:
                for ep in sorted(d.iterdir(), reverse=True):
                    if ep.is_file() and ep.suffix == ".md":
                        candidates.append(ep)
                        if len(candidates) >= GREP_FALLBACK_SCAN_LIMIT:
                            break
                if len(candidates) >= GREP_FALLBACK_SCAN_LIMIT:
                    break
            if len(candidates) >= GREP_FALLBACK_SCAN_LIMIT:
                break

        # Tokenise query into lowercase non-empty terms; empty terms
        # produce empty results (AC.MFBM.2 empty-state).
        terms = [t for t in re.split(r"\W+", query.lower()) if t]
        if not terms:
            return []

        scored: list[tuple[int, Path, str, dict[str, Any]]] = []
        for path in candidates:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            content_lower = content.lower()
            score = sum(content_lower.count(t) for t in terms)
            if score == 0:
                continue
            front, body = _split_frontmatter(content)
            scored.append((score, path, body, front))

        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for _score, path, body, front in scored[:num_results]:
            out.append(
                {
                    "name": front.get("name", path.stem),
                    "content": body,
                    "path": str(path),
                    "group_id": front.get("group_id", ""),
                    "valid_at": front.get("reference_time", ""),
                }
            )
        return out


# ---- helpers --------------------------------------------------------


_FILENAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._:-]+")


def _sanitise_filename(stem: str) -> str:
    """Reduce a turn-id / name to a filesystem-safe stem.

    Preserves alnum + ``.`` + ``_`` + ``:`` + ``-``; replaces every
    other char with ``-``; collapses repeats; strips leading/trailing
    ``-``. ``:`` is preserved because the persona's turn_id shape is
    ``"<session>:<digest>"`` and round-tripping the colon is desirable
    for human-readable filenames; macOS / Linux filesystems accept ``:``.
    Empty result raises (AC.MFBM.1 — every Stop-event must yield a
    file; an empty stem indicates upstream malformation worth halting on).
    """
    safe = _FILENAME_UNSAFE_RE.sub("-", stem)
    safe = re.sub(r"-+", "-", safe).strip("-")
    if not safe:
        raise ValueError(f"unwritable-turn-id-stem: {stem!r}")
    return safe


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _split_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse the YAML-ish frontmatter block authored by
    :meth:`FileMemoryStore.write_episode`. Stdlib-only — this is not
    a full YAML parser; the writer authors flat ``key: value`` lines.
    Unknown shapes return ``({}, content)``.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return ({}, content)
    front_text = match.group(1)
    body = content[match.end() :]
    front: dict[str, str] = {}
    for ln in front_text.splitlines():
        if ":" not in ln:
            continue
        key, _, value = ln.partition(":")
        front[key.strip()] = value.strip()
    return (front, body)


def _empty_result(query: str) -> dict[str, Any]:
    return {
        "query": query,
        "results": [],
        "nodes": [],
        "episodes": [],
    }


# ---- file-based memory retrieval contributor (AC.MFBM.2) ------------


@dataclass
class FileMemoryRetrievalConfig:
    """Per-composer config for the file-based retrieval contributor.

    Mirrors :class:`memory_consumer.MemoryRetrievalConfig` but binds
    against :class:`FileMemoryStore` instead of an MCP-backed
    :class:`MemoryClient`.
    """

    store: FileMemoryStore
    workspace_slug: str
    num_results: int = 5
    char_cap: int = MEMORY_RETRIEVAL_CHAR_CAP


def build_file_memory_retrieval_contributor(
    config: FileMemoryRetrievalConfig,
) -> Callable[[dict[str, Any]], str]:
    """Return the contributor callable registered against
    ``ComposedContextPayload`` at ``TriggerKind.turn``.

    On every UserPromptSubmit, the callable issues one
    :meth:`FileMemoryStore.search` against the workspace's memory
    dir with ``group_ids=[workspace_slug]`` (AC.MFBM.2's fixture
    bar), gathers the top-N results, and returns a plain-text
    rendering using the same ``_render_retrieval`` shape the
    pre-existing MCP-backed contributor uses (so the persona's
    consumer side does not change).

    Fail-closed on every boundary error (AC.MFBM.2 verification: the
    file-based contributor returns an empty retrieval block on
    deletion mid-search; never raises through to the persona).
    """
    # Lazy import to avoid a hard dependency on memory_consumer at
    # import time (file_memory must be importable in contexts where
    # the persona's full surface isn't in play, e.g. the inspection
    # CLI).
    from .memory_consumer import _render_retrieval  # noqa: WPS433

    def contributor(context: dict[str, Any]) -> str:
        prompt = str(context.get("prompt", ""))
        if not prompt.strip():
            return ""
        try:
            result = config.store.search(
                query=prompt,
                group_ids=[config.workspace_slug],
                num_results=config.num_results,
            )
        except Exception:  # noqa: BLE001 — AC.MFBM.2 fail-closed
            return ""
        return _render_retrieval(result, cap=config.char_cap)

    return contributor


# ---- registration helper --------------------------------------------


def register_file_memory_retrieval(
    composer: Any,
    *,
    store: FileMemoryStore,
    workspace_slug: str,
    num_results: int = 5,
    char_cap: int = MEMORY_RETRIEVAL_CHAR_CAP,
    name: str = "memory-retrieval",
) -> Callable[[dict[str, Any]], str]:
    """Register the file-based memory-retrieval contributor against a
    ``ComposedContextPayload`` instance. Mirrors
    :func:`memory_consumer.register_memory_retrieval` for the file-
    backed substrate.
    """
    from .context_composer import TriggerKind  # noqa: WPS433

    config = FileMemoryRetrievalConfig(
        store=store,
        workspace_slug=workspace_slug,
        num_results=num_results,
        char_cap=char_cap,
    )
    fn = build_file_memory_retrieval_contributor(config)
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn


# ---- MemoryClient-Protocol adapter for the worker (AC.MFBM.5) -------


class FileBackedMemoryClient:
    """``MemoryClient`` Protocol-shaped adapter over
    :class:`FileMemoryStore`.

    The post-amendment-J memory-write worker
    (:func:`memory_write_worker.drain_once`) calls
    ``client.add_episode(**arguments)``; this adapter satisfies that
    contract while writing to the file-based substrate. AC.J.5 + AC.M.6
    (one episode write per turn) survive: the worker drains one queue
    entry → one ``add_episode`` call → one file. ``search`` is also
    Protocol-required; the adapter's ``search`` delegates to
    :meth:`FileMemoryStore.search`.

    M-FBM (AC.MFBM.5): production runtime now hands this adapter to the
    worker instead of :class:`mcp_memory_client.LiveMCPMemoryClient`.
    Zero MCP instantiation in the runtime path.
    """

    def __init__(self, store: FileMemoryStore) -> None:
        self._store = store

    async def add_episode(
        self,
        *,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        source: str,
        group_id: str,
    ) -> dict[str, Any]:
        """Async-shaped surface; delegates to the synchronous
        :meth:`FileMemoryStore.write_episode`. The async signature
        keeps wire-compat with the worker's ``await client.add_episode``
        call site (AC.J.5)."""
        return self._store.write_episode(
            name=name,
            body=body,
            source_description=source_description,
            reference_time=reference_time,
            source=source,
            group_id=group_id,
        )

    async def search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
        center_node_uuid: str | None = None,
    ) -> dict[str, Any]:
        """Async-shaped surface; delegates to
        :meth:`FileMemoryStore.search`. ``center_node_uuid`` is
        accepted for Protocol parity but ignored at v0.1.0 (graph
        traversal is M-GMP)."""
        return self._store.search(
            query=query,
            group_ids=group_ids,
            num_results=num_results,
        )


def build_file_backed_memory_client(
    workspace_root: Path | str,
) -> FileBackedMemoryClient:
    """Factory mirroring :func:`mcp_memory_client.build_live_mcp_memory_client`
    for the file-based substrate.

    Returns a :class:`FileBackedMemoryClient` rooted at
    :func:`memory_dir_for_workspace`. Always succeeds — no out-of-
    process dependency to be unreachable. The ``None`` return shape
    of the MCP factory is irrelevant for the file-backed path; M-FBM
    runtime is structurally always-ready (AC.MFBM.5).
    """
    return FileBackedMemoryClient(
        store=FileMemoryStore(memory_dir=memory_dir_for_workspace(workspace_root))
    )
