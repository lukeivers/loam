# Memory redesign — Standing retrieval telemetry (the baseline-capture layer, pure observation)

**Status:** PLAN + BUILD (this cycle). Plan authored BEFORE code (hard gate). Single-component sealed amendment on `framework/primary-persona` (`new_component: false`).
**Predecessor:** S1a ground-floor extraction, sealed on `origin/main` at `5f23c3c2`.
**Successor (gated on this):** the ranker change (design Stage 3 = the `s2-recency-relocation` plan-doc) — DO NOT build this cycle; it depends on the baseline this layer captures.
**Design source (owner REQUIREMENT):** `workspace/strategy/research/memory-human-vs-harness-2026-07-02/owner-refinements-2026-07-02.md` item #1 — "Store, per turn, {the prompt} vs {which memories got pulled}. Disk is cheap — write lots of telemetry somewhere reviewable... a STANDING layer, not just a one-week experiment... a reviewable dataset to fine-tune the pull-algorithm." + `synthesis-v2.md` §"Where the telemetry layer sits" + Stage 2 (`[pure instrumentation, ship early to baseline]`).

---

## §1 — Objective

Add a STANDING, per-turn retrieval-telemetry layer that records — for each turn where memory recall runs — the query (prompt + work-anchor) against the candidate memories that were discovered (with their discovery scores + event-time), which of those crossed into the injected set, and the effective budget — appended to a reviewable, disk-cheap, gitignored on-disk log. The log is the baseline + growing dataset the coming ranker cycle offline-tunes the relevance threshold + recency re-weight against.

---

## §2 — The load-bearing constraint: PURE OBSERVATION

The telemetry records what the ranker ALREADY did. It MUST NOT change recall behavior, results, or ordering, and MUST NOT add measurable regression to the recall path. Concretely, this cycle guarantees:

- `retrieve()` returns a **byte-identical** block with telemetry configured vs not (AC.RTEL.1).
- The recorder reads **copies of scalar fields** off the already-computed hit dicts; it NEVER mutates a hit dict, NEVER re-runs a search, NEVER adds I/O that the ranker would otherwise not do beyond one guarded append.
- If capturing something cleanly would require altering the recall flow (e.g. widening the candidate fetch to see sub-cut candidates), this cycle **captures less** rather than perturb behavior — the telemetry captures the candidate pool the ranker actually fetched, not a re-derived wider pool (named limitation, §11).
- Every write is **fail-open**: any recorder error is swallowed and the turn proceeds unchanged (AC.RTEL.4).

---

## §3 — Findings pinned at plan-authoring (Tier-0, from the live code at `origin/main` `5f23c3c2`)

1. **The single point where the candidate pool AND the injected subset are both known is the end of `rank()`** (`keep_pace/retrieval.py:479`). At `return decision_hits + merged` (`:554`), four locals are in scope: `corpus_hits`, `episode_hits`, `decision_hits` (the full candidate pool per source), and `merged` (the post-gate/floor/dedup/top-N survivors). The injected subset is `decision_hits + merged`; the discovered-but-not-injected candidates are the pool members absent from it. `retrieve()` (`:557`) sees only `merged` — it cannot distinguish discovered-not-injected, so it is the WRONG capture point.
2. **`rank()`'s return value + signature are a SEALED contract** — the P@5 retrieval-relevance metric reads `rank()`'s ordered merged hits (docstring `:486`, "There is exactly ONE ranking code path: what the metric measures IS what the production turn injects"). Therefore the capture is a **side-effect call before the existing return** — no signature change, no return-value change.
3. **`_merge_by_score` re-binds its `episode_hits` parameter when it filters** (`:859`, `:873`) — it does NOT mutate `rank()`'s `episode_hits` local, so at the end of `rank()` that local is still the full pre-gate candidate pool. Salience-gated / floored / deduped / top-N-cut candidates are visible as pool-minus-injected.
4. **Event-time is already fetched, just not carried onto the hit.** `file_memory.py` episode search results carry `"valid_at"` (= `reference_time`, the EVENT time) + `"_bm25_raw"` (FTS path `:1142/:1159`, grep-fallback `:1268/:1273`). But `_episode_hits` (`retrieval.py:288`) copies only `{pointer, path, score, _episode, _salience}` onto the hit — NOT `valid_at`. Carrying `valid_at` onto the episode hit is a behavior-inert additive read (no downstream ranker reads that key; the byte-identical render is unchanged) and is what makes offline recency-re-weight tuning possible from the log.
5. **The discovery score to capture is the raw `score` slot** — `BM25 × supersession` for episodes (the `_bm25_raw` carried onto `score`), `BM25 × length × supersession` for corpus hits. That raw per-source score is the discovery-relevance signal the coming threshold tunes against; the internal normalized/boosted value is a prioritization artifact discarded inside `_merge_by_score` and is NOT the threshold input.
6. **`.loam/` and `.scratch/` are gitignored** (`.gitignore:68`, `:32`). A telemetry dir under `<workspace_root>/workspace/.loam/` is standing-on-disk yet untracked — exactly the owner's "reviewable, disk is cheap" requirement without polluting the tree.

