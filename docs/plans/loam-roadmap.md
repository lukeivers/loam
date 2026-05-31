# loam — the live build roadmap (the single "what's next" driver)

**Date:** 2026-05-31. **Status:** LIVE — this is the standing, prioritized,
dependency-ordered roadmap the primary persona drives "what's next" from.
**Owner:** Luke Ivers. **Class:** durable plan-doc (read-only synthesis; nothing
built here).

**What this is.** The ONE roadmap. When the question is "what do we build next,"
the answer is the top unblocked item in NEXT-UP below — not a re-derivation, not
a fresh ask. Items move between groups (DONE / IN-FLIGHT / NEXT-UP / LATER) as
state changes; new items append to the right group without a rewrite.

**How it relates to the existing plans.** It does **not** supersede
`docs/plans/loam-vnext-build-plan.md` — that plan holds the *kernel build CONTENT*
(the phased Phase 0–3 program with per-slice ACs) and remains the authority on
*how each kernel slice is built*. `docs/plans/loam-vnext-build-workflow.md` holds
the *per-slice PROCESS* (examine→define→build→prove→integrate, the gates, the
position cursor). **This roadmap sits above both**: it is the full-program
backlog — it absorbs the v-next plan's phasing AND folds in the captured-work
items the v-next plan does not cover (the contribution mechanism, skill triage,
structure-flatten + PyPI, the build-process hygiene fixes, the
memory↔reality-reconciliation mechanism, the reasoning-acceleration layer). For
any kernel slice, read the v-next plan for content and the workflow doc for
process; read THIS for "what's the next thing, and why."

**Trust discipline.** Every status below is reconciled against the git ref graph
+ live operational reality on 2026-05-31, not against task-title claims. Where a
captured-status and the code disagree, the divergence is recorded in §6
(Reconciliation findings) — that divergence is signal. Statuses are Tier-0 where
a SHA/test/file backs them; inferences are marked [INFER].

---

## 1. The value spine (what every item ladders to)

Every item below ladders to the **loam prime directive — per-user-tuned
translation + protection** (`docs/design/loam-doctrine.md`;
`feedback_loam_prime_directive_user_tuned_translation.md`). An item that does not
reduce the user→machine translation burden, add to the persona's toolkit, or
protect against a known AI failure mode does not belong here. The roadmap's
top-level acceptance is the doctrine's own structure: **learn the user / enable
them / prune continuously**, with the **framework ↔ user-meaningful-state
boundary** as the load-bearing seam the whole cutover rests on.

---

## 2. DONE (reconciled against the git ref graph + live behaviour, 2026-05-31)

| Item | What it delivers | Evidence (Tier-0) |
|---|---|---|
| **FBM memory-quality system — rank-normalize + rule-weight/floor + salience gate + path consolidation, LIVE** | The episode store + rules corpus now retrieve as ONE junk-gated surface on the live per-turn hook. Delivers the doctrine's "real memory" guard. | Seals `7e9af6b` (rank-normalize merge / AC-FBM-LIVE-2), `81c7780` (rule-weight + hard floor), `fb26be2` (episode salience gate B3), `c82131e`/`055f937` (spread-neighbour gate leak fix AC-FBM-SAL-6), `7dcb95b` (path consolidation — gated UPS hook). Cold-walk proofs: `test_AC_FBM1_S_fresh_session_write_lands_and_retrieves.py`, `test_AC_FBM_SAL_5_live_store_cold_walk.py`, `test_AC_FBM_CON_S_real_hook_junk_gated.py`. pos3 runs the gated `user-prompt-submit` hook (`pos3/.claude/settings.json:41`). |
| **User-state migration / upgrade ENGINE + release-gate — sealed** | Versioned `*.migration.yaml` files, a cursor, cumulative ordered replay, idempotent. AND the 7th release-gate that HARD-BLOCKS publishing any version without a declared migration ("no-op" valid). The structural answer to the "lapsed re-eval" class. | `framework/state-migration-engine/` (replay/envelope/cursor/schema/cli). Gate 7 `check_migration_declared` is in `ALL_GATES` (`framework/tools/loam/src/loam_cli/release/gates.py:638-760`). Seal `58bead7`; engine `c08cbcb`/`6587e94`. Outcome test `test_AC_MIG_UPGRADE_real_entrypoint.py`. |
| **v0.14.0 release-integration merged to main** | The HARD-smoke'd release landed; lockstep pyproject bumps; D.1 rebaseline. | Merge `3ac70a7`; `docs/ACTIVE_MINOR`, `docs/STATE.md` bumped; `release-integration-v0-14-0.md` + `-hard-smoke.md`. |

