# Harness usage audit — 13 sealed components vs persona / production callers

**Date:** 2026-04-26.
**Author:** dispatched audit agent (Opus 4.7, 1M context).
**Lens:** Lens 2 (VALUE_PROPOSITION.md) — *the harness is the toolkit the persona draws from*. Components built but not drawn-from are a value-prop failure.
**Working tree audited:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Reading method:** for each of the 13 sealed components, read `docs/archive/component-research/<name>/proposal.md` heads + `<src>/__init__.py` (public surface) + grep for production callers (excluding tests, `.egg-info`, in-component imports).

---

## Headline verdict

Most of the harness is wired structurally — nine of thirteen components have at least one production import path. The damage is not "dead code that nobody imports"; it is that **nothing on the persona-facing layer ever asks the harness anything**. The persona's prompt makes zero references to budgets, ceilings, kill switches, reversibility, rollback, correction, or system health. Every IPC method built into cost-governance / safety-layer / reversibility-primitive / self-correction is **technically reachable but persona-invisible**.

The single most acute gap is the one Luke flagged: **cost-governance's gate fires only when a `ScopeSpec` reaches `activate_scope`, and the only production code path that ever constructs a `ScopeSpec` is `self-correction/spec_builder.py`**. Every other component — including the agent dispatches the persona issues every turn — runs *outside* the cost gate entirely. Cost-governance is "the harness the persona refuses to lean on" by structural omission, not by design.

---

## One-page summary — component-by-component verdict

| # | Component | Surface (one-line) | Production callers | Gap class | Persona fix | Amendment candidate |
|---|---|---|---|---|---|---|
| 1 | **memory-system** | FastAPI sidecar + JSONL sinks; Pydantic schemas; retention runtime | bootstrap launches sidecar; persona writes via **MCP** (`memory-graphiti`) — not via memory-system's own API | dual-path divergence — sidecar built, persona uses MCP | persona narrate which memory it's writing/reading | **A1**: triage memory-system vs MCP — collapse to one; sidecar may be dormant |
| 2 | **scope-of-work** | `ScopeSpec`, `Budget`, `ScopeRuntime`, pyee emitter | `cost-governance`, `self-correction`, `graceful-degradation`, `primary-persona/monitor`, orchestrator | partial — `ScopeRuntime` consumed; `ScopeSpec` constructor used only by `self-correction/spec_builder.py` | persona MUST author a ScopeSpec for every dispatch (agent, scheduled, background) | **A2**: agent-dispatch-as-scope wrapper (closes cost gap too) |
| 3 | **primary-persona-layer** | contract loader, awareness monitor, authoring pipeline, introduction dispatcher, MCP memory client, session-start hook | bootstrap; orchestrator (BackgroundWorkMonitor); graceful-degradation channels; cost-governance channels; self-correction notifier | partial — loader/monitor/composer wired; `AuthoringPipeline` + `IntroductionDispatcher` + `retire_persona` not invoked in production | persona must invoke creation-trigger detector when the user names a workflow that warrants a specialist | **A3**: creation-trigger live-detection adapter (currently only test-fired) |
| 4 | **objective-tracker** | objective registry, scope binding, projection-view query | orchestrator (bind_scope), `tools/heavy-b-migrate`, `tools/pos-amend`, persona `tracker_context.py`, bootstrap | OK | persona narrate which objective every dispatch ladders up to | none |
| 5 | **session-resilient orchestrator** | `Orchestrator`, `IPCServer`, `activate_scope`, `pause_activation` | bootstrap, all wraps, self-correction, self-upgrade, safety, reversibility, cost | OK | none — fully exercised | none |
| 6 | **graceful-degradation** | `ClaudeClient` adapter, six per-mode FSMs, pause/resume hooks, notification | bootstrap; self-upgrade probes; self-correction triggers (indirect via orchestrator pause) | partial — runtime state machine exists; **`ClaudeClient` adapter is not the path most LLM calls use** (most LLM calls in pos-v2 are agent dispatches the persona issues, not in-process Anthropic SDK calls) | persona narrate degraded-mode entry/exit; surface paused-scope count to user | **A4**: agent-dispatch-via-ClaudeClient routing (composes with A2) |
| 7 | **observability-aggregator** | OTel SpanProcessor + JSONL tailer; DuckDB store; `QueryAPI.find_spans/replay_*`; NL path; `pos obs` CLI | bootstrap; self-correction polls `find_spans`; CLI | partial — ingest works, persona never queries | persona invoke `replay_session/replay_scope` on owner "why did you do X" / on every audit-shaped question | **A5**: persona "why did I" surface — wires NL path to a persona tool |
| 8 | **self-upgrade framework** | external CLI, manifest, fetch/snapshot/probe/swap, clause-by-clause checks | self-upgrade is its own CLI; bootstrap probes; safety-layer ask-list reads it | OK as built, but **never invoked in normal operation** — no upgrades have run | persona surface upgrade-availability checks on a cadence (cron) | none for v1 |
| 9 | **safety-layer** | KillEngine, AlwaysAskList, DangerousOpGate, IPC kill methods, ask-gate | bootstrap; reversibility imports `structural_hash`; activation-wrap installs | partial — gates fire on `activate_scope` + scopes are not being activated by persona dispatches; **KillEngine surfaces (`pos kill {scope|session|system}`) are persona-invisible** | persona must know how to halt own work; must know the always-ask list | **A6**: persona-owned safety surface (kill phrases + ask-list awareness rule) |
| 10 | **reversibility-primitive** | `register_compensation`, `rollback`, path-choice ranking, activation-gate wrap | bootstrap; self-correction registers compensation; self-upgrade rollback; pos-amend apply | partial — `register_compensation` only used by self-correction + self-upgrade + pos-amend; **`rank_alternatives` (path-choice telemetry) has no production caller at all** | persona invoke `rank_alternatives` when proposing 2-of-3 deliverables in the proposal-moment | **A7**: path-choice consumer in persona authoring pipeline |
| 11 | **cost-governance** | `CostController`, `CostLedger`, `register_cost_governance_ipc`, `cost.{status,scope,session,rolling,adjust_ceiling,list_adjustments}` IPCs, ceiling-warning emission | bootstrap (single import path), `self-correction/spec_builder.py` (passes through `Budget`) | **acute** — ceilings configured but no dispatch ever passes through the gate; agent dispatches don't open scopes; ceiling-warning emission has no production scope to fire on | persona declare a budget for every dispatch; treat cost.status as part of the morning-briefing surface | **A8** (highest leverage): agent-dispatch-as-scope wrapper — every Agent tool call lands as a `ScopeSpec` with declared budget and runs through the four-gate chain |
| 12 | **self-correction loop** | trigger queue, four-part protocol records, completion pre-check, IPC `correction.user_reported` / `report_review_verdict` | bootstrap; orchestrator emits to triggers via pyee; observability-aggregator polled by triggers | partial — triggers fire only when actual scopes fail in scope-of-work; without A2/A8 the persona's failures (a misclassified turn, a wrong agent dispatch) never produce a `CorrectionTrigger` | persona invoke `correction.user_reported` on every "that's not what I expected" capture rule | **A9**: wire persona's existing self-correction trait (prompt §"Self-correction") to the IPC method |
| 13 | **workspace-bootstrap** | host harness; declarative adapter list; phase-ordered contribution graph | hands-off-lifecycle hooks; main entry | OK | none | none |

