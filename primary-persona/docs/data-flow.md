# Primary-persona layer — representative data flow

## End-to-end walkthrough: session start to retirement

The diagram below traces one complete lifecycle: session begins, a
gap emerges in the persona roster, a new persona is authored and
introduced, the user acknowledges, and eventually retires them.

```
Session start
 │
 ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. PersonaLoader.load()                                      │
│    - reads <workspace>/personas/                             │
│    - parses each contract.yaml                               │
│    - validates against Pydantic PersonaContract              │
│    - confirms prompt.md present                              │
│    - emits OTel span: pos.persona.loader (outcome="loaded")  │
│    - returns [LoadedPersona, ...]                            │
└──────────────────────────────────────────────────────────────┘
 │
 ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. BackgroundWorkMonitor.start()                             │
│    - subscribes to scope-of-work pyee "*" channel            │
│    - launches asyncio.create_task(tick_loop)                 │
│    - ticks every 30s; each tick queries runtime.list(...)    │
│      for counts per category, optionally runs stuck-reason   │
│      second pass for ≤ stuck_reason_budget scopes.           │
└──────────────────────────────────────────────────────────────┘
 │
 ▼
Per UserPromptSubmit:
 │
 ├── is PreCompact flag present?
 │     ├── yes → consume_survival_payload(...)                 (D4)
 │     │       - reads contract for identity + authority
 │     │       - reads runtime.list() for scope context
 │     │       - reads runtime.list(include_pending_extension=True)
 │     │       - reads memory via provider callback
 │     │       - clears flag
 │     │       - returns CompactionSurvivor (5 items)
 │     └── no → skip
 │
 └── monitor.on_user_prompt(turn_id)
         - builds AwarenessBlock from runtime.list()
         - categories: active / pending_decision / stuck /
           recently_finished / escalated / failed
         - 5 rows per category max
         - trims from low-priority categories if > 1k tokens
         - emits OTel event: pos.persona.monitor.inject
         - returns AwarenessBlock.to_json() inserted into context
```

## Authoring trigger + pipeline flow

```
Observation stream feeds the detector:
 │
 ├── user said "that's not quite right" on a task in domain X
 │        └── CreationTrigger(signal=request_decline, domain=X)
 │
 ├── user corrected primary persona's handling of X
 │        └── CreationTrigger(signal=domain_correction, domain=X)
 │
 ├── a scope kept referencing domain X
 │        └── CreationTrigger(signal=cross_domain_scope, domain=X)
 │
 ├── memory retrieval kept returning X-peripheral matches
 │        └── CreationTrigger(signal=low_relevance_memory_hit, domain=X)
 │
 └── user literally said "wish I had someone for X"
          └── CreationTrigger(signal=explicit_user_mention, domain=X)

 After each observation:
 ▼
 detector.evaluate(signal, domain)
   │
   ├── if count-in-window < min_count → None (nothing to do)
   │
   └── else → judgment_fn(signal, domain, recent_triggers)
              (Claude-via-Max call inside a budgeted
               scope-of-work — "should we author?")
              │
              ├── yes    → pipeline.author(...)
              │
              ├── no     → record rejection; stop
              │
              └── defer  → set _defer_until[key]; re-evaluate later

If yes:
 ▼
┌──────────────────────────────────────────────────────────────┐
│ AuthoringPipeline.author(...)                                │
│                                                              │
│ Root span: pos.persona.authoring (signal attr)               │
│                                                              │
│ Step 1: style_harvest                                        │
│   - LLM reads existing personas for voice consistency        │
│   - Emits pos.persona.authoring.style_harvest span           │
│   - Debits tokens against authoring_scope_id                 │
│                                                              │
│ Step 2: domain_research                                      │
│   - LLM describes practitioner attention + failure modes     │
│   - Emits pos.persona.authoring.domain_research span         │
│                                                              │
│ Step 3: contract_synthesis                                   │
│   - LLM returns two-part payload:                            │
│      1. JSON matching the Pydantic contract schema           │
│      2. "---PROMPT---" delimiter                             │
│      3. prompt.md prose                                      │
│   - Pipeline parses + validates; force                       │
│     pending_introduction=True, is_addressable=False.         │
│                                                              │
│ Step 4: self_review (up to 2 iterations)                     │
│   - LLM judges four dimensions:                              │
│      - voice_distinctiveness ("not generic" test)            │
│      - scope_fit                                             │
│      - redundancy (vs existing home_persona_for)             │
│      - contract_correctness                                  │
│   - Emits pos.persona.authoring.self_review event            │
│     per iteration.                                           │
│   - On pass → persist to disk.                               │
│   - On 3rd failure → AuthoringOutcome.rejected_after_retries │
└──────────────────────────────────────────────────────────────┘
 │
 On persisted outcome:
 ▼
┌──────────────────────────────────────────────────────────────┐
│ IntroductionDispatcher.introduce(new_persona, ...)           │
│                                                              │
│ - Renders the introduction text (name, domain, trigger,      │
│   retire instructions)                                       │
│ - Selects the first active OneOnOneChannel                   │
│   (is_group=True is rejected at construction by the          │
│    dataclass + at __post_init__ by the dispatcher)           │
│ - If no active channel → queue the payload; fires on         │
│   next flush_queue() call.                                   │
│ - On delivery: emits OTel event                              │
│   pos.persona.introduction.dispatched                        │
└──────────────────────────────────────────────────────────────┘
 │
 ▼
 Before any message identifying the new persona as sender:
   IntroductionDispatcher.assert_not_sent_before_addressable(...)
   raises RuntimeError if contract.is_addressable is False.
 │
 ▼
 User's next non-retire message:
   dispatcher.make_addressable(handle)
     - re-reads contract.yaml
     - sets pending_introduction=False, is_addressable=True
     - writes back
 │
 ▼ (eventually)
 User says "retire <handle>":
   retirement.retire_persona(handle, reason)
     - moves <workspace>/personas/<handle>/ →
            <workspace>/personas/_retired/<handle>-<timestamp>/
     - emits OTel event pos.persona.retired
     - LoaderPersona.load() ignores _retired/* on the next call
```

## Authoritative-source replay on compaction

The compaction-survival mechanism is the cleanest example of the
"never replay from a snapshot" principle. Three sources, one
output:

```
  contract.yaml  ─── identity + authority boundary ───┐
                                                      ▼
  scope-of-work ─── current scope context,          ┌─────────────────┐
  runtime.list()   pending decisions                │ CompactionSurv. │
                                                    │  (5-item list)  │
  memory provider ─ recent corrections ─────────────▶                 │
                                                    └─────────────────┘
                                                              │
                                                              ▼
                                           injected into first post-
                                           compact UserPromptSubmit;
                                           flag cleared.
```

No field comes from a pre-compact snapshot. If a contract is edited
between sessions, the persona identity replayed after compaction is
the new one — divergence cannot happen.
