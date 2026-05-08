# v0.4.0 Cycle 2 — Code-gen outcome-altitude verification on `jsts-playwright-app` (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-4-0-cycle-2-code-gen-outcome-altitude-verification`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 2.
**Predecessor cycles:** Cycle 1 (sealed). Inherits the code-gen surface that C1 ships.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

C1 ships SOFT-altitude code-gen against synthetic fixtures; that's necessary but insufficient for the END-USER class quality gate. v0.4.0's release-roadmap §3 AC.V040.6 requires outcome-altitude verification — the test invokes the production entry-point, exercises real `claude -p` subprocess, uses no monkeypatched stubs, asserts on the produced diff's per-commit `objectives:` block.

C2 closes that requirement against the `jsts-playwright-app` canonical fixture (the same fixture v0.1.8 → v0.2.3 used to verify the JS/TS adapter + multi-source synthesis). Per `feedback_test_outcome_altitude_required.md`, three v0.2.x failures shipped because cycle ACs went green at synthetic-altitude while the real-world HARD smoke was broken; C2 prevents that failure mode for v0.4.0 by closing the outcome-altitude AC at the cycle level, not deferring to release-gate.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.4.0 §3 outcome → AC.V040.1 + AC.V040.6 (outcome-altitude) → C2 ACs below (close AC.V040.1 + verify AC.V040.6).

## §3 — Component fence

PRIMARY: outcome-altitude test at `plugins/dev-sdlc/code-gen/tests/test_AC_V040_6_outcome_altitude.py` (or component-equivalent path post-C1; the test path follows C1's fence decision — NEW component vs build-next extension).

Secondary:
- `jsts-playwright-app` fixture access (read-only) — verify fixture state at C2 dispatch; if shape changed since v0.1.8 sealing, fixture-update is in-cycle (NEW commit, not `--amend`).
- C1's code-gen surface — UNIVERSAL ADMISSION for prompt-shape adjustments needed to make outcome-altitude pass; NEW commits only (no `--amend`).

Read-only: `framework/`, sealed `objective-tracker`, sealed v0.1.8 / v0.2.3 / v0.2.5 surface.

## §4 — AC family seed `AC.CGV.*`

Load-bearing concerns to be tightened at dispatch time:

- `AC.CGV.1` — Outcome-altitude test invokes `loam build-next` (or named successor) production CLI with real `jsts-playwright-app` fixture inputs. NO monkeypatched `claude -p` subprocess. NO pre-arranged objectives.yaml that the production code would normally produce via reverse-ODD (per pre-arrangement detection rubric in `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md`). `outcome-altitude: true`.
- `AC.CGV.2` — Produces non-empty diff or branch with ≥1 commit. `outcome-altitude: true`.
- `AC.CGV.3` — Per-commit `objectives:` block populates with valid `lifted_from = {source_doc, source_ac, source_commit}` data. Each `source_doc` resolves to a real path in the fixture; each `source_ac` resolves to a real AC ID extracted via the v0.2.3 multi-source synthesis pipeline; each `source_commit` is a valid git SHA at the time of the test run. `outcome-altitude: true`.
- `AC.CGV.4` — Behavioral assertion: produced diff compiles + lints + passes the existing fixture's test surface (`npm test` or fixture-equivalent). `outcome-altitude: true`.
- `AC.CGV.5` — AC.V040.1 marked closed in master plan §11 SHA register; AC.V040.6 marked `outcome-altitude: true` per ODD grounding lean §"Outcome-altitude AC requirement". Doc-only.
- `AC.CGV.6` — Pre-arrangement rubric documented in C2 plan-doc §3 explicitly: the test cannot pre-arrange state the production code would produce; the objectives.yaml comes from a real prior reverse-ODD run on the fixture, not a hand-authored mock.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Multi-fixture outcome-altitude verification (e.g., rd-automation-class real-world targets stay v0.5.0+).
- ProgramBench v0 run (C4).
- Behavioral test pass-rate scoring across many tasks (that's C4 ProgramBench territory).
- Any C1 surface widening beyond what makes outcome-altitude pass (defer to C1 in-cycle correctives if scope creeps).

## §10 — F2 RF gaps to surface at dispatch

- jsts-playwright-app fixture state at C2 dispatch — verify fixture surface pre-dispatch; if shape changed since v0.1.8, fixture-update is in-cycle.
- AC.CGV.4 behavioral assertion's exact shape — does "produced diff passes fixture's test surface" mean `npm test` exit 0, or per-test pass-rate threshold? Surface for ruling at dispatch.
- Pre-arrangement rubric — the objectives.yaml MUST come from a real prior reverse-ODD run; whether that run is part of C2's setup or pre-arranged from a saved fixture state needs ruling. Pre-arranged-fixture is acceptable IF the fixture state itself was produced by a real reverse-ODD run + audit-trail-recorded.

## §11 — Provenance trail

Master plan §3 Cycle 2; release-roadmap §3 v0.4.0 AC.V040.1 + AC.V040.6; `docs/odd-llm-grounding.lean.md` §"Outcome-altitude AC requirement"; `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md` (pre-arrangement detection rubric); `feedback_test_outcome_altitude_required.md` (rationale); v0.1.8 / v0.2.3 jsts-playwright-app fixture sealing history.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Method-decision record finalized at C2 plan-doc dispatch time.

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc commit | (pending) |
| Source-edit commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (pending) |
