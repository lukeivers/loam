# Research Plan — Safety Layer

**Component:** Safety Layer — the deterministic-layer enforcement of kill switches (scope / session / system), the "always ask the user" list, and dangerous-operation gates for irreversible-blast-radius actions.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for the safety layer such that:

- Each of the three kill-switch levels (scope / session / system) is independently testable, stops work within a bounded time, and can be triggered by the user through an obvious and always-available surface.
- The "always ask the user" list exists as a first-class testable artifact, enforced deterministically — not as an advisory rule interpreted by the primary persona at runtime.
- Dangerous-operation gates block irreversible-blast-radius actions before they execute. The definition of "irreversible blast radius" leverages scope-of-work's existing reversibility-class declarations.
- The safety layer composes the sealed components' existing safety surfaces (orchestrator's `pause_activation`, scope-of-work's `cancel`, graceful-degradation's `pause_activation` consumer pattern) into a coherent user-facing whole — without amending any of them.
- The user-facing ergonomics match the spec's non-tech-user posture: a kill switch has to be *findable and obvious* under duress, not a CLI subcommand nobody remembers at 3am.

## Starting position

- **Eight sealed components on `pos-v2`** — the full foundational layer (Phases 1 + 2) closed at 14:12 CDT. Safety integrates with orchestrator (`pause_activation` / `resume_activation`), scope-of-work (`cancel` + reversibility-class field), graceful-degradation (existing pause path on the orchestrator), primary-persona layer (user-facing notification via one-on-one channel).
- **Three partial safety surfaces already exist:**
    - Scope-level: scope-of-work's `cancel(scope_id)` + `halt-cascade` on parent scopes.
    - Session-level: orchestrator's `pause_activation("reason")` stops new scope activations.
    - System-level: no existing surface. This is the gap the safety layer fills.
- **No "always ask" list exists yet.** The spec calls for it; no component has implemented it.
- **No dangerous-operation gate exists yet.** Scope-of-work's reversibility class is declared but not enforced as a blocker.
- **Python 3.13 dev target, `pos-v2` branch.** Permitted deps stdlib + pydantic + pyee + opentelemetry + PyYAML + duckdb.
- **No amendments to sealed components** — safety layer consumes their public surfaces.

## Questions the research must answer

### 1. Kill-switch surface — three levels

1. What's the user-facing surface for triggering each kill switch? Candidates: CLI commands (`pos kill scope <id>`, `pos kill session`, `pos kill system`); primary-persona conversation (user says "stop" / "halt" / "emergency stop" and persona triggers); hardware-accessible (a specific key combo or signal); all three.
2. How does each kill propagate to the right sealed component's existing halt surface?
    - **Scope kill** → scope-of-work `cancel(scope_id)` with appropriate cascade policy.
    - **Session kill** → orchestrator `pause_activation` + primary-persona monitor broadcasts to active session.
    - **System kill** → new ground: orchestrator stops all activity, graceful-degradation-style. Does system kill shut down the orchestrator process itself, or pause everything indefinitely?
3. What's the bounded time commitment for each? The spec says "stops work within a bounded time" — what's the actual time budget the research recommends for each level, and how is it measured?
4. What happens to state when a kill fires? Work-in-progress from the killed level — preserved for resume, or terminated? Per-level choice or uniform?
5. Is a kill reversible? Can the user "un-kill" a session after killing it? If so, what's the resume path? If not, how does the user restart?

### 2. "Always ask" list — the testable artifact

6. What is the "always ask" list concretely — a YAML file, a Python registry, declared in the persona contract, all of the above?
7. What categories of action should the default list include? Candidates from the spec (rules): committing external funds, external communications that represent the user to a real person, strategy pivots, personal-life judgment, high-stakes irreversible actions. Should the default list be workspace-tunable? Framework-fixed? Hybrid (framework-fixed floor + workspace additions)?
8. What does "enforced at the deterministic layer" mean concretely? The check must happen before an LLM call that would perform the action, not after — that's the point of determinism. Where does the gate sit — in the orchestrator's dispatch path (before `bind_scope`)? In scope-of-work's activation path? In a new interceptor?
9. How does the gate surface the ask to the user? Through the primary persona's one-on-one channel (v1.1 R13 + v1.2 R15 discipline)? Via the same notification surface as graceful-degradation?
10. What's the response protocol? The user answers yes/no; the gate releases or refuses. What's the timeout? What if the user doesn't answer?

### 3. Dangerous-operation gate — blast-radius enforcement

11. How is "irreversible blast radius" defined operationally? The spec gives examples (commits external funds, sends communications, publishes content, modifies production systems, destroys data, affects legal/financial/health standing). The research needs a concrete decision procedure the gate applies at runtime.
12. Does the gate integrate with scope-of-work's `reversibility_class` field? A scope with class `irreversible` triggers the gate; `compensatable` is softer; `fully_reversible` bypasses. Is this the only signal, or are additional signals needed (tool type, side-effect class, etc.)?
13. Where does the gate sit in the execution path? Before the action executes; after the action has been proposed but before it's committed. Tool-call-level gate? Scope-activation-level gate? Both?
14. How does the gate handle the case where an LLM has *already* spent budget on planning before the gate fires? The plan's cost is sunk; the action is blocked. Is there a refund semantic analogous to scope-of-work's budget refund?
15. What's the user-facing message when a gate fires? The dangerous-operation's nature; why it's gated; what resolution options exist (approve one-time, approve and add to an allow-list, refuse, refuse and add to a deny-list).

