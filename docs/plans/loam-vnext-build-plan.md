# loam v-next — the build plan (vision → execution bridge)

**Date:** 2026-05-31
**Status:** PLAN (read-only synthesis; nothing built here — every build step below is owner-gated)
**Owner:** Luke Ivers
**Author:** dispatched synthesis agent (Opus)
**Purpose:** Fold the complete v-next doctrine + the mechanisms articulated across the 2026-05-31 session into ONE prioritized, dependency-ordered build program. This is the gate document for the whole build (plan-before-code): the first Phase-1 slice below is made concretely buildable with outcome-altitude acceptance criteria; the rest is sequenced and owner-gated.

**Sources synthesized (all Tier-0 on disk 2026-05-31):**
- `docs/design/loam-doctrine.md` — the cornerstone doctrine.
- `docs/design/doctrine-inserts.md` — the two owner-pending enshrinement inserts (VALUE_PROPOSITION prime objective + CLAUDE.md Lens 0).
- `docs/design/adaptive-interaction-model.md` — the Pillar-1 user-model engine (its own AIM-0..8 build plan, folded in here as Phase 2).
- `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` — the FBM truth (designed-vs-built table; the "built ≠ live" drift).
- `docs/reviews/claude-primitives-adoption-matrix.md` + `claude-capability-adoption-loop-design.md` + `claude-primitives-integration-review.md` — the primitive-adoption work and the recurring loop.
- Memory anchors: `feedback_loam_prime_directive_user_tuned_translation.md`, `feedback_abstraction_first_default.md`, `feedback_defined_workflow_in_context_pause_if_lost.md`, `feedback_session_is_a_surface_never_infer_user_rhythm.md`, `feedback_user_distress_is_priority_diagnostic_signal.md`, `feedback_narration_is_not_action.md`.

---

## 0. The one-screen version

loam v-next is the doctrine made real: a kernel that **learns the specific user** and **translates their intent into the machine**, **protected** against the known ways AI fails, **pruned** continuously, built in **clean layers** with one load-bearing seam — the **framework ↔ user-meaningful-state boundary**. The owner wants to *build*, and chose the safe cutover: build a **new clean loam** and carry the user forward into it by **selective migration**, keeping the old pos3 intact as fallback — never prune-in-place.

The build is four phases:

- **Phase 0 — Foundation.** Enshrine the doctrine as the kernel's cornerstone (owner-verifies wording; non-blocking). Lock the framework↔user-state boundary as the organizing architecture. *Doc-only; cheap; unblocks everything.*
- **Phase 1 — The kernel.** The minimum to **initialize, onboard, and hold state** across sessions: the user-state store (FBM, wired live — the first brick), the `.loam/` workspace layout, the versioned user-state migration system + its release-gate, the onboarding/init flow, and the MVP user-model + config riding the already-live keep-pace hooks.
- **Phase 2 — Mechanisms on the kernel.** Full adaptive user-model; the failure-mode-guard matrix + protection floor; the defined-workflow system + position cursor + pause-if-lost; the recurring capability-adoption loop; non-tech self-recovery; the owner work-visibility window.
- **Phase 3 — Migrate + cut over.** Stand up a fresh instance, onboard it (dogfood), selectively carry forward (doctrine, keep-worthy rules, LitRPG pipeline + chapters, Cairn pointer, money/house work, live objectives), run old pos3 as fallback, retire it only when the new instance is proven.

The pruning leg and the recurring loops run **continuously** from the moment their mechanism lands, governed by the protection floor.

**The single first build step:** wire the already-built FBM episode store **live** behind the framework↔user-state boundary and prove a fact written in session A is retrievable in a cold session B (Phase 1, slice FBM-LIVE — §6). It is the smallest slice that delivers the doctrine's "real memory" promise and is the brick every later piece reads.

---

## 1. What the doctrine pins (the acceptance frame for the whole program)

Every phase ladders up to the doctrine (`loam-doctrine.md`). The program's top-level acceptance is the doctrine's own structure:

