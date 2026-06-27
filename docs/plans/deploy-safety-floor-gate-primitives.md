# Deploy-safety FLOOR — framework-native gate primitives (plan-doc)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-06-27 by `loam-plan-author`.
**Working directory:** `/Users/lukeivers/loam/` (CANONICAL loam — NOT pos3).
**Parent / governing frame:** architecture decision `…/devops-pipeline-2026-06-27/03-architecture-decision-plugins-vs-native.md` (RECOMMENDATION, owner ratification **pending** — see HALT-1). Floor = framework-native, non-trivially-disable-able hooks; deploy tiers are opt-in capabilities ON TOP. This plan covers **only the floor**.
**Predecessors (load-bearing prior seals):**
- Research artefacts (pos3): `01-loam-feature-design.md` (F-0…F-9 floor + §12 hardening log + §13 residuals), `02-redteam-gate-gaps.md` (the 6+ CRITICAL gaps), `03-architecture-decision-plugins-vs-native.md`, plus `destructive-action-gates.md` / `secrets-and-security-profiles.md` / `database-lifecycle-safety.md`.
- `framework/safety-layer/` (sealed) — `action_class.py` `FrameworkFloorCategory`, `dangerous_op.py` `DangerousOpGate.classify(spec)`, PreToolUse guards (`secret_pattern_guard`, `dangerous_flag_guard`, `config_write_guard`, `wd_discipline_guard`); fail-policy convention `D-SECHK.FAIL-OPEN`.
- `framework/protection-matrix/` (sealed) — `data/failure-mode-guard-matrix.yaml` + `loam guards` coverage verb.
- `docs/FUTURE_IDEAS_DRAFT.md` lines 481–483 — `F-SECURE-BUILD-BASELINE` Tilth directive (part of this floor).
- `docs/design/loam-plugin-product-architecture.md` — Floors / Good-by-default / Capabilities trust-tier model.
**BASELINE (pre-build tip):** assigned at build-dispatch time (current canonical HEAD `1fcad58` is the candidate; reconcile-first per `feedback_sync_check_before_build_on_checkout`).
**Status-file target:** `<workspace>/.scratch/claude-output/deploy-safety-floor-status-2026-06-27.md`.
**Quality bar:** a floor that betrays no user. No partial gate. Every floor guarantee is either enforced framework-side OR honestly named as deferred-to-deploy-tier (no oversold gate — §10 F2).

---

## §1. Summary / TL;DR

This plan authors the **always-on safety FLOOR** for loam's productionizing capability: framework-native PreToolUse gate primitives that every higher (opt-in) deploy tier composes on top of, and that no user, agent, or marketplace toggle can casually turn off. It is the high-confidence, reversible first slice (F4: outcome shape is well-specified by the red-team → tight scope).

**What ships (the floor primitives, NOT the deploy tiers):**

1. **Per-environment config abstraction** — an inert, owner-editable `deploy.yaml` / `.loam/environments.yaml` schema (`is_production` boolean, `tier`, `reversible`, `gate`, `security_profile`, immutable ULID identity) that the gate hooks READ. Policy in YAML; enforcement in the hook.
2. **Destructive-action classifier + gate-decision** keyed off the **RESOLVED TARGET's** production-ness, never the environment label. Gate strength = `max(declared protection, resolved-target production-ness)` (closes G2). Rename-safety preserved (gate reads structured fields, not the name — G-preserve).
3. **Fail-CLOSED gate-policy primitive** — a per-gate fail-policy so a destructive gate whose hook errors **blocks**, inverting the existing sealed `D-SECHK.FAIL-OPEN` convention *for the floor gate class only* (closes G15). This is the keystone deliverable; it is purely framework-side.
4. **Floor-attestation record contract + refuse-all-destructive default** — the framework-side half of F-0/G1: an environment may not operate as `is_production` / `tier: real-infra` without a non-stale attestation record; absent/stale ⇒ refuse-all-destructive + plain-words "not yet protected". (The *live provider probes* that populate the record are deploy-tier — see §3 Surface D / HALT-2.)
5. **Secure-build baseline (Tilth, F-SECURE-BUILD-BASELINE)** — secrets-never-committed at the commit/push boundary; a dependency-hygiene audit gate (`npm audit` / `pip-audit` shelled-out) on the build path; artifact-cleanliness (correct generated `.gitignore` for harness runtime state + secrets + a pre-commit sweep).
6. **Protection-matrix catalogue rows** — every new floor guard is registered in `failure-mode-guard-matrix.yaml` as `default-on: true`, `floor: true`, so `loam guards` reports coverage and the floor is machine-verifiable.

**AC families:** `AC.DSF.*` (deploy-safety floor: config / classifier / fail-closed / attestation) + `AC.SBB.*` (secure-build baseline) + `AC.COV.*` (protection-matrix coverage). One outcome-altitude AC (`AC.DSF.7`) invokes the real PreToolUse hook entry-point with raw stdin and no pre-arranged state.

**F2 on scope realism (full §10):** several items the design doc calls "floor" (F-2 prod-cred isolation, F-3 irreversible proof-of-intent, F-8 backup-freshness, F-9 loam-held go-live) are floor *guarantees* whose enforcement **cannot exist framework-side without a provider integration that lives in the deploy tiers**. This plan delivers the framework-side primitives that are real today and **explicitly defers the provider-dependent halves**, naming each so no gate is oversold. That honest split is the single most important thing this plan does.

