# keep-pace — The Right-Things-at-the-Right-Time Problem (Surfacing)

**Date:** 2026-05-28
**Status:** research (external + foundation-read; design recommendations, no implementation)
**Owner:** Luke Ivers
**Author:** strategy research over the surfacing frontier
**Research dimension:** RIGHT-THINGS-AT-THE-RIGHT-TIME — dynamic retrieval, relevance ranking, working-set management, and especially **context-miss detection + on-demand mid-conversation retrieval**. The storage layer (`memory-architecture.md`) is largely solved; this doc covers the part it did not: deciding *what to load per task* and *recovering when the loaded context does not match the request*.

**Frame against Luke's vision:** the model CAN store everything; the only real problem is *"ensuring the right things surface at the right times."* Tonight's failure was the assistant forgetting/failing-to-surface relevant things *while actively working on related topics.* This doc's job is the surfacing engine that stops that — built on a Claude Code harness whose memory is markdown files + an optional MCP store, serving a non-technical user.

---

## 0. The spine in five sentences

The surfacing problem decomposes into four mechanisms the best 2026 agentic-memory systems converge on, and all four are buildable on loam's file+hook substrate without an embedding API. **(1) Per-prompt retrieval** — a `UserPromptSubmit` hook embeds/keyword-matches the user's actual prompt against the memory store and injects the top-N relevant items *before* Claude sees the prompt, so relevance is decided by what was *just typed*, not only by what loaded at session start (claude-mem, claude-memory, the unified-hooks pattern all do exactly this). **(2) Context-miss detection** — a *gate* (the Context Awareness Gate's Vector-Candidates method) measures whether the current prompt's similarity to the loaded/available context falls below the relevant-pair distribution; if it does, the loaded context is *wrong for this request* and the system must fetch the right memory *now* rather than proceeding as though context exists — this is precisely Luke's requirement #5. **(3) Working-set rotation** — frequency+recency scoring (the same orthogonal pair every cache-eviction system uses) plus predictive prefetch (PBKV) keeps the bounded hot index tied to the user's *current* scope of work, rotating cold items out and likely-needed items in, which is Luke's requirement #4/#7. **(4) Cross-session propagation** — keep the memory layer *outside* any one session (files + optional MCP), have every session write durably and every session's per-prompt hook read live, so simultaneous sessions cross-load (requirement #3). The hard, loam-specific recommendation: build the retrieval and the gate on **BM25/keyword over the markdown corpus, not embeddings** — the corpus is small (113 files) and highly technical (slugs, AC-IDs, exact terms), the regime where sparse retrieval *beats* dense and needs no API (honoring `feedback_no_anthropic_api_key`).

---

## 1. What the best agentic-memory systems do (2026 state of the art)

Source: [State of AI Agent Memory 2026 (mem0)](https://mem0.ai/blog/state-of-ai-agent-memory-2026); [Memory for Autonomous LLM Agents: Mechanisms, Evaluation, Frontiers (survey, arXiv 2603.07670)](https://arxiv.org/html/2603.07670v1); [Designing Agentic Memory in 2026](https://thenuancedperspective.substack.com/p/designing-agentic-memory-in-2026); [MemMachine (arXiv 2604.04853)](https://arxiv.org/pdf/2604.04853).

The 2026 consensus, distilled:

1. **Memory is a component separate from the context window.** Working memory = the live context (loaded files, current conversation, recent tool results). Long-term memory lives in an external store; the job of the *surfacing layer* is to move the right slice from long-term → working memory at the right moment. loam already has this split (MEMORY.md index = working; topic files + S3 graph = long-term). The gap is the *mover*.

2. **Retrieval is per-query, multi-signal.** "Relevant memories are retrieved using semantic similarity, keyword matching, and entity matching, then injected into the context window *before the model responds*." The retrieval is triggered by the *current query*, not only at session start. MemMachine adds **contextualized retrieval** — expand a nucleus match with its neighboring episode context, because the relevant evidence is often distributed across adjacent turns/entries (directly applicable: when loam matches `feedback_X.md`, also surface its declared composes-with siblings).

3. **Memory is distilled, not logged.** "Memory serves as a compressed and distilled representation of past information, selectively extracting salient details, removing irrelevant information." The unified-hooks "dream phase" (below) enforces *merge-not-append*: memories are living documents rewritten when new events contradict them, not append-only logs. This is loam's existing "update the CLAUDE.md after every correction" rule, mechanized.

4. **Selective forgetting / working-set management is a first-class competency.** [MemoryAgentBench (ICLR 2026)](https://github.com/HUST-AI-HYZ/MemoryAgentBench) probes four competencies: accurate retrieval, test-time learning, long-range understanding, **and selective forgetting**. A memory system is graded on what it *drops from the working set*, not only what it keeps in the store. This validates Luke's rotation intuition (#7): the hot index must shed cold items as scope shifts.

5. **Learned control of the memory operations.** The survey frames store/retrieve/update/summarize/discard as *callable tools* a controller invokes (MemGPT/Letta self-edit memory in the reasoning loop; AgeMem trains the operations via RL). loam's lighter, API-free analog: deterministic hooks + a `claude -p` controller call only where judgment is genuinely needed (e.g. the dream-phase distillation), not an RL policy.

---

## 2. Per-prompt retrieval — the surfacing mechanism (THE core of requirement #1, #5)

This is the single most directly portable pattern, and it is exactly what tonight's failure needed: relevance decided by *what the user just typed*, not only by what loaded at session start.

### 2.1 The working pattern (three independent implementations agree)

Sources: [claude-mem hooks architecture](https://docs.claude-mem.ai/hooks-architecture); [claude-mem UserPromptSubmit hook (DeepWiki)](https://deepwiki.com/thedotmack/claude-mem/3.1.2-userpromptsubmit-hook); [LupoGrigi0/claude-memory](https://github.com/LupoGrigi0/claude-memory); [Unified Agentic Memory Across Harnesses Using Hooks (TDS)](https://towardsdatascience.com/unified-agentic-memory-across-harnesses-using-hooks/).

The shared flow, fired on **every** `UserPromptSubmit` (before Claude processes the prompt):

1. Take the user's prompt text.
2. Score it against the memory store (embeddings, keyword, or hybrid).
3. Inject the top-N matches into context as `Relevant memories: [...]` via stdout / `additionalContext`.
4. **Skip trivial prompts** (yes/no, bare commands) and **stay silent when nothing matches** — no noise injection.
5. Hard timeout (claude-memory: 5s; never blocks the turn), one-shot per prompt.

**Two real implementations, two retrieval substrates:**

| System | Store | Retrieval | Latency | Cost | N injected |
|---|---|---|---|---|---|
| [claude-mem](https://docs.claude-mem.ai/hooks-architecture) | SQLite | **FTS5 full-text (keyword only)**, `ORDER BY rank LIMIT 20`; progressive-disclosure index injected, full detail via MCP search on demand | 45ms avg / 250ms p99 | $0 (local, no API) | top-20 index lines |
| [claude-memory](https://github.com/LupoGrigi0/claude-memory) | Qdrant vectors | **Hybrid** vector+keyword + **time-decay** (≈58-day half-life favoring fresher) | ≤5s timeout | ~$0.00002/query (OpenAI embed) | max 3 (configurable) |

**The loam-load-bearing observation:** claude-mem proves the *whole pattern works with zero embedding API* — FTS5 keyword search, 45ms, $0, with progressive disclosure (inject the index, fetch detail JIT). That is loam's exact architecture (`memory-architecture.md` §3.3 index-vs-detail + §3.2 warm-JIT) plus the missing *trigger*: a per-prompt hook that decides *which index lines are relevant to this prompt* instead of always-loading the whole index.

### 2.2 Why this fixes tonight's failure

The failure was: assistant working on related topic X, fails to surface the on-file memory about X. Today loam loads the *whole* MEMORY.md index at session start (and it truncates — `memory-architecture.md` FM-1) and then never re-evaluates relevance against the actual prompts. The per-prompt hook flips this: when the prompt mentions X, the hook matches `feedback_X.md` (or the relevant FIDRAFT/plan-doc/objective) and injects a high-salience pointer *into the turn where X is live*. Relevance is recomputed every turn against the real query — the definition of surfacing-at-the-right-time.

---

## 3. Context-miss detection — recognizing the loaded context is WRONG (requirement #5, the hard frontier)

Per-prompt retrieval surfaces *more*. Context-miss detection is the harder, distinct capability Luke named: **recognize that the loaded/guessed context does NOT match the current request, and stop proceeding as though it does.** The formal mechanism exists and is cheap.

### 3.1 The Context Awareness Gate (CAG) + Vector Candidates

Source: [Context Awareness Gate for Retrieval Augmented Generation (arXiv 2411.16133)](https://arxiv.org/html/2411.16133v1).

CAG decides — *without invoking an LLM* — whether a query is in-scope for the available context. The **Vector Candidates** method, O(1) per query after a one-time precompute:

1. **Offline (one-time, O(C) for C contexts):** generate ~3 pseudo-queries per memory item; compute the cosine-similarity *distribution* of genuinely-relevant query↔context pairs.
2. **Online (per query):** compute the query's max similarity to all contexts.
3. **Decision rule:** `if max_similarity(query, contexts) > Policy(Distribution) − Threshold: use retrieval; else: the query is OUTSIDE the knowledge scope — do NOT force-load irrelevant context.`

The empirical separation is large and clean: on their dataset, **relevant pairs median 0.716** (95%+ above 0.55); **irrelevant pairs median 0.039** (95%+ below 0.21). A query whose best match sits in the low band is a *miss*. Measured payoff: context relevancy 0.06 → 0.684 (≈11×); answer relevancy 0.186 → 0.821. The companion result across the adaptive-RAG literature: *"adding a relevance-evaluation gate and query-rewriting loop can cut RAG query failure rates in half"* ([Agentic RAG: Self-Correcting Retrieval](https://letsdatascience.com/blog/agentic-rag-self-correcting-retrieval); [Self-RAG, arXiv 2310.11511](https://arxiv.org/pdf/2310.11511); [Adaptive-RAG]; [Self-Routing RAG, arXiv 2504.01018](https://arxiv.org/pdf/2504.01018)).

### 3.2 The loam translation (the genuinely novel piece for a file-based harness)

CAG's insight maps onto loam *without* embeddings if you use the **score gap** rather than absolute cosine. On every `UserPromptSubmit`, the retrieval hook already computes a BM25 score for the top match. Add a gate:

- **MATCH (top BM25 score above the in-corpus relevant-band threshold):** surface the matched memory normally (§2).
- **MISS (top score in the low band — the prompt's terms barely hit anything loaded or in the hot index):** this is the context-miss signal. The hook emits a **high-salience steering note** into context: *"This request does not match the loaded working set. Before answering, run a broader memory sweep: grep the full topic corpus / FIDRAFT / plan-docs / objectives for [salient terms], and load what fits."* This converts a silent miss into an explicit, in-turn instruction to recover — Luke's exact requirement that the system "must NOT keep going as though the context doesn't exist."

The gate is the difference between a retriever (surfaces more) and a *self-aware* retriever (knows when it has surfaced nothing useful and says so). It is ~20 lines on top of the §2 hook and needs no model call.

### 3.3 Why a gate beats always-injecting

The CAG paper's core finding — *forced retrieval of irrelevant context actively hurts* (relevancy 0.06 under blind RAG) — is the same "lost in the middle" / context-distraction failure the L5 scout flagged ([Liu et al. 2307.03172](https://arxiv.org/abs/2307.03172)). A naive "always inject top-3 memories" hook would *add* noise on off-topic turns. The gate's silence-on-miss + steer-on-miss is what keeps injection precise. This is also why N must be small (claude-memory caps at 3) and silence-when-nothing-matches is mandatory.

---

## 4. Working-set rotation + predictive preload (requirements #4, #7)

Luke's mechanism intuition — *rotate things in/out of the always-loaded index (hard size cap) so loaded memory ties to current scope* — is exactly cache-eviction theory, and the agent-specific version exists.

### 4.1 Frequency + recency (the two orthogonal eviction signals)

Source: [DEAP Cache (arXiv 2009.09206)](https://arxiv.org/pdf/2009.09206); cache-eviction literature via the prefetch search.

The durable finding: **frequency and recency are orthogonal** and the best policy blends LRU (recency) and LFU (frequency) rather than picking one. For loam's hot index this is the promotion/demotion rule `memory-architecture.md` §3.2 left as "lowest-value pointers demote," now given a concrete score:

> `hotness(memory) = w_f · access_frequency + w_r · recency_decay + w_s · current_scope_match`

where `current_scope_match` is the BM25 score of the memory against the *current working topic* (recent prompts / active plan-doc / active objective). When the index approaches its byte cap, demote the lowest-hotness pointers to cold (file stays, index line drops — `memory-architecture.md` §3.2). This is the automatic rotation that keeps the bounded hot index tied to current scope *without a human cleanup*.

### 4.2 Predictive preload — learn what the user frequently asks for (requirement #4)

Source: [PBKV — Prediction-based KV-Cache Management for Dynamic Agent Workflows (arXiv 2605.06472)](https://arxiv.org/abs/2605.06472); [Predictive cache systems (access-pattern-by-context)](https://patents.google.com/patent/US5305389A/en).

PBKV predicts which cache entries a workflow will reuse by fusing *historical workflow patterns* + current context, then prefetches them — 1.85× over LRU on dynamic workflows. The loam analog (no GPU, no neural prefetcher needed): a lightweight **access log** the per-prompt hook already could write (which memories matched, per session, per topic). Periodically (a `Stop`-hook or scheduled `claude -p` "dream" pass) mine the log: *"in fiction-writing sessions, the canon-rules and the active-chapter plan-doc are surfaced 90% of the time"* → preload those at SessionStart for that workspace/topic. This is requirement #4 (learn frequent asks, preload likely context) built on a frequency table, not a model — cheap, inspectable, file-resident.

### 4.3 Selective forgetting is graded, not incidental

Per MemoryAgentBench (§1.4), dropping the right things from the working set is a measured competency. loam's cold-tier (`memory-architecture.md` §3.2) + the hotness score (§4.1) operationalize it: forgetting = demotion to cold, fully reversible (the file and its searchability persist), never deletion. This satisfies Luke's "WITHOUT erasing or abandoning old work" constraint exactly.

---

## 5. Cross-session propagation (requirement #3 — simultaneous sessions cross-load)

Source: [Unified Agentic Memory Across Harnesses Using Hooks (TDS)](https://towardsdatascience.com/unified-agentic-memory-across-harnesses-using-hooks/); [claude-mem SessionStart](https://deepwiki.com/thedotmack/claude-mem/3.1.1-sessionstart-hook).

The architectural principle that makes simultaneous-session cross-loading work: **keep the memory layer OUTSIDE the harness; every harness/session plugs into it.** Three roles:

- **Write (every session, continuously):** hooks log events durably; the dream/Stop phase distills them into living markdown (merge-not-append).
- **Read (every session, per prompt):** the §2 UserPromptSubmit hook reads the *current* store state live — so a memory written by session A is matchable by session B's very next prompt.
- **The store is the shared substrate:** files on disk (loam's corpus) + optional MCP — not in-process state siloed to one session.

**loam already has this substrate** — "files are the only memory" *is* the out-of-harness shared layer; the corpus, FIDRAFT, plan-docs, and `workstream-queue.yaml` are read by any session. The cross-session gap is narrow: the per-prompt read (§2) must read the file *fresh each turn* (not cache it at session start), so a sibling session's just-written memory surfaces immediately. One caveat from the field: native subagent `memory:` is **per-agent siloed** (L5 deep-2 §3) — cross-session sharing must go through the *shared file corpus / MCP*, NOT through subagent memory dirs. Concurrent-write safety (two sessions appending the access log / a memory file) needs an atomic-append or lock discipline — a named risk, not a blocker (append-only logs + last-writer-wins distillation is the standard mitigation).

---

## 6. Objective tracking that keeps pace (requirement #6) — surfacing applied to ODD

Luke's #6: loam's objective-tracking has gone stale; likely ZERO objectives on file for his *actual current* work (fiction pipeline; revenue/consulting). The surfacing engine is the fix mechanism, applied to a new memory *kind*: **live objectives.**

- **Objectives are a hot-tier memory kind** (a new row in `memory-architecture.md` §3.1's store map): one terse line per active objective in the always-loaded index, detail in a per-objective file, subject to the same hotness rotation (§4.1) — a finished objective demotes to cold, never erased.
- **Continuous refinement, not re-authoring:** a `Stop`-hook (or scheduled `claude -p` dream pass) compares recent session activity against the on-file objectives; when activity drifts from any objective (the §3 gate fires at the *objective* granularity — recent work doesn't match any logged objective), it surfaces *"current work doesn't map to a tracked objective — propose adding/refining one?"* This is the swarming `CycleVerdict.needs_fresh_start` drift-signal (Lens 5) applied to objective-tracking: detect drift, surface, refine — never silently continue a diverged objective set, never erase the old.
- **Composes with ODD (Lens 3):** objectives stay observable-outcome-shaped; the refinement adds/edits objective files, it does not prescribe method. The new objectives for the fiction pipeline and revenue push get authored *from observed activity*, then maintained by the same surfacing+drift loop.

---

## 7. The abstraction-voice (requirement #8) — load-bearing, and a SURFACING concern

Luke: the assistant must talk as an **abstraction over hard concepts BY DEFAULT** — never make the non-technical user hold file names, mechanisms, or implementation detail. *"Just because the assistant can remember doesn't mean the user can."*

This is a Lens-2 translation requirement and it intersects surfacing directly: **the memory hook injects technical pointers into the persona's context, NOT into the user's view.** The architecture must keep these two surfaces strictly separate:

- **Inbound (hook → persona):** rich, technical — file paths, slugs, BM25 hits, the steer-on-miss note. The persona consumes this.
- **Outbound (persona → user):** the persona *translates* — it says *"I remembered you decided X last week"*, never *"per `feedback_X.md` / matched index line 34."* This is exactly `feedback_translate_outbound_too` (prose-first, no SHAs/AC-IDs/paths) applied to memory-surfacing.

The surfacing engine therefore must never leak its own mechanism into the reply. A concrete guard: the existing Telegram-reply `PreToolUse` jargon/path check (loam already runs `translation_jargon_check.py`) is the right structural enforcement point — extend its blocklist to catch leaked memory-mechanism tokens (`feedback_`, `MEMORY.md`, raw topic-file paths) in outbound replies. Default mode is full abstraction; go technical only when the user asks or on demonstrated-depth topics — a per-topic flag the frequency log (§4.2) can actually *learn* (topics where the user consistently engages with detail).

---

## 8. The retrieval-substrate decision: BM25/keyword, NOT embeddings (the hard recommendation)

This is the load-bearing build decision and it cuts against the reflexive "use embeddings" instinct.

Sources: [Sparse vs Dense Retrieval for RAG (ML Journey)](https://mljourney.com/sparse-vs-dense-retrieval-for-rag-bm25-embeddings-and-hybrid-search/); [Dense vs Sparse Retrieval: FAISS, BM25, Hybrid (DEV)](https://dev.to/vf-insights/dense-vs-sparse-retrieval-mastering-faiss-bm25-and-hybrid-search-4kb1); [How BM25 and RAG Retrieve Differently (MarkTechPost)](https://www.marktechpost.com/2026/03/22/how-bm25-and-rag-retrieve-information-differently/); [claude-mem FTS5 architecture](https://docs.claude-mem.ai/hooks-architecture).

The evidence stack says BM25/keyword is the *right* choice for loam, not merely the constraint-compatible one:

1. **Constraint:** loam is subscription-only, no Anthropic API key (`feedback_no_anthropic_api_key`). OpenAI/Gemini embeddings (claude-memory's path) are off the table for the live store. Embeddings would require either a paid API or a local embedding model to maintain — friction loam should not own.
2. **Corpus regime favors sparse:** *"BM25 is fast and effective for keyword queries in small corpus scenarios (under 10,000 documents)"* — loam's corpus is **113 files**. *"If your corpus is highly technical with precise terminology — API documentation, error messages, code snippets — sparse retrieval contributes heavily."* loam's corpus is exactly this: slugs (`feedback_swarming_recursive_decomposition`), AC-IDs, exact mechanism names. Dense retrieval wins on *paraphrased prose over large corpora* — not loam's regime.
3. **Proof of the full pattern at $0:** claude-mem runs the entire per-prompt surfacing loop on **FTS5 keyword search, 45ms, no API**, with progressive disclosure. It is the existence proof that loam's exact need is met without embeddings.
4. **Operational simplicity:** *"no GPU, no embedding model to maintain, no ANN index to rebuild when documents update."* The corpus changes every time a memory is written; an inverted index updates in single-digit ms, an embedding index needs re-embedding. For a corpus written constantly, sparse is the lower-maintenance choice.

**Recommendation:** build retrieval on BM25 (or SQLite FTS5, matching claude-mem) over the markdown corpus. Reserve dense/MCP-vector as an *optional later hybrid layer* only if keyword retrieval demonstrably misses on paraphrase — the field guidance is *"start sparse; add dense as a safety net only on observed keyword-retrieval failures."* The MCP store (the optional half of loam's substrate) is the natural home for a future dense layer if one is ever justified.

---

## 9. The buildable surfacing engine for loam (synthesis — composes on `memory-architecture.md`)

All four mechanisms ride loam's *existing* hook chain (verified in L5 deep-1: loam already runs 5 `UserPromptSubmit` hooks incl. `queue_status_inject.py`, plus `Stop` hooks). No new engine; new hooks + a small index.

| # | Mechanism | Primitive | Serves Luke's req | Substrate | Effort (AI-time) | Confidence |
|---|---|---|---|---|---|---|
| **K1** | **Per-prompt retrieval hook** — BM25/FTS5 over the corpus + hot index; inject top-N relevant pointers; silent on no-match; skip trivial prompts; read store *fresh each turn* | UserPromptSubmit (sibling to `queue_status_inject.py`) | #1, #3 | markdown + SQLite-FTS5 index | 30–60 min | high (claude-mem proves it at $0) |
| **K2** | **Context-miss gate** — if top score in the low band, emit a steer-to-recover note instead of proceeding | same hook, +gate | #5 | score-gap threshold | +20 min | high (CAG mechanism sound; threshold needs in-corpus calibration) |
| **K3** | **Hotness rotation** — `w_f·freq + w_r·recency + w_s·scope_match`; demote lowest-hotness index lines to cold at byte cap | InstructionsLoaded/SessionStart audit (extends `memory-architecture.md` M2) + access log | #4(part), #7 | frequency table | 30–50 min | medium-high (eviction theory solid; weights need tuning) |
| **K4** | **Predictive preload** — mine the access log per workspace/topic; preload high-frequency memories at SessionStart | Stop-hook or scheduled `claude -p` dream pass | #4 | access log | 30–60 min | medium (n=1 per topic until log accrues) |
| **K5** | **Live objectives as a hot-tier kind + drift surface** — objective index + Stop-hook drift check vs recent activity | new store-map row + Stop-hook | #6 | markdown | 40–70 min | medium (drift threshold = K2's gate at objective granularity) |
| **K6** | **Abstraction-voice outbound guard** — extend `translation_jargon_check.py` to block leaked memory-mechanism tokens in replies | PreToolUse (existing Telegram check) | #8 | blocklist | 15–30 min | high (extends a working hook) |

**Sequencing:** K1 first (the surfacing engine — fixes tonight's failure directly). K2 second (cheap add to K1, delivers requirement #5, the hard frontier). K6 in parallel (independent, protects the user-facing promise). K3/K4 next (rotation + preload — the keep-pace half). K5 last-and-longest (objective tracking; depends on K2's gate generalizing to objective granularity).

**K1+K2 together are the answer to tonight's failure and to the named hard frontier:** K1 surfaces the right memory against the live prompt; K2 catches the case where nothing relevant surfaced and forces a mid-conversation recovery sweep instead of proceeding blind.

---

## 10. Risks / forks / RF

1. **OWNER-ASK — BM25 vs hybrid-with-MCP-vector.** §8 recommends sparse-first. Reasonable people could want dense from day one for paraphrase robustness. *Recommendation: sparse-first (constraint + corpus regime + $0 proof all align); add MCP-dense only on observed keyword-miss. The score-gap gate (K2) will itself surface keyword-retrieval failures — it is the instrument that tells you whether a dense layer is ever needed.* Surfacing because the substrate choice is load-bearing and hard to reverse cheaply.

2. **RISK — gate threshold calibration (K2).** CAG's clean band (relevant 0.716 vs irrelevant 0.039) is *cosine on their dataset*; BM25 scores are unbounded and corpus-specific, so the threshold must be calibrated on loam's own corpus (sample real prompts, measure the matched-score distribution). An un-calibrated gate either over-steers (false misses, noisy recovery prompts) or never fires (silent misses persist). Mitigation: ship K1 first, log scores for a week, set K2's threshold from the observed distribution — empirical, not assumed.

3. **RISK — injection noise re-creating "lost in the middle."** Blind always-inject *hurts* (CAG: 0.06 relevancy). The N-cap (≤3–5), silence-on-no-match, and skip-trivial-prompts are not optional polish — they are the precision guarantees. A K1 that injects too eagerly is net-negative.

4. **RISK — concurrent-session write races (K1 fresh-read + K4 access log).** Simultaneous sessions appending the access log or a memory file can corrupt/lose writes. Mitigation: atomic append (open-append-close per line) for the log; last-writer-wins + merge-on-dream for distilled files. Named, standard, not a blocker — but must be designed in, not bolted on.

5. **RISK — abstraction-voice leak through a NEW surface.** K1 injects technical pointers into persona context; if the persona echoes them, requirement #8 breaks. K6 guards the *Telegram* surface; any *other* outbound surface (terminal-as-diagnostic is fine; a future user-facing surface is not) needs the same guard. The guard must be surface-general, mirroring `memory-architecture.md` M2's "store-general guard" reasoning.

6. **GAP (named, deferred) — predictive preload is cold for new topics.** K4 learns from history; a brand-new topic (Luke starts a new venture) has no access-log signal, so preload is empty until the log accrues. K1+K2 cover the cold case (per-prompt retrieval + miss-recovery work from turn one); K4 is an *optimization* on top, not a dependency. Acceptable; noting it so K4 is never treated as the primary surfacing path.

---

## 11. Lens coverage

- **Lens 1 (Claude-leverage):** every mechanism rides native hooks (UserPromptSubmit, Stop, SessionStart/InstructionsLoaded, PreToolUse) + the optional MCP store; the one judgment-needing step (dream-phase distillation, K4) uses `claude -p` per `feedback_no_anthropic_api_key`. No retrieval engine re-implemented — BM25/FTS5 is a library, the orchestration is hooks.
- **Lens 2 (harness + persona value):** K1/K2 reduce translation burden (the persona surfaces the right context so the user never re-explains); K6 enforces the abstraction-voice promise; all map to the continuity/trust/scaling properties of `memory-architecture.md` §2.
- **Lens 3 (ODD):** recommendations are observable-outcome-shaped (retrieval surfaces relevant memory; gate fires on miss; objectives stay current) — ACs authored at build time, method left to the builder.
- **Lens 4 (scope↔confidence):** K1/K2/K6 high-confidence → tight; K3/K4 medium (weights/log need tuning) → looser, calibrate-then-tighten; K5 loosest → drift-threshold is an open empirical question.
- **Lens 5 (swarming):** six independently-shippable items, each a tighter AC than "fix surfacing"; the K5 objective-drift check IS the `needs_fresh_start` drift-signal applied to objectives.
- **Lens 6 (conflict resolution):** the §8 sparse-vs-dense fork surfaced with signals named (constraint, corpus regime, maintenance, reversibility) rather than silently resolved.
- **Lens 7 (ruthless feedback):** the embeddings reflex named and argued against with evidence; calibration/noise/race risks surfaced with mitigations; the abstraction-voice leak named as a new-surface gap.

---

## 12. Source trust-tier summary

- **Tier-1 (primary / peer-reviewed):** [CAG arXiv 2411.16133](https://arxiv.org/html/2411.16133v1); [Self-RAG 2310.11511](https://arxiv.org/pdf/2310.11511); [Self-Routing RAG 2504.01018](https://arxiv.org/pdf/2504.01018); [memory survey 2603.07670](https://arxiv.org/html/2603.07670v1); [MemoryAgentBench ICLR 2026](https://github.com/HUST-AI-HYZ/MemoryAgentBench); [PBKV 2605.06472](https://arxiv.org/abs/2605.06472); [Lost in the Middle 2307.03172](https://arxiv.org/abs/2307.03172); [DEAP Cache 2009.09206](https://arxiv.org/pdf/2009.09206).
- **Tier-2 (working implementations / operator):** [claude-mem](https://docs.claude-mem.ai/hooks-architecture) (FTS5, latency numbers — strong, code-backed); [claude-memory](https://github.com/LupoGrigi0/claude-memory); [Unified Agentic Memory via Hooks (TDS)](https://towardsdatascience.com/unified-agentic-memory-across-harnesses-using-hooks/); [MarkTechPost BM25-vs-RAG](https://www.marktechpost.com/2026/03/22/how-bm25-and-rag-retrieve-information-differently/); [ML Journey sparse-vs-dense](https://mljourney.com/sparse-vs-dense-retrieval-for-rag-bm25-embeddings-and-hybrid-search/).
- **Tier-3 (vendor framing):** [mem0 State of Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026); [Designing Agentic Memory 2026 (substack)](https://thenuancedperspective.substack.com/p/designing-agentic-memory-in-2026).
- **Tier-0 (verified locally / foundation docs):** `/Users/lukeivers/loam/docs/design/memory-architecture.md`; `l5-context-memory-{scout,deep-1,deep-2}.md`; loam's hook chain per L5 deep-1.

**RF on the vein:** the strongest, most loam-applicable findings are (a) the per-prompt UserPromptSubmit retrieval pattern proven at $0 on keyword search (claude-mem), and (b) the CAG context-miss gate, whose *mechanism* (score-gap below the relevant band → miss → recover) ports cleanly even though its absolute cosine thresholds do not. The weakest are the exact tuning constants — BM25 gate threshold, hotness weights, preload frequencies — all of which must be calibrated on loam's own corpus rather than imported. Do not hard-code any imported number.
