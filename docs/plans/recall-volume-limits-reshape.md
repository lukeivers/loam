# Recall volume-limits reshape — floor + budget replace the count caps

**Status:** sub-plan-doc (build-ready pending owner nod on the §3 budget-derivation call).
**WD:** `/Users/lukeivers/loam` (canonical). Build in an isolated worktree/clone per serialize-amendment discipline.
**Parent plan / design spine:** `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` (design Stages 3–5) + `docs/design/keep-pace-with-user.md` (north star).
**Predecessors (load-bearing sealed tips):**
- `a1166b8d` — S4 rules-store + situational recall seal (current canonical HEAD).
- `79858ab1` — S2 recency-relocation / relevance-threshold recall (the half-landed floor conversion this cycle finishes).
- `a2ce742d` — standing retrieval telemetry (design Stage 2) — the measurement surface the retirement criteria depend on.
**BASELINE candidate:** `a1166b8d` (S4 seal = current HEAD). Retarget at apply time to HEAD~1.
**Status-file target:** `docs/STATE.md` + roadmap.
**Quality bar:** ODD §2.5 (every line maps to a named AC); outcome-altitude AC required; fail-soft hot-path preserved; stdlib-only, NO Anthropic API key on the recall path.

---

## §1 Summary / TL;DR

The recall path today is *threshold-gated inside a count-capped candidate pool* — the count still silently decides the set on three surfaces the S2 "threshold replaces the count" change never reached. This cycle finishes the conversion so **the only two volume controls in the scored recall path are a relevance floor (quality) and a byte budget (attention)**, matching the human-memory north star (long-term store uncapped; only attention bounded).

Ships (build cycle 1 — items 1, 2, 3, 5):
1. Kill the fetch-side count truncation of corpus candidates (`corpus_index.py`), and the twin count bounds on the episode fetch + post-merge truncation, so the floor + byte budget determine the set.
2. Sunset `DEFAULT_TOP_N` and the post-merge `combined[:top_n]` to a *named backstop with a written retirement trigger* tied to telemetry.
3. Drop `SITUATIONAL_RULE_CAP` (count), keeping only the byte sub-budget — **and re-anchor every byte budget to a real named resource** (the §3 open owner call).
4. Structural cap-bias catch: a plan-review checklist line + a seeded situational rule on a new `authoring-plan` trigger.

Deferred to build cycle 2 (item 4): **iterative associative recall** as its own staged cycle (research §1.6). Larger, and it wants a telemetry before/after — see §7.

**Key decisions baked:** floor+budget are the only two limit-kinds in the scored path; count caps survive only on floorless channels or as retirement-dated scaffolding; NEVER a `MAX_PASSES` on the iterative loop.

**F2 on scope realism (§10):** item 4 is scope-realistically its own build cycle; bundling it with the floor conversion would make one oversized amendment. Recommend two sealed cycles under this one plan-doc.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| Corpus fetch de-count | `corpus_index.py` `search()` (the `candidate_limit` window + the `rest_out[:num_results]` truncation) | The count lives in TWO places on the corpus path, not one (see §10 RF-1). Both must defer to the floor. |
| Episode fetch de-count | `retrieval.py` `_episode_hits` (`num_results=config.top_n`) + `_merge_by_score` post-merge `combined[:top_n]` | Twin count bounds; the byte budget is the true ceiling. |
| `DEFAULT_TOP_N` sunset | `retrieval.py:81` (constant + docstring) | Keep as a named backstop with a retirement trigger, not a set-determiner. |
| `SITUATIONAL_RULE_CAP` drop | `retrieval.py:249` | Redundant with `SITUATIONAL_RULE_CHAR_CAP`; its failure is silent suppression of a *matched* directive. |
| Byte-budget re-anchor | `retrieval.py:129` (`INJECTION_CHAR_CAP`) + `:256` (`SITUATIONAL_RULE_CHAR_CAP`) | Both are un-anchored fixed numbers today; anchor to the enforced structural ceiling (§3). |
| Structural catch — checklist | `plugins/dev-sdlc` plan-author + reviewer checklists (docs) | Plan-time altitude where every cap entered. |
| Structural catch — seeded rule | `rules_store.py` `SEEDED_RULES` + new `authoring-plan` trigger in `retrieval.py` `SITUATION_TRIGGERS` | In-context reminder at authoring time; the rules channel's inaugural real case. |

