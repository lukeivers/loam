# Research — Graceful Degradation

**Component:** Graceful Degradation — the policy layer that detects Claude-upstream failure modes and calls the sealed orchestrator's `pause_activation(reason)` / `resume_activation()` hooks.
**Status:** research — produced against the approved plan.
**Authored by:** research agent. **Date:** 2026-04-19.
**Scope:** this is a research document; no code, no proposal, no brief. It answers the plan's eight question groups and delivers its twelve items.

---

## 0. Executive summary

Graceful degradation is a thin policy process that runs **inside the orchestrator's asyncio loop** (co-located with the `BackgroundWorkMonitor` — same hosting rationale), watches Claude-upstream health through three deterministic signals plus a bounded LLM-judge for "garbage," maps that health state into one of four declared response policies, and calls the orchestrator's existing `pause_activation` / `resume_activation` hooks. Safe-mode narrative and the user-facing notification wording are authored by a Claude-via-Max call under an explicitly-budgeted scope-of-work. The user is notified through the primary persona's channel-agnostic-interaction surface (the same `OneOnOneChannel`/`IntroductionDispatcher` path v1.1 R13 and v1.2 R15 established for introductions), which enforces one-on-one delivery at channel construction time.

No amendment to any sealed component is required. The orchestrator's two hooks (`pause_activation`/`resume_activation`) are sufficient. The primary persona layer's channel construct is re-usable; a parallel dispatcher is built for the degradation-notification wording but it is bound by the same `is_group=False` invariant at the type level.

Complexity estimate: **320–410 AI-minutes** — below the orchestrator, above the objective tracker. No spec criteria surface as unsatisfiable. No halt signals are raised.

---

## 1. Survey of existing patterns

### 1.1 Circuit-breaker libraries — pybreaker / aiobreaker / circuitbreaker

The canonical three-state machine (**closed → open → half-open**) is stable across the Python ecosystem. `pybreaker` (Daniel Fernandes) exposes `fail_max` (consecutive failures threshold before opening) and `reset_timeout` (seconds before half-open). `aiobreaker` is the asyncio-native fork used in modern async services. On open, every call fails fast with `CircuitBreakerError`; after `reset_timeout` one probe call is allowed; success closes, failure re-opens.

Takeaways for pOS:
- The three-state FSM is the correct shape for the response-policy FSM (closed = normal; open = paused; half-open = probing recovery).
- Half-open *must* admit exactly one probe call; more than one invalidates the resume signal. The resume policy must serialise the probe.
- pybreaker is a synchronous primitive; pOS is asyncio-native. A direct dependency is unnecessary — the FSM is ~40 lines of asyncio. pybreaker conflicts with the **constrained-deps** rule (requires adding pybreaker) and is **not carried over**.

### 1.2 Tenacity — retry with exponential backoff and jitter

Tenacity's value is the *wait strategy* vocabulary: `wait_exponential(multiplier, max)`, `wait_random_exponential`, `wait_exponential_jitter`. The "AWS equal jitter" formula is:

```
wait = min(cap, random.uniform(0, base * 2**n))
```

…which prevents thundering-herd on recovery when many callers retry simultaneously.

Takeaways for pOS:
- A retry loop is *not* a degradation loop. Retries are per-call and bounded (1–3 attempts with exponential backoff). Degradation is the cross-call policy fired when retries exhaust at enough call sites. The distinction matters: per-call retries live inside Claude-via-Max; degradation sits above.
- Jitter matters only for the probe-when-half-open step (single probe, jittered by 0–2s to avoid lockstep with other pOS processes sharing the same Claude account).
- Adding tenacity as a dependency is unnecessary — the asyncio backoff primitive is 6 lines. Not carried over.

### 1.3 Anthropic SDK error handling

Anthropic's Python SDK surfaces typed exceptions:

| Exception | HTTP | Semantic |
|---|---|---|
| `anthropic.APIConnectionError` | network | Claude unreachable |
| `anthropic.APITimeoutError` | timeout | request exceeded SDK timeout |
| `anthropic.RateLimitError` | 429 | rate limit exceeded (header: `retry-after`, `anthropic-ratelimit-*-remaining`) |
| `anthropic.APIStatusError` (5xx) | 5xx | Anthropic-side error |
| `anthropic.APIStatusError` (529) | 529 | overloaded (shed-load) |
| `anthropic.BadRequestError` | 400 | client-side — do NOT retry, do NOT trigger degradation |
| `anthropic.AuthenticationError` | 401 | credentials bad — degradation but different policy (user action required) |

The SDK ships built-in retries on 429 / 5xx / 529 with exponential backoff; `max_retries` is configurable on the client. **pOS should configure `max_retries=1–2` at the client layer** so the graceful-degradation component sees failures quickly rather than the SDK silently burning 60+ seconds on internal retries.

Three simultaneous rate-limit dimensions are enforced: RPM, TPM, concurrent in-flight. Response headers expose remaining budget on every call, which enables *predictive* degradation (tripping before the 429 if `anthropic-ratelimit-tokens-remaining / elapsed < threshold`). This is optional — the baseline rule is "react to errors, not predict them" — but the signal is available.

**Key decision:** pOS observes Anthropic exception types and headers, but does NOT reimplement the SDK's retry loop. Graceful degradation sees what leaks past the SDK's max_retries and treats the leak as the degradation signal.

### 1.4 litellm router — fallbacks and retries

litellm introduces the **fallback chain** (primary model fails → try next model in chain) and **cooldown-per-deployment** (a deployment that trips rate-limit goes on cooldown for N seconds before being re-considered). Retry-policy granularity is per-exception-type: different retry counts for `AuthenticationError`, `TimeoutError`, `RateLimitError`, `ContentPolicyViolationError`.

