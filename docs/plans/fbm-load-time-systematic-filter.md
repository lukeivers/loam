# FBM load-time systematic relevance+quality filter (Slice B)

**Author:** build agent · **Date:** 2026-06-02 · **Owner:** Luke (greenlit 13582)
**Parent plan:** `workspace/.scratch/claude-output/loam-fbm-quality-and-accuracy-unified-plan.md` (Slice B, P3).
**Mode:** plan-before-code; single-component amendment on the EXISTING `framework/primary-persona/` component.

---

## Objective

Retrieval applies ONE systematic filter stage that, together with the already-sealed
salience gate, holds the injected ≤5 block to **above-floor, distinct** episode hits.
Two mechanisms are added to that stage and the reactive per-case load patches are
consolidated into it:

1. **Absolute relevance floor (B1).** An episode whose RAW BM25 relevance is below an
   absolute floor is excluded BEFORE the per-source min-max normalization — **but only
   when another episode clears the floor** (the over-filter safeguard; see the conflict
   resolution below). So a weak-but-best episode can no longer be promoted to `1.0` by
   min-max and out-rank a real corpus feedback-rule in a populated index. This closes
   FM-4 on the EPISODE side (the corpus side already floors at `MIN_RELEVANCE_SCORE = 0.1`).
2. **Near-duplicate dedup (B2).** Among the surviving hits, near-identical episodes
   (token-Jaccard > 0.85, stdlib-only) collapse to one; the freed top-N slot is filled
   by the next distinct hit.

## The structural bug (Tier-0, verified this session)

- The episode min-max path (`_minmax_norm`, retrieval.py:370) maps each source's BEST
  matched hit to `1.0` and worst to `0.0`. For the EPISODE source this means a
  weak-but-best episode at raw negated-BM25 `~0.5` is promoted to `1.0` and competes
  head-to-head with a genuinely-strong corpus rule, ALSO at `1.0` — the exact
  min-max-promotion failure the parent plan names (FM-4). The CORPUS source already
  guards this: `CorpusIndex.search` drops `rel < MIN_RELEVANCE_SCORE (0.1)` before
  returning (corpus_index.py:482). The EPISODE source has **no** absolute floor — its
  pool arrives at `_merge_by_score` un-floored.
- Tier-0 on the score carried into the merge: `_episode_hits` reads
  `ep.get("_bm25_raw")` (retrieval.py:224). The episode pool's `_bm25_raw` slot is the
  **raw** negated-BM25 the FTS search computed (`-float(score)`, file_memory.py:991) —
  it survives `_compose_score_and_spread` un-overwritten (the compose function uses the
  `composed = bm25_raw × activation × supersession` value only for the intra-pool top-N
  cut, then returns the original `row` dicts whose `_bm25_raw` is still raw BM25,
  file_memory.py:1664). So the floor in `_merge_by_score` is applied to genuine raw
  BM25 on the SAME negated-BM25 scale as the corpus floor — no activation/supersession
  double-count, and no over-filter risk from composing a fresh-but-relevant episode's
  score down below the floor (that composition is not what the merge ranks on).
- No dedup exists anywhere on the load path. Adjacent near-identical episodes (the
  parent plan measured 27 episodes in 8 groups sharing an opening) can occupy multiple
  of the ≤5 slots, crowding out distinct context.

## The reactive patches consolidated (the whack-a-mole this retires)

The salience gate accreted five structural junk signatures (task-notification,
channel/scaffolding-empty, empty-user, bare-ack, compaction-summary-dump), the last two
added as REACTIVE per-case patches after the owner hit recall-pollution twice. Those
already live INSIDE `_merge_by_score`'s salience-gate sub-stage. Slice B makes the
filter stage SYSTEMATIC: the salience gate, the absolute floor, and the dedup are the
single named retrieval pre-merge stage, so the next class of "a weak/duplicate thing
surfaced" is absorbed by the systematic floor+dedup rather than by adding signature #6.
B3 asserts this structurally — no per-case signature lives outside the one stage.

## The filter stage (where each mechanism sits)

`_merge_by_score` already runs the salience gate as the first pre-merge step
(retrieval.py:505). Slice B extends that pre-merge stage in place:

1. **Salience gate** (existing) — drop episode hits with `_salience < salience_threshold`.
2. **Absolute floor (B1, new)** — drop episode hits with `_bm25_raw <
   EPISODE_MIN_RELEVANCE_SCORE` BEFORE `_minmax_norm`. Applies to episodes only; corpus
   hits are already floored at source and pinned rules are never floored.
3. **Near-dup dedup (B2, new)** — over the combined post-sort, pre-truncate ordered hit
   list, collapse any later hit whose token-Jaccard with an already-kept hit exceeds
   `DEDUP_JACCARD_THRESHOLD`; keep the higher-ranked member, let the next distinct hit
   take the freed slot. Pinned rules are never deduped away (the hard floor survives).

