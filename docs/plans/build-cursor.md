# loam v-next build — position cursor ("you are here")

**This is the TRACKED, committable home for the build position cursor.**
It was moved here from `.loam/build-cursor.md` by slice P1.2 (F2
corrective): `.loam/` is gitignored user-state, so a cursor under it could
never be committed (the P1.1 cursor was silently dropped from commit
`8ae3d7b`). The build position cursor is build-methodology, not a shipped
user-state — so it belongs in the tracked docs tree. Per the workflow §5,
when P2.3 builds the persisted-cursor mechanism this manual block is
replaced by it.

```
WORKFLOW: loam v-next build
SLICE:    FBM rule-weighting + hard-floor (B1 — the rank-normalize safety-pair)
STEP:     5 INTEGRATE+RECORD (PROVE done — 4/4 ACs PASS)
DISPOSITION: extend (two sealed functions — corpus_index read/search + retrieval merge)
GATE-STATUS: none pending — fail-safe verified on the every-turn live hook (boost + partition are
             pure arithmetic/set-ops on already-fetched hits; frontmatter parse is fail-soft to the
             no-op baseline; the no-episode early-return is byte-identical, FBMU.2 green). No
             ~/.claude/settings.json, no Cairn, no touch of the live episode store (cold-walk copied
             the real feedback_*.md corpus into a temp repo root; never wrote the live store).
PROVE-RESULT:
  AC-FBM-W-1 GRADIENT ............................. PASS — at equal relevance a higher-weighted rule
             out-ranks a lower-weighted one; weight 50 (baseline) boosts by 1.0 (no-op).
  AC-FBM-W-2 FLOOR/SAFETY (load-bearing) ......... PASS — a pinned rule co-surfaces at ~0 relevance
             against a hyper-relevant episode flood; the SAME rule at MAX weight but UNPINNED drops
             (multiplier-alone-can't-do-it, proven in the same test).
  AC-FBM-W-3 NO-REGRESSION ....................... PASS — no-frontmatter doc => baseline weight,
             body byte-identical; empty-episode merge returns corpus list unchanged.
  AC-FBM-W-4 LIVE-CORPUS COLD-WALK (the bar) ..... PASS — through production retrieve() on a temp
             copy of the REAL feedback_*.md corpus: a pinned doc that the query does NOT match at
             all still surfaces (force-fetch); the unpinned variant drops.
  Tests: framework/primary-persona full suite GREEN (804 passed, 1 pre-existing skip); AC-FBM-W
         9/9; FBMU 1/2/3 + rank-normalize green; seal-fence green.
UPDATED:  2026-05-31
NEXT:     P1.3 user-state migration engine + RELEASE-GATE
```

## This slice — FBM rule-weighting + hard-floor (B1, the rank-normalize safety-pair)
Rank-normalize made rules + episodes compete fairly on RELEVANCE, opening the hole that a
hyper-relevant episode can out-rank a CRITICAL rule. B1 closes it with a per-rule WEIGHT carried as
optional corpus-doc frontmatter: (1) `weight: 1-100` boosts a rule's normalized score
(`norm * weight/50`; baseline 50 => 1.0 no-op so today's corpus is byte-identical); (2) `pinned: true`
is the HARD FLOOR — always-include regardless of relevance. The floor is a force-INCLUDE, not a big
multiplier, because `weight × ~0-relevance ≈ 0` cannot guarantee never-drop. LOAD-BEARING fix found
in PROVE: a pinned rule that the query does not MATCH at all is never in the FTS result, so
`corpus_index.search` now ALSO force-FETCHES every pinned doc (at relevance floor 0.0) — the half a
relevance-ranked query cannot deliver. Migration:
`docs/state-migrations/fbm-rule-weighting-slice.migration.yaml` (no-op — code + optional, backward-
compatible frontmatter convention; the derived FTS index rebuilds on schema mismatch). Plan:
`docs/plans/fbm-rule-weighting-slice-plan.md`.

## PRIOR SLICE — FBM rank-normalize (closes the P1.1 AC-FBM-LIVE-2 gap)
EXAMINE verified the scales EMPIRICALLY against live data (not the reported ones): corpus BM25
~15–285 (steep cliff) vs episode 0–40 in the live 1283-episode store AND ~0.0 for a freshly-written
episode in a sparse FTS index (BM25 IDF collapses with few docs). Raw-score merge buried/truncated
relevant episodes. FIX (decided): `_merge_by_score` now min-max-normalizes each source onto [0,1]
before the combined sort; a single/all-equal source maps to 1.0 (rescues the sparse-store episode).
The empty-episode early-return is preserved unchanged (FBMU.2 byte-identical invariant). Migration:
`docs/state-migrations/fbm-rank-normalize-slice.migration.yaml` (no-op — code-only ranking change).

## F2 corrective applied in P1.2 (retained)
The declared-migration CONTRACT now lives tracked at `docs/state-migrations/`
(P1.1's `fbm-live-slice.migration.yaml` relocated there). The per-workspace
applied-migration CURSOR stays at `<workspace>/.loam/migrations/.cursor`
(gitignored user-state). This makes the §2-F2 boundary physical: framework
contract tracked, user applied-state not.

---

## PRIOR SLICE (P1.2 .loam/ workspace layout) — COMPLETE, for reference
- DISPOSITION: build-new (layout contract + home dirs); leave (live memory/ tree, additive only)
- PROVE: 5/5 ACs PASS. GATE: owner-gated LAYOUT REVIEW pending (established additively meanwhile).
- Migration: docs/state-migrations/loam-layout-slice.migration.yaml (structural-only).

---

## PRIOR SLICE (P1.1 FBM-LIVE) — COMPLETE, for reference
- DISPOSITION: leave (already-live; amendment #154 D1/D2/D3 shipped + owner-activated 2026-05-29)
- PROVE: AC-1 PASS, AC-2 PARTIAL (HALT+surfaced — sealed retrieval.py score-scale mismatch;
  owner/next-cycle fix), AC-3 PASS, AC-4 PASS.
  Evidence: `.scratch/claude-output/fbm-cold-walk/COLD-WALK-RESULTS.md`
- OPEN: AC-FBM-LIVE-2 unify-effectiveness → CLOSED by the FBM rank-normalize slice (above);
  rank-normalize chosen; live-corpus cold-walk now co-surfaces the relevant episode.
