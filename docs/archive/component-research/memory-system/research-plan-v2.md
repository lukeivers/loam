# Research Plan v2 — Memory System

**Component:** Memory System. **Version:** 2. **Predecessor:** `research-plan.md` (v1). **Status:** AUTHORISED WITHOUT FURTHER REVIEW — 2026-04-17 17:02 CDT. Dispatching immediately per the approval.

---

## Why v2 exists

The v1 research (`research.md`) returned with a halt signal on spec clause U1(c) — byte-identical memory preservation through upgrade. read recorded: the v1 framing was over-constricted. Treating every spec criterion as a hard pass/fail gate, with build-from-scratch as the fallback, forces halts on otherwise-strong candidates that miss a single criterion — often for substrate reasons that leaked from the current pOS into the spec.

the owner's revised position for this component:

1. **Build-from-scratch is off the table.** Not worth the time relative to what exists.
2. **Find the best-fit existing solution** — not the one that passes every criterion, but the one that comes closest overall, with the least painful gap.
3. **Include features beyond our base criteria** in the evaluation. If a solution offers capabilities aligned with our overall objectives, those should be surfaced and considered for adoption as new or refined objectives.
4. **Gaps get resolved, not halted on.** Where the recommended candidate misses a spec criterion, the research proposes how to handle the gap (accept, revise spec, or flag for the owner).

## Objective this research must serve

Identify the single existing LLM-harness memory solution that best serves the new pOS memory system as a whole — spec coverage plus aligned capabilities. The recommendation is a solution to *adopt,* not a solution to beat in a build.

## Starting position

The v1 research at `components/memory-system/research.md` surveyed Cognee, MemPalace, Letta/MemGPT, Zep (SaaS and Community Edition), Mem0, and Claude-native memory features. It recommended conditional-adopt of Graphiti (Zep's open-source temporal knowledge graph) with Kuzu, local Ollama embeddings, and Claude-via-Max for all LLM-driven steps.

**Treat that research as input evidence, not a blank page.** Do not re-survey from scratch. Read it, accept its solution-by-solution findings as starting evidence (unless you find concrete reason to disagree with a specific claim), and redirect your effort toward: (a) ranking under the new best-fit rules, (b) enumerating beyond-spec features of the top candidates, (c) gap handling, (d) adaptation scope.

## Questions this research must answer

### Ranking, not gating

1. Using the v1 survey plus any additional actively-maintained LLM-harness memory solution you surface, produce a best-fit ranking of candidates. Best-fit is not "how many criteria pass." It weighs: how close the candidate comes on each criterion; the severity of any miss (substrate-leak misses count far less than conceptual misses like "no supersession support"); the adaptation cost to close remaining gaps.
2. Recommend a single best-fit candidate for adoption. If 2–3 candidates are genuinely close, present a shortlist with a clear primary recommendation among them — not an uncommitted catalogue.

### Features beyond spec

3. For the recommended candidate (and for any close shortlist members), enumerate capabilities the solution offers that are *not* covered by our spec. Include at minimum: data models beyond flat knowledge entries (entities, relationships, events, temporal queries); retrieval patterns beyond straight lookup (semantic search modes, graph traversal, recency/salience weighting, reranking); operational features (backup, replication, multi-tenant, observability hooks); integration surfaces (SDKs, API shapes, plugin mechanisms).
4. For each beyond-spec feature, tag it with one of:
   - `adopt-as-new-objective` — aligns with pOS's overall objectives, should be absorbed into the spec as a new objective,
   - `refine-existing-objective` — enhances an existing spec bullet and should be woven in as a refinement,
   - `capability-available-defer` — useful to know about, but not something to absorb into the spec now,
   - `reject` — at odds with a pOS non-goal or direction.

### Gap handling

5. For each spec criterion the recommended candidate misses, the research documents the gap and proposes three handling options for the owner to choose from:
   - **Accept the gap** as a known compromise, with a defined workaround or acceptance of the limitation.
   - **Revise the spec** — propose specific wording that captures the original intent without the substrate-specific expression that caused the miss.
   - **Flag for the owner** as a real gap requiring founder-level judgment.
6. **Halt-on-miss is retained from v1.** If after evaluation the recommended candidate misses a criterion, the research does not silently proceed — it surfaces the gap as a halt for owner's resolution, consistent with the "NOTHING is worked unless the owner has seen what it is being worked against before work starts" rule. *(Earlier v2 wording relaxed this to "no halts"; that was misread of feedback recorded and has been corrected.)*

### Adaptation scope

7. For the recommended candidate: what must pOS build *around* the candidate to deliver the spec? Adapters, interface layers, workspace-specific customisations, wiring to the scope-of-work/primary-persona/observability/self-upgrade primitives. Complexity estimate in AI-time, honest, with the surprising parts called out.

### Integration

8. Dependency map: how the recommended candidate integrates with (or constrains) the scope-of-work primitive, primary-persona primitive, observability/replay, and self-upgrade verification.

### Prototyping priorities

9. Short list of questions only a prototype can answer — including retrieval-quality test-set design, since v1 flagged that as the chief open question.

## Constraints

- **Max-subscription-first, vendor-free outside Max.** Capabilities accomplishable through the owner's Anthropic Max subscription use Claude without alternative consideration. Subsystems outside Max coverage (standalone embedding endpoints being the obvious case) are evaluated on merit, vendor-free.
- **Zero carryover from the current pOS memory system.** Not a reference implementation.
- **No build-from-scratch recommendation.** The option is struck. The deliverable is "adopt X."
- **No proposals, no code, no briefs.** Only the research document.

## Deliverable

A new document at:

  `docs/rebuild/components/memory-system/research-v2.md`

Containing:

1. **Ranking table** — candidates by best-fit score, with rationale per candidate.
2. **Recommended candidate** — named, with the case for it.
3. **Beyond-spec features** — enumerated and tagged (`adopt-as-new-objective`, `refine-existing-objective`, `capability-available-defer`, `reject`).
4. **Gap table** — any spec criterion the recommended candidate misses, with the three handling options per gap.
5. **Adaptation scope** — what pOS must build around the candidate, with complexity estimate.
6. **Dependency map** — integration with scope-of-work, primary persona, observability, self-upgrade.
7. **Prototyping priorities** — short list of questions only prototypes can answer.

**Return summary** (≤300 words): the recommended candidate, the top 3 beyond-spec features worth absorbing as objectives, any spec revisions proposed, confirmation that the research document has been written.
