# Plan — loam user-state migration engine + release-gate (slice P1.3)

**Status:** sub-plan-doc (PLAN ONLY — no implementation code authored) · **HALT for owner review before build.**
**Working directory:** `/Users/lukeivers/loam` (branch `slice/p1.2-loam-layout`, the carrier of the .loam layout + the FBM migration quartet).
**Parent plan:** `docs/plans/loam-vnext-build-plan.md` (Phase 1 kernel; P1.3 row §6, table line 120).
**Workflow:** `docs/plans/loam-vnext-build-workflow.md` (Step-5 INTEGRATE+RECORD authors the per-version migration; G4 ratifies the release-gate; G★ is the protection floor).
**Predecessors (load-bearing prior seals + artefacts):**
- P1.2 `.loam/` workspace layout — slice plan `docs/plans/loam-layout-slice-plan.md`; migration `docs/state-migrations/loam-layout-slice.migration.yaml`. Establishes `.loam/migrations/` (the applied-cursor home).
- P1.1 FBM-LIVE — established the live `.loam/memory/` episode store.
- The declared-migration CONTRACT home `docs/state-migrations/` (created this session; F2 corrective relocating P1.1's migration from gitignored `.loam/`).
- The migration quartet authored this session (the schema this plan formalizes): `loam-layout-slice`, `fbm-rank-normalize-slice`, `fbm-rule-weighting-slice`, `fbm-episode-salience-slice`, `fbm-spread-salience-gate-fix-slice`, `fbm-live-slice`.
- `framework/reversibility-primitive/` (sealed) — the activation-wrap / rollback envelope this engine composes ON (the safety wrapper; does NOT reinvent backup/rollback).
- `framework/tools/loam/src/loam_cli/release/gates.py` (sealed) — the seven-gate `loam release` framework the release-gate composes ON as gate #8 (does NOT add a separate CI).
**BASELINE candidate:** P1.2 seal `31dc9ca` (HEAD of `slice/p1.2-loam-layout`); confirm at build time against the actual predecessor seal-advance commit.
**Position-cursor target:** `docs/plans/build-cursor.md` (advance SLICE→P1.3 at Step-5).
**Quality bar:** outcome-altitude AC exercises a REAL separate instance at version N upgraded to N+k through intermediate migrations, verified at the true upgrade entry-point (this session's lesson — `feedback_test_outcome_altitude_required`).

---

## §1 Summary / TL;DR

**What ships:** the mechanism that AUTOMATES the manual care-flow we hand-cranked this session (backup → apply pending migrations in order → verify → roll back on failure → advance cursor) so a loam instance — including a non-technical user's — upgrades its `.loam/` user-state in place, safely and repeatably.

**Three parts, one slice (the parent plan bundles engine + gate — decision #3 fix 1, line 125):**
1. **The migration-file schema** — formalize the contract already emerging in `docs/state-migrations/*.migration.yaml` into a validated shape (declared-not-guessed; reversibility class; idempotency).
2. **The replay engine** — read the per-instance applied-cursor → enumerate pending declared migrations → apply IN ORDER (through intermediates, not jumping) → advance the cursor; the whole replay WRAPPED in the reversibility-primitive's backup-verify-rollback envelope.
3. **The release-gate** — gate #8 on the existing `loam release` gate framework (NOT a new GitHub Action) that REJECTS publishing a version lacking a declared migration file.

**AC families:** `AC.MIG-SCHEMA.*` (schema validation), `AC.MIG-REPLAY.*` (ordered cumulative replay + cursor advance), `AC.MIG-SAFE.*` (backup/verify/rollback envelope + idempotency + partial-failure), `AC.MIG-GATE.*` (release-gate rejects gate-less releases), `AC.MIG-UPGRADE.*` (★ outcome-altitude: real N→N+k upgrade at the true entry-point).

**Key decisions baked (confident, tight scope):** compose on `reversibility-primitive` for the envelope; compose on `loam release` gates for the gate; the declared-not-guessed migration file is the single source of truth; the per-instance cursor lives at `<workspace>/.loam/migrations/.cursor` (already decided by P1.2 + README); migrations replay in a total order through intermediates.

**Forks needing an owner ruling (low confidence — see §3):** (D1) cursor ORDERING key — monotonic-sequence file vs declared-predecessor DAG vs release-version order; (D2) declarative-steps vs embedded-scripts for the `during-update` step; (D3) gate STRICTNESS at pre-1.0 (hard-block vs warn-with-override); (D4) the engine's invocation surface (`loam migrate` verb vs folded into `loam onboard`/session-start auto-detect).

**F2 on scope realism:** this slice is scope-realistically a SINGLE dispatch IF the four forks are ruled before build — the engine is ~3 functions (read-cursor, enumerate-pending, apply-wrapped) composing two sealed primitives, plus one gate function mirroring the existing six. If the forks are left open, the builder will hit them mid-build and halt, costing a round-trip. Recommendation: rule D1–D4 at this review, then dispatch. Decomposition into sub-slices is NOT warranted (no sub-task has a tighter AC than the parent — Lens 5 stopping criterion).

---

## §2 Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| Migration-file schema (validator) | **Framework** — new module under `framework/` (builder picks the component home; `self-upgrade` is the WRONG home — see §10 F2 boundary). Its OUTPUT validates files in `docs/state-migrations/` (tracked contract). | The schema is framework code; the files it validates are the tracked framework-side contract (per `state-migrations/README.md` table). |
| Declared migration files (`*.migration.yaml`) | **Framework, tracked** — `docs/state-migrations/` (already there). | Identical for every user; ships + versions with loam. |
| The replay engine | **Framework** code; its EFFECT mutates user-state under `<workspace>/.loam/`. | Engine is framework; the cursor + the state it migrates are user-state. |
| The applied-migration cursor | **User-state, gitignored** — `<workspace>/.loam/migrations/.cursor`. | Per-instance record; P1.2 + `state-migrations/README.md` already locate it here; `.loam/` is gitignored (confirmed `.gitignore:56`). |
| The backup/rollback envelope | **Compose on `framework/reversibility-primitive/`** — do NOT author a new backup mechanism. | The activation-wrap + rollback lifecycle + idempotence + cascade-on-child-failure already exist + are sealed + tested. |
| The release-gate | **Compose on `framework/tools/loam/src/loam_cli/release/gates.py`** as gate #8 in `ALL_GATES` / `run_all`. | Leverage-loam-first: the seven-gate `loam release` framework IS the repo release-gate surface. There is NO `.github/workflows/` (verified). |

---

## §3 Halt-and-surface BEFORE build — the four forks (low confidence; owner rules)

Each carries my recommendation. **Recommendation IS the decision for confident items; these four are the genuine forks where reasonable people weigh signals differently, so they are surfaced (Lens 6 step 4).**

### D1 — Cursor ordering key: how does the engine know the total replay order?
- **Option A — monotonic sequence index.** Each migration gets an integer/ordinal sequence; cursor stores the last-applied ordinal; pending = all with ordinal > cursor. Simplest; total order is explicit. BUT versions are NOT pre-assigned (`feedback_version_numbers_at_release_time`), so the ordinal must be assigned at RELEASE time (a release-time stamp into the migration file), not authoring time.
- **Option B — declared-predecessor DAG.** The files already carry `predecessor:` (e.g. `fbm-episode-salience-slice` → `fbm-rule-weighting-slice`). Topological-sort the DAG; cursor stores the set/frontier of applied slugs; pending = unreachable-from-cursor. No release-time stamp needed; uses what's already declared. BUT the current `predecessor:` is single-valued + sometimes names the "safety-pair" not the strict prior, so the existing chain is NOT a clean total order (e.g. `fbm-rule-weighting` → `fbm-rank-normalize`, but `loam-layout` declares no predecessor).
- **Option C — release-version order.** At release time the migration is stamped with the resolved version; replay in SemVer order. Aligns with how `loam release` already resolves versions.
- **★ Recommendation: C, with the version stamped at release time by the release-gate itself** (the gate already runs at release, already knows the version). The cursor stores the last-applied resolved version. This reuses the existing version-resolution machinery, needs no new authoring-time discipline, and gives an unambiguous total order. `predecessor:` stays as human-readable provenance, NOT the replay key. **Signals:** reversibility (C is append-only + auditable), information-asymmetry (the release-gate already holds the version — lowest new surface), blast-radius (a wrong order corrupts user-state — favors the most-auditable key). Owner rules; B is the fallback if we want zero release-time coupling.

### D2 — `during-update` step: declarative operations vs embedded scripts?
- The current files are PURELY DECLARATIVE (`operation: no-op | structural-only | schema-add-forward-additive`; `creates:`/`leaves_in_place:` path lists; prose `rationale:`). None embeds an executable step — because every migration so far has been no-op / structural-only / forward-additive (the engine does nothing destructive; new fields appear lazily on new writes).
- **Option A — keep it declarative-only**: the engine interprets a fixed vocabulary of operation types (`no-op`, `structural-only`, `create-paths`, `schema-add-forward-additive`, …). A migration that needs real transformation is REJECTED until the vocabulary is extended (forces every transform through a reviewed, named operation type — the protection floor likes this).
- **Option B — allow an embedded/ referenced script** for the `during-update` step (a path to a migration script the engine invokes inside the envelope).
- **★ Recommendation: A — declarative-only for THIS slice, with an explicit out-of-scope note that the transform-script operation type is a LATER slice when a real transform first needs it (YAGNI + protection floor).** Every migration authored to date is expressible declaratively; adding a script-exec path now is speculative surface that widens the blast radius before any migration needs it. **Signals:** scope↔confidence (high confidence the declarative set covers current need — tighten), blast-radius (an exec path is the highest-risk surface — defer until a real driver), reversibility (declarative ops are trivially classifiable for the envelope; arbitrary scripts are not). Owner rules; if a near-term migration is known to need a transform, switch to B now.

### D3 — Release-gate strictness pre-1.0: hard-block vs warn-with-override?
- The parent plan is unambiguous that the gate is NON-OPTIONAL (line 125: "the gate is what makes the mechanism load-bearing"; §10 risk 3: it is the structural answer to the lapsed-re-eval failure). The fork is only the pre-1.0 SHAPE.
- **Option A — hard-block always**: `loam release` returns RED if no migration file matches the version; publish cannot proceed. Mirrors the existing six gates (all hard).
- **Option B — hard-block with a named, logged `--allow-missing-migration` override** for genuine emergencies, the override recorded in the release notes.
- **★ Recommendation: A — hard-block, no override.** The entire POINT of the gate is to defeat "someone forgot" (the lapsed-re-eval shape, §10 parent). An override is exactly the escape hatch that lets the failure mode back in; and "no-op" is already a valid one-line declared migration, so the gate is never genuinely blocking — declaring a no-op is ~30 seconds. The cost of compliance is near-zero, so the override has no real justification. **Signals:** the parent plan's locked intent (the gate must be load-bearing), blast-radius (a skipped migration = a silently un-upgradeable user instance downstream), cost-of-compliance (near-zero — no-op is trivial). Owner rules; B is the fallback only if there's a concrete emergency-publish scenario the owner foresees.

### D4 — Engine invocation surface: where does the upgrade get triggered?
- **Option A — a `loam migrate` CLI verb** the user (or the persona) runs explicitly.
- **Option B — auto-detect at session-start / onboard**: a hook reads the cursor, notices pending migrations, and runs the wrapped replay (surfacing what it did in plain language — non-tech-safe).
- **Option C — both**: the `loam migrate` verb is the engine; a thin session-start check INVOKES it when the cursor is behind (the non-tech path) while the verb stays available for explicit/manual runs.
- **★ Recommendation: C, but build only the `loam migrate` verb in THIS slice and declare the auto-detect hook a fast-follow.** The verb is the testable entry-point the outcome-altitude AC needs (a real entry-point, per today's lesson). The auto-detect hook is a thin consumer of the verb and depends on the live session-start chain (shared with P1.1/P1.5's activation) — folding it in here couples this slice to an owner-class activation flip. Keep the slice's fence on the verb; name the auto-detect as the immediate next step. **Signals:** scope↔confidence (the verb is high-confidence + independently testable; the hook depends on a separate activation — looser), non-tech-safety (the auto-detect is what makes it non-tech-runnable — but it composes cleanly on the verb later, no rework). Owner rules whether the auto-detect rides in this slice or fast-follows.

---

## §4 Spec-objective placement

- Binds to parent plan §6 P1.3 (line 120) + the parent's Phase-1 kernel objective: "the minimum to initialize, onboard, and hold state across sessions … the versioned user-state migration system + its release-gate" (parent §1, line 26).
- Ladders up to the prime objective `docs/VALUE_PROPOSITION.md` AC.PO.1/AC.PO.2 via: a user's accumulated state (profile, rules, content, objectives) is "carried forward across upgrades; never replaced, only migrated" (parent §2, line 55) — i.e. the engine is what makes loam's per-user-tuned state SURVIVE a version bump, which is the precondition for the prime directive's continuous-learning loop (`feedback_loam_prime_directive_user_tuned_translation`).

---

## §5 Acceptance criteria

AC IDs are scope-descriptive (`feedback_scope_descriptive_ac_ids`), not version-packed. Each is outcome-shape; method-in-AC test stated per family. **Method-in-AC test passed:** every AC below can be satisfied by a method other than the one I have in mind (the builder may structure the modules, the cursor file format, and the envelope wiring differently) — so they pin OUTCOME, not method.

### AC.MIG-SCHEMA.* — the declared migration contract is validated, not guessed
- **AC.MIG-SCHEMA.1** — A migration file missing a required field (slug / operation / reversibility class) is REJECTED by the validator with a specific corrective message; a well-formed file PASSES. *(Outcome: malformed contract cannot enter the replay set.)*
- **AC.MIG-SCHEMA.2** — Every existing file in `docs/state-migrations/` (the quartet + layout + live) VALIDATES under the formalized schema. *(Outcome: the formalization is faithful to what's already authored — no retro-breakage.)*
- **AC.MIG-SCHEMA.3 (declared-not-guessed)** — The validator + engine derive the migration's effect SOLELY from the declared file; given two code-diffs with an identical declared migration, the engine's planned actions are identical. *(Outcome: effect is declared, never inferred from a diff/change-type — the owner's locked design.)*

### AC.MIG-REPLAY.* — ordered cumulative replay through intermediates + cursor advance
- **AC.MIG-REPLAY.1** — Given a cursor at version N and declared migrations for N+1…N+k, the engine enumerates EXACTLY the pending set (none already-applied, none beyond target) in a deterministic total order. *(Outcome: pending-set + order are correct + reproducible.)*
- **AC.MIG-REPLAY.2 (through-not-jump)** — Upgrading N→N+k applies every intermediate migration in order, NOT only the target's. *(Outcome: plays THROUGH intermediates — the owner's locked design.)*
- **AC.MIG-REPLAY.3 (cursor advance)** — After a successful replay the cursor reads N+k; re-running is a clean no-op (no migration re-applied). *(Outcome: cursor is the authoritative applied-record + idempotent.)*

### AC.MIG-SAFE.* — the safety envelope (backup / verify / roll back / idempotent / partial-failure)
- **AC.MIG-SAFE.1 (backup-first)** — Before any migration mutates user-state, a recoverable backup of the affected `.loam/` state exists. *(Outcome: the careful-activation backup-first property — generalizes the manual flow.)*
- **AC.MIG-SAFE.2 (rollback-on-failure)** — If a migration in the chain FAILS, the engine rolls user-state back to the pre-replay snapshot AND the cursor is NOT advanced past the last-good migration. *(Outcome: a failed upgrade leaves a consistent, recoverable instance — non-tech-safe; no half-migrated state.)*
- **AC.MIG-SAFE.3 (idempotent / re-runnable)** — Re-running an already-applied migration (or a replay interrupted + restarted) does not double-apply or corrupt state. *(Outcome: safe to re-run — the manual flow's repeatability.)*
- **AC.MIG-SAFE.4 (protection-floor classification)** — A migration declaring it removes/compresses/overwrites user-state is classified by the reversibility envelope and refused-or-gated per the protection floor (G★) unless its reversibility binding/approval is satisfied. *(Outcome: surface-don't-delete — composes the sealed reversibility-primitive's R-class gate, not a new rule.)*

### AC.MIG-GATE.* — the release-gate rejects gate-less releases
- **AC.MIG-GATE.1** — `loam release <version>` (or `--dry-run`) returns RED when no declared migration matches the version, with a specific corrective hint; GREEN when one exists. *(Outcome: a version cannot publish without declaring its migration — the load-bearing gate.)*
- **AC.MIG-GATE.2 (no-op is valid)** — A version whose declared migration is `operation: no-op` PASSES the gate. *(Outcome: the gate forces a DECLARATION, not a non-trivial migration — "no-op" is a valid declared answer.)*
- **AC.MIG-GATE.3 (composes on the existing gate set)** — The release-gate runs as part of the SAME `loam release` gate pass as the existing gates, in one report, no short-circuit. *(Outcome: leverage-loam-first — one gate framework, not a parallel CI.)*

### ★ AC.MIG-UPGRADE.* — outcome-altitude: a REAL N→N+k upgrade at the true entry-point
- **AC.MIG-UPGRADE.1 (outcome-altitude: true)** — A genuinely SEPARATE instance (a temp `.loam/` workspace seeded at a real prior cursor version, with real seeded user-state) is upgraded to a later version by invoking the REAL upgrade entry-point (the `loam migrate` verb, no pre-arranged internal state), replaying the intermediate migrations in order; afterward the cursor reads the target version, the seeded user-state survives intact, and the live store is observably consistent. **This AC may NOT be satisfied by a unit test of the replay function in isolation** — it must drive the production entry-point against a real instance. *(This is today's lesson: ACs hit the real entry-point, not just the inner function. `feedback_test_outcome_altitude_required`.)*

**AC ladder-up:** every AC → the parent P1.3 outcome (versioned migration system + load-bearing gate) → parent Phase-1 kernel objective (hold state across upgrades) → AC.PO.1/AC.PO.2 (per-user state survives, the prime directive's precondition).

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

Per-cycle shape; the builder owns the actual module decomposition.
1. **Manifest** at `docs/plans/loam-migration-engine-and-release-gate-slice.manifest.yaml` — `schema_version: 1`; `amendment` block (number = next global counter, confirm at build); `baseline:` = the confirmed P1.2 seal; `components:` naming the framework home the builder selects for the engine + the `loam_cli/release` component for the gate; `universal_paths:` for `docs/state-migrations/` + `docs/plans/`; `narrative.target: docs/plans/sealed/loam-migration-engine-and-release-gate-slice.md`.
2. **EXAMINE** (Step-1): read the reversibility-primitive public surface (`activation_gate.py`, `rollback.py`, `controller.py`, `spec.py`) + `loam_cli/release/gates.py` `ALL_GATES`/`run_all` to confirm the composition points before writing.
3. **DEFINE** the schema as a validator over the EXISTING files (AC.MIG-SCHEMA.2 forces fidelity to the quartet).
4. **BUILD** the replay engine composing the reversibility envelope; author the gate as a new entry in `ALL_GATES` + `run_all`.
5. **PROVE** every AC; the outcome-altitude AC drives the real `loam migrate` entry-point against a temp seeded instance.
6. **Tests** authored per-AC, ID-named (`test_AC_MIG_*`), under the chosen component's `tests/`.
7. **Apply + seal** via `loam amend apply` + `loam amend seal` (sealed-component dispatch — name `loam amend apply` explicitly, `feedback_dispatch_explicit_loam_amend_apply`); NEW corrective commits if a file is missed, never `--amend`.
8. **INTEGRATE+RECORD** (Step-5): author THIS slice's own declared migration file in `docs/state-migrations/` (the engine slice itself declares a migration — likely `structural-only`: it creates the `.cursor`); advance `docs/plans/build-cursor.md` to P1.3-complete + name P1.4 next.
9. **Smoke:** the outcome-altitude real-upgrade walk IS the smoke for this slice.

---

## §7 Out of scope (deferred + when)

1. **The `during-update` transform-script operation type** (D2 option B) — deferred until a real migration first needs a non-declarative transform. Add the operation type to the vocabulary then, behind the same envelope.
2. **The session-start / onboard auto-detect hook** (D4 option B) — fast-follow; depends on the live session-start activation chain (shared with P1.1/P1.5). The `loam migrate` verb this slice ships is its dependency.
3. **Carry-forward / selective-migration manifest** (parent P3.3, gate G6) — Phase 3; a different, destructive-by-omission concern governed by its own owner gate.
4. **Any reuse of `framework/self-upgrade/` for user-state** — explicitly OUT (boundary leak; see §10). `self-upgrade` migrates the framework CODEBASE; this engine migrates USER-STATE. They sit on opposite sides of the §2-F2 boundary.
5. **The persisted position-cursor mechanism (P2.3)** — distinct from the migration applied-cursor; not this slice.

---

## §8 Halt triggers (in-flight conditions that abort the build)

1. **A fork (D1–D4) is unresolved at build time** — if the dispatch arrives without a ruling on the four forks, HALT and surface rather than guessing the replay-order key or the gate strictness (guessing the order key risks corrupting user-state).
2. **The reversibility-primitive's public surface does not expose a usable backup/rollback-wrap entry-point** — if EXAMINE finds the envelope cannot be composed as a library call, HALT and surface (do NOT author a parallel backup mechanism — that's the boundary leak the parent plan warns against, §10 risk 2).
3. **An existing migration file FAILS the formalized schema** (AC.MIG-SCHEMA.2) — HALT; the formalization is wrong, not the file. Tighten the schema, not the file (`feedback_loose_AC_text_fix_AC_not_implementation` analog).
4. **The gate would touch a sealed component without a manifest entry** — if adding gate #8 to `loam_cli/release` requires edits outside the declared fence, HALT and surface rather than silently widening.
5. **Any step would remove/compress/overwrite live user-state** — G★ standing gate; surface-before-cut, reversible, dependency-checked. The live pos3 store (1288+ episodes) is READ-ONLY-copied into a temp root for the outcome-altitude AC, NEVER written (the same discipline the FBM cold-walk used).

---

## §9 Bookkeeping

1. **`docs/plans/build-cursor.md`** — advance SLICE→P1.3 (Step-5 complete), NEXT→P1.4 onboarding/init.
2. **Parent plan `docs/plans/loam-vnext-build-plan.md`** — P1.3 row marked built; the §4 hidden-dependency fix-1 (gate bundled with engine) confirmed satisfied.
3. **`docs/state-migrations/`** — THIS slice's own declared migration file (structural-only: creates the `.cursor`).
4. **STATE.md / release-roadmap.md** — vnext slices are tracked via the build-cursor, not version rows (versions derive at release time); no row backfill needed UNLESS this slice is bundled into a published version, at which point the release-gate stamps it.
5. **Plan §14 register** — populated by the builder at build time with the D-decisions actually taken + SHAs backfilled at seal.

---

## §10 F2 Ruthless Feedback (honest doubts; named design risks)

1. **The two-migration-systems boundary is the #1 risk and it is EASY to leak.** `framework/self-upgrade/` already exists and already has the word "migration" in it; a builder who greps "migration" will find it and may try to reuse it. **Evidence:** parent plan §10 risk 2 (line 216) names this exact leak; `framework/self-upgrade/` is a real sealed component (`framework/self-upgrade/src` present). **Alternative/mitigation:** §7 item 4 + halt-trigger 2 name the boundary explicitly; the engine composes `reversibility-primitive` (the safety envelope) NOT `self-upgrade` (the framework-codebase migrator). The dispatch brief must carry this boundary as a named constraint.

2. **The existing `predecessor:` field is NOT a clean total order — do not assume it is the replay key.** **Evidence:** `loam-layout-slice.migration.yaml` declares NO predecessor; `fbm-rule-weighting-slice` declares its predecessor as `fbm-rank-normalize-slice` (a "safety-pair", which is a semantic relation, not strictly "the migration applied just before me"). Building the replay order off `predecessor:` (D1 option B) would mis-order. **Alternative:** D1 recommendation C (release-version order) sidesteps this; `predecessor:` stays as human provenance only. This is WHY D1 is a surfaced fork and not an autonomous call.

3. **"No-op makes the gate cheap" is the gate's strength AND a soft hole.** Because declaring `no-op` satisfies the gate in ~30s, the gate cannot distinguish "genuinely no user-state change" from "author was lazy and declared no-op without thinking." **Evidence:** four of the six existing migrations are `no-op` or `structural-only`. **Alternative:** this is acceptable for THIS slice (the gate's job is to force a DECLARATION + a moment's thought, not to verify the declaration's truthfulness); a later slice could add a declared-vs-actual-diff cross-check. Named here so it is not mistaken for a gap this slice must close.

4. **Outcome-altitude AC cost is real.** AC.MIG-UPGRADE.1 requires seeding a real prior-version instance with real state and driving the actual verb — heavier than a unit test. **Evidence:** today's manual flow took backup→swap→apply→reindex→smoke→rollback by hand. **Alternative:** none — this cost IS the lesson (`feedback_test_outcome_altitude_required`); a STUB-class test does not satisfy an outcome-altitude AC. The plan keeps it as the single outcome-altitude AC + the slice smoke (no duplicate heavy walks).

---

## §11 Provenance trail (load-bearing sources)

- Parent plan P1.3 definition + the engine⊕gate bundling + the two-migration boundary + the lapsed-re-eval framing: `docs/plans/loam-vnext-build-plan.md` lines 26, 55, 85, 120, 125, 216, 218.
- Workflow Step-5 (author the migration file) + G4 (release-gate ratification) + G★ (protection floor): `docs/plans/loam-vnext-build-workflow.md` lines 71, 75, 142–151.
- Migration-file emerging schema (the fields this plan formalizes): `docs/state-migrations/README.md` + the six `*.migration.yaml` files (esp. `fbm-episode-salience-slice` for `operation`/`reversible`/`removes_user_state`/`idempotent`/boundary-note, and `loam-layout-slice` for `structural-only`/`creates`/`leaves_in_place`).
- Cursor home + framework↔user-state boundary table: `docs/state-migrations/README.md` lines 14–21; `.loam/build-cursor.md` (the MOVED note); `docs/plans/build-cursor.md`.
- The safety envelope to compose ON: `framework/reversibility-primitive/src/loam/reversibility_primitive/` (`activation_gate.py`, `rollback.py`, `controller.py`, `spec.py`) + tests `test_activation_wrap_gates.py` (R6–R12 reversibility classes), `test_rollback_lifecycle.py`, `test_rollback_idempotence.py`, `test_cascade_on_child_failure.py`.
- The release-gate framework to compose ON (Lens 1): `framework/tools/loam/src/loam_cli/release/gates.py` (`ALL_GATES` tuple line 635, `run_all` line ~650); `docs/release-process.md` §1 (the seven structural gates; `loam release` verb; NO `.github/workflows/` exists — verified).
- AC-ID + plan-doc shape conventions: `plugins/dev-sdlc/docs/conventions/plan-docs.md`.
- The outcome-altitude lesson: `feedback_test_outcome_altitude_required` + this session's manual FBM activation (`docs/plans/fbm-live-slice-plan.md` §13 backup-first activation).
</content>
</invoke>
