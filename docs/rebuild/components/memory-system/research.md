# Memory System — Research

**Component:** Memory System. **Phase:** Research (no design, no code).
**Authored by:** Research Agent. **Date:** 2026-04-17.
**Input brief:** `docs/rebuild/components/memory-system/research-plan.md`
**Spec scored against:** `docs/rebuild/spec/pos-v2-objectives-spec.md` v1.0 (LOCKED).

---

## 0. Reading guide

This document answers the plan's questions. The existing-solutions survey leads. A halt-and-signal is raised at the end of §1 — no existing solution satisfies the full spec as-is, and the build-from-scratch evaluation in §§2–8 identifies one spec clause that *cannot* be satisfied by any available mechanism today (clause (c) of the self-upgrade acceptance criterion as applied to embedding state). This clause must be renegotiated before a proposal is authored. Everything else proceeds.

A note on verification honesty: every claim below carries a provenance. `[verified]` means I read the primary source (docs, repo README, arxiv paper). `[secondary]` means a single authoritative third-party source (Neo4j blog, FalkorDB docs). `[inferred]` means I reasoned from partial evidence — treat with caution. Where sources disagreed I name the disagreement rather than picking.

---

## 1. Existing-solutions survey (leading section)

### 1.1 What the spec actually requires

The memory system must satisfy every behaviour-level acceptance criterion under *Knowledge — accrual and retrieval, as separate concerns* (addendum 2026-04-17 14:21 CDT). Transcribing them as scoring rows:

| ID | Criterion (derived from spec behaviours) |
|----|-----|
| **A1** | **Save-non-ephemeral** — a defined ephemerality rubric decides what is saved vs discarded; a sampled batch of ephemeral-class data is confirmed absent from storage. |
| **A2** | **Time-lock** — the knowledge state at an arbitrary past time T is reproducible. |
| **A3** | **Overridable by later knowledge (supersession)** — superseded entries carry an explicit supersession marker and a pointer to the superseding entry; retrieval excludes superseded entries from active context unless explicitly time-scoped. |
| **R1** | **Retrieve the right thing at the right time** — retrieval surfaces relevant knowledge with measured precision/recall; this is the user-facing quality dimension. (From the top-level "knowledge recall" objective; the spec does not give a specific numeric target but requires the separation of accrual and retrieval failure modes, per the review's tension #3.) |
| **U1** | **Self-upgrade preservation** — after framework upgrade, memory/daily entries (or equivalent) are byte-identical to pre-upgrade; upgrade is itself reversible; every upgrade change is verifiably installed or surfaces a conflict. (Cross-cutting; applies to whichever substrate memory chooses.) |
| **O1** | **Observability** — every autonomous memory operation writes a record containing actor, timestamp, objective cited, inputs, outputs; audit log completeness is sample-verifiable; replay must reproduce the knowledge state available at a past moment. |
| **S1** | **Scope integration** — memory must either be scoped-per-scope-of-work or readable/writable from a scope with attribution. |

### 1.2 Candidate inventory

Active, maintained LLM-harness memory solutions as of 2026-04-17:

1. **Letta / MemGPT** — agent framework with OS-inspired memory hierarchy (core / archival / conversational). Apache-2.0. Claude-supported as LLM, but no Anthropic embedding model. [verified]
2. **Zep (managed SaaS)** — hosted memory platform, $14/mo+ pricing tiers. Bitemporal knowledge graph via Graphiti under the hood. [verified]
3. **Graphiti** — Zep's open-source temporal knowledge graph engine. Apache-2.0. Bitemporal model (event-time + ingestion-time). Supports Anthropic LLM + Ollama/Voyage/OpenAI/Gemini embeddings. Requires Neo4j / FalkorDB / Kuzu / Neptune. [verified]
4. **Mem0** — hybrid graph + vector + kv store. Apache-2.0, self-hostable, cloud variant also offered. Multi-vendor; default OpenAI embeddings. No documented time-locking/supersession. [verified]
5. **Cognee** — knowledge graph + vector pipeline; "memify" self-refinement. Apache-2.0. Claude Code plugin exists. No documented time-locking or supersession. [verified]
6. **MemPalace** (Jovovich/Sigman, April 2026) — verbatim storage + semantic search with pluggable ChromaDB backend. MIT. Contains "temporal entity-relationship graph with validity windows" per one source; the benchmarks doc explicitly denies any time-locking / supersession / ephemerality implementation. Sources disagree; more below. [verified with caveat]
7. **Claude Memory Tool (API)** — Anthropic-native file-based memory primitive. Client-side storage, user-controlled. Claude decides what to write via tool calls. No built-in time-lock or supersession — it is a filesystem, not a knowledge store. [verified]
8. **Claude Code memory (CLAUDE.md + auto-memory)** — native instruction files + auto-generated notes. Context-engineering primitive, not a knowledge base. No time-lock, no supersession, no retrieval layer. [verified]
9. **Zep Community Edition** — **deprecated April 2025**, no longer maintained. Not a live option. [verified]
10. **claude-mem** (third-party plugin, 46k stars) — session context compression + replay for Claude Code. Not a knowledge-store primitive; orthogonal to this research. [verified]

### 1.3 Solutions-by-criteria table

Scoring key: **PASS** = implemented and meets the criterion as written. **PARTIAL** = present but requires material adaptation or has a gap. **FAIL** = not present; would require substantial build to add. **N/A** = category doesn't apply (e.g. substrate is user's filesystem).

