# Data flow — a representative scope lifecycle

Walks through one scope from creation to completion, hitting all the
interesting paths: an LLM call with token debit, a budget threshold
near-miss, an extension request, an extension grant, and a final
escalation.

## Scenario

The user (via the workspace's primary persona) asks Eve to research
"who introduced Aldermere clients to Nordic partners" using the
synthetic Aldermere world from `memory-system/data/scenario_world.md`.
Eve creates a research scope under her own session scope.

## Step-by-step

```
T0  Caller: rt.create(spec, parent_scope_id=session_scope.id)
    spec.budget = Budget(tokens=10_000, money_cents=200, time_seconds=900)
    spec.escalation_triggers = (
        BudgetThreshold(axis=tokens, threshold=2_000),  # warn near limit
        TimeElapsed(seconds=600),                       # 10 min cap
    )
    └─→ ScopeRuntime
        ├─ append: ScopeCreated(...)
        ├─ append: ChildLinked(scope_id=session, child=research)
        ├─ project: research.state = proposed
        └─ pyee.emit("scope:research", ScopeCreated)

T1  Caller: rt.start(research.id)
    └─→ ScopeRuntime
        ├─ start_invoke_scope_span(research)  # OTel
        ├─ append: StateTransitioned(proposed → active)
        ├─ project: research.state = active, active_started_at = T1
        ├─ pyee.emit("scope:research", StateTransitioned)
        └─ trigger eval (no fires; budget full, no time elapsed)

T2  Caller: (memory.search("Aldermere Nordic partners", scope_id=research.id))
    Memory does its work; calls Graphiti, which calls Anthropic.
    Memory reports back: input_tokens=120, output_tokens=80, prompt=ner.

T3  Caller: rt.debit(research.id, input_tokens=120, output_tokens=80,
                     prompt_name='ner', model='claude-haiku-4-5',
                     call_id='call-001')
    └─→ ScopeRuntime
        ├─ append: BudgetDebited(...)
        ├─ emit_chat_span(model='claude-haiku-4-5', ...)  # OTel
        ├─ pyee.emit("scope:research", BudgetDebited)
        ├─ project: tokens_consumed = 200 (from 0)
        ├─ trigger eval: BudgetThreshold(2000) — remaining 9800 > 2000, no fire
        └─ enforce exhaustion: remaining > 0, no action

T4  Caller: rt.debit(research.id, input_tokens=4_000, output_tokens=4_000,
                     prompt_name='extract_facts', call_id='call-002')
    └─→ ScopeRuntime
        ├─ append: BudgetDebited(...)
        ├─ project: tokens_consumed = 8200, remaining = 1800
        ├─ trigger eval: BudgetThreshold(2000) — remaining 1800 < 2000 → FIRE
        │   ├─ append: TriggerFired(trigger_id='warn-tokens', value={remaining: 1800})
        │   ├─ pyee.emit("scope:research", TriggerFired)
        │   ├─ append: StateTransitioned(active → escalated)
        │   └─ project: state = escalated
        └─ (debit returns; caller sees state == escalated)

T5  Eve (observing on pyee) receives the escalation. She decides the
    research is worth more budget; resumes by transitioning back to
    active and granting an extension on tokens.

    Caller: rt.resume(research.id)
            rt.extend(research.id, BudgetAxis.tokens, 5_000)

T6  Caller: rt.debit(... another 800 tokens, call-003)
    └─→ tokens_consumed = 9000, remaining = (10000 + 5000) - 9000 = 6000

T7  Caller: rt.evaluate_success_criterion(
              research.id, criterion_id='answers_question',
              result='met', note='Klemen Doric introduced Sondre Bråten')
    └─→ append: SuccessCriterionEvaluated(criterion_id='answers_question', met)

T8  Caller: rt.complete(research.id)
    └─→ ScopeRuntime
        ├─ append: StateTransitioned(active → completed)
        ├─ project: state = completed, active_cumulative_seconds = T8 - T1
        ├─ set_span_attrs: pos.scope.budget.tokens.remaining = 6000,
                           pos.scope.success_criteria.met = 1
        ├─ end_span(invoke_scope)
        └─ pyee.emit("scope:research", StateTransitioned)
```

## Compact event log for this scenario

| event_id | scope_id | kind | payload (relevant fields) |
|---:|---|---|---|
| 1 | research | scope_created | seven-field spec persisted |
| 2 | session | child_linked | child_scope_id = research |
| 3 | research | state_transitioned | proposed → active |
| 4 | research | budget_debited | call-001, in=120, out=80, prompt=ner |
| 5 | research | budget_debited | call-002, in=4000, out=4000, prompt=extract_facts |
| 6 | research | trigger_fired | trigger=warn-tokens, value={remaining: 1800} |
| 7 | research | state_transitioned | active → escalated |
| 8 | research | state_transitioned | escalated → active (Eve's resume) |
| 9 | research | budget_extended | axis=tokens, amount=5000 |
| 10 | research | budget_debited | call-003, in=400, out=400 |
| 11 | research | success_criterion_evaluated | answers_question = met |
| 12 | research | state_transitioned | active → completed |

## Extension-request path (the alternative arc at T4)

If Eve had configured `tokens_policy=request_extension` on the budget
(the default) **without** the BudgetThreshold trigger, the same
exhaustion at T4 would unfold differently:

```
T4  rt.debit(...)
    └─→ ScopeRuntime
        ├─ append: BudgetDebited(...)
        ├─ project: tokens_consumed = 8200, remaining = 1800 (still > 0)
        └─ no exhaustion (tokens still positive)

T4' Caller: rt.debit(... another 2_000)
    └─→ ScopeRuntime
        ├─ append: BudgetDebited(...)
        ├─ project: tokens_consumed = 10200, remaining = -200
        ├─ trigger eval: no triggers fire
        └─ enforce_budget_exhaustion:
            ├─ append: ExtensionRequested(axis=tokens, remaining=-200, cap=10000)
            ├─ pyee.emit("scope:research", ExtensionRequested)
            ├─ write data/pending_extensions/research.json (human-readable)
            └─ append: StateTransitioned(active → paused, pause_reason=
                       'pending_extension_request:tokens')
```

Eve then either:
- `rt.extend(research, BudgetAxis.tokens, 5_000)` — resumes the scope
  with fresh budget; the pending-extension file is removed.
- `rt.reject(research)` — appends ExtensionRejected, transitions the
  scope to either `completed` (if any success criterion was met) or
  `cancelled` (if none).

## The cross-process variant

If the research scope is dispatched to a long-running background
worker process (a future cross-process scenario), every event above
appears in the same `scope_events` table. The worker process polls
`events_since(last_seen_id)` on a 250 ms cadence and fans the events
into its own pyee emitter. The latency of "parent cancels → child
sees cancel" is bounded by the poll interval. Tuning that interval is
the prototype concern called out in the proposal §6 surprise list;
the code path is the same.
