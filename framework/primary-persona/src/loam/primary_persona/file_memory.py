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
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from . import access_log as _access_log


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
# AC-FBM-WGATE-1/-3 — the write-time salience COLD tier. A turn the ingest
# gate classifies as SALIENCE_JUNK is written here instead of EPISODES_SUBDIR
# and is NOT FTS-indexed, so it never enters the hot retrieval index. It is a
# sibling of ARCHIVED_SUBDIR (NOT a reuse — ``archived/`` carries age-based
# semantics consumed by ``archive_before`` / ``/memory:archive``; the salience
# cold tier is junk-classification-based and must not be conflated). The hot
# retrieval paths (``search`` / ``recent_episodes``) scan EPISODES_SUBDIR only,
# so this subdir is excluded from surfacing by construction. The episode body
# is written here verbatim — never-drop HARD INVARIANT (the turn is on disk,
# just out of the hot index; recoverable by direct read).
COLD_SUBDIR = "cold"
ERRORS_LOG_NAME = ".errors"
SEARCH_INDEX_NAME = "search-index.sqlite"


# ---- episode SALIENCE gate (B3 — AC-FBM-SAL family) -----------------
#
# Junk turns (agent task-notification turns, empty/near-empty channel
# header events, bare acks) get logged as episodes and rank HIGH on
# shared boilerplate tokens, polluting recall. The salience gate tags
# each turn at INGEST with a structural salience score; the retrieval
# merge force-DROPS below-threshold episodes from the SURFACED set.
#
# HARD INVARIANT (load-bearing): salience gates SURFACING only. Every
# turn is still STORED on disk verbatim; nothing is not-stored or
# deleted. A mis-judged junk turn stays on disk and is re-admittable by
# lowering the retrieval threshold (the gate is re-tunable, nothing
# lost). Every default / error path resolves to SALIENCE_FULL so the
# gate can only suppress a turn it AFFIRMATIVELY recognized as junk.

# AC-FBM-SAL-1/-2 — the two salience poles. A turn whose USER half is
# pure scaffolding is tagged SALIENCE_JUNK; everything else (and every
# error / default) is SALIENCE_FULL — fail toward surfacing.
SALIENCE_FULL = 1.0
SALIENCE_JUNK = 0.0

# A user half (residual inner text, after scaffolding wrappers are
# stripped) shorter than this is treated as content-free (empty-user /
# channel-empty junk classes). 8 chars is below any real instruction but
# above a wrapper remnant; calibrated against the live store (the
# channel-empty class had 1-7-char residuals like "Go", "Accept").
_SALIENCE_MIN_CHARS = 8

# AC-FBM-SAL-1 — bare-ack tokens. A user half whose residual inner text
# (lowercased, surrounding punctuation/whitespace stripped) is exactly
# one of these is plumbing, not a memory.
_ACK_TOKENS: frozenset[str] = frozenset(
    {
        "ok", "okay", "k", "yes", "no", "yep", "yeah", "ty",
        "thanks", "thank you", "got it", "nice", "cool", "great",
        "perfect", "sounds good", "done",
    }
)

# Scaffolding wrapper tags whose OUTER markup is plumbing but whose
# INNER text may be real (a <channel>-wrapped Luke message is fully
# salient — the load-bearing protect-real-messages property). The
# residual is what's left after these open/close tags are removed.
_SCAFFOLD_WRAPPER_RE = re.compile(
    r"</?(?:channel|system-reminder)[^>]*>", re.IGNORECASE
)

# AC-FBM-SAL-7 — compaction-summary context-dump signature. A
# compaction-summary turn is the auto-generated context-restoration block the
# CLI logs as a turn; its user half OPENS with this continuation marker,
# followed by a multi-thousand-word summary naming every active objective. It
# matches none of the four prior junk shapes, so it rode at full salience and
# BM25-dominated almost every work-anchored query (it is long + contains every
# objective keyword) — the single worst recall polluter on the live store (19
# such episodes; diagnosis: loam-fbm-relevance-assessment §1.3). The signature
# keys on the dump's STRUCTURAL OPENING — the marker leading the residual user
# half — never on incidental token overlap, so a genuine Luke turn that merely
# mentions a continuation in prose is NOT mis-classified (AC-FBM-SAL-8,
# protect-real-messages, sibling of AC-FBM-SAL-5).
_COMPACTION_SUMMARY_MARKER = (
    "this session is being continued from a previous conversation"
)


