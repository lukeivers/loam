# Handoff Brief — Primary-Persona Layer

**Component:** Primary-Persona Layer (loader + monitor + autonomous authoring)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-18 17:13 CDT, all three open questions resolved per the primary persona's leans)
**Spec:** objectives spec v1.0 + v1.1 addendum
**Predecessor artifacts:** `research-plan.md`, `research.md`, `proposal.md`

---

## Objective

Deliver a production-ready primary-persona layer for the new pOS covering three tightly-coupled halves that share a persona contract: the loader + validator, the background-work monitor, and the autonomous-authoring framework. Include the small scope-of-work amendment (D0) the monitor depends on. Every v1.0 Primary-persona acceptance criterion, STATE.md rule #7, v1.1 R4/R11/R13, and the three staged-for-v1.2 authoring-and-introduction requirements must pass on the built component. When this component lands, a workspace can supply its own primary persona, be aware of background work at all times, and have the primary persona autonomously author specialist personas that are properly introduced to the user before speaking.

---

## Hard constraints

1. **Implementation language:** Python.
2. **Branch discipline:** `pos-v2` on the existing the existing workspace repo repo. No modifications to `main`. Work lives under `pos-v2/primary-persona/` (mirror the pattern `memory-system/` and `scope-of-work/` use). The scope-of-work amendment (D0) lands in `pos-v2/scope-of-work/`.
3. **Zero carryover from current pOS / the existing workspace.** No reading of `prior-pOS .claude/hooks/compaction-resilience.rb`, `.claude/agents/*`, existing Ruby persona files, or any current-pOS machinery for design inspiration. Read once to understand *what* questions they address (compaction survival, persona switching) if needed; do not carry patterns or code structures forward.
4. **Permitted runtime dependencies:** Python stdlib (pathlib, asyncio, uuid, sqlite3, dataclasses), `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`. **PyYAML** is permitted for loading `contract.yaml` (it is stdlib-adjacent in the Python ecosystem and needed for the contract file; flagged here because it wasn't on the scope-of-work permitted list). Any other runtime library requires halt-and-signal. Test-only dependencies (pytest, pytest-asyncio) are fine under the rebuild's rule #8.
5. **Max-first.** All LLM inference inside the layer — monitor's optional stuck-reason pass, creation-trigger yes/no judgment, authoring pipeline (style-harvest, domain-research, contract-synthesis, self-review) — uses Claude via Max. No other vendors.
6. **No personas shipped in pOS core.** The authoring framework, template, quality checks, and introduction protocol live in pOS core. Zero persona content (no `contract.yaml` / `prompt.md` files) in `pos-v2/primary-persona/`. A build-time check must fail if any persona directory appears in pOS-core paths.
7. **No assumed downstream consumer (A1 correction).** The layer emits OTel observability; no consumer is assumed to exist.
8. **Halt on deviation.** If any constraint cannot be honoured, any spec acceptance criterion becomes unsatisfiable, or a design question mid-build reveals the approved direction is untenable, stop immediately, write what you found up to the halt, name the specific constraint or criterion, and return.
9. **Bundled documentation per v1.1 R4.** Ships alongside the code; prose, diagrams, relationship map, API reference.

## rulings recorded baked into this brief

- **Default `expected_duration_seconds` value: `None`.** Scopes opt in to stuck-detection by declaring the field; omission means the monitor does not attempt stuck-inference for that scope.
- **Group-channel introductions: strictly forbidden.** New personas are introduced only to the user's current one-on-one channel (terminal, Claude desktop, or the user's personal Telegram thread). Never to group chats. No edge-case override.
- **Default retire-window: indefinite.** The user can retire a newly-introduced persona at any time after introduction. No hard timeout; the persona's `is_addressable` flag flips True on the user's next non-retire message regardless of delay.
- **Compaction survival approach: replay-from-authoritative-sources.** Use a PreCompact flag + UserPromptSubmit detection for v1 (flag-and-detect workaround for the missing PostCompact hook in the Python Agent SDK).
- **Stuck-detection multiplier: 2×.** Deterministic: `elapsed > 2 × expected_duration_seconds` with no state events triggers stuck; optional Claude-via-Max second pass for `stuck_reason`.

