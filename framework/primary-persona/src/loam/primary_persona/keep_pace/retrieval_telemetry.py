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

"""Standing per-turn retrieval telemetry — the baseline-capture layer
(memory redesign, standing-retrieval-telemetry cycle).

PURE OBSERVATION. This module records what the ranker ALREADY did: for
each turn where memory recall runs, the query (prompt + work-anchor)
against the candidate memories that were discovered (with their
discovery scores + event-time), which crossed into the injected set,
and the effective budget. It NEVER changes recall behavior, results, or
ordering.

The recorder is invoked as a side-effect at the end of
:func:`loam.primary_persona.keep_pace.retrieval.rank` — the single point
where BOTH the full candidate pool (corpus + episode + decision hits)
AND the injected subset (``decision_hits + merged``) are in scope. It
reads SCALAR COPIES off the already-computed hit dicts; it never mutates
a hit, never re-runs a search, and (per the design constraint) captures
the candidate pool the ranker actually fetched rather than perturbing
the flow to see a wider set.

Every write is FAIL-OPEN: any error (serialization, disk, permission)
is swallowed and the turn proceeds unchanged. The recorder is a no-op
when no telemetry sink is configured (``telemetry_dir is None``), so
direct-config callers (tests, the omnibus-penalty suite) are
unaffected — only the two live-wiring resolvers turn it on.

The log is an append-only JSONL file rotated per UTC day
(``retrieval-telemetry-<YYYY-MM-DD>.jsonl``) under the workspace's
gitignored ``.loam`` state dir — standing on disk, reviewable, and the
dataset the coming ranker cycle offline-tunes the relevance threshold +
recency re-weight against.

Stdlib-only. No hot-path LLM, no API key.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

# The on-disk telemetry schema version. Bumped when the record shape
# changes so an offline reader can branch on it.
TELEMETRY_SCHEMA_VERSION = 1

# The workspace-relative telemetry dir (sibling of the episode memory
# dir ``<workspace>/workspace/.loam/memory/``). ``.loam`` is gitignored,
# so the log is standing-on-disk yet untracked.
TELEMETRY_SUBDIR = "retrieval-telemetry"

# The per-day file stem; the UTC date + ``.jsonl`` are appended.
_FILE_STEM = "retrieval-telemetry"

# The per-candidate scalar fields lifted off a hit dict. Only these are
# read — the hit dict itself is never mutated.
_SOURCE_CORPUS = "corpus"
_SOURCE_EPISODE = "episode"
_SOURCE_DECISION = "decision"


def telemetry_dir_for_workspace(workspace_root: Path | str) -> Path:
    """Resolve the standing telemetry dir for ``workspace_root``.

    The path is ``<workspace>/workspace/.loam/retrieval-telemetry/`` —
    the ``.loam`` gitignored state dir, beside the episode memory store
    (mirrors :func:`file_memory.memory_dir_for_workspace`). The dir is
    NOT created here; :func:`record_retrieval` creates it lazily on
    first append.
    """
    from loam.workspace_bootstrap.workspace_paths import (  # noqa: WPS433
        WORKSPACE_STATE_SUBDIR,
    )

    # ``.loam`` mirrors file_memory.LOAM_SUBDIR without importing across
    # the module boundary on this cold path.
    ws_root = Path(workspace_root)
    return ws_root / WORKSPACE_STATE_SUBDIR / ".loam" / TELEMETRY_SUBDIR


def _daily_file(telemetry_dir: Path, *, now: datetime) -> Path:
    """The append target for the given instant — one file per UTC day."""
    day = now.astimezone(timezone.utc).strftime("%Y-%m-%d")
    return telemetry_dir / f"{_FILE_STEM}-{day}.jsonl"


def _source_of(hit: dict[str, object]) -> str:
    """Classify a hit by its origin store (fail-soft to corpus).

    Episode hits carry ``_episode``; decision-ledger hits carry
    ``_decision``; everything else is a corpus feedback-rule hit.
    """
    if hit.get("_decision"):
        return _SOURCE_DECISION
    if hit.get("_episode"):
        return _SOURCE_EPISODE
    return _SOURCE_CORPUS


def _num_or_none(value: object) -> Optional[float]:
    """Coerce a score-like value to float, or ``None`` (fail-soft)."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _candidate_record(
    hit: dict[str, object], *, injected: bool, rank: Optional[int]
) -> dict[str, object]:
    """Build the per-candidate telemetry record from a hit's scalars.

    Reads only — the hit dict is never mutated. ``score`` is the RAW
    discovery-relevance score (the ``score`` slot: BM25 × supersession
    for episodes, BM25 × length × supersession for corpus) — the signal
    the coming ranker cycle tunes a relevance threshold against.
    ``event_time`` is the EVENT time (episode ``valid_at`` /
    ``reference_time``), the signal for a recency re-weight; ``None``
    for timeless corpus rules.
    """
    return {
        "source": _source_of(hit),
        "path": str(hit.get("path", "") or "") or None,
        "pointer": str(hit.get("pointer", "") or "") or None,
        "score": _num_or_none(hit.get("score")),
        "salience": _num_or_none(hit.get("_salience")),
        "event_time": (str(hit.get("_event_time")) if hit.get("_event_time") else None),
        "injected": injected,
        "rank": rank,
    }


