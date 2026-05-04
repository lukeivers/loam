---
description: "At the start of every non-trivial turn in a loam dev-mode workspace (and at the start of every dispatched build), explicitly re-cite the active principles by name before any non-trivial tool call. Refreshes the persona's attention pointer that text-corpus session-start reminders alone don't sustain across long multi-thread sessions. Standard list — CHANNEL / AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES-OVER-IN-MOMENT-JUDGMENT / ODD §2.5 / WD-IN-DISPATCHES / PARTITION RULE / PLAN-BEFORE-CODE / POS-AMEND BOOKKEEPING / SCOPE-ONLY (per cycle, names vary). Use at every turn-start and at the start of every dispatch brief's principle-walk section."
---

# front-load-principle-walk

`feedback_principle_self_reminder_at_end_of_turn` is the
end-of-turn re-cite; this skill is the start-of-turn re-cite.
Together they book-end the turn so principles stay active across
long multi-thread sessions where a single session-start corpus
load is insufficient. This skill is the dispatcher-side and
agent-side ritual for re-anchoring attention to the principles
before any tool call lands.

## What this skill captures

The turn-start re-cite ritual:

1. **At the moment a non-trivial turn begins** (a dispatched
   build, a planning conversation, a research turn, a multi-
   tool-call response), the persona names the active principles
   by name BEFORE the first non-trivial tool call.
2. **Each principle name gets a one-line how-applied** —
   either inline ("CHANNEL — replies route to dispatcher, NOT
   Telegram") or implicitly through dispatch-brief
   structure (the brief's "Principles to apply at turn-start"
   section is the explicit walk).
3. **The list is per-cycle / per-turn** — not every principle
   applies every turn. Pick the ones that bind THIS turn.

The standard catalogue (re-cite by name; bodies live in
CLAUDE.md / memory feedback files):

- **CHANNEL** — Telegram is the only user-visible channel
  when MCP is loaded; dispatcher replies route to dispatcher,
  not Telegram. Per CLAUDE.md "Channel rules".
- **AUTONOMY** — settle decisions yourself; only escalate
  genuinely-critical / public-action / financial. Per
  `feedback_strict_autonomy_no_pause_for_authorized_work`.
- **F2 RUTHLESS FEEDBACK** — name disagreements / scope
  compromises / quality gaps immediately; silent acceptance
  is the silence RF prohibits. Per `feedback_ruthless_feedback`.
- **LOCKED-DESIGN-NOT-LICENSE** — locked decisions are
  revisitable when their outcomes are bad; locked-design is
  not a terminator. Per
  `feedback_locked_design_not_license_for_bad_outcomes`.
- **PROMISES > IN-MOMENT JUDGMENT** — quality bar is non-
  negotiable; release-gates and stated promises override
  in-moment time pressure.
- **ODD §2.5** — every line of code, every branch, every
  test maps to a named AC; unnamed cases = violation. Per
  `feedback_odd_no_non_objective_code`.
- **WD-IN-DISPATCHES** — agents inherit CWD by default; every
  dispatch names the absolute working directory + a NOT-clause.
  Per `feedback_always_specify_wd_in_dispatches`.
- **PARTITION RULE** — sealed-component fences hold; cross-
  component edits ride on `universal_paths` admissions only.
  Per the dev-mode-manifest.yaml partition.
- **PLAN-BEFORE-CODE** — every sealed-component build writes
  the plan-doc before code commits land. Per
  `feedback_plan_before_code` and `plan-before-code-author`
  skill.
- **POS-AMEND BOOKKEEPING** — `loam amend apply` (NOT
  `--amend`); v3 manifest schema; short-form seal commits.
  Per `feedback_no_amend_in_agent_dispatches`.
- **SCOPE-ONLY** — dispatches carry objective + scope +
  constraints + halt + ODD-check ONLY; method is the
  builder's call. Per `feedback_agent_prompts_scope_only` and
  `dispatch-with-gates` skill in loam-skills.
- **THREE-TIER GATING** — base SKILLs (loam-skills) load
  always; dev SKILLs (dev-sdlc) load when plugin enabled;
  workspace-local SKILLs override per-workspace. Per
  v0.1.7 layered-skill discovery.
- **CRITICAL-THINKING-ON-DEVIATIONS** — when norm breaks,
  enumerate resolutions, weigh outcome × cost × risk; pick
  the balance. Per `feedback_critical_thinking_on_deviations`.
- **ASYMMETRIC PROBLEM SOLVING** — hunt for high-leverage
  points proactively; surface them when seen. Per
  `feedback_asymmetric_problem_solving`.
- **PRINCIPLE-CONFLICT MULTI-SIGNAL** — when two principles
  conflict, apply the four-step process: name conflict / name
  signals / make call / surface if non-obvious. Per M5.

The cycle-specific list trims the standard catalogue to the
principles that bind THIS turn, plus any cycle-unique principle
(e.g., "NEW-SCHEMA — manifest v3" for cycles using v3 schema).

## When to use

Trigger conditions:

- Persona is opening any non-trivial turn (≥3 expected tool
  calls; or any sealed-component-affecting turn; or any user-
  visible reply that lands through a dispatch chain).
- Persona is authoring a dispatch brief — the brief's
  "Principles to apply at turn-start" section IS this walk.
- Dispatched agent is opening a build turn — the brief's
  principle list is the agent's anchor; the agent walks it
  at turn-start before any tool call.
- Reviewing a draft turn-opener — apply the walk to verify
  active principles are named.

Skip when:

- Single-tool-call clarification turn (no build, no scope
  change, no user-visible reply).
- Pure status-read turn (read-only; no build, no
  dispatch, no commit).
- Turn already opened with the walk completed (don't repeat
  within a turn — the refresh is per-turn, not per-tool-call).

## How the persona applies it

1. **At turn-start**, before any tool call, identify the
   active principles for this turn. Default: the cycle's
   dispatch-brief list (when the persona is the dispatched
   agent), or the persona's standing CLAUDE.md list (when
   the persona is the dispatcher).
