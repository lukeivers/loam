# N3 — onboarding / init flow (the translate-in intake for a brand-new instance)

**Status:** sub-plan-doc, PLAN-ONLY (plan-before-code). **Research-grade** —
this is USER-FACING product design; the UX/voice calls are surfaced as
forks-with-recommendations for an owner ruling, NOT locked unilaterally.
Authored 2026-05-31.
**Working directory:** `/Users/lukeivers/loam/`.
**Parent plans:**
- `docs/plans/loam-roadmap.md` §4 row **N3** (critical path `N1 → N3 → N4 → Phase 3`; N3 is now the next unblocked kernel slice — N1 is sealed to `main`).
- `docs/plans/loam-vnext-build-plan.md` Phase-1 **P1.4** (the onboarding/init slice).

**Predecessors (load-bearing prior seals + artefacts, Tier-0 on disk 2026-05-31):**
- `9aa611b` — **`main` HEAD**: carries the N1 boundary LOCK (ADR-0001 + the declared allowlist `user-state-homes.yaml` + gate 9 `check_boundary_respected`), the migration engine, FBM-LIVE, and the STATE-OF-LOAM audit. **This is the BASELINE N3 evolves in place on (G2 evolve-in-place ratified).**
- `01f3b40` — **P1.2 the `.loam/` scaffold (already done)**: `establish_loam_layout()`, the declared dirs (`migrations/`, `user-model/`, `session-model/`, `environment-model/`), the self-describing README + boundary-rule prose. **N3 SEEDS INTO this scaffold; it does NOT re-scaffold.**
- `8d160b9` — ADR-0001 + `docs/design/adr/user-state-homes.yaml` (the two legal homes: `~/.claude/` global, `<ws>/.loam/` scoped). **N3's seeded state MUST land inside these homes — gate 9 enforces it.**
- The **existing onboarding ritual** (NOT a seal SHA — a live component): `framework/workspace-bootstrap/src/loam/workspace_bootstrap/onboarding.py` + `onboarding_cli.py`. A six-question **capability-activation** ritual (language / channel / safety-profile / extractor / watch / auto-skill-capture), wired as the `loam … onboard` subcommand. **CRITICAL F2 (§10.1): this is NOT the doctrine's operating-loop intake — it activates capabilities; it does not infer the user's action-oriented end-intent or seed a per-user profile. N3 COMPOSES ON it; it does not duplicate or replace it.**
- `docs/design/adaptive-interaction-model.md` (AIM) — the **N4 adapter's** target schema: `~/.claude/INTERACTION-MODEL.md`, a `component × axis → {value, confidence, evidence}` matrix, openness-biased, every cell starting at `confidence: prior`. **N3 seeds the prior-confidence initial state this matrix begins from; N4 is the engine that moves the cells from evidence.** Build the intake before the adapter (the adapter needs seeded state to adapt).
- `docs/design/loam-doctrine.md` — THE operating loop (infer → propose → verify → learn), the over-reach guard, the "just lost my job as a CTO" worked example. **This IS onboarding's spine.**

**BASELINE (pre-build tip):** `9aa611b` (current `main` HEAD).
**Status-file target:** `<workspace>/.scratch/claude-output/n3-onboarding-status.md` (builder writes build progress here).
**Quality bar:** a **real brand-new instance** (genuinely empty user-state — no `INTERACTION-MODEL.md`, no profile, fresh `.loam/`) runs onboarding **via the real entry-point** and ends with seeded user-state in the **correct two-tier homes** (gate-9 clean), where the seeded state is a *verified hypothesis* the user confirmed — not a silent inference. Verification-heavy, because for a brand-new user loam's inference is at its most fallible.

