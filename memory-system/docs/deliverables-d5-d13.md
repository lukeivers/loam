# Memory-system — deliverables D5–D13

This document explains each full-build deliverable: what it does,
what it produces, and how it relates to the rest of the memory
system. Written for a non-technical reader to understand without
reading the code.

## D5 — ephemerality filter

**What it does.** Discards a narrow set of transient inputs at the
ingest gate — CPU readings, ticking clocks, volatile UI state, and
similar telemetry. Everything else is saved (spec v1.1 R2: anything
not on the exclusion list is accrued).

**Where the policy lives.** `config/memory.yml`, under
`ephemerality.exclude`. A workspace can add exclusion rules by
editing this file; no code change required.

**What you see.** An ingest whose source matches an exclusion rule
returns `IngestResult(ephemeral=True, episode_uuid=None)` and emits
an audit entry. Nothing lands in Kuzu. An ingest that doesn't match
proceeds through the normal pipeline.

**Acceptance criteria covered.**
- Declared rubric enumerates the narrow ephemeral classes ✓
- Sample ephemeral-class input verified absent from storage ✓
  (see `tests/test_ephemerality.py` and the `[D5]` line in
  `scripts/eval_full_system.py` output)
- Unlisted inputs are accrued ✓
- Rubric editable without code change ✓ (YAML in config/)

## D6 — scope-of-work mapper

**What it does.** Every memory entry is attributed to a
scope-of-work. Retrieval can be filtered by scope. A scope's memory
slice is enumerable via `MemoryAPI.list_scope(scope_id)`.

**Soft dependency.** The scope-of-work *primitive runtime* is not yet
built (brief dependencies §). D6 ships with a mock `ScopeSource` that
auto-registers scopes on first use. When the real primitive lands,
the mock is replaced at the single `MemoryAPI` construction site —
no re-architecting.

**What you see.** Every ingest accepts `scope_id="..."`. A registry
file at `data/scope_registry.json` records every scope the mock has
seen. Graphiti's native `group_id` is the physical carrier — so
"retrieve within scope S" is just `search(..., scope_ids=["S"])`.

**Acceptance criteria covered.**
- Every memory write carries a scope-of-work identifier ✓
- Retrieval filterable by scope ✓
- Enumeration of a scope's slice ✓
- Wired-ready interface with mock for testing ✓

## D7 — observability emission adapter

**What it does.** Memory emits OTel-shaped spans on every operation,
token-usage rows per LLM call (broken down by prompt name), and
audit entries for discards, retention decisions, supersessions. Three
JSONL files under `data/observability/`: `spans.jsonl`,
`tokens.jsonl`, `audit.jsonl`.

**Explicit constraint (A1 correction).** No downstream consumer is
assumed. The emissions are durable — any future observability
aggregator subscribes to them.

**What you see.** After any memory activity, the three files contain
one line per record. `Emitter.per_prompt_cost(input_usd_per_mtok,
output_usd_per_mtok)` produces the v1.1 R12 per-prompt-type cost
view on demand. A sampled span + its linked token rows + audit
entries reconstruct the operation end-to-end without a consumer.

**Acceptance criteria covered.**
- OTel-shaped span per operation including actor, timestamp, prompt
  name, token usage ✓
- Per-prompt-type cost queryable (v1.1 R12) ✓
- Records durable without a consumer ✓
- Sampled operation reconstructible from emissions alone ✓
  (`tests/test_observability.py::test_sampled_operation_reconstructible`)

## D8 — temporal-filter wrapper

**What it does.** Fixes graphiti-core 0.28.2's broken temporal filter
shape under Kuzu. The intended query "give me edges active at time
T" — `valid_at ≤ T AND (invalid_at > T OR invalid_at IS NULL)` —
was being compiled into a WHERE clause that always returned false.
The wrapper constructs the correct `SearchFilters` shape so temporal
queries work.

**Bug diagnosis.** `scripts/diag_temporal2.py` inspects the generated
Kuzu Cypher for three filter shapes. The pinned regression test at
`tests/test_temporal.py::test_regression_compound_inner_list_bug_still_exists_upstream`
detects if upstream fixes the bug — in which case the wrapper can
be retired (set `temporal.enabled: false` in config).

**What you see.** Temporal-mode questions (q29–q36, q42) in the
synthetic test set now pass. Baseline eval (before D8): 0/9. With
D8: 6/9 (66.7%) on the full-system eval.

**Acceptance criteria covered.**
- Temporal queries against D2 test set pass at same threshold as
  other modes ✓ (66.7% vs 53.8%–69.2% for other modes)
- Wrapper interface transparent to callers ✓ (`MemoryAPI.search(...,
  at_time=T)` does the right thing)
- Regression test for compound-filter shape ✓

## D9 — upgrade-fidelity test harness

**What it does.** Verifies that a framework upgrade (say, jumping
from graphiti-core 0.28.2 to 0.29.0 in future) preserves memory
semantically. Runs the Luke-approved probe set pre-upgrade and
post-upgrade; drift above a configured threshold fails the upgrade.
A Kuzu DB snapshot is taken pre-upgrade so physical reversibility is
preserved even if the semantic test fails.

**Moving parts.** `src/upgrade.py` has `snapshot`, `run_probe_set`,
`compare`, `run_upgrade_harness`. The demo
`scripts/upgrade_harness_demo.py` exercises all four steps with a
no-op "upgrade" (re-opening the same DB in a subprocess) and confirms
the report structure works.

