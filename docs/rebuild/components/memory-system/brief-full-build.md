# Handoff Brief — Memory System Full Build

**Component:** Memory System
**Phase within component:** Full build (follows the completed prototyping phase)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-18 09:23 CDT; refined by the prototyping-return addendum 2026-04-18 ~10:15 CDT)
**Spec this brief honours:** objectives spec v1.0 + v1.1 addendum (`docs/rebuild/spec/pos-v2-objectives-spec.md`)
**Predecessor artifact:** `brief.md` (prototyping brief, dispatch complete 2026-04-18 ~10:15 CDT)

---

## Why a full-build brief now

The prototyping phase completed. All four prototyping deliverables (D1 Graphiti hosting, D2 synthetic test set, D3 embedding assessment, D4 extraction cost baseline) returned with no halts. The three assumptions the prototyping was meant to test all held, with one diagnosed engine-level bug that has a clear pOS-layer fix.

This brief covers the remaining adaptation work — the eight components named in the proposal plus the six refinements the prototyping return surfaced. The outcome is a production-ready memory system for the new pOS: Graphiti on Kuzu, Python-native, adopted with every v1.0 and v1.1 spec acceptance criterion honoured.

---

## Objective

Deliver a production-ready memory system component for the new pOS, adopting the approved direction. Build the eight remaining adaptation layers, honour the six prototyping refinements as hard constraints, satisfy every v1.0 and v1.1 acceptance criterion in the spec, add the chaos-durability gate, and ship bundled documentation sufficient for a non-technical reader to understand what exists and how it connects.

---

## Hard constraints

1. **Implementation language: Python.** Rebuild-wide.
2. **Branch discipline: `pos-v2`.** All work lands on the existing branch created by the prototyping dispatch. Do not modify main. Do not modify anything outside the branch's scope.
3. **Zero carryover from current-pOS / the existing workspace.** No mining of `memory/daily`, `memory/people`, `memory/companies`, existing personas, or any workspace-specific content. All test fixtures extend the synthetic Aldermere world or invent fresh synthetic scenarios.
4. **No assumed event log or observability aggregator.** Memory *emits* observability records in canonical OTel form; no downstream consumer is assumed to exist. This is spec v1.1 R11 with the A1 correction applied.
5. **Max-subscription-first.** Claude via Max for all LLM work (extraction, contradiction, summarisation, reranking). Local Ollama for embeddings. No other vendors.
6. **No personas.** pOS core ships zero persona content — this is framework code, not persona files.
7. **Halt on deviation.** If any constraint above cannot be honoured, or the approved proposal + addendum direction becomes untenable, halt and signal a named failure. Silent deviation is forbidden.
8. **Pin `graphiti-core` 0.28.2 with the Kuzu-driver patches** from the prototyping phase (in the `factory.py` shim). Do not upgrade graphiti-core without explicit authorisation; do not remove the patches without upstream landing equivalents.
9. **Default embedding model: `nomic-embed-text`.** Default extraction LLM: `claude-haiku-4-5`. Both workspace-overridable per spec v1.1 R12, but these are the defaults this brief ships with.
10. **Bundled documentation per v1.1 R4.** Every component shipped carries human-readable documentation — prose, architecture diagrams, flowcharts, relationship maps — bundled with it, not hosted separately.

---

## Deliverables

Nine named deliverables. Each has an objective and acceptance criteria in objective terms. None prescribe implementation method.

### D5. Ephemerality filter *(proposal adaptation #1; spec A1 v1.1 R2)*

**Objective:** discriminate episodes to save from episodes to discard at ingest, per the narrow exclusion set v1.1 R2 specifies.
**Acceptance:**
- A declared exclusion rubric enumerates the narrow ephemeral classes (current-CPU readings, ticking clocks, volatile UI state, and similar transient telemetry).
- A sample ephemeral-class input is verified absent from storage post-ingest.
- Any input not on the exclusion list is accrued.
- The rubric is editable without code change (config-level).