### 4. Integration with sealed components

16. Orchestrator: the system-level kill switch almost certainly needs to invoke orchestrator machinery. Is a new orchestrator method required, or can system-kill be composed from existing `pause_activation` + SIGTERM? (If a new method is required, halt and surface — no amendments rule.)
17. Scope-of-work: scope-level kill uses `cancel`. The dangerous-operation gate reads reversibility class. Both are consumption only — no amendment expected.
18. Primary-persona layer: notification channel for ask-list + kill-fired surfacing. Consumption only.
19. Graceful-degradation: the safety layer's system-kill looks structurally similar to graceful-degradation's P1 pause-all. Should the two share infrastructure, or are they semantically distinct (safety is user-initiated; degradation is Claude-initiated)?
20. Observability aggregator: safety events are first-class spans — every kill, every ask, every gate-fire must emit. Standard OTel.

### 5. User-facing ergonomics

21. The spec's non-tech-user posture demands the kill switch be *findable and obvious under duress*. What does that mean concretely? A persistent system-tray icon? A keyboard shortcut recognised system-wide? A voice command? A CLI command that's mnemonic enough to remember at 3am?
22. What's the discoverability story? First-run orientation surfaces the kill switch(es) so the user knows they exist. That's orientation-component territory — tracked on BACKLOG — but the safety layer must cooperate.
23. What's the anti-accidental-kill design? The system-kill in particular should not fire on a stray keypress. Two-step confirm? Distinct gesture? Timed-press?

### 6. State and observability

24. The safety layer owns its own state — kill history, always-ask-list content and edits, gate firings, user decisions on asks/gates. Own SQLite at `~/.pos/safety.sqlite`, following the orchestrator / graceful-degradation pattern?
25. What's emitted to OTel? Every kill (scope/session/system), every ask-list gate invocation + resolution, every dangerous-op gate invocation + resolution, every manual add/remove from the always-ask list.

### 7. Testing discipline

26. How does the safety-layer's test suite simulate kills without actually killing productive state? Use an in-memory mock orchestrator + scope runtime; verify the right sealed-component surfaces are called with the right arguments.
27. What's the "bounded time commitment" measurement methodology? A kill is issued; the test measures time-until-halted for each level.
28. How is the always-ask list tested? Synthetic actions matching each default category; verify the gate fires; verify workspace additions + removals take effect.

## Constraints the research must respect

- **Python-native.** Permitted runtime as enumerated.
- **No amendments to sealed components.** Safety layer consumes existing public surfaces.
- **Zero carryover from current pOS.** Rules-file safety machinery is not a reference.
- **Max-first.** LLM inference inside the safety layer is unexpected. If used at all (e.g. for authoring user-facing messages on new gate types), uses Claude via Max.
- **A1 correction held.** Emit OTel; observability aggregator subscribes.
- **No personas in pOS core.**
- **Halt-on-deviation.**
- **One-on-one notification surface only** — v1.1 R13 + v1.2 R15 inherit.
- **Deterministic-layer enforcement.** The always-ask list and dangerous-operation gate must be structural checks, not advisory rules an LLM can reason its way around.

## Deliverable — what the research document must contain

A markdown document at `components/safety-layer/research.md` with:

1. **Survey of existing patterns** — OS-level kill switches (SIGTERM, SIGKILL, Ctrl-C, system panic buttons); approval-gate patterns (sudo prompts, OAuth scopes, deploy-gate approvals); deterministic-pre-check patterns in AI agents (constitutional AI, tool-use permission models, Claude's built-in refusal patterns).
2. **Recommended design shape** — for each of the seven question groups, options considered, recommended option, rationale.
3. **Clause-by-clause spec coverage** — mapping each v1.0 Safety acceptance criterion to the piece of the design that delivers it.
4. **Kill-switch invocation surface specification** — what the user types / says / presses to fire each level; how discoverable it is; anti-accidental-fire discipline.
5. **Always-ask list format + default contents** — concrete YAML schema sketch + recommended default entries the framework ships with.
6. **Dangerous-operation gate specification** — how it reads reversibility class + additional signals; where it sits in the execution path.
7. **Integration sequence diagrams** — user-initiated kill at each level; ask-list gate firing; dangerous-op gate firing.
8. **Relationship to graceful-degradation** — whether safety's system-kill shares infrastructure with degradation's P1 pause-all or they're cleanly separate.
9. **Dependency map** — consumed by: future components (self-correction loop, reversibility primitive may use safety's gate infrastructure). Depends on: orchestrator, scope-of-work, primary-persona layer.
10. **Complexity estimate** — AI-time with calibration note. Expected comparable to graceful-degradation or slightly larger; ballpark 400–550 AI-min → ~40–55 min calibrated wall-clock.
11. **Prototyping priorities** — questions only a prototype can answer (e.g. system-kill bounded-time commitment under realistic workload).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
