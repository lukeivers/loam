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

"""KP1 — BM25/FTS5 index over the markdown corpus.

This is the sparse-first retrieval substrate (Surface #1, owner-ruled):
**BM25 ranking via sqlite-FTS5 over the markdown corpus** — NO
embeddings, NO Anthropic API key (honors ``feedback_no_anthropic_api_key``).
The corpus is the durable memory reality this MVP retrieves over (RF-1:
the graphiti/S3 store is NOT live; memory is file-based markdown only):

  - the ``feedback_*.md`` corpus (+ ``MEMORY.md`` / ``CURRENT-WORK.md``)
    under the user-scope memory dir;
  - the CLAUDE.md hierarchy (user-scope + project);
  - the user-scope ``OBJECTIVES.md`` register.

The index is a **runtime artefact** kept in ``<workspace>/.scratch/``
(gitignored), NOT committed source (plan §2 / manifest). It is a
DERIVED cache — the markdown files are the source of truth — so a
schema-mismatched or missing index is rebuilt from the corpus rather
than migrated.

ACs delivered (plan §5):

  - **AC.KP1.1** — :meth:`CorpusIndex.sync` builds + updates the FTS5
    index from the corpus; a corpus write is reflected on the next
    read (mtime-driven incremental re-index — single-digit-ms for an
    unchanged corpus, only changed docs re-indexed). No embeddings,
    no API call.
  - **AC.KP1.5** — :meth:`CorpusIndex.search` re-syncs before each
    query (fresh read each turn): a corpus change between turns is
    reflected on the next turn with no session restart.

Stdlib-only (``sqlite3`` + ``pathlib`` + ``re``).
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# The corpus-index file name under .scratch/keep-pace/. Distinct from
# the episode store's ``search-index.sqlite`` (file_memory) — KP1
# indexes the markdown corpus, not episode files.
CORPUS_INDEX_NAME = "corpus-index.sqlite"

# Per-document body cap when indexing — keeps the FTS5 row bounded for
# very large corpus docs (a 100KB CLAUDE.md need not be indexed whole;
# the leading window carries the topical signal). Generous; only the
# pathological tail is dropped.
CORPUS_DOC_BODY_CAP = 60_000

# AC.KP1.4 — minimum relevance floor for "silent on no-match". The
# work-anchored key is term-rich (prompt + every active-objective +
# subgoal word), so a low-IDF common word ("notes", "work", "path")
# can produce a spurious FTS5 MATCH against an unrelated doc. BM25
# scores such a single-common-word hit at ~0 (the term carries almost
# no inverse-document-frequency weight against a short doc), while a
# genuine multi-term objective-anchor match scores in the double
# digits (empirically 13+ for the litrpg canon cold-walk). A floor
# just above zero filters pure-noise zero-IDF hits without dropping any
# genuine match — "no-match" means "nothing scored above noise," which
# is the honest reading of AC.KP1.4's silent-on-no-match contract.
MIN_RELEVANCE_SCORE = 0.1


@dataclass
class CorpusDoc:
    """One corpus document to index."""

    path: str
    title: str
    body: str
    pointer: str  # the plain-language pointer surfaced on a hit


def default_index_path(workspace_root: Path | str) -> Path:
    """Resolve the runtime corpus-index path under ``.scratch/``.

    ``<workspace_root>/.scratch/keep-pace/corpus-index.sqlite``. The
    ``.scratch/`` tree is gitignored (plan §2 / Output conventions) —
    the index is a runtime artefact, never committed.
    """
    return (
        Path(workspace_root)
        / ".scratch"
        / "keep-pace"
        / CORPUS_INDEX_NAME
    )


# ---- corpus discovery ----------------------------------------------


def discover_corpus(
    *,
    memory_dir: Path | str | None,
    claude_homes: Iterable[Path | str] = (),
    objectives_path: Path | str | None = None,
    extra_paths: Iterable[Path | str] = (),
) -> list[Path]:
    """Collect the markdown corpus paths to index (AC.KP1.1).

    Sources (RF-1 file-based reality):
      - every ``*.md`` under ``memory_dir`` (the ``feedback_*.md``
        corpus + MEMORY.md + CURRENT-WORK.md);
      - ``CLAUDE.md`` under each ``claude_homes`` entry (the hierarchy);
      - the user-scope ``OBJECTIVES.md`` register, when present;
      - any ``extra_paths`` the caller threads in.

    Missing sources are skipped (a fresh machine has no memory dir
    yet); the index degrades to whatever exists rather than raising.
    """
    paths: list[Path] = []
    seen: set[str] = set()

    def _add(p: Path) -> None:
        rp = str(p.resolve())
        if rp in seen:
            return
        seen.add(rp)
        paths.append(p)

    if memory_dir is not None:
        md = Path(memory_dir)
        if md.exists():
            for f in sorted(md.glob("*.md")):
                if f.is_file():
                    _add(f)
    for home in claude_homes:
        claude_md = Path(home) / "CLAUDE.md"
        if claude_md.is_file():
            _add(claude_md)
    if objectives_path is not None:
        op = Path(objectives_path)
        if op.is_file():
            _add(op)
    for extra in extra_paths:
        ep = Path(extra)
        if ep.is_file():
            _add(ep)
    return paths


_TITLE_RE = re.compile(r"^#\s+(.+)\s*$", re.MULTILINE)


def _doc_title(path: Path, body: str) -> str:
    """First ``# `` heading, else the file stem prettified."""
    m = _TITLE_RE.search(body)
    if m:
        return m.group(1).strip()
    return path.stem.replace("_", " ").replace("-", " ")