| Solution | A1 ephemerality | A2 time-lock | A3 supersession | R1 retrieval quality | U1 upgrade-safe | O1 observability | S1 scope-integration |
|---|---|---|---|---|---|---|---|
| **Letta / MemGPT** | PARTIAL — Claude-curated eviction from core→archival acts as a de-facto rubric, but not user-auditable | FAIL — no bitemporal or versioned query | FAIL — archival is a vector store with no explicit supersession edges | PARTIAL — archival search + hierarchy is a reasonable baseline but no published benchmarks matching spec rigor | FAIL — tied to Letta server state; upgrade path for memory store not a documented guarantee | PARTIAL — logs agent steps; not specifically a knowledge-replay primitive | FAIL — multi-agent shared memory exists (Conversations API Jan 2026) but "scope" as pOS defines it is absent |
| **Zep (SaaS)** | PARTIAL — LLM-extracted facts with implicit filtering; no user-authored rubric | PASS — bitemporal model supports point-in-time query | PASS — tvalid/tinvalid edges encode supersession with a pointer | PASS — 94.8% DMR, +18.5% LongMemEval vs baselines [verified from arxiv] | FAIL — SaaS; data lives on Zep's servers; violates Max-first + privacy-for-personal | N/A — Zep manages the store | PARTIAL — "group" / "user" scopes exist but are not pOS scope-of-work |
| **Graphiti (OSS)** | PARTIAL — same as Zep; LLM-driven fact extraction, rubric implicit | PASS — bi-temporal edges; `reference_time` parameter documented | PASS — invalidation-by-setting-`tinvalid`, preserves history | PASS (inferred) — same engine as Zep; score carries over | PARTIAL — requires external graph DB (Neo4j/FalkorDB/Kuzu); backup = DB backup; upgrade of Graphiti-core version ≠ re-ingest; schema migrations in the DB are a genuine risk | PARTIAL — writes are transactional in the graph DB; replay requires re-querying with reference_time | FAIL — no scope primitive; would need workspace-layer mapping |
| **Mem0** | FAIL — "ADD/UPDATE/DELETE/NOOP" heuristic, no user-authored rubric, no ephemerality audit | FAIL — no bitemporal model; updates overwrite | PARTIAL — UPDATE semantics exist but no time-travel; history is lost | PARTIAL — strong benchmarks on LOCOMO but no temporal dimension | PARTIAL — self-hostable but default cloud; local variant depends on user's vector DB choice | PARTIAL — memory events logged but replay-at-T is not supported | FAIL — no scope primitive |
| **Cognee** | PARTIAL — memify "prunes stale nodes", but not a deterministic rubric | FAIL — memify mutates the graph; no validity intervals documented | FAIL — no documented supersession marker | PARTIAL — graph+vector hybrid, benchmarks less published | PARTIAL — self-hostable; multiple backend options; upgrade guarantees undocumented | PARTIAL — observability blog post exists but not a formal audit log | FAIL — no scope primitive |
| **MemPalace** | FAIL — benchmarks doc says "no fact extraction, no compression, no summarization" — the closest to zero rubric possible. Conflicting claim about "validity windows" in one marketing source not substantiated in benchmarks doc. | FAIL (per benchmarks doc) / PARTIAL (per marketing) — disagreement; treat as FAIL until proven | FAIL (per benchmarks doc) — explicitly stated "no time-locking, supersession, or ephemerality features" | PASS — top reported score on LongMemEval (96.6%/100%) but the 100% hybrid number has been publicly questioned as gamed | PARTIAL — local SQLite + Chroma; backup tractable; upgrade guarantees not documented | PARTIAL — MCP tools exist for inspection; formal audit log not a primitive | FAIL — "wings/rooms/drawers" metaphor is an organising structure, not a scope-of-work |
| **Claude Memory Tool (API)** | FAIL — Claude writes what it decides; no rubric artifact | FAIL — it's a filesystem; there's no time-indexed state unless you build one over it | FAIL — `str_replace` / `rename` / `delete` overwrite in place | FAIL — retrieval is `view` by path; no semantic search primitive | PASS — fully client-side; you store the files; upgrade-safe because the "database" is your directory | PARTIAL — tool calls are visible; no automatic audit layer | PASS — scopes *can* map to subdirectories under /memories cleanly |
| **Claude Code (CLAUDE.md + auto-memory)** | N/A — not a knowledge store | N/A | N/A | N/A | PASS — files in your repo | PARTIAL — auto-memory writes are visible on disk | PASS — per-project CLAUDE.md already exists |

