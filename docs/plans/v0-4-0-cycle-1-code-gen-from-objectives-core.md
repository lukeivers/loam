# v0.4.0 Cycle 1 — Code-gen-from-objectives core (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-4-0-cycle-1-code-gen-from-objectives-core`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 1.
**Predecessor cycles:** N/A (first cycle of v0.4.0). Inherits v0.3.0 SHIPPED state at seal `3c6fdd5`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

C1 supplies the dispatch surface that consumes objectives.yaml + gap-inventory.yaml + build-next.yaml and emits a unified diff (or branch) where each commit carries an `objectives:` block per amendment #38 `lifted_from = {source_doc, source_ac, source_commit}` schema. This is the "loam stops scaffolding and starts shipping code" inflection — pre-C1 loam ends at planning input; post-C1 loam ends at working code attributable to its motivating objectives.

C1 is the largest cycle in v0.4.0 (~120–240 min) because it's the surface introduction. C2 verifies outcome-altitude against the `jsts-playwright-app` canonical fixture; C1 ships SOFT-altitude only (synthetic-fixture smoke) so the cycle stays in the 1-3hr range.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to build software) → v0.4.0 release-roadmap §3 outcome (loam ships working code from extracted objectives) → AC.V040.1 (code-gen-from-objectives integration) → C1 ACs below (SOFT-altitude core; C2 closes outcome-altitude).

## §3 — Component fence

PRIMARY: NEW component likely at `plugins/dev-sdlc/code-gen/` OR extension of existing `plugins/dev-sdlc/odd-extractor/build-next/` surface. Decision finalizes at C1 plan-doc dispatch time; both paths comply with the dev-sdlc plugin partition.

Secondary: CLI surface in `plugins/dev-sdlc/cli.py` (or component-equivalent — `loam build-next` subcommand if named-successor extends existing CLI; new top-level subcommand if NEW component).

Read-only:
- `framework/memory-system/` — code-gen consumes memory state; doesn't write.
- Sealed `objective-tracker` — code-gen consumes the `lifted_from` schema; doesn't widen the schema (any widening is a separate amendment).
- `framework/primary-persona/` — read-only for context-load patterns.

Universal admissions: tests under the new component's `tests/` directory; per-cycle plan-doc + manifest.

## §4 — AC family seed `AC.CGC.*`

Load-bearing concerns to be tightened at dispatch time:

- `AC.CGC.1` — CLI flag + manifest entry exist (`loam build-next --code-gen` or named successor). `outcome-altitude: false`.
- `AC.CGC.2` — objectives.yaml ingestion + Pydantic validation (round-trip via existing `objective-tracker` schema). `outcome-altitude: false`.
- `AC.CGC.3` — gap-inventory.yaml + build-next.yaml ingestion (already-validated upstream surface). `outcome-altitude: false`.
- `AC.CGC.4` — LLM-routed dispatch through `claude -p` with `--strict-mcp-config` + empty MCP config tempfile (per v0.2.5 C5 invariant; AC.WSα.8 precedent). `outcome-altitude: false`.
- `AC.CGC.5` — Diff generation + per-commit `objectives:` block population per amendment #38 `lifted_from` schema. Single-commit case verified at C1; multi-commit case verified at C1 if scope permits, else carry to C2 or v0.4.1 patch. `outcome-altitude: false`.
- `AC.CGC.6` — SOFT-altitude smoke test against synthetic fixture (e.g., the existing `plugins/dev-sdlc/odd-extractor/tests/fixtures/build-next/high-priority-match/` shape). `outcome-altitude: true` BUT against synthetic fixture only — C2 closes the real-world outcome-altitude requirement.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Outcome-altitude verification against `jsts-playwright-app` canonical fixture (C2).
- Routines runtime layer (C3); Code Review composition (C3); Outcomes-pattern ADR (C3).
- ProgramBench v0 run (C4).
- Multi-fixture verification beyond synthetic + (deferred) jsts-playwright-app.
- Schema widening on `objective-tracker` (separate sealed-component amendment if needed).
- `loam status` background-work-inventory primitive (harness-landscape RR.1; out-of-scope per master plan §9).

## §10 — F2 RF gaps to surface at dispatch

- C1 fence decision — NEW `plugins/dev-sdlc/code-gen/` vs extension of `plugins/dev-sdlc/odd-extractor/build-next/` — needs verification against current build-next.py shape at dispatch time.
- `objectives:` block multi-commit case (does each commit inherit the same `lifted_from` from C1's first commit, or does each commit name its own `lifted_from`?). C1 plan-doc verifies single-commit; multi-commit may be in-cycle extension or v0.4.1 patch.
- Synthetic-fixture choice for AC.CGC.6 — surface for C1 plan-doc author at dispatch.

## §11 — Provenance trail

Master plan §3 Cycle 1; release-roadmap §3 v0.4.0 AC.V040.1; amendment #38 schema (`lifted_from`); v0.2.5 C5 propagation invariant (AC.WSα.8); `feedback_no_anthropic_api_key.md`.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Method-decision record finalized at C1 plan-doc dispatch time. Master-plan-altitude decisions (cycle split rationale, fence choice, AI-time band) live in master plan §14. Cycle-altitude decisions (specific prompt shape, multi-commit `objectives:` block carrier, synthetic fixture selection) tighten at dispatch.

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc commit | (pending) |
| Source-edit commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (pending) |