# The OBJECTIVES register is INDEXED (per AC.KP1.1 — its terms are part
# of the searchable corpus) but it is NOT a user-facing retrieval
# pointer: it is the anchor SOURCE (the rotation key), not an on-file
# topic the user forgot. A doc whose title is the register header
# surfaces with an EMPTY pointer so :func:`_render_injection` drops it
# (the boilerplate/template prose otherwise produces spurious
# common-word matches — e.g. "keep", "work" — that are pure noise).
_REGISTER_TITLE_MARKER = "user-objectives"


def _doc_pointer(path: Path, title: str) -> str:
    """The plain-language pointer surfaced on a retrieval hit.

    Plain English — NO file path, NO ``.md`` filename (the surface
    routes through KP9's lint in Cycle 3, but KP1's own pointer is
    authored plain-by-construction so it passes). The pointer names
    the on-file topic, not its storage location.

    Returns ``""`` for the OBJECTIVES register (anchor source, not a
    user-facing pointer — see :data:`_REGISTER_TITLE_MARKER`).
    """
    if title.strip().lower() == _REGISTER_TITLE_MARKER:
        return ""
    return title


def read_corpus_docs(paths: Iterable[Path]) -> list[CorpusDoc]:
    """Read + shape the corpus docs for indexing (AC.KP1.1)."""
    docs: list[CorpusDoc] = []
    for p in paths:
        try:
            body = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        title = _doc_title(p, body)
        docs.append(
            CorpusDoc(
                path=str(p),
                title=title,
                body=body[:CORPUS_DOC_BODY_CAP],
                pointer=_doc_pointer(p, title),
            )
        )
    return docs


# ---- the FTS5 index ------------------------------------------------


