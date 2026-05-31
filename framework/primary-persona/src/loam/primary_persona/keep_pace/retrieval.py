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

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import objectives as _objectives
from .corpus_index import (
    CorpusIndex,
    default_index_path,
    discover_corpus,
)
from .work_anchor import WorkAnchor, is_trivial_prompt


# AC.KP1.3 — top-N injection cap. The design recipe is N <= 5.
DEFAULT_TOP_N = 5

# Soft cap on the injected block so a long corpus title set cannot
# bloat the turn payload. The pointers are short plain-language titles;
# this is a generous ceiling.
INJECTION_CHAR_CAP = 1200

# AC.FBMU.1 — neutral merge score for an episode hit that arrived via
# the store's grep-fallback path (no BM25 score). Placed at the corpus
# relevance floor so a scored corpus hit outranks an unscored episode
# but the episode still merges into the result set rather than dropping.
MERGE_NEUTRAL_SCORE = 0.1

# AC.FBMU.1 — cap the episode pointer summary so a long turn body cannot
# bloat a single pointer line; the block byte budget (INJECTION_CHAR_CAP)
# is the outer ceiling, this keeps any one episode pointer glanceable.
_EPISODE_POINTER_CAP = 160


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
    """Render the top-N corpus hits as plain-language additionalContext.

    AC.KP1.3: a ``[keep-pace]`` block listing the on-file topics the
    live work points at — plain English, NO file paths / ``.md`` names
    (authored plain-by-construction so it passes KP9's Cycle-3 lint).
    Silent on no hits (AC.KP1.4) — returns ``""``.
    """
    if not hits:
        return ""
    lines = ["[keep-pace] On-file context relevant to what you're working on:"]
    for h in hits:
        pointer = str(h.get("pointer", "")).strip()
        if pointer:
            lines.append(f"  - {pointer}")
    block = "\n".join(lines)
    if len(block) > cap:
        block = block[:cap].rstrip()
    return block if len(lines) > 1 else ""


def _episode_hits(
    *, query_tokens: list[str], config: RetrievalConfig, num_results: int
) -> list[dict[str, object]]:
    """Query the FBM episode store + shape hits like corpus hits (AC.FBMU.1).

    Returns ``[{pointer, score}]`` shaped to merge with the corpus
    hits' ``{path, title, pointer, score}`` shape under
    :func:`_render_injection` (which reads ``pointer`` + ``score``).
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
        hits.append({"pointer": pointer, "score": score_val, "_episode": True})
    return hits


def _episode_pointer(ep: dict[str, object]) -> str:
    """Plain-language pointer for an episode hit (AC.FBMU.1).

    Plain English, NO file path / no ``.md`` name (mirrors
    :func:`corpus_index._doc_pointer` so the merged surface passes the
    same KP9 plain-language lint). Surfaces the episode's CONTENT
    summary (the first sentence of the turn body — the on-file topic
    the prior turn carried), NOT the opaque ``turn/<id>`` name (an
    internal id is never a user-facing pointer). Falls back to a
    cleaned name only when the body is empty.
    """
    content = str(ep.get("content", "") or "").strip()
    summary = ""
    if content:
        # First sentence / first line — the meaningful topical pointer.
        first = content.replace("\n", " ").strip()
        for sep in (". ", "! ", "? "):
            idx = first.find(sep)
            if 0 < idx < len(first):
                first = first[: idx + 1]
                break
        summary = first[:_EPISODE_POINTER_CAP].rstrip()
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


def retrieve(
    *,
    prompt: str,
    config: RetrievalConfig,
    last_topic: str = "",
) -> str:
    """The PRODUCTION work-anchored retrieval entry-point (AC.KP1.6).

    Invoked with no pre-arranged retrieval state — it reads the
    objectives fresh, builds the work-anchored key, syncs + searches
    the corpus, and returns the plain-language injection (or ``""``).

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
    """
    if is_trivial_prompt(prompt):
        return ""

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
        return ""

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
    merged = _merge_by_score(corpus_hits, episode_hits, top_n=config.top_n)
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


def _merge_by_score(
    corpus_hits: list[dict[str, object]],
    episode_hits: list[dict[str, object]],
    *,
    top_n: int,
) -> list[dict[str, object]]:
    """Merge corpus + episode hits by descending NORMALIZED score, capped
    at top_n.

    AC.FBMU.1 — one merged result set across both physical indexes.
    AC.FBMU.2 — when ``episode_hits`` is empty the returned list IS
    ``corpus_hits`` (same objects, same order) so the rendered output
    is byte-identical to the pre-unify KP1 output. This early-return path
    is preserved UNCHANGED (no normalization runs) so the no-regression /
    fail-open envelope is byte-exact.
    AC.FBMU.3 — the merge truncates to ``top_n`` so the combined hit
    count never exceeds the cap regardless of how many episode hits
    arrive; the byte budget is then applied by :func:`_render_injection`.
    AC-FBM-RN-1 — when episodes ARE present, each source's raw scores are
    min-max-normalized onto a common ``[0, 1]`` scale BEFORE the combined
    sort (:func:`_minmax_norm`), so a relevant episode co-surfaces against
    a live corpus regardless of the two indexes' incompatible BM25
    magnitudes. The raw-score merge buried/truncated episodes (the
    AC-FBM-LIVE-2 gap); the normalized merge lets the best per-source hit
    compete fairly.

    Sort is stable on the descending NORMALIZED score so equal-normalized
    hits keep their arrival order (corpus hits enumerated before episode
    hits) — the strongest corpus hit still leads a ``1.0``/``1.0`` tie, and
    truncation stays deterministic (AC.FBMU.3 / AC-FBM-RN-2).
    """
    if not episode_hits:
        return corpus_hits
    combined = list(corpus_hits) + list(episode_hits)
    # Normalize per source so the two incompatible BM25 scales compete
    # fairly (AC-FBM-RN-1). Pure arithmetic on already-fetched hit lists —
    # no new I/O, no new failure surface on the every-turn live hook.
    norms = _minmax_norm(corpus_hits) + _minmax_norm(episode_hits)
    order = sorted(
        range(len(combined)), key=lambda i: (-norms[i], i)
    )
    combined = [combined[i] for i in order]
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
