# Plan — scope-only dispatch to delegated agents CDC

**Date:** 2026-04-22. **Author:** recovery build in canonical `ivers-corp-pos-v2` worktree.
**Status:** plan-before-code artefact, authored before the doc edit.

---

## Objective

Codify in `docs/FUTURE_IDEAS.md` — as a peer Core Development
Convention — that any delegation handoff from a session or persona to a
delegated agent (subagent, background agent, scheduled worker, another
persona) carries scope material only. Method — files, symbols,
acceptance-criteria prose, step structure, commit wording — belongs in
the receiving agent's plan, not in the dispatching prompt.

The rule is ODD's delegator/builder split (`docs/odd-methodology.md`
§1.1) applied to the specific surface of session-to-agent handoffs. It is
surface-agnostic: research, scope-of-work, background monitoring, persona
handoffs, code builds, doc authoring all fall under the same asymmetry.

## Context (why the recovery is happening)

A prior dispatch to codify this rule ran against the wrong worktree
(`/Users/lukeivers/pos3/`), which is not the canonical pos-v2 tree; its
commit `d2e8772` is orphaned relative to the live `pos-v2` branch at
`/Users/lukeivers/ivers-corp-pos-v2/`. This plan and the accompanying
doc edit redo the work in the canonical location so the CDC lands on
the branch that actually ships pos-v2.

## Scope

1. Append one `## Core Development Convention — scope-only dispatch to
   delegated agents` entry to
   `/Users/lukeivers/ivers-corp-pos-v2/docs/FUTURE_IDEAS.md`.
2. Place it as the third rule in the CDC chain so the reader encounters
   the companions in composition order:
   - plan-before-code (plans must exist before code),
   - all-work-through-background-agents (execution runs in a delegated
     agent),
   - scope-only-dispatch (the handoff to that delegated agent carries
     scope only).
3. Land this plan file at
   `/Users/lukeivers/ivers-corp-pos-v2/docs/plans/scope-only-dispatch-cdc.md`.
4. Commit plan + doc edit together on branch `pos-v2` in the canonical
   worktree.

Out of scope: any file outside `docs/rebuild/`; any touch of the pos3
worktree; any change to `odd-methodology.md` itself.

## Decisions taken before writing the doc

1. **Placement.** Between the existing "Run all execution work through
   background agents / subagents" CDC and the existing "setup scripts
   self-retire on success" CDC. Rationale: the three session-level
   conventions (plan-before-code, background-agent-default,
   scope-only-dispatch) compose as a chain and should appear
   contiguously; the self-retire rule is a different conceptual
   concern (code lifecycle, not delegation shape) and stays below.

2. **Shape of the CDC entry.** Matches the existing template in the
   file: `## Core Development Convention — <headline>` header, a
   blockquote stating the rule, a `Rationale.` paragraph, an
   application note, and a closing paragraph that names the two
   companion CDCs plus the §1.1 source.

3. **Rule-shape constraint (the rule must obey itself).** The rule is
   stated scope-only: it names *what belongs in scope-authoring*
   (objective, scope boundaries, constraints, halt triggers, shape of
   the acceptance check) and *what does not* (file paths, symbol
   names, acceptance-criteria prose, ordered step lists, commit
   wording). It deliberately does not prescribe a dispatch-prompt
   layout or section ordering — that would be method, and prescribing
   it would make the rule violate itself. This mirrors the ODD posture
   of stating outcomes, not procedures.

4. **Generality.** The rule is written to cover every delegation
   shape — research dispatches, scope-of-work assignments, background
   monitoring runs, persona handoffs, code builds, doc authoring. Not
   dev-specific.

5. **Cross-references.** Cite `docs/odd-methodology.md` §1.1 directly
   (the delegator/builder table). Name the two companion CDCs by
   their short label inline so the three-rule chain is legible in
   one read.

6. **Headline.** "scope-only dispatch to delegated agents" — names the
   input shape (scope-only), the action (dispatch), and the recipient
   (delegated agents, which is general enough to cover subagents,
   background agents, scheduled workers, and other personas).

## Outcome (what must be true at the end)

1. `/Users/lukeivers/ivers-corp-pos-v2/docs/FUTURE_IDEAS.md`
   contains a new `## Core Development Convention — scope-only dispatch
   to delegated agents` section, positioned between the
   background-agent-default CDC and the self-retire CDC.
2. The entry's rule statement is outcome-shaped: it names input vs.
   method surfaces without prescribing a dispatch-prompt template.
3. The entry cross-references `docs/odd-methodology.md` §1.1 and
   names both companion CDCs (plan-before-code and
   all-work-through-background-agents).
4. This plan file exists on disk at the path above.
5. A single commit on branch `pos-v2` in the canonical worktree
   contains both the doc addition and this plan.
6. No file outside `docs/rebuild/` is modified.
7. The pos3 worktree is not touched.

## Halt triggers

1. If `pwd` inside the build step resolves to pos3 and the build cannot
   cd to the canonical worktree — halt and surface.
2. If the target section already exists in the canonical
   `FUTURE_IDEAS.md` with substantively equivalent content — halt and
   surface (the recovery has already happened).
3. If the rule as drafted conflicts with or weakens an existing CDC —
   halt and surface.
4. If the edit expands beyond `docs/rebuild/` — halt.

## Acceptance-check shape

The delegator will confirm:

- The new CDC exists in the canonical `FUTURE_IDEAS.md` in the correct
  chain position.
- The rule is stated scope-only (no dispatch-prompt template, no
  method prescription).
- The cross-reference to §1.1 is present and accurate.
- The companion CDCs are named by label.
- Plan file exists at the declared path.
- Single commit on `pos-v2`; commit SHA returned in the final report.

## ODD self-check

- Outcome-shaped? Yes — the rule names input/method surfaces without
  prescribing a procedure.
- No silent exception branches? Yes — prose doc, no code paths.
- No non-objective code? Yes — no code.
- Rule itself authored scope-only? Yes — it does not prescribe a
  dispatch-prompt template or section ordering.

## Sequencing

1. This plan is written in the main session (plan writes are on the
   main-session allowlist per the background-agent-default CDC).
2. The doc edit and commit run in a background agent per the
   background-agent-default CDC.
3. The dispatch to that background agent carries scope only, per the
   CDC being codified.
4. Final report: plan path, commit SHA, confirmation the commit is in
   the canonical tree, ODD self-check result.
