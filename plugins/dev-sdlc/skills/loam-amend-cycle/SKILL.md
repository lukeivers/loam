---
description: Walk a sealed-component amendment cycle end-to-end — author the plan-doc, author the manifest (schema v3), commit the source-edit feat as BASELINE, run `loam amend apply --plan-doc` to merge manifest + sidecar bumps in one semantic commit, run `loam amend seal --plan-doc` to land the deterministic short-form seal commit + run scoped sweep tests, then backfill the §14 method-decision register with the apply + seal SHAs in a separate post-seal commit. Use when the persona is about to start a sealed-component amendment cycle in a loam dev-mode workspace. Composes on loam-amend (`plugins/dev-sdlc/tools/loam-amend/`) which must be installed in the workspace's venv.
---

# loam-amend-cycle

The sealed-component amendment cycle is loam's load-bearing
authoring discipline for changes to `framework/<component>/` or
plugin source. Every Cycle 1–4b in v0.1.8 walked this exact ritual.
This skill captures the full ladder so a session-fresh persona
(or a stranger running `claude` with the dev-sdlc plugin enabled)
can run a cycle without re-deriving the steps.

## What this skill captures

The amendment-cycle ladder in canonical order:

1. **Plan-doc authoring** at `docs/rebuild/plans/<slug>.md`. Sections:
   Outcome shape (the "why") + Lens checks + Single-component fence +
   AC family (every AC explicit) + Halt-and-surface BEFORE build +
   Smoke (six dimensions) + Out of scope + Halt triggers (in-flight) +
   Bookkeeping + F2 RF + Provenance + Acceptance gate +
   `## 14. Method-decision record` (per AC.D-sa.7 lint).
2. **Manifest authoring** at `docs/rebuild/plans/<slug>.manifest.yaml`
   — schema v3. Required top-level fields: `schema_version: 3` +
   `amendment.slug` + `amendment.title` + `baseline` (7–40 char
   lowercase-hex SHA) + `plan` + `plan_doc_ref` + `ac_count` +
   `smoke_outcome` + `components` (list of `{name, seal_test, sidecar,
   frozen_baseline, extra_allowed_prefixes}`) + `universal_paths` +
   `narrative.target`. The `baseline` SHA is the source-edit feat
   commit; fill it in after step 4 below.
3. **Plan-doc + manifest commit.** A single `docs(plans):` commit
   carrying both files. Plan-doc commits BEFORE source code per
   `feedback_plan_before_code`.
4. **Source-edit feat commit (BASELINE).** The actual code +
   tests changes for the amendment. Commit message shape:
   `feat(<component>): <one-line summary>`. The resulting commit
   SHA is the `baseline:` field's value.
5. **`loam amend apply --plan-doc <abs-path-to-plan-doc>
   <abs-path-to-manifest>`.** Single semantic commit per AC.DPS1.6
   (v3 schema): manifest + sidecar `SEAL_COMMIT` advancement +
   any extra_allowed_prefix mutations land together.
6. **`loam amend seal --plan-doc <abs-path-to-plan-doc>
   <abs-path-to-manifest>`.** Deterministic short-form seal commit
   per AC.DPS2.{1,4,6}: stages the seal narrative, runs the
   sealed-component sweep tests (or `--scoped-sweep` to limit to
   manifest-listed components), creates the
   `chore(seals): <slug> — <component> at <SHA>` commit, verifies
   `loam amend apply --dry-run` is clean post-seal.
7. **§14 method-decision-register backfill.** A separate
   `docs(plans): record <slug> commit SHAs in method-decision
   register` follow-up commit appends the apply + seal SHAs under
   `### Commit SHAs` in the plan-doc's §14, AND backfills the
   parent master plan's §9 row (when the cycle is part of a
   master plan). The seal command writes the per-cycle row when
   `--plan-doc` is set; the parent master-plan §9 update is
   manual.

The five-commit ladder per cycle: plan-doc commit → source-edit
feat (BASELINE) → manifest+apply → seal → §9 backfill.

## When to use

Trigger conditions:

- Persona is about to start any sealed-component amendment cycle
  (in v0.1.x, this is every cycle of every v0.1.x release).
- Persona is reviewing a draft cycle plan and needs to verify the
  ladder is complete.
- Persona is dispatching a build agent for a sealed-component cycle
  — the dispatch brief should reference this skill explicitly per
  `feedback_dispatch_explicit_pos_amend_apply`.

Skip when:

- The change is to an unsealed component / non-component file
  (no manifest / sidecar / seal commit needed).
- The change is a workspace-local edit that does not need a paper
  trail (rare in dev-mode workspaces; see workspace-local edits
  policy in CLAUDE.dev.md).

## How the persona applies it