---

## §3 THE OPEN OWNER DECISION — byte-budget derivation (present, do NOT resolve)

**Both `INJECTION_CHAR_CAP = 5000` and `SITUATIONAL_RULE_CHAR_CAP = 1200` are un-anchored fixed integers.** The 5000 at least carries a stated "fit ≥3 whole records" rationale; the 1200 rules sub-budget carries none. Neither tracks a live resource. Fable's law: any limit not tied to a *named live resource* drifts into harm (the 1200→5000 injection-cap history is the proof — `retrieval.py:122-128`).

**Option A — derive the budget from actual remaining context headroom at injection time (a truly live resource).**
- Pro: the most faithful analog of the human attention bound; self-adjusts as the turn's context fills.
- **Con (feasibility, Tier-0):** the recall path is a stdlib, fail-soft `UserPromptSubmit` hook with NO Anthropic API key (`feedback_no_anthropic_api_key`). Live per-turn remaining-token headroom is not exposed to that hook in any stable field, and measuring it would require a token-count API call on the hot path — which the no-key constraint forbids. So "true live headroom" is **not cheaply available today.**

**Option B — keep fixed char numbers as explicit scaffolding-with-a-written-retirement-trigger.**
- Pro: zero new failure surface; honest about being a placeholder; retirement tied to the telemetry already built.
- Con: still a static integer between now and retirement; relies on discipline to re-derive on regime change.

**RECOMMENDATION — a hybrid that IS anchored to a real named resource without a hot-path API call: derive both budgets as named fractions of `ADDITIONAL_CONTEXT_CAP` (= 10,000, `context_composer.py:59`) — the one limit in the whole system backed by a real, enforced, named resource boundary (construction *refuses* above it).** Concretely: `INJECTION_CHAR_CAP := round(f_fact × ADDITIONAL_CONTEXT_CAP)` and `SITUATIONAL_RULE_CHAR_CAP := round(f_rules × ADDITIONAL_CONTEXT_CAP)`, with `f_fact`/`f_rules` named fractions carrying the "≥3 whole records" sizing rationale, plus a comment naming the resource each derives from so a regime change re-derives instead of drifting. Retirement of the *fractions* to Option A (true live headroom) is deferred until a no-API-cost headroom signal exists in the hook envelope. This gives the owner the "tied to a live resource" property (the ceiling is real and enforced) today, and a clean upgrade path to per-turn headroom later — strictly better than either raw option. **Owner rules on: hybrid (recommended) vs Option B (keep integers + retirement trigger) vs Option A (attempt live headroom now).**

---

## §4 Spec-objective placement

Binds to AC.PO.1 (reduce translation burden — the user brings *what*, loam surfaces the right memory without the user managing recall knobs) and the keep-pace north star ("effectively perfect recall; the only real problem is surfacing the right things at the right time"). Ladders up: recall-reshape ACs → keep-pace outcome ACs → AC.PO.1 / AC.PO.2 (`docs/VALUE_PROPOSITION.md`).

---

## §5 Acceptance criteria

Outcome-shape; each passes the method-in-AC test (satisfiable by a method other than the one in mind). AC.RVL.7 is the outcome-altitude criterion (production `retrieve()` / `search()`, no pre-arranged state).

