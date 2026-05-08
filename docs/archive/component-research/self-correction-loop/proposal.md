# Proposal — Self-Correction Loop

**Component:** Self-Correction Loop — detects system errors from four trigger sources (failed scope, OTel anomaly, review verdict, user correction), opens correction scopes that structurally honour the four-part protocol (class → instance → cause → remedy), and composes with the three-gate chain (safety + reversibility + cost) without adding a fourth wrap or bypassing any gate.
**Status:** DRAFT — awaiting owner's approval before brief authoring.

**Branch:** `pos-v2`. **Language:** Python 3.13.
**Consumes (no amendment):** scope-of-work, safety-layer, reversibility-primitive, cost-governance, orchestrator, observability-aggregator, primary-persona-layer.
**Phase 3 closes on this seal.**

---

## 1. Objective

Deliver self-correction such that:

- Four detection surfaces produce typed `CorrectionTrigger` records: scope-failure via pyee, OTel-anomaly via polling the aggregator, review-verdict via an IPC convention, user-report via an IPC call from a primary-persona session.
- On each trigger (after dedup + depth + cascade checks), the primitive opens a correction scope via the standard `activate_scope` path. The scope flows through the existing three gates — no bypass, no special path.
- The correction scope cannot reach `completed` without four typed records in the sidecar: `FailureClassIdentified`, `InstanceFixed`, `CauseDiagnosed`, `StructuralRemedyApplied`. A pyee-subscribed terminal-transition pre-check raises `-32070 CORRECTION_INCOMPLETE_RECORDS` otherwise.
- Recursion is bounded: depth cap 3 plus same-class-in-600s-window detection (threshold 3). Escalation on either bound fires a one-on-one channel notification.
- Refusals from cost governance are caught and escalated to the user; correction never silently drops.
- All correction activity emits `loam.correction.*` spans via the aggregator's registered provider.

The design and acceptance evidence are in `research.md`; this proposal encodes the owner's four rulings and states the hard contract.

---

## 2. the owner's rulings (locked inputs)

| # | Question | Ruling |
|---|----------|--------|
| 1 | Review-verdict trigger shape | **IPC convention.** `correction.report_review_verdict(scope_id, verdict, reasons, reporter)`. Any reviewer — persona, scope acting as reviewer, external harness — invokes on `verdict=="fail"`. No scope-of-work amendment; no Phase-4 block. |
| 2 | OTel-anomaly detection scope | **Simplest first.** v1.0 ships `status == "ERROR"` AND `retention_class == "high"` as the anomaly predicate. P99 sliding-window detection deferred to v1.1 or later. |
| 3 | Correction-scope budget defaults | **Scale 0.5** of the triggering scope's budget on time and token axes, with floors **60 seconds** and **2,000 tokens**. Cost refusals at the gate are caught and escalated — self-correction never silently reduces below declared to fit. |
| 4 | `correction.user_reported` IPC callers | **Primary-persona callers only for v1.** Caller identity enforced at the IPC boundary. Additional callers (the nested sub-workspace, external hooks) added by explicit authorisation later. |

---

## 3. Design shape (summary — detail in `research.md`)

### 3.1 Composition

A new package `self-correction/` (Python, on `pos-v2`) exposes `SelfCorrectionController`:

