# dev → build → deploy spine — phased unification plan

**Date:** 2026-06-28
**Status:** PLAN-DOC — the complete phased arc for unifying loam's three
fragmented threads (dev-sdlc ODD discipline · hands-off-loop build · the deploy
tiers) into one dev→build→deploy spine. Authored under owner-ratified **Option
C**: commit to the unified target, define the shared contract now (P0, built as
the paired spec), build the deploy tiers on the sealed floor next, fold
dev-sdlc + hands-off-loop into the spine last. Docs-only; no code, no seal in
this dispatch.
**Working tree:** `/Users/lukeivers/loam` (canonical, main)
**Author:** `loam-plan-author`
**Paired spec (P0 deliverable):** `docs/design/dev-build-deploy-shared-contract.md`
**BASELINE candidate (informational; this is a docs cycle):** HEAD `243b3542`
**Status-file target:** `docs/STATE.md` change-log + `docs/release-roadmap.md`
**Quality bar:** every phase is a self-contained, dispatch-ready unit — pick
phase N and build it with no re-discovery.

**Predecessors (Tier-0 verified on disk):**
- SEALED deploy-safety FLOOR — `framework/deploy-safety-floor/` (seals
  `cf1ed11e`, `828de228`, `e8c5d3b4`/`e0e9a258`) + `framework/secure-build-baseline/`
  (seal `3225eeee`). HEAD `243b3542`.
- Architecture decision (Option C) — `…/devops-pipeline-2026-06-27/03-architecture-decision-plugins-vs-native.md`.
- Feature design + dimensions — `…/01-loam-feature-design.md`, `…/environment-model.md`,
  `…/loam-fit-claude-leverage.md`, `…/local-target.md` (the full LOCAL deep-dive
  flagged for P1 fold-in).
- Product architecture — `docs/design/loam-plugin-product-architecture.md`.
- hands-off-loop — `plugins/loam-skills/skills/handsoff-loop/SKILL.md`.

---

## §1 Summary / TL;DR

**What this plan ships (the arc, not the build):** a five-phase sequence that
turns the sealed deploy-safety FLOOR into a complete dev→build→deploy spine. P0
(the shared contract) is built now as the paired spec. P1–P3 build the deploy
tiers on the floor, sequenced by irreversibility (reversible first). P-final —
explicitly last, highest blast radius — restructures dev-sdlc and hands-off-loop
to adopt the spine.

**The phase arc:**

| Phase | Delivers | Reversibility / blast | Composes on |
|---|---|---|---|
| **P0** | the shared Acceptance+Gate vocabulary + the unified config model | docs-only (this dispatch) | the sealed floor's config/gate/attestation primitives |
| **P1** | deploy tier: **LOCAL** | reversible / `local` | the floor (idle at LOCAL) + secure-build baseline |
| **P2** | deploy tier: **Vercel preview→prod** | reversible-with-effort / `shared-preview`→`production` | the floor's `max(declared,resolved)` gate + attestation default + P1 |
| **P3** | deploy tier: **real-infra** | irreversible / `production` | the floor's F-0 attestation + provider-side guarantees + P2 |
| **P-final** | dev-sdlc + hands-off-loop adopt the spine | highest blast radius | all of P0–P3 + the build-publish substrate |

**Key decisions baked (full statements + recommendations in the spec §6 and
this plan §3):** two axes (Acceptance + Gate) not one done/safe word; `tier` is
the floor's risk-class and provider lives in additive `provider_binding` (the
sealed `Tier` enum is NOT extended); `deploy.yaml` authoritative for topology,
provider authoritative for live state; the deploy boundary is always a distinct
owner-asked action.

**F2 on scope realism:** P0 is genuinely done as a docs deliverable (the
contract + spec are the foundation, no code owed now). P1 is small and
high-confidence. P2 carries the first real blast radius and the most named
research rulings still owed (HALT-2 provider probes, Hobby one-step-rollback).
P3 is gated behind provider-side guarantees that **do not yet exist** (R-3: the
loam-hosted credential service / GitHub Pro) — it is correctly last and
correctly behind the heaviest gate. P-final is deliberately loose-scoped here
(deferred, higher-uncertainty) per F4. The realistic risk is not any single
phase but **P2's dependency on owner rulings** the research left open (§9, §11).