1. **Verify the working directory.** `pwd` confirms canonical
   pos-v2 (or the appropriate dev-mode workspace root).
   `feedback_always_specify_wd_in_dispatches` is non-negotiable.
2. **Author the plan-doc FIRST.** No source code is touched until
   the plan-doc lands at `docs/rebuild/plans/<slug>.md`. Use
   `plan-before-code-author` skill for the structural walk.
3. **Author the manifest second.** Schema v3; reference the latest
   sealed cycle's manifest as the structural template (e.g.,
   `v0-1-8-cycle-4b-ruby-fixture-and-dry-refactor.manifest.yaml`).
   The `baseline:` field stays placeholder until step 5.
4. **Commit plan-doc + manifest** as a single `docs(plans):`
   commit. This is the gate: source code only commits AFTER the
   plan-doc lands.
5. **Build the source-edit feat.** Author code + tests within the
   single-component fence. Commit as
   `feat(<component>): <summary>`. Update the manifest's
   `baseline:` field with the resulting SHA in a follow-up
   adjustment if the placeholder was committed; otherwise the
   `baseline:` is filled before the manifest commit lands.
6. **`loam amend validate`** the manifest before apply — catches
   schema errors early.
7. **`loam amend apply --plan-doc <abs path> <manifest>`** — lands
   the manifest+apply merged commit. Verify the diff covers ONLY
   the manifest + sidecars + admitted prefixes; halt + RF if
   anything else lands.
8. **`loam amend seal --plan-doc <abs path> <manifest>`** — lands
   the seal commit + runs the sealed-component sweep. Verify post-
   seal `loam amend apply --dry-run` is clean (the seal command
   already does this; verify the exit code is 0).
9. **§14 backfill.** A `docs(plans): record <slug> commit SHAs ...`
   commit appends apply + seal SHAs to plan-doc §14 under
   `### Commit SHAs`. If the cycle is part of a master plan,
   ALSO update the master plan's §9 method-decision register row
   with the same SHAs in the same or a parallel commit.
10. **Status file.** Write per-AC status + smoke outcome + halt-
    and-surface findings to the dispatch's specified status path
    (typically `<workspace>/.scratch/claude-output/<slug>-status-
    <date>.md`).

## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin:

- The amendment-cycle ladder collapses to a manual five-commit
  workflow: plan-doc → source-edit feat → manifest-equivalent
  (any tracking yaml/md) → "seal" (a chore commit pinning the
  cycle's SHAs in a CHANGELOG.md or equivalent) → backfill.
- `loam amend apply` / `loam amend seal` / `loam amend validate`
  are absent; substitute with `git diff --stat` + `pytest -q` +
  manual sidecar updates (if your repo has one).
- The plan-before-code discipline still applies. Even without
  loam, the plan-doc gate prevents premature code commits.
- The `--amend` prohibition still applies (`feedback_no_amend_in_
  agent_dispatches`): if a file is missed, create a NEW corrective
  commit, never `git commit --amend`.

## Composition

- **`plan-before-code-author` skill** — invoked at step 2; it
  ships the plan-doc structural skeleton this skill assumes.
- **`dispatch-brief-authoring` skill** — when dispatching a build
  agent for the cycle, the dispatch brief follows that skill's
  shape. Reference this skill explicitly in the dispatch
  (`feedback_dispatch_explicit_pos_amend_apply`).
- **`audit-finding-triage` skill** — applied to any halt-and-
  surface findings the build agent returns mid-cycle.
- **`feedback_no_amend_in_agent_dispatches`** — the agent-side
  prohibition on `git commit --amend`. Mirrored in the SKILL's
  step-9 advice (corrective commits, never amend).
- **`feedback_serialize_amendment_builds`** — two amendment
  cycles cannot run in parallel in the same git tree without
  worktree isolation. This skill is single-cycle scope.
- **`feedback_dispatch_explicit_pos_amend_apply`** — the dispatch
  brief must explicitly name `loam amend apply` (not rely on the
  agent inferring usage from corpus).

## Out of scope

- The schema-version migration internals (DPS1 / DPS2 / dev-
  pattern-simplifications cycles introduced v3; this skill
  assumes v3).
- Multi-component fence semantics (this skill walks single-
  component cycles; cross-component admissions ride on the
  manifest's `universal_paths` block).
- The `--scoped-sweep` vs full-sweep tradeoff for `loam amend
  seal` (default is full sweep across every sealed component;
  `--scoped-sweep` limits to manifest-listed components — use
  when the cycle's blast radius is provably bounded; see
  `loam amend seal --help`).
- The recovery walk when `loam amend apply` fails halfway (a
  future v0.1.9 SKILL `hook-violation-recovery` will codify
  the partial-failure recovery pattern).
- Master-plan §9 backfill format (lives in the master plan
  itself; this skill's step-9 references it but doesn't
  enumerate the row schema).
