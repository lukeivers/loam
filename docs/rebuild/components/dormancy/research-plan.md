# Research Plan — Graceful Degradation

**Component:** Graceful Degradation — the policy layer that detects Claude-upstream failure modes and calls the orchestrator's `pause_activation` / `resume_activation` hooks.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for graceful degradation such that:

- Every v1.0 Graceful-degradation acceptance criterion can be honoured by a concrete implementation proposal (simulated one-hour Claude outage does not corrupt in-flight scope state; sessions resume cleanly once the upstream returns; user is informed before blast radius exceeds a declared threshold).
- The component composes cleanly with the orchestrator (already sealed) via its `pause_activation` / `resume_activation` hooks, and with the primary-persona layer (already sealed) for user notification via its channel-agnostic interaction primitive.
- Detection of the three named failure modes (down, rate-limited, garbage-returning) is robust and tunable.
- The response policies (pause all; pause LLM-only; fall through to fail mode; request user decision) are declared, not arbitrary.

## Starting position

- **Orchestrator is sealed (2026-04-19 08:40 CDT)** on `pos-v2`. It exposes `pause_activation(reason)` and `resume_activation()` hooks. No amendment to the orchestrator is permitted without halt-signal.
- **All four Phase 1 primitives are sealed** — memory, scope-of-work, primary-persona layer, objective tracker — plus orchestrator sealed in Phase 2. Graceful degradation integrates via their public APIs; no amendments.
- **Primary-persona layer supplies the user-notification path** via the channel-agnostic-interaction primitive (v1.1 R13) — one-on-one channels only, the same path used for new-persona introductions.
- **Python 3.13 dev target, `pos-v2` branch**, permitted deps unchanged (stdlib + pydantic + pyee + opentelemetry + PyYAML).
- **LLM-judged policy** (per orchestrator research's A1-preserving rationale) — the component's "safe mode narrative" and user-notification wording use Claude via Max.

## Questions the research must answer

### 1. Detection — what counts as "degraded"

1. The spec names three failure modes: Claude API down, rate-limited, returning garbage. What does each look like concretely at the detection layer? Down = connection refused / timeout / 5xx; rate-limited = 429s at thresholds; garbage = schema-violating responses, obvious non-sequiturs, or LLM-refusal loops. Are there additional failure modes worth detecting (e.g. sustained high-latency, regional outage, quota exhaustion distinct from rate-limit)?
2. What is the detection mechanism — passive (observe existing LLM calls made by primitives and infer degradation), active (periodic heartbeat calls to Claude), hybrid? Passive is cheaper; active is faster to notice outages when no calls happen to be in flight.
3. What is the declared threshold for each mode — N consecutive failures in window W, error rate exceeding X%, latency p95 above Y? Tunable per-workspace with sensible defaults, or hard-coded in the pOS framework?
4. How is "returning garbage" detected deterministically vs requiring LLM-judgment? The former is cheaper and more auditable; the latter is more flexible.

### 2. Response policies

5. What response policies are available, and what is the default? Candidates: (a) pause all new scope activations; (b) pause only LLM-dependent activations, allow deterministic-only scopes to continue; (c) fall-through to fail — scopes that can't complete without LLM fail cleanly rather than pause; (d) request-user-decision for each affected scope; (e) throttle — reduce parallelism but do not pause.
6. How does the response policy interact with scope-of-work's default exhaustion policy (request-extension, per the earlier decision)? A scope that hits its budget during a Claude outage is in a compound-failure state — which signal wins?
7. How is the "safe mode narrative" authored? LLM-judged via Claude-via-Max produces a human-readable explanation of what's paused and why; this needs a concrete prompt template.

### 3. User notification and threshold

8. What is "blast radius exceeds a declared threshold" — the boundary at which the user must be informed? Options: time (Claude has been down for >N minutes), count (>N scopes paused), criticality (any scope flagged high-priority has been paused), budget (paused scopes' combined remaining budget exceeds X), hybrid.
9. What is the notification channel — the primary persona speaks to the user via the channel-agnostic-interaction primitive (v1.1 R13), with the same one-on-one-only restriction new-persona introductions have. Does the graceful-degradation component author the notification itself and call the persona to deliver, or does it hand the raw degradation context to the persona and let the persona author the wording?
10. Should the notification include recommendations (pause the whole run, drop low-priority scopes, let paused scopes resume when Claude returns) or just inform?

### 4. Resume behaviour

11. How is resume triggered — automatic on detection that Claude is healthy, or gated on user confirmation? Automatic is convenient; gated is safer (especially if the outage was long enough that context has shifted).
12. What is the healthy signal — N consecutive successful calls in window W? A single successful heartbeat call? Something weighted?
13. What happens to scopes that were paused — do they resume from where they were (state restored from scope-of-work's event log), or do they restart from a checkpoint, or does the user decide per-scope? If a scope was mid-LLM-call at pause, how is the partial result handled?

### 5. State preservation during outage

14. What state does graceful degradation own? At minimum: which scopes are paused, which are failed, the current safe-mode status, recent detection events. Does it persist this in its own SQLite (following the orchestrator's pattern of a small local store), or piggyback on scope-of-work's event log?
15. How does the component itself survive restart? If the graceful-degradation process dies during an outage, and the orchestrator restarts it, does the safe-mode status resume correctly?

### 6. Integration with the orchestrator and the monitor

16. The orchestrator exposes `pause_activation(reason)` / `resume_activation()`. Are those hooks sufficient, or does graceful degradation need additional hook surface? Research should confirm or recommend a single amendment (which would be a halt — orchestrator is sealed).
17. The background-work monitor (inside the orchestrator) subscribes to scope-of-work's pyee emitter. Does graceful degradation need its own subscription for detection, or does it work through the orchestrator's existing subscription?
18. Where does graceful degradation run as a process — inside the orchestrator process (like the monitor), as a peer coroutine, as a separate process? Each has implications for restart behaviour.

### 7. Testing the one-hour outage simulation

19. The spec's acceptance criterion is "simulated one-hour Claude outage does not corrupt in-flight scope state." What does that test look like concretely — a mock Claude client that returns failures for an hour of wall-clock time, or a time-compressed simulation that advances a mock clock? A real one-hour test is impractical in CI.
20. What does "does not corrupt" mean operationally — scope event logs remain consistent; no half-ingested memory records; no orphan spans; no lost bind-scope events? The research should enumerate the consistency invariants the test verifies.

### 8. Observability emission

21. What does graceful degradation emit per v1.1 R11? Detection events (with reason and signal), policy decisions (which policy fired, for which scopes), notification events (what was sent, to which channel, at what threshold), resume events. Emission per A1 correction — no consumer assumed.

## Constraints the research must respect

- **Python-native.** stdlib preferred; permitted deps as enumerated.
- **No amendments to sealed components.** Orchestrator's hook surface is `pause_activation` / `resume_activation` only. Memory, scope-of-work, primary-persona, objective tracker unchanged. If the build genuinely requires an amendment, halt and surface.
- **Zero carryover from current pOS.** Current-pOS rate-limit handling and retry logic are not reference implementations.
- **Max-first.** The safe-mode narrative and any LLM-assisted detection use Claude via Max.
- **No personas in pOS core.** Framework only.
- **No assumed downstream consumer (A1 correction).** OTel emission must succeed with no consumer.
- **Halt-on-deviation.** Surface rather than invent.
- **One-on-one notification channels only.** The v1.1 R13 restriction and R15 Tier A reasoning apply — user notification does not go to group chats.

## Deliverable — what the research document must contain

A markdown document at `components/graceful-degradation/research.md` with:

1. **Survey of existing patterns** — how other systems handle upstream-API degradation. Specifically survey: circuit-breaker libraries (pybreaker, tenacity), rate-limit-aware LLM clients (litellm, openai retry strategies), Temporal's failure-policy model, Anthropic SDK's error handling and retry posture, any AI-harness with explicit safe-mode (Letta, LangGraph interrupt mechanism).
2. **Recommended design shape** — for each of the eight question groups, options considered, recommended option, rationale.
3. **Acceptance-criterion coverage** — mapping each v1.0 Graceful-degradation criterion to the piece of the design that delivers it. Any that cannot be satisfied surfaces as a halt.
4. **Detection rubric specification** — concrete thresholds for each failure mode (defaults; note tunability).
5. **Response-policy specification** — the enumerated policies, how to select the default, how per-scope authors can override.
6. **Notification protocol** — concrete wording structure, threshold logic, channel selection integration with v1.1 R13.
7. **Resume mechanism** — automatic-vs-gated decision with rationale.
8. **State-preservation specification** — what's persisted where, how it survives restart.
9. **Integration sequence diagrams** — detection event → policy decision → orchestrator hook call → scope pause; notification threshold crossing → persona invocation → user message.
10. **Dependency map** — consumed by future components (none Phase 2-level expected); depends on orchestrator, scope-of-work, primary-persona layer.
11. **Complexity estimate** — AI-time, honest. Expected smaller than orchestrator because scope is narrower (policy layer on top of existing hooks), but not trivial because of detection logic + notification + state preservation; ballpark 300–450 AI-minutes.
12. **Prototyping priorities** — questions only a prototype can answer (e.g. detection false-positive rate on the "returning garbage" mode; notification threshold tuning against realistic outage patterns).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies throughout.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
