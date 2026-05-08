# Research Plan — Primary-Persona Layer (Loader + Monitor + Autonomous Authoring)

**Component:** Primary-Persona Layer — three tightly-coupled halves sharing the persona contract: loader + monitor + autonomous authoring.
**Status:** DRAFT — **revised 2026-04-18 14:40 CDT** per the scope expansion. Awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for a three-part primary-persona layer, such that:

- Every v1.0 "Primary persona" acceptance criterion can be honoured by a concrete implementation proposal.
- STATE.md rule #7 (primary persona never loses track of background work) is delivered structurally, not advisorily.
- The loader enforces the contract: workspace personas either conform or are rejected; no pOS-shipped personas exist; a workspace with no persona cannot start a session.
- The monitor subscribes to scope-of-work's existing emission and query surface without requiring changes to scope-of-work.
- The autonomous-authoring framework (the owner's direction 2026-04-18 14:37 CDT) supplies workspaces with a template, a research paradigm, quality-assurance checks, and an introduction protocol. The primary persona can autonomously judge when a new specialist persona would meaningfully improve output, author one, and introduce it to the user — all without pre-approval of the *creation*, but with mandatory user introduction *before the new persona speaks*.

Three concerns pair throughout: what does the persona need to be loadable-and-contract-validatable, what does the monitor need to keep the persona continuously aware, and what does the primary persona need to author a new persona well without user oversight of the authoring itself?

## Starting position

- **Scope-of-work primitive is shipped** (sealed 2026-04-18 14:27 CDT) on `pos-v2`. It exposes: `list(filter)` (filterable by state, parent, owner, pending-extension), `get(scope_id)`, pyee observer subscription, and OTel span emission. The monitor will consume this surface; no changes to scope-of-work are in play.
- **Memory system is shipped** (sealed 2026-04-18 12:08 CDT). It loads workspace personas conceptually — via `scope_source` injection and scoped retrieval — but does not currently do contract validation on a workspace's primary persona. The loader being designed here is new.
- **The current pOS persona-loading machinery** at `prior-pOS .claude/hooks/compaction-resilience.rb` and the `.claude/agents/*` registry is *not* a reference implementation. Current pOS conflates persona-as-content with persona-as-contract; the new pOS separates them cleanly. The researcher may read the current pOS for the *shape* of questions it addresses (compaction survival, session startup, persona switching), but not for solution patterns. (Zero-carryover constraint still applies.)
- **Python-native.** New pOS language.
- **No assumed downstream consumer.** A1 correction applies — the loader and monitor emit their own observability; they do not assume anything subscribes.

## Questions the research must answer

### 1. Persona contract — what must a workspace persona declare?

1. The spec names three functional responsibilities of the primary persona: single point of contact, context holder, escalation judge. What does *declaring conformance* look like concretely — a manifest file, a Python class with required methods, a YAML spec, something else? What fields are mandatory?
2. Which parts of the persona are **content** (voice examples, specific skills, domain of expertise) vs **contract** (the three responsibilities, the authority boundary, the escalation taxonomy)? pOS validates the contract; workspaces author the content.
3. How is the contract versioned? When pOS evolves the contract, how do existing workspace personas migrate?
4. What is the failure mode on a workspace attempting to load a non-conforming persona — a clear error, a diagnostic, a migration suggestion?

### 2. Loader lifecycle

5. When does the loader run — once per session start, on every compaction event, on explicit user-switch, all of the above? (See the current-pOS compaction hook for the shape of the question, but not the implementation.)
6. What state does the loader itself hold? Is it stateless (reload from disk every time) or does it cache (with invalidation)?
7. How does the loader interact with the session boundary — does it produce a "loaded persona" object that the session carries, or is it a subscription the session queries?

### 3. Monitor — what information does the primary persona need from background work?

8. For each background-work state the primary persona needs awareness of (active, paused, pending-extension-request, escalated, stuck, finished, failed), what does "continuous awareness" look like concretely — a prompt-injected status block, a notification stream, a query API the persona calls on demand, an observability dashboard?
9. What is the monitor's cadence — does it push on state change (event-driven), pull on session event (e.g. every user message), or both?
10. What is "stuck"? The primitive reports a scope's current state but has no notion of *stuck* beyond timeouts. How does the monitor infer stuck-ness — elapsed-without-transition threshold, missing-heartbeat, observer silence, LLM-inference judgment?
11. How does the monitor present information to the persona — injected prompt context, tool-call output, background-log file, OTel-to-LLM bridge? What's the token-cost discipline here (the monitor runs frequently; token inflation is a real risk)?
12. Is there a monitor-to-persona conversation path — the persona can ask the monitor "why is this scope paused?" — or is it one-way (monitor feeds, persona reads)?

### 4. Compaction survival

13. The current pOS has a compaction-survival hook (PreCompact snapshot + UserPromptSubmit restoration). The new pOS has this as a spec criterion under Session-resilience: compaction events preserve persona identity, active work items, and pending decisions. The loader-plus-monitor together own this. What is the shape of the compaction-survival mechanism for the new pOS — does it match the current pOS's snapshot-and-restore pattern, or is there a more durable approach (e.g. every persona decision is an event in a log; post-compaction, the log is replayed to restore state)?
14. Which items survive compaction — persona identity, authority boundary, context of current scopes, pending decisions, recent corrections — what is the canonical "survival list" for the new pOS?
15. How does compaction survival integrate with the monitor — the monitor is already streaming state; can it be the compaction-survival mechanism, or are these separate concerns?

### 5. Escalation-judgment mechanism

16. The primary persona "judges escalation at the authority boundary" per the spec. What is the concrete mechanism — a Pydantic policy on the persona's manifest declaring what requires user input, an LLM-inference call each time, a rubric (authority tier), a hybrid? This is a determinism-tier question (v1.0 Layer 1 / 2 / 3).
17. How does the persona communicate an escalation decision to the user — who owns the message-to-user channel, and how does it integrate with the channel-agnostic-interaction objective (v1.1 R13)?

### 6. Integration with scope-of-work and memory

18. How does the loader / monitor interact with the scope-of-work primitive — specifically, how does the persona *create* a scope when the user asks it to do something? Does the persona have a constructor-like API on scope, or does it declare intent and the loader / monitor mediates?
19. How does the persona interact with the memory system — is memory retrieval a tool the persona calls each turn, a pipeline stage that fires before the persona runs, or both?
20. What is the failure isolation — if the monitor crashes, does the persona keep running (degraded mode) or does the session halt?

### 7. Emission surface

21. What does the loader + monitor emit (OTel, log files, events)? Per A1 — they do not assume downstream consumers. What do they emit for future consumers (observability aggregator, audit log, replay harness)?

### 8. Persona template — the canonical manifest

22. What is the canonical shape of a workspace-persona manifest — one file with structured sections, a directory with a convention (prompt.md + config.yml + memory.md + rules/), something else? The current pOS uses a directory-based layout; the new pOS can choose freely.
23. What are the mandatory template sections that every persona must fill in (identity, archetype, voice, hard rules, severity labels, output format) versus the optional ones?
24. How does the template express the *contract* (what pOS validates) versus the *content* (what the workspace authors)? Can the contract parts be structured data and the content parts prose, or is it all markdown?
25. How does the template version? When pOS evolves the template, how do existing workspace personas migrate — automated, prompted, manual?

### 9. Persona-creation triggers — when is a new persona warranted?

26. What signals tell the primary persona that a specialist persona would meaningfully improve output? Candidates: repeated requests in a domain the primary persona is not good at, user frustration with the primary persona's handling of a specific concern, cross-domain work that keeps surfacing, domain expertise beyond the primary persona's authored scope.
27. What is the decision rubric — deterministic thresholds (e.g. N requests in domain X in window Y), LLM-inference judgment by the primary persona, hybrid? This is a determinism-tier question (v1.0 Layer 1 / 2 / 3).
28. Is the decision auditable — can the user see "here's why I decided to author a new persona for Z"? Per the anti-deskilling objective and the owner's explanation-always-paired-with-action principle.

### 10. Research paradigm — how the primary persona fills in a new persona's spec

29. When the primary persona decides to author a new persona, what does it do to gather content? Candidates: web search on the domain, analysis of existing workspace personas for style consistency, review of relevant workspace memory for domain-specific vocabulary, dialogue with the user for calibration (optional — the owner allows autonomous authoring without user involvement in the drafting).
30. How is the primary persona's authoring output constrained to match the workspace's house style — voice, format, roster-consistency? Does the primary persona read other workspace personas as style input before drafting?
31. What is the "research budget" for authoring? the owner's spec says scopes have budgets; the authoring process should sit inside a scope with its own time/token/money ceiling so runaway persona-generation is impossible.

### 11. Quality assurance — ensuring the authored persona is good, not boilerplate

32. What quality checks run on a newly-authored persona before it is activated? Candidates: template-conformance check (mandatory sections filled), voice-calibration check (not-generic — the "if it could come from any AI, rewrite it" test applied automatically), scope-fit check (the persona's declared domain matches the trigger that caused its creation), redundancy check (the persona doesn't overlap meaningfully with existing ones).
33. Do quality checks reject a bad persona outright, or iterate with the primary persona until it passes? If iterate — what's the limit?
34. Who owns the quality threshold — is it a fixed rubric in pOS core, or a per-workspace configurable?

### 12. Introduction protocol — the user is told before the new persona speaks

**the owner's hard rule 2026-04-18 14:37:** the user must be introduced to a newly-authored persona BEFORE receiving any message signed by that persona. The user must never see "some random name" appear in their workspace without the primary persona having introduced them first.

35. What is the concrete introduction mechanism — the primary persona emits a named "persona-introduction" message that includes the new persona's name, domain, why they were authored, and what to expect from them? A notification? A block injected into the next turn's context?
36. What is the introduction's timing — immediately on authoring, or deferred until the new persona is about to operate for the first time?
37. Can the user override or reject a just-introduced persona (e.g. "no, don't have that persona — I didn't want it")? If so, what happens to the authored file — retire it, archive it, delete it?
38. How does the introduction integrate with the channel-agnostic-interaction objective (v1.1 R13)? Does the introduction go to every configured channel, or only the channel the user is currently on?

## Constraints the research must respect

- **Python-native.** Implementation in Python; stdlib preferred; pyee / pydantic / opentelemetry already in scope from prior components. Other libraries require halt-and-signal.
- **Max-first; no LLM inference inside the loader itself.** If the monitor uses LLM inference (e.g. to infer "stuck" semantically, or to summarise background-work status for the persona), that work uses Claude via Max.
- **Zero carryover from current pOS / the existing workspace.** The current-pOS compaction hook, agent registry, and persona-switching machinery are not reference implementations. Read them only to understand *what questions they address*, not *how they address them*.
- **No assumed downstream consumer (A1 correction).** Emit OTel + event log entries; no aggregator assumed.
- **No personas shipped in pOS core.** The loader loads *workspace* personas; pOS provides contract + loader + validator + monitor, nothing else. A build-time check on pOS-core paths fails if any persona file appears.
- **STATE.md rule #7 is structural, not advisory.** The monitor is deterministically triggered; it does not rely on the persona remembering to check.
- **No proposals, no code, no briefs.** Only the research document.

## Deliverable — what the research document must contain

A markdown document at `components/primary-persona-loader/research.md` with:

1. **Survey of existing patterns** — how other LLM harnesses / agent frameworks handle persona contracts, persona loading, compaction survival, background-work awareness, and autonomous persona/agent creation. Specifically survey: Anthropic Agent SDK (hooks, session handling, SubagentStart), Letta (memory blocks as persona identity), LangGraph (checkpointer + interrupt mechanism), any persona-authoring framework that separates contract from content, AutoGen / CrewAI / AgentVerse and similar for multi-agent creation patterns.
2. **Recommended design shape** — for each of the twelve question groups, options considered, recommended option, rationale.
3. **Acceptance-criterion coverage** — mapping each v1.0 Primary-persona acceptance criterion, STATE.md rule #7, relevant v1.1 revisions, and the owner's 2026-04-18 14:37 authoring-and-introduction additions to the piece of the design that delivers it. Any that cannot be satisfied surfaces as a halt.
4. **Contract specification sketch** — the research returns a concrete sketch of what a workspace persona manifest/class must declare (the fields and methods).
5. **Monitor information architecture** — what the monitor feeds the persona, in what form, at what cadence.
6. **Compaction-survival mechanism** — the shape of the new pOS's compaction survival approach (with explicit divergence or convergence from the current pOS pattern).
7. **Persona-template specification** — the canonical shape of a workspace-persona manifest, mandatory vs optional sections, contract-vs-content separation.
8. **Authoring paradigm** — the concrete sequence a primary persona follows to author a new persona (triggers → decision → research → draft → quality-check → introduction → activation), with budget bounds and per-step acceptance.
9. **Introduction protocol** — the concrete mechanism for the user hearing about a new persona before any message from that persona lands. Covers timing, channel-awareness, user-override.
10. **Dependency map** — what depends on the layer (sessions, future orchestrator, observability aggregator, self-correction loop); what the layer depends on (scope-of-work, memory).
11. **Complexity estimate** — AI-time, honest. Expanded scope (three halves rather than two) suggests 450–700 AI-minutes rather than the 300 originally projected; researcher should update.
12. **Prototyping priorities** — any questions only a prototype can answer (e.g. token-cost of monitor-injection per turn, latency of event-driven vs polling monitor, quality of autonomously-authored personas against human-authored baselines).

## Pending spec staging

Three new requirements from the owner 2026-04-18 14:37 would benefit from eventual inclusion in a v1.2 spec addendum (after the research recommends concrete wording):

- Primary persona MAY autonomously create new workspace personas without user pre-approval if they would meaningfully improve output.
- The user MUST be introduced to every new persona before any message signed by that persona is delivered.
- pOS core MUST ship the authoring framework (template + research paradigm + quality checks + introduction protocol) even though it ships zero persona content.

These are not added to the spec now; the research proposes concrete wording, the owner approves, and a v1.2 addendum lands alongside the proposal.

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Agent reads the plan, performs the research, produces `research.md`, and returns. Halt-on-deviation applies: if any spec criterion cannot be satisfied under the constraints, the Agent halts and surfaces the conflict.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches a general-purpose Agent to conduct the research.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks the plan.
