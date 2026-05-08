# Core Development Convention — research before plan for non-trivial new work

> **When building a new solution (including a bug fix that produces a net-new solution rather than modifying an existing one), if the work is more complex than a very simple task, a research step is required before the plan step.**

Rationale. The existing plan-before-code CDC prevents "dive straight into editing." But for new solutions, the plan itself benefits from prior research — exploring adjacent components, reading authoritative docs, confirming constraints, surveying existing primitives — so the plan doesn't propose something that turns out to be infeasible, redundant with an existing surface, or structurally wrong. Research is not required for: (a) modifying an already-present solution, (b) tasks that are very simple (e.g. a rename, a single-line edit, a trivial deletion of orphaned code). Research IS required for: building a new component, adding a new cross-component surface, implementing a non-trivial feature inside an existing component, writing a non-trivial test harness, refactoring that crosses component boundaries. "Very simple" is a judgement call by the dispatcher; when uncertain, run research. The research step is bounded — produce a research document sized proportionately to the work, not an exhaustive survey.

How to apply. Before drafting the plan document for non-trivial new work, produce a research artifact (a short research doc, a set of findings, a primary-source catalogue) at `docs/plans/research/<name>.md` or inline in the plan's §"Research findings" section. The plan then builds on the research rather than inferring from first principles.

Applied immediately to all new-solution work from 2026-04-22 forward.
