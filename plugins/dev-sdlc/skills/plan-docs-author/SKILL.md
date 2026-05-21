---
description: >-
  Author a plan-doc per the dev-sdlc methodology — the structural
  execution of `feedback_plan_before_code`'s "every build writes a plan
  to docs/plans/<slug>.md BEFORE code" rule. Plan-doc carries objective +
  scope + AC family + halt triggers + smoke + bookkeeping + F2 RF +
  provenance + acceptance gate + `## 14.` method-decision register (per
  AC.D-sa.7 lint regex). Distinct from `plan-before-code-author` (which
  carries the WHEN — the rule that a plan must precede code); this skill
  carries the HOW-of-authoring — the section-by-section execution per
  the methodology. Trim discipline applied 2026-05-05: master plan §3
  carries cycle decomposition (light per-cycle entry + AC family seed
  only); sub-plan §4 carries the AC enumeration; §4 per-cycle dispatch
  briefs drop to a stub paragraph (briefs are authored inline at
  dispatch time); SHA backfill centralizes at master plan §9. Use
  whenever a sealed-component or major-feature build is about to start
  in a loam dev-mode workspace.
---

# plan-docs-author

`feedback_plan_before_code` says every build writes a plan to
`docs/plans/<slug>.md` BEFORE code. The first-pass
SKILL `plan-before-code-author` codifies the WHEN — the rule
that a plan-doc must precede code commits. This skill codifies
the HOW-of-authoring — the section-by-section execution per
the dev-sdlc methodology, including the load-bearing `## 14.`
method-decision register that the AC.D-sa.7 lint regex pins.

A plan-doc that exists but skips sections (no §14, no halt
triggers, no smoke dimensions, no F2 RF) is a paper-trail
ritual without substance. This skill is the substance — the
shape that makes the plan-doc actually load-bearing for the
cycle.

## What this skill captures

The plan-doc canonical section layout:

```
# <Plan-doc title — usually the cycle slug + one-line summary>

**Slug:** `<slug>`
**Date authored:** YYYY-MM-DD.
**Parent master plan:** <path or N/A>.
**Predecessor cycles:** <prior-cycle SHAs or N/A>.
**Component fence:** <single-component fence on plugins/<comp>/
                     OR multi-component admission list>.

## §1 — Outcome shape (the "why")
## §2 — Lens checks (per CLAUDE.md design lenses)
## §3 — Single-component fence (or multi-component list)
## §4 — AC family — `AC.<FAMILY>.*`
## §5 — Halt-and-surface BEFORE build (recorded autonomous
        decisions)
## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per
        smoke-test-discipline.md)
## §7 — Out of scope
## §8 — Halt triggers (in-flight)
## §9 — Bookkeeping
## §10 — F2 Ruthless Feedback (gaps named this turn)
## §11 — Provenance trail
## §12 — Acceptance gate
## 14. Method-decision record (per AC.D-sa.7 lint requirement)
```

The required sections + each one's purpose:

1. **Header block (preamble).** Slug + date + parent + predecessors
   + fence in 4–6 lines. Grep-discoverable identification.
2. **§1 Outcome shape.** Why this cycle exists. The deeper objective
   the work ladders up to. Not what — what is in §3 + §4.
3. **§2 Lens checks.** Each of CLAUDE.md's 5 lenses (or however many
   apply) with a one-line answer. Lens 4 (scope ↔ confidence) often
   captures the load-bearing tradeoff.
4. **§3 Component fence.** Exactly which directories the cycle
   edits. Single-component cycles name one fence; multi-component
   cycles enumerate each component's sub-fence. Universal admissions
   (e.g., `docs/plans/`) called out explicitly.
5. **§4 AC family.** Every AC the cycle commits to satisfy. Format:
   `AC.<FAMILY>.<index> — <one-line summary>. <2–4 sentence
   detail>.` Each AC must be testable + observable.
6. **§5 Halt-and-surface BEFORE build.** Pre-build verifications +
   autonomous decisions recorded inline. WD confirmation,
   predecessor verification, pre-flight empirical checks, locked
   methodological choices.