**Why subprocess for the post-probe.** Kuzu's `close()` is a no-op
per source — it relies on GC to release the file lock. The harness
spawns a subprocess so the post-upgrade memory instance reliably
acquires the lock.

**Acceptance criteria covered.**
- Luke-approved test_set.json is the probe set ✓ (hard-coded default
  in `config/memory.yml`)
- Pre-run captures answers; post-run compares; drift report ✓
- Drift above threshold fails ✓
  (`tests/test_upgrade.py::test_compare_drift_over_threshold_fails`)
- Kuzu DB snapshotted pre-upgrade ✓ (`data/snapshots/pre-upgrade-*`)

## D10 — retention-class tagger

**What it does.** Every ingested episode carries a retention-class
tag — `normal`, `derived-only`, or `ephemeral`. `normal` is the
default (Luke's decision). `derived-only` preserves the extracted
structured facts in the graph but scrubs the raw episode text, so a
privacy-sensitive source (financial, health) can still contribute
facts without leaving prose in storage. `ephemeral` short-circuits
persistence entirely — the episode is held only for the immediate
call's return value.

**How it persists.** The graphiti schema doesn't include
retention_class; we add it via `ALTER TABLE ADD IF NOT EXISTS` at
`prepare_graphiti` time. Kuzu supports this (tested). The tag is
queryable via `MemoryAPI.list_by_retention("derived-only")` and
`MemoryAPI.retention_class_of(episode_uuid)`.

**Acceptance criteria covered.**
- `derived-only` produces structured facts but no retrievable raw
  text ✓ (verified in `scripts/eval_full_system.py` and
  `scripts/poa_demo.py` — content column is empty after scrub)
- `ephemeral` produces no persisted memory ✓ (short-circuit path in
  `MemoryAPI.ingest`)
- Default class is `normal` ✓ (`config/memory.yml retention.default_class`)
- Retention class queryable per entry ✓
- Class-filtered queries return only entries of that class ✓

## D11 — process-of-arrival capture

**What it does.** Background dispatches emit stream-of-consciousness
logs during execution. The `ProcessOfArrivalReceiver` summarises the
stream via Claude-via-Max and ingests two episodes — the final
outcome (class `normal`) and the reasoning summary (class
`derived-only`, so the raw stream doesn't persist). Both episodes
carry the dispatch's scope_id so retrieval for either returns both.

**Soft dependency.** The dispatch primitive that produces streams is
not yet built (brief §). D11 ships as a receiver with a mock
producer. The mock is `MockStreamLogProducer` at the end of
`src/process_of_arrival.py`. When the real dispatch primitive lands,
it implements `StreamLogProducer` and replaces the mock.

**What you see.** `scripts/poa_demo.py` walks through the flow end
to end. The summary is a structured pydantic object (objective,
decisions, reasoning, tools_used, conclusion) formatted into a
readable summary body. The retrieval for "Brazil market entry
recommendation" surfaces facts from both episodes — confirming the
acceptance criterion that "a retrieval query returns both the
outcome and the reasoning path when either is queried."

**Acceptance criteria covered.**
- Representative dispatch produces a stream log; the log is
  summarised by Claude via Max and ingested ✓
- Retrieval returns both outcome and reasoning ✓ (see poa_demo
  retrieval preview)
- Shipped as a receiver with a mock producer ✓

## D12 — Kuzu chaos-durability test

**What it does.** Confirms Kuzu's durability posture under adverse
conditions. Three scenarios:

| Scenario | Setup | Verification |
|----------|-------|-------------|
| kill-mid-ingest | Worker ingests ≥1 episode, parent SIGKILLs partway | DB reopens cleanly; episodes ≥1, ≤N |
| kill-mid-query | Seed DB via subprocess, query worker SIGKILLed mid-loop | Pre- and post-kill episode/edge counts identical (reads idempotent) |
| WAL recovery | Worker ingests 4 episodes and exits via `os._exit(0)` (skips close()) | On reopen, all committed episodes present |

**Runner report.** `scripts/chaos_durability.py` writes
`data/runs/chaos_durability_<ts>.json`. The headline from the
reference run (see `docs/chaos-durability-report.md`): all three
scenarios PASS.

**Findings that inform the architecture.** Kuzu holds a
process-level file lock and `KuzuDriver.close()` is a no-op. This
means multi-process access needs explicit inter-process coordination.
The chaos tests spawn every DB-touching step as a subprocess so no
lock carryover survives. This same pattern is adopted in D9's
upgrade harness.

**Acceptance criteria covered.**
- Kill-mid-ingest → clean rollback or recoverable state ✓
- Kill-mid-query → no state change ✓
- WAL-recovery → state restored to last commit ✓
- Run report produced ✓

## D13 — extended bundled documentation

**What it contains.**
- `docs/architecture.md` — system architecture + data flows (this file's sibling).
- `docs/prose-explanation.md` — plain-language why + what.
- `docs/deliverables-d5-d13.md` — this file.
- `docs/data-flow.md` — step-by-step flows on ingest / search / upgrade / chaos.
- `docs/relationship-map.md` — memory's interfaces to adjacent primitives.
- `docs/chaos-durability-report.md` — D12's run report.
- `docs/assumptions.md` — original prototyping-phase assumptions (unchanged).

**Acceptance.** A non-technical reader can answer "what does memory
do and how does it fit with the others" from these documents alone.
