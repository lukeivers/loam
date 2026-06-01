# loam 1.0 Acceptance Smoke — harness build + first run (cycle plan)

**Status:** BUILT + FIRST-RUN COMPLETE. The design (objective, the three
role-play variants, the rubric = the prime-objective promise, the runner +
judge architecture, AC ladder SMOKE.1-5, forks F1-F5 ruled) is the authoritative
upstream: `docs/plans/loam-1.0-acceptance-smoke.md`. This doc is the cycle
plan for the harness component itself + its first run.

## 1. Objective

Ship the loam 1.0 acceptance smoke as a reusable, re-runnable sealed component
AND produce the first 1.0-readiness report against a genuinely fresh loam.

## 2. Fence (single new component)

One NET-NEW component: `framework/tools/loam-acceptance-smoke/`. It composes on
`loam-workspace-bootstrap` (drives `run_first_run_intake` + the real deep-role-
research provider) and on `loam-spawn-isolation` (the mandated isolation surface
for every `claude -p`) — both via lazy import, neither edited. No edits to any
other sealed component.

## 3. What it is

- `scripts/variant_{a,b,c}.md` — the three role-play persona briefs (human-
  readable mirror of `src/.../variants.py`).
- `src/loam_acceptance_smoke/`:
  - `variants.py` — the three machine-consumable VariantSpecs.
  - `spawn.py` — the COUNTED isolation wrapper; every `claude -p` routes
    through `loam_spawn_isolation.spawn_isolated_claude` and is recorded for the
    protection audit.
  - `runner.py` — instantiates a throwaway fresh loam via real `loam init`,
    drives the real `run_first_run_intake` with a `claude -p`-backed role-play
    answerer against an isolated global home, wires the real RoleResearchProvider
    for the idea-vacuum variant.
  - `judge.py` — deterministic scorers (seed-written / deep-research gating /
    cross-variant diff) + one isolated `claude -p` LLM-as-judge probe per soft
    dimension.
  - `report.py` / `cli.py` — render the 1.0-readiness report; `loam-acceptance-
    smoke` console-script.

## 4. AC ladder (from design §5 — outcome-shape, method the builder's call)

- **AC.SMOKE.1** (outcome-altitude) — runs the harness with zero pre-arranged
  state, driving the production `loam init` + first-run intake (not inner
  modules), producing a scored report per variant.
- **AC.SMOKE.2** — the three variants produce materially-different seeds (a
  deterministic cross-variant diff).
- **AC.SMOKE.3** — variant C and only variant C triggers deep-role-research,
  within the sealed ≤3 round-trip budget; A and B reach zero research.
- **AC.SMOKE.4** — every rubric dimension scored per variant with cited
  evidence; any FAIL names the specific promised outcome that didn't land.
- **AC.SMOKE.5** — re-runnable + self-cleaning (throwaway temp workspace; no
  residue in the real `~/.claude`).
- **AC.SMOKE.S** — sealed-component fence invariant (the introduction diff
  touches only the component + universal admissions).

## 5. Halt-and-surface (honest verdict)

Report what is ACTUALLY observed; a FAIL/PARTIAL with transcript evidence over a
manufactured green. The verdict feeds the owner's real 1.0 decision.

## 6. First-run outcome (recorded)

First run verdict: **NOT-READY** — the smoke caught four real production bugs in
the intake's natural-language handling (proposal echo pastes the whole raw
reply; affirmation parser fails on trailing punctuation, which suppressed the
deep-research opt-in for variant C; brittle idea-vacuum classifier; unresolved
role-noun slot in the leverage close). Full evidence + root-cause + fix shape:
`docs/experiments/loam-1.0-acceptance-smoke-run.md`. Infrastructure (real init,
isolation, seeding, self-clean) is sound; the gaps are in the production
prime-objective conversation. 28 `claude -p` spawns, all spawn-isolated; live
`~/.claude` never written.
