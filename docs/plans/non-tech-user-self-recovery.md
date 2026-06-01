# non-tech-user self-recovery — the safety net that gets a stuck non-technical user unstuck — plan

**Status:** sub-plan-doc (PLAN-ONLY; no code authored by this drive).
**Working directory:** `/Users/lukeivers/loam` (canonical loam tree). This plan
was authored in the isolated worktree `/Users/lukeivers/loam-wt-selfrecovery` on
branch `plan/non-tech-self-recovery` to avoid racing a concurrent build in the
main tree; the build agent that picks this up works the canonical tree per the
manifest fence.
**Parent doctrine:** `docs/design/loam-doctrine.md` §"The two sides of leg 2 —
translation in, protection around" + §"Two standing constraints" #1 (the
non-negotiable floor, *"always on for everyone … invisibly, especially for a
non-technical user who cannot even name [the failures]"*). This system IS that
floor's last-resort safety net: when a guard fails anyway and the user is stuck,
the floor must still get them unstuck.
**Owner directive:** Telegram 13231 / 13225 (2026-05-31) — born from the real
6-hour silent-night comms failure (Telegram 13150–13195). The motivating
sentence: a non-technical user who hits a broken loam has *no way to diagnose or
recover* — they would be **"stuck forever."**
**Predecessors (load-bearing, Tier-0 read at plan-time @ `6b76f9ef`):**
- `feedback_user_distress_is_priority_diagnostic_signal.md` — the fire-alarm law (full statement: 2nd signal at the latest; explicitly names this self-recovery roadmap item as its product home).
- `feedback_narration_is_not_action.md` — the silent-night root cause (the stall bug + the compounding invisible-text bug; fired four times in one night).
- `feedback_telegram_outage_selfheal_and_confident_continue.md` — the comms-outage self-heal procedure (the out-of-band direct-send + reconnect-prep; the watchdog's recovery substrate).
- `framework/protection-matrix/` @ `6b76f9ef` (sealed `729ce44d`) — the failure-mode-guard matrix; this system is the STRUCTURAL GUARD that closes several of its named floor gaps (see §4 + §10).
- `framework/reversibility-primitive/src/loam/reversibility_primitive/` @ `6b76f9ef` — the activation-gate / fail-closed-refusal / handler-registry primitive (the safe-reset's reversibility floor).
- `framework/state-migration-engine/src/loam/state_migration_engine/envelope.py` @ `6b76f9ef` — `MigrationSafetyEnvelope.snapshot/.guard/.restore` (AC.MIG-SAFE.*): the EXISTING backup-first `.loam/` snapshot + restore primitive the safe-FBM-reset composes on (it does NOT re-implement byte-level backup).
- `framework/telegram-interface/src/loam/telegram_interface/{availability,fallback}.py` @ `6b76f9ef` — the comms-path liveness probe (`AvailabilityProbe`) + out-of-band fallback delivery (`write_fallback`) the watchdog reuses.
- `framework/self-correction/src/loam/self_correction/triggers.py` @ `6b76f9ef` — `build_trigger_from_user_report` + `TriggerSource.user_reported`: the EXISTING self-correction trigger surface the distress detector feeds (it does NOT build a parallel correction engine).
- `framework/dormancy/src/loam/dormancy/` @ `6b76f9ef` — the stuck/silent-agent detection rubric substrate the watchdog extends.
**BASELINE candidate:** current `main` @ `6b76f9ef` (`docs(plans): record failure-mode-guard-matrix commit SHAs`).
**Status-file target:** `docs/STATE.md` rollup + `docs/release-roadmap.md` §2 (backfilled at seal; see §9). Roadmap row: `docs/plans/loam-roadmap.md` line 109 ("Non-tech-user self-recovery").
**Quality bar:** dev-mode ODD/CDC; every AC outcome-shape; ≥1 outcome-altitude AC verified at a real entry-point with no pre-arranged state.

---

## §1 — Summary / TL;DR

**What ships:** the **safety net of the protection floor** — when loam breaks for
a non-technical user (silent agent, dead channel, a betrayal a guard missed), the
user gets *unstuck* without reading a stack trace, without knowing ODD, and
**without ever losing the irreplaceable store.** Four composable parts, each built
on an EXISTING primitive (Lens 1 — this is a *wiring* cycle, not a net-new-engine
cycle):

1. **Distress detection → forced self-diagnosis.** Repeated/escalating user
   distress ("are you there? / is this broken? / you keep saying X but don't") is
   detected on the inbound-message path and, **by the 2nd signal**, TRIPS a
   self-diagnosis: (a) is my last user-facing output actually reaching the user
   (did it go through the channel, or only to a terminal the user never sees), and
   (b) did I claim work I have not verifiably done (artifact-on-disk vs claim).
   Composes on the existing distress-signal law + the self-correction
   `user_reported` trigger surface.
2. **Watchdog.** Detects a stuck/silent agent or a dead comms channel
   *without* waiting for the user to notice. Composes on the dormancy detection
   rubric (stuck-agent) + the telegram-interface availability probe (dead-channel)
   + the outage self-heal procedure (recovery).
3. **Plain-language recovery.** Whatever the watchdog or self-diagnosis finds is
   rendered to the non-technical user as **clear plain-English steps to get
   unstuck** — never a stack trace, never internal IDs (abstraction-first voice).
4. **Safe hard-reset on the file-based memory / user-state store (FBM).** When the
   `.loam/` user-state is corrupted past plain recovery, reset it **backup-first**:
   snapshot the store, gate the destructive step behind the reversibility floor
   (fail-closed — no backup ⇒ refuse), THEN reset — so the irreplaceable store is
   **never lost.** Composes on `MigrationSafetyEnvelope.snapshot/.guard/.restore`.

**AC families:**
- **AC.SR-DISTRESS** — repeated distress on the inbound path trips the
  self-diagnosis routine by the 2nd signal; the diagnosis checks comms-path
  liveness + recent-actions-vs-claims.
- **AC.SR-WATCH** — a stuck/silent agent OR a dead channel is detected
  proactively (not user-prompted) and routed to recovery.
- **AC.SR-RECOVER** — the recovery surface a non-technical user sees is
  plain-language + actionable + carries zero internal vocabulary (no stack traces,
  AC-IDs, file paths, SHAs).
- **AC.SR-RESET** — the FBM hard-reset is **backup-first and fail-closed**: a reset
  with no recoverable snapshot is REFUSED; after a reset the pre-reset store is
  restorable byte-for-byte.
- **AC.SR-S** ★ — outcome-altitude: a real distress/stuck scenario at a real
  entry-point trips detection → produces a plain-language recovery → (for the
  reset branch) leaves the prior store restorable, with no pre-arranged state.

**Key decisions baked (recommendations in §12; forks for the dispatcher in §13):**
1. **Distress detection is a PreToolUse/inbound hook + a small persistent
   counter**, NOT an LLM intent-classifier on every message (`feedback_no_anthropic_api_key`:
   deterministic, no LLM call, no network). The counter is keyed to a short
   rolling window; the 2nd qualifying signal trips. Recommendation: adopt.
2. **The self-diagnosis routine is the EXISTING self-correction `user_reported`
   trigger**, fed by the distress hook (Lens 1 — `build_trigger_from_user_report`
   already exists). The distress hook is the new *detector*; the correction engine
   is reused. Recommendation: adopt.
3. **The safe-reset composes the migration-safety envelope's
   snapshot/guard/restore** — it does NOT re-implement backup. The reset declares
   `removes_user_state=true`, so the reversibility activation gate's fail-closed
   refusal (`ProtectionFloorRefusal`) already forbids a reset with no compensation
   path. Recommendation: adopt — this is the reversibility floor, for free.
4. **Plain-language rendering reuses the abstraction-first voice layer** the
   non-tech-user surface (v0.7.0) already ships, not a new renderer.

**F2 scope-realism (Lens 7):** this is a **safety net, and a safety net must be
proportionate** (doctrine §"Proportionality"). The fence is the *detection + the
recovery surface + the safe-reset wiring* — composing four existing primitives.
It is explicitly **NOT** a new correction engine, a new scheduler, a new channel
transport, or a new memory store. The single highest-stakes piece is the FBM
reset (it touches the irreplaceable store); §10 names the load-bearing risk that
a too-eager reset is itself a betrayal, and the design answers it with
backup-first + fail-closed-refusal as a HARD invariant, not a discipline.

---

## §2 — Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| Distress detector (inbound hook + counter) | **new hook** under `framework/self-correction/hooks/` (the engine it feeds) — registered in `settings.json` on the inbound/UserPromptSubmit surface | The detector's only job is to FEED the self-correction `user_reported` trigger; it belongs beside that engine, not in a new component. Lens 1: no new engine. |
| Self-diagnosis routine | **composes existing** `self-correction` (`build_trigger_from_user_report` + the controller's correction episode) — the new code is the *diagnosis check* (comms-path liveness + recent-actions-vs-claims), wired as the correction's first step | The correction engine, episode store, and notifier already exist. The new work is the diagnosis CONTENT, not the orchestration. |
| Watchdog (stuck-agent) | **composes** `framework/dormancy/` detection rubric; the new code is the recovery-routing on a detected stall | Dormancy already detects stuck/garbage output; this system adds the *route-to-plain-recovery* leg, not a new detector. |
| Watchdog (dead-channel) | **composes** `telegram-interface` `AvailabilityProbe` + the outage self-heal procedure | The availability probe + out-of-band fallback already exist; the watchdog wires "channel down ⇒ self-heal + out-of-band notify + queue low-confidence" per the outage memory. |
| Plain-language recovery surface | **new module** `framework/self-correction/src/loam/self_correction/recovery_surface.py` (the renderer) + a SKILL/template for the plain steps | The render is genuinely new (no existing "what a non-tech user does to get unstuck" surface), but it composes the abstraction-first voice. Lives beside the engine that triggers it. |
| Safe FBM hard-reset | **new entry-point** `framework/self-correction/src/loam/self_correction/safe_reset.py` (or a `loam recover` verb) that **delegates** `MigrationSafetyEnvelope.snapshot/.guard/.restore` | The byte-level backup/restore + the fail-closed gate ALREADY EXIST in the migration-safety envelope. The new code is the *reset orchestration* that calls them in the right order; it does NOT touch `.loam/` bytes itself except through the envelope. |
| The user-facing recovery verb | a `loam recover` verb (or the persona-invoked recovery flow) registered via `loam.cli.subcommands` | Mirrors how `loam audit` / `loam guards` register; persona-invokable + non-tech-user-invokable. (Verb-name is FORK F-1.) |

---

## §3 — Halt-and-surface recorded DURING plan authoring

Decisions made autonomously at plan-time (recorded, not gates the builder
re-asks) plus the genuine forks the builder/dispatcher must respect.

**Recorded autonomous (no re-ask needed):**
- **R-1.** The four parts compose on FOUR existing, sealed primitives (verified
  Tier-0 this drive): self-correction triggers (`build_trigger_from_user_report`),
  dormancy detection, telegram-interface availability+fallback, and the
  migration-safety envelope's snapshot/guard/restore. This is a wiring cycle, not a
  net-new-engine cycle. Decided: compose, do not rebuild (Lens 1).
- **R-2.** Distress detection is deterministic (a counter + a phrase/escalation
  rubric on the inbound path), NOT an LLM intent-classifier
  (`feedback_no_anthropic_api_key` — no API key, no per-message LLM call). The
  rubric is the same shape as the existing distress-signal memory ("are you there
  / is this broken / you keep saying X but don't"). The 2nd qualifying signal in
  the rolling window trips (per the fire-alarm law: "2nd signal at the latest").
- **R-3.** The safe-reset NEVER touches `.loam/` bytes directly — every byte-level
  operation goes through `MigrationSafetyEnvelope` so backup-first + fail-closed
  refusal are inherited, not re-implemented (the reversibility floor is structural,
  not a discipline the reset re-derives).
- **R-4.** The plain-language recovery surface carries ZERO internal vocabulary by
  construction (the abstraction-first contract from v0.7.0's stranger-clone probe);
  this is an AC (AC.SR-RECOVER), not a style preference.

**Gates the builder must respect (genuine forks → §13):**
- **F-1** — the user-facing entry-point: a `loam recover` CLI verb, a persona-flow,
  or both?
- **F-2** — the distress-detection counter's window + trip threshold parameters.
- **F-3** — does the safe-reset run interactively (asks the user to confirm in
  plain language) or autonomously-with-surface, given the store is irreplaceable?
- **F-4** — does this cycle also ADD the two missing matrix rows
  (`FM.COMMS-PATH-DEAD`, and flip `FM.NARRATION-NOT-ACTION` to guarded), or is the
  matrix backfill a separate doc cycle?

---

## §4 — Spec-objective placement (ladder-up)

- **Binds to:** the **protection side of leg 2** of the doctrine, specifically
  §"Two standing constraints" #1 — *the non-negotiable floor, "always on for
  everyone … invisibly, especially for a non-technical user who cannot even name
  [the failures]."* This system is the floor's **safety net**: when a guard fails
  anyway, the floor must still get the user unstuck. Through the doctrine it binds
  to `VALUE_PROPOSITION.md` §"prime objective" whose acceptance condition is:
  *"when the user … is being betrayed by a known AI failure mode loam should have
  guarded, the prime objective has failed."* A non-technical user who is "stuck
  forever" is the maximal form of that failure.
- **Ladders up to** the **prime directive** (`feedback_loam_prime_directive_user_tuned_translation`):
  loam is useful only when it WORKS for *that* person; a non-technical person who
  cannot self-recover is the person loam most exists to serve.
- **Closes named matrix gaps (the structural-guard wiring):**
  - **FM.NARRATION-NOT-ACTION** (floor gap, `NO-PROGRAMMATIC`) — the silent-night
    failure mode. The distress detector + self-diagnosis is the first *programmatic*
    leg over it: a user who is stuck because the agent narrated-without-acting now
    trips a diagnosis that checks "did I claim work I have not done (artifact on
    disk)?" — the exact narration-not-action check.
  - **FM.COMMS-PATH-DEAD** (NOT YET a matrix row — see §10 finding) — the
    compounding invisible-text bug (replies to a terminal the user never sees). The
    watchdog's dead-channel detection + the self-diagnosis's "is my output actually
    reaching the user?" check is the programmatic guard for it.
  - Composes on (does not replace) **FM.DESTRUCTIVE-PRUNE**'s reversibility
    primitive for the safe-reset's backup-first floor.
- **AC.PO binding:** VALUE_PROPOSITION harness test — yes, it adds `loam recover` +
  the watchdog to the persona's toolkit; primary-persona test — yes, it reduces the
  non-tech user's translation burden to *zero* at the worst moment (they express
  confusion in plain English; loam diagnoses + recovers without them naming
  anything).

---

## §5 — Acceptance criteria (outcome-shape; method-in-AC test passed on each)

### AC.SR-DISTRESS.1 — repeated distress trips self-diagnosis by the 2nd signal
On the inbound-message path, a 2nd qualifying distress signal within the detection
window TRIPS the self-diagnosis routine (a self-correction `user_reported` episode
or equivalent) — it does NOT wait for the user to escalate to an explicit
"diagnose this." *Outcome-shape: pins the 2nd-signal trip + that a diagnosis runs;
the counter/rubric implementation is the builder's.*

### AC.SR-DISTRESS.2 — the self-diagnosis checks the two load-bearing things
The triggered diagnosis checks, at minimum, (a) comms-path liveness — is the
agent's user-facing output actually reaching the user's channel vs a terminal —
and (b) recent-actions-vs-claims — was work claimed that has no artifact on disk
(the narration-not-action check). *Outcome-shape: pins WHAT the diagnosis must
establish (the two silent-night root causes); the check method is the builder's.*

### AC.SR-WATCH.1 — a stuck/silent agent is detected without user prompting
A stalled or silent agent (no progress past a tunable threshold) is detected by the
watchdog and routed to recovery, with NO user distress signal required to trigger
it. *Outcome-shape: pins proactive stuck-detection; composes the dormancy rubric,
threshold is the builder's.*

### AC.SR-WATCH.2 — a dead comms channel is detected and self-heal is attempted
A down comms channel (availability probe negative) is detected and triggers the
outage self-heal path (attempt reconnect + out-of-band notify + queue
low-confidence work), without waiting for the user to report silence.
*Outcome-shape: pins dead-channel detection + self-heal attempt; composes the
availability probe + outage procedure.*

### AC.SR-RECOVER.1 — the recovery surface is plain-language and actionable
The surface a non-technical user receives when detection fires is plain-English,
gives a concrete next action to get unstuck, and is satisfiable by a non-technical
user (no requirement to read logs, run dev commands, or know internal concepts).
*Outcome-shape: pins the plain-language + actionable property; the wording template
is the builder's.*

### AC.SR-RECOVER.2 — the recovery surface carries zero internal vocabulary
The user-facing recovery text contains no stack traces, AC-IDs, commit SHAs,
file paths, agent-IDs, or ODD/methodology vocabulary (the abstraction-first
contract; the v0.7.0 stranger-clone probe shape applied to the recovery surface).
*Outcome-shape: pins the zero-internal-vocabulary invariant; verifiable by a probe
over the rendered text.*

### AC.SR-RESET.1 — the FBM hard-reset is backup-first and fail-closed
A hard-reset of the `.loam/` user-state store takes a recoverable snapshot BEFORE
any destructive step, and a reset attempt with no recoverable snapshot path is
REFUSED (fail-closed — the reversibility activation gate's `ProtectionFloorRefusal`
fires). *Outcome-shape: pins backup-first + fail-closed-refusal as a HARD invariant;
the orchestration delegates to `MigrationSafetyEnvelope`, which is the builder's
composition call.*

### AC.SR-RESET.2 — after a reset the prior store is restorable byte-for-byte
After a hard-reset, the pre-reset `.loam/` store is restorable from the snapshot
byte-for-byte (the irreplaceable store is never lost — only reset behind a
recoverable backup). *Outcome-shape: pins the never-lose-the-store invariant; the
restore path is `MigrationSafetyEnvelope.restore`.*

### ★ AC.SR-S.1 — outcome-altitude: a real stuck scenario trips, recovers, and preserves the store
**`outcome-altitude: true`.** A real scenario at the production entry-point, with
NO pre-arranged state: (a) a simulated stuck/silent condition OR a 2nd distress
signal trips detection through the real detector; (b) the system produces a real
plain-language recovery surface (verified to carry zero internal vocabulary); and
(c) for the reset branch, after running the real reset entry-point the prior
`.loam/` store is restorable byte-for-byte (and a no-backup reset is refused). The
test invokes the real entry-points; it does not stub the detector, pre-seed the
recovery text, or fake the snapshot. *Outcome-shape: pins a real end-to-end
trip→recover→preserve; satisfiable by any implementation.* *(Per
`feedback_test_outcome_altitude_required`: a STUB-class test that pre-arranges the
trip or the snapshot does NOT satisfy this AC — the entry-points must run for real.)*

---

## §6 — Build steps (method-level guidance only; builder's call per ODD §1.1)

Single component touched (`self-correction`, extended) + composes-on four sealed
primitives. Per-cycle:

1. **Manifest** at `docs/plans/non-tech-user-self-recovery.manifest.yaml` (paired,
   `schema_version: 3`); component `self-correction` (existing — advance its
   sidecar, `new_component: false`); `extra_allowed_prefixes` for the new hook +
   modules under `framework/self-correction/`.
2. **Source edits in dependency order:** the distress-detection hook + counter →
   the self-diagnosis check content (fed into the existing `user_reported` trigger)
   → the watchdog routing (compose dormancy + availability) → the
   `recovery_surface` renderer → the `safe_reset` orchestration (delegating
   `MigrationSafetyEnvelope`) → the `loam recover` verb registration.
3. **Tests authored** per AC family above, one file per family; the
   outcome-altitude AC (AC.SR-S.1) drives the real entry-point with no pre-arranged
   state.
4. **Apply** via `loam amend apply` against the manifest (the sealed-component
   bookkeeping mechanism — `feedback_dispatch_explicit_loam_amend_apply`).
5. **Seal** via `loam amend seal`; advance the `self-correction` sidecar.
6. **Smoke:** a single real run that trips detection on a simulated stuck/distress
   condition and produces the plain-language recovery surface in a cold workspace;
   plus a real `safe_reset` round-trip (snapshot → reset → restore) verifying the
   store survives.

---

## §7 — Out of scope (deferred + when)

1. **A new correction/self-diagnosis ENGINE.** The self-correction controller,
   episode store, and notifier already exist; this cycle adds the *detector* + the
   *diagnosis content* + the *recovery surface*, not a parallel engine. *Deferred:
   never — composition is the design.*
2. **A new comms transport or a new channel.** The watchdog composes the existing
   availability probe + out-of-band fallback; it does not build a new channel.
3. **Auto-fixing the root cause of an arbitrary stall.** The watchdog detects +
   routes to recovery + (for the channel) self-heals; it does not auto-repair an
   arbitrary stuck build. *Deferred: per-failure-class remediation is downstream.*
4. **The full adaptive user-model's fast-down-on-distress trigger.** This system
   SHARES the distress detector with that trigger (roadmap line 109), but the
   tone/learning-appetite down-shift is the user-model's surface, not this one.
   *Deferred to: the full adaptive user-model cycle.*
5. **The owner work-visibility window (#37).** Related (a live view of in-flight
   work), but a distinct QoL feature with its own dependency (live `.loam/` state).
   *Deferred to: its own cycle.*
6. **Adding the missing matrix rows** (`FM.COMMS-PATH-DEAD`; flipping
   `FM.NARRATION-NOT-ACTION` to partially-guarded). *Deferred per FORK F-4 — may
   fold into this cycle or be a separate doc backfill.*

---

## §8 — Halt triggers (in-flight; abort the build + surface)

- The safe-reset would touch `.loam/` bytes WITHOUT going through
  `MigrationSafetyEnvelope` (or any path where backup-first / fail-closed is not
  structurally inherited) → HALT. The reset must never have a code path that can
  delete the store without a recoverable snapshot. This is the highest-stakes
  invariant in the plan.
- The distress detector would require an LLM call / network / API key to classify
  a message → HALT (`feedback_no_anthropic_api_key`: the detector must be
  deterministic; if it can't be, the design is wrong — surface it).
- Composing the watchdog would require EDITING a sealed primitive's source
  (dormancy / availability / the migration envelope) rather than calling its public
  surface → out of fence; HALT (this cycle wires + extends `self-correction`; it
  does not modify the sealed primitives it composes).
- The outcome-altitude test (AC.SR-S.1) can only be made to pass by pre-arranging
  the trip or the snapshot → HALT: a STUB-class test does not satisfy an
  outcome-altitude AC; the entry-points must run for real.
- The plain-language recovery surface cannot be rendered without leaking an
  internal ID/path → HALT: AC.SR-RECOVER.2 is a hard invariant, not best-effort.

---

## §9 — Bookkeeping (backfill at seal)

- `docs/STATE.md` — append the rollup: objective sentence + seal SHA + the
  "non-tech user can self-recover" headline + which matrix gaps it guards.
- `docs/release-roadmap.md` §2 — new row with the seal anchor.
- `docs/plans/loam-roadmap.md` line 109 — mark the self-recovery row built (or
  its first slice), noting the shared distress detector with the user-model.
- `docs/design/protection-matrix.md` (+ the matrix YAML) — IF F-4 folds in: add
  `FM.COMMS-PATH-DEAD` and flip `FM.NARRATION-NOT-ACTION`'s guard from
  `persona-discipline only` to the new programmatic guard (regenerated, not
  hand-edited).
- A `*.migration.yaml` declaring the user-state interaction: the safe-reset is a
  user-state operation; declare it so `check_migration_declared` passes at publish
  and the reversibility class is explicit.
- Parent-doctrine backfill: a pointer from `docs/design/loam-doctrine.md`
  §"non-negotiable floor" to this system as the floor's safety net (doc-only).

---

## §10 — F2 Ruthless Feedback (honest doubts + named risks)

1. **The matrix is missing a `FM.COMMS-PATH-DEAD` row — and that gap is exactly
   the silent-night's compounding bug.** *Disagreement:* the protection matrix
   names `FM.NARRATION-NOT-ACTION` (the stall) but NOT the *invisible-text* bug
   (replies routed to a terminal the user never sees) — yet the silent-night memory
   is explicit that these were **two stacked bugs**, and the second is what made
   the stall look like silence to Luke. *Evidence:* `docs/design/protection-matrix.md`
   has no COMMS row (grep, this drive); `feedback_narration_is_not_action.md`
   §"The two stacked bugs" names the invisible-text bug as distinct. *Alternative:*
   this system's dead-channel watchdog + the "is my output reaching the user?"
   diagnosis IS the programmatic guard for that unnamed mode — so the cycle should
   ADD the row and wire this system as its guard (FORK F-4). Surfacing the missing
   row is itself the F2 value.

2. **A too-eager hard-reset is its own betrayal — the recursive risk.** *Risk:* a
   self-recovery system whose reset fires too readily would DESTROY the
   irreplaceable store while "helping" — the `FM.DESTRUCTIVE-PRUNE` failure, applied
   to the user's whole memory, by the very system meant to protect them.
   *Evidence:* the owner's words "WITHOUT losing the irreplaceable store" + the
   reversibility floor's whole reason to exist. *Mitigation baked in:* AC.SR-RESET.1
   makes backup-first + fail-closed-refusal a HARD invariant (delegated to
   `MigrationSafetyEnvelope`, which already refuses a destructive op with no
   compensation path); §8 halts on any reset code path that bypasses it; and the
   reset is the LAST resort (plain recovery is tried first, §1 part 3→4 ordering).
   FORK F-3 surfaces whether the reset should also require an explicit plain-language
   user confirm.

3. **Detection sensitivity is a genuine tension and I cannot fully resolve it at
   plan-time.** *Doubt:* trip too early (2nd signal) and a chatty non-distress user
   triggers spurious self-diagnosis (annoying, erodes trust); trip too late and we
   reproduce the 6-signal silent-night. *Evidence:* the fire-alarm law mandates
   "2nd signal at the latest" — so the bias MUST be toward early. *Resolution:* bias
   early per the law; make the window + threshold tunable (FORK F-2); and note that
   a spurious self-diagnosis is cheap + invisible-if-clean (it checks comms-path +
   artifact state and, finding nothing wrong, says nothing), whereas a missed one is
   the "stuck forever" failure. The asymmetry favors early. This is a real
   signal-weighing call (Lens 6) the dispatcher may want to see, hence F-2.

4. **Honest scope doubt: the watchdog's stuck-agent leg leans on dormancy, which I
   read at the rubric level, not exhaustively.** *Doubt:* dormancy's detection is
   built for *output-garbage / silence* rubrics; whether a *narration-without-action
   stall* (turn ends cleanly but did nothing) is detectable by it is not certain
   from my read. *Alternative:* the distress-detection leg is the BACKSTOP for that
   exact case (the user notices the stall and signals) — so even if the watchdog's
   proactive leg misses a clean-narration stall, the distress leg catches it. The
   two legs are deliberately redundant on the silent-night failure mode; that
   redundancy is a feature, not duplication.

---

## §11 — Provenance trail (every load-bearing source)

**Doctrine + objective:**
- `docs/design/loam-doctrine.md` — §"two sides of leg 2" (protection pillar); §"Two standing constraints" #1 (the non-negotiable floor, "invisibly, especially for a non-technical user") + #2 (proportionality — the safety-net must be proportionate).
- `docs/VALUE_PROPOSITION.md` — §"prime objective" (the protection-failure condition).
- `feedback_loam_prime_directive_user_tuned_translation.md` — loam is useful only when it works for *that* person; the non-tech user who can't self-recover is the maximal failure.

**Failure-mode law + root causes (the motivation):**
- `feedback_user_distress_is_priority_diagnostic_signal.md` — the fire-alarm law (2nd-signal trip; the STOP-and-self-diagnose routine; explicitly names this self-recovery system as its product home).
- `feedback_narration_is_not_action.md` — the silent-night root cause; §"The two stacked bugs" (the stall bug + the invisible-text/comms bug — the basis for the §10 missing-matrix-row finding).
- `feedback_telegram_outage_selfheal_and_confident_continue.md` — the outage self-heal procedure (the watchdog's dead-channel recovery substrate + the out-of-band direct-send).

**Compose-on primitives (Tier-0 read this drive @ `6b76f9ef`):**
- `framework/self-correction/src/loam/self_correction/triggers.py` — `build_trigger_from_user_report` + `TriggerSource.user_reported` (the self-diagnosis trigger surface the distress hook feeds); `controller.py` (the correction episode runtime).
- `framework/dormancy/src/loam/dormancy/detection.py` — the stuck/silent-agent detection rubric substrate.
- `framework/telegram-interface/src/loam/telegram_interface/availability.py` (`AvailabilityProbe`, `AvailabilityState`) + `fallback.py` (`write_fallback`, the out-of-band surface) — the dead-channel detection + recovery.
- `framework/state-migration-engine/src/loam/state_migration_engine/envelope.py` — `MigrationSafetyEnvelope.snapshot` (AC.MIG-SAFE.1 backup-first), `.guard` (AC.MIG-SAFE.4 fail-closed `ProtectionFloorRefusal`), `.restore` (AC.MIG-SAFE.2 byte-level rollback) — the safe-reset's entire backup/restore floor.
- `framework/reversibility-primitive/src/loam/reversibility_primitive/{activation_gate,controller}.py` — the fail-closed activation gate + handler registry the envelope's `.guard` composes.
- `framework/protection-matrix/` (`docs/design/protection-matrix.md`) — the matrix; `FM.NARRATION-NOT-ACTION` floor gap (the mode this guards) + the absent `FM.COMMS-PATH-DEAD` row (the §10 finding).

**Roadmap:**
- `docs/plans/loam-roadmap.md` line 109 — the "Non-tech-user self-recovery" row (deps: N1 state-to-reset + full user-model; shares the distress detector with the user-model's fast-down trigger).

**Methodology:**
- `CLAUDE.md` Lens 1 (Claude-leverage / compose-on-primitives), Lens 3 (ODD), Lens 4 (scope↔confidence — forks-with-recs), Lens 6 (M5 — the detection-sensitivity call), Lens 7 (RF).
- `feedback_no_anthropic_api_key.md` (the detector is deterministic, no LLM); `feedback_test_outcome_altitude_required.md` (AC.SR-S.1); `feedback_abstraction_first_default.md` (AC.SR-RECOVER.2).

---

## §12 — Summary of named decisions (owner-readable recommendations)

1. **Compose on four existing primitives, don't rebuild.** *Recommendation: adopt.*
   Lens 1 — the self-correction trigger, dormancy detection, availability+fallback,
   and the migration-safety envelope all exist and are sealed. This is a wiring
   cycle.
2. **Distress detection is a deterministic inbound hook + counter, 2nd-signal
   trip.** *Recommendation: adopt.* No LLM/API (`feedback_no_anthropic_api_key`);
   the 2nd-signal trip is mandated by the fire-alarm law.
3. **The self-diagnosis is the existing `user_reported` correction trigger, fed by
   the new detector.** *Recommendation: adopt.* The engine exists; the new work is
   the diagnosis content (comms-path liveness + actions-vs-claims).
4. **The safe-reset delegates the migration-safety envelope's
   snapshot/guard/restore.** *Recommendation: adopt — this is the reversibility
   floor for free.* Backup-first + fail-closed-refusal become inherited invariants,
   not re-implemented discipline.
5. **The plain-language recovery surface reuses the abstraction-first voice and
   carries zero internal vocabulary (an AC, not a style note).** *Recommendation:
   adopt.* The v0.7.0 stranger-clone probe shape applied to the recovery surface.
6. **This cycle structurally guards two matrix failure modes
   (`FM.NARRATION-NOT-ACTION`, the unnamed `FM.COMMS-PATH-DEAD`).**
   *Recommendation: adopt + wire this system as their guard.* The gap-closure is a
   first-class deliverable, not a side effect.

---

## §13 — Forks for the dispatcher to rule (with recommendations)

- **F-1 — the user-facing entry-point shape.** (a) a `loam recover` CLI verb, (b)
  a persona-invoked recovery flow, or (c) both. *Recommendation: (c) both — the verb
  for the deterministic/non-tech entry-point, the persona-flow for the in-conversation
  trip.* Signals: the non-tech user needs a single named thing to run; the persona
  needs the in-flight trip. Low cost to ship both since they share the same
  underlying detect→recover→reset core.
- **F-2 — distress-detection window + threshold.** Exact rolling-window size +
  what counts as a "qualifying" signal. *Recommendation: bias EARLY (2nd signal per
  the fire-alarm law), make both tunable, default to a short window.* Signals (Lens
  6): a spurious self-diagnosis is cheap + silent-if-clean; a missed one is the
  "stuck forever" failure — the asymmetry favors early. Reasonable people could want
  it less twitchy, so it is a fork, not an autonomous ruling.
- **F-3 — does the safe-reset require an explicit plain-language user confirm?**
  (a) reset autonomously-with-surface (backup-first makes it safe), or (b) require a
  plain-English "yes, reset" from the user first. *Recommendation: (b) require the
  plain confirm — the store is irreplaceable + the reset is the last resort, so the
  reversibility floor (backup-first) AND a human-in-the-loop confirm is the
  proportionate belt-and-suspenders for the highest-stakes operation.* Signals
  (Lens 6): blast radius (the whole store) + reversibility (recoverable, but a
  non-tech user may not know to restore) → favor the confirm. The dispatcher may
  weigh "a stuck user can't always answer a confirm" the other way, hence a fork.
- **F-4 — fold the matrix-row backfill into this cycle?** (a) ADD
  `FM.COMMS-PATH-DEAD` + flip `FM.NARRATION-NOT-ACTION` to guarded in THIS cycle's
  seal, or (b) ship the system here and backfill the matrix in a separate doc cycle.
  *Recommendation: (a) fold in — wiring the guard and not recording it in the matrix
  leaves the matrix lying about its own coverage (the `FM.HALLUCINATION` failure
  applied to loam's protection ledger).* The matrix is generated from the YAML, so
  the backfill is a YAML edit + regenerate, cheap.

---

## §14 — Method-decision record (builder, post-build)

ODD §1.1: builder owns method, this plan owns scope. The fork rulings
(F-1=(c) both, F-2=bias-early, F-3=require explicit confirm, **F-4=REMOVED
from this cycle** — the matrix backfill is a dispatcher-owned follow-on,
since the matrix rows live in the protection-matrix sealed component, a
DIFFERENT fence) were baked into the dispatch and are honored below.

**D-build.1 — Distress detection (AC.SR-DISTRESS.1).** A deterministic
phrase/escalation rubric (`classify_distress`) + a persistent rolling-window
counter (`DistressDetector`, JSON state, atomic write). Three qualifying
classes (presence / broken / unfulfilled) matching the silent-night distress
shapes. The 2nd qualifying signal in the window trips (default threshold 2,
window 600s; both tunable per F-2 bias-early). No LLM, no network
(`feedback_no_anthropic_api_key`). The hook entry-point
(`hooks/distress_detector.py:main`) reads the inbound JSON, advances the
counter, emits a trip decision on stdout. **The hook entry-point + tests are
the SEALED deliverable; wiring into a live `settings.json` is owner-gated
instance-config, left out of this cycle.**

**D-build.2 — Self-diagnosis content (AC.SR-DISTRESS.2).** `self_diagnosis.py`
— two pure checks: comms-path liveness (injected probe; a probe error counts
as "not reaching") + recent-actions-vs-claims (artifact-on-disk existence per
`ClaimCheck`). `open_user_reported_correction` feeds the EXISTING
`build_trigger_from_user_report` → `controller.intake` — the trip opens a real
correction episode via the sealed engine; no parallel engine (Lens 1).

**D-build.3 — Watchdog (AC.SR-WATCH.1/.2).** `watchdog.py` — `StallWatchdog`
heartbeat (progress quiet past a tunable threshold = stuck, no user signal)
+ `check_channel_and_self_heal` (injected async channel probe → on dead, the
out-of-band self-heal delivery). `availability_probe_to_channel_probe` adapts
the telegram-interface `AvailabilityProbe.probe_once` to the thin bool the
watchdog consumes — composition is a public-surface library call, the sealed
primitives are not edited. The stall heartbeat is the route-to-recovery leg,
NOT a re-implementation of dormancy's degradation FSM (plan §10 #4 — the
distress leg is the deliberate redundant backstop for a clean-narration stall).

**D-build.4 — Plain-language recovery surface (AC.SR-RECOVER.1/.2).**
`recovery_surface.py` — five situation blocks (headline + concrete next
action, both plain-English) + a zero-internal-vocabulary probe
(`find_internal_vocabulary`) covering AC-IDs / SHAs / file+module paths /
tracebacks / agent-IDs / ODD-methodology vocab. `render_recovery` self-checks
and RAISES `RecoverySurfaceLeak` on a leak (the hard invariant, plan §8 — not
best-effort).

**D-build.5 — Safe FBM hard-reset (AC.SR-RESET.1/.2, highest-stakes).**
`safe_reset.py` — `SafeFbmReset` orchestration that DELEGATES
`MigrationSafetyEnvelope.snapshot/.guard/.restore`; never touches `.loam/`
bytes except through the envelope (plan §8 halt-trigger 1). Order: require the
explicit plain-English confirm (F-3 → `ResetNotConfirmed` before any
destructive step) → snapshot (backup-first) → register the snapshot as the
compensation binding → `guard` (irreversible class; no-binding ⇒
`ProtectionFloorRefusal` — fail-closed) → destructive remove. `restore` brings
the pre-reset store back byte-for-byte. The backup/snapshot lives OUTSIDE
`.loam/` (`.loam-recovery/`) so it survives the reset.

**D-build.6 — User-facing recover verb (F-1 = (c) both).** `recover_cli.py`
— `loam recover check` (read-only plain-language status) + `loam recover reset`
(the safe reset, requires `--confirm "yes, start fresh"`). Registered via the
`loam.cli.subcommands` entry-point group (symmetric to `loam amend`) +
standalone `loam-recover` script. The persona-flow half of F-1 is the
in-conversation distress trip (D-build.1/.2 sharing the same core).

**Outcome-altitude (★ AC.SR-S.1).**
`test_AC_SR_S_outcome_altitude_real_entrypoint.py` drives the real
entry-points with NO pre-arranged state: an empty distress counter takes a
real 2nd-signal trip; a real recovery surface is rendered + vocab-probed; the
real `loam recover reset` verb runs (refused without confirm, then confirmed)
and the user's real `.loam/` data is restored byte-for-byte from the snapshot
the production path made. No stubbed detector, no pre-seeded text, no faked
snapshot.

**Env note.** The worktree had no installed loam env; the build used a
worktree-local gitignored venv (`.venv-build/`, excluded via git
`info/exclude`, not committed) with the loam component packages
editable-installed so the cross-importing `loam.*` namespace resolved. Pure
dev-mode bootstrap.

**Commit SHAs (backfilled post-seal):**
- BASELINE (source-edit): `fa618f45` (the plan-doc commit; re-baselined from
  the plan-time `6b76f9ef` so the seal-diff window narrows to this surface).
- `loam amend apply` auto-commit: `6811fcd2`.
- §14 builder-record corrective (amendment tip): `ec28630e`.
- `loam amend seal`: `73090c97` (sidecar `SEAL_COMMIT` → `ec28630e`).
- Component: `self-correction` (existing — sidecar advanced; `new_component: false`).
- Branch `plan/non-tech-self-recovery` — NOT pushed, NOT merged (owner-gated;
  the dispatcher handles merge-on-seal).
