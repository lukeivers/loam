# N1 — framework ↔ user-state boundary LOCK (ADR + enforcement gate)

**Status:** sub-plan-doc, PLAN-ONLY (plan-before-code). Authored 2026-05-31.
**Working directory:** `/Users/lukeivers/loam/`.
**Parent plans:**
- `docs/plans/loam-roadmap.md` §4 row **N1** (critical-path head; unblocks N3 onboarding).
- `docs/plans/loam-vnext-build-plan.md` §2 (the boundary architecture) + §Phase-0 **F0.2** (lock-the-boundary step) + §Phase-1 **P1.2** (the scaffold, already built).

**Predecessors (load-bearing prior seals + artefacts, Tier-0 on disk 2026-05-31):**
- `01f3b40` — **P1.2 the scaffold (already done)**: `establish_loam_layout()`, the declared `.loam/` dirs, the self-describing README carrying the boundary-rule prose, and `docs/state-migrations/` as the tracked framework-side migration-contract home. N1 does NOT re-scaffold any of this.
- `58bead7` / `c08cbcb` / `6587e94` — the user-state migration **engine + 7th release-gate** (`check_migration_declared` in `ALL_GATES`). This is the **composition target** for N1's enforcement (a parallel 8th gate of the same shape).
- `3ac70a7` — v0.14.0 release-integration merged to `main` (the BASELINE tree N1 evolves in place).

**BASELINE (pre-build tip):** `ea2f3a0` (current `main` HEAD; carries FBM-live + migration-engine + the in-progress audit work).
**Status-file target:** `<workspace>/.scratch/claude-output/n1-boundary-lock-status.md` (builder writes build progress here).
**Quality bar:** the boundary is LOCKED — written as an ADR a later kernel author reads first, AND a real boundary violation (framework code writing user-state outside the homes) is **CAUGHT at the real release entry-point**, not merely catchable by a unit test of an inner function.

**Scope-tightness (F4):** TIGHT where practice settled it (repo shape, two-tier home, evolve-in-place — all ratified by G2 / by what landed today); FORKED-with-recommendation where genuinely uncertain (enforcement entry-point choice; path-side declaration mechanism). Method stays the builder's call.

---

## §1. Summary / TL;DR

N1 ships the **LOCK** on the framework ↔ user-state boundary — the seam every later kernel piece (N3 onboarding, N4 user-model, Phase-3 migrate) reads and writes through. P1.2 already built the *scaffold* (the `.loam/` dirs + the boundary-rule prose in the README). N1 adds the two things the scaffold does not give: a **durable architectural decision record** so the boundary is a citable contract rather than a docstring, and a **structural enforcement check** so a framework-code path that writes user-state outside the two homes is CAUGHT rather than silently leaking.

Two AC families:

- **AC.BLOCK-ADR.\*** — the ADR exists at a durable, conventional home; names the two sides (framework vs user-state), the two-tier physical home (`~/.claude/` global + `<ws>/.loam/` scoped), the evolve-in-place repo shape, the seam contract (framework replaced wholesale / user-state migrated never overwritten), and **how a component declares which side a path is on**.
- **AC.BLOCK-ENFORCE.\*** — a boundary-violation check, composed on the **existing release-gate `ALL_GATES` framework** (an 8th gate, twin of gate 7 `check_migration_declared`), that goes RED when framework code writes user-state outside the homes. Includes the ★ **outcome-altitude** AC: a *planted real violation* is caught at the real `loam release` gate entry-point.

**Key decisions baked (settled by practice — not re-opened):**
1. **Repo shape = evolve-in-place on the existing canonical tree.** Today's v-next work (migration-engine, the audit subpackage, keep-pace) all landed inside `framework/` on `main`. G2 ratified this. (Supersedes the v-next-build-plan §3 decision-#1 *recommendation* of "a clean new tree" — see §10 F2 #1: the plan recommended a clean tree; practice chose evolve-in-place, and the ADR records the decision that was actually made.)
2. **User-state home = two-tier, already live.** Global → `~/.claude/`; workspace-scoped → `<ws>/.loam/` (gitignored at `.gitignore:56`/`:59`). The FBM store + the migration cursor already live here.

