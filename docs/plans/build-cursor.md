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
SLICE:    P1.2 .loam/ workspace layout
STEP:     5 INTEGRATE+RECORD (PROVE done — 5/5 ACs PASS)
DISPOSITION: build-new (layout contract + home dirs); leave (the live memory/ tree, additive only)
GATE-STATUS: owner-gated LAYOUT REVIEW pending — the durable on-disk contract is surfaced for
             ratification (master plan P1.2). Established additively + non-destructively in the
             meantime; nothing in ~/.claude/settings.json touched; no .pos/ or memory/ move.
PROVE-RESULT:
  AC-LOAM-LAYOUT-1 fresh tree → complete layout ... PASS (cold-walk on temp dir)
  AC-LOAM-LAYOUT-2 self-describing README ......... PASS
  AC-LOAM-LAYOUT-3 boundary additive / memory kept  PASS (live pos3: 1283 eps + index unchanged)
  AC-LOAM-LAYOUT-4 idempotent / fail-safe ......... PASS (2nd run no-op; annotations preserved)
  AC-LOAM-LAYOUT-5 migration recorded ............. PASS (docs/state-migrations/loam-layout-slice.migration.yaml)
  Test: framework/workspace-bootstrap/tests/test_AC_LOAM_LAYOUT_establish.py (4/4)
UPDATED:  2026-05-31
NEXT:     P1.3 user-state migration engine + RELEASE-GATE
```

## F2 corrective applied this slice
The declared-migration CONTRACT now lives tracked at `docs/state-migrations/`
(P1.1's `fbm-live-slice.migration.yaml` relocated there). The per-workspace
applied-migration CURSOR stays at `<workspace>/.loam/migrations/.cursor`
(gitignored user-state). This makes the §2-F2 boundary physical: framework
contract tracked, user applied-state not.

---

## PRIOR SLICE (P1.1 FBM-LIVE) — COMPLETE, for reference
- DISPOSITION: leave (already-live; amendment #154 D1/D2/D3 shipped + owner-activated 2026-05-29)
- PROVE: AC-1 PASS, AC-2 PARTIAL (HALT+surfaced — sealed retrieval.py score-scale mismatch;
  owner/next-cycle fix), AC-3 PASS, AC-4 PASS.
  Evidence: `.scratch/claude-output/fbm-cold-walk/COLD-WALK-RESULTS.md`
- OPEN: AC-FBM-LIVE-2 unify-effectiveness → FBM Cycle-2 (reserve-slot / rank-normalize / per-source quota)
