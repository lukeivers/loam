# Memory System — Research v2

**Component:** Memory System. **Phase:** Research (no design, no code).
**Predecessor:** `research.md` (v1). **Date:** 2026-04-17.
**Brief:** `research-plan-v2.md` (authorised without further review, 2026-04-17 17:02 CDT).

---

## READER ANNOTATIONS — the owner 2026-04-18 08:45 CDT

Three annotations from read recorded, recorded here so they travel with the document.

### A1 — Event-log leak (framing correction)

The research treats "pOS event log" as an existing substrate to integrate with — notably at §3.3 (OTel sink), §4.2 Gap handling, §5 adaptation-scope item 3 ("Event-log wrapper"), §6.1 architecture diagram, §6.3 integration points, and §8.7 ("pOS event log is one OTel sink"). **An event log has not yet been designed for the new pOS.** Memory is the first foundational layer; it must be specified without presupposing observability infrastructure that doesn't exist yet.

**Correction going into the proposal phase:** memory emits its own observability records (OTel spans, token-usage rows, op-audit entries) in a canonical format. Consumers of those records — including an eventual event-log component — subscribe to memory's emissions. Memory does not write into a pre-existing log; it publishes, and the observability layer (when designed) aggregates. This changes the adaptation surface: the "event-log wrapper" becomes an "observability-emission adapter" with no downstream consumer assumed.

### A2 — Gap 4.1 accepted: U1(c) revised to semantic round-trip equivalence

the owner accepts the research's recommended handling option (b) for Gap 4.1. The v1.0 spec clause "memory/daily entries are byte-identical to pre-upgrade" is retired and replaced in v1.1 with a semantic round-trip equivalence test: pre-upgrade probe queries plus post-upgrade query replay, with a drift-report threshold for pass/fail. Kuzu DB snapshot pre-upgrade preserves physical reversibility.

### A3 — New objectives proposed by the owner (for v1.1 spec)

Three new objectives land from read recorded:

1. **Comprehensive accrual (tighten "ephemeral" to near-zero).** Nearly all knowledge goes into the memory system: every conversation, every decision, every piece of research, every unit of work. "Extremely ephemeral" is to be defined narrowly — current-CPU readings, ticking clock values, volatile UI state — not "anything not obviously worth keeping." This refines the accrual behaviour in the spec.

2. **Process-of-arrival capture from background dispatches.** Every background dispatch (agent, research, long-running task) emits a stream-of-consciousness log during execution. That stream is summarised and ingested into memory alongside the dispatch's output, so memory records not just outcomes but the process of arriving at them. New objective under the accrual stack, with a dependency on whatever dispatch primitive pOS ends up with.

3. **Human-readable documentation bundled alongside every pOS component.** Every component shipped into pOS carries human-readable documentation — prose, diagrams, flowcharts, relationship maps — bundled with it, so the owner and others can understand how it works and how the pieces relate. Cross-cutting principle for the rebuild, not just memory-system-specific; belongs as a new objective in the Architectural layer.

These three objectives are staged for v1.1 alongside the U1(c) change (A2) and the research's earlier-proposed §7–§8 revisions. Full v1.1 revision list is maintained in `components/memory-system/component.md` pending confirmation on each.

### A4 — Prototyping data must not come from existing pOS / the existing workspace content

The research's prototyping priorities (§5 item 6, §9 retrieval test-set) propose building a retrieval test set from "the owner's actual past sessions" (specifically `memory/daily` content). the owner rejects this: (a) there is no new-pOS content yet, and (b) reading from the current pOS memory has a strong chance of corrupting the build by leaking old assumptions into what we're building fresh.

**Correction going into the proposal phase:** the retrieval test set, and any other prototyping data, must be **synthetic** — generated arbitrary content that is genuinely unrelated to anything currently worked by the existing workspace or the old pOS framework. No mining of `memory/daily`, no reading of existing personas, no extraction from current task records. If we need example queries and ground-truth answers, they are fabricated fresh (possibly from invented scenarios with invented entities) so they have zero carryover from the current workspace. This preserves the "authentic fresh pOS experience" that the rebuild is meant to deliver.

**Implication for adaptation scope (§5 item 6 — "Retrieval test set"):** the item is not owner-curation from the owner's history; it is synthetic-data generation with owner-curated ground-truth labels. Complexity estimate shifts upward: generating synthetic Q/A pairs that test the retrieval features meaningfully (multi-hop, context-aware, temporal) requires deliberate design, not mining. This becomes the #1 prototyping-phase design task.

---
**Spec scored against:** `docs/rebuild/spec/loam-objectives-spec.md` v1.0 (LOCKED), *Knowledge — accrual and retrieval* section plus self-upgrade clause U1.

---

## 0. Reading guide

v1 halted on a single spec clause (U1(c), byte-identical memory preservation) and treated every criterion as a hard gate. read recorded: the gating was too tight — byte-identity was a substrate leak from the current `memory/` directory, not a design requirement.

v2 reframes the evaluation as *best-fit* rather than *pass-all-gates*. This document:

1. Uses v1's candidate findings as input evidence and does not re-survey the basics.
2. Produces a best-fit ranking with a single primary recommendation.
3. Enumerates **beyond-spec features** of the recommended candidate and tags each for absorption.
4. For every spec criterion the recommended candidate misses, presents three handling options (accept / revise / flag) rather than halting.
5. Does **not** consider build-from-scratch; the owner has struck that option.

**Recommendation in one line:** Adopt **Graphiti (getzep/graphiti)** on an **embedded Kuzu** graph backend, **Claude (via Max) for all LLM inference** (entity/edge extraction, contradiction resolution, community summaries, reranking), and a **local Ollama embedding model** (Qwen3 or bge-large) for the capability Max doesn't cover. Recommend revising spec clause U1(c) from byte-identical to semantic-preserved. Several beyond-spec Graphiti features should be absorbed as new or refined pOS objectives.

---

## 1. Candidate ranking

### 1.1 Scoring method

Best-fit weights, from highest cost of miss to lowest:

- **Conceptual misses** (the candidate has no mechanism for the spec concept at all, e.g. "no supersession"): heavy penalty.
- **Depth misses** (concept present but shallow, e.g. "supersession exists but no pointer to superseder"): medium penalty.
- **Adaptation-cost misses** (concept present, fits on top with a workspace-layer adapter): light penalty.
- **Substrate-leak misses** (the criterion is written as if the substrate were flat files, e.g. "byte-identical"): near-zero penalty — the spec should be revised, not the candidate rejected.

Adaptation cost is measured in AI-time for the glue code to close the gap (rule 15 anchors from `prior-pOS .claude/rules/task-orchestration.md`).

Anything SaaS-only with user-data-on-vendor-servers is disqualified at the privacy gate, not scored further. This follows security.md Tier A reasoning and the owner's vendor-free-outside-Max framing.

### 1.2 Ranking table

| Rank | Candidate | Conceptual | Depth | Adaptation | Substrate-leak | Net verdict |
|------|-----------|------------|-------|------------|----------------|-------------|
| **1** | **Graphiti (OSS) — Kuzu + Anthropic + Ollama** | none | none on A2/A3/R1; minor on A1 (rubric) | moderate (scope mapping, ephemerality filter, event-log wrapper, retrieval test set) | one (U1(c) byte-identity) | **Primary recommendation.** The only candidate that implements bitemporal time-lock + pointered supersession natively, with a first-class group/namespace partition that maps to scope-of-work, and an Anthropic LLM driver. All outstanding gaps are adapter-layer, not engine-layer. |
| 2 | Mem0 (OSS / self-host) | **no time-lock, no supersession-with-pointer** | heavy on A2/A3 | heavy — would need to build bitemporal layer | moderate | Strong LOCOMO benchmarks, but the conceptual misses on A2/A3 are the exact things hardest to retrofit. Rejected as primary on the same logic v1 used. |
| 3 | Cognee | heavy on A2/A3 | mutate-in-place graph destroys history | heavy — would need versioning layer | minor | memify is pruning, not supersession. Same defect class as Mem0. |
| 4 | Letta / MemGPT | no native time-lock; no supersession-with-pointer | OS-inspired hierarchy is orthogonal to the spec | heavy — retrofit both missing concepts | minor | Agent-framework baggage (server, state) is heavier than the memory problem needs. |
| 5 | MemPalace | conflicting claims; benchmarks doc says "no time-lock, no supersession, no ephemerality"; marketing says validity windows | per docs: everything missing | heavy — would need to build both | minor | Treat as FAIL per benchmarks doc until primary evidence contradicts. Published high LongMemEval number is contested as gamed. |
| 6 | Claude Memory Tool (API) | no semantic search, no time-lock, no supersession | filesystem only | heavy — would need to build a retrieval engine *and* a temporal layer on top | **zero** (it is files) | Filesystem preservation is trivially byte-identical, but then you own the retrieval problem outright. Flipping U1(c) removes the only reason this ranks above #1. |
| — | Zep (managed SaaS) | passes most conceptual criteria | native bitemporal | n/a | n/a | **Disqualified at privacy gate.** Personal health/finance/household data on a third-party SaaS, outside Max coverage, is an auto-reject category. Same reasoning as v1. |
| — | Zep Community Edition | — | — | — | — | **Deprecated April 2025.** Not a live option. |

### 1.3 Shortlist

Only Graphiti is close enough to be worth naming a shortlist. #2 Mem0 is genuinely the second-strongest but the A2/A3 conceptual gap is the single largest cost-of-miss in the table. The difference between #1 and #2 is not close.

### 1.4 Why Graphiti wins on best-fit, not just pass-count

v1 noted Graphiti at 3 PASS / 3 PARTIAL / 1 FAIL. Under best-fit weighting:

- **A2 time-lock** and **A3 supersession** — the two genuinely hard criteria — are **native** (bitemporal `valid_at` / `invalid_at` / `expired_at` / `created_at` on every `EntityEdge`, with pointers between superseding and superseded edges). Every other candidate either lacks the concept or implements it shallowly. This dominates the weighting.
- **S1 scope-integration** — Graphiti's `group_id` is on every node and edge, with `delete_by_group_id`, `get_by_group_ids(limit, uuid_cursor)`, and query-level `group_ids: list[str]` filtering. This is not "a partition we'd need to bolt on" — it is a **first-class primitive** that maps cleanly to scope-of-work.
- **O1 observability** — native OpenTelemetry `Tracer` hook plus per-prompt `TokenUsageTracker`. v1 missed both. The tracer takes spans for every internal operation; the token tracker aggregates input/output tokens by prompt name.
- **U1 upgrade-safe** — the one genuine miss, and it is substrate-leak (criterion written for files). Proposed revision in §4.

---

## 2. Recommended candidate — the case

**Graphiti (getzep/graphiti), graphiti-core ≥ 0.28.2, on embedded Kuzu.** LLM: Anthropic (via Max). Embeddings: Ollama + local 2026-vintage model. Reranker: cross-encoder reranking (Graphiti ships a cross-encoder reranker path; configure to Claude via the Anthropic client).

**Why this shape:**

1. **Apache-2.0, self-hosted, portable.** No vendor lock-in; the data lives in your graph DB. If Graphiti stops development, you still have a schema'd Kuzu graph.
2. **Anthropic-native LLM client.** `graphiti_core/llm_client/anthropic_client.py` is first-class, on par with the OpenAI client. Claude via Max covers every LLM-driven step without vendor-free evaluation.
3. **Ollama for embeddings is the one vendor-free-on-merit call.** Anthropic has no embedding API as of 2026-04-17. Local embedding keeps personal data on-device. Graphiti's `openai_generic_client` accepts Ollama's OpenAI-compatible endpoint.
4. **Kuzu is the right DB for a single-user, five-year store.** Embedded (no server process), columnar (fast point-in-time + BFS traversal at scale), released to 0.11.2+ which Graphiti supports. FalkorDB is a credible fallback if Kuzu maturity disappoints in a prototype; v1 named this correctly.
5. **Recent releases (Jan-Feb 2026) address the chief operational complaints.** v0.26.0 added Sagas (conversation-thread summarisation), v0.27.x added ingest-efficiency work targeting the 600k-tokens-per-conversation complaint flagged in the Vaughan review. v0.28.0 refactored the GraphDriver integrations; v0.28.2 hardened search against Cypher injection. The project is actively maintained with weekly releases.
6. **The published benchmarks are on this engine.** Graphiti is the engine Zep measured with 94.8% DMR and +18.5% LongMemEval vs baselines. Adopting Graphiti is adopting those numbers' substrate.

