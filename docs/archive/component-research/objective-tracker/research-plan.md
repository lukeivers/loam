# Research Plan — Objective Tracker

**Component:** Objective Tracker (third and final Phase 1 primitive).
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for the objective-tracker primitive such that:

- Every v1.0 Objective acceptance criterion can be honoured by a concrete implementation proposal.
- Scope-of-work's "parent objective" references become enforceable — orphan objectives are rejected at creation; every scope traces to a top-level user-authored objective.
- ODD (Objective-Driven Design) has a real runtime to operate against — tests can be authored against objectives, negative cases re-extended up the chain as new positive objectives.
- The tracker works coherently with scope-of-work (already sealed) and memory (sealed) without requiring changes to either, and with the primary-persona layer's authoring pipeline (personas are scoped to objectives they serve).

## Starting position

- **Three Phase 1 components already sealed.** Memory, scope-of-work, primary-persona layer. All on `pos-v2`. The tracker integrates with them; it does not require amendments to them (if the research surfaces an amendment requirement, that's a halt signal).
- **Scope-of-work carries parent-objective references** in its seven-field `ScopeSpec` — the field exists, but no runtime enforces that the reference resolves to a real objective. Today's behaviour: the string is stored, unverified.
- **ODD is a methodology baked into the rebuild** — research plans and briefs reference it throughout. A real objective runtime lets ODD test-suites be composed against the objective tree rather than against ad-hoc scope descriptors.
- **The spec defines three required fields** per objective: parent (or root marker), testable acceptance criterion, time-bound-or-evergreen mark. Plus one implied field: the objective's own goal statement.
- **Python-native.** New pOS language.
- **No assumed downstream consumer (A1 correction).** The tracker emits observability; consumers come later.

## Questions the research must answer

### 1. Objective primitive — schema and fields

1. What are the complete fields on an objective primitive? The spec names four (goal, parent-or-root, testable criterion, time-bound-or-evergreen). Does the primitive need more — owner, created-at, status (draft/active/achieved/abandoned), priority, measurement cadence? Which are mandatory vs optional at creation?
2. How is the "testable criterion" represented — free text, a reference to a test file, a structured predicate like scope-of-work's Pydantic discriminated-union triggers, all of the above as variants? Is it executable at check time, or is "testable" only a contract?
3. How is "time-bound-or-evergreen" expressed — a deadline, an explicit `evergreen: true` flag, a review cadence for evergreen items?
4. How is status modelled — as an event-sourced log like scope-of-work, or as mutable state on the objective itself?

### 2. Hierarchy and traceability

5. What structure best supports the required parent-tracing — a strict tree, a DAG allowing shared parents, a forest of trees? If DAG, what are the semantics when multiple parents' acceptance conflicts?
6. How does the tracker enforce "every scope traces to a top-level user-authored objective"? Options: reject scope creation when the parent-objective-id is not found; reject scope creation when the referenced objective is not ancestor-linked to a user-authored root; validate lazily at first scope event; validate deterministically at creation.
7. How does the tracker distinguish "user-authored" from "system-authored" objectives — a field on the objective, an ACL, a provenance chain?
8. What happens to in-flight scopes when a parent objective is marked abandoned or achieved — cascade, notify, ignore?

### 3. Persistence and integration with scope-of-work

9. What persistence substrate? Scope-of-work uses SQLite WAL; the natural question is whether the tracker shares that store (one DB file) or uses its own. Trade-offs: shared simplifies transactional queries ("give me all scopes under this objective"); separate keeps domain boundaries clean.
10. What is the relationship model between objectives and scopes — one-to-many (a scope has exactly one parent objective), many-to-many (a scope can serve multiple objectives), hierarchical (a scope inherits all ancestor objectives)?
11. How does the tracker expose a query surface that scope-of-work needs — when scope-of-work creates a scope with `parent_objective_id`, how does it verify the id resolves, under what latency?

### 4. Acceptance-criterion evaluation

12. How is an objective's acceptance criterion checked — on demand (user asks "is this objective achieved?"), continuously (every scope completion triggers a re-check), at a scheduled cadence, or all three? Is it the tracker's job to *run* the check, or just to *record* the criterion and let callers run?
13. How is the result of an acceptance check stored — a boolean flag on the objective, a log of check events, a derivable state from scope events?
14. How does the acceptance check interact with ODD's negative-case handling? When a negative case is re-extended up the chain as a new positive objective, does the tracker automatically create the new objective, or does it surface the case for the persona to author?

### 5. ODD-compatibility and test harness integration

15. What is the tracker's role in authoring tests against objectives? Is it passive (tests are authored separately, the tracker provides the criterion; tests run externally) or active (the tracker can execute tests against objectives, similar to pytest's collection mechanism)?
16. Does the tracker provide a way to list all objectives under a root that are below a certain status (e.g. "all active, unchecked, non-evergreen objectives under my top-level goal")? This is the base query ODD test runs will need.
17. How does the tracker represent the "objective chain" for a given scope — as a materialised path, a runtime walk of parents, a cached ancestry array?