def _salience_user_residual(user_text: str) -> str:
    """Strip scaffolding wrapper tags from a user half, keep inner text.

    A ``<channel …>`` / ``<system-reminder>`` wrapper is plumbing; the
    text INSIDE it may be a real Luke message. Returns the residual so
    the junk signatures key on actual content, never on the mere
    presence of a wrapper tag (AC-FBM-SAL-5 protect-real-messages).
    """
    return _SCAFFOLD_WRAPPER_RE.sub("", user_text).strip()


def compute_salience(user_text: str, assistant_text: str = "") -> float:
    """Structural salience score for a turn (B3, AC-FBM-SAL-1/-2).

    Cheap, deterministic, stdlib-only. Returns :data:`SALIENCE_JUNK`
    (0.0) when the turn's USER half matches a structural junk signature,
    else :data:`SALIENCE_FULL` (1.0). The five junk signatures (verified
    against the live episode store):

    1. **task-notification** — the user half (lstripped) starts with
       ``<task-notification>`` (an agent-completion notification that
       got logged as a turn; pollutes recall on ``task-id`` /
       ``tool-use-id`` / ``status`` boilerplate tokens).
    2. **channel/scaffolding-empty** — after stripping ``<channel …>`` /
       ``<system-reminder>`` wrappers, the residual inner text is
       shorter than :data:`_SALIENCE_MIN_CHARS` (an empty channel
       event).
    3. **empty-user** — the whole user half is shorter than
       :data:`_SALIENCE_MIN_CHARS` and not real content.
    4. **bare-ack** — the residual inner text (lowercased,
       punctuation-stripped) is a pure ack token (:data:`_ACK_TOKENS`).
    5. **compaction-summary dump** — the residual user half OPENS with the
       compaction-summary continuation marker
       (:data:`_COMPACTION_SUMMARY_MARKER`) — the auto-generated
       context-restoration block logged as a turn; keyed on the structural
       opening so a real turn that merely mentions a continuation is not
       mis-classified (AC-FBM-SAL-7/-8).

    The scorer keys on the USER half only: a substantive ASSISTANT half
    does NOT rescue a turn whose user half is pure plumbing, because the
    recall-polluting boilerplate tokens live in the user half. A
    ``<channel>``-wrapped Luke message with real text inside is fully
    salient (the residual is the real text) — the load-bearing
    protect-real-messages property.

    Fail-safe (the hot ingest path): ANY exception returns
    :data:`SALIENCE_FULL` — a scorer error fails toward
    storing-at-full-salience + surfacing, never toward dropping (the
    never-drop floor / HARD INVARIANT).
    """
    try:
        u = (user_text or "").strip()
        # (1) task-notification turn.
        if u.lstrip().startswith("<task-notification>"):
            return SALIENCE_JUNK
        residual = _salience_user_residual(u)
        # (2) channel/scaffolding-empty: a wrapper with no real content.
        if u.lstrip().startswith(("<channel", "<system-reminder")):
            if len(residual) < _SALIENCE_MIN_CHARS:
                return SALIENCE_JUNK
        # (3) empty-user: the whole user half is content-free.
        if len(u) < _SALIENCE_MIN_CHARS:
            return SALIENCE_JUNK
        # (4) bare-ack: residual inner text is a pure ack token.
        ack_key = residual.lower().strip(" .!?,;:\n\t")
        if ack_key in _ACK_TOKENS:
            return SALIENCE_JUNK
        # (5) compaction-summary context-dump (AC-FBM-SAL-7): the residual
        # user half OPENS with the continuation marker. Keying on the
        # structural opening (not mere token presence) protects a real Luke
        # turn that only mentions a continuation in prose (AC-FBM-SAL-8).
        if residual.lower().lstrip(" \t\n#*->").startswith(
            _COMPACTION_SUMMARY_MARKER
        ):
            return SALIENCE_JUNK
        return SALIENCE_FULL
    except Exception:  # noqa: BLE001 — never-drop floor on the hot path
        return SALIENCE_FULL