1. **Prime directive — per-user-tuned translation.** The kernel learns the user and owns *how*; the user brings *what*. (Phase 1 user-model + Phase 2 full adaptive model.)
2. **The two sides of leg 2 — translate-in + protect-around.** Intake funnel (the operating loop) and the protection floor are both built. (Phase 1 onboarding/init = intake; Phase 2 failure-mode matrix = protect.)
3. **The three legs — learn / enable / prune.** Pruning is a continuous, protection-governed mechanism, not a one-time pass. (Phase 2 + continuous.)
4. **The standing commitments** — substance-exposed/vocabulary-adapts; openness-with-floor; proportionality; leverage-Claude-first; follow-the-defined-workflow/pause-if-lost — are constraints on *every* build step, not features.
5. **Layered build model** — clean interfaces; the framework↔user-state boundary is the first and most load-bearing seam (Phase 0 locks it).

These are not separate work items; they are the lenses every step below is checked against.

---

## 2. The load-bearing architectural decision — the framework ↔ user-meaningful-state boundary

This is the seam the whole cutover strategy rests on, and it must be built in from day one (owner-confirmed). State it precisely so every later step can respect it:

- **Framework** = loam's own machinery: the persona, the hooks, the components under `framework/`, the doctrine, the methodology, the migration *engine*. Ships with loam; versioned with loam; identical for every user; replaced wholesale on upgrade.
- **User-meaningful-state** = everything that is *about this user and their work*: their profile / interaction-model, their rules and preferences, their content (LitRPG chapters, Cairn pointers), their objectives and work-state, AND the migration **cursor** that records which state-migrations have been applied. Unique per user; carried forward across upgrades; never replaced, only migrated.

**Why this seam is load-bearing (and why it earns a clean interface, per the layering model):**
- It is what makes "build a new clean loam and carry the user forward" *possible* — selective migration only has a clean job if user-state is already a separable thing, not tangled through the framework.
- It is what makes the upgrade mechanism safe — the framework can be swapped wholesale because user-state lives on the other side of the boundary and is migrated, never overwritten.
- It contains blast radius — a framework change cannot silently corrupt user-state if the boundary is real (protection pillar); a prune of framework cruft cannot delete user content (pruning leg, governed by protection).

**F2 — the boundary already half-exists and must not be confused with the wrong one.** `framework/self-upgrade/` already migrates the **loam framework codebase** between versions (the `d-migration` plan series). That is a *framework-side* mechanism (dev-internal: "upgrade loam's own code"). The v-next upgrade mechanism in this plan is a **state-side** mechanism (`.loam/migrations/`: "migrate this user's stored state when loam's state-schema changes"). **These are two different migration systems on two sides of the boundary.** The plan keeps them distinct (§Phase 1, MIGRATE). Conflating them — putting user-state migrations inside `self-upgrade`, or vice-versa — is the first way the boundary leaks. Flagged, not assumed.

