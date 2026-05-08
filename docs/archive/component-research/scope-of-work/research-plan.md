# Research Plan — Scope-of-Work Primitive

**Component:** Scope-of-Work Primitive. **Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape of the scope-of-work primitive such that:

- Every spec acceptance criterion in objectives spec v1.0 "Core primitives" section can be honoured by a concrete implementation proposal authored from this research.
- The relevant v1.1 revisions that depend on scope semantics (R11 observability, R12 per-prompt cost) are supported.
- The primitive is consistent with the already-built memory system (which currently uses `MockScopeSource`) such that retiring the mock is straightforward.
- The primitive is coherent with the objective-tracker and primary-persona-loader primitives that will follow (they reference scope semantics).

This research produces the options, tradeoffs, and recommendations. The proposal that follows converts the research into a build plan. No code is written in this phase.

## Starting position

- **Spec defines the seven fields.** Goal, constraints, budget (time/tokens/money), reversibility class, success criteria, observers, escalation triggers. These are fixed; the research does not re-open them.
- **Memory system already exists** on the new pOS (pos-v2 branch). It uses `MockScopeSource` at `pos-v2/memory-system/src/scope.py` to stand in until the real primitive lands. Whatever shape this research recommends must be retrofittable into memory's scope-attribution layer without rewriting it.
- **No other new-pOS components exist yet.** The other foundational concerns named in the spec — session-resilience, observability consumption, graceful degradation, self-upgrade, cost governance, safety, reversibility — are later components with their own separate design. Scope-of-work ships on its own and emits observability; downstream components subscribe when they are built. A1 correction applies: this primitive does not assume any consumer exists.
- **Python-native.** New pOS language.

## Questions the research must answer

### Survey first — what exists

Unlike memory, no existing harness has a primitive matching all seven fields. But several have partial analogues that inform design. The survey should canvass:

1. What do existing agent frameworks use as their unit-of-work? Anthropic Agent SDK's "task," Letta's "message/thread," LangChain's "chain run," LlamaIndex's "workflow step," Claude's native agent pattern. For each, which of the seven fields are present, which are absent, and what is the lifecycle model?
2. What do workflow engines (Temporal, Prefect, Dagster, Airflow) use as their unit-of-work? These are not AI-native, but they solve the durable-state-across-restarts problem — what patterns are reusable?
3. Is there any AI-harness library designed specifically around budgeted, observed, escalatable units of work (as opposed to bare task/thread primitives)? If yes, score it against the seven fields.

For each candidate surveyed, report which of the seven fields it natively supports, which would need adaptation, and which are conceptually incompatible with its design.

### Lifecycle

4. What lifecycle model fits the seven-field primitive? Candidates: finite state machine (proposed → active → paused → {completed | failed | cancelled}), event-sourced log with derived state, actor-model with supervisor. For each, what are the implications for persistence, concurrency, and rollback (reversibility primitive will depend on this)?
5. What is the concurrency model? Can a scope spawn child scopes? Can multiple scopes run in parallel under a common parent? How are transitions between states observed?

### Budget enforcement

6. How is the budget (time/tokens/money) tracked and enforced? Per-LLM-call debit, poll-based metering, external-rate-limiter, or hybrid? How will the primitive cooperate with a future cost-governance component (spec v1.0 — system-wide ceilings and throttling) without coupling to any specific implementation of it?
7. What happens when a scope hits its budget? Halt-and-signal (per rebuild rule), throttle, request-extension-from-owner, or scope-dependent? Who decides?

### Observers and escalation triggers

8. How do observers get notified of scope events (state change, budget crossing, completion)? Pub-sub, polling, callback, hook? How is the observer list defined and modified?
9. How are escalation triggers specified declaratively (budget exceeds X, time exceeds Y, confidence below Z, specific event fires), and how are they fired operationally?

### Hierarchy

10. How do scopes nest and relate? Is there a parent-child tree, a dependency graph, both, neither? How does a sub-scope's outcome propagate up to its parent? How does a parent's cancellation affect children?

