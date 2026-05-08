# Handoff Brief — Self-Correction Loop

**For:** the general-purpose Agent dispatched to build self-correction.
**From:** the primary persona, 2026-04-20 11:24 CDT.
**Status:** awaiting owner's review of this brief; not yet dispatched.
**Phase 3 closes on this component's seal.**

---

## 1. What you are building

The self-correction component for pOS on the `pos-v2` branch of `the existing workspace root`. It detects system errors from four trigger sources (failed scope, OTel anomaly, review verdict, user-reported) and opens correction scopes that structurally honour the four-part protocol (`FailureClassIdentified`, `InstanceFixed`, `CauseDiagnosed`, `StructuralRemedyApplied`). It composes with the existing three-gate chain (safety + reversibility + cost) via consumption only — **no fourth wrap**.

The work is greenfield Python on `pos-v2`. It consumes every sealed component — including the three Phase 3 gates already landed — as read-only surfaces.

## 2. Authoritative documents (read in this order)

1. **This brief** — operational form of the objective, constraints, acceptance criteria.
2. **`docs/rebuild/components/self-correction-loop/proposal.md`** — the contract approved. Binding. Halt and signal rather than deviate.
3. **`docs/rebuild/components/self-correction-loop/research.md`** — design detail, prior-art survey, sequence diagrams, SQL schema, Pydantic shapes. Reference only; the proposal is the contract.
4. **`docs/rebuild/spec/loam-objectives-spec.md`** — spec v1.0 + v1.1 + v1.2 addenda.
5. **`docs/rebuild/STATE.md`** — governing rules for the rebuild.
6. **`prior-pOS .claude/rules/prime.md`** — the four-part correction protocol lives here as prose. This component structurally enforces it.

**Precedents to emulate** (all on `pos-v2`, all sealed):
- `objective-tracker/src/store.py` — sidecar table pattern.
- `safety-layer/src/events.py` — structural-impossibility Pydantic pattern (clause-g).
- `reversibility-primitive/src/rollback.py` — FSM with state transitions via typed records.
- `cost-governance/src/ledger.py` — pyee multi-source subscription pattern.
- `cost-governance/src/notification.py` — `OneOnOneChannel` subclass pattern (the template for `CorrectionChannel`).
- `observability-aggregator` — `QueryAPI.find_spans(SpanFilter)` is the anomaly-poll read surface.

## 3. The objective (single sentence)

Deliver self-correction such that every incoming trigger (after dedup + depth-cap + same-class-cascade checks) opens a correction scope via the standard `activate_scope` path, every correction scope declares `compensatable` and flows through the three-gate chain unchanged, every correction scope is structurally refused at `completed` transition unless all four typed records are persisted, and cost-ceiling refusals are caught and escalated to the user rather than silently dropped — all without amending any sealed component and without adding any new activation wrap.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** Eleven are sealed. Halt and signal with named component + surface + sidecar alternative if you think one is required.
- **No new activation wrap.** Self-correction is a consumer, not a gate. If you find a case where a wrap is genuinely needed, halt and signal — the no-wrap contract is load-bearing for the design.
- **No bypass of safety / reversibility / cost.** Correction scopes flow through the three gates like any other scope. A correction that would blow the session cap is refused by cost and escalated to the user; a correction with an irreversible side effect requires a compensation-path binding (which the primitive registers at scope construction).
- **Structural four-part enforcement.** A correction scope cannot reach `completed` without all four record types in `correction_episode_records`. The pyee-subscribed terminal-transition pre-check raises `-32070 CORRECTION_INCOMPLETE_RECORDS` before the transition commits. No advisory enforcement; no LLM inside the pre-check.
- **Recursion bounded.** Depth cap 3 via `parent_correction_id` walk; same-class cascade detection with 600s window and threshold 3. Both escalate to the user via `CorrectionChannel` (one-on-one subclass).
- **Refusals escalated, never silently dropped.** Cost-ceiling refusals (`-32060/61/62`) are caught in `controller`-layer code and surfaced via `CorrectionChannel`; episode state becomes `refused`.
- **Gate-refusal reasons excluded from trigger intake.** `reason` strings matching `^safety-gate/`, `^cost-ceiling/`, `^reversibility-gate/`, or transitions to `cancelled`/`escalated` do NOT fire triggers. Verify the actual prefix strings against the gates' source; challenge the inference in proposal §8 #1 if they differ.
- **Per ruling recorded #1:** review-verdict trigger is the IPC convention `correction.report_review_verdict(scope_id, verdict, reasons, reporter)`. No scope-of-work amendment for review-scopes.
- **Per ruling recorded #2:** OTel-anomaly predicate is `status == "ERROR"` AND `retention_class == "high"`. P99 sliding-window detection is NOT in v1.0.
- **Per ruling recorded #3:** correction-scope budget inherits from triggering scope with scale 0.5, floors 60s time / 2000 tokens.
- **Per ruling recorded #4:** `correction.user_reported` enforces primary-persona-only caller identity at the IPC boundary.
- **Error-code range `-32070..-32079`** reserved to self-correction; no overlap with safety (`-32040..-32049`), reversibility (`-32050..-32059`), or cost (`-32060..-32069`).
- **A1 correction held.** `trace.get_tracer("pos.self_correction")` only; do not construct a `TracerProvider`.
- **One-on-one channel only** for every user-facing notification; inherit `is_group=True` rejection via `CorrectionChannel` subclass.
- **Seal-test pattern mandatory.** `test_no_sealed_amendments.py` must define a `SEAL_COMMIT` constant and diff `BASELINE..SEAL_COMMIT`, NOT `..HEAD`. Baseline is `04951b6` (cost-governance seal). Do not reintroduce the HEAD-based defect that was fixed on commit `f94d602`.
- **Zero carryover from current pOS.**
- **Max-first.**
- **Halt on deviation.**