**F2 on scope realism:** N1 is M-sized (1 doc + 1 gate function + its test pair + the `ALL_GATES` wiring) — NOT the M–L the roadmap N1 cell estimates, because the roadmap cell still bundles "scaffold the `.loam/` dir" into N1, which P1.2 already shipped. The real remaining N1 is the LOCK only. The roadmap N1 cell and the v-next-plan P1.2 row should both be re-marked to reflect that the scaffold is DONE and N1 = ADR + enforcement (§9 bookkeeping).

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| The boundary ADR | `docs/design/adr/boundary-framework-vs-user-state.md` (NEW `adr/` subdir under the existing `docs/design/` design-doc home) | `docs/design/` is loam's settled design-doc home (doctrine, AIM, memory-architecture all live there). No `adr/` convention exists yet — N1 establishes it (a numbered/named ADR home a later kernel author cites). **Fork D-1 below offers the alternative of a flat `docs/design/` file with no `adr/` subdir.** |
| The boundary-violation enforcement check | `framework/tools/loam/src/loam_cli/release/gates.py` (an 8th `check_*` gate in `ALL_GATES`) | Lens 1 + Lens-loam: the release-gate framework is the *proven, committed* enforcement spine (7 gates, runs as one report, HARD-BLOCK precedent at gate 7). A boundary violation is exactly the class "a release must not ship a leak." Composing here reuses `GateResult` / `run_all` / `format_report` / the corrective-hint convention — zero new machinery. |
| The gate's test pair (1 passing, 1 failing-on-planted-violation) | `framework/tools/loam/tests/test_AC_BLOCK_ENFORCE_*.py` | Co-located with the existing per-gate test pairs (`test_AC_V060_2_*`, `test_AC_MIG_GATE_*`). |
| The "which side is this path on" declaration mechanism | Decided in the ADR; **enforced** by the gate reading it (see Fork D-2) | The declaration is *contract* (ADR-side, framework-tracked); the check *reads* the declaration. Keeps declaration and enforcement on the same side of the seam they describe. |

---

## §3. Halt-and-surface BEFORE build (decisions recorded at plan-time)

### Surface #1 (no halt — recorded; the boundary classification rule)

**Decision (autonomous, settled by P1.2's README prose + the §2 of the v-next plan):** the boundary classifies by **what a path is ABOUT**, not by what writes it. Framework code routinely *writes* user-state (that is its job — `establish_loam_layout` is framework code whose output is user-state; so is `gates.py`, `cost-governance`, the hands-off-lifecycle hooks). So the enforcement check does NOT ban framework→user-state writes. It bans framework→user-state writes **landing outside the two declared homes**. Classification:

- **Framework** = loam's own machinery: everything under `framework/` and `plugins/`, the doctrine, the methodology, the migration *engine*. Versioned with loam; identical for every user; replaced wholesale on upgrade.
- **User-state** = everything *about this user and their work*: profile / interaction-model, rules / preferences, content, objectives + work-state, the FBM episode store, AND the migration **cursor**. Unique per user; migrated never overwritten.
- **The two homes** (the ONLY legal physical homes for user-state): `~/.claude/` (global, cross-workspace) and `<workspace>/.loam/` (workspace-scoped). A framework-code write of user-state to anywhere else is the violation the gate catches.

### Surface #2 (no halt — recorded; the enforcement is detection-not-prevention at N1)

**Decision (autonomous):** N1's enforcement is a **release-gate detection** (a violation is CAUGHT before publish), NOT a runtime PreToolUse/PreWrite *prevention* hook. Rationale (M5 signals): the structural-enforcement memory says "a rule violated >once → a hook." The boundary rule has not yet been violated even once (it is brand new); a release-gate is the proportionate first enforcement (matches gate 7's precedent exactly — declare-and-check, not runtime-block). A runtime PreWrite guard is the correct *escalation* IF a real violation slips a release; it is named in §7 (out of scope, deferred) and §5's AC.BLOCK-ENFORCE.4 records the gate as the FIRST line, not the only conceivable one.

