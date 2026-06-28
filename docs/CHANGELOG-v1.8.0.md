# loam v1.8.0 — CHANGELOG

**Class:** MINOR over published v1.7.0 (`next_MINOR(v1.7.0) = v1.8.0`).
**Quality tag:** FLOOR — a non-tunable protection baseline that is on by
default for every build; the only tunable is per-gate strictness (block vs
surface), never the floor itself.
**Migration:** `no-op` (`docs/state-migrations/v1-8-0-deploy-safety-floor.migration.yaml`).
**Plan-doc:** `docs/plans/release-integration-v1-8-0-deploy-safety-floor.md`
(release integration); feature sub-plan `docs/plans/deploy-safety-floor-gate-primitives.md`.

> **Objective sentence —** loam ships a framework-native deploy-safety FLOOR: a
> destructive-action gate keyed off the *resolved target's* production-ness with
> an attestation / refuse-all-destructive default, a per-gate fail-policy
> primitive that makes the floor's destructive gates fail CLOSED while advisory
> guards keep failing open, and a secure-build baseline (secrets-never-committed
> at the commit boundary + a dependency-audit gate + artifact-cleanliness) for
> the artifact loam PRODUCES.

---

## Headline — the deploy-safety FLOOR (framework-native, default-on, non-tunable)

The v1.8.0 window is **one coherent feature area — the deploy-safety FLOOR** —
built and sealed in three sub-cycles. It is framework-native (not a plugin) per
the build's architecture decision: a protection floor must not be
trivially-disable-able. Two NEW components are introduced whole in this release
(`framework/deploy-safety-floor/` + `framework/secure-build-baseline/`), each at
its own **0.1.0**, OUT of the install graph and OUT of the lockstep set this cut
(mirrors how v1.7.0 shipped `deliberate-reasoning` at 0.1.0 — D-LOCK). The two
sealed-component extends (`safety-layer`, `protection-matrix`) ride the lockstep
bump.

### Sub-cycle A — gate primitives (`framework/deploy-safety-floor/`, NEW)

A destructive-action gate whose strength is `max(declared, resolved)`:

- **Resolved-target classification (AC.DSF.2):** a destructive command resolved
  against a target matching the config's declared-prod identity (host / bucket /
  account) is gated at the prod level **even when the active environment is
  declared non-prod**. The gate height derives from structured fields, never the
  environment label.
- **Inert config (AC.DSF.1):** a per-environment `deploy.yaml` parses into a
  typed model with fail-closed load; the file triggers no action — only a gate
  reading it does.
- **Rename-safety preserved (AC.DSF.3):** an environment renamed away from
  "production" while `is_production: true` retains the full prod gate
  (regression guard).
- **Write-time prod-string block (AC.DSF.4):** a prod-shaped connection string
  written into a non-prod / local config is blocked at write time, with the
  secret value never echoed into any reply, brief, or log.
- **Attestation + refuse-all-destructive default (AC.DSF.6):** an
  `is_production` / `tier: real-infra` environment with no attestation record
  (or a stale one) refuses every destructive verb and surfaces, in plain words,
  that it is not yet protected.
- **Outcome-altitude (AC.DSF.7):** the real PreToolUse hook entry-point, fed raw
  stdin with no pre-arranged state, returns a deny whose message names the target
  + destructive sub-action in non-technical vocabulary; the same entry-point,
  fed input that makes its classifier raise, still returns deny (fail-closed).

### Sub-cycle B — per-gate fail-policy primitive (`framework/safety-layer/`, extend)

- **Fail-CLOSED for the floor gate class (AC.DSF.5 — the G15 keystone):** a floor
  destructive gate whose hook raises / times out / receives malformed input
  **denies** the action; a non-floor advisory guard under the same fault still
  fails open (existing convention preserved). A `hooks/_fail_policy.py` primitive
  carries the `FAIL_OPEN` default; floor gates opt into `FAIL_CLOSED`. The four
  existing advisory guards now DECLARE `FAIL_OPEN` through it (behavior-preserving).
- **Empirically verified (artifact-probed, not self-reported):** a PreToolUse
  `permissionDecision: deny` IS honored as a tool-call block under BOTH
  `--permission-mode bypassPermissions` and `--dangerously-skip-permissions` —
  the floor's fail-CLOSED destructive guarantee is reachable framework-side.