---

## §2. Placement decisions (per partition rule)

| Item | Placement (recommended) | Rationale |
|---|---|---|
| Per-environment config schema + loader (`deploy.yaml`/`environments.yaml`) | NEW component `framework/deploy-safety-floor/` | The config is a new policy surface read by new gates; co-locating schema + classifier + attestation in one floor component keeps the fence coherent. (Alternative: workspace-bootstrap owns schemas — see Decision A.) |
| Destructive-action classifier + gate-decision (`max(declared, resolved)`, rename-safety) | NEW component `framework/deploy-safety-floor/` | Net-new classifier; reads the config above. Composes on `safety-layer`'s `action_class.FrameworkFloorCategory` + `dangerous_op` enums rather than re-deriving them. |
| Fail-CLOSED gate-policy primitive (per-gate fail-policy field) | `framework/safety-layer/` (extend) | The fail-policy convention `D-SECHK.FAIL-OPEN` lives here; the new fail-policy field belongs where the convention it amends lives, so existing advisory guards keep failing open (no regression) and only floor gates opt into fail-closed. |
| Attestation-record contract + refuse-all-destructive default posture | NEW component `framework/deploy-safety-floor/` | Framework-side half of F-0. The record schema + default posture + the gate that enforces "is_production needs a fresh record" are inert without provider probes (deferred). |
| Secrets-never-committed at commit/push | `framework/safety-layer/` (extend `secret_pattern_guard`) | A staged-diff secret guard at the commit boundary is the same surface as the existing inbound-paste secret guard; extend, don't fork. |
| Dependency-hygiene audit gate + artifact-cleanliness sweep | NEW component `framework/secure-build-baseline/` | Tilth's directive targets artifacts loam **BUILDS** (a distinct surface from securing loam ITSELF). FUTURE_IDEAS names the natural home as "a secure-build baseline gate the build capability applies by default." Kept as its own component so the build-path floor is not entangled with the deploy-path floor. (Alternative: fold into `hands-off-lifecycle` — see Decision B.) |
| Catalogue rows for every new guard | `framework/protection-matrix/` (extend `failure-mode-guard-matrix.yaml`) | The floor must be machine-verifiable via `loam guards`; an un-catalogued floor guard is an invisible floor. |
| Hook registration | each component's `settings.fragment.json`, composed by the workspace-sync auto-composer | Matches the existing framework-native hook-wiring pattern (`frame-kernel/hooks/settings.fragment.json`). |

---

## §3. Halt-and-surface BEFORE build (named decisions + recommendations)

Every decision below is surfaced WITH a recommendation. Decisions A–E are autonomous-and-recorded (builder proceeds on the recommendation unless owner overrides). **HALT-1 and HALT-2 are genuine owner gates** — the build does not start (HALT-1) / does not claim a guarantee it cannot enforce (HALT-2) until ruled.

### HALT-1 (owner gate) — the governing architecture decision is ratified-PENDING

The floor is built UNDER `03-architecture-decision…` which is a RECOMMENDATION awaiting Luke's async ratification. The doc-work (this plan) proceeds per the drop-and-complete authorization, but **no build dispatches until the floor=framework-native decision is ratified** (recording it durably in the artefact per `feedback_record_owner_ratification_before_dispatch`). *Recommendation: ratify as written (floor = framework-native, non-disable-able); it is the unambiguous, reversible part everyone agrees on per `03` §6.*

### HALT-2 (owner gate / F2) — "floor" items that CANNOT be enforced framework-side

This is the load-bearing disagreement with the design docs (Lens 7). The red-team's own meta-finding is that the honest "impossible-by-accident" guarantee lives at the provider layer (Wall 3), which is **out of this floor's scope** (it is the deploy tiers). Consequence: the following design-labelled "floor" guarantees have **no framework-side enforcement** and this plan delivers only their framework-side *scaffold*:

| Design "floor" item | Framework-side (in this plan) | Provider-side (deferred to deploy tier) |
|---|---|---|
| **F-0 / G1** floor-attestation | attestation-record contract + refuse-all-destructive default + the gate that enforces "is_production needs a fresh record" | the **live Tier-0 provider read** that proves deletion-protection on / Object-Lock on / app-role-lacks-DDL / `prevent_destroy` present / OIDC scoped — needs provider adapters |
| **F-2** prod-cred isolation | `reachable_from` config field + a deny on cross-profile secret resolution *within loam's own resolver* | OIDC/IAM scoping so the dev role *physically cannot mint* a prod token |
| **F-3 / G4** irreversible proof-of-intent | n/a framework-side without a destructive provider verb to gate | the not-displayed-fact challenge fires only when a real irreversible op exists |
| **F-8 / G6** backup-freshness | n/a — there is no backup without a provider | the live snapshot-timestamp + drill-heartbeat read |
| **F-9 / G8** loam-held go-live | n/a — there is no deploy credential to scope yet | credential-scoping so a raw push has no promote credential |

