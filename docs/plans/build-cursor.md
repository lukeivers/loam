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
SLICE:    FBM rank-normalize (AC-FBM-LIVE-2 fix)
STEP:     5 INTEGRATE+RECORD (PROVE done — 4/4 ACs PASS)
DISPOSITION: extend (one sealed function — primary_persona keep_pace retrieval merge)
GATE-STATUS: none pending — fail-safe verified on the every-turn live hook (no new I/O; the
             no-episode early-return is byte-identical, FBMU.2 green). No ~/.claude/settings.json,
             no Cairn, no touch of the live 1283-episode store (cold-walk used a temp repo root).
PROVE-RESULT:
  AC-FBM-RN-1 live-corpus co-surface (load-bearing) PASS — fresh relevant episode now appears
              alongside corpus hits in a single retrieve() call; was truncated out (raw merge).
  AC-FBM-RN-2 corpus-only sane / no-regression .... PASS — episode_memory_dir=None byte-identical;
              merged IS corpus (unit) + corpus head still leads any merged set.
  AC-FBM-RN-3 episode-only sane ................... PASS — descending order, top-N capped.
  AC-FBM-RN-4 sealed FBMU_* green ................. PASS — FBMU 1/2/3 all green; FBMU.3 raw-score
              ordering tests restated to the normalized contract WITH justification (not weakened).
  Tests: framework/primary-persona full suite GREEN (1 skip); FBMU suite 9/9; seal-fence 2/2.
UPDATED:  2026-05-31
NEXT:     P1.3 user-state migration engine + RELEASE-GATE
```

## This slice — FBM rank-normalize (closes the P1.1 AC-FBM-LIVE-2 gap)
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
