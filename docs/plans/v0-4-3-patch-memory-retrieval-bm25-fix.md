# v0.4.3 patch — FBE.7 retrieval BM25-bypass + grep-length-bias fix + cosmetic log fix

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code` (hard rule). Owner ratifies before any cycle dispatches.
**Slug:** `v0-4-3-patch-memory-retrieval-bm25-fix`
**Date authored:** 2026-05-09.
**Class:** END-USER (per `docs/release-versioning-policy.md` §40 — operational defect on user-facing memory-retrieval surface; closure stays within v0.4.2's shipped outcome shape, no new capability).
**Predecessor:** v0.4.2 SHIPPED LOCAL (seal `3f3df670`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Owner authorization:** Telegram 10487 ("Yeah dispatch 0.4.3"), thread 10473 → 10474 → 10476 → 10478 → 10479 → 10480 → 10482 → 10483 → 10485 → 10487. Owner intends to clear session after this plan-doc lands so v0.4.3 build picks up across the session boundary with the plan-doc + curated session-summary memories as durable handoff.

---

## §1 — Outcome shape (the "why")

The file-based memory store (`framework/primary-persona/src/loam/primary_persona/file_memory.py`) collects episodes correctly — 438 episodes on disk for `pos3` group; FTS5 index current; group-id filter scoped — but **retrieval is broken**. Every UserPromptSubmit prompt is wrapped as a single FTS5 phrase at line 504 (`safe_query = '"' + query.replace('"', "") + '"'`). Natural-language prompts never appear verbatim → 0 FTS5 hits → fall-through to `_grep_search` (line 540) which scores `sum(content_lower.count(t) for t in terms)` with no length normalization → giant compaction-summary episodes (one is 123 KB; another 17 KB; typical episode is 1–4 KB) win every common-stop-word query. Empirically: 5 of 6 representative probes returned irrelevant compaction-summaries despite the right content being present (BallotPath in 37 episodes; Eric in 71; F-DESIGN-1 in 4; subscription-only in 9). See `/Users/lukeivers/pos3/workspace/.scratch/claude-output/memory-retrieval-quality-investigation.md` for the empirical characterization.

v0.4.3 is a PATCH per `docs/release-versioning-policy.md` §32 — defect closure on v0.4.2's outcome shape (file-based memory retrieval is part of the persona surface that ships with v0.4.2). It does NOT extend v0.4.2's outcome shape; it makes the existing surface return relevant episodes for natural-language queries.

A side-issue cosmetic defect rides along: `memory_write_worker.py:284` logs `episode_uuid: null` because the file-based store returns `{path, name, group_id}` — no UUID — and the worker hard-codes the graphiti-era `episode_uuid` field. Bundled with the algorithm fix because it touches the same component (memory-system surface) and was a real diagnostic-time cost in the investigation cycle.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to build software) → durable cross-session memory is one of the persona's translation-burden reducers → file-based memory retrieval surfaces the right episodes at session-start so the persona doesn't need to re-elicit context the user already provided → v0.4.3 ACs `AC.V043.*` below (token-sanitized FTS5 + length-normalized grep + outcome-altitude probe + HARD smoke + cosmetic log fix).

## §3 — Component fence

**PRIMARY:** `framework/primary-persona/` — same component sealed in amendment chain that introduced the file-based store. Edits land in:

- `framework/primary-persona/src/loam/primary_persona/file_memory.py` — `_fts_search` token-sanitization + OR-of-tokens (AC.V043.1); `_grep_search` length-normalization (AC.V043.2).
- `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py:284` — log-line correction (AC.V043.3).
- `framework/primary-persona/tests/test_AC_V043_*.py` — new tests covering token-sanitization + length-normalization + log-shape + outcome-altitude retrieval probe.

**Read-only:**
- `framework/primary-persona/src/loam/primary_persona/memory_consumer.py` — `_render_retrieval` (rendering layer; not defective; unchanged).
- `framework/primary-persona/src/loam/primary_persona/session_start_emitter.py` — runtime registration (unchanged).
- All other framework components — sealed.
- File-based store schema (`SEARCH_INDEX_NAME`, `episodes` FTS5 table) — extended via query-construction only; NO schema change, NO re-index.

**Universal admissions:** this plan-doc + manifest, seal narrative file, `docs/release-roadmap.md` §6 entry (v0.4.2 → v0.4.3 follow-on row), `docs/STATE.md` (v0.4.3 SHIPPED rollup row), and the FUTURE_IDEAS_DRAFT capture for the deferred ideas (stopword list, task-notification stripping, recency boost, FastMCP service.py rip-out).

**Out of fence:** `plugins/`, any other framework component, any seal directory. Edits outside fence = halt.

## §4 — AC family `AC.V043.*` (TIGHT)

Each AC maps to ≥1 test under `framework/primary-persona/tests/test_AC_V043_*.py` OR an empirical artefact (the outcome-altitude retrieval probe + the HARD smoke writeup). The agent authors test names within the convention.

### AC.V043.1 — `_fts_search` uses token-level sanitization + OR-of-tokens

`_fts_search` at `file_memory.py:489–538` MUST replace the line-504 phrase-wrap with token-level sanitization. Construction:

- Split the prompt on whitespace.
- Strip FTS5-meaningful punctuation per token (e.g., reduce to `[A-Za-z0-9_]` content; lowercase).
- Drop tokens shorter than 2 chars.
- Drop a small in-tree stopword set (builder authors the set within reason — see §14 D-V043.1; minimal English-question stopwords like `what, how, the, was, did, does, is, are`; ASCII-lowercase set; not the full NLTK list).
- If zero survivors, return empty list (matches existing empty-state contract — AC.MFBM.2).
- Join survivors with `" OR "` so FTS5 BM25 ranks by relevance across any-token-matches.

Existing `bm25(episodes)` ORDER BY clause stays unchanged. Length normalization comes for free from BM25's `b` parameter.

**Test:** `test_AC_V043_1_fts_token_sanitization.py` — invokes `_fts_search` with a natural-language prompt against an in-memory FTS5 fixture containing 3 short focused episodes + 1 long compaction-shaped episode. Asserts: (a) the focused episode containing the rarest query term ranks #1; (b) the long compaction episode does NOT rank #1 for a query whose only common terms are stop-words; (c) zero-survivor query (e.g., `"is"` only) returns `[]`; (d) FTS5-meaningful punctuation in the prompt (`.`, `-`, `?`) does not raise `OperationalError`.

`outcome-altitude: false` (query-construction unit-altitude verification).

### AC.V043.2 — `_grep_search` applies length normalization

`_grep_search` at `file_memory.py:540–612` MUST replace the line-594 raw `score = sum(content_lower.count(t) for t in terms)` ranker with a length-normalized form. Builder picks ONE path (documented in §14 D-V043.2):

- (a) **Square-root length normalization** — `score = sum(content_lower.count(t) for t in terms) / math.sqrt(max(len(content), 1))`. Cheap, deterministic, no extra deps.
- (b) **BM25-style length factor** — closer to FTS5's BM25 (`score / (k1 * ((1 - b) + b * (doclen / avgdoclen)))`). More principled but requires per-corpus avg-length precomputation.

Path (a) is the default; (b) acceptable if builder argues the corpus shape needs it. Empty-string content stays length-zero (skip; matches existing `score == 0` skip on line 595–596). Builder rules.

**Test:** `test_AC_V043_2_grep_length_normalization.py` — invokes `_grep_search` with a known-shape query against a fixture directory containing: (i) one 100 KB compaction-shaped episode that mentions every query term ≥10 times; (ii) one 2 KB focused episode that mentions the rarest query term 2 times + matches no other terms. Asserts the focused episode ranks above the compaction episode despite lower raw count.

`outcome-altitude: false` (ranker unit-altitude verification).

### AC.V043.3 — `memory_write_worker.py:284` log line is honest

The diag emission at `memory_write_worker.py:277–287` MUST replace `"episode_uuid": result.get("episode_uuid") if isinstance(result, dict) else None` with `"path": result.get("path") if isinstance(result, dict) else None`. The `episode_uuid` key is dropped entirely (the file-based store does not produce one; surfacing what the substrate actually emits beats hard-coding a never-populated field).

**Test:** `test_AC_V043_3_worker_log_shape.py` — invokes the worker's success path against a stub store that returns `{"path": "/tmp/x", "name": "n", "group_id": "g"}`. Reads back `memory-writes.log`. Asserts: (a) the `worker-ok` line has `"path": "/tmp/x"` (substring or JSON parse, builder rules); (b) the line has NO `"episode_uuid"` key.

`outcome-altitude: false` (logging shape; diagnostic-altitude).

### AC.V043.4 — No regression on test suite

All previously-passing tests still pass. Specifically:

- `pytest framework/primary-persona/tests/` returns 0 with the v0.4.2-sealed test count plus the new `AC_V043_*` tests (verify pre-existing tests untouched via `git diff --stat`; if existing fixtures were testing the phrase-wrap behavior empirically — i.e., they expected zero results for natural-language prompts — those fixtures get UPDATED to test the new contract, and the update is explicit per `feedback_loose_AC_text_fix_AC_not_implementation`).
- `loam amend apply --dry-run` GREEN against the v0.4.3 manifest pre-apply AND post-seal.
- v0.4.0 / v0.4.1 / v0.4.2 outcome-altitude AC outputs (jsts-playwright-app, ProgramBench, HARD smoke ride-along) NOT re-run inline — sealed state is the baseline.

`outcome-altitude: false` (no-regression invariant; covered by suite).

### AC.V043.5 (outcome-altitude) — Live-store retrieval probes return relevant episodes

Re-run the 6 probe queries from the investigation report against the live `~/lukeivers/pos3/workspace/.loam/memory/` store (the same store that produced the empirical 1/6 baseline) under v0.4.3 HEAD. Probe set:

1. "What was v0.4.2?"
2. "How does the BallotPath schema work?"
3. "What did Eric report broken?"
4. "Stage 7.7 verification corrections"
5. "F-DESIGN-1 closure"
6. "How does loam handle subscription-only?"

Plus 4 additional probes targeting the curated session-summary memories now in the corpus (per the open-question recommendation):

7. "What is the current BallotPath project status?"
8. "What did v0.4.0 ship?"
9. "What memory-rules were captured this session?"
10. "What v0.4.1 and v0.4.2 closures landed?"

**Verdict shape:** GREEN if ≥7/10 surface a relevant episode in top-3 (vs investigation's 1/6 ≈ 17%; target ≥70%). YELLOW if 6/10 (partial recovery; surface for owner ruling). RED if ≤5/10 (fix didn't move the needle — surface as F-DESIGN-x candidate).

Builder authors a deterministic rerun harness (e.g., `framework/primary-persona/tests/test_AC_V043_5_live_store_probes.py` with `pytest.mark.requires_live_store` so it's skip-by-default in CI but runnable locally). Output writeup at `<workspace>/.scratch/claude-output/v0-4-3-retrieval-probe.md` with per-probe verdict + top-3 paths + relevance judgment.

`outcome-altitude: true` per the rubric — real on-disk store, real natural-language queries, real top-N results. Not a stubbed FTS5 fixture; not a synthetic corpus.

### AC.V043.6 (outcome-altitude) — HARD smoke against rd-automation

Per `feedback_hard_smoke_per_minor_before_publish.md`: every minor's release sequence has a HARD smoke gate against rd-automation. v0.4.3 is a patch but the rule applies because public-action gating happens at the v0.4.3 publish line (paired with v0.4.2 if owner chooses joint publish). Cold install of v0.4.3 HEAD into a fresh venv; real `claude -p` subprocess; real rd-automation tree at `/Users/lukeivers/pos3/workspace/rd-automation`; end-to-end extract + verify objectives.yaml + key fields; regression ride-along on F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN closures from v0.2.5.1.

**Verdict:** GREEN before publish. RED triggers corrective NEW commit + re-smoke.

**Output:** writeup at `<workspace>/.scratch/claude-output/v0-4-3-hard-smoke.md` per the v0.3.0 / v0.4.0 / v0.4.1 / v0.4.2 precedent.

`outcome-altitude: true` per the rubric — cold install + real `claude -p` + real fixture, no monkeypatch.

### AC.V043.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/primary-persona/src/loam/primary_persona/file_memory.py`.
- `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py`.
- `framework/primary-persona/tests/test_AC_V043_*.py` (new files).
- `framework/primary-persona/tests/test_*` (existing test fixtures, only if AC.V043.4 surfaces ones that need explicit contract update).
- `docs/plans/v0-4-3-patch-memory-retrieval-bm25-fix.{md,manifest.yaml}` (this plan + manifest + seal narrative).
- `docs/release-roadmap.md` (§6 v0.4.3 row appended; §2 SHIPPED row on completion).
- `docs/STATE.md` (v0.4.3 SHIPPED rollup row).
- FUTURE_IDEAS_DRAFT.md (deferred items capture).

