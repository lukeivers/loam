# Research Plan — Memory System

**Component:** Memory System. **Gate:** Phase 2 (memory) of the rebuild. **Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

The memory system must deliver every acceptance criterion in objectives spec v1.0 under "Knowledge — accrual and retrieval, as separate concerns," including the behaviour-level criteria for each declared behaviour.

The research does not design the memory system. The research answers the open questions a designer would need answered before writing a proposal.

## Questions the research must answer

The questions are grouped by what they decide. Each question must be answered with options evaluated, a recommendation, and a rationale.

**The survey below comes first.** Existing LLM-harness memory solutions are the starting position; build-from-scratch is the fallback only if no existing solution (used as-is or with light adaptation) can meet the spec's acceptance criteria.

### Prior survey — existing LLM-harness memory solutions

0a. What memory-management solutions currently exist that were designed specifically for LLM harnesses? The survey should include at minimum: Cognee, MemPalace, Letta/MemGPT, Zep, Mem0, and any other actively-maintained solution the researcher surfaces. Claude-native memory features (if any exist as of research date) should also be evaluated.

0b. For each solution: how does it score against every acceptance criterion in objectives spec v1.0 for knowledge accrual and retrieval? A table form is natural here — rows are solutions, columns are criteria, cells are pass / partial / fail with a one-sentence rationale.

0c. Which solutions, if any, meet the spec's acceptance criteria either as-is or with light adaptation the primary persona and the owner would reasonably undertake? Light adaptation means configuration, a thin wrapper, or a small number of contributions upstream — not a substantial fork or rewrite.

0d. If one or more solutions pass 0c, the recommendation is to adopt it (or to pilot one of a shortlist); build-from-scratch questions below become informational rather than decisive. If zero solutions pass, the research proceeds to the build-from-scratch questions below as the operative evaluation.

### Storage substrate *(conditional on 0d — evaluate only if no existing solution passes)*

1. What storage substrate best supports time-locked, append-preferring, queryable knowledge at the scale a single pOS user produces over years? Candidates to evaluate include: SQLite with temporal schema, PostgreSQL with temporal extensions, a dedicated embedded DB (DuckDB, LMDB), flat append-only logs with an index, or a hybrid (append log + queryable index).
2. What are the size/performance projections for a single-user workload over 5 years? (Rough order of magnitude — enough to rule out clearly inadequate choices.)
3. What are the backup, portability, and self-upgrade characteristics of each candidate? (The seven-clause self-upgrade criterion applies: a pOS upgrade must not corrupt or lose the memory store.)

### Time-locking mechanism *(conditional — see 0d)*

4. How is "reproduce the knowledge state at time T" implemented mechanically? Candidates: append-only log with timestamp query, versioned rows, git-style snapshots, event sourcing with materialised views, temporal database features.
5. What are the costs and guarantees of each approach — storage overhead, query latency, correctness guarantees, operational complexity?
6. How does time-locking interact with supersession (below)?

### Supersession *(conditional — see 0d)*

