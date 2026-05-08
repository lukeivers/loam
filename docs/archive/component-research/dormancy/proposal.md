# Graceful Degradation — Proposal

**Component:** Graceful Degradation (second Phase 2 component)

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 + v1.2 addenda
**Informed by:** `research-plan.md`, `research.md` (returned 2026-04-19 08:59 CDT). owner's approval of research recommendations 2026-04-19 09:04 CDT.

---

## Summary

Build the graceful-degradation component as a policy layer that wraps Claude API calls in a `ClaudeClient` adapter, tracks six failure modes through per-mode finite-state machines, and calls the sealed orchestrator's `pause_activation(reason)` / `resume_activation()` hooks when degradation is detected. State lives in its own small SQLite at `~/.pos/degradation.sqlite`; user notification rides the primary-persona layer's one-on-one channel surface with a compound-OR threshold that's unlikely to over-page. A deterministic fallback narrative covers the case where Claude itself is the failure source — the user always gets informed even during a total outage. No sealed-component amendment required.

## Direction

### Detection — `ClaudeClient` wrapper + per-mode FSM

- All LLM calls made anywhere in pOS (memory's extraction pipeline, primary-persona's monitor stuck-reason pass, authoring pipeline, anywhere else) route through a new `ClaudeClient` adapter. The adapter observes the Anthropic SDK's typed exceptions and `retry-after` headers; it does not inject calls Claude wouldn't otherwise see (passive-first).
- Six per-mode FSMs (closed → open → half-open → closed). Active probing fires only during half-open, so cost stays bounded.
- Six modes with research-recommended thresholds (all per-workspace-tunable with these defaults):