---

## §4 — Acceptance criteria

Outcome-shape; method inferable from the constraints, never stated. AC family `RTEL` = Retrieval TELemetry (scope-descriptive, not version-packed, per `feedback_scope_descriptive_ac_ids`). One test per criterion. AC.RTEL.7 is the outcome-altitude criterion (production entry-point, no pre-arranged state); AC.RTEL.1 is the pure-observation/no-behavior-change criterion; AC.RTEL.4 is the fail-open criterion.

| AC | Outcome | Verification |
|---|---|---|
| **AC.RTEL.1** — pure observation / no behavior change | `retrieve()` returns a byte-identical injection block whether or not a telemetry sink is configured, on the same fixture (corpus + episodes). Telemetry never alters recall results or ordering. | Same fixture, two configs (telemetry_dir set vs `None`) → identical returned block. `test_AC_RTEL_1_*`. |
| **AC.RTEL.2** — per-turn record shape | A turn that discovers ≥1 candidate appends exactly ONE JSONL record carrying `{turn_id, ts, prompt, work_anchor_tokens, budget{top_n,char_cap}, candidates[]}`; each candidate carries `{source, path, score, injected, rank}`. | Run one retrieval with a telemetry_dir; parse the one appended line; assert the keys + one candidate's shape. `test_AC_RTEL_2_*`. |
| **AC.RTEL.3** — discovered-vs-injected distinction | When the candidate pool exceeds the injected set (a gated/floored/deduped/cut candidate), the log records the dropped candidate with `injected=false` (no rank) AND the surfaced ones with `injected=true` + an integer rank — so the dataset separates discovered-not-injected from injected. | Fixture with more candidates than survive the merge → the record's `candidates[]` contains at least one `injected=false` and the `injected=true` set equals the returned block's records. `test_AC_RTEL_3_*`. |
| **AC.RTEL.4** — fail-open | A telemetry write failure (unwritable sink / serialization error) does not raise and does not change `retrieve()`'s returned block. | Point telemetry_dir at an unwritable location → `retrieve()` returns the correct block, no exception. `test_AC_RTEL_4_*`. |
| **AC.RTEL.5** — tuning-sufficiency | Each candidate record carries the raw discovery `score`; an episode candidate additionally carries its `event_time`. An offline reader can therefore recompute a threshold cut AND a recency re-order from the log alone. | Episode-bearing fixture → the episode candidate record has a numeric `score` and a non-null `event_time`; a corpus candidate has a numeric `score`. `test_AC_RTEL_5_*`. |
| **AC.RTEL.6** — standing / append + daily rotation | Two turns append two records to the SAME day's file (append-only, never overwrite); the file lives at the daily-rotated gitignored telemetry path. | Two retrievals → the day file holds two JSONL lines; the path matches the `retrieval-telemetry-<UTC-date>.jsonl` shape under the workspace `.loam` telemetry dir. `test_AC_RTEL_6_*`. |
| **AC.RTEL.7** (outcome-altitude) — production `retrieve()`, no pre-arranged state | Over the real resolver + `retrieve()` from an empty starting state with a configured telemetry sink, a genuine retrieval writes ONE well-formed record whose `injected=true` candidates match the returned block's records, AND the returned block equals the block produced with telemetry off. | `test_AC_RTEL_7_OA_*` drives `retrieve()` with no pre-set state; cross-checks the record against the live block + the telemetry-off block. |

