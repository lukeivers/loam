---
description: >-
  Author an ODD-shaped plan-doc at `docs/plans/<slug>.md` BEFORE any source
  code is written for a sealed-component amendment cycle. The plan-doc
  carries Outcome shape + Lens checks + Single-component fence + AC family
  (every AC explicit) + Halt-and-surface BEFORE build + Smoke (six
  dimensions) + Out of scope + Halt triggers (in-flight) + Bookkeeping +
  F2 RF + Provenance + Acceptance gate + `## 14. Method-decision record`
  (per AC.D-sa.7 lint). Trim discipline applied 2026-05-05: master plan §3
  carries the cycle decomposition (light per-cycle entry + AC family
  seed); sub-plan §4 carries the full AC enumeration; sub-plan §5 build
  dispatch brief drops to a one-paragraph stub (briefs are authored inline
  at dispatch time per dispatch-brief-authoring SKILL). Use when the
  persona is about to start any sealed-component amendment cycle. Composes
  on `feedback_plan_before_code` (the hard rule); this skill ships the
  structural skeleton.
---

# plan-before-code-author

`feedback_plan_before_code` says every sealed-component build
writes a plan-doc to `docs/plans/<slug>.md` BEFORE code.
This skill ships the structural skeleton — the ODD-shaped section
ladder every Cycle 1–4b plan-doc walked. The skill replaces "did
I miss a section?" with a checklist; the persona authors body
prose, not skeleton.

## What this skill captures

The plan-doc structural skeleton, in canonical order:

1. **Title + status header.** `# <slug-or-title>` plus
   `**Status:** plan-author phase — sub-plan authored
   <date>, predecessor: <prior cycle> sealed at <SHA>.`
2. **§0 — Scope decision (autonomous, F2 surface).** Names
   the in-cycle scope decision and any F2 RF on it. Optional;
   omit if the dispatch's scope is unambiguous.
3. **§1 — Outcome shape (the "why").** 3–5 bullets of "Pin:"
   statements that name the outcome shape from the user's
   perspective + the verification anchor. Outcome-shaped, not
   step-list.
4. **§2 — Lens checks (per CLAUDE.md design lenses).** Per-lens
   check (Lens 1 Claude-leverage / Lens 2 harness + persona /
   Lens 3 ODD authoring / Lens 4 prompt scope ↔ confidence /
   Lens 5 swarming). Each lens gets 1–4 sentences of pass /
   fail / partial reasoning.
5. **§3 — Single-component fence.** Names the component(s)
   the cycle modifies; `universal_paths` admissions; explicit
   "no edits to <other surfaces>" exclusions.
6. **§4 — AC family — `AC.<FAMILY>.*`.** The headline section.
   Every AC is named with its acceptance text + at least one
   explicit pytest path (or equivalent verification surface).
   ODD §2.5: every line of code, every branch, every test
   maps to a named AC.
7. **§5 — Halt-and-surface BEFORE build (recorded autonomous
   decisions).** Decisions A, B, C, ... that the persona made
   autonomously at plan-author time, with rationale. Each
   decision's "evidence" line. Triggers halt-and-surface if
   any decision needs owner ruling.
8. **§6 — Smoke (REALISTIC CONDITION — all 6 dimensions).**
   D1 cold-state / D2 steady-state / D3 restart / D4 reboot /
   D5 cross-session / D6 telemetry-floor. Mark n/a structurally
   with reasoning. Plus full-suite green sweep (pre-cycle
   baseline test count). Plus release-level gate if applicable.
9. **§7 — Out of scope (this cycle).** Explicit exclusions
   deferred to next cycles / versions.
10. **§8 — Halt triggers (in-flight).** Conditions during the
    build that abort + surface. Standard set + cycle-specific.
11. **§9 — Bookkeeping.** The loam-amend cycle ladder per
    `loam-amend-cycle` skill; manifest fields named exactly;
    universal admissions named; status-file path; tag-push
    policy (typically NOT until owner gates).
12. **§10 — F2 Ruthless Feedback (gaps named this turn).**
    Numbered list of gaps / scope compromises / quality risks
    the persona surfaces explicitly. Each gap gets a
    Mitigation line.
13. **§11 — Provenance trail.** Bulleted list of prior seals,
    dispatch briefs, methodology references, and pre-cycle
    baselines (test counts, file counts, etc.).