| ID | Outcome | Verification |
|---|---|---|
| **AC.RVL.1** | When more corpus records clear the relevance floor than the legacy count, records beyond the legacy count still reach the merge — the floor, not a fixed count, determines the corpus discovered set. | Fixture corpus with N≫legacy floor-clearing rules; assert all floor-clearing rules are candidates at the merge (none dropped by a pre-merge count). |
| **AC.RVL.2** | The episode discovered set is determined by the relevance floor, not by a fetch-side count bound: when >legacy episodes clear the floor they are all candidates at the merge. | Fixture episode store; assert episode candidate count at merge tracks floor-clearing count, not a fixed bound. |
| **AC.RVL.3** | The per-turn injected set is bounded only by the byte budget (best-first, drop-whole on overflow) — no count truncation silently decides which records inject. | Inject-many-relevant fixture; assert the cut is byte-budget-driven, and removing the byte budget (raising it) admits more records with no count wall. |
| **AC.RVL.4** | `DEFAULT_TOP_N` / post-merge count survive only as a named backstop whose docstring states an explicit, telemetry-measurable retirement trigger; the backstop is a no-op on all normal-volume turns. | Assert the constant's docstring names the retirement criterion; assert a normal-volume turn's output is identical with the backstop present vs at its no-op value. |
| **AC.RVL.5** | A matched situational rule is never dropped by a *count*: the rules block is bounded only by its byte sub-budget; every matched rule that fits the byte budget injects. | Fixture with >legacy-cap matched rules that all fit the byte budget; assert all inject. `SITUATIONAL_RULE_CAP` removed or proven a no-op. |
| **AC.RVL.6** | Every byte budget in the recall path names, in-source, the resource constraint it derives from; a byte budget with no named resource is absent. | Grep/assert each budget constant carries a resource-naming comment; per §3 ruling, budgets derive from `ADDITIONAL_CONTEXT_CAP` (hybrid) or carry a written retirement trigger (Option B). |
| **AC.RVL.7 (outcome-altitude)** | Production `retrieve()` with no pre-arranged state: given a corpus + episode store where more records clear the floor than the legacy count of 5, the injected set contains records beyond the 6th and is cut by the byte budget — not at 5; a floorless-only cue still surfaces empty. | Cold-walk the production entry-point on a fixture dir; assert >5 floor-clearing records inject and the cut is byte-driven. |
| **AC.RVL.8** | The plan-review checklist carries the cap-bias line, and the reviewer gate enforces it; a plan introducing a numeric limit with no named resource is flagged. | Assert the checklist line is present in the plan-author + reviewer checklists; the line reads per §6 build step 5. |
| **AC.RVL.9** | A seeded situational rule fires on an `authoring-plan` situation directing floor+budget over count caps, provenance-anchored to this artifact; the `authoring-plan` trigger detects a plan-authoring turn and stays silent on ambiguous input. | Fixture turn text that announces plan authoring → rule surfaces; ambiguous turn → silent (the under-fire bias, AC.RSR.3 parity). |

### Build cycle 2 (item 4 — iterative associative recall), ACs declared here, built next cycle

| ID | Outcome | Verification |
|---|---|---|
| **AC.IAR.1** | Recall proceeds in passes: each pass is seeded by the prior pass's admitted hits; a record admitted only via association (not the seed cue) can appear. | Fixture where a 2nd-hop record is unreachable from the seed cue alone; assert it surfaces via a later pass. |
| **AC.IAR.2** | Iteration terminates when a pass admits nothing new — with NO `MAX_PASSES` cap anywhere. | Assert termination on convergence; assert absence of any pass-count ceiling constant (grep-level). |
| **AC.IAR.3** | A per-hop relevance gate + an anchor gate back to the original turn bound associative drift: an associated record below the anchor gate for the original cue is not admitted. | Fixture with a topically-drifting association; assert it is gated out by the anchor gate. |
| **AC.IAR.4** | Per-pass admissions are logged to the existing telemetry so pass-depth distribution is measurable. | Assert telemetry records per-pass admission counts. |
| **AC.IAR.5 (outcome-altitude)** | Production entry-point, no pre-arranged state: a seed cue whose direct hits reference a second entity surfaces the second entity's records via association, converging without a pass cap. | Cold-walk; assert associative surfacing + convergence. |