| Mode | Detector | Default policy |
|---|---|---|
| **Down** | 3 connection/timeout/5xx failures in 60 s | P1 pause-all |
| **Overloaded 529** | 2 × 529 in 30 s | P1 pause-all |
| **Rate-limited 429** | Any 429 (honour `retry-after` header) | P2 pause-LLM-only |
| **Garbage** | 3 of last 10 responses fail: pydantic-schema → regex → Claude-judge (5-judge/hour budget) | P2 pause-LLM-only |
| **Auth-broken 401** | Any 401 | P4 request-user-decision (user-only — Claude can't fix it) |
| **Latency-sustained** | p95 > threshold for 5 min | Advisory, no pause |

### Response policies

Four enumerated policies with per-mode defaults above; scope authors can override per-scope via the same metadata surface scope-of-work already supports:

- **P1 pause-all** — orchestrator's `pause_activation(reason)` halts all new activations; in-flight scopes pause-not-fail.
- **P2 pause-LLM-only** — only scopes needing LLM inference pause; deterministic-only scopes continue.
- **P3 fall-through-to-fail** — scopes that can't complete without Claude fail cleanly rather than pause. Useful when recovery is unlikely.
- **P4 request-user-decision** — per-scope decision surface goes to the user via the notification channel; each scope proceeds according to the user's call.

### Notification — compound OR threshold

Notification fires when any of the following is true:

- Wall-clock degraded ≥ 5 minutes, OR
- Paused-scope count ≥ 3, OR
- Any paused scope carries a user-relevant escalation trigger, OR
- Auth-broken (fires immediately, always).

One notification per episode (de-duped by UUID). Resume fires a second notification. Tier 2 default; Tier 1 for auth-broken. Channel: the primary-persona layer's one-on-one channel surface (v1.1 R13 + v1.2 R15 — same restriction as new-persona introductions, no group chats).

### Safe-mode narrative

The notification content is Claude-authored (via Max) when Claude is partially working (rate-limit, garbage, latency). **When Claude is the failure source itself** (down, overloaded, auth-broken), a **deterministic fallback template** fills the narrative — structured fields the persona presents directly, without needing an LLM turn. User always gets informed, even during a total outage.

### Resume

- **Automatic** for transient modes (Down, Overloaded, Rate-limited, Garbage) once the healthy signal passes (N consecutive successful probe calls; N = 1 for binary modes, N = 2 for Garbage).
- **Gated on user confirmation** for:
    - Auth-broken (user must actually fix the credential).
    - Any episode whose dwell exceeds **30 minutes** (default, tunable) — context-coherence safeguard. A long outage may mean the user's intent has shifted; we ask rather than assume.

### State preservation

Own SQLite at `~/.pos/degradation.sqlite` (configurable), mirroring the orchestrator's event-sourced local-state pattern. Three tables:

- `detection_events` — every detection signal with mode, timestamp, signal content.
- `episodes` — one row per degradation episode (start, end, modes touched, notifications fired, scopes paused, resume reason).
- `fsm_state` — current state per mode (redundant with event log but cheap cache; rebuildable).

Paused-scope details remain in scope-of-work's event log (no amendment); degradation stores only the scope IDs it paused, tagged by episode UUID. Restart reconciliation handles all four cross-state cases (orchestrator alive + degradation dead; both dead; degradation alive + orchestrator dead; both alive).

### Integration

- **Orchestrator:** `pause_activation(reason)` and `resume_activation()` are the only hooks used. No amendment to orchestrator or its hook surface.
- **Scope-of-work:** existing per-scope metadata carries the policy override. No amendment.
- **Primary-persona layer:** notification goes through its channel-agnostic interaction primitive. No amendment.
- **Memory / objective tracker:** no direct integration.

---

## Deliverables

Ten deliverables D1–D10.

### D1. `ClaudeClient` adapter

**Objective:** a thin wrapper around the Anthropic SDK that all pOS LLM calls route through; observes typed exceptions and `retry-after` headers for passive detection; exposes an active-probe interface for half-open states.
**Acceptance:** every pOS LLM call (pre-existing callsites in memory extraction pipeline, primary-persona monitor's stuck-reason pass, primary-persona authoring pipeline, any orchestrator-level calls) routes through the adapter; exceptions propagate; `retry-after` values are readable; an active probe call is exposed for FSM half-open testing.

### D2. Per-mode FSMs

**Objective:** six finite-state machines (one per failure mode) with closed/open/half-open/closed transitions; transitions fire from detector events (D3).
**Acceptance:** each mode's FSM transitions correctly from synthetic detector events; tests cover at least one full cycle per mode; state is deterministic from the event log.

### D3. Detection rubrics

**Objective:** the six detectors from the research matrix, each with its default thresholds, all per-workspace-tunable via configuration.
**Acceptance:** injecting synthetic Claude failures produces the right FSM transitions at the right thresholds; workspace configuration overrides the defaults cleanly; the garbage detector's pydantic→regex→LLM-judge chain respects the 5-judge/hour budget.

### D4. Response-policy dispatch

**Objective:** four policies (P1/P2/P3/P4) implementable; per-mode defaults wired; per-scope override respected; orchestrator `pause_activation(reason)` called for P1/P2.
**Acceptance:** a mode entering `open` triggers the right policy via the orchestrator's hook; per-scope overrides (marked at scope creation) change policy for that scope only; P3 fall-through cleanly marks scopes failed with recoverable state; P4 produces a per-scope user-decision surface via the notification channel.

### D5. Notification threshold

**Objective:** the compound-OR notification threshold fires correctly; one notification per episode (de-duped by UUID); Tier 1 for auth-broken, Tier 2 otherwise; resume fires a second notification.
**Acceptance:** synthetic degradation episodes hitting each of the four conditions produce notifications at the right moment; duplicates within an episode are suppressed; auth-broken fires Tier 1 immediately; resume fires a second notification.

### D6. Safe-mode narrative + deterministic fallback

**Objective:** Claude-authored narrative when Claude is partially working; deterministic template when Claude is the failure source; user always gets informed.
**Acceptance:**
- Rate-limited / Garbage / Latency-sustained / partial-Overloaded scenarios produce a Claude-authored narrative via the `ClaudeClient` adapter (using a secondary probe call, budgeted).
- Down / Overloaded (fully out) / Auth-broken scenarios use the deterministic template; no Claude call attempted in the notification path.
- The deterministic template is human-readable, structured, covers the essentials (what's paused, which mode, recommended user action, resume conditions).

### D7. Resume mechanism

**Objective:** automatic resume for transient modes when the healthy signal passes; gated on user confirmation for auth-broken and for any episode whose dwell exceeds the tunable threshold (default 30 min).
**Acceptance:**
- Each transient mode resumes automatically after N consecutive successful probes.
- Auth-broken requires explicit user confirmation via the notification channel; no automatic resume.
- Any episode in dwell > 30 min (tunable) gates resume on user confirmation regardless of mode.
- Resume calls `orchestrator.resume_activation()`; scopes resume per scope-of-work's existing pause/refund semantics.

### D8. State preservation + restart reconciliation

**Objective:** own SQLite with three tables; event-sourced pattern mirroring orchestrator; restart cleanly reconciles cross-state cases (orchestrator-alive-degradation-dead, both-dead, degradation-alive-orchestrator-dead, both-alive).
**Acceptance:**
- Database exists at `~/.pos/degradation.sqlite` on first run; configurable path.
- Event log plus FSM-state cache.
- Simulated crash scenarios (SIGKILL at various moments) produce correct reconciliation on restart.
- v1.1 R1 semantic round-trip upgrade test passes.

### D9. OTel observability emission

**Objective:** every operation emits per v1.1 R11; A1-safe (no consumer assumed).
**Acceptance:** detection events, FSM transitions, policy dispatches (which policy, which scopes), notification-threshold crossings, resume events — all produce OTel spans/events; A1-safe (no consumer required); v1.1 R12 per-prompt-type cost attribution for any Claude calls made by the narrative path.

### D10. Bundled documentation + one-hour-outage verification

**Objective:** v1.1 R4 bundled docs plus the one-hour-outage acceptance test (time-compressed simulation with an injectable clock).
**Acceptance:**
- Prose, architecture diagram (ClaudeClient adapter + FSMs + orchestrator hooks + notification channel), data-flow for a representative episode, relationship map, API reference.
- One-hour-outage simulation runs in CI time (compressed clock); the eight consistency invariants enumerated in the research pass (scope events remain consistent; no half-ingested memory records; no orphan spans; no lost bind-scope events; FSM state rebuildable from event log; paused-scope IDs match scope-of-work's paused set; notification dedup correct; resume reconciles).
- Measurement: false-positive rate on the Garbage detector, against a synthetic corpus of known-good Claude outputs.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Graceful-degradation — 1hr outage does not corrupt in-flight state | D8 + D10 |
| v1.0 Graceful-degradation — sessions resume cleanly | D7 + D8 |
| v1.0 Graceful-degradation — user informed before blast-radius threshold | D5 + D6 |
| v1.0 Observability — every action auditable | D9 |
| v1.1 R1 — semantic round-trip upgrade | D8 |
| v1.1 R4 — bundled documentation | D10 |
| v1.1 R11 — OTel observability | D9 |
| v1.1 R12 — per-prompt-type cost attribution (for narrative Claude calls) | D9 |
| v1.1 R13 — channel-agnostic interaction (one-on-one only for notifications) | D5 |

---

## Dependencies

### Hard dependencies

- **All five sealed components.** Orchestrator (hooks only), primary-persona layer (notification channel), scope-of-work (per-scope policy override metadata), memory (own extraction pipeline routes through ClaudeClient), objective tracker (no direct integration but present for completeness). **No amendments.** If the build genuinely requires an amendment, halt and surface.

### Soft dependencies

- Future observability aggregator (subscribes to OTel emissions).
- Future self-upgrade framework (own SQLite participates in pOS-wide upgrade-fidelity story).

### Permitted runtime dependencies

- stdlib, pydantic, pyee, opentelemetry-api/sdk, PyYAML. Anthropic SDK is already in scope via the primitives. Anything additional requires halt-and-signal.

---

## Assumptions (inference recorded — flagged so the builder can challenge)

1. **`ClaudeClient` adapter replaces direct Anthropic SDK calls everywhere in pOS.** Research recommends this; it's the cleanest passive-detection integration. If the builder finds a sealed component has a reason not to route through the adapter, halt and flag — the alternative is leaving a detection blind spot, which is worse than the adaptation cost.
2. **Detection thresholds and dwell defaults are the primary persona-calibrated from research conventions** (pybreaker/tenacity/Anthropic-SDK retry patterns). If the builder finds them unrealistic on test workloads, halt and flag.
3. **Deterministic fallback template is a single authored template, not per-mode.** Workspace-tunable wording. If the builder finds per-mode templates materially clearer, halt and flag.

---

## Open questions for the owner

Three decisions would sharpen the handoff brief. the primary persona has a lean on each.

1. **Default notification tier — Tier 2 (silent delivery) or Tier 1 (audible push)?** Research recommends Tier 2 default with Tier 1 for auth-broken. recommendation: **accept.** Tier 2 is right for the compound-OR threshold being modest; auth-broken legitimately needs an audible interrupt.

2. **Model default for Claude-authored safe-mode narrative.** Options: use the same `claude-haiku-4-5` that extraction uses (cheap, consistent); use a larger model only here (quality); per-workspace-tunable. recommendation: **per-workspace-tunable, default to `claude-haiku-4-5`.** Consistent with the rest of the rebuild's cost posture.

3. **Per-workspace tunability defaults — ship the research thresholds as baked-in defaults, or ship them as an editable `~/.pos/degradation-config.yaml` that workspaces can override?** recommendation: **editable YAML with research defaults as starting values.** Matches the "workspace is content, framework is contract" pattern Phase 1 established.

Default to leans unless any reads wrong to you.

---

## What happens on approval

1. I draft the handoff brief. the owner decisions baked in from research: six failure modes with defaults, four policies, compound-OR notification, 30-min resume-gate, own SQLite, Claude-or-fallback narrative. Plus the three the primary persona leans above on approval.
2. On brief review, a general-purpose agent is dispatched.
3. Halt-on-deviation applies. Any sealed-component amendment genuinely required → halt and surface.