### 6. API surface and integration

18. What does the API surface look like for `create`, `update-status`, `mark-achieved`, `mark-abandoned`, `decompose-into-children`, `list-by-parent`, `list-by-root`, `trace-to-root`? Thin async Python mirroring scope-of-work's posture.
19. How does the tracker expose an emission surface for observability (OTel) and for future consumers (self-correction loop subscribing to acceptance-check events)?
20. How does the primary-persona-layer's autonomous-authoring pipeline interact with objectives — does authoring a new persona produce objectives, consume them, or both?

### 7. Interaction with primary-persona authoring (v1.2 R14)

21. The v1.2 R14 authoring pipeline is budgeted by a scope-of-work. That scope-of-work has a parent objective. What is the convention for what that objective should be — "improve roster coverage for domain X," "author persona Y," or something more general like "maintain coherent workspace roster"?
22. When the authoring pipeline completes successfully, does the new persona inherit objectives from the authoring scope, get its own objectives, or remain objective-less until first used?

## Constraints the research must respect

- **Python-native.** stdlib preferred; pydantic, pyee, opentelemetry-api/sdk, PyYAML already in scope. Other libraries require halt-and-signal.
- **Zero carryover from current pOS / the existing workspace.** The current-pOS intake/workflow/task hierarchy, `GOALS.md` convention, and SDLC stage definitions are not reference implementations. Read them only to understand *what questions they address*, not *how*.
- **No amendments to sealed components (scope-of-work, memory, primary-persona).** If the research concludes one of them needs amendment to support the tracker cleanly, halt and surface the conflict for decision recorded — do not silently assume an amendment is ok.
- **Max-first; LLM inference inside the tracker is unexpected.** If the research surfaces a scenario where LLM inference is useful (e.g. automated negative-case re-extension suggestions), that work uses Claude via Max.
- **No assumed downstream consumer (A1 correction).** The tracker emits OTel; consumption is future work.
- **No proposals, no code, no briefs.** Only the research document.
- **Halt-on-deviation.** If any v1.0 Objective acceptance criterion or relevant v1.1/v1.2 revision cannot be satisfied, halt and surface.

## Deliverable — what the research document must contain

A markdown document at `components/objective-tracker/research.md` with:

1. **Survey of existing patterns** — how other frameworks handle hierarchical objectives, OKR-style goal tracking, or test-against-objective patterns. Specifically survey: BDD test runners (behave, pytest-bdd) for their given-when-then / scenario hierarchy; OKR tooling (Lattice, Gtmhub) for hierarchical objective modelling; LangGraph's goal-state modelling; any pytest or hypothesis plugin that binds tests to external criteria.
2. **Recommended design shape** — for each of the seven question groups, options considered, recommended option, rationale.
3. **Acceptance-criterion coverage** — mapping each v1.0 Objective criterion and relevant v1.1/v1.2 revisions to the piece of the design that delivers it. Any that cannot be satisfied surfaces as a halt.
4. **Schema sketch** — concrete Pydantic-shape for the objective primitive.
5. **Enforcement mechanism** — how scope-of-work's `parent_objective_id` reference becomes enforceable (the integration test for this is the key acceptance signal).
6. **ODD integration sketch** — how the tracker supports tests authored against objectives rather than against behaviours.
7. **Dependency map** — what depends on the tracker (every future scope; the self-correction loop when built; the primary-persona authoring pipeline indirectly); what the tracker depends on (scope-of-work for the consuming relationship; nothing else hard).
8. **Complexity estimate** — AI-time, honest. Expected smaller than primary-persona-layer (it's a single primitive with no authoring-pipeline equivalent) — ballpark 300–450 AI-minutes.
9. **Prototyping priorities** — questions only a prototype can answer (e.g. latency of parent-resolution at scope-creation time, ODD test-harness UX).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Agent reads the plan, performs the research, produces `research.md`, and returns. Halt-on-deviation applies throughout.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