---

## §6 Build steps (method-level guidance; builder's call per ODD §1.1)

**Cycle 1 — manifest `docs/plans/recall-volume-limits-reshape.manifest.yaml` (this cycle).**

1. **Corpus fetch-floor conversion** (`corpus_index.py`): the count gates the set in TWO places — the SQL `candidate_limit = max(num_results*5, num_results)` window (`:574`) AND `out = pinned_out + rest_out[:num_results]` (`:656`). Make the discovered set floor-determined: fetch a window that is not a fixed multiple of the injected count (floor-bounded / generously wide) and remove the count truncation so all floor-clearing corpus hits reach the merge. The existing `MIN_RELEVANCE_SCORE` cut at `:641` is the floor; keep it.
2. **Episode + post-merge de-count** (`retrieval.py`): `_episode_hits` fetches `num_results=config.top_n` (`:716-718`) and `_merge_by_score` truncates `combined[:top_n]` (`:1402-1403`). Defer both to the byte budget; the floor gates episodes at the merge (`RELEVANCE_THRESHOLD`, already present).
3. **`DEFAULT_TOP_N` sunset** (`retrieval.py:81`): rewrite the docstring to a named backstop with an explicit retirement trigger — e.g. "retire once telemetry shows p99 floor-clearing-set-size fits the byte budget across ≥Nk turns"; keep the constant as a no-op-on-normal-turns safety ceiling until then.
4. **Byte-budget re-anchor + `SITUATIONAL_RULE_CAP` drop** (`retrieval.py:129/:249/:256`): per the §3 ruling. Drop the count cap; keep the byte sub-budget. Anchor both budgets per the ruling (hybrid fractions of `ADDITIONAL_CONTEXT_CAP`, or retirement-dated integers).
5. **Structural catch (two parts):**
   - Checklist line (plan-author + reviewer docs): *"Every numeric limit in this plan names (a) the RESOURCE constraint it derives from and (b) why the relevance floor + byte budget don't already cover it. A quantity cap with no named resource is a defect. Named exceptions: a channel with no relevance signal (count as budget denomination), or temporary scaffolding carrying a written retirement criterion."*
   - Seeded rule (`rules_store.py` `SEEDED_RULES`) on a new `authoring-plan` situation, provenance → this artifact + the 2026-07-08 decision record; add the `authoring-plan` trigger to `SITUATION_TRIGGERS` (`retrieval.py:270`) as a high-precision, under-fire-biased pattern pair (AC.RSR.3 parity).
6. Author tests per AC.RVL.1–9; `loam amend apply`; `loam amend seal`; smoke the production `retrieve()` cold-walk.

