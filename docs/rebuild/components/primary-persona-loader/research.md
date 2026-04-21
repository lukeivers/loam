# Research — Primary-Persona Layer (Loader + Monitor + Autonomous Authoring)

**Component:** Primary-persona layer — three tightly coupled halves that share the persona contract: (1) loader + validator, (2) background-work monitor, (3) autonomous-authoring framework.
**Status:** DRAFT for owner's review.
**Authored by:** general-purpose Agent dispatched by the primary persona, per the approved research plan.
**Date:** 2026-04-18.
**Plan executed against:** `docs/rebuild/components/primary-persona-loader/research-plan.md` (revised 2026-04-18 14:40 CDT).

---

## 0. Executive summary

The new pOS primary-persona layer is best implemented as **three Python packages with a single shared contract module**: `pos.persona.contract` (Pydantic schemas, the canonical artefact both halves agree on), `pos.persona.loader` (validates and binds the workspace persona to a session), `pos.persona.monitor` (subscribes to scope-of-work emissions and synthesises a continuously-injected awareness block), and `pos.persona.authoring` (the framework primary personas use to autonomously create new specialists — template + research budget + quality checks + introduction protocol).

The recommended persona shape is a **directory** under workspace control (`workspace/personas/<handle>/`) containing `contract.yaml` (Pydantic-validated, the parts pOS enforces), `prompt.md` (free prose, what the persona actually says), and `voice.md` (calibration examples, optional). The directory shape gives clean separation of contract from content; the YAML+Markdown split makes the contract machine-checkable while the content stays editable as prose.

Compaction survival is handled by an **event-sourced replay** rather than the snapshot-and-restore of current pOS: the monitor's emission stream IS the survival mechanism. Identity is reasserted by re-reading the loaded persona's `prompt.md` (the persona file is the canonical source); active-work awareness is reasserted by replaying the monitor's most recent injection block; pending decisions are read from the scope-of-work runtime's `list(filter)` query. There is no separate snapshot file because there is no separate state to snapshot.

The autonomous-authoring framework treats authoring as a **scope of work**: the primary persona opens an `authoring` scope with a budget (tokens, money, wall time), runs a four-stage pipeline (signal-detection → drafting → quality-check → introduction), and the new persona only becomes addressable after a user-visible introduction message succeeds. A build-time check (a `pytest` collection-time assertion shipped in pOS) fails CI if any persona file appears in `pos/` paths.

Three halt signals are raised below. None are fatal; each names a place where the spec needs clarification recorded before the proposal phase can begin.

---

## 1. Survey of existing patterns

### 1.1 Anthropic Claude Agent SDK — subagents, hooks, sessions

The Agent SDK exposes subagents through an `AgentDefinition` shape with five core fields (`description`, `prompt`, `tools`, `model`, optionally `skills` / `memory` / `mcpServers`); the SDK accepts these either programmatically (Python `AgentDefinition` dataclass passed in `ClaudeAgentOptions.agents=`) or as Markdown-with-YAML-frontmatter files in `.claude/agents/`. Programmatically-defined agents take precedence. Subagents start with a fresh context window — only the parent's tool-call prompt string and project CLAUDE.md cross the boundary; intermediate tool calls and reasoning stay inside the subagent. The parent receives the subagent's final message verbatim and may summarise it.

The Python SDK exposes hook events `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`, `SubagentStart`, `PermissionRequest`. `SessionStart`, `SessionEnd`, `PostCompact`, and `TaskCompleted` exist in the TypeScript SDK; Python lags. `PreCompact` receives `hook_event_name`, `trigger` (`manual` / `auto`), `custom_instructions`, and can block compaction by exiting code 2 or returning `{"decision":"block"}`. `PostCompact` (TS only) receives `trigger` and `compact_summary`, the model-generated conversation summary. The hook callback signature in Python is `Callable[[HookInput, str | None, HookContext], Awaitable[HookJSONOutput]]`.

Detection of subagent invocation is via `tool_use` blocks named `Agent` (formerly `Task`); subagent-context messages carry a `parent_tool_use_id`. Subagent transcripts persist independently of main-conversation compaction and can be resumed by capturing `session_id` + agent ID and passing `resume=session_id` plus the same agent definition on the next `query()`.

**Relevance:** the SDK gives us the runtime mechanics (hooks, session resume, programmatic agent definitions) but not the contract surface — there is no validation of an agent's "responsibilities" beyond the description field. The new pOS layer fills that gap.

### 1.2 Letta / MemGPT — memory blocks as identity

Letta's persona is a **memory block** with three required fields (`label`, `value`, `limit`), two optional fields (`description`, `read_only`), and no formal versioning — last-write-wins on the `value` string. Identity is encoded by convention via the `label` (`persona`, `human`) and the `description` (which the agent reads to decide how to interact with the block). Framework-vs-content separation is loose: `label`, `limit`, `read_only` are framework-enforced; `value` and `description` are content. The agent itself can edit its own persona block via tools.

**Relevance:** the block-as-content / metadata-as-contract split is the right pattern, but the Letta version is too thin for our needs — there is no validation that the persona declares the three functional responsibilities the spec requires, and the unversioned full-replace mutation model is incompatible with the contract-evolution requirement (research question 3).

### 1.3 LangGraph — checkpointer + interrupt for state recovery

LangGraph stores graph state via a **checkpointer** keyed on `thread_id`. `interrupt()` pauses execution, persists state, waits indefinitely. Resume is bit-exact: the graph picks up exactly where it left off with the human input present in the resumed node. Production deployments use durable checkpointers (Postgres, Redis); ephemeral ones use SQLite or in-memory.

**Relevance:** this is the cleanest pattern for compaction survival as state-recovery, but it presumes the agent IS the graph. Our primary persona is the consumer of state (scopes, memory) rather than a stateful entity itself — its survival reduces to "reload the persona file + replay the monitor's last frame." We don't need a checkpointer per se; we need re-loading from authoritative sources.

### 1.4 AutoGen / CrewAI / MetaGPT — persona authoring conventions

CrewAI defines agents in YAML with `role`, `goal`, `backstory` as the persona spec; optionally `tools`, `temperature`, `allow_delegation`. Method names in Python decorate the YAML entries. The role/goal/backstory triplet is widely copied: it's load-bearing because backstory drives tone consistency more than role does.

AutoGen exposes flexible role + capability + system-prompt configuration; AutoGen Studio adds a low-code drag-and-drop builder. Dynamic agent creation in AutoGen happens via `GroupChatManager` orchestrating a pool — the framework doesn't generate net-new agents at runtime by default.

MetaGPT encodes Standard Operating Procedures as inter-agent protocols; agent roles are predetermined by the framework designer and remain fixed. This is the opposite of what wanted from the autonomous-authoring framework.

### 1.5 AutoAgents — automatic agent generation