---

## §2 Predecessors / context

This plan composes against the SEALED floor and the RECOMMENDATION-pending
architecture decision. The floor delivers the framework-side half only: the
destructive-action gate keyed off `max(declared, resolved)`, the
refuse-all-destructive default, the attestation *contract* (not the provider
probes), per-gate fail-closed, and the secure-build baseline. Everything above
the floor — the opt-in deploy *tiers* — is forward work this plan sequences.
The governing Option-C decision itself stays RECOMMENDATION-pending; this plan
is the planning half it authorized, and proceeds on the unambiguous, reversible
part everyone agrees on.

---

## §3 Placement decisions (Option C, made concrete)

1. **P0 = the contract, built now as a spec.** The unified vocabulary and
   config model are the foundation every later phase implements against. They
   are pure design — no code, no seal — so they ship as a docs deliverable in
   this dispatch. *Rationale:* a contract authored after the first tier is built
   is a contract retrofitted to one tier's accidents; authored first, it is the
   target all tiers aim at (the dispatch's "easy to finish out when it's time"
   requirement).

2. **Deploy tiers are Capabilities; the gates beneath them are Floor.** Per the
   architecture decision: the floor (sealed) is framework-native and
   non-disable-able; the `/publish` `/promote` `/provision` tiers are opt-in
   capabilities that compose ON the floor. P1–P3 build capabilities; none of
   them weakens or re-implements the floor. *Rationale:* a safety gate a
   marketplace toggle can turn off is a contradiction for a non-technical owner
   (architecture decision §"Evidence").

3. **dev-sdlc adoption is LAST and its own phase.** Restructuring dev-sdlc +
   hands-off-loop to run on the spine is the highest-blast-radius change and is
   explicitly deferred (owner ruling: "fold into the spine in a LATER,
   deliberate cycle — not now"). P-final is scoped loose here (F4: deferred,
   higher-uncertainty) and will be re-planned at its own time with tight ACs.

4. **Sequence by reversibility/blast-radius, MVP-reversible first.** P1 (LOCAL,
   nothing irreversible) → P2 (Vercel, reversible-with-effort) → P3 (real-infra,
   irreversible). Each tier earns the next by proving its gates held — the tiers
   are escalating irreversibility regimes, not additive supersets (feature
   design §2.3).

---

## §4 Halt-and-surface recorded at plan-authoring

Decisions taken autonomously and recorded here (Lens 7 surfacing; none is
critical-call / public-action / financial, so each is decided, not escalated):

- **The sealed `Tier` enum has no `vercel` value.** Recorded as spec D-SC.3:
  reconciled by reading `tier` as the floor's risk-class and putting the
  provider in additive `provider_binding`. *This is the one finding a builder
  could otherwise "fix" by editing a sealed component — it is named here and in
  the spec so no phase breaks the seal to add a provider value.*
- **"Done" and "safe" are two axes.** Recorded as spec D-SC.1; the contract
  holds both rather than collapsing them.
- **`deploy.yaml` authoritative-vs-cache** was an open question in two
  dimension deep-dives. Decided (spec D-SC.4: authoritative for topology,
  provider for live state, divergence surfaced).

**Gates the phase builders MUST respect (not autonomous — these are hard
preconditions carried from the research):**

- **HALT-2 (research §3 / attestation scope boundary):** the live provider
  probes that populate an attestation record (deletion-protection / Object-Lock
  / `prevent_destroy` / OIDC reads) are deploy-tier work and were OUT of the
  floor's scope. P3 owns them; P3 may not ship `is_production` real-infra
  operation until they populate a fresh attestation (F-0 / AC.FLOOR.0).
- **Fail-closed (G15 / AC.FLOOR.6):** any new destructive gate a tier adds
  fails CLOSED, verified under every `permission_mode`. This is a build entry
  condition, not a gap to raise later.
