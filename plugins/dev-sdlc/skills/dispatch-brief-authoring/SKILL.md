---
description: Author a dispatch brief for a sealed-component build, sub-task agent, or research dispatch in a loam dev-mode workspace. The brief carries Working directory + Principles to apply at turn-start + QUALITY BAR + Source pointers + Sub-plan path + Fence + Acceptance criteria + Smoke + Halt triggers + Out of scope + Bookkeeping + Model rationale — in that order. Sets scope but never method; the sub-agent authors the plan-doc and method choices. Use when the persona is about to dispatch any build / research / authoring agent in a loam workspace.
---

# dispatch-brief-authoring

Every Cycle 1–4b in v0.1.8 used a dispatch brief in this exact
shape. The brief is the persona's contract with the dispatched
agent — it sets the boundary, the principles, and the halt
conditions, while leaving method, code-level decisions, and
artefact prose as the agent's responsibility. This skill
externalises the structural shape so the persona doesn't have
to reconstruct it from CLAUDE.md every cycle.

## What this skill captures

The dispatch-brief structural shape, in canonical order:

1. **Title line** — e.g., `# v0.1.8 Cycle 5 — 6 dev-sdlc SKILLs
   (closes v0.1.8 + release-level smoke gate)`. Names the cycle
   slug + the headline outcome.
2. **Working directory** — absolute path to the canonical
   workspace, with a NOT-clause naming the wrong path. Example:
   `Working directory: /Users/lukeivers/ivers-corp-pos-v2/
   (canonical pos-v2). NOT pos3.` Per
   `feedback_always_specify_wd_in_dispatches`.
