# Research Plan — Self-Correction Loop

**Component:** Self-Correction Loop — detects system errors (failed scope, OTel anomaly, review verdict, user correction) and opens correction scopes that follow the four-part structural-remedy contract (name the class, fix the instance, diagnose the cause, apply the structural remedy), composing with safety / reversibility / cost-governance gates without bypassing any.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for self-correction such that:

- Detection surfaces produce typed `CorrectionTrigger` events from at least four sources: failed scope (pyee), OTel anomaly (threshold violation on observability-aggregator spans), review verdict (review-scope terminal state with verdict=fail), user correction (explicit IPC call from a primary-persona session).
- On each trigger, the loop opens a correction scope that structurally honours the four-part protocol: name the failure class, fix the specific instance, diagnose the systemic cause, apply a structural remedy that closes the class.
- Correction scopes flow through the full four-wrap chain (safety → reversibility → cost → orig_activate); no bypass paths exist. A correction scope that would blow the session ceiling is refused by cost governance, same as any other scope.
- Cascading correction failures are bounded. A correction that itself produces a trigger could open a correction-of-correction; depth must be capped and escalated to the user at the cap.
- Correction activity is OTel-visible as first-class spans with the trigger source and the remedy applied.
- Integration with sealed components is clean: self-correction reads triggers from scope-of-work emissions + observability-aggregator spans + review-scope terminal states; opens correction scopes via the standard `activate_scope` path; owns its own sidecar state for trigger-history and remedy-records.

## Starting position

- **Eleven components on `pos-v2`:** seven foundational + self-upgrade + safety + reversibility + cost-governance (sealed). Self-correction is Phase 3's final component.
- **Detection surfaces already emit enough signal:**
    - Scope failure: `ScopeRuntime.emitter` fires `StateTransitioned(to_state=failed)` (verified during reversibility research).
    - OTel: observability aggregator stores spans in DuckDB and already has a query surface (verified during its build).
    - Review verdicts: reviewers are scopes themselves; their terminal state with `verdict` attribute is the signal.
    - User correction: primary-persona can invoke an IPC method; this is the surface self-correction needs to register.
- **Four-part protocol is an operating rule, not a data model.** It lives in `prior-pOS .claude/rules/prime.md` as advisory prose. Self-correction makes it structural by requiring every correction scope to emit four typed records — `FailureClassIdentified`, `InstanceFixed`, `CauseDiagnosed`, `StructuralRemedyApplied` — and refusing to reach `completed` until all four are recorded.
- **Sidecar/wrap precedent established quadruply.** Sidecar `CorrectionTrigger` + `CorrectionEpisode` tables owned by the component; activation gate if needed at all (see Q-group 7 below — correction opens scopes via the existing gates rather than intercepting them).
- **Python 3.13, `pos-v2` branch.** Permitted deps as per standard.

## Questions the research must answer

### 1. Detection surfaces — what produces a `CorrectionTrigger`?

