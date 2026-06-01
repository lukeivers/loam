# foundation-polish cluster — SUB-ITEM 3: migration auto-detect / auto-upgrade trigger — apply ladder

Foundation-polish cluster per `docs/plans/foundation-polish-cluster.md`.
The D4 fast-follow: wire the ALREADY-SEALED migration engine + `loam migrate`
verb to a session-start auto-detect so a non-technical user's stale
user-state is upgraded automatically, safely, and explained in plain words.

SUB-ITEM 3 (this amendment — AUTONOMOUS module build; the LIVE arm is
owner-gated):
  1. AUTO-DETECT (AC.UPGR.1) — a NEW fail-soft SessionStart contributor
     (`framework/orchestrator/scripts/auto_upgrade.py`) reads the
     per-workspace applied-migration cursor and enumerates the pending
     declared migrations in release-version order, WITHOUT the user running
     anything. Composes the SEALED engine's own pending-set computation
     (`read_cursor` → `load_migration_dir` → `enumerate_pending`).
  2. WRAPPED REPLAY (AC.UPGR.2) — on a gap, the contributor builds the
     envelope EXACTLY as the sealed `loam migrate` verb does
     (`ReversibilityStore` + `MigrationSafetyEnvelope`) and calls the
     SEALED `replay.replay`. Backup-first / protection-floor /
     rollback-on-failure are INHERITED. ZERO re-implementation of any
     apply/replay/backup path (plan §8.3 — the #1 boundary-leak risk).
  3. PLAIN-LANGUAGE SURFACE (AC.UPGR.3) — after an upgrade the user is told
     in plain words what happened ("loam brought your saved settings up to
     date (N updates applied); your existing work was preserved") — NO
     SHAs / cursor internals / AC-IDs. On a FAILURE the inherited rollback
     fires and the user is told the state was put back exactly as it was,
     nothing left half-changed.
  4. ★ outcome-altitude AC.UPGR.S COLD-WALK: a genuinely SEPARATE temp
     instance seeded at a real prior cursor with real seeded user-state
     reaches the live-shaped SessionStart entry-point
     (`emit_auto_upgrade_surface`) with NO pre-arranged trigger state;
     auto-detect fires, the wrapped replay runs the intermediates, the
     cursor reads the target, the seeded user-state survives intact, and
     the plain-language surface is EMITTED as the live additionalContext
     line. Drives the real session-start entry-point against a real stale
     instance — NOT a unit test of the trigger function
     (feedback_test_outcome_altitude_required). The live pos3 store is
     NEVER written (the FBM cold-walk discipline, plan §8.6).

Composes on (Lens 1, NO re-implementation): the SEALED migration engine
(`framework/state-migration-engine/` — `replay`, `enumerate_pending`,
`read_cursor`, `load_migration_dir`); the SEALED reversibility envelope
(`ReversibilityStore` + `MigrationSafetyEnvelope`); the live SessionStart
hook chain's fail-soft-contributor pattern (`pos_session_start.py` /
`session_surface.py` — KP7). The orchestrator pyproject gains
`loam-state-migration-engine` + `loam-reversibility-primitive` as runtime
deps so the composed import resolves in a real install.

OWNER-GATED, NOT in this amendment (plan §8.4): the LIVE SessionStart ARM.
`emit_auto_upgrade_surface` is the contributor entry-point the live
`pos_session_start.py:main()` wiring would call (one-line addition,
mirroring `_emit_keep_pace_surface`), but it is NOT wired into `main()`
here — flipping an always-on auto-upgrade that mutates user-state on every
session is owner-class runtime behaviour (the FBM / KP7 activation class).
The module is BUILT + PROVEN; the live wiring is surfaced for owner
sign-off, not flipped.

BASELINE 19a14b91 — HEAD of the plan/foundation-polish-auto-upgrade branch
(the pre-amendment tip); confirm at apply time. Counter 162 is the next
free slot; confirm at apply time. Single-component fence (orchestrator).
