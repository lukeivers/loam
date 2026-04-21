# Research Plan — Domain-Workspace Migration

**Component:** Domain-Workspace Migration — the first real use of the pOS-v2 foundation, migrating the existing workspace from the current pOS (at `the existing workspace root`) into a running pOS-v2 workspace that the ten sealed components compose through workspace-bootstrap.
**Status:** DRAFT — awaiting owner's approval before research begins.

**Phase 4 second component.**

---

## Objective this research must serve

Produce a migration audit of the existing workspace, a wave-scoping recommendation, and a wave-1 specification, such that the output is enough to drive a proposal that the owner can approve and a brief that dispatches wave-1 migration work cleanly. The research does not migrate anything; it inventories, maps, and scopes.

Specifically, the research must:

- Enumerate every category of content in the existing workspace that has migration relevance (personas, memory stores, configs, close-associate list, projects/products, content, hooks, cron jobs, bridges, owner-profile, the nested sub-workspace, MCP integrations, session context caches).
- For each category, determine the destination shape in pOS-v2 (which sealed component consumes it, what format it expects, whether the mapping is direct, translated, or authored-fresh).
- Identify content with no destination in pOS-v2 (current pOS conventions that don't carry over — CLAUDE.md rules files, `.claude/` hooks, orchestrator-specific config) and decide whether to drop, reframe, or defer.
- Recommend a wave structure — wave-1 minimum-viable-workspace, wave-2+ progressive additions — with explicit acceptance for each wave.
- Surface every case where the migration forces a design call on pOS-v2 that wasn't made during component builds (e.g. workspace-content directory convention, multi-workspace support posture, persona contract schema validation).

## Starting position

- **Eleven sealed components on `pos-v2`** at commit `aab5800` (seal-ritual retrofit). Workspace-bootstrap's extension protocol admits workspace-local adapters via `bootstrap.yaml` path-plus-callable entries. The three-gate chain composes; the four-wrap dispatch works; the four-part correction protocol enforces structurally.
- **Current the existing workspace** at `the existing workspace root` on the `main` branch. Substantial content: ~23 personas, years of memory files, active products, creative content, close-associate list, calendar + Gmail MCP integrations, cron + launchd schedules, the nested sub-workspace as a nested sub-workspace, The sibling workspace bridge stub.
- **Current pOS workspace conventions** encoded in `prior-pOS .claude/rules/*.md`, `prior-pOS .claude/CLAUDE.md`, `config/stack.yml`, `memory/`, `personas/`, `context/SESSION_CORE.md`. These conventions were authored against the Ruby-based current-gen pOS; pOS-v2 has its own conventions encoded in per-component configs and workspace `bootstrap.yaml`.
- **pOS-v2 is Python-native, uses per-component SQLite sidecars, has no concept of `prior-pOS .claude/rules/`, no concept of a Ruby orchestrator, no concept of `config/stack.yml`.** The migration translates where possible, authors fresh where necessary, drops what doesn't carry.
- **the owner is the first and only user of the new pOS.** This is his migration, not an external adopter's. Onboarding is deferred to a later component (per the 2026-04-20 15:28 sequencing ruling); this migration is for the owner (as designer) using the owner's (as user) content.

## Questions the research must answer

### 1. Personas

1. Enumerate every persona in the existing workspace: name, handle, file path, size, domain, reports-to. Expected count ~23 from `personas/README.md` and `prior-pOS .claude/rules/org-hierarchy.md`.
2. For each persona, map to the pOS-v2 persona primitive (contract + loader + validator; workspace-supplied content). Does the current `.md` format carry over directly, or does it need re-authoring against the primitive's schema?
3. Some personas are deferred in current pOS (deferred personas per `prior-pOS .claude/rules/org-hierarchy.md`). Do they migrate (as deferred), drop, or defer?
4. Primary persona — the primary persona in current pOS. Does the primary persona migrate as-is, re-author against pOS-v2's primary-persona primitive, or author a fresh primary-persona-v2 with lessons learned?
5. Per-persona memory files (`personas/<handle>/memory.md`) — these carry substantial correction-history and calibration notes. Migrate as seed content to pOS-v2's memory system, or as persona-local files?

### 2. Memory

6. Current pOS has `memory/daily/`, `memory/weekly/` (synthesis output), `memory/people/`, `memory/companies/`. What exists at volume? Date ranges?
7. pOS-v2's memory-system is a Graphiti-backed FastAPI sidecar. What does memory migration look like — bulk ingest of existing daily files as Graphiti nodes/edges, or preserve the files as seed content and let the system ingest naturally?
8. Weekly synthesis files — are they authoritative durable content that migrates, or are they derived content that the pOS-v2 memory system will re-synthesise?
9. Entity files (`memory/people/<name>.md`, `memory/companies/<name>.md`) — direct mappings to Graphiti entity nodes, or workspace-local content?
10. Retention policies differ — current pOS prunes daily files past 90 days; pOS-v2 memory-system has its own retention. Do we migrate everything and let pOS-v2 prune, or pre-prune at migration time?

### 3. Configs and workspace content

11. `config/stack.yml` — enumerate every key: attribution, session mode, notification caps, capability bindings, minimal-mode triggers, calibration status. For each, determine the pOS-v2 destination (per-component yaml, workspace bootstrap.yaml, or no destination).
12. `prior-pOS .claude/rules/*.md` and `prior-pOS .claude/standards/*.md` — current pOS uses these as always-on context. pOS-v2 has no equivalent by design (the sealed components own their own behaviour). What survives: the PRIME rules (prime.md, prime-rules.md)? Rules that encode workspace-specific policy (delegation-rules.md, micro-business.md)? Drop the rest?
13. `CLAUDE.md` and `prior-pOS .claude/CLAUDE.md` — these orient Claude Code to the workspace. pOS-v2 doesn't use Claude Code as its session layer; it has its own primary-persona loader. Does CLAUDE.md content translate into persona-loader config, or is it abandoned?
14. `prior-pOS .claude/hooks/*` — current pOS has substantial hook machinery. pOS-v2 has component-level event handlers via pyee; hooks-as-scripts don't fit. Which hooks are behavioural (translate into pOS-v2 component config) vs ceremonial (drop)?
15. `config/` more broadly — `config/owner-profile.md`, `config/tech-stack.md`. Workspace content; copy or re-home.

### 4. Close-associates, calendar, email

16. `personal/close-associates.yml` — maps directly to pOS-v2 safety's workspace allowlist additions. What's the shape translation?
17. Calendar and Gmail MCP integrations — currently wired through Claude Code settings. pOS-v2 uses its own IPC layer; calendar and email access happen via workspace-local adapters or the orchestrator's capability bindings. How does this re-plumb?
18. Telegram integration — current pOS has substantial Telegram integration for primary-persona-to-owner one-on-one channel. pOS-v2's primary-persona layer owns the one-on-one channel concept but doesn't ship a Telegram transport. Migration = author a workspace-local Telegram adapter for the OneOnOneChannel.

### 5. Projects, products, content

19. `products/` — workspace-specific product codebases. Workspace content; copy. Any registrations needed (scopes, budget defaults, orchestrator-tracked workflows)?
20. `personal/projects/` — personal project directories. Same pattern.
21. `content/` — creative content (a creative-content series, business briefs). Copy.
22. `company/` — governance, calendar, finances, roadmap. Copy + re-home any integrations.

### 6. Infrastructure

23. `ops/cron/crontab` — current pOS has an extensive crontab (memory rotations, backup, event log rotation, telegram watchdog, etc). pOS-v2's orchestrator has its own scheduling surface. Which current cron jobs remain relevant? Which are obsoleted by pOS-v2's built-ins? Which are workspace-local ops that migrate?
24. `ops/launchd/*.plist` — same question for launchd services.
25. `ops/tools/*` — ancillary scripts. Migrate as workspace tools, or abandon?
26. `ops/events.jsonl` (append-only source of truth in current pOS) — how does this relate to pOS-v2's observability aggregator?

### 7. Bridges and sub-workspaces

27. a sibling-workspace bridge stub (`personas/bridge-stub.md`, `context/bridge-protocol.md`) — current workspace has a bridge to the sibling workspace for business work. Does this bridge concept survive in pOS-v2?
28. `the nested sub-workspace` — nested sub-workspace. Does the nested sub-workspace (a) migrate as content within the existing workspace pOS-v2 workspace, (b) become its own independent pOS-v2 workspace, (c) stay on current-gen pOS?

### 8. Session context and operational state

29. `context/SESSION_CORE.md`, `context/PHONE_BRIEF.md`, `context/CONTEXT_INDEX.md` — current pOS's session-startup context. pOS-v2's primary-persona loader handles session startup; these files either translate to primary-persona config or are regenerated naturally.
30. `context/handoffs/` (existing workspace convention) — an extensive history of handoff documents from prior sessions. Preserve as memory content, or archive?
31. `docs/rebuild/` — this directory. Contains the rebuild work's own context (component specs, research docs, proposals, briefs). Does it stay where it is, or migrate as historical reference?

### 9. Design calls the migration forces on pOS-v2

32. **Workspace content directory convention** — where does workspace content physically live? `~/pos-workspaces/the existing workspace/` with its own `bootstrap.yaml` and content subdirectories? Or does content stay in the current repo and the `bootstrap.yaml` references it via paths?
33. **Multi-workspace posture** — is pOS-v2 single-workspace-per-install by convention, or does the design admit multiple workspaces (e.g. the existing workspace + the nested sub-workspace + future)? Current pOS-v2 assumes single-workspace per orchestrator process.
34. **Persona contract schema** — pOS-v2's primary-persona primitive is "contract + loader + validator; workspaces supply content." What IS the contract's schema? The research must inspect the sealed primary-persona code and state the schema in precise terms so the migration knows what each persona file must conform to.

### 10. Wave scoping recommendation

35. Based on 1–34, recommend a wave-1 scope that gets the owner actually using the new pOS. Candidate wave-1: (a) owner-profile + the primary persona + 3–5 most-used specialist personas, (b) minimal memory (last 30 days daily files + key entity files), (c) close-associate list, (d) attribution config, (e) one workspace-local adapter (Telegram for OneOnOneChannel), (f) `bootstrap.yaml`. Defer to wave-2+: full persona set, full memory, projects/products, cron/launchd, bridges, the nested sub-workspace, extensive historical content.
36. For wave-1, state the acceptance criterion — what observable behaviour proves the workspace is usable? Candidate: "the owner can open a session against the pOS-v2 workspace, the primary persona loads and responds in the primary persona's proper voice, a test scope activates and flows through the three-gate chain, a memory query against the seeded 30-day window returns relevant results, a Telegram message from the primary persona arrives on the one-on-one channel."
37. Recommend the wave-1 dispatch shape — is wave-1 itself large enough to warrant a single build agent, or does it naturally decompose into sub-waves (persona migration, memory migration, config translation, adapter authoring)?

## Constraints the research must respect

- **This component does not migrate anything.** It produces the audit + scoping recommendation. The proposal approves scope; the build does the migration.
- **No amendments to sealed components.** If the audit surfaces a pOS-v2 design gap that can only be closed by amending a sealed component, halt and signal — the gap becomes its own component cycle, not a sidebar inside migration.
- **Wave structure is the default.** Big-bang migration is rejected as the likely-to-go-wrong pattern. Research's job is to propose the wave-1 minimum and defer the rest explicitly.
- **the owner is the user.** No speculative design for external adopters. Every migration decision is against the owner's actual use patterns.
- **Preserve provenance.** Memory content that migrates carries its original timestamps and source file references. No content is silently re-authored at migration time.
- **A1 correction held.** Any migration-time observability emissions go through the aggregator's registered tracer.
- **Max-first.** No LLM inference inside the migration logic. Persona + memory migrations may use LLM for *content translation* where shape differs, but the decision to do so is surfaced in the proposal for owner's approval.
- **Halt-on-deviation.**

## Deliverable — what the research document must contain

A markdown document at `components/domain-workspace-migration/research.md` with:

1. **Current-workspace inventory** — every category of content with counts, file paths, date ranges, sizes.
2. **Destination-mapping table** — one row per category: current location, pOS-v2 destination, mapping type (direct / translated / authored-fresh / drop), notes.
3. **Persona contract schema** — extracted from the sealed primary-persona primitive; states exactly what a workspace-supplied persona file must conform to.
4. **Memory migration approach** — bulk-ingest vs seed-and-let-the-system-ingest, provenance preservation mechanism.
5. **Config translation table** — `stack.yml` key by key, `prior-pOS .claude/rules/*.md` file by file, `prior-pOS .claude/hooks/*` behavioural-vs-ceremonial classification.
6. **Design-call inventory** — the pOS-v2 design decisions this migration forces (workspace directory convention, multi-workspace posture, etc), each with options considered and recommendation.
7. **Wave structure recommendation** — wave-1 scope, wave-2+ deferred items, rationale for the split, acceptance criterion per wave.
8. **Wave-1 dispatch-shape recommendation** — single build agent vs sub-wave decomposition.
9. **Open questions for ruling recorded** — decisions that sit above the migration's authority.
10. **Complexity estimate** — AI-time for the research itself (this audit is its own work) and a rough estimate for wave-1 build.

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. The agent's job is to read the existing workspace, read the ten sealed pOS-v2 components, and produce the audit. No migration work happens in the research; halt-on-deviation applies. Any design call the audit surfaces that requires pOS-v2 changes is flagged rather than improvised.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
