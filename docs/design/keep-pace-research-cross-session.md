# Keep-Pace Research — Cross-Session + Frequency-Aware Memory

**Date:** 2026-05-28
**Status:** research (read + external research; no implementation)
**Owner:** Luke Ivers
**Dimension:** CROSS-SESSION live memory sharing + USAGE/FREQUENCY-aware preloading
**Serves:** Luke's vision items #3 (multiple simultaneous sessions cross-load), #4 (learn what's frequently asked, preload it), #7 (rotate the bounded hot-index to track current scope of work)
**Builds on:** `memory-architecture.md` (storage layer solved — index/detail, 25KB hot cap, M1/M2 guard), `l5-context-memory-{scout,deep-1,deep-2,deep-3}.md` (compaction hooks, subagent `memory:`, structural enforcement)

---

## Bottom line

The storage problem is solved (memory-architecture.md). The frontier this doc covers has two halves, and the research lands cleanly on both:

1. **Cross-session live sharing** — multiple concurrent Claude Code / CLI sessions, one writing memory while others pull it in. **No mature product solves the concurrency-safety half** — Hindsight, mem0, SAMEP, Cloudflare Agent Memory all document the *sharing intent* and the *identity-scoping* model but explicitly omit race-condition / concurrent-write handling. That gap is loam's to fill, and the OS literature already has the answer for a file-based system: **POSIX `O_APPEND` atomic appends + atomic write-via-`rename` + a partition-per-writer journal** give lock-free, corruption-free cross-session sharing without a database. This is the same primitive git itself uses (one append-only log per actor; merge is deterministic because each writer owns its partition).