### 1.4 Shortlist analysis

No row is all-PASS. The closest is **Graphiti (OSS)** at 3 PASS / 3 PARTIAL / 1 FAIL. Zep SaaS is 3 PASS / 2 PARTIAL / 1 FAIL / 1 N/A but is disqualified by the Max-first constraint: personal-life data on a third-party SaaS is an auto-reject category for this workspace (personal health, finances, household covered in `prior-pOS .claude/rules/security.md` Tier A). The Zep SaaS offering stores that data on servers you do not control and was not configured with Max — it is a vendor substitute for capabilities that are outside Max coverage but also outside the "vendor-free on merit" envelope the plan allows, because the data involved is not embeddable data, it's *the memory itself*.

**Graphiti** is the single candidate that passes the two technically-hardest criteria (A2 time-lock, A3 supersession) on merit. It is open-source, self-hostable, supports Claude as the LLM provider, and supports local-only embedding via Ollama if desired. The weaknesses are real but addressable:

- **A1 ephemerality.** Graphiti's LLM-driven fact extraction from conversational chunks is not a user-authored rubric; an adaptation would add a pre-ingest filter governed by a stack-configured rubric (rule-based or LLM-as-judge).
- **U1 upgrade-safe.** The underlying graph DB (Neo4j/FalkorDB/Kuzu) is the durable state; the Graphiti library is a client over it. Upgrades of graphiti-core that change the schema would require an explicit migration step — this is the risk worth calling out. Byte-identical preservation of user data across upgrades becomes a property of the graph DB's own migration hygiene, not of Graphiti itself.
- **O1 observability.** Every edge in Graphiti carries `t'created` — the ingestion timestamp — which already gives a replay-at-T primitive for knowledge state. An external audit log of who-invoked-what (the pOS event log) would sit alongside, not inside, Graphiti.
- **S1 scope.** No candidate has pOS's scope-of-work primitive; any solution will need a workspace-layer mapping from scope-ID → memory partition.
- **R1 retrieval quality.** Benchmarks are published and favourable, but they are not pOS's test set. A retrieval evaluation harness against pOS-representative prompts is needed regardless of which solution is picked.

The case for **adopt Graphiti with light adaptation** is strong. "Light adaptation" here means:
1. Writing a pre-ingest ephemerality filter (workspace-authored rule set, fail-open with audit).
2. Writing the scope→partition mapper.
3. Setting up an external pOS event log that records `(actor, timestamp, objective, operation)` whenever memory is written or read — a wrapper at the pOS harness layer, not a Graphiti change.
4. Choosing the graph DB (likely FalkorDB or Kuzu for embedded-ness; see §2).
5. Selecting the embedding model (see §2 — this is the genuinely vendor-free-on-merit decision).

None of those are a fork of Graphiti. They are glue at the pOS layer that Graphiti is designed to accommodate.

### 1.5 The halt signal — one criterion no candidate satisfies

Spec criterion **U1(c)** requires *memory/daily entries (or equivalent) are byte-identical to pre-upgrade*. For a file-based store (Claude memory tool, CLAUDE.md, the current pOS memory layout), this is straightforward — the files are files and upgrades don't touch them. **For any graph-DB-backed store (Graphiti/Zep/Mem0/Cognee), byte-identical preservation is well-defined only at the underlying DB level, not at the memory-library level.** If the memory library changes its schema, byte-identity at the DB level is trivially preserved but the *semantics* of the stored bytes have drifted; if it is a semantic preservation that's required, byte-identity is the wrong metric.

This is a live conflict. I am signalling it rather than papering it. There are three ways to resolve it before a proposal can be written:

- **(a)** Revise U1(c) to read "memory is preserved across upgrades without content loss or corruption, verified by a round-trip test of stored→retrieved fidelity" — semantic rather than byte-literal preservation. This is the normal database-upgrade bar.
- **(b)** Keep U1(c) byte-literal; accept that the memory substrate must be a user-controlled filesystem with versioned flat-file content (e.g. git-backed markdown or JSONL), which forces the choice toward something in the MemPalace / Claude-memory-tool family — but those solutions FAIL on A2 and A3, so then time-lock and supersession must themselves be implemented as a build-from-scratch layer over the flat files.
- **(c)** Drop U1(c) and treat memory as a special case: upgrade reversibility guaranteed via snapshots, fidelity tested by replay, byte-identity not required.

