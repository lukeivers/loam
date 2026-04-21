# Research — Self-Correction Loop

**Component:** Self-Correction Loop — detects system errors (failed scope, OTel anomaly, review verdict, user correction) and opens correction scopes that structurally honour the four-part protocol (name the class, fix the instance, diagnose the cause, apply the structural remedy), composing with safety / reversibility / cost-governance gates without bypass.
**Status:** DRAFT research — input to build.
**Branch:** `pos-v2`. **Date:** 2026-04-20.
**Author:** research agent (general-purpose), dispatched by the primary persona per plan at `components/self-correction-loop/research-plan.md`.

---

## 0. Fact-verification before design

Two load-bearing assertions in the research plan were checked against `pos-v2` source before the design below was drawn.

### 0.1 `StateTransitioned` carries enough to drive a trigger — CONFIRMED

`scope-of-work/src/events.py` lines 74-79:

```python
class StateTransitioned(_EventBase):
    kind: Literal["state_transitioned"] = "state_transitioned"
    from_state: ScopeState
    to_state: ScopeState
    reason: str | None = None
    pause_reason: str | None = None
```

The envelope also carries `scope_id`, `event_id`, `created_at`, `otel_span_id`, `otel_trace_id` (lines 38-48). `ScopeState.failed` is enum-value 5 of 7 (`spec.py` line 45). Sufficient for a trigger: subscribe to the emitter, filter `to_state == ScopeState.failed`, read `scope_id` + `reason`. No amendment needed.

`ScopeRuntime.emitter` is a public property (`runtime.py` line 97) backed by `AsyncIOEventEmitter`; `subscribe_all("*", callback)` is the canonical consumer pattern (line 141). Precedent: `cost-governance/src/ledger.py` line 375 does exactly this — `scope_runtime.emitter.on("*", self._on_event)`.

### 0.2 Review-scopes as a first-class concept — **NOT PRESENT** (halt signal — see §11)

Grep of `scope-of-work/src/**.py` for `verdict|review` returns zero matches. The only `verdict` in `pos-v2` lives in `primary-persona/src/authoring.py` as `SelfReviewVerdict` — persona-authoring's four-dimension self-review loop, NOT a generic "review scope" concept.

This contradicts the research plan's assumption that "reviewers are scopes themselves; their terminal state with `verdict` attribute is the signal" (Q-group 1 #3). No `verdict` attribute exists on any ScopeState; review-scopes are a convention, not a primitive.

**Resolution (per §3 and §11):** the review-verdict trigger becomes an **IPC-call convention** rather than an emitter subscription. A reviewer — whether it is a scope acting as reviewer, a persona session, or an external harness — calls `correction.report_review_verdict(scope_id, verdict, reasons)` on the self-correction IPC when it produces a fail verdict. Self-correction treats this as one of four trigger surfaces and records it. No scope-of-work amendment is required, and no Phase 4 component blocks on this — if/when a "review-scope" primitive lands later, it can simply call the same IPC.

### 0.3 Plan terminology — minor correction

The plan refers to a "four-wrap chain (safety → reversibility → cost → orig_activate)". The source shows **three gate wraps** (safety, reversibility, cost) layered over `orig_activate`. Dispatch order at runtime per `cost-governance/src/ipc_wiring.py` line 9: `safety → reversibility → cost → orig_activate`. Registration order is the reverse. Research doc uses "three-gate chain" throughout; build can use whichever term the owner prefers.

---

## 1. Survey of existing patterns

Four families of prior art are relevant; each offers a partial analogue, none is a drop-in.

### 1.1 Retry patterns (exponential backoff, circuit breaker)

**Backoff.** AWS SDK, Stripe, Kubernetes controllers. Retry a transient failure with increasing delay; cap attempts; eventually surface. Solves transient I/O errors; does not address *class* of failure or structural remedy.

**Circuit breaker** (Hystrix, Polly). Three states — closed, open, half-open. After N failures in a window, the breaker opens and short-circuits calls. Relevant analogy for recursion-bound and same-class-cascade detection (plan Q17): the "open" state is equivalent to "escalate, do not keep trying."

**Applicability:** the recursion bound (§5) and cascade-detection window borrow the half-open semantics. Correction's four-part protocol is not retry — it is a richer structural contract — so backoff alone is insufficient.

### 1.2 Supervisor trees (Erlang OTP)

Erlang supervisors organise processes into a tree; a failing child is restarted according to a declared strategy (`one_for_one`, `one_for_all`, `rest_for_one`). Restart intensity is bounded: more than N restarts in T seconds escalates the failure one level up the tree.

**Applicability:** the "restart intensity bound" maps directly to the plan's cascade-detection rule (Q17 — "same failure class triggered 3 corrections in 10 minutes → escalate"). The tree structure is less relevant here because correction scopes are flat in depth (cap 3) and their parent is the orchestrator, not a supervisor. Take the bound, leave the tree.

