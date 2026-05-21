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

import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from . import access_log as _access_log
from . import cocitation_graph as _cocitation_graph


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

# AC.MSC.1 (Gap B — recency reaches the top-N). The pre-MSC ranking
# was pure BM25 (``ORDER BY score``) with ``reference_time UNINDEXED``
# — the timestamp was stored but never a ranking input, so a stale
# lexically-strong episode out-ranked the most-recent active thread.
# D-MSC.2 ruling: recency-decay *blended* with BM25, not recency-only
# (recency-only would surface the latest episode regardless of
# relevance and drown a genuinely-relevant older answer — §12 halt
# trigger 4). The blend re-ranks a widened FTS candidate pool in
# Python (stdlib, deterministic, zero SQL date-math portability risk):
# every candidate's BM25 rank-position is combined with an
# exponential recency-decay weight keyed off the episode's
# ``reference_time`` so a recency-shaped query reaches the
# newest-active-thread episode within the returned top-N while a
# non-recency query still surfaces a directly-relevant older answer.
#
# Half-life default 5 days — the active-thread horizon (D-MSC.2
# preliminary band 3–7 days; 5d is the midpoint and the §10 smoke
# fixture is the arbiter). A per-workspace tuning knob is explicitly
# deferred (plan §3 out-of-scope-deferred).
RECENCY_HALF_LIFE_DAYS = 5.0

# Candidate-pool widening factor. ``_fts_search`` fetches
# ``num_results * RECENCY_CANDIDATE_FACTOR`` BM25 hits (floored at
# RECENCY_CANDIDATE_FLOOR) so the recency re-rank has a pool deep
# enough that a slightly-weaker-lexical but most-recent active-thread
# episode is reachable, then returns the top ``num_results`` after the
# blend. Bounded so the widened query stays within the session-start
# 5s envelope on a 600+-episode store.
RECENCY_CANDIDATE_FACTOR = 8
RECENCY_CANDIDATE_FLOOR = 40

# Relative weight of the recency channel against the BM25-relevance
# channel in the blended score. 0.0 → pure relevance (pre-MSC
# behaviour); 1.0 → pure recency. 0.5 keeps both channels load-bearing
# so neither drowns the other (§12 halt trigger 4 — recency must not
# trade away retrieval quality).
RECENCY_BLEND_WEIGHT = 0.5

