# Memory redesign — S2: recency as a prioritization signal + relevance-threshold recall (the ranker change)

**Status:** BUILT + SEALED LOCALLY (2026-07-07) — owner GAVE GO on the §10 forks ("go ahead with ranker stuff", accepting the plan-author recommendations); Fork 1 (measure-before-change) satisfied by STACKING on the sealed telemetry cycle (design Stage 2, tip `a2ce742d`). Code landed on branch `feat/memory-redesign-s2-ranker`. STOPPED before push (behavior-changer — owner-gated public step). See §14 for the ratified rulings + build decisions + SHAs.
**Component (sealed):** `framework/primary-persona` — advances the existing sidecar (`new_component: false`). Single-component amendment.
**Predecessors:** S1a ground-floor extraction (`RANK_CONSTITUTIONAL_FLOOR = False`), sealed on `origin/main` at `5f23c3c2`; the memory-recall-cycle Slice 1 (AC.EVX — activation neutralized default-off, co-citation deleted) + the FBM correctness / supersession / salience / dedup slices, all live in `file_memory.py` + `keep_pace/retrieval.py` + `keep_pace/corpus_index.py`.
**Design source:** `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` (design **Stage 3** — "recency relocation: discovery vs prioritization in (b)") + `owner-refinements-2026-07-02.md` (#2 recency-is-prioritization) + `owner-refinements-round2-2026-07-02.md`.
**Design-stage mapping (read this — the numbering is a trap):** the dispatch's `S2` file-slug = the **design's Stage 3**. The design's **Stage 2 is standing telemetry**, which is NOT yet built and is the ordering fork in §10 Fork 1.

---

## §1 — Objective

Make topical relevance the sole determiner of WHICH on-file memories are recalled per turn (an absolute relevance threshold, empty-OK — not a fixed count), and make event-recency a bounded prioritizer that only re-orders records already discovered as relevant — never a discovery signal and never keyed on how recently/often a record was previously injected.

---

## §2 — Findings pinned at plan-authoring (Tier-0, from the live code)

Every claim here is read from the canonical tree at `origin/main` `5f23c3c2`. These correct a stale premise in the design and right-size the stage.

1. **The live per-turn episode ranking is pure relevance — recency is NOT currently a discovery signal.** `keep_pace/retrieval.py::_episode_hits` calls `FileMemoryStore.search` → `_fts_search` (`file_memory.py:1076`) → `_compose_score` (`file_memory.py:1854`). `_compose_score` computes `BM25 × activation_multiplier × supersession_penalty`. With activation **default-OFF** (`activation_enabled()`, `ACTIVATION_FLAG_ENV`, `file_memory.py:1828`) the multiplier is a neutral `1.0`, and co-citation is deleted (AC.EVX Slice 1 verdict). So the live episode discovery score is **BM25 × supersession** — no recency term.
2. **The W=0.5 recency-in-discovery blend is DEAD code.** `_blend_recency` (`file_memory.py:1759`, `RECENCY_BLEND_WEIGHT = 0.5`, `RECENCY_HALF_LIFE_DAYS = 5.0`) blends event-recency INTO the discovery score — but it has **zero call sites** anywhere in `framework/primary-persona/` (verified by grep across src + tests). It is orphaned by the AC.EVX Slice-1 simplification to `_compose_score`. Its recency-decay primitive `_recency_weight` (`file_memory.py:1533`, keyed on the episode's `reference_time`/`valid_at` — an EVENT time) is reusable, but the *blend-into-discovery* wiring is exactly the design's stale premise.
3. **The corpus half has no recency at all.** `corpus_index.py::CorpusIndex.search` ranks `BM25 × length_penalty × supersession_penalty`, floors noise at `MIN_RELEVANCE_SCORE = 0.1`, then truncates to `num_results`. No event-time term. Corpus feedback-rules are effectively timeless (design: "a rule is timeless until superseded").
4. **Recall is a FIXED COUNT, not a threshold.** `DEFAULT_TOP_N = 5` (`retrieval.py:72`) truncates at three places — `CorpusIndex.search` (`rest_out[:num_results]`), `_episode_hits` num_results, and `_merge_by_score` `combined[:top_n]` (`retrieval.py:911`). `MIN_RELEVANCE_SCORE` / `EPISODE_MIN_RELEVANCE_SCORE` (both `0.1`) are pure-noise floors, not a relevance threshold that decides the surfaced set. Nothing surfaces "the relevant few, possibly zero" — it surfaces "the top 5 that cleared noise."
5. **Injection-frequency self-reinforcement — the design's headline worry — is ALREADY neutralized on the live default.** Activation (the injection-history power-law) is default-off; co-citation is deleted. So the loop "a record ranks higher because it was injected, which causes more injection" is not live. This narrows the stage: it is not "rip a runaway recency/frequency term out of the ranker"; it is "convert count→threshold + ADD a bounded event-recency prioritizer over the discovered set, and lock the injection-history-is-never-a-signal guarantee structurally."

**Net (the honest shape of the stage):** discovery is already relevance-only — the stage makes that an explicit, tested invariant and forbids re-wiring recency in; the two real deltas are (a) fixed-count → relevance-threshold recall (empty-OK), and (b) event-recency added as a NEW bounded prioritizer applied AFTER the threshold selects the set. This is a smaller, safer change than the design's "strip-and-relocate" framing implies — but it still alters recall on every live turn, so §10 Fork 1 (measure-before-you-change) governs.

---

## §3 — Halt-and-surface recorded at plan-authoring

- **The design's Stage-3 premise is stale (F2, load-bearing).** The design says "strip recency from the discovery score." On the live default path recency is not in the discovery score (finding §2.1–2.2). The stage is re-shaped to the accurate reality in §2 (net). This is a plan-time correction, not a scope change; surfaced to the owner as a named F2 finding, not silently absorbed.
- **This cycle changes recall behavior on every turn (reversibility + measurability binding).** Per the dispatch's own governing principle and the design's dependency spine ("Stage 2 telemetry before Stage 3"), the discovery/prioritization change must not flip live **before** baseline telemetry is capturing. Recorded as §10 Fork 1 (gating) + §8 halt trigger.
- **The dead `_blend_recency` is a hazard to leave in place** — a future builder could re-wire it into discovery and silently re-introduce recency-as-discovery (violating AC.RDP.1). Recommendation recorded in §10 Fork 6: retire or explicitly quarantine it in this cycle.

---

## §4 — Acceptance criteria

Outcome-shape; method inferable from the constraints, never stated. AC IDs scope-descriptive (`RDP` = Recency → Discovery/Prioritization), not version-packed (per `feedback_scope_descriptive_ac_ids`). Each is one-test-per-criterion; AC.RDP.6 is the outcome-altitude criterion (production entry-point, no pre-arranged state).

| AC | Outcome | Verification |
|---|---|---|
| **AC.RDP.1** — discovery is relevance-only (invariant) | Whether a record enters the discovered set is decided by topical relevance to the work-anchored prompt alone; neither event-time nor injection-history changes set MEMBERSHIP. | A strongly-relevant OLD record + a weakly-relevant RECENT record: the old-relevant one is discovered, the recent-weak one is not — and the result is invariant to swapping their event-times. `test_AC_RDP_1_*`. |
| **AC.RDP.2** — relevance-threshold recall, empty-OK | The discovered set is the records at/above a NAMED absolute relevance threshold, not a padded fixed count. One relevant record → one surfaced (not padded toward K); zero relevant → empty. | Query matching exactly one relevant record surfaces one; query matching none surfaces `""`. `test_AC_RDP_2_*`. |
| **AC.RDP.3** — event-recency prioritizes WITHIN the discovered set | Among records that BOTH clear the threshold, the newer-by-EVENT-TIME is ordered ahead when relevance is comparable; the re-order never promotes a below-threshold record into the surfaced set. | Two equally-relevant discovered records, different event-times → newer first; a below-threshold near-miss stays out regardless of its recency. Owner's example: newest "project complete" ahead of oldest "project incomplete". `test_AC_RDP_3_*`. |
| **AC.RDP.4** — injection-history is never a ranking signal (structural) | No signal derived from how recently/often a record was previously injected participates in discovery or prioritization. | Injecting a record on turn N does not raise its discovery membership or prioritization rank on turn N+1, holding relevance + event-time fixed. `test_AC_RDP_4_*`. |
| **AC.RDP.5** — reversible via named levers | The threshold, the recency-prioritizer weight, and the optional count cap are NAMED tunable constants; restoring legacy values reproduces the pre-stage ranking. | Levers set to legacy values → pre-stage top-N ordering reproduced byte-for-byte on a fixture the current suites already cover. `test_AC_RDP_5_*`. |
| **AC.RDP.6** (outcome-altitude) — production `retrieve()`, no pre-arranged state | Over the real resolver + `retrieve()` from an empty starting state, on a query with two genuinely-relevant records of different event-age plus one below-threshold near-miss: the surfaced block carries BOTH relevant records newest-first and EXCLUDES the near-miss; a query with only below-threshold near-misses surfaces an empty block. | `test_AC_RDP_6_OA_*` drives the production entry-point with no pre-set ranking state. |

**No-regression (AC.RDP.5 envelope):** the KP1 / FBMU / FBM-FILTER / SRF / RQ80 / SUP / DLG / EVX / MSC suites stay green, EXCEPT where a fixture legitimately encodes the old fixed-count semantics the threshold replaces — those fixtures are updated in-cycle and the change is named in §14. Any suite whose expectation changes is surfaced, not silently edited.

**Ladder-up:** AC.RDP.* → the design's Stage-3 outcome (best on-file context for the subject, recency as tiebreak-not-discovery) → AC.PO.1/AC.PO.2 (per-user translation + protection-from-betrayal, `docs/VALUE_PROPOSITION.md`): this stage protects the "best relevant context, not the loudest/most-recent" guarantee and reduces the translation burden of a turn surfacing stale-but-frequent junk.

---

## §5 — The fence

**Primary (in-fence, edited):**
- `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py` — the merge is where the threshold + the post-threshold event-recency prioritizer + the optional count cap live (they operate over the unified corpus+episode+decision set); the named levers are declared here beside `DEFAULT_TOP_N` / `INJECTION_CHAR_CAP` / `RANK_CONSTITUTIONAL_FLOOR`.
- `framework/primary-persona/src/loam/primary_persona/file_memory.py` — keep `_compose_score` discovery relevance-only; expose the event-time (`reference_time`/`valid_at`) on each episode hit so the merge-side prioritizer can read it (`_recency_weight` is the reusable decay primitive); retire or quarantine the dead `_blend_recency` (§10 Fork 6).
- `framework/primary-persona/src/loam/primary_persona/keep_pace/corpus_index.py` — TOUCHED ONLY IF the threshold semantics require the corpus-side `rest_out[:num_results]` truncation to defer the set-cut to the merge; if the threshold is applied wholly at the merge, this file is unchanged. The builder confirms at build time and names it in §14.
- `framework/primary-persona/tests/test_AC_RDP_*` — the AC suite.

**Explicitly NOT touched:** the ground-floor lever `RANK_CONSTITUTIONAL_FLOOR` (S1a); the decision-ledger + whole-record injection (DLG); the salience gate, absolute episode floor, near-dup dedup, rule-weight/pin hard-floor (Slice B); the SessionStart corpus-inline floor / subagent bundle / native CLAUDE.md load; any `CLAUDE.md` file; `settings.json`; the session-start active-thread recency scan (AC.MSC.2, a separate surface from the per-turn ranked pool).

**Blast radius:** `retrieve()` is on the live per-turn path (main-session UserPromptSubmit + SessionStart composer + every subagent memory tier — all route through the two resolvers). The change alters ordering + set-membership under the existing fail-open contracts; no new I/O on the hot path (the prioritizer is arithmetic over already-fetched hits, mirroring `_merge_by_score`'s existing weight/salience math).

**Reversibility:** named levers restore the prior ranking (AC.RDP.5); git-revert the seal is the whole-cycle rollback. No data migration — ranking-only over a derived `.scratch/` index and the on-disk episodes/corpus, all untouched.

---

## §6 — Build steps (method-level; builder's call per ODD §1.1)

1. Author `test_AC_RDP_*` first (plan-before-code; TDD-guard).
2. Declare the named levers in `retrieval.py` (relevance threshold; recency-prioritizer weight; optional count cap) with no-op-preserving defaults where a no-op is meaningful, and the new-behavior defaults otherwise.
3. Make discovery-relevance-only an explicit invariant + convert the fixed-count truncation to the threshold (empty-OK) at the merge; keep the byte cap.
4. Add the bounded event-recency prioritizer over the post-threshold, post-dedup set, before the count cap; read event-time from the hit (episodes/decisions carry it; timeless corpus rules are recency-neutral via the `_recency_weight` fail-soft).
5. Retire/quarantine `_blend_recency` per §10 Fork 6.
6. Run the AC suite + the no-regression suites; update only the fixtures that legitimately encoded fixed-count semantics (name them in §14).
7. `loam amend apply` then `loam amend seal` against the manifest (never `git commit --amend`; new corrective commits if a file is missed).

---

## §7 — Out of scope (deferred)

- **Standing telemetry (design Stage 2)** — its own cycle; §10 Fork 1. Its `{prompt/work-anchor → candidates+scores → crossed-threshold → injected → engagement}` log is the baseline this cycle needs but does not itself build.
- **Rule store (c) + situational recall + write-side fact/rule split (design Stage 4 / owner #3,#4).**
- **Offline consolidation / rule-derivation / parameter auto-tuning (design Stage 5).** The threshold + recency-weight this cycle ships are *tuned offline against telemetry later* — this cycle ships sensible named defaults, not the tuner.
- **Re-enabling activation (injection-history)** — stays default-off; AC.RDP.4 forbids it as a signal in this cycle.
- **Per-workspace recency half-life tuning** — deferred (already out-of-scope in the MSC plan).

---

## §8 — Halt triggers (abort the in-flight build)

1. **No baseline telemetry capturing** and the owner has not ruled Fork 1 to proceed without it → halt (measure-before-you-change).
2. A no-regression suite fails for a reason that is NOT the deliberate fixed-count→threshold fixture update → halt + surface (a real regression, not an expected semantic shift).
3. The threshold default, on the live corpus, collapses recall to near-empty on ordinary work prompts (over-tight) or changes nothing (over-loose) → halt + surface for a threshold re-pick (Fork 2).
4. Implementing AC.RDP.3 requires resurrecting an injection-history signal to make recency work → halt (AC.RDP.4 is structural; the prioritizer keys on EVENT time only).
5. Any surrounding ODD violation surfaces (unnamed code, method-in-AC drift) → halt + surface per `feedback_subagent_odd_violation_halt`.

---

## §9 — Bookkeeping (backfilled at seal)

- `docs/STATE.md` — memory-redesign progress line: S1a sealed → S2 (this) sealed.
- `docs/plans/v0-1-x-roadmap.md` §8 — the memory-redesign stage ledger (design Stage 3 done; telemetry Stage 2 + Stage 4/5 pending).
- Parent design dir — no edit (research artefact is immutable); this plan cites it.
- §14 below — method-decision register + SHA backfill by `loam amend seal --plan-doc`.

---

## §10 — Named decisions / forks (owner GO required)

Each carries an explicit recommendation. Fork 1 is gating.

**Fork 1 — ORDERING: build standing telemetry (design Stage 2) BEFORE flipping this live [GATING].**
The design spine is explicit ("2 before 3"; "ship telemetry before the score changes to capture the baseline over-injection rate"), the owner's #1 refinement is standing telemetry, and the dispatch's own binding principle is "reversible + measurable — this changes recall every turn." Telemetry is the smaller, additive, fail-soft, mechanical (Sonnet-tier) slice; this ranker change is judgment-grade and alters every turn.
**Recommendation:** build the standing-telemetry cycle first (its own small plan + manifest), let it capture a baseline, THEN ship this cycle. Do NOT flip the discovery/prioritization change unmeasured. If the owner wants to proceed without telemetry, this cycle's §8 Halt-trigger 1 is waived by explicit ruling and recorded in §14.

**Fork 2 — THRESHOLD value + how it is tuned.**
The absolute relevance threshold that decides the discovered set (empty-OK).
**Recommendation:** ship a conservative NAMED default calibrated just above today's noise floor (the `0.1`-scale) on the live corpus so day-one recall does not collapse, and tune it OFFLINE against Stage-2 telemetry later (never a hot-path LLM). Start slightly loose, measure, tighten — the asymmetry favors a missed-tighten (a little extra context) over an over-tighten (a silent recall gap, invisible).

**Fork 3 — TOP-K above the threshold: keep as a safety cap or remove.**
**Recommendation:** KEEP a count cap (default 5, the current `DEFAULT_TOP_N`) as a SAFETY CAP above the threshold, with the threshold as the primary set-determiner and empty-OK below it. A pure-threshold-no-cap turn risks a pathological over-injection if many records clear threshold; the byte cap exists but a cheap count cap is insurance. Reversible via the named lever.

**Fork 4 — RECENCY re-weight shape at prioritization: bounded re-weight vs pure tiebreak.**
**Recommendation:** BOUNDED re-weight (a NAMED weight applied POST-threshold over the discovered set only), NOT a pure tiebreak. The owner's "5 memories all materially relevant → recency decides weighting" is a re-weight, not merely a tie-break. Bound it so recency can reorder WITHIN the discovered set and can NEVER resurrect a below-threshold record (that boundary is AC.RDP.3). Keep event-recency vs injection-recency strictly separated (AC.RDP.4).

**Fork 5 — EVENT-TIME source.**
Prioritization keys on `reference_time`/`valid_at` (when the thing happened), not ingest/injection time.
**Recommendation:** use event/reference time (the field `_recency_weight` already reads); absent → recency-neutral (existing fail-soft). Low-risk; surfaced for confirmation only.

**Fork 6 — the dead `_blend_recency`: retire or quarantine in this cycle.**
**Recommendation:** RETIRE it (delete + its now-unused constants) OR quarantine behind an explicit "not-a-discovery-signal" guard, so a future builder cannot re-wire recency into discovery and silently break AC.RDP.1. Deleting dead code that is a correctness hazard is in-scope for this cycle (`feedback_evaluate_rules_not_just_patch`). Low-risk; reversible from git history if ever needed.

---

## §11 — F2 Ruthless Feedback (honest doubts / risks)

1. **The design's Stage-3 framing is stale — named, not smoothed over.** "Strip recency from the discovery score" describes a code state that no longer exists on the live default path (finding §2). Building literally to the design's words would produce a no-op-on-discovery plus confusion. This plan builds to the accurate reality. Evidence: `_blend_recency` has zero call sites; `_compose_score` is BM25 × supersession. Alternative rejected: "follow the design verbatim" — it would target dead code.
2. **The every-turn recall change is real even though it is smaller than advertised.** The threshold (count→relevance) and the new prioritizer both move what surfaces on ordinary turns. Without the Stage-2 baseline you cannot tell an improvement from a regression. This is why Fork 1 is gating, not advisory.
3. **Threshold-picking is the judgment risk with an invisible failure mode.** Over-tight → a silent recall gap (a relevant record never surfaces; you cannot see what did not appear). Over-loose → over-injection returns. The invisible direction (over-tight) is the one to instrument first (Fork 2 recommendation leans loose-then-tighten; telemetry makes the gap visible).
4. **Corpus rules are timeless, so the recency prioritizer mostly reorders episodes/decisions.** That matches the owner's examples (project complete/incomplete) but means the headline benefit is concentrated on the episode/decision half; corpus feedback-rules are recency-neutral. Not a defect — worth stating so expectations match.

---

## §12 — Provenance trail

- Design Stage 3 + telemetry spine: `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` (§"Staged build plan", Stage 3 + the 1→3 / 2-before-3 dependency spine; the injection-recency-vs-event-recency split).
- Owner refinements: `.../owner-refinements-2026-07-02.md` #2 (recency is prioritization, not discovery; supersession-by-recency tiebreak) + `.../owner-refinements-round2-2026-07-02.md` (liberal fact ingest safe because relevance-gated).
- Live code (canonical `origin/main` `5f23c3c2`): `file_memory.py` `_compose_score:1854`, `_fts_search:1076`, `_blend_recency:1759` (dead), `_recency_weight:1533`, `activation_enabled:1828`, `RECENCY_BLEND_WEIGHT:558`; `keep_pace/retrieval.py` `DEFAULT_TOP_N:72`, `_merge_by_score:781`, `_episode_hits:288`; `keep_pace/corpus_index.py` `search:536`, `MIN_RELEVANCE_SCORE:82`.
- S1a predecessor: `docs/plans/memory-redesign-s1-ground-floor-extraction.md` + its manifest.

---

## §14 — Method-decision register (populated at build; SHA-backfilled at seal)

**Owner fork rulings (ratified — "go ahead with ranker stuff", accepting the plan-author recommendations):**

- **D-Fork1 (GATING — ordering):** build telemetry (design Stage 2) BEFORE flipping this live → SATISFIED by stacking this cycle on the sealed telemetry tip `a2ce742d` (main → telemetry → ranker). Telemetry captures the ranker's before/after; §8 Halt-trigger 1 does not fire.
- **D-Fork2 (threshold value + tuning):** RELEVANCE threshold, empty-OK; a NAMED conservative default just above the noise floor; start slightly LOOSE; tune OFFLINE against telemetry. → `RELEVANCE_THRESHOLD = 0.5` (raw negated-BM25 scale, 5× the `0.1` noise floor). Data-informed (verified against the live store this session): a genuine multi-term episode match scores ~2.9–5.2; a single-weak-term near-miss ~0.6; noise <0.1. So `0.5` trims only sub-0.5 near-noise and never hides a real match — honoring the owner's asymmetry (an over-tighten silently hides a memory; a missed-tighten costs a little extra context). Offline tuning likely moves it toward ~1.0–1.5 once the distribution is measured.
- **D-Fork3 (count cap):** KEEP top-5 as a SAFETY CAP above the threshold. → `DEFAULT_TOP_N = 5` reframed + documented as the safety cap; the threshold is the primary set-determiner, the cap is insurance. Named/tunable (per-call `top_n`).
- **D-Fork4 (recency shape):** BOUNDED re-weight over the discovered set, not a pure tiebreak. → `RECENCY_PRIORITIZER_WEIGHT = 0.3`; factor `(1-W) + W·recency_weight ∈ [0.7, 1.0]` applied post-threshold to the boosted score. Reorders within comparable relevance; can never resurrect a below-threshold record or leapfrog a much-stronger-relevance record.
- **D-Fork5 (event-time source):** use EVENT/reference time (`valid_at`=`reference_time`); absent → recency-neutral. → the prioritizer reads the hit's `_event_time` (carried by the telemetry cycle's `_episode_hits`); absent/unparseable → factor 1.0 (neutral). Note: `_recency_weight(None)` returns `0.0` (its additive-channel neutral), so the merge-side prioritizer treats "no event-time" as factor `1.0` DIRECTLY (the multiplicative neutral) so a timeless corpus rule is never demoted.
- **D-Fork6 (dead `_blend_recency`):** RETIRE it. → deleted `_blend_recency` + `RECENCY_BLEND_WEIGHT` from `file_memory.py`; kept `_recency_weight` + `RECENCY_HALF_LIFE_DAYS` (reused by the merge-side prioritizer); reworded the stale recency-in-discovery comments to state DISCOVERY IS RELEVANCE-ONLY (AC.RDP.1 lock). Recoverable from git history.

**Builder method decisions:**

- **D-build.1 (levers):** two new named levers in `keep_pace/retrieval.py` — `RELEVANCE_THRESHOLD`, `RECENCY_PRIORITIZER_WEIGHT` — plus `DEFAULT_TOP_N` documented as the safety cap. All three threaded as per-call params through `_merge_by_score` / `rank` / `retrieve` (mirroring the sealed `salience_threshold` per-call pattern).
- **D-build.2 (threshold placement + sparse-rescue safeguard):** the relevance threshold is applied to EPISODE hits at the merge, AFTER the pure-noise episode floor, in the POPULATED regime only — `_apply_relevance_threshold` mirrors `_apply_episode_floor`'s over-filter safeguard (self-disables when no episode clears the noise floor), so the sealed lone-sparse-episode rescue (AC-FBM-RN-2 / AC-FBM-FLOOR-1 safeguard) is preserved byte-for-byte. Resolves the empty-OK ↔ sparse-rescue tension: a raw~0 fresh episode in an IDF-collapsed store is a scoring artefact (rescue), not a below-threshold near-miss (gate) — the distinguisher is the noise-floor regime, exactly the owner's over-tighten asymmetry.
- **D-build.3 (scope — episodes not corpus):** the threshold gates EPISODE hits only. Corpus feedback-rules are source-floored (`MIN_RELEVANCE_SCORE`) and timeless; genuine corpus matches score 15–285 (far above any conservative threshold); the owner's examples are episode/decision-centric. This preserves the AC.FBMU.2 byte-identical corpus-only path. Reversible: the lever could extend to corpus in a later offline-tuned cycle.
- **D-build.4 (corpus_index.py NOT touched):** per plan §5's conditional — the threshold + cap are applied wholly at the merge, so the corpus-side `rest_out[:num_results]` truncation is unchanged.
- **D-build.5 (fixtures):** NO sealed fixture required updating — the full `framework/primary-persona` suite (1319 passed, 1 skipped) stayed green with the new levers at their day-one defaults, confirming the loose start is conservative enough not to disturb any sealed contract (§8 Halt-trigger 2 did not fire; §4's "fixtures updated in-cycle" list is empty).

**Verification:** AC.RDP.1–6 all pass (14 tests); full component regression green; before/after telemetry probe confirms the recall delta is captured (legacy levers inject the near-miss; S2 levers gate it, `injected=False` at raw 0.608 < threshold, event-recency orders newest-first).

- **SOURCE SHA:** _backfilled below._
- **APPLY SHA / SEAL SHA:** _backfilled by `loam amend seal --plan-doc`._
