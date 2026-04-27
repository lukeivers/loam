# Primary-persona layer — relationship map

The primary-persona layer does not stand alone. This map names every
adjacent pOS component it talks to, the direction of the dependency,
and the nature of the coupling.

## Hard dependencies (this layer imports them)

### scope-of-work primitive

The monitor subscribes to scope-of-work's pyee emitter and polls
`runtime.list(...)` for every awareness-block build. It also reads
`runtime.list(stuck=True)` from the D0 amendment to surface stuck
scopes deterministically. The authoring pipeline runs inside a
scope-of-work scope (caller-supplied `authoring_scope_id`) and
debits per-LLM-call tokens + money against that scope so the per-
prompt cost view (v1.1 R12) aggregates authoring costs alongside
every other scope's costs.

Interface:
- `ScopeRuntime.subscribe_all(callback)` — monitor's pyee listener
- `ScopeRuntime.list(states=, include_pending_extension=, stuck=, ...)` — all awareness/compaction queries
- `ScopeRuntime.debit(scope_id, input_tokens=, output_tokens=, money_cents=, prompt_name=, model=)` — authoring cost tracking

### memory-system (soft coupling — via callable)

The compaction-survival payload includes "recent corrections" from
memory. This layer does **not** import the memory-system directly;
instead, the caller supplies a `RecentCorrectionsProvider` callable.
This keeps the layer swappable and the dependency loose. If the
caller omits the provider, the recent-corrections field is empty —
the layer degrades gracefully.

## Soft dependencies (they consume our emissions)

### observability aggregator

Every operation emits OTel spans and events. When an observability
aggregator component is built, it subscribes to those emissions.
Until then, emission succeeds silently with no consumer (A1
correction).

Emitted spans:
- `pos.persona.loader`
- `pos.persona.monitor.snapshot`
- `pos.persona.monitor.tick`
- `pos.persona.authoring`
- `pos.persona.authoring.{style_harvest,domain_research,contract_synthesis,self_review}`
- `pos.persona.introduction`
- `pos.persona.retirement`

Emitted events:
- `pos.persona.monitor.tick` (per tick, with category counts)
- `pos.persona.monitor.inject` (per UserPromptSubmit)
- `pos.persona.authoring.self_review` (per iteration, with verdict)
- `pos.persona.introduction.dispatched`
- `pos.persona.retired`

### safety layer (future)

The safety layer consumes `authority_boundary` declarations from
persona contracts. When a persona attempts an action, the safety
layer reads `contract.authority_boundary.action_for(tier)` to
decide whether to gate the action. This layer does not call the
safety layer; the safety layer reads the contract via the loader
and gates on its own schedule.

### cost governance (exists in scope-of-work)

The authoring pipeline's cost tracking is inherited from scope-of-
work's budget enforcement — no per-layer coordination required.
Per-prompt aggregation (v1.1 R12) via
`runtime.per_prompt_costs()` shows authoring costs attributed to
`style_harvest`, `domain_research`, `contract_synthesis`,
`self_review_iter_N`.

### self-correction loop (future)

When a self-correction loop component is built, it will subscribe
to `pos.persona.authoring.self_review` events where the verdict was
"failed" — the rejection signal is the material the correction
loop learns from. The current layer records the events; no direct
wire is required.

### channel-agnostic-interaction (future)

The introduction protocol takes `OneOnOneChannel` objects whose
`send` callable is the transport. When the channel-agnostic-
interaction component lands, it supplies the concrete channels
(terminal, Claude desktop, personal Telegram). Until then, the
caller wires whatever transport they have.

## Forbidden dependencies

- **Current-pOS / ivers-corp machinery** — no reading of the current
  `.claude/hooks/compaction-resilience.rb`, `.claude/agents/*`, or
  any existing Ruby persona files. Clean-slate design.
- **Any runtime library beyond stdlib + pydantic + pyee +
  opentelemetry-api/sdk + PyYAML** — requires halt-and-signal per
  STATE.md rule 8.
- **pOS-shipped persona content** — the loader's `_check_no_personas_in_core`
  will raise `PersonaInCoreError` if a `contract.yaml` appears in a
  pOS-core path (brief constraint 6, v1.0 primary-persona criterion).

## Surface area of the layer

The layer's public API (what downstream code imports) is deliberately
small:

```
from primary_persona import (
    # D1
    PersonaContract, load_contract, AuthorityBoundary, TierAction,
    # D2
    PersonaLoader, LoadedPersona,
    PersonaDirectoryNotFoundError, PersonaValidationError, PersonaInCoreError,
    # D3
    BackgroundWorkMonitor, AwarenessBlock, AwarenessCategory,
    # D4
    CompactionSurvivor, SURVIVAL_LIST,
    # D5
    CreationTriggerDetector, TriggerSignal, CreationTrigger,
    # D6
    AuthoringPipeline, AuthoringResult, AuthoringOutcome, LLMCallable,
    # D7
    IntroductionDispatcher, OneOnOneChannel, IntroductionOutcome,
    # D8
    retire_persona, RetirementReason,
)
```

Everything else is internal. A reviewer looking for the exact API
shape can read `src/__init__.py`.