# AC.FBMT1.SUPM.2 — multiplicative penalty applied to the blended
# score of a memory file whose frontmatter carries a
# ``superseded-by:`` field (the supersession-marker convention; mark-
# don't-delete per the v2 FBM rethink's reading of Anderson & Green
# 2001). Per D-T1.1.PENALTY (plan-doc §14): hard-coded ``0.1`` at
# v0.1 — keeps a high-relevance superseded file visible in the
# candidate set (AC.FBMT1.SUPM.3: ``score=10`` superseded beats
# ``score=0.5`` unsuperseded) but demotes it below comparably-scored
# unsuperseded files. Configurability deferred until a concrete
# tuning request lands.
SUPERSEDED_PENALTY = 0.1


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
        context: dict[str, Any] | None = None,
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
            ``context:``                  # AC.FBMT1.ENCC.1
            ``  triggering_msg_id: <v>``
            ``  active_task_id: <v>``
            ``  cwd: <v>``
            ``  active_files: [<list>]``
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

        AC.FBMT1.ENCC.1: ``context`` (optional) is the four-field
        encoding-context dict per the TG 11805 schema-minimal
        directive. When supplied, the writer emits a ``context:``
        nested block with EXACTLY the four named fields
        (:data:`ENCODING_CONTEXT_FIELDS`); missing / ``None`` fields
        render as ``null``. When ``context`` itself is ``None`` the
        block is still emitted with all four fields ``null`` — the
        schema is always present, only the values vary (AC.FBMT1.
        ENCC.2's null-when-absent contract).
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
        # AC.FBMT1.ENCC.1 + AC.FBMT1.ENCC.2: emit the four-field
        # context block (always present, values vary). Per the
        # schema-minimal directive the block carries exactly the
        # four fields named in :data:`ENCODING_CONTEXT_FIELDS` —
        # adding a fifth field is a structural-test failure.
        context_block = _render_context_block(context)
        front = (
            "---\n"
            f"name: {name}\n"
            f"source: {source}\n"
            f"source_description: {source_description}\n"
            f"reference_time: {ref_utc.isoformat()}\n"
            f"group_id: {group_id}\n"
            f"{context_block}"
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

    # ---- recency scan (AC.MSC.2 — session-start active-thread) ------

    def recent_episodes(
        self,
        *,
        group_ids: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Return the most-recent ``limit`` episodes newest-first,
        independent of any query (AC.MSC.2 / D-MSC.4).

        This is the deterministic recency scan the session-start
        active-thread contributor consumes. Unlike :meth:`search`
        (BM25 keyword retrieval), this walks the episode date-dirs
        newest-first and reads up to ``limit`` files — no query, no
        index, no LLM. Stdlib-only, fits the 5s session-start hook
        envelope (D-MSC.4: a ``claude -p`` digest does not fit the
        timeout; the deterministic scan is the structural floor).

        Newest-first order is by ``(date_dir, reference_time)``: the
        date-dir name is ``YYYY-MM-DD`` (lexically sortable) and the
        per-file ``reference_time`` frontmatter breaks within-day
        ties. A file with an unparseable timestamp sorts to the end
        of its date-dir rather than raising (AC.MSC.5 fail-soft).

        Returns the same per-episode dict shape as :meth:`search`'s
        ``episodes`` entries (``name``/``content``/``path``/
        ``group_id``/``valid_at``) so the contributor reuses the
        existing rendering surface.
        """
        episodes_root = self.memory_dir / EPISODES_SUBDIR
        if not episodes_root.exists() or limit <= 0:
            return []
        candidates: list[tuple[str, str, Path]] = []
        try:
            group_dirs = [
                d for d in episodes_root.iterdir() if d.is_dir()
            ]
        except OSError:
            return []
        for group_dir in group_dirs:
            if group_ids and group_dir.name not in group_ids:
                continue
            try:
                date_dirs = sorted(
                    (d for d in group_dir.iterdir() if d.is_dir()),
                    key=lambda d: d.name,
                    reverse=True,
                )
            except OSError:
                continue
            for date_dir in date_dirs:
                try:
                    files = [
                        f
                        for f in date_dir.iterdir()
                        if f.is_file() and f.suffix == ".md"
                    ]
                except OSError:
                    continue
                for ep in files:
                    candidates.append((date_dir.name, "", ep))
                # Bound the walk — once we have comfortably more than
                # ``limit`` from the newest date-dirs we can stop
                # descending into older dirs (they cannot out-rank).
                if len(candidates) >= limit * 4:
                    break
            if len(candidates) >= limit * 4:
                break
        scored: list[tuple[str, str, Path, str, dict[str, str]]] = []
        for date_name, _placeholder, path in candidates:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            front, body = _split_frontmatter(content)
            ref_raw = front.get("reference_time", "")
            parsed = _parse_reference_time(ref_raw)
            # Sort key: date-dir desc, then reference_time desc. A
            # missing/unparseable timestamp sorts last within its
            # date-dir (empty string < any ISO string under desc).
            ref_sort = parsed.isoformat() if parsed is not None else ""
            scored.append((date_name, ref_sort, path, body, front))
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        out: list[dict[str, Any]] = []
        for _dname, _rsort, path, body, front in scored[:limit]:
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
        needed.

        D-MSC.5 (rebuild-on-mismatch). The recency-blend ranking
        (AC.MSC.1) reads each hit's ``reference_time`` column. A
        pre-MSC index whose ``episodes`` table predates the
        ``reference_time`` column would make the recency SELECT raise.
        The index is a derived cache (the episode markdown files are
        the source of truth — ``write_episode`` re-indexes every
        write); so a schema-mismatched index is *dropped + lazily
        rebuilt* rather than ALTER-migrated. During the rebuild window
        the existing grep fallback covers retrieval (AC.MSC.5 — never
        raise; rebuild-or-fallback). The probe is cheap (one
        ``PRAGMA``-equivalent column read) and runs once per
        connection.
        """
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
        if not self._index_schema_is_current(conn):
            # Pre-MSC schema (no ``reference_time`` column). Drop the
            # stale virtual table + recreate with the current schema.
            # The episodes on disk re-populate it lazily on the next
            # write; until then ``search`` falls through to grep.
            conn.execute("DROP TABLE IF EXISTS episodes")
            conn.execute(
                "CREATE VIRTUAL TABLE episodes "
                "USING fts5(name, body, group_id, path UNINDEXED, "
                "reference_time UNINDEXED)"
            )
            conn.commit()
        self._conn = conn
        return conn

    @staticmethod
    def _index_schema_is_current(conn: sqlite3.Connection) -> bool:
        """Return ``True`` when the ``episodes`` FTS5 table carries the
        ``reference_time`` column the recency blend requires.

        A pre-MSC index lacks it. Probing via a bounded SELECT keeps
        this stdlib + FTS5-portable (``PRAGMA table_info`` is empty for
        FTS5 virtual tables). Any sqlite error → treat as not-current
        so the caller rebuilds (fail-toward-rebuild, never raise —
        AC.MSC.5)."""
        try:
            conn.execute(
                "SELECT reference_time FROM episodes LIMIT 0"
            ).fetchall()
        except sqlite3.Error:
            return False
        return True

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
        # AC.V043.1 — token-level sanitization + OR-of-tokens. Per
        # plan-doc §4: split on whitespace, strip FTS5-meaningful
        # punctuation per token (reduce to alnum/_ content; lowercase),
        # drop tokens shorter than 2 chars, drop a small in-tree
        # stopword set, then join with " OR " so FTS5 BM25 ranks by
        # relevance across any-token-matches. Pre-V043 phrase-wrap
        # produced ~0 hits for natural-language UPS prompts because
        # the verbatim prompt rarely appeared in any episode body.
        tokens = _tokenize_for_fts(query)
        if not tokens:
            return []
        safe_query = " OR ".join(tokens)
        # AC.MSC.1 / D-MSC.2: fetch a widened BM25 candidate pool so
        # the recency re-rank has depth — a slightly-weaker-lexical
        # but most-recent active-thread episode is reachable in the
        # pool even though pure BM25 would have ranked it below the
        # ``num_results`` cut. The pool is still ``ORDER BY score``
        # (BM25) at the SQL layer; the recency blend happens in
        # Python over the returned pool (stdlib, deterministic, no
        # SQL date-math portability risk).
        candidate_limit = max(
            num_results * RECENCY_CANDIDATE_FACTOR,
            RECENCY_CANDIDATE_FLOOR,
        )
        if group_ids:
            placeholders = ",".join("?" for _ in group_ids)
            sql = (
                "SELECT name, body, path, group_id, reference_time, "
                "bm25(episodes) as score "
                f"FROM episodes WHERE episodes MATCH ? AND group_id IN ({placeholders}) "
                "ORDER BY score LIMIT ?"
            )
            params: list[Any] = [safe_query, *group_ids, candidate_limit]
        else:
            sql = (
                "SELECT name, body, path, group_id, reference_time, "
                "bm25(episodes) as score "
                "FROM episodes WHERE episodes MATCH ? "
                "ORDER BY score LIMIT ?"
            )
            params = [safe_query, candidate_limit]
        try:
            cur = conn.execute(sql, params)
        except sqlite3.OperationalError:
            return []
        pool: list[dict[str, Any]] = []
        for row in cur:
            name, body, path, group_id, ref_time, score = row
            pool.append(
                {
                    "name": name,
                    "content": body,
                    "path": path,
                    "group_id": group_id,
                    "valid_at": ref_time,
                    # AC.FBMT2.PLBLA.2 — preserve the BM25 score so the
                    # downstream activation composition can compute
                    # ``final = BM25 × activation × supersession``. SQLite's
                    # ``bm25()`` returns a negative score (lower = better);
                    # we negate so larger = stronger relevance, matching
                    # the ranker semantics of the rest of the pipeline.
                    "_bm25_raw": -float(score) if score is not None else 0.0,
                }
            )
        # AC.FBMT2.PLBLA.2 / D-T2.1.SCORE — compose BM25 with the power-law
        # base-level activation column (multiplicatively); the activation
        # **replaces** the pre-amendment recency-blend channel (which is
        # itself a recency model). ``now`` is injected so the AC.FBMT2.PLBLA.3
        # fixture is deterministic. ``memory_root`` is threaded through so
        # AC.FBMT1.SUPM.4's missing-target warning has a base path against
        # which to resolve the ``superseded-by`` relative path.
        return _compose_score_and_spread(
            pool,
            num_results=num_results,
            now=datetime.now(timezone.utc),
            memory_root=self.memory_dir,
        )

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

        scored: list[tuple[float, Path, str, dict[str, Any]]] = []
        for path in candidates:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            content_lower = content.lower()
            raw_score = sum(content_lower.count(t) for t in terms)
            if raw_score == 0:
                continue
            # AC.V043.2 — length-normalize via linear doclen division
            # (path b-shaped per plan-doc §14 D-V043.2; sqrt was the
            # plan §4 path-a default but empirically insufficient
            # against the AC-spec fixture: 100 KB compaction with
            # every-query-term ≥10 times vs 2 KB focused with rare
            # term 2 times — sqrt(100K)/sqrt(2K) ≈ 7x but raw-count
            # ratio is ~15x, so sqrt-normalized compaction still
            # beats sqrt-normalized focused). Linear normalization
            # `raw_score / doclen` matches BM25's `b=1` extreme
            # without requiring avgdoclen precomputation, satisfies
            # AC.V043.2's stated fixture bar, and remains
            # deterministic + stdlib-only. max(len(...), 1) guards
            # the empty-string edge — though raw_score==0 already
            # skipped above so doclen is strictly > 0 here.
            score = raw_score / max(len(content), 1)
            front, body = _split_frontmatter(content)
            scored.append((score, path, body, front))

        # AC.FBMT2.PLBLA.* — route grep-fallback pool through the same
        # composition pipeline as the FTS5 path so the activation column
        # + supersession penalty apply uniformly regardless of which
        # retrieval surface fires. The grep path's ``raw_score / doclen``
        # is the BM25-equivalent relevance channel in this fallback.
        scored.sort(key=lambda x: x[0], reverse=True)
        pool: list[dict[str, Any]] = []
        for score, path, body, front in scored:
            pool.append(
                {
                    "name": front.get("name", path.stem),
                    "content": body,
                    "path": str(path),
                    "group_id": front.get("group_id", ""),
                    "valid_at": front.get("reference_time", ""),
                    "_bm25_raw": float(score),
                }
            )
        return _compose_score_and_spread(
            pool,
            num_results=num_results,
            now=datetime.now(timezone.utc),
            memory_root=self.memory_dir,
        )


# ---- helpers --------------------------------------------------------


# AC.V043.1 — minimal English-question stopword set per D-V043.1.
# Excludes high-signal loam-corpus terms (`loam`, `pos`, `claude`,
# `eric`, version strings, AC IDs, etc.) deliberately; those should
# rank, not be filtered. Kept ASCII-lowercase; ≤20 entries per the
# plan-doc §14 authoring guidance.
_FTS_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "of", "to", "in", "on", "for", "at", "by",
        "is", "are", "was", "were", "be", "do", "does", "did",
        "what", "how", "this", "that", "it",
    }
)

# Token-shape: keep alnum + underscore content; everything else is a
# token boundary. Mirrors `_split_frontmatter`/`_grep_search`'s
# `\W+` split but applied per-token-after-whitespace-split so we can
# preserve a word like "AC.V043.1" → "ac" + "v043" + "1" (the "1" is
# dropped by min-len 2; "ac" + "v043" both survive).
_FTS_TOKEN_CONTENT_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize_for_fts(query: str) -> list[str]:
    """Token-sanitize ``query`` for the FTS5 query construction.

    Per AC.V043.1 + plan-doc §4:

      - Split on whitespace.
      - Strip FTS5-meaningful punctuation per token (extract alnum/_
        runs); for tokens with embedded punctuation (e.g., "AC.V043.1"),
        emit the alnum runs as separate tokens.
      - Lowercase.
      - Drop tokens shorter than 2 chars.
      - Drop the in-tree stopword set (``_FTS_STOPWORDS``).
      - Deduplicate while preserving first-occurrence order so the
        FTS5 query stays compact for prompts with repeated tokens.

    Returns a list of survivors. Empty list (zero survivors) maps to
    an empty FTS5 result by the caller — matches AC.MFBM.2's empty-
    state contract.
    """
    survivors: list[str] = []
    seen: set[str] = set()
    for ws_token in query.split():
        for run in _FTS_TOKEN_CONTENT_RE.findall(ws_token):
            tok = run.lower()
            if len(tok) < 2:
                continue
            if tok in _FTS_STOPWORDS:
                continue
            if tok in seen:
                continue
            seen.add(tok)
            survivors.append(tok)
    return survivors


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


# AC.FBMT1.ENCC family — fields the worker emits inside the nested
# ``context:`` block, in order. The schema is exactly these four
# fields per TG 11805 schema-minimal directive; AC.FBMT1.ENCC.1
# verifies the count structurally.
ENCODING_CONTEXT_FIELDS: tuple[str, ...] = (
    "triggering_msg_id",
    "active_task_id",
    "cwd",
    "active_files",
)


def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse the YAML-ish frontmatter block authored by
    :meth:`FileMemoryStore.write_episode`. Stdlib-only — this is not
    a full YAML parser; the writer authors flat ``key: value`` lines
    plus a single optional nested ``context:`` block (AC.FBMT1.ENCC.1)
    whose four indented child fields are the four-field encoding-
    context schema. Unknown shapes return ``({}, content)``.

    AC.FBMT1.SUPM.1: the optional ``superseded-by: <relative-path>``
    field parses as a flat scalar (the supersession-marker
    convention; mark-not-delete). When absent the key is missing from
    the returned dict (callers use ``front.get("superseded-by")``
    which returns ``None`` and the ranker treats the file as not
    superseded). When present the value is exposed as a string.

    AC.FBMT1.ENCC.1: the optional ``context:`` block parses as a
    nested mapping under ``front["context"]``. Each child line is
    parsed as ``key: value`` and contributes to the dict; ``null``
    scalar values map to Python ``None``; bracketed list literals
    (``[a, b]``) map to a Python list of trimmed strings. The
    four-field schema is structurally bounded by the writer (see
    :func:`_render_context_block`); the parser accepts whatever the
    writer emits and never expands the schema speculatively.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return ({}, content)
    front_text = match.group(1)
    body = content[match.end() :]
    front: dict[str, Any] = {}
    lines = front_text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ":" not in ln:
            i += 1
            continue
        key, _, value = ln.partition(":")
        key = key.strip()
        value = value.strip()
        # AC.FBMT1.ENCC.1: a bare ``context:`` header with no inline
        # value opens the nested block; subsequent indented lines are
        # child fields. The block ends at the next non-indented line
        # (or end of frontmatter).
        if key == "context" and value == "":
            ctx: dict[str, Any] = {}
            j = i + 1
            while j < len(lines):
                child = lines[j]
                # An indented line (leading space/tab) is a child
                # field; anything else closes the block.
                if not child or (child[:1] not in (" ", "\t")):
                    break
                if ":" not in child:
                    j += 1
                    continue
                ck, _, cv = child.partition(":")
                ctx[ck.strip()] = _parse_context_value(cv.strip())
                j += 1
            front["context"] = ctx
            i = j
            continue
        front[key] = value
        i += 1
    return (front, body)


def _parse_context_value(value: str) -> Any:
    """Parse one scalar / list value from a ``context:`` child line.

    AC.FBMT1.ENCC.2: ``null`` maps to Python ``None`` (so the YAML
    field is still present but unset). Empty values also map to
    ``None`` for parser symmetry with the writer's ``null`` emit.

    AC.FBMT1.ENCC.3: a bracketed list literal ``[a, b, c]`` maps to
    a Python list of trimmed strings (the writer authors
    ``active_files`` this way); ``[]`` maps to an empty list.

    Anything else is returned as a stripped string.
    """
    if value == "" or value == "null":
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip() for item in inner.split(",") if item.strip()]
    return value