Takeaways for pOS:
- The fallback chain idea is **not applicable** — pOS is Claude-only (the owner's 2026-04-17 14:17 CDT non-goal). No model fallback.
- The per-exception-type policy granularity **is applicable**: different failure classes merit different response policies (see §3). A 429 with a short `retry-after` is a 60-second pause; an `AuthenticationError` is a hard stop that escalates to the user.
- "Deployment cooldown" is essentially the open-state dwell time from §1.1; same mechanism, different vocabulary.

### 1.5 Temporal failure-policy model

Temporal separates **activity retry policy** (automatic, exponential, default 2.0 backoff coefficient, 1s → 100s interval cap, unlimited attempts) from **workflow retry policy** (no default — workflows do not retry unless explicitly configured). Failures flagged `non_retryable` bypass the retry policy entirely and surface to the workflow.

Temporal's instructive contribution is the **failure-type taxonomy**: `ApplicationFailure`, `ActivityFailure`, `CanceledFailure`, `TerminatedFailure`, `ServerFailure`, `TimeoutFailure`. Each carries a `non_retryable` flag. The workflow author decides which failure types are transient and which are terminal.

Takeaways for pOS:
- pOS's scope-of-work primitive already has a "fail" transition (`rt.fail(scope_id, reason)`) — that's the "ActivityFailure" analogue. Graceful degradation should not duplicate this; it should classify Claude failures into `retryable_transient` vs `terminal` and let individual scopes decide their own policy for each.
- The `non_retryable` flag on a failure tells the system "do not reschedule." In graceful-degradation terms: `AuthenticationError` is non-retryable; `RateLimitError` is retryable-after-delay; `APIConnectionError` is retryable-with-backoff.

### 1.6 LangGraph interrupt mechanism

LangGraph's `interrupt()` function pauses a graph node mid-execution, persists state to the checkpoint store, and returns control to the caller with a `__interrupt__` key. The caller resumes with `Command(resume=value)`. **Interrupted threads hold no resources beyond storage**; resumption can happen months later on a different machine.

The orchestrator's `pause_activation` already approximates this at the dispatch layer (new activations refused, paused reason recorded). What LangGraph adds is *per-in-flight-task pause*: a task already running can be frozen and resumed. pOS's scope-of-work primitive supports this via `rt.pause(scope_id, reason)` / `rt.resume(scope_id)` — the primitives already exist.

Takeaways for pOS:
- Degradation's response policies already map cleanly to scope-of-work's existing pause/resume per-scope: the degradation component calls `rt.list(states=[active])` to enumerate in-flight scopes, and for each LLM-dependent one, calls `rt.pause(scope_id, reason="claude_api_degraded")`. On resume, it calls `rt.resume(scope_id)`.
- Because scope-of-work is event-sourced, pause is durable across orchestrator restart. That matches LangGraph's "resume months later" property without any new persistence layer.
- The degradation component does NOT need its own checkpoint store. Scope-of-work already is one.

### 1.7 Letta / MemGPT

Letta's failure-mode literature is dominated by the difficulty of getting non-Claude open-weights models to behave reliably within the MemGPT loop — "90% stacktraces, 10% working" in user reports. The V1 architecture rewrite deprecated heartbeats and side-channel tool calls in favour of direct assistant-message generation, specifically because the heartbeat mechanism compounded failure modes.

Takeaways for pOS:
- **Explicit negative lesson**: a heartbeat-ping loop against Claude is the *least* reliable degradation signal because it introduces its own failure class (the heartbeat-pings failing is ambiguous — is Claude down or is the heartbeat code broken?). Prefer passive observation of real traffic.
- Letta's pain with open-weights is irrelevant — pOS is Claude-only. But the general lesson stands: **the simplest reliable signal is the failure of the work you were already doing**.

---

## 2. Design shape — eight question groups

### Q1. Detection — what counts as "degraded"

#### Q1.a Concrete failure-mode signatures

| Mode | Claude-side signal | Pythonic signature |
|---|---|---|
| **Down** | connection refused, DNS failure, TCP timeout, 5xx | `APIConnectionError`, `APITimeoutError`, `APIStatusError` with status 500–504 |
| **Overloaded** | 529 overloaded | `APIStatusError` with status 529 |
| **Rate-limited** | 429 with `retry-after` | `RateLimitError` (SDK raises typed) |
| **Returning garbage** | schema-violating JSON, obvious non-sequitur, refusal loop | pydantic `ValidationError` on the expected response shape, OR LLM-judge returning `bad=yes` |
| **Auth-broken** | 401 | `AuthenticationError` (terminal until user intervenes) |
| **Bad request** | 400 | `BadRequestError` (caller-side; do not trigger degradation) |
| **High latency (optional)** | p95 > T | latency histogram observation |

Additional worth-detecting modes (beyond the plan's named three):

1. **529 overloaded** — Anthropic-side shed-load signal. Distinct from 5xx; typically shorter recovery. *Recommended: treat as a fourth named mode, with a faster half-open probe.*
2. **401 auth-broken** — escalate to user immediately; cannot self-resolve. *Recommended: treat as a degraded mode with policy = "pause + escalate to user, no auto-resume."*
3. **Latency sustained** — p95 > 30s for a window. Not a failure but indicative of upstream stress. *Recommended: log the signal, emit an OTel event, but do NOT pause — the cure (pausing while requests succeed) is worse than the disease. Defer any policy action unless latency crosses into timeout territory.*

#### Q1.b Detection mechanism — passive vs active vs hybrid

**Recommendation: passive, with a bounded active probe ONLY in the half-open state.**

Rationale:
- Passive observation (wrap every Claude-via-Max call site in a decorator that reports success/failure to the detection layer) is free — no extra API calls, no cost overhead, no attribution to an unowned scope.
- Active heartbeats have the Letta failure mode: heartbeat-code bugs masquerade as outages. Cost also adds up (1 ping/minute = 1440/day; even at 1 cent/call that's $14/month attributed to no scope — violates v1.1 R12 per-prompt attribution).
- Active probing is legitimately needed in **half-open** state only: after the open-state dwell, one probe call decides whether to close. That probe is attributed to a well-named "degradation-probe" prompt (R12 compliant).

Implementation shape: every call into Claude-via-Max goes through a pOS-side `ClaudeClient` wrapper. The wrapper (a) enforces `max_retries=1` on the SDK client (fail-fast), (b) records success/failure against the detection layer, (c) attributes cost via scope-of-work's `debit(prompt_name=...)`. The degradation detector never calls Claude directly outside the half-open probe.

#### Q1.c Declared threshold — defaults with per-workspace tunability

**Recommendation: thresholds ship as per-mode defaults in the pOS framework; workspaces override via `~/.pos/degradation.yaml`.**

Default thresholds:

| Mode | Trip threshold | Half-open dwell | Probe success requirement |
|---|---|---|---|
| Down | 3 failures in 60s | 30s | 1 probe call succeeds |
| Overloaded (529) | 2 failures in 30s | 15s | 1 probe call succeeds |
| Rate-limited (429) | 1 failure; honour `retry-after` | `retry-after` seconds (from header) | 1 probe call succeeds |
| Returning garbage | 3 garbage-verdicts in 10 calls | 60s | 2 consecutive probe calls succeed |
| Auth-broken | 1 failure | infinite (no auto-recovery) | user resolves + explicit resume |
| Latency sustained | p95 > 30s over 20-call window | n/a — advisory only, no pause | n/a |

Rationale for the asymmetric thresholds:
- 429 is self-describing — Anthropic tells you the exact recovery time via `retry-after`. Honour it verbatim.
- Garbage is noisier and more subjective; a higher-ratio threshold (30% = 3 of 10) avoids one bad generation tripping the breaker.
- 401 is categorically different and must not auto-recover.

Tunability: a pydantic model `DegradationConfig` loaded from `~/.pos/degradation.yaml`; unset fields fall back to framework defaults. Per-workspace override satisfies the plan's tunability requirement without forcing every workspace to declare thresholds.

#### Q1.d Garbage detection — deterministic vs LLM-judged

**Recommendation: hybrid — deterministic first, LLM-judge fallback, with an explicit budget ceiling on the LLM path.**

Deterministic tier (always run first):
1. **Pydantic schema violation.** Every Claude-via-Max call declares its expected response shape (a pydantic model). A `ValidationError` on the response counts as one garbage sample. Free, fast, auditable.
2. **Structural emptiness.** Response is `""`, whitespace-only, or shorter than a declared minimum for the prompt type. Free.
3. **Obvious refusal markers.** Heuristic regex for known refusal phrases ("I can't help with that", "I cannot", "I'm sorry, but I'm unable"). Free; low false-positive if scoped to calls that have passed structure but returned text.

LLM-judge tier (only when deterministic tier can't decide):
- A second Claude-via-Max call with a fixed "is this response a reasonable completion of this prompt?" judge prompt. Attributed to `degradation-garbage-judge` prompt name.
- **Budget ceiling:** no more than 5 judge calls per hour per workspace. If exceeded, the detector falls back to "assume fine" and logs a "budget exhausted" event. This prevents a degraded state from spawning a judge-call storm that worsens the degradation.

This hybrid is cheaper and more auditable than pure LLM-judged; the LLM path exists only where pydantic cannot decide.

### Q2. Response policies

#### Q2.a Policy catalogue and default

Four declared policies (named, not arbitrary). Each maps to a specific orchestrator-hook invocation and a specific in-flight-scope handling:

| Policy | Orchestrator hook | In-flight scopes (LLM-dependent) | In-flight scopes (deterministic) | Default for |
|---|---|---|---|---|
| **P1. Pause all activations** | `pause_activation(reason)` | leave running; they'll fail on next LLM call and enter policy-handler | leave running | default for Down / Overloaded |
| **P2. Pause LLM-dependent only** | `pause_activation(reason)` + `rt.pause(scope_id)` for each LLM-dependent active scope | explicitly paused | continue | default for Rate-limited |
| **P3. Fall through to fail** | `pause_activation(reason)` + `rt.fail(scope_id, reason="claude_api_unavailable")` for each LLM-dependent scope that cannot complete deterministically | fail cleanly with structured reason | continue | default for Auth-broken after user defer |
| **P4. Request-user-decision** | `pause_activation(reason)` + notification with decision prompt | paused pending user choice | continue | escalation when blast-radius exceeds threshold |

**Default policy per failure mode:**
- Down → P1 (Pause all)
- Overloaded → P1
- Rate-limited → **P2** (deterministic scopes can progress; only LLM-dependent ones pause)
- Garbage → P2 with a lowered confidence (garbage might be transient prompt-quality issue; avoid halting deterministic work)
- Auth-broken → P4 (Request-user-decision, because only the user can resolve)

**Why P2 default for rate-limit, P1 default for Down:** when Claude is unreachable nothing new starts anyway; pausing LLM-only and leaving deterministic alone adds complexity without value. When rate-limited, Claude is reachable and deterministic scopes can genuinely continue to progress.

Per-scope override: a scope's `ScopeSpec` already carries `escalation_triggers` and `owner_persona`. The workspace-author can declare `degradation_policy: fall_through_to_fail` at scope creation time (extension via a new optional field on the spec — this is a workspace-level extension of the scope's semantics, not a core-framework amendment; it rides on scope-of-work's existing constraints tuple OR a workspace-side mapping). **No amendment to scope-of-work itself is required** — the degradation component reads metadata the workspace supplies via the spec's `constraints` or `observers` fields and applies the right policy.

#### Q2.b Interaction with scope-of-work's request-extension policy

If a scope hits its budget during a Claude outage and its exhaustion policy is `request_extension`, scope-of-work pauses it to the pending-extension directory. Which signal wins?

**Recommendation: both signals fire; the earlier-recorded pause reason is preserved, the later one is recorded as a supplementary tag.**

Concretely: a scope that (a) hits budget first and pauses `reason=budget_exhausted`, then (b) experiences a Claude outage, stays in `paused` with its budget-exhausted reason — the Claude outage does not touch paused scopes (pause is already paused). On resume (Claude recovers), the degradation component checks each paused scope's pause_reason and only resumes the ones whose reason matches the degradation identifier, leaving budget-paused scopes in their budget-paused state for the user to handle via the pending-extension directory.

The reverse (Claude outage first, then budget exhausted) cannot happen — a paused scope is not consuming budget.

No state corruption. No conflicting signal. The degradation component tags paused scopes with its reason and only resumes those it caused.

#### Q2.c Safe-mode narrative authoring

**Recommendation: Claude-via-Max, with a fallback template for the case where Claude itself is the failure source.**

The primary case (garbage / rate-limit / latency — Claude is reachable enough to author the narrative):
- A scope is created with a small budget (tokens: ~500, money_cents: ~5, time_seconds: 30) and prompt name `degradation-narrative`.
- Prompt template — fixed, shipped with the framework:
  ```
  Claude upstream has entered a degraded state. Detected signal: {signal}.
  Count of affected in-flight scopes: {n}. Policy applied: {policy}.
  Write a 2-3 sentence plain-language summary for the user explaining:
  (a) what is paused; (b) why; (c) what happens next.
  Do not speculate about cause; report only the observed signal.
  Do not use personas' voice — you are narrating from the framework layer.
  ```
- The response is pydantic-validated to the shape `{headline: str, body: str, recommendation: str | None}`.

The fallback case (Claude is Down — the primary narrative call would itself fail):
- Ship a **deterministic template** in the framework, populated with structured fields:
  ```
  [Claude upstream unavailable at {iso_time}.]
  Detected signal: {signal}. {n} scope(s) paused ({policy}).
  Waiting up to {dwell_seconds}s before probing recovery.
  Reply 'resume' to force a probe now; reply 'cancel all' to fail paused scopes.
  ```
- This is hard-coded, no LLM call. It's the "safe-mode-within-safe-mode" narrative.

Selection: if the signal is Down, use the template. Otherwise attempt Claude-via-Max under a 2-second timeout; fall back to template on timeout or error.

### Q3. User notification and threshold

#### Q3.a Blast-radius threshold — when must the user be informed?

**Recommendation: compound threshold (OR of four conditions). Any one being true notifies.**

1. **Time:** Claude has been degraded for >5 minutes of wall-clock (below this, the event may self-resolve without user awareness being useful; above this, user should know).
2. **Count:** ≥3 scopes have been paused due to degradation (below this, the blast is minor).
3. **Criticality:** any paused scope has an `escalation_trigger` tagged as user-relevant (the scope itself declared via its trigger that it wants to surface; honour that).
4. **Auth-broken signal:** always notify immediately regardless of time/count. 401 is a user-action mode.

These are OR-ed. The user wants to know sooner, not be precisely-threshold-gated; the point is that we don't spam on 30-second blips.

**De-dup:** after notifying for a given degradation episode (identified by a UUID minted at trip-time), do not notify again for the same episode unless policy escalates (e.g., threshold 1 fires → 1 notification; threshold 2 then fires → no second notification; resume → 1 resume notification).

#### Q3.b Channel — authoring vs delegation

**Recommendation: the degradation component authors the raw context; the primary persona (if loaded) authors the final wording. Delivery uses a parallel dispatcher built on the primary-persona layer's `OneOnOneChannel` type with the same `is_group=False` invariant at construction.**

The architectural point: per STATE.md rule 4 and v1.2 R16, pOS core ships **no persona content**. The degradation component cannot assume a primary persona exists (some test workspaces may not load one). Therefore:

- Primary-persona-present path: degradation hands a structured context (`DegradationNotification`) to the persona; the persona re-wraps it in its own voice and calls the channel-agnostic-interaction surface. This uses the persona's existing channel wiring.
- Primary-persona-absent path: degradation uses the template-rendered text directly with its own dispatcher built on the same `OneOnOneChannel` type (exported from `primary_persona.introduction`, or a parallel sibling type with the same invariants). No identity is claimed — the dispatcher uses a sender label like `[pOS framework]` which is not a persona handle.

The one-on-one invariant is preserved in both paths because:
- `OneOnOneChannel.__post_init__` raises on `is_group=True`.
- The dispatcher's `__post_init__` re-checks every channel in the sequence.
- No override path exists at the type level — a group channel cannot be constructed.

This satisfies v1.1 R13 (channel-agnostic reachability), v1.2 R15 (one-on-one-only constraint extended from introductions to notifications), and the plan's explicit one-on-one restriction.

#### Q3.c Recommendations in the notification

**Recommendation: include up to two structured recommendations in the notification, formatted as inline verbs the user can reply with.**

Structure of the rendered notification:

```
[pOS — claude upstream degraded]
<headline — 1 line>
<body — 2-3 sentences, describes signal, count, policy>
<recommendation lines — 0, 1, or 2>

Reply 'resume' to probe recovery now.
Reply 'cancel all' to fail paused scopes.
```

Per communication-routing.md rule 1 and the workspace's Tier-2 register, these are all Tier 2 notifications ("worth knowing"), Tier 1 only for Auth-broken (user-action-required, time-sensitive). Recommendation lines are included for P4 (request-user-decision) policy; omitted for P1 (pause-all auto-resume expected) unless the user count threshold is exceeded.

### Q4. Resume behaviour

#### Q4.a Automatic vs gated on user confirmation

**Recommendation: automatic for Down / Overloaded / Rate-limited / Garbage; gated on user confirmation for Auth-broken and when any paused scope has dwell-time > 30 minutes.**

Rationale:
- Down/Overloaded/Rate-limited/Garbage are *transient* by definition; the cure arrives by itself. Gating adds friction without value. Automatic resume.
- Auth-broken requires user action anyway; no auto-path exists. Gated.
- Long dwell (>30 min): context may have shifted. A scope paused for an hour might be working on yesterday's problem. User re-confirms "yes resume these" before the degradation component calls `rt.resume` on each.

The 30-minute threshold is tunable (`degradation.resume.user_confirm_after_seconds`). Default 1800.

#### Q4.b Healthy signal shape

**Recommendation: N consecutive successful probe calls, with N varying by mode.**

| Mode | Probe success requirement | Rationale |
|---|---|---|
| Down | 1 success | Binary — reachable or not |
| Overloaded (529) | 1 success | Same |
| Rate-limited (429) | 1 success (post `retry-after`) | Anthropic tells us when |
| Garbage | 2 consecutive successes | Guard against one lucky generation |
| Auth-broken | user-confirmed + 1 success | Double-signal (user says they fixed it; probe confirms) |

The probe calls are attributed to `degradation-probe` prompt name. They use a known-good minimal prompt (e.g., "respond with exactly the word OK") to keep the probe's own signal clean — a garbage response from a canonical prompt is unambiguously Claude's problem.

#### Q4.c Paused-scope resumption

**Recommendation: resume from scope-of-work's event log. No checkpoint layer. For mid-LLM-call pauses, the partial result is discarded and the scope re-attempts from the beginning of its current step on resume.**

Detail:
- On pause, any Claude-via-Max call in flight for a scope returns an exception to its caller; the caller (the prompt-invocation wrapper) refunds the tokens via `rt.refund(scope_id, call_id)` and surfaces the exception. The scope's event log records the failed-then-refunded attempt.
- On resume, the scope's next activation re-attempts the same step. Because the refund was recorded, budget is intact. Because the event log captured both the debit and the refund, provenance is clear.
- Per-scope restart vs continue: for scopes with long sequences of LLM calls (multi-turn), resume is per-step, not per-scope. The step that was interrupted restarts; completed prior steps are not re-run (their event-sourced outputs remain valid).

This avoids introducing a checkpoint layer. The refund mechanism scope-of-work already has is the cleanup path.

### Q5. State preservation during outage

#### Q5.a What state does graceful degradation own?

Minimum owned state (non-redundant with sealed components):

1. **Current detection state** — per mode: (closed | open | half-open), last transition timestamp, consecutive failure count, last probe result.
2. **Active degradation episode** — UUID, started-at, signal, policy applied, paused scope list, notification record (time + channel + outcome).
3. **Recent detection events** — last N (bounded) `{mode, signal, timestamp, result}` tuples for observability/debugging.
4. **Notification dedup state** — which episodes have been notified on, at which threshold.

What it does NOT own (already in sealed components):
- Paused-scope details themselves → scope-of-work's event log (we only hold the list of IDs we paused)
- Hook-call history → orchestrator's local SQLite (`pause_activation` / `resume_activation` events are already recorded there)
- Cost attribution per prompt → scope-of-work's per-prompt view

#### Q5.b Persistence — own SQLite vs piggyback

**Recommendation: own SQLite at `~/.pos/degradation.sqlite`, event-sourced in the orchestrator's pattern.**

Rationale:
- Piggybacking on scope-of-work's event log would require emitting synthetic "scope events" that aren't scope events — a semantic abuse of that log.
- Piggybacking on orchestrator's local SQLite would work (the orchestrator already emits `pause_activation`/`resume_activation` events there), but mixes detection-state with orchestrator lifecycle state. Separation of concerns wins.
- A dedicated SQLite (~one file, ~3 tables) matches the orchestrator/scope-of-work/objective-tracker/memory-system pattern. Consistent architecture across components.

Tables:
- `detection_events` (append-only): mode, signal, result, timestamp
- `episodes` (append-only, state reconstructible from events): episode_id, started_at, resolved_at, signal, policy, paused_scope_ids (json), notification_sent_at
- `fsm_state` (singleton-row cache for fast restart): current mode state for each of the 6 modes

#### Q5.c Survive-restart behaviour

**Recommendation: on orchestrator restart, degradation component replays its event log, rebuilds FSM state, verifies against orchestrator's current paused status, and reconciles.**

Reconciliation cases:
1. **Orchestrator paused, degradation says open:** consistent — was in a degradation episode; continue half-open probe cycle (or re-notify if we've crossed time threshold since initial notification).
2. **Orchestrator paused, degradation says closed:** likely degradation crashed mid-pause. Re-open degradation state with a recovered-from-restart tag, resume probe cycle.
3. **Orchestrator not paused, degradation says open:** degradation didn't call `resume_activation` before death. Call it now with a `reconciled_on_restart` reason.
4. **Orchestrator not paused, degradation says closed:** normal state. No action.

All four cases are handled automatically. No user intervention required on degradation-component restart.

### Q6. Integration with orchestrator and monitor

#### Q6.a Hook sufficiency

**Finding: `pause_activation(reason)` / `resume_activation()` are sufficient. No additional orchestrator hook surface is required.**

Mapping:
- "Pause all activations" (P1) → `pause_activation(reason="claude_upstream_degraded:{signal}:{episode_id}")`
- "Resume" → `resume_activation()`
- "Pause specific scopes" (P2) → scope-of-work's existing `rt.pause(scope_id, reason=...)`, no orchestrator hook needed
- "Fail specific scopes" (P3) → scope-of-work's existing `rt.fail(scope_id, reason=...)`, no orchestrator hook needed
- "Resume specific scopes" → scope-of-work's existing `rt.resume(scope_id)`

Everything the degradation component needs to do, it can do through:
- Orchestrator's two pause/resume hooks (already exposed)
- Scope-of-work's public API (already sealed)
- Primary-persona's channel-agnostic surface (already sealed)

**No halt signal. No amendment required.**

#### Q6.b Subscription to scope-of-work emitter

**Recommendation: subscribe independently via `scope_runtime.subscribe_all(callback)`. Do not share the orchestrator's existing subscription.**

Rationale: pyee's subscribe-all allows multiple independent subscribers. The background-work-monitor already has one subscription (per the primary-persona layer); adding a second for degradation is clean and does not couple the two components. If the monitor needs different filtering than degradation, they shouldn't share a subscription.

What degradation subscribes to:
- Debit events (for cost-rate observability — optional, for the latency/cost-anomaly mode)
- Scope failure events (for detecting "scopes failing because of LLM errors" — this is how passive detection gets its signal for in-flight work)

Most of degradation's detection signal comes from the Claude-client wrapper (which is a thin layer over the Anthropic SDK, on the Claude-via-Max call path), not the pyee emitter. The pyee subscription is supplementary.

#### Q6.c Process hosting

**Recommendation: same asyncio loop as the orchestrator. Peer coroutine alongside `BackgroundWorkMonitor`.**

Rationale (matches the monitor-hosting decision in `orchestrator/docs/architecture.md` lines 79–90):
- scope-of-work's pyee emitter is in-process — cross-process fan-out would require a second durable queue, which violates the constrained-deps rule.
- Degradation state (especially the active episode) is longer-lived than a single session turn and must coexist with orchestrator pause state — co-located is safer than IPC-coupled.
- The orchestrator is already the single composition point for long-lived coroutines; adding a second peer coroutine matches the established pattern.

The degradation coroutine is started in `Orchestrator._startup()` after the monitor; stopped in `_shutdown()` before the monitor (so it can emit a final "shutdown" event in its own log before the monitor tears down).

The graceful-degradation component itself is a separate Python package/module (`graceful_degradation/`) — it's not inside the orchestrator package. The orchestrator imports and instantiates it at startup; this is workspace bootstrap wiring, not a framework amendment. (Parallel to how `ObjectiveTracker` is imported and instantiated by the orchestrator today.)

### Q7. Testing the one-hour outage simulation

#### Q7.a Test shape — time-compressed, deterministic

**Recommendation: time-compressed simulation using an injectable clock. No wall-clock one-hour tests.**

Construction:
- A `FakeClaudeClient` with scripted behaviour: a sequence of `[success, success, failure, failure, failure, failure, ..., success]` responses keyed to call index.
- An injectable `clock` parameter (same pattern the orchestrator already uses — see `Orchestrator.__init__(clock=...)` at line 82 in `orchestrator.py`). Advance the clock manually via `clock.advance(seconds)`.
- Test flow:
  1. Construct degradation + orchestrator + scope-of-work with the fake clock.
  2. Create 5 scopes; 3 LLM-dependent, 2 deterministic.
  3. Drive the fake clock to trigger the failure sequence; advance 3600s with periodic check-ins at 60s, 300s, 1800s, 3600s.
  4. Restore the FakeClaudeClient to success.
  5. Verify post-conditions.

This runs in seconds, not an hour, and exercises the full FSM + policy + resume path.

#### Q7.b "Does not corrupt" — enumerated invariants

The following invariants must hold after the simulated outage:

1. **Scope event log consistency:** every debit has either a completion event or a refund event; no orphaned debits. (Verified by iterating every scope's event log and checking debit/refund pairing.)
2. **No half-ingested memory records:** any memory write started during the outage is either fully committed (with full provenance) or fully absent. (Verified by memory-system's own consistency check, which exists per the sealed memory contract.)
3. **No orphan OTel spans:** every span opened during the outage is closed with a final status. (Verified by inspecting the OTel test exporter's span record — every span has `end_time` populated.)
4. **No lost `bind_scope` events:** scopes that were bound pre-outage remain bound; scopes that attempted to bind during outage either bound successfully or have a `bind_refused` event. No partial binds. (Verified by querying objective-tracker for each scope.)
5. **Orchestrator pause/resume is balanced:** every `pause_activation` event has a matching `resume_activation` event (unless the test ends in degraded state, which is a separate assertion).
6. **Degradation-component event log is balanced:** every `episode_started` has a matching `episode_resolved` (same exception as above).
7. **Deterministic scopes completed normally:** 2 of 2 deterministic scopes should have completed during the outage window (the outage does not stop them under P1, but they should continue under P2; test both policies).
8. **LLM-dependent scopes resumed and completed:** 3 of 3 LLM-dependent scopes, after resume, finish without re-running prior completed steps.

These eight invariants constitute the operational definition of "does not corrupt."

### Q8. Observability emission

Per v1.1 R11 OTel + A1 no-consumer-assumed correction:

Span names (`pos.degradation.*` namespace):
- `pos.degradation.detection_event` — per Claude-call observation (attributes: `mode`, `signal`, `result`, `call_id`, `prompt_name`)
- `pos.degradation.fsm_transition` — per mode FSM transition (attributes: `mode`, `from_state`, `to_state`, `trigger`)
- `pos.degradation.episode_started` — episode minted (attributes: `episode_id`, `signal`, `policy`, `paused_scope_count`, `paused_scope_ids`)
- `pos.degradation.episode_resolved` — episode closed (attributes: `episode_id`, `duration_seconds`, `resolution_kind` ∈ {auto, user_confirmed, user_cancelled})
- `pos.degradation.notification_dispatched` — user notification sent (attributes: `episode_id`, `channel`, `outcome`, `threshold_triggered`)
- `pos.degradation.probe_call` — half-open probe (attributes: `mode`, `result`, `attempt_n`)
- `pos.degradation.policy_decision` — policy applied (attributes: `policy`, `episode_id`, `reason`)

Every emission uses `opentelemetry.trace.get_tracer("pos.degradation", "0.1.0")`. No downstream consumer is assumed — per the A1 correction in the plan, a span emitted to the noop tracer is a successful emission. If a consumer exists (OTel collector, event log, viewer), it can subscribe; if not, nothing breaks.

---

## 3. Acceptance-criterion coverage

The v1.0 Graceful-degradation criterion:
> "simulated one-hour Claude outage does not corrupt in-flight scope state; sessions resume cleanly once the upstream returns; user is informed before blast radius exceeds a declared threshold."

Decomposed:

| Behaviour | Delivered by |
|---|---|
| B1. Simulated one-hour Claude outage does not corrupt in-flight scope state | §7 test harness (fake clock + fake Claude) verifying eight invariants in §7.b; FSM correctness + scope-of-work's existing event-sourced pause/refund semantics |
| B2. Sessions resume cleanly once the upstream returns | §4 automatic-resume for transient modes; user-confirmed resume for long dwell / auth-broken; scope-of-work's existing `rt.resume` on paused scopes tagged with our episode ID |
| B3. User informed before blast radius exceeds declared threshold | §3.a compound OR-threshold (time ≥5min OR count ≥3 OR criticality OR auth-broken); §3.b one-on-one channel delivery; §3.c structured notification content |

All three behaviours mapped. **No halt signals.** No criterion surfaces as unsatisfiable under the stated constraints.

One risk I want to name without escalating: the LLM-authored safe-mode narrative assumes Claude-via-Max is reachable. When Claude itself is the failure source, the deterministic template kicks in (§2.c). This is documented, not a gap.

---

## 4. Detection rubric specification — complete table

Consolidates the defaults from Q1.c with tunability:

```yaml
# ~/.pos/degradation.yaml — workspace override; unset fields inherit framework defaults

degradation:
  modes:
    down:
      trip_threshold:
        failures: 3
        window_seconds: 60
      half_open_dwell_seconds: 30
      probe_success_requirement: 1
      default_policy: pause_all
    overloaded:  # 529
      trip_threshold:
        failures: 2
        window_seconds: 30
      half_open_dwell_seconds: 15
      probe_success_requirement: 1
      default_policy: pause_all
    rate_limited:  # 429
      trip_threshold:
        failures: 1
        window_seconds: 1
      half_open_dwell_seconds: null  # uses retry-after header
      probe_success_requirement: 1
      default_policy: pause_llm_only
    garbage:
      trip_threshold:
        failures: 3
        window_calls: 10
      half_open_dwell_seconds: 60
      probe_success_requirement: 2
      default_policy: pause_llm_only
      judge_budget_per_hour: 5
    auth_broken:  # 401
      trip_threshold:
        failures: 1
        window_seconds: 1
      half_open_dwell_seconds: null  # no auto-recovery
      probe_success_requirement: 1  # user must fix + probe must succeed
      default_policy: request_user_decision
    latency_sustained:  # advisory-only
      trip_threshold:
        p95_seconds: 30
        window_calls: 20
      action: emit_signal_only  # no pause

  notification:
    thresholds:
      time_seconds: 300
      paused_scope_count: 3
      auth_broken_immediate: true
    tier: 2  # Tier 1 for auth_broken
    dedup_per_episode: true

  resume:
    auto_resume_modes: [down, overloaded, rate_limited, garbage]
    user_confirm_after_seconds: 1800  # long-dwell gate
```

All values are tunable; framework ships these as defaults.

---

## 5. Response-policy specification

Enumerated in §2.a; restated for the specification deliverable:

```
P1. pause_all
    - orchestrator.pause_activation(reason)
    - leaves in-flight scopes running (they'll fail on next LLM call and route into policy-handler)
    - no per-scope action at trip-time

P2. pause_llm_only
    - orchestrator.pause_activation(reason)
    - for each scope in rt.list(states=[active]) that is LLM-dependent:
        rt.pause(scope_id, reason="degradation:{episode_id}")
    - deterministic scopes continue untouched

P3. fall_through_to_fail
    - orchestrator.pause_activation(reason)
    - for each LLM-dependent active scope:
        rt.fail(scope_id, reason="degradation:{episode_id}:no_auto_resume")
    - deterministic scopes continue untouched

P4. request_user_decision
    - orchestrator.pause_activation(reason)
    - for each LLM-dependent active scope:
        rt.pause(scope_id, reason="degradation:{episode_id}:awaiting_user")
    - notify user with structured decision prompt (see §3.c)
    - on user response, invoke the corresponding policy
```

Selecting the default per mode: per §2.a table. Per-scope override: workspaces declare `degradation_policy: <policy_name>` as scope metadata (implementation detail — rides on scope-of-work's existing metadata fields without amendment).

---

## 6. Notification protocol

Wording structure — the rendered notification text:

```
[pOS — claude upstream degraded]
{headline}

{body}

{optional_recommendation_block}

Reply 'resume' to probe recovery now.
Reply 'cancel all' to fail paused scopes and continue.
```

Threshold logic — OR of:
- time_seconds_degraded >= config.notification.thresholds.time_seconds
- paused_scope_count >= config.notification.thresholds.paused_scope_count
- any_paused_scope_has_user_relevant_trigger == true
- mode == auth_broken

Channel selection — integration with v1.1 R13:
- Query the primary-persona layer's loaded `IntroductionDispatcher.channels` (or a workspace-registered degradation-channel list; same shape).
- First `is_active == true` channel wins.
- If zero active one-on-one channels, the notification queues to `.pos/degradation_queue/<episode_id>.json` and fires on next channel activation (same pattern as introduction-queue).
- `is_group=True` is rejected at type-construction; no override path exists.

---

## 7. Resume mechanism

Decision: **automatic for transient modes, gated for auth_broken and long dwell.**

```
on_detection_closed(mode, episode_id):
    if mode == auth_broken:
        require_user_confirmation()
    elif episode_duration_seconds > config.resume.user_confirm_after_seconds:
        require_user_confirmation()
    else:
        auto_resume(episode_id)

def auto_resume(episode_id):
    paused = local_sqlite.get_paused_scope_ids(episode_id)
    for scope_id in paused:
        rt.resume(scope_id)
    orchestrator.resume_activation()
    mark_episode_resolved(episode_id, "auto")
    notify_user("[pOS] Claude upstream recovered; {n} scopes resumed.")

def require_user_confirmation():
    notify_user_with_decision_prompt()
    # on 'resume' user reply: auto_resume(episode_id)
    # on 'cancel all' user reply: fail_paused_scopes(episode_id)
```

Rationale for gated on long dwell: context coherence. A scope paused for an hour may be working on an objective that has since shifted under the user's hand; asking "resume?" is cheap and correctness-preserving. 30 minutes is the default; tunable.

---

## 8. State preservation specification

Owned state:

| State | Location | Persistence | Reconstruction on restart |
|---|---|---|---|
| Per-mode FSM state (closed/open/half-open) | `~/.pos/degradation.sqlite:fsm_state` table | row-per-mode, upserted on transition | direct read |
| Detection events | `~/.pos/degradation.sqlite:detection_events` | append-only | replayed to rebuild counters |
| Active episodes | `~/.pos/degradation.sqlite:episodes` | append-only with resolved_at nullable | replayed; unresolved episodes become active on boot |
| Notification dedup | `episodes.notification_sent_at` | row field | direct read |

Not owned (lives in sealed components):
- Paused-scope details → `scope-of-work.db` (event-sourced)
- Orchestrator pause/resume history → `~/.pos/orchestrator.sqlite`
- Cost attribution for degradation-probe/judge/narrative prompts → scope-of-work's per-prompt view (v1.1 R12 compliance)

Restart reconciliation: four cases enumerated in §5.c. All handled automatically.

---

## 9. Integration sequence diagrams

### 9.1 Detection → policy decision → orchestrator hook call → scope pause

```
ClaudeClient        DegradationDetector      DegradationPolicy       Orchestrator        ScopeRuntime
  │                         │                       │                    │                    │
  │ call Claude             │                       │                    │                    │
  │ (via Max)               │                       │                    │                    │
  │ ──────── APIConnectionError ─────▶              │                    │                    │
  │                         │ record_failure(down)   │                    │                    │
  │                         │ counter += 1           │                    │                    │
  │                         │ counter >= threshold?  │                    │                    │
  │                         │ yes → trip             │                    │                    │
  │                         │ fsm: closed → open     │                    │                    │
  │                         │──── trip_event(mode=down, episode_id) ─────▶│                    │
  │                         │                       │ select_policy(down)│                    │
  │                         │                       │ → P1 (pause_all)   │                    │
  │                         │                       │────────────────────▶ pause_activation   │
  │                         │                       │                    │ local_state.append │
  │                         │                       │                    │ obs.emit_event     │
  │                         │                       │◀─── ok ────────────│                    │
  │                         │                       │ (P1 = no per-scope pause)               │
  │                         │                       │                    │                    │
  │                         │                       │ (for P2/P3/P4, iterate rt.list(active) →│
  │                         │                       │  call rt.pause/fail per scope with      │
  │                         │                       │  reason="degradation:{episode_id}")     │
  │                         │                       │                    │                    │
  │                         │                       │ record episode in degradation.sqlite    │
  │                         │                       │ emit pos.degradation.episode_started    │
  │                         │                       │                    │                    │
  │                         │                       │ if threshold met:                       │
  │                         │                       │   render narrative (via Max or template)│
  │                         │                       │   → notification pipeline               │
```

### 9.2 Notification threshold crossing → persona invocation → user message

```
DegradationPolicy    NotificationPipeline   PrimaryPersonaLayer?   OneOnOneDispatcher    User channel
  │                         │                       │                    │                    │
  │ threshold met           │                       │                    │                    │
  │ ──────▶ render context  │                       │                    │                    │
  │                         │                       │                    │                    │
  │   primary_persona loaded?                       │                    │                    │
  │  ┌────── yes ──────────▶│                       │                    │                    │
  │  │                      │ persona.notify_user(context)               │                    │
  │  │                      │ ──────────────────────▶                    │                    │
  │  │                      │                       │ render in voice    │                    │
  │  │                      │                       │ assert_not_sent_before_addressable?     │
  │  │                      │                       │ (primary persona, by contract, has      │
  │  │                      │                       │  is_addressable=True always; degradation│
  │  │                      │                       │  notifications are framework voice not  │
  │  │                      │                       │  a new-persona-intro, so this guard is  │
  │  │                      │                       │  satisfied by construction)             │
  │  │                      │                       │ ───────────────────▶ dispatch           │
  │  │                      │                       │                    │                    │
  │  └── no (no persona loaded) ─▶                  │                    │                    │
  │                         │ render template directly                   │                    │
  │                         │ sender_label = "[pOS framework]"           │                    │
  │                         │ ────────────────────────────────────────────▶ dispatch          │
  │                         │                       │                    │                    │
  │                         │                       │                    │ __post_init__:     │
  │                         │                       │                    │ is_group=False     │
  │                         │                       │                    │ (rejected if True) │
  │                         │                       │                    │ ──── send(text) ──▶│
  │                         │                       │                    │◀─── delivered ─────│
  │                         │ record notification in degradation.sqlite   │                    │
  │                         │ emit pos.degradation.notification_dispatched│                    │
```

### 9.3 Half-open → probe → resume

```
DegradationFSM       ClaudeClient         DegradationPolicy       Orchestrator        ScopeRuntime
  │                        │                    │                     │                    │
  │ dwell timer expires    │                    │                     │                    │
  │ fsm: open → half_open  │                    │                     │                    │
  │ ───── probe_call(prompt="degradation-probe") ─▶                   │                    │
  │                        │ call Claude        │                     │                    │
  │                        │◀─── "OK" ──────────│                     │                    │
  │ ◀── success ───────────│                    │                     │                    │
  │ probe_ok_count += 1    │                    │                     │                    │
  │ >= requirement?        │                    │                     │                    │
  │ yes → fsm: half_open → closed               │                     │                    │
  │ ───── close_event(episode_id) ────────────▶ │                     │                    │
  │                        │                    │ gate check:         │                    │
  │                        │                    │   auth_broken? → gated                    │
  │                        │                    │   duration > 30min? → gated               │
  │                        │                    │   else → auto_resume                      │
  │                        │                    │                     │                    │
  │ auto_resume path:                                                                        │
  │                        │                    │ for scope_id in episode.paused_scope_ids: │
  │                        │                    │ ────────────────────────────────────────▶ │
  │                        │                    │                     │       rt.resume    │
  │                        │                    │                     │    (scope_id)      │
  │                        │                    │                     │◀── active ─────────│
  │                        │                    │────────────────────▶ resume_activation   │
  │                        │                    │                     │ local_state.append │
  │                        │                    │                     │ obs.emit_event     │
  │                        │                    │◀─── ok ─────────────│                    │
  │                        │                    │ record episode_resolved                    │
  │                        │                    │ emit pos.degradation.episode_resolved      │
  │                        │                    │ render recovery narrative → notify user    │
```

---

## 10. Dependency map

**Upstream dependencies (this component consumes):**
- **Orchestrator** (sealed) — `pause_activation`/`resume_activation` hooks; co-hosted as peer coroutine; local SQLite pattern borrowed.
- **Scope-of-work** (sealed) — `rt.list`, `rt.pause`, `rt.resume`, `rt.fail`, `rt.refund`, `rt.debit`; pyee `subscribe_all` for supplementary observation; `per_prompt_costs()` for R12 attribution of probe/judge/narrative.
- **Primary-persona layer** (sealed) — `OneOnOneChannel` type (or equivalent parallel dispatcher adhering to the same `is_group=False` invariant); loaded-persona-optional path when pOS-core ships no persona.
- **Objective tracker** (sealed) — not directly consumed; the degradation component does not activate scopes itself.
- **Memory system** (sealed) — not directly consumed. The degradation component's detection events are in its own SQLite; they are not memory-worthy. (The narrative call's *output* may be memory-worthy per v1.1 R3 process-of-arrival — but the detection and policy mechanics are not.)

**Downstream dependencies (who consumes this):**
- None at Phase 2 level. No persona reads degradation state today. When a primary persona is loaded, it receives notifications via the pipeline but does not query degradation state.
- Future components (observability viewer, event-log aggregator) may subscribe to the OTel `pos.degradation.*` span namespace. Per A1 correction, emission is consumer-independent — the component does not require any consumer.

**Amendments required:** **None.** All five sealed components remain unamended.

---

## 11. Complexity estimate

**Range: 320–410 AI-minutes.** Broken down by area:

| Area | Effort (AI-minutes) | Notes |
|---|---|---|
| FSM per mode (6 modes × ~20 min each) | 60 | Small asyncio-native FSM with typed transitions |
| Detection — ClaudeClient wrapper + signal routing | 50 | Decorator + Anthropic exception type mapping + latency histogram + pyee observer |
| Garbage detection tier (pydantic schema + regex + LLM-judge) | 45 | Three-tier pipeline with judge-call budget |
| Response-policy dispatcher (P1–P4 + scope-iteration) | 40 | Four policies × scope.list filter × rt.pause/fail calls |
| Local SQLite (3 tables, event-sourced + fsm_state) | 35 | Mirrors orchestrator's local_state pattern |
| Safe-mode narrative (Claude-via-Max call + fallback template + pydantic validation) | 30 | Prompt authoring is light; response validation + fallback branching is the meat |
| Notification pipeline (threshold OR-logic + channel selection + dispatcher) | 40 | Parallels introduction-dispatcher; needs persona-optional branching |
| Restart reconciliation (4 cases) | 25 | Read FSM state, read orchestrator paused status, reconcile |
| OTel emission helpers (degradation-namespace span conventions) | 15 | Mirrors orchestrator/observability.py |
| Config loader (pydantic DegradationConfig + YAML + defaults) | 15 | Standard pydantic-from-yaml loader |
| Test harness (fake Claude + injectable clock + 8 invariants) | 40 | The one-hour simulation test |
| Bundled documentation (R4) | 20 | Prose + relationship map + sequences |
| **Total** | **415** | Top-of-range |

Below the orchestrator's sealed range (the orchestrator sealed around 500+ AI-minutes per its history). Above the objective tracker's range. Matches the plan's 300–450 ballpark. The FSM + detection being novel is the cost driver; everything else leverages sealed primitives.

---

## 12. Prototyping priorities

Questions only a prototype will answer:

1. **False-positive rate on the garbage detector.** The three-tier pipeline (pydantic schema + regex + LLM-judge) may over-trip on legitimately weird responses. A prototype with 100 real Claude-via-Max calls scored against a human-labelled "is this garbage?" set will tell us whether the 30% (3-of-10) threshold is too tight. Acceptable precision ≥ 0.85; below that, raise the threshold or add an appeal step.

2. **Half-open dwell tuning.** 30s for Down might be too short (recovery jitter from Anthropic side) or too long (users waiting). Prototype by replaying logged outages from current pOS (if they exist) against different dwell values; measure mean time to recovery and rate of repeat-trip.

3. **Notification threshold calibration.** The 5-minute / 3-scope threshold is a guess. A prototype week in a real workspace logging "would-have-notified" events at various thresholds tells us what users actually want to know. Expect the count threshold to be more load-bearing than the time threshold.

4. **Claude-via-Max narrative latency during degraded states.** The narrative call itself is at risk during rate-limit degradation. Prototype the "timeout → fall back to template" behaviour and measure the fallback-trigger rate; if it's >20%, default to template always for rate-limit mode.

5. **Concurrent degradation episodes.** Can two modes trip simultaneously (e.g., rate-limited and high-latency in the same window)? Design assumes episodes are independent but this may need first-one-wins or union semantics — prototype reveals which.

6. **Restart reconciliation load.** How long does replay take on a workspace with 10,000 detection events? If > 2s, introduce a checkpoint row (snapshot FSM state every N events) to bound cold-start time.

These six are the items where "think harder" won't get us further than "build it minimally and measure."

---

## 13. Constraints verification checklist

- ✅ **Python-native, constrained deps.** Runtime uses stdlib + pydantic + pyee + opentelemetry + PyYAML. No new dependency required. (Discussed pybreaker and tenacity; both rejected in favour of in-tree minimal implementations.)
- ✅ **No amendments to sealed components.** Orchestrator's `pause_activation`/`resume_activation` are sufficient (§6.a). Scope-of-work's existing `pause`/`resume`/`fail`/`refund` are sufficient. Primary-persona's `OneOnOneChannel` invariant is reused. No amendment requested.
- ✅ **Zero carryover from current pOS.** No reference to current-pOS retry or rate-limit logic. Survey treated pybreaker/tenacity/litellm as external patterns, not as reference implementations to port.
- ✅ **Max-first.** Safe-mode narrative and garbage-judge use Claude via Max; both attributed to named prompt types (`degradation-narrative`, `degradation-garbage-judge`, `degradation-probe`) for v1.1 R12 per-prompt cost aggregation.
- ✅ **No personas in pOS core.** Notification path branches: primary-persona-present (voice wrapping) and primary-persona-absent (framework-voice template). Neither path hard-codes any persona identity.
- ✅ **No assumed downstream consumer.** OTel emission succeeds with noop tracer per A1; §8 list of span names is the emission surface, consumer-independent.
- ✅ **One-on-one notification channels only.** `OneOnOneChannel.__post_init__` rejects `is_group=True`; dispatcher `__post_init__` re-checks; no framework override path exists. Matches v1.1 R13 + v1.2 R15 constraints explicitly.
- ✅ **Halt-on-deviation.** No criterion surfaces as unsatisfiable under the stated constraints. No halt signal raised.

---

**End of research document.**
