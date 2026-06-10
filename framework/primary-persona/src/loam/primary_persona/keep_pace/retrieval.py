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

"""KP1 — the work-anchored per-prompt retrieval entry-point.

This module is the PRODUCTION entry-point (the surface AC.KP1.6's
cold-walk invokes with no pre-arranged state) + the KP0-chain
``Contributor``-compatible callable that the staged live wiring
registers.

Flow per turn (design §1 fix #1):
  1. Skip trivial prompts (greetings / acks) — AC.KP1.4.
  2. Read the active objectives + subgoals FRESH from the OBJECTIVES
     register (AC.KP5.5 binding; falls back to the in-source seed so
     the anchor always has the two real objectives — AC.KP1.6 no
     pre-arranged state).
  3. Build the work-anchored key (prompt + objective + subgoal +
     last-topic) — AC.KP1.2.
  4. BM25-rank the markdown corpus on the key, fresh-read each turn
     (AC.KP1.1 / AC.KP1.5).
  5. Inject the top-N <=5 pointers as plain-language additionalContext
     (AC.KP1.3); silent on no-match (AC.KP1.4).

The objective anchor is what rescues a vague prompt: "continue the
batch" tokenizes to almost nothing, but the active fiction objective's
text ("LitRPG", "Patch Notes for Reality", "production pipeline",
"canon") pulls the litrpg canon pointer out of the corpus. That is
tonight's failure, fixed (AC.KP1.6).

Registration into the KP0 chain (the
``framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py``
``contributors()`` surface) is part of the GATED live wiring — STAGED,
not done in this cycle (RF-6: live activation waits for a quiescent
production window). :func:`build_keep_pace_contributor` returns the
callable that staged wiring imports; its shape matches the chain's
``Contributor.fn`` contract (``fn(envelope: dict) -> Optional[str]``).

Stdlib-only. Fail-soft throughout — any boundary error yields an empty
injection and the turn proceeds (composes with the chain's
fail-open-whole-chain guarantee, AC.KP0.4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import objectives as _objectives
from .corpus_index import (
    BASELINE_WEIGHT,
    CorpusIndex,
    default_index_path,
    discover_corpus,
)
from .work_anchor import WorkAnchor, is_trivial_prompt


# AC.KP1.3 — top-N injection cap. The design recipe is N <= 5.
DEFAULT_TOP_N = 5

# AC.SRF.3 (memory recall cycle, Slice 2) — the NAMED, tunable
# ~5KB-class per-turn injection budget, sized to accommodate at least
# THREE whole structured records (decision records and equivalents)
# plus substantive pointer lines. The pre-cycle 1200-char cap was
# tuned for a context-scarcity regime that 1M-token context windows
# ended; the truncated, path-less pointer block it produced was one of
# the three legs of the 2026-06-09 $750k recall failure.
INJECTION_CHAR_CAP = 5000

# AC.FBMU.1 — neutral merge score for an episode hit that arrived via
# the store's grep-fallback path (no BM25 score). Placed at the corpus
# relevance floor so a scored corpus hit outranks an unscored episode
# but the episode still merges into the result set rather than dropping.
MERGE_NEUTRAL_SCORE = 0.1

# AC.FBMU.1 — cap the episode pointer summary so a long turn body cannot
# bloat a single pointer line; the block byte budget (INJECTION_CHAR_CAP)
# is the outer ceiling, this keeps any one episode pointer glanceable.
# AC.SRF.3: raised with the budget so pointers carry substantive text.
_EPISODE_POINTER_CAP = 320

# B3 (AC-FBM-SAL-1/-4) — the salience gate threshold. An episode hit whose
# structural salience is BELOW this is force-DROPPED from the SURFACED set
# (the recall side of the never-not-store / gate-surfacing-only invariant).
# A NAMED, tunable constant: lowering it re-admits previously-gated junk
# episodes (AC-FBM-SAL-4 re-tunable), proving the gate is reversible and
# nothing was lost. Structural junk scores 0.0 (< 0.5 → gated); a
# substantive turn scores 1.0 (>= 0.5 → surfaces). Corpus hits + any hit
# with no declared salience ride at the full-salience default (never gated).
SALIENCE_THRESHOLD = 0.5

# B3 — the full-salience default. A hit with no ``_salience`` slot (every
# corpus hit; any episode written before the salience field, whose body
# nonetheless scores fresh in the search path) rides at full salience so the
# gate can only ever drop a hit affirmatively scored as junk (never-drop
# floor). Mirrors ``file_memory.SALIENCE_FULL`` without importing across the
# package boundary on the hot path.
_SALIENCE_FULL_DEFAULT = 1.0

# AC-FBM-FLOOR-1 (Slice B / B1) — the ABSOLUTE EPISODE RELEVANCE FLOOR. An
# episode hit whose RAW BM25 relevance (the ``_bm25_raw`` slot — the negated
# sqlite ``bm25()``, larger = stronger) is below this is dropped from the
# surfaced set BEFORE the per-source min-max normalization (:func:`_minmax_norm`)
# — BUT ONLY when at least one OTHER episode in the same result set clears the
# floor (see :func:`_apply_episode_floor`). Rationale (Tier-0, verified against
# the live 1400-episode store this session): in a POPULATED index a genuine
# multi-term episode match scores 5–20 on this scale, so ``0.1`` filters only
# the pure-noise zero-IDF single-common-word hits (the FM-4 keyword-density bug —
# a weak episode min-max-promoted to ``1.0`` out-ranking a real corpus
# feedback-rule). The value MIRRORS the corpus floor
# ``corpus_index.MIN_RELEVANCE_SCORE = 0.1`` on the identical negated-BM25 scale.
# The "at least one other episode clears it" guard is the OVER-FILTER SAFEGUARD:
# in the SPARSE / fresh-write regime BM25's IDF term collapses and EVERY episode
# (relevant or not) scores ~0 — there raw BM25 is not a relevance discriminator,
# so the floor SELF-DISABLES and the min-max rescue of a lone relevant episode is
# preserved (the sealed AC-FBM-RN-2 / AC.FBMU.1 contract). A NAMED, tunable
# constant: lowering it re-admits previously-floored episodes (reversibility,
# mirroring the salience threshold). Corpus hits are floored at source; pinned
# rules are never floored (the hard floor survives).
EPISODE_MIN_RELEVANCE_SCORE = 0.1

# AC-FBM-DEDUP-1 (Slice B / B2) — the NEAR-DUPLICATE token-Jaccard threshold.
# Among the surfaced hits, a later hit whose token-set Jaccard with an
# already-kept hit EXCEEDS this collapses (only one occupies a top-N slot; the
# freed slot is filled by the next distinct hit). 0.85 is the GBrain near-dup
# threshold the parent plan specifies — high enough that only near-identical
# openings collapse (two genuinely-distinct turns that merely share vocabulary
# score well below 0.85 on full token sets), which is the conservative end
# (a lower threshold risks collapsing distinct context — the named over-filter
# risk). Stdlib token-set Jaccard — NO embeddings, NO API key
# (``feedback_no_anthropic_api_key``). A NAMED, tunable constant.
DEDUP_JACCARD_THRESHOLD = 0.85

# Token-shape for the dedup Jaccard — alnum/underscore runs, lowercased. Mirrors
# the FTS tokenizer's content shape so the duplicate signal keys on content
# tokens, not punctuation.
_DEDUP_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass
class RetrievalConfig:
    """Resolution config for the work-anchored retrieval entry-point.

    All paths are injectable so AC.KP1.6's cold-walk + the unit tests
    point at fixture dirs rather than the live machine. In live wiring
    these default to the user-scope memory dir + ``~/.claude`` home.

    ``episode_memory_dir`` (AC.FBMU.1) is the FBM episode store's
    ``<workspace>/workspace/.loam/memory/`` dir — distinct from
    ``memory_dir`` (the ``feedback_*.md`` markdown corpus). When set,
    :func:`retrieve` queries the episode store via
    ``FileMemoryStore.search`` and merges its episode hits into the
    corpus result set by score (D2 unify). When ``None`` or empty the
    merge contributes zero and the corpus-side output is byte-identical
    to the pre-unify KP1 output (AC.FBMU.2 — fail-open / no-regression).
    """

    workspace_root: Path
    memory_dir: Optional[Path] = None
    claude_homes: tuple[Path, ...] = ()
    objectives_home: Optional[Path] = None  # base for OBJECTIVES.md
    top_n: int = DEFAULT_TOP_N
    # AC.FBMU.1 — FBM episode store dir; None => unify contributes
    # nothing (pre-unify behaviour preserved, AC.FBMU.2).
    episode_memory_dir: Optional[Path] = None
    # AC.FBMU.1 — episode group ids to scope the episode search; None
    # => the store searches every group (the live workspace slug).
    episode_group_ids: Optional[tuple[str, ...]] = None

    def objectives_path(self) -> Path:
        return _objectives.user_scope_objectives_path(self.objectives_home)


def _build_index(config: RetrievalConfig) -> CorpusIndex:
    """Construct the CorpusIndex with a FRESH corpus discovery closure.

    The discover closure re-runs on every sync so a corpus file added
    mid-session is picked up (AC.KP1.5 fresh-read).
    """
    obj_path = config.objectives_path()

    def _discover() -> list[Path]:
        return discover_corpus(
            memory_dir=config.memory_dir,
            claude_homes=config.claude_homes,
            objectives_path=obj_path if obj_path.is_file() else None,
        )

    return CorpusIndex(
        index_path=default_index_path(config.workspace_root),
        discover=_discover,
    )


def _render_injection(hits: list[dict[str, object]], *, cap: int) -> str:
    """Render the top-N merged hits as MODEL-facing additionalContext.

    AC.KP1.3: a ``[keep-pace]`` block listing the on-file topics the
    live work points at, in plain language. Silent on no hits
    (AC.KP1.4) — returns ``""``.

    Memory recall cycle, Slice 2 (AC.SRF.1–3):

      - **AC.SRF.1** — every pointer line carries its source path
        (``[source: <path>]``) when the hit has one, so the model can
        follow the pointer. This block is MODEL-facing context (the
        pre-cycle "NO file paths" rule mis-applied the KP9 user-prose
        lint here — a scope error this cycle reverses; the lint keeps
        its correct user-facing scope on outbound drafts).
      - **AC.SRF.3** — a hit flagged ``_whole_record`` (decision
        records and equivalents) renders its ``record_text`` WHOLE —
        ruling + reasoning + source pointer — never truncated to a
        one-line pointer. A record that does not fit the remaining
        budget is dropped whole, never half-emitted; pointer lines
        keep filling the remaining budget.
    """
    if not hits:
        return ""
    header = "[keep-pace] On-file context relevant to what you're working on:"
    lines: list[str] = [header]
    budget_used = len(header) + 1
    for h in hits:
        path = str(h.get("path", "") or "").strip()
        if h.get("_whole_record"):
            record_text = str(h.get("record_text", "") or "").strip()
            if not record_text:
                continue
            title = str(h.get("pointer", "") or "").strip() or "record"
            block = (
                f"  === record: {title}"
                + (f" (source: {path}) ===" if path else " ===")
                + "\n"
                + record_text
            )
            if budget_used + len(block) + 1 > cap:
                continue  # AC.SRF.3 — drop whole, never half-emit
            lines.append(block)
            budget_used += len(block) + 1
            continue
        pointer = str(h.get("pointer", "")).strip()
        if not pointer:
            continue
        line = f"  - {pointer}" + (f" [source: {path}]" if path else "")
        if budget_used + len(line) + 1 > cap:
            break
        lines.append(line)
        budget_used += len(line) + 1
    return "\n".join(lines) if len(lines) > 1 else ""


def _episode_hits(
    *, query_tokens: list[str], config: RetrievalConfig, num_results: int
) -> list[dict[str, object]]:
    """Query the FBM episode store + shape hits like corpus hits (AC.FBMU.1).

    Returns ``[{pointer, path, score}]`` shaped to merge with the
    corpus hits' ``{path, title, pointer, score}`` shape under
    :func:`_render_injection` (which reads ``pointer`` + ``path`` +
    ``score``). AC.SRF.1 (memory recall cycle, Slice 2): the episode's
    source path rides on the hit so the rendered pointer line carries
    a followable ``[source: <path>]``, same as corpus hits.
    Empty / absent episode store => ``[]`` (AC.FBMU.2 — corpus-side
    output unchanged). Fail-soft: any boundary error yields ``[]`` so
    the merge degrades to corpus-only (chain fail-open, AC.KP0.4).
    """
    if config.episode_memory_dir is None or num_results <= 0 or not query_tokens:
        return []
    try:
        from ..file_memory import FileMemoryStore

        store = FileMemoryStore(memory_dir=Path(config.episode_memory_dir))
        group_ids = (
            list(config.episode_group_ids)
            if config.episode_group_ids is not None
            else None
        )
        # The episode FTS index is term-OR ranked the same way the
        # corpus index OR-joins the work-anchored tokens.
        result = store.search(
            query=" ".join(query_tokens),
            group_ids=group_ids,
            num_results=num_results,
        )
    except Exception:  # noqa: BLE001 — fail-soft; merge degrades to corpus-only
        return []
    hits: list[dict[str, object]] = []
    for ep in result.get("episodes", []):
        if not isinstance(ep, dict):
            continue
        # The episode store's ranking (BM25 × activation × supersession
        # × co-citation) is preserved on the ``_bm25_raw`` slot; fall
        # back to a neutral score when the grep-fallback path produced
        # the hit (no BM25 score) so the episode still merges.
        score = ep.get("_bm25_raw")
        try:
            score_val = float(score) if score is not None else MERGE_NEUTRAL_SCORE
        except (TypeError, ValueError):
            score_val = MERGE_NEUTRAL_SCORE
        pointer = _episode_pointer(ep)
        if not pointer:
            continue
        # B3 (AC-FBM-SAL-1) — carry the episode's structural salience onto
        # the hit so the merge can gate below-threshold (junk) episodes out
        # of the surfaced set. Absent => full salience (never-drop default).
        salience = ep.get("_salience")
        try:
            salience_val = (
                float(salience)
                if salience is not None
                else _SALIENCE_FULL_DEFAULT
            )
        except (TypeError, ValueError):
            salience_val = _SALIENCE_FULL_DEFAULT
        # AC.SRF.1 — carry the episode's source path onto the hit so
        # the model-facing render can emit a followable pointer.
        path = str(ep.get("path", "") or "").strip()
        hits.append(
            {
                "pointer": pointer,
                "path": path,
                "score": score_val,
                "_episode": True,
                "_salience": salience_val,
            }
        )
    return hits


def _episode_pointer(ep: dict[str, object]) -> str:
    """Plain-language pointer for an episode hit (AC.FBMU.1).

    Surfaces the episode's CONTENT summary, NOT the opaque
    ``turn/<id>`` name (an internal id is never a useful pointer).
    Falls back to a cleaned name only when the body is empty.

    AC.SRF.2 (memory recall cycle, Slice 2): the summary is the shared
    :func:`memory_consumer.salient_snippet` — the first SUBSTANTIVE
    line of the turn body, never a channel envelope /
    task-notification header / role label — so both model-facing
    render paths derive pointer text from salient content. (The
    pointer text itself stays path-free; the source path rides
    separately on the hit per AC.SRF.1 and is rendered by
    :func:`_render_injection`.)
    """
    content = str(ep.get("content", "") or "").strip()
    summary = ""
    if content:
        # Lazy cross-module import (module convention — keep_pace stays
        # importable without the persona's full consumer surface).
        from ..memory_consumer import salient_snippet

        # AC.SRF.2 — first substantive line, envelope junk skipped.
        first = salient_snippet(content, cap=_EPISODE_POINTER_CAP)
        # Trim to the first sentence so the pointer stays glanceable.
        for sep in (". ", "! ", "? "):
            idx = first.find(sep)
            if 0 < idx < len(first):
                first = first[: idx + 1]
                break
        summary = first.rstrip()
    if not summary:
        name = str(ep.get("name", "") or "").strip()
        # Strip the internal ``turn/`` prefix; an opaque turn-id is not
        # a user-facing pointer, so a name-only episode degrades to no
        # pointer (dropped by _render_injection) rather than leaking it.
        if name.startswith("turn/"):
            return ""
        summary = name
    if not summary:
        return ""
    return f"From an earlier turn: {summary}"


def _decision_hits(
    *, query_tokens: list[str], config: RetrievalConfig
) -> list[dict[str, object]]:
    """Decision-ledger hits shaped for whole-record injection
    (AC.DLG.3 + AC.SRF.3 — memory recall cycle, Slice 3).

    The ledger lives beside the episode store
    (``<episode_memory_dir>/decisions/``); no separate config knob —
    where episodes go, decisions go. Two sub-sources, deduped by path:

      - query-matched records (entity-vocabulary match), and
      - ``status: open`` records, surfaced WITHOUT an explicit query
        (an open owner question rides along on work-anchored turns).

    Every hit carries ``_whole_record`` + ``record_text`` so
    :func:`_render_injection` emits the ruling WHOLE — question,
    ruling, reasoning, source pointer — never a one-line pointer.
    Fail-soft: no ledger / any boundary error contributes nothing.
    """
    if config.episode_memory_dir is None:
        return []
    try:
        from ..decision_ledger import open_decisions, search_decisions

        matched = search_decisions(
            config.episode_memory_dir, query_tokens
        )
        opens = open_decisions(config.episode_memory_dir)
    except Exception:  # noqa: BLE001 — fail-soft; ledger degrades to absent
        return []
    hits: list[dict[str, object]] = []
    seen: set[str] = set()
    for rec in list(matched) + list(opens):
        if rec.path in seen:
            continue
        seen.add(rec.path)
        hits.append(
            {
                "pointer": rec.question or rec.ruling,
                "path": rec.path,
                "score": 1.0,
                "_whole_record": True,
                "record_text": rec.record_text(),
                "_decision": True,
            }
        )
    return hits


def rank(
    *,
    prompt: str,
    config: RetrievalConfig,
    last_topic: str = "",
    salience_threshold: float = SALIENCE_THRESHOLD,
) -> list[dict[str, object]]:
    """The PRODUCTION ranked-hit accessor — the ordered merged hit list,
    PRE-render, that :func:`retrieve` injects (AC.KP1.6 + AC.FBM-P5-METRIC.*).

    Runs the EXACT production retrieval pipeline — trivial-skip, fresh
    objectives, work-anchor key, corpus :meth:`CorpusIndex.search`, episode
    :func:`_episode_hits`, and :func:`_merge_by_score` (salience gate +
    absolute floor + dedup + weight/salience boost + top-N) — and returns the
    ordered list of merged hits. :func:`retrieve` delegates to this then
    renders; the P@5 retrieval-relevance metric reads this to inspect each
    top-N hit's identity (the rendered string discards per-hit identity).
    There is exactly ONE ranking code path: what the metric measures IS what
    the production turn injects.

    Returns ``[]`` for a trivial prompt (AC.KP1.4 skip) or an empty
    work-anchor key (silent-on-no-match); fail-soft on the corpus search
    (chain fail-open, AC.KP0.4).
    """
    if is_trivial_prompt(prompt):
        return []

    # Read objectives FRESH (AC.KP5.5 binding; seed fallback => no
    # pre-arranged state needed for AC.KP1.6).
    try:
        objs = _objectives.load_user_scope_register(config.objectives_home)
    except Exception:  # noqa: BLE001 — fail-soft; anchor degrades to prompt-only
        objs = list(_objectives.SEEDED_OBJECTIVES)

    anchor = WorkAnchor(
        prompt=prompt,
        objective_texts=_objectives.active_objective_texts(objs),
        subgoals=_objectives.active_subgoals(objs),
        last_topic=last_topic,
    )
    query_tokens = anchor.query_tokens()
    if not query_tokens:
        return []

    index = _build_index(config)
    try:
        corpus_hits = index.search(
            query_tokens=query_tokens, num_results=config.top_n
        )
    except Exception:  # noqa: BLE001 — fail-soft per chain fail-open contract
        corpus_hits = []
    finally:
        index.close()

    # D2 unify (AC.FBMU.1) — query the FBM episode store and merge its
    # hits with the corpus hits by score. With no episode store
    # configured this returns [] and the merged set equals corpus_hits
    # exactly (AC.FBMU.2 byte-identical no-regression).
    episode_hits = _episode_hits(
        query_tokens=query_tokens, config=config, num_results=config.top_n
    )
    merged = _merge_by_score(
        corpus_hits,
        episode_hits,
        top_n=config.top_n,
        salience_threshold=salience_threshold,
    )
    # AC.DLG.3 (memory recall cycle, Slice 3) — decision records are a
    # THIRD merged source, positioned FIRST for whole-record injection
    # (a matched ruling IS the answer's substance; AC.SRF.3 renders it
    # whole). Query-matched records + ``status: open`` records on the
    # ledger (the latter surface WITHOUT an explicit query). With no
    # ledger on disk this contributes nothing and the merged output is
    # unchanged (the AC.FBMU.2 no-regression envelope extends here).
    decision_hits = _decision_hits(query_tokens=query_tokens, config=config)
    return decision_hits + merged


def retrieve(
    *,
    prompt: str,
    config: RetrievalConfig,
    last_topic: str = "",
    salience_threshold: float = SALIENCE_THRESHOLD,
) -> str:
    """The PRODUCTION work-anchored retrieval entry-point (AC.KP1.6).

    Invoked with no pre-arranged retrieval state — it reads the
    objectives fresh, builds the work-anchored key, syncs + searches
    the corpus, and returns the plain-language injection (or ``""``).

    Delegates to :func:`rank` for the ranking (the single ranking code
    path) then renders the ordered merged hits via :func:`_render_injection`
    — the output is byte-identical to the pre-refactor inline pipeline (the
    KP1 / FBMU / FBM-FILTER suite is the no-regression guard).

    AC.KP1.4: a trivial prompt returns ``""`` (skipped) before any
    work; a no-match returns ``""`` (silent).
    AC.KP1.6: a vague "continue" + an active fiction objective surfaces
    the litrpg canon pointer via the objective anchor — the objective
    text supplies the tokens the bare prompt cannot.
    AC.FBMU.1: when an episode store is configured, a single retrieval
    call returns BOTH a corpus hit AND an episode hit for a query that
    matches both corpora — the two physical indexes are merged at the
    retrieval call by score, under the same top-N + byte budget.
    AC.FBMU.2: an absent / empty episode store leaves the corpus-side
    output byte-identical to the pre-unify KP1 output.
    AC.FBMU.3: the merged surface respects the top-N <= 5 cap +
    INJECTION_CHAR_CAP byte budget (episode hits cannot blow it).
    AC-FBM-SAL-1: a structural-junk episode (a ``<task-notification>``
    turn, an empty channel event, a bare ack) is tagged near-zero
    salience at ingest and is force-DROPPED from the surfaced set here,
    so it does not surface even when it shares tokens with the query.
    AC-FBM-SAL-4: ``salience_threshold`` is tunable per call — lowering
    it re-admits previously-gated junk episodes (the gate is reversible;
    the episode was never removed from disk, only gated from surfacing).
    """
    merged = rank(
        prompt=prompt,
        config=config,
        last_topic=last_topic,
        salience_threshold=salience_threshold,
    )
    return _render_injection(merged, cap=INJECTION_CHAR_CAP)


def _minmax_norm(hits: list[dict[str, object]]) -> list[float]:
    """Min-max-normalize one source's raw scores onto ``[0, 1]``.

    AC-FBM-RN — the two physical indexes emit BM25 on incompatible,
    regime-dependent scales (corpus ~15–285 vs episode 0–40 in the live
    store, and ~0.0 for a freshly-written episode in a sparse FTS index —
    BM25's IDF term collapses with few documents). Raw-score merging
    therefore buries every episode below the corpus head (scale mismatch)
    AND truncates a fresh relevant episode out entirely (it scores ~0).
    Min-max maps each source's BEST matched hit to ``1.0`` and worst to
    ``0.0`` so the genuinely-best result per source competes fairly.

    A single-element or all-equal source maps every hit to ``1.0`` — a
    present, FTS-matched hit is fully its-source-best. This is what
    rescues the sparse-store regime (a lone relevant episode at raw 0.0
    still surfaces). Relevance is gated upstream: ``_episode_hits`` /
    ``CorpusIndex.search`` only return hits the query actually matched, so
    normalization never force-surfaces noise.
    """
    if not hits:
        return []
    scores = [float(h.get("score", 0.0) or 0.0) for h in hits]
    lo = min(scores)
    span = max(scores) - lo
    if span <= 0.0:
        return [1.0] * len(hits)
    return [(s - lo) / span for s in scores]


def _weight_of(hit: dict[str, object]) -> int:
    """The hit's importance weight (AC-FBM-W-1), fail-soft to BASELINE_WEIGHT.

    Episode hits and any hit without a declared weight ride at the baseline,
    where the gradient boost factor is exactly ``1.0`` (no-op) — so the merge
    is byte-identical for a corpus where no doc declares a weight (today's
    corpus, AC-FBM-W-3).
    """
    w = hit.get("weight")
    try:
        return int(w) if w is not None else BASELINE_WEIGHT
    except (TypeError, ValueError):
        return BASELINE_WEIGHT


def _is_pinned(hit: dict[str, object]) -> bool:
    """Whether the hit is the hard floor (AC-FBM-W-2) — an always-include rule.

    Episode hits are never pinned (no frontmatter surface); a hit without the
    key is unpinned (fail-soft).
    """
    return bool(hit.get("pinned"))


def _salience_of(hit: dict[str, object]) -> float:
    """The hit's structural salience (B3, AC-FBM-SAL-1), fail-soft to full.

    Junk episodes carry a near-zero salience; substantive episodes + every
    corpus hit (which never declares the slot) ride at the full-salience
    default. Any malformed value also resolves to full salience — the
    never-drop floor, so the gate only ever suppresses an affirmatively
    junk-scored hit.
    """
    s = hit.get("_salience")
    try:
        return float(s) if s is not None else _SALIENCE_FULL_DEFAULT
    except (TypeError, ValueError):
        return _SALIENCE_FULL_DEFAULT


def _bm25_raw_of(hit: dict[str, object]) -> float:
    """The episode hit's RAW BM25 relevance (AC-FBM-FLOOR-1), fail-soft to 0.0.

    Carried on the ``score`` slot for an episode hit (``_episode_hits`` set it
    to ``_bm25_raw`` — the negated sqlite ``bm25()``, larger = stronger). A hit
    with no usable score resolves to ``0.0`` so a malformed episode floors out
    rather than surfacing on a noise score (the floor is a quality gate; a
    score-less episode carries no relevance evidence).
    """
    s = hit.get("score")
    try:
        return float(s) if s is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _apply_episode_floor(
    episode_hits: list[dict[str, object]], *, floor: float
) -> list[dict[str, object]]:
    """Drop sub-floor episode hits when the floor is a meaningful discriminator.

    AC-FBM-FLOOR-1 (B1) — the ABSOLUTE EPISODE RELEVANCE FLOOR with its
    over-filter safeguard. An episode whose raw BM25 (the ``score`` slot =
    ``_bm25_raw``) is below ``floor`` is dropped — BUT ONLY when at least one
    OTHER episode clears the floor. The guard distinguishes the two regimes:

      - POPULATED index (production) — genuine matches score well above the
        floor; a pure-noise zero-IDF episode below the floor is dropped (FM-4:
        it can no longer be min-max-promoted to 1.0 and out-rank a corpus rule).
      - SPARSE / fresh-write index — BM25's IDF term collapses and EVERY episode
        scores ~0, relevant or not. Raw BM25 is not a discriminator here, so the
        floor self-disables (nothing clears it → no drop) and the sealed min-max
        rescue of a lone relevant episode is preserved (AC-FBM-RN-2 / AC.FBMU.1).

    Conservative by construction: the floor only ever removes an episode that is
    BOTH below the absolute floor AND out-competed by another above-floor episode
    — never a lone relevant-but-sparse hit (the named over-filter risk).
    """
    if not episode_hits:
        return episode_hits
    if not any(_bm25_raw_of(h) >= floor for h in episode_hits):
        # Sparse regime — no episode is a meaningful-BM25 discriminator; the
        # floor self-disables so a lone relevant episode is not over-filtered.
        return episode_hits
    return [h for h in episode_hits if _bm25_raw_of(h) >= floor]


def _dedup_tokens(hit: dict[str, object]) -> frozenset[str]:
    """The hit's content token-set for the near-dup Jaccard (AC-FBM-DEDUP-1).

    Tokens are the lowercased alnum/underscore runs of the hit's plain-language
    ``pointer`` — the exact text that would be surfaced — so two hits that would
    render near-identically are recognized as duplicates. Stdlib-only; no
    embeddings, no API key.
    """
    pointer = str(hit.get("pointer", "") or "")
    return frozenset(t.lower() for t in _DEDUP_TOKEN_RE.findall(pointer))


def _is_near_duplicate(
    a: frozenset[str], b: frozenset[str], *, threshold: float
) -> bool:
    """Whether two token-sets exceed the near-dup Jaccard ``threshold``.

    AC-FBM-DEDUP-1 — token-set Jaccard ``|a ∩ b| / |a ∪ b|``. Two empty sets are
    NOT duplicates (no content to compare — fail toward keeping distinct hits,
    the conservative side against over-collapse).
    """
    union = a | b
    if not union:
        return False
    return (len(a & b) / len(union)) > threshold


def _dedup_hits(
    ordered: list[dict[str, object]], *, threshold: float
) -> list[dict[str, object]]:
    """Collapse near-duplicate hits in a ranked list (AC-FBM-DEDUP-1 / B2).

    Walks ``ordered`` (already sorted best-first) and keeps a hit only when its
    content token-set is not a near-duplicate (token-Jaccard > ``threshold``) of
    any already-kept hit. The HIGHER-ranked member of a near-dup pair is kept
    (it is reached first); the freed slot is filled by the next distinct hit
    downstream because the truncation to ``top_n`` happens AFTER this collapse.

    A pinned hit is NEVER deduped away (the hard floor must survive — AC-FBM-W-2)
    and never suppresses a later hit (it is kept unconditionally and not added to
    the comparison set, so a pinned always-include rule cannot collapse a
    distinct episode).
    """
    kept: list[dict[str, object]] = []
    kept_tokens: list[frozenset[str]] = []
    for hit in ordered:
        if _is_pinned(hit):
            kept.append(hit)
            continue
        toks = _dedup_tokens(hit)
        if any(
            _is_near_duplicate(toks, prev, threshold=threshold)
            for prev in kept_tokens
        ):
            continue
        kept.append(hit)
        kept_tokens.append(toks)
    return kept


def _merge_by_score(
    corpus_hits: list[dict[str, object]],
    episode_hits: list[dict[str, object]],
    *,
    top_n: int,
    salience_threshold: float = SALIENCE_THRESHOLD,
) -> list[dict[str, object]]:
    """Merge corpus + episode hits by descending WEIGHTED-NORMALIZED score,
    with pinned rules force-included, below-salience episodes gated, capped
    at top_n.

    Slice B — the SYSTEMATIC pre-merge filter stage. Three mechanisms run in one
    named stage here, replacing the reactive per-case load patches
    (AC-FBM-FILTER-STAGE-1): (1) the SALIENCE GATE (drop ``_salience <
    salience_threshold``); (2) the ABSOLUTE EPISODE FLOOR (AC-FBM-FLOOR-1 — drop
    raw BM25 below :data:`EPISODE_MIN_RELEVANCE_SCORE`, mirroring the corpus floor,
    BEFORE min-max so a weak-but-best episode cannot be promoted to 1.0 and
    out-rank a corpus rule — FM-4 closed on the episode side); (3) NEAR-DUPLICATE
    DEDUP (AC-FBM-DEDUP-1 — collapse hits with token-Jaccard >
    :data:`DEDUP_JACCARD_THRESHOLD` over the ranked list before the top-N cut, so
    duplicates do not crowd out distinct context). All three are named tunable
    constants consumed in this one function; no per-case signature lives outside it.

    B3 (AC-FBM-SAL-1) — each hit's boosted score is multiplied by its
    structural SALIENCE, and any hit whose salience is BELOW
    ``salience_threshold`` is force-DROPPED from the surfaced set BEFORE the
    relevance cut (the episode mirror of the pinned force-INCLUDE). A junk
    episode (salience 0.0) therefore cannot surface even on a query with no
    competition — the recall side of the never-not-store / gate-surfacing-only
    invariant. Corpus hits + substantive episodes ride at full salience
    (>= the threshold) and are never gated. ``salience_threshold`` is a NAMED,
    tunable parameter (default :data:`SALIENCE_THRESHOLD`): lowering it
    re-admits previously-gated junk episodes (AC-FBM-SAL-4 re-tunable),
    proving the gate is reversible and nothing was lost.

    AC.FBMU.1 — one merged result set across both physical indexes.
    AC.FBMU.2 — when ``episode_hits`` is empty the returned list IS
    ``corpus_hits`` (same objects, same order) so the rendered output
    is byte-identical to the pre-unify KP1 output. This early-return path
    is preserved UNCHANGED (no normalization / no boost / no partition runs)
    so the no-regression / fail-open envelope is byte-exact.
    AC.FBMU.3 — the merge truncates to ``top_n`` so the combined hit
    count never exceeds the cap regardless of how many episode hits
    arrive; the byte budget is then applied by :func:`_render_injection`.
    AC-FBM-RN-1 — when episodes ARE present, each source's raw scores are
    min-max-normalized onto a common ``[0, 1]`` scale BEFORE the combined
    sort (:func:`_minmax_norm`), so a relevant episode co-surfaces against
    a live corpus regardless of the two indexes' incompatible BM25
    magnitudes.

    AC-FBM-W-1 (GRADIENT) — each hit's normalized score is BOOSTED by its
    importance weight: ``boosted = norm * (weight / BASELINE_WEIGHT)``. A hit
    at the baseline weight (every episode + any rule that declares no weight)
    boosts by ``1.0`` (no-op — the AC-FBM-W-3 no-regression guarantee); a
    higher-weighted rule out-ranks an equally-relevant lower-weighted one.
    AC-FBM-W-2 (FLOOR / SAFETY) — a ``pinned`` rule is FORCE-INCLUDED at the
    FRONT of the result regardless of its relevance, ahead of the relevance
    cut. This is the property a multiplier ALONE cannot deliver: a pinned rule
    at ~0 relevance has boosted score ~0, so a pure-weight merge would still
    drop it under a hyper-relevant episode; the force-include guarantees it
    survives. Pinned rules occupy the leading top_n slots and are never
    displaced by a non-pinned hit.

    Sort within each partition is stable on the descending BOOSTED score so
    equal hits keep their arrival order (corpus hits enumerated before episode
    hits) — the strongest corpus hit still leads a tie, and truncation stays
    deterministic (AC.FBMU.3 / AC-FBM-RN-2).
    """
    if not episode_hits:
        return corpus_hits
    # B3 (AC-FBM-SAL-1) — SALIENCE GATE. Force-drop any episode hit whose
    # structural salience is below the threshold BEFORE the merge so a junk
    # episode never occupies a slot, even with no competition. Pinned rules
    # are never gated (they ride at full salience — a corpus hit declares no
    # ``_salience`` slot, so ``_salience_of`` returns the full-salience
    # default). This gates SURFACING only; the episode is still on disk
    # verbatim (HARD INVARIANT — storage is untouched). Re-tunable: a lower
    # ``salience_threshold`` re-admits the gated episodes (AC-FBM-SAL-4).
    episode_hits = [
        h for h in episode_hits if _salience_of(h) >= salience_threshold
    ]
    # AC-FBM-FLOOR-1 (Slice B / B1) — ABSOLUTE EPISODE RELEVANCE FLOOR (with the
    # over-filter safeguard). Drop a sub-floor episode BEFORE the per-source
    # min-max normalization below — but only when another episode clears the
    # floor (the populated-index regime where raw BM25 is a real discriminator).
    # This closes FM-4 on the episode side (``_minmax_norm`` would otherwise
    # promote the EPISODE source's best hit to 1.0 no matter how weak it is,
    # letting a pure-noise weak-but-best episode out-rank a genuine corpus rule)
    # WITHOUT over-filtering a lone relevant-but-sparse episode (the floor
    # self-disables in the IDF-collapsed sparse regime — AC-FBM-RN-2 / AC.FBMU.1
    # preserved). Applied to RAW BM25 (the ``score`` slot = ``_bm25_raw``), never
    # the composed/normalized value (D-FILTER.1).
    episode_hits = _apply_episode_floor(
        episode_hits, floor=EPISODE_MIN_RELEVANCE_SCORE
    )
    if not episode_hits:
        # Every episode was gated out as junk OR sub-floor — fall back to the
        # byte-identical corpus-only path (AC-FBM-SAL-2 / AC.FBMU.2 no-regression:
        # a turn with no surviving episode renders exactly the corpus output).
        return corpus_hits
    combined = list(corpus_hits) + list(episode_hits)
    # Per-source min-max normalize so the two incompatible BM25 scales compete
    # fairly (AC-FBM-RN-1), then apply the per-hit weight boost (AC-FBM-W-1)
    # and the per-hit salience factor (AC-FBM-SAL-1). Pure arithmetic on
    # already-fetched hit lists — no new I/O, no new failure surface on the
    # every-turn live hook.
    norms = _minmax_norm(corpus_hits) + _minmax_norm(episode_hits)
    boosted = [
        norms[i]
        * (_weight_of(combined[i]) / BASELINE_WEIGHT)
        * _salience_of(combined[i])
        for i in range(len(combined))
    ]
    # Partition: pinned rules are the hard floor (AC-FBM-W-2) — force-included
    # at the front regardless of relevance; the rest sort by boosted score.
    pinned_idx = [i for i in range(len(combined)) if _is_pinned(combined[i])]
    rest_idx = [i for i in range(len(combined)) if not _is_pinned(combined[i])]
    pinned_order = sorted(pinned_idx, key=lambda i: (-boosted[i], i))
    rest_order = sorted(rest_idx, key=lambda i: (-boosted[i], i))
    order = pinned_order + rest_order
    combined = [combined[i] for i in order]
    # AC-FBM-DEDUP-1 (Slice B / B2) — NEAR-DUPLICATE COLLAPSE over the combined,
    # ranked, pre-truncate list (D-FILTER.2). A later hit whose content
    # token-Jaccard with an already-kept hit exceeds DEDUP_JACCARD_THRESHOLD is
    # dropped; the higher-ranked member of a near-dup pair is kept (it is reached
    # first in best-first order) and — because truncation to ``top_n`` happens
    # AFTER this collapse — the freed slot is filled by the next distinct hit.
    # Pinned hits are never deduped away (the hard floor survives). Pure
    # arithmetic on already-fetched hits; no new I/O.
    combined = _dedup_hits(combined, threshold=DEDUP_JACCARD_THRESHOLD)
    if top_n > 0:
        combined = combined[:top_n]
    return combined


# ---- KP0-chain contributor (STAGED live wiring import target) ------


def _resolve_live_config(envelope: dict) -> RetrievalConfig:
    """Resolve the live RetrievalConfig from a UserPromptSubmit envelope.

    Live defaults: the workspace project dir from the envelope (for the
    ``.scratch/`` index) + the user-scope memory dir + ``~/.claude``
    home for the corpus + OBJECTIVES.md. Used only by the staged live
    wiring; tests construct RetrievalConfig directly against fixtures.
    """
    ws = envelope.get("workspace") if isinstance(envelope, dict) else None
    project_dir = None
    if isinstance(ws, dict):
        project_dir = ws.get("project_dir")
    workspace_root = Path(project_dir) if project_dir else Path.cwd()
    claude_home = Path.home() / ".claude"
    # The user-scope memory dir (the feedback_*.md corpus lives under
    # the project-scoped auto-memory path; the live wiring resolves the
    # active project slug from cwd). Kept resolvable-from-home so the
    # corpus is discoverable without threading the slug through.
    memory_dir = None
    projects_root = claude_home / "projects"
    if projects_root.is_dir():
        # Prefer the memory dir whose slug matches the cwd path shape.
        slug = "-" + str(workspace_root).strip("/").replace("/", "-")
        candidate = projects_root / slug / "memory"
        if candidate.is_dir():
            memory_dir = candidate

    # AC.FBMU.1 — resolve the FBM episode store dir for the unify merge.
    # ``memory_dir_for_workspace`` appends the ``workspace`` segment
    # (the designed resolver contract), so it needs the REPO ROOT, not
    # the operator workspace ``project_dir`` (which already ends in
    # ``workspace``). Honour ``LOAM_WORKSPACE_ROOT`` (the worker's
    # canonical repo-root env, shared single source of truth), else
    # strip a trailing ``workspace`` segment off the project dir. This
    # mirrors the writer-side caller fix (AC.FBMW.1) so the contributor
    # reads episodes from exactly where the writer/worker land them.
    episode_memory_dir = None
    try:
        from ..file_memory import memory_dir_for_workspace
        from loam.workspace_bootstrap.workspace_paths import (
            WORKSPACE_STATE_SUBDIR,
        )
        import os as _os

        env_root = _os.environ.get("LOAM_WORKSPACE_ROOT")
        if env_root:
            repo_root = Path(env_root)
        elif workspace_root.name == WORKSPACE_STATE_SUBDIR:
            repo_root = workspace_root.parent
        else:
            repo_root = workspace_root
        candidate_ep = memory_dir_for_workspace(repo_root)
        if candidate_ep.exists():
            episode_memory_dir = candidate_ep
    except Exception:  # noqa: BLE001 — fail-soft; unify degrades to corpus-only
        episode_memory_dir = None

    return RetrievalConfig(
        workspace_root=workspace_root,
        memory_dir=memory_dir,
        claude_homes=(claude_home,),
        objectives_home=claude_home,
        episode_memory_dir=episode_memory_dir,
    )


def build_keep_pace_contributor(
    config: Optional[RetrievalConfig] = None,
) -> Callable[[dict], Optional[str]]:
    """Return the KP0-chain ``Contributor.fn``-compatible callable.

    Shape matches the chain contract
    (``fn(envelope: dict) -> Optional[str]``). The STAGED live wiring
    registers this on the
    ``framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py``
    ``contributors()`` list — that registration is the GATED live step
    (RF-6), NOT done in this cycle.

    When ``config`` is None the callable resolves a live config from
    the envelope per turn (the live-wiring path); when supplied the
    callable uses it (the test path). The ``last_topic`` is read from
    the envelope's ``keep_pace.last_topic`` slot when present (the
    KP7 re-assert / session-continuity threads it; absent at MVP =>
    empty, graceful per AC.KP1.2).

    Fail-soft: any error yields ``None`` (no injection) so the chain's
    fail-open-whole-chain guarantee holds (AC.KP0.4).
    """

    def contributor(envelope: dict) -> Optional[str]:
        try:
            prompt = ""
            last_topic = ""
            if isinstance(envelope, dict):
                prompt = str(envelope.get("prompt", "") or "")
                kp = envelope.get("keep_pace")
                if isinstance(kp, dict):
                    last_topic = str(kp.get("last_topic", "") or "")
            cfg = config if config is not None else _resolve_live_config(envelope)
            block = retrieve(prompt=prompt, config=cfg, last_topic=last_topic)
            return block or None
        except Exception:  # noqa: BLE001 — fail-soft; chain fail-open
            return None

    return contributor


def _resolve_composer_config(
    workspace_root: Path,
    workspace_slug: str,
) -> RetrievalConfig:
    """Resolve a RetrievalConfig for the ComposedContextPayload turn
    contributor (AC-FBM-CON-1).

    The composer surface (``session_start_emitter.build_session_composer``)
    knows the ``workspace_root`` + ``workspace_slug`` explicitly — it does
    NOT pass a UserPromptSubmit ``workspace.project_dir`` envelope. So this
    resolver threads those two values directly rather than re-deriving them
    from an envelope (the live-chain path's :func:`_resolve_live_config`).

    The episode store dir is resolved via ``memory_dir_for_workspace`` so the
    GATED path reads exactly the same live episode store the retired ungated
    ``register_file_memory_retrieval`` contributor read; the corpus + objectives
    home is the user-scope ``~/.claude``. Fail-soft on the episode-store
    resolution: an absent store leaves ``episode_memory_dir=None`` and the
    merge degrades to corpus-only (AC.FBMU.2).
    """
    claude_home = Path.home() / ".claude"
    # The feedback_*.md corpus lives under the project-scoped auto-memory
    # path; resolve it by the workspace_root path-shape slug (mirrors
    # _resolve_live_config so the corpus is discoverable without threading
    # the auto-memory slug separately).
    memory_dir: Optional[Path] = None
    projects_root = claude_home / "projects"
    if projects_root.is_dir():
        slug = "-" + str(workspace_root).strip("/").replace("/", "-")
        candidate = projects_root / slug / "memory"
        if candidate.is_dir():
            memory_dir = candidate

    episode_memory_dir: Optional[Path] = None
    try:
        from ..file_memory import memory_dir_for_workspace

        candidate_ep = memory_dir_for_workspace(workspace_root)
        if candidate_ep.exists():
            episode_memory_dir = candidate_ep
    except Exception:  # noqa: BLE001 — fail-soft; unify degrades to corpus-only
        episode_memory_dir = None

    return RetrievalConfig(
        workspace_root=workspace_root,
        memory_dir=memory_dir,
        claude_homes=(claude_home,),
        objectives_home=claude_home,
        episode_memory_dir=episode_memory_dir,
        episode_group_ids=(workspace_slug,) if workspace_slug else None,
    )


def register_keep_pace_turn_contributor(
    composer: object,
    *,
    workspace_root: Path,
    workspace_slug: str,
    name: str = "memory-retrieval",
) -> Callable[[dict], str]:
    """Register the GATED keep-pace retrieval contributor on a
    ``ComposedContextPayload`` at ``TriggerKind.turn`` (AC-FBM-CON-1).

    This is the CONSOLIDATION entry-point: it replaces the live
    registration of the ungated ``file_memory.register_file_memory_retrieval``
    contributor inside ``build_session_composer``'s production (client-None)
    branch. The contributor it registers runs the GATED :func:`retrieve`
    entry-point — rank-normalize + rule-weight/hard-floor + salience gate —
    so the live ``user-prompt-submit`` hook surfaces corpus/rules AND episodes
    junk-gated, instead of the raw ungated episode dump.

    The contributor name defaults to ``memory-retrieval`` (the same name the
    retired ungated contributor used) so no downstream consumer keying on the
    block name changes.

    The contributor callable returns a ``str`` ALWAYS (never ``None``):
    :func:`retrieve` already returns ``""`` on no-match, and the wrapper coerces
    any falsy result to ``""`` so ``context_composer._serialise_turn``'s
    ``text.strip()`` is safe (AC-FBM-CON-2). Fail-closed: any boundary error
    yields ``""`` (matches the retired contributor's AC.MFBM.2 fail-closed +
    AC46.2 graceful-empty contract).
    """
    from ..context_composer import TriggerKind  # noqa: WPS433

    cfg = _resolve_composer_config(workspace_root, workspace_slug)

    def contributor(context: dict) -> str:
        try:
            prompt = ""
            if isinstance(context, dict):
                prompt = str(context.get("prompt", "") or "")
            if not prompt.strip():
                return ""
            block = retrieve(prompt=prompt, config=cfg) or ""
            # AC.DLG.2 (memory recall cycle, Slice 3) — the pending
            # ruling-gap steer flagged at the previous turn-close is
            # delivered model-facing on THIS turn (steer-not-block;
            # consume-on-read). Fail-open: a steer that cannot be read
            # is dropped, never blocks the turn.
            try:
                if cfg.episode_memory_dir is not None:
                    from ..decision_ledger import (  # noqa: WPS433
                        consume_pending_steer,
                    )

                    steer = consume_pending_steer(cfg.episode_memory_dir)
                    if steer:
                        block = steer + ("\n\n" + block if block else "")
            except Exception:  # noqa: BLE001 — steer is fail-open
                pass
            return block
        except Exception:  # noqa: BLE001 — fail-closed; turn proceeds
            return ""

    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=contributor)
    return contributor