**Honest operational risks, called out upfront:**

- Graphiti is Python-async. Published integration reports (Saeed Hajebi, Medium) note event-loop conflicts when Graphiti is embedded inline in other async frameworks. The working pattern is to run Graphiti as a separate process with its own event loop — FastAPI microservice or the official MCP server. pOS is Ruby-first; in-process embedding was never the plan. This aligns with the correct pattern, not against it.
- Ingest cost is real. Each episode triggers LLM calls for entity/edge extraction + contradiction resolution. Ingest must be batched and throttled; a pOS ephemerality rubric that *doesn't* go to Graphiti (files, decisions, routine events) materially reduces cost.
- Schema migrations of graphiti-core may require a Kuzu-level migration. The `graphiti_core/migrations/` directory is scaffolded but sparse as of 0.28.2 — the project does not yet ship migration runbooks. This is the operational burden pOS inherits. §5 names the mitigation.

---

## 3. Beyond-spec features — enumerated and tagged

Read the spec's knowledge section — it asks for save/discard, time-lock, supersession, retrieval. Graphiti ships materially more. Each feature below is tagged:

- `adopt-as-new-objective` — belongs in the spec as a new objective; pOS should commit to it.
- `refine-existing-objective` — enhances an existing spec bullet; weave it in as a refinement.
- `capability-available-defer` — useful but not worth absorbing into the spec right now.
- `reject` — at odds with a pOS non-goal or direction.

### 3.1 Data model