7. **§6 Smoke (REALISTIC CONDITION).** Each of the 6 smoke
   dimensions (D1 cold-state / D2 steady-state / D3 restart / D4
   reboot / D5 cross-session / D6 telemetry-floor) named with how
   it's exercised — verified, inherited, or n/a-with-rationale.
   Plus a full-suite green sweep clause.
8. **§7 Out of scope.** What this cycle does NOT cover (deferred to
   later versions / explicitly excluded surfaces). Prevents
   scope-creep when the build agent finds adjacent work.
9. **§8 Halt triggers (in-flight).** Conditions that fire mid-build
   stop the build for surface-and-RF. Different from §5 (pre-build
   gates).
10. **§9 Bookkeeping.** `loam amend` usage, manifest schema version,
    commit ladder shape, §14 backfill, master-plan §9 row update,
    tag-push policy.
11. **§10 F2 Ruthless Feedback.** Gaps named at plan-author time.
    The honest doubts about the cycle's shape, named explicitly to
    prevent silent drift.
12. **§11 Provenance trail.** Every load-bearing input (master
    plan, predecessor cycles, FIDRAFT entries, research artefacts,
    feedback memories) with SHA / line-number citations.
13. **§12 Acceptance gate.** A checklist of pre-cycle conditions
    (predecessors sealed, plan-doc authored, AC family locked,
    smoke dimensions covered, bookkeeping discipline named).
14. **§14 Method-decision record (per AC.D-sa.7 lint).** Every
    method-level decision that's not the default, with rationale.
    The heading must be `## 14. Method-decision record` literally
    — the lint regex pins on `## 14.` (not `## §14`).

The §14 heading shape is load-bearing: AC.D-sa.7 in dev-sdlc
methodology pins the lint regex on the literal `## 14.`
prefix (no §, no leading zero, no trailing whitespace before the
period).

## When to use

Trigger conditions:

- About to start any sealed-component amendment cycle — plan-doc
  is the gate; source code only commits after the plan-doc lands.
- Authoring a master plan (multi-cycle plan-doc) — same shape
  applies; the cycle decomposition lives in §3 of the master plan.
- Reviewing a draft plan-doc for dispatch readiness — verify
  every section is present + populated; missing sections are
  halt-and-surface findings.
- Repairing a plan-doc that skipped §14 (lint failure surfaces
  the gap) or skipped halt-triggers (in-flight halts have no
  documented exit ramp).

Skip when:

- The change is a workspace-local edit / non-sealed file /
  documentation-only README touch — these don't need the full
  ODD-shaped plan-doc per `feedback_odd_cdc_scope`.
- The change is FIDRAFT capture / TaskCreate / scratch-file
  authoring — different surfaces with different ritual.
- The change is a test-only edit within a sealed component
  (test-fix amendment) — author a smaller plan-doc covering
  only §1 + §3 + §4 + §9 + §14; full 14-section shape is
  overkill.

## How the persona applies it

1. **Verify the working directory.** `pwd` confirms the canonical
   dev-mode workspace. Per `feedback_always_specify_wd_in_
   dispatches`.
2. **Lock the slug.** Slug is kebab-case + version-prefixed for
   versioned cycles (e.g., `v0-1-9-cycle-3-skills-and-cleanup`)
   or feature-named for one-off amendments (e.g.,
   `dev-pattern-simplifications-2`). Slug is the filename stem.
3. **Author the header block first.** Slug + date + parent +
   predecessors + fence. ~6 lines. Establishes identity.
4. **Author §1 Outcome shape.** Why this cycle. The "deeper
   objective" the work ladders up to. 1–3 paragraphs.
5. **Author §2 Lens checks.** Each lens with a checkmark + 1–2
   line rationale. Lens 4 (scope ↔ confidence) usually carries
   the load-bearing tradeoff; spend more text there.
6. **Author §3 Fence.** Enumerate every directory + every file
   the cycle edits. Universal admissions called out. Multi-
   component cycles list each sub-fence.
