# Memory System — Proposal

**Component:** Memory System

**Status:** DRAFT — awaiting owner's review and approval before the handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 addendum (both in `docs/rebuild/spec/pos-v2-objectives-spec.md`)
**Informed by:** research v1 (`research.md`), research v2 (`research-v2.md`), and the owner's annotations A1–A4

---

## Summary

Adopt **Graphiti** (Zep's open-source temporal knowledge graph) on embedded **Kuzu**, with **Claude via Max** for all LLM-driven ingestion steps and **local Ollama** for embeddings — the one subsystem outside Max coverage. Build a set of pOS-side adaptation layers to deliver the parts of the spec Graphiti doesn't supply natively (ephemerality filter, scope attribution, observability emission, upgrade fidelity, retention-class tagging, process-of-arrival capture, synthetic retrieval test set, bundled documentation). Prototype the retrieval quality bar with **synthetic-only** data — no mining of current pOS or the existing workspace content. The single largest risk is the synthetic test-set design; prototype it first.

---

## Direction

### Core stack

- **Implementation language:** Python. the owner's rebuild-wide decision 2026-04-18 09:18 — the new pOS is Python-native. Graphiti itself is Python; adaptation layers integrate natively with no language boundary.
- **Knowledge engine:** Graphiti (graphiti-core ≥ 0.28.2), self-hosted as a local MCP service.
- **Graph database:** Kuzu, embedded — zero network dependency.
- **LLM for extraction, contradiction resolution, summarisation, reranking:** Claude via Anthropic Max subscription.
- **Embedding model:** local Ollama (candidate models: Qwen3 or bge-large, to be chosen by the builder on quality-vs-resource trade-off). This is the one component outside Max coverage and is evaluated vendor-free on merit.

### Why this direction

- Graphiti is the sole candidate surveyed that natively implements **bitemporal time-lock, pointered supersession, and first-class namespace partitioning** — the three spec requirements most expensive to retrofit.
- Anthropic LLM client ships out of the box; no wrapper required.
- No fork or upstream rewrite needed. Adaptation lives at the pOS boundary; the engine stays stock.
- Python-native integration. Graphiti is Python; pOS is now Python; adaptation layers call Graphiti directly — no language-boundary marshalling, no MCP-only workaround for async issues.
- Local-first architecture satisfies privacy by default and aligns with Max-first.

### Non-goals of this proposal

- Not a commitment to Graphiti in perpetuity. If retrieval-quality acceptance fails at prototyping, we revisit.
- Not a specification of code structure, file layout, function names, class hierarchies, or line-level design. Those are the builder's call and live in the handoff brief, not here.
- Not a surrounding-infrastructure proposal. This is memory only; observability, event log, self-upgrade framework, scope runtime, primary persona loader are addressed by their own components.

---

## Adaptation layer — what pOS builds around Graphiti

Nine adaptation components, each with a stated objective and acceptance. None prescribe implementation method.

### 1. Ephemerality filter

**Objective:** discriminate episodes to save from episodes to discard at ingest.
**Spec coverage:** v1.0 accrual behaviour + v1.1 R2 (tighten "ephemeral" to narrow exclusion set).
**Acceptance:** a declared exclusion rubric enumerates the narrow ephemeral classes (telemetry readings, ticking clock values, volatile UI state, and similar); a sampled ephemeral-class input is verified absent from storage; anything not on the exclusion list is accrued.

### 2. Scope-of-work mapper

**Objective:** attribute every memory entry to the scope-of-work it was produced within or about.
**Spec coverage:** core primitive — scope of work; v1.0 retrieval.
**Acceptance:** every memory write carries a scope-of-work identifier; retrieval can be filtered by scope; a scope's memory slice is enumerable.
**Dependency:** scope-of-work primitive runtime must exist.

### 3. Observability emission adapter *(A1 correction)*

**Objective:** memory emits structured observability records — OTel spans, token-usage rows, operation audits — in a canonical format for any future consumer.
**Explicit constraint:** memory assumes **no downstream consumer exists yet.** There is no "event log" to write into. Memory publishes; whatever component aggregates observability in future (when the observability layer is designed) subscribes.
**Spec coverage:** v1.0 observability + v1.1 R11 (OpenTelemetry as trace format) + v1.1 R12 (per-prompt-type cost attribution).
**Acceptance:** every memory operation emits a structured record including actor, timestamp, operation, inputs, outputs, prompt name, token usage; records are durable and queryable without requiring a consumer; a sampled operation is reconstructible from its emissions alone.

### 4. Graphiti MCP hosting

**Objective:** run Graphiti as a managed local service available to pOS.
**Acceptance:** the service auto-starts with the system, restarts on failure, exposes a health check, and is queryable through the MCP interface.

### 5. Upgrade-fidelity test harness *(v1.1 R1)*

**Objective:** test that a framework upgrade preserves memory semantically.
**Spec coverage:** v1.1 R1 (U1(c) byte-identical retired; semantic round-trip equivalence landed).
**Acceptance:** a declared probe set of queries runs pre-upgrade and post-upgrade; a drift report compares answers and fails the upgrade if drift exceeds a declared threshold; the underlying Kuzu DB is snapshotted pre-upgrade to preserve physical reversibility.

### 6. Retention-class tagger *(v1.1 R10)*

**Objective:** each ingested episode carries a retention class — `normal`, `derived-only`, or `ephemeral`.
**Spec coverage:** v1.1 R10.
**Acceptance:** `derived-only` episodes produce structured facts in memory but no retrievable raw text; `ephemeral` episodes produce no persisted memory beyond immediate use; retention class is queryable per entry; class-filtered queries return only entries of that class.

### 7. Process-of-arrival capture ingestion *(v1.1 R3)*

**Objective:** background dispatches' stream-of-consciousness logs are summarised and ingested alongside outcomes.
**Spec coverage:** v1.1 R3.
**Acceptance:** a representative background dispatch produces a stream log during execution; the log is summarised (by Claude via Max) and ingested; a retrieval query returns both the outcome and the reasoning path when either is queried.
**Dependency:** dispatch primitive must exist and must emit stream logs in a declared format.

### 8. Synthetic retrieval test set *(A4 constraint; v1.1 R8/R9)*

**Objective:** a curated test set of Q/A pairs exercises retrieval quality (semantic, multi-hop, context-aware, temporal) at acceptance-gate thresholds.
**Hard constraint:** the test set is **synthetic — fabricated scenarios with invented entities**, with **zero carryover** from the existing workspace or current-pOS content. No mining of `memory/daily`, no reading of existing personas, no extraction from current task records.
**Spec coverage:** v1.0 retrieval + v1.1 R8 (multi-hop) + v1.1 R9 (context-aware) + v1.1 R1 (used also in upgrade-fidelity).
**Acceptance:** the test set covers each retrieval mode (semantic top-k, multi-hop traversal, context-aware anchor reranking, temporal `reference_time`); declared precision/recall thresholds pass on a baseline Graphiti deployment; retrieval cost per query stays within a declared token budget.
**Note:** this is the **#1 prototyping-phase risk.** the owner's curation judgment is required for ground-truth labels on the synthetic Q/A pairs; the builder drafts scenarios, the owner approves labels.

### 9. Bundled documentation *(v1.1 R4)*

**Objective:** the memory component ships with human-readable documentation — prose explanation, architecture diagram, data-flow diagram, and relationship map to adjacent components.
**Spec coverage:** v1.1 R4 (cross-cutting; applies to every component going forward).
**Acceptance:** documentation bundles with the component; a representative non-technical reader can answer "what does memory do and how does it fit with the others" after reading the bundled docs alone; absence at release is a release-gate failure.

---

## How v1.1 revisions are honoured (mapping)

| Revision | Honoured by |
|---|---|
| R1 — semantic round-trip upgrade | Adaptation #5 + Kuzu snapshot |
| R2 — narrow ephemerality | Adaptation #1 |
| R3 — process-of-arrival capture | Adaptation #7 |
| R4 — bundled documentation | Adaptation #9 |
| R5 — 4-dim temporal model | Graphiti native (`valid_at`, `invalid_at`, `created_at`, `updated_at`) |
| R6 — supersession with audit | Graphiti native (contradiction resolution + audit edges) |
| R7 — provenance | Graphiti native (episode subgraph) |
| R8 — multi-hop retrieval | Graphiti native (`NODE_HYBRID_SEARCH_RRF` and BFS traversal) + test set #8 |
| R9 — context-aware retrieval | Graphiti native (`center_node_uuid` node-distance reranking) + test set #8 |
| R10 — per-episode retention class | Adaptation #6 wrapping Graphiti's `store_raw_episode_content` |
| R11 — OpenTelemetry observability | Adaptation #3 (engine emits OTel natively; adapter extends framework-wide) |
| R12 — per-prompt-type cost | Adaptation #3 (Graphiti's `TokenUsageTracker`) |
| R13 — channel-agnostic interaction | *Not in scope of this proposal — handled by the onboarding and channel components, which are downstream of memory.* |

Core-spec objectives (v1.0) are satisfied by the combination of Graphiti's native features plus adaptations #1, #2, #5. See §"Acceptance in spec terms" below for the full mapping.

---

## Dependencies and assumptions

### Hard dependencies (memory cannot ship without these)

- **Scope-of-work primitive runtime.** Memory's scope attribution is a foreign key to scope IDs. Scope-of-work is scheduled ahead of memory in Phase 1 of the rebuild proposal, so this sequencing is already correct.
- **Primary persona loader.** Retrieval is invoked by the persona in-turn; without the persona loader there is no caller.

### Soft dependencies (memory is buildable and shippable; these integrate later)

- **Observability aggregator.** Memory emits; the aggregator subscribes when built. No blocking.
- **Self-upgrade framework.** Memory's upgrade-fidelity harness (adaptation #5) runs standalone; it plugs into a broader upgrade framework when that framework exists.
- **Dispatch primitive.** Process-of-arrival capture (adaptation #7) requires the dispatch primitive to emit stream logs. If the dispatch primitive is not yet built when memory ships, adaptation #7 ships as a receiver with no producer — functional but dormant — and becomes live when the dispatch primitive lands.

### Assumptions (marked as inference recorded, not stated by the owner)

1. **Claude via Max is sufficient for Graphiti's extraction-class prompts.** Graphiti's typical LLM workload is a handful of extraction and contradiction calls per episode. Max usage limits are assumed adequate. *inference recorded — should be confirmed or prototyped.*
2. **Local Ollama embeddings meet retrieval quality targets.** Graphiti supports remote embedding providers; we are choosing local to avoid vendor lock outside Max. Retrieval quality is to be verified against the synthetic test set. *inference recorded — prototyping priority.*
3. **Kuzu scales to multi-year single-user workload.** v1 research suggested this is well within Kuzu's operating envelope; no scale test has been run against a projection of the owner's eventual data volume. *inference recorded — should be sanity-checked during prototyping.*

---

## Prototyping priorities

Before the full build, three things should be prototyped:

1. **Synthetic retrieval test set design.** This is the top risk. the owner's ground-truth labelling is the gating input. The builder drafts scenarios; the owner approves.
2. **Local Ollama embedding quality on that test set.** Confirms assumption (2) above.
3. **Extraction-prompt cost profile under realistic workload.** Confirms assumption (1) — gives us a per-episode token-cost baseline that informs the cost-governance spec.

Each of these is a scoped prototype, not the full build. They reduce the largest uncertainties before committing to the complete adaptation-layer work.

---

## Acceptance in spec terms

The proposal honours every v1.0 + v1.1 objective as mapped in the table above. No spec acceptance criterion is left unaddressed. One previous halt (v1's U1(c)) is retired by R1's revision. No new halts are raised.

---

## Complexity estimate

AI-time, honest. Categorised by certainty.

- **Well-understood adaptation work:** adaptations #1, #2, #4, #6, #9 — ~60–90 AI-time minutes combined. These are thin pOS-side wrappers with clear shape.
- **Moderately risky adaptation work:** adaptations #3, #5, #7 — ~60–90 AI-time minutes combined. Emission design, upgrade-fidelity probe set, and process-of-arrival summarisation each have a handful of design choices that may need iteration.
- **The prototyping risk:** adaptation #8 (synthetic test set) — AI-time is small but owner-curation time is real and uncertain. This is the single item most likely to stretch the calendar.

Total AI-time for the adaptation work: ~120–180 minutes of agent execution (not calendar time). The owner-curation bottleneck on #8 dominates the calendar risk, as is correct — quality gates should constrain pace.

---

## Open questions for the owner (before handoff brief)

These are the decisions I'd want ruled on before drafting the handoff brief; none are urgent and none require founder-level authority, but they will shape the brief's scope.

1. **Prototype all three items before full build, or ship #2 and #3 as part of the build and prototype only the synthetic test set?** recommendation: prototype all three. The Max-usage and embedding-quality assumptions are cheap to verify before commitment.
2. **Ground-truth curation for the synthetic test set — how do you want to do it?** Options: you author scenarios and labels yourself; the builder drafts and you approve; I draft and you approve. recommendation: the builder drafts scenarios and you approve the labels, so the builder has skin in the scenario quality and you don't have to start from a blank page.
3. **Retention-class defaults — which class is default for ingested episodes?** Options: `normal` (persist raw text by default, opt-in to `derived-only` per source); `derived-only` (privacy-first, opt-in to `normal` per source); per-source-declared (no default, source always declares). recommendation: `normal` with well-documented opt-in to `derived-only` for sources like financial or health content. This is a real judgment call; happy to go whichever way.
4. **Channel of feedback on the proposal itself.** Annotations on this file, a reply in chat, or a voice conversation — whichever is cheapest for your attention.

---

## What happens on approval

On your approval of this proposal:

1. I draft the handoff brief for the builder. The brief states objectives, constraints, acceptance criteria, and dependencies — but does not prescribe file paths, function names, class structure, or step-by-step execution. You review the brief before dispatch to catch overspecification.
2. On your review, a general-purpose agent is dispatched against the brief.
3. If the agent cannot execute per the proposal, it halts and signals — per the rebuild rules. The proposal is revised and re-approved before execution resumes.

---

## Addendum — refinements from prototyping return (2026-04-18 ~10:15 CDT)

The prototyping dispatch (brief scoped to D1–D4) returned with six refinements the full-build brief must honour. These narrow choices; they do not change direction.

1. **Pin `graphiti-core` 0.28.2 with local Kuzu-driver patches.** Two upstream bugs in the Kuzu driver were identified and patched in a local factory module during prototyping. The full-build keeps those patches in place until upstream lands equivalent fixes (or raises them as upstream PRs).

2. **Temporal-filter wrapper at the pOS layer.** Graphiti's default compound `valid_at + invalid_at` SearchFilter shape does not translate correctly to Kuzu Cypher — it returns zero edges even when data is correct. A thin pOS-layer wrapper re-translates the compound filter into Kuzu-compatible form. Diagnosed in prototyping; ~10–20 AI-minutes to implement.

3. **Default embedding model: `nomic-embed-text`.** Evaluated against the the owner-approved synthetic test set alongside `bge-large`. Wins on overall pass rate, latency (36ms vs 47ms mean), and ingest time. Workspace-overridable per spec v1.1 R12.

4. **Default extraction LLM: `claude-haiku-4-5`.** Cost baseline from D4: ~$0.0176/episode, 7.1 LLM calls/episode mean, ~$53/year at 3,000 events. Workspace-overridable per spec v1.1 R12.

5. **Kuzu chaos-durability prototype added.** Research v2 §7.3 flagged this; the D1–D4 brief did not scope it. Added as a prototype gate before the full build is declared production-ready — a kill-mid-ingest / kill-mid-query / WAL-recovery test confirms Kuzu's durability posture under adverse conditions.

6. **the owner-approved test set as upgrade-fidelity gate.** The the owner-approved (the primary persona-in-lieu-of-the owner 2026-04-18) `test_set.json` becomes the semantic round-trip probe set for the upgrade-fidelity test harness (adaptation #5). The upgrade harness replays the test set pre- and post-upgrade, reporting drift against the declared threshold.

---

## Addendum — reviewed labels in lieu of the owner (2026-04-18 10:40 CDT)

delegated label approval to the primary persona, citing insufficient context to meaningfully curate. Forty-three of forty-four pairs accepted as drafted; one correction (q33 temporal active-in-October) landed under the primary persona's strict reading. No override from the owner required unless the owner disagrees with the q33 call on review.