| Feature | What it is | Tag | Rationale |
|---------|-----------|-----|-----------|
| **Episode subgraph** — every ingested piece of raw data is a first-class `EpisodicNode`, with every derived fact pointing back to its source episode(s) via `episodes: list[str]` on `EntityEdge` | Provenance-by-construction: every fact carries its derivation chain | **`adopt-as-new-objective`** | pOS spec has "autonomous scope of work" as a primitive but no provenance primitive. This is the observability objective's foundation — you can't replay "why did the system believe X" without source-to-claim links. Make provenance-of-knowledge a first-class primitive. |
| **Custom entity types (Pydantic ontology)** — `entity_types: dict[str, type[BaseModel]]` passed to `add_episode` lets the workspace define its own schema (e.g. `Person`, `Project`, `Decision`) with docstring-driven classification | Structured extraction with user-defined types; supports hybrid-ontology (custom + freeform) or strict-ontology (reject everything that doesn't fit) | **`refine-existing-objective`** | The knowledge-accrual objective says "save non-ephemeral"; this refines it toward "save with type-tagged schema that's workspace-controlled." Aligns with the pOS principle that workspace supplies content, framework supplies contract. |
| **Community subgraph** — periodic label-propagation clustering (not Leiden — chosen for dynamic update) produces community nodes whose summaries aggregate member entities | Higher-level view above raw entities: "who is the owner's inner circle," "what are the live projects," etc. | **`adopt-as-new-objective`** | Summarisation over time is a capability the spec doesn't name. The observability / "why-queries" objective benefits directly — a why-query against "why did you flag the owner's finances as at-risk" can traverse to the community summary, not just raw edges. |
| **Sagas (v0.26.0, Jan 2026)** — rolling LLM-maintained summaries over chains of episodes (threads). `SagaNode` + `HasEpisodeEdge` + `summarize_saga` prompt | Conversation-thread-level summary that updates incrementally as new episodes are added | **`refine-existing-objective`** | Refines the retrieval objective: when retrieval returns N episodes, returning the saga summary rather than the episodes themselves is cheaper and often higher-quality. Also refines session-resilience: a saga is a durable thread representation that survives compaction. |
| **Four temporal dimensions per edge** — `created_at` (ingestion), `valid_at` (real-world true), `invalid_at` (real-world ceased), `expired_at` (logical deletion / versioning) | Bitemporal plus a soft-delete dimension | **`refine-existing-objective`** | Spec's A2 says "time-lock"; the spec is simpler than Graphiti's model. Refine A2 to distinguish ingestion time from real-world time from logical-deletion time — matters for replay fidelity. `expired_at` as a soft-delete preserves audit trail. |
| **`group_id` namespacing** on every node and edge, with bulk partition operations (`delete_by_group_id`, `get_by_group_ids(limit, uuid_cursor)`) | First-class partitioning with cursored iteration | **`refine-existing-objective`** | The spec's S1 says "scope integration." Refine: adopt `group_id` as the canonical scope-partition primitive in pOS memory. Map scope-of-work ID directly to `group_id`; cross-scope queries pass a list. |

### 3.2 Retrieval

| Feature | What it is | Tag | Rationale |
|---------|-----------|-----|-----------|
| **Three rerankers (RRF, MMR, cross-encoder)** applicable to all three search scopes (nodes, edges, communities) | Reciprocal rank fusion, maximal marginal relevance (diversity-aware), LLM cross-encoder | **`refine-existing-objective`** | Spec's R1 says "retrieval quality." Refine: retrieval is a configurable stack with named rerankers. MMR specifically matters for the pOS anti-bloat principle — diversity prevents retrieval collapse where the top-5 are near-duplicates. |
| **Pre-made search recipes** (`NODE_HYBRID_SEARCH_RRF`, `COMBINED_HYBRID_SEARCH_CROSS_ENCODER`, `EDGE_HYBRID_SEARCH_NODE_DISTANCE`, and a dozen more) | Named configurations bundling search scope + retrieval method + reranker | **`capability-available-defer`** | Good to know. Not an objective. |
| **Node-distance reranking** (`center_node_uuid` / `focal_node_uuid`) — prioritises results near a given node in the graph | Proximity-aware retrieval; "what do I know about topics near this person/project" | **`adopt-as-new-objective`** | The spec doesn't have graph-proximity retrieval. This is the mechanism that enables "when the owner asks a specialist about a project, preferentially surface memory near that project entity." New objective: **context-aware retrieval keyed on active scope entities.** |
| **Multi-hop BFS traversal** inside the hybrid search | Walk edges from matched entities to find related facts | **`refine-existing-objective`** | Refinement to R1: retrieval must support multi-hop, not just semantic-top-k. |
| **`reference_time` parameter** on historical queries | Query the graph state as of time T | **`refine-existing-objective`** | The spec's O1 asks for replay-at-T; this is how it works mechanically for knowledge-state replay. Refine O1 to reference the mechanism: `reference_time` for knowledge, git commit for config, event log replay for actions. |

### 3.3 Operational

| Feature | What it is | Tag | Rationale |
|---------|-----------|-----|-----------|
| **OpenTelemetry tracer hook** (`tracer: Tracer`, `trace_span_prefix` constructor args) | Every internal Graphiti operation emits an OTel span | **`adopt-as-new-objective`** | This is a full observability plumbing channel — not just event-log writes but structured spans for every DB/LLM round-trip. Adopt OTel as the cross-component observability standard, with pOS's event log as one sink. |
| **`TokenUsageTracker`** — per-prompt-type aggregation of input/output tokens, thread-safe, queryable | Cost visibility broken down by prompt name ('extract_nodes.extract_message', etc.) | **`adopt-as-new-objective`** | Maps directly to the cost-governance spec objective. Per-prompt aggregation is more useful than per-session — you can see which prompt is eating tokens and tune it, not just that the bill was high. |
| **`store_raw_episode_content: bool`** flag | Trade storage for privacy — don't persist raw text, only derived structure | **`adopt-as-new-objective`** | This is a privacy-governance primitive the spec doesn't have. Some episodes should not persist raw text (health intake, financial statements); derived structured facts can persist, raw text must be droppable. New objective: **per-episode retention class.** |
| **`SEMAPHORE_LIMIT` concurrency control** (env var + `max_coroutines` constructor arg) | Throttle LLM calls to respect rate limits | `capability-available-defer` | Useful at wiring time; not an objective. |
| **MCP server** (official, at `mcp_server/`) with tools `add_episode`, `search_nodes`, `search_facts`, `delete_entity_edge`, `delete_episode`, `get_entity_edge`, `get_episodes`, `clear_graph`, `get_status` | Native MCP interface Claude can call as tools | **`refine-existing-objective`** | The pOS integration path is MCP. Refine the primary-persona primitive: the persona talks to memory via MCP tools, not via a Ruby-native binding. This avoids the Python-async-integration problem entirely. |
| **Cypher-injection hardening** (0.28.2 security release) | Search filters validated against Cypher injection | `capability-available-defer` | Good that it exists. |
| **GLiNER NER client** (`gliner2_client.py`) | Deterministic (non-LLM) entity extraction option for some prompts | **`capability-available-defer`** | Aligns with deterministic-first. Not in scope for first prototype but worth remembering when LLM cost is a problem. |

### 3.4 Ingestion and resolution

| Feature | What it is | Tag | Rationale |
|---------|-----------|-----|-----------|
| **Automatic contradiction resolution** — on ingest, LLM-driven reconciliation: if a new edge contradicts an existing one, the older is invalidated (`invalid_at` set) with a pointer to the superseding edge | Supersession happens automatically, not by user annotation | **`refine-existing-objective`** | Spec's A3 presumes manual supersession. Refine: "supersession is automatic by default, with user override available; every supersession event is audited." |
| **Dedup utilities** (`dedupe_nodes_bulk`, `dedupe_edges_bulk`) | First-class deduplication, not just on ingest but runnable as a maintenance op | **`capability-available-defer`** | Maintenance mechanics; not spec-worthy. |
| **Episode chain via `NextEpisodeEdge`** | Episodes carry explicit "next" edges — the raw sequence is preserved as a chain | **`refine-existing-objective`** | Refines O1 (replay) and A2 (time-lock) — the raw event chain is reconstructible in order, separate from the semantic extraction. |
| **Bulk ingest** (`add_episode_bulk`) | Batched ingest path for large imports | `capability-available-defer` | Useful for one-time seed ingest. |

### 3.5 Nothing rejected

Nothing in Graphiti's beyond-spec surface conflicts with a pOS non-goal. The two risks — multi-LLM-vendor baggage and SaaS lock-in — are both avoided by the self-hosted + Anthropic-client-only configuration.

---

## 4. Gap handling — spec criteria the recommended candidate misses

Ordered by severity. For each, the three handling options per the v2 plan.

### 4.1 U1(c) — "memory/daily entries (or equivalent) are byte-identical to pre-upgrade"

**The miss:** Graphiti stores memory in a graph DB, not as flat files. Byte-identity applies only at the DB-file level, which upgrades of graphiti-core may legitimately alter (schema migrations, index changes). Byte-identity is the wrong metric for a DB-backed store.

**Severity:** Substrate-leak. The criterion was written while the existing `memory/` directory was in scope. Near-zero penalty in best-fit weighting.

**Handling options:**

- **(a) Accept the gap.** Adopt Graphiti; accept that upgrade fidelity is tested semantically (round-trip: ingest→query equivalence pre- and post-upgrade) not by `diff`. Practical workaround: snapshot the Kuzu DB directory before every upgrade so that the state is physically recoverable even when byte-identity at the memory-entry level is not guaranteed. Reversibility (U1(f)) is preserved by the snapshot.
- **(b) Revise the spec.** Proposed wording for U1(c): *"memory state is preserved across upgrades without content loss or semantic corruption, verified by a round-trip fidelity test: a snapshot of queries over a representative probe set returns the same results pre- and post-upgrade (modulo explicitly-documented schema-migration consequences)."* This captures the intent ("memory isn't destroyed or corrupted by upgrading pOS") without the substrate-specific expression. **This is the recommended option.**
- **(c) Flag for the owner.** Only if he wants to hold byte-identity as the bar, which rules out every graph-DB-backed candidate and returns the problem to a flat-file build — struck by v2.

**Recommended:** (b). Revise U1(c) as above. If the owner prefers (a), the adopt-Graphiti path still works; the spec remains unchanged but a known-compromise note is added alongside the criterion.

### 4.2 A1(a) — "a defined ephemerality rubric decides what is saved vs discarded"

**The miss:** Graphiti's default behaviour is LLM-driven extraction from whatever you feed it. It has no user-authored ephemerality filter at the pre-ingest layer. Anything you call `add_episode` with gets processed; anything you don't, doesn't.

**Severity:** Adaptation-cost miss — the mechanism isn't in Graphiti, but it belongs at the pOS layer, not the engine layer. Light penalty.

**Handling options:**

- **(a) Accept the gap.** Treat every pOS event as a potential episode; rely on Graphiti's extraction-to-discard to filter noise. Cost-expensive (every event hits an LLM call). Fails the "sampled batch of ephemeral-class data is confirmed absent from storage" sub-test because extraction may produce zero entities but the episode is still stored.
- **(b) Revise the spec.** Not warranted — the criterion is right. A1 is a genuine pOS objective independent of substrate.
- **(c) Flag for the owner.** Not warranted — this is a glue-layer job.

**Resolution (not a the owner decision):** pOS builds a **pre-ingest ephemerality filter** at the workspace layer, between event capture and `add_episode`. Workspace-authored YAML rules (hand-authored for common cases — code blocks, arithmetic, routine completion noise) plus a Claude-as-judge fallback for ambiguous cases, each decision audited to a rubric-audit log. v1 §5 named this; v2 confirms: it's ~10-15 AI-time min and lives in pOS, not Graphiti.

### 4.3 R1 — "retrieval surfaces relevant knowledge with measured precision/recall"

**The miss:** Graphiti has published benchmarks (94.8% DMR, +18.5% LongMemEval vs baselines) but those are not on pOS's content. pOS has no test set. The criterion "measured precision/recall" cannot be evaluated without one.

**Severity:** Not a Graphiti miss — it's a pOS preparation miss. No penalty to Graphiti.

**Handling options:**

- **(a) Accept the gap.** Trust published benchmarks. Not recommended: the owner's content (task records, decisions, entity cards) is shape-different from chat-corpus QA on LongMemEval.
- **(b) Revise the spec.** Not warranted.
- **(c) Flag for the owner.** Not warranted — it's a pOS-owned deliverable.

**Resolution:** pOS commissions a retrieval test set of 50-100 query/expected-result pairs drawn from the owner's actual past sessions before the memory system is declared production. Targets: precision@5 ≥ 0.8 for recall-style questions, ≥ 0.9 for entity-lookup. Run at every graphiti-core minor version bump; regression is a blocker for upgrade. This is the *single highest-value prototype deliverable* (see §7).

### 4.4 S1 — scope-of-work as a primitive concept

**The miss:** Graphiti's `group_id` is a flat partition identifier. The pOS scope-of-work primitive carries goal, budget, reversibility class, observers, escalation triggers — none of which exist in Graphiti.

**Severity:** Conceptual vs adaptation is a question of where scope-of-work lives. If scope metadata is a pOS-side primitive stored in an event log / sidecar DB and Graphiti holds only the memory side, `group_id` is an acceptable foreign-key to that pOS primitive. Under that split: adaptation-cost miss, not conceptual.

**Handling options:**

- **(a) Accept the gap.** pOS owns the scope-of-work primitive (probably in SQLite). Graphiti's `group_id` is set to the scope's UUID. Memory operations within a scope pass the scope's `group_id`; cross-scope queries pass a list. `created_by_scope` and `observed_in_scope` attribution patterns sit on top of Graphiti's native partition. **This is the recommended option.**
- **(b) Revise the spec.** Not warranted — scope-of-work is a real pOS primitive independent of memory.
- **(c) Flag for the owner.** Not warranted.

**Resolution:** (a). Build a `scope ↔ group_id` mapper at the pOS layer. ~5-10 AI-time min for the mapping logic, plus attribution fields on every memory write.

### 4.5 O1 — observability (actor, objective-cited fields)

**The miss:** Graphiti's native telemetry gives tracer spans + token usage, but not "actor" (which pOS persona initiated the operation) and not "objective cited" (which scope objective drove the operation). Those are pOS-layer semantics Graphiti doesn't know about.

**Severity:** Adaptation-cost miss. Graphiti emits the spans; pOS decorates them with workspace context.

**Handling options:**

- **(a) Accept the gap.** pOS wraps every Graphiti MCP call with a pOS event-log entry capturing (actor, timestamp, objective, operation, inputs, outputs). Graphiti's tracer and token-tracker feed a sub-record into the same event log. Audit completeness tested via the sampled-reconstruction test from the spec. **Recommended.**
- **(b) Revise the spec.** Not warranted.
- **(c) Flag for the owner.** Not warranted.

**Resolution:** (a). The pOS observability primitive wraps memory ops, using Graphiti's OTel tracer as the internal-operation layer. This is glue, ~10 AI-time min to wire.

### 4.6 Summary of gap handling

No criterion requires a halt. Recommended spec revision: **U1(c) byte-identical → semantic-preserved, round-trip verified.** All other gaps resolve at the adapter layer with straightforward glue.

---

## 5. Adaptation scope — what pOS must build around Graphiti

Eight glue components, all at the pOS layer. AI-time estimates per rule 15 anchors. Honest — the surprises are called out.

| # | Component | What it does | AI-time | Surprise? |
|---|-----------|--------------|---------|-----------|
| 1 | **Ephemerality filter** | Workspace-authored YAML rule set + Claude fallback; audit log of save/discard decisions | 10-15 min | No |
| 2 | **Scope-mapper** | Scope-of-work UUID → `group_id`; attribution fields (`created_by_scope`, `observed_in_scope`) on every write | 5-10 min | No |
| 3 | **Event-log wrapper** | Wraps Graphiti MCP calls; emits `(actor, ts, objective, op, inputs, outputs)` to pOS event log; pulls in OTel spans + token usage as sub-records | 10-15 min | No |
| 4 | **Graphiti MCP hosting** | Run the Graphiti MCP server as a managed local service (launchd entry, health check, restart policy) | 10-15 min | Minor — this is the cleanest way to avoid the Python-async integration pain |
| 5 | **Upgrade-fidelity test harness** | Pre-upgrade probe set + post-upgrade query replay; compares results and reports drift | 15-20 min | Yes — this is what the revised U1(c) is tested against. Must exist before first upgrade. |
| 6 | **Retrieval test set** | 50-100 Q/A pairs from the owner's actual past sessions; runs as a gate at every graphiti-core bump | 20-30 min | **Yes — the biggest surprise.** the owner should own curation; automation can only go so far. This is the single item most worth prototyping first. v1 also flagged this. |
| 7 | **Kuzu snapshot runbook** | `pre-upgrade-snapshot` and `rollback-to-snapshot` commands; stored as a tarball under a versioned path | 10 min | No |
| 8 | **Pre-ingest tagger** | Optional: workspace-custom Pydantic entity types (Person, Project, Decision, Task, Transaction) passed to `add_episode(entity_types=...)` — narrows extraction to the pOS ontology | 10-15 min | No, but worth considering upfront — Graphiti supports hybrid-ontology, so freeform extraction still happens for anything outside the custom types |

**Total: 90-130 AI-time minutes.** Within 15% of v1's estimate. The surprise isn't the glue count; it's the **test set** (#6) and the **upgrade-fidelity harness** (#5). Both are test-set-curation work, which is AI-resistant — the owner must review candidates even if agents draft them.

**Not in scope of the build:**

- No Graphiti fork. The configuration surface covers everything the spec needs. If it doesn't, raise upstream as a feature request; don't fork.
- No custom DB driver. Kuzu is an officially-supported backend.
- No custom LLM client. `anthropic_client.py` is first-class.

---

## 6. Dependency map

```
                                ┌──────────────────────────────┐
                                │   scope-of-work (pOS)        │
                                │   goal, budget, observers,   │
                                │   escalation, group_id       │
                                └────┬─────────────────┬───────┘
                                     │                 │
                               writes group_id     reads scope context
                                     v                 v
         ┌──────────────────────────────────────────────────────┐
         │   Graphiti MCP service (local process, launchd)      │
         │                                                       │
         │   add_episode(text|json|message, group_id,           │
         │               reference_time, entity_types)          │
         │   search(query, group_ids, center_node_uuid,         │
         │          search_recipe, reference_time)              │
         │                                                       │
         │   ┌─────────────────┐    ┌─────────────────────┐     │
         │   │ Claude (Max)    │<-->│ Ollama (local)      │     │
         │   │ LLM inference   │    │ embeddings          │     │
         │   └─────────────────┘    └─────────────────────┘     │
         │             │                                         │
         │             v                                         │
         │   ┌──────────────────────────────────────────────┐   │
         │   │ Kuzu (embedded) — graph store of record      │   │
         │   │   episodes, entities, edges, sagas,          │   │
         │   │   communities, group_id partitions           │   │
         │   └──────────────────────────────────────────────┘   │
         └──────────┬───────────────────────────┬──────────────┘
                    │                           │
           OTel tracer spans       pOS event-log wrapper
           + TokenUsageTracker     (actor, objective, op, I/O)
                    │                           │
                    v                           v
         ┌──────────────────────────────────────────────────┐
         │   Observability / replay (pOS)                   │
         │   - appends to event log                         │
         │   - supports replay-at-T via reference_time      │
         │   - cost attribution via token tracker           │
         └──────────────────────────────────────────────────┘
                    ^                           ^
                    │                           │
         ┌──────────┴───────────────────────────┴──────────┐
         │   primary persona (workspace-supplied)          │
         │   invokes memory via MCP tools every turn:      │
         │     - pre-turn active-recall (search)           │
         │     - post-turn ingest (add_episode, filtered   │
         │       through the pOS ephemerality filter)      │
         └──────────────────────────────────────────────────┘
                    ^
                    │
         ┌──────────┴──────────────────────────────────────┐
         │   self-upgrade (pOS)                            │
         │   - Kuzu snapshot before upgrade                │
         │   - graphiti-core version pin bump              │
         │   - upgrade-fidelity probe replay               │
         │   - rollback on fidelity-test regression        │
         └──────────────────────────────────────────────────┘
```

### 6.1 Directional notes

- **Scope-of-work → Graphiti:** one-way. Memory ops carry scope's `group_id`; scope does not own memory content.
- **Primary persona ↔ Graphiti:** bidirectional every turn — pre-turn search, post-turn ingest. Latency-critical path. Local Ollama + Kuzu + local MCP keeps the round-trip off the network.
- **Observability ← Graphiti:** one-way. Graphiti emits tracer + token usage; pOS event log consumes.
- **Self-upgrade → Graphiti:** one-way with veto. pOS upgrade process gates on the fidelity test; Graphiti never initiates its own upgrade.

### 6.2 Where the design is pressured

- **Hot path is persona ↔ memory.** Pre-turn retrieval latency must be < 500ms p95, or every persona interaction feels laggy. Local embedding + local Kuzu is non-negotiable for this.
- **Cold path is ingest.** Batch, throttle, filter. Use the pOS ephemerality rubric to keep LLM-call volume bounded. Token tracker makes cost visible.
- **Upgrade gate is the quiet dependency.** Without the fidelity probe set, upgrade is blind. Build the probe before the first production upgrade, not after.

---

## 7. Prototyping priorities

Four questions only a prototype can answer, ordered by value-of-information.

### 7.1 Does Graphiti's retrieval quality hold on pOS content? **[highest value]**

Published benchmarks are on chat corpora. the owner's content is task-records + decisions + entity cards.

- **Build:** 50-100 Q/A pairs from the owner's actual past sessions (one-time read of existing `memory/daily/` per the research plan's permitted-factual-reading clause). Categories: entity-lookup ("which lawyer did we use for X"), decision-recall ("what did we decide about HELOC refi last month"), temporal ("who did I meet with in March 2026"), multi-hop ("what projects are blocked on missing people"), supersession ("what is the owner's current employer").
- **Measure:** precision@5, recall@5 per category; note categories where Graphiti's hybrid underperforms.
- **Decision:** if precision@5 < 0.7 on any category, identify whether the gap is retrieval config (try different search recipes, try cross-encoder reranking with Claude) or fundamental (flag to the owner — at that point consider whether a pre-turn pOS-side reranking layer is needed).
- **AI-time:** 20-30 min to build the set, 5 min to run. the owner curates.