### Sub-cycle C — secure-build baseline (`framework/secure-build-baseline/`, NEW)

The baseline for the artifact loam BUILDS, not only loam's own repo:

- **Secrets-never-committed at the boundary (AC.SBB.1):** a commit/push whose
  staged diff contains a credential pattern is blocked at the commit/push
  boundary, with no secret value echoed anywhere. Extends the sealed
  `secret_pattern_guard` with a new staged-diff branch reusing the sealed
  content-pattern set.
- **Dependency-hygiene audit gate (AC.SBB.2):** a build of a supported-ecosystem
  artifact (Node/Next + Python first) runs the ecosystem audit and, on a
  known-vuln at or above a configured severity floor, blocks-or-surfaces per the
  configured strictness; a clean audit passes silently.
- **Artifact-cleanliness (AC.SBB.3):** a generated project carries a correct
  `.gitignore` (harness runtime state + secrets + `.env`) AND a pre-commit sweep
  prevents those paths entering the artifact even under `git add -A`.
- **Non-tunable floor (AC.SBB.4):** the three guarantees are on for every build
  by default and cannot be disabled by ordinary project config; strictness
  (block vs surface) is the only tunable — the floor (a secret is never
  committed) is not among the tunables.

### Catalogue coverage (`framework/protection-matrix/`)

- **Every floor guard catalogued + default-on (AC.COV.1):** each new gate is
  present in `failure-mode-guard-matrix.yaml` as `default-on: true`, `floor:
  true`, with its verification method; `loam guards` reports the floor guards as
  covered and names no floor gap introduced by this cycle (new rows
  `FM.DESTRUCTIVE-PROD-UNGATED`, enriched `FM.SECRET-LEAK`,
  `FM.VULN-DEPENDENCY-SHIPPED`, `FM.ARTIFACT-LEAKS-RUNTIME-STATE`).

---

## Honesty flags (carried per the feature plan's F2)

- **"Floor" is framework-side scaffold + a default posture, not a total
  guarantee.** The honest promise loam keeps framework-side is the one it CAN
  keep: *an unattested production environment refuses all destructive verbs by
  default.* The provider-native guarantees (the only fully-honest destructive
  control) live in the deploy-tier provider layer, OUT of this floor — named as a
  follow-on, not claimed as shipped.
- **Resolved-target detection is reduce-not-eliminate.** It ships the closeable
  part (declared-identity comparison + write-time block, AC.DSF.4); the residual
  (OIDC cannot un-leak a string a human typed; heuristics miss novel forms) is
  named, not papered over by AC.DSF.2.
- **The fail-CLOSED keystone (AC.DSF.5) was a hard entry precondition, not an
  assumption** — Sub-cycle B carried it with a HALT, and the empirical probe
  confirmed `deny` is honored under bypass/accept-all modes before B proceeded.

---

## Versioning

- Lockstep bump: `docs/ACTIVE_MINOR` 1.7.0 → 1.8.0, the 31 in-scope
  `pyproject.toml` version fields 1.7.0 → 1.8.0, and the meta-package
  `loam --version` literal 1.7.0 → 1.8.0 — in one source-of-truth prep commit.
  The two sealed-component extends (`safety-layer`, `protection-matrix`) are
  in the in-scope set and ride the bump.
- Out of lockstep this cut: `deploy-safety-floor` (0.1.0, out-of-graph) +
  `secure-build-baseline` (0.1.0, out-of-graph) — the two NEW components, per
  the D-LOCK precedent for new components.
- Zero BREAKING changes — the floor is purely additive: new gates + a new
  fail-policy primitive (advisory guards behavior-preserving) + a new
  commit-boundary secret branch (the inbound-paste fail-open path unchanged). No
  public surface removed or changed incompatibly.

---

## Standing debt (named, not hidden)

Shipping the two new floor components OUT of the install graph + lockstep
repeats the v1.6.0 / v1.7.0 pattern (a third consecutive minor's worth of new
components at 0.1.0 out-of-graph). Folding them into the install graph +
lockstep is a named future item, not permanent drift. Separately, the
provider-side destructive guarantee (deploy-tier adapters) is the follow-on that
turns the floor's framework-side scaffold into a fully-honest end-to-end control.