14. **§12 — Acceptance gate.** Numbered list of gate-ready
    conditions; the plan-doc is gate-ready when every condition
    is checked.
15. **`## 14. Method-decision record`.** Required by AC.D-sa.7
    lint. The seal-tool regex expects `## 14.` not `## §14`.
    Markdown table with columns `| Decision | Choice |
    Rationale |` covering every non-default method-level
    decision. Plus a `### Commit SHAs` placeholder that
    `loam amend seal --plan-doc` populates.

## When to use

Trigger conditions:

- Persona is about to start any sealed-component amendment
  cycle in a loam dev-mode workspace.
- Persona is reviewing a draft plan-doc — apply the section
  checklist to catch missing sections before commit.
- Persona is dispatching a build agent and the dispatch brief
  references "author the plan-doc per `plan-before-code-author`
  skill" — the agent uses this skill at plan-author phase.

Skip when:

- The change is to an unsealed component / non-component file.
- The change is documentation-only and doesn't gate a sealed-
  component test sweep (rare; most doc-only changes still ride
  on the sealed-component cycle ladder for §9 traceability).

## How the persona applies it

1. **Pick the slug.** `kebab-case`; matches the manifest's
   `amendment.slug`. Plan-doc lives at
   `docs/plans/<slug>.md`; manifest at
   `docs/plans/<slug>.manifest.yaml`.
2. **Author §1 first.** Outcome shape pins. Use "Pin:" prefix
   for each bullet. Anchor each pin to a verification surface
   (test path / spec ref / smoke dimension).
3. **Walk the lens checks.** Each of the 5 lenses gets a
   pass / fail / partial verdict with reasoning. If any lens
   fails, the cycle's design needs revision — halt + surface.
4. **Author §3 fence.** Name the component path explicitly.
   List universal_paths admissions. Explicitly exclude every
   other surface.
5. **Author §4 AC family.** Every AC has acceptance text +
   pytest path (or equivalent). Don't enumerate ACs in the
   dispatch brief — the brief seeds the family; the plan-doc
   tightens. ODD §2.5: every line maps to a named AC.
   **Outcome-altitude requirement:** every AC set includes ≥1
   AC marked `outcome-altitude: true` per
   `docs/odd-llm-grounding.lean.md`. Outcome-altitude ACs are
   verified by tests invoking the production entry-point with
   realistic inputs (no pre-arrangement bypass). Risk-band
   classifier: production-facing surface (CLI / plugin /
   user-visible artefact / config / cross-session persistence)
   → HARD per-cycle required; pure-internal refactor →
   release-gate HARD acceptable. Full rubric in
   `plugins/dev-sdlc/skills/odd-test-altitude-discipline/
   SKILL.md`.
6. **Author §5 autonomous decisions.** Each decision A/B/C/...
   has a one-line rationale + (when applicable) an evidence
   citation. If any decision needs owner ruling, halt + surface
   here.
7. **Author §6 smoke.** Walk all 6 dimensions. Mark n/a
   structurally with reasoning. Always include the full-suite
   green-sweep line (pre-cycle baseline test count). For
   release-gating cycles, include the release-level gate ref.
8. **Author §7 out-of-scope.** Be explicit. Vague "future
   work" is a regression.
9. **Author §8 halt triggers.** Standard set: WD drift / plan-
   before-code violation / fence breach / time-budget overrun /
   more-than-N escalations / partial-ship. Plus cycle-specific
   triggers.
10. **Author §9 bookkeeping.** Reference `loam-amend-cycle`
    skill. Name the manifest fields exactly. Always
    "DO NOT push tags".
11. **Author §10 F2 RF.** Surface every quality gap / scope
    compromise / design tradeoff. Each gap gets a Mitigation
    line. Per `feedback_ruthless_feedback`: name the
    disagreement, name the evidence, name the alternative.
12. **Author §11 provenance.** Bulleted seal SHAs + ref docs
    + pre-cycle baseline test counts (verified, not guessed,
    per `feedback_specific_claims_verified_or_marked_guess`).
13. **Author §12 acceptance gate.** Numbered list of gate
    conditions; check each.
14. **Author §14 method-decision record.** Markdown table
    covering every non-default method choice. Include the
    `### Commit SHAs` placeholder that `loam amend seal
    --plan-doc` populates.
15. **Commit the plan-doc + manifest as a single
    `docs(plans):` commit BEFORE source code.** This is the
    gate. Per `loam-amend-cycle` skill step 4.