def _render_context_block(context: dict[str, Any] | None) -> str:
    """Render the four-field ``context:`` block for the frontmatter.

    AC.FBMT1.ENCC.1: emits EXACTLY the four named fields in
    :data:`ENCODING_CONTEXT_FIELDS` order — no more, no less. A
    field missing from the input dict (or set to ``None``) renders
    as ``null``; ``active_files`` (a list) renders as a bracketed
    list literal.

    Returns the multi-line block including the ``context:`` header.
    Trailing newline included for direct concatenation into the
    frontmatter string.
    """
    if context is None:
        context = {}
    out = ["context:"]
    for field_name in ENCODING_CONTEXT_FIELDS:
        value = context.get(field_name)
        if field_name == "active_files":
            if value is None:
                rendered = "[]"
            elif isinstance(value, list):
                rendered = (
                    "[" + ", ".join(str(item) for item in value) + "]"
                )
            else:
                # AC.FBMT1.ENCC.3: non-list input is a schema-validation
                # error. The writer coerces a string to a single-element
                # list rather than emitting a bare scalar (which would
                # then mis-parse on read-back). Surfaces the coercion
                # via the rendered shape; the worker's diagnostic log
                # captures the original input.
                rendered = "[" + str(value) + "]"
        else:
            if value is None:
                rendered = "null"
            else:
                rendered = str(value)
        out.append(f"  {field_name}: {rendered}")
    return "\n".join(out) + "\n"