### 7.2 Is local Ollama embedding fast enough? **[latency-critical]**

- **Target:** embed + hybrid search + cross-encoder rerank < 500ms p95 on the owner's laptop.
- **Setup:** Ollama + Qwen3 (or bge-large); a 1000-query-warm test.
- **Decision:** if p95 > 500ms, try smaller/quantised model; if still too slow, fall back to sentence-transformers or relax the latency target.
- **AI-time:** 10 min to wire, 5 min to run.

### 7.3 Is Kuzu stable under load and adverse conditions? **[durability]**

- **Setup:** ingest 1000 episodes over an hour; hard-kill the Kuzu process five times mid-ingest; verify no corruption post-restart.
- **Control:** same test with FalkorDB.
- **Decision:** pick the more durable under chaos. v1 called Kuzu primary; this prototype falsifies or confirms.
- **AI-time:** 15-20 min.

### 7.4 Does the ephemerality rubric hold? **[rubric calibration]**

- **Setup:** run one week of pOS events through the rubric in **audit-only mode** — every classification is logged, nothing is actually discarded. At week end, review discard candidates manually.
- **Decision:** refine the rules based on false-positives and false-negatives. No discarding until the rubric has a clean audit week.
- **AI-time:** 10 min to wire audit-only mode. One week elapsed-time for the signal to accumulate.