def build_record(
    *,
    prompt: str,
    work_anchor_tokens: Sequence[str],
    corpus_hits: Sequence[dict[str, object]],
    episode_hits: Sequence[dict[str, object]],
    decision_hits: Sequence[dict[str, object]],
    injected: Sequence[dict[str, object]],
    top_n: int,
    char_cap: int,
    turn_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict[str, object]:
    """Assemble one per-turn telemetry record (turn-level + candidates).

    The candidate pool is ``corpus_hits + episode_hits + decision_hits``
    (what the ranker fetched); the ``injected`` subset is the ordered
    list the turn actually surfaced (``decision_hits + merged``).
    Membership + rank are keyed on OBJECT IDENTITY so a candidate that
    the merge dropped (salience-gated / floored / deduped / top-N-cut)
    is recorded ``injected=false`` with no rank, while a surfaced one
    carries ``injected=true`` + its integer rank — the discovered-vs-
    injected distinction the dataset needs.
    """
    now = now or datetime.now(timezone.utc)
    injected_rank: dict[int, int] = {
        id(h): i for i, h in enumerate(injected)
    }
    candidates: list[dict[str, object]] = []
    for hit in list(corpus_hits) + list(episode_hits) + list(decision_hits):
        rank = injected_rank.get(id(hit))
        candidates.append(
            _candidate_record(hit, injected=rank is not None, rank=rank)
        )
    n_injected = sum(1 for c in candidates if c["injected"])
    return {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "turn_id": turn_id or uuid.uuid4().hex,
        "ts": now.astimezone(timezone.utc).isoformat(),
        "prompt": prompt,
        "work_anchor_tokens": list(work_anchor_tokens),
        "budget": {"top_n": top_n, "char_cap": char_cap},
        "counts": {"n_candidates": len(candidates), "n_injected": n_injected},
        "candidates": candidates,
    }


def record_retrieval(
    *,
    telemetry_dir: Optional[Path],
    prompt: str,
    work_anchor_tokens: Sequence[str],
    corpus_hits: Sequence[dict[str, object]],
    episode_hits: Sequence[dict[str, object]],
    decision_hits: Sequence[dict[str, object]],
    injected: Sequence[dict[str, object]],
    top_n: int,
    char_cap: int,
    turn_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> None:
    """Append one per-turn telemetry record — FAIL-OPEN, no-op if unset.

    Returns ``None`` always. Any error (no sink configured,
    serialization failure, unwritable path, disk full) is swallowed so
    the recorder can NEVER break the turn or perturb recall — the load-
    bearing pure-observation guarantee. The append is the only I/O and
    the hit dicts are read-only throughout.
    """
    if telemetry_dir is None:
        return
    try:
        record = build_record(
            prompt=prompt,
            work_anchor_tokens=work_anchor_tokens,
            corpus_hits=corpus_hits,
            episode_hits=episode_hits,
            decision_hits=decision_hits,
            injected=injected,
            top_n=top_n,
            char_cap=char_cap,
            turn_id=turn_id,
            now=now,
        )
        line = json.dumps(record, ensure_ascii=False)
        directory = Path(telemetry_dir)
        directory.mkdir(parents=True, exist_ok=True)
        target = _daily_file(directory, now=now or datetime.now(timezone.utc))
        with target.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:  # noqa: BLE001 — fail-open; telemetry never breaks a turn
        return


def build_situational_record(
    *,
    prompt: str,
    situation_tags: Sequence[str],
    matched_rules: Sequence[object],
    injected_rules: Sequence[object],
    rule_cap: int,
    char_cap: int,
    turn_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict[str, object]:
    """Assemble one ``{situation -> rules fired}`` telemetry record
    (memory redesign Stage 4 / AC.RSR).

    The situational-rules channel runs SEPARATELY from the store-(b) merge
    (it never enters ``rank``), so it emits its OWN record — ``kind:
    "situational-recall"`` — leaving the fact-recall record shape untouched
    (the RTEL suite's byte-identical guarantee holds). Both failure
    directions are measurable: an OVER-fire shows a large ``n_matched`` on a
    situation that should not have fired; an UNDER-fire shows an empty
    ``situation`` on a turn where a rule was wanted. ``rules`` carries each
    MATCHED rule's identity + whether it was injected (cap / budget may drop
    a matched rule) and its rank."""
    now = now or datetime.now(timezone.utc)
    injected_ids = {id(r): i for i, r in enumerate(injected_rules)}
    rules: list[dict[str, object]] = []
    for rule in matched_rules:
        rank = injected_ids.get(id(rule))
        rules.append(
            {
                "path": str(getattr(rule, "path", "") or "") or None,
                "directive": str(getattr(rule, "directive", "") or "") or None,
                "situation": list(getattr(rule, "situation", ()) or ()),
                "strength": getattr(rule, "strength", None),
                "injected": rank is not None,
                "rank": rank,
            }
        )
    return {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "kind": "situational-recall",
        "turn_id": turn_id or uuid.uuid4().hex,
        "ts": now.astimezone(timezone.utc).isoformat(),
        "prompt": prompt,
        "situation": list(situation_tags),
        "budget": {"rule_cap": rule_cap, "char_cap": char_cap},
        "counts": {
            "n_matched": len(rules),
            "n_injected": sum(1 for r in rules if r["injected"]),
        },
        "rules": rules,
    }


def record_situational_recall(
    *,
    telemetry_dir: Optional[Path],
    prompt: str,
    situation_tags: Sequence[str],
    matched_rules: Sequence[object],
    injected_rules: Sequence[object],
    rule_cap: int,
    char_cap: int,
    turn_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> None:
    """Append one ``{situation -> rules fired}`` record — FAIL-OPEN, no-op
    if unset. Same daily-rotated JSONL log as the fact-recall records
    (distinguished by ``kind: "situational-recall"``); any error is
    swallowed so the recorder can NEVER break the turn or perturb recall."""
    if telemetry_dir is None:
        return
    try:
        record = build_situational_record(
            prompt=prompt,
            situation_tags=situation_tags,
            matched_rules=matched_rules,
            injected_rules=injected_rules,
            rule_cap=rule_cap,
            char_cap=char_cap,
            turn_id=turn_id,
            now=now,
        )
        line = json.dumps(record, ensure_ascii=False)
        directory = Path(telemetry_dir)
        directory.mkdir(parents=True, exist_ok=True)
        target = _daily_file(directory, now=now or datetime.now(timezone.utc))
        with target.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:  # noqa: BLE001 — fail-open; telemetry never breaks a turn
        return