- **R-3 (research §13):** real-infra's go-live substitute (F-9 credential-gated
  promote) depends on a loam-hosted credential service or GitHub Pro that **does
  not yet exist**. P3 may not present real-infra as protected until that
  prerequisite is met or the owner accepts Wall-1+Wall-3-only with it named.

---

## §5 Spec-objective placement / ladder-up

The spine binds to the prime objective in `docs/VALUE_PROPOSITION.md`
(AC.PO.1 reduce-translation-burden, AC.PO.2 add-to-persona-toolkit) and to the
feature design's objective (`01-loam-feature-design.md` §1): *let a
non-technical owner publish and operate real software expressing only plain
intent, such that no irreversible production action fires by accident, every
consequence is shown in their vocabulary first, and the protection floor holds
independent of behaviour.* Each phase's ACs ladder to that, which ladders to
AC.PO.1/AC.PO.2. Lens 0: the owner brings WHAT ("put it live", "undo that");
the spine owns HOW across dev→build→deploy. Lens 2: each phase adds a
persona-invokable verb (`/publish`, `/promote`, `/provision`) and reduces the
owner's translation burden (they never learn `vercel --prod`, `tofu apply`,
OIDC, expand/contract).

---

## §6 The phase arc

Each phase below is a self-contained dispatch-ready unit. A phase's manifest
YAML is authored at *that phase's* build-time against the fence named here (per
the plan-docs convention; versions derive at release time, not pre-allocated).
ACs are outcome-shaped — for each, the method-in-AC test ("could a different
method satisfy this?") passes; the method is named only as the builder's
inferable option, never as the contract.

---

### P0 — the shared contract (BUILT NOW, as the paired spec)

- **Objective:** define the one Acceptance+Gate vocabulary and the one
  per-environment config model that dev-sdlc, hands-off-loop, and all three
  deploy tiers speak, such that a build's proof of correctness can ride into a
  deploy gate as data and "done"/"safe" are one consistent plain language.
- **Scope (in):** the Acceptance record; the Gate record built on the sealed
  floor's primitives; the bridge (Acceptance as a Gate precondition); the
  additive-superset config model + the tier→risk-class reconciliation + the
  authoritative-vs-cache decision. **Out:** any code; any change to the sealed
  floor; the tiers themselves.
- **Outcome-shaped ACs:**
  - **AC.SPINE.1:** a single Acceptance record shape exists that a dev-sdlc AC,
    a hands-off-loop frozen-acceptance, and a deploy gate-condition can each be
    expressed in without loss of any property each carries today
    (independence-of-producer, frozen-unseen, outcome-altitude, ladder-up).
    *(method-test: passes — any serialization satisfies it.)*
  - **AC.SPINE.2:** the Gate vocabulary is expressible entirely in terms of the
    sealed floor's existing enums (`GateLevel`, `Tier`, attestation
    fresh/stale/absent, `max(declared,resolved)`) plus additive above-floor
    values, introducing no change to a sealed enum.
  - **AC.SPINE.3:** a promote-to-production gate can name a build's Acceptance
    as a precondition and enforce artefact-hash identity between what was proven
    and what is deployed.
  - **AC.SPINE.4:** the config model is a strict additive superset of the
    sealed `deploy.yaml` schema — every sealed field unchanged; every new field
    optional and ignored by the floor.
  - **AC.SPINE.5 (the tier reconciliation):** a Vercel-production environment is
    expressible with the sealed `Tier` enum unchanged, the provider carried in
    an additive field, and no field reading as a contradiction.
- **Dependencies:** none (foundation).
- **Composes on:** the sealed floor's `config.py` / `classifier.py` /
  `attestation.py` / `gate.py` — by *reading and naming* their contracts, never
  editing them.
- **Blast-radius / reversibility:** docs-only; fully reversible.
- **Fence:** `docs/design/dev-build-deploy-shared-contract.md` +
  `docs/plans/dev-build-deploy-spine.md`. No component fence (no seal).
- **Primitive check:** no new mechanism — P0 names existing primitives (the
  sealed floor's PreToolUse gate, hands-off-loop's frozen-acceptance, dev-sdlc's
  AC convention) and the contract over them.
- **Independently shippable when:** the spec is authored and the named decisions
  carry recommendations. **(MET by this dispatch.)**