7. **Author §4 AC family.** Every AC named, with 2–4 sentence
   detail. AC numbering: `AC.<FAMILY-NAME>.<index>` where
   family-name uses uppercase + dashes. Each AC must be testable.
   **Each AC set MUST include ≥1 AC explicitly marked at
   outcome-altitude** per `docs/odd-llm-grounding.lean.md`
   "Outcome-altitude AC requirement" section. Mark each AC
   `outcome-altitude: true|false`. Outcome-altitude ACs are
   verified by tests that invoke the production entry-point
   the user invokes, do NOT pre-arrange state the production
   code would produce, and assert on the outcome artefact.
   Risk-band classifier: cycles touching production-facing
   surface (CLI command / flag / plugin surface / user-visible
   artefact / config schema / cross-session persistence) require
   HARD per-cycle verification; pure-internal refactor with no
   observable change can rely on release-gate HARD. Full rubric
   in `plugins/dev-sdlc/skills/odd-test-altitude-discipline/
   SKILL.md`.
8. **Author §5 Halt-and-surface BEFORE build.** Pre-build
   verifications + autonomous decisions recorded inline.
   Numbered list; ~5–10 entries.
9. **Author §6 Smoke.** All 6 dimensions named explicitly. For
   each: `verified by <test file>` OR `inherited from <upstream
   sealed cycle>` OR `n/a structurally because <rationale>`.
   Plus a full-suite green sweep line.
10. **Author §7 Out of scope.** Bulleted list. Each item names
    the deferral surface (later version / explicit exclusion).
11. **Author §8 Halt triggers (in-flight).** Conditions that fire
    mid-build. Different from §5; these are the build-agent's
    halt-and-surface conditions.
12. **Author §9 Bookkeeping.** `loam amend` / manifest schema /
    commit ladder / §14 backfill / master-plan §9 row / tag-push
    policy.
13. **Author §10 F2 RF.** 2–6 honest doubts named. Each with
    mitigation. Per `feedback_ruthless_feedback`.
14. **Author §11 Provenance trail.** Every load-bearing input
    cited with SHA / line / path. The plan-doc's "where this
    decision came from."
15. **Author §12 Acceptance gate.** Numbered checklist of
    pre-cycle conditions. Each checked at plan-author time.
16. **Author §14 Method-decision record with `## 14.` heading
    LITERALLY.** Table form: `| Decision | Choice | Rationale |`.
    Every non-default method-level decision named. AC.D-sa.7
    lint regex pins on `## 14.` — verify by `grep '^## 14\.'
    docs/plans/<slug>.md` returning the heading line.
17. **Reserve commit-SHA backfill section at the bottom.** Empty
    placeholders for plan-doc commit / source-edit commit /
    apply commit / seal commit / §14 backfill commit. Filled
    post-cycle by the §14 backfill.