- **`CorrectionTrigger`** — normalised Pydantic record covering all four sources (`trigger_id`, `source ∈ {scope_failure, otel_anomaly, review_verdict, user_reported}`, `scope_id?`, `trace_id?`, `failure_class_hint?`, `raw_payload`, `received_at`). `extra="forbid"`, `frozen=True`.
- **`CorrectionEpisode`** — the sidecar record for a correction-in-progress. Carries `episode_id`, `trigger_id`, `correction_scope_id`, `parent_correction_id` (for depth walk), `failure_class`, `opened_at`, `state ∈ {running, completed, escalated, refused}`.
- **Four record types** for the four-part protocol, all Pydantic with `extra="forbid"`, `frozen=True`: `FailureClassIdentified`, `InstanceFixed`, `CauseDiagnosed`, `StructuralRemedyApplied`. Persisted to `correction_episode_records` with `UNIQUE(episode_id, record_type)`.
- **Detection surfaces** — four intake paths into one internal queue:
  - pyee subscription on `ScopeRuntime.emitter.on("*")` filtered on `StateTransitioned(to_state=failed)` excluding gate-refusal reasons (`^safety-gate/`, `^cost-ceiling/`, `^reversibility-gate/`, `cancelled`, `escalated`).
  - Polling loop (default 30s) against `observability-aggregator.QueryAPI.find_spans(SpanFilter(status="ERROR", retention_class="high"))`.
  - IPC `correction.report_review_verdict(scope_id, verdict, reasons, reporter)` — records only on `verdict=="fail"`.
  - IPC `correction.user_reported(description, related_scope_id?)` — caller-identity check enforces primary-persona-only.
- **Trigger dedup** — sidecar `correction_trigger_dedup` keyed on SHA-256 of `(scope_id, source, normalised_reason)` with 60s TTL.
- **Depth + cascade checks** — at trigger intake, before `activate_scope`: walk `parent_correction_id` for depth; count same-class episodes in the last 600s. Either bound trips escalation and refuses to open a correction scope.
- **Spec builder** — deterministic `build_correction_spec(trigger) -> ScopeSpec` with objective text from a template, `reversibility_class="compensatable"` forced (declaring `irreversible` is refused at build time), and budget inherited-and-scaled per ruling #3.
- **Compensation binding** — registered at scope construction via reversibility's `register_compensation` IPC; the handler reverts the structural remedy from the episode's records.
- **Completion pre-check** — pyee subscription on the correction scope's own emitter for `StateTransitioned(to_state=completed)`. Queries `correction_episode_records` for the four record types. If any missing, raises `-32070 CORRECTION_INCOMPLETE_RECORDS` before the transition commits.
- **OTel** — spans via `trace.get_tracer("loam.self_correction")`. Enumerated names in research §2.5.
- **Notification** — `OneOnOneChannel` subclass (`CorrectionChannel`); inherits `is_group=True` refusal.
- **CLI** — `pos correction status`, `pos correction episode <id>`, `pos correction history --class <name>`, `pos correction trigger --source user --description "..."`.

### 3.2 No new activation wrap

Self-correction is the first Phase 3 component that is a **pure consumer** of the three-gate chain. All refusal surfaces live outside the activation path:

- Spec validation (reversibility_class != irreversible) runs at `build_correction_spec` time, before any IPC call.
- Depth and cascade checks run at trigger intake, before `activate_scope`.
- Completion pre-check runs on the scope's own terminal-transition subscription, after `activate_scope` has long since completed.

The registration order and dispatch order of the three-gate chain (safety → reversibility → cost → orig_activate) is unchanged.

### 3.3 Refusal boundary

Reserve `-32070..-32079` to self-correction. Ship one error code:

- `-32070 CORRECTION_INCOMPLETE_RECORDS` — terminal-transition pre-check refusing `completed` without all four records.

`-32071..-32079` reserved for future (richer anomaly classes, cascade-specific codes if diagnostics demand differentiation).

Cost refusals (`-32060..-32062`) encountered when opening a correction scope are caught at the self-correction layer and turned into a user-facing escalation notification — they are not self-correction's own error codes, merely propagated.

### 3.4 SQLite store at `~/.pos/correction/correction.sqlite`

Four tables — all WAL + `synchronous=FULL` + `foreign_keys=ON`:

- `correction_triggers` — the intake log.
- `correction_episodes` — one row per opened or refused episode; `parent_correction_id` FK-self for depth walk.
- `correction_episode_records` — the four record types; `UNIQUE(episode_id, record_type)`.
- `correction_trigger_dedup` — hash + expires_at; pruned by TTL.

---

## 4. Acceptance criteria (ODD — 24 objectives)

### 4.1 Detection surfaces