The min-max normalization, weight boost, salience multiply, pinned force-include, and
top-N truncation are otherwise unchanged. The no-episode early-return
(`if not episode_hits: return corpus_hits`, AC.FBMU.2 byte-identical) is preserved: with
no episodes the floor/dedup do not run and corpus-only output is byte-exact.

## Conflict resolution — B1 absolute floor vs the SEALED AC-FBM-RN-2 (M5, Lens 6/7)

**The conflict (named).** Slice B's B1 wants a sub-floor episode NOT to out-rank a corpus
rule (FM-4). The sealed AC-FBM-RN-2 (`test_AC_FBM_RN_sparse_episode_at_raw_zero_co_surfaces`)
asserts the OPPOSITE for a hand-set raw-`0.0` episode: it must co-surface at rank 2,
*ahead of a weaker corpus hit* — the IDF-collapse rescue for a lone relevant fresh-write
episode. An UNCONDITIONAL absolute floor at `0.1` breaks RN-2 and three other sealed tests
(FBMU-1, SAL-2, SAL-7) — all of which seed a single relevant episode that, in a sparse
test store, legitimately scores ~0 (verified Tier-0: a relevant sparse episode scored
`6e-06` and a noise sparse episode scored `1e-06` — **raw BM25 is not a discriminator in
the sparse regime**).

**The signals weighed.** (1) *Information asymmetry / operational reality* — Tier-0 against
the LIVE 1400-episode store: genuine matches score 5–20 on this scale; the floor is only
operative in the POPULATED regime, never in the sparse one. The sparse near-0 case is a
test-fixture artifact, not a production case. (2) *Reversibility* — breaking a sealed AC is
high blast-radius; a safeguard that preserves it is low-risk. (3) *Scope-confidence* — the
parent plan's FM-4 is "a weak episode out-ranks a real feedback-rule **by keyword density**"
— keyword density is only meaningful in a populated index, confirming the floor belongs to
the populated regime.

**The resolution.** The floor SELF-DISABLES when no episode clears it (the sparse /
IDF-collapsed regime), and applies only when at least one OTHER episode clears it (the
populated regime where raw BM25 genuinely discriminates). This closes FM-4 in production
(a pure-noise sub-floor episode is dropped when real matches are present) AND preserves the
sealed RN-2 / FBMU-1 / SAL-2 / SAL-7 behaviour (a lone relevant-but-sparse episode is never
over-filtered). No sealed AC's behaviour changes; no sealed test is edited. This is the
conservative reading of B1 — over-filtering genuine memory is the load-bearing risk, and
the safeguard structurally prevents it.

## Thresholds chosen (+ rationale — conservative, over-filter is the named risk)

- **`EPISODE_MIN_RELEVANCE_SCORE = 0.1`** — mirrors the corpus `MIN_RELEVANCE_SCORE =
  0.1` (corpus_index.py:79) on the identical negated-BM25 scale. Rationale: verified
  Tier-0 against the live 1400-episode store, a genuine multi-term episode match scores
  5–20 on this scale; `0.1` filters only pure-noise zero-IDF single-common-word hits.
  Setting it EQUAL to the corpus floor is the conservative choice. **Applied with the
  self-disable safeguard** (above): the floor only removes a sub-floor episode when
  another episode clears it (populated regime), so a lone relevant-but-sparse episode is
  never over-filtered. Pinned rules + corpus hits are never subjected to it (corpus is
  floored at source; episodes carry no pin). A NAMED, tunable constant: lowering it
  re-admits previously-floored episodes (reversibility, like the salience threshold).
- **`DEDUP_JACCARD_THRESHOLD = 0.85`** — the GBrain near-dup threshold the parent plan
  specifies (token-set Jaccard over the pointer/content tokens). Rationale: 0.85 is high
  enough that only near-identical openings collapse (two genuinely-distinct turns that
  merely share vocabulary score well below 0.85 on full token sets); it is the
  conservative end (a lower threshold risks collapsing distinct context, the named
  over-filter risk). Stdlib-only token-set Jaccard — no embeddings, no API key
  (`feedback_no_anthropic_api_key`). Tunable named constant.

## Constraints (hard)

- Compose on `_merge_by_score` / `_minmax_norm` / `_render_injection` in retrieval.py and
  the existing `SALIENCE_THRESHOLD` salience gate. Do NOT author a new retrieval entry
  point or a sixth salience signature.
- The absolute floor mirrors the corpus `MIN_RELEVANCE_SCORE = 0.1` and is applied to
  RAW BM25 (the `_bm25_raw` slot), not the composed/normalized value — so a relevant
  episode whose activation/supersession composition is low is NOT over-filtered.
- Dedup is token-Jaccard at 0.85, stdlib-only, no embeddings (no API key).
- Conservative on both thresholds — over-filtering (suppressing genuinely-useful memory)
  is the load-bearing risk; B4 proves a genuinely-relevant episode still surfaces.
