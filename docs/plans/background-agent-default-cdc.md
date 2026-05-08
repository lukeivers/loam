# Plan — background-agent-default CDC

## Objective

Codify in `docs/FUTURE_IDEAS.md` that all execution work in pos-v2
(build, commit, edit, test, scripted probes, anything that is not direct
conversation / reading / memory-or-plan writing) runs through background
agents or subagents, with no "short work is fine in foreground" carve-out.

## Context (ruling 2026-04-22)

- The main conversational session between Luke and the primary-persona-layer
  assistant is an interactive channel.
- Every tool call in the main session blocks that channel — the owner
  cannot redirect, interject, or halt without waiting for the call to
  return.
- Background agents preserve interactivity unconditionally.
- Earlier softening ("short work is fine in foreground") is struck.
- This is a companion to the existing "plan before code, always" CDC,
  which already has a Subagent flow subsection. The new CDC formalises
  the subagent flow as the default path, not a preference.

## Acceptance criteria

1. `docs/FUTURE_IDEAS.md` gains a new top-level Core Development
   Convention titled "Run all execution work through background agents /
   subagents".
2. The CDC is inserted between the existing "plan before code, always"
   CDC and the existing "setup scripts self-retire on success" CDC —
   a peer, not a subsection.
3. CDC states the rule, the why (main session is interactive channel),
   the legitimate main-session operations (reading files, direct-answer
   tool calls to user questions, memory writes, plan writes,
   conversation), and that "everything else" goes to background.
4. No carve-out for "short work".

## Files changed

- `docs/FUTURE_IDEAS.md` (additive only — new section inserted
  between existing CDCs).
- `docs/plans/background-agent-default-cdc.md` (this plan).

## Validation

1. `grep -n "Run all execution work through background agents"
   docs/FUTURE_IDEAS.md` returns one hit, under a `## Core
   Development Convention` header.
2. `git diff --name-only HEAD` after the edit shows exactly two paths:
   `docs/FUTURE_IDEAS.md` and
   `docs/plans/background-agent-default-cdc.md`.
3. The existing "plan before code, always" and "setup scripts
   self-retire on success" CDCs are unchanged (grep confirms their
   headers still present).

## Halt triggers

- If the working diff touches any file outside the two listed above,
  halt and escalate.
- If the insertion would modify any prose inside the two adjacent CDCs,
  halt and escalate.

## ODD compliance

Doc-only change, prose rule, no method prescription, no code, no silent
exception branches, no non-objective code. ODD-clean.