### Persistence and integration

11. What is the persistence substrate? Candidates to consider include at minimum: SQLite (embedded), Graphiti on Kuzu (reuse memory's substrate — scopes as entities in the knowledge graph), an append-only log with an index, a dedicated embedded key-value store, or a Python data-file approach. For each, score on durability, query-ability, scale, and compatibility with the spec's semantic round-trip upgrade test (v1.1 R1).
12. How does a scope survive session restart, system restart, or Claude outage (per graceful-degradation spec)? What state is recoverable, what is lost?
13. How does the primitive emit observability in OTel form (per R11 + A1 correction)? Which scope events translate to spans, which to logs, which to metrics?

### API surface

14. What is the API surface for callers (primary persona, agents, dispatched work)? What does scope creation look like? State transition? Querying? Completion?
15. Is the API synchronous, asynchronous, or both? How does it compose with Python's async model? How does it compose with Graphiti's async patterns already in pOS?

### Retirement of memory's mock

16. What is the minimum interface memory's scope-attribution layer needs from the real primitive to retire `MockScopeSource`? Specifically: what does `MemoryAPI.ingest(scope_id=...)` need, and what does `MemoryAPI.search(scope_id=...)` need? The research surfaces this as a direct integration acceptance test.

## Constraints the research must respect

- **Python-native.** Pure Python implementation; stdlib-preferred where possible; well-maintained packages acceptable when they solve concrete problems (pydantic for schema, etc.).
- **Max-subscription-first, vendor-free outside Max.** Scope-of-work is mostly deterministic infrastructure (no LLM calls expected inside the primitive itself) — so the Max constraint is effectively non-binding here. If research surfaces a scenario where the primitive benefits from LLM inference (e.g. auto-generating escalation triggers from natural-language descriptions), that work uses Claude via Max.
- **Zero carryover from current pOS.** No reading of `ops/orchestrator/`, existing task/workflow/job schemas, or any current-pOS code for design inspiration. Treat the problem fresh.
- **No proposals, no code, no briefs.** Only the research document.
- **Halt-on-deviation.** If the research concludes any spec acceptance criterion cannot be met by a reasonable design, halt and surface the conflict. Do not propose a design that quietly fails the spec.
- **ODD-compatible.** Each recommended design trace traces back to a spec objective. Options that cannot be tested against an objective are noted as untestable and discarded.

## Deliverable — what the research document must contain

A markdown document at `components/scope-of-work/research.md` with:

1. **Survey results** — candidates-by-seven-fields table; patterns from workflow engines worth reusing; one-paragraph verdict on each candidate.
2. **Recommended design shape** — lifecycle model, concurrency model, persistence substrate, budget mechanism, observer/escalation mechanism, hierarchy model, API surface. For each, the alternatives considered and the rationale for the recommendation.
3. **Acceptance-criterion coverage** — mapping each spec acceptance criterion and each dependent v1.1 revision to the piece of the design that delivers it. Any that cannot be satisfied surfaces as a halt.
4. **Memory-mock retirement path** — concrete integration test asserting the minimum interface memory needs.
5. **Dependency map** — what the primitive depends on (nothing yet, ideally), what later components (as spec objectives, not named current-pOS components) will depend on it — objective tracker, primary persona loader, observability consumer, cost governance, safety layer, reversibility primitive. Note each as one-way or bidirectional. The primitive names its emission shape and API surface; consumers are future work.
6. **Complexity estimate** — AI-time, honest, with surprises called out. Expected larger than memory's adaptation layer because this is core-primitive work; the builder starts from nothing rather than adapting an existing library.
7. **Open questions for prototyping** — list questions only a prototype can answer, with proposals for minimum prototypes.

## Execution note

On owner's approval, this plan is passed to a general-purpose Agent. The Agent reads the plan, performs the research, produces `research.md`, and returns. If the Agent concludes any question cannot be answered under the constraints as written, it halts and surfaces the conflict.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches a general-purpose Agent to conduct the research.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks the plan.
