# Primary-persona layer — API reference

One-page reference for the layer's public API. All symbols are
importable from `primary_persona` (see `src/__init__.py`).

## D1 — Persona contract

```python
PersonaContract.model_validate(raw_dict) -> PersonaContract
load_contract(yaml_path: str | Path) -> PersonaContract
PersonaContract.to_yaml() -> str
```

Mandatory fields: `handle`, `given_name`, `contract_version`,
`responsibilities`, `authority_boundary`, `escalation_taxonomy`,
`severity_vocabulary`.
Optional: `delegates_to`, `home_persona_for`, `voice_markers`,
`is_primary`, `pending_introduction`, `is_addressable`.

## D2 — Loader

```python
loader = PersonaLoader(workspace_root, enforce_no_personas_in_core=True)
loader.load() -> list[LoadedPersona]
loader.load_one(handle) -> LoadedPersona
loader.primary() -> LoadedPersona       # exactly one is_primary=True
loader.reload(handle) -> LoadedPersona  # alias for load_one
```

Raises:
- `PersonaDirectoryNotFoundError` — no `personas/` dir or empty dir.
- `PersonaValidationError` — contract invalid, prompt missing, etc.
- `PersonaInCoreError` — persona dir smuggled into pOS-core path.

## D3 — Background-work monitor

```python
monitor = BackgroundWorkMonitor(
    runtime,                     # scope_of_work.ScopeRuntime
    tick_interval_seconds=30.0,
    finished_lookback_seconds=3600.0,
    stuck_reason_fn=None,        # optional async (proj) -> str | None
    stuck_reason_budget=3,
)
await monitor.start()
block: AwarenessBlock = monitor.on_user_prompt(turn_id=None)
await monitor.stop()
```

`AwarenessBlock` fields: `turn_id`, `generated_at`, `active`,
`pending_decision`, `stuck`, `recently_finished`, `escalated`,
`failed`. Each is a tuple of `AwarenessRow`. Block methods:
`to_dict()`, `to_json()`, `token_estimate()`, `total_rows()`.
Constants: `MAX_ROWS_PER_CATEGORY=5`, `MAX_TOKENS=1_000`.

## D4 — Compaction survival

```python
mark_precompact(flag_dir) -> Path          # PreCompact hook
precompact_flag_present(flag_dir) -> bool
clear_precompact_flag(flag_dir) -> None

build_survival_payload(
    *, persona, runtime,
    recent_corrections_provider=None,
    corrections_limit=5,
) -> CompactionSurvivor

consume_survival_payload(
    *, flag_dir, persona, runtime,
    recent_corrections_provider=None,
    corrections_limit=5,
) -> CompactionSurvivor | None
```

`CompactionSurvivor.to_dict()` contains every item in `SURVIVAL_LIST`:
`persona_identity`, `authority_boundary`, `current_scope_context`,
`pending_decisions`, `recent_corrections`.

## D5 — Creation-trigger detector

```python
detector = CreationTriggerDetector(
    rubrics=ThresholdRubric.defaults(),
    judgment_fn=my_claude_max_judge,   # async (signal, domain, recent) -> JudgmentResult
)
detector.observe(CreationTrigger(signal=, domain=, observed_at=time.time()))
detector.threshold_crossed(signal, domain) -> bool
await detector.evaluate(signal, domain) -> JudgmentResult | None
detector.rejections() -> list[dict]
```

`TriggerSignal`: `request_decline`, `domain_correction`,
`cross_domain_scope`, `low_relevance_memory_hit`,
`explicit_user_mention`. `JudgmentVerdict`: `yes | no | defer`.

## D6 — Authoring pipeline

```python
pipeline = AuthoringPipeline(
    llm=my_llm_callable,   # async (prompt_name, prompt_text) -> LLMResult
    runtime=scope_runtime,
    workspace_root=Path(...),
    max_review_iterations=2,
    model="claude-haiku-4-5",
)
result: AuthoringResult = await pipeline.author(
    trigger_signal=TriggerSignal.explicit_user_mention,
    domain="cooking",
    existing_personas=loader.load(),
    authoring_scope_id="authoring-scope-xyz",
    proposed_handle=None,
)
```

`AuthoringResult.outcome` is one of `persisted | rejected_after_retries | failed`.
On `persisted`, `result.persona_dir` points to the new directory.
Per-step span names: `loam.persona.authoring.{style_harvest,domain_research,contract_synthesis,self_review}`.

## D7 — Introduction dispatcher

```python
dispatcher = IntroductionDispatcher(
    channels=[OneOnOneChannel(kind=ChannelKind.terminal, name="t", send=send_fn)],
    workspace_root=workspace_root,
)
record = await dispatcher.introduce(
    new_persona=new_loaded,
    trigger_signal=TriggerSignal.request_decline,
    retire_instruction=None,   # defaults to 'reply "retire <handle>"'
)
delivered = await dispatcher.flush_queue()    # when channel becomes active
dispatcher.make_addressable(handle)            # on next non-retire message

IntroductionDispatcher.assert_not_sent_before_addressable(persona, sender_handle)
# raises RuntimeError if the persona is pending_introduction=True
```

`OneOnOneChannel` construction rejects `is_group=True`. The
dispatcher re-checks at `__post_init__`.

`IntroductionOutcome`: `delivered | queued_no_channel | failed`.

## D8 — Retirement

```python
record = retire_persona(
    workspace_root=Path(...),
    handle="mara",
    reason=RetirementReason.user_initiated,
)
# moves personas/<handle>/ -> personas/_retired/<handle>-<ts>/
# emits OTel event loam.persona.retired
```

`RetirementReason`: `user_initiated`, `never_acknowledged`,
`workspace_policy`, `superseded`.

Un-retirement is a manual `mv` (intentional; the brief states it
must require explicit action).

## D9 — Observability helpers

`primary_persona.observability` is internal; it is invoked by every
other module automatically. No manual use is required. Span names
and event names are documented in `relationship-map.md`.