2. **Frequency-aware preloading** — the hot-index rotation Luke wants (#7) is *exactly* the cache-replacement problem, and the answer is **ARC (Adaptive Replacement Cache) / LFU2**: track both recency and frequency per memory, keep a bounded hot set (the 25KB index), and let the lowest recency×frequency score demote to cold automatically. PostgreSQL and ZFS ship ARC in production; it is well-understood, deterministic, and implementable in a few hundred lines reading a usage-counter file.

The realistic loam shape: a **`UserPromptSubmit` recall hook** + a **`Stop`/`SessionEnd` retain hook** writing to an **append-only event journal** (one file per session = one writer per partition = no locks), with a **periodic compactor** that folds the journal into the index and runs the ARC rotation against a usage-counter file. This composes on hooks loam already owns (`queue_status_inject.py` is 80% of the recall hook) and re-implements no engine. Cross-session liveness comes for free from the journal being on disk: session B's `UserPromptSubmit` hook reads what session A's `Stop` hook appended seconds ago.

---

## 1. The cross-session sharing landscape (what exists, what breaks)

### 1.1 Hindsight (Vectorize) — the closest reference, session-level hooks (Tier-2)
Source: [Hindsight — Your Claude Code Subagents Don't Share What They Learn](https://hindsight.vectorize.io/blog/2026/05/06/claude-code-subagents-shared-memory)

The shared-memory-bank plugin fires **four session-level hooks**, not subagent-internal ones:
- **SessionStart** — health check on the bank.
- **UserPromptSubmit** — auto-recall relevant memories before the model is called.
- **Stop** — auto-retain the session transcript when the turn ends.
- **SessionEnd** — cleanup.

Key architectural choice: **hooks fire at the orchestrator level, not inside subagent loops.** Recall happens once on the orchestrator's turn; the orchestrator carries what it knows into the subagent prompt via the Task tool. Subagents inherit context *indirectly through the orchestrator* — they need no hooks of their own. This is directly relevant to loam: loam dispatches background agents from a main session, so the main session's recall hook is where cross-session memory should land, and it propagates into dispatch briefs.

Identity scoping: a static `bankId` per project; every session and every subagent it spawns reads/writes that one bank. `dynamicBankId: true` + `dynamicBankGranularity: ["agent","project"]` / `["user"]` for finer isolation.

**The load-bearing absence (verified by fetching the article):** Hindsight documents *zero* about concurrency — no file locking, no append-only strategy, no conflict resolution, no concurrent-write safety guarantee, no recall ranking algorithm. It is architectural intent, not mechanism. **This is the single most important finding for loam:** the off-the-shelf reference does not solve the hard part (two live sessions writing at once), so loam cannot adopt it for safety — it must define the concurrency discipline itself.

### 1.2 mem0 — multi-scope identity model (Tier-2/3, the scoping vocabulary)
Source: [mem0 — State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)

The **multi-scope memory pattern**: every memory write is tagged with at least one identity scope —
- `user_id` — belongs to the user, persists across all sessions (the always-relevant tier).
- `agent_id` — belongs to a specific agent instance (per-persona, maps to loam's subagent `memory:`).
- `run_id` / `session_id` — scoped to one conversation/run (ephemeral).
- `app_id` / `org_id` — shared organizational context.

These scopes are **composed at retrieval time with automatic merging and ranking** — user-level facts rank above session-specific context. Metadata filtering (`{"context":"healthcare"}`) further constrains. Retrieval scoring is semantic + BM25 + entity-matching.

**Named 2026 production gaps (mem0's own list — all relevant to loam):**
- **Cross-session structure:** systems *overwrite* rather than *model evolving state* (a location change clobbers history). → Luke's #6/#7 "refine objectives WITHOUT erasing old work" is the explicit fix.
- **Memory staleness:** high-relevance facts become confidently incorrect after a state change (employer updates). → objectives drifting stale is exactly this.
- **Cross-session identity:** multi-device/anonymous resolution unresolved. → loam sidesteps this (single user, single machine).
- Concurrency: **mem0 mentions async writes as a latency requirement but documents no race/conflict/ordering handling.** Same gap as Hindsight.

**loam tie-in:** the multi-scope model maps onto loam's existing stores — `user_id` ≈ CLAUDE.md + MEMORY.md (always-on), `agent_id` ≈ subagent `memory:` (per-persona), `session_id` ≈ the per-session journal, the shared/`app` tier ≈ the workstream-queue + plan-docs + S3 graphiti. loam already HAS multi-scope; it just hasn't named the compose-at-retrieval discipline.

### 1.3 SAMEP — secure cross-agent context protocol (Tier-2, academic)
Source: [SAMEP: A Secure Protocol for Persistent Context Sharing Across AI Agents (arXiv:2507.10562)](https://arxiv.org/abs/2507.10562)

A protocol for persistent, semantically-searchable, access-controlled memory sharing across agents (persistent context preservation + fine-grained access control + semantic discovery). PDF body not text-extractable in this pass; the abstract names the three properties but the concrete concurrency mechanism is not captured here. **Useful as a design-vocabulary reference (access-control + semantic-discovery framing), NOT an adoption target** — it is a multi-org-agent protocol; loam is single-user local. Flag: do not cite SAMEP mechanism detail beyond the abstract without reading the full paper.

### 1.4 Cloudflare Agent Memory + AutoGen shared-state (Tier-2/3, the race-condition statement)
Sources: [Cloudflare — Introducing Agent Memory](https://blog.cloudflare.com/introducing-agent-memory/); [AutoGen Discussion #7144 — shared state across multi-agent](https://github.com/microsoft/autogen/discussions/7144); [DEV — 7 AI Agent Orchestration Patterns](https://dev.to/dohkoai/7-ai-agent-orchestration-patterns-for-scaling-concurrent-systems-with-production-code-1onc)

These name the failure mode precisely: **"race conditions occur when multiple agents write to the same shared state — without explicit concurrency control, agents overwrite each other's results, read stale values, or corrupt the shared state."** The classic ABA: Agent A reads prefs, Agent B updates them, Agent A writes stale data back. The prescribed fix is **centralized state with atomic conflict resolution — agents don't write directly; they propose changes, the system validates for conflicts, then commits atomically.** This is the propose-validate-commit pattern; the append-only-journal design (§2) is its file-based realization (the "commit" is an atomic append; the "fold" is the compactor).

---

## 2. The concurrency-safety mechanism for a file-based system (the part nobody else documents)

This is the load-bearing engineering content. The products above punt on concurrency; the OS literature solves it.

### 2.1 POSIX `O_APPEND` — lock-free atomic appends across processes (Tier-1 OS semantics)
Sources: [Paul Khuong — Appending to a log](https://pvk.ca/Blog/2021/01/22/appending-to-a-log-an-introduction-to-the-linux-dark-arts/); [Not The Wizard — Are File Appends Really Atomic?](https://www.notthewizard.com/2014/06/17/are-files-appends-really-atomic/)

POSIX `O_APPEND` guarantees: when the flag is set, the file offset is moved to end-of-file *atomically, immediately before each write, with no intervening modification*. Multiple processes (multiple live Claude sessions) can append to the same log concurrently **without a lock** and without interleaving each other's records — provided each record is written in a single `write()` under the OS atomic-append size (PIPE_BUF / filesystem-dependent; small JSON lines are safely under it). 

**Caveat (named):** userspace buffering (a runtime that batches writes and flushes on its own schedule) undermines the kernel guarantee. The discipline: write each journal record as one line, flush/fsync per record, keep records small. For loam's hook scripts (short Python), `open(path,'a')` + a single `f.write(json_line+'\n')` + `f.flush()` is the safe shape.

### 2.2 Atomic write-via-`rename` for the index (Tier-1 OS semantics)
Sources: [python-atomicwrites](https://python-atomicwrites.readthedocs.io/); [javaspring — Atomic file moves](https://www.javaspring.net/blog/how-to-guarantee-atomic-move-or-exception-of-a-file-in-java/)

For the *index* (a whole-file replace, not an append — e.g. when the compactor rewrites MEMORY.md), the safe pattern is **write-to-temp + atomic `rename`**: write the new file fully to a tempfile in the same directory, then `rename()` over the target. `rename` is atomic on POSIX same-filesystem — a concurrent reader sees either the complete old file or the complete new file, never a half-written one. If a crash occurs mid-write, the old file survives untouched. This is exactly the property P2 (trust — never silently lose) needs for the hot index.

### 2.3 Partition-per-writer journal = git's own model (Tier-1/2, the architecture)
Sources: [CRDTs: Theory and Practice](https://blog.psychollama.io/crdts-theory-and-practice/); [Git merge-conflict / CRDT](https://zenn.dev/hina_dev/articles/git-merge-conflict-crdt-intro?locale=en); [Hacker News — git-bug CRDTs](https://news.ycombinator.com/item?id=47142157)

The cleanest cross-session model avoids write-contention entirely: **one append-only journal file per session** (filename = session_id). Each session is the *sole writer* to its own partition → no two processes ever write the same file → locks are unnecessary by construction. This is precisely how git works: "one log per actor and branch pair, guaranteeing total local order because you're the only one appending to your partition." The git `.git/objects` store is itself a CRDT (a Merkle G-Set — append-only, removal never needed). 

**Reading is the merge:** any session's recall hook reads ALL journal partitions (its own + every other live session's), sorts by timestamp, and folds them. Because each record is immutable and timestamped, the fold is **order-independent and deterministic** (the CRDT property: "no matter the order data is merged, the final result is the same"). Conflicts only arise when you *mutate* shared state; an append-only journal never mutates, so it never conflicts. State evolution (Luke's #6 "refine without erasing") is modeled as *new append records that supersede*, not overwrites — the staleness/overwrite gap mem0 named (§1.2) is structurally avoided.

**The compactor** (a periodic job — `SessionEnd` hook, or a cron) folds the journals into the durable index + topic files using **last-write-wins per key with declared merge** (the CRDT-merge pattern: per-field deterministic resolution, not a manual dedup script), then truncates folded journal partitions. This is the file-based realization of the propose-validate-commit pattern §1.4 prescribed.

---

## 3. Frequency-aware preloading (Luke's #4 + #7 — the hot-index rotation)

Luke's #7 is, precisely, a **bounded-cache eviction problem**: the hot index has a HARD size cap (25KB), and it must hold the memories tied to the user's *current* scope of work, rotating others out to cold (where they stay recoverable). This is the most-studied problem in all of systems engineering.

### 3.1 ARC / LFU2 — recency × frequency, the right algorithm (Tier-1/2 systems literature)
Sources: [FreqRec — adaptive LFU-LRU hybrid](https://www.researchgate.net/publication/400479709_FreqRec_A_Lightweight_and_Adaptive_LFU-LRU_Hybrid_Policy_for_Cache_Block_Replacement); [LRU vs LFU caching](https://medium.com/@alxkm/introduction-to-lru-and-lfu-caching-concepts-implementations-and-practical-use-cases-ab90f2e168bd); [DEAP Cache — deep eviction/admission/prefetching](https://arxiv.org/pdf/2009.09206)

- **LRU** (least-recently-used) tracks recency only — good for "what was I just working on" (Luke's #2 session-start surfacing).
- **LFU** (least-frequently-used) tracks frequency only — good for "what does the user ask for most" (Luke's #4).
- **LFU2 / ARC** combine both: each item carries a **usage counter (frequency)** AND a **recency counter**, and eviction scores on both. **ARC (Adaptive Replacement Cache)** — shipped in PostgreSQL and ZFS — maintains two lists (one recency-LRU, one frequency-LFU) and **dynamically resizes the target balance between them** based on the observed access pattern. This is exactly Luke's intent: preload the most-likely-needed context (frequency) AND what was just being worked (recency), and adapt the mix.

**The loam realization:** a small `usage-counters.json` file alongside MEMORY.md. Each memory's index entry carries `{hits, last_access}`. The recall hook increments `hits` and updates `last_access` whenever a memory is surfaced/consulted (observable from which topic-file the model reads, or which `group_id` the S3 search returns). A periodic compactor scores every memory `score = f(hits, recency)` and keeps the top-N that fit the 25KB hot budget in the index; the rest demote to cold (file stays, index line goes — exactly memory-architecture.md §3.2's promotion/demotion rule, now with a *concrete eviction function* instead of a hand-wave). This makes §3.2's "lowest-value pointers demote" **mechanical and automatic** (P3 scaling), which is what Luke's #7 demands.

### 3.2 Prefetch / admission for new memories (Tier-2)
Source: [DEAP Cache](https://arxiv.org/pdf/2009.09206); [Purdue — kernel prefetching on buffer cache](https://engineering.purdue.edu/~ychu/publications/tc07_pref.pdf)

A newly-written memory has zero hits — naive LFU would never load it. The fix (from the prefetch literature): **admit new blocks as "not accessed yet" with a seeded frequency, adjust on first access.** For loam: a freshly-captured memory gets a recency-boost (it's about *current* work by definition), so it enters the hot index immediately and earns/loses its place over the next sessions. This directly serves Luke's #6 (newly-noted objectives surface right away) without waiting for frequency to accumulate.

### 3.3 Context-miss recovery (Luke's #5) — the cache-miss handler
This is the cache-*miss* path of the same model. When the user asks something **not aligned with the loaded hot set** (a miss), the system must *not* proceed as if the context doesn't exist — it must run a retrieval pass *at that moment* to load the right cold memories. Mechanism: the `UserPromptSubmit` recall hook computes relevance of the incoming prompt against the *full* index (hot + cold pointers — pointers are cheap, the bodies are not), and if the top hits are NOT currently in the hot set, it pulls those topic files / S3 facts JIT and injects them, AND bumps their usage counters (so a repeated miss promotes them to hot — the system *learns* the user's shifting scope, Luke's #4+#7). This is the demand-paging analog: a miss triggers a load, and the loaded item's counter rises so future access is a hit.

---

## 4. The realistic loam shape (buildable on hooks + markdown + optional MCP)

Composes on primitives loam already owns. Re-implements no engine. Serves the non-technical user invisibly (they never see a journal, a counter, or an eviction — they just see the assistant remember and stay current).

| Piece | Mechanism | Primitive | Luke's item | Concurrency-safe via |
|---|---|---|---|---|
| **Cross-session liveness** | One append-only journal per session (`<workspace>/.scratch/memory-journal/<session_id>.jsonl`); each session sole-writes its own | `Stop` / `SessionEnd` hook appends; `O_APPEND` + per-record flush | #3 | partition-per-writer (no lock needed) |
| **Live pull-in** | Recall hook reads ALL journal partitions (own + other live sessions), folds by timestamp | `UserPromptSubmit` hook (extend `queue_status_inject.py`) | #3 | append-only = order-independent fold (CRDT) |
| **Frequency-aware preload** | `usage-counters.json` tracks `{hits,last_access}` per memory; compactor runs ARC/LFU2 eviction against the 25KB hot budget | periodic compactor (`SessionEnd` or cron); recall hook increments | #4, #7 | atomic `rename` rewrite of index |
| **Session-start surfacing** | Recency-ranked recent-journal fold → "last session you were working X, state Y" | `SessionStart` hook | #2 | read-only, no contention |
| **Context-miss recovery** | Recall hook scores prompt vs full index; cold hits get JIT-loaded + counter-bumped | `UserPromptSubmit` hook | #5 | read-only + atomic counter append |
| **Objective tracking** | Objectives are append records superseding prior ones (never overwrite); compactor folds to current-objectives index | journal records typed `objective`; S3 graphiti for relational | #6, #7 | append-only supersede (no staleness clobber) |

**Sequencing rationale (F4 — scope ↔ confidence):**
- HIGH confidence / tight scope: the journal + recall-fold (§2.3 + §4 rows 1–2) — git's own proven model, loam already has the hook. Build first.
- HIGH confidence: ARC counter file + compactor (§3.1) — textbook algorithm. Build second; it makes memory-architecture.md's demotion rule mechanical.
- MEDIUM confidence / verify-first: context-miss relevance scoring (§3.3) — "relevance of prompt vs index" needs a cheap scorer (BM25 over index lines, or a `claude -p` micro-classification). Probe the cheap path before the LLM path.

---

## 5. Risks, gaps, and F2 forks

1. **`O_APPEND` atomicity is filesystem-and-size-dependent.** It holds for small records under PIPE_BUF on local POSIX FS; it is NOT guaranteed on all network filesystems (NFS) or for large records. Mitigation: keep journal records small (one fact/event per line), local-FS only (loam is single-machine), fsync per record. **Risk, not a fork** — the partition-per-writer design (one writer per file) makes even non-atomic appends safe because there's no concurrent writer to interleave with; `O_APPEND` atomicity is belt-and-suspenders, only load-bearing if loam ever shares a journal file across sessions (which the design avoids).

2. **OWNER-ASK — compactor cadence + who runs it.** The journal grows until folded. Options: (a) `SessionEnd` hook folds that session's journal (simple, but a crashed session never folds — orphan journals accumulate); (b) a periodic cron/launchd compactor (robust, but adds a background process); (c) fold-on-`SessionStart` (next session cleans up the last). *Recommendation: fold-on-SessionStart (c) — self-healing, no extra process, runs when context is being assembled anyway. Reasonable people could prefer the cron for liveness across long single sessions; surfacing.*

3. **Relevance scoring for recall + miss-recovery is the soft frontier.** The cache algorithms (ARC) tell you *what to evict given access data*; they do NOT tell you *what is relevant to the current prompt* (that's the access signal itself). loam already has TWO relevance paths (S2 topic-file JIT on keyword signal; S3 graphiti semantic search) — the recall hook should lean on S3's existing `search(group_ids)` for semantic relevance rather than building a new scorer. **F2 disagreement with a naive design:** do not build a fresh relevance engine; the frequency layer is new, the relevance layer already exists (S3). Bolt the counter onto S3's retrieval, don't replace it.

4. **Cross-session staleness window.** Session B's recall hook only sees session A's writes *after* A's `Stop` hook fires (turn end), not mid-turn. So liveness is turn-granular, not instant. For Luke's use (concurrent sessions on related work) turn-granular is almost certainly fine — but it is NOT real-time shared state. **Named so it's not a surprise:** if two sessions edit the *same objective* within the same turn, the later fold wins (last-write-wins); the earlier is preserved in the journal (recoverable) but not in the current index. Acceptable for memory; would NOT be acceptable for a shared mutable counter (don't use this design for that).

5. **No product validates the concurrency design at loam's scale.** Hindsight/mem0/SAMEP punt on it; the OS primitives (O_APPEND, rename, ARC) are individually battle-tested but their *composition into a memory layer* is loam-specific. This is an n=1 architectural build, not an adoption — verify the journal-fold + ARC-rotation empirically on a two-concurrent-session test before trusting it (per loam's n1-architectural rule: prior-informed, large effect, binary verifier "did session B see session A's memory, yes/no").

6. **Abstraction-voice (Luke's #8) is a presentation rule, not a mechanism here** — but it constrains this design: the journal, counters, eviction, and folds must be *completely invisible* to the user. The user never hears "I rotated your hot index" — they hear "you mentioned last week you're focused on the fiction pipeline, so I've got that context loaded." All the machinery in §2–4 lives below the abstraction line by default.

---

## 6. Sources (trust-tiered)

**Tier-1 (primary / OS-semantics / authoritative):**
- [POSIX O_APPEND atomic-append semantics — Paul Khuong](https://pvk.ca/Blog/2021/01/22/appending-to-a-log-an-introduction-to-the-linux-dark-arts/)
- [Are File Appends Really Atomic? — Not The Wizard](https://www.notthewizard.com/2014/06/17/are-files-appends-really-atomic/)
- [python-atomicwrites (write-temp + atomic rename)](https://python-atomicwrites.readthedocs.io/)
- [Claude Code subagent docs — memory: frontmatter + session hooks](https://code.claude.com/docs/en/sub-agents) (via L5 deep-2)

**Tier-2 (operator / academic / plausible):**
- [Hindsight — Claude Code shared memory bank](https://hindsight.vectorize.io/blog/2026/05/06/claude-code-subagents-shared-memory) (session-hook architecture; concurrency NOT documented)
- [mem0 — State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026) (multi-scope identity model; 2026 production gaps)
- [SAMEP — Secure cross-agent context protocol (arXiv:2507.10562)](https://arxiv.org/abs/2507.10562) (abstract only — full mechanism not extracted)
- [Cloudflare — Agent Memory](https://blog.cloudflare.com/introducing-agent-memory/)
- [AutoGen Discussion #7144 — shared multi-agent state / race conditions](https://github.com/microsoft/autogen/discussions/7144)
- [DEV — 7 AI Agent Orchestration Patterns (propose-validate-commit)](https://dev.to/dohkoai/7-ai-agent-orchestration-patterns-for-scaling-concurrent-systems-with-production-code-1onc)
- [FreqRec — adaptive LFU-LRU hybrid eviction](https://www.researchgate.net/publication/400479709_FreqRec_A_Lightweight_and_Adaptive_LFU-LRU_Hybrid_Policy_for_Cache_Block_Replacement)
- [LRU vs LFU caching concepts](https://medium.com/@alxkm/introduction-to-lru-and-lfu-caching-concepts-implementations-and-practical-use-cases-ab90f2e168bd)
- [DEAP Cache — deep eviction/admission/prefetching (arXiv:2009.09206)](https://arxiv.org/pdf/2009.09206)
- [CRDTs: Theory and Practice (git as CRDT / append-only G-Set)](https://blog.psychollama.io/crdts-theory-and-practice/)
- [Git merge-conflict vs CRDT](https://zenn.dev/hina_dev/articles/git-merge-conflict-crdt-intro?locale=en)
- [HN — git-bug CRDTs / per-actor append log](https://news.ycombinator.com/item?id=47142157)

**Tier-0 (verified locally):**
- `memory-architecture.md` (storage layer; §3.2 demotion rule this doc makes mechanical)
- `l5-context-memory-deep-1.md` (`queue_status_inject.py` = 80% of recall hook; UserPromptSubmit reliable injection path; #15174 SessionStart-compact bug)
- `l5-context-memory-deep-2.md` (subagent `memory:` = the `agent_id` scope; siloing limitation)
</content>
</invoke>