**Reconciliation note (carried into §6):** the FBM item is marked DONE here but
is still marked "NOT WIRED LIVE — owner-gated / dark" in BOTH
`fbm-state-and-memory-roadmap-2026-05-29.md` (Q1) and the v-next plan's
FBM-LIVE-is-the-first-unbuilt-slice framing. Those two docs are now STALE on this
point — see finding R-1.

---

## 3. IN-FLIGHT (started, not complete)

| Item | What's left | Dependency | Owner-gated? | Size |
|---|---|---|---|---|
| **loam upgrade mechanism — full non-tech-automatic flow** | Migration ENGINE is done (§2). What remains: the **auto-detect-on-upgrade hook** (detect a version bump → run pending migrations automatically) + the **carry-forward manifest** flow. The engine exists; the automatic *trigger + UX* around it does not. | migration engine (DONE) | The auto-run-on-upgrade behaviour is owner-class (runtime). | M (single-component, ~30–60 min) |
| **Doctrine ENSHRINEMENT into VALUE_PROPOSITION + CLAUDE.md** | Inserts A (VALUE_PROPOSITION prime-objective) + B (CLAUDE.md Lens 0) are *assembled and ready to paste* (`docs/design/doctrine-inserts.md`) but **NOT yet applied** — grep of both live docs returns no prime-objective/Lens-0 section. Purely owner-wording-gated. | none (non-blocking) | **Yes — owner verifies the wording** (single-pass; TG 13221 pending). | S (doc-only, 1–3 min once approved) |

---

## 4. NEXT-UP (unblocked; dependency-ordered — the top item is the next thing to build)

The kernel's first brick (FBM-LIVE) is DONE, which **re-bases the critical path**.
The next unblocked kernel slices are the `.loam/` layout and the
reasoning-acceleration record. Ordered so the top is genuinely next:

| # | Item | What + why (value) | Dependency | Owner-gated? | Size |
|---|---|---|---|---|---|
| **N1** | **`.loam/` workspace layout + boundary lock (v-next F0.2 + P1.2)** | Scaffold the per-workspace `.loam/` dir (user-state store, `migrations/` + `.cursor`, profile/rules/objectives homes) AND write the framework↔user-state boundary as an architectural decision record. This is the seam the whole cutover rests on; everything else in the kernel reads/writes through it. **It is now the true critical-path head** (FBM-LIVE, which it used to follow, is done). | FBM-LIVE (DONE) | **Yes — G2: ratify repo shape (clean new tree in the canonical repo) + user-state physical home** (`~/.claude/` global + `<ws>/.loam/` scoped). Blocks the rest of the kernel. | M–L (1–2 components) |
| **N2** | **STATE-OF-LOAM operative-reality record + substrate-audit gate (R-1 + R-3)** | A single always-loaded "what loam currently IS + currently RUNS" record (which hooks wired, which backends live, which components dark), machine-backed by a cheap liveness probe, read first by every design step; plus a plan-author gate that blocks any "rides existing X" claim until verified against it. **Directly prevents the most expensive class loam has hit** (40 days reasoning against a dark graphiti backend; the FBM "built-but-dark" drift THIS roadmap just had to correct). Highest-leverage reasoning-process fix. | FBM-LIVE / live state to probe (DONE) | The gate is a process change → owner-gated to turn ON. | M |
| **N3** | **onboarding / init flow (v-next P1.4)** | The "translate-in" intake for a brand-new instance: run the operating loop on a new user, seed initial user-state. This is what Phase 3 dogfoods — building it before the user-model that adapts the state is the right order (the adapter needs something to adapt). | N1 (`.loam/` to write seeded state into) | Owner-gated flow review. | M–L |
| **N4** | **MVP user-model + config (v-next P1.5) — FLAGSHIP pillar 1, first slice** | The smallest adaptive layer riding the now-live keep-pace hooks: seed `INTERACTION-MODEL.md`, map work-anchor→area, inject the exposure/autonomy cell on the live hook, explicit-override + plain-language inspect. **This is the per-user-tuned-translation engine's first real brick** — the home for FBM rule auto-weighting (infer + surface). | N3 (state to adapt) + live hooks (DONE) | **Yes — G5: ratify the openness-default revision of `abstraction_first_default.md`** before seeding (reverses a Luke-tuned `minimal` default). | M–L |

