# Handoff Brief — Graceful Degradation

**Component:** Graceful Degradation (second Phase 2 component)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-19 09:16 CDT, all three open questions resolved per the primary persona's leans)
**Spec:** objectives spec v1.0 + v1.1 + v1.2 addenda

---

## Objective

Deliver a production-ready graceful-degradation component. Build deliverables D1–D10 from the proposal. The component ships on the `pos-v2` branch as a policy layer that wraps all Claude API calls via a `ClaudeClient` adapter, tracks six failure modes through per-mode finite-state machines, calls the sealed orchestrator's `pause_activation` / `resume_activation` hooks on state changes, notifies the user via the primary-persona layer's one-on-one channel surface when a compound-OR blast-radius threshold is crossed, and preserves state across restart. No sealed component is amended.

---

## Hard constraints

1. **Implementation language:** Python 3.13 dev target, `pos-v2` branch. Work lives under `pos-v2/graceful-degradation/` (mirror prior component layouts).
2. **No amendments to any of the five sealed components.** Memory, scope-of-work, primary-persona layer, objective tracker, orchestrator all stay as they are. The orchestrator's hook surface is `pause_activation(reason)` / `resume_activation()` only. If the build genuinely requires an amendment, halt and surface.
3. **Zero carryover from current pOS.** Current-pOS retry/rate-limit logic is not a reference.
4. **Permitted runtime dependencies:** stdlib, `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`, `PyYAML`. Anthropic SDK is already in scope via the primitives. Test-only (pytest, pytest-asyncio) permitted. Anything else requires halt-and-signal.
5. **Max-first.** Safe-mode narrative and any LLM-assisted detection use Claude via Max. Default model for narrative authoring: `claude-haiku-4-5` (workspace-tunable per decision below).
6. **No personas in pOS core.** Framework only.
7. **No assumed downstream consumer (A1 correction).** OTel emission must succeed with no consumer present.
8. **One-on-one notification channels only.** Inherits v1.1 R13 + v1.2 R15 — no group-channel notifications, no framework override.
9. **Halt-on-deviation.** Silent deviation forbidden.
10. **Bundled documentation per v1.1 R4.** Ships at `graceful-degradation/docs/`.

## rulings recorded baked into this brief

- **Detection:** `ClaudeClient` adapter wraps all pOS Claude calls. Passive observation of Anthropic SDK typed exceptions + `retry-after` headers. Active probing only during half-open FSM state.
- **Six failure modes with default thresholds** (per-workspace-tunable):
    - **Down** — 3 connection/timeout/5xx failures in 60 s → P1 pause-all
    - **Overloaded 529** — 2 × 529 in 30 s → P1 pause-all
    - **Rate-limited 429** — any 429 (honour `retry-after`) → P2 pause-LLM-only
    - **Garbage** — 3 of last 10 fail the pydantic → regex → LLM-judge chain (5-judge/hour budget) → P2 pause-LLM-only
    - **Auth-broken 401** — any 401 → P4 request-user-decision
    - **Latency-sustained** — p95 > threshold for 5 min → advisory only
- **Four response policies:** P1 pause-all, P2 pause-LLM-only, P3 fall-through-to-fail, P4 request-user-decision. Per-scope overrides via scope-of-work's existing metadata.
- **Compound-OR notification threshold:** wall-clock ≥ 5 min OR paused-scope count ≥ 3 OR any paused scope carries a user-relevant escalation trigger OR auth-broken (always fires). One notification per episode (UUID-deduped); resume fires a second.
- **Notification tier policy:** Tier 2 default (silent delivery); Tier 1 for auth-broken (audible push).
- **Safe-mode narrative:** Claude-authored (Haiku 4.5 default, workspace-tunable) when Claude is partially working; deterministic fallback template when Claude is the failure source. Single fallback template, workspace-tunable wording.
- **Resume:** automatic for Down / Overloaded / Rate-limited / Garbage once the healthy signal passes; gated on user confirmation for auth-broken and for any episode whose dwell exceeds **30 minutes** (tunable).
- **State:** own SQLite at `~/.pos/degradation.sqlite` (configurable). Three tables: `detection_events`, `episodes`, `fsm_state`. Paused-scope details remain in scope-of-work's event log; degradation stores only the IDs it paused, tagged by episode UUID.
- **Per-workspace tunability:** editable `~/.pos/degradation-config.yaml` with research defaults as starting values. Workspace overrides supersede defaults cleanly.