---

### P1 — deploy tier: LOCAL

- **Objective:** let the owner run and verify their project against a LOCAL
  environment profile, expressing plain intent ("run it", "is it working"),
  with the floor idle (nothing irreversible exists at LOCAL) and the build's
  Acceptance produced in the shared shape.
- **Scope (in):** the LOCAL `role`/`tier: local` environment profile;
  `backing_services` declaration + the plain-language parity-gap surface
  (local SQLite vs prod Postgres, etc.); the `build` verb producing a shared
  Acceptance record; LOCAL secrets in the OS keychain (not SOPS-in-repo, the
  non-tech-safe default). **Out:** any remote deploy; any prod verb; promotion.
- **Outcome-shaped ACs:**
  - **AC.LOCAL.1:** a LOCAL build produces an Acceptance record in the P0 shape,
    judged by an independent check the builder did not control.
  - **AC.LOCAL.2:** the enabled command set at LOCAL contains no irreversible
    action (verified by absence of any prod/destroy verb) — the floor idles;
    a destructive-SQL guard at LOCAL warns, does not block (local DB disposable).
  - **AC.LOCAL.3:** when the LOCAL backing service differs from a downstream
    env's, the divergence is surfaced in plain language before any promotion is
    offered.
  - **AC.LOCAL.4:** a LOCAL secret is stored in the OS keychain, never written
    to a repo-committed file.
- **Dependencies:** P0 (the Acceptance shape + config model).
- **Composes on:** the sealed floor (idle at LOCAL but present); the
  secure-build baseline (secrets-never-committed already enforces AC.LOCAL.4's
  commit boundary); the full `local-target.md` deep-dive (folded in here — it
  was a degraded probe stub in the feature design; the real 29KB dimension is on
  disk).
- **Blast-radius / reversibility:** reversible; worst case is a local-only
  hiccup the owner sees.
- **Fence:** a new opt-in capability component (the LOCAL tier runbook/skill) +
  the additive config fields `role` / `backing_services`. Does NOT touch the
  sealed floor component.
- **Primitive check:** Skill (the LOCAL runbook, `paths:` auto-load in a
  deployable project) + the existing `build` verb (hands-off-loop generalized).
  No bespoke mechanism.
- **Independently shippable when:** the owner can build+verify+run locally
  through the spine with a shared Acceptance, and the parity-gap surface works,
  with no remote capability present.

---

### P2 — deploy tier: Vercel (preview → prod)

- **Objective:** let the owner publish to Vercel — preview by default
  (reversible), production behind a gate (reversible-with-effort via rollback) —
  expressing plain intent ("put it live", "undo that"), with go-live a
  loam-held action, not a git side-effect.
- **Scope (in):** the `preview` (ephemeral, `lifecycle: ephemeral`) and
  `production` environments with `provider_binding.provider: vercel`;
  `/publish` (preview default), `/promote`, `/rollback`; the
  promote-to-prod gate enforcing the P0 bridge (frozen Acceptance met +
  artefact-hash identity, AC.PROMOTE.1); F-9 loam-held go-live (a raw
  `git push` / web-UI merge builds a preview only, AC.GOLIVE.1); per-env secret
  isolation via `security_profiles` + `reachable_from` (F-2); Vercel Sensitive
  Env Vars; Spend-Management auto-pause; the read-only drift probe (D-SC.4
  divergence surface). **Out:** real-infra / IaC; irreversible DB migrations
  (P3); raw-cloud anything.
- **Outcome-shaped ACs:**
  - **AC.VRCL.1:** an owner publish with no target named produces a *preview*
    deploy (non-prod default); a broken result is visible only to the owner.
  - **AC.VRCL.2:** a production go-live cannot be triggered by a raw `git push`
    or web-UI merge — such a push yields a preview only; the only path that mints
    a production-deploy credential is loam's gated promote (AC.GOLIVE.1).
  - **AC.VRCL.3:** a promote-to-prod proceeds only when the artefact's frozen
    Acceptance is met AND the deployed hash equals the proven hash; a mismatch
    is surfaced as a NEW deploy needing fresh verification, never carried
    forward silently (AC.PROMOTE.1).
  - **AC.VRCL.4:** a request to resolve a `prod`-profile secret from a context
    not in that profile's `reachable_from` is denied (F-2).
  - **AC.VRCL.5:** every deploy/promote states its target and reversibility in
    the owner's vocabulary before it runs; a raw provider diff is never the
    surface (AC.TRANSLATE.1).
  - **AC.VRCL.6:** the one-step-rollback limit on Vercel Hobby is surfaced
    honestly (reversibility is one step deep on the free tier) — the gate-height
    logic accounts for "reversible *once*", not "reversible".
