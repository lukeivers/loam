# Memory redesign S2 (design Stage 3) — recency as a prioritizer + relevance-threshold recall

Per `docs/plans/memory-redesign-s2-recency-relocation-discovery-prioritization.md`
(build-ready pending owner GO on the §10 forks) and the ratified design
`workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md`
(design Stage 3 — "recency relocation: discovery vs prioritization"). Single-component
amendment on the EXISTING `framework/primary-persona/` component; advances the sidecar.
Composes on S1a ground-floor extraction (`RANK_CONSTITUTIONAL_FLOOR = False`) and the
memory-recall Slice 1 (activation neutralized default-off, co-citation deleted).

Tier-0 finding pinned at plan-authoring (corrects the design's stale premise): on the
live default path recency is NOT a discovery signal. `_episode_hits` → `_fts_search`
→ `_compose_score` ranks BM25 × activation(off=1.0) × supersession; the W=0.5
recency-in-discovery blend `_blend_recency` is DEAD code (zero call sites). The corpus
half (`corpus_index.py::search`) has no recency term. Recall is a fixed top-N=5
truncation, not a relevance threshold. Injection-frequency self-reinforcement — the
design's headline worry — is already neutralized (activation default-off, co-citation
deleted). So this stage is not "strip recency out of the ranker"; it is two deltas plus
a lock:

  - RELEVANCE-THRESHOLD recall (empty-OK) replaces the fixed count as the
    set-determiner; an optional count cap stays as a safety cap above the threshold.
  - A bounded EVENT-RECENCY prioritizer is added AFTER the threshold, over the
    discovered set only — newer-by-event-time ranks ahead when relevance is comparable
    (owner's supersession example), never resurrecting a below-threshold record.
  - Discovery-relevance-only is locked as a tested invariant, and injection-history is
    structurally forbidden as a ranking signal (AC.RDP.4); the dead `_blend_recency` is
    retired/quarantined so recency cannot be re-wired into discovery.

All levers are NAMED and reversible (threshold, recency-prioritizer weight, count cap),
mirroring RANK_CONSTITUTIONAL_FLOOR / MIN_RELEVANCE_SCORE / RECENCY_BLEND_WEIGHT;
restoring legacy values reproduces the pre-stage ranking (AC.RDP.5). Ranking-only — no
data migration; the derived `.scratch/` index + on-disk episodes/corpus are untouched.

  - AC.RDP.1 — discovery is relevance-only: set membership is decided by topical
    relevance alone, invariant to event-time and injection-history.
  - AC.RDP.2 — relevance-threshold recall, empty-OK: one relevant record surfaces one
    (not padded to K); zero relevant surfaces empty.
  - AC.RDP.3 — event-recency prioritizes WITHIN the discovered set: newer-by-event-time
    ahead on comparable relevance; never promotes a below-threshold record.
  - AC.RDP.4 — injection-history is never a ranking signal: injecting a record on turn N
    does not raise its discovery or prioritization on turn N+1 (relevance + event-time
    fixed).
  - AC.RDP.5 — reversible via named levers.
  - AC.RDP.6 (outcome-altitude) — production `retrieve()` with no pre-arranged state:
    two relevant records of different event-age surface newest-first and a
    below-threshold near-miss is excluded; a query with only near-misses surfaces empty.

Gating precondition (plan §10 Fork 1): baseline telemetry (design Stage 2) must be
capturing before the split flips live, per the design spine and the reversible+measurable
binding, unless the owner explicitly waives it. No ODD violation in surrounding code;
the change is named tunable levers consumed at the merge, no defensive code for unnamed
cases.