### D6. Scope-of-work mapper *(proposal adaptation #2; core primitive)*

**Objective:** every memory entry is attributed to the scope-of-work it was produced within or about.
**Acceptance:**
- Every memory write carries a scope-of-work identifier.
- Retrieval can be filtered by scope.
- A scope's memory slice is enumerable.
- **Soft dependency:** the scope-of-work primitive runtime is not yet built. This deliverable ships as a wired-ready interface with a mock scope source for testing. When the scope-of-work primitive lands in a later rebuild phase, wiring replaces the mock without re-architecting memory.

### D7. Observability emission adapter *(proposal adaptation #3; spec v1.1 R11 + R12; A1 correction)*

**Objective:** memory emits structured observability records in OTel form for any future consumer.
**Acceptance:**
- Every memory operation emits a structured OTel span including actor, timestamp, operation, inputs, outputs, prompt name, token usage.
- Per-prompt-type cost attribution is queryable (v1.1 R12).
- Records are durable and queryable without requiring a consumer to exist.
- A sampled operation is reconstructible from its emissions alone.
- **No downstream consumer assumed.** When the observability component is later designed, it subscribes to these emissions — it is not a precondition of memory shipping.

### D8. Temporal-filter wrapper *(new; from prototyping call-out 2)*

**Objective:** fix the temporal retrieval mode. Graphiti's compound `valid_at + invalid_at` SearchFilter shape does not translate correctly to Kuzu Cypher. A thin pOS-layer wrapper re-translates the compound filter into Kuzu-compatible form so temporal queries return the correct edges.
**Acceptance:**
- Temporal queries against the D2 synthetic test set's temporal-mode pairs (q29–q36, q42) pass at the same threshold as the other retrieval modes.
- The wrapper's interface is transparent to callers — they use Graphiti's normal SearchFilter API; the wrapper operates beneath.
- A regression test exercises the specific compound-filter shape that fails upstream.

### D9. Upgrade-fidelity test harness *(proposal adaptation #5; spec v1.1 R1; call-out 6)*

**Objective:** test that a framework upgrade preserves memory semantically.
**Acceptance:**
- The the owner-approved (the primary persona-in-lieu-of-the owner) `memory-system/data/test_set.json` becomes the probe set.
- The harness runs the probe queries pre-upgrade, captures answers; re-runs post-upgrade; compares and produces a drift report.
- Drift above a declared threshold fails the upgrade; below, passes.
- Kuzu DB is snapshotted pre-upgrade so physical reversibility (u1(f)) is preserved alongside the semantic test.

### D10. Retention-class tagger *(proposal adaptation #6; spec v1.1 R10)*

**Objective:** each ingested episode carries a retention-class tag (`normal`, `derived-only`, `ephemeral`), enforcing the declared persistence behaviour per class.
**Acceptance:**
- Episodes tagged `derived-only` produce structured facts in memory but no retrievable raw text.
- Episodes tagged `ephemeral` produce no persisted memory beyond immediate use.
- Default class is `normal` (decision recorded at proposal approval).
- Retention class is queryable per entry; class-filtered queries return only entries of that class.
- Test fixtures demonstrate each class's observed behaviour.

### D11. Process-of-arrival capture ingestion *(proposal adaptation #7; spec v1.1 R3)*

**Objective:** background dispatches' stream-of-consciousness logs are summarised and ingested alongside outcomes.
**Acceptance:**
- A representative background dispatch (mocked, since the dispatch primitive is not yet built) produces a stream log during execution; the log is summarised (by Claude via Max) and ingested.
- A retrieval query returns both the outcome and the reasoning path when either is queried.
- **Soft dependency:** the dispatch primitive is not yet built. This deliverable ships as a receiver with a mock producer; the mock is replaced when the dispatch primitive lands.

### D12. Kuzu chaos-durability test *(new; from prototyping call-out 5)*