**Sequencing note.** N1 and N2 are *both* unblocked off the done FBM-LIVE and are
near-parallel (N2 has no hard dependency on N1 — it only needs live state to
probe, which exists). N1 is placed first because it locks the boundary that N3/N4
write through; N2 can run alongside N1 as a parallel track (different surface).
N3→N4 are strictly sequential (onboarding creates the state the user-model
adapts).

---

## 5. LATER (blocked, or correctly deferred behind the kernel)

Grouped by the thing they wait on. Within each group, dependency-ordered.

### 5a. Phase-2 mechanisms (ride the completed kernel — N1–N4)

| Item | What + why | Dependency | Owner-gated? | Size |
|---|---|---|---|---|
| **Owner work-visibility window** | Live view of current/queued/in-flight work beyond Telegram (Tailscale/iOS), reading live kernel state. Early QoL win — its only hard dep is "live state exists," which the kernel produces. | N1 (live `.loam/` state) | n | M |
| **Full adaptive user-model (FLAGSHIP pillar 1, remainder)** | Behavioural signal counters + hysteresis (dark-launch first), fast-down-on-distress, tone + learning-appetite axes, weekly re-eval consolidation + drift judge. The full per-user engine. | N4 (MVP user-model) | partial (behaviour changes owner-gated) | L |
| **Failure-mode-guard matrix + protection floor (FLAGSHIP pillar 2)** | Living catalogue: AI failure mode × loam's guard × default-on coverage, refreshed on cadence. The non-negotiable floor (hallucination / silent regression / context loss / lost-thread / narration-not-action / inferred-rhythm) always-on; proportionality above it. The twin of the capability-adoption matrix. | kernel (N1–N4) | n (seeding); behaviour-changing guards owner-gated | L |
| **Scheduled concept-altitude / drift-audit review (R-2)** | A self-fired recurring "does recent work still ladder to the prime directive?" pass that diffs output-shape against the doctrine spine and surfaces drift with evidence. Converts owner-caught drift (the translator→orchestrator miss) into self-caught drift. Slots beside the capability-adoption loop. | kernel; composes with the adoption loop's Routine+launchd scheduling | n | M |
| **Defined-workflow system + position cursor + pause-if-lost** | Structured flow definitions for real processes + an always-in-context active-flow + a persisted **position cursor** + follow-it/pause-if-lost re-injected at every context-loss point. **The position cursor is the one genuinely-novel, under-designed piece — scope it tightly, design before building.** The v-next-build-workflow doc is its first real input (dogfood). | N1 (durable store for the cursor) + the compaction-reinject hook (exists) | n | M–L (cursor design is the risk) |
| **Recurring capability-adoption loop + adopt-now items** | The standing weekly+trigger loop (feature-refresh / usage-telemetry / usage-drift; auto-apply safe doc edits, owner-gate behaviour). Plus the top adopt-now cluster (subagent definition files / `skills:`-preload / `mcpServers:` telegram-scrub / `isolation:worktree`). Already fully designed — wiring + scheduling build. | kernel | partial | M |
| **Non-tech-user self-recovery** | distress-as-fire-alarm → forced self-diagnosis → watchdog hooks → plain-language recovery → safe hard-reset on the user-state store. Shares the distress detector with the user-model's fast-down trigger. | N1 (state to reset) + full user-model (reads recovery-pitch level) | partial | M–L |
| **Intent-evolution "concept changelog" (R-4)** | Append-only "we thought X; it became Y; on DATE; because Z" record so each new design inherits current understanding instead of re-deriving a stale version. Concept-level analogue of the user-state migration log. | kernel | n | S–M |

