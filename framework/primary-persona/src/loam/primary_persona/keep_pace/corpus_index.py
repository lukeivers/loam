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

import math
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .work_anchor import tokenize as _tokenize_for_length


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

# AC.RQ80.2 (#80 omnibus length-normalization) — the OMNIBUS-BIAS lever. SQLite
# FTS5 ``bm25()`` length-normalizes at its fixed internal ``b=0.75``, but that is
# too weak against the OR-token query: a large omnibus doc matches MORE DISTINCT
# query terms (each weakly) and out-scores a focused single-rule doc on term
# mass. Measured (Tier-0, live pos3 corpus): a 1041-token omnibus and the
# 1188-token MEMORY index occupied top-5 slots for THREE unrelated queries. The
# fix applies a GENTLE, BOUNDED post-``bm25()`` length penalty to a doc longer
# than ``LENGTH_NORM_PIVOT_TOKENS``:
#     penalty = max(LENGTH_NORM_FLOOR, 1 / (1 + log(doclen / PIVOT)))
# (penalty = 1.0 for doclen <= PIVOT). BOUNDED BELOW by ``LENGTH_NORM_FLOOR`` so
# an omnibus doc is NUDGED DOWN, never penalized to zero — it stays retrievable
# (AC.RQ80.3). The pivot is set ABOVE the live corpus's longest genuinely-
# relevant FOCUSED rule (the 1217-token Telegram self-heal rule) so the penalty
# bites only true omnibus / index docs, never a relevant long rule — verified
# neutral on the live number and positive on a controlled fixture (a short
# focused doc beats an off-topic omnibus). TRUE token-length (not a char/space
# proxy, which over-penalizes a prose-dense relevant doc) is indexed at sync time
# as an UNINDEXED column (computed once, not per-query; UNINDEXED so FTS matching
# is byte-identical — AC-FBM-W-3 no-regression). NAMED, tunable constants:
# raising the pivot or the floor weakens the penalty (reversibility).
LENGTH_NORM_PIVOT_TOKENS = 1250
LENGTH_NORM_FLOOR = 0.5


def _length_penalty(doc_token_len: int) -> float:
    """The bounded omnibus length penalty for a doc's token length (AC.RQ80.2).

    Returns ``1.0`` (no-op) for a doc at or below
    :data:`LENGTH_NORM_PIVOT_TOKENS`; for a longer doc returns a multiplier in
    ``[LENGTH_NORM_FLOOR, 1.0)`` that shrinks gently with length and is BOUNDED
    BELOW by :data:`LENGTH_NORM_FLOOR` (never zero — the omnibus stays
    retrievable, AC.RQ80.3). A non-positive / malformed length resolves to the
    no-op ``1.0`` (fail-soft on the every-turn hot path).
    """
    if doc_token_len <= LENGTH_NORM_PIVOT_TOKENS or doc_token_len <= 0:
        return 1.0
    return max(
        LENGTH_NORM_FLOOR,
        1.0 / (1.0 + math.log(doc_token_len / LENGTH_NORM_PIVOT_TOKENS)),
    )

# AC-FBM-W (rule-weighting slice) — the per-rule importance gradient is a
# 1..100 scalar carried as optional ``weight`` frontmatter on a corpus doc.
# BASELINE_WEIGHT is the default a doc resolves to when it declares no weight;
# it is chosen so the gradient boost at the default is a NO-OP multiplier
# (boost = weight / BASELINE_WEIGHT = 1.0), preserving today's behaviour for
# the entire current corpus (no doc declares a weight). Kept here next to the
# corpus-doc reader, re-exported into retrieval where the boost is applied.
BASELINE_WEIGHT = 50
WEIGHT_MIN = 1
WEIGHT_MAX = 100

# AC.SUP.2 (FBM correctness cycle, Slice 3) — corpus-side honor of the
# T1.1 ``superseded-by`` marker convention: a marked doc's relevance is
# multiplicatively DEMOTED (mirroring the episode-side
# ``file_memory.SUPERSEDED_PENALTY`` semantics — demote, never blanket-
# delete from the index) so a superseded rule no longer outranks its
# successor for queries both match. ADDITIVE ranking factor: a doc with
# no marker multiplies by 1.0 exactly (today's corpus is byte-identical
# in score and rank). The episode-side constant is NOT imported across
# the package boundary on the hot path (mirrors the salience-default
# pattern) and its semantics are untouched.
CORPUS_SUPERSEDED_PENALTY = 0.1