def _salience_from_body(body: str) -> float:
    """Compute salience from a written episode body (B3, AC-FBM-SAL-1).

    The worker authors the body as ``[user]\\n<msg>\\n\\n[assistant]\\n
    <reply>\\n`` (see ``memory_write_worker._build_episode_args``). This
    splits on those markers and scores the user half. Fail-safe:
    unparseable body → :data:`SALIENCE_FULL`.
    """
    try:
        text = body or ""
        u = ""
        a = ""
        mu = re.search(r"\[user\]\n(.*?)(?:\n\[assistant\]|\Z)", text, re.S)
        ma = re.search(r"\[assistant\]\n(.*)\Z", text, re.S)
        if mu:
            u = mu.group(1).strip()
        if ma:
            a = ma.group(1).strip()
        if not mu and not ma:
            # No [user]/[assistant] markers — treat the whole body as
            # the user half (a non-persona writer's plain body).
            u = text.strip()
        return compute_salience(u, a)
    except Exception:  # noqa: BLE001 — never-drop floor
        return SALIENCE_FULL


# --- AC.VOL.1 — write-side volatility classifier -----------------------
#
# A captured fact is classified into one of three volatility classes so
# the read side can dispose of it without ever serving a stale
# operational-status claim as current (Lens-0 protection: no
# confidently-wrong recall). Deterministic, stdlib-only (``re``), keyed
# on the tells the feedback memory names:
#
#   * VOLATILITY_HARD  — an unambiguous operational-status claim
#     (is-broken / up-down / current-version / latest-SHA /
#     pending-count / who's-allowed). Born with a CLOSED interval
#     (``volatile_until``) so the default current view FILTERS it out
#     (hard-exclude, D1). The durable DECISION behind it is a SEPARATE
#     record and is never touched (D2).
#   * VOLATILITY_SOFT  — a borderline freshness claim (``right now`` /
#     ``as of today`` / ``at the moment`` with no hard tell), OR a hard
#     tell that co-occurs with a durable-decision signal (the D2 safe
#     bias — ambiguity never hard-excludes). Born OPEN; surfaced with a
#     re-verify annotation (D1).
#   * VOLATILITY_DURABLE — everything else (the default). Born OPEN; no
#     annotation. Fail-safe: any classifier error returns DURABLE so a
#     misfire only ever leaves a record visible (never silently drops or
#     excludes one — the protection floor's safe direction).
VOLATILITY_DURABLE = "durable"
VOLATILITY_HARD = "volatile-hard"
VOLATILITY_SOFT = "volatile-soft"

#: How long after ``reference_time`` a HARD-volatile record's validity
#: interval stays open. Short enough that ANY cross-session recall (a
#: separate read, after the writing instant) falls outside it and is
#: filtered by the default current view; long enough that an ``as_of``
#: query at the writing instant still reaches the record (filtering ≠
#: deletion — AC.SUP.2 preserved for the volatility close).
VOLATILE_WINDOW = timedelta(minutes=5)

#: Read-side annotation prefix for a SOFT-volatile surfaced pointer
#: (AC.VOL.4 / D1). The substance is exposed; only the re-verify
#: caution is added.
VOLATILE_SOFT_ANNOTATION = "[VOLATILE — re-verify before serving]"

# A durable-decision signal. Its presence VETOES a hard classification
# down to SOFT (D2): a ruling phrased with an operational tell stays
# visible-but-annotated, never hard-excluded.
_DURABLE_SIGNAL_RE = re.compile(
    r"\b(?:"
    r"decided|decision|rul(?:ed|ing)|agreed|"
    r"we\s+will|we\s+chose|going\s+forward|"
    r"the\s+(?:rule|policy|standard|convention)\s+is|"
    r"by\s+convention|from\s+now\s+on|henceforth"
    r")\b",
    re.IGNORECASE,
)

# The unambiguous HARD operational-status tells (D1). Each maps to one
# of the named classes; any match (absent a durable veto) is hard.
_HARD_VOLATILE_RES: tuple[re.Pattern[str], ...] = (
    # is-broken / up-down — present-state service/host status.
    re.compile(
        r"\b(?:is|are|was|were|currently|now)\s+"
        r"(?:broken|down|failing|offline|unavailable|unreachable|"
        r"not\s+working|working\s+again|back\s+(?:up|online)|"
        r"up\s+again|restored|fixed\s+now)\b",
        re.IGNORECASE,
    ),
    # current-version.
    re.compile(
        r"\b(?:current\s+version|version\s+is|running\s+v(?:ersion)?\s*\d|"
        r"now\s+on\s+v?\d|latest\s+version\s+is)\b",
        re.IGNORECASE,
    ),
    # latest-SHA — a commit/HEAD claim with a hex sha.
    re.compile(
        r"\b(?:latest|current|head)\b[^\n]*\b[0-9a-f]{7,40}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bHEAD\s+(?:is|at)\b", re.IGNORECASE),
    # pending-count — N <units> pending/open/remaining.
    re.compile(
        r"\b\d+\s+(?:tasks?|items?|prs?|pull\s+requests?|tickets?|jobs?)\s+"
        r"(?:pending|in\s+flight|open|remaining|queued|left)\b",
        re.IGNORECASE,
    ),
    # who's-allowed — current access state.
    re.compile(
        r"\b(?:is|are)\s+(?:allowed|approved|paired|whitelisted|blocked|"
        r"banned|on\s+the\s+allowlist)\b",
        re.IGNORECASE,
    ),
)