18. **Author the paired manifest's `narrative.target` to the
    canonical form `docs/plans/sealed/<slug>.md`** (per amendment
    #142 Scope A; closes FIDRAFT 330). This matches the
    post-#134 T1.4 archive convention and the empirical
    convergence at amendments #137 / #139 / #140 / #141. NEVER
    author `narrative.target` as a bare component name (e.g.,
    `dev-sdlc`) — the seal tool writes the narrative to that
    exact path, producing an orphan top-level file (the #138 bug
    shape, recovered via fixup `26f3a9e`). The pre-T1.4 legacy
    form `plugins/<plugin>/seals/SEAL_COMMIT.<slug>` is allowed
    as back-compat for historical manifests but is NOT the
    default for new amendments.
19. **Author the paired manifest's `baseline:` via the
    walk-forward discipline** (per amendment #142 Scope B;
    closes FIDRAFT 336). Walk forward from the predecessor
    seal commit: if any `chore(amend-fixup):` commits exist
    between the predecessor seal and current HEAD, BASELINE is
    the latest such fixup; else BASELINE is the seal commit
    itself (or, when the predecessor is fully published with
    no intervening fixups, the publish-state commit per the
    post-#141 convention — e.g., the
    `docs(readme): bump current-release to v0.X.Y` commit).
    Pinning BASELINE to a bare seal SHA that is now stale
    relative to a corrective fixup forces a `MISSING_ADMISSION`
    halt at apply time, requiring a corrective re-baseline
    commit (the #139 → #138 pattern, recovered via `ca16e41`).
    Tier-0 verify the chosen BASELINE SHA via `git rev-parse`
    + `git log --oneline <pred-seal>..HEAD` before authoring
    the manifest.
18. **Run `loam amend validate` against the manifest companion**
    — if the manifest is invalid, the plan-doc commit lands but
    the apply will fail; catch early.
19. **Commit the plan-doc + manifest as a single `docs(plans):`
    commit.** Plan-before-code gate: source code only commits
    AFTER this commit.

## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin:

- The 14-section shape still applies. The plan-doc lives at
  whatever paper-trail surface the project uses (`docs/`,
  `plans/`, GitHub Issue, Notion doc).
- §14 method-decision record is universally valuable — the
  AC.D-sa.7 lint is dev-sdlc-specific, but the discipline
  (record non-default decisions with rationale) carries to
  any project.
- The smoke-dimensions framework (D1–D6) generalizes: cold
  start / steady state / process restart / reboot / cross
  session / telemetry. Apply per-feature; substitute project-
  specific equivalents.
- Detection on fallback: if the sub-agent or co-authoring
  persona produces a plan-doc that's missing §14 or skips
  halt-triggers, surface the gap inline — don't silently
  accept a stub plan-doc. See
  `graceful-fallthrough-with-detection` for the wider
  pattern.

## Composition

- **`plan-before-code-author` skill** — the WHEN. Pairs with
  this skill: that one says "plan-doc must exist before code";
  this one says "and here's the section-by-section shape."
  Use both together for plan-doc authoring.
- **`loam-amend-cycle` skill** — the wider ladder. Plan-doc
  is step 1 of the 5-commit ladder; this skill drills into
  the plan-doc authoring; `loam-amend-cycle` covers the rest.
- **`seal-narrative-writer` skill** — the downstream surface.
  The plan-doc is what the seal narrative points AT;
  plan-doc shape determines what the seal narrative
  summarises.
- **`dispatch-brief-authoring` skill** — when dispatching a
  build agent for the cycle, the dispatch brief composes
  with the plan-doc; the brief carries scope + halt + status
  file path; the plan-doc carries §1–§14.
- **`audit-finding-triage` skill** — if the build agent
  surfaces a halt-and-surface finding mid-cycle, the triage
  may amend §10 (deferral) or §4 (AC tightening).
- **`odd-test-altitude-discipline` skill** — every §4 AC set
  authored by this skill includes ≥1 outcome-altitude AC per
  the discipline; the test-altitude SKILL carries the
  pre-arrangement detection rubric + risk-band classifier
  used at AC-authoring time.
- **`fidraft-capture` skill** — out-of-scope §7 entries that
  warrant capture beyond the plan-doc go to FIDRAFT via
  this skill.
- **`feedback_summarize_and_surface_decisions`** — the
  plan-doc itself is a summary surface; Luke rules from §1
  + §10 + §12, not by reading every section.
- **`feedback_locked_design_not_license_for_bad_outcomes`** —
  if a §10 RF surfaces a previously-locked decision producing
  a bad outcome, the plan-doc is the right surface to revisit
  (don't terminate at "it's the locked design").

## Master plan vs sub-plan shape (trim discipline, Luke 2026-05-05)

Master plans (multi-cycle plan-docs at e.g.
`docs/plans/v0-X-Y-master-plan.md`) decompose into
cycle sub-plan-docs. The trim discipline ratified
2026-05-05 makes the master/sub-plan partition strict:

**Master plan §3 — cycle decomposition (light per-cycle entry).**
Each cycle entry carries:

- **Theme** — one sentence.
- **Scope-tightening** — how this cycle's AC is strictly
  tighter than the parent's.
- **Fence** — PRIMARY component + read-only compose-points.
- **AC family seed** — one-line summary naming the AC family
  (`AC.<FAMILY>.*`) and the load-bearing concerns it covers.
  **Full AC enumeration is the cycle sub-plan-doc's §4
  responsibility, NOT the master plan's.**
- **Smoke dimensions** — one line listing covered + inherited
  + n/a dimensions.
- **Dependencies** — one line.
- **Out-of-scope** — one line.
- **AI-time band** — one line per the duration-estimation
  rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`).
- **Eric-relevance** (or persona-relevance) — one line,
  optional.

Master plan §3 entries do NOT carry: full AC.X.N enumeration
(sub-plan §4 covers); per-cycle quality-bar audit (redundant
with §6 honest doubts + §5 release smoke gate at master-plan
altitude).

**Master plan §4 — per-cycle dispatch briefs.** Replaced
with a one-paragraph stub:

> Per-cycle dispatch briefs are authored inline at dispatch
> time per the dispatch-brief-authoring SKILL. Source-of-truth
> for fence + ACs + smoke + AI-time + out-of-scope lives at §3
> above + the cycle sub-plan-doc. Common shape: WD <canonical
> path>; LOAD `docs/odd-llm-grounding.lean.md` FIRST;
> principles per dispatch-brief-authoring SKILL; manifest
> schema v3; loam amend apply (NOT --amend); single semantic
> commit; short-form seal; §14 backfill separate; master plan
> §9 backfill on seal.

The dispatch wrapper carries fence + ACs + halt triggers +
model-rationale at dispatch time. Stale dispatch briefs in
the master plan drift from the true dispatch and cause more
rework than they save.

**Master plan §9 — canonical SHA register.** Master plan §9
carries the per-cycle SHA backfill table (Apply SHA / Seal
SHA per cycle). STATE.md SHIPPED entries summarize (cycle
count + key seal SHAs + tests-green count + smoke verdict)
without repeating the full apply / seal / §14 / master plan
§9 ladder. Sub-plan §14 keeps the cycle's own commit ladder
for the cycle-doc audit trail.

**Sub-plan §5 — build dispatch brief** — replaced by a
one-paragraph stub: *"Build dispatch brief authored inline
by dispatcher at dispatch time per dispatch-brief-authoring
SKILL."*

When this skill is applied to a master plan, the 14-section
ladder above still anchors but §3 expands into the
cycle-decomposition shape; §4 drops to the stub; §9 carries
the SHA register. When applied to a sub-plan, the 14-section
ladder applies as-is, full AC enumeration in §4, §5 drops
to the dispatch-brief stub.

## Compose on Claude Code review primitives (v0.4.0 C3)

Per Lens 1 (Claude-leverage-first) and the v0.4.0 C3
substrate-composition cycle: when a plan-doc has a step that
reviews diffs / branches / PRs, **compose on the Claude-native
review surface rather than reimplementing review prose inside
loam**.

### Verified-live invocation surface (HEAD `2.1.128`, 2026-05-08)

The conference research at
`<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md`
§1 #5 + §1 #7 named the CLI as `claude code review` +
`claude code security review`. **Those verbs do NOT exist
at HEAD.** The Code Review + Security Review capabilities
are exposed via four verified-live surfaces:

- **`claude ultrareview`** subcommand — *"Run a cloud-hosted
  multi-agent code review of the current branch (or a PR
  number / base branch) and print the findings."* Best for
  cross-branch / PR-level multi-agent review.
- **`/review` SKILL** — *"Review a pull request."* In-session
  PR review.
- **`/security-review` SKILL** — *"Complete a security
  review of the pending changes on the current branch."*
  Security-specific review of pending changes.
- **`/ultrareview` SKILL** — slash-surface wrapper around
  the `claude ultrareview` CLI.

Verified-live wins over secondary citation per
`feedback_trust_operational_reality` and
`feedback_specific_claims_verified_or_marked_guess`. If a
future Anthropic release adds the literal `claude code
review` alias, this section's invocation guidance updates;
the *pattern* is stable.

### When to compose Code Review

Three composition shapes:

1. **Review-as-plan-step** (most common). The cycle has a
   discrete review step at a named ladder position (typically
   after the source-edit feat commit + before `loam amend
   apply`). Plan-doc names the SKILL or CLI invocation
   inline; build agent runs it; output feeds the next step
   (e.g., HIGH-severity findings → halt-and-surface; LOW
   findings → §10 F2 RF).
2. **Review-as-cycle**. Entire cycle is "review the prior
   cycle's output" (e.g., a v0.X.Y patch cycle that's purely
   a review pass with no source-edit). The SKILL or CLI runs
   as the cycle's primary action; plan-doc §4 ACs name the
   review verdicts as observable outcomes.
3. **Hand-author review prose**. Last resort. Only when no
   verified-live review surface fits the cycle's review
   altitude (rare; almost always one of the four surfaces
   above matches). The plan-doc author writes a review
   checklist into §10 F2 RF and the build agent self-reviews.
   Detect-and-document via
   `graceful-fallthrough-with-detection` SKILL.

### Choosing among the four surfaces

- **`/security-review` SKILL** — when the cycle's AC family
  includes input-validation / injection / auth / authz /
  crypto / supply-chain concerns. Specificity wins.
- **`claude ultrareview`** — when the review needs to run
  cross-branch / against a specific PR number / base-branch
  comparison; produces multi-agent findings on a remote
  cloud session.
- **`/review` SKILL** — in-session PR review; lighter-weight
  than `claude ultrareview`; runs in the current session
  context.
- **`/ultrareview` SKILL** — slash-surface to the CLI verb;
  use when a plan-doc step prefers the SKILL composition
  over a raw CLI invocation.

### Composition inside the §4 AC family

A review-step AC takes the shape:

```
- AC.<FAM>.<n> — <Review verb> dispatched at <ladder
  position> against <target>; <SKILL or CLI> output captured
  in build report; HIGH-severity findings = halt-and-surface
  before next ladder step; outcome-altitude: <true|false>.
```

Outcome-altitude is `true` when the AC asserts on the
review's actual verdict (e.g., "no HIGH-severity findings,
or owner ratifies a documented exception"). Outcome-altitude
is `false` when the AC asserts only on the dispatch's
existence (e.g., "the review SKILL was invoked at the named
position"). Per `feedback_test_outcome_altitude_required`,
the AC family includes ≥1 outcome-altitude review AC if the
review is load-bearing for the cycle's release gate.

### Worked example

See `docs/plans/example-code-review-composition.md` for a
worked-example plan-doc demonstrating a security-sensitive
cycle that composes on `/security-review` SKILL +
`claude ultrareview` as discrete plan-steps. The example
shows the AC shape, the dispatch ladder position, and the
graceful-degradation fallback when neither SKILL is
available.

### Composition with existing rules

- **`feedback_no_anthropic_api_key.md`** — `claude
  ultrareview` and the SKILLs run on subscription auth; no
  API key needed; subscription-only invariant preserved.
- **`feedback_specific_claims_verified_or_marked_guess.md`**
  — every plan-doc citing the review surface verifies
  against `claude --help` + the available-skills list at
  authoring time; invocation lines that don't match HEAD are
  halt-and-surface findings.
- **`graceful-fallthrough-with-detection`** SKILL — the
  detection pattern for when SKILLs aren't available; routes
  to the next composition shape down the rubric.
- **`audit-finding-triage`** SKILL — review findings feed
  into triage; HIGH findings update §4 AC families; LOW
  findings update §10 F2 RF.
- **PR-safety SKILL** — final pre-public gate; runs against
  the cycle's diff after seal + before any `git push`.
  Distinct from the cycle-internal review-step composition.

## Out of scope

- The AC.D-sa.7 lint mechanism's implementation — this skill
  captures the OUTPUT (the `## 14.` heading); the lint
  regex's source lives in dev-sdlc methodology code.
- ODD methodology rationale — `feedback_odd_no_non_objective_
  code` carries the rationale for AC-mapping discipline; this
  skill captures the §4 shape that operationalises it.
- Manifest schema (lives in `loam-amend` schema docs).
- Smoke-test framework rationale — lives in
  `plugins/dev-sdlc/docs/smoke-test-discipline.md`; this
  skill references the 6 dimensions but doesn't justify them.
- Repair walks for plan-docs that drifted from the shape — a
  drifted plan-doc is repaired in a follow-on amendment;
  this skill informs the corrective rewrite.