1. Scope-failure trigger: subscribe to `ScopeRuntime.emitter` for `StateTransitioned(to_state=failed)`. Verify the event carries enough context (`scope_id`, `reason`, `failure_metadata` or equivalent); if not, halt and signal. Which failures should trigger correction (all? only those with a specific `reason` tag? exclude safety-gate refusals so the gate itself doesn't recurse)?
2. OTel-anomaly trigger: the observability aggregator stores spans. What's the query surface — does it expose a "anomaly detection" primitive, or does self-correction run its own queries against DuckDB? Design principle: self-correction is a consumer, not an aggregator modifier.
3. Review-verdict trigger: verify review-scopes are a first-class concept on scope-of-work. Their terminal state carries `verdict`; self-correction subscribes to review-scope terminals and triggers on `verdict=fail`.
4. User-correction trigger: IPC method `correction.user_reported(description, related_scope_id?)`. Workspace-facing; corrupts the correction log with a user-authored entry.
5. Trigger deduplication: two failure signals within N seconds on the same `scope_id` should produce one trigger, not two. What's N (60s? event-hash-based)?

### 2. Correction episode — the four-part structural enforcement

6. How is the four-part protocol structurally enforced? Default assumption: a correction scope cannot reach `completed` state until it emits four typed records in its scope-of-work event log: `FailureClassIdentified`, `InstanceFixed`, `CauseDiagnosed`, `StructuralRemedyApplied`. The completion pre-check runs as a pyee-subscribed handler; if any of the four is missing, the correction scope is auto-escalated to the user.
7. Ordering: do the four records have to be emitted in protocol order (class → instance → cause → remedy), or is any order acceptable as long as all four exist by completion? Default: any order, but the ordering is recorded and surfaced in the episode log.
8. What exactly goes in each record? Pydantic shapes proposed:
    - `FailureClassIdentified{class_name, description, similar_prior_count}` — the class is a short name (`state-but-defer`, `verify-before-escalate`, etc.).
    - `InstanceFixed{scope_id_affected, fix_description, artifact_paths?}`.
    - `CauseDiagnosed{root_cause, evidence_refs}`.
    - `StructuralRemedyApplied{change_description, target_file_or_rule, verification_path}`.
9. Who authors these records? Primary assumption: the correction scope's own LLM work authors them as it runs. The sidecar stores the records; scope-of-work events are the authoritative copy.

### 3. Correction scope — how it's opened

10. Entry point: the self-correction runtime receives a `CorrectionTrigger`, constructs a `ScopeSpec` for the correction scope, and calls `activate_scope` via IPC — same path a workspace uses for any scope. No bypass, no sidechannel.
11. What's the scope's objective text? Generated from trigger: "correct `<failure_description>` surfaced by `<trigger_source>`." The scope author is the self-correction runtime's own template builder (deterministic) rather than an LLM, though the scope's *execution* is LLM-driven.
12. What `reversibility_class` does the correction scope declare? Default `compensatable`: a correction that applies a structural remedy has side effects (file edits, rule changes) that may need unwinding. The reversibility primitive's compensation-path registration is therefore required; the correction runtime registers it at scope construction time.
13. What `budget` does the correction scope declare? Default budget proposed: inherit from the triggering scope's own budget, scaled down (50%?) to leave headroom in the session. If the session ceiling would be exceeded, cost governance refuses — and self-correction surfaces the refusal to the user rather than silently dropping.

### 4. Recursion bound — correction of correction

14. Correction scope A runs; its own work triggers a failure; that produces another `CorrectionTrigger`; the runtime opens correction B on A. Depth must be bounded.
15. What's the depth cap? Default proposed: 3. At depth 3, the trigger is not acted on by opening another scope; it's escalated to the user via the one-on-one channel as "correction cascade — manual intervention needed."
16. How is depth tracked? A `parent_correction_id` foreign key on the correction-episode record; depth = walk-up count. Simple.
17. Cascade detection: does the system detect "the same failure class has triggered 3 corrections in 10 minutes" and escalate even within the depth cap? Tentatively yes — same-class repeats within a short window are a specific anti-pattern (quality-standards.md rule 15's "repeated correction" pattern).

### 5. Integration with safety / reversibility / cost

18. Safety layer — does correction-loop require any safety-layer coordination beyond the activation gate composing normally? Tentative no: a correction that would do a dangerous-op action (send comms, commit funds) gets its safety gate just like any other scope. The correction runtime does NOT bypass safety "because it's correction."
19. Reversibility — correction scopes default to `compensatable` (Q12). What does the compensation path actually do? Proposed: the correction's compensation is a "rollback-to-pre-correction" scope that removes the file changes / rule edits from the structural remedy.
20. Cost — correction scopes count against session and rolling-window ceilings. A session where correction loops are eating budget will hit the ceiling and be refused; this is correct behaviour. No bypass.
21. Observability aggregator — self-correction emits `pos.correction.*` spans. No aggregator amendment needed.

### 6. Primary-persona integration

22. The primary persona's operating rule (four-part correction protocol in `prime.md`) is exactly what this component structurally enforces. Does the primary persona's runtime need to know about self-correction, or does self-correction subscribe transparently?
23. How does a user-initiated correction from the primary persona's one-on-one channel reach the correction runtime? IPC `correction.user_reported` — the persona's message handler parses a correction intent and calls the IPC.
24. Escalation to user: when the depth cap fires, or when a structural-remedy is deferred beyond the correction scope's own budget, who notifies the user — the correction runtime directly (via `OneOnOneChannel`), or does the primary persona mediate? Default: direct dispatch via `OneOnOneChannel` — the persona observes the notification but does not gate it.

### 7. Deterministic enforcement pattern (sidecar/wrap)

Default assumption per quadruple precedent: sidecar tables own the trigger log + episode records; the correction runtime does not intercept `activate_scope` (it uses it, it does not wrap it). **This is the first Phase 3 component that does not add a new activation wrap** — self-correction is a consumer of the activation path, not a gate on it.

25. Confirm or rebut the "no new wrap" design. The correction runtime subscribes to emissions, opens scopes through the standard path, and records state in its own sidecar. If any refusal shape genuinely needs a wrap (e.g. "correction scopes must declare specific metadata"), halt and signal with a named failure mode and the sidecar alternative.
26. Pydantic shapes: `CorrectionTrigger`, `CorrectionEpisode`, and the four record types. Apply the clause-(g) pattern — an episode without all four records cannot be marked `completed` at the schema level.

### 8. Testing discipline

27. Synthetic detection: tests construct fake failed scopes, fake OTel anomalies, fake review verdicts, and fake user-correction IPC calls; assert each produces the correct `CorrectionTrigger`.
28. Four-part enforcement: a correction scope that emits only three records cannot reach `completed`; it auto-escalates. Test one case per missing record.
29. Recursion-bound: construct a trigger that deterministically produces another trigger; assert depth cap fires at 3 and the user is notified.
30. Cost-ceiling interaction: construct a trigger whose correction scope's declared budget would exceed the session ceiling; assert cost governance refuses; assert the user is notified rather than silent drop.

## Constraints the research must respect

- **Python-native.** Permitted runtime as enumerated.
- **No amendments to sealed components.** Default: sidecar + subscription + scope-of-work consumer pattern. Halt and signal only with a named failure mode.
- **No new activation wrap.** Self-correction consumes the four-wrap chain; it does not add a fifth.
- **Four-part protocol is structural, not advisory.** A correction scope that skips any of the four records cannot reach `completed`.
- **No bypass of safety / reversibility / cost.** Correction scopes are scopes; they flow through the same gates.
- **Recursion-bounded.** Depth cap + cascade-detection escalate to the user.
- **A1 correction held.** OTel via aggregator's registered provider.
- **One-on-one channel only** for user-facing correction surfaces.
- **Zero carryover from current pOS.**
- **Halt-on-deviation.**
- **Seal-test pattern (new):** the component's `test_no_sealed_amendments.py` must pin to a `SEAL_COMMIT` constant, not `HEAD` — see BACKLOG note from cost-governance build. This applies from this component forward to all Phase 3+ components.

## Deliverable — what the research document must contain

A markdown document at `components/self-correction-loop/research.md` with:

1. **Survey of existing patterns** — retry patterns (exponential backoff, circuit breaker), supervisor trees (Erlang OTP), exception-handling philosophies (Rust's `Result`, Go's explicit error return), AI-agent self-reflection loops (constitutional AI, reflection agents).
2. **Recommended design shape** — for each of the eight question groups, options considered, recommended option, rationale.
3. **Clause-by-clause spec coverage** — each acceptance criterion mapped to a design piece.
4. **Four-part protocol specification** — concrete Pydantic shapes, event ordering (or lack thereof), completion pre-check mechanism.
5. **Recursion-bound specification** — depth tracking, cascade detection, escalation path.
6. **Detection-surface specification** — four trigger sources, dedup semantics, trigger-to-scope flow.
7. **Integration sequence diagrams** — trigger → correction scope → reconciliation; cascade escalation; user-initiated correction flow.
8. **Relationship to safety / reversibility / cost** — which gates fire; nothing is bypassed.
9. **Dependency map** — consumed by: none (this is Phase 3's final component; Phase 4 begins after). Depends on: scope-of-work, safety, reversibility, cost-governance, orchestrator, observability-aggregator, primary-persona-layer.
10. **Complexity estimate** — AI-time calibrated against cost-governance (~16 min), reversibility (~30 min), safety (~35 min). Self-correction is structurally less gate-heavy than cost (no wrap) but has more state-machine logic (four-part enforcement, recursion tracking). Anchor 25–35 AI-min wall-clock; red-line 40.
11. **Prototyping priorities** — questions only a prototype can answer (e.g. whether pyee subscription ordering is reliable under cascade conditions; whether the four-part completion pre-check composes cleanly with scope-of-work's existing terminal-transition hooks).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies. Sidecar + subscription is the default per quadruple precedent; activation wrap is NOT expected. The seal-test pattern (pin to own-seal commit) is mandatory from this component forward.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