@dataclass
class CorpusDoc:
    """One corpus document to index.

    AC-FBM-W — ``weight`` (1..100 importance gradient) + ``pinned`` (the hard
    floor: an always-include rule) are read from the doc's optional leading
    YAML frontmatter. A doc with no frontmatter resolves to
    ``weight=BASELINE_WEIGHT, pinned=False`` (the no-op baseline that keeps the
    current corpus byte-identical).
    """

    path: str
    title: str
    body: str
    pointer: str  # the plain-language pointer surfaced on a hit
    weight: int = BASELINE_WEIGHT  # AC-FBM-W-1 importance gradient
    pinned: bool = False  # AC-FBM-W-2 hard floor (always-include)
    # AC.RQ80.2 — TRUE token-length of the indexed body, computed once at read
    # time and carried into the FTS5 UNINDEXED ``doclen`` column so the omnibus
    # length penalty (:func:`_length_penalty`) needs no per-query tokenization.
    doc_token_len: int = 0
    # AC.SUP.2 — the doc's ``superseded-by`` marker value ("" = not
    # superseded). Read from frontmatter at index time; drives the
    # ranking demotion + the surfaced-hit annotation.
    superseded_by: str = ""


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


# AC-FBM-W — a leading YAML frontmatter block, ``---`` on its own first line
# through the next ``---`` line. Only the ``weight`` + ``pinned`` keys are read;
# the rest of the block (name/description/type/derivation) is metadata, not
# topical corpus prose, so it is stripped from the indexed body.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.DOTALL)
_FM_WEIGHT_RE = re.compile(r"^weight:[ \t]*(\S+)", re.MULTILINE)
_FM_PINNED_RE = re.compile(r"^pinned:[ \t]*(\S+)", re.MULTILINE)
# AC.SUP.2 — the T1.1 supersession-marker key (the same key
# ``file_memory._split_frontmatter`` parses episode-side and the
# Slice-3 marking entry point writes).
_FM_SUPERSEDED_RE = re.compile(r"^superseded-by:[ \t]*(\S+)", re.MULTILINE)


def _split_frontmatter(body: str) -> tuple[str, str]:
    """Split a leading YAML frontmatter block off the body.

    Returns ``(frontmatter_text, remaining_body)``. No leading ``---`` block
    => ``("", body)`` unchanged — the 102-of-132 no-frontmatter docs index
    byte-identically (AC-FBM-W-3 no-regression).
    """
    m = _FRONTMATTER_RE.match(body)
    if not m:
        return "", body
    return m.group(1), body[m.end():]


def _weight_pinned_from_frontmatter(fm_text: str) -> tuple[int, bool]:
    """Read ``weight`` (1..100, clamped) + ``pinned`` (bool) from frontmatter.

    Fail-soft: a missing key, a malformed value, or an empty block resolves to
    the no-op baseline ``(BASELINE_WEIGHT, False)`` — the every-turn hot path
    never raises on a malformed frontmatter block (AC-FBM-W-3).
    """
    weight = BASELINE_WEIGHT
    pinned = False
    if not fm_text:
        return weight, pinned
    wm = _FM_WEIGHT_RE.search(fm_text)
    if wm:
        try:
            w = int(wm.group(1).strip().strip("\"'"))
            weight = max(WEIGHT_MIN, min(WEIGHT_MAX, w))
        except (TypeError, ValueError):
            weight = BASELINE_WEIGHT
    pm = _FM_PINNED_RE.search(fm_text)
    if pm:
        pinned = pm.group(1).strip().strip("\"'").lower() in {"true", "yes", "1"}
    return weight, pinned


def _superseded_from_frontmatter(fm_text: str) -> str:
    """The ``superseded-by`` marker value, or ``""`` (AC.SUP.2).

    Fail-soft like the weight/pinned readers: no block / no key / a
    malformed line resolves to the unmarked no-op."""
    if not fm_text:
        return ""
    m = _FM_SUPERSEDED_RE.search(fm_text)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'")


def _plain_successor(successor: str) -> str:
    """A plain-language rendering of the successor pointer (AC.SUP.2 —
    the annotation the reader sees; never a file path / ``.md`` name,
    matching the ``_doc_pointer`` plain-by-construction discipline)."""
    stem = Path(successor).stem
    plain = stem.replace("_", " ").replace("-", " ").strip()
    if plain.lower().startswith("feedback "):
        plain = plain[len("feedback "):]
    return plain or "a newer rule"


def _annotate_superseded(pointer: str, superseded_by: str) -> str:
    """AC.SUP.2 — a surfaced superseded doc carries its supersession
    annotation: the reader sees "superseded by X", never the bare
    stale rule. An empty pointer stays empty (the doc is not a
    user-facing pointer at all)."""
    if not pointer or not superseded_by:
        return pointer
    return f"{pointer} (superseded by: {_plain_successor(superseded_by)})"