**No-regression:** the KP1 / FBMU / FBM-FILTER / SRF / SUP / DLG / EVX / MSC / GFE suites stay green unchanged — this cycle is additive (a new module + a guarded side-effect + one behavior-inert hit field + two resolver threadings). No existing fixture encodes anything this cycle changes; any suite that goes red is a real regression → halt (§8).

**Ladder-up:** AC.RTEL.* → the design's telemetry Stage 2 (baseline dataset for offline auto-tune) → the ranker Stage 3 depends on it → AC.PO.1/AC.PO.2 (`docs/VALUE_PROPOSITION.md`): telemetry protects the "tune toward the best relevant context" guarantee by making the pull algorithm measurable before it is changed, and reduces the owner's translation burden of blind-tuning a recall behavior that touches every turn.

---

## §5 — The fence

**Primary (in-fence, edited):**
- `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py` — (a) add `telemetry_dir: Optional[Path]` (+ optional `telemetry_turn_id`) to `RetrievalConfig`; (b) one guarded side-effect call to the recorder at the END of `rank()`, before the existing return, reading `corpus_hits`/`episode_hits`/`decision_hits`/`merged` (no mutation, no signature change); (c) carry `_event_time` from `ep["valid_at"]` onto the episode hit in `_episode_hits` (behavior-inert additive read); (d) thread `telemetry_dir` in the two live resolvers (`_resolve_live_config`, `_resolve_composer_config`) via the new `telemetry_dir_for_workspace` helper.
- `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval_telemetry.py` — NEW module: `telemetry_dir_for_workspace(root)` (mirrors `file_memory.memory_dir_for_workspace`), the daily-rotated file path, the JSONL record builder, and `record_retrieval(...)` — the fail-open append. Keeping it a separate module keeps the hot path a single guarded call.
- `framework/primary-persona/tests/test_AC_RTEL_*` — the AC suite (+ any `_helpers_keep_pace` addition needed for an episode-bearing fixture).

**Explicitly NOT touched:** `file_memory.py` (event-time is already on the search-result dict; the path helper lives in the new module — no file_memory edit); the ranker itself (no threshold/recency change — that is Stage 3, deferred); the S2 `recency-relocation` plan-doc + its manifest (untracked, must NOT be committed by this cycle); `RANK_CONSTITUTIONAL_FLOOR` (S1a); the decision-ledger / whole-record injection; the salience gate / floor / dedup / rule-weight / pin hard-floor; the SessionStart floor / subagent bundle / native CLAUDE.md load; any `CLAUDE.md`; `settings.json`.

**Blast radius:** `rank()` is on the live per-turn path (main-session UserPromptSubmit + SessionStart composer + every subagent memory tier route through the two resolvers). The change adds ONE guarded, fail-open append per turn to a gitignored disk path and one behavior-inert dict field; it does not alter set-membership or ordering (the returned list is the same object it was before the recorder call). No new hot-path LLM, no new search.

**Reversibility:** telemetry is disabled by leaving `telemetry_dir=None` (direct-config default); the two resolvers are the only place it is turned on. Deleting the log dir removes all telemetry. Git-revert the seal is the whole-cycle rollback. No data migration (the log is derived, gitignored, disposable).

---

## §6 — Build steps (method-level; builder's call per ODD §1.1)