- **Dependencies:** P0, P1. **Owner rulings owed before build (carried from
  research §11):** Hobby-vs-Pro mandate for a locked-down prod site (open-Q 9);
  off-site backup DR rigor (open-Q 10, J); env-graph source-of-truth confirmed
  (decided P0 D-SC.4, ratify).
- **Composes on:** the floor's `max(declared,resolved)` gate (a Vercel-prod env
  is `tier: staging, is_production: true` per spec D-SC.3 — prod-gated, the floor
  already pins it to `high`); the refuse-all-destructive default; F-9
  credential-scoping.
- **Blast-radius / reversibility:** reversible-with-effort (rollback exists, one
  step deep on Hobby) — `shared-preview` for preview, `production` for live.
  First tier the public can see.
- **Fence:** the Vercel-tier capability component + additive config fields
  `provider_binding` / `promotes_to` / `domains` / `lifecycle` + the
  `security_profiles` block. Sealed floor untouched.
- **Primitive check:** Skills (`/publish` `/promote` `/rollback` runbooks) +
  PreToolUse gate composing on the sealed floor (no new gate engine — the
  promote gate adds preconditions to the floor's decision) + PostToolUse audit
  (AC.AUDIT.1) + background task for the deploy + Monitor for health. All
  existing primitives.
- **Independently shippable when:** the owner can publish a preview, promote to
  prod through the gate, and roll back — with go-live loam-held and the
  Acceptance bridge enforced — and no real-infra capability present.

---

### P3 — deploy tier: real-infra (irreversible)

- **Objective:** let the owner provision and operate real cloud infrastructure
  expressing plain intent, where genuinely irreversible actions exist, only
  behind the floor's F-0 attestation and the provider-side structural
  guarantees the floor deferred.
- **Scope (in):** the `tier: real-infra` environments with
  `provider_binding.provider: fly|render|aws|…`; the **live provider probes that
  populate the attestation record** (HALT-2 — the deferred half: deletion-protection
  / Object-Lock / app-role-cannot-DDL / `prevent_destroy` / versioned+encrypted
  state backend / scoped OIDC); `/provision` wrapping `tofu plan -out` → plain
  surface → human-only proof-of-intent (a fact loam did not display, AC.IRREV.1)
  → apply of the saved plan; OIDC keyless creds; loam-held state-backend write
  credential (G9); mandatory cooling-off on irreversible×prod (AC.COOL.1);
  expand/contract DB migrations with Tier-0-live backup verification (AC.DB.1);
  structural spend caps at provisioning (AC, G10). **Out:** dev-sdlc/hands-off
  restructure (P-final); multi-prod regional (deferred opt-in).
- **Outcome-shaped ACs:**
  - **AC.INFRA.1 (F-0 keystone):** an environment cannot be operated as
    real-infra production until a live read has verified its applicable floor
    controls are armed; absent/stale attestation ⇒ every destructive verb
    refused + owner told in plain words it is not yet protected. *(This
    populates the attestation contract the floor already enforces the default
    side of.)*
  - **AC.INFRA.2:** an irreversible destructive verb cannot be satisfied by any
    agent-settable token nor a verbatim echo of a displayed unlock word — only a
    human-produced fact loam did not display (AC.IRREV.1).
  - **AC.INFRA.3:** an irreversible×production action is queued behind a
    mandatory, default-on cancel window with a one-tap CANCEL on the owner's
    channel (AC.COOL.1).
  - **AC.INFRA.4:** a one-shot rename/drop migration is refused and decomposed
    into expand/contract; the contract (destructive) step is gated on a
    Tier-0-live fresh-backup + green restore-drill, with an overdue drill
    demoting the backup to unverified ⇒ refuse (AC.DB.1).
  - **AC.INFRA.5:** `tofu force-unlock` / state surgery is unreachable from the
    owner's terminal because loam holds the state-backend write credential (G9).
  - **AC.INFRA.6:** a destructive gate added here fails CLOSED under every
    `permission_mode` (AC.FLOOR.6) — verified as a precondition before the gate
    ships.
- **Dependencies:** P0, P2. **Hard prerequisites (carried, NON-NEGOTIABLE):**
  the F-0 provider probes (HALT-2); the R-3 go-live substitute prerequisite (a
  loam-hosted credential service / GitHub Pro that does not yet exist) — P3 may
  not present real-infra as protected until met or the owner accepts and names
  Wall-1+Wall-3-only.
- **Composes on:** the floor's F-0 attestation contract + refuse-all-destructive
  default (P3 supplies the probes the contract was built to consume); the
  fail-closed primitive (`framework/safety-layer/_fail_policy.py`); secure-build
  baseline.
- **Blast-radius / reversibility:** irreversible; `production`. Ships LAST,
  behind the heaviest gate, because it is the first tier with genuinely
  irreversible actions.
- **Fence:** the real-infra capability component + additive IaC config + the
  attestation-probe module that writes `.loam/attestations.yaml`. Sealed floor
  untouched (it reads the record; P3 writes it).
- **Primitive check:** Skills (`/provision` runbook) + PreToolUse gate (composing
  the floor) + launchd/CronCreate read-only drift + restore-drill probes +
  channel out-of-band CANCEL (commit `3db9360` alerting) + the persona for the
  plain-language translation of `tofu plan`. All existing primitives.
- **Independently shippable when:** the owner can provision real infra through
  the full ceremony, with F-0 attestation gating production-ness, the cooling-off
  and human-only-proof gates live, and the provider-side guarantees attested —
  or the honest refusal fires when they are not.

---

### P-final — dev-sdlc + hands-off-loop adopt the spine (LAST; loose-scoped)

- **Objective (provisional — re-planned at its own time):** restructure dev-sdlc
  and hands-off-loop so they run ON the spine's shared vocabulary and verbs
  rather than alongside them — dev-sdlc's ODD ACs *are* spine Acceptance
  records; hands-off-loop's `build` *is* the substrate `build` verb wired to
  `gate` and (owner-asked) `publish`.
- **Scope (deliberately loose — F4: deferred, highest-uncertainty):** the method
  for migrating dev-sdlc's existing AC corpus to the shared shape; the
  size-tiered ceremony fork (F1 in the product architecture — does `build` run
  the full amendment ritual or a scaled-down ceremony for small artefacts);
  whether capability plugins carry their own domain floors (F4 there). These are
  named as open forks, not decided here.
- **Outcome-shaped ACs (provisional, to be tightened at re-plan):**
  - **AC.ADOPT.1:** a dev-sdlc amendment cycle's ACs are expressible as spine
    Acceptance records with no loss of the seal-fence discipline.
  - **AC.ADOPT.2:** the hands-off-loop `build` verb, on completion, calls `gate`
    before returning "done", and `publish` (when owner-asked) calls `gate`
    before emitting a link — the floors are wired into the verbs' control flow,
    not left to persona discipline.
  - **AC.ADOPT.3:** the size-tiered ceremony resolves so a one-file widget gets
    objective+acceptance+floors only (no plan-doc, no seal) while a large/recurring
    build gets the full ODD cycle.
- **Dependencies:** P0–P3 all sealed and proven.
- **Composes on:** the entire spine + the build-publish substrate
  (`build`/`gate`/`publish` verbs, product architecture §3b).
- **Blast-radius / reversibility:** highest in the plan — it changes how loam
  builds loam (product == platform special case). Explicitly LAST.
- **Fence:** TBD at re-plan — spans `plugins/dev-sdlc/` and
  `plugins/loam-skills/skills/handsoff-loop/` + the substrate verbs. The widest
  fence in the arc; a reason it is last.
- **Primitive check:** to be authored at re-plan (the substrate verbs +
  hands-off-loop are existing; the wiring is the new mechanism).
- **Independently shippable when:** to be defined at re-plan. Named here only so
  the arc is complete and the deferred restructure has a home.

---

## §7 Cross-phase dependency graph + floor composition

```
            P0 (contract + spec)  ──────────────┐
              │  (Acceptance shape, config model, bridge, tier→risk-class)
              ▼                                  │
            P1 LOCAL ──► P2 Vercel ──► P3 real-infra ──► P-final (adopt)
              │            │              │
   composes:  │            │              │
   floor idle ┘            │              │
   max(declared,resolved) ─┘              │
   refuse-all-default ─────┘              │
   F-0 attestation contract ──────────────┘  (P3 supplies the deferred probes)
   per-gate fail-closed ──────────────────┘
   secure-build baseline ── P1,P2,P3 (secrets-never-committed boundary)
```

- **P1 composes on:** the floor (present, idle) + secure-build baseline.
- **P2 composes on:** `max(declared,resolved)` gate + refuse-all-default + F-9
  credential-scoping + P1.
- **P3 composes on:** the F-0 attestation *contract* (P3 writes the probes the
  floor already refuses-by-default without) + the fail-closed primitive + P2.
- **P-final composes on:** all of P0–P3 + the build-publish substrate.

**The load-bearing cross-phase fact:** the floor was built to consume an
attestation record it does not itself populate (HALT-2). P3 is the phase that
populates it. Until P3, the floor's promise ("an unattested production env
refuses all destructive verbs") is true *because nothing has attested* — the
default posture holds. P3 does not weaken that; it adds the path by which an env
can become attested-and-operable.

---

## §8 Out of scope (deferred + when)

- **dev-sdlc / hands-off-loop restructure** — P-final, re-planned at its own
  time (owner ruling: later, deliberate, not now).
- **Multi-prod (regional prod-us/prod-eu)** — deferred to a gated opt-in after
  P3 (research open-Q 11).
- **Marketplace distribution of loam-internal plugins** — a go-to-market call,
  separate from this architecture (architecture decision §"Open/deferred").
- **Any edit to the sealed floor's config/classifier/attestation/gate** — a
  fenced amendment to `deploy-safety-floor`, never folded into a tier phase.
- **`docs/spec/` objective edits** — outside any cycle's fence.

---

## §9 Halt triggers (in-flight, abort the build)

A phase builder halts and surfaces when:

- A phase's work would require editing a sealed floor source file (config /
  classifier / attestation / gate enum) — halt; the sealed enum is frozen
  (spec D-SC.3 exists precisely to prevent this).