**Cycle 2 — item 4, separate manifest at build time.** Iterative associative recall per research §1.6 (seed → frontier above floor → new cues from admitted hits' FTS tokens → per-hop gate + anchor gate → stop on no-new / byte budget). Dispatch after cycle 1 seals and telemetry captures a before/after. NEVER a `MAX_PASSES`.

---

## §7 Out of scope

- **Iterative associative recall (item 4)** — declared here (AC.IAR.*), built as cycle 2 with its own manifest; deferred so cycle 1 is a clean, small, measurable floor conversion and item 4 gets its own telemetry before/after.
- Offline threshold-tuning engine (design Stage 5) — the retirement triggers *reference* it but do not build it.
- Storage-side changes — the store already keeps everything (never-not-store); this is recall-side only.
- `OPEN_DECISION_CAP` / `DECISION_TOP_N` on floorless channels — legitimate as budget denomination where no relevance signal exists (research §1.5.5); left as-is but their comments should name "no relevance signal on this channel; count is the budget denomination" (fold into cycle 1 step 4 if cheap; otherwise a docs follow-on).

## §8 Halt triggers (in-flight)

1. A score appears on the situational-rule *match* side (rules match by exact tag set-membership, never a score) — halt (S4 §6.1 invariant).
2. Removing a fetch-side count regresses the sealed lone-sparse-episode rescue / pinned-hard-floor (AC-FBM-RN-2 / AC-FBM-W-2) — halt and surface.
3. The byte-budget re-anchor would need a hot-path API call (violates no-API-key) — halt; fall back to Option B.
4. Any change would touch a sealed component with no manifest entry — halt rather than widen the fence.
5. The iterative loop (cycle 2) shows unbounded pass growth on a fixture — the fix is the anchor-gate value, NEVER a pass cap; halt and surface if a cap seems needed.

## §9 Bookkeeping

- `docs/STATE.md` change-log entry on each seal.
- Roadmap: mark the recall-reshape cycle under the memory-redesign track.
- Backfill §11 SHAs at seal via `loam amend seal --plan-doc`.
- Decision record `2026-07-08-memory-recall-volume-limits-fable-review-rulings.md` status → fully-ruled once the owner rules §3.

## §10 F2 Ruthless Feedback (honest doubts, named)

- **RF-1 (Tier-0, load-bearing correction to the accepted scope).** Scope item 1 names ONE count truncation (`corpus_index.py:656`). There are **two** count gates on the corpus path: the SQL `candidate_limit = max(num_results*5, num_results)` fetch window at `corpus_index.py:574` runs *before* `:656`. Removing only `:656` leaves the SQL LIMIT still count-bounding the candidate pool at 25 (5×5) — the floor conversion would be half-done again. **The builder must convert BOTH.** Evidence: `corpus_index.py:574,579-582,656`. Alternative: fetch floor-bounded (LIMIT by a generous constant, or unbounded-with-floor) and let `MIN_RELEVANCE_SCORE` + the byte budget gate. This is the single most likely way this cycle repeats S2's half-landing.
- **RF-2 (feasibility on the §3 headline).** Option A ("live remaining context at injection time") is presented per the dispatch, but I have not found a hook-envelope field exposing live token headroom, and computing it needs an API call the no-key constraint forbids on the hot path. Presenting Option A as freely available would be dishonest; my recommendation routes around it via the enforced structural ceiling. Evidence: `context_composer.py:59` (real ceiling), `feedback_no_anthropic_api_key`. If the owner knows of a headroom signal in the envelope, that flips the recommendation to A.
- **RF-3 (agree with the owner's per-item rulings — one nuance).** The research verdict I concur with: the single measured harm in this history came from a *byte* cap set for a dead regime, not a count cap. So the reshape's own new byte-budget anchoring (§3) is where the next $750k-class failure would hide, not in the count removals. That is why RF-2's "anchor to a real resource" matters more than the count drops — the counts fail *silently* but cheaply-to-detect; a mis-anchored byte budget fails *silently and expensively*. Lean the design's rigor there.
- **RF-4 (scope realism, F4/Lens 5).** Item 4 is a new recall STAGE, not a lever tweak; bundling it with the floor conversion produces an oversized amendment whose ACs span two very different confidence levels. Recommend two sealed cycles under this plan-doc (cycle 1 tight/high-confidence; cycle 2 looser/design-shaped). This plan is authored that way.

## §11 Provenance trail

- Decision record: `workspace/.loam/memory/decisions/2026-07-08-memory-recall-volume-limits-fable-review-rulings.md` (owner rulings; 1/2/4/5 accepted, 3 pending).
- Fable audit: `workspace/strategy/memory-recall-volume-limits-and-cap-bias-2026-07-08.md` (§1.2 half-landed conversion; §1.5 steelman; §1.6 iterative sketch; §2.4 structural catch).
- Code (Tier-0, this session, canonical HEAD `a1166b8d`): `corpus_index.py:574,641,656`; `retrieval.py:81,104,129,181,249,256,270,704-706,716-718,1402-1403`; `context_composer.py:59`; `rules_store.py:359`; `retrieval_telemetry.py:196,297`.
- North star: `docs/design/keep-pace-with-user.md`.
- Principles: `feedback_structural_enforcement_on_recurrence`, `feedback_no_anthropic_api_key`, `feedback_odd_no_non_objective_code`, `feedback_scope_descriptive_ac_ids`, `feedback_version_numbers_at_release_time`.

## §14 Method-decision register (populated at build time)

- D-Q.1 (§3 budget derivation) — owner ruling: **HYBRID** — both byte budgets derive as named fractions of `ADDITIONAL_CONTEXT_CAP` (the enforced structural ceiling); `INJECTION_CHAR_CAP = round(0.5 × 10000) = 5000`, `SITUATIONAL_RULE_CHAR_CAP = round(0.12 × 10000) = 1200` (both preserve sealed values exactly). ; SHA: `204b97cc`
- D-build.1 (corpus double de-count, RF-1) — BOTH corpus count gates removed: the SQL `candidate_limit` window (fetch-all-with-floor) AND `rest_out[:num_results]`; the corpus is the bounded rules store so unbounded-with-floor is cheap and leaves no count to name. SHA: `204b97cc`
- D-build.2 (episode + post-merge de-count) — episode fetch uses the generous named `EPISODE_CANDIDATE_WINDOW` (large store ⇒ fetch window with a written retirement trigger, not a set-determiner); post-merge `combined[:top_n]` bounded only by the raised backstop. SHA: `204b97cc`
- D-build.3 (`DEFAULT_TOP_N` retirement-triggered backstop) — raised to 50 (no-op on normal turns, byte budget cuts first); p@5 metric decoupled onto `P_AT_K_MEASUREMENT_WINDOW = 5` so the raise does not corrupt the measurement. SHA: `204b97cc`
- D-build.4 (`SITUATIONAL_RULE_CAP` drop + budget anchor) — `SITUATIONAL_RULE_CAP` raised to 50 (no-op backstop; a matched rule is never dropped by count); both byte budgets re-anchored per D-Q.1. SHA: `204b97cc`
- D-build.5 (structural catch: checklist + seeded rule + `authoring-plan` trigger) — cap-bias line in the plan-author (§7.6) + reviewer (§8.2 item 15) checklists; seeded `authoring-plan` situational rule + high-precision under-fire-biased `SITUATION_TRIGGERS` pattern pair. SHA: `204b97cc`

**Apply commit:** `eee91c2f` — **Seal commit:** `dba2211f` — baseline `3c24102c`.

## §15 Backwards-compat verification

- All existing keep-pace / retrieval tests pass; the S2 AC.RDP.*, S4 AC.RSR.*, FBM AC-FBM-*, decision-ledger AC.DLG.* suites unchanged.
- Reversibility: restoring the legacy count values (DEFAULT_TOP_N as set-determiner, SITUATIONAL_RULE_CAP=3) reproduces pre-cycle recall byte-for-byte (named-lever discipline).
- Pinned hard-floor (AC-FBM-W-2) + lone-sparse-episode rescue (AC-FBM-RN-2) preserved.

## §16 Halt-and-surface findings (plan-authoring)

- The §3 budget-derivation call is the owner-gated headline; recorded here, surfaced to the owner, NOT resolved by the plan-author (recommendation given).
- RF-1 (corpus double de-count) recorded as autonomous build guidance — no owner gate needed; the builder acts on it.
- Item 4 decomposition recorded as a plan-author call (F4/Lens 5) — two cycles under one plan-doc.

## Primitive check

No new Claude/Claude Code primitive introduced. The structural catch reuses the existing situational-rules store (`rules_store.py`) + situation-trigger seam (`retrieval.py SITUATION_TRIGGERS`) built in S4, and the existing plan-author/reviewer checklist docs — the correct existing altitude, not a new hook (a hook on numeric constants was rejected in the research §2.4 as un-greppable). Primitive check for the checklist: prose convention, no mechanism.