### Surface #3 (HALT-WORTHY but RESOLVED — the §10 F2 #1 contradiction: clean-tree vs evolve-in-place)

**The contradiction:** `loam-vnext-build-plan.md` §3 decision-#1 *recommends* "(a) a clean new structure inside the canonical loam repo … the new kernel is clean (its own tree) … the old `framework/` stays intact as fallback." But what actually happened today is **evolve-in-place**: migration-engine, the audit subpackage, keep-pace all landed *inside* the existing `framework/` on `main` — no new `kernel/` tree. **G2 ratifies evolve-in-place.** This is the locked-design-is-not-license case in reverse: practice chose differently than the plan recommended, and that practice IS the ratified decision.

**Resolution (NOT a re-open — the dispatch instructs G2 is ratified):** the ADR records the decision that was *actually made and ratified by practice* — evolve-in-place — and notes that the v-next-plan §3 recommendation of a separate clean tree was superseded by G2. The ADR is the durable record of the real decision; the v-next-plan §3 decision-#1 text gets a dated-and-superseded note (§9 bookkeeping). **I surface this in the final report as a named decision** because a reader of the v-next plan would otherwise believe a clean tree is coming.

### Surface #4 (no halt — recorded; the audit subpackage is NOT a composition target)

**Decision (autonomous, Tier-0 verified):** `git ls-files framework/tools/loam/src/loam_cli/audit/` returns **empty** — the audit subpackage `.py` sources are NOT committed (only stale `.pyc` on disk). The dispatch's framing ("the loam_cli audit subpackage … rolled forward on main") is therefore not yet true on the ref graph. **The enforcement composes on the committed release-gate `ALL_GATES`, NOT on the uncommitted audit subpackage.** Flagged in §10 F2 #2.

---

## §4. Spec-objective placement

**Binds to:**
- **The prime directive — per-user-tuned translation + protection** (`docs/design/loam-doctrine.md`; `feedback_loam_prime_directive_user_tuned_translation`). The boundary is the *protection* leg's load-bearing seam: it is what makes "framework replaced wholesale, user-state migrated never overwritten" enforceable, which is what contains blast radius (a framework change cannot corrupt user-state; a prune of framework cruft cannot delete user content).
- **v-next-build-plan §2** (the boundary architecture) + **F0.2** (the lock step) + **P1.2** (the scaffold this builds the lock onto).
- **roadmap §4 N1** (critical-path head).

**Ladders up:** AC.BLOCK-ADR.\* + AC.BLOCK-ENFORCE.\* → N1 (boundary locked) → N3 onboarding + N4 user-model + Phase-3 migrate (all read/write user-state THROUGH this locked seam) → the prime directive's protection leg.

---

## §5. Acceptance criteria

> ODD note: every AC below is **outcome-shape** — it states the observable outcome, not the method. Method-in-AC test applied to each: the AC can be satisfied by a method other than the one the author has in mind (e.g. the gate could read a manifest, or hardcode the homes, or shell out — the AC pins the *caught violation*, not the *how*).

### AC.BLOCK-ADR.\* family — the boundary as a durable, citable contract

