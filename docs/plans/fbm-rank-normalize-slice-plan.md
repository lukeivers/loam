# FBM rank-normalize slice plan (AC-FBM-LIVE-2 fix)

**Status:** slice plan-doc (plan-before-code per the v-next build workflow)
**Working dir:** `/Users/lukeivers/loam` (canonical loam)
**Branch:** `slice/p1.2-loam-layout` (current build branch)
**Date:** 2026-05-31
**Workflow:** `docs/plans/loam-vnext-build-workflow.md` (per-slice loop)
**Predecessor slice:** P1.1 FBM-LIVE (`fbm-live-slice-plan.md`) — surfaced
the AC-FBM-LIVE-2 unify-effectiveness gap. This slice fixes ONLY that gap.
**Predecessor seal:** amendment #154 (FBM Cycle 1 — write-path fix + unify),
seal `505b32eb`, BASELINE `14e972e`.

---

## Objective
Make the FBM episode store co-surface alongside the rules corpus in the
**live** unified retrieval — closing the AC-FBM-LIVE-2 gap that P1.1's
cold-walk surfaced and HALTed. The fix is DECIDED: **rank-normalize** the
two physical indexes' scores onto a common scale BEFORE the merge, so the
genuinely-best result from each source competes fairly regardless of the
source's raw BM25 magnitude. This is a surgical change to one function in
one sealed component (primary-persona `retrieval.py:_merge_by_score`).

## EXAMINE — the verified scales (empirical, against LIVE data)

Instrumented the production search paths against the live corpus
(`~/.claude/projects/-Users-lukeivers-pos3/memory` + `OBJECTIVES.md`,
132 docs) and the live episode store (1283 episodes), plus a temp
single-episode store. Scripts: `.scratch/claude-output/fbm-rank-normalize/`.

**Both indexes negate SQLite `bm25()` (larger = better), but the magnitudes
are incompatible AND regime-dependent:**

| Source | Observed raw-score range (live) | Note |
|---|---|---|
| Corpus (`corpus_index.search`) | ~15–285; steep cliff (top 2 hits 225–285, rest ~30) | 132-doc index; OBJECTIVES/CURRENT-WORK dominate |
| Episode (`_episode_hits` `_bm25_raw`) | 0–40 in the 1283-episode store; **0.0 for a freshly-written episode in a sparse store** | BM25 IDF collapses toward 0 when the store has few documents |

Two distinct truncation regimes confirmed (NOT one, as the P1.1 note
framed it):
1. **Scale mismatch** — live episodes max ~40 vs corpus top hits ~285, so
   raw-merge buries relevant episodes below the corpus head. (The P1.1
   "episode bm25 ~0–1" reading was specific to the *synthetic single
   codeword episode*, not the live store.)
2. **Sparse-store BM25-collapse** — a freshly-written relevant episode
   scores `0.0` in its own near-empty FTS index, so raw-merge ranks it
   dead last and it truncates out of `top_n` entirely. This is the exact
   scenario the P1.1 cold-walk hit (codeword episode never surfaced).

**Prototype of min-max-per-source normalization fixes BOTH regimes**
(`.scratch/.../proto_norm.py`):
- Regime 1 (live store): episodes move to ranks 2–3, co-surface.
- Regime 2 (single relevant episode @ raw 0.0): min-max maps a source's
  best (and sole) hit → 1.0, so the lone relevant episode co-surfaces at
  rank 2 — the codeword now appears.

**Relevance is gated upstream:** `_episode_hits` only returns episodes the
FTS `MATCH` query hit; an irrelevant prompt returns zero episode hits
(verified), so normalization never force-surfaces noise.

EXAMINE disposition: **extend** (one sealed function, surgical).

## DEFINE — outcome-altitude acceptance criteria

- **AC-FBM-RN-1 (load-bearing, outcome-altitude)** — against the **LIVE**
  rules corpus, a single `retrieve()` call co-surfaces a relevant,
  freshly-written episode (a distinctive codeword written through the
  production enqueue→drain→retrieve path) in the top-N results — the exact
  thing AC-FBM-LIVE-2 had as PARTIAL. Verified by a live-corpus cold-walk
  in a fresh process with no pre-arranged state, against a temp episode
  store (does not touch the live 1283-episode store).
- **AC-FBM-RN-2** — corpus-only behaviour sane: with no episode hits the
  merge returns the corpus hits unchanged (byte-identical no-regression —
  the FBMU.2 invariant); the strongest corpus hit still leads any merged
  set (corpus-before-episode stable tie-break preserved).
