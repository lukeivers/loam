# loam user-state migration engine + release-gate (slice P1.3) — apply ladder

2026-05-31. Phase-1 kernel slice P1.3 per
`docs/plans/loam-migration-engine-and-release-gate-slice-plan.md`.
Builds the mechanism that AUTOMATES the manual care-flow (backup →
apply pending migrations in order → verify → roll back on failure →
advance cursor) so a loam instance — including a non-technical
user's — upgrades its `.loam/` user-state in place, safely and
repeatably.

Four parts, one slice:
  1. The declared-migration SCHEMA + validator — formalizes the
     contract already emerging in `docs/state-migrations/*.migration.yaml`
     (the FBM quartet + layout + live). All six existing files validate
     UNCHANGED; no schema adjustment was forced.
  2. The REPLAY engine — read the per-instance applied cursor
     (`.loam/migrations/.cursor`) → enumerate pending in release-version
     order (D1) → apply declarative steps IN ORDER through intermediates
     (D2 declarative-only; no embedded scripts) → advance the cursor;
     the whole replay WRAPPED in the reversibility-primitive safety
     envelope (backup-first / protection-floor gate / rollback-on-failure)
     composed as a LIBRARY CALL (ActivationGate + ReversibilityStore +
     ReversibilityClass — not a parallel backup mechanism).
  3. The `loam migrate` CLI verb (D4) — the real, testable entry-point;
     the session-start auto-detect hook is a fast-follow, OUT of fence.
  4. The release-gate — the 7th gate in loam_cli/release ALL_GATES
     (D3 hard-block, no override; a no-op declaration is valid).

AC families: AC.MIG-SCHEMA.* (validated, declared-not-guessed),
AC.MIG-REPLAY.* (ordered through-not-jump replay + cursor advance),
AC.MIG-SAFE.* (backup-first / rollback-on-failure / idempotent /
protection-floor classification), AC.MIG-GATE.* (rejects gate-less
release, no-op valid, composes in the existing gate set), and the
★ outcome-altitude AC.MIG-UPGRADE.1 (a SEPARATE seeded instance at
version N upgraded to N+k by driving the REAL `loam migrate` verb
through the unified CLI dispatcher — not the inner replay function).

BOUNDARY (plan §2 / §10): this migrates USER-STATE.
`framework/self-upgrade/` migrates the framework CODEBASE — a different,
non-conflated concern reusing NONE of it.

BASELINE 31dc9ca — HEAD of slice/p1.2-loam-layout. Two-component fence:
the new `state-migration-engine` + the `loam-cli` release-gate surface.