---

## Deliverables

Eleven deliverables D0–D10 as named in the proposal. Each has an objective and acceptance criteria in objective terms. None prescribe implementation method, file layout, module names, class structure, or function signatures beyond the API surface and the directory layout the proposal has sketched.

### D0. Scope-of-work amendment — `expected_duration_seconds` field

**Objective:** add an optional `expected_duration_seconds: float | None = None` field to `ScopeSpec` in the sealed scope-of-work primitive. This is the single change needed to enable deterministic stuck-detection in D3.
**Acceptance:**
- Field exists on `ScopeSpec` as an optional float.
- Default is `None`; scopes without the field load and behave as before.
- Field flows through the event log and projection cache.
- All existing scope-of-work tests (63 passing) remain green.
- One new test asserts that when `expected_duration_seconds` is set and `elapsed > 2 × expected_duration_seconds` without state events, the scope is identifiable as stuck via `list(filter={stuck: true})`.
- Ships as its own commit before D1 begins (small atomic change).

### D1. Persona contract + template

**Objective:** the canonical persona directory layout is defined and the contract is Pydantic-validated.
**Acceptance:**
- Directory layout: `workspace/personas/<handle>/contract.yaml` + `prompt.md` (mandatory), with optional `voice.md` and `home/`.
- `contract.yaml` mandatory fields: handle, given_name, contract_version (semver), responsibilities (single_point_of_contact, context_holder, escalation_judge), authority_boundary (per Tier A/B/C/D: execute/defer/not_applicable), escalation_taxonomy, severity_vocabulary.
- `contract.yaml` optional fields: delegates_to, home_persona_for, voice_markers.
- A Pydantic model validates the YAML and rejects missing mandatory fields with errors that name each missing field.
- Template directory exists in pOS core as a copy-to-workspace starter (documented; a workspace can copy, fill in, and load).

### D2. Loader + validator

**Objective:** pOS loads a workspace-supplied persona directory at session start, validates against the contract, fails closed on any invalidity.
**Acceptance:**
- Valid persona loads cleanly; invalid persona rejects with a clear error naming the failing field.
- No persona directory present in workspace → session cannot start (a deterministic check, not advisory).
- Build-time check fails if any persona directory appears in pOS-core paths (`pos-v2/primary-persona/` or any other pOS-core path) — v1.0: no personas in core.
- Loader is stateless; reloading the same directory produces identical results.
- Loader runs on session start and on explicit reload API call.

### D3. Background-work monitor

**Objective:** a long-lived asyncio coroutine subscribes to scope-of-work's pyee emitter and a 30-second stuck-detection tick; produces a capped structured awareness block injected on every UserPromptSubmit.
**Acceptance:**
- Monitor starts with the session; handles pyee events in real time; handles the 30-sec tick deterministically.
- Awareness block ≤ 1,000 tokens; structured format (JSON-like); six categories (active / pending-decision / stuck / recently-finished / escalated / failed); ≤ 5 rows per category.
- Stuck detection fires for scopes where `elapsed > 2 × expected_duration_seconds` with no state events since start (depends on D0).
- Stuck detection's optional Claude-via-Max second pass populates `stuck_reason` on flagged scopes; budget-capped per tick.
- Injection on every UserPromptSubmit is structural (not reliant on the persona remembering to check) — STATE.md rule #7 is a hook, not an instruction.
- Monitor survives brief asyncio task failures (one failed tick does not kill the coroutine).
- Monitor emits its own health via OTel.

### D4. Compaction survival — replay-from-authoritative-sources

**Objective:** after compaction, persona identity, authority boundary, current scope context, pending decisions, and recent corrections are re-injected deterministically on the first post-compaction UserPromptSubmit.
**Acceptance:**
- PreCompact hook writes a flag file; UserPromptSubmit checks for the flag on each turn and triggers restoration exactly once.
- Restoration injects from authoritative sources: loaded contract (for persona identity + authority boundary), scope-of-work `list(filter)` (for current scope context + pending decisions), memory (for recent corrections).
- The canonical five-item survival list (persona identity, authority boundary, current scope context, pending decisions, recent corrections) is verifiably intact after restoration.
- A simulated compaction-and-restore test confirms end-to-end correctness.
- Flag is cleared after successful restoration; repeated UserPromptSubmit turns do not re-inject.

