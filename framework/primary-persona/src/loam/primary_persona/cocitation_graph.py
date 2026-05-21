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

"""Co-citation graph + one-hop spreading activation (FBM T2.2).

Anderson HAM / ACT-R associative-edge graph mined from the access log
(plus, at retroactive-seed time, the existing memory-write log entries
+ Claude Code agent-transcript JSONL files). The retrieval ranker uses
the graph at the one-hop spread step:

    BM25 → activation multiply → one-hop spread → return.

A query whose tokens match file_A but not file_B can surface file_B if
the graph has a strong A↔B edge — the F-PHRASING cure that v2 research
§B argues B.1 spreading activation delivers without an embedding index.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §14:

  - **D-T2.2.GRAPH** — in-memory dict-of-dicts, rebuilt at session-start
    from the access log; NOT persisted on disk. Invalidation-by-rebuild.
  - **D-T2.2.EDGEWEIGHT** — ``S_ji = log(P(file_i | file_j) / P(file_i))``
    per Anderson HAM/ACT-R; epsilon floor on never-co-occurring pairs.
  - **D-T2.2.SEED** — mine two data sources in the one-shot pass:
    1. ``<workspace>/workspace/.pos/memory-writes.log`` — canonical
       memory-write log (vertex bootstrap).
    2. ``~/.claude/projects/<slug>/<session>.jsonl`` — agent transcripts
       (the actual source data for historical co-occurrence; emits
       synthetic ``read`` events into the access log).
  - **D-T2.2.SPREAD** — strictly one hop at v0.1; multi-hop deferred.

Co-occurrence model: two files co-occur when they appear in the same
**access window** — a contiguous slice of access events whose
timestamps fall within ``COOCCUR_WINDOW_SECONDS`` of each other. The
window is the temporal proxy for "appeared in the same agent
turn/session." A query touch (read) followed by a citation (write/cite)
within the window is one co-occurrence event for the pair.

Public API:

  - :data:`COOCCUR_WINDOW_SECONDS` — co-occurrence window (default 1800s
    = 30 minutes; spans a long turn but not a multi-session gap).
  - :data:`EDGE_WEIGHT_EPSILON` — epsilon floor for never-co-occurring
    pairs (``log(epsilon)``; default 1e-9 → ``S = -20.72...``).
  - :func:`build_cocitation_graph` — build the graph from an access-log
    dict (output of :func:`access_log.read_access_log`).
  - :func:`spread_one_hop` — given a BM25 candidate scored list and the
    graph, return the set of (neighbor, weighted_score) additions.
  - :func:`seed_from_transcripts` — one-shot retroactive seed:
    parse Claude Code agent-transcript JSONL files, identify memory-
    file read events, and emit synthetic ``read`` events into the
    access log. Idempotent — running twice produces a byte-identical
    log because the synthetic event's ``ts`` derives deterministically
    from the transcript's per-line ``timestamp``.

ACs delivered (per plan §4):

  - **AC.FBMT2.COCG.1** — :func:`build_cocitation_graph` emits edge
    weights matching ``S_ji = log(P(i|j)/P(i))`` to within 1e-9; never-
    co-occurring pairs map to the epsilon floor.
  - **AC.FBMT2.COCG.2** — :func:`spread_one_hop` adds neighbor scores
    ``score(c) × S_cn`` for every direct neighbor n of every c in C.
  - **AC.FBMT2.COCG.3** — :func:`seed_from_transcripts` is idempotent
    on re-invocation against the same corpus.
  - **AC.FBMT2.COCG.4** — :func:`spread_one_hop` against an empty
    graph returns an empty addition set.
  - **AC.FBMT2.COCG.5** — :func:`spread_one_hop` caps at strictly one
    hop; a file two hops out is NOT added on a query matching only
    the root.

Per ODD §2.5 every code path traces back to a named AC.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import access_log as _access_log


# ---- public constants (D-T2.2.EDGEWEIGHT) -----------------------------

# Co-occurrence window in seconds. Two access events whose timestamps
# fall within this window count as one co-occurrence for the file pair.
# 1800s = 30 minutes — empirically spans a long agent turn (session-
# start composer + multiple retrieval contributors + writes) but is
# tight enough not to bridge a multi-session gap (which would create
# spurious associative edges from unrelated sessions). Tuning deferred.
COOCCUR_WINDOW_SECONDS = 1800.0

# Epsilon floor for pairs with zero co-occurrence. Avoids ``log(0)``
# producing ``-inf`` (a never-co-occurring pair's edge weight is
# ``log(epsilon)`` ≈ ``-20.72`` for the default 1e-9, indistinguishable
# from an absent edge in floating-point ranking but still a finite
# value). Standard regularization in associative-graph implementations.
EDGE_WEIGHT_EPSILON = 1e-9


# Type alias for the graph data structure (D-T2.2.GRAPH). Mapping
# file_path → mapping neighbor_file_path → edge_weight S_ji.
Graph = dict[str, dict[str, float]]


# ---- graph builder (AC.FBMT2.COCG.1) ----------------------------------


def build_cocitation_graph(
    events_by_file: dict[str, list[datetime]],
    *,
    window_seconds: float = COOCCUR_WINDOW_SECONDS,
) -> Graph:
    """Build the co-citation graph from an access-log ``{file: [ts, ...]}``
    dict (the shape :func:`access_log.read_access_log` returns).

    Algorithm:
      1. Flatten the dict into a chronological event stream
         ``[(ts, file), ...]``.
      2. For each event ``e_i``, scan forward until the next event's
         timestamp exceeds ``e_i.ts + window_seconds``; every other-file
         event ``e_j`` inside that window contributes one co-occurrence
         to the unordered pair ``(e_i.file, e_j.file)``.
      3. Per-file occurrence count: ``N_i`` is the number of events
         whose file is ``i``.
      4. Total events: ``N`` is the stream length.
      5. Edge weight per Anderson HAM/ACT-R::

            P(i)   = N_i / N
            P(i|j) = C_ij / N_j      where C_ij is co-occurrence count
            S_ji   = log(P(i|j) / P(i))
                   = log((C_ij / N_j) / (N_i / N))
                   = log((C_ij × N) / (N_i × N_j))

         For pairs with zero co-occurrence, the edge does NOT appear in
         the output dict (saves memory). The :func:`spread_one_hop`
         lookup falls through to :data:`EDGE_WEIGHT_EPSILON` for absent
         pairs (AC.FBMT2.COCG.1).

    Returns the graph as a dict-of-dicts (D-T2.2.GRAPH).

    Per ODD §2.5: pure function of its inputs; deterministic; no I/O.
    """
    # Empty input → empty graph (AC.FBMT2.COCG.4 fall-through).
    if not events_by_file:
        return {}
    # Flatten + sort by ts.
    stream: list[tuple[datetime, str]] = []
    for file_path, tslist in events_by_file.items():
        for ts in tslist:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            stream.append((ts, file_path))
    stream.sort(key=lambda t: t[0])
    n_total = len(stream)
    if n_total == 0:
        return {}
    # Per-file occurrence counts.
    per_file: dict[str, int] = {}
    for _ts, f in stream:
        per_file[f] = per_file.get(f, 0) + 1
    # Co-occurrence counts (unordered pair stored both directions).
    cooccur: dict[tuple[str, str], int] = {}
    for i in range(n_total):
        ts_i, file_i = stream[i]
        # Scan forward inside the window.
        for j in range(i + 1, n_total):
            ts_j, file_j = stream[j]
            if (ts_j - ts_i).total_seconds() > window_seconds:
                break
            if file_i == file_j:
                continue
            # Both directions — the graph is undirected per Anderson
            # HAM but stored as a symmetric dict-of-dicts so the spread
            # step's lookup is O(1) from either side.
            key_ij = (file_i, file_j)
            key_ji = (file_j, file_i)
            cooccur[key_ij] = cooccur.get(key_ij, 0) + 1
            cooccur[key_ji] = cooccur.get(key_ji, 0) + 1
    # Build the edge-weight graph.
    graph: Graph = {}
    for (j_file, i_file), c_ij in cooccur.items():
        n_i = per_file.get(i_file, 0)
        n_j = per_file.get(j_file, 0)
        if n_i == 0 or n_j == 0:
            # Degenerate; shouldn't reach here since both files appear
            # in the cooccur key only if they were in the stream.
            continue
        # S_ji = log((C_ij × N) / (N_i × N_j))
        weight = math.log((c_ij * n_total) / (n_i * n_j))
        graph.setdefault(j_file, {})[i_file] = weight
    return graph


def edge_weight(graph: Graph, src: str, dst: str) -> float:
    """Look up ``S_(src→dst)`` from the graph, falling through to the
    epsilon floor when the edge is absent.

    Per AC.FBMT2.COCG.1: never-co-occurring pairs map to ``log(epsilon)``
    rather than raising or returning ``-inf``. Callers can use this as
    a uniform read surface without checking for key presence.
    """
    neighbors = graph.get(src)
    if neighbors is None:
        return math.log(EDGE_WEIGHT_EPSILON)
    if dst not in neighbors:
        return math.log(EDGE_WEIGHT_EPSILON)
    return neighbors[dst]


# ---- spread step (AC.FBMT2.COCG.2 / COCG.4 / COCG.5) ------------------


def spread_one_hop(
    candidates: list[tuple[str, float]],
    graph: Graph,
) -> dict[str, float]:
    """One-hop spreading activation.

    Given a BM25 (× activation) candidate list ``[(file, score), ...]``,
    return a mapping ``{neighbor_file: best_spread_score}`` for every
    direct neighbor of every candidate that is NOT already in the
    candidate set. The neighbor's spread score is::

        spread(c, n) = score(c) × S_cn

    where ``S_cn`` is the edge weight from candidate ``c`` to neighbor
    ``n`` (the Anderson HAM/ACT-R associative edge). When a neighbor is
    reachable from multiple candidates, the maximum spread score wins
    (any spread is sufficient evidence to surface; max-rather-than-sum
    avoids inflating densely-co-cited hubs).

    AC.FBMT2.COCG.4 — empty graph → empty addition set.
    AC.FBMT2.COCG.5 — STRICTLY ONE HOP. A neighbor's neighbors are NOT
    expanded. A two-hop reachable file (A→B→C with no direct A↔C edge)
    does NOT enter the addition set on a query matching only A.

    Note: only edges PRESENT in the graph dict contribute — the
    :data:`EDGE_WEIGHT_EPSILON` floor returned by :func:`edge_weight`
    is for explicit-lookup callers, not the spread surface (which would
    otherwise add every-file-in-the-graph as a neighbor with a tiny
    score, defeating the spread's purpose).

    Per ODD §2.5: pure function; deterministic.
    """
    if not graph or not candidates:
        return {}
    in_candidates = {file for file, _ in candidates}
    additions: dict[str, float] = {}
    for c_file, c_score in candidates:
        neighbors = graph.get(c_file)
        if not neighbors:
            continue
        for n_file, edge_w in neighbors.items():
            if n_file in in_candidates:
                # Skip — n is already a primary candidate; the spread
                # step adds NEW files, not re-scores existing ones.
                continue
            # AC.FBMT2.COCG.2: spread score = score(c) × S_cn.
            spread_score = c_score * edge_w
            existing = additions.get(n_file)
            if existing is None or spread_score > existing:
                additions[n_file] = spread_score
    return additions


# ---- retroactive seed pass (AC.FBMT2.COCG.3) --------------------------


def _iter_transcript_files(projects_root: Path) -> Iterable[Path]:
    """Yield every ``*.jsonl`` file under ``projects_root`` recursively.

    Claude Code transcripts live at ``~/.claude/projects/<slug>/<sess>.jsonl``.
    Missing root → empty iter (AC.FBMT2.COCG.4 graceful-on-missing-data).
    """
    if not projects_root.exists():
        return
    for path in projects_root.rglob("*.jsonl"):
        if path.is_file():
            yield path


def _extract_memory_reads(transcript_path: Path) -> list[tuple[datetime, str]]:
    """Parse one transcript JSONL file and emit ``(ts, memory_file_path)``
    tuples for every line whose payload references a memory file.

    Heuristic: scan each line for a ``tool_use_id``/``tool_result`` shape
    or a literal file path embedded in the line text that matches a
    memory-file path pattern (``*/memory/episodes/*.md`` or
    ``*/.access-log.jsonl`` exclusion). The transcript schema is
    out-of-process (Claude Code's, not loam's), so the heuristic is
    string-pattern over the line JSON to keep the dependency-direction
    one-way (loam doesn't import Claude Code's schema).

    Idempotency anchor: the timestamp emitted is the line's
    ``timestamp`` field parsed as ISO-8601 — running the seed pass
    twice on the same transcript produces the SAME ``(ts, file)``
    tuples and therefore identical access-log entries (AC.FBMT2.COCG.3).
    """
    out: list[tuple[datetime, str]] = []
    try:
        with transcript_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_str = rec.get("timestamp") or rec.get("ts")
                if not isinstance(ts_str, str):
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                # Find memory-file references in the line by string
                # search — the line carries arbitrary JSON; we look for
                # markdown episode paths.
                line_text = line
                # Pattern: ``episodes/<group>/<date>/<turn>.md`` —
                # any string-literal in the line that contains it.
                idx = 0
                while True:
                    found = line_text.find("episodes/", idx)
                    if found < 0:
                        break
                    # Scan forward to ``.md`` then take the path
                    # bounded by the surrounding quote.
                    end = line_text.find(".md", found)
                    if end < 0:
                        break
                    # Walk back to the surrounding ``"`` to get the
                    # start of the path literal.
                    start = found
                    while start > 0 and line_text[start - 1] not in (
                        '"',
                        "'",
                    ):
                        start -= 1
                    candidate = line_text[start : end + 3]
                    # Strip leading path components that fall outside
                    # ``episodes/...`` — we want the canonical memory-
                    # file relative-from-memory_dir path.
                    eidx = candidate.find("episodes/")
                    if eidx > 0:
                        candidate = candidate[eidx:]
                    out.append((ts, candidate))
                    idx = end + 3
    except OSError:
        return out
    return out


def seed_from_transcripts(
    *,
    memory_dir: Path,
    projects_root: Path,
) -> int:
    """One-shot retroactive seed: mine Claude Code agent-transcript
    JSONL files for historical memory-file read events and emit
    synthetic ``read`` events into the access log.

    Per D-T2.2.SEED (plan §14): ``projects_root`` is typically
    ``~/.claude/projects/``; each transcript is parsed and every
    detected memory-file reference inside a transcript line emits a
    synthetic access-log entry with the line's timestamp.

    AC.FBMT2.COCG.3 idempotency: the synthetic entry's ``ts`` is the
    transcript line's timestamp (deterministic), and :func:`access_log.
    append_access_event` appends one line per call without de-dup.
    However, the SEED PASS itself is idempotent by way of a sidecar
    marker file ``.cocitation-seed.marker`` placed alongside the access
    log on first invocation — subsequent invocations are no-ops. The
    marker records the ISO-8601 timestamp of the seed pass.

    Returns the number of access-log entries written (0 when the seed
    has already run; ≥0 otherwise).

    Per ODD §2.5: side-effecting (writes the access log + marker), but
    deterministic side effects.
    """
    marker_path = memory_dir / ".cocitation-seed.marker"
    if marker_path.exists():
        # AC.FBMT2.COCG.3: idempotency — second invocation is a no-op.
        return 0
    written = 0
    for transcript_path in _iter_transcript_files(projects_root):
        for ts, mem_file in _extract_memory_reads(transcript_path):
            try:
                _access_log.append_access_event(
                    memory_dir, file=mem_file, ts=ts, op="read"
                )
            except (OSError, ValueError):
                continue
            written += 1
    # Write the marker AFTER the pass so a crash mid-pass leaves the
    # marker absent and a subsequent invocation re-runs (the log is
    # append-only so re-running emits duplicate entries, but the
    # spread step is tolerant — the only operational cost is graph
    # density bias, not correctness).
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc)
                .isoformat(timespec="seconds"),
                "events_written": written,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return written