AutoAgents (ICLR 2024, [arxiv:2309.17288](https://arxiv.org/abs/2309.17288)) is the closest published precedent for what the owner is asking for. It defines a generated agent as **𝒜 = {P, D, T, S}** — Prompt (detailed expert identity, profile + goal + constraints), Description (additional concrete identity), Toolset (selected from predefined tools), Suggestions (output expectations and execution-step guidance). A two-stage pipeline runs:

- **Drafting stage:** three meta-agents (Planner, Agent Observer, Plan Observer) negotiate a custom team. The Planner proposes; the Agent Observer validates structural compliance + task compatibility + role rationality (eliminating duplicates, identifying missing roles); the Plan Observer reviews the execution plan.
- **Execution stage:** the team executes; observers run self-refinement (single-agent improvement) and collaborative refinement (knowledge sharing).

**Relevance:** this is the spec-shape precedent. We adopt {P, D, T, S} as the bones of our persona contract, with pOS-specific extensions (the three functional responsibilities, authority boundary, severity vocabulary). We adopt the Planner+Observer split as the quality-check gate but collapse it from three meta-agents to a deterministic rubric plus one Claude judgment call (cheaper, more explainable).

### 1.6 Persona drift / Anthropic persona vectors

[Anthropic's persona-vector research](https://www.anthropic.com/research/persona-vectors) shows persona drift is measurable as activation-space movement; LLaMA2-chat-70B drops more than 30% on persona-consistency benchmarks after 8–12 turns. Mitigations include split-softmax and finite-state tone protocols (EchoMode: Sync → Resonance → Insight → Calm).

**Relevance:** drift detection is in scope as a future enhancement to the monitor (or as a separate "persona-health" component), but is *not* in scope for this layer's first ship. Pending spec staging item — see §13.

### 1.7 Compaction survival in the wild

The published patterns are:
1. **Snapshot + restore** (current pOS, OpenClaw, Termo): write a checkpoint at PreCompact, re-inject at next prompt.
2. **WAL + working buffer** (Microsoft Agent Framework, Google ADK): persist every step as a log entry, replay relevant entries after compaction.
3. **Indexed event store** (`context-mode`): every event is FTS5-indexed; on compaction, retrieve only what's relevant via BM25 search.

The new pOS already has the building blocks for option 2 (scope-of-work emits a full event stream; OTel spans cover persona actions; memory system stores conversational episodes). Option 1 is what current pOS does and is being deliberately superseded. Option 3 is overkill for our scale.

---

## 2. Recommended design shape — for each of the twelve question groups

Each subsection: options considered → recommendation → rationale.

### 2.1 Persona contract — what must a workspace persona declare?

**Options considered.**
- (a) A single Markdown file with conventional sections (current pOS approach).
- (b) A Python class with required methods, registered via entry-points.
- (c) A YAML manifest (the contract part) plus separate Markdown files (the content part) inside a per-persona directory.
- (d) A Pydantic model the workspace instantiates and pOS introspects.

**Recommendation: (c) directory layout, contract in YAML, content in Markdown.**

The persona lives at `workspace/personas/<handle>/` with the layout:

```
workspace/personas/eve/
├── contract.yaml      # pOS-validated; Pydantic schema; the contract
├── prompt.md          # the persona's voice, prose; the content
├── voice.md           # optional — calibration examples, tone markers
└── home/              # optional — reference materials persona reads on load
```

`contract.yaml` is parsed by `pos.persona.contract.PersonaContract` (a Pydantic model). `prompt.md` is loaded as a string, hashed, and the hash is recorded in the loaded-persona object so compaction-survival can verify the file hasn't changed.

**Rationale.** This separates contract from content the way [Letta does](https://docs.letta.com/guides/agents/memory-blocks/) but with the strictness of [Pydantic AI](https://ai.pydantic.dev/) on the contract side. Workspaces own the prose; pOS owns the schema. Keeping prose in `.md` (not packed into YAML strings) means it survives editor newlines and stays diffable.

**Mandatory contract fields** (the spec-criterion set, see §3 mapping):
- `handle` (string, slug-safe — the addressable identifier).
- `given_name` (string — natural-language name used in the workspace).
- `responsibilities` (object with three required keys: `single_point_of_contact`, `context_holder`, `escalation_judge`; each is a one-sentence declaration of how this persona discharges that responsibility).
- `authority_boundary` (object; per-tier declaration of what this persona may execute autonomously vs requires user approval — keys `tier_a`, `tier_b`, `tier_c`, `tier_d` mapping to `execute` / `defer` / `not_applicable`).
- `escalation_taxonomy` (list of enum strings — what classes of decision are escalated, drawn from the framework-supplied taxonomy `founder_authority` / `irreversible_high_stakes` / `cross_persona_conflict` / `external_communication` / `policy_clarification`).
- `severity_vocabulary` (list of label strings — domain-calibrated severities the persona uses; pOS does not validate semantics, only that a vocabulary is declared).
- `contract_version` (semver string — pinned to a pOS contract release).

**Optional contract fields:** `delegates_to` (list of handles for declared specialists), `voice_markers` (free-form list of phrases the persona uses), `home_persona_for` (workspace handle this persona is the primary persona for — empty for specialists).

**Content fields** (Markdown, not validated):
- `prompt.md` — the system prompt body, freely authored.
- `voice.md` — optional calibration snippets.

### 2.2 Content vs contract split

**Recommendation.** pOS validates only `contract.yaml`. The Markdown files are read-only-from-pOS's-perspective: pOS records the SHA-256 of `prompt.md` at load time and refuses to rebind a persona mid-session if the hash changes (use the file watcher + an explicit `reload-persona` command). This is the framework-vs-content separation the [no-personas-in-pOS-core decision](docs/rebuild/spec/pos-v2-objectives-spec.md) requires.

### 2.3 Contract versioning

**Recommendation.** Semver in `contract_version` field. pOS ships a `pos.persona.contract` module exposing `CURRENT_VERSION` and a `migrate(contract_dict, from_version)` function that applies a chain of migrators (small Python functions, one per minor version). On load:

1. Read `contract_version` from YAML.
2. If it equals `CURRENT_VERSION`, validate against current Pydantic schema.
3. If it's older minor, run migrators in sequence, then validate.
4. If it's older major, fail the load with a named error and a pointer to the migration guide (workspaces must opt in to major migrations).
5. If it's newer than `CURRENT_VERSION`, fail with "this persona requires a newer pOS."

Migrators are deterministic; the loader logs every migration applied. This keeps the workspace persona file unchanged on disk; pOS migrates in memory at load time.

### 2.4 Failure modes on non-conforming personas

**Recommendation.** Three failure classes, each with a named exception:

- `PersonaContractError` — schema validation failed (missing required field, wrong type, unknown enum value). Message includes the failing field path and what would satisfy it.
- `PersonaVersionError` — major-version mismatch beyond the migrator chain.
- `PersonaContentError` — content file missing (no `prompt.md`).

Each error fails the session load deterministically — there is no fallback persona, no degraded mode. A workspace with an invalid persona cannot start a session. This honours the v1.0 acceptance criterion *"a workspace with no primary persona cannot start a session; failure mode is clear and immediate."*

### 2.5 Loader lifecycle

**Recommendation.** Loader runs in three places:

1. **Session start** (every interactive session). Reads `workspace/personas/<handle>/`, validates contract, loads content, returns a `LoadedPersona` Pydantic dataclass to the session.
2. **Explicit reload** via a programmatic API (`runtime.reload_persona()`) — used after the persona is autonomously edited (authoring framework) or manually changed.
3. **Post-compaction restoration** — see §2.7 below; this is the loader being called as part of compaction-survival, not a third lifecycle event.

**The loader does NOT run on every compaction event automatically.** Compaction does not change the persona file on disk; what compaction loses is the in-context awareness, not the persona binding. The compaction-survival mechanism re-asserts identity from the already-loaded persona object, not by reloading from disk. This is a deliberate departure from current pOS, where the PreCompact hook wrote a snapshot file from disk every compaction event.

### 2.6 Loader state

**Recommendation: stateless on disk, cached in memory per session.** The loader holds no persistent state — every read is from disk. Per-session, the `LoadedPersona` is held in a session-scoped object (an `asyncio` task-local or an explicit injection into the agent loop). Cache invalidation is the explicit reload API; there is no background file watcher in v1 (deferred to v1.x).

### 2.7 Loader-to-session interaction

**Recommendation.** The loader returns a `LoadedPersona` immutable Pydantic model. The session takes this and binds it into the LLM call construction (system prompt assembly, persona-name in messages, authority-boundary checks). The session does not query the loader during turns; the binding is established once at session start. The monitor (separate concern) updates per-turn.

### 2.8 Monitor — what does the persona need from background work?

**Recommendation: a single, structured "awareness block" injected before every user message.**

Per [STATE.md rule #7](docs/rebuild/STATE.md), the persona must never lose track of background work. The structural way to deliver this is to inject a deterministic block into the LLM context every turn — analogous to how current pOS's `monitor-check.rb` injects unclaimed-task manifests, but reading from scope-of-work's `list(filter)` instead of file manifests.

The awareness block has six sections (each shown only if non-empty):

```
[BACKGROUND WORK — as of 2026-04-18 14:42:11 UTC]
Active (3): scope-abc / "research persona-loading patterns" — owner: eve, runtime 4m
            scope-def / "draft cal voice update"             — owner: cal,  runtime 12m
            scope-ghi / "weekly memory synthesis"             — owner: eve, runtime 47s
Pending decision (1): scope-jkl — extension request: tokens (50% over cap)
                     respond with runtime.extend(scope-jkl, tokens, N) or runtime.reject(scope-jkl)
Stuck (1): scope-mno / "review betting backtest"             — last transition 23m ago, expected ≤8m
Recently finished (2): scope-pqr (success) — "draft handoff brief"
                       scope-stu (failed)  — "validate cron syntax" — reason: bash exit 2
Escalated (0):
Failed (0):
[/BACKGROUND WORK]
```

Token cost is bounded: each scope row is ~30 tokens; with caps of 5/section the whole block is under 1,000 tokens. The block is suppressed entirely when all sections are empty (the common case) — STATE.md rule #7 is satisfied by *capability* even when the block has nothing to say.

### 2.9 Monitor cadence

**Recommendation: hybrid — event-driven update of a cached frame, pull-on-prompt for injection.**

The monitor runs as a long-lived `asyncio` coroutine subscribed to scope-of-work's pyee emitter (`subscribe_all`). Every event triggers an in-memory recomputation of the awareness block (cheap — it's a query against the projection). When the user submits a prompt, the prompt-construction path reads the cached block and injects it.

The monitor *also* runs a periodic stuck-detector (see §2.10) on a 30-second `asyncio.sleep` loop — independent of events because stuckness is the absence of events.

This is event-driven for state changes, polled for time-elapsed conditions. Both feed the same cached frame. No LLM inference at this stage.

### 2.10 What is "stuck"?

**Recommendation: deterministic threshold + optional LLM second-pass.**

Layer 1 (deterministic, always on): a scope is stuck if it has been in `active` state for > 2× its declared expected duration without a single OTel span event. The scope spec carries `expected_duration_seconds` (added as an optional field on `ScopeSpec` — *halt signal #1*, see §4); if absent, the threshold is a per-stack default (proposed: 600s).

Layer 2 (LLM second-pass, opt-in): when a Layer-1 stuck-flag fires, the monitor queues a Claude (Max) call summarising the scope's recent OTel spans and asking "is this scope actually stuck or making slow progress?" The summary becomes the `stuck_reason` field shown in the awareness block. Cost-bounded: at most one such call per scope per hour.

The Layer 2 call is the *only* LLM inference inside the monitor. It is gated, rate-limited, and uses Claude via Max per the constraints.

**Halt signal #1.** The scope-of-work primitive does not currently carry `expected_duration_seconds` on `ScopeSpec`. Adding it is a one-field migration to scope-of-work (already-shipped component) — small, but a change. Surfaced for decision recorded: (a) add the field to scope-of-work, (b) carry the threshold in the monitor's config and skip per-scope tuning, (c) infer expected duration from owner-persona historical averages stored in memory. Recommend (a) — it's the cleanest contract shape.

### 2.11 Monitor presentation discipline

Already covered in §2.8 — structured awareness block, capped at five rows per section, suppressed when empty. No raw OTel spans, no JSONL surfacing, no log files in the persona's view. The monitor is one-way (monitor feeds, persona reads); the persona can ask follow-up questions which are answered by tool calls into the scope-of-work query API (see §2.12).

### 2.12 Monitor-to-persona conversation path

**Recommendation: tool-call API, not bidirectional channel.**

The monitor injects the awareness block. If the persona wants to drill into a specific scope, it uses an exposed tool call:

- `pos.scope.get(scope_id)` — full projection.
- `pos.scope.events(scope_id, since=...)` — recent events.
- `pos.scope.list(filter)` — the scope-of-work query surface, exposed to the persona.

This keeps the monitor stateless from the persona's perspective (it injects; it doesn't dialogue) and satisfies the deterministic-first principle (the persona's drill-down uses script-tier queries, not LLM judgments).

### 2.13 Compaction survival mechanism

**Recommendation: replay-from-authoritative-sources, not snapshot-and-restore.**

Compaction wipes mid-conversation context. The pOS-authoritative state lives in:
1. The persona file on disk (`prompt.md`, `contract.yaml`).
2. The scope-of-work event store (active work, pending decisions).
3. The memory system (recent corrections, decisions, conversational episodes within the current scope).

The compaction-survival mechanism uses a `PostCompact` hook (TS only today; we register a Python equivalent via the SDK's `PreCompact` blocking trick + a UserPromptSubmit fallback for parity until `PostCompact` lands in Python). The hook does three things:

1. **Re-inject persona identity** — read `LoadedPersona.prompt_text`, prepend to next system message as a `[PERSONA RESTORATION]` block. Includes the persona handle, given name, three responsibilities, authority boundary, and severity vocabulary. ~500 tokens.
2. **Re-inject the awareness block** — same as the monitor's normal injection but flagged `[POST-COMPACTION RESTORATION]` so the persona knows the prior turn was lost. ~500 tokens at cap.
3. **Re-inject the survival list** — the canonical items below. ~300 tokens.

No snapshot file is written. The PreCompact hook does NOT save state; PostCompact rebuilds from authoritative sources. Cleaner audit trail, no stale-snapshot drift, no hooks that can fail silently and lose data.

**Halt signal #2.** Python SDK lacks `PostCompact` today (TS-only). Three workable interim approaches: (a) wait for Python parity (timing unknown; could block the rebuild); (b) detect the post-compaction state in `UserPromptSubmit` by comparing current message count to the stored prior count + a "we just compacted" flag set by `PreCompact`; (c) write a thin TypeScript shim that handles the hook and shells out to Python for restoration. Recommend (b) for v1 — it works today, lives entirely in Python, and the only downside is the restoration block lands one turn later than ideal. Surfaced for decision recorded because it affects whether we wait or design around.

### 2.14 Survival list

The canonical items every primary persona must recover after compaction:

1. Persona handle, given name, three responsibilities, authority boundary, severity vocabulary, escalation taxonomy. (Re-read from `contract.yaml` + `prompt.md`.)
2. Active scopes the persona owns or is subscribed to. (Query `runtime.list(owner_persona=handle)`.)
3. Pending decisions awaiting persona judgment. (Query `runtime.list(include_pending_extension=True)`; plus pending escalations from any scope with state `escalated`.)
4. Recent corrections from the user, with the specific behaviour each correction targeted. (Query memory for episodes tagged `correction` with `valid_at` in the last 24 hours; surface as a list with the *dial adjusted*, per [`session-management.md` rule 6](prior-pOS rules at prior-pOS .claude/rules/session-management.md).)
5. The user's currently-active task, as best inferable from the most recent user-input scope. (Query `runtime.list(states=[active], owner_persona=user)`.)

This list is the framework's; workspaces can extend it via a `persona_survival_extras` callable in `contract.yaml`. Per the spec criterion *"compaction events preserve persona identity, active work items, and pending decisions (verified against the compaction-survival list — the list itself is a maintained artifact, not an implicit property)."*

### 2.15 Monitor-as-survival-mechanism

The monitor IS the survival mechanism for items 2, 3, 5. Item 1 is a separate concern (loader's responsibility to re-inject identity from disk). Item 4 is a memory query. There is no separate "survival" subsystem — the components that already exist deliver this between them.

### 2.16 Escalation-judgment mechanism

**Recommendation: hybrid — deterministic policy table + LLM judgment for edge cases.**

The persona's `authority_boundary` (Pydantic-validated, contract-required) declares per-tier behaviour. The escalation-judgment runtime works like this:

```
def should_escalate(action, persona_contract) -> EscalationDecision:
    tier = classify_action(action)              # deterministic — function of action shape
    policy = persona_contract.authority_boundary.get(tier)
    if policy == "execute":   return EscalationDecision.execute_then_inform
    if policy == "defer":     return EscalationDecision.escalate_to_user
    if policy == "not_applicable": return EscalationDecision.policy_error
```

This is determinism-tier Layer 1 (hook-level enforceability per [v1.0 spec](docs/rebuild/spec/pos-v2-objectives-spec.md)). For genuinely ambiguous classifications — actions that don't cleanly map to a tier — the runtime falls back to a Layer-3 LLM judgment using the persona's own voice (Claude via Max), with the result audit-logged.

### 2.17 Escalation communication channel

**Recommendation: emit an OTel-annotated `escalation` event on the active scope; rely on a downstream channel-router to route to the user.**

The persona doesn't own the user-message channel. Per [v1.1 R13](docs/rebuild/spec/pos-v2-objectives-spec.md) (channel-agnostic interaction), the channel layer is a separate component that subscribes to escalation events. The persona layer's job is to emit; the channel router's job is to deliver.

This honours A1 (no assumed downstream consumer) — escalations are emitted via the scope-of-work event stream; if no channel router exists, they accumulate as unread escalations visible in the awareness block on the next interactive turn. The system degrades gracefully: missing the channel router doesn't break the persona; it just makes escalations land in the next session instead of in real time.

### 2.18 Persona ↔ scope creation API

**Recommendation: explicit `pos.persona.dispatch(spec)` helper; persona never calls `runtime.create()` directly.**

The persona expresses intent ("I want to do X with these constraints"); the dispatch helper:

1. Validates the spec satisfies the `ScopeSpec` requirements.
2. Sets `owner_persona` from the loaded persona's handle.
3. Adds the persona's default observers (the persona itself, the monitor).
4. Calls `runtime.create(spec)` and `runtime.start(scope_id)`.
5. Returns the scope projection.

This indirection lets the dispatch helper inject the persona-uniform defaults (observers, telemetry, retry policy) without each persona needing to know them. The scope-of-work primitive remains untouched.

### 2.19 Persona ↔ memory interaction

**Recommendation: tool-call retrieval, not pipeline injection.**

Memory retrieval is a tool the persona calls when needed (`memory.search(query, scope_ids=[current_scope], anchor_node_uuid=...)`), not a pre-turn injection. Reasoning:

- Pre-turn injection bloats every prompt with potentially irrelevant memory.
- The persona's expertise is judging *when* a memory query is needed; pre-injecting denies that judgment.
- Cost discipline: pre-turn injection is paid every turn whether used or not; tool-call is paid only when invoked.

Exception: the loader injects a *pointer* to memory ("you have access to the memory system; recent corrections are visible at the top of every session in the survival block") into the system prompt. Actual content is fetched on demand.

### 2.20 Failure isolation between monitor and persona

**Recommendation: monitor crash degrades the session to "monitor unavailable" state, persona continues.**

If the monitor coroutine crashes, the awareness-block injection becomes a fixed string: `[BACKGROUND WORK — monitor unavailable; check scope-of-work runtime directly via tool calls]`. The persona keeps running. The crash is logged via OTel and surfaces as a Tier 1 notification. The persona retains drill-down ability via the scope-of-work query tools.

This honours rule 13 of [prime-rules.md](prior-pOS rules at prior-pOS .claude/rules/prime-rules.md) — autonomous-action transparency — and the [graceful degradation](docs/rebuild/spec/pos-v2-objectives-spec.md) objective.

### 2.21 Emission surface

**Recommendation: OTel spans + structured JSONL events, no assumed consumer.**

The loader emits a span on every `load`, `validate`, `migrate`, `reload` operation. Attributes: `persona.handle`, `persona.contract_version`, `persona.content_hash`, `persona.load_outcome`. Failure spans carry the named exception class.

The monitor emits a span per awareness-block construction (cheap, useful for debugging cost). Attributes: `monitor.section_counts`, `monitor.token_estimate`, `monitor.injection_emitted`.

Authoring emits spans per stage (signal-detection, drafting, quality-check, introduction). Attributes: `authoring.persona_handle`, `authoring.trigger_signal`, `authoring.stage_outcome`, `authoring.budget_consumed`.

JSONL event log mirrors the OTel for components that don't speak OTel. Per A1, no aggregator is assumed.

### 2.22 Persona template — canonical shape

Already specified in §2.1. Recap:

```
workspace/personas/<handle>/
├── contract.yaml      # mandatory; Pydantic-validated
├── prompt.md          # mandatory; free prose
├── voice.md           # optional; calibration examples
└── home/              # optional; reference materials
```

`contract.yaml` schema (Pydantic, in `pos.persona.contract`):

```yaml
handle: eve                              # required, slug
given_name: the primary persona                          # required, str
contract_version: "1.0.0"                # required, semver pinned to pOS contract
responsibilities:                        # required, all three keys
  single_point_of_contact: "..."         # one-sentence declaration
  context_holder: "..."
  escalation_judge: "..."
authority_boundary:                      # required, all four keys
  tier_a: defer                          # enum: execute|defer|not_applicable
  tier_b: defer
  tier_c: execute
  tier_d: execute
escalation_taxonomy:                     # required, list of enum strings
  - founder_authority
  - irreversible_high_stakes
severity_vocabulary:                     # required, list[str]; pOS doesn't validate semantics
  - blocking
  - serious
  - watch
delegates_to:                            # optional, list[handle]
  - mara
  - cal
home_persona_for: the existing workspace             # optional; this persona is the primary for the workspace
voice_markers:                           # optional, list[str]
  - "lead with the answer"
```

### 2.23 Mandatory vs optional template sections

Mandatory in `contract.yaml`: handle, given_name, contract_version, responsibilities (with all three keys), authority_boundary (with all four tier keys), escalation_taxonomy (non-empty), severity_vocabulary (non-empty).

Mandatory file: `prompt.md` (any non-empty content).

Optional in `contract.yaml`: delegates_to, home_persona_for, voice_markers.

Optional file: `voice.md`, `home/`.

### 2.24 Contract-vs-content expression

`contract.yaml` is structured (Pydantic). `prompt.md` is unstructured prose. The contract validates *that* the prose exists; it does not validate *what* the prose says. This is the design discipline that prevents pOS from leaking workspace content into core.

### 2.25 Template versioning

Already covered in §2.3 — semver in `contract_version` field, in-memory migration chain, fail-closed on major version mismatch.

### 2.26 When is a new persona warranted? (Authoring triggers)

**Recommendation: deterministic signal scoring + LLM judgment over the score.**

Five signals, each with a deterministic counter:

| Signal | Counter |
|---|---|
| Repeated requests in a domain the primary persona declines or struggles with | per-domain count of declines or low-confidence responses, 7-day window |
| User frustration with primary's handling of a specific concern | per-domain count of corrections tagged `domain-handling`, 14-day window |
| Cross-domain work surfacing repeatedly | per-pair count of scopes spanning two domains, 14-day window |
| Domain expertise outside primary's authored scope | per-domain count of memory retrievals returning low-relevance hits, 7-day window |
| User explicit suggestion (e.g. "you should have someone for X") | per-mention count of "[noun] persona" or "specialist for [noun]" patterns in user messages |

When any single signal crosses a threshold (defaults: 5 occurrences for the first three; 3 for low-relevance retrievals; 1 for explicit user suggestion), the primary persona is *prompted* (via injection, not forced) to consider authoring. The decision to actually author is the primary persona's LLM-judgment call — not deterministic, because the judgment "would a specialist meaningfully improve output here?" is genuinely qualitative.

Audit: every authoring decision writes an episode to memory tagged `authoring-decision` with the triggering signal, the persona's reasoning, and the proposed handle.

### 2.27 Decision rubric

Hybrid (above) — deterministic threshold detection, LLM judgment on the decision. This is determinism-tier Layer 2 (rubric produces score; LLM acts on it). The deterministic side keeps signals visible and tunable; the LLM side keeps the *yes/no* in the persona's hands.

### 2.28 Auditability of authoring decisions

Every authoring event produces three artefacts:

1. A memory episode (tagged `authoring-decision`) with the triggering signal, the persona's reasoning, and a diff of the workspace persona roster before/after.
2. An OTel span (`authoring.decision`) with structured attributes: `signal_type`, `signal_count`, `persona_proposed_handle`, `persona_proposed_domain`, `decision_outcome`.
3. A user-visible introduction message (see §2.35).

This honours the [anti-deskilling](prior-pOS rules at prior-pOS .claude/rules/anti-deskilling.md) principle — the user can always answer "why did I get a new persona?" by checking the audit trail.

### 2.29 Authoring research paradigm

**Recommendation: a four-step deterministic pipeline that the persona executes, with LLM inference at three of the four steps.**

The pipeline runs inside an `authoring` scope-of-work with an explicit budget (default: 10k tokens, $0.50, 5 minutes wall — overrideable per workspace).

1. **Style harvest** (no LLM). Read all existing workspace persona contracts; extract the workspace's house-style markers — tone register, average prompt length, severity-vocabulary patterns, voice-marker patterns, preferred output structures. Output: a `house_style.json` working artefact.
2. **Domain research** (LLM). Claude (Max) is asked: "draft a {domain} expert profile in the style described by house_style.json, fitting this trigger signal {signal}, addressing this gap {gap}." Output: a draft `prompt.md`. The prompt template is in `pos.persona.authoring.templates.draft_prompt`.
3. **Contract synthesis** (LLM). A second Claude call: "given this prompt, what `contract.yaml` fields satisfy the pOS persona contract?" Output: a draft `contract.yaml`. The synthesis call is constrained: the model is given the Pydantic schema and must return YAML that validates.
4. **Self-review** (LLM). A third Claude call: "you are a critical reviewer. Score this persona on the following rubric: voice-distinctiveness (does it sound like *this* workspace, not generic AI?), scope-fit (does it actually fit the trigger?), redundancy (does it overlap meaningfully with existing personas?), contract-correctness (does it satisfy schema validation?). Output: pass/fail per dimension, with specific quotes."

If any dimension fails, the persona iterates (max 2 iterations per the budget). If still failing, the authoring scope is marked `failed` and the user is informed. The user can then choose to author manually or override the threshold.

### 2.30 House-style constraint mechanism

Step 1 above. The style harvest is deterministic: count word lengths, harvest punctuation patterns (does the workspace use em-dashes? oxford commas? bullet markers?), pull severity-vocabulary terms, list voice-marker phrases. The harvested file is shown to the LLM in step 2 as both prose and structured signals.

### 2.31 Authoring research budget

Already specified — wraps the entire pipeline in a scope-of-work. Defaults: 10k tokens, $0.50, 5min wall. Workspace can override via `config/stack.yml` `authoring.budget_*` keys. Budget exhaustion follows scope-of-work's `request_extension` policy by default; the primary persona must explicitly approve extensions (this is a Tier C action since it commits autonomously-budgeted resources, but capped).

### 2.32 Quality checks

Already covered in §2.29 step 4. The four dimensions: voice-distinctiveness, scope-fit, redundancy, contract-correctness.

The contract-correctness check is deterministic (run the loader against the candidate; pass = loads cleanly).

The other three are LLM-judged. The judgment uses Claude (Max), with the rubric framed as a critical reviewer (the technique from [AutoAgents](https://arxiv.org/abs/2309.17288)'s Agent Observer).

### 2.33 Quality-check iteration limit

Two iterations max per the authoring scope's budget. After two failures, the scope is marked `failed` and the user is informed via the standard escalation path. No silent retries.

### 2.34 Quality threshold ownership

**Recommendation: fixed rubric in pOS core; per-workspace severity tuning.**

The four dimensions are fixed (pOS-defined). The pass thresholds for each dimension are per-workspace configurable via `config/stack.yml` `authoring.quality_thresholds.*`. Defaults (proposed):

- voice-distinctiveness: passes if the LLM judgment of distinctiveness is "fits workspace" or higher.
- scope-fit: passes if the trigger signal is named in the persona's prompt.
- redundancy: passes if no existing persona overlaps by > 50% (LLM-judged with quotes).
- contract-correctness: passes if `pos.persona.loader.validate(candidate)` returns clean.

### 2.35 Introduction protocol — concrete mechanism

**Recommendation: introduction is a user-visible message authored by the primary persona, dispatched through the workspace's primary channel before the new persona is registered as addressable.**

Sequence:

1. Authoring scope completes successfully (passes quality checks).
2. Primary persona authors an introduction message containing: new persona's handle, given_name, declared domain (from prompt.md), the trigger signal that motivated authoring, what kinds of work will route to them, and an explicit "say `no, retire that persona` to remove them" override.
3. The introduction message is dispatched through the channel layer (terminal, Telegram, etc. — channel-agnostic per [v1.1 R13](docs/rebuild/spec/pos-v2-objectives-spec.md)).
4. The new persona file is written to disk but `contract.yaml` carries `pending_introduction: true`.
5. On the next user message, if the user has not retired the persona, the loader removes the `pending_introduction` flag and registers the persona as addressable.
6. If the user retires the persona, the file is moved to `workspace/personas/_retired/<handle>-<timestamp>/` (audit-preserved, not deleted).

The new persona may not author messages, dispatch work, or act in any user-visible way until step 5 completes. This is enforced by the loader: `LoadedPersona` for a pending-introduction persona is constructable but `is_addressable` returns False, and the dispatch API refuses to route work to non-addressable personas.

### 2.36 Introduction timing

**Recommendation: immediately on successful authoring, before any work is routed.**

Deferring introduction creates the failure mode the owner explicitly forbids (the user sees a name they don't recognise). Immediate introduction means at most one extra message between the trigger and the new persona's first action.

### 2.37 User override

Already covered in §2.35 step 6. Override is detected by simple pattern match (`/^(no|retire|remove|don't add)\s+(that\s+)?(persona|specialist)/i` plus mentions of the proposed handle). On override, the file is moved to `_retired/`, the audit episode in memory records the override, and the threshold counters that triggered authoring are reset (so a single rejected proposal doesn't immediately re-trigger).

### 2.38 Channel awareness for introduction

Per [v1.1 R13](docs/rebuild/spec/pos-v2-objectives-spec.md), introduction goes to the channel the user is currently active on (terminal session, Telegram thread, etc.). The primary persona is reachable through whichever channel the user is using; the introduction follows the same rule. If no user is active, the introduction queues and lands at the start of the next interactive session.

---

## 3. Acceptance-criterion coverage

Mapping each spec criterion to the design element that delivers it.

| Spec criterion | Source | Delivered by |
|---|---|---|
| Contract is formally specified; workspace persona either conforms or is rejected at load time | v1.0 primary-persona primitive | §2.1, §2.4 — Pydantic schema + named exceptions |
| No pOS-shipped persona content; build-time check fails on persona files in pOS paths | v1.0 primary-persona primitive | §6 — pytest collection-time assertion shipped in pOS |
| Workspace with no persona cannot start a session; failure mode clear and immediate | v1.0 primary-persona primitive | §2.4 — `PersonaContractError`, no fallback |
| Primary persona present in every interactive session — asserted by session-start test | v1.0 user-facing addendum | §2.5 — loader runs at session start |
| Compaction events preserve persona identity, active work items, pending decisions | v1.0 session-resilience addendum | §2.13, §2.14 — replay-from-authoritative-sources, canonical survival list |
| The compaction-survival list is a maintained artifact, not implicit | v1.0 session-resilience addendum | §2.14 — five-item canonical list, framework-defined, workspace-extensible |
| Background-work awareness: persona never loses track of in-flight work | STATE.md rule #7 | §2.8, §2.9, §2.13 — awareness block, hybrid cadence, post-compaction re-injection |
| Channel-agnostic interaction (R13) | v1.1 R13 | §2.17, §2.38 — escalation events emitted; channel layer subscribes; introduction goes to active channel |
| Anti-deskilling: auto-create paired with auto-explain; silent auto-creation is a lint failure | v1.0 user-facing addendum | §2.28, §2.35 — every authoring event produces an audit trail and a user introduction |
| Primary persona MAY autonomously create new personas without user pre-approval | the owner 2026-04-18 14:37 | §2.26–§2.34 — five-signal detection, four-step pipeline, quality gate |
| User MUST be introduced to every new persona before any message from that persona | the owner 2026-04-18 14:37 | §2.35–§2.36 — pending-introduction flag, non-addressable until step 5 |
| pOS core ships authoring framework, never content | the owner 2026-04-18 14:37 | §6 — build-time assertion; framework lives in `pos.persona.authoring`, content in workspace |
| Verification discipline (cognitive model) | prime.md | §2.20 — monitor failure ≠ persona failure; persona retains drill-down via tool calls |

**No criteria flagged unsatisfiable.** The two halt signals raised in §4 are scope expansions / clarifications, not blockers.

---

## 4. Halt signals raised

Per the plan's halt-on-deviation rule:

**Halt signal #1 — `ScopeSpec.expected_duration_seconds` field.** Stuck-detection (§2.10) needs a per-scope expected-duration. scope-of-work shipped without this. Three options enumerated in §2.10. Recommendation: add the field. Decision required from the owner before scope-of-work is touched.

**Halt signal #2 — Python SDK lacks `PostCompact`.** Compaction-survival (§2.13) wants a `PostCompact` hook to trigger restoration cleanly. Python SDK doesn't have it; TypeScript does. Three workable workarounds enumerated in §2.13. Recommendation: option (b), detect post-compaction in `UserPromptSubmit` via stored counter + flag set by `PreCompact`. Works in pure Python today. Decision required from the owner whether (b) is acceptable as the v1 approach.

**Halt signal #3 — close-associates allowlist for new-persona introductions on external channels.** §2.38 has the new-persona introduction go to whatever channel the user is on. If the channel is Telegram and the user is in a group chat, that is technically a "system speaking to other people." Per [security.md rule 11](prior-pOS rules at prior-pOS .claude/rules/security.md), group chats restrict to delivery notifications. An introduction is arguably narrative. Recommendation: introductions are restricted to one-on-one channels (terminal, DM, owner's personal Telegram thread); group-channel introductions queue until a one-on-one channel is next active. Decision required from the owner whether to confirm this restriction.

---

## 5. Persona contract sketch — concrete

Module: `pos.persona.contract`. Pydantic v2.

```python
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, field_validator

CURRENT_VERSION = "1.0.0"

class TierPolicy(str, Enum):
    execute = "execute"
    defer = "defer"
    not_applicable = "not_applicable"

class EscalationCategory(str, Enum):
    founder_authority = "founder_authority"
    irreversible_high_stakes = "irreversible_high_stakes"
    cross_persona_conflict = "cross_persona_conflict"
    external_communication = "external_communication"
    policy_clarification = "policy_clarification"

class Responsibilities(BaseModel):
    single_point_of_contact: str = Field(..., min_length=1)
    context_holder: str = Field(..., min_length=1)
    escalation_judge: str = Field(..., min_length=1)

class AuthorityBoundary(BaseModel):
    tier_a: TierPolicy
    tier_b: TierPolicy
    tier_c: TierPolicy
    tier_d: TierPolicy

class PersonaContract(BaseModel):
    handle: str = Field(..., pattern=r"^[a-z][a-z0-9-]*$")
    given_name: str = Field(..., min_length=1)
    contract_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    responsibilities: Responsibilities
    authority_boundary: AuthorityBoundary
    escalation_taxonomy: list[EscalationCategory] = Field(..., min_length=1)
    severity_vocabulary: list[str] = Field(..., min_length=1)
    delegates_to: list[str] = Field(default_factory=list)
    home_persona_for: str | None = None
    voice_markers: list[str] = Field(default_factory=list)
    pending_introduction: bool = False  # set by authoring; cleared by loader on first interaction

class LoadedPersona(BaseModel):
    contract: PersonaContract
    prompt_text: str
    voice_text: str | None
    prompt_hash: str  # sha256 of prompt.md
    workspace_root: str
    is_addressable: bool  # False while pending_introduction is True
```

`pos.persona.loader` exposes:

```python
def load(workspace_root: str, handle: str) -> LoadedPersona: ...
def validate(yaml_dict: dict) -> PersonaContract: ...           # raises PersonaContractError
def reload(workspace_root: str, handle: str) -> LoadedPersona: ...
def list_personas(workspace_root: str) -> list[str]: ...       # returns handles
def home_persona(workspace_root: str) -> LoadedPersona: ...     # returns the one with home_persona_for set
```

---

## 6. Build-time check (pOS-core ships zero personas)

Implementation: `tests/test_no_persona_in_core.py` ships in pOS. Test:

```python
import pathlib
def test_no_persona_files_in_core():
    pos_root = pathlib.Path(__file__).parent.parent / "pos"
    forbidden_paths = list(pos_root.glob("**/personas/**"))
    forbidden_paths += list(pos_root.glob("**/contract.yaml"))
    forbidden_paths += [p for p in pos_root.glob("**/prompt.md")
                        if "templates" not in str(p)]  # template files allowed
    assert not forbidden_paths, f"pOS core must not contain persona files: {forbidden_paths}"
```

CI must run this on every commit. Failure blocks merge. The carve-out is `templates/` paths — pOS ships persona templates (the authoring framework needs starter templates) but never personas themselves.

---

## 7. Monitor information architecture

Already covered in §2.8–§2.12. Concise recap of the architecture:

**Inputs.**
- pyee subscription to `runtime.subscribe_all()` — every scope event.
- Periodic 30-second sleep loop — for stuck detection (absence of events).
- Optional Claude (Max) call — for stuck-reason inference (Layer 2, gated).

**Internal state.**
- Cached awareness block (regenerated on every event).
- Per-scope last-event timestamp (for stuck detection).
- Per-scope last-stuck-inference timestamp (rate-limit gate).

**Outputs.**
- Awareness block injected into UserPromptSubmit prompt construction.
- OTel spans on every block construction and stuck inference.
- JSONL events to `data/observability/persona-monitor.jsonl`.

**Failure mode.**
- Coroutine crash → fixed string injection ("monitor unavailable; check via tool calls").
- Persona retains drill-down via `pos.scope.get/list/events` tool calls.

---

## 8. Compaction-survival mechanism

Already covered in §2.13–§2.15. Concise recap:

**Trigger.** `PreCompact` hook fires; sets a flag in the loader's session-scoped state and records the pre-compaction message count.

**Detection.** First `UserPromptSubmit` after the flag is set sees the flag and triggers restoration.

**Restoration.** Three blocks injected (one OTel span per block):
1. Persona identity (re-read from disk via `loader.reload`).
2. Awareness block (re-built from current scope-of-work state).
3. Survival list (built from the canonical five items).

**Authoritative sources.** Persona file + scope-of-work event store + memory system. No snapshot file.

**Divergence from current pOS.** Current pOS writes a snapshot file at PreCompact and reads it at UserPromptSubmit. New pOS does not write a snapshot — it rebuilds from authoritative sources because those sources exist in the new architecture (current pOS predated scope-of-work). This is a cleaner model: the snapshot can drift from reality; the rebuild cannot.

---

## 9. Authoring paradigm — concrete sequence

Concise recap of §2.26–§2.36 as the actionable pipeline:

1. **Signal detection.** Five deterministic counters incremented on relevant events (request decline, correction tagged `domain-handling`, cross-domain scope, low-relevance memory hit, explicit user mention).
2. **Threshold crossing.** Any single signal crosses its threshold → injection block to primary persona: "consider whether a {domain} specialist would help here."
3. **Decision.** Primary persona LLM-judges yes/no. If no, audit and exit. If yes, proceed.
4. **Authoring scope opens.** `runtime.create(ScopeSpec(goal="author <handle> persona", budget=Budget(tokens=10_000, money_cents=50, time_seconds=300), owner_persona=primary_handle, ...))`.
5. **Style harvest.** Deterministic — read existing personas, extract style markers.
6. **Domain research.** Claude Max — draft prompt.md.
7. **Contract synthesis.** Claude Max — draft contract.yaml; loader validates; iterate up to 2× on schema failures.
8. **Self-review.** Claude Max — score against four dimensions; iterate up to 2× per the budget.
9. **Persistence (pending-introduction).** Files written to `workspace/personas/<handle>/` with `pending_introduction: true`.
10. **Introduction.** Primary persona authors the introduction message; channel layer dispatches.
11. **Activation.** On next user message that doesn't retire the persona, loader clears the flag; persona becomes addressable.
12. **Audit.** Memory episode tagged `authoring-decision`; OTel span; introduction message archived to `workspace/personas/<handle>/_introduction.md`.

Total budget per authoring run: ~10k tokens, ~$0.05 (Haiku) to ~$0.50 (Sonnet) depending on which Claude tier is selected, ~5 min wall time. Configurable in `config/stack.yml`.

---

## 10. Introduction protocol

Already covered in §2.35–§2.38. Concise recap as a user-facing protocol:

**The introduction message format** (authored by the primary persona; framework supplies the structural skeleton):

> A specialist persona has been added to your workspace.
> 
> **Name:** {given_name} ({handle})
> **Domain:** {domain inferred from prompt.md}
> **Why now:** {trigger signal in plain language}
> **What they'll handle:** {scope inferred from prompt.md}
>
> They are not yet active. Reply with anything other than `retire {handle}` and they will start work on the next request that fits their domain. Reply `retire {handle}` to remove them.

**Channel.** Goes to the channel the user is currently active on, restricted to one-on-one channels. Group-channel introductions queue (halt signal #3).

**Override pattern.** `/^(no|retire|remove|don't add)\s+(that\s+)?(persona|specialist|{handle})/i`.

**Files on retire.** Moved to `workspace/personas/_retired/<handle>-<timestamp>/`. Audit episode written.

---

## 11. Dependency map

**This layer depends on** (upstream):
- `scope-of-work` runtime — `runtime.list`, `runtime.get`, `runtime.subscribe_all`, `runtime.create`, `runtime.start`, `runtime.subscribe`. (One halt signal: needs `expected_duration_seconds` on `ScopeSpec`.)
- `memory-system` — `memory.search` (for retrievals + correction queries during compaction restoration), `memory.ingest` (for authoring-decision audit episodes).
- Claude Agent SDK (Python) — `query`, `ClaudeAgentOptions`, hook event types. (One halt signal: needs `PostCompact` parity.)
- pyee — already in scope-of-work's deps.
- pydantic — already in memory-system's deps.
- opentelemetry-api/sdk — already in scope-of-work's deps.

**This layer depends on** (no other libraries — full dependency list is pyee + pydantic + OTel + Claude Agent SDK + stdlib).

**This layer is depended on by** (downstream, not yet built):
- The future session runtime — needs `LoadedPersona` to construct system prompts.
- The future channel router (R13) — subscribes to escalation events.
- The future self-correction loop — subscribes to authoring-decision events to track persona-roster evolution.
- The future observability aggregator — subscribes to all OTel spans this layer emits.

---

## 12. Complexity estimate

Honest AI-time estimates for the full layer build, calibrated against the [task-orchestration.md rule 15](prior-pOS rules at prior-pOS .claude/rules/task-orchestration.md) AI-time anchors. The plan's revised projection of 450–700 minutes is in the right zone; my estimate lands at ~520 AI-minutes for code, plus ~100 AI-minutes for tests and documentation, total ~620.

| Sub-component | Files | Estimated AI-minutes |
|---|---|---|
| `pos.persona.contract` (Pydantic models, migration chain, exception classes) | 3 | 30 |
| `pos.persona.loader` (load, validate, reload, list, home_persona, hash check) | 2 | 35 |
| `pos.persona.monitor` (event subscription, awareness-block construction, stuck detector, Claude inference gate) | 4 | 90 |
| `pos.persona.dispatch` (scope-creation helper, observer injection) | 1 | 25 |
| `pos.persona.authoring.signals` (five counter implementations + threshold detector) | 2 | 50 |
| `pos.persona.authoring.pipeline` (style harvest, domain research, contract synthesis, self-review, four Claude-call orchestration) | 4 | 120 |
| `pos.persona.authoring.introduction` (pending-introduction lifecycle, channel dispatch, override detection) | 2 | 45 |
| `pos.persona.compaction` (PreCompact / UserPromptSubmit-fallback hook implementation, restoration block construction) | 2 | 55 |
| pos hooks wiring (PreCompact, UserPromptSubmit, SessionStart) | 1 | 15 |
| Observability emission (spans, JSONL writers across all sub-modules) | 1 | 35 |
| Build-time check (`tests/test_no_persona_in_core.py`) | 1 | 10 |
| Documentation bundle (R4) — prose explanation, relationship map, data flow diagram | 3 | 100 |
| Tests — unit tests per module, integration test for the full authoring pipeline | 8 | ~120 estimated separately |

The complexity sits mostly in the authoring pipeline (Claude-call orchestration with budget enforcement and iteration) and the monitor (event subscription, cached frame, post-compaction restoration). The contract, loader, and build-time check are mechanical.

---

## 13. Prototyping priorities

Three questions that warrant a prototype before the full build:

1. **Token cost of the awareness block injection per turn.** The block is bounded at ~1k tokens but only when it has work to surface. In a real workspace with 10–20 active scopes, what's the actual median injection cost? If it's higher than expected, the section caps need tightening. Prototype: spin up a synthetic scope-of-work with N scopes in mixed states, measure the awareness block size distribution.

2. **Quality of autonomously-authored personas.** The key quality risk is that LLM-authored personas come out generic ("Sarah is a thoughtful researcher who values clarity") and fail the voice-distinctiveness check. Prototype: take 3 trigger signals from the existing workspace's history, run the full authoring pipeline in a sandbox, ask the owner to blind-rank the outputs against personas in the existing roster. If the LLM-authored ones are obviously inferior, the style-harvest step needs to feed more workspace-specific structure.

3. **Compaction-survival accuracy in practice.** The replay-from-authoritative-sources approach is theoretically sound but the persona's behavioural continuity post-compaction is the actual test. Prototype: construct a long conversation that triggers compaction, restore using the new approach, and measure whether the persona's responses on the next 3 turns reflect the pre-compaction context (corrections honoured? active scopes referenced correctly? authority boundaries respected?). Compare against current pOS's snapshot-restore baseline.

These three are sequential — token cost first (cheapest, fastest); persona quality second (needs more workspace history); compaction third (needs the rest of the layer integrated).

---

## 14. Pending spec staging — proposed v1.2 wording

Concrete proposed wording for the three additions flagged on 2026-04-18 14:37, ready for the v1.2 addendum on owner's approval.

### Addition 1 — autonomous persona authoring

Insert under **User-facing layer → Primary persona** in the v1.0 spec:

> **Autonomous persona authoring.** The primary persona may author new specialist personas in the workspace without user pre-approval, subject to (a) the threshold-and-judgment trigger gating defined in the persona-loader spec, (b) the four-dimension quality gate (voice-distinctiveness, scope-fit, redundancy, contract-correctness), and (c) the introduction protocol below. Authoring runs inside an `authoring` scope-of-work with a per-workspace-configurable budget. Authoring decisions are auditable.
>
> Acceptance: a representative trigger signal in a synthetic workspace produces an authored persona whose voice-distinctiveness score passes the workspace's threshold; the authored persona's contract validates against `pos.persona.contract.PersonaContract`; the authored persona does not become addressable until the introduction protocol completes.

### Addition 2 — introduction-before-message rule

Insert under **User-facing layer → Primary persona** immediately after Addition 1:

> **Introduction before first message.** The user must be introduced to every newly-authored specialist persona before that persona is permitted to send any message to the user. The introduction is a one-message format authored by the primary persona, dispatched on whichever one-on-one channel the user is currently active on (group-channel introductions queue). The new persona is non-addressable until the user's first subsequent message that does not retire it.
>
> Acceptance: the new persona's `is_addressable` is False between authoring and first non-retire user message; the workspace's persona-roster diff is visible in the audit log; user retirement moves the persona file to `_retired/` rather than deleting it.

### Addition 3 — pOS core ships authoring framework, not content

Insert under **Architectural layer** as a new explicit constraint (and a build-gate mirror):

> **pOS ships the authoring framework, never persona content.** The persona contract, loader, validator, monitor, signal-detector, authoring pipeline, quality-check rubric, and introduction protocol are all pOS-core. Specific personas — including any starter set, any "default" persona, or any fallback — are workspace content. A build-time check fails on any persona file (`contract.yaml`, `prompt.md`) under pOS-core paths, with carve-outs only for explicit template files under `templates/`.
>
> Acceptance: `tests/test_no_persona_in_core.py` passes on every pOS-core release; the carve-out exception is the only path under which any `prompt.md` may exist in the pOS-core repo; CI fails the build if a workspace persona file lands in core.

---

## 15. Reading-back the constraints

Verifying the design respects every constraint in the plan:

- **Python-native.** All proposed code is Python. Dependencies: stdlib + pyee + pydantic + opentelemetry-api/sdk + Claude Agent SDK Python — all already in the rebuild's dependency list. No new libraries proposed. ✓
- **Max-first.** Three places use LLM inference: the monitor's optional stuck-reason inference (Layer 2, gated), and the authoring pipeline's three Claude calls (research / synthesis / self-review). All use Claude via Max. No other vendors. ✓
- **Zero carryover from current pOS.** The current pOS PreCompact-snapshot pattern is explicitly diverged from; the agent registry shape is explicitly diverged from (directory-based with separate contract/content rather than single Markdown with frontmatter); the persona-guard hook is not carried forward (its function is structurally enforced via the Pydantic contract and the loader's authority-boundary check). I read the current files only to confirm what questions they address; the patterns, schemas, and code structures are net-new. ✓
- **No assumed downstream consumer (A1).** Every emission point (loader, monitor, authoring) emits OTel + JSONL without assuming an aggregator exists. The escalation channel is event-emission with graceful degradation when no router is subscribed. ✓
- **No personas shipped in pOS core.** §6 build-time check enforced at CI. Authoring framework lives in `pos.persona.authoring`, content lives in `workspace/personas/`. ✓
- **STATE.md rule #7 is structural.** The monitor injects every turn via a deterministic UserPromptSubmit hook; the persona cannot avoid seeing the awareness block when it has content. The hook is the structural enforcement point — it doesn't rely on the persona remembering. ✓
- **the owner's 2026-04-18 14:37 rules.** §2.26–§2.34 cover autonomous authoring; §2.35–§2.38 cover the introduction-before-message rule; §6 covers the no-content-in-core rule. Concrete v1.2 wording in §14. ✓

---

## 16. What I did not find

Honesty per the plan:

- I did not find a published precedent for the "primary-persona-as-contract-not-character" pattern with quite the discipline pOS wants. Letta is closest but treats the persona as content with a thin metadata wrapper, not as a contract with separated content. AutoAgents is structurally closest but treats agents as ephemeral generations rather than long-lived workspace artefacts. The pOS pattern proposed here combines AutoAgents' {P, D, T, S} bones with Letta's content/metadata split and Pydantic-AI's contract-validation discipline.
- I did not find a precedent for the introduction-before-message rule. Letta's persona blocks are silently editable; AutoAgents' generated agents speak as soon as they're spawned; Claude Agent SDK's subagents need no introduction because they're not user-facing entities. the owner's rule is novel and worth treating as a pOS-distinctive contribution.
- I did not find a precedent for compaction-survival via authoritative-source replay rather than snapshot. Current pOS, OpenClaw, Termo, Microsoft Agent Framework — all snapshot. The authoritative-source approach is feasible only because pOS has scope-of-work + memory + the persona file as separate, durable, queryable surfaces. This is a deliberate architectural exploitation of the pOS shape, not a borrowed pattern.
- I did not find published numbers for the token cost of structured background-work-awareness injection at the cadence proposed. The estimate in §13 prototyping priority 1 is the right way to find out.

---

## Sources

Surveyed during the research:

- [Anthropic Claude Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)
- [Anthropic Claude Code Hooks reference](https://code.claude.com/docs/en/hooks)
- [Letta — Memory blocks (core memory)](https://docs.letta.com/guides/agents/memory-blocks/)
- [Letta — Memory blocks (the key to agentic context management)](https://www.letta.com/blog/memory-blocks)
- [LangGraph — Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [LangChain blog — Making it easier to build human-in-the-loop agents with interrupt](https://blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/)
- [AutoGen — Microsoft Research](https://www.microsoft.com/en-us/research/project/autogen/)
- [CrewAI — Agents documentation](https://docs.crewai.com/en/concepts/agents)
- [AutoAgents — A Framework for Automatic Agent Generation (arXiv:2309.17288)](https://arxiv.org/abs/2309.17288)
- [AgentVerse (arXiv:2308.10848)](https://arxiv.org/abs/2308.10848)
- [AgentSpawn — Adaptive Multi-Agent Collaboration (arXiv:2602.07072)](https://arxiv.org/abs/2602.07072)
- [MetaGPT (arXiv:2308.00352)](https://arxiv.org/abs/2308.00352)
- [Pydantic AI](https://ai.pydantic.dev/)
- [Anthropic — Persona vectors](https://www.anthropic.com/research/persona-vectors)
- [Persona Drift research (arXiv:2402.10962)](https://arxiv.org/html/2402.10962v1)
- [Microsoft Agent Framework — Compaction](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/compaction)
- [Google ADK — Context compression](https://google.github.io/adk-docs/context/compaction/)
- [Compaction Survival System (Termo)](https://termo.ai/skills/compaction-survival)
- [context-mode — context window optimization](https://github.com/mksglu/context-mode)
- [Self-Organizing LLM Agents (arXiv:2603.28990)](https://arxiv.org/html/2603.28990)
