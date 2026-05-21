---
description: "Before starting a multi-part task, check whether it can be partitioned into subtasks each with a measurably tighter acceptance criterion than the parent. Use when the user gives a task that feels large, multi-faceted, or could plausibly run as a single agent loop but might benefit from parallel decomposition. Stops decomposition when further splits add only coordination overhead. Never silently extends a single-agent loop on work that should be swarmed."
---

# scope-decompose

Recursive task decomposition driven by acceptance-criterion
tightness. When a task can be split into subtasks each with a
strictly tighter acceptance criterion, decompose. When the
proposed split adds only coordination overhead with no
tightening, stop. This skill makes the "is this actually
decomposable?" check explicit before assuming a single-agent loop
is the right shape.

## What this skill captures

Loam's F3 swarming principle: any task whose subtasks have
measurably tighter acceptance criteria than the parent should be
decomposed and executed in parallel (or dependency order), not
sequentially in a single agent loop. The principle ships three
reference patterns from kyegomez/swarms (verified at HEAD
`e48100a`, 2026-05-02):

1. **PlannerWorkerSwarm cycle.** Planner emits typed tasks → workers
   claim from a dependency-aware queue → judge produces
   `CycleVerdict` (`is_complete`, `gaps`, `needs_fresh_start`).
   The `needs_fresh_start` flag is the drift escape hatch:
   discard subtasks and restart from the planner.
2. **`ModelOutput.rationale` field.** Every model-selection
   decision records why. In dispatch briefs, this is a required
   `model-rationale: <model> — <reason>` line for non-default
   model selection.
3. **`EVAL_DIMENSIONS` named-axis judging.** Evaluate
   acceptance criteria on orthogonal dimensions concurrently
   rather than collapsing into a single yes/no.

## When to use

Trigger phrases / shapes the persona should recognise:

- A task description that lists ≥3 distinct deliverables
  ("build A and B and C").
- A task that names a parent goal and obvious sub-goals
  ("ship the v0.1.3 release" → plan + author each artefact +
  verify each + tag).
- A task where a single agent loop would cycle through ≥10 tool
  calls before producing the artefact.
- A task with multiple independent hazards that benefit from
  parallel verification.

Also use defensively when a task LOOKS small but the subtasks
would each benefit from tighter scope (e.g., "write 5 SKILL.md
packages" — each package is a separate subtask with its own
acceptance criterion).

## How the persona applies it

1. **Restate the parent acceptance criterion.** What does "done"
   look like at the top level?
2. **Enumerate the proposed subtasks.** List each one's
   acceptance criterion as plainly as possible.
3. **Tightness check.** For each subtask: is its acceptance
   criterion strictly tighter than the parent's? If yes, the
   split is justified. If no, the subtask is just coordination
   overhead — collapse back into the parent.
4. **Recurse if warranted.** Apply the same check to each
   subtask; stop when further splits would add only coordination
   overhead.
5. **Pick model tier per subtask.** When dispatching, the
   `model-rationale` rule applies — Opus / Haiku selections
   require a one-sentence reason; Sonnet is the default and
   needs no rationale line.
6. **Set `max_planner_depth` explicitly.** Default depth is 1 (no
   sub-planners). Deeper recursion requires opt-in.
7. **Watch for drift.** If a subtask's output starts diverging
   from the parent goal, restart from the planner with the
   judge's feedback — never continue a diverged chain to
   completion.

## Graceful degradation

When raw Claude Code (no loam dispatch infrastructure):

1. Apply the tightness check mentally before delegating to the
   `Task` tool or a sub-agent.
2. Pass each subtask as a separate `Task` invocation with its
   own scoped objective.
3. The single-conversation persona can still apply the principle
   internally — partition the response into named sub-objectives
   and address each, rather than meandering.

## Composition

- **Loam's F4 (prompt-scope ↔ confidence) principle.** The
  stopping criterion uses scope-confidence as its primary signal:
  high confidence in a single specific outcome → tight subtask
  scope; low confidence → broad scope so the agent can think.
- **Loam's M5 (principle-conflict resolution).** When subtasks
  conflict (e.g., one wants tight scope, another wants broad),
  apply the four-step process: name the conflict, name the
  signals, make the call, surface if non-obvious.
- **HeavySwarm 4-role pattern** (deferred to v0.2 V2.C) — for
  high-uncertainty research tasks, the 4-role decomposition
  (Research / Analysis / Alternatives / Verification → Synthesis
  aggregator) is a named recipe that fits the
  `scope-decompose` shape.

## Out of scope

- Task execution mechanics (this skill is about deciding to
  decompose, not the mechanics of dispatch — see
  `dispatch-with-gates`).
- Specific swarm-runtime primitives (PlannerWorkerSwarm,
  CycleVerdict, EVAL_DIMENSIONS) — those are post-v0.2 V2.C
  work; this skill ships the principle, not the runtime.
- Choosing between parallel and sequential execution within a
  decomposed plan (depends on dependency graph; the `Task` tool
  handles this when subtasks are independent).
