---
flow: loam-vnext-build
title: loam v-next build
entry: examine
steps:
  - id: examine
    name: 1 EXAMINE
    transitions: [define]
  - id: define
    name: 2 DEFINE
    transitions: [build]
  - id: build
    name: 3 BUILD
    transitions: [prove, gate_destructive]
  - id: gate_destructive
    name: G★ destructive-step / slice gate
    gate: true
    transitions: [build]
  - id: prove
    name: 4 PROVE
    transitions: [build, integrate_record]
  - id: integrate_record
    name: 5 INTEGRATE+RECORD
    transitions: [loop]
  - id: loop
    name: 6 LOOP
    transitions: [examine]
gates:
  - id: G1
    name: Doctrine wording
  - id: G2
    name: Build-location decision
  - id: G3
    name: Live-activation flip
  - id: G4
    name: Migration release-gate
  - id: G5
    name: Openness-default revision
  - id: G6
    name: Carry-forward manifest
  - id: G7
    name: Retire old pos3
  - id: "G★"
    name: Any destructive / pruning step
---
# loam v-next build — the flow

This is the build-workflow (`docs/plans/loam-vnext-build-workflow.md`) expressed
in the flow-definition format (AC.FLOWDEF.2 / AC.DOGFOOD.1). It is the FIRST real
flow the defined-workflow system holds, and the dogfood the persisted position
cursor is driven against. The companion `docs/plans/loam-vnext-build-workflow.md`
carries the full prose; this artefact carries the machine-walkable graph that the
position cursor walks, plus the human-followable summary below.

## The per-slice loop (the six work steps)

Every slice of the v-next build walks the same six steps. You are always at exactly
one numbered step of exactly one slice — that pair is your position (the cursor).

1. **EXAMINE** — establish ground truth empirically, from git refs + live
   operational reality, NOT from stale docs. Built ≠ live. Outputs a
   build-disposition (build-new / wire-live / extend / leave). EXAMINE is also how
   you re-find your place when the cursor is unclear.
2. **DEFINE** — state what "done" looks like behind the framework ↔
   user-meaningful-state boundary; produce outcome-altitude acceptance criteria
   (each verifiable at the production entry-point with no pre-arranged state).
3. **BUILD** — build the slice clean, composing on Claude primitives + existing
   sealed assets. Plan-before-code: write the slice's plan-doc BEFORE any code. If
   this step crosses a gate, stop at the gate first.
4. **PROVE** — run the slice's outcome-altitude ACs as a real empirical cold-walk.
   "It's wired" is not proof; a passing cold-walk is. On failure, return to BUILD
   (or to DEFINE if the target was wrong).
5. **INTEGRATE+RECORD** — wire the proven slice in behind the boundary; author the
   version's user-state migration file; commit (new corrective commits, never
   `--amend`); UPDATE THE CURSOR to mark the slice and name the next.
6. **LOOP** — advance to the next slice in the plan's dependency order; return to
   EXAMINE for that slice — never carry an assumption forward.

## The gates (owner-decision points — STOP and surface)

At every gate: surface the decision + a recommendation, get the answer, record the
ratification durably into the artefact BEFORE dispatching the dependent work, then
proceed. A gate is never passed by assumption.

- **G1 — Doctrine wording.** Ratify the doctrine enshrinement wording. Rides
  alongside, non-blocking.
- **G2 — Build-location decision.** Ratify repo shape + the physical home of
  user-state. Blocks all of Phase 1.
- **G3 — Live-activation flip.** Ratify the `~/.claude/settings.json` activation
  flip that makes the keep-pace hooks run live. Owner-class (runtime behaviour).
- **G4 — Migration release-gate.** Ratify the release-gate that blocks publishing
  any version without a declared migration file.
- **G5 — Openness-default revision.** Ratify reversing the abstraction-first
  `minimal` default to `open` before the user-model MVP seeds it.
- **G6 — Carry-forward manifest.** Ratify which user-state migrates into the fresh
  instance vs what is left behind (destructive-by-omission → surface-before-cut).
- **G7 — Retire old pos3.** Ratify the final prune of the old instance once the new
  one is proven. The last destructive step.
- **G★ — Any destructive / pruning step.** A standing gate: any step that removes,
  compresses, or overwrites user-state must be reversible (git), surfaced before it
  happens, and dependency-checked. Promoted on the spot when a work step turns out
  destructive (modeled as the `gate_destructive` node off BUILD).

## Pause-if-lost (the standing rule)

At any moment you must be able to say: "I am at step N of slice X, disposition D,
gate G pending/clear." If you cannot fill that sentence in, you are lost → PAUSE all
other work and re-establish position (re-run EXAMINE against git refs + live state)
before doing anything else. This is the single most load-bearing behaviour in the
flow, and it is what the persisted cursor + re-injection hook make structural.