**Scope-tightness (F4):** TIGHT where the doctrine + N1 already settled it (the operating loop is the intake's spine; the two homes are the only legal seed targets; compose-on-existing-ritual not rebuild). FORKED-with-recommendation where it is genuinely the **owner's product call** (how much to ASK vs INFER; what the minimum seed is; where the over-reach line falls; the entry trigger; the voice). Method stays the builder's call; this plan does not prescribe files or symbols.

---

## §1. Summary / TL;DR

N3 ships the **translate-in intake** — the first-run funnel that runs loam's
operating loop (infer → propose → verify → learn) on a brand-new user and
**seeds the initial per-user state** the rest of the kernel reads. It is the
front door of the prime directive: per-user-tuned translation *begins here*,
with the user loam knows least about, which is exactly why the loop's
**verification** discipline is load-bearing at this moment above all others.

The plan's central design stance, surfaced for owner ruling: **for a
brand-new user, infer little and verify almost everything.** The doctrine says
inference is most fallible for a user we barely know; onboarding therefore
**asks a small number of high-leverage questions, proposes a healthy shape it
infers from them, and surfaces that proposal for confirmation before any of it
is written as the user's seeded state.** The over-reach guard bounds the
ambition: onboarding seeds the *minimum useful* prior, not an elaborate model —
the elaborate version is something N4 grows from evidence, not something the
first touch front-loads.

Three AC families:

- **AC.ONINTAKE.\*** — the intake runs the operating loop on a new user: it
  surfaces a small set of intake prompts, **proposes** an inferred end-intent
  shape, and **surfaces the proposal for verification** before committing —
  inference is never silently written as fact.
- **AC.ONSEED.\*** — the verified result is **seeded as initial user-state into
  the two-tier home**, respecting the N1 boundary (gate 9 GREEN): the global
  half lands under `~/.claude/`, the workspace-scoped half under `<ws>/.loam/`;
  the seeded interaction-model is at `confidence: prior` so N4 can move it.
- **AC.ONFIRE.\*** — onboarding **fires on a brand-new instance** through a real
  entry-point (the trigger — fork D-4) and is **idempotent / non-destructive**:
  it never clobbers existing user-state on a re-run (the protection floor).
  Includes the ★ **outcome-altitude** AC: a genuinely-empty instance, run through
  the real entry-point, ends with correctly-homed seeded state.

**Key stances surfaced (the OWNER-FACING product calls — §11 forks):**
1. **D-1 — ask-vs-infer balance.** Verification-heavy: a *small* set of asked
   questions, an inferred *proposal* from them, confirmed before commit.
   (Recommended: the lean confirm-the-proposal shape.)
2. **D-2 — the minimum seed (what state, where).** Seed the smallest prior that
   makes the next session useful — the user's stated end-intent(s) as
   objective(s), an openness-biased interaction-model at `prior` confidence, and
   the channel/voice basics — and NOT a full model. (Recommended: the minimal
   four-item seed below.)
3. **D-3 — the over-reach line.** Onboarding proposes structure *at most one
   level up* from the literal ask and only as an opt-in; it never auto-builds an
   elaborate recurring framework on a first touch. (Recommended: one-level-up,
   opt-in.)
4. **D-4 — the trigger / entry.** A `loam init` verb that detects first-run and
   composes the existing capability-activation ritual + the new translate-in
   intake into one front door. (Recommended: `loam init` orchestrates; the
   existing `onboard` ritual becomes one phase inside it.)

**F2 on scope realism:** N3 is **M–L** as the roadmap estimates, and the single
biggest scope risk is **mistaking it for the existing ritual** (§10.1). The
existing six-question ritual is capability-activation, not intake; N3 is net-new
*intake + seed* machinery that composes on it. If a builder reads "onboarding"
and extends the existing `onboarding.py` question list, that is the wrong shape —
N3 adds a translate-in phase + a seed-writer, behind the boundary, with its own
ACs. Named here so the dispatch carries the distinction.

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| The translate-in intake (operating-loop runner for a new user) | A new module/phase under `framework/workspace-bootstrap/` — the component that already owns first-run (`onboarding.py`, `loam_layout.py`, `new_workspace.py`) | Lens 1 / compose-don't-rebuild: first-run already lives here. The intake is a *new phase* in the same component, NOT an extension of the existing question list. The builder owns the exact module boundary. |
| The seed-writer (writes verified state into the two homes) | Same component; writes **only** under `~/.claude/` (global) + `<ws>/.loam/` (scoped) | The seed-writer is framework code whose *output* is user-state (the `establish_loam_layout` shape exactly). Gate 9 enforces it lands in-home. It composes on `establish_loam_layout()` for the scaffold, then *fills* the declared homes. |
| The seeded interaction-model file | `~/.claude/INTERACTION-MODEL.md` (global, cross-workspace) | The AIM design declares this exact path; it is global (the user's voice/exposure prefs cross workspaces). N3 seeds it at `confidence: prior`; N4 moves the cells. |
| The seeded objective(s) (the inferred end-intent) | `~/.claude/OBJECTIVES.md` (global) — the live file-shape precedent | OBJECTIVES.md already exists with the `status`/`last-touched`/`cadence`/`detail-path` header pattern (Tier-0: live, 1689 bytes). The user's stated end-intent seeds as an objective in this exact shape; `status` is owner-gated (the user confirmed it — that IS the gate). |
| The workspace-scoped seed (session/environment priors, if any) | `<ws>/.loam/user-model/` + `<ws>/.loam/session-model/` (the declared, currently-empty homes) | P1.2 declared these homes empty for exactly this. Whether N3 seeds them at all vs leaves them for N4 is **fork D-2** (recommend: seed only the global minimum at N3; leave the workspace model homes for N4). |
| The trigger (first-run detection + the `loam init` verb) | A `loam init` subcommand composing on the existing `loam … onboard` entry-point + `establish_loam_layout()` | **Fork D-4.** Recommend `loam init` as the single front door that runs: scaffold → capability-activation ritual (existing) → translate-in intake (new) → seed. The builder owns the CLI wiring; the entry-point altitude is what the outcome-altitude AC pins. |

---

## §3. Halt-and-surface BEFORE build (decisions recorded at plan-time)

### Surface #1 (no halt — recorded; the intake is NOT the existing ritual)

**Decision (autonomous, Tier-0 verified by reading `onboarding.py`):** the
existing six-question ritual (language / channel / safety-profile / extractor /
watch / auto-skill-capture) is **capability-activation** — it turns features on
and writes manifest fields. It does **not** infer the user's action-oriented
end-intent, propose a healthy enablement, or seed a per-user profile. N3's
translate-in intake is **net-new** and **composes on** the existing ritual
(they run in sequence inside `loam init`), it does not extend the question list.
*Surfaced in the final report* because a builder who reads "onboarding" will
otherwise edit the wrong surface (§10.1).

### Surface #2 (no halt — recorded; verification-heavy by doctrine, not by choice)

**Decision (autonomous, per the doctrine):** the operating loop's verification
step is load-bearing *most of all* at onboarding, because the user-model is
empty and inference is at its most fallible. So the intake's inferred end-intent
is a **hypothesis surfaced for confirmation, never silently written.** This is
not a tunable product choice — it is the doctrine's standing discipline applied
at the moment it matters most. The *amount* asked vs inferred (D-1) and the
*minimum seeded* (D-2) ARE product choices, forked in §11.

### Surface #3 (no halt — recorded; seeds land in-home, gate 9 enforces)

**Decision (autonomous, per N1):** every byte N3 seeds is user-state and MUST
land in one of the two declared homes (`~/.claude/`, `<ws>/.loam/`). A seed
written anywhere else is a boundary violation gate 9 catches at release. The
seed-writer composes on `establish_loam_layout()` (which already creates the
homes) and then fills them — it never invents a third location. This is why an
AC family (AC.ONSEED) pins *where* the seed lands, not just *that* it lands.

### Surface #4 (HALT-WORTHY but RESOLVED — the doctrine is PROPOSED-not-ratified)

**The tension:** `docs/design/loam-doctrine.md` is "Proposed wording … pending
owner verification," and the prime-directive memory records enshrinement into
VALUE_PROPOSITION + CLAUDE.md as **PENDING owner wording-okay**. N3's spine *is*
the doctrine's operating loop. **Does building N3 require the doctrine ratified
first?** *Resolution (no halt):* N3 builds the *mechanism* of the operating loop
(infer → propose → verify → learn on a new user) — which is already the live,
in-use loam behaviour (the prime-directive memory documents this session
dogfooding it). The mechanism is not gated on the doctrine *document's* final
wording; only the *enshrinement edits to VALUE_PROPOSITION/CLAUDE.md* are
owner-wording-gated, and N3 touches neither. **Surfaced** so the owner knows N3
proceeds on the loop-as-behaviour, not on the loop-as-ratified-doc.

### Surface #5 (no halt — recorded; product/UX forks are owner-facing, not author-locked)

**Decision (per the dispatch + F2):** the ask-vs-infer balance (D-1), the
minimum-seed set (D-2), the over-reach line (D-3), and the entry trigger (D-4)
are **product/UX calls** where reasonable people weigh signals differently
(M5 / scope↔confidence: confidence in a single correct UX shape is medium, not
high). Each is therefore a **fork with a recommendation** in §11, surfaced for
an owner ruling — NOT locked unilaterally. The build does not start until the
owner rules the four forks (or ratifies the recommendations).

---

## §4. Spec-objective placement

**Binds to:**
- **The prime directive — per-user-tuned translation** (`docs/design/loam-doctrine.md`; `feedback_loam_prime_directive_user_tuned_translation`). Onboarding is **where the per-user learning STARTS**: it is the first run of the operating loop on a person, the first seed of the state every later translation draws on. N3 is the prime directive's literal front door.
- **The protection leg** (same doctrine; ADR-0001): the seed lands behind the locked boundary (in-home, gate-9 clean) and never clobbers existing state (idempotent / non-destructive) — the protection floor applied to first-run.
- **AIM** (`docs/design/adaptive-interaction-model.md`): N3 seeds the `confidence: prior` initial matrix AIM/N4 then adapts.
- **roadmap §4 N3** + **v-next P1.4**.

**Ladders up:** AC.ONINTAKE.\* + AC.ONSEED.\* + AC.ONFIRE.\* → N3 (intake + seed
shipped) → N4 (the user-model adapts the seeded state) → Phase-3 (the cutover
dogfoods a real onboarding) → the prime directive's two pillars (translate-in +
protect-around). Reverse-trace per `feedback_value_proposition_as_prime_objective`:
every AC traces to AC.PO.\* (the prime objective in VALUE_PROPOSITION) via the
per-user-tuned-translation directive.

---

## §5. Acceptance criteria

> ODD note: every AC below is **outcome-shape** — it states the observable
> outcome, not the method. Method-in-AC test applied to each: the AC can be
> satisfied by a method other than the one the author has in mind (the intake
> could be a CLI prompt loop, a survey-file pre-fill, a single guided
> conversation — the AC pins the *verified-then-seeded* outcome, not the *how*).
> The exact question *wording* and *count* are deliberately NOT pinned here —
> they resolve from the D-1 ruling, and pinning them would be method-in-AC.

### AC.ONINTAKE.\* — the intake runs the operating loop on a new user

- **AC.ONINTAKE.1 (the intake surfaces a bounded set of intake prompts).** On a
  brand-new instance, onboarding presents a **small, bounded** set of
  intake prompts that gather the high-leverage signals needed to infer an
  end-intent (the count + wording resolve from D-1; the AC pins *bounded and
  small*, not the number). *Verified by:* a run with a scripted answerer
  observes the intake ask its bounded set and stop — it does not interrogate.
- **AC.ONINTAKE.2 (an end-intent is PROPOSED, not assumed).** From the answers,
  the intake composes a **proposed** action-oriented end-intent shape (e.g. "it
  sounds like you want X as a repeatable thing — shall I set that up?") and
  presents it. The proposal is distinct from the raw answers — it is the *infer*
  + *propose* legs of the loop. *Verified by:* a run shows a proposal surfaced
  that is a healthy-enablement shape over the raw answers, not a verbatim echo.
- **★ AC.ONINTAKE.3 (the proposal is SURFACED FOR VERIFICATION before any commit
  — the load-bearing one).** No seeded user-state is written until the user has
  **confirmed or corrected** the proposal. A "no, simpler" / "yes, and also…"
  path exists and changes what gets seeded. *Verified by:* a run where the
  answerer rejects/edits the proposal results in **different** seeded state than
  a run where it confirms — proving the seed is gated on verification, not on
  the silent inference.
  - **`outcome-altitude: true`** is NOT claimed here (this AC is about the
    verify-gate behaviour; the cold-walk outcome-altitude AC is AC.ONFIRE.3).
- **AC.ONINTAKE.4 (over-reach guarded — proposes at most one level up, opt-in).**
  The proposed structure is **at most one level up** from the literal ask
  (a "do X once" never auto-becomes "a recurring deterministic framework"); any
  elaborate version is presented as an **opt-in suggestion**, never the default
  that gets built. *Verified by:* a "one-time" answer yields a proposal that
  does not silently seed a recurring framework; the recurring option is offered,
  not assumed. (Per D-3.)

### AC.ONSEED.\* — the verified result is seeded into the two-tier home

- **AC.ONSEED.1 (the seed lands in the correct homes — gate 9 GREEN).** Every
  byte of seeded user-state lands under `~/.claude/` (global) or `<ws>/.loam/`
  (workspace-scoped) — nothing under `framework/` or a cwd-relative path. *Verified
  by:* after a real run, `check_boundary_respected` (gate 9) is GREEN against the
  resulting tree, and the seeded files are enumerable under the two homes.
- **AC.ONSEED.2 (the interaction-model seeds at `confidence: prior`).** The
  seeded `~/.claude/INTERACTION-MODEL.md` exists in the AIM matrix shape with
  every cell at `confidence: prior` (the openness-biased default), so N4 can
  move the cells from evidence. *Verified by:* the seeded file parses to the AIM
  schema with `confidence: prior` cells. (N3 seeds; it does NOT adapt — adapting
  is N4.)
- **AC.ONSEED.3 (the confirmed end-intent seeds as an objective).** The
  user-confirmed end-intent is written as an objective in the live
  `~/.claude/OBJECTIVES.md` file-shape (`status` / `last-touched` / `cadence` /
  `objective` / `detail-path`), with `status` reflecting that the user
  confirmed it. *Verified by:* the seeded objective parses to the OBJECTIVES.md
  shape and reflects the confirmed (not the raw) intent.
- **AC.ONSEED.4 (the seed is the MINIMUM useful prior, not a full model).** The
  seeded set is bounded to the D-2 minimum (the confirmed objective(s) +
  the `prior`-confidence interaction-model + the channel/voice basics) and does
  NOT pre-populate the full per-user model (that is N4's job from evidence).
  *Verified by:* the seeded surface matches the D-2 minimum set and the
  workspace model homes (`user-model/`, `session-model/`) are NOT pre-filled
  with inferred content (per the recommended D-2). (Per D-2 ruling.)

### AC.ONFIRE.\* — onboarding fires on a brand-new instance, idempotently

- **AC.ONFIRE.1 (fires through a real entry-point on first-run).** Onboarding is
  reachable through a real CLI entry-point (the D-4 trigger — recommended `loam
  init`) that detects a brand-new instance and runs scaffold → capability ritual
  → translate-in intake → seed. *Verified by:* invoking the real entry-point on
  a fresh workspace runs the full first-run flow end-to-end.
- **AC.ONFIRE.2 (idempotent / non-destructive on re-run — the protection floor).**
  Running onboarding again on an already-seeded instance does **not** clobber
  existing user-state: an existing `INTERACTION-MODEL.md`, an existing seeded
  objective, an existing `.loam/` tree are detected and left intact (the
  `establish_loam_layout` fail-safe shape, extended to the seed). *Verified by:*
  a second run on a seeded tree makes no destructive change to the prior seed.
- **★ AC.ONFIRE.3 (OUTCOME-ALTITUDE — a genuinely-empty instance, run through the
  real entry-point, ends with correctly-homed seeded state).** Starting from a
  **genuinely empty** user-state (no `INTERACTION-MODEL.md`, no seeded objective,
  fresh `.loam/`, no pre-arranged in-memory state), the **real onboarding
  entry-point** is invoked with a scripted-but-realistic set of answers + a
  confirmation, and the run ends with: (a) seeded state present in the correct
  two homes, (b) gate 9 GREEN, (c) the interaction-model at `confidence: prior`,
  (d) the confirmed objective recorded. A STUB-class unit test of an inner
  function does NOT satisfy this — it must drive the production entry-point on an
  empty instance (the cold-walk standard). *Verified by:* the cold-walk test
  asserts the four post-conditions after driving the real entry-point on an
  empty fixture instance.
  - **`outcome-altitude: true`** (per `feedback_test_outcome_altitude_required` —
    invokes the production entry-point with no pre-seeded state).

---

## §6. Build steps (method-level guidance only — builder's call per ODD §1.1)

> The builder owns method. This is sequence + the bookkeeping mechanism, not
> file-by-file prescription. **The build does not start until the owner rules
> the four §11 forks (D-1..D-4) or ratifies the recommendations** (§5 ACs that
> reference a fork resolve once the fork is ruled).

**Likely a single cycle** (one component — `workspace-bootstrap` — one fence),
unless the builder finds the intake + seed-writer + `loam init` wiring large
enough to warrant decomposition into (a) intake + (b) seed-writer + (c) trigger
sub-cycles with tighter ACs (Lens 5; the builder's call per the scope-confidence
stopping criterion).

1. **Confirm the fork rulings are recorded** in this plan-doc's §11 before any
   code (record-ratification-before-dispatch). The build reads the ruled forks,
   not a conversational memory of them.
2. **Examine the existing ritual + scaffold FIRST** (do not re-derive): read
   `onboarding.py` (the capability-activation phase N3 composes on, NOT extends),
   `loam_layout.py` (`establish_loam_layout` — the seed-writer composes on it),
   `new_workspace.py` (the first-run materialisation), the AIM matrix shape, and
   the OBJECTIVES.md live file-shape. Confirm the boundary homes via
   `user-state-homes.yaml`.
3. **Author the cold-walk test FIRST** (TDD, dev-mode default): AC.ONFIRE.3 — an
   empty fixture instance, the real entry-point, a scripted answer+confirm, and
   the four post-conditions (homed seed / gate-9 GREEN / `prior` matrix /
   confirmed objective). Then the verify-gate test (AC.ONINTAKE.3 — reject vs
   confirm yields different seed) and the idempotency test (AC.ONFIRE.2).
4. **Build the translate-in intake** (the infer → propose → verify legs on a new
   user) per the ruled D-1 shape. The propose+verify gate is the load-bearing
   bit (AC.ONINTAKE.2/.3); the over-reach guard is AC.ONINTAKE.4 (per D-3).
5. **Build the seed-writer** — composes on `establish_loam_layout()`, then fills
   the D-2 minimum seed into the two homes (interaction-model at `prior`;
   confirmed objective in OBJECTIVES.md shape). Idempotent / non-destructive
   (AC.ONFIRE.2). Gate-9-clean by construction (AC.ONSEED.1).
6. **Wire the trigger** (`loam init` per D-4) — scaffold → capability ritual
   (existing) → translate-in intake (new) → seed. First-run detection.
7. **Run the boundary gate (gate 9) against a post-onboarding tree** — confirm
   GREEN (AC.ONSEED.1). Run the existing onboarding-ritual tests — confirm N3's
   composition did not regress the capability-activation ritual.
8. **`loam amend apply` / seal** — `workspace-bootstrap` has shipped via
   amendment cycles before; the builder verifies against
   `docs/conventions/sealed-component-invariants.md` at build-time and, if the
   component is sealed, names `loam amend apply` as the bookkeeping mechanism.
9. **Seal** per the standard ladder; backfill each AC GREEN into this plan-doc's
   §status verdict matrix; **merge the sealed slice to `main`** (the now-standard
   per-slice merge).
10. **Bookkeeping** (§9): re-mark roadmap N3 DONE; mark v-next P1.4 delivered;
    note N4 is now unblocked (it has seeded state to adapt).

---

## §7. Out of scope (deferred + when)

- **The user-MODEL that ADAPTS the seeded state — N4.** N3 seeds the
  `confidence: prior` initial state; **moving the cells from evidence is N4**
  (gated on G5 — the openness-default ratification). N3 does NOT build the
  adaptation engine, the hysteresis, the signal counters, or the re-eval loop.
- **Re-scaffolding `.loam/`** — DONE by P1.2 (`01f3b40`). N3 SEEDS the declared
  homes; it does not re-create the layout.
- **Extending the existing six-question capability ritual** — N3 composes on it,
  does not add to its question list (§10.1). If a capability question is missing,
  that is a *separate* change to `onboarding.py`, not N3.
- **The full "just-lost-my-job-as-a-CTO" human-problem flow** — the doctrine's
  human-problem worked example is the *aspiration* the loop generalises to; N3
  builds the *mechanism* (infer → propose → verify → seed) and proves it on the
  brand-new-instance case. A rich life-coaching intake is a later, larger surface
  the same mechanism supports — not N3's build.
- **Workspace-scoped model seeding (`user-model/`, `session-model/`)** — per the
  recommended D-2, N3 seeds only the global minimum; the workspace model homes
  are left for N4 to fill from evidence. (If the owner rules D-2 differently, this
  moves in-scope.)
- **A runtime first-run-detection hook** (auto-firing onboarding on a fresh
  session with no `loam init`) — deferred. N3's trigger is the explicit `loam
  init` verb (D-4); an auto-detect hook is a later convenience, not N3.

---

## §8. Halt triggers (in-flight conditions that abort the build)

1. **The forks are not ruled.** If the build starts and D-1..D-4 are not recorded
   in §11, HALT — the product/UX shape is unresolved and building on an
   unconfirmed shape is exactly the silent-inference failure the doctrine warns
   against (record-ratification-before-dispatch).
2. **The cold-walk cannot reach real-entry-point altitude.** If AC.ONFIRE.3 can
   only be tested by stubbing an inner function (the real `loam init` /
   onboarding entry-point cannot be driven on an empty instance without
   pre-arranged state), HALT — the AC is unsatisfiable as written and needs
   re-framing before code (loose-AC → fix the AC, not the implementation).
3. **The seed cannot be made gate-9-clean.** If any seed must land outside the
   two homes to be useful (a real third-location need surfaces), HALT and surface
   — do NOT widen the boundary silently; the boundary is locked (N1) and a
   genuine need to seed elsewhere is an ADR-level decision, not a build call.
4. **Extending the existing ritual looks easier than composing.** If the builder
   is tempted to add intake questions to `onboarding.py`'s six-question list
   instead of building a distinct translate-in phase, HALT and re-read §10.1 —
   that is the wrong-surface failure this plan exists to prevent.
5. **`workspace-bootstrap` is a sealed component without an amend path named.**
   If sealed and the dispatch did not name `loam amend apply`, HALT
   (sealed-component-dispatch rule).

---

## §9. Bookkeeping (STATE.md + roadmap + parent-plan backfill)

1. **`docs/plans/loam-roadmap.md` §4 N3 cell** — re-mark DONE at seal (SHA +
   amendment number); note N4 is now unblocked (seeded state exists to adapt).
   Update the critical-path line if N3 completion re-bases it.
2. **`docs/plans/loam-vnext-build-plan.md` Phase-1 P1.4** — mark the
   onboarding/init slice delivered by N3 (SHA).
3. **`docs/STATE.md`** — record the N3 seal (amendment number + SHA) per the
   standard ladder once sealed.
4. **This plan-doc §status / verdict-matrix** — backfill each AC GREEN at seal so
   release gate 2 (`check_acs_verified`) can read it.
5. **The fork rulings (§11)** — record the owner's D-1..D-4 rulings in §11 BEFORE
   the build dispatch (record-ratification-before-dispatch).

---

## §10. F2 Ruthless Feedback (honest doubts + named design risks)

1. **THE LOAD-BEARING FINDING — "onboarding" already exists, but it is the wrong
   thing for N3.** *The disagreement:* a reader equates N3 ("onboarding / init
   flow") with the existing `onboarding.py` ritual and extends it. *The
   evidence:* `framework/workspace-bootstrap/src/loam/workspace_bootstrap/onboarding.py`
   is a six-question **capability-activation** ritual (language / channel /
   safety-profile / extractor / watch / auto-skill-capture) that writes manifest
   fields and fires activations — it contains **no** inference of the user's
   action-oriented end-intent, **no** propose-and-verify loop, and **no** per-user
   profile seed. The doctrine's operating-loop intake is a *different shape*.
   *The alternative:* N3 builds a **net-new translate-in phase + seed-writer**
   that *composes on* the existing ritual (runs after it, inside `loam init`),
   not an extension of its question list. This is the #1 scope risk; it is named
   in Surface #1, the placement table, the build steps, and halt trigger #4 so
   it cannot be missed.

2. **The doctrine N3 implements is PROPOSED, not ratified — but the mechanism is
   already live.** *The disagreement:* one could argue N3 is blocked on the
   doctrine's owner-wording ratification. *The evidence:*
   `docs/design/loam-doctrine.md` is "Proposed wording … pending owner
   verification"; the prime-directive memory marks enshrinement PENDING. *The
   alternative:* N3 builds the operating-loop *mechanism* (which is already the
   live, dogfooded loam behaviour), not the doctrine *document*; only the
   VALUE_PROPOSITION/CLAUDE.md enshrinement edits are wording-gated, and N3
   touches neither (Surface #4). Named so the owner can rule otherwise if they
   want the doctrine ratified first.

3. **Risk: the verify-gate (AC.ONINTAKE.3) is the whole point, and it is the
   easiest to fake.** *The evidence:* a weak implementation could "surface for
   verification" by printing a proposal and seeding regardless of the answer —
   satisfying a naive reading while violating the doctrine. *The
   alternative / mitigation:* AC.ONINTAKE.3 is written to require that
   **reject-vs-confirm produces different seeded state** — a behaviour a
   print-and-ignore implementation cannot pass. The cold-walk (AC.ONFIRE.3)
   drives a confirm path; a sibling test must drive a reject path and assert the
   seed differs. Named so the builder authors the reject-path test, not just the
   happy path.

4. **Risk: the over-reach guard (AC.ONINTAKE.4 / D-3) is judgment, not a
   mechanism.** *The evidence:* "propose at most one level up" is a quality the
   model must exercise, not a deterministic check — there is no gate that proves
   a proposal didn't over-reach. *The alternative / mitigation:* keep N3's seed
   *minimum* (D-2) so even an over-eager proposal can only seed the bounded set;
   the over-reach guard governs the *proposal voice*, and the *seed bound* is the
   hard backstop. The AC tests the bound (seed is minimum), and the proposal
   quality is an LLM-as-judge / review concern, not a unit assertion. Named so
   the owner knows the over-reach line is partly a voice-discipline, partly a
   seed-bound — and the seed-bound is the enforceable half.

5. **Open question for the owner (not a blocker): should onboarding seed
   ANYTHING workspace-scoped at N3, or only global?** *The evidence:* the
   `.loam/user-model/` + `session-model/` homes are declared and empty (P1.2),
   waiting to be filled. N3 *could* seed a workspace prior; the recommended D-2
   says don't (leave them for N4's evidence). *The alternative:* if the owner
   wants a workspace-scoped first-touch (e.g. a per-repo intent), D-2 moves it
   in-scope. Forked in §11 D-2 with the global-only recommendation.

---

## §11. Named decisions / forks (with recommendations — OWNER-FACING product calls)

> These four are the USER-FACING product/UX decisions the dispatch asks to
> surface. Each is a fork with my recommendation; the owner rules (or ratifies
> the recommendation) BEFORE the build. Recorded here is the durable
> ratification surface the builder Tier-0-reads (record-ratification-before-dispatch).

### D-1 — ask-vs-infer balance (how much onboarding ASKS vs INFERS)

- **(a) Verification-heavy / confirm-the-proposal (lean).** Ask a *small* set of
  high-leverage questions (e.g. who-are-you / what-do-you-want-loam-to-help-with /
  how-do-you-want-to-be-talked-to), infer a *proposed* end-intent shape from
  them, and **confirm the proposal** before seeding. Few asks; the inference is
  surfaced, not silent.
- **(b) Ask-everything (no inference).** Ask enough questions to seed every field
  directly, no inference step. Safest against wrong inference, but exhausting
  (the over-reach guard's cousin: an interrogation is its own failure) and it
  defeats the point — the loop's *infer* leg is what loam adds over a raw form.
- **(c) Infer-heavy (minimal asks, heavy inference).** Ask one or two questions,
  infer aggressively. Fastest, but the doctrine says inference is *most fallible*
  for a brand-new user — this maximises the silent-wrong-inference risk at the
  exact moment it is highest.
- **Recommendation: (a).** The doctrine is explicit: for a user we barely know,
  inference is most fallible, so verification is load-bearing. (a) keeps the
  *infer* leg loam adds over a raw form, but gates it behind confirmation — the
  hypothesis-not-assumption discipline at the moment it matters most. (b) throws
  away the inference loam exists to provide; (c) front-loads the inference risk.
  **Confidence: high on the shape (verify-heavy is doctrine-mandated), medium on
  the exact question set (the question wording/count is genuinely the owner's
  product call — left to the ruling, deliberately NOT pinned in the ACs).**

### D-2 — the minimum seed (what state, and where)

- **(a) Minimal four-item global seed (recommended).** Seed only: (1) the
  user-confirmed end-intent as an objective in `~/.claude/OBJECTIVES.md`; (2) an
  openness-biased `~/.claude/INTERACTION-MODEL.md` with every cell at
  `confidence: prior`; (3) the channel/voice basics (which the existing ritual
  already captures — Q2 channel); (4) nothing in the workspace model homes (leave
  `.loam/user-model/`, `session-model/` for N4's evidence). The smallest prior
  that makes the next session useful.
- **(b) Minimal + a workspace-scoped intent prior.** (a) plus a per-repo intent
  seed in `.loam/user-model/`. More useful per-workspace on day one, but it
  front-loads inference into the workspace model that N4 is designed to grow from
  evidence — risking a wrong workspace prior that N4 then has to unlearn.
- **(c) Rich seed (full first model).** Pre-populate as much of the AIM matrix +
  the model homes as the answers allow. Maximally useful day-one, maximally
  over-reaching — directly violates the over-reach guard and the doctrine's "scale
  structure to what you've learned, and you've learned almost nothing yet."
- **Recommendation: (a).** It is the doctrine's over-reach guard made concrete:
  seed the minimum useful prior, let N4 grow the rest from evidence. It keeps the
  interaction-model at `confidence: prior` (exactly what AIM expects to adapt
  from) and avoids seeding a workspace prior N4 might have to unlearn. (b) is a
  reasonable owner preference if day-one per-repo usefulness matters more than
  keeping the workspace model evidence-pure; (c) is rejected as over-reach.
  **Confidence: high** — (a) is the doctrine's guard applied directly; (b) is the
  only genuinely live alternative.

### D-3 — the over-reach line (how far onboarding proposes)

- **(a) One-level-up, opt-in (recommended).** A proposal goes *at most one level
  up* from the literal ask (a "help me write a chapter" can propose "a repeatable
  chapter pipeline?" — but only as an opt-in offer, never auto-built), and the
  elaborate version is always a suggestion the user accepts, never the default
  that gets seeded.
- **(b) Literal-only (no structural proposal at onboarding).** Onboarding only
  captures what the user literally says; structural proposals wait until loam
  knows the user better (later sessions). Safest against over-reach, but it
  removes the *propose-healthy-enablement* leg from the exact front-door moment
  the doctrine's worked examples ("evaluate my engineers" → a framework) showcase.
- **(c) Aspirational (propose the full structure).** Propose the elaborate
  recurring-framework version up front. Directly the over-reach failure the
  doctrine names ("don't meet every 'do this once' with 'shouldn't this be a
  framework?'") — exhausts a brand-new user.
- **Recommendation: (a).** It preserves the *propose* leg (loam's value over a
  raw form) while honouring the over-reach guard: one level up, opt-in, never
  auto-built. The seed-bound (D-2 minimum) is the hard backstop so even an
  over-eager proposal cannot over-seed. (b) is defensible if the owner wants the
  first touch to be pure capture with proposals deferred; (c) is rejected.
  **Confidence: high** — (a) is the over-reach guard's literal application.

### D-4 — the trigger / entry (how onboarding fires)

- **(a) A `loam init` verb that orchestrates (recommended).** A new `loam init`
  subcommand is the single front door: it detects a brand-new instance and runs
  scaffold (`establish_loam_layout`) → capability-activation ritual (existing
  `onboard`) → translate-in intake (new) → seed. Composes the existing pieces;
  one obvious verb a new user runs.
- **(b) Extend the existing `onboard` verb.** Fold the translate-in intake into
  the existing `loam … onboard` subcommand. Fewer verbs, but it conflates
  capability-activation with the translate-in intake (the §10.1 risk made into a
  CLI shape) and overloads a verb whose name says "onboard" but whose current
  job is narrower.
- **(c) Auto-fire on first-run detection (a SessionStart hook).** No explicit
  verb — onboarding fires automatically when loam detects a fresh instance.
  Smoothest for a non-tech user (nothing to run), but auto-firing an interactive
  intake from a hook is heavier machinery, harder to test at entry-point
  altitude, and a worse first build — better as a *later* convenience layered on
  top of an explicit verb (deferred, §7).
- **Recommendation: (a).** `loam init` is the conventional first-run verb a new
  user expects (`git init`, `npm init`), it composes the existing ritual +
  scaffold + new intake into one orchestrated front door (Lens 1
  compose-don't-rebuild), and it gives the outcome-altitude AC a clean real
  entry-point to drive. (c)'s auto-fire is the right *eventual* non-tech-user UX,
  but layered on (a), not instead of it (§7 defers it). (b) overloads a
  narrower verb. **Confidence: high on `loam init` as the orchestrating verb;
  medium on whether the existing `onboard` ritual runs before or after the
  translate-in intake — recommend BEFORE (capabilities first, then intent), the
  builder's call on exact ordering if the owner has no preference.**

---

## §12. Provenance trail (load-bearing sources, with refs)

- **The operating-loop spine:** `docs/design/loam-doctrine.md` — the four-step
  loop (§"The operating loop", lines 36–69), the verification-is-load-bearing
  passage (lines 58–63), the over-reach guard (lines 65–69), the
  "just-lost-my-job-as-a-CTO" worked example (lines 171–186).
- **The prime directive (why onboarding is the front door):**
  `feedback_loam_prime_directive_user_tuned_translation.md` — the operating loop
  + verification-most-fallible-for-a-new-user (lines 71–83), the over-reach guard
  (lines 79–83).
- **The two-tier home + boundary (where seed lands):** ADR-0001
  (`docs/design/adr/boundary-framework-vs-user-state.md` §3 the two homes, §6 the
  gate-9 enforcement) + the declared allowlist
  (`docs/design/adr/user-state-homes.yaml`).
- **The scaffold the seed-writer composes on:** `01f3b40`;
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/loam_layout.py`
  (`establish_loam_layout`, the idempotent/fail-safe/additive invariants, the
  declared `user-model/`/`session-model/`/`environment-model/` homes).
- **The existing capability-activation ritual (compose-on, NOT extend — §10.1):**
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/onboarding.py`
  (the six-question `QUESTION_SLUGS`, the manifest-write + activation dispatch),
  `onboarding_cli.py` (the `onboard` subcommand entry-point, the `_stdin_answerer`).
- **The adapter N3 seeds for (AIM):** `docs/design/adaptive-interaction-model.md`
  — the `~/.claude/INTERACTION-MODEL.md` matrix shape (§1a), the openness-biased
  `confidence: prior` default (§0, §1a), the asymmetric-update safety property
  (§0 F2 headline) that N4 — not N3 — implements.
- **The seeded-objective file-shape precedent:** `~/.claude/OBJECTIVES.md` (live,
  Tier-0 1689 bytes — the `status`/`last-touched`/`cadence`/`objective`/
  `detail-path` header pattern the seeded objective reuses).
- **The roadmap placement:** `docs/plans/loam-roadmap.md` §4 N3 (`N1 → N3 → N4`
  critical path; N3 unblocks N4 which is gated on G5), §4 N4 (what N3 seeds that
  N4 adapts).
- **Methodology:** `docs/conventions/plan-docs.md` (this plan's shape);
  `feedback_test_outcome_altitude_required` (AC.ONFIRE.3);
  `feedback_loose_AC_text_fix_AC_not_implementation` (halt trigger 2);
  `feedback_record_owner_ratification_before_dispatch` (the §11 fork-ruling gate);
  `feedback_value_proposition_as_prime_objective` (the AC ladder-up).

---

*Principles applied at authoring: PRIME DIRECTIVE as the spine (onboarding is
where per-user-tuned translation starts; the operating loop is the intake's
shape; verification-heavy for a barely-known user — D-1 (a)); the over-reach
guard (D-2 (a) minimum-seed + D-3 (a) one-level-up-opt-in — don't over-engineer
a new user's first touch); EXAMINE-before-designing (read the existing
`onboarding.py` ritual, `loam_layout.py`, the AIM matrix, the live OBJECTIVES.md
shape, the boundary allowlist BEFORE authoring — caught the load-bearing §10.1
finding that "onboarding" already exists as a different thing); compose-don't-
rebuild (Lens 1 — N3 composes on the existing ritual + `establish_loam_layout` +
the AIM schema; it rebuilds none of them); plan-before-code (PLAN-ONLY — no code
written); outcome-altitude AC at the real init entry-point (AC.ONFIRE.3); ODD
authoring (every AC outcome-shape, method-in-AC test passed, question wording/
count deliberately NOT pinned); F2 (named the wrong-surface risk, the
proposed-doctrine tension, the fake-verify-gate risk, the over-reach-is-judgment
risk — each with evidence + an alternative); scope↔confidence (TIGHT where the
doctrine + N1 settled it; the four UX/product calls FORKED with recommendations
where confidence in a single correct shape is medium, not high — owner rules).*

---

## §13 §status — verdict matrix (backfilled at seal)

*Populated at seal time per the standard ladder. Forks D-1..D-4 ruling recorded
in §11 BEFORE the build dispatch.*

| AC | Verdict | Evidence |
|---|---|---|
| AC.ONINTAKE.1 | (pending) | |
| AC.ONINTAKE.2 | (pending) | |
| AC.ONINTAKE.3 | (pending) | |
| AC.ONINTAKE.4 | (pending) | |
| AC.ONSEED.1 | (pending) | |
| AC.ONSEED.2 | (pending) | |
| AC.ONSEED.3 | (pending) | |
| AC.ONSEED.4 | (pending) | |
| AC.ONFIRE.1 | (pending) | |
| AC.ONFIRE.2 | (pending) | |
| AC.ONFIRE.3 ★ outcome-altitude:true | (pending) | |
