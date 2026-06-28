# dev → build → deploy — the shared contract (P0 foundation spec)

**Date:** 2026-06-28
**Status:** DESIGN SPEC — the P0 foundation of the dev→build→deploy spine
unification (Option C, owner-ratified). This is the contract every later
phase (P1 LOCAL, P2 Vercel, P3 real-infra, P-final dev-sdlc/hands-off-loop
adoption) implements against. Docs-only; no code, no seal.
**Working tree:** `/Users/lukeivers/loam` (canonical, main)
**Parent plan:** `docs/plans/dev-build-deploy-spine.md`
**Author:** `loam-plan-author`
**Quality bar:** outcome-shaped requirements; method left to the phase builders.

**Predecessors (load-bearing, Tier-0 verified on disk this session):**
- The SEALED deploy-safety FLOOR — `framework/deploy-safety-floor/` (seals
  `cf1ed11e` config+classifier+attestation+gate; `828de228` per-gate
  fail-policy primitive in `framework/safety-layer/`; `e8c5d3b4`/`e0e9a258`
  fail-policy adoption) and `framework/secure-build-baseline/` (seal
  `3225eeee`). HEAD at authoring: `243b3542`.
- The architecture decision — `…/devops-pipeline-2026-06-27/03-architecture-decision-plugins-vs-native.md`
  (Option C: commit to the unified target, define the shared contract now,
  build the tiers next, fold dev-sdlc + hands-off-loop in last).
- The feature design + dimension deep-dives — `…/01-loam-feature-design.md`,
  `…/environment-model.md`, `…/loam-fit-claude-leverage.md`.
- The product architecture — `docs/design/loam-plugin-product-architecture.md`
  (Tier-0 substrate = build-publish engine + floors; the `build`/`gate`/`publish`
  verbs; `build` IS hands-off-loop generalized).
- The hands-off-loop SKILL — `plugins/loam-skills/skills/handsoff-loop/SKILL.md`
  (frozen-acceptance, independent judge, honest-negative).

---

## §0 What this contract is, in one paragraph

Three threads currently express "done" and "safe" in three private
vocabularies: **dev-sdlc** uses ODD acceptance criteria (one outcome-shaped
AC per test, laddering to the prime objective); **hands-off-loop** uses a
frozen, hash-pinned, independently-judged "done-when" statement; the
**deploy floor** uses a gate decision keyed to an environment's
production-ness, reversibility, and attestation. They share no surface today
— a deploy gate cannot reference what a build proved, and a build cannot
state its result in terms a deploy tier understands. This spec defines the
one vocabulary all three speak, so a single artefact can carry a proof of
correctness from build into a deploy gate without re-deriving it, and a
non-technical owner can be told "done" and "safe" in one consistent plain
language. It defines two things: (1) the unified acceptance-and-gate
vocabulary; (2) the unified per-environment config model spanning build and
deploy. Method — schema serialization, regex form, CLI flags — stays the
phase builders' call.

---

## §1 The load-bearing decision: two axes, not one word (Lens 7)

**The instinct this spec resists.** "Unify the acceptance vocabulary" reads
like "find one word that means done-and-safe." Forcing that collapse would be
the papered-over unification the dispatch warned against, and it would be
wrong on the evidence.

**The evidence.** "Done" and "safe" are measured against different things:

- dev-sdlc's AC and hands-off-loop's frozen-acceptance both answer **is the
  artefact correct** — verified by a deterministic check over the artefact
  (a test, an independent tool exit code). They are already the *same shape*:
  the product-architecture doc states the substrate `build` verb IS
  hands-off-loop generalized (§3b), and hands-off-loop's judge IS loam's own
  build methodology run for the user. These two need *naming*, not
  reconciling — they converged already.
- The deploy floor answers a different question entirely — **is this action
  safe to perform against this environment** — verified by reading the
  environment's structured production-ness, reversibility, and a live
  attestation, never by reading the artefact (`gate.py:evaluate_bash`). A
  perfectly correct artefact can still be unsafe to deploy (unattested prod,
  irreversible action, no fresh backup).

**The alternative (named).** Hold both as distinct, related concepts under one
contract:

1. **Acceptance** — the "done/correct" axis. A frozen, outcome-shaped,
   independently-checkable criterion. Shared verbatim by dev-sdlc ODD ACs and
   hands-off-loop frozen-acceptance.
