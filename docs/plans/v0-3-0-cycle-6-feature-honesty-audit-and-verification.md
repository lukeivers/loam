# v0.3.0 Cycle 6 — Feature-honesty audit + memory FBE.7 verification + claude -p discipline + ODD-conformance sweep (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-6-feature-honesty-audit-and-verification`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 6.
**Predecessor cycles:** Cycles 1–5 (sealed).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Verify documented surface against operational reality. Stranger-perspective. Last cycle to validate everything else landed correctly. Bundles four verification ACs (V030.1 / V030.3 / V030.4 / V030.5) because each is a verification pass against already-shipped surface and they share the audit-altitude theme. Stranger cloning loam at v0.3.0 can run every named capability + verify it operates per docs; this cycle is the meta-evidence v0.3.0 ships.

## §3 — Component fence

PRIMARY: `docs/v0-3-0-feature-honesty-audit.md` (NEW).

Read-only across:
- `README.md`, `docs/getting-started.md`, `docs/dev-mode-getting-started.md` — every named capability.
- Sealed-component surface — `framework/` components + `plugins/` source.
- `claude -p` invocations in `framework/` + `plugins/` source.
- Workspace state on stranger-clone (FBE.7 cross-session verification).

Tertiary: per-component `objectives.yaml` or named exemption; tracked-allowlist for ODD-orphans.

## §4 — AC family seed — `AC.FHA.*`

Load-bearing concerns to be tightened at dispatch time:

- Stranger-clone audit deliverable at `docs/v0-3-0-feature-honesty-audit.md`.
- 100% match between named capabilities (in README + getting-started docs) and sealed-component surface (or named exemption).
- FBE.7 stranger-clone verification — cold install on fresh machine (or sandboxed equivalent); run a session; `/clear`; run another session; verify memory surface returns content from prior session. Outcome-altitude.
- `claude -p --strict-mcp-config` invariant test — repo-wide grep proves every `claude -p` subprocess in loam source carries the flag.
- ODD-conformance sweep — every `framework/` component declares `objectives.yaml` or named exemption; orphans triage to close OR tracked-allowlist with rationale.
- An outcome-altitude AC — full audit deliverable cross-references resolve + FBE.7 stranger-clone passes end-to-end.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- New feature additions surfaced during audit (those go to FIDRAFT or future minor).
- New ODD-conformance enforcement mechanisms (those are v0.7.0 structural enforcement).
- Audit of plugin-specific capabilities beyond dev-sdlc (other plugins land in v0.10.0+).

## §10 — F2 RF gaps to surface at dispatch

- Stranger-clone verification mechanism — Docker-equivalent fresh environment vs actual fresh machine. If can't execute at AI-time (requires owner-driven fresh machine), the AC moves to release-roadmap §6 owner-action-line; surface for owner ruling.
- 100% match standard — strict; if the audit surfaces any docs-claims-vs-reality gap, halt for owner ruling on whether the gap is a real feature gap (close as PATCH within v0.3.0) or a docs-claim gap (rewrite docs).
- ODD-conformance sweep — orphans triage may surface real gaps that warrant tracked-allowlist with rationale rather than close-in-cycle. Surface for owner triage.

## §11 — Provenance trail

Master plan §3 C6; release-roadmap §3 v0.3.0 AC.V030.{1,3,4,5}; `feedback_test_outcome_altitude_required.md`.

## §14 — Method-decision record (backfilled at dispatch + seal)

To be filled at cycle-dispatch authoring + post-seal backfill.
