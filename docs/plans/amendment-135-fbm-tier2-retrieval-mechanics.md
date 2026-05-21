# Amendment #135 — FBM Tier 2 retrieval mechanics (power-law base-level activation + co-citation graph + one-hop spreading activation)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21.
**Working directory:** `/Users/lukeivers/loam/`.
**Parent research artefact:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbm-end-to-end-rethink-v2-synthesized-2026-05-21.md` — the v2 design this plan implements (Tier 2 section).
**Research substrate:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/human-memory-structural-concepts-for-fbm-2026-05-21.md` — A.1 anchored in Anderson & Schooler 1991 / ACT-R; B.1 anchored in Tulving 1973 + Anderson HAM/ACT-R + Anderson et al. 2004.
**Predecessors (load-bearing):**
- `612500304c5ad6d17ec8440d9fd551ba723b981d` — amendment-134 seal (FBM Tier 1 foundations: supersession marker + encoding-context capture + FIDRAFT cleanup-on-seal + plan-doc archive-on-seal); Tier 2 retrieval reads Tier 1's frontmatter at score time.
- `1a1f830` — M-FBM operational-health AC family seal (file-based memory baseline; the BM25/FTS5 retrieval surface that Tier 2 extends).
- canonical loam HEAD at plan-author time (`48e7b29`) — BASELINE candidate; pinned at apply time.
**BASELINE (pre-build tip):** TBD — pinned in the manifest at apply time; the build agent records the SHA into §14 at apply.
**Quality bar:** two scope-disjoint AC families (PLBLA + COCG) each verified by unit + the outcome-altitude smoke (`AC.FBMT2.S`); no method-in-AC; canonical loam component fence on `framework/primary-persona/` respected.

---

## §1. Objective / Summary / TL;DR

Ship **two scope-disjoint retrieval-mechanics primitives** that close the F-RECENCY and F-PHRASING failure modes named in the v2 FBM rethink, anchored in primary cognitive-science literature (Anderson & Schooler 1991 for the power-law functional form; Anderson 1983 / Anderson et al. 2004 for the spreading-activation mechanism). Per Q2 + Q4 owner ratification (TG 11809 + 11810), the two items ship as a **single multi-component amendment** scoped to T2.1 + T2.2 only; T2.3 working-set is owner-deferred and explicitly out of scope.

The two primitives (each described by an outcome-shape AC family — see §4):

1. **T2.1 Power-law base-level activation column** (`AC.FBMT2.PLBLA`) — a sidecar access log records every memory read/write/cite touch; the retrieval ranker computes per-file activation `B_i = ln(Σ_j (now − t_j)^(−d))` with `d = 0.5` (canonical Anderson & Schooler 1991 / ACT-R value); final retrieval score = BM25 × activation. Pure-recency-without-frequency boost is replaced by this formula. Cures F-RECENCY: recent-but-irrelevant chatter fades unless repeatedly accessed; pattern-of-repeated-relevance dominates over single-recent-touch.
2. **T2.2 Co-citation graph + one-hop spreading activation** (`AC.FBMT2.COCG`) — a co-citation graph is built from the access log + agent transcripts; edge weight `S_ji = log(P(file_i | file_j) / P(file_i))` per Anderson HAM/ACT-R. At retrieval time, BM25 produces candidate set C; spread one hop, add neighbor n of c ∈ C with `score(c) × S_cn`, capped at one hop. Cures F-PHRASING: a query about "X" can surface a file that never contains the literal token "X" if associative edges connect to a token the file does contain.

Plus one outcome-altitude smoke (`AC.FBMT2.S`) that exercises both primitives end-to-end against the production retrieval contributor with no pre-arranged state.

**Per Q3 owner ratification (TG 11809):** B.1 (T2.2) ships **build-forward** (always-on capture from new turns) AND **one-shot retroactive seed** that mines existing access logs + agent-transcript JSONL files at deploy time to bootstrap the graph. Without the seed, the graph has weeks of warm-up before usable coverage; with the seed, useful coverage from day one. The seed scope (D-T2.2.SEED) is the existing memory-write log entries (already on disk in canonical loam) and the Claude Code agent-transcript JSONL files under `~/.claude/projects/`.

