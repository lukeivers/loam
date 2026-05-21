---
description: "When the persona needs goal-directed multi-step work with autonomous halt — drive iteratively toward a stated goal, halt when the goal state is met — invoke the `/goal` slash command. `/goal` is the autonomous-loop sibling of `/loop`: the goal state is the halt criterion (not 'when the model feels done'). It is the keep-going leg of loam's `handsoff-loop` build methodology and the right primitive for any 'drive to outcome' multi-step where the outcome is checkable in-band. Use when: driving a build toward a frozen acceptance, iterating on a fix until the failing test passes, multi-step problem-solving with a clear success predicate. Composes with `loop-command` (`/loop` keeps running; `/goal` halts on success) and `handsoff-loop` (which uses `/goal` internally for the keep-going leg)."
---

# goal-command

Drive toward a stated goal across multiple iterations; halt when
the goal state is met.

## When to load me

- Persona has a checkable success predicate and wants the model to
  iterate until it passes.
- Persona is about to author a "keep trying until it works" multi-
  step task.
- Persona is invoking loam's `handsoff-loop` — `/goal` is the
  keep-going leg the orchestrator uses internally; if you're
  composing your own multi-step driver, reach for `/goal` for the
  same shape.
- Persona has a build / fix / iterate task where the success
  criterion is in-band runnable (a test, a check command, a tool-
  executing predicate).

## What the primitive does

`/goal` is a slash command that takes a stated goal and runs
iteratively toward it. Each iteration:

1. Model reads the goal + prior iterations' context.
2. Model decides next action (tool call / edit / dispatch).
3. Halt evaluator (Haiku transcript-only by default) checks the
   surfaced exit-code line / predicate output.
4. If goal met: halt cleanly. If not: continue iterating.

Compared to `/loop`: `/loop` keeps running until the model decides
to stop (or session ends); `/goal` halts the instant the goal
predicate passes. `/goal` is autonomous — no human drives the
loop; the halt evaluator decides done. Use `/loop` when the
iteration itself is the work; use `/goal` when the work is to
reach a state.

In loam's `handsoff-loop` (`framework/tools/handsoff-loop/`), each
dispatched sub-agent runs `/goal` driving the keep-going leg, with
the frozen acceptance check as the independent verifier.

## Composition

- **`loop-command`** (sibling SKILL) — `/loop` is iteration-
  shaped; `/goal` is goal-directed with autonomous halt. Pick by
  whether the work shape has a success predicate (use `/goal`) or
  is open-ended iteration (use `/loop`).
- **`handsoff-loop`** (sibling SKILL) — handsoff-loop uses `/goal`
  internally for the keep-going leg; the orchestrator wraps `/goal`
  with frozen-unseen acceptance + an independent judge. If you're
  building from scratch, use `/goal` directly. If the work is a
  full build with verification, use handsoff-loop.
- **`feedback_swarming_recursive_decomposition.md`** (memory) —
  F3 swarming: `/goal` is the per-subtask driver inside a swarm
  cycle. The `EVAL_DIMENSIONS` named-axis judging pattern composes
  with `/goal`'s halt evaluator.

## Anti-patterns

- Using `/goal` without a checkable success predicate — the halt
  evaluator has nothing to evaluate against, and the loop runs
  until rate-limit.
- Using `/goal` for open-ended iteration (research, exploration,
  brainstorming) — `/loop` is the right shape; `/goal` overfits
  to "reach this exact state."
- Trusting the sub-agent's self-report as the halt signal —
  `/goal`'s halt evaluator only reads the surfaced exit-code line
  from an independent check; self-reports are not the success
  signal.
- Using `/goal` for trivial single-step work — direct tool calls
  are cheaper.

## Example invocation

```
/goal The failing test in tests/test_foo.py::test_bar must pass.
       Verify with `pytest tests/test_foo.py::test_bar -x`.
       Halt the instant the test passes.
```

The model iterates: read failure → propose fix → apply → re-run.
Each iteration ends with the verification command; `/goal`'s halt
evaluator reads the exit code and halts on success.

Inside `handsoff-loop` orchestration:

```
Per sub-agent dispatch:
  claude -p (with /goal driving the keep-going leg)
  goal: "Make <frozen-acceptance-check> exit 0"
  halt-evaluator: Haiku reads transcript's surfaced exit-code line
  judge (separate, post-completion): independent frozen check
```