- **CR1.** A scope-of-work `StateTransitioned(to_state=failed)` event with `reason` not matching the exclusion prefix fires a `CorrectionTrigger(source="scope_failure")` within one event-loop tick.
- **CR2.** A `StateTransitioned(to_state=failed, reason="safety-gate/ask-refused")` does NOT fire a trigger. (Gate-refusal exclusion.)
- **CR3.** An aggregator poll that finds a span matching `status="ERROR"` AND `retention_class="high"` fires a `CorrectionTrigger(source="otel_anomaly")`. The poll interval defaults to 30s; a bare `status=="ERROR"` without the retention_class match does NOT fire. (Locks ruling #2.)
- **CR4.** `correction.report_review_verdict(scope_id, verdict="fail", reasons, reporter)` IPC fires a `CorrectionTrigger(source="review_verdict")`. `verdict="pass"` fires no trigger.
- **CR5.** `correction.user_reported(description, related_scope_id?)` called from a primary-persona session fires a trigger; the same call from a non-persona caller is refused at the IPC boundary. (Locks ruling #4.)
- **CR6.** Trigger dedup: the same trigger fired twice within 60s produces exactly one episode; the second emits `loam.correction.trigger_deduplicated` and persists to the dedup table.

### 4.2 Four-part structural enforcement

- **CR7.** A correction episode with fewer than four record types at `completed`-transition time raises `-32070 CORRECTION_INCOMPLETE_RECORDS`. Enforced via `UNIQUE(episode_id, record_type)` lookup returning a set and comparing against `{class, instance, cause, remedy}`.
- **CR8.** All four record types present → the terminal transition proceeds normally; episode state flips to `completed`; `loam.correction.closed` span emits.
- **CR9.** Record authoring via `correction.record_part(episode_id, part_type, payload)` IPC validates the Pydantic payload; malformed payloads rejected with `-32602 INVALID_PARAMS`. No LLM inference inside the validator.
- **CR10.** Record ordering is any-order but order-preserving: the persisted `at` timestamp on each record tells the real story.

### 4.3 Correction scope opening

- **CR11.** `build_correction_spec(trigger)` produces a `ScopeSpec` with `reversibility_class="compensatable"`. Attempting to build one with `irreversible` raises at the builder (structural refusal).
- **CR12.** Budget is inherited from the triggering scope and scaled by 0.5 on time/tokens axes. Floors: 60s time and 2000 tokens apply before scaling so a very small triggering scope still produces a workable correction budget. (Locks ruling #3.)
- **CR13.** Compensation-path binding is registered with reversibility at scope construction; the registered handler reverts the structural remedy from the episode's records.
- **CR14.** `activate_scope` for the correction spec flows through the full three-gate chain. Safety, reversibility, and cost each get their normal turn.

### 4.4 Recursion bound

- **CR15.** Trigger-intake depth walk: an incoming trigger whose parent chain already has 3 correction episodes does NOT open a fourth; instead `CorrectionCascadeEscalated(reason="depth_cap")` is recorded and a `OneOnOneChannel` notification fires. Episode state is `escalated`.
- **CR16.** Same-class cascade: three or more episodes of identical `failure_class` opened within 600s trigger a `CorrectionCascadeBySameClass` escalation regardless of depth. Same notification path.
- **CR17.** `parent_correction_id` is set at episode creation by matching the triggering scope_id against the in-memory map of running correction scopes.

### 4.5 No-bypass composition

- **CR18.** A correction scope whose planned dangerous-op action hits the safety dangerous-op gate produces `-32041 DANGEROUS_OP_GATE_BLOCKED`; correction does not bypass. Integration test via mock reviewer + mock dangerous-op payload.
- **CR19.** A correction scope whose budget exceeds the session ceiling produces `-32061 COST_SESSION_CEILING_EXCEEDED`; self-correction catches the `ApplicationError`, records episode state as `refused`, and dispatches a `OneOnOneChannel` notification. Silent drop is refused.
- **CR20.** Reversibility rollback of a correction scope invokes the registered compensation handler, which restores the target file/rule from the pre-remedy snapshot.

### 4.6 Cross-cutting integration

- **CR21.** `git diff --stat 04951b6..<self-correction-seal>` shows only `self-correction/` changes. Zero deltas to any sealed component.
- **CR22.** OTel spans flow through `trace.get_tracer("loam.self_correction")`; no `TracerProvider` construction.
- **CR23.** All user-facing escalation notifications use `CorrectionChannel` (subclass of `OneOnOneChannel`); group-channel refusal inherited.
- **CR24.** `test_no_sealed_amendments.py` pins to `SEAL_COMMIT` constant (populated at seal time), diffs `04951b6..SEAL_COMMIT`, NOT `..HEAD`. (Structural remedy from commit `f94d602` — do not reintroduce the HEAD-based bug.)

---

## 5. Constraints

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** Halt and signal with named component + surface + sidecar alternative if you believe an amendment is required.
- **No new activation wrap.** Self-correction is a consumer, not a gate. If you find a case where a wrap is genuinely needed, halt and signal.
- **No bypass of safety / reversibility / cost.** Correction scopes are scopes; they flow through the three gates.
- **Four-part protocol is structural.** A correction scope cannot reach `completed` without all four records. No advisory enforcement.
- **Recursion bounded.** Depth cap 3; same-class-in-600s threshold 3.
- **Refusals escalated, never silently dropped.** Cost-ceiling refusals catch-and-notify via `OneOnOneChannel`.
- **A1 correction held.** `trace.get_tracer(...)` only.
- **One-on-one channel only** for notifications.
- **Error-code range `-32070..-32079`.**
- **Seal-test pattern mandatory.** `SEAL_COMMIT` constant; no `..HEAD`.
- **Max-first.** No LLM inference inside the primitive.
- **Zero carryover from current pOS.**
- **Halt on deviation.**

---

## 6. Suggested file layout

```
self-correction/
  src/
    spec.py              # CorrectionTrigger, CorrectionEpisode, four record types, error codes
    config.py            # CorrectionConfig loader (depth_cap, windows, floors, poll interval)
    store.py             # SQLite schema + upsert/query for four tables
    triggers.py          # four intake paths normalised to CorrectionTrigger
    dedup.py             # hash + TTL logic
    bounds.py            # depth walk + same-class cascade detection
    spec_builder.py      # build_correction_spec(trigger) -> ScopeSpec
    controller.py        # SelfCorrectionController composed runtime
    completion_check.py  # pyee terminal-transition pre-check for four-record enforcement
    observability.py     # loam.correction.* span helpers
    notification.py      # CorrectionChannel (OneOnOneChannel subclass)
    cli.py               # pos correction ... subcommands
    ipc.py               # correction.record_part, correction.report_review_verdict, correction.user_reported
  tests/
    test_detection_scope_failure.py     # CR1, CR2
    test_detection_otel_anomaly.py      # CR3
    test_detection_review_verdict.py    # CR4
    test_detection_user_reported.py     # CR5
    test_trigger_dedup.py               # CR6
    test_four_part_enforcement.py       # CR7, CR8 (one case per missing record)
    test_record_authoring.py            # CR9, CR10
    test_spec_builder.py                # CR11, CR12
    test_compensation_binding.py        # CR13
    test_gates_flow_through.py          # CR14
    test_depth_cap.py                   # CR15
    test_same_class_cascade.py          # CR16
    test_parent_linking.py              # CR17
    test_no_bypass_safety.py            # CR18
    test_cost_refusal_escalates.py      # CR19
    test_rollback_reverts.py            # CR20
    test_no_sealed_amendments.py        # CR21 (with SEAL_COMMIT pinned)
    test_observability_routing.py       # CR22
    test_one_on_one_channel_only.py     # CR23
```

File cohesion is the builder's judgement. Test list is the minimum mapped to the acceptance criteria.

---

## 7. Build phases and estimate

**Calibrated AI-time estimate: 28–35 minutes wall-clock. Red line at 40.**

Anchors: cost-governance ~16.5 min (simpler — no sidecar cascade, fewer scenarios), reversibility ~30 min (comparable sidecar complexity but with two wraps, which self-correction doesn't have). Self-correction's no-wrap simplicity offsets its richer state-machine logic (four sidecar tables, OTel poller, depth + cascade).

**If the build exceeds 40 minutes, halt and signal.** Two named failure classes to investigate: (a) sophisticated OTel-anomaly detection (P99 sliding windows etc) that was supposed to be deferred per ruling #2, or (b) in-component user-intent parsing that belongs in the primary persona, not here.

Suggested phase shape (builder's call):

1. Pydantic schemas + store (four tables) — CR7 matrix + CR11 + CR27-style structural defences.
2. Spec builder with `irreversible`-refusal — CR11, CR12.
3. Trigger intake paths (four sources) + normalisation + dedup — CR1–CR6.
4. Depth + cascade bounds — CR15, CR16, CR17.
5. Compensation-binding registration — CR13.
6. Completion pre-check on correction scopes — CR7, CR8.
7. Cost-refusal catch-and-escalate — CR19.
8. OTel emission + notification channel — CR22, CR23.
9. CLI + IPC surfaces — CR9, CR10.
10. Integration tests for the gate-flow + structural remedies — CR14, CR18, CR20, CR21.

Atomic commits per phase acceptable; single cohesive commit acceptable.

---

## 8. inferences recorded — flagged for the builder to challenge

These items are the primary persona's extrapolation rather than the owner's direct words; challenge any with a halt signal and proposed alternative:

1. **Exclusion prefixes for gate-refusal `reason` strings.** Research proposed `^safety-gate/`, `^cost-ceiling/`, `^reversibility-gate/`. If the actual reason strings emitted by the three gates don't match these prefixes (verify at build time), the pattern widens silently. Challenge with the observed strings.
2. **Dedup TTL 60s.** Anchored on cost-governance's notification-dedup TTL. If 60s produces double-firing on real-world trigger bursts, challenge.
3. **Aggregator poll interval 30s.** Reasonable default; research §11.3 flagged this as prototype territory. If 30s causes sustained-failure problems (50 spans in one poll), the dedup granularity may need tightening to `(trace_id, anomaly_kind)` rather than `(scope_id, source, reason)`.
4. **Cascade window 600s + threshold 3.** the primary persona's defaults. If longer windows and/or higher thresholds serve the user better in practice, challenge.
5. **Correction scope objective template text.** drafted as `"Correct failure class '<class>' surfaced by <trigger_source>. Apply the four-part protocol..."`. Builder may refine wording if more specific phrasing helps the LLM execution produce better records.
6. **Four-part record shape field names.** Proposed in research §2.2 — `class_name`, `fix_description`, `root_cause`, `change_description` etc. If different field names compose better with existing primary-persona authoring patterns, challenge.
7. **`CorrectionChannel` subclass naming.** Pattern borrowed from cost's notification subclass. Challenge if the owner has a preferred name or if the notifier can use the existing `CorrectionChannel` equivalent from primary-persona without a new subclass.
8. **OTel span names with `loam.correction.*` prefix.** Parallel to `loam.cost.*`, `loam.reversibility.*`, `loam.safety.*`. Challenge if the convention is meant to be `loam.self_correction.*` (matching the tracer name); the research used `loam.correction.*` throughout — the primary persona carried that forward.

---

## 9. Approval ask

sign-off on this proposal moves the component to `proposal_approved` and opens handoff-brief drafting. On brief review, the background agent is dispatched. **Phase 3 closes on self-correction's seal.**

Specifically requesting approval of:

- The locked rulings in §2 as faithful to the conversation.
- The 24 ODD acceptance criteria in §4 (CR1–CR24) as the complete objective set.
- The constraints in §5 (no new wrap, no bypass, structural four-part, seal-test pattern, error-code range).
- The 28–35 min estimate with 40-min red line.
- the primary persona's flagged inferences in §8 (approve as written, or adjust and re-land).

Approve as-is, approve with changes, or reject.