### 5b. Build-process hygiene + structure (independent of the kernel; ride existing cycles)

These are not kernel work; they are loam-on-loam hygiene. None blocks the kernel;
several are cheap ride-alongs.

| Item | What + why | Dependency | Owner-gated? | Size |
|---|---|---|---|---|
| **memory↔reality reconciliation mechanism** | Auto-detect + heal stored-claim-vs-truth divergence — the structural form of THIS roadmap's reconciliation pass. Born from a real failure (a stale note trusted over Luke's direct observation). Closely related to R-1 (STATE-OF-LOAM is the substrate-liveness half; this is the general stored-vs-truth half). **Recommend folding into N2** rather than tracking separately — see §6 redundancy note. | live state | n | M |
| **loam structure flatten (`framework/framework`) + PyPI publish / conventional install** | Flatten the cosmetic `framework/framework` doubling (~3.5 h, ride a `workspace-bootstrap` cycle; risk = keep `pos-sync --ff-only` working) + publish to PyPI so `pip install loam; loam init` works (~9 h, the v0.2 documented target, blocked solely by no-publish-yet). | none (hygiene) | PyPI account/credential steps owner-gated | M (flatten) + L (PyPI) |
| **build-process hygiene fixes** | Cluster: guard-on-subagent no-op (root-caused), outbound internal-ID-leak guard, pre-build sync-check gate (multi-worktree divergence prevention), corpus-gate-missing diagnostic, D.1 pyproject-exclude PATCH. Small structural-enforcement fixes; each cheap; several captured in FUTURE_IDEAS. | none | n (mostly) | S each |
| **skill triage + loam↔Claude-primitives integration review** | Install good skills + retire dead ones; review where loam should compose on a Claude primitive rather than re-implement. Composes with the capability-adoption loop (this is the manual first pass the loop later automates). | none | n | S–M |

### 5c. loam CONTRIBUTION + management mechanism (NEW owner ask 2026-05-31)

| Item | What + why | Dependency | Owner-gated? | Size |
|---|---|---|---|---|
| **loam contribution + management mechanism (OSS-hygiene, modeled on what Cairn got)** | CONTRIBUTING-style hygiene + management scaffolding for loam as an OSS project, mirroring what Cairn received. NEW ask; not yet scoped into a plan. **Recommend a short scoping pass first** (what did Cairn get, what maps to loam) before sizing — see §6. | none (independent) | n (scoping); publish-class steps owner-gated | UNSCOPED — scope first |

### 5d. Phase-3 cutover (waits on the whole kernel)

| Item | What | Dependency | Owner-gated? |
|---|---|---|---|
| **Stand up fresh instance → onboard (dogfood) → selective carry-forward → run old pos3 as fallback → retire when proven** | The safe cutover: a clean loam on the new kernel, onboarded as a brand-new user, then deliberately migrate only keep-worthy user-state (doctrine, keep-worthy rules pruned on the way, LitRPG pipeline + chapters, Cairn pointer, money/house work, live objectives); old pos3 stays intact as literal fallback until the new instance is proven. | Kernel complete (N1–N4) + migration engine (DONE) | **Yes — G6 carry-forward manifest** (destructive-by-omission → surface-before-cut) + **G7 retire** (final prune, reversible via the intact fallback). |

### 5e. Explicitly NOT loam-harness build (tracked for awareness; do NOT prioritize into this roadmap)

These are real owner objectives but are **not** loam-harness build items — they do
not enter NEXT-UP ordering:

- **local→remote PUSH of v-next** — owner-gated; a release/ops action, not a build.
- **Cairn security review + public flip** — separate product; do not touch the Cairn repo.
- **cause-coordination engine** — separate product.
- **money / books objectives** — Luke's parallel priorities (LitRPG novels, money push), governed by their own pipelines.

---

## 6. Reconciliation findings (status-vs-reality divergences caught — this is signal)