- **AC-FBM-RN-3** — episode-only behaviour sane: with no corpus hits the
  episode hits render in their own descending order, capped at top-N.
- **AC-FBM-RN-4** — existing sealed `test_AC_FBMU_*` stay green, OR the
  FBMU.3 raw-score-contract tests are updated to the normalized contract
  WITH justification recorded here (they encode raw-score ordering, which
  rank-normalize deliberately changes).

## Normalization design (the merge change — method)

`_merge_by_score` gains a per-source **min-max normalization** before the
combined sort:
- Each source's hits are normalized independently onto `[0, 1]`:
  `norm = (score - min) / (max - min)`.
- **Single-element or all-equal source → norm `1.0`** (a present, matched
  hit is fully its-source-best; this is what rescues the sparse-store
  regime-2 episode).
- Combined list sorts by descending `norm`; ties keep arrival order
  (corpus enumerated before episodes) — the existing stable tie-break, so
  the strongest corpus hit still leads on a 1.0–1.0 tie.
- Truncate to `top_n` (unchanged).
- **The `if not episode_hits: return corpus_hits` early return is preserved
  UNCHANGED** — this is the FBMU.2 byte-identical no-regression invariant;
  normalization only runs when episodes actually merged.

Min-max (not z-score / not pure rank) is chosen because: it is
scale-free, handles the single-element store gracefully via the all-equal
→ 1.0 rule, needs no distribution assumption, and is stdlib-trivial /
deterministic — matching the module's stdlib-only fail-soft posture.

## Edit list (surgical)
1. `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py`
   — rewrite `_merge_by_score` to min-max-normalize each source before the
   combined sort; preserve the empty-episode early return + top_n cap +
   stable tie-break. Add a `_minmax_norm` helper. (The `score` field stays
   on each hit for transparency; sort key becomes the normalized value.)
2. `framework/primary-persona/tests/test_AC_FBMU_3_merged_surface_respects_caps.py`
   — update the two raw-score-ordering assertions to the normalized
   contract (justification below); keep the cap + byte-budget + tie-break
   assertions. Add an AC-FBM-RN regime test (sparse episode @ raw 0 still
   surfaces).
3. `docs/state-migrations/fbm-rank-normalize-slice.migration.yaml` — declared
   migration (structural / no-op: no user-state schema change; the merge is
   pure framework-code ranking).
4. `docs/plans/build-cursor.md` — advance the cursor.

### Sealed-test update justification (AC-FBM-RN-4)
`test_AC_FBMU_3_merge_caps_at_top_n` and
`test_AC_FBMU_3_merge_descending_score_deterministic` assert the OLD
**raw-score** ordering (e.g. "5 episodes at raw 16–20 outrank 5 corpus at
raw 6–10", "merged[0] is the raw-9.0 corpus hit, merged[-1] the raw-1.0
corpus hit"). Rank-normalize **deliberately** replaces raw-score ordering
with per-source-normalized ordering — that is the fix. Updating these is
required, not a weakening: the cap (`len == top_n`), the byte budget, and
the corpus-before-episode stable tie-break (FBMU.3's
`equal_score_stable` test) are PRESERVED unchanged; only the cross-source
raw-magnitude ordering claims are restated to the normalized contract,
which is the new intended behaviour. FBMU.1 (both surface) and FBMU.2
(byte-identical no-regression) are untouched and stay green.

## Fail-safe (every-turn live hook)
`retrieval.py` is the live global keep-pace UPS hook firing on every turn.
The change is fail-safe by construction: (a) the no-episode early-return is
byte-identical (FBMU.2); (b) min-max is pure arithmetic on already-fetched
hit lists — no new I/O, no new failure surface; (c) the module's
`Exception → []`/`""` fail-soft envelope is unchanged. If the prototype had
shown a corpus-relevance regression I could not prove acceptable, the slice
would HALT per the dispatch's fail-safe rule — it does not (corpus head
still leads; episodes only gain the slots raw-merge already gave the
*trailing* corpus hits, which are the weakest corpus matches).

## Halt triggers honoured
- Sealed-component edit: one function in primary-persona — followed via the
  amend/seal discipline (advance `tests/SEAL_COMMIT`, run touched + sweep
  tests). No content-filter, no Cairn, no `~/.claude/settings.json`, no
  touch of the live 1283-episode store (cold-walk uses a temp repo root).
- No `claude -p` spawn needed (in-process production entry points), so no
  bot-slot-steal risk; had one been needed it would use `--strict-mcp-config`.