2. **Gate** — the "safe-to-act" axis. An allow/ask/deny decision over a
   consequence-bearing action, keyed to reversibility × blast-radius ×
   attestation. Owned by the deploy floor and the tiers above it.

The **bridge** (§4) is what makes this a unification rather than two parallel
vocabularies: a Gate's preconditions may *require* an Acceptance to have
passed. Acceptance is an *input* to a Gate, not a synonym for it.

**Why this is the right call, not a hedge.** loam's own corpus keeps landing
on the same move — refuse to collapse two orthogonal axes into one. The
product-architecture doc split *tier* from *default-state* (§2) rather than
forcing Publish into one axis; the shared-artefact catalogue organizes by
*profile-class × blast-radius* (two axes); the floor itself computes
`max(declared, resolved)` because declared-label and resolved-target are two
axes. A one-word done/safe vocabulary would be the first place loam flattened
what it everywhere else keeps separate. **[HIGH confidence — this is the
spec's keystone decision; D-SC.1 in §6.]**

---

## §2 The Acceptance vocabulary (the "done/correct" axis)

The canonical Acceptance record. Every dev-sdlc AC, every hands-off-loop
frozen-acceptance unit, and every deploy gate-condition that references "did
the build pass" speaks this shape.

| Field | Meaning | Outcome-shaped requirement |
|---|---|---|
| `id` | scope-descriptive identifier (per `feedback_scope_descriptive_ac_ids`) | never version-packed; derived from the work's purpose |
| `statement` | the outcome, in one sentence, renderable to plain language | states WHAT is true when done, never HOW it was achieved |
| `check` | the deterministic, independent verifier | a method exists that decides pass/fail without trusting any builder's self-report; the *form* of the check (a test, a tool exit code, a probe) is the builder's call |
| `frozen` | whether the criterion is hash-pinned before any builder/sub-agent sees it | required `true` for any hands-off / dispatched build; the criterion is seen by no sub-agent and no per-sub-task judge |
| `altitude` | whether this is an outcome-altitude criterion | at least one Acceptance per set is satisfiable only by invoking the production entry-point with no pre-arranged state (per `feedback_test_outcome_altitude_required`) |
| `ladder` | the parent objective this rolls up to | every Acceptance traces up to AC.PO.1 / AC.PO.2 in `docs/VALUE_PROPOSITION.md` |

**What this generalizes (so no thread loses a property it has today):**

- dev-sdlc ACs already carry `id` / `statement` / `check` / `ladder` +
  outcome-altitude (the §4-§5 plan-doc convention + `feedback_test_outcome_altitude_required`).
  The contract adds `frozen` as an explicit field — already implicit in
  "author the test before the code" (plan-before-code).
- hands-off-loop already carries `statement` (the plain-English "done-when"),
  `frozen` (hash-pinned, frozen-unseen), and `check` (the independent
  tool-executing judge's exit code). The contract adds `id` / `ladder` /
  `altitude` so a hands-off "done" can be referenced by a gate and traced to
  the prime objective.

**The non-negotiable property the contract preserves from both:** the check is
**independent of the producer**. dev-sdlc forbids non-objective code that no
test names; hands-off-loop forbids trusting a sub-agent's self-report. The
unified rule: *an Acceptance is met only when a check no builder controlled
says so.* A leak of a frozen criterion into a brief or judge is a refusal,
not a warning (hands-off-loop hard rule, preserved).

**Honest-negative is a first-class Acceptance outcome.** A definite "not met,
here is the evidence" is a complete result, never retried-to-green or softened
(hands-off-loop). The contract carries this so a deploy gate that depends on an
Acceptance can distinguish *failed* from *not-yet-run* and refuse on either.

---

## §3 The Gate vocabulary (the "safe-to-act" axis)

The canonical Gate record, built directly on the sealed floor's primitives so
the tiers extend the floor rather than reinventing it.

| Field | Values | Source / status |
|---|---|---|
| `action` | the consequence-bearing operation (deploy, promote, destroy, migrate, provision) | the thing being gated |
| `reversibility` | `reversible` · `reversible-with-effort` · `irreversible` | the dominant gate-height signal (Lens 6). The sealed floor carries a coarse `reversible` boolean per env (`config.py`); this taxonomy is its refinement — the boolean is the conservative projection (`reversible-with-effort` and `irreversible` both map to `reversible: false`) |
| `blast_radius` | `local` · `shared-preview` · `production` | who is affected if it goes wrong |
| `declared_gate` | `none` · `low` · `medium` · `high` | **sealed enum — KEEP EXACT** (`config.py:GateLevel`); a production-class env is pinned to ≥ `high` |
| `effective_gate` | `max(declared, resolved-target production-ness)` | **sealed — KEEP EXACT** (`classifier.py:compute_gate_strength`); the keystone that stops a low label disarming a prod-pointed action |
| `attestation` | `fresh` · `stale` · `absent` | **sealed — KEEP EXACT** (`attestation.py`); absent/stale ⇒ refuse-all-destructive |
| `decision` | `allow` · `ask` · `deny` | the floor emits `allow`/`deny` today (`gate.py:Decision`); `ask` is the above-floor middle the tiers add (a human-only proof-of-intent or a cooling-off window), never a floor-level value |

**The gate-level → behavior mapping (above-floor, defined per tier).** The
sealed `none|low|medium|high` ordinal is the *declared protection*; the
*behavior* each level triggers is layered by the tiers and is additive:

- `none` → no gate (LOCAL disposable).
- `low` → state the target in plain words, proceed.
- `medium` → target-confirm before acting.
- `high` → on a *reversible* prod action, target-confirm; on an *irreversible×production*
  action, a human-only proof-of-intent loam did not display (a record count,
  not an echoed token — AC.IRREV.1 in the research) **plus** a mandatory
  cooling-off cancel window (AC.COOL.1).

This keeps the sealed enum frozen and expresses every research gate behavior
(confirm / target-confirm / name-match / cooling-off) as a *behavior bound to a
level*, never a new enum value. **[D-SC.2 in §6.]**

**Plain-language is a floor property of every Gate, not a tier nicety.** The
floor already renders deny messages with the substance exposed and the
vocabulary adapted, secret values never echoed (`deny_message.py`, doctrine
"expose the substance, adapt the vocabulary"). The contract makes this a
required property of *every* Gate decision message at every tier: name what
would happen, to what, and whether it can be undone, in the owner's words; a
raw provider diff (`tofu plan`, `~ aws_db_instance.main (forces replacement)`)
is never the surface (AC.TRANSLATE.1).

---

## §4 The bridge — Acceptance as a Gate input

This is the single seam that makes the spine one thing instead of three.

A Gate's `preconditions` is a set that may contain Acceptance references. The
canonical example, already named in the research as AC.PROMOTE.1: a
**promote-to-production** Gate's preconditions are

1. the frozen Acceptance for this artefact is `met` (the build proved correct),
   **and**
2. the artefact hash promoted is identical to the one the Acceptance checked
   (no silent rebuild — a hash mismatch is a NEW deploy needing fresh
   Acceptance), **and**
3. the environment's `effective_gate` is satisfied and its `attestation` is
   `fresh`.

Condition (1) is the bridge: the *same* Acceptance object a build produced is
read by a deploy gate. Without the shared vocabulary, the gate would have to
re-prove correctness or trust an unverifiable claim; with it, the proof rides
forward as data. Condition (2) is why Acceptance carries an artefact identity —
a "done" is "done *for this exact artefact*," and the gate enforces that the
thing being deployed is the thing that was proven.

**Direction of dependency (load-bearing):** Acceptance never depends on Gate.
A build can complete and be "done" with no deploy in sight (hands-off-loop is
local-only today — it builds and verifies, never publishes). A Gate depends on
Acceptance only at the deploy boundary, and that boundary is always a distinct,
owner-asked action — never an automatic continuation of a build. The spine is
**build → gate → deploy with an owner gate at the deploy boundary**, not a
pipeline that ships on green.

---

## §5 The unified per-environment config model (build + deploy)

### 5.1 The reconciliation principle: additive superset over the sealed core

The sealed floor already defines and reads a per-environment config
(`config.py`, `.loam/environments.yaml` ‖ `deploy.yaml`). That schema is
**SEALED** — the contract does not change it; later phases add *optional*
fields the floor ignores and the tiers read. Three bands:

**CORE (sealed — frozen, every field exactly as shipped; changing any is a
fenced amendment to `deploy-safety-floor`, explicitly out of this spine's
near phases):**

```
name · id · is_production · tier · reversible · gate · security_profile ·
identities{hosts,buckets,accounts} · active
```

**TIER-EXTENSION (additive, optional; the floor ignores these, the deploy
tiers read them; introduced by the phase that needs each):**

```
role            # development | preview | production | custom (P1/P2)
promotes_to     # next node in the promotion DAG, or null (P2)
provider_binding{ provider, target }   # vercel|fly|render|aws|… + the provider-side env (P2/P3)
domains         # attached URLs (P2)
lifecycle       # ephemeral → auto-teardown on PR close (P2)
branch_tracking # git ref that auto-deploys here (P2)
backing_services # declared kind+version, for parity checking (P1)
```

**SECURITY-PROFILES (additive top-level block the `security_profile` string
keys into; introduced when prod-credential isolation lands, P2/P3):**

```
security_profiles:
  <name>:
    reachable_from: [<env>, …]   # the load-bearing isolation field (F-2)
    secret_store: oidc | vercel-sensitive | os-keychain
    credential_scope: least-privilege
    audit_level: full | light
    rotation: { max_age_days: N }
```

The sealed floor's `security_profile` field is the *key*; this block is the
*definition* it points at. Additive — the floor reads only the string today.

### 5.2 The tier reconciliation (Lens 7 — a real gap in the sealed schema)

**The finding.** The sealed `Tier` enum is exactly `{local, staging,
real-infra}` (`config.py:Tier`, verified). The deploy tiers are LOCAL →
**VERCEL** → real-infra. There is **no `vercel` value** in the sealed enum,
and `staging` is a deployment-*stage* name, not a provider. A naïve mapping
would force a Vercel-production environment to declare `tier: staging,
is_production: true`, which reads as a contradiction and invites a future
builder to "fix" it by editing the sealed enum.

**The resolution (do NOT touch the sealed enum).** Treat the sealed `tier` as
the floor's coarse **risk class**, not the provider:

- `local` → disposable (the floor mostly idles).
- `staging` → reversible remote (rollback exists — Vercel preview *and*
  production both land here; reversibility, not provider, is what the floor
  cares about).
- `real-infra` → irreversible-capable (the floor treats it as production-class
  regardless of `is_production` — `config.py:is_production_class`).

The **provider** (vercel / fly / aws / …) lives in the additive
`provider_binding`, an orthogonal axis. The floor only ever branches on
`real_infra` and `is_production` — it never needs the provider — so this
mapping respects the seal completely while giving the tiers the provider field
they need. **A Vercel-production env is `tier: staging, is_production: true,
reversible: true, provider_binding.provider: vercel` — and that is coherent,
not contradictory, once `tier` is read as risk-class.** **[D-SC.3 in §6 — the
spec's most consequential reconciliation; it is the difference between the
tiers composing on the sealed floor and a future builder breaking the seal to
add `vercel`.]**

### 5.3 Authoritative-vs-cache (resolves research open-Q6 / environment-model open-Q1)

`deploy.yaml` is **authoritative for topology and policy** — the environment
set, the promotion DAG, the structured gate-relevant fields. Provider state
(Vercel's server-side env, Terraform state) is **authoritative for live
reality**. Divergence between them is **surfaced, never silently resolved**:
a read-only drift probe (the deploy tiers own it) compares declared topology to
provider reality and reports the gap in plain language; remediation is a gated,
dry-run-first action, never an auto-sync. This mirrors the floor's own
"policy in YAML, enforcement in hook" split and the F-0 attestation model,
where `.loam/attestations.yaml` records a live provider read rather than the
YAML asserting the provider's state. **[D-SC.4 in §6.]**

### 5.4 Identity and rename-safety (inherited, stated so phases don't re-litigate)

Identity is the immutable `id` (ULID-shaped), never the name — already sealed
(`config.py`, `classifier.py:resolve_target` matches structured identities, not
names). Rename is therefore the *safest* mutation (cosmetic relabel, zero
downstream breakage); remove-production is the *most dangerous* (HARD gate,
default-refuse, secrets tombstoned). Phases inherit this; none may key any gate
or secret binding off the name.

---

## §6 Named decisions, with recommendations

Each carries a recommendation as a decision (not a question). The owner rules
only where a decision is critical-call / public-action / financial — none here
are; these are design calls inside the authorized foundation, surfaced for
visibility per Lens 7.

1. **D-SC.1 — Two axes (Acceptance + Gate), not one done/safe word.**
   *Recommendation:* adopt. It is the keystone; it is what every other loam
   two-axis decision precedents support; collapsing would be the one place
   loam flattened what it everywhere keeps separate (§1).

2. **D-SC.2 — Gate behaviors are bound to the sealed `none|low|medium|high`
   levels, not expressed as new enum values.** *Recommendation:* adopt. Keeps
   the sealed enum frozen; expresses every research gate behavior as a
   level-bound behavior the tiers layer additively (§3).

3. **D-SC.3 — `tier` is the floor's risk-class; provider lives in additive
   `provider_binding`; the sealed `Tier` enum is NOT extended with `vercel`.**
   *Recommendation:* adopt. This is the difference between the tiers composing
   on the sealed floor and a future builder breaking a sealed component to add
   a provider value. Highest-leverage reconciliation in the spec (§5.2).

4. **D-SC.4 — `deploy.yaml` authoritative for topology+policy; provider
   authoritative for live state; divergence surfaced not auto-resolved.**
   *Recommendation:* adopt. Resolves the open question both dimension
   deep-dives flagged; matches the sealed policy/enforcement split (§5.3).

5. **D-SC.5 — Config grows only as additive optional bands; each TIER-EXTENSION
   field is introduced by the phase that first needs it, against the full
   target schema named here.** *Recommendation:* adopt. Prevents schema sprawl
   (every phase improvising fields) and prevents a premature mega-schema; the
   target is fixed now, the fields land just-in-time (§5.1).

6. **D-SC.6 — The deploy boundary is always a distinct owner-asked action; the
   spine never ships on green.** *Recommendation:* adopt. Preserves
   hands-off-loop's local-only hard rule and the product-architecture's
   "offering is open, acting is surface-first" asymmetry (§4).

---

## §7 What this contract deliberately leaves to the phase builders (method)

Per ODD, the contract fixes outcomes; method is the builder's call. Left open:

- The serialization of the Acceptance record (a JSON sidecar, a YAML block, a
  dataclass) — the *shape* is load-bearing, the encoding is not.
- The regex / parser form of every gate classifier (the floor already chose
  `re`; tiers choose their own detectors).
- Which external binaries detect what (gitleaks, `tofu plan`, `vercel`, engine
  detection) — composed tooling, the builder selects and the phase brief names.
- The cooling-off window length, the salience-budget thresholds, the drift-probe
  cadence — calibration, dark-launched per the interaction-model discipline.
- Whether a given Acceptance check is a pytest, a shell exit code, or a probe.

---

## §8 Provenance trail

- Sealed floor source read this session: `framework/deploy-safety-floor/src/loam/deploy_safety_floor/{config,classifier,attestation,gate,deny_message}.py`;
  `hooks/settings.fragment.json`; `framework/secure-build-baseline/src/loam/secure_build_baseline/strictness.py`.
  `Tier` enum confirmed `{local, staging, real-infra}` at `config.py:61-67`.
- Research artefacts: `…/devops-pipeline-2026-06-27/{03-architecture-decision-plugins-vs-native,01-loam-feature-design,environment-model,loam-fit-claude-leverage}.md`.
- loam corpus: `docs/design/loam-plugin-product-architecture.md` (two-axis precedent §1-§2, build/gate/publish verbs §3b);
  `plugins/loam-skills/skills/handsoff-loop/SKILL.md` (frozen-acceptance, independent judge, honest-negative, local-only);
  `plugins/dev-sdlc/docs/conventions/plan-docs.md` (AC convention);
  `feedback_test_outcome_altitude_required`, `feedback_scope_descriptive_ac_ids`,
  `feedback_value_proposition_as_prime_objective`.
- The research's AC families this contract carries forward by reference:
  AC.FLOOR.*, AC.IRREV.1, AC.COOL.1, AC.PROMOTE.1, AC.TRANSLATE.1, AC.AUDIT.1,
  AC.GOLIVE.1, AC.DB.1 (`01-loam-feature-design.md` §10).
