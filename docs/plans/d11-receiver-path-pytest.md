# Amendment #15 — D11 receiver-path pytest plan

**Status:** plan (written before any test edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `fd7c6cf` (skip-launchctl-dead-code-removal seal — amendment #14's seal commit).
**Amends:** `memory-system/tests/` — adds the pytest file that exercises D11 (process-of-arrival capture ingestion) against the `ProcessOfArrivalReceiver` public API. Test-only. Zero `memory-system/src/` edits.
**Motivation:** D11 is a named acceptance criterion in `docs/archive/component-research/memory-system/brief-full-build.md` (lines ~102–109). The receiver (`memory-system/src/process_of_arrival.py`) + mock producer + working demo (`memory-system/scripts/poa_demo.py`) + a real 2026-04-18 audit run (`memory-system/data/observability_poa/audit.jsonl`) all ship — but no pytest test file asserts the AC. Under ODD §8.2 rule 9 a demo script is not a regression surface; a 1:1 AC↔test mapping is required. This amendment closes that coverage gap.

D11's AC text explicitly declares the mocked path is the full proof ("*mocked, since dispatch primitive not yet built*"), so no real-dispatch integration test is planned, dormant, or skipif'd.

---

## 1. Objective

Add `memory-system/tests/test_D11_process_of_arrival.py`, mapping D11's AC sub-behaviours 1:1 to outcome-shaped pytest functions that exercise `ProcessOfArrivalReceiver` via its public API with `MockStreamLogProducer` as input.

## 2. Scope

**Primary surface:** `memory-system/tests/test_D11_process_of_arrival.py` (new file).

**Secondary surfaces (bookkeeping):**
- `memory-system/tests/test_no_sealed_amendments.py` — advance `BASELINE` to pre-amendment tip (`fd7c6cf`); extend the BASELINE-history comment block with this amendment's narrative. No `allowed_prefixes` change (the existing tuple already admits `memory-system/` + `docs/plans/` + `data/`).
- `memory-system/tests/SEAL_COMMIT` — sidecar bump to the amendment commit SHA (seal-commit step).
- `hands-off-lifecycle/tests/test_cross_cutting.py` — `BASELINE` advance from `079258f` to `fd7c6cf`; extend the BASELINE-history comment block with this amendment's narrative. No `allowed` top-level set change (`memory-system` already admitted).
- `hands-off-lifecycle/tests/SEAL_COMMIT` — sidecar bump mirroring memory-system.
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append an amendment-cycle narrative note.
- `docs/plans/d11-receiver-path-pytest.md` — this plan.

**Not touched:**
- `memory-system/src/*` — zero implementation edits. The receiver ships; this amendment adds test surface only.
- `memory-system/scripts/poa_demo.py` — left as demo; tests are regression surface.
- Any other sealed component's src or tests.
- No `FUTURE_IDEAS.md` edit: the "real-dispatch integration test" idea belongs to a future dispatch-primitive component's own scope, not this amendment (explicit dispatch-brief directive).

## 3. Test names + assertion shapes

D11 packs several sub-behaviours into one criterion. Per ODD §8.2 rule 9 (one test per named AC sub-behaviour), tests split by behaviour; every name starts with `test_D11_` so grepping by D11 finds them all.

The AC text names these sub-behaviours:
1. A representative background dispatch (mocked) produces a stream log during execution; the log is summarised (by Claude via Max) and ingested.
2. A retrieval query returns both the outcome and the reasoning path when either is queried.
3. The mock producer stands in for the dispatch primitive (soft dependency).

Plus the receiver's invariant that the raw stream is NOT persisted (retention=DERIVED_ONLY on the reasoning episode, NORMAL on the outcome episode — `config/memory.yml` §process_of_arrival declares this contract).

### 3.1 `test_D11_mock_producer_log_is_summarised_and_ingested_as_two_episodes`

Covers sub-behaviour #1 + #3 (mocked-stream-log → summarise → dual ingest). Builds a `StreamLog` via `make_mock_log(...)`, runs it through `MockStreamLogProducer` → `receiver.receive(log)`, asserts the `ProcessOfArrivalResult` carries:
- An `outcome_episode_uuid` distinct from `summary_episode_uuid` (two episodes, not one).
- A non-empty `summary_text` (Claude summarisation fired and produced content).
- `dispatch_id` matching the input log.

Mocking strategy:
- `memory_ingest` → a fake async callable that captures kwargs per call and returns a deterministic synthetic UUID per call (`f"uuid-{call_index}"`). This is the documented injection point per the `ProcessOfArrivalReceiver.__init__` docstring ("Injected so this class does not depend on the full MemoryAPI construction path — tests substitute a fake ingest").
- `llm_client` → a fake object with `async generate_response(...)` returning the `_StreamSummary` schema dict shape directly. This mirrors the injection pattern the receiver is designed for (the class docstring names `llm_client` as a public constructor parameter with an "any LLMClient subclass works" contract).
- No real subprocess, no real Graphiti, no network, no real DB.

### 3.2 `test_D11_both_episodes_share_scope_id_and_dispatch_linkage`

Covers sub-behaviour #2 at the ingest-time invariant that makes retrieval-by-either-query work: both episodes are tagged with the same `scope_id` and their names encode the dispatch_id so retrieval-by-scope OR retrieval-by-dispatch returns both. (The receiver does not own the retrieval engine — that's MemoryAPI — so we assert the invariant at the ingest boundary, where the receiver's contract lives. Sub-behaviour #2 is "a retrieval query returns both," and the ingest-boundary invariant is the necessary-and-sufficient precondition the receiver provides for that guarantee.)

Assertion shape:
- The two `_ingest(...)` calls captured by the fake carry the same `scope_id` keyword argument (the log's scope_id).
- The outcome call's `name` matches `f"dispatch:{dispatch_id}:outcome"`.
- The summary call's `name` matches `f"dispatch:{dispatch_id}:reasoning"`.
- The summary call's body references `dispatch:{dispatch_id}:outcome` (explicit cross-reference so retrieval from the reasoning side can traverse back to the outcome).

### 3.3 `test_D11_reasoning_episode_is_tagged_derived_only_and_outcome_is_normal`

Covers the retention-class invariant named in the receiver docstring and the D11 brief ("the raw stream is not persisted; the summary is"). The reasoning episode must be tagged `DERIVED_ONLY`; the outcome episode must be tagged `NORMAL`. This is the necessary-and-sufficient precondition for the "raw stream not persisted" guarantee: DERIVED_ONLY causes the staging→drain path to scrub content post-extraction (per `retention.py` `apply_retention` and the receiver's config-derived default).

Assertion shape:
- The two `_ingest(...)` calls captured by the fake carry `retention_class=RetentionClass.NORMAL` (outcome) and `retention_class=RetentionClass.DERIVED_ONLY` (summary) respectively.

### 3.4 `test_D11_audit_record_captures_the_process_of_arrival_ingest`

Covers the observability contract for the ingest: an audit entry lands with `operation="process_of_arrival.ingest"`, naming the dispatch_id + both episode UUIDs + the retention-class decision. The audit record is how the memory-system surfaces that the raw stream was NOT persisted — without this, D7's "reconstructible without a consumer" guarantee would not hold for D11's flow.

Assertion shape:
- After `receiver.receive(log)` returns, the emitter's audit log contains at least one entry with `operation="process_of_arrival.ingest"`, `scope_id==log.scope_id`, `extras["dispatch_id"]==log.dispatch_id`, and `extras["outcome_episode_uuid"]` + `extras["summary_episode_uuid"]` matching the returned result. The rationale string references retention class.
- Uses a fresh `Emitter(sink_dir=tmp_path)` swapped in via `reset_default_emitter(...)` for isolation.

### 3.5 `test_D11_truncation_guard_elides_oversized_streams_before_summarisation`

Covers the receiver's `max_stream_chars` bound (config §process_of_arrival, default 24000). Oversized logs get truncated before being sent to the summariser. Without this bound, a runaway dispatch could exhaust the summariser's context budget — a named invariant at `ProcessOfArrivalReceiver.receive` lines 126–128. This is not a separate AC in D11's text, but it IS part of the receiver's documented contract; per ODD §8.2 rule 9 (one test per named behaviour), this invariant gets a test at the behaviour it names, not one of the broader tests above.

Assertion shape:
- Build a log with `lines` whose joined `raw_stream_text` exceeds `max_stream_chars`.
- Capture the `user_content` arg the fake LLM client receives.
- Assert the stream excerpt embedded in the prompt has the truncation marker `[truncated: N chars elided]`.
- Assert the excerpt length (modulo the marker) is exactly `max_stream_chars`.

## 4. Test-count delta

- `memory-system/`: 62 → 67 (+5 new tests in `test_D11_process_of_arrival.py`).
- `hands-off-lifecycle/`: 66 → 66 (unchanged — BASELINE + narrative edits only, no new tests).
- All other sealed components: unchanged.

## 5. BASELINE advances

- `memory-system/tests/test_no_sealed_amendments.py`: `77389ce` → `fd7c6cf` (the pre-amendment tip — amendment-#14's seal commit immediately before this amendment's code commit).
- `hands-off-lifecycle/tests/test_cross_cutting.py`: `079258f` → `fd7c6cf` (same pre-amendment tip).

No other BASELINE advances. All other sealed components' seal-diff tests read their own `SEAL_COMMIT` sidecars (not advanced by this amendment), so their diff windows do not widen.

## 6. Halt triggers

- [x] Receiver can be exercised deterministically under clean mocks. `memory_ingest` + `llm_client` are both documented injection points on `ProcessOfArrivalReceiver.__init__`; no private-attribute inspection needed. **Not hit.**
- [x] Test does not require real Claude or real Graphiti. Mocks cover both subprocess + Graphiti surfaces. **Not hit.**
- [x] Scope stays within `memory-system/tests/` + plan doc + BASELINE-bump-of-hands-off-lifecycle. No other sealed component touched. **Not hit.**
- [x] D11's AC as-written matches what the receiver does (dual ingest, DERIVED_ONLY + NORMAL retention, scope-id linkage, audit). Verified by reading `process_of_arrival.py` + the brief in parallel. **Not hit.**
- [x] No permanent-dormant test (no `@pytest.mark.skipif` waiting on future dispatch primitive — D11's AC calls the mocked path the full proof). **Not hit.**

## 7. Commit structure

Two commits (no amends — audit-trail structure):

1. **Amendment commit** — `fix(memory-system, hands-off-lifecycle): D11 process-of-arrival receiver-path pytest (amendment #15)` — includes the new test file, BASELINE bumps in both sealed-component seal tests, BASELINE-history comment blocks, this plan doc. All test suites green before commit.

2. **Seal commit** — `chore(seals): d11-receiver-path-pytest seal — memory-system + hands-off-lifecycle at <amendment-sha>` — bumps `memory-system/tests/SEAL_COMMIT` and `hands-off-lifecycle/tests/SEAL_COMMIT` to the amendment commit's SHA; appends the amendment-cycle narrative to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`. Tests green again against the bumped sidecars.