My recommendation is **(a)**: revise the clause. Byte-identical preservation was a sensible criterion for the existing file-based memory layer, but the spec is deliberately agnostic about substrate (per the plan's zero-carryover rule). A semantic-preservation criterion aligned with "replay must reproduce the knowledge state available at a past moment" (O1) tests the thing that actually matters.

If the owner chooses (b), the recommendation flips from "adopt Graphiti with light adaptation" to "build-from-scratch over flat files" and §§2–8 become the operative evaluation. I have written §§2–8 in enough depth for that case.

### 1.6 Recommendation (conditional)

- **If U1(c) is revised per §1.5(a):** pilot Graphiti against a pOS-representative test set for 2 weeks before committing. Light adaptation as described above. Substrate and embedding-model decisions in §2.
- **If U1(c) is held byte-literal per §1.5(b):** build-from-scratch over git-backed flat files; §§2–8 are operative.

The rest of this document covers both branches, because a build-from-scratch evaluation is required input to a sound "adopt Graphiti" decision too — it names what we would have had to build, which is what we're paying Graphiti to avoid.

---

## 2. Storage substrate (operative under 1.5(b); informational under 1.5(a))

### 2.1 Candidates and verdicts

| Candidate | For | Against | Verdict for this workload |
|---|---|---|---|
| **SQLite** | Single-file, no server, byte-identical backup is `cp`, durable, mature FTS5 for keyword search, easy replication | Limited graph query power; JSON functions work but aren't graph-native; vector support only via extensions (sqlite-vec, sqlite-vss) | **Primary choice for flat-file branch.** For single-user scale over 5 years this is more than enough. |
| **DuckDB** | Columnar, fast analytics, embeddable, good for audit-log scans | Not ideal for high-write OLTP; less battle-tested as long-lived system of record | Secondary; good for analytics over the audit log, not the memory store itself. |
| **PostgreSQL** | Mature, has temporal extensions, strong JSON, pgvector | Server process, operational overhead violates micro-business preference | Overkill; rejected. |
| **Kuzu** (embedded graph DB) | Embedded, columnar graph, supports Graphiti, single-file-ish | Newer, smaller ecosystem, less ops experience | **Primary graph-DB choice** for Graphiti branch. |
| **FalkorDB** | Graph, Redis-backed, supports Graphiti | Redis process, multi-file state | Secondary graph-DB choice; acceptable if Kuzu is too new. |
| **Neo4j** | Mature graph DB | JVM process, operational weight | Rejected for single-user personal stack. |
| **Git-backed flat files** (markdown / JSONL) | Byte-identical preservation trivial; upgrade-safe; user-inspectable with `cat`; reversible via git | No query engine; every retrieval implies either in-memory scan or an index you maintain | **Viable only as a `src` with SQLite as a `build` index.** Flat files are the system of record, SQLite is derived and rebuildable. |

### 2.2 Size and performance projections (order of magnitude, 1 user, 5 years)

Working from observed the owner-workload signals:
- ~1 meaningful session event per active hour → ~3,000/year of meaningful events
- Entities (people, companies, projects): ~500 total, growing ~100/year
- Conversational data: assume 50k tokens of retained-worthy transcript/day (high estimate) × 365 × 5 = 91M tokens retained, which compresses to order-of magnitude 400 MB of text.
- Graphiti knowledge graph from that text: ~10-50k edges/year → 50-250k edges in 5 years. Any of Kuzu/FalkorDB/Neo4j handles this trivially.
- Embeddings at 1024 dim × 4 bytes × (say) 200k chunks = ~800 MB.

All three substrates handle 5 years of single-user scale. The bottleneck is *retrieval quality*, not storage volume. This rules nothing out on size grounds; rules in SQLite or any embedded graph DB as adequate.

### 2.3 Backup, portability, self-upgrade

| Substrate | Backup | Portability | Upgrade-resilience |
|---|---|---|---|
| Git-backed flat files | `git clone` | Works anywhere git works | Byte-identical by definition |
| SQLite | `sqlite3 .backup` or `cp` under write lock | Single file | Schema migrations well-understood; `ALTER TABLE` or `dump+restore` |
| DuckDB | Single file | Single file | Still evolving; less production-proven |
| Kuzu (embedded graph) | Snapshot directory | Directory-move | Newer; schema migration story less mature |
| FalkorDB | Redis RDB/AOF | Redis dump | Redis tooling; extra process |
| Graphiti over any of the above | Depends on DB | Re-ingest possible | Library upgrade may require schema migration in the DB |

**The self-upgrade risk for Graphiti specifically:** a graphiti-core minor version bump that adds a new edge field or changes the validity-interval encoding would require a migration in the underlying graph DB. This is a real operational burden but not categorically different from any database schema migration.

### 2.4 Recommendation

- **For Graphiti branch:** Kuzu (embedded, columnar graph, single-user friendly). FalkorDB if Kuzu proves immature in a pilot.
- **For build-from-scratch branch:** git-backed markdown/JSONL as the system of record; SQLite with FTS5 + sqlite-vec as a derived query index. The index is fully rebuildable from the flat files, which is what enables byte-identical upgrade preservation.

---

## 3. Time-locking mechanism (operative under 1.5(b))

### 3.1 Options

1. **Append-only log with timestamp query.** Write every fact with a timestamp; queries at time T linearly scan where ts ≤ T. Correct. Slow at scale. Recoverable.
2. **Versioned rows.** Each entity has versions; query picks the version valid at T. Standard temporal-DB pattern. Fast with indexing.
3. **Bitemporal edges (Graphiti pattern).** Each fact has `(tvalid, tinvalid)` pair; query at T selects edges with `tvalid ≤ T ≤ tinvalid`. Also tracks ingestion time separately. Gold standard for this problem.
4. **Git snapshots.** The file tree at commit C is the state at time of C. Free, user-inspectable. But querying across snapshots is painful.
5. **Event sourcing + materialised views.** Store only events; materialise any point-in-time state by replay. Correct, storage-heavy, replay cost grows over time unless snapshotted.

### 3.2 Recommendation

- **Bitemporal edges** (option 3) is what Graphiti gives us for free. Adopt under §1.5(a).
- **Append-only log + SQLite versioned rows** (hybrid of options 1 and 2) under §1.5(b). The flat files are the append log; SQLite's index tables hold `(entity, fact, tvalid, tinvalid)` tuples for query. This is a simplification of Graphiti's model but loses community-tested edge cases.

### 3.3 Interaction with supersession

Bitemporal is the cleanest substrate: supersession *is* `tinvalid` + pointer to the superseding edge's id. A flat-file branch would record supersession as an explicit pointer in the new entry's frontmatter (e.g. `supersedes: abc123`), with the SQLite index storing the forward and reverse pointers.

---

## 4. Supersession (operative under 1.5(b))

### 4.1 Options

1. **Pointer-on-superseded entry.** The older entry gets an annotation `superseded_by: xyz`. Simple. Requires mutating the older entry, which conflicts with append-only.
2. **Pointer-on-superseding entry.** The newer entry carries `supersedes: abc`. Append-only friendly. Requires a reverse-index to ask "what superseded this."
3. **Supersession edges** (Graphiti style). A separate edge relationship. Queryable, supports partial supersession naturally (different edges can invalidate different facts).
4. **Tombstone-with-redirect.** The older entry is replaced by a redirect. Destroys history. Rejected.

### 4.2 Partial supersession

Can one entry correct a *subset* of another's facts?

- **Whole-entry supersession:** simpler; "this page replaces that page." Loses information when only one fact has changed.
- **Fact-level supersession:** each fact (entity attribute or edge) is independently versioned. Better fidelity. Graphiti does this natively.

For pOS, fact-level is the right grain because personal context changes incrementally — the owner's employer changes while the owner's home city does not, and a re-assertion shouldn't invalidate all sibling facts.

### 4.3 Retrieval discrimination

At query time, retrieval filters by temporal predicate. Default query: "facts valid at `now()`." Historical query: "facts valid at `T`." Graphiti's `reference_time` parameter is exactly this. For flat-file branch, the SQLite index must carry `tvalid`/`tinvalid`, and the retrieval layer must default-filter by `tinvalid IS NULL OR tinvalid > now()` unless an explicit time reference is passed.

---

## 5. Ephemerality rubric (operative in both branches — Graphiti needs this too)

### 5.1 Options

1. **Explicit rule set per source type.** Hand-authored rules (e.g. "ignore tokens in code blocks", "ignore pure arithmetic", "always save decisions"). Deterministic; auditable; requires maintenance.
2. **LLM-as-judge classifier.** An LLM call per candidate chunk decides save/discard. Slow, expensive, but handles novel cases.
3. **Hybrid (rules first, LLM fallback).** Rules handle the common cases cheaply; anything rule-ambiguous goes to the LLM.
4. **No discard + filter-at-retrieval.** Keep everything, filter at query. Inflates storage; makes retrieval harder; fails A1's sampled-batch-absence check.

### 5.2 Recommendation

**Hybrid (option 3).** Rules live in a workspace-authored YAML file; fall through to Claude (inside Max coverage) for ambiguous cases. Every save/discard decision writes an audit row so the rubric itself is observable and updateable.

### 5.3 Update loop

Rubric changes get versioned. Corrections ("this should have been saved") feed back into the rules, either as a new rule or as training-data for fine-tuning the prompt used by the LLM fallback.

### 5.4 False-positive / false-negative recovery

- **False-positive** (discarded something important): if the source material still exists (chat transcripts, etc.), re-ingest with the updated rubric.
- **False-negative** (saved junk): GC-style sweeps periodically — the rubric scans old entries and flags ones that would now be discarded for human review.

The false-positive case is the worst — if the owner's transcript sources are themselves ephemeral (Telegram, for instance), there's no re-ingest path. This is the strongest argument for bias-toward-save.

---

## 6. Retrieval — right knowledge at right time (operative in both branches)

### 6.1 Mechanisms considered

1. **Embedding-based semantic search.** Standard. Single-vector per chunk, top-k by cosine similarity.
2. **Active recall triggered by primary-persona context.** A pre-turn step looks at what the user just said and what's in-context and pulls related memory. This is how Claude Memory tool is designed to work.
3. **Keyword/tag search.** Complements semantic; especially good for named entities (people, projects).
4. **Hybrid retrieval with reranking.** Both of the above + an LLM rerank at the top of the candidate list. Gold-standard quality.
5. **Knowledge-graph traversal.** Graphiti's query model — walk edges from matched entities.

### 6.2 Recommendation

Hybrid. Graph traversal (if Graphiti) or keyword+vector (if flat files), with a Claude-driven rerank of the top-k. Rerank inside Max.

### 6.3 Embedding model — the vendor-free-on-merit decision

Embeddings are the clearest capability **outside Max coverage.** Anthropic has no embedding API as of 2026-04-17 (Letta's docs: "there are no supported embedding models for Anthropic"). Options on merit:

| Option | Quality | Latency | Cost | Privacy | Local | Verdict |
|---|---|---|---|---|---|---|
| OpenAI text-embedding-3-small | Good | Cloud | $0.02/M tokens | External | No | Rejected for personal data. |
| Voyage-3 | Best-published | Cloud | $0.06-0.18/M | External | No | Rejected for personal data. |
| Gemini embedding (free tier) | Good | Cloud | Free | External | No | Rejected for personal data. |
| **Ollama + local model (e.g. Qwen3, bge-large)** | 90% of Voyage-3 | Local | Local compute | On-device | Yes | **Recommended.** |
| sentence-transformers via Python | Solid | Local | Local compute | On-device | Yes | Backup option. |

For a *personal* memory store that includes health, finances, and relationships (personas' domain), personal data should never leave the device. Local embedding via Ollama + a 2026-vintage model (Qwen3 or bge-large) is the right call. Graphiti supports Ollama natively.

### 6.4 Test-set quality measurement

A pOS-representative test set does not exist. To measure retrieval quality (for R1):

- **Build set:** 50-100 hand-curated query/expected-result pairs drawn from the owner's actual past sessions — "what were the options I was considering for HELOC refinancing last month", "which contractor did Jo recommend for X", etc.
- **Targets:** precision@5 ≥ 0.8 for recall-style questions, ≥ 0.9 for entity-lookup.
- **Cadence:** run at every major memory-layer version bump; treat regression as a blocker.

### 6.5 Context-window cost budget

Retrieval returns small. A single retrieval should never cost more than ~2k tokens in the final context window: 5–10 chunks × 200 tokens each + a one-line citation row per hit. If we're spending >3k tokens on retrieval, either the rubric is loose (R1 and A1 are coupled) or the rerank isn't doing its job.

### 6.6 Pipeline stage vs persona capability

Both. A pre-turn active-recall stage (pipeline) pulls obvious context; a tool (capability) lets the persona query deeper when needed.

---

## 7. Integration with adjacent systems

### 7.1 Observability

Every memory write/read emits an event to the pOS event log with `(actor, ts, objective, operation, target_ids, bytes_in, bytes_out)`. Replay-at-T: given a past timestamp, the observability layer can answer "what memory was available to the persona at time T" by:

- **Graphiti branch:** querying the graph with `reference_time=T`.
- **Flat-file branch:** reading the git commit at-or-before T and the SQLite index rebuilt to that commit.

### 7.2 Self-upgrade

Named as the live conflict in §1.5. Summary of the branches:

- **Graphiti branch:** memory resilience to upgrade = graphiti-core schema migrations + underlying graph-DB migrations. Semantic preservation guarantee, not byte-identical.
- **Flat-file branch:** memory resilience to upgrade = "framework never touches the memory directory." Byte-identical trivially. The index is rebuildable from the files.

### 7.3 Scope-of-work integration

Three options:

1. **Per-scope partition.** Every scope has its own memory partition; cross-scope queries explicitly request other partitions. Good for isolation; bad for cross-scope knowledge reuse (the whole point).
2. **Shared store with attribution.** Every fact carries `created_by_scope` and `observed_in_scope`. Retrieval defaults to "facts observed anywhere, weighted toward this scope." Better for reuse.
3. **Hybrid: shared entity graph, per-scope episode log.** The semantic/entity layer is shared; the episode layer is scope-partitioned. This matches Graphiti's three-subgraph architecture (episode, semantic, community) naturally.

**Recommend option 3.** It's what Graphiti already structures toward, and it preserves the principle that facts about the owner's employment belong to the owner, not to any particular scope, while episode-level "what we did in the scope 'refinance-heloc'" stays scoped.

---

## 8. Dependency map

How memory interacts with the other named pOS primitives:

```
                 ┌─────────────────────────┐
                 │  scope-of-work          │
                 │  (goal, budget, obs)    │
                 └──────┬──────────────┬───┘
                        │              │
                   writes/reads    reads at start
                        │              │
                        v              v
  ┌──────────────────────────┐   ┌──────────────────────────┐
  │  memory system           │<->│  primary persona         │
  │  - accrual (write)       │   │  - invokes memory as     │
  │  - retrieval (read)      │   │    a capability          │
  │  - time-lock             │   │  - passes retrieval into │
  │  - supersession          │   │    context each turn     │
  └────────┬────┬────────────┘   └──────────┬───────────────┘
           │    │                           │
           │    └── emits events ───────────┤
           │                                │
           v                                v
  ┌──────────────────────────┐   ┌──────────────────────────┐
  │  observability /         │<->│  self-upgrade            │
  │  event log               │   │  - must preserve memory  │
  │  - captures all ops      │   │    across upgrades       │
  │  - supports replay-at-T  │   │  - preserves audit log   │
  └──────────────────────────┘   └──────────────────────────┘
```

Directional notes:
- The **primary persona** depends on memory for every turn; memory does not depend on the persona's identity.
- **Observability** consumes memory events; memory does not depend on observability (it writes to the log; the log is external).
- **Scope-of-work** is the context in which memory is written/read; memory carries scope attribution but does not own scope definition.
- **Self-upgrade** must not corrupt memory. The guarantee is one-way.

Where the dependency graph pressures the design: the primary persona and memory are hot-coupled at every turn, which argues for a low-latency local implementation (Graphiti + local graph DB + local embedding, or SQLite + flat files) rather than a cloud roundtrip.

---

## 9. Complexity estimate (AI-time)

Using the `task-orchestration.md` rule 15 anchors: AI agents work 20-100× faster than human estimates, so complex cross-cutting features in the 20-45 min range.

### 9.1 Adopt Graphiti branch (under §1.5(a))

- Pilot setup (clone, spin up Kuzu, connect Claude, ingest 1 week of sample data): **10-15 min AI-time**.
- Ephemerality rubric (rule YAML + pre-ingest filter): **10-15 min**.
- Scope-mapper + pOS event-log integration: **15-25 min**.
- Retrieval test set (50 Q/A pairs): **20-30 min** (this is the one that requires real-data review; the owner should own it).
- Retrieval wrapper with Claude rerank inside Max: **10-15 min**.
- Migration runbook for graphiti-core version bumps: **10 min**.

Total: ~75-110 AI-time minutes to pilot. Rebuild from zero is *not* the time cost here — the time cost is writing the glue and, critically, building the test set. **The surprise is the test set.** Without a honest retrieval test set, R1 is an assertion not a criterion, and every decision downstream floats.

### 9.2 Build-from-scratch branch (under §1.5(b))

- Append-only JSONL + frontmatter spec: **5 min**.
- SQLite index (FTS5 + sqlite-vec + bitemporal columns + supersession pointers): **20-30 min**.
- Rubric/pre-ingest filter: **10-15 min** (same as above).
- Ingest pipeline: **15-25 min**.
- Retrieval layer (hybrid, with rerank): **20-30 min**.
- Time-travel query + supersession discrimination: **15-25 min** (this is the hardest piece — Graphiti is the open-source alternative because this is hard).
- Test set: **20-30 min** (same as above).
- Replay integration with event log: **10-15 min**.

Total: ~115-175 AI-time minutes. **The surprises here are (a) the time-travel query semantics — boundary cases around "what if an entry is written with a backdated tvalid" etc. are subtle and are where Graphiti earned its published benchmark — and (b) the fact that you now own a temporal DB engine in addition to a memory system.** Every bug is your bug. This is the thing Graphiti buys you out of.

### 9.3 Verdict on complexity

Graphiti is ~60% the AI-time of build-from-scratch and avoids a substantial class of long-tail correctness risk. The adapt-Graphiti cost is in glue and test-set; the build-from-scratch cost is in novel engine work on a genuinely hard problem (bitemporal modelling).

---

## 10. Questions that need prototyping to answer

Flagged not-yet-answerable under the research-only constraint:

1. **Does Graphiti's LongMemEval performance hold on pOS's actual content?** The published 94.8% DMR is on chat-style QA corpora; owner's memory is task-records + decisions + entity cards, not conversations. Prototype: ingest 2 weeks of the owner's current `memory/daily/` and entity files (one-time, with the owner's permission — this is the one permitted use of existing memory per the plan's factual-reading clause) and run a retrieval eval against hand-authored queries.

2. **Is Kuzu stable enough for a 5-year store?** Kuzu is embedded and columnar and fits the operational profile perfectly, but is new relative to SQLite. Prototype: ingest-and-query for a week, hard-kill the process mid-ingest five times, verify no corruption. Compare to FalkorDB (Redis-backed) as a control.

3. **Is the local Ollama embedding fast enough for pre-turn active recall?** Pre-turn adds latency to every persona interaction. Target: retrieval (embed + query + rerank) under 500ms p95. Prototype: Ollama + Qwen3 on the owner's laptop; measure.

4. **Does the rubric hold?** An ephemerality rubric authored ahead of time will have false classes. Prototype: one week of running with audit-only (every ingest logged; no data actually discarded), review the discard candidates manually.

None of these prototypes are a build commitment; they are decision inputs. Each is <1 day AI-time.

---

## 11. Spec acceptance coverage — honest accounting

### 11.1 Recommended direction (adopt Graphiti under §1.5(a))

Satisfies:
- **A1 ephemerality** — via workspace-authored rubric + audit (glue layer, not Graphiti).
- **A2 time-lock** — Graphiti's bitemporal model with `reference_time` parameter.
- **A3 supersession** — `tvalid`/`tinvalid` edges with pointer to superseding edge.
- **R1 retrieval quality** — conditional on the test set meeting the targets in §6.4. Prototype required.
- **U1 upgrade-safe** — *IF spec clause U1(c) is revised* to read "preserved without loss or corruption, verified by round-trip fidelity test" rather than "byte-identical." **This is the halt-and-signal item.**
- **O1 observability** — via pOS event-log wrapper around memory ops, plus Graphiti's own ingestion timestamps for replay-at-T.
- **S1 scope integration** — via workspace-layer mapper; matches Graphiti's three-subgraph structure.

**Cannot satisfy without revision:** U1(c) byte-identical clause. See §1.5.

### 11.2 Build-from-scratch branch (under §1.5(b))

Satisfies:
- **A1** — same rubric/glue layer.
- **A2, A3** — via append-only JSONL + SQLite bitemporal index + supersession pointers. Correct in principle; long-tail correctness is build risk.
- **R1** — conditional on test set; same caveat as above.
- **U1** — byte-identical preserved trivially (files are files; index is derived and rebuildable).
- **O1** — native via the event log; replay is git-checkout + index-rebuild.
- **S1** — via directory partitioning.

**Risk:** the time-travel + supersession query semantics have subtle cases (backdated facts, partial supersession, retroactive corrections) where Graphiti has battle-tested answers and a from-scratch build doesn't. Under U1(c) held byte-literal, this risk is unavoidable.

---

## 12. Summary and next step

One halt signal: spec U1(c) byte-identical preservation needs revision for a graph-DB backed store to be viable. I recommend revising it; the owner may prefer to hold the line, which moves the recommendation.

With that one revision: **adopt Graphiti with light adaptation**, piloted against a pOS-representative test set, Kuzu as the embedded graph DB, local Ollama embeddings, Claude (inside Max) for all LLM-driven steps (rubric fallback, entity extraction, retrieval rerank).

Without that revision: **build-from-scratch over git-backed flat files**, with SQLite as the derived index. ~60% more AI-time, more long-tail correctness risk, but byte-identical preservation is trivial.

Either way, the retrieval test set is the single highest-value thing to commission early — every acceptance criterion for R1 is floating until it exists.

---

## Sources

- Letta / MemGPT — [repo](https://github.com/letta-ai/letta), [Anthropic provider docs](https://docs.letta.com/guides/server/providers/anthropic/), [architecture blog](https://www.letta.com/blog/letta-v1-agent)
- Zep / Graphiti — [arxiv paper](https://arxiv.org/abs/2501.13956), [paper HTML](https://arxiv.org/html/2501.13956v1), [Graphiti repo](https://github.com/getzep/graphiti), [CE deprecation notice](https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/), [FalkorDB Graphiti docs](https://docs.falkordb.com/agentic-memory/graphiti.html)
- Mem0 — [repo](https://github.com/mem0ai/mem0), [arxiv paper](https://arxiv.org/abs/2504.19413), [state-of-memory 2026 blog](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- Cognee — [repo](https://github.com/topoteretes/cognee), [Memgraph blog](https://memgraph.com/blog/from-rag-to-graphs-cognee-ai-memory)
- MemPalace — [repo](https://github.com/milla-jovovich/mempalace), [benchmarks doc](https://github.com/milla-jovovich/mempalace/blob/main/benchmarks/BENCHMARKS.md), [review with criticism](https://www.danilchenko.dev/posts/2026-04-10-mempalace-review-ai-memory-system-milla-jovovich/)
- Claude Memory Tool — [Anthropic docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- Claude Code memory — [Anthropic docs](https://docs.anthropic.com/en/docs/claude-code/memory), [community benchmark review](https://lord.technology/2026/04/11/claude-codes-memory-tool-ecosystem-is-mostly-redundant-with-its-own-defaults.html)
- Embedding-model comparisons — [Voyage vs OpenAI](https://www.buildmvpfast.com/blog/best-embedding-model-comparison-voyage-openai-cohere-2026), [2026 benchmark roundup](https://dev.to/chen_zhang_bac430bc7f6b95/which-embedding-model-should-you-actually-use-in-2026-i-benchmarked-10-models-to-find-out-58bc)
- Storage substrates — [DuckDB vs SQLite](https://motherduck.com/learn/duckdb-vs-sqlite-databases/), [DataCamp comparison](https://www.datacamp.com/blog/duckdb-vs-sqlite-complete-database-comparison)
- Context on memory architectures — [LangMem conceptual guide](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/), [Letta agent memory post](https://www.letta.com/blog/agent-memory)
