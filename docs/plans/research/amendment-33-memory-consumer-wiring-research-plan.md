# Research plan — memory-system consumer wiring (D7)

**Status:** research-plan for the D7 research cycle. Authored 2026-04-24. Opens a five-gate cycle (this research-plan → research → proposal → brief → build); subsequent gates not yet scoped. Biggest uncompleted work in the project per `STATE.md` line 70.

**Session-start corpus:** research agent reads all five mandatory paths in `CLAUDE.md`'s session-start-discipline section. Component-scoped reads: `docs/archive/component-research/memory-system/`, `docs/archive/component-research/primary-persona-layer/` (or whatever that component's current directory is), `docs/archive/component-research/scope-of-work/`, `docs/archive/component-research/orchestrator/`, `docs/archive/component-research/objective-tracker/`, `docs/archive/component-research/self-correction/`. And the three ODD docs for shape.

---

## 1. Context

Amendment #24 (memory-system MCP migration, sealed 2026-04-23) §5 explicitly defers consumer integration: *"No MCP-client-side integration into any pOS consumer (primary-persona etc.). That's downstream work."* `STATE.md` line 70 acknowledges the gap: *"follow-ons pending primitives that reference it."* The 2026-04-23 pos3 session confirmed empirically — a grep across orchestrator, primary-persona-layer, scope-of-work, self-correction source found zero references to the memory MCP endpoint. Memory-system is a sealed, functional, unreached island.

The value proposition (`VALUE_PROPOSITION.md` Lens 2) requires memory to be part of the toolkit the primary persona draws from. It cannot be, today.

This research cycle surfaces the shape of that integration — who writes, who reads, what triggers, retention/group-id scheme, cost model — so subsequent proposal/brief/build cycles can commit to concrete component amendments.

## 2. Questions for the research agent

### 2.1 Consumer identification

- Which pos-v2 sealed components are candidate first-consumers of memory? Rank by value + integration cost.
  - Primary-persona-layer (session-level memory for persona continuity)?
  - Scope-of-work (scope-activation events → episodes; search at scope-start for context)?
  - Orchestrator (state-transition events → episodes; search for prior-similar-scope examples)?
  - Objective-tracker (objectives → entities; cross-objective relationships)?
  - Self-correction (correction-loop outcomes → episodes; search for prior-similar-error patterns)?
- Identify the subset that should integrate in a first wave vs deferred waves. No "all of them at once" recommendation — the question is about minimum-viable consumer set.

### 2.2 Write-path shape

- What's the canonical "event → episode" translation for each identified consumer? Do events map 1:1 to episodes, or is aggregation required (e.g., a scope's full lifecycle becomes one episode on scope-completion, not N episodes)?
- Write-path cost model: the 2026-04-23 session measured add_episode at 113s for a 9-entity/8-edge episode via claude-haiku-4-5. At pos-v2's expected event rate, how many episodes per day and what's the implied Claude Max subscription cost? (Budget context: cost-governance C15 config applies.)
- Sync-writes vs async-writes: who bears the latency? Direct synchronous add_episode from the primary persona blocks the user for two minutes per writable event — clearly wrong. Async writes via orchestrator's background-scope primitive? Buffered writes aggregated at session-close? Rank the architectural candidates.

### 2.3 Read-path shape

- What triggers a memory read? Session-start (once per session)? Turn-start (once per user message)? Scope-activation (once per scope)? On-demand via a "search memory for X" persona tool?
- What's the query-construction shape? Raw user message? Scope name + goal? Derived from the most recent N turns? Each has precedent in adjacent systems; this research surfaces which fits pos-v2's primary-persona shape.
- How much context gets injected? Top-N facts by semantic similarity? A time-windowed slice? A persona-authored "what matters" filter over search results? The research rules between options informed by token-budget and relevance concerns, not foregone.

### 2.4 Retention and group_id scheme