---

## Top 3 highest-leverage gaps (asymmetric — biggest leverage / lowest cost)

1. **Cost gate is bypassed because agent dispatches aren't scopes (A8 / A2).** Eve dispatches an Agent every couple of turns; none of those dispatches construct a `ScopeSpec`, none get a budget, none flow through `activate_scope`, none touch the cost ledger. Effect: **all four sealed gates (safety, reversibility, cost, observability hooks) fire only on the one production caller that opens scopes — `self-correction/spec_builder.py`**. The harness's three Phase-3 components (safety, reversibility, cost) are sealed correctly but starved of input. Fix: a thin adapter that wraps every Agent dispatch issued from the main session into a `ScopeSpec` (objective, constraints, budget on time/tokens/money axes inferred from the dispatch + duration-estimation rubric, success criteria from the agent's halt-and-surface contract) and routes it through the existing four-gate chain. **Single highest-leverage move in the audit.**
2. **Persona is ignorant of the entire harness IPC surface (A6, A8, A9).** The persona prompt does not name `cost.status`, `pos kill`, `correction.user_reported`, `register_compensation`, `cost.adjust_ceiling`, or `replay_session`. The 6-trait + 8-rule prompt is good general AI behaviour but does not *teach the persona that pos-v2's harness exists*. Fix: add a §"Harness surfaces I draw from" block to `personas/primary/prompt.md` enumerating the IPC methods + when to invoke them (one-line each) — composes with the existing "Lean on the harness" rule, which currently has no concrete contents. This is a doc-edit-scale fix; effect is large because traits without specific verbs do not change behaviour.
3. **Memory-system / MCP dual-path divergence (A1).** The memory-system component built a FastAPI sidecar with retention/process-of-arrival/staging, but amendment #47-#48 routed the persona through `memory-graphiti` MCP. The sidecar still launches in bootstrap and the persona writes via MCP — two memory paths, one consumer. Either the sidecar needs a triage (deprecate? collapse?) or the MCP path needs to ingest into the sidecar. Risk of leaving as-is: the persona believes it is leveraging memory-system but is in fact using a different store, and "what's in memory" depends on which path someone reads from. Fix is a triage research, not a build — but it should land before any further memory-related amendment, because the next memory feature will need to know which substrate it composes onto.

---

## Decisions for owner ruling (genuinely uncertain)

Per confidence-delegation, only these need owner input:

**D1. Cost gate scope: agent dispatches?** Should the **agent-dispatch-as-scope** wrapper (A8) be the actual amendment direction, or does the owner want the cost gate to remain orchestrator-scoped only and a *separate* token-accounting layer cover Eve's dispatches? Audit recommends A8 — one gate, one chain — but a token-accounting-only path is simpler and keeps the gate uncontaminated by user-conversation-shape work.

**D2. Memory-system / MCP collapse direction.** Is the FastAPI sidecar's retention/POA/staging pipeline going to be re-pointed to live behind the MCP server (memory-graphiti becomes the API, sidecar becomes its retention engine), or is the sidecar going to be retired in favour of MCP-only? The audit cannot decide this — both are coherent designs.

**D3. Path-choice ranking — opt-in or default?** The reversibility primitive's `rank_alternatives` has no caller. Was that intentional (opt-in for workspaces that want it) or an unwired-consumer gap (the persona's proposal-moment in `prompt.md` should always rank its 2-3 deliverables)? Audit guess is that the latter is right — the proposal-moment is exactly the structural place to invoke ranking — but this is the kind of "intent that got built into a primitive without a consumer" that the foundation audit would flag and the owner should rule on.