## 5. Acceptance (ODD — 24 criteria, in proposal §4)

CR1–CR6: detection surfaces — four sources normalised, exclusion working, dedup on 60s TTL.
CR7–CR10: four-part structural enforcement — incomplete-records raise, Pydantic validation, order-recorded-but-not-prescribed.
CR11–CR14: correction scope opening — spec builder refuses irreversible, budget scale+floors, compensation binding registered, three-gate flow unchanged.
CR15–CR17: recursion bounded — depth cap 3, same-class cascade 3-in-600s, parent linking.
CR18–CR20: no-bypass composition — safety/cost/reversibility each fire normally on correction scopes.
CR21–CR24: cross-cutting — no sealed-component mutation, aggregator-routed OTel, one-on-one channel, seal-test pattern pinned.

Each criterion is an objective. Tests target it directly. Negative cases re-extend as positive objectives — if you find one worth naming, add as CR25+ with rationale in the commit message.

## 6. Verify-against-code discipline

Before relying on any sealed-component surface, open the file on `pos-v2` and confirm the symbol exists with the shape you expect. Four surfaces to verify first because the research's findings matter here:

- **`ScopeRuntime.emitter` wildcard subscription** — `emitter.on("*", handler)` pattern, precedent in `cost-governance/src/ledger.py`.
- **`StateTransitioned` envelope** — carries `scope_id`, `from_state`, `to_state`, `reason`, `pause_reason`, plus OTel identifiers. Verify `ScopeState.failed` is the correct enum value.
- **Gate-refusal reason string prefixes** — the exclusion pattern assumes `^safety-gate/`, `^cost-ceiling/`, `^reversibility-gate/`. Grep the three gate sources for the actual prefixes used when they raise and adjust the pattern accordingly. If the strings don't match a clean prefix pattern, halt and signal.
- **`observability-aggregator.QueryAPI.find_spans(SpanFilter)`** — the anomaly-poll read surface. Verify the filter supports `status="ERROR"` AND `retention_class="high"` as a combined query.

If any proposal-level claim doesn't match the code, halt and signal with the named file and symbol.

## 7. inferences recorded (proposal §8) — challenge any that feel wrong

Eight items are the primary persona's extrapolation rather than the owner's direct words:

1. Gate-refusal exclusion prefixes (`^safety-gate/`, `^cost-ceiling/`, `^reversibility-gate/`).
2. Trigger dedup TTL 60 seconds.
3. Aggregator poll interval 30 seconds.
4. Cascade window 600 seconds with threshold 3.
5. Correction scope objective template text.
6. Four-part record field names.
7. `CorrectionChannel` subclass name.
8. OTel span namespace `pos.correction.*` (vs `pos.self_correction.*` matching the tracer).

Challenge any with a halt signal and proposed alternative. Not load-bearing unless the owner confirms.

## 8. Estimate

**28–35 AI-minutes wall-clock. Red line at 40.**

Anchors: cost-governance ~16.5 min (simpler — no sidecar cascade, fewer scenarios), reversibility-primitive ~30 min (comparable sidecar, but has two wraps which this component does not).

**If the build exceeds 40 minutes, halt and signal.** Two named failure classes to investigate on overrun:
- Sophisticated OTel-anomaly detector (P99 windows etc) — this was explicitly deferred per ruling recorded #2; scope-creep if it appears.
- User-intent parsing inside this component — intent parsing lives in the primary persona; self-correction exposes the IPC and stays deterministic.

Do not extend silently.

## 9. What I need back

On completion:

1. **Paths to the commits on `pos-v2`.** Atomic per phase acceptable; single cohesive commit acceptable.
2. **Test results** — every CR-criterion (CR1–CR24, plus any CR25+ you added) mapped to a passing test. If any is unsatisfied, name it and explain.
3. **Sealed-component diff check** — `git diff --stat f94d602..<your-head>` should show only `self-correction/` changes (and possibly `data/` if runtime test-output lands there as it did for cost). Any other delta is a halt-signal.
4. **primary-persona inferences you challenged** and the alternative you chose (or halted on).
5. **Any halt signals** — named component + surface + what you tried first.
6. **Actual wall-clock vs the 28–35 min estimate.**
7. **Confirmation that your `test_no_sealed_amendments.py` uses `SEAL_COMMIT` pinning**, not HEAD.

Return summary: under 500 words. Code and tests carry the detail.

## 10. Failure modes I am watching for

- "Improving" the spec while building. Don't — file enhancement ideas in the commit message for a later component.
- Monkey-patching a sealed component. Halt and signal.
- Adding a new activation wrap. The no-wrap contract is architectural; if you find yourself reaching for one, halt.
- Bypassing any of the three gates for "correction scopes are special." They are not special at the gate layer.
- Soft-enforcing the four-part protocol with a warning rather than a structural refusal.
- Silent drops of cost-refused correction scopes. Every refusal is a `OneOnOneChannel` notification.
- Reintroducing the HEAD-based `test_no_sealed_amendments.py` pattern that was fixed on `f94d602`. Use `SEAL_COMMIT` pinning.
- Letting the estimate slip past 40 minutes quietly. Halt at 40 and signal scope-creep.
- Building LLM intent-parsing inside the primitive. The persona handles intent; the primitive handles the deterministic path.

---

**End of brief.** the owner reviews; on the owner's green light, dispatch follows. **Phase 3 closes on self-correction's seal.**