- **AC.BLOCK-ADR.1 (the ADR exists at a durable home).** A design-doc exists at a stable, conventional path under `docs/design/` that a later kernel author finds by convention (not by archaeology). It is tracked (committed), not a docstring or a `.scratch/` note. *Verified by:* the file exists at the home §2 names and is in `git ls-files`.
- **AC.BLOCK-ADR.2 (it names the two sides + the two-tier home).** The ADR states, unambiguously: what is framework vs user-state; that user-state's ONLY two physical homes are `~/.claude/` (global) and `<ws>/.loam/` (scoped); and that the classification is by *what the path is about*, not by *what writes it* (Surface #1). *Verified by:* a reader can answer "is path X framework or user-state, and where may it legally live" from the ADR alone.
- **AC.BLOCK-ADR.3 (it records the seam contract + the ratified repo shape).** The ADR states the upgrade contract (framework replaced wholesale; user-state migrated never overwritten) AND records evolve-in-place as the G2-ratified repo shape, noting the v-next-plan §3 clean-tree recommendation was superseded (Surface #3). *Verified by:* both the contract and the superseded-recommendation note are present and dated.
- **AC.BLOCK-ADR.4 (it names how a component declares which side a path is on).** The ADR specifies the declaration mechanism (per Fork D-2) so a component author and the enforcement check share ONE source of truth for "this path is user-state / this path is framework." *Verified by:* the declaration mechanism is written such that the AC.BLOCK-ENFORCE gate reads the SAME declaration the ADR describes (no second, divergent rule).

### AC.BLOCK-ENFORCE.\* family — the boundary holds, structurally

- **AC.BLOCK-ENFORCE.1 (the check exists in the release-gate spine).** A boundary-violation check is a member of `ALL_GATES` in `gates.py`, returns a `GateResult` with a corrective hint on RED, and runs in the SAME `loam release` pass as the other gates (one report, no parallel CI) — the gate-7 shape. *Verified by:* the gate is in the `ALL_GATES` tuple and `run_all` invokes it.
- **AC.BLOCK-ENFORCE.2 (clean tree is GREEN, no false-positive on legitimate writes).** On a repo where framework code writes user-state ONLY to the two declared homes (the real current state — `establish_loam_layout`, `gates.py`, cost-governance all write to `.loam/` or `~/.claude/` legitimately), the gate is GREEN. *Verified by:* the passing test of the pair runs the gate against the real (or a fixture-real) tree and asserts GREEN — the legitimate framework→user-state writes do NOT trip it.
- **★ AC.BLOCK-ENFORCE.3 (OUTCOME-ALTITUDE — a planted real violation is CAUGHT at the real entry-point).** A real boundary violation is planted — framework code that writes user-state to a path OUTSIDE the two homes (e.g. a framework module that writes a per-user file under `framework/` or under a cwd-relative junk path) — and the **`loam release` gate pass goes RED on it**, with a corrective hint naming the offending path and the legal homes. This is verified by invoking the **real release gate entry-point** (`run_all` / the `loam release` gate flow) against a tree carrying the planted violation, with NO pre-arranged in-memory state — the cold-walk / real-entry-point standard. A STUB-class unit test of an inner classifier function does NOT satisfy this AC; the lesson is "the violation is caught at the lesson, not in a unit test." *Verified by:* the failing test of the pair plants the violation, runs the real gate flow, asserts RED + the hint identifies the path.
  - **`outcome-altitude: true`** (per `feedback_test_outcome_altitude_required` — this AC invokes the production entry-point with no pre-seeded state).
- **AC.BLOCK-ENFORCE.4 (the gate reads the ADR's declaration, not a divergent second rule).** The set of legal homes + the classification the gate enforces is sourced from the SAME declaration the ADR (AC.BLOCK-ADR.4) describes — there is ONE boundary rule, not a doc-rule and a code-rule that can drift. *Verified by:* the gate's notion of "legal home" traces to the declaration mechanism Fork D-2 picks; changing the declaration changes both the doc and the check.

---

## §6. Build steps (method-level guidance only — builder's call per ODD §1.1)

> The builder owns method. This is sequence + the bookkeeping mechanism, not file-by-file prescription.

**This is a single cycle (no serialization needed — one doc + one gate + its test pair, one fence).**

1. **Author the ADR** at the §2 home (per Fork D-1 ruling). Cover AC.BLOCK-ADR.1–4. Pull the boundary prose forward from P1.2's `.loam/README.md` + the migrations README + v-next-plan §2 (do not re-derive — those are the settled statements). Record evolve-in-place as G2-ratified; note the v-next §3 clean-tree recommendation superseded.
2. **Decide the declaration mechanism** (Fork D-2) and write it into the ADR.
3. **Author the test pair FIRST** (TDD, per the dev-mode default): the failing test plants a real violation and asserts the real gate flow goes RED (AC.BLOCK-ENFORCE.3, the outcome-altitude one); the passing test asserts GREEN on a clean tree (AC.BLOCK-ENFORCE.2).
4. **Implement the 8th gate** (`check_boundary_respected` or builder's name) in `gates.py`, add it to `ALL_GATES`, thread it through `run_all` + `format_report` matching gate 7's shape (corrective hint convention). Make the planted-violation test go RED and the clean test GREEN.
5. **Run the gates test suite** (`test_AC_V060_2_*`, `test_AC_MIG_GATE_*`, the new `test_AC_BLOCK_ENFORCE_*`) — confirm no regression to the existing 7 gates and the new gate's pair passes.
6. **No `loam amend apply`** is required UNLESS the builder determines `loam_cli` / the release component is a sealed component that needs the amend bookkeeping — verify against `docs/conventions/sealed-component-invariants.md` at build-time; if sealed, the dispatch names `loam amend apply` as the bookkeeping mechanism. (Plan-author flag: the release-gate component has shipped via amendment cycles before — the builder should expect this is amend-tracked.)
7. **Seal** per the standard ladder; write the verdict matrix into this plan-doc's §status backfill so the AC.\*-GREEN gate (gate 2) can later read it.
8. **Bookkeeping** (§9): re-mark roadmap N1 + v-next P1.2/F0.2; date-and-supersede v-next §3 decision-#1's clean-tree text.

---

## §7. Out of scope (deferred + when)

- **Re-scaffolding `.loam/`** — DONE by P1.2 (`01f3b40`). N1 touches none of `loam_layout.py`, the declared dirs, the README, or `docs/state-migrations/`.
- **A runtime PreWrite/PreToolUse prevention hook** for boundary violations — deferred. The release-gate is the proportionate first enforcement (Surface #2). A runtime guard becomes correct IF a real violation ever slips a release (the structural-enforcement-on-recurrence trigger). Tracked as a follow-up, not built at N1.
- **The migration ENGINE / cursor** — already sealed (`58bead7`); N1 only *reads* the home it established.
- **N2 (STATE-OF-LOAM record + substrate-audit gate)** — a parallel track, different surface. N1 does not depend on it; do not fold it in. (Note: N2 is where the uncommitted audit subpackage — Surface #4 — actually belongs once it lands.)
- **N3 onboarding / N4 user-model** — they CONSUME the locked seam; they are downstream.

---

## §8. Halt triggers (in-flight conditions that abort the build)

1. **The gate cannot reach real-entry-point altitude.** If `run_all` cannot be invoked against a tree carrying a planted violation without pre-arranging in-memory state (i.e. the only way to test is a STUB of an inner function), HALT — AC.BLOCK-ENFORCE.3 is unsatisfiable as written and the AC needs re-framing before code (loose-AC → fix the AC, not the implementation).
2. **The declaration mechanism (Fork D-2) cannot be made the single source for both doc and check.** If doc-rule and code-rule must diverge, AC.BLOCK-ENFORCE.4 fails — HALT and surface the fork for an owner ruling.
3. **A pre-existing real boundary violation is discovered in the current tree.** If implementing the gate reveals that framework code TODAY already writes user-state outside the two homes (a real leak), HALT — surface it (F2: name path + evidence + the fix) before deciding whether N1's gate should ship RED-on-main or whether the leak is fixed first. Do NOT silently widen N1 to fix the leak.
4. **`loam_cli` / release is a sealed component without an amend path named.** If sealed and the dispatch did not name `loam amend apply`, HALT (sealed-component-dispatch rule).

---

## §9. Bookkeeping (STATE.md + roadmap + parent-plan backfill)

1. **`docs/plans/loam-roadmap.md` §4 N1 cell** — re-mark: the `.loam/` scaffold is DONE (P1.2 `01f3b40`); N1's remaining scope is the LOCK (ADR + enforcement gate) only. Update the size estimate M–L → M.
2. **`docs/plans/loam-vnext-build-plan.md`** — (a) §Phase-1 P1.2 row: mark the scaffold DONE (`01f3b40`); (b) §3 decision-#1: add a dated-and-superseded note — the clean-tree recommendation was superseded by G2's evolve-in-place ratification (Surface #3 / §10 F2 #1); (c) §Phase-0 F0.2: mark the boundary-lock delivered by N1's ADR.
3. **`docs/STATE.md`** — record the N1 seal (amendment number + SHA) per the standard ladder once sealed.
4. **This plan-doc §status / verdict-matrix** — backfill each AC GREEN at seal so release gate 2 (`check_acs_verified`) can read it.

---

## §10. F2 Ruthless Feedback (honest doubts + named design risks)

1. **The v-next plan recommends a clean tree; practice chose evolve-in-place — the docs now disagree with reality.** *Evidence:* `loam-vnext-build-plan.md` §3 decision-#1 recommends "(a) a clean new structure inside the canonical loam repo … its own tree"; but `git log` shows today's migration-engine (`c08cbcb`), keep-pace, and the audit work all landed inside the existing `framework/` on `main` — no `kernel/` tree exists. G2 ratifies evolve-in-place. *Alternative:* the ADR records evolve-in-place as the ratified decision and the v-next §3 text gets a dated-and-superseded note (§9.2b). Not silently resolved — surfaced as a named decision in the final report. **This is the most load-bearing finding: a future kernel author reading the v-next plan would otherwise build toward a clean tree that is never coming.**
2. **The dispatch's "audit subpackage on main" premise is not true on the ref graph.** *Evidence:* `git ls-files framework/tools/loam/src/loam_cli/audit/` is EMPTY; only stale `.pyc` exist on disk. *Alternative:* compose the enforcement on the committed release-gate `ALL_GATES` (proven, gate-7 precedent), NOT on the uncommitted audit subpackage. N1's enforcement is therefore unaffected by the audit work's commit state — but the audit subpackage SHOULD be committed (it's N2's home) and its uncommitted state is itself a reconciliation gap worth the owner knowing.
3. **Risk: the gate is only as good as its violation-detection method, which the AC deliberately does not pin.** *Evidence:* AC.BLOCK-ENFORCE.3 is outcome-shape (pins "planted violation caught"), so the builder picks the detection method (static scan of write-sites? a manifest of declared user-state paths checked against actual writes? a runtime-trace fixture?). *The risk:* a weak method could pass the single planted violation while missing the general class. *Alternative / mitigation:* the planted violation in the outcome-altitude test should be a *representative* leak (framework module writing a per-user file outside the homes via a realistic path), and the ADR's declaration mechanism (D-2) should make the legal-home set explicit enough that the gate checks membership, not pattern-matches one known-bad path. Named so the builder authors a representative violation, not a strawman.
4. **The "which side is a path on" declaration (AC.BLOCK-ADR.4 / D-2) is the genuinely-novel design bit.** Everything else composes on settled parts (the README prose, gate-7's shape). The declaration mechanism does not yet exist — D-2 forks it with a recommendation, but it carries the most design uncertainty in N1. Scoped tightly (F4): recommend the cheapest mechanism that makes doc and check share one source (D-2 rec below).

---

## §11. Named decisions / forks (with recommendations)

### D-1 — ADR home: new `docs/design/adr/` subdir vs flat `docs/design/` file
- **(a) `docs/design/adr/boundary-framework-vs-user-state.md`** — establishes an `adr/` convention; future kernel decisions get a numbered/named home a later author cites by convention.
- **(b) flat `docs/design/boundary-framework-vs-user-state.md`** — no new convention; sits beside doctrine/AIM/memory-architecture as just another design doc.
- **Recommendation: (a).** An `adr/` home pays off immediately — N1 is the first of a *series* of kernel architectural decisions (the boundary, later the cursor design, the upgrade-trigger UX), and a citable ADR series is exactly what "a later kernel author reads first" wants. Low cost (one subdir), clear payoff. **Confidence: high** — tight scope.

### D-2 — how a component declares which side a path is on (the single source for doc + check)
- **(a) A declared user-state-paths manifest** — a tracked file (e.g. `docs/design/adr/user-state-homes.yaml` or a section in the ADR) listing the two legal homes as the allowlist; the gate checks that no framework-written user-state lands outside them. Doc and check both read this list.
- **(b) Convention-only (the two homes are hardcoded in both the ADR prose and the gate).** Simplest; but doc and code can drift (AC.BLOCK-ENFORCE.4 risk).
- **(c) A path-tagging scheme** (framework code annotates each user-state write with its home) — most precise, most machinery.
- **Recommendation: (a) — a small declared allowlist of the two homes, read by both the ADR and the gate.** It satisfies AC.BLOCK-ENFORCE.4 (one source, no drift) at minimal cost, mirrors how gate-7 reads `docs/state-migrations/` as its declared contract (Lens-1 symmetry), and avoids (c)'s per-write annotation machinery N1 does not need. (b) is rejected precisely because it permits the doc↔code drift AC.BLOCK-ENFORCE.4 exists to prevent. **Confidence: medium** — this is the novel bit (§10.4); forked deliberately so the owner sees the choice. If the owner prefers (c)'s precision for a later runtime guard, (a) is forward-compatible (the allowlist becomes the guard's input too).

### D-3 — enforcement altitude: release-gate (N1) vs runtime PreWrite hook
- **Settled, not a live fork** (Surface #2): release-gate at N1; runtime guard deferred to the recurrence trigger. Recorded here for completeness, not for a ruling. **Confidence: high.**

---

## §12. Provenance trail (load-bearing sources, with refs)

- **P1.2 scaffold (already built):** `01f3b40`; `framework/workspace-bootstrap/src/loam/workspace_bootstrap/loam_layout.py` (the `establish_loam_layout` + `DECLARED_DIRS` + the boundary-rule README prose, lines 68–103); `docs/state-migrations/README.md` (the framework-side migration-contract home + the framework/user-state split table).
- **The release-gate composition target:** `framework/tools/loam/src/loam_cli/release/gates.py` — `GateResult` (l.43), `check_migration_declared` (l.693, the gate-7 HARD-BLOCK twin), `ALL_GATES` (l.752), `run_all` (l.763), `format_report` (l.794); `runner.py` (the `loam release` flow); test pairs `framework/tools/loam/tests/test_AC_V060_2_*.py` + `test_AC_MIG_GATE_migration_declared.py`. Engine/gate seals `58bead7`/`c08cbcb`/`6587e94`.
- **The boundary architecture:** `docs/plans/loam-vnext-build-plan.md` §2 (the two sides + why load-bearing), §3 decision-#1 (the clean-tree recommendation that practice superseded — §10 F2 #1), F0.2 (the lock step), §7 #2 (the two-migration-systems boundary-leak risk).
- **The roadmap placement:** `docs/plans/loam-roadmap.md` §4 N1 (critical-path head; G2 ratification text), §7 (N1 is next), §6 R-1 (the built-≠-live reconciliation discipline this plan applies).
- **The gitignore reality:** `.gitignore:56` (`.loam/`) + `:59` (`.claude/`) — the two homes are already gitignored user-state.
- **The audit-subpackage-uncommitted finding (§10 F2 #2):** `git ls-files framework/tools/loam/src/loam_cli/audit/` → empty (Tier-0, 2026-05-31).
- **Methodology:** `docs/conventions/plan-docs.md` (this plan's shape); `feedback_test_outcome_altitude_required` (AC.BLOCK-ENFORCE.3); `feedback_loose_AC_text_fix_AC_not_implementation` (halt trigger 1); `feedback_structural_enforcement_on_recurrence` (Surface #2 / D-3); `feedback_locked_design_not_license_for_bad_outcomes` (the clean-tree-superseded reasoning).

---

*Principles applied at authoring: RECONCILE-against-reality (examined P1.2's actual `01f3b40` scaffold + verified the audit subpackage is uncommitted on the ref graph — did not assume the dispatch's premise); EXAMINE-before-designing (read the layout module, the gates spine, the migrations README, the v-next plan §2/§3 before authoring); plan-before-code (PLAN-ONLY — no code written); outcome-altitude AC at the real `loam release` gate entry-point (AC.BLOCK-ENFORCE.3); Claude/loam-leverage-first (enforcement composes on the committed release-gate `ALL_GATES`, not new machinery); ODD authoring (every AC outcome-shape, method-in-AC test passed); F2 (named the clean-tree-vs-evolve-in-place doc/reality divergence + the audit-uncommitted premise gap, each with evidence + an alternative); scope↔confidence (TIGHT where practice settled it; D-2 forked with a recommendation where the declaration mechanism is genuinely novel).*

---

## §13 §status — verdict matrix (backfilled at seal 2026-05-31)

Built on branch `n1-loam-boundary-lock-adr-and-enforcement-gate`.
Artefacts: ADR-0001 (`docs/design/adr/boundary-framework-vs-user-state.md`);
the declared allowlist (`docs/design/adr/user-state-homes.yaml`); gate 9
`check_boundary_respected` in
`framework/tools/loam/src/loam_cli/release/gates.py` (wired into
`ALL_GATES` + `run_all`); test pair
`framework/tools/loam/tests/test_AC_BLOCK_ENFORCE_boundary_respected.py`
(7 tests). Forks ruled: D-1 = `docs/design/adr/` (a); D-2 = declared
allowlist (a). G2 ratified evolve-in-place. No pre-existing boundary leak
found in the real tree (`check_boundary_respected` GREEN on the canonical
repo).

| AC | Verdict | Evidence |
|---|---|---|
| AC.BLOCK-ADR.1 | GREEN | ADR exists + tracked at `docs/design/adr/boundary-framework-vs-user-state.md` (committed). |
| AC.BLOCK-ADR.2 | GREEN | ADR §2 names framework vs user-state + classification-by-what-it's-about; §3 names the two-tier home (`~/.claude/` + `<ws>/.loam/`). |
| AC.BLOCK-ADR.3 | GREEN | ADR §4 records the seam contract (replaced-wholesale / migrated-never-overwritten) + the G2-ratified evolve-in-place repo shape + the dated supersede of the v-next §3 clean-tree recommendation. |
| AC.BLOCK-ADR.4 | GREEN | ADR §5 names the declared allowlist (`user-state-homes.yaml`) as the single source the gate reads. |
| AC.BLOCK-ENFORCE.1 | GREEN | `check_boundary_respected` ∈ `ALL_GATES`; `run_all` invokes it; `len(ALL_GATES)==9`. (`test_AC_BLOCK_ENFORCE_1`.) |
| AC.BLOCK-ENFORCE.2 | GREEN | Clean fixture tree + the real canonical tree are both GREEN (no false-positive on legitimate framework→home writes). (`test_AC_BLOCK_ENFORCE_2`, `_2b`.) |
| AC.BLOCK-ENFORCE.3 | GREEN ★ outcome-altitude:true | Planted real violation (framework module writing `OBJECTIVES.md` under `framework/`) CAUGHT at the real `run_all` entry-point, no pre-arranged state; hint names the path + legal homes. (`test_AC_BLOCK_ENFORCE_3`, `_3b`.) |
| AC.BLOCK-ENFORCE.4 | GREEN | Mutating ONLY the allowlist flips the gate verdict → gate reads the declared file, not a hardcoded parallel rule. (`test_AC_BLOCK_ENFORCE_4`, `_4b`.) |