---

## Deliverables

Ten deliverables D1–D10 as named in the proposal. Objective-level acceptance; no prescribed module names, class hierarchies, file layout, or function signatures beyond the API surface sketched in the proposal.

### D1. `ClaudeClient` adapter

**Objective:** a thin wrapper around the Anthropic SDK that every pOS LLM call routes through. Observes typed exceptions + `retry-after` headers for passive detection; exposes an active-probe interface for half-open FSM states.
**Acceptance:**
- Every existing pOS LLM call routes through the adapter (memory extraction, primary-persona monitor's stuck-reason pass, primary-persona authoring pipeline, any other).
- Exceptions propagate to callers unchanged; `retry-after` readable on rate-limit errors.
- Active probe interface returns success/failure + timing for use by FSMs.
- Integration test confirms all sealed components' existing LLM paths continue to work after routing through the adapter.

### D2. Per-mode FSMs

**Objective:** six finite-state machines (closed → open → half-open → closed) with transitions driven by D3 detector events.
**Acceptance:**
- Each mode's FSM handles its full lifecycle correctly from synthetic events.
- State transitions are deterministic from the event log (given the same events, same state).
- Independent FSMs — one mode opening doesn't accidentally transition another.

### D3. Detection rubrics

**Objective:** the six detectors with research-recommended default thresholds, all per-workspace-tunable via `~/.pos/degradation-config.yaml`.
**Acceptance:**
- Synthetic Claude-side failures produce correct FSM transitions at the documented thresholds.
- Workspace configuration in the YAML overrides defaults cleanly; malformed YAML rejects with a clear error.
- Garbage detector's pydantic → regex → LLM-judge chain respects the 5-judge/hour budget.

### D4. Response-policy dispatch

**Objective:** policies P1/P2/P3/P4 implemented; per-mode defaults wired; per-scope override via scope-of-work's existing metadata; orchestrator hooks called correctly.
**Acceptance:**
- Mode entering `open` triggers the correct policy; `pause_activation(reason)` called on the orchestrator for P1/P2.
- Per-scope metadata override at scope creation changes policy for that scope only.
- P3 fall-through marks scopes failed with recoverable state via scope-of-work's existing fail semantics.
- P4 produces a per-scope user-decision surface via the notification channel; scope waits for response.

### D5. Notification threshold

**Objective:** compound-OR threshold fires correctly; dedup per episode; Tier 1 for auth-broken, Tier 2 otherwise; resume fires a second notification.
**Acceptance:**
- Synthetic episodes hitting each of the four threshold conditions produce notifications at the correct moment.
- Duplicate-threshold-crossings within a single episode are suppressed (UUID dedup).
- Auth-broken fires Tier 1 immediately on detection; all other modes fire Tier 2 on threshold.
- Resume fires a second notification per episode.
- Notification channel: the primary-persona layer's one-on-one surface (terminal / Claude desktop / user's personal Telegram). Group channels rejected at construction per v1.2 R15.

### D6. Safe-mode narrative + deterministic fallback

**Objective:** Claude-authored narrative when Claude is partially available; deterministic template when Claude is the failure source; user always informed.
**Acceptance:**
- Rate-limited / Garbage / Latency-sustained / partial-Overloaded scenarios produce a Claude-authored narrative using `claude-haiku-4-5` via the `ClaudeClient` adapter (budgeted secondary call).
- Down / fully-Overloaded / Auth-broken scenarios use the deterministic template; no Claude call attempted in this path.
- Template is human-readable, structured, covers: what's paused, which mode, recommended user action, resume conditions.
- Model is workspace-tunable via `~/.pos/degradation-config.yaml`; default is `claude-haiku-4-5`.
- Template wording is workspace-tunable via the same YAML.

### D7. Resume mechanism

**Objective:** automatic for transient modes; gated on user confirmation for auth-broken and for any episode whose dwell exceeds the tunable threshold (default 30 min).
**Acceptance:**
- Each transient mode auto-resumes after N consecutive successful probes (N=1 for binary modes, N=2 for garbage; tunable).
- Auth-broken requires explicit user confirmation via the notification channel; no auto-resume.
- Any episode in dwell > 30 min (tunable) gates resume on user confirmation regardless of mode.
- Resume calls `orchestrator.resume_activation()`; paused scopes resume per scope-of-work's existing pause/refund semantics.

### D8. State preservation + restart reconciliation

