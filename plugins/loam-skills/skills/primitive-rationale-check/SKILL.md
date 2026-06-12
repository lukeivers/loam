---
description: "When the persona is about to invoke a non-default primitive — spawning a background Agent instead of inline tool calls, building a bespoke loop/scheduler/orchestrator instead of reaching for the native one, using a hook instead of a memory rule, using launchd instead of a session-cron, using a non-Sonnet model — verify the dispatch carries a `primitive-rationale:` line naming the primitive (or naming `bespoke`) plus a one-sentence reason. Mirrors the `model-rationale:` discipline for Opus/Haiku selection. The line is BOTH the escape hatch and the audit record. Composes with tool-selection-rubric (decides which primitive) and claude-feature-awareness (the corpus catalogue); this SKILL records the choice — and the dispatch-time structural check enforces its presence on bespoke-equivalent dispatches."
---

# primitive-rationale-check

When authoring a dispatch, a hook addition, a SKILL, a scheduler
choice, or a model override, and the chosen primitive is NOT the
default — record the choice with a one-line rationale. The line is
small overhead and it is the audit trail.

This discipline is no longer advisory-only. The dispatch-time
structural check (the primitive-check guard, shipped as a PreToolUse
`Task` hook in the dev-sdlc plugin) reads every Agent-dispatch prompt:
when the prompt describes building a bespoke equivalent of a catalogued
primitive and carries no `primitive-rationale:` line, the check
surfaces it. The rationale line is exactly what clears the check. This
SKILL documents the shape the hook enforces.

## When to load me

When authoring a dispatch / hook / SKILL / scheduler choice / model
override, and the chosen primitive deviates from the default:

- Inline tool calls (vs background Agent dispatch).
- The native primitive (vs a bespoke loop / scheduler / orchestrator).
- Sonnet model (vs Opus / Haiku override).
- Memory rule (vs hook addition).
- Session-only scheduling (vs a durable launchd plist).
- Bash (vs an MCP tool when both are available).

If the chosen primitive matches the default, this SKILL does not fire.
If it deviates, add the line.

## What the primitive does

The shape:

```
primitive-rationale: <primitive or "bespoke"> — <one-sentence reason>
```

`primitive-rationale: bespoke — <reason>` is **explicitly valid**.
Bespoke is sometimes correct; the discipline demands *consideration*,
not surrender. The line records that the alternative was weighed and
names why the choice was made. Examples:

```
primitive-rationale: background Agent dispatch — multi-artefact
authoring benefits from independent context to avoid main-session
pollution; the work is minutes-long, past the inline budget.

primitive-rationale: launchd plist — durable cross-session scheduling
is required (the job must fire on cadence whether or not a session is
open); a session-bound scheduler cannot meet that.

primitive-rationale: bespoke — the native primitive does not expose the
mid-run hook this workflow needs; a thin custom wrapper is the smaller
surface than bending the primitive. (Weighed against the native option;
chosen deliberately.)
```

## Why this exists

Without a rationale-of-record, primitive selection is invisible. Three
failure modes:

1. **Default-creep.** Every dispatch becomes a background Agent by
   habit; nobody asks "could this be inline." Tokens burn on setup.
2. **Sunk-cost capture.** An early primitive choice ossifies even after
   the work shifts; without a record, nobody re-checks.
3. **Audit-gap.** When a choice goes badly, the post-mortem asks "why
   did we use X" with no answer but inference from what got built.

The rationale line is one sentence and closes all three.

## Composition

- **`tool-selection-rubric`** — provides the seven-decision framework
  for WHICH primitive. This SKILL records the choice the rubric makes.
- **`claude-feature-awareness`** — the corpus catalogue of options the
  rubric reads from.
- **The dispatch-time primitive-check guard** (dev-sdlc PreToolUse
  `Task` hook) — the structural enforcement of this discipline. The
  `primitive-rationale:` line is the hatch that clears it; the line is
  also written into the hook's audit log, so using the hatch leaves a
  record. The `model-rationale:` line (already required on every
  Opus/Haiku dispatch) is the sibling discipline this one extends from
  MODEL to PRIMITIVE.
- **F2 Ruthless Feedback** — silently accepting a default primitive is
  the silence F2 prevents; the rationale line makes the choice visible.

## Anti-patterns

- **Writing a bespoke loop/scheduler/orchestrator without first reading
  the corpus catalogue.** The native primitive may already do it;
  `claude-feature-awareness` routes you to the entry.
- **Treating the line as paperwork.** It is the audit record AND the
  hatch. One sentence that names the real reason is worth more than a
  paragraph that restates the choice.

## Example invocation

> Persona is about to dispatch an agent to "build a polling loop that
> re-checks the deploy every hour." The rubric (decision E) names
> `/loop` / `/schedule` as the native candidates. The persona judges a
> bespoke loop is genuinely needed and writes
> `primitive-rationale: bespoke — the per-iteration work needs a custom
> stop-condition the native loop does not expose`. The dispatch-time
> check reads the line, allows the dispatch, and logs the hatch-use.