Anything outside that set is a halt condition.

## §5 — Hard constraints

1. **No `--amend`.** Corrective commits are NEW commits. Streak intact (every cycle since v0.3.0 C5 stayed clean).
2. **Scope fence per §3.** Edits outside fence = halt.
3. **No Anthropic API key, no `pip install anthropic`.** All LLM calls route through `claude -p` subprocess via the existing `claude_print_synthesis_client.py` shape. v0.4.3 doesn't add LLM calls; constraint preserved by inspection.
4. **`--strict-mcp-config` invariant.** Any production-path `claude -p` invocation in the HARD smoke passes `--strict-mcp-config` + empty MCP config tempfile per the v0.2.5 C5 propagation invariant.
5. **No new runtime deps.** stdlib only — `re`, `sqlite3`, `math` (already imported). No new packages on the import surface.
6. **Backward-compat on FTS5 index.** No `DROP TABLE`, no `INSERT INTO ... SELECT`, no schema migration. Existing index stays usable; new query construction reads it.
7. **`loam amend apply --dry-run` green** is a hard prereq + hard post-apply gate.
8. **No public action.** No `git push`, no `git tag`, no GitHub Release. v0.4.3 HALTS at seal; owner gates the publish (v0.4.2 + v0.4.3 ship together OR separately at owner's call).
9. **Plan-before-code.** This plan-doc lands BEFORE source edits.
10. **ODD §2.5 + §2.4.** Every line of code maps to a named AC. No method-in-AC. No "options to rule on" framing.
11. **Outcome-altitude AC requirement** per `feedback_test_outcome_altitude_required.md`. AC.V043.{5,6} are the outcome-altitude probes (real corpus + real `claude -p`).

## §6 — Out of scope (explicit)

- **Stopword list expansion** beyond the minimal in-tree set — deferred to FUTURE_IDEAS_DRAFT (full-NLTK or curated stoplist is a bigger design call; AC.V043.1's minimal set is sufficient for the outcome).
- **Task-notification block stripping on write** — deferred to FUTURE_IDEAS_DRAFT (would reduce signal-poison on the write side; orthogonal to retrieval; v0.5.0+ candidate).
- **Recency boost in BM25 ranking** (multiply score by `1 + α/age_days`) — deferred to FUTURE_IDEAS_DRAFT (a separate ranking improvement; verify v0.4.3 baseline first).
- **FastMCP `service.py` rip-out** — deferred to v0.5.0+ refactor; not in retrieval path; can stay until then.
- **Schema migration / re-index** — out by §5.6.
- **BYOK / multi-provider** — subscription-only architectural floor preserved.
- **Multi-fixture HARD smoke beyond rd-automation** — v0.5.0+ territory.

All four "deferred to FUTURE_IDEAS_DRAFT" items get captured per `feedback_durable_capture_for_planned_work` — append to `docs/FUTURE_IDEAS_DRAFT.md` (or local equivalent) as part of the v0.4.3 seal commit chain.

## §7 — Halt triggers

1. Cross-component scope expansion beyond `framework/primary-persona/`. Halt + surface.
2. AC.V043.* count grows beyond 6 (excluding `.S`). ODD §2.5 violation triage; halt.
3. AC.V043.5 live-store probe ≤5/10. Halt; surface as F-DESIGN-x candidate (entanglement: deeper retrieval-quality issue beyond the BM25-bypass).
4. AC.V043.6 HARD smoke RED. Halt; corrective NEW commit + re-smoke.
5. Any reach for `--amend`, `git push`, or `git tag`. Immediate halt.
6. Subscription-only constraint violated (any new `import anthropic`, any new `ANTHROPIC_API_KEY` env reference). Immediate halt.
7. AI-time exceeds upper band (150 min) by >50% → 225 min wall-clock. Halt with current state.
8. ODD §2.5 violation discovered in surrounding code. Halt + surface (e.g., `_grep_search` is shared with a code path the diagnosis didn't anticipate — surface before silently extending).
9. WD mismatch — `pwd` returns anything other than `/Users/lukeivers/ivers-corp-pos-v2`. Immediate halt.
10. The 6 investigation probes don't reproduce on fresh testing (corpus shifted; baseline invalid). Halt + re-investigate before fixing.
11. `_grep_search` is invoked from a non-retrieval code path the investigation missed. Halt + surface entanglement before changing the ranker.
12. Schema change appears necessary to satisfy any AC. Halt — backward-compat constraint per §5.6.

## §8 — Dependencies

- v0.4.2 SHIPPED LOCAL state (seal `3f3df670`) — predecessor; consumed read-only.
- File-based memory store sealed surface (FTS5 schema, episode write contract, `_split_frontmatter`) — consumed read-only.
- `framework/memory-system/src/claude_print_client.py` (subscription-only LLM wrapper) — consumed read-only by the HARD smoke; v0.4.3 doesn't modify it.
- v0.2.5 C5 `claude -p --strict-mcp-config` invariant — consumed read-only by the HARD smoke.
- Live `pos3` memory store at `/Users/lukeivers/pos3/workspace/.loam/memory/` — consumed read-only by AC.V043.5; if shifted between investigation time and build time, AC.V043.5 verdict shape stays valid because the curated session-summary memories (probes 7–10) provide a stable known-good baseline.

## §9 — F2 RF gaps to surface during build

- **Stopword set choice.** Builder picks the minimal in-tree set; if the choice excludes a high-frequency English term that's actually high-signal in the loam corpus (e.g., `loam` itself appears in many episodes — should NOT be a stopword), surface for owner ruling rather than silently filtering. RF on the chosen set composition.
- **Length-normalization path (a) vs (b).** Path (a) sqrt is the default; if the empirical AC.V043.5 probes show path (a) is insufficient (e.g., 6/10 instead of 7/10) AND path (b) BM25-style would close the gap, surface and switch — don't ship a known-suboptimal ranker just because path (a) was the §14 default.
- **Existing test fixture updates.** If any pre-existing test in `framework/primary-persona/tests/` was empirically testing the phrase-wrap behavior (e.g., asserting that `_fts_search` returns empty for a natural-language query), surface the fixture + the contract change explicitly. Per `feedback_loose_AC_text_fix_AC_not_implementation`: tighten the AC text in the fixture, don't retrofit the implementation.
- **Cosmetic log fix bundling.** AC.V043.3 is a 3-line change. Bundling with the algorithm fix risks a single-commit-multi-AC diff. Builder option: separate commits within the same cycle (one for AC.V043.{1,2}, one for AC.V043.3), or single commit. RF on the bundling choice — preference is bundle (same component, same release, joint test-pass), but builder rules.
- **AC.V043.5 verdict-band tuning.** ≥7/10 GREEN is the §4 spec; if builder argues the curated session-summary memories should be excluded from the count (because they're known-good plants and inflate the base rate), surface and re-tune. Stays at ≥7/10 unless builder makes the case.
- **`_grep_search` invocation surface.** Investigation report claims `_grep_search` is the FTS5-fallback only. If any non-retrieval caller invokes it (e.g., a CLI verb, a debug surface), changing the ranker mid-stream affects them too. RF before edit: grep the codebase for `_grep_search` callers, surface the set.

## §10 — F4 self-check (scope-confidence)

The defect was empirically characterized in the investigation report (438 episodes baselined; 6 probes per-verdict; root cause cited at line 504 with the exact code snippet). High author confidence in the outcome shape → tight scope (objective + constraints + AC.V043.{1,2,3,4,5,6} pin the outcome; method stays builder's call within fence). AC.V043.5 is the confidence-bearing outcome probe (real corpus + 10 probes + ≥7/10 verdict band) — TIGHT scope at AC level (run real probes against real store and report verdict); LOOSE on what the empirical numbers will show.

Per Lens 4 (compose-with-F4): tight scope leaves method *inferable from constraints*. The constraints in §5 + halt-triggers in §7 + AC text in §4 are sufficient for the builder to infer: token-sanitization is a regex-based query-construction extension; length-normalization is a single-line ranker swap with a documented divisor; log-line fix is a key rename. Method NOT named in AC text; the §14 method-decisions register documents the chosen path post-build per the SHA-register convention.

## §11 — Dispatch shape

Single PATCH cycle, build inline in the next session (the one Luke clears to after this plan-doc lands) per the `feedback_serialize_amendment_builds` constraint (working-tree-level serialization for builds touching the same component). Build order:

1. **Plan-doc lands** (this file, current dispatch) + manifest stub.
2. **Cycle dispatch** (next session) — single agent, scope-only brief naming the plan-doc + ACs + halt triggers + WD literal cd.
   - Source edit + new tests (AC.V043.{1,2,3}).
   - No-regression check (AC.V043.4).
   - AC.V043.5 live-store probe + writeup.
   - AC.V043.6 HARD smoke + writeup.
   - `loam amend apply` + `loam amend seal` (single seal commit).
3. **HARD HALT** — no push, no tag, no Release.

Decomposition decision: ONE cycle, not two. The `_fts_search` fix and `_grep_search` fix touch the same file (`file_memory.py`) and are tested together (length-normalization is the belt-and-suspenders for any FTS5 fall-through case). Splitting them adds coordination overhead (two seal commits, two manifest entries) without tightening any subtask's AC. Per Lens 5 stopping criterion: stop when the proposed split adds only coordination overhead.

## §12 — Provenance trail

- Investigation report at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/memory-retrieval-quality-investigation.md` — empirical defect characterization (438 episodes baselined; 6 probes; root-cause citation at line 504 + line 540).
- Telegram thread 10473 → 10474 → 10476 → 10478 → 10479 → 10480 → 10482 → 10483 → 10485 → 10487 — owner directive arc from "memory retrieval feels off" → "investigate retrieval quality" → "yeah dispatch 0.4.3."
- Curated session-summary memories at `/Users/lukeivers/pos3/workspace/.loam/memory/episodes/pos3/2026-05-09/session-summary-*.md` — 8 known-good episodes plant-tested in AC.V043.5 (probes 7–10).
- `feedback_hard_smoke_per_minor_before_publish.md` — HARD smoke procedural rule.
- `feedback_test_outcome_altitude_required.md` — outcome-altitude AC requirement; per-AC marking.
- `feedback_no_anthropic_api_key.md` — subscription-only architectural floor.
- `feedback_durable_capture_for_planned_work.md` — FUTURE_IDEAS_DRAFT capture for §6 deferred items.
- `feedback_loose_AC_text_fix_AC_not_implementation.md` — fixture-update guidance under AC.V043.4.
- v0.4.2 SHIPPED LOCAL at seal `3f3df670` per `docs/release-roadmap.md`.
- File-based memory surface at `framework/primary-persona/src/loam/primary_persona/file_memory.py` (extended).

## §13 — AI-time band

Per duration-estimation rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`):

- Plan-doc + manifest: 5–10 min (current dispatch).
- Source edits (AC.V043.{1,2,3}): 25–40 min (3 focused edits in 2 files).
- New tests (4 test files; one per AC + the live-store probe): 20–35 min.
- No-regression check (AC.V043.4): 5–10 min.
- AC.V043.5 live-store probe + writeup: 15–25 min.
- AC.V043.6 HARD smoke + writeup: 30–45 min (mirrors v0.4.2's ~230s Stage 1 + writeup).
- Apply + seal + report: 10–15 min.

**Aggregate range: 110–180 min ≈ 1.8–3.0 hr AI-time.** Midpoint ~2.5 hr. Within halt-trigger 7 upper bound (150 min × 1.5 = 225 min); the 180 min upper edge is within tolerance because the HARD smoke is the dominant variance and v0.4.2 actuals (230s + writeup ≈ 30 min) sit at the band's middle.

## §14 — Method decisions

Backfilled at build time per the v0.4.2 / v0.4.1 / v0.4.0 precedent.

- **D-V043.1** (stopword set composition): _builder rules at build time_. Authoring guidance: minimal set ≤20 entries; ASCII-lowercase English-question stopwords (`what, how, the, was, did, does, is, are, a, an, of, to, in, on, for, this, that, it, be, at`); excludes high-signal loam-corpus terms (`loam`, `pos`, `claude`, `eric`, version strings). Surface set composition in the build report.
- **D-V043.2** (length-normalization path): _builder rules at build time_. Authoring guidance: path (a) sqrt is the default; switch to path (b) BM25-style only if AC.V043.5 verdict falls short on path (a) OR builder argues corpus shape requires it. Document the chosen path + the empirical justification (probe verdict before/after) in the build report.
- **D-V043.3** (cosmetic log bundling): _builder rules at build time_. Default: bundle in same source-edit commit as AC.V043.{1,2}; alternative: separate commit `fix(memory-write-worker): episode_uuid → path log shape` if builder prefers cleaner audit trail.
- **D-V043.4** (existing-fixture handling under AC.V043.4): if any pre-existing test in `framework/primary-persona/tests/` empirically depended on the phrase-wrap behavior, the builder updates the fixture under the AC.V043.4 no-regression umbrella, names the fixture + the change in the build report, and keeps the contract update visible in the diff.
- **D-V043.5** (AC.V043.5 probe harness shape): builder authors the harness as a pytest module marked `requires_live_store` (skip-by-default in CI; runnable locally). Output writeup at `<workspace>/.scratch/claude-output/v0-4-3-retrieval-probe.md` with per-probe verdict table + top-3 paths + relevance judgment + verdict band.

### Commit SHAs

| Order | Type | SHA | Description |
|---|---|---|---|
| 1 | plan-doc | _pending_ | docs(plans): v0.4.3 patch — FBE.7 retrieval BM25-bypass + grep-length-bias plan-doc + manifest |
| 2 | source-edit | _pending_ | fix(file-memory): token-sanitized FTS5 + length-normalized grep (AC.V043.{1,2}) |
| 3 | source-edit | _pending_ | fix(memory-write-worker): episode_uuid → path log shape (AC.V043.3) — _OR_ bundled into commit 2 per D-V043.3 |
| 4 | tests | _pending_ | test(file-memory): AC.V043.* test family (token-sanitization + length-normalization + log-shape + live-store probe) |
| 5 | docs (probe writeup) | _pending_ | docs(experiments): v0.4.3 retrieval probe — verdict ≥7/10 |
| 6 | docs (HARD smoke) | _pending_ | docs(experiments): v0.4.3 HARD smoke against rd-automation — GREEN |
| 7 | docs (SHIP rollup) | _pending_ | docs: v0.4.3 SHIPPED rollup — STATE.md + release-roadmap §2/§3/§6 |
| 8 | docs (FUTURE_IDEAS) | _pending_ | docs(future-ideas): capture v0.4.3 deferred items (stopword expansion / task-notification stripping / recency boost / FastMCP rip-out) |
| 9 | manifest baseline-update | _pending_ | docs(plans): v0.4.3 patch manifest baseline → <SHA> |
| 10 | apply | _pending_ | chore(amend): v0-4-3-patch-memory-retrieval-bm25-fix manifest+apply |
| 11 | seal | _pending_ | chore(seals): v0-4-3-patch-memory-retrieval-bm25-fix — primary-persona at <SHA> |

## §15 — SHA register

Backfilled at seal time into §14 above (per AC.D-sa.7 convention).

---

## Open questions for owner ratification

1. **AC.V043.5 verdict band.** Plan specifies ≥7/10 GREEN (vs investigation 1/6 ≈ 17%; target ≥70%). Recommend GREEN as authored. Alternative bands (≥6/10 / ≥8/10) acceptable if owner prefers stricter or looser; surface for explicit ratification.
2. **Cosmetic log fix (AC.V043.3) commit bundling.** Recommend bundle with AC.V043.{1,2} into one source-edit commit per D-V043.3 default (same component, same release). Alternative: separate commit for cleaner audit trail. Builder ruling at build time per D-V043.3 unless owner pins.
3. **Joint v0.4.2 + v0.4.3 publish vs separate publishes.** v0.4.2 is SHIPPED LOCAL (not yet pushed/tagged). Owner has the option to publish them together (single push + two tags + two Releases) or sequentially (v0.4.2 first, v0.4.3 once retrieval verified working in production). Plan stays neutral; surfaces for explicit ruling at the post-seal HARD HALT.