### 1.3 Exception-handling philosophies (Rust Result, Go errors)

**Rust `Result<T, E>`:** explicit at every call site; errors cannot be silently ignored (the `?` operator propagates, the `Result` warning fires on discard). Errors are typed — `E` is a sum type the caller matches on.

**Go explicit return:** `if err != nil` everywhere; errors are values; wrapping (`fmt.Errorf("context: %w", err)`) preserves chains.

**Applicability:** both share a principle — errors are typed, first-class, and impossible to forget. That maps to the four-part records being typed Pydantic models stored in the correction-episode log. The `FailureClassIdentified` record is the `E` — typed, required, non-discardable. Correction's enforcement (cannot reach `completed` without all four) is the schema-level analogue of the Rust compiler forcing you to match every `Err` branch.

### 1.4 AI-agent self-reflection loops

Three variants in the 2023-2025 literature:

**Reflexion (Shinn et al., 2023).** An agent that fails a task writes a natural-language reflection to episodic memory; next attempt reads the reflection. Loop bounded by max-iterations. Pure LLM mechanism — no typed records, no structural contract.

**Constitutional AI (Anthropic, 2022).** A critique-then-revise loop governed by a written constitution (rules the revised output must satisfy). The constitution is the structural contract; the critique checks adherence; the revision is the remedy.

**Agentic debug-loops (Devin, SWE-agent, 2024-2025).** On test failure, the agent runs a diagnose-fix-rerun loop with exponential backoff on progress and a max-iteration cap. Heavy LLM-in-loop; little structural discipline.

**Applicability:** Constitutional AI is the nearest — a written contract that revisions must satisfy. Self-correction's four-part protocol is constitutional in this sense: `prior-pOS .claude/rules/prime.md` is the constitution; the four record types are the check; the correction scope's LLM execution is the revise. Reflexion's bounded-iterations is the recursion cap. **The distinctive move self-correction makes** is that the constitution is enforced at the **schema** level, not at inference — an episode without all four records cannot be marked `completed`. That's the clause-(g) pattern from self-upgrade applied to the correction protocol.

### 1.5 Synthesis

Self-correction is **supervisor-tree restart intensity** + **typed-error discipline** + **constitutional-AI structural contract**, with the pOS-specific twist that the constitution is enforced deterministically on the episode log, not inside the LLM loop. No LLM inside the primitive's refusal path; the LLM's role is authoring the four records inside a correction scope's execution — which happens in a scope, under the normal gates.

---

## 2. Recommended design shape

Eight question-groups from the plan. For each: options considered, recommended option, rationale.

### 2.1 Q-group 1 — Detection surfaces

**Four trigger sources. Recommendation: four independent intake paths, all normalised into a single `CorrectionTrigger` record.**

| Source | Transport | Payload |
|--------|-----------|---------|
| Scope failure | `ScopeRuntime.emitter` subscription (`*`) filtered on `StateTransitioned(to_state=failed)` | `scope_id`, `reason`, `failure_metadata` (projected from the event) |
| OTel anomaly | DuckDB query against `observability-aggregator.QueryAPI.find_spans(SpanFilter)` on a scheduler | `trace_id`, `span_id`, threshold violated, observed value |
| Review verdict | IPC call `correction.report_review_verdict(scope_id, verdict, reasons)` (see §0.2) | `scope_id`, `verdict="fail"`, `reasons`, reporter identity |
| User correction | IPC call `correction.user_reported(description, related_scope_id?)` from primary-persona session | `description`, optional `related_scope_id`, timestamp |

**Filtering (which failures trigger correction).** The plan asks whether safety-gate refusals should self-exclude. Yes — otherwise the safety gate will recurse on its own refusals. Recommendation: exclude `reason` values matching `^safety-gate/` or `^cost-ceiling/` or `^reversibility-gate/` (gate refusals are *working correctly*, not errors to correct). Also exclude `cancelled` and `escalated` transitions; only `failed` triggers.

**Trigger deduplication.** The plan proposes 60s or event-hash. Recommendation: **event-hash with a 60-second TTL window**. Hash = SHA-256 of `(scope_id, trigger_source, normalized_reason)`. Write the hash to `correction_trigger_dedup` sidecar table on first fire; a second fire within TTL that hashes the same is dropped (logged as `pos.correction.trigger_deduplicated`). TTL configurable; 60s default anchors on cost-governance's own notification-dedup TTL.

### 2.2 Q-group 2 — Four-part structural enforcement

**Recommendation: Pydantic-typed records stored in a sidecar `correction_episode_records` table; completion pre-check is a pyee-subscribed terminal-transition handler on the correction scope's emitter.**

Shape (Pydantic, `extra="forbid"`, `frozen=True`):