### 7.5 Test-set design — v1's chief open question, addressed

v1 flagged that there is no pOS-representative retrieval test set and called its absence the single most important open question. v2 confirms and sharpens:

- The test set is the **acceptance criterion for R1**. Without it, R1 is an assertion.
- The test set is also the **upgrade gate**. Every graphiti-core minor version bump runs it; regression blocks upgrade.
- Curation is the owner-owned. Agents can draft from past sessions, but the owner must judge whether a given pair is a fair query.
- The set is versioned in the workspace, not in Graphiti's repo — it is pOS content, not framework content. Per the CLAUDE.md "workspace-specific content" designation.

---

## 8. Spec revisions proposed

Consolidated from §3 (beyond-spec tags) and §4 (gap handling). the owner to accept/reject each independently.

### 8.1 U1(c) — byte-identity → semantic-preserved

**Current:** "memory/daily entries (or equivalent) are byte-identical to pre-upgrade."

**Proposed:** "memory state is preserved across upgrades without content loss or semantic corruption, verified by a round-trip fidelity test: a probe set of representative queries returns equivalent results pre- and post-upgrade, modulo explicitly-documented schema-migration consequences. Reversibility (U1(f)) is preserved via a pre-upgrade snapshot of the memory substrate regardless of semantic-level drift."