- Amendment #24 preserved graphiti's group_id semantics. What's the pos-v2 convention? Per-workspace (group_id = workspace slug)? Per-user (group_id = user identity, cross-workspace)? Per-scope (group_id = scope UUID)? Hierarchical (user → workspace → scope)?
- What's the retention/eviction policy? Memory-system already ships retention (D10 retention_class column per `decay-retention-analysis.md`). How do consumer-writes assign retention class? Default + explicit-override? Computed from event type?

### 2.5 Composition with D8 (Idea-8 context-load gate)

**Owner ruling (2026-04-24):** D7 and D8 share a common `additionalContext`-emitter layer. Research does NOT re-litigate whether to merge vs keep adjacent; that's ruled.

Research focuses on the SHAPE of the shared layer:
- What are the clean entry points for the two triggers (session-start vs turn-start / `UserPromptSubmit`)?
- What's the payload-composition model — session-level context and turn-level memory-retrieval merged into one additionalContext stream, or interleaved, or emitted as complementary but distinct additionalContext contributions?
- What's the contract between D7's write (memory-retrieval per turn) and D8's write (corpus + service-state per session)? Ordering? Mutual exclusion? Shared buffering?
- Are there cases where one trigger should suppress or modify the other's output (e.g., a heavy session-start payload may argue for a lighter turn-start retrieval that session)?

### 2.6 Flagged inferences

Surface explicitly for owner challenge:
- Any assumption about which consumer ranks first. Research author may infer based on Lens-2 logic (primary persona is the highest-leverage consumer) but flags the inference.
- Any assumption about sync vs async writes. Research author may infer async is correct based on the 113s write cost but flags the inference.
- Any assumption about read-trigger granularity (session vs turn vs scope). Research author may infer turn-level is right based on the primary persona's translation-layer job but flags the inference.

## 3. Scope

- Read-only research. No source edits.
- Working directory `/Users/lukeivers/ivers-corp-pos-v2/`.
- Cap: ~1500 lines (larger than a typical research doc because the question set is broad; proportional to scope).
- May propose sub-research cycles if any question's answer space is too large to close in one pass. Document and signal.

## 4. Halt triggers

1. **The research surfaces that consumer-wiring requires spec v1.x amendment** (e.g., the primary-persona-layer's v1.2 spec doesn't name memory-consumption as an objective it backs). Halt and signal; owner decides path.
2. **A research question's answer requires empirical data that does not yet exist** (e.g., "what's the event rate per day?" requires a pos-v2 eval workspace running real workloads, which is future work). Mark the question as "pending evaluation-workspace data" and proceed with the rest.
3. **The research's scope grows past ~1500 lines** with open questions remaining. Halt, decompose into sub-research-plans, signal owner.
4. **ODD break detected as strongly required.** Halt and signal.
5. **Fundamental architectural conflict** (e.g., "async writes need a new sealed component that doesn't exist"). Halt; owner rules.

## 5. Acceptance (research-plan gate)

Research document at `docs/plans/research/memory-consumer-wiring-research.md` answering §2.1–§2.5 with evidence + flagged-inferences block + per-question implication for the subsequent proposal. Executive summary ≤15 lines naming: first-wave consumer set, write-path shape, read-path shape, group_id scheme, D8 composition, top-3 owner decisions.

## 6. CDC adherence

- **Plan-before-code:** research plan exists (this); subsequent research-artefact writes precede any code.
- **Research-before-plan:** this is the research step; proposal follows research.
- **Scope-only dispatch:** this plan carries scope material (questions, boundaries, halt triggers); does not prescribe which consumers to integrate or what the proposal's ACs will be.
- **Background-agent-default:** research step dispatches background. Agent brief derived from this plan.
- **Session-start corpus:** mandatory at dispatch; noted in §header.

## 7. Composition note

This cycle runs in parallel with D8's research cycle. Both are research-only gates that consume no canonical code-surface changes. They share the session-start injection-point shape as a composition surface (cf. §2.5). If both cycles converge on a shared answer, proposal-phase decides whether they merge into one cross-cutting amendment or stay as two adjacent ones.