**Open question for the owner (decision #1 below resolves it):** where the user-state actually physically lives today — `~/.claude/` (where OBJECTIVES.md, the feedback corpus, INTERACTION-MODEL.md all sit) vs a per-workspace `.loam/` dir vs both. The current corpus is split (`~/.claude/` for global user-state; per-workspace memory sidecars for workspace-state). The boundary decision must name the physical home; §3 decision #1 recommends one.

---

## 3. Decisions to resolve (recommend + flag)

### Decision #1 — where the new kernel is built

> **⚠️ SUPERSEDED 2026-05-31 by G2 (evolve-in-place) — see ADR-0001
> (`docs/design/adr/boundary-framework-vs-user-state.md` §4).** The
> recommendation below was (a) "a clean new structure inside the
> canonical loam repo … its own tree." That was **never executed**:
> today's v-next work (migration engine, audit subpackage, keep-pace)
> all landed *inside* the existing `framework/` tree on `main` — there is
> no separate `kernel/` tree. G2 ratifies **evolve-in-place on the
> existing canonical tree** (git history is the fallback, not a parallel
> intact `framework/`). A future kernel author must NOT build toward a
> clean tree that is not coming. The text below is retained for the
> reasoning record only; the ratified decision is in ADR-0001.

**Three candidates:**

- **(a) Clean new structure inside the canonical loam repo** (a new top-level tree, e.g. `kernel/` or a versioned `framework/`-successor, built alongside the existing `framework/` which stays as the fallback source).
- **(b) A brand-new repo.**
- **(c) In-place refactor of `framework/`.**

**Recommendation: (a) — a clean new structure inside the canonical loam repo, NOT a new repo and NOT an in-place refactor.**

Reasoning (the "fresh, don't prune-in-place" philosophy applies to the framework too, but a new *repo* over-applies it):
1. **The dangerous path is in-place mutation of a running user's state**, which decision #1 is not about — the user's clean base comes from selective *state* migration into a fresh instance (Phase 3), and that is orthogonal to where the framework *code* lives. So (c)'s danger is overstated for code; its real cost is that an in-place refactor of `framework/` loses the intact fallback the owner explicitly wants. Reject (c).
2. **A new repo (b) throws away the migration engine, the build methodology, the seal/amend machinery, the 781-agent dispatch corpus, and the entire git history** — all of which are *framework* assets the v-next kernel composes on (leverage-Claude-first and leverage-loam-first). It also splits the doctrine across two repos during the most fragile period. The "clean base" the owner wants is a clean *user-state* base, not a clean *git history*. Reject (b).
3. **(a) gives every property the owner asked for:** the new kernel is clean (its own tree, authored fresh against the doctrine), the old `framework/` stays intact as the literal fallback source, and both live under one repo so the build methodology, migration engine, and history carry forward. When the new kernel is proven, the old `framework/` is *pruned* (leg 3, protection-governed) — which dogfoods the pruning leg on loam's own body.

**Physical home of user-state (the §2 open question), recommended with (a):** keep global user-state at `~/.claude/` (where it already lives and where the live keep-pace hooks already read it) and introduce a per-workspace `.loam/` dir for *workspace-scoped* user-state + the migration cursor. The boundary is then: **framework code under the repo's kernel tree; user-state under `~/.claude/` (global) + `<workspace>/.loam/` (workspace-scoped).** This matches the already-live read paths (no new wiring to make existing hooks work) and gives the migration system a concrete cursor home (`<workspace>/.loam/migrations/.cursor`).

**This decision is owner-gated** — it sets the repo shape for the whole program. Recommend ratifying (a) + the user-state home before Phase 1 cuts code.

### Decision #2 — the first buildable slice (defined crisply in §6)

The dispatch named FBM as "the first brick." **F2 — there is a precision correction the owner needs (it changes the slice's shape, not its priority):** FBM is **not unbuilt**. The roadmap (`fbm-state-and-memory-roadmap-2026-05-29.md` Q1) shows FBM Tiers 0–2 are **built and sealed** (#134 `0347760`, #135 `32608d2`) — *but sitting dark behind an un-flipped activation switch.* So the first brick is **not "build FBM"** — it is **"wire the already-built FBM live behind the new boundary, and prove cross-session continuity end-to-end."** This is a higher-leverage, lower-risk first slice than a from-scratch build, and it directly delivers the doctrine's "real memory" guard. The crisp definition + outcome-altitude ACs are §6.

### Decision #3 — sequencing fixes to the skeleton (applied in §4)

Three hidden dependencies / mis-sequencings found and fixed (detail in §4): (1) the migration *release-gate* must land in the **same** Phase-1 slice as the migration engine, not after it; (2) the user-model MVP depends on the keep-pace hooks being live, which is the *same* activation as FBM-LIVE — so they share one gated step, not two; (3) the visibility window was skeletoned in Phase 2 but its only hard dependency is "live state exists to view," which Phase 1 produces — so it can move **earlier** as a Phase-2 quick win (kept in Phase 2 but flagged as the first Phase-2 item).

---

## 4. The phased build program (dependency-ordered)

Notation: each item names its **dependency**, its **Claude-primitive leverage** (Lens 1), and its **owner-gate**. Nothing below is built in this plan.

### Phase 0 — Foundation (doc-only; unblocks everything; ~tens of minutes AI-time + owner read)

| Step | What | Dependency | Owner-gate |
|---|---|---|---|
| **F0.1** | Enshrine the doctrine: paste Insert A into `VALUE_PROPOSITION.md` (prime objective) + Insert B into `CLAUDE.md` (Lens 0), per `doctrine-inserts.md`. | none | **Owner verifies the wording** (single-pass, already assembled). Non-blocking for the rest of Phase 0/1 — the doctrine doc itself is already the cornerstone; the inserts are the enshrinement. |
| **F0.2** ✅ **DELIVERED** by N1 (2026-05-31) | Lock the framework↔user-state boundary (§2) as a written architectural decision record: name the two sides, the physical homes (per decision #1), and the rule "framework replaced wholesale, user-state migrated never overwritten." **Delivered as ADR-0001 (`docs/design/adr/boundary-framework-vs-user-state.md`) + the declared allowlist (`docs/design/adr/user-state-homes.yaml`) + the `boundary-respected` release gate (gate 9 in `gates.py`).** | decision #1 ratified (→ G2 evolve-in-place) | **Owner ratifies decision #1** (repo shape + user-state home). |

*Sequencing note:* F0.1 is non-blocking (the doctrine is already captured; enshrinement is owner-wording-gated and can ride alongside Phase 1). F0.2 **is** blocking — Phase 1 cannot lay out `.loam/` without the boundary locked.

### Phase 1 — The kernel (the minimum to initialize, onboard, and hold state)

Dependency-ordered. **FBM-LIVE is the first brick** and the first build step of the whole program (§6).

| Step | What | Dependency | Primitive leverage | Owner-gate |
|---|---|---|---|---|
| **P1.1 — FBM-LIVE (FIRST BRICK)** | Wire the already-built FBM episode store live behind the boundary; prove cross-session continuity. Full crisp definition + outcome-altitude ACs in §6. | F0.2 (boundary located) | The live keep-pace UserPromptSubmit/Stop hooks (already wired) + the built `file_memory.py` store. | **The `~/.claude/settings.json` activation flip is owner-class** (it changes runtime behavior). Then mostly wiring. |
| **P1.2 — `.loam/` workspace layout** ✅ **SCAFFOLD DONE** (`01f3b40`) | Define + scaffold the per-workspace `.loam/` dir: user-state store, `migrations/` dir, `migrations/.cursor` state, the workspace's profile/rules/objectives homes. **`establish_loam_layout()` + the declared dirs + the self-describing README shipped at `01f3b40`.** | F0.2 + P1.1 (knows where episodes live) | `workspace-bootstrap` component (exists) extended to scaffold `.loam/`. | Owner-gated layout review (it's the durable on-disk contract). |
| **P1.3 — user-state migration engine + RELEASE-GATE** | Versioned migration files `.loam/migrations/<version>/`; a cursor; cumulative replay of pending migrations; author-declared, idempotent, ordered. **AND in the same slice:** the repo release-gate that blocks publishing any version without its migration file ("no-op" is a valid declared migration). Protection-floor governs execution (reversible; surface-don't-delete user-state). | P1.2 (`.loam/migrations/` exists) | Composes on the proven DB-migration pattern; distinct from `framework/self-upgrade` (§2 F2). The gate is a repo CI/seal check. | Owner-gated (the gate blocks releases — a process change). |
| **P1.4 — onboarding / init flow** | The "translate-in" intake for a brand-new instance: the operating loop run on a new user (infer end-intent → propose healthy enablement → surface → learn), seeding the initial user-state (profile defaults, first objectives). This is what Phase 3 dogfoods. | P1.2 (somewhere to write seeded state) | `loam-init` component (exists) + the primary-persona operating loop; `start-project` skill precedent. | Owner-gated flow review. |
| **P1.5 — MVP user-model + config** | The smallest adaptive layer: `INTERACTION-MODEL.md` seeded openness-biased (AIM-0); the read-path that maps work-anchor→area and injects the cell on the live hook (AIM-1, exposure + autonomy axes only); the explicit-statement override + plain-language inspect (AIM-3). Includes the **session-usage model** field (single-continuous vs clears-often — per `feedback_session_is_a_surface...`) and **cautious-autonomy-on-consequence** default. | **P1.1's same activation** (the hooks are live) | The live keep-pace hooks (AIM-1 rides UserPromptSubmit; AIM-2 enforces at the live draft-gate). | Owner ratifies the **openness-default revision of `abstraction_first_default.md`** (AIM §6.1) before seeding; hook edits owner-gated. |

**Sequencing fixes applied here (decision #3):**
- **Fix (1):** P1.3 bundles the migration engine *and* its release-gate in one slice — a migration system without the gate that forces every version to declare a migration is the exact "lapsed re-eval" failure shape from the FBM roadmap (a safety mechanism that exists but isn't enforced). The gate is what makes the mechanism load-bearing.
- **Fix (2):** P1.5's user-model MVP and P1.1's FBM both need the keep-pace chain *live* — that is **one** owner-gated `~/.claude/settings.json` activation, not two. The plan flips it once (in P1.1) and P1.5 rides the same live chain.
- **Fix (3):** the onboarding flow (P1.4) is sequenced **before** the user-model MVP (P1.5) in build order even though both are Phase 1, because onboarding is what *creates* the initial user-state the model then adapts — building the adapter before the thing it adapts is backwards.

### Phase 2 — Mechanisms on the kernel

Each rides the kernel. Ordered by dependency + quick-win value.

| Step | What | Dependency | Notes |
|---|---|---|---|
| **P2.0 — Owner work-visibility window (quick win, moved earliest)** | A live view of current/queued/in-flight work beyond the chat (Tailscale dashboard / iOS), reading live kernel state. | P1.1+P1.2 (live state exists to view) | **Decision #3 fix (3):** its only hard dependency is "live state exists," which Phase 1 produces — so it is the first Phase-2 item, an early QoL win, not a late one. |
| **P2.1 — Full adaptive user-model** | The remaining AIM items: behavioral signal counters + hysteresis (AIM-4, dark-launch first); fast-down-on-distress wired to the distress detector (AIM-5); the tone + learning-appetite axes (AIM-6); the weekly re-eval consolidation pass + drift judge (AIM-7). | P1.5 + (AIM-7 needs FBM consolidation, P2.x below) | The AIM doc's own backlog, folded in. Ship the classifier calibrated, not eager (AIM §7 flag). |
| **P2.2 — Failure-mode-guard matrix + protection floor** | A living catalogue: known AI failure mode × loam's guard × default-on, with visible coverage (guarded vs not-yet), refreshed on a recurring cadence. The non-negotiable floor (hallucination / silent regression / context loss / lost-thread / narration-not-action / inferred-rhythm) always-on for everyone; proportionality above it. | P1.x kernel | The twin of the capability-adoption matrix. Seeds from the already-named guards (objective-driven authoring, FBM, verify-before-acting, channel auto-route, distress alarm, narration-is-not-action, session-is-a-surface). |
| **P2.3 — Defined-workflow system + position cursor + pause-if-lost** | Structured flow definitions for real processes (Claude-capability adoption flow, pruning flow, book-writing flow, dev flows); an always-in-context active-flow; a persisted **position cursor**; the follow-it/pause-if-lost directive re-injected at every context-loss point. | P1.1 (durable store for the cursor) + the compaction-reinject hook (exists, extend it) | Compose on Claude workflow primitives (`/goal` etc.). **The genuinely novel part is the position cursor** (`feedback_defined_workflow...` flags this as needing real design) — scope it tightly. |
| **P2.4 — Recurring capability-adoption loop + adopt-now items** | The standing loop (`claude-capability-adoption-loop-design.md`): weekly floor + version-bump/changelog-hash triggers; 3 sub-passes (feature-refresh / usage-telemetry / usage-drift); auto-apply only safe doc edits, owner-gate behavior changes. Plus actioning the top adopt-now cluster (subagent definition files + `skills:`-preload + `mcpServers:` telegram-scrub + `isolation:worktree`). | P1.x | Already fully designed; this is a wiring + scheduling build (Routine + launchd split). |
| **P2.5 — Non-tech-user self-recovery** | distress-as-fire-alarm detector → forced self-diagnosis → watchdog hooks → plain-language recovery → safe hard-reset on the user-state store. | P1.1 (state to reset) + P2.1 (reads the user-model for recovery-pitch level) | The distress detector is also AIM-5's trigger (shared seam). |

### Phase 3 — Migrate + cut over (dogfoods onboarding + the upgrade mechanism)

| Step | What | Dependency | Owner-gate |
|---|---|---|---|
| **P3.1 — Stand up a fresh instance** | A clean loam instance on the new kernel, empty user-state. | Phase 1 complete | — |
| **P3.2 — Onboard it (dogfood P1.4)** | Run the real onboarding flow as a brand-new user would. This is the test that the intake funnel works. | P3.1 | — |
| **P3.3 — Selective carry-forward** | Migrate, deliberately, only the keep-worthy user-state into the fresh instance: the doctrine, keep-worthy rules (prune the corpus on the way — leg 3, protection-governed), the LitRPG pipeline + chapters, the Cairn pointer (do NOT touch the Cairn repo), money/house work, the live objectives. Old pos3 stays intact. | P3.2 + P1.3 (migration engine) | **Owner ratifies the carry-forward manifest** (what migrates vs what's left behind) — destructive-by-omission, so surface-before-cut (protection floor). |
| **P3.4 — Run old pos3 as fallback; retire when proven** | The new instance runs as primary; old pos3 stays as the literal fallback until the new instance is proven across real work. Retire (prune) old pos3 only then. | P3.3 + observed stability | **Owner-gated retire decision** (the final prune; reversible via git/the intact fallback until the moment of retire). |

### Continuous (from the moment each mechanism lands)

- **Pruning leg** runs continuously, protection-governed (reversible / surface-before-cut / check-depends-on-it), the moment P2.2's floor + P2.3's flows exist to govern it.
- **The recurring loops** (capability-adoption P2.4; user-model re-eval P2.1/AIM-7; failure-mode-matrix refresh P2.2) run on their cadences once landed.

---

## 5. Dependency graph (the critical path, in one view)

```
F0.2 (boundary locked)  ──►  P1.1 FBM-LIVE  ──►  P1.2 .loam/ layout  ──►  P1.3 migration engine + release-gate
                                  │                      │
                                  │ (same activation)    └──►  P1.4 onboarding/init ──► P1.5 user-model MVP
                                  ▼
                            P2.0 visibility window (early QoL)
                                  │
   P1.x kernel complete ──►  P2.1 full user-model  /  P2.2 failure-matrix  /  P2.3 workflow+cursor  /  P2.4 adoption-loop  /  P2.5 non-tech-recovery
                                  │
                                  ▼
                            Phase 3: fresh instance ► onboard ► selective migrate ► fallback ► retire

F0.1 (doctrine enshrinement) — owner-wording-gated, rides alongside, non-blocking.
Pruning + recurring loops — continuous once P2.2/P2.3/P2.4 land.
```

**Critical path = F0.2 → P1.1 → P1.2 → P1.3 → P1.4 → P1.5 → Phase 3.** Phase 2's other mechanisms parallelize off the completed kernel (independent of each other except AIM-7→FBM-consolidation).

---

## 6. The first buildable slice — FBM-LIVE (defined crisply, with outcome-altitude ACs)

**This is the single first build step. It is owner-gated at the activation flip, then mostly wiring.**

### Objective
Make loam's already-built episodic memory **actually run** behind the framework↔user-state boundary, so a user-meaningful fact stated in one session is reliably retrieved in a later cold session — delivering the doctrine's "real memory" protection guard, and producing the live state every later kernel piece reads.

### Why this slice first (Lens 4 — high confidence, tight scope)
The store is built and sealed (FBM Tiers 0–2, #134/#135); the read/write hooks are wired live (keep-pace KP0/KP1/KP7/KP9). The only thing missing is the owner-gated activation flip + unifying the two existing indexes (FBM episodes + the keep-pace corpus index) into one retrieval surface (roadmap R1). High-confidence, tight scope — and it is the brick literally everything in Phase 1 sits on.

### Constraints (from the doctrine + the boundary decision)
- Episodes are **user-meaningful-state** → they live on the user-state side of the boundary (per decision #1: `~/.claude/` global + `<workspace>/.loam/` workspace-scoped), never inside framework code.
- **Fail-open:** if the store is missing/unreadable, retrieval returns nothing and the persona behaves exactly as today (no regression) — the protection floor's "never silently break what works."
- **Surface, don't silently lose** (memory promise P2): a write that would lose prior user state is surfaced, never overwritten.
- No Anthropic API key anywhere in the path (`feedback_no_anthropic_api_key`); any LLM step routes through `claude_print_client.py`.

### Outcome-altitude acceptance criteria
*(Each invokes the production entry-point with no pre-arranged in-memory state — the cold-walk standard. STUB-class tests do not satisfy these.)*

- **AC-FBM-LIVE-1 (cross-session continuity — THE outcome).** In a cold session B (fresh process, no carried context), a user-meaningful fact written to the store during a separate prior session A is retrieved and surfaced when session B's prompt is relevant to it. Verified by: write fact in a real session-A turn through the live write path → start a genuinely new session-B process → submit a relevant prompt → assert the fact appears in the injected context. No pre-seeded index; the production hooks do the write and the read.
- **AC-FBM-LIVE-2 (unified retrieval surface).** One retrieval call at turn time sees **both** the FBM episode store **and** the keep-pace corpus index (rules + OBJECTIVES.md) — not two indexes blind to each other (roadmap R1). Verified by: a prompt whose best answer lives in an episode AND a prompt whose best answer lives in the rules corpus both surface from the *same* live read path in a cold session.
- **AC-FBM-LIVE-3 (fail-open, no regression).** With the store dir absent/unreadable, a real session runs end-to-end with zero error and the persona's behavior is identical to the pre-activation baseline. Verified by: rename the store dir → run a real cold session → assert no error and normal operation.
- **AC-FBM-LIVE-4 (boundary respected).** The episode store physically resides on the user-state side of the boundary (the home decision #1 names), and no framework-code path writes user-state anywhere else. Verified by: after a real session that writes episodes, the only new user-state files are under the declared user-state home; `framework/` (or the new kernel tree) is unchanged.

### Owner-gate
The `~/.claude/settings.json` activation flip is owner-class (runtime behavior change). The owner flips it; the unify + boundary-placement is then wiring against built parts.

### First concrete action when the build is authorized
Author the FBM-LIVE plan doc under the build-methodology plan path, then (owner having flipped the activation) wire FBM episode retrieval into the live keep-pace UserPromptSubmit read path as one unified surface, and prove AC-FBM-LIVE-1 with a real two-session cold-walk.

---

## 7. Gaps and contradictions flagged (F2 — named, not invented)

1. **FBM is built, not unbuilt (precision correction — changes the first slice's shape).** The dispatch frames FBM as "the first brick" to build. The roadmap proves Tiers 0–2 are **built + sealed but dark** (`fbm-state-and-memory-roadmap-2026-05-29.md` Q1; seals `0347760`/`32608d2`). **Resolution:** the first brick is *wire-it-live + unify*, not *build-from-scratch* (§6, decision #2). This is higher-leverage and lower-risk, and it is the correct reading of "first brick."

2. **Two migration systems, one boundary (must not conflate).** `framework/self-upgrade/` already migrates the loam *framework codebase*; the v-next upgrade mechanism migrates *user-state* (`.loam/migrations/`). They sit on opposite sides of the boundary (§2 F2). **Resolution:** the plan keeps them distinct (P1.3). If a future step tries to reuse `self-upgrade` for user-state migrations, that is the boundary leaking — flag it.

3. **The "lapsed re-eval" failure pattern is a live risk for the release-gate.** The FBM roadmap documents a deferred item whose "re-evaluate in ~1 week" trigger silently lapsed (`feedback_workaround_masks_rootcause_urgency` shape). The migration **release-gate** (P1.3) is the structural answer to exactly this class — a mechanism that *forces* a declared migration per release rather than relying on someone remembering. **Resolution:** P1.3 bundles the gate with the engine (decision #3 fix 1); the gate is non-optional.

4. **The position cursor (P2.3) is the one genuinely-novel, under-designed piece.** `feedback_defined_workflow_in_context_pause_if_lost.md` explicitly flags "POSITION-TRACKING needs real design." Everything else in the plan composes on built or designed parts; the cursor does not yet have a design. **Resolution:** P2.3 carries a tight-scope flag — design the cursor before building it; do not let it ride in on the workflow-definitions work as if it were solved.

5. **The openness-default revision of `abstraction_first_default.md` is an unratified edit to a Luke-tuned rule.** P1.5 (user-model MVP) defaults `technical-exposure: open`, which *reverses* the current `minimal` default of a memory rule Luke tuned (AIM §6.1 justifies it but flags it needs ratification). **Resolution:** P1.5's owner-gate is exactly this ratification, recorded before the seed is written (`feedback_record_owner_ratification_before_dispatch`).

6. **Phase 0 doctrine enshrinement is owner-wording-gated and must not be silently applied.** Inserts A/B are *proposed* wording pending single-pass owner verification (`doctrine-inserts.md`; foundational-doc class). **Resolution:** F0.1 is explicitly non-blocking and owner-gated; the doctrine doc itself already serves as the cornerstone while the inserts await the owner's okay.

7. **No genuine contradiction found between the doctrine and the mechanisms.** The mechanisms (FBM, user-model, failure-matrix, workflow-system, adoption-loop, recovery, visibility, upgrade) each map cleanly onto a doctrine element (§1 frame). The only frictions are the precision corrections above, not contradictions.

---

## 8. Lens coverage (the doctrine's own lenses, applied to this plan)

- **Prime directive / Lens 0:** the program's spine (P1.5 + P2.1) *is* the per-user-tuned-translation engine; the onboarding flow (P1.4) *is* the intake funnel; the protection floor (P2.2) *is* protect-around. The plan ladders entirely up to the prime directive.
- **Lens 1 (Claude-leverage-first):** every step names the primitive it rides — live keep-pace hooks (P1.1/P1.5), `workspace-bootstrap`/`loam-init` components (P1.2/P1.4), Routine+launchd (P2.4), the compaction-reinject hook (P2.3), `/goal` (P2.3). No new engine where one exists.
- **Lens 2 (harness + persona value):** every kernel piece reduces translation burden (the user brings *what*; onboarding/model/migration own *how*) and adds to the persona's toolkit.
- **Lens 3 (ODD):** the first slice (§6) is stated as objective + constraints + outcome-altitude ACs; method is the builder's call. The phase table states outcomes, not steps.
- **Lens 4 (scope↔confidence):** FBM-LIVE is tight-scoped (high confidence — built parts). The position cursor (P2.3) and the behavioral classifier (P2.1/AIM-4) are explicitly loosened/deferred (low confidence — calibrate-on-data).
- **Lens 5 (swarming):** the program decomposes into phases→steps each with a tighter AC than the parent; Phase 2's mechanisms parallelize off the completed kernel; decomposition stops where a step adds only coordination overhead.
- **Lens 6 (conflict resolution):** decision #1 (build location) names the conflict (fresh-vs-leverage), the signals (reversibility, blast radius, fallback-intactness), and resolves to (a) with the reasoning shown — surfaced for owner ratification, not silently ruled.
- **Lens 7 (ruthless feedback):** §7 names six gaps/corrections with evidence (file paths, seal SHAs, the roadmap's drift finding) and the resolution for each, including correcting the dispatch's own "build FBM" framing.

---

## 9. What is owner-gated before any code

1. **Decision #1** — repo shape (recommend: clean new tree inside the canonical repo) + user-state physical home (recommend: `~/.claude/` global + `<workspace>/.loam/` workspace-scoped). *(F0.2 blocks Phase 1 on this.)*
2. **Doctrine enshrinement wording** — Inserts A/B single-pass verification (F0.1; non-blocking).
3. **The keep-pace `~/.claude/settings.json` activation flip** — shared by P1.1 + P1.5 (one flip, owner-class).
4. **The `abstraction_first_default.md` openness-default revision** — recorded before P1.5 seeds the user-model.
5. **The migration release-gate** — a process change blocking releases (P1.3).
6. **The Phase-3 carry-forward manifest** — what migrates vs what's left behind (surface-before-cut).

---

*Principles applied at authoring: plan-before-code (this is the program gate; the first slice is made buildable with outcome-altitude ACs in §6); faithful-synthesis / claim-or-cite (every item traced to a source doc + seal/SHA where load-bearing); F2 (corrected the dispatch's "build FBM" framing, named the two-migration-systems boundary risk, flagged the position cursor as under-designed); scope-discipline (plan only; every build step owner-gated; the first slice marked).*