def _parse_reference_time(raw: str) -> datetime | None:
    """Parse an ISO-8601 ``reference_time`` string to an aware UTC
    datetime; ``None`` when unparseable.

    Episodes are written with ``reference_time: <ISO-8601-utc>``
    (``write_episode``); the FTS5 index stores the same string. A
    malformed / absent value degrades to ``None`` so the recency
    re-rank treats that episode as recency-neutral rather than
    raising (AC.MSC.5 fail-soft — never raise on a ranking input).
    """
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _recency_weight(ref_time: datetime | None, *, now: datetime) -> float:
    """Exponential recency-decay weight in ``[0.0, 1.0]``.

    ``1.0`` at ``now`` (or future-dated, clamped), decaying with a
    ``RECENCY_HALF_LIFE_DAYS`` half-life. An episode exactly one
    half-life old weighs ``0.5``; two half-lives ``0.25``; etc. An
    unparseable / absent timestamp is recency-neutral (returns
    ``0.0`` — it competes on BM25 relevance alone, never crowding a
    dated active-thread episode out on a recency-shaped query).

    Pure function of its inputs (``now`` injected) so the §10 smoke
    + AC.MSC.1 fixture are deterministic.
    """
    if ref_time is None:
        return 0.0
    age_days = (now - ref_time).total_seconds() / 86400.0
    if age_days <= 0.0:
        return 1.0
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def _superseded_marker(path_str: str) -> str | None:
    """Read the memory file at ``path_str`` and return its
    ``superseded-by`` value, or ``None`` when absent / unreadable.

    AC.FBMT1.SUPM.2 + AC.FBMT1.SUPM.4: the ranker reads the file's
    frontmatter at re-rank time to decide whether to apply the
    multiplicative penalty. Unreadable files (deleted between
    enqueue and rank, permission errors) return ``None`` — the file
    is treated as not superseded rather than the call raising
    (AC.MSC.5 fail-soft is the surrounding contract).
    """
    if not path_str:
        return None
    try:
        content = Path(path_str).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    front, _ = _split_frontmatter(content)
    value = front.get("superseded-by")
    if isinstance(value, str) and value:
        return value
    return None