1. **R-1 (LOAD-BEARING) — FBM-LIVE is DONE, but two canonical docs still call it
   dark/unbuilt.** The v-next build plan (`loam-vnext-build-plan.md` §6, dated
   2026-05-31 *earlier* in the day) frames FBM-LIVE as "the single first build
   step," owner-gated at an un-flipped activation switch — and the FBM roadmap
   (`fbm-state-and-memory-roadmap-2026-05-29.md` Q1) states "the comprehensive
   episode store is built but NOT WIRED LIVE … behind the same un-flipped
   `~/.claude/settings.json` activation switch." **Both are now stale.** The
   git ref graph shows the activation + index-unify + salience-gate +
   path-consolidation all landed today (`7e9af6b`, `81c7780`, `fb26be2`,
   `c82131e`, `7dcb95b`; STATE.md amendment #154 `4b258218`), the cold-walk
   outcome tests pass (`test_AC_FBM1_S_…`, `test_AC_FBM_SAL_5_live_store_cold_walk`,
   `test_AC_FBM_CON_S_real_hook_junk_gated`), and pos3 runs the gated
   `user-prompt-submit` hook live. **This IS the R-1 failure-class the
   reasoning-acceleration review names** (built ≠ live; a doc claims dark while the
   refs say live) — caught here only by reconciling against refs, which is exactly
   why N2 (the STATE-OF-LOAM record + substrate-audit gate) is high-priority.
   **Recommendation:** the v-next plan's "first brick" should be re-marked DONE and
   its critical path re-based to start at `.loam/` layout (N1); the FBM roadmap's
   Q1 "dark" claim should be dated-and-superseded, not silently left.

2. **Migration engine: status MATCHES reality (no divergence) — the 7th gate is
   real and load-bearing.** The captured "sealed" claim checks out: the engine
   exists at `framework/state-migration-engine/` and `check_migration_declared` is
   genuinely in the `ALL_GATES` tuple as a HARD-BLOCK (`gates.py:638-760`), not
   merely defined-but-unwired. Recorded as a *positive* reconciliation (the kind
   worth confirming, not just the failures).

3. **Doctrine enshrinement: NOT applied (the captured "PENDING" is accurate).**
   Grep of `docs/VALUE_PROPOSITION.md` + `CLAUDE.md` returns no prime-objective /
   Lens-0 section; the inserts sit ready in `doctrine-inserts.md` marked PROPOSED.
   Correctly tracked as IN-FLIGHT/owner-wording-gated (§3) — no divergence, but
   worth noting it is genuinely un-done despite the doctrine being the de-facto
   cornerstone.

4. **The v-next plan covers ONLY the kernel program — five captured items have no
   home in it.** The contribution mechanism, skill triage, structure-flatten+PyPI,
   the build-process hygiene cluster, and the memory↔reality reconciliation
   mechanism are real captured work but appear nowhere in
   `loam-vnext-build-plan.md`. This roadmap is where they live (§5b–5c). Not a
   contradiction — a coverage gap this doc closes.

### Mis-prioritized / redundant (F2 — named with reasoning)

- **REDUNDANT (fold, don't track twice): "memory↔reality reconciliation
  mechanism" ≈ R-1's STATE-OF-LOAM + substrate-audit gate (N2).** The captured
  reconciliation mechanism ("auto-detect + heal stored-vs-truth divergence") and
  N2's STATE-OF-LOAM record + audit gate are the same failure-class from two
  entry points — both exist to stop a stored claim being trusted over live truth.
  **Recommendation:** build them as ONE mechanism (N2 is the substrate-liveness
  half; the reconciliation mechanism is the general stored-vs-truth half), not two
  parallel tracks. Listed once in N2 with a pointer from §5b.

- **MIS-PRIORITIZED upward: N2 (STATE-OF-LOAM record) deserves NEXT-UP, not
  LATER.** The reasoning-acceleration review ranks R-1 as the single
  highest-leverage reasoning-process fix, and this very roadmap had to perform R-1
  by hand to catch finding #1. A mechanism that prevents the most-expensive class
  loam has repeatedly hit (and that the persona keeps re-doing reactively) belongs
  at the front, not in a Phase-2 bucket. I have placed it at N2 accordingly — F2:
  the v-next plan slots it as a Phase-2 sibling of the failure-matrix; I'm
  promoting it ahead of most of Phase 2 because it is the cheapest, highest-ROI
  guard and it is *already overdue* (it would have prevented finding #1).

- **UNSCOPED (flag, don't fake a size): the loam contribution mechanism has no
  plan yet.** It is a NEW owner ask (2026-05-31) with no scoping pass. I have NOT
  invented a size or a slot in NEXT-UP for it — it needs a short "what did Cairn
  get / what maps to loam" scoping pass first (§5c). Forcing it into the order
  before it is scoped would be false confidence.

---

## 7. What's next (the persona drives from here)

**Top 3 unblocked, in order:**

1. **N1 — `.loam/` workspace layout + boundary lock (v-next F0.2 + P1.2).** Now
   the true critical-path head: FBM-LIVE (the brick it used to wait on) is done,
   so the boundary lock + `.loam/` scaffold is the next thing every later kernel
   piece reads/writes through. **Owner-gate first (G2):** ratify the repo shape
   (clean new tree in the canonical repo) + user-state physical home before any
   code.

2. **N2 — STATE-OF-LOAM operative-reality record + substrate-audit gate (R-1 +
   R-3), folding in the memory↔reality reconciliation mechanism.** Parallel track
   to N1 (no hard dependency — only needs live state to probe, which exists). The
   highest-leverage reasoning-process fix loam has; it would have prevented the
   single most expensive class of miss (built-≠-live), which THIS roadmap had to
   catch by hand.

3. **N3 — onboarding / init flow (v-next P1.4).** Sequenced after N1 (needs the
   `.loam/` home to seed state into), before the user-model that adapts that
   state. The intake funnel Phase 3 dogfoods.

**The dependency spine, in brief:**

```
FBM-LIVE (DONE) ──► N1 .loam/ layout + boundary lock [G2]
        │                    │
        │ (live state)       ├──► N3 onboarding/init ──► N4 user-model MVP [G5]
        ▼                    │
   N2 STATE-OF-LOAM + audit  └──► (kernel complete) ──► Phase-2 mechanisms
   gate  (parallel off DONE)            │                (visibility / full user-model /
                                        │                 failure-matrix / drift-audit /
                                        │                 workflow+cursor / adoption-loop /
                                        ▼                 non-tech-recovery)
                                Phase 3: fresh → onboard → [G6] migrate → fallback → [G7] retire

Independent of the kernel (ride existing cycles, any time):
  structure-flatten + PyPI · build-process hygiene cluster · skill triage ·
  loam contribution mechanism (scope first).
Continuous once their mechanism lands: pruning leg · the recurring loops.
Owner-wording-gated, rides alongside: doctrine enshrinement.
```

The critical path is **N1 → N3 → N4 → Phase 3**, with **N2 a high-ROI parallel
track** and Phase-2 mechanisms fanning out off the completed kernel. The hygiene
and structure items (§5b) and the contribution mechanism (§5c) are
kernel-independent and can ride any convenient cycle.

---

## 8. Maintenance contract (keep this roadmap live)

- **Move items between groups in place** (DONE / IN-FLIGHT / NEXT-UP / LATER) as
  state changes; do not rewrite the doc. Append new captured work to the right
  group.
- **Every status is reconciled against refs + live behaviour, not task titles**
  (the discipline that produced §6). When a status changes, update its evidence
  cell with the new SHA/test.
- **NEXT-UP's top item is always the next thing to build.** When it ships, move it
  to DONE and promote the next unblocked item. If the next item is genuinely
  ambiguous between two, present it as a fork with a recommendation (§4's
  sequencing notes), not a forced order.
- **New reconciliation findings append to §6** — the divergences are the signal
  the persona learns from.

---

*Principles applied: RECONCILE-against-reality (every status checked against the
git ref graph + live hooks, divergences surfaced in §6 not silently resolved);
information-trust (Tier-0 code state over task-title claims — caught the FBM
built-≠-live drift); scope↔confidence (N1/N2 near-parallel presented as a fork
with a recommendation rather than a false strict order; the contribution mechanism
left UNSCOPED rather than given fake confidence); value-laddering (every item's
"why" ladders to the prime directive); F2 (named the FBM-LIVE stale-doc
divergence, the memory↔reality≈N2 redundancy, and the N2-deserves-promotion
mis-prioritization, each with evidence and an alternative); proportionality.*
