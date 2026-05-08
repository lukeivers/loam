# Component — Memory System

**Created:** 2026-04-17 16:32 CDT. **State:** `COMPLETE — sealed 2026-04-18 12:08 CDT.** Full build landed with all D5–D13 complete, every v1.0 + v1.1 acceptance criterion satisfied, no halts, 30 tests green. Five follow-ons named at the end of this file are non-blocking and will be picked up when the primitives they depend on land.

---

## Parent objective (from spec v1.0)

Knowledge must be managed such that:
- Accrual: everything other than extremely ephemeral knowledge is saved; knowledge is time-locked; knowledge is overridable (superseded entries are marked, not deleted).
- Retrieval: right knowledge at right time based on context; retrieval has bounded context-window cost.

Full acceptance criteria at behaviour level — see objectives spec v1.0, section "Knowledge — accrual and retrieval, as separate concerns."

## Why this is the first component

The memory system was flagged with uncommon emphasis (four "really"s). It is the non-negotiable top priority of the rebuild and therefore the first research-and-proposal cycle.

## Artifacts

- `research-plan.md` — drafted 2026-04-17, awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-17 16:32 CDT — component created; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-17 16:38 CDT — research plan revised per feedback recorded: existing LLM-harness memory solutions (Cognee, MemPalace, Letta/MemGPT, Zep, Mem0, and others) become the leading survey; build-from-scratch evaluation becomes conditional on no existing solution meeting the spec.
- 2026-04-17 16:45 CDT — Claude-only constraint refined per clarification recorded: capabilities within Max-subscription scope use Claude without alternative consideration; capabilities outside Max scope (embeddings, etc.) are evaluated vendor-free. Zero-carryover confirmed as a hard constraint, no longer inference recorded.
- 2026-04-17 16:46 CDT — owner approved the research plan ("do it"). General-purpose Agent dispatched with the research plan as brief.
- 2026-04-17 16:54 CDT — Agent returned after ~7 minutes of research across existing LLM-harness memory solutions. Research document produced at `research.md`. Primary recommendation: conditional adopt of Graphiti (Zep's open-source temporal knowledge graph) with Kuzu embedded graph DB, local Ollama embeddings, Claude (inside Max) for LLM steps. One halt signal raised against spec clause U1(c) — byte-identical memory preservation through upgrade — which presupposes flat-file substrate and cannot be met by any graph-DB-backed store. Agent-proposed resolution: revise U1(c) to semantic-preservation / round-trip fidelity.
- 2026-04-17 17:02 CDT — the owner partially reviewed v1 and said the framing was "over-constricted." the primary persona initially interpreted this as "relax the halt-on-miss rule" and drafted v2 accordingly.
- 2026-04-17 17:03 CDT — owner authorised v2 dispatch without further review. Second general-purpose Agent dispatched with v2 plan.
- 2026-04-17 ~17:12 CDT — v2 agent returned. Primary recommendation: Graphiti on Kuzu + Claude-via-Max + local Ollama embeddings. Produced eight proposed spec revisions (load-bearing one: U1(c) byte-identical → semantic-preserved round-trip-verified). No halts raised (because v2 plan had removed the halt rule). Top beyond-spec features identified: provenance of knowledge, context-aware retrieval, per-episode retention class.
- 2026-04-17 ~17:15 CDT — **the owner correction: misread "over-constricted."** the owner meant the SPEC was too tight (needing revision), not the PROCESS. The v1 halt was correct behaviour; loosening halt-on-miss undoes the point of approval-gated work. v2 plan corrected; primary persona's memory updated with the calibration lesson. The v2 research findings remain valuable (same spec-revision proposals the halt would have produced, just framed as proposals rather than halts).
- 2026-04-18 08:45 CDT — the owner read v2 partially and delivered four items: (1) event-log leak identified at multiple points in the research; correction staged for proposal phase — memory emits observability records, doesn't write into an assumed log; (2) Gap 4.1 accepted: U1(c) byte-identical → semantic round-trip equivalence; (3) three new objectives proposed for v1.1: comprehensive accrual, process-of-arrival capture, documentation bundling; (4) no need to redo the research. Annotations added to `research-v2.md`; v1.1 revision list below.
- 2026-04-18 ~08:52 CDT — owner flagged a further leak: the research proposes mining `memory/daily` for the retrieval test set. Rejected — prototyping data must be synthetic, genuinely unrelated to the existing workspace or old pOS content. A4 annotation added to `research-v2.md`. Adaptation-scope item 6 (retrieval test set) shifts from owner-curation of history to synthetic-data generation with owner-curated ground truth.
- 2026-04-18 08:53 CDT — owner accepted revisions #2–#12 on the v1.1 spec list and flagged channel support as a missing objective.
- 2026-04-18 08:58 CDT — owner approved reformatted #13 (channel-agnostic interaction) in spec-native register; v1.1 addendum appended to the objectives spec with all 13 revisions.
- 2026-04-18 09:18 CDT — the owner's rebuild-wide decision: implementation language is Python, not Ruby. Captured in rebuild proposal, memory proposal, STATE rules, and primary persona's memory.
- 2026-04-18 09:23 CDT — owner approved recommendations on all four open questions in the memory proposal; proposal locked.
- 2026-04-18 09:24 CDT — Handoff brief drafted for the prototyping phase (D1 Graphiti hosting, D2 synthetic test set, D3 embedding assessment, D4 extraction cost baseline). Scoped deliberately to prototyping only; full-build brief follows after prototyping returns.
- 2026-04-18 09:33 CDT — owner reviewed the brief and approved dispatch; one correction noted (branch-on-existing-repo was the decision, not inference recorded — brief corrected). General-purpose Agent dispatched.
- 2026-04-18 ~10:15 CDT — Agent returned after ~48 minutes of prototyping. All four deliverables complete, no halts. Branch `pos-v2` created on existing repo (orphan from main; main untouched); worktree at `pos-v2/`. Three commits on pos-v2. Bundled docs produced at `memory-system/docs/` (prose-explanation, architecture, assumptions). **Six call-outs staged for the full-build brief:** (1) pin graphiti-core 0.28.2 with local Kuzu-driver patches until upstream lands fixes; (2) add a temporal-filter wrapper at pOS layer — Graphiti's compound DateFilter fails on Kuzu; (3) default embedding model nomic-embed-text; (4) default extraction LLM claude-haiku-4-5; (5) add Kuzu chaos-durability test as a prototype priority before production-ready; (6) the owner's test-set label approval required before the upgrade-fidelity harness uses it as a gate.
- 2026-04-18 10:40 CDT — owner delegated label approval to the primary persona, citing insufficient context to label meaningfully. reviewed all 44 pairs against the synthetic world; 43 accepted as drafted (the builder's work was thorough); one correction on q33 (temporal "active in October" — adopted strict reading, dropped Halcyon from expected). Test set marked approved by the primary persona in lieu of the owner in the JSON header.
- 2026-04-18 ~10:42 CDT — Proposal addendum landed with the six prototyping-return refinements; proposal's approved body preserved unchanged.
- 2026-04-18 10:45 CDT — Full-build handoff brief drafted at `brief-full-build.md`. Covers D5–D13 (eight remaining adaptations + chaos-durability test + extended docs); integrates the six call-outs as hard constraints; names two primary-persona inferences for the builder to challenge. Awaiting owner's review before dispatch.
- 2026-04-18 10:48 CDT — owner approved ("approved"). General-purpose Agent dispatched against `brief-full-build.md` for the full-build work.
- 2026-04-18 ~11:28 CDT — Agent returned after ~40 minutes. All D5–D13 complete, no halts, single commit `8b28f6d` on `pos-v2`. Test-set pass rates overall 63.6% (temporal went from 0% → 66.7% with the D8 wrapper as designed; multi-hop dipped slightly due to LLM-extraction variance, within envelope). Chaos-durability all three scenarios (kill-mid-ingest, kill-mid-query, WAL recovery) PASS first-run. Refreshed cost baseline: ~$54.12/year at 3,000 events; $270.58 over 5 years. Process-of-arrival overhead ~$0.0215/dispatch. 30 tests passing. Extended documentation bundled at `memory-system/docs/` (7 files: architecture, prose-explanation, deliverables-d5-d13, data-flow, relationship-map, chaos-durability-report, assumptions). Recommended next action: declare memory component complete; follow-ons (not blocking) named below.

---

## Follow-ons surfaced by the full-build return (not blocking memory release)

1. Wire the real scope-of-work primitive when that component lands (replace `MockScopeSource`).
2. Wire the real dispatch primitive when that component lands (replace mock producer in D11).
3. Build the observability aggregator as a JSONL consumer of memory's OTel emissions.
4. Build the self-upgrade framework around `src/upgrade.py` (memory's fidelity harness plugs in when the framework exists).
5. Run a 250k-edge stress chaos test before long-term-volume durability claims go beyond prototype scale.

---

## v1.1 spec revisions — staged for confirmation

Each row below is a proposed revision to objectives spec v1.0. The decision on each unblocks proposal phase. Format: `[status] — revision`.

| # | Source | Status | Revision |
|---|--------|--------|----------|
| 1 | Gap 4.1 (research §4.1) | **CONFIRMED 2026-04-18 08:45** | Retire U1(c) byte-identical. Replace with semantic round-trip equivalence — pre-upgrade probe queries + post-upgrade replay, drift-report threshold for pass/fail. Kuzu DB snapshot preserves physical reversibility. |
| 2 | the owner A3.1 (2026-04-18) | **CONFIRMED 2026-04-18 08:53** | **Refine accrual behaviour:** "extremely ephemeral" is narrow — current-CPU readings, ticking clocks, volatile UI state. Nearly everything else is saved: conversations, decisions, research, work. The ephemerality rubric enumerates what is *excluded,* not what is *included.* |
| 3 | the owner A3.2 (2026-04-18) | **CONFIRMED 2026-04-18 08:53** | **New objective — process-of-arrival capture:** every background dispatch emits a stream-of-consciousness log during execution; the stream is summarised and ingested into memory alongside the dispatch's output. Memory records not just outcomes but the reasoning path. Dependency on the dispatch primitive. |
| 4 | the owner A3.3 (2026-04-18) | **CONFIRMED 2026-04-18 08:53** | **New cross-cutting objective (Architectural layer) — human-readable documentation bundled:** every pOS component ships with human-readable documentation — prose, diagrams, flowcharts, relationship maps — bundled alongside the component. Applies to every component, not just memory. |
| 5 | Research §7 / §8.1 | **CONFIRMED 2026-04-18 08:53** | **New objective — 4-dimensional temporal model** (valid_at, invalid_at, created_at, updated_at). Graphiti's native model; spec currently has only creation timestamp + supersession pointer. |
| 6 | Research §7 / §8.2 | **CONFIRMED 2026-04-18 08:53** | **Refine supersession to automatic-with-audit:** the system infers supersession via LLM-assisted contradiction resolution; every inferred supersession writes an audit record the user can challenge. Today the spec is silent on "who decides." |
| 7 | Research §8.4 | **CONFIRMED 2026-04-18 08:53** | **New objective — provenance of knowledge:** every derived fact points back to the source episode(s) it was derived from. "Why do we believe X?" is a first-class query. |
| 8 | Research §8.5 | **CONFIRMED 2026-04-18 08:53** | **Refine R1 — multi-hop retrieval:** retrieval must support multi-hop graph traversal, not just semantic top-k. |
| 9 | Research §8.6 | **CONFIRMED 2026-04-18 08:53** | **New objective — context-aware retrieval:** retrieval can be re-ranked by node-distance from an anchor node (e.g. current scope's primary entity), not only by query similarity. |
| 10 | Research §8.3 | **CONFIRMED 2026-04-18 08:53** | **New objective — per-episode retention class:** each ingested episode carries a retention-class tag (normal, derived-only, ephemeral). Derived-only persists structured facts, discards raw text. Privacy-governance primitive. |
| 11 | Research §8.7 | **CONFIRMED 2026-04-18 08:53** | **Refine Observability primitive — adopt OpenTelemetry:** pOS observability exposes OTel as the internal-operation trace format. Applies framework-wide, not just memory. *(Resolve alongside A1 event-log correction.)* |
| 12 | Research §8.8 | **CONFIRMED 2026-04-18 08:53** | **Refine Cost governance — per-prompt-type cost attribution:** token/cost tracking aggregated by prompt name, not only per-session. |
| 13 | the owner 2026-04-18 08:53 | **CONFIRMED 2026-04-18 08:58** (conditional on spec-native formatting; delivered) | **New objective under User-facing layer — Channel-agnostic interaction.** Final wording matches the user-facing bullet style: behaviours listed declaratively (reachability across Claude-supported channels; zero setup for defaults; onboarding walks through optional channels; voice/context consistency across channels; zero pOS change when Claude adds a channel); acceptance as three testable criteria. See v1.1 addendum in the objectives spec for the landed text. |