# Borderline freshness tells → SOFT (annotate, don't exclude). Present
# tense "as of now" language with no hard operational claim.
_SOFT_VOLATILE_RE = re.compile(
    r"\b(?:right\s+now|as\s+of\s+(?:today|now|this\s+(?:session|morning))|"
    r"at\s+the\s+moment|at\s+present|as\s+things\s+stand)\b",
    re.IGNORECASE,
)


def classify_volatility(text: str) -> str:
    """Classify ``text`` as DURABLE / HARD / SOFT volatile (AC.VOL.1).

    Deterministic + stdlib-only. The D2 safe bias: a hard tell that
    co-occurs with a durable-decision signal de-escalates to SOFT (a
    ruling is never hard-excluded). Any error → DURABLE (the never-drop
    protection floor — a misfire leaves the record visible).
    """
    try:
        t = text or ""
        hard = any(rx.search(t) for rx in _HARD_VOLATILE_RES)
        durable_signal = bool(_DURABLE_SIGNAL_RE.search(t))
        if hard and not durable_signal:
            return VOLATILITY_HARD
        if hard and durable_signal:
            # D2 — ambiguous: a ruling phrased operationally. Keep it
            # visible, annotated, never excluded.
            return VOLATILITY_SOFT
        if _SOFT_VOLATILE_RE.search(t):
            return VOLATILITY_SOFT
        return VOLATILITY_DURABLE
    except Exception:  # noqa: BLE001 — protection floor: never drop
        return VOLATILITY_DURABLE


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
# AC.SRF.3 (memory recall cycle, Slice 2): raised in lockstep with the
# consumer-side budget to the ~5KB-class whole-record budget.
MEMORY_RETRIEVAL_CHAR_CAP = 5000

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