3. **Principles to apply at turn-start** — bulleted list naming
   the active principles by name (CHANNEL / AUTONOMY / F2 RF /
   LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT /
   ODD §2.5 / WD-IN-DISPATCHES / PARTITION RULE / PLAN-BEFORE-
   CODE / POS-AMEND BOOKKEEPING / SCOPE-ONLY / etc.). Each name
   gets a one-line how-applied. The agent walks this list at
   turn-start (per `front-load-principle-walk` skill).

   **Propagated principles for sub-agents (v0.2.2; AC.DBT.1–6).**
   In addition to the per-cycle principles named above, every
   dispatch brief authored by this skill carries the following
   propagated set so sub-agents inherit them at turn-start:

   - **LEAN-GROUNDING-LOAD** (AC.DBT.2): when the work is
     ODD-shaped (extraction, ratification, plan-authoring,
     AC-tightening, gap-analysis), load
     `docs/odd-llm-grounding.lean.md` FIRST and run §self-checks
     on every output declared "objective," "AC," "constraint," or
     "capability." Non-ODD work omits the load directive. The
     dispatcher decides per-cycle whether the work is ODD-shaped.
   - **NO-CLOSING-LINE-PERMISSION-ASKS** (AC.DBT.3): sub-agent
     post-task reports must not close with "want me to..." on
     in-scope authorized work. Recommendation IS the decision per
     `feedback_no_closing_line_permission_asks`. Universal —
     applies regardless of task shape.
   - **SPECIFIC-CLAIMS-VERIFIED** (AC.DBT.4): every fact in the
     post-task report (line counts, cost estimates, SHAs,
     durations, tool-call counts) is empirically verified OR
     explicitly marked as guess/estimate/band per
     `feedback_specific_claims_verified_or_marked_guess`.
     Universal — applies to every post-task report.
   - **TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING**
     (AC.DBT.5): sub-agent runs the operational-objective test
     before treating any decision as dispatcher-escalation. State
     the operational objective; test if it implies a clear
     answer; if yes, decide autonomously; only escalate on
     critical-call / public-action / financial decisions per
     `feedback_test_against_operational_objective_before_escalating`.
     Universal.
   - **NO-FALSE-FAULT** (AC.DBT.6): sub-agent does not manufacture
     audit ✗ when no real miss occurred. Apply the four-test
     before writing ✗: (1) was upstream input clear? (2)
     over-anticipation? (3) ignored prior signals? (4)
     third-party-reviewer attribution? All no → ship forward
     without retroactive blame per
     `feedback_no_false_fault_admission`. Universal.
   - **TIME-CLAIMS-DISCIPLINE** (added 2026-05-05): every
     time-related claim in plan-doc / manifest / dispatch brief /
     post-task report is verified or correctly translated. Two
     rules: (1) for current-time / elapsed-time claims, run
     `date` (or equivalent verifiable proxy) — don't estimate
     from memory. (2) for expected-duration bands, use AI-time
     not human-developer-time per the rubric (AI is 10-50× faster;
     wall-clock minutes ≈ tool_calls × 0.1-0.15). Plan-authoring
     agents apply this at the AC.AI-time line so downstream
     consumers don't have to translate. See
     `plugins/loam-skills/skills/time-claims-discipline/SKILL.md`.
     Universal — applies to every plan-doc, manifest, dispatch
     brief, and post-task report.

   **AUDIT-BLOCK discipline** (AC.DBT.7; discipline-note prose
   only — not a separate test-AC). Apply minimal audit per
   `feedback_principle_application_front_load_and_audit` —
   surface ✓ on clean turns; surface ✗ + course-correction only
   on real misses. The negative case is pinned by AC.DBT.6
   (no manufactured ✗); the positive case (when to surface ✓)
   is behavioral and lives as prose here rather than as a
   structural AC.

   **When `subagent_type` is not `general-purpose` (v0.5.0;
   AC.V050.3).** Briefs dispatched via a typed persona handle
   (`subagent_type: loam-builder` / `loam-plan-author` /
   `loam-researcher` / `loam-reviewer` / `loam-documenter`)
   MAY omit the AC.DBT principles the persona body already
   carries — the persona prompt loads at dispatch-start and
   re-asserting in the brief is duplication. The omission is
   PARTIAL because the v0.1.7 persona bodies do not carry
   every AC.DBT principle uniformly (per the v0.5.0 audit at
   `workspace/.scratch/claude-output/v0-5-0-dispatch-site-audit.md`
   AC.DBT cross-walk). Per-persona omission table below;
   anything not marked OMIT-OK MUST still propagate in the
   brief.

   | AC.DBT principle | builder | plan-author | researcher | reviewer | documenter |
   |---|---|---|---|---|---|
   | AC.DBT.2 LEAN-GROUNDING-LOAD | propagate (partial coverage; "ODD-fluent" is named, but the lean-grounding load directive is not) | propagate (partial coverage; ODD-fluent + outcome-shape, no explicit lean-grounding load) | OMIT-OK (researcher work is rarely ODD-shaped; Lens 1–3 substitutes) | propagate (partial coverage; ODD §2.5 fluent, no explicit lean-grounding load) | OMIT-OK (documenter work is not ODD-shaped) |
   | AC.DBT.3 NO-CLOSING-LINE-PERMISSION-ASKS | propagate | propagate | propagate | propagate | propagate |
   | AC.DBT.4 SPECIFIC-CLAIMS-VERIFIED | propagate (partial — quotes ACs/SHAs but no explicit verified-or-marked-guess clause) | propagate | OMIT-OK (researcher body explicitly carries VERIFIED / PLAUSIBLE / HYPOTHESISED bands + cites the feedback memory) | OMIT-OK (reviewer body explicitly carries VERIFIED bands + "I never confabulate") | propagate (partial — "never include unverified claims") |
   | AC.DBT.5 TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING | propagate | propagate | propagate | propagate | propagate |
   | AC.DBT.6 NO-FALSE-FAULT | propagate | propagate | propagate | propagate | propagate |
   | TIME-CLAIMS-DISCIPLINE | propagate | propagate | propagate | propagate | propagate |

   The AC.DBT.{3,5,6} + TIME-CLAIMS-DISCIPLINE rows propagate
   for every typed persona because no v0.1.7 persona body
   names them. AC.DBT.{2,4} have per-persona OMIT-OK rows
   only where the persona body explicitly carries the
   discipline. When in doubt: propagate. Briefs MUST still
   carry the structural slots that are NOT AC.DBT principles
   (Working directory + literal `cd <abs-path> && pwd` first
   action + Sub-plan path + Fence + Acceptance criteria + Halt
   triggers + Out of scope + Model rationale) — those are
   universal regardless of `subagent_type`. Briefs dispatched
   via a typed persona MAY also skip the per-cycle re-derivation
   of channel rules / autonomy directive / F2 RF reminder /
   ODD §2.5 reminder / scope-only enforcement (each is
   identity-anchored in the persona body).

   **Backward-compat (universal).** When `subagent_type ==
   general-purpose` (the default for un-typed dispatches),
   the existing AC.DBT.1–6 propagation behavior is preserved
   unchanged — the brief carries the full propagated-principle
   block above. The OMIT-OK clauses apply only to typed
   dispatches.

   **Routing decision is upstream.** Which `subagent_type`
   to choose for a given dispatch is `subagent-routing`
   SKILL territory (work-shape → persona rubric). This brief-
   authoring SKILL applies the brief-shape implications of
   the routing decision; it does not re-derive the routing
   rubric.
