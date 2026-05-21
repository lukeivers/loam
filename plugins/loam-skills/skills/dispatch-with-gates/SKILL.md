---
description: "When invoking a sub-agent (Task tool, dispatched background agent, or shell-out to claude), pass objective + scope + constraints + halt triggers + ODD-check ONLY. Never enumerate files, symbols, acceptance criteria, layouts, or commit prose in the dispatch prompt itself — that prescribes method and reduces the plan to paperwork. Use when the persona is about to invoke any sub-agent surface, especially for build / research / authoring work."
---

# dispatch-with-gates

Scope-only sub-agent dispatches with explicit halt triggers.
Sub-agents do their best work when the dispatcher gives them an
outcome shape and a fence — not a step-by-step recipe. This skill
captures the dispatch shape that keeps method as the builder's
call, while still binding the agent to halt-and-surface on
out-of-fence discoveries.

## What this skill captures

Loam's ODD-authoring discipline applied to sub-agent dispatches.
The dispatch prompt carries:

1. **Objective** — what the agent is producing. Outcome shape, not
   step list.
2. **Scope / fence** — what the agent may touch (files,
   components, ACs); what's out of fence.
3. **Constraints** — hard rules the agent must obey (working
   directory, no `--amend`, plan-before-code, named principles).
4. **Halt triggers** — explicit conditions that abort the dispatch
   and surface to the dispatcher (WD drift, fence breach, schema
   mismatch, time-budget overrun).
5. **ODD-check** — agents must halt-and-surface on ODD violations
   discovered in their work or surrounding code.

The dispatch prompt does NOT carry:

- Specific files to edit (that's the plan's job).
- Specific symbols / function names (the builder picks these).
- Specific acceptance-criterion text (the agent authors ACs from
  the parent objective).
- Specific code layouts / module boundaries.
- Specific commit-message prose.

Pre-specifying method in the dispatch prompt reduces the plan to
paperwork — the dispatcher is silently running the work via the
agent rather than letting the agent author the plan.

## When to use

Trigger shapes / scenarios:

- Persona is about to invoke the `Task` tool for any non-trivial
  work (≥3 expected tool calls in the sub-agent).
- Persona is about to dispatch a background agent (loam's
  `pos dispatch` / equivalent).
- Persona is about to shell out to `claude` for a separate session.
- Persona is authoring a dispatch prompt for human relay
  (Telegram, Slack, email).

Also use when reviewing a draft dispatch — apply the rule to
catch method-in-prompt smuggling before the dispatch goes out.

## How the persona applies it

1. **Author the objective first.** One paragraph, outcome-shape.
   "Author 5 SKILL.md packages" — not "create file X then edit
   file Y then run test Z".
2. **Name the fence.** Which paths / components are in scope.
   Which are explicitly out of scope. The fence is verifiable
   post-build (`git diff` confined to fence).
3. **List the constraints.** Working directory (always specify
   absolute path); plan-before-code; never `--amend`; named
   principles to follow (ODD §2.5, F3, F4, etc.).
4. **List the halt triggers.** "WD drifts → halt"; "fence breach
   → halt"; "schema mismatch → halt"; "time-budget overrun → halt
   with partial findings".
5. **Add the ODD-check.** "Halt-and-surface ODD violations in
   your work or surrounding code." Standard line; never omit.
6. **Verify the dispatch is the right action.** For tighten /
   remove / rename dispatches, grep + read in the dispatcher's
   own session before sending. Verification is the dispatcher
   side of halt-and-surface.
7. **Avoid method-in-acceptance smuggling.** Test: can the
   acceptance criterion be satisfied by a method other than the
   one you have in mind? If yes, scope is tight + good. If no,
   you've stated method (Lens 3 violation).

## Graceful degradation

When raw Claude Code (no loam dispatch infrastructure):

1. The same shape applies to `Task` tool invocations — pass
   objective + scope + constraints + halt triggers + ODD-check.
2. When delegating to a colleague via chat (Slack, Telegram),
   the same five fields make the request crisp without
   prescribing method.
3. When asking another instance of Claude (separate session),
   structure the prompt as an outcome-shape brief, not a recipe.

## Composition

- **Loam's F4 (prompt scope ↔ confidence)** — the dispatch's
  scope-tightness should track the dispatcher's confidence in
  the outcome shape. High confidence → tight scope; low
  confidence → loose scope so the agent can think broadly.
- **Loam's plan-before-code rule** — every build dispatch
  authors a plan-doc at `docs/plans/<name>.md` before
  any source code is written. The plan-doc carries the
  file-level + symbol-level + AC-level detail that the dispatch
  prompt deliberately omits.
- **Loam's `feedback_agent_prompts_scope_only`** — direct
  ancestor of this skill. The skill externalizes that
  feedback memory so the discipline survives session resets.
- **Subagent personas** (v0.1.4 V2.B) — `.claude/agents/<name>.md`
  files prime dispatched background agents with methodology
  fluency, so dispatches stay scope-only without re-deriving
  the methodology each turn.

## Out of scope

- The mechanics of background dispatch (loam-specific tooling).
- Choosing whether to dispatch at all (see `scope-decompose` for
  the decomposition decision; this skill applies once the
  decision to dispatch is made).
- Reviewing dispatched work post-completion (that's a separate
  review pattern).
- Specifying the model tier (model-rationale rule lives in
  `scope-decompose` and the F3 swarming feedback memory).
