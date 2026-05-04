# Dev-mode safety defaults

**Status:** convention. **Authored:** 2026-05-04 (v0.1.6 Cycle 1).
**Composes with:** `framework/workspace-bootstrap/` `safety_profile`
field; `framework/cost-governance/` production-stake floor.

## Summary

The `safety_profile` field on `bootstrap.yaml` (added at v0.1.6 per
AC.PSAFE.1) takes one of three values: `production-stake | dev | research`.
The `dev` profile is the default and is the right choice for any
workspace that is loam itself (canonical pos-v2), a derived
workspace primarily used to develop on loam, or any consumer-side
codebase where the operator is the primary persona's chief engineer
(not a SOC-2-bound production stakeholder).

## What `dev` profile does NOT do

- Does **not** activate the production-stake non-tunable floor
  (no audit-trail-on; no `cost_governance.warning_fraction` floor at
  0.6; no `always_ask` floor extension with
  `production-data-mutation` + `customer-record-edit`).
- Does **not** require a SOC-2 compliance posture — operator is
  assumed to be the dev workspace's user, not Eric-shape.

## What dev-mode safety defaults DO retain

- The framework-floor `always_ask` set (per
  `framework/workspace-bootstrap/`-scaffolded
  `~/.loam/safety/always_ask.yaml`) — `external_payments`,
  `irreversible_user_data_deletion`, `publishing_to_public_surface`,
  `sending_as_owner_to_third_party` — applies regardless of
  `safety_profile` value.
- Cost-governance is opt-in (matches today's behavior — no money/
  token/time ceilings unless the workspace writes `~/.loam/cost/ceilings.yaml`).
- The reversibility-primitive's hard-block on irreversible operations
  remains structural — not a profile-tunable surface.

## When to escalate to `production-stake`

Set `safety_profile: production-stake` in `bootstrap.yaml` whenever:

- The workspace is bound to an external compliance regime (SOC-2,
  HIPAA, PCI-DSS) that demands audit-trail floors.
- The workspace's operations touch customer records / production
  data / external systems where loam's actions ladder up to a
  named compliance owner.
- Eric-shape: any client SaaS engagement where loam is invoked
  inside the client's compliance posture.

## When `research` profile applies

The `research` profile is reserved for sandbox / exploratory
workspaces where the operator deliberately wants neither dev's
default `always_ask` set nor production-stake's floors. v0.1.6
ships the field as a no-op (matches `dev` semantically); future
releases may add research-specific tuning. Surface a FIDRAFT entry
when proposing research-profile additions.