**Why:** removes the substrate leak; tests the thing that actually matters (replay fidelity, not bit-level identity).

### 8.2 A2 — time-lock becomes temporally explicit

**Current (derived):** "the knowledge state at an arbitrary past time T is reproducible."

**Proposed refinement:** every knowledge entry carries four temporal dimensions — ingestion time (`created_at`), real-world validity-start (`valid_at`), real-world validity-end (`invalid_at`), and logical-deletion-time (`expired_at`). Time-lock queries distinguish between "what did we know at T" (ingestion-time) and "what was true at T" (valid-at). Both are reproducible.

**Why:** the two different "times" are materially different and pOS uses both. The current spec blurs them.

### 8.3 A3 — supersession becomes automatic-by-default

**Current (derived):** "superseded entries carry an explicit supersession marker and a pointer to the superseding entry."

**Proposed refinement:** supersession resolution is **automatic on ingest** via LLM-driven contradiction detection; every automatic supersession is logged and reversible via the observability layer. User override (manual supersession, manual un-supersession) is available but not the default path.

**Why:** manual supersession doesn't scale to a high-ingest personal OS. Automatic-with-audit is the shape Graphiti implements and the right posture for pOS.

### 8.4 New objective — provenance of knowledge

**Proposed new objective under Knowledge:** every derived fact points back to the raw source(s) it was derived from. Retrieval can surface sources alongside claims; "why do we believe X?" is a first-class query, not a reconstruction from the event log.

**Why:** Graphiti's episode subgraph gives this for free; the spec should claim it.

### 8.5 New objective — context-aware retrieval

**Proposed new objective under Knowledge:** retrieval is keyed to active scope context — results are reranked by graph proximity to the entities the scope is operating on, not only by query similarity.

**Why:** this is node-distance reranking. It's the mechanism that makes "relevant at the right time" actually work, because "the right time" is scope-specific.

### 8.6 New objective — per-episode retention class

**Proposed new objective under Knowledge (privacy-adjacent):** each episode has a retention class declared at ingest time: `retain-raw-and-derived` (default), `retain-derived-only` (discard raw text after extraction), or `ephemeral` (filtered out by the rubric). Raw-discard is auditable — the retention decision is logged.

