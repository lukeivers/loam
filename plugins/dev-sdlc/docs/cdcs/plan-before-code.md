# Core Development Convention — plan before code, always

> **Every build — every scope of work, every amendment, every fix —
> requires a written build plan on disk BEFORE code writing begins. On
> completion, verify the plan exists and the outcome matches it. ODD
> compliance check runs against every completed scope before moving on.**

Rationale. The 2026-04-22 audit surfaced three RED components
(workspace-bootstrap, hands-off-lifecycle, session-resilient-orchestrator)
with ODD violations that traced back to work proceeding without a
scoped plan against the acceptance criteria. Amendments extended
pre-existing violations (non-objective Linux code, method-in-acceptance)
because the extending author did not pause to verify the existing
surface was itself AC-backed before adding to it. A written plan closes
that gap: it forces the author to name which ACs the work satisfies,
what files are touched, and what validation proves the plan's outcome
before any code is produced.

Mechanics:

- Plans live at `docs/plans/<work-item-name>.md`.
- Plan structure: objective, ACs-satisfied (cite by ID), files changed,
  validation strategy, halt triggers. Mirrors the proposal format at a
  smaller scale for work that doesn't warrant a full five-gate cycle.
- Plan writes-to-disk happen before any source edit.
- Plan commits with (or just before) the code it describes.
- Completion check: verify plan file exists AND the outcome matches
  what the plan declared.

Subagent flow:

- Every subagent dispatched for build work is instructed to write the
  plan file first, then execute against it.
- The agent's final report cites the plan path.
- The main session verifies at return.

ODD compliance check on every completed scope:

- Acceptance criteria are outcome-shaped, deterministic, one-test-per-criterion.
- No method-in-acceptance.
- No silent exception branches for cases no AC names.
- No code supporting cases the objectives do not declare (§2.5).
- Tests assert outcome, not method.

Violations surface immediately, not in a future audit.

Question-asking discipline (companion rule):

- Before asking the owner any question, evaluate it against the
  design corpus: objectives spec v1.0+v1.1+v1.2, odd-methodology.md,
  odd-in-loam.md, VALUE_PROPOSITION.md, STATE.md, FUTURE_IDEAS.md.
- Only surface questions that are NOT answered by those sources.
- Do not present "options to rule on" when the methodology already
  rules — method-level choices are the builder's call per ODD.

Applied immediately to all work from 2026-04-22 forward.
