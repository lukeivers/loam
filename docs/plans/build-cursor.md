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
SLICE:    FBM episode SALIENCE gate (B3 — the recall-quality safety-pair to B1)
STEP:     5 INTEGRATE+RECORD COMPLETE (PROVE done — 5/5 ACs PASS; sealed + committed)
DISPOSITION: extend (two sealed functions — file_memory write_episode/search + retrieval merge)
GATE-STATUS: none pending — fail-safe verified on BOTH every-turn hot paths (ingest AND recall):
             compute_salience is exception-wrapped to SALIENCE_FULL; the search paths compute
             salience fresh from each body (no I/O, correct for pre-salience episodes without
             rewrite); the no-episode early-return stays byte-identical (FBMU.2). HARD INVARIANT
             proven: gates surfacing only — every turn still on disk (SAL-3), re-tunable (SAL-4),
             no not-store/delete path. No ~/.claude/settings.json, no Cairn; the live 1288-episode
             store was READ-ONLY-copied into a temp root for the cold-walk, never written.
PROVE-RESULT:
  AC-FBM-SAL-1 JUNK-FILTERED (load-bearing) ...... PASS — a <task-notification> episode tagged
             salience 0.0 at ingest does NOT surface even sharing the query token; boilerplate
             tokens (task-id/tool-use-id) don't leak.
  AC-FBM-SAL-2 NO-REGRESSION ..................... PASS — a substantive episode still surfaces;
             empty-episode merge returns the SAME corpus list object (FBMU.2 byte-identical);
             corpus hits never gated.
  AC-FBM-SAL-3 NEVER-DELETE (load-bearing) ....... PASS — the junk episode is still WRITTEN to disk
             with its full body verbatim (salience: 0.0 tagged, not deleted) + retrievable by
             direct recent_episodes lookup.
  AC-FBM-SAL-4 RE-TUNABLE (load-bearing) ......... PASS — at the default threshold the junk is
             gated; lowering salience_threshold re-admits it through production retrieve() (gate
             reversible, nothing lost).
  AC-FBM-SAL-5 LIVE-STORE COLD-WALK (the bar) .... PASS — real <task-notification> + real
             <channel>-wrapped Luke-message episodes copied from the live store shape into a temp
             root: junk suppressed AND the real channel message scores salient (protect-real-
             messages proven, not just junk-drop). Live store untouched (still 1288).
  Tests: framework/primary-persona full suite GREEN (813 passed = 804 prior + 9 SAL, 1 pre-existing
         skip); FBMU 1/2/3 + rank-normalize + rule-weighting (AC-FBM-W) green; seal-fence green.
  Commit: fb26be2 (slice) + the seal-advance follow-up (BASELINE d871910, SEAL_COMMIT fb26be2).
  Migration: docs/state-migrations/fbm-episode-salience-slice.migration.yaml (real forward-additive
             schema-add; non-destructive, non-rewriting). Plan:
             docs/plans/fbm-episode-salience-slice-plan.md.
UPDATED:  2026-05-31
NEXT:     P1.3 user-state migration engine + RELEASE-GATE
```

## This slice — FBM episode SALIENCE gate (B3, the recall-quality safety-pair to B1)
Junk turns (agent task-notification turns, empty/near-empty channel-header events, bare acks) were
logged as episodes and ranked HIGH on shared boilerplate tokens, polluting recall. B3: (1) TAG AT
INGEST — `file_memory.write_episode` computes a cheap structural salience score (`compute_salience`)
from the turn's user half and stores a `salience: <float>` frontmatter field. Four junk signatures
verified against the live 1288-episode store: task-notification (494), channel/scaffolding-empty (38),
empty-user (17), bare-ack (12). A `<channel>`-wrapped REAL Luke message is fully salient (the scorer
keys on the residual inner text, not the wrapper tag — the load-bearing protect-real-messages
property; 687 such real messages must NOT be gated). (2) FILTER AT RECALL — `retrieval._merge_by_score`
multiplies each episode hit's weighted-normalized score by its salience AND force-DROPS any hit below
the named, tunable `SALIENCE_THRESHOLD` (default 0.5) — the episode mirror of B1's pinned force-include.
Salience is the episode side of the SAME weight knob B1 added. The search paths compute salience FRESH
from each body, so the 1288 pre-salience episodes get the correct gate WITHOUT any rewrite. HARD
INVARIANT (load-bearing): gates SURFACING only, never storage — no not-store path, no delete path; a
mis-judged junk turn stays on disk verbatim and is re-admittable by lowering the threshold. Fail-safe:
every default/error path resolves to SALIENCE_FULL. Migration:
`docs/state-migrations/fbm-episode-salience-slice.migration.yaml` (REAL forward-additive schema-add —
a new frontmatter field on NEW episodes only; non-destructive, non-rewriting). Plan:
`docs/plans/fbm-episode-salience-slice-plan.md`.

## PRIOR SLICE — FBM rule-weighting + hard-floor (B1, the rank-normalize safety-pair)
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