4. **QUALITY BAR** — a quoted line from the dispatcher
   (typically Luke's voice) naming the acceptance intensity
   for this cycle, plus 2–4 enforcement bullets. Example:
   `> "I want this to WOW him. It can't be half-assed." — Luke
   2026-05-04`. Per-cycle content (not boilerplate); this slot
   is dispatcher-authored every dispatch.
5. **Source pointers** — bulleted list of authoritative
   reference paths the agent reads BEFORE acting. Master plan +
   prior-cycle seals + relevant SKILL bundles + relevant
   feedback memories.
6. **Sub-plan path** — the plan-doc + manifest paths the agent
   will author (per `plan-before-code-author` skill); the
   status file path the agent writes to.
7. **Fence** — the single-component (or named multi-component)
   fence; what's in scope; what's out of scope. The agent
   verifies post-build that `git diff` is confined to the fence.
8. **Acceptance criteria** — seed ACs the agent locks in the
   plan-doc. Per ODD §2.5: every AC has an explicit pytest
   path (or equivalent verification surface). The brief seeds
   the AC family; the plan-doc tightens the per-AC specs.
   **Tests must include an outcome-altitude probe.** The seed
   AC family carries at least one outcome-altitude AC — verified
   by a test that invokes the production entry-point (CLI / API /
   dispatch surface) with realistic inputs (no pre-arrangement of
   state the production code would produce). Risk-band classifier
   governs whether HARD per-cycle is required (production-facing
   surface) or release-gate HARD is acceptable (pure-internal
   refactor). Full rubric in `plugins/dev-sdlc/skills/
   odd-test-altitude-discipline/SKILL.md`.
9. **Smoke** — the six-dimension smoke list per
   smoke-test-discipline.md §6: D1 cold-state / D2 steady-state
   / D3 restart / D4 reboot / D5 cross-session / D6 telemetry-
   floor. Mark inapplicable dimensions n/a structurally with
   reasoning.
10. **Halt triggers** — explicit conditions that abort the
    dispatch and surface to the dispatcher. WD drift / plan-
    doc not authored before code / fence breach / time-budget
    overrun / more-than-N-decisions-need-escalation / any
    SKILL/artefact ships partial.
11. **Out of scope** — explicit exclusions. Lists deferred
    work (next-version / next-cycle / next-release).
12. **Bookkeeping** — the loam-amend cycle ladder (per
    `loam-amend-cycle` skill); whether to push tags (typically
    NOT until owner gates); §9 / STATE.md / roadmap backfill
    requirements.
13. **Reply to dispatcher** — the artefacts the agent returns
    on completion (seal SHA + ACs satisfied + smoke outcome +
    status file path + halt-and-surface findings).
14. **Model rationale** — required line for any non-default
    model selection (Opus / Haiku) per F3 swarming. Sonnet is
    the default and gets a `(none — Sonnet default)` line.

The brief NEVER carries: specific files to edit, specific
symbols / function names, specific AC text beyond the seed,
specific code layouts / module boundaries, specific commit-
message prose. Pre-specifying method reduces the plan-doc to
paperwork (per `dispatch-with-gates` skill in loam-skills).

## When to use

Trigger conditions:

- About to dispatch a sealed-component build agent (`pos
  dispatch` / `loam dispatch` / `claude` shell-out).
- About to invoke the `Task` tool for any non-trivial sub-task
  (≥3 expected tool calls in the sub-agent).
- About to relay a dispatch through Telegram / Slack / email
  to a colleague or another Claude session.
- Reviewing a draft dispatch — apply the structural rule to
  catch missing sections before sending.

Skip when:

- The work is single-tool-call, in-session, by the persona
  itself (no dispatch needed).
- The dispatch is a clarification request to the user (no
  scope / fence / halt-triggers — different shape; surface a
  question, not a brief).

## How the persona applies it

1. **Author the title + WD line first.** WD with the absolute
   path AND the NOT-clause prevents agent CWD inheritance
   from drifting to a sibling tree.
2. **Walk the principle list.** Cite each active principle by
   name with one-line how-applied. The agent's turn-start
   walk relies on this list being explicit.
3. **Author the QUALITY BAR slot.** Per-cycle content. If the
   dispatch is for a low-stakes cycle, the QUALITY BAR is
   short (one line); for a release-gating cycle, it's longer
   (a Luke-voice quote + enforcement bullets).
4. **List source pointers.** Include the master plan + prior-
   cycle seals + the SKILL bundles the agent will compose with.
5. **Name the sub-plan + manifest + status-file paths.**
   Absolute paths. The status file lives in
   `<workspace>/.scratch/claude-output/`.
6. **Name the fence.** Single-component is the default; multi-
   component requires explicit per-component admissions in the
   manifest.
7. **Seed the AC family.** Don't enumerate every AC — that's
   the plan-doc's job. Seed the AC family with the headline ACs
   + AC count target.
8. **List the smoke dimensions.** Mark n/a with reasoning when
   structurally inapplicable.
9. **Author halt triggers.** Standard set: WD drift / plan-
   before-code violation / fence breach / time-budget /
   too-many-escalations / partial-ship. Plus cycle-specific
   triggers if the cycle has a unique failure mode.
10. **Name out-of-scope.** Explicit deferrals to next cycles /
    versions; prevents scope creep.
11. **Author the bookkeeping section.** Reference the
    `loam-amend-cycle` skill or enumerate the ladder. Always
    include "DO NOT push tags" unless owner has explicitly
    authorized.
12. **Author the reply contract.** What the agent returns on
    completion.
13. **Author the model-rationale line.** `(none — Sonnet
    default)` for Sonnet; per-line rationale for Opus / Haiku.
14. **Verify before sending.** Per
    `feedback_verify_dispatch_before_sending`: for tighten /
    remove / rename dispatches, grep + read in main session
    first. Verification is the dispatcher-side mirror of the
    agent's halt-and-surface.

## Graceful degradation

When raw Claude Code without loam:

- The same structural shape applies to `Task` tool invocations
  and Slack/email/Telegram relays. Even without the dev-sdlc
  plugin, the principle list / fence / halt-triggers / scope /
  ODD-check are universal.
- The minimal fallback: objective + scope + constraints + halt
  triggers + ODD-check (per `dispatch-with-gates` in loam-
  skills). The dev-sdlc-specific structure (master plan
  pointers, loam-amend ladder) is dropped; the contract shape
  is preserved.
- For non-loam projects, substitute `loam-amend-cycle` with
  the equivalent project-local commit ladder (e.g.,
  PR-template-driven workflow).

## Composition

- **`plan-before-code-author` skill** — the brief's "Sub-plan
  path" line names where the dispatched agent will author the
  plan-doc; this skill ships the plan-doc skeleton.
- **`loam-amend-cycle` skill** — the brief's "Bookkeeping"
  section references the cycle ladder; this skill ships the
  full ladder.
- **`front-load-principle-walk` skill** — the brief's
  "Principles to apply at turn-start" list is what that skill
  walks at turn-start.
- **`audit-finding-triage` skill** — the brief's "Halt
  triggers" list ties to that skill's surface-when-meaningful
  triage on receipt of agent findings.
- **`dispatch-with-gates` skill (loam-skills plugin)** — the
  generic dispatch shape; this skill is the dev-sdlc-specific
  superset.
- **`feedback_agent_prompts_scope_only`** — the principle
  ancestor of this skill. The prohibition on method-in-
  prompt smuggling lives in that feedback memory.
- **`feedback_dispatch_explicit_pos_amend_apply`** — the brief
  must explicitly name `loam amend apply` (not rely on the
  agent inferring).
- **`feedback_subagent_odd_violation_halt`** — the brief
  carries the "halt and surface ODD violations in your work
  OR surrounding code" line. Standard.
- **`docs/odd-llm-grounding.lean.md`** (AC.DBT.2) — the lean
  ODD grounding prime; loaded FIRST on ODD-shaped sub-agent
  work. Verbose derivation at
  `docs/odd-llm-grounding-derivation.md`.
- **`feedback_no_closing_line_permission_asks`** (AC.DBT.3) —
  recommendation IS the decision; no "want me to..." closes
  on authorized in-scope work.
- **`feedback_specific_claims_verified_or_marked_guess`**
  (AC.DBT.4) — every fact in the post-task report verified or
  marked guess.
- **`feedback_test_against_operational_objective_before_escalating`**
  (AC.DBT.5) — operational-objective test before any
  dispatcher-escalation.
- **`feedback_no_false_fault_admission`** (AC.DBT.6) — no
  manufactured audit ✗; four-test before writing ✗.
- **`feedback_principle_application_front_load_and_audit`**
  (AC.DBT.7 prose) — minimal audit at end of every reply.
- **`subagent-routing` SKILL** (v0.5.0; AC.V050.2) — chooses
  the typed `subagent_type` upstream of brief authoring. The
  brief-extension §"When subagent_type is not general-purpose"
  applies the per-persona omission table when the routing
  decision returns a typed persona. Compose order: routing
  decision first, brief-shape conditional on routing.

## Out of scope

- Specific principle text — lives in CLAUDE.md / memory
  feedback files; this skill ships the structural slot.
- Specific QUALITY BAR text — per-cycle, dispatcher-authored.
- The plan-doc skeleton — see `plan-before-code-author` skill.
- The loam-amend ladder details — see `loam-amend-cycle`
  skill.
- The principle-conflict resolution four-step process — see
  `feedback_principle_conflict_resolution_multi_signal` (M5).
- The decision to dispatch at all (vs handle in-session) — see
  `scope-decompose` skill in loam-skills.
- The model-tier selection rule — see `scope-decompose` skill +
  F3 swarming feedback memory.