**The honest floor (this plan):** items 1, 3, 5, 6 of §1 are *fully* framework-side; the attestation half of item 4 is framework-side scaffold only. *Recommendation: ratify the split — ship the framework-side floor now, and treat each provider-side half as an entry condition of its deploy tier (the attestation PROBES gate `is_production` at tier-onboarding; the floor's refuse-all-default holds until they pass). The floor's promise to the owner is "an unattested production environment refuses all destructive verbs" — which is TRUE framework-side because the default posture is enforced framework-side even though the proof that flips it is provider-side.*

### Decision A (autonomous — recorded) — config schema home

`deploy.yaml`/`environments.yaml` schema lives in the new `deploy-safety-floor` component, not `workspace-bootstrap`. *Recommendation: new-component (chosen). Rationale: the schema is read only by the floor gates and is coupled to the classifier; splitting schema from its sole consumer adds a cross-component seam for no benefit. Reversible (a later cycle can hoist the loader into workspace-bootstrap if a second consumer appears).*

### Decision B (autonomous — recorded) — secure-build-baseline home

Secure-build (dependency-audit + artifact-cleanliness) is its own `framework/secure-build-baseline/` component vs folded into `hands-off-lifecycle`. *Recommendation: own component. Rationale: it secures what loam PRODUCES (distinct surface from `hands-off-lifecycle`'s build *orchestration*); a clean fence + its own catalogue rows keep the floor auditable. Reversible.*

### Decision C (autonomous — recorded / F2 vs the design) — fail-closed without regressing existing guards

The design (01 §3) frames fail-closed as a blanket precondition; but the existing sealed `D-SECHK.FAIL-OPEN` is *correct* for advisory guards (an advisory guard that fails closed would block all work on any bug). *Recommendation: introduce a **per-gate fail-policy field** on gate registration — default `fail-open` (preserves every existing sealed guard's behavior, zero regression); the destructive-floor gate class declares `fail-closed`. This satisfies G15 for the floor without inverting the convention everywhere. The alternative (a separate gate class hierarchy) is heavier for the same outcome.*

### Decision D (autonomous — recorded) — gate-strength target resolution is config-declared, not live-probed

"Resolve the target's production-ness" framework-side means: compare the command's resolved connection target against the **declared** known-prod identities in config (`prod` profile's host/bucket/account), and block a prod-shaped connection string written into a non-prod config. It does NOT mean a live provider call (that is deploy-tier). *Recommendation: ship the config-declared comparison + write-time block now; it closes the G2 cases that need no provider (pasted prod string into `.env.local`, low-protection env pointed at the declared-prod host). The novel-form residual (R-2) stays open and is named to the owner — detection is reduce-not-eliminate.*

### Decision E (autonomous — recorded / F2) — "non-disable-able" is "non-trivially-disable-able"

`03` says framework-native takes "a deliberate file edit / admin policy" to disable, vs a plugin's one-command disable. A settings.json hook IS user-editable. *Recommendation: state this honestly in the floor's own docs — the floor raises disable-friction (no `/plugin disable`; requires editing `settings.json` or the fragment), and TRUE non-disable requires Claude Code managed-settings / admin policy. Recommend wiring the floor fragment as managed-settings-eligible and naming the managed-settings path as the hard-non-disable upgrade, rather than claiming an absolute that the mechanism does not deliver.*

---

## §4. Spec-objective placement (ladder-up)

**Binds to:**
- **AC.PO.1** (translation-burden, `docs/VALUE_PROPOSITION.md`) — the floor lets a non-technical owner operate near production while never learning `is_production`, fail-policy, or `prevent_destroy`; the protection is ambient.
- **AC.PO.2** (harness toolkit) — the gate+classify+config-read primitive is a reusable substrate the persona invokes for any consequence-bearing action, and every deploy tier composes on it.
- **Lens 0 protection floor** — these guard the failures that betray *any* user (dropping prod, leaking a secret, shipping a known-CVE artifact); always-on, non-tunable, identical for everyone.
- **`loam-plugin-product-architecture.md` Floors tier** — this IS the Floors tier instantiated for the deploy/build surface.

**Ladders:** `AC.DSF.*` + `AC.SBB.*` + `AC.COV.*` → deploy-safety-floor → (every opt-in deploy tier composes on it) → AC.PO.1 / AC.PO.2.

---

## §5. Acceptance criteria

Every AC is outcome-shaped. Method-in-AC test applied to each: *could a different method satisfy it?* — yes for all (regex form, YAML key names, which CLI the audit shells out to, whether the classifier is a parser or a table are all the builder's call). Per ODD §2.5 every AC maps to a named floor objective; no AC names a deploy-tier capability.

### AC.DSF.* — deploy-safety floor

- **AC.DSF.1 (config abstraction is inert policy).** A `deploy.yaml` carrying `is_production` / `tier` / `reversible` / `gate` / `security_profile` / immutable-id per environment parses into a typed model; an invalid `tier` or a missing `is_production` is rejected at load (fail-closed load). The file itself triggers no action — only a gate reading it does.
- **AC.DSF.2 (classifier keys off resolved target, gate = max(declared, resolved); G2).** A destructive command resolved against a target matching the config's declared-prod identity (host/bucket/account) is gated at the prod level **even when the active environment is declared non-prod**; gate strength is shown to derive from `max(declared, resolved)`, never the declared label alone.
- **AC.DSF.3 (rename-safety preserved).** An environment renamed away from "production" while `is_production: true` retains the full prod gate; gate height derives from structured fields, not the name. (Regression guard — the design's existing-correct property must not break.)
- **AC.DSF.4 (write-time prod-string block; G2 closeable part).** A prod-shaped connection string (matching a declared-prod identity) written into a non-prod / local config file is blocked at write time, with the secret value never echoed into any reply, brief, or log.
- **AC.DSF.5 (fail-CLOSED for the floor gate class; G15 — keystone).** A floor destructive gate whose hook raises / times out / receives malformed input **denies** the action (does not fall open), while a non-floor advisory guard under the same fault still fails open (existing convention preserved). Verified to hold under every `permission_mode` Claude Code exposes (including any bypass/accept-all mode).
- **AC.DSF.6 (attestation gate + refuse-all-destructive default; F-0/G1 framework-side).** An environment marked `is_production` / `tier: real-infra` with no attestation record, or a stale one, refuses every destructive verb and surfaces, in plain words, that it is not yet protected. (The record is populated by deploy-tier provider probes — out of scope; the DEFAULT POSTURE and the refusal are in scope and enforced here.)
- **AC.DSF.7 (OUTCOME-ALTITUDE).** Invoking the real floor PreToolUse hook entry-point with raw stdin and **no pre-arranged fixture/state** — a fabricated destructive command in an `is_production: true` context with no attestation record — returns a deny decision whose message names the target and the destructive sub-action in non-technical vocabulary; and the same entry-point, fed input that makes its classifier raise, still returns deny (fail-closed). `outcome-altitude: true`.

### AC.SBB.* — secure-build baseline (Tilth F-SECURE-BUILD-BASELINE)

- **AC.SBB.1 (secrets-never-committed at the boundary).** A commit/push whose staged diff contains a credential pattern is blocked at the commit/push boundary, with no secret value echoed anywhere; the block fires for the artifact loam BUILDS, not only for loam's own repo.
- **AC.SBB.2 (dependency-hygiene audit gate).** A build of a supported-ecosystem artifact (Node/Next + Python as the first ecosystems) runs the ecosystem audit and, on a known-vuln at or above a configured severity floor, blocks-or-surfaces per the configured strictness; a clean audit passes silently.
- **AC.SBB.3 (artifact-cleanliness).** A generated project carries a correct `.gitignore` covering harness runtime state (`.scratch/`, workspace memory queues, tracker `.sqlite`) + secrets + `.env`, AND a pre-commit sweep prevents those paths from entering the artifact even under `git add -A`.
- **AC.SBB.4 (baseline is non-tunable floor).** The three guarantees above are on for every build by default and cannot be disabled by ordinary project config; their strictness (block vs surface) is the only tunable, and the floor (a secret is never committed) is not among the tunables.

### AC.COV.* — protection-matrix coverage

- **AC.COV.1 (every floor guard catalogued + default-on).** Each new gate is present in `failure-mode-guard-matrix.yaml` as `default-on: true`, `floor: true`, with its verification method; `loam guards` reports the floor guards as covered and names no floor gap introduced by this cycle.

---

## §6. Build steps (Lens 5 decomposition — serialized sub-cycles, builder's call on method)

Recommended decomposition into three serialized sub-cycles, each with a strictly tighter AC than "the floor" (Lens 5 stopping criterion: stop before any split that adds only coordination). Serialized per `feedback_serialize_amendment_builds`. Each sub-cycle authors its own manifest at build-dispatch time (see §9).

- **Sub-cycle A — config + classifier + attestation scaffold** (`framework/deploy-safety-floor/` NEW). ACs: `AC.DSF.1, .2, .3, .4, .6, .7`. Source: config schema + loader; classifier reading `safety-layer` enums; gate-decision `max(declared, resolved)`; attestation-record contract + refuse-all-destructive default; the PreToolUse hook + `settings.fragment.json`. Tests per AC. `loam amend apply` → `loam amend seal` → smoke (fabricated destructive command in declared-non-prod-but-prod-targeted context is denied).
- **Sub-cycle B — fail-CLOSED gate-policy primitive** (`framework/safety-layer/` extend). ACs: `AC.DSF.5`. Source: per-gate fail-policy field (default fail-open); floor gate class declares fail-closed; the `permission_mode` verification harness (re-verify `permissionDecision` field names + deny-honored-under-every-mode against `code.claude.com/docs/en/hooks` at build time — flag 14). **Entry precondition:** if Claude Code cannot support per-gate fail-closed deny under some `permission_mode`, HALT (the hook is then not-the-floor and the guarantee must move to the deploy-tier provider layer — see §8).
- **Sub-cycle C — secure-build baseline** (`framework/secure-build-baseline/` NEW). ACs: `AC.SBB.1–.4`. Source: staged-diff secret guard (extend `secret_pattern_guard`); dependency-audit gate (shell `npm audit`/`pip-audit`); artifact `.gitignore` template + pre-commit sweep; `settings.fragment.json`.
- **Catalogue rows** (`framework/protection-matrix/`): folded into each sub-cycle's fence as a universal-path admission; `AC.COV.1` verified after C.

### Primitive check (REQUIRED — new mechanism)

| New mechanism | Native primitive chosen | Note |
|---|---|---|
| All hard gates (classifier, attestation, fail-closed, secrets, audit) | **PreToolUse hook** (`permissionDecision: deny`/`ask`, `updatedInput` for safe-sibling rewrite) | deterministic `command` hooks only — the floor must not be probabilistic; never an LLM-judge gate. |
| Per-environment policy | **inert YAML** read by the hook | policy/enforcement split; rename-safe because the gate reads structured fields. |
| Hook registration | **`settings.fragment.json` + workspace-sync auto-composer** | matches `frame-kernel/hooks/settings.fragment.json`; managed-settings path named as the true-non-disable upgrade (Decision E). |
| Dependency-vuln + secret detection | **shell-out to `npm audit` / `pip-audit` / gitleaks** | compose, don't re-implement (Lens 1). |
| Floor machine-verification | **`protection-matrix` catalogue + `loam guards`** | existing coverage primitive; no new orchestration. |

No new loop / scheduler / orchestrator is introduced (the scheduled drift-probe / restore-drill primitives are deploy-tier, out of scope).

---

## §7. Out of scope (deferred to the opt-in deploy tiers / above-floor)

- **All deploy-tier capabilities** — `/publish` `/promote` `/provision` `/rollback` `/status` skills; LOCAL/VERCEL/REAL-INFRA target integrations; OIDC provisioning; the loam-held state-backend credential; the loam-hosted protection/credential service.
- **The provider-side halves named in HALT-2** — live attestation probes (F-0), OIDC/IAM cred-minting isolation (F-2), the irreversible proof-of-intent challenge firing on a real destructive verb (F-3/G4), backup-freshness live reads (F-8/G6), credential-gated go-live (F-9/G8).
- **Above-floor rigor mechanisms** — mandatory cooling-off window (G5/AC.COOL.1), anti-desensitization salience budget (G12), structural spend caps (G10), expand/contract migration linting (G13/AC.DB.1), promotion hash-identity (G14/AC.PROMOTE.1), PostToolUse audit log (AC.AUDIT.1) — all sit ON the floor, not in it.
- **The dev→build→deploy unification spine** + any dev-sdlc re-architecture (`03` §6 — owner-gated, higher blast radius).
- **Build-hygiene flags** the design parks (LOCAL digest stub #13, Atlas migrate-lint tier #15, state-backend bootstrap #16) — deploy-tier.

---

## §8. Halt triggers (in-flight — abort the build + surface)

- **Per-gate fail-closed unsupported** (Sub-cycle B precondition): if `deny` is not honored under some `permission_mode`, or Claude Code cannot support a per-gate fail-policy, HALT — the hook is not-the-floor for that case and the guarantee can only live in the deploy-tier provider layer (which makes the attestation gate doubly load-bearing). Surface to owner; do NOT ship a fail-open destructive gate.
- **`permissionDecision` field names / blocking-event table drifted** from the snapshot (flag 14): re-verify against `code.claude.com/docs/en/hooks` at build time; if changed, HALT + adjust before relying on the field.
- **Extending `secret_pattern_guard` would regress its sealed fail-open behavior** for the inbound-paste path: HALT — the new staged-diff path must be additive, the existing path's `D-SECHK.FAIL-OPEN` behavior unchanged.
- **A floor guarantee cannot be enforced framework-side** that this plan assumed it could (beyond the HALT-2 set): HALT + surface rather than silently widen into the deploy tier.
- **Fence touches a sealed component without a manifest entry** for it: HALT (never silently widen the fence).
- **More than ~5 in-build decisions need owner escalation:** HALT + describe.
- **Any AC ships partial:** HALT + reframe (the AC text, not the implementation, per `feedback_loose_AC_text_fix_AC_not_implementation`).

---

## §9. Bookkeeping

- **Manifest(s) authored at build-dispatch time, one per sub-cycle** — NOT pre-authored here. Rationale: the manifest's `amendment.number` (global counter) and `baseline:` SHA derive at build time (and from the not-yet-settled sub-cycle sequencing), and pre-allocating them now would go stale and pre-commit a sequencing the owner has not ratified (per `feedback_version_numbers_at_release_time` spirit + HALT-1). Each manifest follows the canonical shape (`schema_version: 1`, `amendment` block, `baseline:`, `components:`, `universal_paths:` admitting `docs/plans/`, `narrative.target: docs/plans/sealed/<slug>.md`).
- `loam amend apply` then `loam amend seal` per sub-cycle (NEVER `git commit --amend`; new corrective commits if a file is missed — `feedback_no_amend_in_agent_dispatches`). Name `loam amend apply` explicitly as the bookkeeping mechanism in each dispatch (`feedback_dispatch_explicit_loam_amend_apply`).
- Backfill: `docs/STATE.md` floor row; `docs/FUTURE_IDEAS_DRAFT.md` F-SECURE-BUILD-BASELINE entry → mark graduated-to-build; `docs/design/loam-plugin-product-architecture.md` Floors tier → add the deploy-safety floor as an instance.
- Do NOT push tags / publish until the owner gates the release. HARD smoke per minor before publish (`feedback_hard_smoke_per_minor_before_publish`).

---

## §10. Ruthless Feedback (F2 — honest doubts + named disagreements)

1. **The biggest one (carried as HALT-2): the design over-labels "floor".** *Disagreement:* `01-loam-feature-design.md` §3 lists F-0/F-2/F-3/F-8/F-9 as the protection FLOOR, but each depends on a provider-native control the red-team itself says is the only honest guarantee — and that lives in the deploy tiers, OUT of this floor. *Evidence:* `02-redteam` meta-finding ("the entire honest guarantee rests on Wall 3… nothing verifies Wall 3 is armed"); `framework/safety-layer/` has no provider adapter today; `01` §13 R-3/R-4 concede the loam-hosted service "does not yet exist". *Alternative:* split each floor item into framework-side scaffold (ships now) + provider-side guarantee (deploy-tier entry condition), and make the floor's promise the one thing it CAN keep framework-side: *an unattested production environment refuses all destructive verbs by default.* Built into §3 HALT-2 + AC.DSF.6.
2. **Fail-closed is an inversion of a sealed decision, verified in code.** *Disagreement:* the design treats fail-closed as a clean precondition; in fact `dangerous_flag_guard.py:319` and `secret_pattern_guard.py:297` explicitly `return 0` "fail-OPEN per D-SECHK.FAIL-OPEN". *Evidence:* read both files this session (Tier-0). *Alternative:* per-gate fail-policy field, default fail-open, floor gates opt fail-closed (Decision C) — gets G15 without regressing the (correct) advisory-guard convention. A blanket fail-closed flip would break every advisory guard on its first bug.
3. **"Non-disable-able" is the wrong word for a settings.json hook.** *Disagreement:* `03` leans on framework-native = non-disable-able, but a settings.json hook is one file-edit from off. *Evidence:* `03` §"Evidence" itself says the difference is "disable friction", not impossibility. *Alternative:* say "non-trivially-disable-able", name managed-settings as the true-non-disable upgrade (Decision E). Overclaiming here is itself a Lens-0 protection failure (the owner believes a floor that a stray edit removes).
4. **Resolved-target detection is reduce-not-eliminate, and the plan must not pretend otherwise.** *Evidence:* `01` R-2 — OIDC cannot un-leak a string a human typed; entropy + known-host heuristics miss novel forms. *Alternative:* ship the closeable part (declared-identity comparison + write-time block, AC.DSF.4) and name the residual to the owner; do not let AC.DSF.2 imply total coverage.
5. **Doubt I cannot resolve at plan-time:** whether Claude Code honors `deny` under a bypass/accept-all `permission_mode`. If it does not, the keystone (AC.DSF.5) is unreachable framework-side and the floor's destructive guarantee collapses to the deploy-tier provider layer. This is why Sub-cycle B carries it as a hard entry precondition with a HALT, not an assumption.

---

## §11. Provenance trail

- Floor item set F-0…F-9 + fail-policy + hardening log + residuals: `…/devops-pipeline-2026-06-27/01-loam-feature-design.md` §3 (table), §8 (conflicts E/C/D/K), §10 (AC.FLOOR.*), §11 (items 4/5 + HARD PRECONDITION block), §12 (G15/G1 rows), §13 (R-1…R-4).
- The 6 CRITICAL gaps (G1 attestation, G2 resolved-target, G3 wrappers, G6 backup, G8 go-live, G15 fail-policy): `…/02-redteam-gate-gaps.md` (per-G sections + meta-finding + "single biggest residual").
- Floor=framework-native, deploy-tiers=capabilities, dev-sdlc=substrate: `…/03-architecture-decision-plugins-vs-native.md` §"recommendation" 1–5, §6 (proceeds-now vs waits-for-Luke).
- Secure-build baseline (secrets / dependency-audit / artifact-cleanliness): `docs/FUTURE_IDEAS_DRAFT.md` lines 481–483 (F-SECURE-BUILD-BASELINE, Discord tilth-dev 1520438623898439680, 2026-06-27).
- Existing fail-OPEN convention (Tier-0, read this session): `framework/safety-layer/hooks/dangerous_flag_guard.py:319`, `…/secret_pattern_guard.py:297` (`D-SECHK.FAIL-OPEN`).
- Floor substrate to compose on: `framework/safety-layer/src/loam/safety_layer/{action_class.py:38 FrameworkFloorCategory, dangerous_op.py:65 DangerousOpGate.classify}`; `framework/protection-matrix/` (`failure-mode-guard-matrix.yaml` + `loam guards`); hook-wiring shape `framework/frame-kernel/hooks/settings.fragment.json`.
- Trust-tier model: `docs/design/loam-plugin-product-architecture.md` (Floors / Good-by-default / Capabilities).
- Prime objective ladder: `docs/VALUE_PROPOSITION.md` AC.PO.1 / AC.PO.2.
- Plan-doc + manifest shape: `plugins/dev-sdlc/docs/conventions/plan-docs.md`; exemplar `docs/plans/v0-1-6-production-safety-and-base-skills.md`.

---

## §12. Build SHA register (Sub-cycle A — sealed local 2026-06-27)

Built by `loam-builder` on canonical `main`, local seal only (owner gates
the release; no push, no publish). Pre-build sync check: canonical HEAD was
`1fcad58`, equal to `origin/main` (not behind).

| Commit | SHA | Note |
|---|---|---|
| BASELINE (plan-doc, commit P) | `f27bbd667be8a06aeed77e3b6bce6a384cc1075f` | plan-before-code commit; the HEAD~1 the NEW component's fence pins to |
| Source (feat, commit S) | `c0eae5ae5b8c14677da49908077a6c4121d8dbf0` | `framework/deploy-safety-floor/` + protection-matrix row + regenerated companion + manifest |
| Apply | `51761a81ddc972efb49cd3930f5be53a4d177648` | sidecar advance to baseline (empty-diff window) |
| Seal | `cf1ed11ea2210e4b618f1303e6ce0b8998effbf2` | deterministic seal; guard-sweep floor + touched suite green; post-seal `apply --dry-run` clean |

**ACs satisfied (Sub-cycle A):** AC.DSF.1, AC.DSF.2, AC.DSF.3, AC.DSF.4,
AC.DSF.6, AC.DSF.7 (outcome-altitude), AC.COV.1. **Tests:**
`framework/deploy-safety-floor/tests/` 24 passed;
`framework/protection-matrix/tests/` 42 passed (the new
`FM.DESTRUCTIVE-PROD-UNGATED` row catalogued + companion regenerated; `loam
guards` reports it `[ok]`, no divergence, no new floor gap).

**Field-contract re-verify (flag 14, information-trust):** the Claude Code
PreToolUse `permissionDecision` field contract was re-verified live against
`code.claude.com/docs/en/hooks` at build time — `hookSpecificOutput.{
hookEventName, permissionDecision ∈ {allow,deny,ask,defer},
permissionDecisionReason}`; input envelope `{tool_name, tool_input, cwd,
permission_mode ∈ {default,plan,acceptEdits,auto,dontAsk,bypassPermissions}}`.
No drift from the sealed `dangerous_flag_guard` shape; the HALT-on-drift
condition did not fire.

**Out of this cycle (per dispatch):** Sub-cycle B (the generalized per-gate
fail-policy primitive in `safety-layer`, AC.DSF.5) and Sub-cycle C
(secure-build baseline, AC.SBB.*). Pending dispatcher-side backfill:
`docs/STATE.md` change-log row, `docs/release-roadmap.md` / roadmap §8, the
parent architecture-decision doc's method-decision register, and the
`docs/design/loam-plugin-product-architecture.md` Floors-tier instance entry.

---

## §13. Build SHA register (Sub-cycle B — sealed local 2026-06-27)

Built by `loam-builder` on canonical `main`, local seal only (owner gates
the release; no push, no publish). Pre-build sync check: canonical HEAD was
`1edf16ee`, **5 commits ahead** of `origin/main` (`1fcad58`) from Sub-cycle
A's local seals + §12 backfill (not yet pushed); built on local HEAD per
`feedback_build_forward_on_publish_pending`.

**Keystone (mandatory first gate — plan §6 Sub-cycle B entry precondition,
§8 halt) — EMPIRICALLY VERIFIED, artifact-probed (not self-reported):** a
PreToolUse `permissionDecision: deny` IS honored as a tool-call block under
Claude Code bypass-all modes — confirmed under BOTH `--permission-mode
bypassPermissions` and `--dangerously-skip-permissions`, in an isolated temp
project with an MCP-isolated `claude -p`; the sentinel `touch` did NOT execute
under either mode (marker-file absent). **Keystone POSITIVE** ⇒ the floor's
fail-CLOSED destructive guarantee is reachable framework-side; the build
proceeded. This closes the exact question Sub-cycle A's AC.DSF.7
`test_real_entrypoint_bypass_mode_still_returns_deny` deferred to Sub-cycle B.
Evidence file (workspace-local):
`workspace/.scratch/claude-output/deploy-safety-floor-subcycleB-keystone-2026-06-27.md`.

| Commit | SHA | Note |
|---|---|---|
| BASELINE (feat, commit S) | `14d5f90dda635cc437aa2bb6fbadff61fabe9156` | `hooks/_fail_policy.py` primitive + the 4 advisory guards declaring `FAIL_OPEN` + 3 AC.DSF.5 test files; the EXISTING-component extend pins BASELINE to the feat commit (source baked into baseline) |
| Apply | `29173794df3d9bc26b413c72d9de74c731fda1c7` | sidecar advance to baseline (empty-diff window) + manifest |
| Seal | `828de228ccdc20ace40a1cc2ab12f50d3b2e0713` | deterministic seal; touched suite + guard-sweep floor green |
| Corrective (admission) | `ffddd6e1` | admit safety-layer seal-bookkeeping (sidecar + narrative) via `extra_allowed_files` so post-seal `apply --dry-run` is clean (safety-layer's seal_test is the STRUCTURAL A15/A17/A18 test, no allowed_* diff bindings); post-seal dry-run exit 0 |

**AC satisfied (Sub-cycle B):** AC.DSF.5 (fail-CLOSED gate-policy primitive,
G15 keystone). **Tests:** `framework/safety-layer/tests/` 195 passed (the new
`test_AC_DSF_5_fail_policy_primitive` + `test_AC_DSF_5_advisory_guards_fail_open`
+ `test_AC_DSF_5_outcome_altitude`, plus the pre-existing fail-open regression
suites `test_AC_SECHK_4_fail_open` / `test_AC_WDGUARD_5_fail_open` still green —
zero regression).

**Scope boundary (plan Decision C, F2-surfaced):** this sub-cycle delivers the
generalized per-gate fail-policy primitive in `safety-layer` (default
`FAIL_OPEN`; floor gates opt into `FAIL_CLOSED`) and wires the four advisory
guards to DECLARE `FAIL_OPEN` through it (behavior-preserving). The
`deploy-safety-floor` gate (Sub-cycle A) already fails CLOSED ad-hoc and was
NOT touched — having it ADOPT the shared primitive (replacing its in-gate
`_floor_should_fail_closed`) is a **named, owner-gated follow-up**; no
functionality is lost by deferring it. The harness-level hook process-KILL
timeout is a Claude Code platform behavior, not catchable in-process — the
primitive covers the catchable in-process faults (raise / malformed input / a
gate's own internal-budget timeout routed through it).

**Out of this cycle:** Sub-cycle C (secure-build baseline, AC.SBB.*). Pending
dispatcher-side backfill: `docs/STATE.md` change-log row, roadmap §8, the
parent architecture-decision doc's method-decision register.

---

## §14. Build SHA register (Sub-cycle C — sealed local 2026-06-27)

Built by `loam-builder` on canonical `main`, local seal only (owner gates
the release; no push, no publish). Pre-build sync check: canonical HEAD was
`5d66451f`, **10 commits ahead** of `origin/main` (`1fcad58`) from Sub-cycles
A + B local seals + §12/§13 backfill (not yet pushed); built on local HEAD
per `feedback_build_forward_on_publish_pending`.

This is the FINAL sub-cycle of the floor: the framework-side secure-build
baseline (Tilth `F-SECURE-BUILD-BASELINE`) for the artifact loam PRODUCES.
Fence: NEW component `framework/secure-build-baseline/` + an **additive**
EXTEND of the sealed `framework/safety-layer/` `secret_pattern_guard`
(AC.SBB.1) + protection-matrix catalogue rows (universal-admitted, AC.COV.1).

| Commit | SHA | Note |
|---|---|---|
| BASELINE (plan tip, Sub-cycle B §13 register) | `5d66451fbefc5aca9ea1503c8a0a9169a6bd0efb` | the HEAD~1 the NEW component's fence pins to |
| Source (feat, commit S) | `bd11429c65a7af96baa0013e061b6214ccbcca21` | new component + additive safety-layer extend + new safety-layer test + 2 new + 1 enriched protection-matrix row + regenerated companion |
| Apply | `149e8e4251baa3c1b1f5ec98fbd47a71088d53da` | schema-v3 merged manifest+apply; sidecar advance (secure-build-baseline + safety-layer) to baseline; safety-layer BASELINE literal correctly skipped (structural test) |
| Seal | `3225eeee961926b3f90450f93b77e25cc7970648` | deterministic seal; touched suites (safety-layer 202 + secure-build-baseline 31) + guard-sweep floor green; post-seal `apply --dry-run` clean |

**ACs satisfied (Sub-cycle C):** AC.SBB.1, AC.SBB.2, AC.SBB.3, AC.SBB.4,
AC.COV.1; plus the outcome-altitude
`test_AC_SBB_C_outcome_altitude` (real PreToolUse hook entry-point over raw
stdin, no pre-arranged state). **Tests:**
`framework/secure-build-baseline/tests/` 31 passed;
`framework/safety-layer/tests/` 202 passed (the +7 `test_AC_SBB_1_*` staged-
diff tests, plus the pre-existing `test_AC_SECHK_4_fail_open` /
`test_AC_WDGUARD_5_fail_open` fail-open regression suites still green — the
extension is strictly additive, plan §8 HALT honored);
`framework/protection-matrix/tests/` 42 passed (the enriched FM.SECRET-LEAK +
new FM.VULN-DEPENDENCY-SHIPPED + FM.ARTIFACT-LEAKS-RUNTIME-STATE rows
catalogued + companion regenerated; `loam guards` reports all three `[ok]`,
DIVERGENCES none, gap count unchanged at 10 — no new floor gap).

**Field-contract re-verify (flag 14, information-trust):** the Claude Code
PreToolUse `permissionDecision` field contract was re-verified live against
`code.claude.com/docs/en/hooks` at build time —
`hookSpecificOutput.{ hookEventName, permissionDecision ∈
{allow,deny,ask,defer}, permissionDecisionReason }`. No drift from the
sealed `secret_pattern_guard` / `deploy_safety_floor_guard` shape; the
HALT-on-drift condition did not fire.

**Scope boundary (F2-surfaced):** AC.SBB.1's enforcement lives in
`safety-layer` (plan §2 placement) and was extended ADDITIVELY — a new
commit/push-boundary branch reusing the sealed CONTENT-pattern set; none of
the existing CONTENT/FILE logic or the `D-SECHK.FAIL-OPEN` fault policy
changed (a `git` read failure yields no match, so the inbound-paste path's
fail-open behavior is preserved). The `secret-commit` floor's NON-tunability
(AC.SBB.4) is declared in the secure-build-baseline `strictness` module (the
config surface) even though the enforcing guard is in safety-layer. The
dependency-audit composes on the ecosystem's OWN tool via an injectable
runner; when the tool is unavailable the gate SURFACES rather than faking a
clean result (Lens 0 honesty — no oversold guarantee).

**Pending dispatcher-side backfill:** `docs/STATE.md` change-log row, roadmap
§8, the parent architecture-decision doc's method-decision register, and the
`docs/FUTURE_IDEAS_DRAFT.md` F-SECURE-BUILD-BASELINE graduation mark (LEFT
unmarked this cycle — the file already carries a dispatcher-owned uncommitted
edit, so marking it in-cycle would commingle with that change; deferred to
the dispatcher to keep the dispatcher-owned file exactly as found).