- Pinned corpus rules (the hard floor) are NEVER floored or deduped away.
- AC.FBMU.2 byte-identical no-episode path preserved; salience-gate non-regression
  (AC-FBM-SAL-1..9) preserved.
- stdlib-only; ODD §2.5 — every line maps to a named AC; no defensive `if` without an
  AC anchor.

## ACs

- **AC-FBM-FLOOR-1 (B1)** — in a POPULATED result set (≥1 above-floor episode), an
  episode whose RAW BM25 is below `EPISODE_MIN_RELEVANCE_SCORE` is dropped so it cannot
  be min-max-promoted to out-rank a corpus rule (FM-4 closed on the episode side); an
  above-floor episode still surfaces. The SAFEGUARD side: when NO episode clears the
  floor (the sparse / IDF-collapsed regime), the floor self-disables and a lone relevant
  sub-floor episode still co-surfaces (the sealed AC-FBM-RN-2 / AC.FBMU.1 behaviour is
  preserved — the floor filters noise, never a lone relevant-but-sparse memory).
- **AC-FBM-DEDUP-1 (B2)** — when two retrieved hits share > `DEDUP_JACCARD_THRESHOLD`
  token-Jaccard, only one occupies a top-N slot and the freed slot is filled by the next
  distinct hit (a third, distinct hit that would otherwise have been below the cut now
  appears).
- **AC-FBM-FILTER-STAGE-1 (B3)** — the salience gate, the absolute floor, and the dedup
  are a single named pre-merge filter stage in `_merge_by_score`; no per-case relevance
  or duplicate signature lives outside it. Verified structurally: the three mechanisms
  are the named constants `SALIENCE_THRESHOLD`, `EPISODE_MIN_RELEVANCE_SCORE`,
  `DEDUP_JACCARD_THRESHOLD`, all consumed in the one merge function; the reactive-patch
  pattern is retired (no new entry point, no sixth signature).
- **AC-FBM-FILTER-2 (outcome-altitude, B4)** — invoke the PRODUCTION `retrieve()` over a
  real `FileMemoryStore` with NO pre-arranged retrieval state, seeded with (a) a
  below-floor weak episode, (b) a near-duplicate pair of episodes, and (c) a
  genuinely-relevant distinct episode. Assert the injected block: excludes the
  below-floor episode, contains only ONE member of the near-dup pair, and STILL contains
  the genuinely-relevant distinct episode. Drives `retrieve → _episode_hits → store.search
  → _merge_by_score → _render_injection` with no internal-call shortcut.

## Non-regression

- AC-FBM-SAL-1..9 stay green — the salience gate sub-stage is unchanged; the floor +
  dedup are additive pre-merge steps after it.
- AC.FBMU.1/.2/.3 stay green — the no-episode early-return (byte-identical corpus-only)
  is preserved; the top-N cap + byte budget still bound the merged surface.
- AC-FBM-RN-1/.2 and AC-FBM-W-1/.2 stay green — min-max normalization, weight boost, and
  pinned force-include run after the floor exactly as before; pinned rules are never
  floored or deduped.

## Out of scope (named)

- Purging the existing ~600 hot-tier junk episodes (owner-gated; deferred, parent plan §7).
- Slices C/D/E/F (per-project STATE record, lens injection, multi-repo snapshot,
  BrainBench metric) — separate serialized slices.
- Any change to the write-time gate (Slice A, sealed) or the salience signatures.

## Method-decision register

- **D-FILTER.1** — the absolute floor is applied to RAW BM25 (`_bm25_raw`), NOT the
  composed/normalized value. Rationale: the merge already ranks episodes on raw BM25
  (the compose function's `composed` value is used only for the intra-pool cut, not
  carried into the cross-source merge — Tier-0 file_memory.py:1664); flooring raw BM25
  mirrors the corpus floor on the identical scale and avoids over-filtering a relevant
  episode whose activation/supersession composition is low.
- **D-FILTER.4** — the floor SELF-DISABLES when no episode clears it (the
  over-filter safeguard reconciling B1 with the sealed AC-FBM-RN-2). Rationale +
  full M5 conflict resolution: see "Conflict resolution" above. In the sparse /
  IDF-collapsed regime raw BM25 is not a relevance discriminator (verified Tier-0),
  so the floor must not fire there; it fires only in the populated regime where a
  sub-floor episode is genuinely out-competed by another above-floor episode.
- **D-FILTER.2** — dedup runs over the COMBINED, ordered, pre-truncate hit list (corpus
  + surviving episodes), so a near-dup that spans the corpus/episode boundary is also
  collapsed; the higher-ranked member is kept. Pinned hits are exempt (the hard floor
  must survive). Rationale: dedup is a property of the surfaced set, not of one source.
- **D-FILTER.3** — thresholds set conservative (floor EQUAL to the corpus floor; Jaccard
  at the high 0.85 end) so over-filtering of genuine memory is structurally minimized;
  B4 proves a real memory still surfaces.