```python
class FailureClassIdentified(BaseModel):
    correction_episode_id: str
    class_name: str            # short, kebab-case, e.g. "state-but-defer"
    description: str
    similar_prior_count: int   # lookup against episode history within window
    at: str                    # iso timestamp

class InstanceFixed(BaseModel):
    correction_episode_id: str
    scope_id_affected: str | None
    fix_description: str
    artifact_paths: tuple[str, ...] = ()
    at: str

class CauseDiagnosed(BaseModel):
    correction_episode_id: str
    root_cause: str
    evidence_refs: tuple[str, ...]   # paths, span ids, event ids
    at: str

class StructuralRemedyApplied(BaseModel):
    correction_episode_id: str
    change_description: str
    target_file_or_rule: str         # e.g. "prior-pOS .claude/rules/prime.md:21"
    verification_path: str           # e.g. "pytest path/to/test::test_x"
    at: str
```

**Ordering.** Plan asks protocol-order vs any-order. Recommendation: **any order, but order is recorded.** Rationale: an author who diagnoses the cause before fixing the instance (because they needed to understand root cause first to apply a safe fix) is doing correct work; forcing protocol order would create artificial gymnastics. What matters structurally is **all four exist** before `completed`.

**Completion pre-check.** Subscribe on the correction scope's own `scope_runtime.emitter` for `StateTransitioned(to_state=completed)`. In the handler, query the sidecar for the four record types on the episode. If any is missing, raise `ApplicationError(-32070 CORRECTION_INCOMPLETE_RECORDS)` **before** the transition is persisted. The pre-check runs inside the runtime's append flow; this is the clause-(g) enforcement style lifted from self-upgrade.

An alternative considered and rejected: emit the four records as *scope-of-work events* on the correction scope's event stream. Rejected because it requires adding four new event types to `scope-of-work/src/events.py` — an amendment to a sealed component. The sidecar table keeps the amendment budget at zero.

**Authoring.** The correction scope's LLM execution authors each record and calls `correction.record_part(episode_id, part_type, payload)` IPC. The primitive validates the payload (Pydantic) and persists. No LLM inside the primitive's enforcement path — §9 `no-LLM` rule held.

### 2.3 Q-group 3 — Correction scope opening

**Recommendation: deterministic `ScopeSpec` builder + standard `activate_scope` IPC call.**

```
trigger received
  → CorrectionTriggerRecord persisted (sidecar)
  → SpecBuilder.build_correction_spec(trigger) -> ScopeSpec
  → IPCClient.activate_scope(spec) via orchestrator IPC (goes through the three gates)
  → on success, CorrectionEpisode persisted with (episode_id, trigger_id, scope_id, parent_correction_id=None|parent)
```

**Scope objective text.** Template:
`"Correct failure class '<class>' surfaced by <trigger_source>. Apply the four-part protocol: identify class, fix instance, diagnose cause, apply structural remedy."`

**`reversibility_class`.** Default `compensatable`. Any structural remedy that edits a file, rule, or rule config is compensatable by definition (revert the commit / restore from snapshot). Register a compensation-path binding at episode creation time: the compensation is "revert-structural-remedy-<episode_id>", handled by a deterministic rollback handler that (a) reads the `target_file_or_rule` from the StructuralRemedyApplied record, (b) restores from the episode's pre-remedy snapshot taken at scope creation. If no remedy has been applied yet at rollback time, the handler is a no-op and returns `succeeded`.

Corrections whose sole action is to draft a report or update memory may declare `fully_reversible` — but the safer default is `compensatable`. `irreversible` is forbidden for correction scopes by validation at spec-build time; a correction that declares `irreversible` halts and escalates.

**Budget.** Plan proposes inherit-and-scale at 50%. Recommendation: **inherit from triggering scope with scaling 0.5** on time and tokens axes. Floors: minimum 60s time, minimum 2,000 tokens. If the session ceiling would be exceeded by the scaled budget, the correction primitive **does not reduce budget to fit** — it lets cost-governance refuse normally, catches the `ApplicationError(-32060|61|62)`, and escalates to the user via `OneOnOneChannel` with `"correction refused — cost ceiling exceeded"`. Silent drop is forbidden (per §9 `report-refusals`).

### 2.4 Q-group 4 — Recursion bound

**Recommendation: depth cap 3 via `parent_correction_id` walk + same-class-cascade detection with a 10-minute window.**

```
CorrectionEpisode(
  episode_id: str,
  trigger_id: str,
  correction_scope_id: str,
  parent_correction_id: str | None,   # for depth walk
  failure_class: str,
  opened_at: str,
  state: Literal["running", "completed", "escalated", "refused"],
)
```