2. **Name each principle by name.** One line per principle:
   `<NAME> — <one-line how-applied>`. The names are the
   re-cite anchor; the one-line bodies are the binding
   reminders.
3. **Cite uncommon principles explicitly.** The standard
   catalogue is a baseline; cycle-unique principles
   (e.g., "FRESH-USER smoke = canonical pos-v2") get
   their own line.
4. **Include in dispatch briefs.** The brief's "Principles
   to apply at turn-start" section is this walk, surfaced
   as the dispatched agent's anchor.
5. **End-of-turn pair.** At end-of-turn, re-walk the same
   list to verify each principle was honored (per
   `feedback_principle_self_reminder_at_end_of_turn`). Mark
   ✓ or N/A per principle. Surface a course-correction
   reply if a miss is detected.
6. **Telegram footer pair.** Per
   `feedback_principle_application_footer_in_telegram`,
   every Telegram reply ends with a `Principle application
   this exchange:` footer enumerating each active principle
   as ✓ with one-line how-applied OR N/A. The start-of-turn
   walk seeds the footer's content; the end-of-turn walk
   verifies it.

## Graceful degradation

When raw Claude Code without loam:

- The same ritual applies to any structured turn-opener.
  Without the loam principle catalogue, substitute the
  user's stated principles (project conventions, code-of-
  conduct, technical standards).
- Minimal fallback: name the 3–5 most load-bearing
  principles for the turn (e.g., "no force-push to main",
  "tests must pass before merge", "ask before destructive
  ops"). Even degraded, the re-cite refreshes attention.
- The per-turn refresh discipline is universal: any agent
  operating across many tool calls drifts unless its
  principles are re-anchored periodically.

## Composition

- **`feedback_principle_self_reminder_at_end_of_turn`** —
  the end-of-turn pair. Together they book-end the turn.
- **`feedback_session_start_discipline`** — the session-
  start corpus walk; this skill is the per-turn refresh
  on top of session-start.
- **`feedback_principle_application_footer_in_telegram`**
  — the Telegram-message footer pair. Start-of-turn walk
  seeds; end-of-turn walk verifies; footer surfaces.
- **`dispatch-brief-authoring` skill** — the dispatch
  brief's "Principles to apply at turn-start" section
  IS this walk, externalised into the brief.
- **`feedback_principle_conflict_resolution_multi_signal`**
  (M5) — when two principles in the walk conflict, apply
  the four-step process; this skill names the principles,
  M5 resolves conflicts.
- **`audit-finding-triage` skill** — the triage walk on a
  dispatched agent's findings checks against the active
  principles (the walk's list).

## Out of scope

- The full text of each principle (lives in CLAUDE.md /
  memory feedback files; this skill carries the names + the
  re-cite ritual).
- The principle-conflict resolution four-step process (M5;
  this skill names the principles, M5 handles conflicts).
- The end-of-turn audit-block trailer (different shape; see
  `audit-block-on-telegram` skill in loam-skills + the
  feedback memory).
- Single-tool-call turns (the refresh is per-non-trivial-
  turn; trivial turns are exempt).
- The Telegram-channel routing rule (different surface; see
  CLAUDE.md "Channel rules" + the channel-only-Telegram
  feedback memory).
