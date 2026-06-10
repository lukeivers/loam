---
description: "When the user wants a buildable artifact — a tool, script, program, package, library, CLI — that they expect to actually work when finished, invoke the packaged hands-off loop. The trigger is the build-with-verification intent, NOT specific phrasing. It fires equally on imperative asks ('build me X and check it works', 'I want Y, just go', 'don't come back until it's done and tested') AND on soft plain-language asks ('I want a small tool that does X', 'I want a thing that converts X to Y', 'I need something that does X', 'can you make me a thing that...', 'build a tool that...', 'show me it works', 'prove it works', 'run an example to show it works', 'make sure it actually works'). Non-technical users naturally use the softer phrasing — recognizing the underlying intent (user wants something built AND wants evidence it works) is this skill's job, not the user's. It runs loam's own build methodology as one capability: turn the fuzzy ask into a checkable 'done' with a single plain-language approval, decompose into scoped sub-tasks, dispatch real sub-agents with /goal driving the keep-going leg, and judge the result with an independent check the sub-agents never saw. Use whenever the work is a real build with a verifiable outcome. Do NOT use for trivial one-liners ('rename this variable'), pure question-answering ('what does this code do?'), or tasks with no machine-checkable outcome."
---

# handsoff-loop

The real orchestrated hands-off loop, packaged as a single
primary-persona-invocable capability. This is loam's own build
methodology run *for the user*.

## What this is

One capability the persona invokes — `handsoff-loop` (the CLI at
`framework/tools/handsoff-loop/`). The user states intent in plain
language, approves a plain-English "done" once, walks away, and comes
back to real verified work.

The pipeline:

1. **Intake** (`intake.py`) — fuzzy plain-language intent → bounded
   *elicit-the-minimum* (at most a few plain questions, never a spec
   interview) → a plain-English "done when:" statement → **exactly one
   plain-language approval gate** → a machine-checkable form, with an
   independent faithfulness check guarding the checkable-but-wrong
   failure. When a checkable "done" cannot be pinned (the gate would
   be empty/broken, or the faithfulness check catches a proxy), intake
   does **not** dead-end: it enters a **bounded goal-refinement**
   (interactive clarification first, else self-refine, else a
   *measurable milestone on the path* the user agrees to with a
   re-engaged check-in) — and only a definite, evidence-named
   honest-negative when even on-the-path refinement is irreducible
   (the bound is finite; the honest-negative is a valid outcome, never
   a fabricated pass).
2. **Freeze** (`verify.py`) — the machine-checkable acceptance is
   authored, hash-pinned, and frozen *before any sub-agent runs*; it is
   seen by no sub-agent and no per-sub-task judge.
3. **Decompose + dispatch** (`orchestrator.py`) — the objective is
   decomposed into scoped sub-tasks (the **probe-proven** pattern; the
   user never sees decomposition — D-UNIT). Each sub-task is a real
   `claude -p` sub-agent with **`/goal` driving the keep-going leg** (no
   human drives the loop).
4. **Judge** (`verify.py`) — loam's **independent tool-executing
   check** plus an **anti-overfit held-out check** decides "done". The
   sub-agents' self-reports are never trusted; `/goal`'s Haiku
   transcript-only evaluator only keys off the surfaced exit-code line
   the in-turn check prints — `/goal` drives, loam decides.
5. **Honest verdict** — a definite done, or a definite **dead-end**.
   Both are valid: a definite negative is reported straight, **never
   retried to green, never softened**.

## Per-request intent understanding (the general build-from-intent path)

Any vague build-shaped ask — per-request, in an established workspace,
not only at first-run onboarding — gets a LIVE intent read before
anything is built (`handsoff-loop understand --ask "<their words>"`,
one bounded spawn-isolated model call):

- the inferred end-intent is surfaced back **in plain language for
  confirmation**, derived from THAT ask (never canned — two different
  asks produce two different inferences);
- **meaningful questions only when a build-shaping decision is
  genuinely open** — at most 3, never a spec interview; an unambiguous
  ask proceeds with zero questions;
- the stated objective echoes the ask's specifics; no objective text
  exists anywhere in pipeline source;
- the proposed form factor (something you click around in / a command
  you run / something that runs on its own) is surfaced in the confirm
  in plain words.

The persona relays the confirm (and any questions) to the user in
their own vocabulary, collects answers, and only then proceeds. A
failed live read is surfaced honestly ("I couldn't get a reliable read
of this ask") — nothing is built on an un-understood intent.

## How the persona invokes it

```
handsoff-loop describe          # the capability contract (JSON)
handsoff-loop understand \
    --ask "<the user's vague build-shaped ask, verbatim>"
handsoff-loop run \
    --objective "<the user's plain-language objective>" \
    --frozen <frozen-acceptance+subtasks.json> \
    --work-dir <dir> --artifact-dir <dir>
```

Intake is `handsoff_loop.intake.derive_acceptance_from_intent(...)`
(produces the single approved unit + the independent faithfulness
verdict).

## Hard rules (load-bearing — do not relax)

- **AC.FOUND.0** — the decompose→dispatch→judge core is *already
  Tier-0 verified*. This skill **composes** it; it never re-proves it.
  Re-running the core loop to "make sure" is a named scope violation.
- **Frozen-unseen done** — the acceptance is frozen + hash-pinned
  before any sub-agent and seen by none. A leak into a brief/judge is a
  refusal, not a warning.
- **Independent judge decides** — sub-agent self-reports are never the
  "done" signal; the tool-executing check's exit code is.
- **Honest negative is success** — "the packaged mechanism is
  materially worse than hand-run" or "fuzzy intent can't be made
  faithfully checkable reliably enough" are **complete, correct
  results**, reported plainly. There is no retry-to-green path.
- **NO Anthropic API key** — every model call is the real `claude`
  binary, default Sonnet. `--bare` is never used.
- **Local only** — this capability builds and verifies; it never
  pushes, publishes, or tags. The public step is a separate
  owner-asked action.
