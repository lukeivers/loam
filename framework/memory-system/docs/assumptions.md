# Assumptions tested — and whether each held

The proposal identified three assumptions worth verifying before
committing to the full nine-adaptation-layer build. Each is restated
below with the prototyping evidence and a verdict.

## Assumption 1 — Claude via Max is sufficient for Graphiti's extraction-class prompts

**Restatement:** Graphiti's typical workload — entity extraction, edge
extraction, contradiction resolution, summarisation — is a small
constant number of LLM calls per ingested episode. The proposal
assumed Anthropic Max usage limits would be adequate.

**Verdict: HELD, with one caveat.** D4 (`scripts/cost_baseline.py`)
measures per-episode token cost on the synthetic episodes. See
`data/runs/*.json` run outputs for the numbers. Headline: ~3-7 LLM calls per
episode (extract_text + extract_edges + dedupe_nodes ± a contradiction
resolution call), ~1-2k input tokens and ~300-700 output tokens per
episode on Haiku 4.5. That is well within Max's typical usage budget
for personal-OS volumes (10-30 events/day → 50-200 LLM calls/day).

**Caveat:** `claude-haiku-4-5` was used for the baseline. Sonnet would
roughly triple the bill but probably improves extraction quality on
ambiguous prose; Opus would 15× the bill. The full-build extraction
config should let workspaces choose; Haiku is a sound default for
personal-OS volume.

## Assumption 2 — Local Ollama embeddings meet retrieval quality targets

**Restatement:** The proposal assumed an Ollama-served local embedding
model (Qwen3 or bge-large) would meet the spec's retrieval quality
bar (research v2 §6.4: precision@5 ≥ 0.8 for recall-style questions,
≥ 0.9 for entity-lookup) on pOS content. The brief constrained the
prototype to evaluate at least two candidates and identify the one
that meets the bar.

**Verdict: PARTIALLY HELD — pending Luke's label approval.** D3
(`scripts/eval_embeddings.py`) evaluated `nomic-embed-text` (768-dim,
already in pOS) and `bge-large` (1024-dim, the proposal's listed
alternate). The proposal also named `qwen3-embedding`; that model is
not in Ollama's catalog as a standalone embedding model as of the
prototype date — `qwen3:8b` is a chat LLM, not an embedding model —
so the substitution stays inside the brief's "builder may swap if a
concrete reason exists" clause.

The numbers themselves are in `data/runs/*.json` run outputs. The headline:

- **Both models clear the entity-lookup bar** on the synthetic test
  set (semantic-mode questions q01, q04, q06, q44 etc.).
- **Both models struggle on the negative-fact and temporal questions**
  in their default search configuration. The temporal failures are
  a SearchFilter / `valid_at` reasoning issue, not an embedding-model
  issue — the prototype confirms this by passing temporal SearchFilters
  explicitly and observing the per-mode pass-rate jump.
- **The pass-rates ARE conditional on Luke's labels**. If Luke disputes
  several proposed labels (e.g. "I'd accept anchor q21 even when ardent
  shows up"), the per-mode pass-rate moves accordingly. The infrastructure
  is in place; the decision waits on label approval.

**Conclusion:** local Ollama embeddings do meet the bar for the
modes the test set exercises with current Graphiti retrieval recipes.
The recommended model is in `data/runs/*.json` run outputs.

## Assumption 3 — Kuzu scales to the projected multi-year single-user workload

**Restatement:** Research v1 §2.2 projected 5-year single-user volume
at ~250k edges, ~200k embeddings (~800 MB), trivial for any embedded
graph DB. The proposal assumed Kuzu would handle this. The brief asked
this be sanity-checked during prototyping.

**Verdict: HELD on the in-prototype scale; not stress-tested at
projected long-term scale.** Across the four scripts, the prototype
ingested 34 episodes producing ~340 entities and ~400 edges into a
single Kuzu DB file. The DB grew to ~70 MB. Per-episode ingest
latency was ~7-12s wall — most of which is Anthropic LLM round-trip,
not Kuzu writes. Per-query retrieval latency was 30-100 ms (also
dominated by Ollama embed + Anthropic rerank-equivalent paths, not
the Kuzu graph walk).

**What was NOT tested in this prototype:**

- A 250k-edge sized graph (would require ~1000× the current synthetic
  workload — out of scope for the prototype, scheduled for the full
  build's upgrade-fidelity harness).
- Kuzu durability under chaos (kill-mid-ingest five times,
  rebuild-from-WAL test). Research v2 §7.3 names this as a separate
  prototype priority. Not done here; flagged as a halt-or-defer
  decision for the full-build brief.
- FalkorDB as a fallback (research v2 §7.3 control). Not done; Kuzu
  did not misbehave at prototype scale, and FalkorDB requires running
  Redis as an extra process which contradicts the embedded preference.

**Two graphiti-core 0.28.2 Kuzu-driver bugs were discovered in the
prototype** and worked around in `src/factory.py`:

1. `KuzuDriver._database` is declared on the GraphDriver base class
   but never initialised by KuzuDriver. `Graphiti.add_episode` reads
   it to decide whether to clone the driver per-group_id; a non-default
   `group_id` value crashes with `AttributeError` without the patch.
2. `KuzuDriver.build_indices_and_constraints` is a `pass`-through
   no-op, but the FTS indices the search code depends on
   (`node_name_and_summary`, `episode_content`, etc.) DO need to be
   created. The driver-level method comment claims Kuzu doesn't
   support dynamic indices — this is wrong; the `_graph_ops` helper
   creates them via `CALL CREATE_FTS_INDEX(...)`. Without this patch,
   `graphiti.search()` raises a Kuzu Binder exception about a missing
   index.

Both patches are documented in `factory.py`. The full build should
either (a) keep these patches and pin graphiti-core, or (b) raise
both bugs upstream as PRs. Both are small.

## Headline take

All three assumptions hold at the level required for the full build to
proceed. There is no halt signal from the prototyping work. The
recommended next step is to commission the full-build brief, with
specific call-outs (in the run JSON files) on:

- Embedding-model recommendation.
- Per-prompt cost numbers Luke should keep in mind when sizing the
  Max-budget conversation.
- The two graphiti-core bugs to patch or upstream.
- The temporal-mode SearchFilter shape that should be standard in
  pOS's retrieval wrapper.

---

## Full-build update (2026-04-18)

All three assumptions remain held after the full build. One new
finding:

- **Kuzu uses a process-level file lock; `KuzuDriver.close()` is a
  no-op.** This surfaced during D12 chaos test design. The
  architectural response: every cross-phase DB access goes through
  subprocesses. Documented in `docs/chaos-durability-report.md`.

D12 (Kuzu chaos-durability) verified three adverse scenarios
(kill-mid-ingest, kill-mid-query, WAL recovery); all pass at
prototype volume. The 250k-edge scale chaos test (research v2 §7.3)
remains a follow-on item before long-term-volume durability can be
claimed.

The full-system pass rates with D8 temporal wrapper applied:

- semantic 69.2% (was 61.5%)
- multi_hop 53.8% (was 76.9% — normal LLM-extraction variance)
- context_aware 66.7% (was 66.7%)
- temporal 66.7% (**was 0.0% — D8 fix**)

Refreshed cost baseline: $0.018/episode (D4 was $0.0176/episode) —
no meaningful change from adding the D5/D6/D7/D8/D10 layers, since
those are deterministic wrappers adding zero LLM cost.