# AC.EVX.2 (memory recall cycle, Slice 1) — the NAMED switch that
# re-enables the power-law activation multiplier with no code change.
# DEFAULT-OFF: the June-7 eval measured activation net-harmful on the
# current store (the BM25 floor arm beat the live ranker ~2×), so
# production ranks BM25 × supersession until a live-access-log re-run
# of the harness beats the floor (plan §7 re-enable gate). See
# :func:`activation_enabled`.
ACTIVATION_FLAG_ENV = "LOAM_FBM_ACTIVATION"


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
        # B3 (AC-FBM-SAL-1/-2): tag the turn with a structural salience score
        # AT INGEST, computed from the body. AC-FBM-WGATE-1/-2: the salience
        # value now ALSO selects the write tier. A SALIENCE_JUNK turn is
        # diverted to COLD_SUBDIR (never indexed → never enters the hot
        # retrieval index); a SALIENCE_FULL turn writes to EPISODES_SUBDIR +
        # FTS-indexes exactly as before (byte-identical for non-junk). The
        # ``salience`` frontmatter scalar is still emitted on both tiers so the
        # read-side gate (defence in depth for pre-amendment hot-tier episodes)
        # stays correct. Fail-open: _salience_from_body returns SALIENCE_FULL on
        # any error, so a classifier error routes the turn to the HOT tier — the
        # write gate only diverts a turn it affirmatively recognized as junk.
        salience = _salience_from_body(body)
        is_cold = salience <= SALIENCE_JUNK
        write_subdir = COLD_SUBDIR if is_cold else EPISODES_SUBDIR
        target_dir = self.memory_dir / write_subdir / group_id / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{stem}.md"
        tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        # AC.FBMT1.ENCC.1 + AC.FBMT1.ENCC.2: emit the four-field
        # context block (always present, values vary). Per the
        # schema-minimal directive the block carries exactly the
        # four fields named in :data:`ENCODING_CONTEXT_FIELDS` —
        # adding a fifth field is a structural-test failure.
        context_block = _render_context_block(context)
        # AC.VOL.1 / AC.VOL.2 — classify the turn's volatility AT INGEST
        # and, for the HARD class, close its validity interval at birth
        # (``volatile_until = reference_time + VOLATILE_WINDOW``) so the
        # default current view filters it from any later-session recall
        # (D1 hard-exclude) while an ``as_of`` query at the writing
        # instant still reaches it (D3, AC.SUP.2 preserved). DURABLE and
        # SOFT are born OPEN (no close). The ``volatility`` class field is
        # emitted on every tier for transparency; only HARD adds the
        # ``volatile_until`` close. Fail-safe: ``classify_volatility``
        # returns DURABLE on any error, so a misfire never closes an
        # interval it did not affirmatively recognize as hard-volatile.
        volatility = classify_volatility(body)
        volatile_block = f"volatility: {volatility}\n"
        if volatility == VOLATILITY_HARD:
            volatile_until = (ref_utc + VOLATILE_WINDOW).isoformat()
            volatile_block += f"volatile_until: {volatile_until}\n"
        front = (
            "---\n"
            f"name: {name}\n"
            f"source: {source}\n"
            f"source_description: {source_description}\n"
            f"reference_time: {ref_utc.isoformat()}\n"
            f"group_id: {group_id}\n"
            f"salience: {salience}\n"
            f"{volatile_block}"
            f"{context_block}"
            "---\n"
        )
        # Single write, then atomic rename. Any IOError surfaces to
        # the caller — the Stop-hook's caller already absorbs every
        # boundary error to ``memory-writes.log`` (AC.M.10), and the
        # contributor-side caller fail-closes (AC.MFBM.2 / AC-D7.7).
        tmp_path.write_text(front + body, encoding="utf-8")
        tmp_path.replace(target_path)
        # AC-FBM-WGATE-1: a cold-tier (junk) turn is NOT FTS-indexed — that is
        # what keeps it out of the hot retrieval index. AC-FBM-WGATE-2: a
        # hot-tier (substantive) turn is indexed exactly as before. Best-effort
        # FTS5 index update; failure is non-fatal — next search rebuilds the
        # index from scratch via grep fallback (which also scans EPISODES_SUBDIR
        # only, so the cold tier stays excluded even on a rebuild).
        if not is_cold:
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
        as_of: datetime | None = None,
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

        AC.SUP.1 / AC.SUP.2 — supersession validity-interval filtering:
          * ``as_of is None`` (DEFAULT current view): superseded
            (closed-interval) records are FILTERED OUT — the current
            fact wins, the stale one never surfaces. This is the
            default the persona reads, so a corrected fact no longer
            has to be re-stated.
          * ``as_of`` (an aware datetime): the HISTORY view — returns
            records whose validity interval CONTAINS ``as_of``
            (``valid_from <= as_of < valid_to``), so a record stale
            now-but-current-as-of-τ is reachable. Proves filtering ≠
            deletion.
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
                as_of=as_of,
            )
        except (sqlite3.Error, OSError):
            episodes = []
        if not episodes:
            episodes = self._grep_search(
                query=query,
                group_ids=group_ids,
                num_results=num_results,
                as_of=as_of,
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
        as_of: datetime | None = None,
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
                    # B3 (AC-FBM-SAL-1) — structural salience for the
                    # retrieval gate. Computed from the body so it is
                    # correct for episodes written before the salience
                    # field existed (those have no stored field but the
                    # body is in the index). Old episodes thus get the
                    # right gate without any rewrite (never-touch-stored
                    # / HARD INVARIANT). A turn whose user half is pure
                    # scaffolding scores SALIENCE_JUNK; everything else
                    # SALIENCE_FULL (the never-drop default).
                    "_salience": _salience_from_body(body),
                    # AC.FBMT2.PLBLA.2 — preserve the BM25 score so the
                    # downstream activation composition can compute
                    # ``final = BM25 × activation × supersession``. SQLite's
                    # ``bm25()`` returns a negative score (lower = better);
                    # we negate so larger = stronger relevance, matching
                    # the ranker semantics of the rest of the pipeline.
                    "_bm25_raw": -float(score) if score is not None else 0.0,
                }
            )
        # AC.EVX.1 — compose BM25 with the supersession penalty (the
        # June-7 floor arm); activation participates only behind the
        # default-off AC.EVX.2 switch. ``now`` is injected so the
        # flag-on activation fixture stays deterministic. ``memory_root``
        # is threaded through so AC.FBMT1.SUPM.4's missing-target
        # warning has a base path against which to resolve the
        # ``superseded-by`` relative path.
        return _compose_score(
            pool,
            num_results=num_results,
            now=datetime.now(timezone.utc),
            memory_root=self.memory_dir,
            as_of=as_of,
        )

    def _grep_search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
        as_of: datetime | None = None,
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

        # AC.EVX.1 — route the grep-fallback pool through the same
        # composition pipeline as the FTS5 path so the supersession
        # penalty (and the flag-gated activation, AC.EVX.2) apply
        # uniformly regardless of which retrieval surface fires. The
        # grep path's ``raw_score / doclen`` is the BM25-equivalent
        # relevance channel in this fallback.
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
                    # B3 (AC-FBM-SAL-1) — structural salience for the
                    # retrieval gate, computed from the body (correct
                    # for pre-salience episodes too; no rewrite).
                    "_salience": _salience_from_body(body),
                    "_bm25_raw": float(score),
                }
            )
        return _compose_score(
            pool,
            num_results=num_results,
            now=datetime.now(timezone.utc),
            memory_root=self.memory_dir,
            as_of=as_of,
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


#: The supersession marker frontmatter keys (the convention authored by
#: :func:`supersession.mark_superseded`; the same keys the existing
#: ``_superseded_marker`` honor reads). Defined module-locally so the
#: validity-interval reader composes on the marker without importing
#: ``supersession`` (which would create an import cycle).
_SUPERSEDED_BY_KEY = "superseded-by"
_SUPERSEDED_DATE_KEY = "superseded-date"

#: The volatility close key (AC.VOL.2 / AC.VOL.3). Written at ingest by
#: :meth:`FileMemoryStore.write_episode` for a HARD-volatile turn; read
#: here as an ADDITIVE interval close alongside the supersession marker.
_VOLATILE_UNTIL_KEY = "volatile_until"


# --- AC.SUP.1 / AC.SUP.2 / AC.SUP.3 — validity-interval supersession ---
#
# The supersession marker (``superseded-by`` + ``superseded-date``,
# written by :func:`supersession.mark_superseded`) is PROMOTED here into
# a real bitemporal validity interval. A record's interval is
# ``[valid_from, valid_to)``:
#
#   * ``valid_from`` = the episode's ``reference_time`` (its creation /
#     ingest instant; the same field the recency channel reads).
#   * ``valid_to``   = the marker's ``superseded-date`` (the instant the
#     successor closed this record's interval AT CREATION — AC.SUP.3),
#     or ``None`` for an OPEN interval (not superseded — the default).
#
# The DEFAULT current view FILTERS closed-interval records out
# (AC.SUP.1: current-over-stale, the marked record is removed not merely
# demoted — this is the gap the old ``SUPERSEDED_PENALTY`` left open).
# An explicit ``as_of τ`` query returns a record whose interval CONTAINS
# τ (``valid_from <= τ < valid_to``), so history stays reachable
# (AC.SUP.2: filtering ≠ deletion). With no marker the interval is open
# and the record is always current (AC.SUP.5: retrieval keys ONLY on
# interval state, so un-marking restores prior behaviour exactly).


def _supersession_interval(
    path_str: str,
) -> tuple[datetime | None, datetime | None]:
    """Read the record at ``path_str`` and return its validity interval
    ``(valid_from, valid_to)`` (AC.SUP.1 / AC.SUP.3).

    ``valid_from`` is the record's ``reference_time``; ``valid_to`` is
    the ``superseded-date`` marker (close instant) or ``None`` (open —
    not superseded). Composes on the EXISTING marker convention rather
    than a new on-disk schema: ``superseded-date`` IS the close
    timestamp. Fail-soft — an unreadable file / absent fields returns
    ``(None, None)`` (an open interval; the record is treated as current
    rather than the call raising, mirroring :func:`_superseded_marker`).
    """
    if not path_str:
        return (None, None)
    try:
        content = Path(path_str).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return (None, None)
    front, _ = _split_frontmatter(content)
    valid_from = _parse_reference_time(str(front.get("reference_time", "")))
    valid_to: datetime | None = None
    marker = front.get(_SUPERSEDED_BY_KEY)
    if isinstance(marker, str) and marker:
        valid_to = _parse_reference_time(
            str(front.get(_SUPERSEDED_DATE_KEY, ""))
        )
        # A marked record with an unparseable / absent close date still
        # carries a closed interval (it IS superseded). Use a far-future
        # sentinel close so the default view filters it (close known to
        # exist) while an ``as_of`` query can still reach it before the
        # sentinel. The marker's PRESENCE is the close signal; the date
        # only refines WHERE the close falls (AC.SUP.1 keys on
        # superseded-ness, not on a parseable date).
        if valid_to is None:
            valid_to = _SUPERSEDED_SENTINEL_CLOSE
    # AC.VOL.3 / D3 — a HARD-volatile record closes its interval via the
    # ``volatile_until`` frontmatter key (written at ingest by
    # ``write_episode``). This is an ADDITIVE close source on the same
    # interval machinery — no new on-disk schema, no change to
    # ``_interval_current`` / ``_filter_by_interval`` (closed is closed;
    # the default view filters it, an ``as_of``-in-window query reaches
    # it). PRECEDENCE: an explicit supersession marker is the writer-
    # recorded invalidation instant and GOVERNS the interval — the
    # volatility heuristic only supplies a close when NO supersession
    # close exists (the unmarked-record gap the volatility classifier
    # exists to cover). This keeps supersession-marked records byte-
    # identical to pre-VOL behaviour (AC.SUP.2 as_of window unchanged),
    # while a marked record is already filtered from the current view
    # regardless, so hard-exclude still holds either way.
    if valid_to is None:
        volatile_until = _parse_reference_time(
            str(front.get(_VOLATILE_UNTIL_KEY, ""))
        )
        if volatile_until is not None:
            valid_to = volatile_until
    return (valid_from, valid_to)


def _interval_current(
    interval: tuple[datetime | None, datetime | None],
) -> bool:
    """Whether ``interval`` is OPEN (current) — i.e. not superseded
    (AC.SUP.1). An open interval (``valid_to is None``) is current; a
    closed interval is filtered from the default view."""
    return interval[1] is None


def _interval_contains(
    interval: tuple[datetime | None, datetime | None], as_of: datetime
) -> bool:
    """Whether ``interval`` contains the instant ``as_of`` —
    ``valid_from <= as_of < valid_to`` (AC.SUP.2, the ``as_of`` history
    path). An open interval (``valid_to is None``) contains every
    instant at/after ``valid_from``. A missing ``valid_from`` is treated
    as unbounded-below (the record existed before any recorded start)."""
    valid_from, valid_to = interval
    if valid_from is not None and as_of < valid_from:
        return False
    if valid_to is not None and as_of >= valid_to:
        return False
    return True


def _filter_by_interval(
    rows: list[dict[str, Any]], *, as_of: datetime | None
) -> list[dict[str, Any]]:
    """Apply the supersession validity-interval FILTER (AC.SUP.1 /
    AC.SUP.2) — the default-current-view filter, or the ``as_of``
    history view when ``as_of`` is supplied.

    * ``as_of is None`` (default current view): keep only OPEN-interval
      (not-superseded) records — the closed/stale records are FILTERED
      OUT, not merely demoted. This is the architectural change.
    * ``as_of is not None`` (history query): keep records whose interval
      CONTAINS ``as_of`` — so a record stale-as-of-now but current-as-of
      τ is returned (filtering ≠ deletion).
    """
    out: list[dict[str, Any]] = []
    for row in rows:
        interval = _supersession_interval(str(row.get("path", "")))
        if as_of is None:
            if _interval_current(interval):
                out.append(row)
        else:
            if _interval_contains(interval, as_of):
                out.append(row)
    return out


#: Far-future close sentinel for a marked record whose ``superseded-date``
#: is unparseable/absent (the marker's PRESENCE still closes the interval).
_SUPERSEDED_SENTINEL_CLOSE = datetime(9999, 12, 31, tzinfo=timezone.utc)


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


def activation_enabled() -> bool:
    """Whether the power-law activation multiplier is live (AC.EVX.2).

    The June-7 retrieval eval measured activation net-harmful against
    the current store (BM25-floor beat the live ranker ~2× on
    recall@10 / MRR / miss-rate): on a stale access log the power-law
    decay collapses into a frequency prior that fights relevance. The
    verdict was FIX-not-kill — the theory is sound for a live,
    continuously-refreshed log — so the machinery stays in code,
    DEFAULT-OFF, behind this named switch.

    The switch is the :data:`ACTIVATION_FLAG_ENV` environment variable
    (truthy values: ``1`` / ``on`` / ``true``, case-insensitive).
    Default (unset / any other value) is OFF → activation contributes
    a neutral 1.0 factor and the ranking is BM25 × supersession (the
    eval's measured-best floor arm — AC.EVX.1). Re-enabling requires
    no code change (AC.EVX.2) and is gated on a live-access-log
    re-measurement beating the floor arm (plan §7).
    """
    return os.environ.get(ACTIVATION_FLAG_ENV, "").strip().lower() in (
        "1",
        "on",
        "true",
    )


def _compose_score(
    rows: list[dict[str, Any]],
    *,
    num_results: int,
    now: datetime,
    memory_root: Path,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    """Compose BM25 with the supersession penalty (and, only when the
    :func:`activation_enabled` switch is ON, the power-law activation
    multiplier); return the top ``num_results``.

    Memory recall cycle, Slice 1 (AC.EVX.1 / AC.EVX.2) — executes the
    owner's June-7 eval verdict:

      - **Co-citation spread: KILLED.** The one-hop spread step lowered
        retrieval quality on every measured metric (recall@10 −12% rel,
        precision@10 −15% rel, MRR −0.035, 2× latency) and rescued 0 of
        the 88 phrasing-mismatch queries it existed for. The spread
        path and ``cocitation_graph.py`` are deleted; re-adding
        requires fresh evidence (re-build from git history).
      - **Activation: NEUTRALIZED, default-off** (AC.EVX.2 — see
        :func:`activation_enabled`). With the switch off the access
        log is not read at all on the search path (the floor arm's
        single-search latency, AC.EVX.OA).
      - **AC.FBMT1.SUPM.2** — the supersession penalty is unchanged:
        multiplied through after (neutral or live) activation; a
        high-relevance superseded file still surfaces, just demoted.

    AC.FBMT1.SUPM.4 surface preserved: ``_LAST_RANKER_WARNINGS`` is
    populated when ``superseded-by`` points at a missing target.
    """
    global _LAST_RANKER_WARNINGS  # noqa: PLW0603 — AC.FBMT1.SUPM.4 surface
    _LAST_RANKER_WARNINGS = []
    if not rows:
        return []
    # AC.SUP.1 / AC.SUP.2 — apply the validity-interval FILTER FIRST,
    # BEFORE scoring + the top-N cut. The default current view
    # (``as_of is None``) removes closed-interval (superseded) records
    # entirely (current-over-stale); an ``as_of`` query keeps records
    # whose interval contains that instant (history reachable). This is
    # the promotion of the old demote-not-filter ``SUPERSEDED_PENALTY``
    # into a real filter — the penalty below still applies to whatever
    # survives the filter (it is a no-op on the default view since the
    # only rows carrying a marker are filtered out there, but it remains
    # correct for an ``as_of`` view where a marked-but-in-window record
    # survives and should still rank under an unmarked one).
    rows = _filter_by_interval(rows, as_of=as_of)
    if not rows:
        return []
    # AC.EVX.2 — the default-off switch. OFF: the access log is never
    # read; every multiplier is the neutral 1.0 (the floor arm).
    events_by_file: dict[str, list[Any]] = (
        _access_log.read_access_log(memory_root) if activation_enabled() else {}
    )
    activation_cache: dict[str, float] = {}

    def _activation_multiplier(file_key: str) -> float:
        """Convert the activation log-sum into a multiplicative factor.

        ``compute_activation`` returns ``ln(Σ t^-d)`` (Anderson &
        Schooler 1991). ``exp(B_i)`` undoes the ``ln``; the empty-sum
        case (``B_i = -inf``) clamps to 1.0 so a never-accessed file
        ranks on pure BM25. With the switch OFF ``events_by_file`` is
        empty, so every lookup short-circuits to the neutral 1.0
        (AC.EVX.1 — zero activation contribution by default).
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
        composed = bm25_raw * _activation_multiplier(path_str)
        # AC.FBMT1.SUPM.2 / SUPM.3 — supersession penalty applies last;
        # the file stays in the candidate set, just demoted.
        marker = _superseded_marker(path_str)
        if marker is not None:
            composed = composed * SUPERSEDED_PENALTY
            if _superseded_marker_target_missing(marker, memory_root):
                _LAST_RANKER_WARNINGS.append(
                    f"superseded-by target missing: "
                    f"{path_str!s} -> {marker}"
                )
        scored.append((composed, idx, row))

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
