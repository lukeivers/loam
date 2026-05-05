---
description: Walk a workspace's `<workspace>/.claude/skills/` directory, evaluate each workspace-local SKILL across the 3-signal MVP (Categorization + Quality + Conflict primary; Reusability + Tests + Usage secondary non-blocking), match each candidate against the 10-row promotion-decision matrix, render a structured per-candidate table to the workspace's `.scratch/claude-output/skill-promotion-review-<date>.md`, surface each non-stay-workspace-local candidate one-at-a-time through the per-project-pm batch API with default-to-no framing per Decision G, and on owner-Y dispatch tests + run the loam-amend-cycle to graduate the SKILL to `plugins/loam-skills/skills/` (HARNESS-GENERAL) or `plugins/dev-sdlc/skills/` (DEV-SPECIFIC), then replace the workspace-local copy with a single-line pointer.md. Demotion path covered. Use when the owner invokes `/skill-promotion-review`, says "review my workspace skills" / "what skills should I promote", or it has been ≥90 days since the last review artefact under `.scratch/claude-output/skill-promotion-review-*.md`. Composes on `loam-amend-cycle`, `audit-finding-triage`, `owner-decision-summary`, `dispatch-brief-authoring`, `plan-before-code-author`. Dev-scoped per three-tier gating; only dev-mode workspaces should invoke this.
---

# skill-promotion-review

The persona-attached pipeline that turns workspace-local SKILL
accumulation into compounding harness value. Auto-skill-capture
(v0.2.0 Cycle 2) deposits candidate SKILLs under
`<workspace>/.claude/skills/<name>/` whenever recurring patterns
fire above the threshold; this SKILL is the disciplined evaluation
surface that walks each candidate, computes the 3-signal MVP,
renders per-candidate recommendations, surfaces them one-at-a-time
to the owner via the per-project-pm batch API (default-to-no), and
on ratification graduates the SKILL into a plugin via the
`loam-amend-cycle` ladder. Without this SKILL, workspace-local
SKILLs accumulate as workspace-junk OR get over-promoted without
disciplined review; with it, only the SKILLs that genuinely
deserve graduation make it into the harness.

## What this skill captures

The 3-signal MVP per Decision L (master plan §9 + layered-skills
§4.1) — three primary signals that gate any promotion
recommendation, three secondary signals discussed but
non-blocking:

**Primary signal 1 — Categorization.** Where does the SKILL
belong on the partition?

- `HARNESS-GENERAL` — universal concepts (translation discipline,
  channel rules, decision-summary, owner-onboarding). Target:
  `plugins/loam-skills/skills/`.
- `DEV-SPECIFIC` — mentions loam-amend / plan-before-code /
  sealed-component / dispatch-brief / amendment / pos-amend /
  ODD §2.5 / cycle / SKILL-package authoring. Target:
  `plugins/dev-sdlc/skills/`.
- `PROJECT-SPECIFIC` — mentions workspace-local business-domain
  identifiers, single-codebase paths, owner-only vocabulary.
  Target: stay workspace-local.

If a candidate's body splits across HARNESS-GENERAL +
DEV-SPECIFIC keywords, the categorisation is **ambiguous** —
halt and surface to the owner: "ambiguous category for
`<skill_name>`; classify as (1) HARNESS-GENERAL (2) DEV-SPECIFIC
(3) PROJECT-SPECIFIC". Never silent miscategorisation.

**Primary signal 2 — Quality.** Is the SKILL.md well-formed?
Match the structural-test convention from
`test_AC_SKILLS_DSDLC1_*_skill_present.py`:

- Frontmatter parses as YAML mapping with non-empty
  `description` ≤1536 chars (Anthropic combined-cap).
- Body non-empty post-frontmatter.
- Body covers the 6-section convention: What this skill
  captures / When to use / How the persona applies it /
  Graceful degradation / Composition / Out of scope.