**Objective:** confirm Kuzu's durability posture under adverse conditions before the memory system is declared production-ready.
**Acceptance:**
- Kill-mid-ingest scenarios (send SIGKILL to the memory process during episode ingestion) produce either a clean-rollback state or a recoverable-WAL state — never a corrupted DB.
- Kill-mid-query scenarios produce no state change (reads are idempotent by design, but verification is required).
- WAL-recovery scenarios confirm that state is restored to the last successful commit on restart.
- A run report documents scenarios tested, failure modes observed (if any), and remediations applied.

### D13. Extended bundled documentation *(proposal adaptation #9; spec v1.1 R4)*

**Objective:** extend the prototyping-phase documentation to cover the full-build deliverables.
**Acceptance:**
- A prose explanation covers every deliverable D5–D12, what it does, and how it relates to the others.
- Architecture and data-flow diagrams are updated to show the full-build shape, not just prototyping scaffolding.
- A relationship map shows memory's interfaces to scope-of-work (mocked), primary persona (mocked), observability (emission-only), upgrade framework (harness-ready), and dispatch (receiver-ready).
- A non-technical reader can answer "what does memory do and how does it fit with the others" from the bundled docs alone.

---

## Dependencies and assumptions carried forward

- **Hard dependencies** (unchanged from the proposal): scope-of-work primitive runtime and primary persona loader are not yet built. D6 and retrieval-caller hooks ship as wired-ready interfaces with mocks.
- **Soft dependencies**: observability aggregator, self-upgrade framework, dispatch primitive. Memory ships shippable without these; each integrates when its component lands.
- **Assumptions confirmed by prototyping:** Max sufficiency (held), Ollama retrieval quality (held, pending temporal fix via D8), Kuzu scale at prototype volume (held, durability pending D12).

---

## Halt conditions

Halt and return with a named failure if:

- Any hard constraint (§"Hard constraints") cannot be honoured.
- A spec acceptance criterion is discovered to be unsatisfiable under the approved direction + refinements — do not silently drop it. Surface the conflict.
- Any soft dependency's mock design creates an architectural commitment that would be painful to undo when the real component lands — surface the concern rather than inventing a workaround.
- Any ambiguity in this brief that would require inventing a constraint the owner has not specified.

Halts return control to the primary persona, who reviews with the owner; the proposal is adjusted as needed and execution resumes against the revised version.

---

## Return format

When the brief's scope is complete, return with:

1. A summary (≤600 words) covering: which deliverables D5–D13 completed, which halted (if any), which spec acceptance criteria now pass on the memory system, and the recommended next action (declare memory component complete, proceed to next pOS component, or flag remaining gaps).
2. The extended bundled documentation at `memory-system/docs/`.
3. Updated test-set pass rates for all four retrieval modes (now with the D8 temporal wrapper applied).
4. The D12 chaos-durability run report.
5. A final cost baseline (D4 refreshed on realistic full-system usage).

---

## What this brief is NOT

- Not a specification of file layout, module structure, package organisation, or code style beyond the pinned constraints (language, embedding model, LLM, branch).
- Not a step-by-step execution plan.
- Not a commitment to building the adjacent primitives (scope-of-work runtime, persona loader, dispatch, observability aggregator) — those have their own components and briefs.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Two items below come from the primary persona's interpretation rather than the owner's verbatim words. Marked here so the builder can surface objections:

- *Default retention class is `normal`.* Derived from the owner's 2026-04-18 09:23 decision on the proposal's open questions (option: `normal` with documented opt-in to `derived-only` for privacy-sensitive sources). If the builder finds a concrete reason to default differently, halt and flag.
- *D8 temporal wrapper's interface is transparent to Graphiti's normal SearchFilter API.* the primary persona's design inclination, not the owner's stated instruction. If the builder finds that transparency creates more complexity than an explicit pOS-side API surface, halt and flag.
