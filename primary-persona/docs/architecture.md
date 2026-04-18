# Primary-persona layer — architecture

## Three halves + one shared contract

```
                   ┌──────────────────────────────┐
                   │  workspace/personas/         │
                   │   └── <handle>/              │
                   │        ├── contract.yaml ◄───┼── D1: Pydantic
                   │        ├── prompt.md         │   PersonaContract
                   │        └── voice.md (opt.)   │
                   └──────────────────────────────┘
                                 │
                                 │  session start
                                 ▼
            ┌─────────────────────────────────────┐
            │ D2: PersonaLoader                   │
            │  - validates contract               │
            │  - fails closed on missing/invalid  │
            │  - emits OTel loader span           │
            │  - build-time check: no personas    │
            │    in pOS-core paths                │
            └─────────────────────────────────────┘
                                 │
                                 ▼
                         LoadedPersona(s)
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
  ┌─────────────┐       ┌──────────────┐       ┌──────────────────┐
  │  D3 Monitor │       │ D4 Compaction│       │ D5+D6 Authoring  │
  │             │       │   Survival   │       │                  │
  │ subscribes  │       │              │       │ detector → 4-step│
  │ to scope-of-│       │ PreCompact   │       │ pipeline:        │
  │ work pyee   │       │   flag +     │       │  style_harvest   │
  │ emitter     │       │ UserPrompt-  │       │  domain_research │
  │             │       │ Submit detect│       │  contract_synth  │
  │ 30s tick    │       │              │       │  self_review ×2  │
  │             │       │ replay from  │       │                  │
  │ awareness   │       │ authoritative│       │ emits new        │
  │ block on    │       │ sources      │       │ persona dir      │
  │ every turn  │       │ (contract +  │       │ (pending, non-   │
  │ (≤1k tok,   │       │  scope list +│       │ addressable)     │
  │ 6 categories│       │  memory)     │       │                  │
  │  × 5 rows)  │       │              │       │                  │
  └─────────────┘       └──────────────┘       └──────────────────┘
                                                         │
                                                         ▼
                                               ┌──────────────────┐
                                               │ D7 Introduction  │
                                               │  Dispatcher      │
                                               │                  │
                                               │ one-on-one only  │
                                               │ (group forbidden)│
                                               │                  │
                                               │ queues when no   │
                                               │ channel active   │
                                               │                  │
                                               │ guards every     │
                                               │ message from a   │
                                               │ non-addressable  │
                                               │ persona          │
                                               └──────────────────┘
                                                         │
                                                         ▼
                                               user acknowledges →
                                               is_addressable=True
                                                         │
                                                         ▼
                                               ┌──────────────────┐
                                               │ D8 Retirement    │
                                               │ moves dir to     │
                                               │ _retired/<h>-<ts>│
                                               │ emits event      │
                                               └──────────────────┘

All operations emit OTel spans/events (D9).
```

## Module layout

```
primary-persona/
├── pyproject.toml                  ← package metadata
├── requirements.txt                ← runtime + test deps
├── pytest.ini                      ← test config
├── docs/                           ← bundled documentation (D10 + v1.1 R4)
├── templates/
│   └── persona-template/           ← copy-to-workspace starter (D1)
│       ├── contract.yaml
│       └── prompt.md
├── src/
│   ├── __init__.py                 ← public re-exports
│   ├── contract.py                 ← D1: Pydantic contract + load_contract
│   ├── loader.py                   ← D2: PersonaLoader + validation
│   ├── monitor.py                  ← D3: BackgroundWorkMonitor
│   ├── compaction.py               ← D4: CompactionSurvivor + flag API
│   ├── creation_triggers.py        ← D5: CreationTriggerDetector
│   ├── authoring.py                ← D6: AuthoringPipeline (4-step LLM)
│   ├── introduction.py             ← D7: IntroductionDispatcher
│   ├── retirement.py               ← D8: retire_persona
│   └── observability.py            ← D9: OTel span/event helpers
└── tests/
    ├── conftest.py                 ← shared fixtures + OTel provider
    ├── test_d1_contract.py
    ├── test_d2_loader.py
    ├── test_d3_monitor.py
    ├── test_d4_compaction.py
    ├── test_d5_creation_triggers.py
    ├── test_d6_authoring.py
    ├── test_d7_introduction.py
    ├── test_d8_retirement.py
    └── test_d9_observability.py
```

## Concurrency model

- The monitor's tick runs as a single asyncio coroutine (`asyncio.Task`
  spawned by `BackgroundWorkMonitor.start()`). One failed tick does
  not kill the coroutine; the exception is recorded on the tick span
  and the loop continues.
- The monitor's event callback (`pyee.on`) is synchronous inside the
  emitter dispatch; a callback exception is swallowed so the emitter
  stays healthy.
- The authoring pipeline runs inside a caller-supplied scope-of-work
  scope; the caller declares the budget (time/tokens/money).
  Per-step LLM calls debit against the scope.
- The loader is stateless — every call re-reads disk.

## State flow at a glance

1. Session starts → loader runs → primary persona resolved.
2. Background-work monitor starts → subscribes + ticks.
3. Every UserPromptSubmit:
   - If PreCompact flag present → consume, inject survival payload,
     clear flag.
   - Call `monitor.on_user_prompt(turn_id)` → awareness block.
   - Both payloads are delivered as the prefix of the model's
     context for this turn.
4. Ongoing work observations fed into the creation-trigger detector.
5. On a yes verdict → authoring pipeline produces a pending
   persona → introduction dispatched to one-on-one channel.
6. On user acknowledgement → `make_addressable(handle)` flips flags.
7. On retirement instruction → `retire_persona(...)` moves directory.