### D5. Creation-trigger detector

**Objective:** five deterministic signals monitor ongoing work for opportunities to author a new specialist persona; a judgment step decides whether to act.
**Acceptance:**
- Each of the five signal types is detectable from observable events: request declines (repeated user pushback in a domain), domain corrections, cross-domain scopes, low-relevance memory hits, explicit user mentions.
- A threshold rubric is defined per signal with concrete numbers (not "vibes"); thresholds are tunable per workspace.
- When a threshold is crossed, a judgment LLM call (Claude-via-Max) runs inside a small budgeted scope-of-work; output is one of `yes | no | defer` with rationale recorded to memory.
- `yes` triggers the authoring pipeline (D6); `no` records the rejection; `defer` schedules a re-check after a tunable delay.

### D6. Autonomous authoring pipeline

**Objective:** a four-step Claude-via-Max pipeline produces a new persona directory that passes the D1 contract and the self-review quality bar.
**Acceptance:**
- Pipeline runs inside an authoring scope-of-work with a declared budget (time/tokens/money) such that runaway generation is impossible.
- Four steps execute in order: style-harvest (read existing workspace personas for voice consistency) → domain-research (web search and/or memory query on the domain) → contract-synthesis (fill in the Pydantic schema + prompt.md) → self-review (four dimensions: voice-distinctiveness via the "not-generic" test, scope-fit, redundancy with existing personas, contract-correctness).
- Maximum two iterations through self-review. On the third failure, the authoring scope terminates with a failure recorded to memory; primary persona chooses to log and stop or retry with adjusted scope.
- Newly-authored persona directory passes D1's validation by construction (tested).
- Cost per authored persona is measurable and surfaced via the per-prompt cost view on scope-of-work.

### D7. Introduction protocol — one-on-one channel only

**Objective:** on successful authoring, the user is introduced to the new persona before any message from that persona is delivered.
**Acceptance:**
- New persona directory is persisted with `pending_introduction: true` and `is_addressable: false` as declared fields in its state.
- Primary persona writes a structured introduction (new persona's name, domain, trigger that caused authoring, what they'll handle, retire instructions) and dispatches **only to the user's current one-on-one channel** — terminal, Claude desktop, or the user's personal Telegram thread. Never to group channels.
- If the user is currently reachable on zero one-on-one channels, the introduction is queued and fires when a one-on-one channel is next active.
- `is_addressable` flips True only on the user's next non-retire message; a retire instruction moves the directory to `_retired/<handle>-<timestamp>/` and the flag never flips True.
- An integration test verifies no message identifying the new persona as sender can be delivered before `is_addressable: true`.

### D8. Retirement

**Objective:** retired personas are cleanly removed from the active roster; history is preserved; auditable.
**Acceptance:**
- Retirement moves `personas/<handle>/` to `personas/_retired/<handle>-<timestamp>/`.
- Active loader ignores `_retired/*`; memory/scopes referencing the retired persona by ID continue to resolve via history.
- Retirement emits an auditable event with the retirement reason (user-initiated, never-acknowledged, workspace-policy).
- A test asserts that a retired persona cannot be reloaded without explicit un-retirement (moving the directory back).

### D9. OTel observability emission

**Objective:** every operation in the persona layer emits OTel spans/events per v1.1 R11.
**Acceptance:**
- Loader runs produce spans with outcome (loaded / failed + field).
- Monitor ticks and injections emit events (one event per tick; one per injection).
- Authoring pipeline produces a parent span with one child span per of the four steps; self-review verdicts are events on the span.
- Introduction dispatch emits an event naming the new persona's handle and the channel used.
- Retirement emits an event naming the persona and reason.
- Emission succeeds with no consumer present (A1 correction).

### D10. Bundled documentation