- An AC about to be authored at build-time can only be satisfied by the one
  method the builder has in mind (method-in-AC) and cannot be reframed
  outcome-shape — halt; the feature may itself be method.
- A fail-closed verification (AC.FLOOR.6 / AC.INFRA.6) cannot be demonstrated
  under some `permission_mode` — halt; per G15 this is a build entry condition,
  the gate does not ship.
- P3 reaches production-operation with the R-3 prerequisite (loam-hosted
  credential service / GitHub Pro) unmet and the owner has not ruled
  accept-and-name — halt; do not present real-infra as protected.
- A provider probe (HALT-2) cannot read the provider state to attest a control —
  fail closed (unverifiable ⇒ unprotected ⇒ refuse), surface to owner (R-4).

---

## §10 Bookkeeping

- **`docs/STATE.md`** — change-log entry when each phase seals (P0 is docs-only:
  a note that the contract + spine plan landed).
- **`docs/release-roadmap.md`** — the spine arc registered as forward work;
  versions derive at each phase's release time, never pre-allocated
  (`feedback_version_numbers_at_release_time`).
- **`docs/design/loam-plugin-product-architecture.md` §6** — the Tier-0
  substrate elements `0g` (deploy-safety floor) and `0h` (secure-build baseline)
  already record the SEALED floor; backfill a pointer to this spine plan as the
  forward arc that builds the opt-in tiers on top.