---

## Body — full per-component analysis

### 1. memory-system

**Surface.** A FastAPI sidecar exposing memory operations; Pydantic schemas for episodes, entities, temporal records; retention runtime; Process-of-Arrival staging. Public package: `memory_system` with submodules `service`, `process_of_arrival`, `retention`, `temporal`, `staging`, `factory`, `ephemerality`.

**Production callers.** `workspace-bootstrap/adapters/memory_system.py` launches the sidecar via `python -m memory_system.service` and probes `/health`. `self-upgrade/probes.py` references the sidecar for upgrade probes. **No other production import** of `memory_system` exists. The persona consumes memory through `memory-graphiti` MCP (amendments #47-#48), not through `memory_system`.

**Gap.** **Dual-path divergence.** memory-system built itself; the persona was wired to a separate MCP server. The sidecar still boots; the persona reads/writes a *different* store. Tests for memory-system pass; tests for the persona's MCP path pass; nothing tests they agree.

**Persona fix.** Persona narration on memory writes should name which memory it is using ("writing to memory-graphiti" vs "writing to memory-system retention") — at least until the collapse lands. Right now memory writes are ambient and untraceable from the user's vantage point.

**Amendment.** **A1 — memory triage research.** A research-shaped doc at `docs/plans/research/memory-system-vs-mcp-triage.md` enumerating: which features each path has (POA/staging/retention/temporal vs vector-search/episode-add); which is the canonical path going forward; the migration shape if a collapse is required. Sequence: before any further memory-touching amendment.

### 2. scope-of-work primitive

**Surface.** `ScopeSpec` (Pydantic, requires `Budget` with at least one axis, requires `reversibility_class`, requires success criteria), `ScopeRuntime` (pyee emitter, `start/cancel/list`), state-transition events (`StateTransitioned`, `BudgetDebited`, `BudgetRefunded`), projection view, triggers.

**Production callers.** `cost-governance` (subscribes to `ScopeRuntime.emitter`, reads `ScopeSpec.budget`), `self-correction/spec_builder.py` (constructs `ScopeSpec`), `self-correction/triggers.py` (subscribes to emitter), `graceful-degradation/policy.py` (reads scope metadata for policy override), `primary-persona/monitor.py` (subscribes to runtime for awareness block), `primary-persona/authoring.py`, orchestrator (owns `ScopeRuntime`).

**Gap.** **Partial — `ScopeRuntime` is fully consumed; `ScopeSpec` constructor is consumed by exactly one production code path (`self-correction/spec_builder.py`).** Every other consumer reads scopes that already exist; nothing else creates them. The orchestrator's `activate_scope` runs only on scopes that something else built, and the only thing that builds them in production is self-correction. The implication: **the four-gate dispatch chain (safety/reversibility/cost/orchestrator) only ever fires on correction scopes**. Everything else — persona dispatches, agent invocations, scheduled work — runs outside the chain.

**Persona fix.** Persona must construct a `ScopeSpec` for every dispatched action — every agent call, every scheduled job, every background task — declaring the budget, the reversibility class, the success criteria. The persona's own §"ODD-shaped internal model" rule already says "objective + constraints + acceptance"; that internal model should externalise as a `ScopeSpec`.

**Amendment.** **A2 — agent-dispatch-as-scope wrapper.** A workspace-level helper that takes the persona's natural-language dispatch ("research X with budget Y, halt on Z") and constructs a `ScopeSpec` for it, registers it through `activate_scope`, and only then invokes the actual Agent tool. Composes with A8.

### 3. primary-persona layer

**Surface.** `PersonaContract` + loader + validator (per-workspace contract); `BackgroundWorkMonitor` (pyee subscriber → `AwarenessBlock` injected into UserPromptSubmit); `AuthoringPipeline` (creation-trigger → 4-step LLM pipeline → new-persona-directory); `IntroductionDispatcher` (one-on-one channel intro of new persona); `OneOnOneChannel` reusable by other components; `ComposedContextPayload` + `register_*` contributors (memory, tracker); session-start hook + stop emitter; `MCP memory client`; `retire_persona`.

**Production callers.** Orchestrator instantiates `BackgroundWorkMonitor`. Bootstrap wires session-start hook + memory contributor + tracker contributor. `graceful-degradation`, `cost-governance`, `self-correction` import `OneOnOneChannel` for their own notification. **`AuthoringPipeline` + `CreationTriggerDetector` + `IntroductionDispatcher` + `retire_persona` have no production caller** — only test-exercised.

**Gap.** **Partial — three of the layer's most ambitious surfaces (auto-authoring, introduction, retirement) are silent dead code in production.** The capability to author a new specialist persona on user signal exists; the capability to detect that signal in conversation does not run anywhere in the live persona loop. This is exactly the value-prop test failure: harness has the toolkit, persona never reaches for it.

**Persona fix.** Add a rule to `personas/primary/prompt.md`: *when the user names a recurring workflow that warrants a domain specialist (legal, finance, ops), invoke `CreationTriggerDetector` and propose the new persona before continuing*. Specific.

**Amendment.** **A3 — creation-trigger live-detection adapter.** A lightweight inner-hook that runs `CreationTriggerDetector` over the most recent N user turns at session-start (or on user-prompt-submit) and surfaces a `TriggerSignal` block in the persona's awareness stream when a trigger fires. Currently only the unit tests exercise the detector.

### 4. objective-tracker

**Surface.** Objective registry (Pydantic objective records), scope-binding API (`bind_scope`), projection-view query, `trace_to_root`, ObjectiveFilter.

**Production callers.** Orchestrator's `activate_scope` calls `bind_scope`. `tools/heavy-b-migrate` and `tools/pos-amend` use it for component/amendment AC tracking. `primary-persona/tracker_context.py` (amendment #40) contributes "in-flight objectives" to the persona's session-start payload. Bootstrap seeds tracker.

**Gap.** OK — the tracker's main surfaces are wired. The `tracker_context` contributor surfaces in-flight objectives at session-start, which is exactly the persona-leverage shape Lens 2 wants.

**Persona fix.** Persona should narrate which objective each dispatch ladders up to (it has the data; it doesn't yet narrate the linkage). One-line per dispatch.

**Amendment.** None.

### 5. session-resilient orchestrator

**Surface.** `Orchestrator` (asyncio main loop, heartbeat, pause/resume, request_stop), `IPCServer` (handler registration + JSON-RPC), `activate_scope` IPC, dispatch sequence.

**Production callers.** Bootstrap launches; cost-governance, reversibility-primitive, safety-layer, self-correction, self-upgrade all import `pos_orchestrator` and register handlers / wraps. orchestrator/scripts/install_launchd.py for daemonisation.

**Gap.** OK — fully wired. This is the central piece every other component composes onto.

**Persona fix.** None.

**Amendment.** None.

### 6. graceful-degradation

**Surface.** `ClaudeClient` adapter (wraps Anthropic SDK calls; observes typed exceptions + `retry-after` headers); six per-mode FSMs; pause/resume hooks consuming orchestrator's `pause_activation`/`resume_activation`; compound-OR notification threshold; deterministic safe-mode narrative for full-outage case; SQLite at `~/.pos/degradation.sqlite`; reconcile-on-restart.

**Production callers.** Bootstrap installs adapter. `self-upgrade/probes.py` reads degradation state for upgrade go/no-go. `self-correction/triggers.py` may receive pause notifications (indirect).

**Gap.** **Partial — the FSM runtime is wired but the `ClaudeClient` adapter only observes LLM calls that go through the in-process Anthropic SDK.** The vast majority of LLM activity in pos-v2 is the persona dispatching Agent tools (Claude Code → Anthropic) — those calls do **not** go through pos-v2's `ClaudeClient` adapter, because pos-v2 doesn't see them. This is the same shape as the cost gap: the gate exists, but the dominant traffic doesn't traverse it.

**Persona fix.** Persona narrate degraded-mode entry/exit; surface paused-scope count to user. ("Degraded mode active — three scopes paused, retry-after 45s.")

**Amendment.** **A4 — agent-dispatch-via-ClaudeClient routing.** Compose with A2: when the persona dispatches an Agent, the dispatch wrapper (A2) also pipes the inferred LLM call shape through `ClaudeClient` for failure-mode tracking. (May need a different transport — observation-only — since pos-v2 doesn't *make* the call, Claude Code does. Possibly a 429/529-observation post-hook on the agent's return.)

### 7. observability-aggregator

**Surface.** Custom `SpanProcessor` + `SpanExporter` registered via bootstrap; JSONL tailer for memory-system; DuckDB store with normalised schema; `QueryAPI.find_spans/get_trace/cost_by_prompt/replay_session/replay_scope/replay_objective`; NL path (two-LLM-call) for "why did you do X at time T"; `pos obs` CLI; three-tier retention with v1.1 R10 retention-class honoured.

**Production callers.** Bootstrap registers processor. `self-correction/triggers.py` polls `find_spans(SpanFilter(status="ERROR", retention_class="high"))`. `pos obs` CLI exposes the API to the user.

**Gap.** **Partial — ingest is full-fidelity; query surface has exactly one consumer.** The proposal explicitly named "primary persona's 'show me why'" as the integration target (proposal §"Integration with primary-persona's 'show me why'"). That integration was never wired. The persona never queries observability for its own reflection, never replays a scope or session, never runs the NL path.

**Persona fix.** When the user asks "why did you do X" or "show me what happened with Y", the persona should call `replay_scope` / `replay_session` / NL path. Make this part of the prompt: *"audit-shaped questions go through observability-aggregator's NL path before I answer from inference."*

**Amendment.** **A5 — persona "why did I" surface.** A persona-callable tool exposed to the persona as something like `pos_obs_explain(question)` that wraps the NL path. Composes with the persona's §"Test theories before acting on them" rule — the rule's evidentiary substrate exists; it just hasn't been wired in.

### 8. self-upgrade framework

**Surface.** External CLI; release-tag + manifest; fetch / pre-snapshot / pre-probe / pause / drain / SIGTERM / symlink-swap / launchctl restart / post-probe / sha-verify; clause-by-clause checks (a–g); whole-upgrade atomic rollback; framework-owned aggregator probe set.

**Production callers.** Self-upgrade is its own CLI invoked externally. Bootstrap probes; safety-layer ask-list reads the upgrade-availability surface.

**Gap.** OK as built — the component is correctly self-contained as an external CLI per the proposal. **However: in normal operation, no upgrades have ever run.** The component is dormant by design (you don't upgrade weekly), but its existence is also persona-invisible — the persona never surfaces "an upgrade is available" or "the system is X versions behind."

**Persona fix.** Persona surface upgrade-availability checks on a cadence (cron); narrate when an upgrade is pending. Lens-2 test: this is what reduces translation burden — the user shouldn't have to remember to run `pos self-upgrade check`.

**Amendment.** None for v1; possibly a cron-routine that pings `self-upgrade check` daily and feeds the result into the persona's awareness block.

### 9. safety-layer

**Surface.** `KillEngine` (scope/session/system kills with bounded time budgets), `AlwaysAskList` (Pydantic-validated YAML at `<workspace>/.pos/safety/always_ask.yaml`), `DangerousOpGate`, IPC methods (`kill_scope`, `kill_session`, `kill_system`, `ask_gate_decide`, `safety_status`), activation-wrap, SQLite at `~/.pos/safety/safety.sqlite`.

**Production callers.** Bootstrap registers wrap + IPC. `reversibility-primitive/__init__.py` and `activation_gate.py` import `safety_layer.events.structural_hash` for spec-hash equivalence with safety. cost-governance composition test verifies wrap order.

**Gap.** **Partial — gates fire correctly when scopes activate, but the dominant work-shape (persona conversation + agent dispatch) doesn't activate scopes (see A2/A8). KillEngine surfaces are persona-invisible.** The persona prompt does not name `pos kill scope`, `pos kill session`, or `pos kill system`. The user can't tell the persona "kill that" and have it land structurally — the persona has no awareness of the surface. The always-ask list exists at `<workspace>/.pos/safety/always_ask.yaml` but the persona doesn't read it on every turn to decide whether the requested action is in the ask-list.

**Persona fix.** Add to prompt: *"Halt phrases I respect: 'halt scope X', 'halt session', 'kill system' — these route to KillEngine. Always-ask list at `<workspace>/.pos/safety/always_ask.yaml` — I read it before any external action and pause for explicit approval if the action matches."*

**Amendment.** **A6 — persona-owned safety surface**. (1) Add the always-ask read to the persona's session-start contributor (mirror the tracker-context shape); (2) add halt-phrase recognition to the persona's prompt; (3) consider adding a "kill" verb to the persona's awareness-block contract so the user's halt requests get a deterministic structural path, not a "trust the LLM to invoke the right tool" path.

### 10. reversibility-primitive

**Surface.** `register_compensation` IPC; `rollback` IPC + four-state FSM with idempotency; activation-gate wrap (refuses `compensatable` without binding, refuses `irreversible` without safety approval); cascade-trigger via pyee on child failure; `rank_alternatives(alternatives) -> RankedAlternatives` with `pos.reversibility.path_chosen` span emission and `downrank_warning` flag; SQLite at `~/.pos/reversibility/reversibility.sqlite`.

**Production callers.** Bootstrap. `self-correction/controller.py` registers compensation handlers for correction scopes. `self-upgrade` registers compensation for upgrade rollback. `tools/pos-amend/commands/apply.py` registers compensation for amendment apply. **`rank_alternatives` has zero production callers.**

**Gap.** **Partial — compensation registration is consumed by three callers; path-choice ranking is unused entirely.** The proposal called out path-choice as a first-class concern (proposal §1, last bullet). The persona's proposal-moment in `prompt.md` (§"Proposal moment") explicitly produces 2-3 alternative deliverables — that is exactly the moment `rank_alternatives` should fire, but the prompt-rule doesn't reach for it.

**Persona fix.** Add to §"Proposal moment": *"When I offer 2-3 deliverables, I rank them via reversibility-primitive's `rank_alternatives` and surface the choice + reason inline. If a less-reversible option ranks higher than a more-reversible alternative, the `downrank_warning` flag fires and I surface the trade-off explicitly to the user."*

**Amendment.** **A7 — path-choice consumer in persona authoring pipeline.** A workspace tool (or skill) the persona can invoke that takes 2-3 candidate `ScopeSpec` shapes and returns the ranked set with downrank-warning context. Wires the existing primitive to its intended consumer.

### 11. cost-governance — Luke's specific focus

**Surface.** `CostController.build()` (composes ledger + store + notifier + scope_runtime); `CostLedger` (subscribes to `ScopeRuntime.emitter` for `BudgetDebited`/`BudgetRefunded`/`StateTransitioned`; reserves at activation; refuses with `-32060/-32061/-32062`; emits `pos.cost.ceiling_warning` at 80% threshold by default); `CostStore` (SQLite at `~/.pos/cost/cost.sqlite`; reservations, session_rollups, rolling_rollups, ceiling_adjustments tables); `CostConfig` (YAML at `~/.pos/cost/ceilings.yaml`; per-axis session ceilings + rolling-window list); `RollupTask` (interval-closure scheduler); IPC methods: `cost.status`, `cost.scope`, `cost.session`, `cost.rolling`, `cost.adjust_ceiling`, `cost.list_adjustments`; CLI: `pos cost {status,scope,session,rolling,adjust}`; activation-wrap registered as innermost.

**Production callers — verified.** Exactly two:
1. `workspace-bootstrap/adapters/cost_governance.py` — instantiates `CostStore`, `CostConfig`, `CostNotifier`, `CostController.build(...)`, calls `register_cost_governance_ipc(server, ledger, spec_resolver)`. **Wires correctly per proposal §3.2 + integration test.**
2. `self-correction/spec_builder.py` — constructs `Budget` and `ScopeSpec` for correction scopes. These do flow through the cost gate.

**No other production caller constructs a `Budget` or a `ScopeSpec`.** Therefore no other production code path reaches the cost gate.

**Gap class.** **Acute — built, structurally correct, integration-tested, but starved of input.** Cost-governance does the right thing when a scope reaches `activate_scope` with a declared budget. The dominant work the persona does (conversation, agent dispatch, file reads) **does not** reach `activate_scope` because nothing wraps it as a scope. Therefore:

- Per-scope budgets: declared only on correction scopes.
- Session ceilings: configured but never debited because no scope is debiting.
- Monthly / rolling ceilings: empty rollups.
- Automatic throttling at 80%: cannot fire — there's nothing to throttle.
- Ceiling-warning emission (`pos.cost.ceiling_warning`): zero production fires.
- `cost.adjust_ceiling` IPC: zero production callers.
- `cost.status` IPC: zero production callers (the persona never queries cost).

Luke's intuition was right: **the budgeting infrastructure was built and never drawn from**. The component itself is correctly designed; the consumer that should feed it doesn't exist.

**Persona fix.** Two layers:
1. **Per-dispatch budget declaration.** Every agent dispatch the persona issues should carry a `Budget` declaration (time_seconds + tokens). The persona's §"ODD-shaped internal model" rule already says objective + constraints + acceptance; budget is part of constraints.
2. **Cost-status as part of awareness.** Add `cost.status` to the session-start contributors (alongside memory + tracker-context). The persona reads aggregate spend at session-start and narrates it when relevant ("we're at 60% of today's token ceiling — flagging because three open dispatches will likely cross 80%").

**Amendment.** **A8 — agent-dispatch-as-scope wrapper.** This is the highest-leverage amendment in the audit. A small adapter that:
- Takes the persona's natural-language dispatch (objective, constraints, halt conditions, expected duration).
- Builds a `ScopeSpec` with `Budget(time_seconds=..., tokens=..., money_cents=...)` inferred from the duration-estimation rubric (already in MEMORY.md — `feedback_duration_estimation_rubric`).
- Calls `activate_scope` on the orchestrator's IPC.
- The four-gate chain (safety / reversibility / cost / orchestrator) fires.
- On approval, the actual Agent tool is invoked.
- On `BudgetDebited`/`BudgetRefunded` events, cost ledger updates aggregate.
- On scope close, reservation reconciles.

This single amendment turns cost-governance, safety-layer, reversibility-primitive, observability-aggregator, and self-correction from "wired but starved" into "wired and exercised on every turn." It is the **one amendment** that closes Luke's complaint structurally.

Sequence: after D1 (cost gate scope ruling) — owner needs to confirm A8 is the right shape vs a simpler token-accounting-only path.

### 12. self-correction loop

**Surface.** Four detection surfaces (scope_failure / otel_anomaly / review_verdict / user_reported); typed `CorrectionTrigger`; `CorrectionEpisode`; four-part-protocol records (`FailureClassIdentified`, `InstanceFixed`, `CauseDiagnosed`, `StructuralRemedyApplied`); deterministic `build_correction_spec` (reversibility forced compensatable; budget inherited-and-scaled with floors); compensation registration via reversibility's IPC; pyee completion pre-check; IPC methods: `correction.report_review_verdict`, `correction.user_reported`, `correction.status`; CLI; SQLite.

**Production callers.** Bootstrap. orchestrator emits `StateTransitioned` events that triggers subscribe to. observability-aggregator polled by triggers' OTel-anomaly path.

**Gap.** **Partial — the four detection surfaces are correctly wired but most fire only on already-existing scopes (which only self-correction creates).** `correction.user_reported` IPC is unconsumed — the persona prompt has a §"Self-correction" trait that says *"every 'that's not what I expected' gets the capture-or-fix treatment"* but the trait doesn't invoke `correction.user_reported`. The trait writes to `FUTURE_IDEAS_DRAFT.md` instead. Two failure-capture mechanisms, no overlap.

**Persona fix.** Wire the §"Self-correction" trait to the IPC method: capture in FUTURE_IDEAS_DRAFT.md *and* fire `correction.user_reported(description, related_scope_id?)` so the harness actually opens a correction scope.

**Amendment.** **A9 — wire persona self-correction to correction IPC.** A one-line adapter the persona invokes when its capture-or-fix rule fires. Composes with A2/A8: when persona dispatches go through scopes, scope-failure detection covers most cases automatically; user_reported covers everything else.

### 13. workspace-bootstrap

**Surface.** Phase-ordered adapter contribution graph; declarative `BaseContribution` registration; per-phase ordering constraints (`after`); host harness (`host.require`, `host.register_shutdown`, `host.channel_registry`); CLI `pos bootstrap`.

**Production callers.** `hands-off-lifecycle/hooks/first_run_helper.py`, `hands-off-lifecycle/hooks/first_run_scaffold_runner.py`, `workspace-bootstrap/main.py`.

**Gap.** OK — bootstrap is exactly what it needs to be: the wiring point for everything else. Its surface is fully consumed by adapters of every other sealed component.

**Persona fix.** None.

**Amendment.** None.

---

## Cross-cutting observations

### Observation 1 — the "wired but starved" pattern

Five components share the same shape: **structurally wired into the dispatch chain, IPC handlers registered, but no production caller upstream produces the input shape they need**. Cost (no scopes activated), safety (kill engine never invoked from persona), reversibility (`rank_alternatives` never called), observability (`replay_*` never called), self-correction (`user_reported` never called).

This is the inverse of what the foundation audit looked for. The foundation audit found ODD §2.5 violations — code paths without acceptance criteria. This audit found the opposite — **acceptance criteria with no caller**. The components satisfy their own ODD; nothing else satisfies *the implied ODD that the harness-as-toolkit would need to be drawn from*.

The fix is at the persona/dispatch layer, not in any of the five components themselves. **A8 (agent-dispatch-as-scope) plus persona-prompt amendments closing the IPC-method awareness gap closes most of the cross-cutting damage in one move.**

### Observation 2 — the persona prompt is general, not pos-v2-specific

`personas/primary/prompt.md` is high-quality general AI behaviour (6 traits + 8 rules per the latest version). It does not name a single pos-v2 IPC method, sealed component, or harness surface. The §"Lean on the harness" rule says "Claude Code / hook / MCP / skill / plugin / scheduled-routine primitive" — Claude-side capabilities, not pos-v2-side capabilities.

This is not a critique of the prompt's quality — the prompt is good as-is for any Claude-attached chief-of-staff. It is a critique of the prompt's *specificity to this harness*. The harness has thirteen sealed components; the prompt names zero of them.

Fix: a §"pos-v2 surfaces I draw from" block, mirroring §"Top-value traits" in shape, that names each surface in one line + when to use it. ~30 lines. Doc-edit-scale fix; closes most of the awareness gap.

### Observation 3 — `IntroductionDispatcher` and `retire_persona` are pure orphan code

Two surfaces in primary-persona-layer have **no production caller and no path to one**: `IntroductionDispatcher` (only invoked by `AuthoringPipeline` — itself uncalled in production) and `retire_persona` (no caller anywhere outside tests).

Per ODD §2.5, "code paths without an AC are a violation." These are AC-backed (the persona-layer proposal § creation-trigger and § retirement both authored ACs against them) but the AC-backed callers are themselves not wired into the live persona loop. This is one removed level from a §2.5 violation — the surfaces are correct, the consumers exist in test fixtures, the *production wiring* is the gap.

This belongs in A3 (creation-trigger live-detection adapter) — the consumer wiring. Same fix shape.

---

## Halt conditions

None of the four halt conditions in the dispatch fire. Specifically:

- **No component is severely under-built relative to its proposal.** Each of the 13 satisfies its own ACs — the ODD is internally clean. The audit's findings are about wiring to consumers, not about gaps inside the components.
- **No ODD §2.5 violation surfaces.** The "orphan surfaces" in primary-persona-layer (IntroductionDispatcher, retire_persona, AuthoringPipeline) are AC-backed; their production wiring is missing. That's a one-removed shape, not a §2.5 violation in the components themselves.
- **No required new top-level objective surfaces.** The amendments named (A1–A9) are all consumer-wiring amendments that ladder up to the existing prime objective (VALUE_PROPOSITION's two tests). None reshapes the value-prop.
- **No systemic value-prop break needing strategic ruling.** The value-prop is correct; the consumer layer is incomplete. That's a tactical gap, not a strategic one. The three decisions (D1, D2, D3) are owner-ruling-shape but not value-prop-reshaping.

---

## Sequencing recommendation (asymmetric — biggest leverage / lowest cost)

If only one thing happens: **persona-prompt amendment naming the harness surfaces** (cost ≈ 60 lines of prompt; effect: persona stops being ignorant of the toolkit it has).

If two things happen: persona-prompt amendment + **A8 (agent-dispatch-as-scope)** (cost: a small dispatch wrapper; effect: every turn exercises the four-gate chain and feeds cost/safety/reversibility/observability/self-correction — closes most of the cross-cutting damage).

If three things happen: + **A1 (memory triage)** (cost: a research doc; effect: collapses the memory-system-vs-MCP divergence before the next memory amendment compounds the gap).

Everything else (A3, A4, A5, A6, A7, A9) is incremental on top of those three.