**Depth walk.** At trigger-intake time, if `parent_correction_id` is non-null, walk up the chain. If walk count `>= 3`, do not open a correction scope. Instead, escalate via `OneOnOneChannel`: `"correction cascade — depth 3 reached on class '<class>'. Manual intervention needed. Episode chain: <ids>."` Record a `CorrectionCascadeEscalated` sidecar record; emit OTel span `pos.correction.cascade_escalated`.

**Cascade detection (same-class-in-window).** Independent of depth. At trigger-intake, count episodes of the same `failure_class` opened in the last 10 minutes. If `>= 3`, escalate even if depth cap has not been hit. Same message pattern; separate record type `CorrectionCascadeBySameClass`. The window and threshold are `correction.cascade_window_seconds=600` and `correction.cascade_same_class_threshold=3`, configurable.

**Parent-detection.** A correction episode is "child of" another when: trigger's `scope_id` matches a currently-running correction scope's `scope_id`. The self-correction runtime maintains an in-memory map `{scope_id: episode_id}` for running correction scopes; this is rebuilt from the sidecar on bootstrap.

### 2.5 Q-group 5 — Integration with safety / reversibility / cost

**Safety.** Correction scopes do not bypass safety. A correction whose planned action requires a dangerous-op (send email, commit funds, push to public repo) will have that dangerous-op fire the safety gate exactly as for any scope — the gate's state is indexed by `structural_hash(spec)`, and the correction scope has a distinct spec. No extra coordination. **One configuration item:** some correction classes (e.g. "anti-deskilling trigger misfire") should not themselves be asked about — a safety always-ask-list entry for "open a correction scope" would be a recursion trap. Recommendation: the `activate_scope` IPC path does NOT require safety approval (correction scope creation is not a dangerous-op); safety fires only when the correction's execution invokes a dangerous-op, same as any other scope.

**Reversibility.** Correction scopes default `compensatable` (§2.3); the compensation-path binding is registered at scope-construction time. Rollback of a correction scope unwinds the structural remedy. If the rollback itself fails, reversibility's notification fires (existing infrastructure); self-correction does not need its own rollback-of-correction retry logic.

**Cost.** Correction scopes count against session and rolling-window ceilings. A correction cascade that eats budget hits the ceiling and is refused. This is correct behaviour — the system is telling the user "we have spent too much correcting; stop and look." No bypass. The escalation path is the `OneOnOneChannel` message described in §2.3.

**Observability aggregator.** Self-correction emits spans under `trace.get_tracer("pos.self_correction")` (A1 held). Span names proposed: `pos.correction.trigger_received`, `pos.correction.scope_opened`, `pos.correction.record_persisted`, `pos.correction.completion_pre_check`, `pos.correction.cascade_escalated`, `pos.correction.refused`. No aggregator amendment — these are consumed by the aggregator's existing OTel ingestion.

### 2.6 Q-group 6 — Primary-persona integration

**Recommendation: transparent subscription — the primary persona's runtime does not need to know about self-correction; self-correction is an independent component that subscribes to emissions.**

The primary persona's only contact with self-correction is the IPC surfaces:

1. `correction.user_reported(description, related_scope_id?)` — when the user says "that was wrong" in the one-on-one channel, the persona parses the intent and calls this IPC. Detection logic lives in the persona; the call is deterministic.
2. `correction.report_review_verdict(scope_id, verdict, reasons)` — if a reviewer persona produces a fail verdict, they call this IPC. Reviewer identity passed through for audit.
3. Escalation notifications arriving on `OneOnOneChannel` originate from the correction runtime directly; the persona observes but does not gate. Rationale: cascade escalation is time-critical (same-class-in-window triggers mean the system is hot), and routing through the persona would add latency and a per-message decision surface that defeats the point.

The primary persona's operating rule (`prior-pOS .claude/rules/prime.md` four-part protocol section) is the source this component structurally enforces. The persona continues to follow the rule as prose; the self-correction component ensures no correction *scope* can be marked complete without the four records.

### 2.7 Q-group 7 — Sidecar + subscription vs wrap

**Recommendation: no new activation wrap. Sidecar + subscription only.** The design above has:

- **Three sidecar tables** owned by the correction component: `correction_triggers` (log), `correction_episodes` (with `parent_correction_id` for depth), `correction_episode_records` (the four part records, keyed by `(episode_id, record_type)` with uniqueness so missing-record tests are trivial). Plus `correction_trigger_dedup` for §2.1.
- **Three subscriptions:** (a) `scope_runtime.emitter.on("*", on_scope_event)` to catch `StateTransitioned(to_state=failed)` for trigger #1 and `to_state=completed` for the completion pre-check on correction scopes; (b) a polling loop (default 30s interval) against the observability-aggregator QueryAPI for trigger #2; (c) IPC methods for triggers #3 and #4.
- **Zero activation wraps.** Correction opens scopes through the normal `activate_scope` IPC; they flow through safety, reversibility, cost in the standard way.