**Owner-ratification record (durable, recorded here per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11804 | 2026-05-21T16:10:07Z | Q1 = (a) keep T1.2 (encoding-context capture is now substrate; Tier 2 may consume it later — but at v0.1 of Tier 2 the activation + co-citation primitives do NOT depend on the encoding-context fields). |
| TG 11808 | 2026-05-21T16:14:01Z | Build-strategy delegation ("trust you on build strategies; happy to provide input if you're not confident") — the seven §14 method-decisions are persona-class per this ruling. |
| TG 11809 | 2026-05-21T16:15:00Z | Q3 = both forward + one-shot retroactive seed for B.1 co-citation graph. |
| TG 11810 | 2026-05-21T16:?? | Q4 = (b) defer T2.3 working-set; explicitly NOT in this Tier 2 plan-doc. |
| TG 11817 | 2026-05-21T16:?? | Dogfood-then-autonomous-publish process ratified — composes with this plan's build-complete step (§9). |

**F2 Ruthless Feedback on scope realism (§10):** two retrieval primitives + a co-citation graph + a retroactive seed pass in a single multi-component fence is at the upper edge of what one build agent can cleanly seal. Both items land in `framework/primary-persona/` (single component) so there is no cross-component coordination cost — the upper-edge concern is test surface (≥9 ACs) and the seed pass's empirical risk (the existing access logs may be too sparse to bootstrap a useful graph). The natural in-flight split is T2.1 first (the simpler primitive; gives F-RECENCY cure on its own) then T2.2 second (the graph + spread mechanism); documented in §8 halt triggers as the in-flight escape hatch.

**Pre-flight verification (per `feedback_verify_fidraft_against_canonical_before_dispatch`):**

- `ls framework/primary-persona/src/loam/primary_persona/file_memory.py` — present; Tier 1's `ENCODING_CONTEXT_FIELDS` + `SUPERSEDED_PENALTY` symbols verified at lines 969–974 + 258.
- `grep -rn 'base.level.activation\|co.citation.graph\|spreading.activation' framework/ --include='*.py'` — **zero matches**. No T2.1 / T2.2 implementation exists.
- `git log --oneline --grep='base.level.activation\|spreading.activation\|co.citation' --all | head -10` — **zero matches**. No prior seal commit for any Tier 2 item.
- Tier 1 amendment-134 sealed on main at `612500304c5ad6d17ec8440d9fd551ba723b981d` (verified at canonical HEAD).
- `ls framework/primary-persona/` confirms the component exists (the fence path the dispatching brief named is accurate this time, unlike #134 where the brief named non-existent components — this brief learned from that miss).

Pre-flight clean. Building forward is correct.

---

## §2. Predecessors / context

This amendment composes against:

- **File-memory substrate** at `framework/primary-persona/src/loam/primary_persona/file_memory.py`. T2.1 extends `_blend_recency` (or a new `_blend_activation` sibling) to multiply by the power-law activation column; T2.2 extends the retrieval-contributor pipeline with a post-BM25 spread step. Tier 1 substrate (`SUPERSEDED_PENALTY`, `ENCODING_CONTEXT_FIELDS`, the `superseded-by` parser branch) survives unchanged.
- **Memory-write worker** at `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py`. T2.1's access-log appender hooks into the worker's drain path (every `add_episode` is a `write` event) AND into the retrieval contributor's call site (every `search` candidate hit is a `read`/`cite` event).
- **Existing access traces** under `~/.claude/projects/*/memory/` + agent-transcript JSONL files. These are the **input** to T2.2's retroactive seed pass; the pass mines them once at amendment apply time.

---

## §3. Scope

### In-scope

- T2.1 power-law base-level activation column on memory files.
- T2.2 co-citation graph + one-hop spreading activation.
- T2.2's one-shot retroactive seed pass (per Q3 ratification).
- The outcome-altitude smoke (`AC.FBMT2.S`) exercising both primitives end-to-end.

### Out of scope (deferred)

- **T2.3 pinned working set** — owner-deferred per Q4 ruling TG 11810; explicitly NOT in this plan-doc. Separate design conversation later.
- **Tier 3 orchestration** — C.1 session-end consolidation + C.2 scheduled consolidation routine. Depends on Tier 1 + Tier 2 done first; separate amendment.
- **Embedding-based retrieval** — v2 research explicitly rejected this in favor of B.1 spreading activation (research §B claims B.1 + light query-expansion gets ~80% of an embedding index at ~5% of operational complexity — conjecture flagged in the research's "Conjectures explicitly flagged" §). No embedding model, no LLM at retrieval time.
- **Multi-hop spreading** — strictly one hop at v0.1 per D-T2.2.SPREAD (the cognitive-science evidence specifically supports one-hop dominance; multi-hop is exponentially more expensive). Multi-hop is a future tuning amendment if observed need lands.
- **Activation-decay tuning** — `d` is hard-coded at `0.5` (the canonical ACT-R value) per D-T2.1.DECAY. Configurability deferred until a concrete tuning request lands.
- **Persisted graph file** — the co-citation graph is rebuilt at session-start from the access log per D-T2.2.GRAPH; no graph file on disk. Persisting + invalidating is deferred until rebuild cost becomes a measured problem.
- **Encoding-context retrieval lane** — Tier 1's `context:` block (`triggering_msg_id`, `active_task_id`, `cwd`, `active_files`) IS substrate Tier 2 may consume later, but at v0.1 of Tier 2 the activation + co-citation primitives do NOT condition on encoding-context fields. Surfacing context-conditioned retrieval is a future amendment; the Tier 1 substrate is in place for it.

---

## §4. Acceptance criteria

AC IDs per `feedback_scope_descriptive_ac_ids` — scope-descriptive (FBMT2.*), NOT version-packed.

### AC.FBMT2.PLBLA family — power-law base-level activation

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT2.PLBLA.1** | Every memory touch (write via the worker; read/cite via the retrieval contributor surfacing the file in a result set) appends a structured entry to a sidecar access log. The log entry records the touched file, an ISO-8601 UTC timestamp, and an operation tag from a closed enum. | Test drives a memory write through the worker, then a retrieval through the contributor; reads the sidecar log; asserts each touch produced exactly one entry whose fields parse to the expected structure (file path resolvable, timestamp parseable as ISO-8601 UTC, op ∈ closed enum). |
| **AC.FBMT2.PLBLA.2** | The retrieval ranker's final score composes BM25 with activation **multiplicatively** in a way that observably re-orders results. Concretely: a file with high BM25 + low activation ranks **below** a file with moderate BM25 + high activation when the activation differential exceeds the BM25 differential. | Test constructs two memory files with controlled BM25 scores (via synthetic content + query); seeds the access log so file_A has many recent accesses and file_B has none; asserts file_A ranks above file_B even when file_B's pre-activation BM25 score is higher (the multiplicative composition observable). |
| **AC.FBMT2.PLBLA.3** | The activation formula matches the Anderson & Schooler 1991 functional form: for synthetic access patterns (single access at t_1; two accesses at t_1 and t_2; etc.), the computed activation equals the expected `B_i = ln(Σ_j (now − t_j)^(−d))` to within floating-point tolerance. | Test injects a synthetic access pattern with known timestamps; computes the expected activation in the test using the formula directly; calls the production activation function; asserts the production value matches the expected within `1e-9` tolerance. Bands at least the single-access case, the two-access case (frequency-pattern observable), and the zero-access case (returns the floor / epsilon — see D-T2.1.FLOOR). |
| **AC.FBMT2.PLBLA.4** | A workspace with no access log file present (fresh workspace; cold start) returns the **pure-BM25 ranking** without raising. The activation column degrades to neutral when no signal exists. | Test runs the retrieval contributor against a workspace whose memory directory has no access-log sidecar; asserts the ranker returns results in BM25 order (no activation contribution) and does not raise. |
| **AC.FBMT2.PLBLA.5** | Backwards-compat: existing memory files written before this amendment (no Tier-1 `context:` block, no access-log history) retrieve cleanly under the new ranker. | Test seeds a memory file with the pre-amendment shape; asserts the retrieval contributor returns it in BM25 order; asserts no schema-validation error or warning fires. |

### AC.FBMT2.COCG family — co-citation graph + one-hop spreading activation

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT2.COCG.1** | A co-citation graph is built from the access log (and at retroactive-seed time, from existing memory-write log entries + agent-transcript files). Edge weight matches the Anderson HAM/ACT-R functional form: `S_ji = log(P(file_i | file_j) / P(file_i))` computed from co-occurrence counts, floored at a small epsilon to avoid `log(0)`. | Test seeds a synthetic access log + transcript corpus with known co-occurrence counts; builds the graph; asserts each edge weight equals the expected `log(P(i|j)/P(i))` to within `1e-9` tolerance; asserts never-co-occurring pairs map to the epsilon floor (not `−inf` / not raised). |
| **AC.FBMT2.COCG.2** | At retrieval time, when BM25 produces a candidate set C, the ranker adds to the returned result set every one-hop neighbor n of c ∈ C scored as `score(c) × S_cn`, capped at one hop. Concretely: the F-PHRASING cure is observable — a query whose tokens appear in file_A but not file_B, where the co-citation graph has a strong A↔B edge, surfaces file_B in the result even though pure BM25 would have missed it. | Test seeds the graph with a strong A↔B edge; constructs a query that lexically matches A but not B; asserts file_B appears in the result set; asserts its score is `score(A) × S_AB`. |
| **AC.FBMT2.COCG.3** | The one-shot retroactive seed pass populates the graph from existing memory-write log entries + agent-transcript JSONL files at amendment-apply time (Q3-ratified). The seed pass is idempotent (running it twice does not double-count). | Test runs the seed pass against a synthetic corpus of existing log + transcript files with known co-occurrences; asserts the resulting graph has the expected edge weights; runs the seed pass a second time against the same corpus; asserts the graph is byte-identical to the first-pass result (idempotency). |
| **AC.FBMT2.COCG.4** | A workspace with an empty graph (fresh workspace; no co-occurrences yet) returns BM25 + activation results unchanged (no spread contribution). The spreading-activation step degrades to neutral when no graph exists. | Test runs the retrieval contributor against a workspace whose access log exists but contains no co-occurring touches; asserts the result set is exactly the BM25 × activation result (no neighbors added); asserts no error or warning. |
| **AC.FBMT2.COCG.5** | The graph is capped at strictly one hop. A two-hop reachable file (A→B→C, no direct A↔C edge) does NOT enter the result set on a query matching only A. | Test seeds A↔B and B↔C edges with no A↔C edge; runs a query lexically matching only A; asserts file_C is NOT in the result set; asserts file_B IS in the result set (one hop from A). |

### AC.FBMT2.S — outcome-altitude smoke (single end-to-end exercise)

**Marked `outcome-altitude: true` per `feedback_test_outcome_altitude_required`.** Invokes the production retrieval contributor with no pre-arranged state beyond a synthetic memory corpus + a synthetic access-log seed; verifies both primitives' behaviors in one synthetic flow.

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT2.S** | A single test exercises the full Tier 2 retrieval surface: (a) seed a memory corpus of ≥3 files with controlled lexical overlap; (b) seed an access log with ≥5 events showing the frequency-pattern observable (file_A accessed many times recent, file_B accessed once recent, file_C accessed never) — verifies the activation column observable (T2.1); (c) seed the co-citation graph with a strong A↔C edge — verifies the one-hop spread observable when a query lexically matches A and the result includes C without C being lexically matched (T2.2); (d) issue the query through the production `build_file_memory_retrieval_contributor` factory — the contributor is the production entry-point, not a test stub. | The test invokes `build_file_memory_retrieval_contributor` (or its production wiring equivalent in `register_file_memory_retrieval`) with the synthetic corpus + seed; asserts the returned result set contains file_C (the spread observable, T2.2); asserts file_A ranks above file_B despite identical BM25 (the activation observable, T2.1); asserts the test does not patch internal helpers like `_blend_recency` or `_superseded_marker` (the production code path is what's exercised — `feedback_test_outcome_altitude_required` risk-band: HIGH because Tier 1's V025-C1 lesson today showed how easily a stub patches the wrong path). |

---

## §5. Sealed-component fence (multi-component)

**Components touched:**

- `framework/primary-persona/` — file-memory access log writer + reader (`file_memory.py`), retrieval-ranker extension for activation composition (`file_memory.py`), co-citation graph data structure + builder + retrieval-time lookup (new module or extension to `file_memory.py`; builder's call per ODD §1.1), retroactive-seed mining utility (one-shot; ephemeral or part of `file_memory.py`'s public surface — builder's call), and the memory-write worker access-log hook (`memory_write_worker.py`). All Tier 2 source edits land in this component.

**Single-component fence in practice.** Although the dispatching brief framed this as "multi-component," in canonical loam every Tier 2 source edit is in `framework/primary-persona/`. There is no `dev-sdlc` change in this amendment. The manifest declares only the primary-persona component.

**Universal admissions** (per amendment #22 ruling #3):

- `docs/plans/` prefix (this plan-doc + manifest). Per Tier 1's T1.4 (now sealed in amendment-134), this plan-doc archives itself into `docs/plans/sealed/` on seal — second non-trivial dogfood of T1.4.
- `docs/STATE.md` — bookkeeping update (§9).
- `docs/FUTURE_IDEAS_DRAFT.md` — admitted in case the retroactive seed surfaces an idea worth durable capture; the dispatching brief does not require touching it.

**Out of fence (halt-and-surface trigger):**

- Any component under `framework/` or `plugins/` other than `framework/primary-persona/`.
- Any edit to `docs/spec/` (objectives spec; outside any cycle's fence per persona instructions).
- Tier 2 retrieval should NOT modify Tier 1's `SUPERSEDED_PENALTY` or `ENCODING_CONTEXT_FIELDS` constants — those are sealed substrate. Any code that needs to reference them imports them; modifying them is a halt-and-surface.

---

## §6. Build steps (multi-component, single cycle)

**Sequencing within the cycle.** The two AC families are scope-disjoint; T2.1 lands first because T2.2's spread step composes against T2.1's activation column (final score = BM25 × activation × spread). The builder's call per ODD §1.1.

1. **Plan-doc lands** (this file) + manifest YAML.
2. **Source edits — T2.1 (PLBLA cluster):**
   - `framework/primary-persona/src/loam/primary_persona/file_memory.py` — add an access-log sidecar reader/writer (`{file, ts, op}` JSONL; reader returns the parsed event list); add an activation-column computer (`_compute_activation(events: list, now: datetime) -> float`); extend the ranker composition step to multiply by activation; preserve the existing `SUPERSEDED_PENALTY` branch unchanged.
   - `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py` — extend the worker's drain path to append a `write` event to the access log on every successful `add_episode` call.
   - `framework/primary-persona/src/loam/primary_persona/file_memory.py` — extend the retrieval contributor (the `build_file_memory_retrieval_contributor` / `FileBackedMemoryClient.search` surface) to append `read` events for every result the contributor surfaces. The `cite` event is reserved for an explicit "file referenced in plan-doc / source edit" emit path that this amendment does NOT wire — the enum is closed at `{read, write, cite}` for future-compat but only `read` and `write` fire from production code at v0.1.
3. **Tests authored — T2.1:**
   - `framework/primary-persona/tests/test_AC_FBMT2_PLBLA_1_access_log_records_touches.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_PLBLA_2_multiplicative_composition.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_PLBLA_3_formula_matches_anderson_schooler.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_PLBLA_4_graceful_on_absent_log.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_PLBLA_5_backwards_compat.py`
4. **Source edits — T2.2 (COCG cluster):**
   - `framework/primary-persona/src/loam/primary_persona/file_memory.py` (or a new sibling `cocitation_graph.py` — builder's call) — co-citation graph data structure (dict-of-dicts per D-T2.2.GRAPH); graph builder that reads the access log + (at seed time) the existing transcript files; edge-weight computer per `S_ji = log(P(i|j)/P(i))`; one-hop spread function that takes a BM25 candidate set + the graph and returns the spread additions.
   - `framework/primary-persona/src/loam/primary_persona/file_memory.py` — extend the retrieval pipeline to: BM25 → activation multiply → one-hop spread → return.
   - Retroactive seed utility — builder's call whether this is a CLI subcommand (e.g. `loam memory seed-graph`) or a one-shot script invoked at amendment apply time. Both shapes satisfy AC.FBMT2.COCG.3; the recommendation is a CLI subcommand for future re-invocation but a one-shot script also passes if the build agent prefers minimal surface area.
5. **Tests authored — T2.2:**
   - `framework/primary-persona/tests/test_AC_FBMT2_COCG_1_edge_weight_formula.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_COCG_2_one_hop_spread_observable.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_COCG_3_retroactive_seed_idempotent.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_COCG_4_graceful_on_empty_graph.py`
   - `framework/primary-persona/tests/test_AC_FBMT2_COCG_5_one_hop_cap.py`
6. **Outcome-altitude smoke:**
   - `framework/primary-persona/tests/test_AC_FBMT2_S_end_to_end_smoke.py` — exercises both primitives against `build_file_memory_retrieval_contributor` with no pre-arranged state beyond a synthetic memory corpus + seed events.
7. **Touched-tests run** (new tests + existing `framework/primary-persona/tests/` suite — specifically the AC.MFBM.*, AC.MSC.*, AC.FBMT1.* families must remain green; AC.FBMT1.SUPM.2's "ranker demotes superseded files" assertion specifically must survive the activation-column composition).
8. **One-shot retroactive seed pass:** the build agent invokes the seed utility against the canonical `~/.claude/projects/*/memory/` + agent-transcript JSONL files. The graph artifact is rebuilt at session-start; the seed pass's role is to populate the access log with historical co-occurrence events so the graph builder has data to work from. The seed pass is a bookkeeping step (NOT a production-code commit), BEFORE `loam amend apply` so the apply step's seal-diff window sees a clean fence. Per AC.FBMT2.COCG.3 the pass is idempotent; the build agent runs it once.
9. **`loam amend apply`** — auto-commit lands per v0.1.2 ergonomics.
10. **`loam amend seal`** — deterministic seal commit; this seal IS the **second non-trivial user of T1.4** (the plan-doc archives itself on seal, eating Tier 1's dog food a second time).
11. **Smoke (D1 cold-state):** fresh workspace → memory write appends a `write` event to a new access log → retrieval surfaces the file → a `read` event appends → activation column observable; second file co-cited with the first surfaces via spread on a query matching only the first.
12. **Dogfood-then-autonomous-publish step (per TG 11817):** before publish gate, exercise the new retrieval mechanics in the pos3 derived workspace against real memory traces. Publish gate is owner-asked per `feedback_hard_smoke_per_minor_before_publish` (HARD smoke only required at the per-minor publish boundary; this is a per-cycle build).

---

## §7. Ship shape

**Single cycle, multi-component (single-component in practice — only `framework/primary-persona/`).** No sub-amendment series. The two AC families ship under one manifest + one apply commit + one seal commit. The retroactive seed pass is one bookkeeping invocation prior to apply (no commit; the access log is workspace-local data).

**Commit ladder (expected):**

1. plan-doc + manifest commit (this file).
2. Source-edits commit — `feat(primary-persona): FBM Tier 2 retrieval mechanics (T2.1 power-law base-level activation + T2.2 co-citation graph + one-hop spreading activation + Q3 retroactive seed)`.
3. `loam amend apply` auto-commit.
4. `loam amend seal` deterministic seal commit (this commit DOES the T1.4 move on itself — second non-trivial T1.4 user).

---

## §8. Halt triggers (in-flight)

- WD drifts (anything other than `/Users/lukeivers/loam`) → halt + surface.
- Any source edit outside `framework/primary-persona/` → halt + surface.
- Any AC ships partial → halt + reframe; do NOT seal partial.
- Outcome-altitude smoke `AC.FBMT2.S` fails after all unit ACs green → halt + investigate; the unit tests passing without the smoke is a known method-in-AC red flag (the V025-C1 lesson today).
- The Anderson & Schooler formula's `(now − t_j)^(−d)` is undefined when `t_j == now` (zero-duration); surface the floor / epsilon decision as a §14 method-decision (D-T2.1.FLOOR — recommended in §14 below but builder may discover a better floor empirically). Halt if the recommended floor produces test-observable artifacts.
- The retroactive seed pass finds **zero existing co-occurrences** (suggests the access-log instrumentation never fired historically — which is correct for this amendment since the instrumentation didn't exist before) — this is NOT a halt; it's expected. The seed instead mines agent-transcript JSONL files for historical file-touch co-occurrences. If THAT also finds zero (transcript files not where expected), halt + surface (the data source is missing).
- A test's stub or fixture patches the wrong code path — per V025-C1 lesson, verify production-path symbols are the patch targets; halt-and-surface if a test would pass by stubbing past the production retrieval entry-point.
- Fence-pressure: build agent finds it cannot cleanly seal both T2.1 + T2.2 in one cycle and surfaces the natural split (T2.1 first, T2.2 second) per §1 F2-RF note → halt + surface to dispatcher; this is the documented escape hatch.
- The graph rebuild at session-start exceeds the 5s session-start envelope (per AC.MSC.*'s deterministic-scan budget) — halt + surface (D-T2.2.GRAPH may need to switch from rebuild-on-session-start to persisted-on-disk; the deferred-decision in §3 may need promotion).
- Spread step produces O(|C|²) candidate explosion on a query matching the densest hub-file (a "FUTURE_IDEAS_DRAFT.md"–scale file with thousands of co-occurring neighbors) — halt + surface; recommend per-edge surface cap.

---

## §9. Bookkeeping

- `loam amend apply` (NOT `git commit --amend`; per `feedback_no_amend_in_agent_dispatches`).
- One semantic commit per ladder step (see §7).
- Update `docs/STATE.md` with the amendment #135 row.
- §14 method-decision register populated by the builder at apply time.
- §14 SHA backfill via `loam amend seal --plan-doc docs/plans/amendment-135-fbm-tier2-retrieval-mechanics.md` (which, post-T1.4, will land at `docs/plans/sealed/amendment-135-fbm-tier2-retrieval-mechanics.md`). Note from Tier 1's §16 Finding #5: the seal-tool's `--plan-doc` §14 backfill regex matches `## 14.` but NOT `## §14.`. **This plan-doc uses `## §14.`** for consistency with #134 — the builder should expect to do the §14 SHA backfill manually as #134's builder did. The corrective amendment to widen the regex is a separate follow-up (named in §10 doubt #5).
- Retroactive seed pass is a bookkeeping step (not a commit); the access log written by the pass is workspace-local data under `~/.claude/projects/*/memory/.access-log.jsonl`.
- Post-seal: append an FIDRAFT entry capturing any T2.2 graph-quality observations from the dogfood pass that warrant future tuning (D-T2.1.DECAY, D-T2.2.SPREAD, D-T2.2.GRAPH all named as candidates for future revisit per the v2 research's "Conjectures explicitly flagged" §).

---

## §10. F2 Ruthless Feedback (honest doubts)

Five named doubts on this plan, surfaced per `feedback_ruthless_feedback`:

1. **Multiplicative composition with the existing recency blend.** Tier 1 (and pre-Tier-1) ranker code already carries a recency-blend mechanism via `_blend_recency` (file_memory.py L1203 — RECENCY_BLEND_WEIGHT=0.5, RECENCY_HALF_LIFE_DAYS=5.0). T2.1's power-law activation is a **different mathematical model** of the same phenomenon (recency-shaped retrieval relevance). Naive composition (`BM25 × recency_blend × activation`) double-counts recency. The recommendation per D-T2.1.SCORE is to **replace** the existing `_blend_recency` recency channel with the activation column (the activation IS the recency model the v2 research argues should win, anchored in Anderson & Schooler 1991), keeping the BM25-relevance channel intact. The natural side-effect: AC.MSC.1's "recency reaches the top-N" behavior changes — the test will need updating to assert the activation-blend equivalent. Halt-and-surface if the existing AC.MSC.1 test fails after the swap and the builder is unsure whether to update the test or revisit the swap.

2. **Retroactive seed data sparsity.** The retroactive seed pass mines existing access traces, but the **instrumentation that emits those traces is being added by this amendment**. Existing canonical loam has no `.access-log.jsonl` file; the seed pass's only data source is the agent-transcript JSONL files under `~/.claude/projects/`. Those files do exist and DO capture which files an agent read in a turn (via tool-result records), but they're not currently parsed for memory-file co-occurrence. The recommendation is to ship the seed pass against transcript files and expect graph density to be **light** at v0.1; the build-forward instrumentation then enriches the graph over days/weeks. If the seed pass produces an edge-list of <50 edges total, the F-PHRASING cure observable in AC.FBMT2.COCG.2 may not fire in real-world traffic until the graph warms up. Recommendation: accept the slow warm-up; AC.FBMT2.COCG.2 is verified against a **seeded synthetic graph** (the test arranges the edges directly), so the AC ships green; real-world cure is empirical.

3. **The "~80% of an embedding-index" claim is research conjecture.** The v2 research artifact §B explicitly flags "B.1 + B.2 in combination probably gets ~80% of what an embedding-index would deliver on F-PHRASING" as "**my conjecture, not in any cited source.**" This amendment ships B.1 only (no B.2 query-expansion fallback); the claim is unverified. The right empirical measurement is: at some point post-ship, instrument a query corpus and measure recall@K against an embedding-index baseline. That measurement is OUT OF SCOPE for this amendment but should land as an FIDRAFT entry post-seal.

4. **`d = 0.5` is the canonical ACT-R value, but loam's memory corpus is not ACT-R's experimental dataset.** Anderson & Schooler 1991 derived `d ≈ 0.5` from empirical fits to child-directed speech, NYT headlines, and email logs. Loam's memory corpus (personal rules, plan-docs, agent transcripts) is in a different distribution. The value may need tuning. Recommendation per D-T2.1.DECAY: ship `d = 0.5` hard-coded at v0.1; configurability deferred per `feedback_principle_application_front_load_and_audit` (don't expose tuning knobs until evidence of need lands). FIDRAFT entry on post-seal observations covers the tuning lane.

5. **The seal-tool §14 backfill regex narrowness (Tier 1 finding #5) is still in place.** This plan-doc uses `## §14.` heading; the seal-tool's `--plan-doc` backfill regex won't match. The builder MUST do the §14 SHA register backfill manually, exactly as #134's builder did. A separate corrective amendment to widen the regex is the right durable fix — FIDRAFT entry post-seal. Surfacing here so the builder is not surprised.

---

## §14. Method-decision register

**Ratification table (recorded at plan-doc commit time, per `feedback_record_owner_ratification_before_dispatch`):**

| Decision | Recommendation | Ratified by | Authority |
|----------|----------------|-------------|-----------|
| D-T2.1.DECAY | `d = 0.5` (canonical Anderson & Schooler 1991 / ACT-R value); hard-coded at v0.1 | persona | Owner build-strategy delegation TG 11808 |
| D-T2.1.LOGFMT | JSONL with fields `{file, ts, op}`; op enum `{read, write, cite}` | persona | Owner build-strategy delegation TG 11808 |
| D-T2.1.SCORE | Multiplicative: final = BM25 × activation; **replaces** existing recency-blend channel | persona | Owner build-strategy delegation TG 11808 |
| D-T2.1.FLOOR | Floor `t_j = now − epsilon` (epsilon = 1.0 second) when `t_j == now` | persona | Owner build-strategy delegation TG 11808 |
| D-T2.2.GRAPH | In-memory dict-of-dicts rebuilt at session-start from the access log; not persisted | persona | Owner build-strategy delegation TG 11808 |
| D-T2.2.EDGEWEIGHT | `S_ji = log(P(i|j) / P(i))` per Anderson HAM/ACT-R; epsilon floor on never-co-occurring pairs | persona | Owner build-strategy delegation TG 11808 |
| D-T2.2.SEED | Mine `~/.claude/projects/*/memory/` + agent-transcript JSONL files; idempotent one-shot | persona | Owner Q3 ratification TG 11809 + build-strategy delegation TG 11808 |
| D-T2.2.SPREAD | Strictly one hop at v0.1; multi-hop deferred | persona | Owner build-strategy delegation TG 11808 |

Ratification rationale: owner's TG 11808 explicitly delegated build-strategy decisions to the persona ("trust you on build strategies; happy to provide input if you're not confident"). All eight §14 decisions are build-strategy detail (decay constant, log format, score composition, floor value, graph data structure, edge formula, seed scope, hop count). Persona confident on all eight per the rationale below; no owner escalation needed.

Populated at build time + sealed in by `loam amend seal --plan-doc` (with manual §14 backfill — see §10 doubt #5). The eight method-decisions named here at plan-time:

### D-T2.1.DECAY — Power-law decay constant `d`

**Decision (recommendation):** `d = 0.5` — the canonical Anderson & Schooler 1991 value (also used by the ACT-R cognitive architecture per Anderson et al. 2004).

**Rationale:** the canonical value is the right starting point for a v0.1 implementation. Anderson & Schooler derived it empirically across three datasets (child-directed speech, NYT headlines, email logs); the cross-domain consistency is the evidence that `d ≈ 0.5` is a robust environmental constant rather than dataset-specific. Loam's memory corpus is a fourth distribution, but starting at the literature's value gives a defensible baseline.

**Alternative:** configurable via env var or config-file. **Recommendation:** rejected at v0.1 per `feedback_principle_application_front_load_and_audit` (don't expose tuning knobs until evidence of need lands). FIDRAFT entry post-seal covers the future-tuning lane.

### D-T2.1.LOGFMT — Access-log format

**Decision (recommendation):** JSONL (one event per line, newline-delimited JSON), located at `<workspace>/workspace/.loam/memory/.access-log.jsonl` (D.2-shape; sibling to the episodes directory). Each event:

```json
{"file": "<relative-path-from-memory-dir>", "ts": "<ISO-8601-UTC>", "op": "<read|write|cite>"}
```

**Rationale:** the sidecar markdown corpus is already file-based and stdlib-stored; JSONL keeps the storage model uniform with the substrate. Append-only writes are atomic on POSIX (single `write()` syscall for sub-page entries); reads are stdlib parse-line-by-line. Mirrors the access-log shape the v2 research §A.1 candidate-implementation 1 named directly.

**Alternative:** sqlite-backed log (rejected — adds an indexed mutable store where append-only would do; sqlite is already used for the FTS5 index but extending it for the access log conflates two failure modes).

### D-T2.1.SCORE — Composition with BM25 and the existing recency blend

**Decision (recommendation):** **multiplicative**: final = BM25 × activation. The existing `_blend_recency` channel (RECENCY_BLEND_WEIGHT=0.5) is **replaced** by the activation column (per §10 doubt #1).

**Rationale:** multiplicative composition is what the ACT-R primary literature uses (Anderson et al. 2004 — activation multiplies the base retrieval probability). The replacement of the existing recency blend is necessary because the activation IS a recency model (with the frequency-multiplier the existing blend lacks); composing both double-counts. The natural side-effect on AC.MSC.1 is noted in §10 doubt #1; the AC.MSC.1 test will need updating to assert the activation-blend equivalent (most likely: keep the assertion shape, swap the underlying expectation to match the new ranker behavior).

**Alternative (a):** additive composition (`final = BM25 + activation`) — rejected; additive composition lets activation dominate on long-tail BM25 scores and is not what the ACT-R literature uses.

**Alternative (b):** keep both the existing recency blend AND add activation as a third multiplier — rejected per §10 doubt #1 (double-counts recency).

### D-T2.1.FLOOR — Zero-duration floor on `(now − t_j)`

**Decision (recommendation):** floor `t_j = now − epsilon` with `epsilon = 1.0 second` when `t_j >= now`. The activation contribution for an access "just now" is `epsilon^(−0.5) = 1.0` (the maximum single-access contribution).

**Rationale:** the formula `(now − t_j)^(−d)` is undefined at `t_j == now`. A second-scale epsilon is the natural floor at the time-scale the access log emits (the worker writes the `ts` field at second-precision ISO-8601). The chosen epsilon is consistent with one second being the smallest distinguishable interval the access log records.

**Alternative:** sub-second epsilon (millisecond) — rejected as it pretends to a precision the log doesn't carry.

### D-T2.2.GRAPH — Co-citation graph data structure

**Decision (recommendation):** in-memory dict-of-dicts (`graph: dict[file, dict[neighbor_file, edge_weight]]`), rebuilt at session-start from the access log. The graph is NOT persisted on disk.

**Rationale:** the access log is the source of truth (Tier-0 verified data); the graph is derived. Rebuild is cheap (O(N×K) where N=events, K=window-of-co-occurrence) for the access-log sizes loam will see in v0.1 (hundreds-to-low-thousands of events per session-start). Avoids the invalidation complexity of a persisted graph (stale graph reads → ranker bug; the cure is "rebuild always" which dominates).

**Alternative:** persisted graph file (e.g. `.cocitation-graph.json`), updated incrementally on each access-log append — rejected at v0.1; adds invalidation complexity. Promoted to candidate if §8 halt trigger #9 fires (rebuild exceeds 5s session-start envelope).

### D-T2.2.EDGEWEIGHT — Edge weight formula

**Decision (recommendation):** Anderson HAM / ACT-R formula `S_ji = log(P(file_i | file_j) / P(file_i))` computed from co-occurrence counts. Epsilon floor on never-co-occurring pairs: `S_ji = log(epsilon)` for pairs with zero co-occurrence (avoids `log(0) = −inf`).

**Rationale:** this is the formula Anderson 1983 / Anderson et al. 2004 use; the cognitive-science anchoring is the verification (rather than empirical loam-corpus fitting). The epsilon floor is a standard regularization in associative-graph implementations.

**Alternative:** pointwise mutual information (PMI), Jaccard, raw co-occurrence count — all rejected; the ACT-R formula is what the primary literature names.

### D-T2.2.SEED — Retroactive seed scope

**Decision (recommendation):** mine TWO data sources in the one-shot pass:

1. **Existing memory-write log entries** at `<workspace>/workspace/.pos/memory-writes.log` (the canonical loam log; per the workspace-state convention). These don't carry per-file access events directly, but they do carry per-turn write events that bootstrap the graph's vertex set.
2. **Agent-transcript JSONL files** at `~/.claude/projects/<slug>/<session>.jsonl` (the Claude Code transcripts; the actual source data for co-occurrence). The seed pass parses each transcript, identifies tool-use events that read memory files, and emits synthetic `read` events into the access log with the transcript's turn-timestamp.

The output of the seed pass is a populated access log (not a populated graph); the graph builds from the access log on next session-start.

**Rationale:** per Q3 owner ratification TG 11809 ("both forward + retroactive seed"). Forward-only (rejected by Q3) would leave weeks of warm-up; the seed pass gives day-one coverage. The transcript files are the actual source data for historical co-occurrence (the access-log instrumentation didn't exist pre-amendment).

**Alternative:** forward-only — explicitly rejected by Q3 owner ratification.

### D-T2.2.SPREAD — Spreading hop count

**Decision (recommendation):** **strictly one hop** at v0.1.

**Rationale:** the cognitive-science evidence specifically supports one-hop dominance — Anderson et al. 2004's spreading-activation calculations are over a single hop. Multi-hop is exponentially more expensive (O(|C| × avg_degree²) for two hops; |C| × avg_degree^N for N hops) and the marginal recall gain is not literature-supported. v2 research §B.1 candidate-implementation 1 specifically names "capped at one hop to keep cost O(|C| × avg_degree)."

**Alternative:** two-hop with decay — rejected at v0.1; multi-hop is a future tuning amendment if observed need lands.

### Commit SHAs

To be backfilled at seal time (manual fallback per §10 doubt #5).

---

## §15. Backwards-compat verification

Tests that must still pass after this amendment seals:

- All existing tests under `framework/primary-persona/tests/` — memory-write worker + retrieval contributor + file-memory store. Specifically:
  - **AC.MFBM.*** family — file-based memory baseline.
  - **AC.MSC.*** family — recency-blend behavior. AC.MSC.1 will likely need its assertion updated to reflect the activation-column replacement (per D-T2.1.SCORE + §10 doubt #1); this is in-scope as a test-update commit.
  - **AC.FBMT1.SUPM.*** family — the supersession-marker penalty must survive the activation-column composition. Specifically AC.FBMT1.SUPM.2's "demotes superseded files" assertion must remain green; the activation column is a separate multiplicand, so the SUPM penalty applies on top.
  - **AC.FBMT1.ENCC.*** family — encoding-context schema; this amendment does NOT consume the `context:` fields but must not break their parse path.
  - **AC.J.*** family — memory-write queue / worker integrity.

---

## §16. Halt-and-surface findings

### Finding #1 (no halt — fence is single-component despite the multi-component framing)

**Surface:** the dispatching brief framed Tier 2 as a "multi-component plan-doc" for consistency with Tier 1 (which spanned `framework/primary-persona/` + `plugins/dev-sdlc/tools/loam-amend/`). Per pre-flight verification, every Tier 2 source edit lands in `framework/primary-persona/`. There is no dev-sdlc change.

**Resolution (autonomous, plan-author):** the manifest declares only the primary-persona component. The plan-doc's §5 names the fence as single-component, with an explicit note that "multi-component" in the brief framing translates to "single-component in practice" here. Per `feedback_test_against_operational_objective_before_escalating`, the operational objective (ship T2.1 + T2.2 retrieval-mechanics primitives) implies a clear answer (one component fence) so this is autonomous correction not owner-escalation.

### Finding #2 (no halt — D-T2.1.SCORE replaces the existing recency blend)

**Surface:** Tier 1 substrate has `_blend_recency` with `RECENCY_BLEND_WEIGHT=0.5` (file_memory.py L246) — a different recency model than the power-law activation column. Composing both double-counts recency.

**Resolution (autonomous, plan-author):** D-T2.1.SCORE recommends replacing the existing recency channel with the activation column. The natural side-effect on AC.MSC.1's test is named in §15 + §10 doubt #1; the builder updates the AC.MSC.1 test assertion to match the new ranker behavior in this amendment's test-update commit.

**Why this is not a halt-and-surface back to dispatcher:** the operational objective (ship the power-law activation per v2 research §A.1) requires the swap; the v2 research explicitly anchors A.1 in Anderson & Schooler 1991's power-law form, which IS the recency model. Per the operational-objective test, the answer is clear.

### Finding #3 (no halt — D-T2.2.SEED's data sources are inferred from the canonical workspace state)

**Surface:** the dispatching brief named "existing memory-write log + agent transcripts" as the seed data sources. The brief did not specify exact paths; per pre-flight, `<workspace>/workspace/.pos/memory-writes.log` exists at the workspace root (per the workspace-state convention) and `~/.claude/projects/<slug>/<session>.jsonl` is the Claude Code transcript path.

**Resolution (autonomous, plan-author):** D-T2.2.SEED names both paths explicitly. The builder may need to handle path variations (workspace slug derivation, multiple projects, etc.) at build time; this is build-strategy detail.

### Finding #4 (no halt — T2.3 working-set is owner-deferred and explicitly out of scope)

**Surface:** the v2 research's Tier 2 section includes T2.3 (pinned working set) as the third Tier 2 item. Per Q4 owner ratification TG 11810, T2.3 is deferred to a separate design conversation.

**Resolution (autonomous, plan-author):** §3 explicitly names T2.3 as out-of-scope per Q4 ratification. The amendment ships T2.1 + T2.2 only. The Tier 2 numbering in this plan-doc (T2.1 = PLBLA = power-law activation; T2.2 = COCG = co-citation graph) intentionally does NOT pre-allocate a T2.3 slot in the §4 ACs — T2.3 is a separate amendment if/when it's ratified.

---

## §17. Composition (M5 derivation line)

- **Composes with** Tier 1 amendment-134 (sealed at `612500304c5ad6d17ec8440d9fd551ba723b981d`) — Tier 2's retrieval surface reads Tier 1's frontmatter at score time (`SUPERSEDED_PENALTY` from `file_memory.py` L258; `ENCODING_CONTEXT_FIELDS` from L969–974). The supersession penalty composes multiplicatively with the activation column.
- **Anchors in** Anderson & Schooler 1991 (power-law activation `B_i = ln(Σ_j t_j^(−d))`, `d ≈ 0.5`), Anderson 1983 (HAM spreading activation), Anderson et al. 2004 (ACT-R integrated theory), Tulving & Thomson 1973 (encoding specificity — motivates the co-citation graph's associative-edge approach to F-PHRASING).
- **Composes with** `feedback_record_owner_ratification_before_dispatch` — §1 owner-ratification table makes the five msg-IDs Tier-0-verifiable durable artifact.
- **Composes with** `feedback_scope_descriptive_ac_ids` — AC.FBMT2.* are scope-descriptive; no version-packing.
- **Composes with** `feedback_version_numbers_at_release_time` — no version number pre-allocated; version derives when this amendment publishes.
- **Composes with** `feedback_verify_fidraft_against_canonical_before_dispatch` — §1 pre-flight verifies no prior implementation exists.
- **Composes with** the dogfood-then-autonomous-publish process ratified TG 11817 — §6 step 12 wires the dogfood pass.
- **Composes with** `feedback_test_outcome_altitude_required` — AC.FBMT2.S is the outcome-altitude smoke; risk band HIGH because today's V025-C1 lesson showed how easily a stub patches the wrong path.
- **Independent of** F4 (scope-confidence) — discipline-scope work, not prompt-scope work.
- **Supersedes** nothing in the prior corpus; this is a forward-build of new retrieval mechanics. Tier 1 substrate stands unchanged.