- Description carries a trigger phrase (a "when to use" cue
  Anthropic's discovery can match against user intent).

Quality signal: `PASS` / `FAIL` / `NEEDS-REVISION`. `FAIL`
short-circuits to Author-time-fix recommendation; promotion
never offered before the body is well-formed.

**Primary signal 3 — Conflict.** Does this SKILL overlap with
something already under `plugins/loam-skills/skills/` or
`plugins/dev-sdlc/skills/`? Two-pass detection:

1. **Literal-name match.** Walk each plugin's `skills/`
   directory; if a directory of the same name exists, signal
   `DUPLICATE`.
2. **Description-keyword overlap.** Tokenise the candidate's
   description (lowercased, stop-words dropped) and each
   existing SKILL's description; compute Jaccard overlap. A
   candidate whose description shares >70% of its keywords with
   an existing SKILL is signal `DUPLICATE`. The 70% threshold
   is heuristic; halt-and-surface if a fixture mis-categorises.

Conflict signal vocabulary: `NO-CONFLICT` / `DUPLICATE` /
`WIDER` (workspace-local subsumes existing) / `NARROWER`
(existing subsumes workspace-local) / `ADJACENT` (overlapping
but distinct).

**Secondary signals — non-blocking inputs.** Discussed in the
review summary but do NOT block a promotion recommendation that
the 3 primary signals pass:

- *Reusability* — `STRONG` (pattern reads cleanly across
  workspaces) / `MEDIUM` (dev-only) / `WEAK` (workspace-bound).
- *Tests* — `HAS-TESTS` / `NEEDS-TESTS`. Promotion always
  requires authoring tests during graduation; a workspace-local
  SKILL is NOT expected to ship with tests.
- *Usage* — fire-count signal: `STRONG` (≥5 auto-loads or ≥2
  user-invocations in last 30 days) / `MEDIUM` / `WEAK` /
  `NONE`. At MVP this is owner-judgment; the persona does not
  query telemetry. A `NONE`/`WEAK` candidate routes to
  Defer recommendation per the matrix.

Decision matrix (10 rows mirroring layered-skills §4.2 verbatim;
the persona walks this during the review and surfaces the
matched row + recommended action per candidate):

| # | Reusability | Categorization | Quality | Tests | Usage | Conflict | Recommendation |
|---|---|---|---|---|---|---|---|
| 1 | STRONG | HARNESS-GENERAL | PASS | YES or AUTHOR | STRONG | NO-CONFLICT | **Promote-to-base** (`plugins/loam-skills/skills/<name>/`) |
| 2 | STRONG | DEV-SPECIFIC | PASS | YES or AUTHOR | STRONG | NO-CONFLICT | **Promote-to-plugin** (`plugins/dev-sdlc/skills/<name>/`) |
| 3 | MEDIUM | DEV-SPECIFIC | PASS | YES or AUTHOR | MEDIUM+ | NO-CONFLICT | **Promote-to-plugin** |
| 4 | WEAK | PROJECT-SPECIFIC | (any) | (any) | (any) | NO-CONFLICT | **Stay-workspace-local** |
| 5 | (any) | (any) | FAIL | (any) | (any) | (any) | **Author-time-fix** before any promotion |
| 6 | (any) | (any) | (any) | NEEDS-TESTS | (any) | (any) | **Author-tests** before promotion |
| 7 | (any) | (any) | (any) | (any) | NONE/WEAK | (any) | **Defer** — not enough usage data |
| 8 | (any) | (any) | (any) | (any) | (any) | DUPLICATE | **Deprecate** workspace-local |
| 9 | (any) | (any) | (any) | (any) | (any) | WIDER | **Promote-with-deprecation-pointer** to existing |
| 10 | (any) | (any) | (any) | (any) | (any) | NARROWER | **Fold-into-existing-or-keep-workspace-specific** |

The matrix is human-readable; the persona walks it during the
review and surfaces the matched row + recommendation per
candidate SKILL.

The 7-step graduation workflow (per layered-skills §4.3) applies
only to candidates whose recommendation is one of Promote-to-base
/ Promote-to-plugin / Promote-with-deprecation-pointer.

The demotion path (per layered-skills §4.4) is rare; treated as
explicit visible amendment, not routine; covered in §"How the
persona applies it" below.

## When to use

Two triggers — primary on-demand + secondary owner-self-discipline
cadence. Auto-fire via `framework/scope-of-work/` is **deferred to
v0.2.x**; Cycle 2 ships on-demand-only at MVP.

**Primary — on-demand.**

- Owner invokes `/skill-promotion-review` from chat.
- Owner's intent matches the SKILL description: "review my
  workspace skills" / "what skills should I promote" /
  "promotion review" / "evaluate my workspace's SKILLs". Anthropic's
  native description-matching auto-loads this SKILL.
- Persona, mid-cycle, observes a workspace with notable SKILL
  accumulation and asks the owner: "would now be a good time to
  run skill-promotion-review?" — owner ratifies.

**Secondary — 90-day owner-self-discipline cadence.**

When the SKILL fires (either trigger above), check filesystem
mtime on `<workspace>/.scratch/claude-output/skill-promotion-review-*.md`
artefacts. If the most-recent review is older than 90 days (or
none exist and the workspace has ≥3 candidate SKILLs under
`<workspace>/.claude/skills/`), surface "it's been >90 days since
the last review; recommend running through this cycle". This is
**recommendation, not auto-fire** — the SKILL still runs only if
the owner confirms.

Skip when:

- The workspace's `bootstrap.yaml` has `enable_auto_skill_capture: false`
  (Q6=N from v0.2.1 Cycle 1 onboarding); workspace will be empty.
  Surface "no workspace-local SKILLs found; auto-skill-capture is
  disabled — consider re-running `loam onboard`" and exit cleanly.
- The workspace is non-dev-mode (this SKILL is dev-scoped per
  three-tier gating; non-dev users accumulate SKILLs locally,
  Luke-side reviews them later).
- Auto-fire from `framework/scope-of-work/` calendar trigger
  (deferred to v0.2.x; not active at MVP).

## How the persona applies it

The 7-step walk. Every step maps to a named AC in the cycle
plan-doc §3.

1. **Verify the working directory** (per
   `feedback_always_specify_wd_in_dispatches`). `pwd` confirms
   the workspace root. If main-session CWD is pos3 / parent
   dispatcher, halt and surface — this SKILL runs in the
   workspace whose SKILLs are being evaluated.

2. **Walk `<workspace>/.claude/skills/`.** Use Anthropic's
   `Read` / `ls` primitives; for each subdirectory containing a
   `SKILL.md`, treat it as a candidate. Skip subdirectories
   whose `SKILL.md` is a single-line "graduated to ..." pointer
   (already-promoted, do not double-evaluate). If the directory
   is empty or absent, surface "no workspace-local SKILLs
   found; auto-skill-capture has not produced candidates yet"
   and exit cleanly. (AC.PROMOTE.4)

3. **Per-candidate 3-signal evaluation.** For each candidate:
   - Read its `SKILL.md`; parse frontmatter; extract description
     + body.
   - Run the Quality check (frontmatter validity + body presence
     + 6-section coverage + key-term presence). If `FAIL`, route
     directly to Author-time-fix (matrix row 5); skip remaining
     signals for this candidate.
   - Run the Categorization check via the keyword-allowlist
     above. If split / ambiguous, halt-and-surface to owner.
   - Run the Conflict check: literal-name match against
     `plugins/dev-sdlc/skills/` + `plugins/loam-skills/skills/`
     first (cheap fast-path); then description-keyword overlap.
   - Compute the secondary signals (Reusability + Tests + Usage)
     as best-effort owner-judgment; record them in the table.
   - Match the signal-tuple against the decision matrix; record
     the matched row class + recommendation.

4. **Render the structured per-candidate table.** Write a
   markdown table to
   `<workspace>/.scratch/claude-output/skill-promotion-review-<date>.md`
   (one row per candidate; columns: skill-name / Reusability /
   Categorization / Quality / Tests / Usage / Conflict /
   matched-row / recommendation). Inline a short summary in
   chat plus the artefact path; per `output-to-disk` in
   CLAUDE.md, do NOT inline the full table.

5. **Surface each non-stay-workspace-local candidate one-at-a-time
   via the per-project-pm batch API.** For each candidate whose
   recommendation is Promote-to-base / Promote-to-plugin /
   Promote-with-deprecation-pointer / Deprecate / Fold-into-existing,
   call:
   - `PMRuntime.enqueue_decision(question_text=...,
      provenance=f"skill-promotion-review:{skill_name}")`
   - `PMRuntime.surface_next_questions_batch(n=1)` — n=1 is
     load-bearing per Decision Q; never bundle.
   - Await `PMRuntime.record_response(...)` before moving on.

   Question template (default-to-no per Decision G):
   `"Promote `<skill_name>` to `<target>`? (1) No (default)
   (2) Yes — author tests + run amendment cycle (3) Defer to next
   review."`

   The default-to-no is explicit; bundled-question shape (asking
   about multiple candidates in one prompt) is forbidden — PM
   blocks per-candidate. Stay-workspace-local candidates are NOT
   surfaced (no decision needed). Author-time-fix +
   Author-tests + Defer recommendations are surfaced per the
   matrix routing — owner can ratify the action OR defer.
   (AC.PROMOTE.5)

6. **On owner-Y, run the graduation sub-flow.**

   - **Author tests if NEEDS-TESTS.** Dispatch a sub-agent (using
     the `dispatch-brief-authoring` SKILL) to author the
     AC-shaped structural test under
     `plugins/<target>/tests/test_AC_SKILLS_*_<skill_name>_skill_present.py`
     mirroring the `test_AC_SKILLS_DSDLC1_*` template:
     frontmatter validity + body non-empty + key-term presence.
     The dispatch carries scope only (no method); the sub-agent
     authors the test file, halt-and-surface on any
     misalignment. (AC.PROMOTE.6)

   - **Run the loam-amend-cycle** for the graduation. Compose
     wholesale on the `loam-amend-cycle` SKILL — do NOT
     re-implement the amendment ladder. The graduation-specific
     source-edit:
     - Move `<workspace>/.claude/skills/<name>/SKILL.md` (and any
       package files) to `plugins/<target>/skills/<name>/`
       (HARNESS-GENERAL → `plugins/loam-skills/skills/`;
       DEV-SPECIFIC → `plugins/dev-sdlc/skills/`).
     - Commit as
       `feat(<target-plugin>): promote <skill_name> from
       workspace-local`.
     - Run `loam amend apply --plan-doc <abs path> <manifest>`.
     - Run `loam amend seal --plan-doc <abs path> <manifest>`.
     - Backfill the plan-doc §14 with apply + seal SHAs.
     (AC.PROMOTE.7)

7. **Post-seal — replace workspace-local copy with pointer.md.**
   Delete `<workspace>/.claude/skills/<name>/SKILL.md` and
   replace with a single-line `pointer.md` reading:

   ```
   This skill graduated to <target-plugin>/skills/<name>/ at
   commit <SHA>; auto-discovery now loads it from the plugin.
   ```

   The original `SKILL.md` MUST be deleted; leaving both copies
   in place would cause Anthropic's filesystem-discovery to
   auto-load both and produce ambiguous behavior. (AC.PROMOTE.8)

**Demotion path** (per layered-skills §4.4, rare).

When the persona observes that a previously-promoted SKILL has
fired N times since promotion (auto-detect: low or zero
auto-load matches; user-side reports the SKILL surfaces in
unhelpful contexts), surface to the owner:

> "skill `<name>` has fired N times since promotion at commit
> `<SHA>`; demote (return to workspace-local) or retire (delete
> entirely)?"

Apply the M5 multi-signal conflict-resolution discipline when
ruling demote-vs-retire — name the signals (signal-strength,
audience, blast-radius, alternatives), make the call, surface
the rationale. On ratify:

- **Demote.** Corrective amendment cycle; move SKILL.md back to
  `<workspace>/.claude/skills/<name>/`. Commit as
  `feat(<plugin>): demote <skill_name>`.
- **Retire.** Corrective amendment cycle; delete SKILL.md +
  the test file. Commit as `feat(<plugin>): retire <skill_name>`.

Demotion is rare; treated as explicit visible amendment, not
routine. (AC.PROMOTE.9)

**Synthetic-skill fixtures as worked examples.** Four reference
fixtures live under
`plugins/dev-sdlc/tests/fixtures/skill-promotion-review/synthetic-skills/`
and exercise the named signal-evaluation paths. A
session-fresh persona walking real workspace SKILLs can use
these as worked examples:

- `well-formed-harness-general/SKILL.md` — universal-concept
  shape; expected Categorization=HARNESS-GENERAL, Quality=PASS,
  Conflict=NO-CONFLICT, recommendation=Promote-to-base (matrix
  row 1).
- `well-formed-dev-specific/SKILL.md` — mentions loam-amend /
  plan-before-code; expected Categorization=DEV-SPECIFIC,
  Quality=PASS, Conflict=NO-CONFLICT, recommendation=Promote-to-plugin
  (matrix row 2 or 3).
- `duplicate-of-existing/SKILL.md` — description-keywords
  overlap >70% with `loam-amend-cycle`; expected Quality=PASS,
  Conflict=DUPLICATE, recommendation=Deprecate (matrix row 8).
- `quality-fail/SKILL.md` — malformed (missing frontmatter
  description OR missing required body section); expected
  Quality=FAIL, recommendation=Author-time-fix (matrix row 5).

(AC.PROMOTE.11)

## Graceful degradation

When raw Claude Code is invoked without the loam-amend tooling
installed (no `loam` binary on PATH; no `pos-amend apply`
shorthand):

- The 7-step walk through steps 1–5 still applies — Read /
  filesystem walk / signal evaluation / decision-matrix lookup
  / per-candidate question-surfacing all use Anthropic-native
  primitives (Read, Write, the `/<skill>` invocation
  mechanism). The PM-batch-API call collapses to a manual
  "ask the user this one question, await answer" pattern.
- The graduation amendment cycle (step 6) collapses to a
  manual git-cycle: `git mv` the SKILL.md from workspace-local
  to plugin path; `git commit -m "feat(<plugin>): promote
  <name> from workspace-local"`; manually advance any
  CHANGELOG.md or equivalent paper trail. The
  `loam-amend-cycle` SKILL itself documents this fallback;
  this SKILL composes on it.
- The pointer.md replacement (step 7) is identical regardless
  of tooling (single-line file write; Anthropic-native).
- The 3-signal MVP + 10-row decision matrix + default-to-no
  framing remain intact — they live in the SKILL body the
  persona reads, not in any binary.
- The `feedback_no_amend_in_agent_dispatches` prohibition still
  applies: never `git commit --amend` when a step misses a
  file; create a NEW corrective commit.
- Apply the M5 multi-signal conflict-resolution discipline
  when ambiguous-categorisation surfaces — never silent
  miscategorisation.

## Composition

Composing SKILLs (each load-bearing for one or more steps):

- `loam-amend-cycle` — graduation amendment-cycle delegate
  (step 6). Step-by-step ladder lives in that SKILL; this one
  delegates wholesale.
- `audit-finding-triage` — applied to any halt-and-surface
  findings the build sub-agent (test-author dispatch) returns
  mid-cycle.
- `owner-decision-summary` — formats the per-candidate
  recommendation surface on Telegram per the Summary +
  Named Decisions with Recommendations shape.
- `dispatch-brief-authoring` — when the test-author sub-agent
  is dispatched in step 6, the dispatch brief follows that
  SKILL's shape (scope only, no method).
- `dispatch-with-gates` — for any longer-running graduation
  sub-flow, gate the dispatch with explicit halt-triggers per
  the gating skill's shape.
- `plan-before-code-author` — invoked before the graduation
  amendment cycle if the SKILL graduation is non-trivial
  (multiple SKILLs in one cycle, cross-plugin moves, etc.).

Composing feedback memories:

- `feedback_subagent_odd_violation_halt` — the test-author
  sub-agent must halt + surface ODD violations.
- `feedback_principle_conflict_resolution_multi_signal` (M5) —
  applied for ambiguous-categorisation ruling and demote-vs-retire
  ruling.
- `feedback_no_amend_in_agent_dispatches` — prohibits
  `git commit --amend`; corrective commits only.
- `feedback_dispatch_explicit_pos_amend_apply` — the
  graduation cycle's dispatch brief explicitly names
  `loam amend apply` as the bookkeeping mechanism.
- `feedback_summarize_and_surface_decisions` — the
  per-candidate question carries the recommendation as the
  default ratification path; owner rules from the summary.

## Out of scope

- **Auto-promotion without owner ratification** — never on
  roadmap. Every promotion is owner-ratified per Decision G;
  the SKILL surfaces, the owner rules.
- **Demotion-by-disuse-trigger** — automatic demotion when a
  SKILL stops firing. Deferred to v0.2.x; the demotion path
  this SKILL covers is owner-driven only.
- **Cross-workspace skill sharing** — SKILLs accumulated in
  workspace A surfacing as candidates in workspace B. Not on
  roadmap; the partition rule is per-workspace at MVP.
- **6-signal full evaluation** — Reusability + Tests + Usage
  as gating signals. Deferred to v0.2.x; MVP has them as
  secondary discussion only per Decision L.
- **Auto-fire quarterly trigger via `framework/scope-of-work/`**
  — calendar-based auto-invocation. Deferred to v0.2.x; MVP
  ships on-demand only with 90-day cadence as
  owner-self-discipline.
- **Telemetry-driven Usage signal** — fire-count from
  Anthropic's auto-load telemetry. Deferred until the
  telemetry surface stabilises; MVP uses owner-judgment.
- **Multi-SKILL batch graduation in one amendment** — the
  `loam-amend-cycle` SKILL walks single-cycle scope per
  `feedback_serialize_amendment_builds`; multi-SKILL batches
  ride one-cycle-each at MVP.
- **`loam-amend-cycle` ladder internals** — the apply / seal /
  §14 backfill mechanics live in that SKILL, not here. This
  SKILL composes on it; the graduation step delegates wholesale.