7. What mechanism marks an entry as superseded by another? Candidates: pointer field on the superseded entry, separate supersession edges, tombstone-with-redirect, audit-log of supersession events.
8. How does retrieval discriminate current-active entries from superseded ones, whilst preserving the ability to query past states?
9. Can supersession be partial (an entry corrects a subset of another's facts) or is it strictly whole-entry? What are the trade-offs?

### Ephemerality rubric *(conditional — see 0d; but still relevant if an existing solution requires adaptation for this)*

10. What defines the boundary between "save" and "discard as ephemeral"? Candidates: explicit rules authored per source type, a learned classifier trained on examples, hybrid (rules with human-review fallback), no discarding at all with filtering at retrieval.
11. How is the rubric itself updated over time as the user's preferences change? (Self-correction loop applies.)
12. What are the false-positive and false-negative risks of each approach, and what's the recovery path if the rubric discards something it shouldn't have?

### Retrieval — right knowledge at right time *(conditional — see 0d)*

13. What mechanism surfaces the right knowledge at the right moment? Candidates: embedding-based semantic search (what collection, embedded by what model), active recall triggered by primary-persona context, keyword/tag search, hybrid retrieval with reranking, RAG pipeline.
14. What is the quality measurement — test set structure, precision/recall targets, evaluation frequency? How is the test set generated and maintained?
15. What is the context-window cost budget per retrieval query? (Concrete number; trade-off between recall and cost.)
16. How does retrieval interact with the primary-persona primitive? Is retrieval a capability the persona invokes, a pipeline stage that fires before the persona runs, or both?

### Integration with adjacent systems

17. How does the memory system integrate with the observability layer (replay must reproduce the knowledge state available at a past moment)? What does the event log need to record about memory operations?
18. How does it integrate with self-upgrade? The seven-clause criterion applies — upgrade must preserve memory byte-identically, verifiably.
19. How does it integrate with the scope-of-work primitive? Does a scope carry its own scoped-memory slice, or does it read/write the shared store with attribution?

## Constraints the research must respect

- **Max-subscription-first, vendor-free outside Max.** Any capability that can be accomplished through the owner's Anthropic Max subscription uses Claude — no alternatives considered, no abstractions allowing vendor swap for those parts. For capabilities *outside* the Max subscription's scope (standalone embedding endpoints for retrieval are the obvious case; there may be others the survey surfaces), vendor lock-in is not a concern — candidates are evaluated on merit alone (quality, cost, latency, privacy, self-hosting feasibility). The research must explicitly name which parts of the memory system fall outside Max coverage and therefore get vendor-free treatment, and which parts fall inside Max coverage and therefore must use Claude.
- **Zero carryover from the current pOS memory system.** The existing `memory/daily/`, `memory/people/`, `memory/companies/`, `context/SESSION_CORE.md` layer is not a reference implementation. The research treats memory as a fresh problem. *(Confirmed by the owner 2026-04-17 16:45 CDT.)*
- **No proposals in this document.** The research document evaluates options and recommends; the proposal that follows is a separate artifact, authored from this research and approved before any build work is briefed.
- **ODD-compatible.** Each recommendation must trace back to a spec objective. Options that cannot be tested against a spec objective are noted as untestable and discarded.

## Deliverable — what the research document must contain

A markdown document at `components/memory-system/research.md` with:

1. **The existing-solutions survey (question 0a–0d) as the leading section.** Solutions-by-criteria table, shortlist of passing candidates (if any), and a clear recommendation: adopt a specific solution, pilot a shortlist, or proceed to build-from-scratch.
2. For each subsequent question that remains operative: options evaluated, recommended option, rationale, risks.
3. A dependency map showing how memory interacts with scope-of-work, primary persona, observability, self-upgrade.
4. A complexity estimate (AI-time, honest), with the parts most likely to surprise called out.
5. Any questions that could not be answered without prototyping — with a proposal for how to prototype them (not prototyping them yet).
6. An explicit list of spec acceptance criteria the recommended design will satisfy, and any criteria it cannot satisfy with rationale. *(If any criterion cannot be satisfied — whether by an existing solution or a build-from-scratch design — the research halts and surfaces the conflict rather than proposing something that fails the spec.)*

## What this research is NOT

- Not a build plan. Not a proposal. Not code. The researcher does not modify any files outside `components/memory-system/research.md` and its cited sources.
- Not a survey of the existing pOS memory layer. The researcher does not read `memory/` or `context/SESSION_CORE.md` for design inspiration; they are only permitted to read them if asking "what does the owner currently do with memory in practice" needs an answer, and even then the reading is factual, not inspirational.

## Execution note

This research plan, once the owner approves it, is passed to a general-purpose Agent with the plan itself as the brief. The Agent reads the plan, performs the research, produces `research.md`, and returns. If the Agent concludes any question cannot be answered under the constraints as written, it halts and surfaces the conflict — per decision 11 of the rebuild proposal.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches a general-purpose Agent to conduct the research and produce `research.md`.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks the plan from scratch.