**Objective:** v1.1 R4 — human-readable documentation bundled with the component.
**Acceptance:**
- Prose explanation covering all three halves.
- Architecture diagram (three halves + shared contract artifact).
- Data-flow diagram for a representative lifecycle: session start → loader → monitor tick → authoring trigger → authoring pipeline → introduction → activation → retirement.
- Relationship map: subscribes to scope-of-work emitter; reads from memory; emits to OTel; surfaces to channel-agnostic-interaction when that component lands.
- One-page API reference for loader, monitor, authoring triggers, retirement.
- Non-technical reader can answer "what does this layer do and how does it fit with the others" from the bundled docs alone.

---

## Dependencies carried forward

- **Hard dependencies:** scope-of-work (with D0 amendment) and memory-system (no changes needed).
- **Soft dependencies:** observability aggregator (subscribes to emissions), safety layer (consumes authority-boundary declarations), cost governance (consumes scope budgets), self-correction loop (subscribes to persona-authored-but-rejected events).
- **Permitted runtime:** stdlib + pydantic + pyee + opentelemetry-api/sdk + PyYAML. Anything else requires halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion is discovered to be unsatisfiable under the approved direction (do not silently drop it).
- An additional runtime dependency beyond the permitted list appears necessary (surface it; do not add unilaterally).
- Any ambiguity requiring an invented constraint that the owner has not specified.
- Group-channel-introduction policy is challenged by a concrete scenario the research did not anticipate (surface it; the rule is strict one-on-one).
- A spec conflict surfaces between the v1.0 primary-persona criteria and the proposed authoring/introduction mechanics — such as the introduction being classified as a Tier A violation in a context the research didn't cover.

Halts return control to the primary persona, who reviews with the owner. The proposal is adjusted; execution resumes against the revised version.

---

## Return format

On completion, return with a summary (≤700 words) covering:

1. Which deliverables D0–D10 completed, which halted (if any).
2. Which spec acceptance criteria now pass on the component (cite v1.0 behaviour or v1.1/v1.2 revision number).
3. The three staged-for-v1.2 spec revisions with concrete wording proposals (ready for owner's approval to land in a v1.2 addendum).
4. Test counts and pass rates across all deliverables.
5. Complexity outcome — AI-time actually taken vs. the proposal's ~620-minute estimate.
6. Confirmation that scope-of-work's D0 amendment landed cleanly (all 63+ pre-existing tests still passing plus the one new stuck-detection test).
7. Commits on `pos-v2`.
8. Any halt signals raised.
9. Recommended next action: declare the component complete / flag remaining gaps.

---

## What this brief is NOT

- Not a specification of module names, class hierarchies, file internal structure, or function signatures beyond the API surface and directory layout the proposal has sketched.
- Not a step-by-step execution plan.
- Not a commitment to designing adjacent primitives (observability aggregator, safety layer, cost-governance enforcer, self-correction loop). Those have their own components and briefs.
- Not a commitment to retrofit previous pOS persona-authoring patterns. The autonomous-authoring framework is novel new-pOS work.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Three items below come from the primary persona's interpretation rather than the owner's verbatim words. Marked so the builder can surface objections:

- *PyYAML is permitted for `contract.yaml` loading.* Not explicitly on the owner's permitted-list, but `contract.yaml` is the owner-specified and PyYAML is the standard Python library for YAML. If the builder prefers a stdlib-only approach (e.g. `tomllib` with `contract.toml` instead), halt and flag.
- *The "if you are currently reachable on zero one-on-one channels, queue the introduction" clause in D7.* the owner stated the restriction (one-on-one only) but did not name the queueing behaviour for the zero-channels case. inference recorded: queue and fire on next one-on-one activity. If the builder reads this differently, halt and flag.
- *Threshold rubric values for the five creation-trigger signals are tunable per workspace with sensible defaults.* the owner did not specify defaults. the primary persona's inclination: reasonable starting defaults in the brief (e.g. 3 repeated declines in a 7-day window) that workspaces can override. If the builder needs owner's per-signal defaults specified before proceeding, halt and flag.