**Objective:** own SQLite with three tables; event-sourced pattern mirroring orchestrator; restart cleanly reconciles the four cross-state cases (orchestrator-alive-degradation-dead, both-dead, degradation-alive-orchestrator-dead, both-alive).
**Acceptance:**
- Database exists at `~/.pos/degradation.sqlite` (configurable) on first run.
- Event log + FSM-state cache; cache rebuildable from events.
- Simulated SIGKILL at various lifecycle moments produces correct reconciliation on restart; no orphan pauses, no lost notifications, no stale FSM state.
- v1.1 R1 semantic round-trip upgrade test passes.

### D9. OTel observability emission

**Objective:** every operation emits per v1.1 R11; per-prompt-type cost attribution for narrative Claude calls per v1.1 R12; A1-safe.
**Acceptance:**
- Detection events, FSM transitions, policy dispatches, notification-threshold crossings, resume events all produce OTel spans/events with relevant attributes.
- Narrative Claude calls produce spans with `pos.prompt.type = degradation-narrative` attribution matching scope-of-work's per-prompt cost view.
- Emission succeeds with no consumer present.

### D10. Bundled documentation + one-hour-outage verification

**Objective:** v1.1 R4 documentation plus the one-hour-outage acceptance test (time-compressed simulation with injectable clock).
**Acceptance:**
- Prose explanation covering all deliverables.
- Architecture diagram (ClaudeClient adapter + FSMs + orchestrator hooks + notification channel + SQLite).
- Data-flow diagram for a representative episode (detection → FSM → policy → notification → resume).
- Relationship map (depends on all 5 sealed components; consumed by future observability aggregator).
- One-page API reference covering the public surface.
- One-hour-outage simulation runs in CI time via an injectable clock; the eight consistency invariants enumerated in the research all pass.
- Measurement: Garbage-detector false-positive rate on a synthetic corpus of known-good Claude outputs.

---

## Dependencies

### Hard dependencies (no amendments permitted)

- All five sealed components: memory, scope-of-work, primary-persona layer, objective tracker, orchestrator. Integration via public APIs and emission surfaces only.

### Soft dependencies (future)

- Observability aggregator (subscribes to OTel emissions)
- Self-upgrade framework (own SQLite participates in pOS-wide upgrade-fidelity story)

### Permitted runtime dependencies

As enumerated in hard constraints. No additional libraries without halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion becomes unsatisfiable under the approved direction.
- Any sealed component amendment appears genuinely required — do not modify silently; surface.
- An additional runtime dependency appears necessary — surface; do not add.
- A research threshold proves unrealistic on the test corpus (e.g. the Garbage detector's false-positive rate is unacceptable at the documented threshold) — surface the measurement and the implied threshold change.
- Any ambiguity requiring an invented constraint not in owner's words.

Halts return control to the primary persona, who reviews with the owner.

---

## Return format

On completion, return a summary (≤700 words):

1. Which deliverables D1–D10 completed, which halted.
2. Which spec criteria now pass (cite v1.0 behaviour or v1.1/v1.2 revision).
3. Confirmation that all five sealed components' tests still pass (scope-of-work 77, objective-tracker 86, primary-persona 101, memory 30, orchestrator 56).
4. Test counts on the graceful-degradation component itself.
5. Garbage-detector false-positive rate measurement.
6. One-hour-outage simulation result (which of the eight invariants passed).
7. Complexity outcome — AI-time vs the proposal's 320–410-minute estimate.
8. Commits on `pos-v2`.
9. Any halt signals raised.
10. Recommended next action.

---

## What this brief is NOT

- Not a specification of module names, class hierarchies, file layout, or function signatures beyond the API surface the proposal has sketched.
- Not a step-by-step execution plan.
- Not a commitment to designing adjacent components (observability aggregator, self-upgrade framework) — those have their own briefs later.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Three items come from the primary persona's interpretation rather than the owner's verbatim words:

- *`ClaudeClient` adapter replaces direct Anthropic SDK calls everywhere in pOS.* Research recommends this; cleanest passive-detection integration. If a sealed component has a reason not to route through the adapter, halt and flag — the alternative (leaving a detection blind spot) is worse than the adaptation cost.
- *Detection thresholds are the primary persona-calibrated from research conventions* (pybreaker/tenacity/Anthropic-SDK retry patterns). If the builder finds them unrealistic on test workloads, halt and flag with measurements.
- *Single deterministic fallback template, not per-mode.* If the builder finds per-mode templates materially clearer, halt and flag.