## Trim discipline (Luke 2026-05-05)

The structural skeleton above operationalises the
plan-doc shape; the trim discipline ratified 2026-05-05
governs **what goes inside the sections** when the
plan-doc is part of a master/sub-plan pair.

**Sub-plan §4 (AC family) carries the full AC
enumeration.** Every AC named with acceptance text +
pytest path. The master plan §3 cycle-decomposition entry
carries only an AC family seed (one-line summary naming
`AC.<FAMILY>.*` + the load-bearing concerns). Do NOT
duplicate the full AC.X.N enumeration in the master plan
§3 entry — it drifts from sub-plan §4 over the cycle's
life and creates a stale parallel surface.

**Build dispatch brief drops to a stub paragraph.** Some
legacy sub-plan-docs included a "§5 — Build dispatch
brief" section (between AC family and halt-and-surface)
enumerating the dispatch operational fields (WD, manifest
schema, model rationale, halt triggers). With the trim
discipline, this is dropped; the section is replaced by
a one-paragraph stub:

> Build dispatch brief authored inline by dispatcher at
> dispatch time per `dispatch-brief-authoring` SKILL.

The dispatcher's brief at dispatch time is the
source-of-truth — the dispatch wrapper carries fence +
ACs + halt triggers + model rationale + WD. Keeping a
parallel build dispatch brief in the plan-doc creates
drift between what's planned and what's actually
dispatched.

**SHA backfill centralizes at master plan §9.** The
master plan §9 method-decision register carries the
canonical per-cycle SHA backfill table. Sub-plan §14
keeps the cycle's own commit ladder (plan-doc / source /
apply / seal SHAs) for the cycle-doc audit trail.
STATE.md SHIPPED entries summarize (cycle count + key
seal SHAs + tests-green count + smoke verdict) without
repeating the full ladder.

## Graceful degradation

When raw Claude Code without loam:

- The same skeleton applies to any structured plan-doc. Drop
  the loam-specific sections (§9 bookkeeping references
  loam-amend; §11 provenance references seal SHAs); keep the
  structural ones (Outcome / ACs / Halt triggers / Smoke /
  Out of scope / RF).
- Minimal fallback: a `plan.md` covering Objective + ACs +
  Halt triggers + Done condition. Even without ODD discipline,
  this prevents premature code commits.
- The plan-before-code rule is universal: any non-trivial
  build benefits from a written contract that pre-dates the
  code.

## Composition

- **`loam-amend-cycle` skill** — invoked at step 15; this
  skill ships the cycle ladder this skill assumes.
- **`dispatch-brief-authoring` skill** — when this skill is
  invoked by a dispatched build agent, the dispatch brief
  references this skill at "Sub-plan path".
- **`fidraft-capture` skill** — the §10 F2 RF section
  surfaces gaps that may need durable capture; the
  fidraft-capture skill names the routing.
- **`feedback_plan_before_code`** — the hard-rule ancestor.
  This skill is the structural operationalisation.
- **`feedback_subagent_odd_violation_halt`** — the §8 halt
  triggers include the standard ODD-violation halt clause.
- **`feedback_summarize_and_surface_decisions`** — the §5
  autonomous-decisions section is the persona-side mirror;
  named decisions surface inline rather than buried.
- **`feedback_locked_design_not_license_for_bad_outcomes`**
  — the §10 F2 RF section explicitly admits "this is a
  locked design but the outcome may be bad" surfaces; the
  feedback memory says locked-design isn't a terminator.
- **`feedback_specific_claims_verified_or_marked_guess`** —
  every test count / file count / SHA in §11 provenance is
  empirically verified before stating, OR explicitly marked
  as guess/estimate.
- **`odd-test-altitude-discipline` skill** — §4 AC family
  authoring runs through this skill's outcome-altitude
  requirement + pre-arrangement detection rubric +
  risk-band classifier.

## Out of scope

- The actual code (this skill is plan-time-only).
- The manifest authoring (lives in `loam-amend-cycle`
  skill's step 2).
- The seal-time §14 backfill (the seal command does this;
  this skill ships the §14 placeholder).
- The master-plan §9 row format (lives in the master plan
  itself).
- The ODD methodology depth (`plugins/dev-sdlc/docs/
  odd-methodology.md` carries the per-language and per-
  framework conventions).
- The principle-conflict resolution four-step process
  (M5; lives in `feedback_principle_conflict_resolution_
  multi_signal`).