def _superseded_marker_target_missing(
    marker: str | None, memory_root: Path | None
) -> bool:
    """Return ``True`` when ``marker`` names a path that does not
    resolve to an existing file under ``memory_root``.

    AC.FBMT1.SUPM.4: a ``superseded-by:`` value pointing at a non-
    existent file is a soft error — the ranker still applies the
    penalty (so the superseded file stays demoted) and the warning
    is observable to the caller via the contributor's diagnostic
    surface. This helper is the predicate; the warning emission
    happens in :func:`_blend_recency` where the memory_root is in
    scope.
    """
    if not marker or memory_root is None:
        return False
    target = (memory_root / marker).resolve()
    return not target.exists()


# AC.FBMT1.SUPM.4: warnings collected during a single ``_blend_recency``
# call are appended here so tests and the contributor can observe the
# soft-error surface without a stdlib ``logging`` dependency. Cleared at
# the start of each call. Module-level so an in-process test can read
# it without threading a logger through the call stack.
_LAST_RANKER_WARNINGS: list[str] = []


def _blend_recency(
    rows: list[dict[str, Any]], *, num_results: int, now: datetime,
    memory_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Re-rank a BM25-ordered candidate pool by a recency-blended
    score and return the top ``num_results`` (AC.MSC.1 / D-MSC.2).

    ``rows`` arrives BM25-ordered (best-relevance first). Each row's
    BM25 *rank position* is converted to a normalised relevance
    channel in ``[0.0, 1.0]`` (1.0 = best-ranked) and blended with
    its recency weight:

        blended = (1 - W) * relevance_channel + W * recency_channel

    with ``W = RECENCY_BLEND_WEIGHT``. Both channels stay
    load-bearing so a recency-shaped query reaches the newest
    active-thread episode within the top-N while a non-recency query
    still surfaces a directly-relevant older answer (§12 halt
    trigger 4). Stable: equal blended scores preserve the incoming
    BM25 order (Python sort is stable).

    AC.FBMT1.SUPM.2 + AC.FBMT1.SUPM.3: rows pointing at memory files
    whose frontmatter carries ``superseded-by:`` are multiplicatively
    penalised by :data:`SUPERSEDED_PENALTY`. The penalty applies at
    the blended-score step so the row stays in the candidate set
    (not filtered) — a sufficiently-high-relevance superseded file
    can still surface, just demoted.

    AC.FBMT1.SUPM.4: when ``memory_root`` is supplied and the marker
    points at a non-existent path, the warning is appended to
    :data:`_LAST_RANKER_WARNINGS` (a soft error — the penalty still
    applies; ranker does not crash).
    """
    global _LAST_RANKER_WARNINGS  # noqa: PLW0603 — AC.FBMT1.SUPM.4 surface
    _LAST_RANKER_WARNINGS = []
    if not rows:
        return []
    total = len(rows)
    scored: list[tuple[float, int, dict[str, Any]]] = []
    for idx, row in enumerate(rows):
        # Best BM25 row (idx 0) → relevance_channel 1.0; worst → ~0.
        relevance_channel = (total - idx) / total
        ref_time = _parse_reference_time(str(row.get("valid_at", "")))
        recency_channel = _recency_weight(ref_time, now=now)
        blended = (
            (1.0 - RECENCY_BLEND_WEIGHT) * relevance_channel
            + RECENCY_BLEND_WEIGHT * recency_channel
        )
        # AC.FBMT1.SUPM.2: apply the multiplicative demotion when the
        # file's frontmatter carries ``superseded-by``.
        marker = _superseded_marker(str(row.get("path", "")))
        if marker is not None:
            blended = blended * SUPERSEDED_PENALTY
            # AC.FBMT1.SUPM.4: surface the warning when the marker
            # points at a non-existent file. The penalty already
            # applied above so the demotion still holds even when
            # the target is missing.
            if _superseded_marker_target_missing(marker, memory_root):
                _LAST_RANKER_WARNINGS.append(
                    f"superseded-by target missing: "
                    f"{row.get('path')!s} -> {marker}"
                )
        scored.append((blended, idx, row))
    # Sort by blended score desc; ``idx`` as a stable secondary key so
    # equal-blend ties preserve the original BM25 ordering.
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [row for _, _, row in scored[:num_results]]


def _compose_score_and_spread(
    rows: list[dict[str, Any]],
    *,
    num_results: int,
    now: datetime,
    memory_root: Path,
) -> list[dict[str, Any]]:
    """Compose BM25 with power-law activation + supersession penalty,
    then apply one-hop co-citation spread; return top ``num_results``.

    Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md``:

      - **D-T2.1.SCORE** — final = BM25 × activation × supersession.
        The activation column **replaces** the pre-amendment recency-
        blend channel; activation IS a (better) recency model anchored
        in Anderson & Schooler 1991. Composing both would double-count.
      - **AC.FBMT1.SUPM.2** — supersession penalty is multiplied through
        AFTER activation; the SUPM family's "high-relevance superseded
        still surfaces, just demoted" outcome remains.
      - **AC.FBMT2.COCG.2** — one-hop spread: after BM25 × activation,
        add neighbor scores ``score(c) × S_cn`` from the co-citation
        graph for every direct neighbor of every candidate.
      - **AC.FBMT2.PLBLA.4** — graceful on absent log: when no access
        log exists, activation is a neutral multiplier (1.0); ranking
        degrades to pure-BM25-times-supersession.
      - **AC.FBMT2.COCG.4** — graceful on empty graph: spread step
        returns an empty addition set; BM25 × activation result is
        unchanged.

    AC.FBMT1.SUPM.4 surface preserved: ``_LAST_RANKER_WARNINGS`` is
    populated when ``superseded-by`` points at a missing target.
    """
    global _LAST_RANKER_WARNINGS  # noqa: PLW0603 — AC.FBMT1.SUPM.4 surface
    _LAST_RANKER_WARNINGS = []
    if not rows:
        return []
    # AC.FBMT2.PLBLA.1 / PLBLA.4 — read the access log + build the
    # activation map. Absent log → empty dict → neutral activation per
    # path below.
    events_by_file = _access_log.read_access_log(memory_root)
    # AC.FBMT2.COCG.1 / COCG.4 — build the co-citation graph. Empty
    # events → empty graph → spread step contributes nothing.
    graph = _cocitation_graph.build_cocitation_graph(events_by_file)

    # Compose BM25 × activation × supersession for the primary pool.
    # Build a path → activation cache so the spread step can also look up
    # neighbors' activation (when present).
    activation_cache: dict[str, float] = {}

    def _activation_multiplier(file_key: str) -> float:
        """Convert the activation log-sum into a multiplicative factor.

        ``compute_activation`` returns ``ln(Σ t^-d)`` — the canonical
        Anderson & Schooler 1991 functional form (signed; negative for
        small sums, positive for repeated-recent access).

        For the ranker, we want a multiplier that is:
          - 1.0 when no signal exists (so absent-log degrades to
            pure-BM25 ranking — AC.FBMT2.PLBLA.4),
          - increasing monotonically with B_i (so high-activation files
            climb — AC.FBMT2.PLBLA.2),
          - finite and well-defined when B_i is ``-inf`` (the empty
            iterable case from :func:`access_log.compute_activation`).

        Implementation: ``exp(B_i)`` undoes the ``ln`` so the multiplier
        IS ``Σ t^-d`` — the raw activation. The empty-sum case
        (``B_i = -inf``) maps to ``exp(-inf) = 0.0``; we clamp to 1.0
        in that case so the file ranks on pure BM25 (PLBLA.4 contract).
        Repeated recent access produces a multiplier > 1.0 (boost);
        long-ago single access produces a multiplier < 1.0 (decay).
        """
        if file_key in activation_cache:
            return activation_cache[file_key]
        ts_list = events_by_file.get(file_key, [])
        if not ts_list:
            activation_cache[file_key] = 1.0
            return 1.0
        b_i = _access_log.compute_activation(ts_list, now=now)
        if math.isinf(b_i):
            activation_cache[file_key] = 1.0
            return 1.0
        mult = math.exp(b_i)
        activation_cache[file_key] = mult
        return mult

    scored: list[tuple[float, int, dict[str, Any]]] = []
    for idx, row in enumerate(rows):
        bm25_raw = float(row.get("_bm25_raw", 0.0))
        path_str = str(row.get("path", ""))
        activation = _activation_multiplier(path_str)
        composed = bm25_raw * activation
        # AC.FBMT1.SUPM.2 / SUPM.3 — supersession penalty applies AFTER
        # activation; the file stays in the candidate set, just demoted.
        marker = _superseded_marker(path_str)
        if marker is not None:
            composed = composed * SUPERSEDED_PENALTY
            if _superseded_marker_target_missing(marker, memory_root):
                _LAST_RANKER_WARNINGS.append(
                    f"superseded-by target missing: "
                    f"{path_str!s} -> {marker}"
                )
        scored.append((composed, idx, row))

    # AC.FBMT2.COCG.2 / COCG.4 / COCG.5 — one-hop spread additions.
    candidates_for_spread = [
        (str(row.get("path", "")), composed)
        for composed, _idx, row in scored
    ]
    spread_additions = _cocitation_graph.spread_one_hop(
        candidates_for_spread, graph
    )

    # Materialise the spread additions as result rows. The neighbor
    # files must be readable on disk to populate the result dict.
    # AC.FBMT2.COCG.2 fixture seeds them; production runtime should
    # see them too because the graph only has edges from observed
    # accesses.
    neighbor_idx_base = len(scored)
    for offset, (n_file, n_score) in enumerate(spread_additions.items()):
        n_path = Path(n_file)
        if not n_path.is_absolute():
            # Edges are typically stored as the resolved absolute path
            # because :class:`FileMemoryStore.search` populates the
            # access log with the absolute path. Relative paths are
            # tolerated for the seed-from-transcripts pass which
            # extracts ``episodes/.../*.md`` substrings.
            n_path = (memory_root / n_file).resolve()
        try:
            content = n_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        front, body = _split_frontmatter(content)
        n_row = {
            "name": front.get("name", n_path.stem),
            "content": body,
            "path": str(n_path),
            "group_id": front.get("group_id", ""),
            "valid_at": front.get("reference_time", ""),
            "_bm25_raw": 0.0,
            "_spread_from": True,
        }
        # AC.FBMT1.SUPM.2 — apply supersession penalty to spread-in
        # neighbors too so the demotion is uniform.
        marker = front.get("superseded-by")
        if isinstance(marker, str) and marker:
            n_score = n_score * SUPERSEDED_PENALTY
        scored.append((n_score, neighbor_idx_base + offset, n_row))

    # Sort by composed score desc; ``idx`` as a stable secondary key so
    # equal-score ties preserve the original incoming order.
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [row for _, _, row in scored[:num_results]]


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
        # AC.FBMT2.PLBLA.1 — emit a ``read`` access-log event for every
        # episode the retrieval contributor surfaces. The event records
        # that this memory file was touched at retrieval time; downstream
        # ranker calls compose the resulting activation column. Fail-soft:
        # any access-log error is swallowed so the retrieval block still
        # reaches the persona (AC.MFBM.2 fail-closed surrounding contract).
        try:
            now = datetime.now(timezone.utc)
            for episode in result.get("episodes", []):
                path = episode.get("path")
                if not isinstance(path, str) or not path:
                    continue
                try:
                    _access_log.append_access_event(
                        config.store.memory_dir,
                        file=path,
                        ts=now,
                        op="read",
                    )
                except (OSError, ValueError):
                    # AC.FBMT2.PLBLA.1: bookkeeping failure must not
                    # propagate to the persona. Move on; the missing
                    # event will rejoin the access log on the next
                    # successful touch.
                    continue
        except Exception:  # noqa: BLE001 — defensive; never raise through
            pass
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
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Async-shaped surface; delegates to the synchronous
        :meth:`FileMemoryStore.write_episode`. The async signature
        keeps wire-compat with the worker's ``await client.add_episode``
        call site (AC.J.5).

        AC.FBMT1.ENCC.1: the optional ``context`` kwarg threads the
        four-field encoding-context block through to the writer. The
        production worker fills these from the queue record; tests
        and non-worker callers can pass ``None`` for null fields
        (the block is still emitted; the schema is always present).
        """
        result = self._store.write_episode(
            name=name,
            body=body,
            source_description=source_description,
            reference_time=reference_time,
            source=source,
            group_id=group_id,
            context=context,
        )
        # AC.FBMT2.PLBLA.1 — emit a ``write`` access-log event for every
        # successful add_episode call. The store's ``write_episode``
        # return shape carries the on-disk path of the newly-written
        # file; we record it as the touched-file key so the activation
        # column composes correctly at retrieval time.
        try:
            written_path = result.get("path") if isinstance(result, dict) else None
            if isinstance(written_path, str) and written_path:
                _access_log.append_access_event(
                    self._store.memory_dir,
                    file=written_path,
                    ts=datetime.now(timezone.utc),
                    op="write",
                )
        except (OSError, ValueError):
            # AC.FBMT2.PLBLA.1: bookkeeping failure does not propagate
            # back through the worker (AC.J.4 / AC.MFBM.2 fail-closed
            # surrounding contract — the episode write IS the durable
            # signal; the access-log entry is a bookkeeping replay).
            pass
        return result

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