- **`feedback_*` corpus** — no new memory owed by this docs cycle; the
  tier→risk-class reconciliation (D-SC.3) is captured in the spec, which is the
  durable surface.

---

## §11 F2 Ruthless Feedback (honest doubts + design risks)

1. **The three threads CAN share one contract cleanly — but only because the
   contract is two axes, not one.** If a future reader insists on a single
   done/safe word, the unification breaks and becomes a forced collapse. The
   spec's keystone (D-SC.1) is load-bearing; if it is ever "simplified" to one
   axis, re-open this plan. *Evidence:* `gate.py` reads the environment, never
   the artefact; dev-sdlc/hands-off read the artefact, never the environment —
   they are measuring different things. *Alternative if D-SC.1 were rejected:
   two parallel vocabularies with no bridge, which is the status quo this plan
   exists to fix.*

2. **P2 is the real risk, not P3.** P3 is correctly gated behind things that do
   not exist yet (R-3) and will honestly refuse until they do — its danger is
   visible and self-limiting. P2 carries the first public blast radius AND the
   most unresolved owner rulings (Hobby-vs-Pro, DR rigor, env-graph
   source-of-truth). *Recommendation:* P2's build dispatch must not start until
   research open-Q 9 / 10 are owner-ruled; the plan names them as build
   prerequisites (§6 P2 dependencies), not mid-build discoveries.