1. Author `test_AC_RTEL_*` first (plan-before-code; TDD-guard).
2. Add the `retrieval_telemetry.py` module: `telemetry_dir_for_workspace`, daily-file path (`retrieval-telemetry-<UTC-date>.jsonl`), the record builder (turn-level + candidates[]), `record_retrieval(...)` fully wrapped fail-open.
3. Add `telemetry_dir` (+ optional `telemetry_turn_id`) to `RetrievalConfig` (keyword field, default `None` → no-op for direct-config callers).
4. Carry `_event_time = ep.get("valid_at")` onto the episode hit in `_episode_hits`.
5. Insert the single guarded `record_retrieval(...)` call at the end of `rank()`, before the return — reading scalar copies off the four in-scope locals, marking injected by object identity against `decision_hits + merged`, never mutating a hit.
6. Thread `telemetry_dir` in `_resolve_live_config` + `_resolve_composer_config`.
7. Run the AC suite + the full `framework/primary-persona` regression; confirm GREEN.
8. Commit source+tests, then `loam amend apply` then `loam amend seal` against the manifest (never `git commit --amend`; new corrective commits if a file is missed).

---

## §7 — Out of scope (deferred)

- **The ranker change** (threshold / recency-relocation — design Stage 3 / the `s2-recency-relocation` plan-doc). This cycle only OBSERVES; it changes no recall behavior.
- **Engagement backfill / auto-labeling** (synthesis' "did the turn reference the injected record" signal). Stage 5 / offline. This cycle captures the `{prompt → candidates → injected}` half; the engagement label is a later additive column. A stable envelope-derived `turn_id` (vs the generated uuid4) is the hook for it — noted, not built.
- **The offline tuner** that fits the threshold + recency weight against the log (design Stage 5). This cycle ships the dataset, not the tuner.
- **Widening the candidate fetch** to log sub-cut candidates the ranker never fetched — would perturb behavior (§2); captured-less by design.
- **Log rotation/pruning policy beyond daily files** — disk is cheap (owner); daily files bound each file + make a future prune trivial; no pruner built.

---

## §8 — Halt triggers (abort the in-flight build)

1. Making the capture reach the full candidate pool would require changing `rank()`'s signature/return or re-running a search → halt (pure-observation is the #1 constraint; capture less instead).
2. A no-regression suite goes red for any reason → halt + surface (this cycle is additive; a red suite is a real regression, not an expected semantic shift).
3. The byte-identical guarantee (AC.RTEL.1) cannot be met — telemetry-on and telemetry-off produce different blocks → halt (the telemetry is perturbing recall; that is the one thing it must never do).
4. Carrying `_event_time` or the recorder call changes any existing test's expectation → halt + surface (it should be inert; if it is not, the assumption in §3.3–§3.4 is wrong).
5. Any surrounding ODD violation surfaces (unnamed code, method-in-AC drift) → halt + surface per `feedback_subagent_odd_violation_halt`.

---

## §9 — Bookkeeping (backfilled at seal)

- `docs/STATE.md` — memory-redesign progress line: S1a sealed → standing-telemetry (this) sealed → ranker Stage 3 next (gated on the baseline this captures).
- `docs/plans/v0-1-x-roadmap.md` §8 — memory-redesign stage ledger (telemetry Stage 2 done; ranker Stage 3 + Stage 4/5 pending).
- §12 below — method-decision register + SHA backfill.

---

## §10 — Named decisions / method calls (builder's call — recommendation IS the decision)

None of these are owner-gated (no critical-call / public-action / financial decision); each flows from the operational objective (a reviewable auto-tune dataset, pure observation) + the dispatch's explicit "capture enough for threshold + recency tuning." Recorded for the audit trail.

- **D1 — Capture point = end of `rank()`, side-effect before the return.** The only point where the full candidate pool AND the injected subset are both known; preserves the sealed P@5-metric `rank()` contract. (§3.1–§3.3)
- **D2 — What to capture.** Turn-level: `schema_version, turn_id, ts (UTC ISO), prompt, work_anchor_tokens, budget{top_n,char_cap}, counts{n_candidates,n_injected}`. Per-candidate: `source (corpus|episode|decision), path, pointer, score (raw discovery), salience (episode; null else), event_time (episode valid_at; null else), injected (bool), rank (int|null)`. Enough to offline-tune a threshold (per-candidate score + injected) AND a recency re-weight (event_time).
- **D3 — Format = JSONL, one object per turn**, candidates embedded as an array (jq-reviewable).
- **D4 — Location = `<workspace_root>/workspace/.loam/retrieval-telemetry/`** (sibling of the episode store; `.loam/` gitignored → standing but untracked). Resolved only by the two live resolvers; direct-config callers pass `None` → no-op.
- **D5 — Retention = daily-rotated `retrieval-telemetry-<UTC-date>.jsonl`, append-only, no deletion** (disk is cheap; daily files bound each file + keep it reviewable + make a future prune trivial).
- **D6 — Failure mode = fully fail-open**; any recorder error swallowed, turn unchanged; the recorder reads scalar copies and never mutates a hit dict.
- **D7 — turn_id = generated uuid4** (optional envelope-supplied id via `telemetry_turn_id` for later engagement correlation; uuid4 is sufficient for the standing dataset this cycle ships).

---

## §11 — F2 Ruthless Feedback (honest doubts / limitations)

1. **The candidate pool captured is the ranker's fetched pool, not the full matched set.** `CorpusIndex.search` / `_episode_hits` fetch a bounded pool (`num_results` / a widened candidate limit) before the cut; the telemetry logs what the ranker fetched, not everything the FTS matched below that. Widening the fetch to see deeper candidates would change behavior (§2), so it is out. Consequence: offline threshold-tuning sees the fetched pool's scores — sufficient to tune the surfaced-set threshold, but it cannot measure recall of records the ranker never fetched. Named, not smoothed over; a deeper-pool telemetry variant is a future, opt-in, non-hot-path option.
2. **The char-budget final drop happens in `_render_injection` (in `retrieve()`), after `rank()`.** A candidate that `rank()` returns but the 5000-char budget later drops is marked `injected=true` in the log (it entered the render). The char budget is recorded as a turn-level parameter, not re-derived per candidate. For threshold/recency tuning this is immaterial (the budget is generous and separate from the relevance threshold); noted for fidelity honesty.
3. **`event_time` is null for corpus rules (timeless) and may be null for decisions.** Recency re-weight tuning therefore concentrates on the episode/decision half — matching the ranker's own recency-neutrality for corpus rules. Not a defect; stated so the dataset's coverage is understood.
4. **uuid4 turn ids don't correlate to turn output**, so engagement backfill (which injected record the turn actually used) needs a stable envelope id later. Captured as the `telemetry_turn_id` hook; the standing `{prompt → candidates → injected}` dataset this cycle ships is complete without it.

---

## §12 — Method-decision register (populated at build; SHA-backfilled at seal)

- D1–D7 — builder method decisions (§10), recorded pre-build; all held as built (no in-flight fork fired).
- Capture point as built: `keep_pace/retrieval.py::rank()` — `injected = decision_hits + merged` then a guarded `_record_telemetry(...)` before the return; `rank()` signature/return unchanged.
- Fixtures updated in-cycle: NONE — the cycle is additive (new module + guarded side-effect + behavior-inert `_event_time` field + two resolver threadings). Full `framework/primary-persona` regression green (1305 passed, 1 pre-existing `requires_live_store` skip).
- SOURCE SHA: `08ce1e93` (feat commit — source + AC.RTEL.1..7 tests).
- APPLY SHA: `c5e4370b` (manifest + sidecar/BASELINE bump to `5f23c3c2`).
- SEAL SHA: `a7ef6ce2` (deterministic seal; post-seal `apply --dry-run` clean; sidecar advanced to `c5e4370b`).
- BASELINE: `5f23c3c2` (S1a seal tip on origin/main).
