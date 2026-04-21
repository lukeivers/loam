# Primary-Persona Layer — Proposal

**Component:** Primary-Persona Layer (loader + monitor + autonomous authoring)

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 addendum
**Informed by:** `research-plan.md` (revised 14:40 CDT), `research.md` (returned 14:50 CDT, 853 lines). the owner's three halt-signal rulings 2026-04-18 17:07 CDT are baked in.

---

## Summary

Build the primary-persona layer as three tightly-coupled halves sharing a persona contract: a directory-based loader that validates workspace personas against a Pydantic schema, an always-on background-work monitor that keeps the primary persona aware of in-flight scopes, and an autonomous-authoring framework that lets the primary persona judge when a specialist persona is warranted and create one — with mandatory user introduction before any message from the new persona lands. Compaction survival is by replay-from-authoritative-sources, a clean divergence from the current-pOS snapshot-and-restore. The build also includes a small amendment to the sealed scope-of-work primitive (adding an `expected_duration_seconds` field to `ScopeSpec`) so the monitor's stuck-detection can operate deterministically.

## Direction

### Persona contract — directory layout

Each workspace persona is a directory: `workspace/personas/<handle>/` containing:

- `contract.yaml` — structured, Pydantic-validated. Fields: handle, given name, contract semver, three functional responsibilities (single point of contact, context holder, escalation judge), authority boundary per Tier A/B/C/D, escalation taxonomy, severity vocabulary. Optional fields: delegates-to, home-persona-for, voice markers.
- `prompt.md` — free prose. The persona's voice, calibration examples, domain, rules. pOS does not parse this; the workspace owns it.
- Optional `voice.md` and `home/` directory for supplementary content.

pOS validates the YAML; the workspace owns the prose.

### Loader

Stateless: reads the persona directory on session start (and on explicit reload), validates against the Pydantic schema, returns a loaded-persona object. Fail-closed on missing directory, invalid YAML, contract mismatch, or version skew — no fallback persona ever. The clear failure mode satisfies the spec's "a workspace with no primary persona cannot start a session; failure mode is clear and immediate."

### Monitor

Long-lived asyncio coroutine. Subscribes to scope-of-work's `pyee` emitter for state transitions; runs a 30-second tick for stuck-detection. On every `UserPromptSubmit`, produces a structured awareness block (~1k tokens max, capped at 5 rows per category: active / pending-decision / stuck / recently-finished / escalated / failed) and injects it into context. Stuck-detection is deterministic (elapsed > 2× `expected_duration_seconds` with no state events) with an optional Claude-via-Max second pass for `stuck_reason`. STATE.md rule #7 is delivered structurally — the monitor injects every turn; the persona cannot forget to check.

### Compaction survival

Replay-from-authoritative-sources, *not* snapshot-and-restore. On the first `UserPromptSubmit` after compaction (detected via a `PreCompact` flag + `UserPromptSubmit` check — the owner-approved workaround for the missing Python SDK `PostCompact` hook), re-inject: persona identity from the loaded contract, current awareness block from scope-of-work, and a five-item canonical survival list (persona identity, authority boundary, current scope context, pending decisions, recent corrections). Clean divergence from the current-pOS snapshot-restore pattern.

### Autonomous authoring — five-signal detector → Claude-Max pipeline

Deterministic detector watches five signals during ongoing work:

1. Request declines (user says "that's not quite right" repeatedly in a domain).
2. Domain corrections (user corrects the primary persona's handling of a domain).
3. Cross-domain scopes (a scope keeps touching a domain the primary persona isn't good at).
4. Low-relevance memory hits (retrieval keeps returning peripheral matches on a topic).
5. Explicit user mentions ("wish I had someone for X").

When a signal-threshold is crossed, primary persona runs an LLM judgment (Claude-via-Max): does authoring a specialist materially improve future output? If yes, it launches an authoring scope (budgeted via scope-of-work) that runs four steps: style harvest (read existing workspace personas for voice consistency), domain research (web search / memory query on the domain), contract synthesis (fill in the Pydantic schema), self-review against four dimensions (voice-distinctiveness via the "not-generic" test, scope-fit, redundancy, contract-correctness). Up to two iterations; then persist the new persona directory.

### Introduction protocol — one-on-one channel only (the owner-approved)

On successful authoring, the persona file is written with `pending_introduction: true` and `is_addressable: false`. Primary persona authors a structured introduction message (new persona's name, domain, trigger that caused authoring, what they'll handle, how to retire them if unwanted) and dispatches **only to the user's current one-on-one channel** — terminal, Claude desktop app, or the user's personal Telegram thread. Never to group chats (Tier A safety per security.md).

The new persona's `is_addressable` flag remains False until the user's next non-retire message. If the user responds with a retire instruction, the persona directory is moved to `_retired/<handle>-<timestamp>/` and the flag is never flipped True.

## Deliverables

Eleven deliverables D0–D10. Each has an objective and acceptance criteria; none prescribe implementation method.

### D0. Scope-of-work amendment — `expected_duration_seconds` field

**Objective:** add an optional `expected_duration_seconds` field to `ScopeSpec` in the scope-of-work primitive so the monitor's stuck-detection operates deterministically. ruling recorded 2026-04-18 17:07 CDT.
**Acceptance:** field exists; default is `None` (scope opts out of stuck-detection when omitted); field flows through event log and projection; no existing scope-of-work tests break; one new integration test asserts stuck-detection fires when `elapsed > 2 × expected_duration_seconds`.

### D1. Persona contract + template

**Objective:** the canonical persona directory layout and Pydantic contract are defined and published as part of pOS core's framework surface.
**Acceptance:** `contract.yaml` schema validates against a concrete Pydantic model; a workspace can copy a template directory and fill it in; the schema rejects missing mandatory fields at load time with clear errors; contract semver is present.

### D2. Loader + validator

**Objective:** pOS loads a workspace-supplied persona directory at session start, validates it against the contract, fails closed on any invalidity.
**Acceptance:**
- Valid persona loads cleanly; invalid persona rejects with clear error naming the field.
- No persona directory present → session cannot start.
- A build-time check fails if any persona directory appears in pOS-core paths (v1.0: no personas in core).
- Loader is stateless; reloads produce identical results given identical input.

### D3. Background-work monitor

**Objective:** a long-lived asyncio coroutine subscribes to scope-of-work's pyee emitter and stuck-detection tick; injects a capped structured awareness block into every UserPromptSubmit.
**Acceptance:**
- Monitor starts with the session; handles pyee events in real time; handles 30-sec tick deterministically.
- Awareness block is capped at ~1k tokens; structured JSON-like format; five categories (active / pending-decision / stuck / recently-finished / escalated / failed); 5 rows per category max.
- Stuck detection fires for scopes where `elapsed > 2 × expected_duration_seconds` with no state events (requires D0).
- Monitor survives brief asyncio task failures; reports its own health via OTel.
- Injection is deterministic on every UserPromptSubmit (structural, not advisory — STATE.md rule #7).

### D4. Compaction survival — replay-from-authoritative-sources

**Objective:** after compaction, persona identity, authority boundary, current scope context, pending decisions, and recent corrections are re-injected deterministically on the first post-compaction UserPromptSubmit.
**Acceptance:**
- PreCompact hook writes a flag; UserPromptSubmit detects the flag and triggers restoration.
- Restoration block injects from authoritative sources (contract.yaml for persona, scope-of-work `list(filter)` for scopes, memory for recent corrections) — not from a saved snapshot.
- A simulated compaction-and-restore test confirms the five-item canonical survival list is intact.
- Flag is cleared after successful restoration.

### D5. Creation-trigger detector

**Objective:** five deterministic signals monitor ongoing work for opportunities to author a new persona; a judgment step decides whether to act.
**Acceptance:**
- Each of the five signal types is detectable from observable events (memory queries, scope events, user messages).
- A threshold rubric is defined per signal (concrete numbers, not vibes).
- When a signal threshold is crossed, the judgment LLM call (Claude-via-Max) runs under a small scope-of-work with budget; output is `yes | no | defer` with rationale.
- `yes` triggers the authoring pipeline (D6); `no` records the rejection to memory; `defer` schedules re-check after a tunable delay.

### D6. Autonomous authoring pipeline

**Objective:** a four-step Claude-via-Max pipeline produces a new persona directory that passes the contract + quality checks.
**Acceptance:**
- Pipeline runs inside an authoring scope-of-work with declared budget (time/tokens/money) — runaway generation impossible.
- Four steps execute in order: style-harvest → domain-research → contract-synthesis → self-review.
- Self-review covers voice-distinctiveness (not-generic test), scope-fit, redundancy with existing personas, contract-correctness.
- Max two iterations through self-review; then persisted regardless, or rejected if still failing (rejection notifies primary persona, who chooses to log and stop or retry with adjusted scope).
- Newly-authored persona directory passes D1's validation by construction.

### D7. Introduction protocol

**Objective:** on successful authoring, the user is introduced to the new persona before any message from that persona is delivered.
**Acceptance:**
- New persona file is persisted with `pending_introduction: true` and `is_addressable: false`.
- Primary persona writes a structured introduction (name, domain, trigger, what-they-handle, retire-instructions) and dispatches only to the user's one-on-one channel (terminal / desktop / personal Telegram) — never to group channels.
- `is_addressable` flips True only on the user's next non-retire message; retire instruction moves directory to `_retired/` without ever flipping the flag.
- A test verifies no message carrying the new persona's identity can be delivered before `is_addressable: true`.

### D8. Retirement

**Objective:** retired personas are cleanly removed from the active roster; history is preserved.
**Acceptance:**
- Retirement moves `personas/<handle>/` to `personas/_retired/<handle>-<timestamp>/`.
- Active loader ignores `_retired/*`; memory/scopes referencing the retired persona by ID continue to resolve via history.
- Retirement is itself an auditable event.

### D9. OTel observability emission

**Objective:** every operation in the persona layer emits OTel spans/events per v1.1 R11.
**Acceptance:**
- Loader runs produce spans with outcome (loaded / failed + reason).
- Monitor ticks and injections emit events.
- Authoring pipeline produces a parent span with one child per step; self-review verdicts are events.
- Introduction dispatch emits an event naming the new persona and the channel.
- No downstream consumer is assumed (A1 correction).

### D10. Bundled documentation

**Objective:** v1.1 R4 — human-readable documentation bundled with the component.
**Acceptance:** prose explanation; architecture diagram (three halves + their shared contract artifact); data-flow diagram (session start → load → monitor tick → authoring trigger → introduction → activation); relationship map (subscribes to scope-of-work emitter; reads from memory; emits to OTel; surfaces to channel-agnostic-interaction surface when that lands); one-page API reference for the loader, monitor, and authoring triggers; retirement / override / user-controls reference.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Primary persona — contract formally specified; workspace persona conforms or is rejected | D1 + D2 |
| v1.0 Primary persona — no pOS-shipped persona content; build-time check | D2 |
| v1.0 Primary persona — workspace without persona cannot start session | D2 |
| v1.0 Session resilience — compaction preserves persona identity, work items, pending decisions, recent corrections | D4 |
| v1.0 Observability — every action produces an auditable record | D9 |
| v1.1 R4 — bundled documentation | D10 |
| v1.1 R11 — OTel observability | D9 |
| v1.1 R13 — channel-agnostic interaction (intro protocol is one-on-one channel aware) | D7 |
| STATE.md rule #7 — primary persona never loses track of background work | D3 (structural injection on every turn) |
| **Staged for v1.2 — primary persona MAY author new personas** | D5 + D6 |
| **Staged for v1.2 — user MUST be introduced before any message from new persona** | D7 |
| **Staged for v1.2 — pOS core ships the authoring framework, never the content** | D1 + D5 + D6 (all live in pOS; no personas shipped) |

---

## Dependencies

### Hard dependencies

- **Scope-of-work primitive** (sealed; D0 adds one field — small amendment).
- **Memory system** (sealed; no amendment needed — already has `scope_source` injection; persona loader uses memory for style-harvest and recent-corrections).

### Soft dependencies (future consumers)

- Observability aggregator (subscribes to OTel emissions)
- Safety layer (consumes authority-boundary declarations from personas)
- Reversibility primitive (consumes reversibility declarations from scope-of-work; no direct persona-layer link)
- Cost governance (consumes scope budgets already emitted by scope-of-work)
- Self-correction loop (subscribes to persona-authored-but-rejected events for learning)

### Permitted runtime dependencies

- Python stdlib (pathlib, asyncio, uuid, sqlite3, dataclasses)
- Pydantic (contract schema)
- pyee (already in scope-of-work)
- opentelemetry-api + opentelemetry-sdk (already in scope-of-work)
- No additional third-party runtime libraries without halt-and-signal.

---

## Assumptions (inference recorded — flagged so the builder can challenge)

1. **Claude-via-Max for the authoring pipeline.** Four LLM calls per new persona (style-harvest, domain-research, contract-synthesis, self-review). Cost estimate at Haiku 4.5 rates: ~$0.05–0.10 per authored persona, well within scope budget ceilings.
2. **Monitor awareness-block token cost.** ~1k input tokens per UserPromptSubmit injection. At 20 turns/day and Haiku 4.5 rates, roughly $0.06/day or ~$2/month. Acceptable. If costs exceed expectations, the awareness-block cap and category-row cap are tunable.
3. **Stuck-detection multiplier is 2×.** Research's recommendation; matches current-pOS convention. Configurable per-scope at creation.
4. **Creation-trigger signal thresholds** — concrete numbers come out of the build. Placeholder values in D5 acceptance criteria; actual thresholds are tunable workspace-level.

---

## Open questions for the owner (before handoff brief)

Three decisions would sharpen the handoff brief. the primary persona has a lean on each.

1. **Default `expected_duration_seconds` when scope authors don't declare one.** Options: require every scope to declare (no default, omission rejects scope creation); `None` default (scope opts out of stuck-detection); per-scope-category defaults (e.g. research scope = 30 min, build scope = 60 min). recommendation: **`None` default** — scopes opt in to stuck-detection by declaring the field. This matches the existing scope-of-work posture of optional fields on optional behaviours.

2. **Group-channel introductions for the case when the owner is on a group and the new persona is relevant to that group's topic.** the owner already approved restricting to one-on-one; is there any edge case where a group introduction is desirable? recommendation: **stay strict** — one-on-one only. If the persona is relevant to a group conversation later, the user can invite them explicitly once they exist.

3. **Default retire-window before the user can reject a newly-introduced persona.** Options: indefinite (user can retire whenever); fixed window (e.g. 72 hours from introduction). recommendation: **indefinite** — matches the rebuild's silence-by-choice posture. Workspaces can tune.

These are minor; default to the primary persona's leans unless any reads wrong to you.

---

## What happens on approval

1. I draft the handoff brief. Objectives, constraints, acceptance criteria, dependencies — no prescribed file paths, class names, or step-by-step execution plans. You review the brief to catch overspecification.
2. On your review, a general-purpose agent is dispatched against the brief. D0 lands as the first commit (tiny scope-of-work amendment); D1–D10 land as the persona-layer build.
3. The three staged spec addendum items land as v1.2 revisions alongside the build's completion, with your sign-off.
4. Halt-on-deviation applies throughout.