**Why:** sensitive episodes (health, finance, relationship-substantive) should be representable as structured facts without the raw text persisting. Graphiti's `store_raw_episode_content: bool` is episode-level and supports this.

### 8.7 Refinement — Observability adopts OpenTelemetry

**Proposed:** pOS observability primitive exposes OpenTelemetry spans as the internal-operation trace format. The pOS event log is one OTel sink; other sinks (a local viewer, a long-term archive) are pluggable.

**Why:** Graphiti already emits OTel; adopting OTel at the pOS layer means memory observability is free, and other components can plug in under the same standard. Tier: foundational — this change affects many components, not just memory.

### 8.8 Refinement — Cost governance adopts per-prompt tracking

**Proposed:** cost budgets are tracked per prompt-type, not only per scope/session. Aggregation is thread-safe and queryable; overruns per prompt-type surface before the scope budget is exhausted.

**Why:** Graphiti's `TokenUsageTracker` pattern is strictly more useful than scope-level-only aggregation. When a budget is exceeded, you want to know which prompt was expensive, not just that *something* was.

---

## 9. Constraints re-stated — what sits inside vs outside Max

Per the research plan's max-first, vendor-free-outside-Max framing.

**Inside Max (Claude-only, no vendor evaluation):**

- Entity extraction, edge extraction, contradiction resolution, saga summarisation, community summarisation, ephemerality-rubric fallback, cross-encoder reranking. All use the `anthropic_client.py` driver.
- Any LLM-as-judge evaluation step (test-set grading, etc.).

**Outside Max (vendor-free on merit):**

- **Embeddings.** No Anthropic embedding API as of 2026-04-17. Recommendation: local Ollama + Qwen3 or bge-large. Privacy-local, no cloud calls, 90% of Voyage-3 quality for single-user personal content. Backup: sentence-transformers.
- **Graph DB.** Kuzu primary (embedded, columnar, Graphiti-supported ≥ 0.11.2). FalkorDB fallback if Kuzu durability disappoints.
- **Cross-encoder reranker (if not via Claude).** Graphiti ships Gemini and OpenAI cross-encoder clients; the Anthropic cross-encoder route uses the same `CrossEncoderClient` interface with Claude's structured-outputs GA support. Preferred: route cross-encoder via Claude inside Max. If latency is a problem, a local cross-encoder is the vendor-free fallback.

---

## 10. Summary

**Best-fit recommendation:** Graphiti (getzep/graphiti, graphiti-core ≥ 0.28.2) on embedded Kuzu, Claude via Max for all LLM steps, local Ollama embeddings.

**Best-fit rationale:** only candidate with native bitemporal time-lock + pointered supersession + first-class group-based partitioning + Anthropic LLM driver; active weekly releases in 2026; Apache-2.0; self-hostable; published benchmarks.

**One spec revision recommended:** U1(c) byte-identical → semantic-preserved. Other revisions proposed (§8) are refinements and new objectives drawn from Graphiti's beyond-spec surface — take or leave per owner's judgment.

**Top beyond-spec features worth absorbing as new pOS objectives:**

1. **Provenance of knowledge** (episode subgraph — every fact points to its source).
2. **Context-aware retrieval** (node-distance reranking keyed on active scope entities).
3. **Per-episode retention class** (`retain-raw`, `retain-derived`, `ephemeral`).
4. **OTel-based observability** (framework-level, beyond memory).
5. **Per-prompt cost tracking** (framework-level, beyond memory).

**Adaptation scope:** ~90-130 AI-time minutes for eight glue components at the pOS layer. No Graphiti fork. The two surprises are the retrieval test set and the upgrade-fidelity probe set — both test-set curation work that the owner must own.

**Prototype priorities, in order:** (1) retrieval quality on pOS content; (2) Ollama embedding latency; (3) Kuzu durability under chaos; (4) ephemerality-rubric audit-only week.

**No halt signal.** v1's halt on U1(c) resolves via spec revision 8.1.

---

## Sources

### Primary (code)

- Graphiti repo: `github.com/getzep/graphiti` — `graphiti_core/graphiti.py`, `graphiti_core/edges.py`, `graphiti_core/namespaces/nodes.py`, `graphiti_core/llm_client/token_tracker.py`, `graphiti_core/prompts/summarize_sagas.py`, `graphiti_core/migrations/`, `graphiti_core/tracer.py`
- Releases read: v0.26.0 (Sagas, 2026-01-16), v0.27.0 (ingest efficiency, 2026-02-11), v0.28.0 (GraphDriver refactor, 2026-02-17), v0.28.2 (Cypher-injection hardening, 2026-03-11)

### Primary (docs)

- [Graphiti README — capability enumeration](https://github.com/getzep/graphiti)
- [Graphiti search documentation](https://help.getzep.com/graphiti/working-with-data/searching)
- [Custom Entity and Edge Types — Zep Documentation](https://help.getzep.com/graphiti/core-concepts/custom-entity-and-edge-types)
- [How do you search a Knowledge Graph — Zep blog](https://blog.getzep.com/how-do-you-search-a-knowledge-graph/)
- [ZEP paper — Temporal Knowledge Graph Architecture for Agent Memory (Jan 2025)](https://arxiv.org/abs/2501.13956)
- [Graphiti MCP server](https://github.com/getzep/graphiti/tree/main/mcp_server)

### Secondary (reviews and operational reports)

- [Graphiti: Should the Knowledge Flywheel Use It? (Vaughan, Mar 2026)](https://codex.danielvaughan.com/2026/03/30/graphiti-agent-memory-store/)
- [A Production-Ready API for Graphiti's Powerful but Flawed Memory (Hajebi, Medium)](https://medium.com/@saeedhajebi/a-production-ready-api-for-graphitis-powerful-but-flawed-memory-15f17a9c1b41)
- [Claude structured outputs GA](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

### Inherited from v1

- v1's primary-source survey (Letta, Zep, Mem0, Cognee, MemPalace, Claude Memory Tool, Claude Code memory) — `components/memory-system/research.md` §1.2. Accepted as input evidence per plan.