3. **`hands-off-loop` is local-only by hard rule today** ("never pushes,
   publishes, or tags"). The spine extends its remit past that rule at
   P-final. That is expected and correct — the deploy tiers ARE the separate
   owner-asked public step — but P-final must explicitly rewrite that hard rule,
   not silently violate it. Named so the adoption phase does not look like a
   regression. *Evidence:* `handsoff-loop/SKILL.md` "Local only" hard rule.

4. **Schema sprawl is a live risk across P1–P3.** Five+ additive config fields
   land across three phases. D-SC.5 (each field introduced just-in-time against
   the fixed target schema) is the mitigation, but it only holds if each phase
   builder reads the spec's §5.1 target before adding a field. The plan can't
   enforce that structurally from here; it is named as a standing risk for the
   phase dispatches to carry.

5. **P-final's scope is genuinely uncertain (F4 honest).** The size-tiered
   ceremony fork (F1 in the product architecture) is unresolved — where the cut
   is between "a one-file widget gets no ceremony" and "this gets the full ODD
   cycle" is not known. P-final is loose-scoped here deliberately; do not treat
   its provisional ACs as dispatch-ready. They are placeholders so the arc is
   complete.

---

## §12 Provenance trail

- Sealed floor source (Tier-0 read this session):
  `framework/deploy-safety-floor/src/loam/deploy_safety_floor/{config,classifier,attestation,gate,deny_message}.py`
  (`Tier` enum `{local,staging,real-infra}` at `config.py:61-67`);
  `framework/deploy-safety-floor/hooks/settings.fragment.json`;
  `framework/secure-build-baseline/src/loam/secure_build_baseline/strictness.py`.
- Research: `…/devops-pipeline-2026-06-27/{03-architecture-decision-plugins-vs-native,01-loam-feature-design,environment-model,loam-fit-claude-leverage}.md`
  (the `local-target.md` full deep-dive flagged for P1 fold-in; `02-redteam-gate-gaps.md`
  is the gap source the feature design's §12 hardening log indexes).
- loam corpus: `docs/design/loam-plugin-product-architecture.md`;
  `plugins/loam-skills/skills/handsoff-loop/SKILL.md`;
  `plugins/dev-sdlc/docs/conventions/plan-docs.md`;
  `feedback_version_numbers_at_release_time`, `feedback_scope_descriptive_ac_ids`,
  `feedback_test_outcome_altitude_required`, `feedback_value_proposition_as_prime_objective`,
  `feedback_strict_autonomy_no_pause_for_authorized_work`.
- Paired P0 deliverable: `docs/design/dev-build-deploy-shared-contract.md`.
- Predecessor seals: `cf1ed11e`, `828de228`, `e8c5d3b4`/`e0e9a258`, `3225eeee`; HEAD `243b3542`.