**Failure mode stress-test.** Does any refusal shape require a wrap? Reviewed:
- "Correction scopes must declare `compensatable`" — validated at spec-build time before `activate_scope`; no wrap needed.
- "Correction scopes at depth 3 must not open" — enforced at trigger-intake before scope construction; no wrap needed.
- "Correction episode missing records cannot reach `completed`" — enforced via the terminal-transition pre-check on scope-of-work's existing hooks; no wrap needed.

**Conclusion:** the no-wrap pattern holds cleanly. This is the first Phase 3 component whose refusal surfaces all live outside the activation path — self-correction is a *consumer* of the gate chain, not a gate on it.

### 2.8 Q-group 8 — Testing discipline

The plan's tests (27–30) are the right list. Expansion:

1. **Synthetic detection tests** (27): one test per source. For OTel anomaly, use the aggregator's in-memory store fixture; inject spans; assert trigger fired with correct payload.
2. **Four-part enforcement tests** (28): four tests — episode with only 3 records (one per missing). All four assert `completed` transition raises `-32070`.
3. **Recursion-bound test** (29): synthesize a deterministic trigger loop (correction scope whose execution triggers its own failure). Assert episode 1, 2, 3 open; 4th attempt is escalated; `OneOnOneChannel.send` was called with `"correction cascade"`.
4. **Cost-ceiling-interaction test** (30): construct trigger with declared budget that would exceed session ceiling; assert `ApplicationError(-32060)` raised by cost-governance; assert self-correction caught it and escalated to `OneOnOneChannel`; assert episode state is `refused`, not silently dropped.
5. **Dedup test** (new): fire the same trigger twice within 60s; assert one episode opened.
6. **Exclusion test** (new): fire a `StateTransitioned(to_state=failed, reason="safety-gate/ask-refused")`; assert no correction scope opens.
7. **Same-class cascade test** (new): open three episodes of class `state-but-defer` within 10 minutes; 4th is escalated even at depth 1.
8. **OTel-visibility test** (new): fire a trigger; assert a `pos.correction.scope_opened` span appears in the aggregator store with trigger source + class name attributes.
9. **`test_no_sealed_amendments.py`** (mandatory): pins to `SEAL_COMMIT` constant (self-correction's own seal). Diffs `BASELINE..SEAL_COMMIT`. `BASELINE="04951b6"` (cost-governance seal). `allowed_prefixes = ("self-correction/", "data/")`. This is the structural-remedy anchor from commit `f94d602`; do NOT re-introduce the HEAD-based variant.
10. **One-on-one channel test**: assert all correction notifications go through a subclass of `OneOnOneChannel` (pattern from `cost-governance/src/notification.py` line 17); assert the group-rejection check fires on a synthetic group channel.

---

## 3. Clause-by-clause spec coverage

Each plan acceptance clause maps to a design piece.

| Plan clause | Design piece |
|---|---|
| Typed `CorrectionTrigger` from 4 sources | §2.1 — emitter sub, aggregator poller, two IPC methods, normalised record |
| Four-part structural honour | §2.2 — sidecar table + completion pre-check + four Pydantic shapes |
| Flow through three-gate chain, no bypass | §2.3, §2.5 — standard `activate_scope`; spec declares `compensatable`; cost counts normally |
| Cascade bounded | §2.4 — depth cap 3 + same-class-in-window escalation |
| OTel-visible | §2.5 — `pos.self_correction` tracer; span names enumerated |
| Clean integration with sealed components | §2.7 — no wrap, three sidecars, three subscriptions |

---

## 4. Four-part protocol specification

Already detailed in §2.2. Key structural property: **no episode can reach `completed` state without four records**, because the terminal-transition pre-check raises before the append. Enforcement is pyee-subscribed, runs deterministically, does not use an LLM. The pre-check is keyed by `(episode_id, record_type)` with a UNIQUE constraint in `correction_episode_records`, so the check is `SELECT DISTINCT record_type FROM correction_episode_records WHERE episode_id = ?` → `if set != {class, instance, cause, remedy}: raise`.

Unit-addressable failure modes for tests:
- missing `FailureClassIdentified` → raise
- missing `InstanceFixed` → raise
- missing `CauseDiagnosed` → raise
- missing `StructuralRemedyApplied` → raise
- all four present → proceed to normal `completed` transition

An episode that the correction LLM cannot complete within budget times out as `failed` (normal scope-of-work behaviour). A `failed` correction does *not* require the four records — only `completed` does — and a `failed` correction is itself a trigger under §2.1 rule #1. Depth cap and cascade detection handle the recursion.

---

## 5. Recursion-bound specification

Detailed in §2.4. Compact:

**Depth** = walk-up count on `parent_correction_id` starting from the candidate trigger's parent.
- depth < 3 → open correction scope; record `parent_correction_id`
- depth >= 3 → refuse; record `CorrectionCascadeEscalated(reason="depth_cap")`; notify user

**Same-class window** = count of episodes with matching `failure_class` opened within `cascade_window_seconds` (default 600).
- count < 3 → proceed to depth check
- count >= 3 → refuse; record `CorrectionCascadeBySameClass(class=..., count=..., window=...)`; notify user

Both checks run at trigger-intake, before `activate_scope` is called.

**Config defaults:**
```yaml
correction:
  depth_cap: 3
  cascade_window_seconds: 600
  cascade_same_class_threshold: 3
  trigger_dedup_ttl_seconds: 60
  aggregator_poll_interval_seconds: 30
  budget_scale_factor: 0.5
  budget_time_floor_seconds: 60
  budget_tokens_floor: 2000
```

---

## 6. Detection-surface specification

Detailed in §2.1. Four sources summarised:

1. **Scope failure** — subscription to `ScopeRuntime.emitter`, `to_state==failed`, exclude gate-refusal reasons.
2. **OTel anomaly** — polling loop over `observability-aggregator.QueryAPI.find_spans`. Anomaly definition is configurable; starter set:
   - span `status == "ERROR"` with `retention_class=="high"` and the error is not a known gate-refusal
   - span `duration_ns` > configured P99 threshold for that span name within a sliding window
   - presence of a named event on a span (e.g. `pos.scope.trigger_fired` events with specific trigger_kind)
3. **Review verdict** — IPC `correction.report_review_verdict(scope_id, verdict, reasons)`; only fires on `verdict=="fail"`.
4. **User correction** — IPC `correction.user_reported(description, related_scope_id?)`.

All four sources normalise into `CorrectionTrigger(trigger_id, source, scope_id?, trace_id?, failure_class_hint?, raw_payload, received_at)`. Dedup by event-hash over 60s TTL.

---

## 7. Integration sequence diagrams

Three flows. Text-only diagrams (pos-v2 convention).

### 7.1 Happy-path: failed scope → correction → remedy

```
scope-of-work              self-correction          orchestrator IPC       gates chain
      |                           |                        |                    |
      | emit StateTransitioned    |                        |                    |
      | (to=failed, reason="X")   |                        |                    |
      |-------------------------->| on_scope_event         |                    |
      |                           | dedup check (miss)     |                    |
      |                           | depth check (0<3)      |                    |
      |                           | class cascade (ok)     |                    |
      |                           | build CorrectionSpec   |                    |
      |                           |--- activate_scope ---->|                    |
      |                           |                        |--- safety ok ----->|
      |                           |                        |--- rev ok -------->|
      |                           |                        |--- cost ok ------->|
      |                           |                        |---- orig_act ----->|
      |<---- scope created -------|<----------------------|<-------------------|
      | (LLM executes scope)      |                        |                    |
      | record four parts via     |                        |                    |
      |<-- correction.record_part IPC (x4) --              |                    |
      | emit StateTransitioned    |                        |                    |
      | (to=completed)            |                        |                    |
      |-------------------------->| pre-check: 4/4 records |                    |
      |                           | allow transition       |                    |
      |                           | emit                   |                    |
      |                           | pos.correction.closed  |                    |
```

### 7.2 Cascade escalation

```
self-correction                                           OneOnOneChannel
      |                                                         |
      | trigger intake (depth=3 or same_class_count>=3)         |
      | refuse: no activate_scope called                        |
      | record CorrectionCascadeEscalated                       |
      | emit pos.correction.cascade_escalated                   |
      |---- send(cascade_escalation_notification) ------------->|
      |                                                         | (user surface)
```

### 7.3 User-reported correction

```
primary-persona                 self-correction            ... (as §7.1)
      |                                |
      | parse intent from user msg     |
      | correction.user_reported ----->|
      |                                | build trigger
      |                                | (proceeds as §7.1 from depth check)
```

### 7.4 Cost-refusal escalation

```
self-correction             cost-governance gate           OneOnOneChannel
      |                              |                             |
      | activate_scope for           |                             |
      | correction scope ----------->|                             |
      |                              | reservation math → refuse   |
      |                              | raise -32060 SESSION_CEIL   |
      |<-- ApplicationError ---------|                             |
      | catch, record episode state  |                             |
      | = "refused"                  |                             |
      |---- send(refused_notif) --------------------------------->|
```

---

## 8. Relationship to safety / reversibility / cost

Tabulated so no gate is elided.

| Gate | Fires on correction scope? | How |
|------|---------------------------|-----|
| Safety ask-list | Yes — when the correction's action is on the ask-list | Normal safety gate; approval keyed by structural_hash(correction_spec) |
| Safety dangerous-op | Yes — when the correction invokes a dangerous-op action | Normal gate; no special treatment |
| Safety kill-switch | Yes — a system-kill during correction blocks activation | Correct — do not bypass |
| Reversibility binding | Yes — correction spec declares `compensatable` → binding required | Self-correction registers the binding at scope construction time |
| Reversibility rollback | Yes — rollback of a correction reverts its structural remedy | Via registered compensation handler |
| Cost session ceiling | Yes — counts exactly as any scope | Refusal → `-32060` → escalate to user |
| Cost rolling ceiling | Yes — counts exactly as any scope | Refusal → `-32061` → escalate |
| Cost scope budget | Yes — correction declares its own scaled budget | Refusal → `-32062` → escalate |

**Nothing is bypassed. All refusals are escalated, not silently dropped.**

---

## 9. Dependency map

**Consumed by:** none (Phase 3 close; Phase 4 begins after).

**Depends on:**

| Component | Surface used | Role |
|---|---|---|
| scope-of-work | `ScopeRuntime.emitter.on("*", ...)`, `ScopeSpec`, `StateTransitioned`, `ScopeState.failed`/`completed`, `activate_scope` IPC | emitter consumer + scope opener |
| orchestrator (IPC) | `IPCServer.register_method`, `IPCClient.activate_scope`, `ApplicationError` error codes | IPC channel |
| safety-layer | `structural_hash(spec)` import (canonical hash), pass-through on dangerous-op | no-bypass integration |
| reversibility-primitive | `register_compensation` IPC call | binding registration at scope construction |
| cost-governance | refusal codes `-32060/-32061/-32062`, catch-and-escalate | no-bypass integration |
| observability-aggregator | `QueryAPI.find_spans(SpanFilter)` | OTel-anomaly trigger source |
| primary-persona | `OneOnOneChannel` subclass | escalation channel |

No amendments to any of the above. All integration is consumer-only.

---

## 10. Complexity estimate

**AI-time anchors (named priors):**
- `cost-governance` ~16.5 min — three-table sidecar, pyee subscription, one wrap, notifier subclass
- `reversibility-primitive` ~30 min — FSM, two wraps, compensation registry, cascade subscription
- `safety-layer` ~35 min — three gates, kill switch, ask-list, dangerous-op, several notification paths

**Self-correction compared:**
- **Simpler than cost-governance and reversibility** in one dimension: no new activation wrap (the single biggest source of integration friction in both those builds was the wrap-composition ordering and tests).
- **Richer than cost-governance** in state-machine logic: four sidecar tables (triggers, episodes, records, dedup), four trigger sources (three are trivial; the OTel-anomaly poller adds a supervisor loop), four-part completion pre-check, depth + cascade detection.
- **Richer than cost-governance** in testing: ~10 distinct test scenarios listed in §2.8, several of which require multi-scope orchestration in-test (cascade escalation, depth chain).

**Estimate: 28–35 AI-min wall-clock; anchor ~32.** This sits above cost-governance (no wrap but fewer moving parts) and near reversibility (comparable sidecar complexity, but simpler FSM since scope-of-work itself owns the correction scope's state machine — self-correction only tracks the episode, not the scope). Under the plan's red-line of 40.

**Caveats that could push over:**
- OTel-anomaly trigger source if built with a sophisticated anomaly detector (P99 sliding windows etc). Recommendation: **ship the simplest useful anomaly definition** (status==ERROR + retention_class==high) for first build; richer definitions are sidecar config later. Keeps estimate anchored.
- Primary-persona intent-parsing for `user_reported` IPC if built in this component. Recommendation: **do not** — intent parsing lives in the persona; self-correction exposes the IPC and stays deterministic.

If either caveat bleeds into scope, estimate is 40–50 min and that is a signal to descope.

---

## 11. Prototyping priorities

Three things only a prototype can answer:

### 11.1 pyee subscription ordering under cascade conditions

Question: when a correction scope A emits `StateTransitioned(to_state=failed)`, the self-correction subscription fires **and** (because A is compensatable) reversibility's cascade-subscription also fires. Does pyee guarantee ordering? Do both fire on the same event loop tick? If reversibility fires first and cancels/completes A before self-correction reads, does the self-correction handler race on stale state?

**Prototype shape:** a 20-line script that spins a ScopeRuntime with both self-correction and reversibility subscribed, emits a failure event, and logs the order + timing. If subscription order is non-deterministic, the build must either (a) serialise the handlers via a single dispatcher, or (b) tolerate eventual-consistency on episode state. Answer informs ~2 design decisions.

### 11.2 Completion pre-check composition with scope-of-work's terminal-transition hooks

Question: scope-of-work's `ScopeRuntime.complete_scope()` persists the `StateTransitioned(to_state=completed)` event and then fans out to subscribers. If self-correction's subscriber raises inside the callback, does the event-store transaction roll back, or does the event persist and the scope becomes "completed in the log, completion pre-check raised on notification"?

**Prototype shape:** construct a completion pre-check that always raises; drive a correction scope through it; assert either (a) the scope's event log does not contain `StateTransitioned(to_state=completed)`, or (b) it does. Answer determines whether the pre-check needs to intercept *before* the append (hooking into the runtime at a different point) or whether post-append is fine.

Hypothesis: post-append is fine — the raise surfaces as an escalation notification, the scope's projection shows `completed`, but the episode remains `running` in self-correction's sidecar until records land. Verify.

### 11.3 OTel-anomaly poll interval under sustained failure

Question: at `aggregator_poll_interval_seconds=30`, does the 30-second window introduce problematic latency between a failing span and correction scope opening? If a 30s poll catches 50 ERROR spans, does the primitive open 50 correction scopes (cascade escalation immediate) or dedup against the same trace_id prefix?

**Prototype shape:** generate 50 synthetic ERROR spans with same `scope_id`; run one poll; assert dedup produces ≤1 trigger per `(scope_id, anomaly_kind)` pair. Answer informs dedup rule granularity for anomaly source specifically (§2.1's dedup is keyed on `(scope_id, trigger_source, reason)` — prototype verifies this is the right granularity for anomalies, or whether `(trace_id, anomaly_kind)` is better).

---

## 12. Halt signals / cases the plan did not anticipate

One halt-level finding, raised in §0.2 above and repeated here for the primary persona's triage visibility.

### 12.1 Review-scopes are not a first-class concept (halt signal, mitigable)

- **Failure mode:** the plan treats review-scopes as if they exist and carry a `verdict` attribute on terminal state. They do not. There is no code in `scope-of-work/src/` matching `verdict` or `review`.
- **Impact on design:** the trigger-source for review verdicts cannot be an emitter subscription. It has to be an IPC call from whoever plays the reviewer role.
- **Sidecar alternative applied (not an amendment):** IPC method `correction.report_review_verdict(scope_id, verdict, reasons, reporter)`. Reviewer (human, scope, persona, external) calls this when they produce a fail verdict. Zero amendment to scope-of-work. When/if a "review-scope" primitive lands later, it calls the same IPC — no migration.
- **Decision needed:** the owner to confirm the IPC-convention approach is acceptable. Alternatives:
  1. (recommended) IPC convention as above.
  2. Wait for review-scopes to be a Phase 4 component before trigger source #3 fires. Trigger #3 is a no-op until then; §2.1 lists only three active sources.
  3. Amend scope-of-work to add a review-scope type. Rejected — sealed component, would require a new research cycle.

**Recommendation: option 1.** Non-blocking for build.

---

## 13. Open questions requiring ruling recorded

1. **Review-verdict trigger shape.** Per §12.1, confirm IPC-convention approach (recommended) vs defer trigger source #3 to Phase 4.
2. **OTel-anomaly definition scope.** Start with simplest anomaly definition (`status==ERROR` + `retention_class==high`) and defer richer P99-sliding-window detection, or build both now? (the primary persona recommends defer; it keeps the build under red-line.)
3. **Budget-scale factor default.** Plan proposes 0.5; floors at 60s / 2000 tokens. Any adjustment? (the primary persona recommends accept defaults.)
4. **User-reported IPC callers.** Any callers beyond primary-persona session? E.g. the nested sub-workspace, external hooks. Recommendation: scope to primary-persona only for v1; add callers as explicit authorisation later.

None of the four blocks build; all can be defaulted and adjusted.

---

## 14. Summary

- **No new activation wrap.** Three sidecar tables + three subscription surfaces + four IPC methods. Sidecar-only pattern holds cleanly through every refusal surface examined.
- **Four-part protocol enforced structurally.** Pydantic-typed records + completion pre-check raise = cannot mark `completed` without all four. Same clause-(g) pattern as self-upgrade.
- **No amendments to any sealed component.** One factual correction to the plan (review-scopes don't exist in scope-of-work) resolved with an IPC convention, not an amendment.
- **All gates fire; no bypass.** Correction scopes declare `compensatable`, register a binding, count against cost ceilings, are subject to safety.
- **Recursion-bounded.** Depth cap 3 + same-class-in-window (3 / 600s) escalation. Both logged; both notify via `OneOnOneChannel`.
- **OTel-visible.** `trace.get_tracer("pos.self_correction")` — A1 held.
- **Estimate 28–35 AI-min; anchor ~32; under red-line 40.**
- **Seal-test pattern mandatory.** `SEAL_COMMIT`-pinned `test_no_sealed_amendments.py`, baseline `04951b6` (cost-governance seal). HEAD-based variant is the bug from `f94d602`; do not reintroduce.

Ready for build dispatch on ruling recorded on §13 open questions (or acceptance of defaults).
