# Handoff Brief — Memory System Prototyping Phase

**Component:** Memory System
**Phase within component:** Prototyping (not yet full build)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Approved proposal this brief delivers against:** `components/memory-system/proposal.md` (approved 2026-04-18 09:23 CDT)
**Spec this brief honours:** objectives spec v1.0 + v1.1 addendum (`docs/rebuild/spec/loam-objectives-spec.md`)

---

## Why prototyping first

The approved proposal identifies three assumptions worth verifying before committing to the full nine-adaptation-layer build:

1. Claude via Max is sufficient for Graphiti's extraction-class prompts.
2. Local Ollama embeddings meet retrieval quality targets.
3. Kuzu scales to the projected multi-year single-user workload.

Approved prototyping all three before full build. This brief covers that prototyping work only. A separate brief will follow for the full build, informed by what prototyping returns.

---

## Objective

Run the three prototypes, produce honest findings, and return — without proceeding to the full adaptation-layer build. The deliverable is information the owner and the primary persona need to decide whether the proposal's direction holds or must be revised.

---

## Hard constraints

1. **Implementation language: Python.** Rebuild-wide decision. Current-pOS Ruby does not apply to the new pOS.
2. **No reading from current-pOS / the existing workspace content.** Zero carryover. No mining of `memory/daily`, `memory/people`, `memory/companies`, existing personas, or any workspace-specific content. Synthetic and fabricated data only.
3. **No assumed event log or observability aggregator.** Emissions happen; no downstream consumer is assumed to exist.
4. **Max-subscription-first outside embeddings.** Anthropic Max for all LLM work; local Ollama for embeddings; no other vendors.
5. **No full-build work.** The nine adaptation layers from the proposal are not this brief's scope. If you find yourself building adaptation #1 (ephemerality filter) or the other full-build components beyond what the prototypes require, stop — that's the next brief.
6. **Halt on deviation.** If you conclude any constraint above cannot be honoured, or the proposal's direction becomes untenable based on prototype findings, halt and signal with a named failure state. Do not silently adapt.
7. **No personas.** This work lands in the new pOS core, which ships zero personas.
8. **owner-curation bottleneck on the synthetic test set's ground-truth labels is real.** Do not block other prototypes waiting for labels; proceed on what you can, return the labelling request to the owner as a discrete ask.

---

## Deliverables

Four artifacts, located under a new repository branch (see §"Where to work" below). Each has an acceptance criterion stated in objective terms — how the result is recognised as correct, not how to produce it.

### D1. Graphiti local service running

**Objective:** Graphiti is installed and runs as a managed local service, reachable from a Python process on the same machine.
**Acceptance:** a test Python call reaches Graphiti, submits an episode, retrieves it via query — round-trip succeeds. Service auto-starts and survives a restart.

### D2. Synthetic retrieval test set — designed and partially labelled

**Objective:** a fabricated test set of Q/A pairs exercises the four retrieval modes pOS cares about: semantic top-k, multi-hop graph traversal, context-aware anchor reranking, and temporal `reference_time` queries. Scenarios and entities are invented fresh — zero overlap with current-pOS content.
**Acceptance:** a minimum of 40 Q/A pairs covering all four retrieval modes, with scenario descriptions written in prose for owner's review; each pair has a *proposed* ground-truth answer for the owner to approve or correct; the set is stored as structured data (format at builder's discretion).
**the owner's input required:** the owner reviews scenarios and approves / corrects the ground-truth labels. The builder does not self-approve labels.

### D3. Embedding model quality assessment

**Objective:** identify which local Ollama embedding model to use for retrieval, evaluated against the synthetic test set.
**Acceptance:** at least two candidate embedding models (builder's choice — Qwen3 and bge-large are the proposal's starting suggestions) are each run against the the owner-approved test set; precision/recall and latency numbers are reported for each; a recommendation is made with rationale; the recommendation identifies which model meets the acceptance thresholds the spec sets for retrieval.
**Dependency:** D2 must have the owner-approved labels before this deliverable can complete, but the builder may set up the infrastructure whilst labels are pending.

### D4. Extraction cost baseline

**Objective:** establish a realistic token-cost profile for Graphiti's extraction-class prompts on representative synthetic episodes.
**Acceptance:** a representative sample of synthetic episodes (drawn from the D2 scenarios, not from real content) is ingested through Graphiti; per-episode token usage is measured and broken down by prompt type (using Graphiti's `TokenUsageTracker`); a baseline figure and a variance estimate are reported; a projection to anticipated pOS usage volume is provided with assumptions stated.

---

## Bundled documentation requirement *(v1.1 R4)*

Per spec v1.1 R4, every component ships with human-readable documentation. The prototyping phase ships:

- A prose explanation of what was built and what the prototypes revealed.
- A simple architecture diagram showing how Graphiti, Ollama, Kuzu, and the Python harness relate.
- A summary of assumptions tested and whether each held.

Documentation bundles alongside the code under the same branch.

---

## Where to work

Create a new branch on the existing the existing workspace repository for the new pOS rebuild. Burn down existing content on that branch and build fresh. decision recorded 2026-04-17: the new pOS is greenfield; the main branch of this repo continues to serve current pOS in maintenance mode. Branch name at builder's discretion (sensible default: `pos-v2` or similar).

All work for this brief lives within that branch. No modifications to the main branch. No modifications anywhere in the current workspace outside the branch.

---

## Halt conditions

Halt and return with a named failure if any of the following occur:

- A hard constraint (§"Hard constraints") cannot be honoured.
- A prototype reveals the proposal's direction is untenable (e.g., Max-usage limits are insufficient for extraction, or Ollama retrieval quality falls materially below what the spec requires and no alternative that honours the constraints is available).
- the owner-approved labels for D2 are required to proceed on D3 and are not available — halt D3 progress, proceed on D1 and D4, return with the labels request as a discrete ask.
- Any ambiguity in this brief that would require inventing a constraint the owner has not specified.

A halt is not a failure of the builder — it is the correct behaviour. The alternative (silent deviation) is the failure mode the rebuild rules exist to prevent.

---

## Return format

When the brief's scope is complete, return with:

1. A summary (≤500 words) covering: which deliverables completed, which halted (if any), the headline findings on each assumption, and the recommended next action (proceed to full-build brief / revise proposal / different path).
2. The bundled documentation as described above.
3. Links to all artifacts produced (code, docs, test set, findings).

---

## What this brief is NOT

- Not a commitment to any specific file layout, module structure, package organisation, or code style beyond the constraints above.
- Not a step-by-step execution plan.
- Not the full-build brief. Full build follows in a separate brief after the owner reviews the prototyping findings.

---

## inferences recorded in this brief (marked so you can challenge)

Two constraints in this brief come from the primary persona's interpretation rather than the owner's verbatim words. They are marked here so the builder can surface objections:

- *Minimum 40 Q/A pairs in D2.* the primary persona's calibration — enough to cover four retrieval modes with ten pairs each. Builder may propose a different number with rationale.
- *Two candidate embedding models in D3.* Proposal named Qwen3 and bge-large; this brief accepts those as the starting pair. Builder may swap either if a concrete reason exists.

*(The "branch on existing repo, not new repo" decision is the owner's direct instruction from 2026-04-17 — not an the primary persona inference. An earlier draft of this brief misattributed it; corrected 2026-04-18.)*