@dataclass
class CorpusIndex:
    """BM25/FTS5 index over the markdown corpus (AC.KP1.1 + AC.KP1.5).

    Incremental + mtime-driven: :meth:`sync` re-indexes only the docs
    whose on-disk mtime changed since the last sync (AC.KP1.1's
    single-digit-ms unchanged-corpus path), and drops index rows for
    docs that disappeared. :meth:`search` re-syncs first so every
    query sees the current corpus (AC.KP1.5 fresh-read-each-turn).
    """

    index_path: Path
    # The corpus-path resolver — called fresh on every sync so a corpus
    # file added mid-session is discovered (AC.KP1.5). A callable, not a
    # static list, so the fresh-read contract holds.
    discover: object  # Callable[[], list[Path]]
    _conn: sqlite3.Connection | None = field(default=None, repr=False)

    def _connection(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.index_path))
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS corpus "
            "USING fts5(path UNINDEXED, title, body, pointer UNINDEXED, "
            "mtime UNINDEXED)"
        )
        conn.commit()
        self._conn = conn
        return conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def sync(self) -> int:
        """Re-index changed corpus docs; drop vanished ones.

        Returns the count of docs (re)indexed this call. Mtime-driven:
        an unchanged corpus indexes zero docs (the single-digit-ms
        AC.KP1.1 path). Best-effort — any sqlite error rebuilds lazily
        on the next call rather than raising (the index is a derived
        cache; the markdown is the source of truth).
        """
        conn = self._connection()
        paths = list(self.discover())  # type: ignore[operator]
        on_disk: dict[str, float] = {}
        for p in paths:
            try:
                on_disk[str(p.resolve())] = p.stat().st_mtime
            except OSError:
                continue
        indexed: dict[str, float] = {}
        try:
            for row in conn.execute("SELECT path, mtime FROM corpus"):
                indexed[str(row[0])] = float(row[1] or 0.0)
        except sqlite3.Error:
            indexed = {}

        # Drop rows for docs that vanished.
        for gone in set(indexed) - set(on_disk):
            conn.execute("DELETE FROM corpus WHERE path = ?", (gone,))

        # (Re)index changed / new docs.
        changed_paths = [
            p
            for p in paths
            if str(p.resolve()) not in indexed
            or on_disk.get(str(p.resolve()), 0.0) > indexed.get(str(p.resolve()), -1.0)
        ]
        count = 0
        if changed_paths:
            for doc in read_corpus_docs(changed_paths):
                resolved = str(Path(doc.path).resolve())
                mtime = on_disk.get(resolved, 0.0)
                conn.execute("DELETE FROM corpus WHERE path = ?", (resolved,))
                conn.execute(
                    "INSERT INTO corpus (path, title, body, pointer, mtime) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (resolved, doc.title, doc.body, doc.pointer, mtime),
                )
                count += 1
        conn.commit()
        return count

    def search(
        self,
        *,
        query_tokens: list[str],
        num_results: int,
    ) -> list[dict[str, object]]:
        """BM25-rank the corpus for ``query_tokens``; top ``num_results``.

        Re-syncs first (AC.KP1.5 fresh read). ``query_tokens`` is an
        already-sanitised OR-of-tokens (see :mod:`work_anchor`); an
        empty token list returns ``[]`` (silent-on-no-match composes
        upstream). Returns ``[{path, title, pointer, score}]``.
        """
        if num_results <= 0 or not query_tokens:
            return []
        # Fresh read each turn — the index reflects mid-session corpus
        # writes without a restart (AC.KP1.5).
        try:
            self.sync()
        except sqlite3.Error:
            pass
        conn = self._connection()
        match = " OR ".join(query_tokens)
        sql = (
            "SELECT path, title, pointer, bm25(corpus) AS score "
            "FROM corpus WHERE corpus MATCH ? "
            "ORDER BY score LIMIT ?"
        )
        try:
            cur = conn.execute(sql, (match, num_results))
            rows = cur.fetchall()
        except sqlite3.Error:
            return []
        out: list[dict[str, object]] = []
        for path, title, pointer, score in rows:
            # SQLite bm25() is negative (lower = better); negate so
            # larger = stronger relevance.
            rel = -float(score) if score is not None else 0.0
            # AC.KP1.4 — drop pure-noise zero-IDF hits below the
            # relevance floor (silent-on-no-match).
            if rel < MIN_RELEVANCE_SCORE:
                continue
            out.append(
                {
                    "path": path,
                    "title": title,
                    "pointer": pointer,
                    "score": rel,
                }
            )
        return out