def read_corpus_docs(paths: Iterable[Path]) -> list[CorpusDoc]:
    """Read + shape the corpus docs for indexing (AC.KP1.1).

    AC-FBM-W — reads the optional ``weight``/``pinned`` frontmatter and strips
    the frontmatter block from the indexed body (the block is metadata, not
    topical prose, so dropping it removes only spurious metadata-key matches —
    the ``# Title`` + prose that carry the real topical signal are untouched).
    A doc with no frontmatter is unchanged: empty frontmatter, full body,
    baseline weight, unpinned.

    AC.SUP.2 — additionally reads the ``superseded-by`` marker; a
    marked doc's pointer is annotated at read time so EVERY surfaced
    occurrence carries the supersession notice. An unmarked doc is
    byte-identical to its pre-Slice-3 shape.
    """
    docs: list[CorpusDoc] = []
    for p in paths:
        try:
            raw = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm_text, body = _split_frontmatter(raw)
        weight, pinned = _weight_pinned_from_frontmatter(fm_text)
        superseded_by = _superseded_from_frontmatter(fm_text)
        title = _doc_title(p, body)
        indexed_body = body[:CORPUS_DOC_BODY_CAP]
        docs.append(
            CorpusDoc(
                path=str(p),
                title=title,
                body=indexed_body,
                pointer=_annotate_superseded(
                    _doc_pointer(p, title), superseded_by
                ),
                weight=weight,
                pinned=pinned,
                # AC.RQ80.2 — true token-length of the indexed body (the
                # same FTS tokenizer the query uses), for the omnibus penalty.
                doc_token_len=len(_tokenize_for_length(indexed_body)),
                superseded_by=superseded_by,
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
            "mtime UNINDEXED, weight UNINDEXED, pinned UNINDEXED, "
            "doclen UNINDEXED, superseded UNINDEXED)"
        )
        # AC-FBM-W / AC.RQ80.2 / AC.SUP.2 — the index is a DERIVED .scratch/
        # cache (the markdown is the source of truth). When an older-schema
        # index (pre-weight, pre-doclen, or pre-superseded) is on disk,
        # ``IF NOT EXISTS`` leaves it untouched and later INSERTs of the new
        # columns would raise. Detect the schema mismatch and rebuild from
        # scratch rather than migrate (the documented derived-cache contract).
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(corpus)")]
            if (
                "weight" not in cols
                or "pinned" not in cols
                or "doclen" not in cols
                or "superseded" not in cols
            ):
                conn.execute("DROP TABLE IF EXISTS corpus")
                conn.execute(
                    "CREATE VIRTUAL TABLE corpus "
                    "USING fts5(path UNINDEXED, title, body, pointer UNINDEXED, "
                    "mtime UNINDEXED, weight UNINDEXED, pinned UNINDEXED, "
                    "doclen UNINDEXED, superseded UNINDEXED)"
                )
        except sqlite3.Error:
            pass
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
                    "INSERT INTO corpus "
                    "(path, title, body, pointer, mtime, weight, pinned, "
                    "doclen, superseded) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        resolved,
                        doc.title,
                        doc.body,
                        doc.pointer,
                        mtime,
                        int(doc.weight),
                        1 if doc.pinned else 0,
                        int(doc.doc_token_len),
                        doc.superseded_by,
                    ),
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
        upstream). Returns ``[{path, title, pointer, score, weight, pinned}]``.

        AC-FBM-W-2 (the hard floor) — a ``pinned`` doc is the always-include
        floor: it is returned REGARDLESS of whether the query matched it, so a
        critical rule that is currently irrelevant to the prompt still surfaces.
        This is the load-bearing semantic ("always included regardless of
        relevance"): the relevance-ranked MATCH query alone cannot deliver it
        because a non-matching doc never appears in the MATCH result at all.
        Pinned docs the query did NOT match enter at relevance ``0.0`` (the
        floor); the downstream merge force-includes them ahead of the cut.
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
        # AC.RQ80.2 — fetch the per-doc ``doclen`` (UNINDEXED) for the omnibus
        # length penalty. Fetch a WIDER candidate window than ``num_results``
        # (ORDER BY raw bm25) so that when the penalty demotes an omnibus doc the
        # freed top-N slot can be filled by a focused doc that was just outside
        # the raw-bm25 cut. The penalized re-rank + truncation to ``num_results``
        # happens below.
        candidate_limit = max(num_results * 5, num_results)
        sql = (
            "SELECT path, title, pointer, weight, pinned, doclen, "
            "superseded, bm25(corpus) AS score "
            "FROM corpus WHERE corpus MATCH ? "
            "ORDER BY score LIMIT ?"
        )
        try:
            cur = conn.execute(sql, (match, candidate_limit))
            rows = cur.fetchall()
        except sqlite3.Error:
            return []
        out: list[dict[str, object]] = []
        seen: set[str] = set()

        def _emit(
            path, title, pointer, weight, pinned, rel, superseded=""
        ) -> None:
            try:
                w = int(weight) if weight is not None else BASELINE_WEIGHT
            except (TypeError, ValueError):
                w = BASELINE_WEIGHT
            out.append(
                {
                    "path": path,
                    "title": title,
                    "pointer": pointer,
                    "score": rel,
                    "weight": w,
                    "pinned": bool(pinned),
                    # AC.SUP.2 — the marker rides the hit so consumers
                    # can see the supersession ("" = not superseded).
                    "superseded_by": str(superseded or ""),
                }
            )
            seen.add(str(path))

        for path, title, pointer, weight, pinned, doclen, superseded, score in rows:
            # SQLite bm25() is negative (lower = better); negate so
            # larger = stronger relevance.
            rel = -float(score) if score is not None else 0.0
            # AC.RQ80.2 — apply the bounded omnibus length penalty. A doc longer
            # than the pivot is NUDGED DOWN (never to zero — bounded by
            # LENGTH_NORM_FLOOR) so a focused single-rule doc can out-rank a big
            # omnibus that matched many query terms weakly. A pinned hit is the
            # hard floor and is NOT length-penalized (its inclusion is by-design,
            # not by relevance — AC-FBM-W-2).
            is_pinned = bool(pinned)
            if not is_pinned:
                try:
                    rel = rel * _length_penalty(int(doclen) if doclen else 0)
                except (TypeError, ValueError):
                    pass
            # AC.SUP.2 — demote a superseded doc multiplicatively (the
            # episode-side SUPERSEDED_PENALTY semantics mirrored): a
            # marked rule no longer outranks its successor for queries
            # both match. Demote-not-filter at this step; the relevance
            # floor below applies to the final score exactly as it does
            # for the length penalty. A pinned hit is the hard floor and
            # is not demoted (its inclusion is by-design); it still
            # carries its annotation.
            if superseded and not is_pinned:
                rel = rel * CORPUS_SUPERSEDED_PENALTY
            # AC.KP1.4 — drop pure-noise zero-IDF hits below the relevance
            # floor (silent-on-no-match), applied to the PENALIZED score. A
            # PINNED hit bypasses the cut — the hard floor is carried regardless
            # of relevance (AC-FBM-W-2).
            if rel < MIN_RELEVANCE_SCORE and not is_pinned:
                continue
            _emit(path, title, pointer, weight, pinned, rel, superseded)

        # AC.RQ80.2 — re-rank by the PENALIZED relevance (descending) and
        # truncate the NON-PINNED matched hits to num_results: the wider
        # candidate window was fetched in raw bm25 order, so the penalty's
        # demotion of an omnibus only takes effect after this re-sort. Pinned
        # matched hits are NEVER truncated (the hard floor survives at its real
        # matched score — AC-FBM-W-2), so they are partitioned out and kept ahead
        # of the truncation. Stable on a secondary path key so the order is
        # deterministic for equal penalized scores (no clock / no randomness).
        pinned_out = [h for h in out if bool(h.get("pinned"))]
        rest_out = [h for h in out if not bool(h.get("pinned"))]
        rest_out.sort(key=lambda h: (-float(h["score"]), str(h["path"])))
        out = pinned_out + rest_out[:num_results]
        seen = {str(h["path"]) for h in out}

        # AC-FBM-W-2 — force-fetch every pinned doc the MATCH query did NOT
        # surface, so an always-include rule that is currently IRRELEVANT to
        # the prompt still enters the result set (at the relevance floor, 0.0).
        # This is the half a relevance-ranked query cannot do. Best-effort: a
        # sqlite error here degrades to the matched set (fail-soft hot path).
        try:
            pin_rows = conn.execute(
                "SELECT path, title, pointer, weight, superseded "
                "FROM corpus WHERE pinned = 1"
            ).fetchall()
        except sqlite3.Error:
            pin_rows = []
        for path, title, pointer, weight, superseded in pin_rows:
            if str(path) in seen:
                continue
            _emit(path, title, pointer, weight, 1, 0.0, superseded)
        return out
