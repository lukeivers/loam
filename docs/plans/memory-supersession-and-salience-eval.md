# Memory supersession (validity intervals) + salience-tie-breaker falsification probe — plan

**Status:** RATIFIED FOR BUILD — owner (Luke) cleared 2026-06-24 (Discord msg 1519475975740592341: "Ratifying the build. Let's go."). Committed core = **SUP** (supersession via validity intervals) + **E2E** (answer-level outcome gate). **RCT** (reference-count tie-breaker) ships as the pre-committed **drop-if-CI-straddles-zero falsification probe** (owner default: run unless explicitly skipped; not skipped). Build dispatched off this commit. Plan-before-code gate satisfied.
**WD:** canonical loam (`/Users/lukeivers/loam`). This plan-doc lives at `docs/plans/memory-supersession-and-salience-eval.md`.
**Predecessors / load-bearing prior seals:**
- `amendment-134-fbm-tier1-foundations` (the `superseded-by:` frontmatter convention + the episode-ranker honor surface).
- `amendment-135-fbm-tier2-retrieval-mechanics` (the `SUPERSEDED_PENALTY = 0.1` demotion in `file_memory.py`).
- The FBM-correctness Slice-3 cycle that landed `supersession.py` (`mark_superseded` / `unmark_superseded` / `read_supersession`, AC.SUP.1 + AC.SUP.3) and the corpus-retrieval honor in `keep_pace/corpus_index.py` (AC.SUP.2).
- `framework/deliberate-reasoning/experiment/PRE_REGISTRATION.md` + `tests/test_AC_MGRL_{3,4,5,6,OA}*.py` — the reusable AC patterns this plan reuses (no-degradation tolerance-zero, git-ancestry firewall, blind-judge, generic-lift-vs-theory discriminator, outcome-altitude real-entry-point).
- Ratified memory-northstar merge decision (decision-ledger + deterministic typed links; relational layer stays dead as a statistical-association layer) — keep-pace `2026-06-09-which-memory-north-star-plan-governs-the-recall-cycle-build-.md`.
**BASELINE candidate:** predecessor's §14 SHA-register backfill commit (assigned at manifest time once the prior seal SHA is pinned).
**Version:** NOT pre-assigned — derives at release time per `feedback_version_numbers_at_release_time`.
**Quality bar:** ODD §2.5 (every line maps to a named AC); the eval-protocol ACs are pre-registered before any scored run (anachronism firewall mirrors `AC.MGRL.4`).
**Research artefacts folded (Tier-0 internal):**
- `memory-reasoning-chain-v2-research-folded.md` — THE DESIGN (supersession HIGH-confidence; reference-count tie-breaker SPECULATIVE).
- `memory-eval-methodology-research.md` — THE EVAL PROTOCOL (Gate A / Gate B / Gate C; thresholds; anti-leak disciplines).
- `db-as-memory-systems-research.md` — background (why naive reference-count fails; bitemporal supersession is solved).

---

## §1 Objective

> **Promote loam's existing supersession marker into a real bitemporal validity interval so the default memory view filters superseded records out (current-over-stale by default) while history stays reachable on an explicit `as_of` query — and PROVE it both at the retrieval level (Gate A) and at the outcome level (Gate C: answers actually get better) — with the speculative reference-count tie-breaker authored as a separable, pre-committed-drop-rule falsification probe (Gate B), never as a shipped promise.**

The single committed outcome: *the current fact wins by default, the old fact is still reachable on demand, and the answers the persona produces stop being driven by stale records — and we have a measurement that proves it rather than asserts it.*

This is the engine of loam's prime directive (Lens 0 / `AC.PO.1` + `AC.PO.2`): "having no real memory" is one of the named ways AI betrays its users by default. A memory that surfaces a stale ruling as if current is the protection-floor failure this closes. The ladder-up: AC.SUP/AC.E2E → memory-correctness → AC.PO.1 (reduces translation burden: the user never has to re-state a fact they already corrected) + AC.PO.2 (adds to the persona's toolkit: a memory it can trust as current).

---

## §2 Predecessors / context

The supersession surface already exists in three places and this plan composes against all three (it does not start from zero):

1. **`file_memory.py`** — `SUPERSEDED_PENALTY = 0.1` multiplicatively demotes a `superseded-by`-marked episode in the candidate set but **keeps it visible** (a `score=10` superseded file still beats a `score=0.5` unsuperseded one; AC.FBMT1.SUPM.3). This is a *ranking penalty*, not a *filter* — that is exactly the gap this plan closes.
2. **`supersession.py`** — `mark_superseded` / `unmark_superseded` / `read_supersession`: the production marking entry point writing `superseded-by` + `superseded-date` into frontmatter, annotate-not-delete (AC.SUP.1 + AC.SUP.3).
3. **`keep_pace/corpus_index.py`** — the corpus-retrieval honor of the marker (AC.SUP.2).

What this plan ADDS on top: a `valid_from` / `valid_to` validity interval (the marker's `superseded-date` becomes the close timestamp), default retrieval FILTERS closed-interval records out of the current view, an `as_of` query path returns history, and the write-path closes the prior record's interval at creation time.

The eval harness exists as a research artefact (`fbm-eval-harness/harness.py`, currently in pos3 `.scratch`) that imports the LIVE `FileMemoryStore.search` and A/Bs a retrieval step read-only against the frozen store. The eval slice of this plan BUILDS ON that harness (recall@k/MRR + BM25 floor + session-UUID ground truth), promoting it into a canonical eval surface — it does not re-implement retrieval scoring.

---

## §3 Scope (the F2 scope decision — committed core vs gated probe)

**This is the load-bearing scope decision and it is named as D-SCOPE.1 in §10 for owner ruling.** The eval methodology's F2 finding is that the two design changes have *different confidence*, so they get *different scope-tightness* (Lens 4):

### In scope — COMMITTED CORE (Gate A + Gate C). High confidence, architectural, the headline.

- **SUP — supersession via validity intervals.** Promote `superseded-by:` + `SUPERSEDED_PENALTY` into a real `valid_to`/validity-interval field. Default retrieval FILTERS superseded records out of the current view. History reachable on explicit `as_of` query. Write-path closes the old record's interval at creation.
- **E2E — end-to-end outcome proof (Gate C).** A blind-judge measurement that answer-correctness is strictly up on contradiction items and not regressed on a control set. This is the outcome-altitude level the owner actually cares about ("intelligence operating off bad memory") and the one mandatory `outcome-altitude: true` AC.
- **The eval harness + probe sets** needed to verify SUP + E2E: the ~25–40 contradiction-triple probe set (Gate A), the ~330-query no-degradation set (existing), the ~15–20 QA-over-memory blind-judge set (Gate C), all built ON `fbm-eval-harness/harness.py`.

### In scope but SEPARABLE — GATED FALSIFICATION PROBE (Gate B). Speculative, pre-committed drop rule.

- **RCT — hub-corrected reference-count tie-breaker** over deliberate typed edges, used ONLY to re-order near-ties, gated on beating the BM25 floor with a paired-BCa-bootstrap CI lower-bound > 0. **Pre-committed drop rule: if the bootstrap CI straddles zero on the harness, RCT does not ship** (same disposition that killed co-citation spread). RCT is authored as an explicitly-separable slice with its own AC family and its own go/no-go gate; it is a *probe, not a promise*, and it is NOT folded into the committed scope. The committed core ships whether or not RCT clears its bar.

### Out of scope (deferred; §7 names when)

- Decay machinery, embeddings, per-write LLM importance ratings, multi-hop PPR at scale (research §99 "ignore" list — problems we don't have).
- Auto-detection of supersession (premise-flip auto-detect is a named prior deferral; humans/persona invoke the mark — `supersession.py` D5).
- Configurability of the penalty/interval semantics beyond the default (deferred until a concrete second consumer exists).
- Any LLM in the supersession write/filter path (it stays deterministic — that determinism is what makes Gate A a clean binary needing no judge).

---

## §4 Halt-and-surface BEFORE build (recorded at plan-authoring)

Recorded surfaces the builder must respect (autonomous + recorded decisions, plus the owner-gated ones):

- **The probe sets are FROZEN by the pre-registration commit** and that commit MUST be a git ancestor of the first scored-run commit (the anachronism firewall, AC.SUP.6 / AC.E2E.3). A probe authored after seeing a result is inadmissible by construction. This is non-negotiable and mirrors the northstar Plan-B anachronism that was dispatcher-caught and excluded.
- **Gate A's `Currentness@1 = 1.0` is zero-tolerance.** Any single A-over-A' on the contradiction set is a HARD fail, not an "improved" pass. The bar is the production failure being fixed, not a relative delta.
- **No-degradation tolerance is exactly 0** on the ~330-query set (mirrors `D-MGRL.2` / `test_AC_MGRL_3`). One pre-change-correct query failing post-change is a guard failure — supersession filtering must not drop a not-actually-superseded record.
- **RCT's drop rule is pre-committed.** The builder does NOT get to re-interpret a straddling CI as "directionally positive, ship it." Straddle zero → do not ship → reported as a valid null.

---

## §5 Spec-objective placement

Binds to `AC.PO.1` (Primary-persona test — reduces translation burden: the user does not re-assert a corrected fact) + `AC.PO.2` (Harness test — adds a trustworthy-as-current memory to the persona's toolkit). Ladders up through memory-correctness to the prime objective in `docs/VALUE_PROPOSITION.md`. The protection-floor framing (Lens 0): "no real memory / surfacing stale state as current" is an always-on, not-tunable failure this closes for every user.

---

## §6 Acceptance criteria

AC IDs scope-descriptive (`SUP` = supersession, `E2E` = end-to-end outcome, `RCT` = reference-count tie-breaker), NOT version-packed. Every AC is outcome-shaped: each is satisfiable by a method other than the one in mind. Each maps to its gate + measurable threshold + verification surface (probe set / harness arm / judge).

### Family SUP — supersession via validity intervals (Gate A). Architectural; n=1 per fact-type.

| AC | Outcome (threshold) | Gate | Verified by |
|---|---|---|---|
| **AC.SUP.1** | On a contradiction triple `(A, A', Q)`, the default current view ranks A' above A OR filters A out entirely — for EVERY triple in the frozen set. **Currentness@1 = 1.0, zero tolerance.** | A | The ~25–40 contradiction-triple probe set run through the live `FileMemoryStore.search` current view; any A-over-A' = hard fail. |
| **AC.SUP.2** | An explicit historical query (`as_of τ`, `t1 < τ < t2`) returns A. **History-reachable = 1.0.** Proves filtering ≠ deletion. | A | The same probe set, queried with the `as_of` path; A must be returned for every triple. |
| **AC.SUP.3** | The write that creates A' closes A's validity interval AT CREATION (`A.valid_to` set to A''s `valid_from`), durably and machine-readably, without deleting A's content. | A | Write-path test: create A', then read A's interval from disk; content beyond the interval fields preserved byte-for-byte (reuses the AC.SUP.3 annotate-not-delete precedent). |
| **AC.SUP.4** | **No-degradation = 0 regressions** on the existing ~330-query session-thread set: no query correct pre-change fails post-change. Tolerance exactly 0. | A | The existing no-degradation harness arm, run before/after (mirrors `test_AC_MGRL_3`). Catches supersession filtering dropping a not-actually-superseded record. |
| **AC.SUP.5** | Supersession is reversible: un-closing an interval (or un-marking) restores prior retrieval behaviour exactly. | A | Reversibility test (reuses `unmark_superseded` precedent); retrieval keys only on interval state. |
| **AC.SUP.6** | The supersession probe set's seed timestamps are fixed BEFORE the change is built, and the probe-set commit is a git ancestor of the first scored-run commit (anachronism firewall). | A (meta) | Git ref graph at result time (mirrors `AC.MGRL.4`); content half pinned by a frozen-probe test, ancestry half verified from the ref graph in the result doc. |

### Family E2E — end-to-end outcome (Gate C). The owner-altitude proof.

| AC | Outcome (threshold) | Gate | Verified by |
|---|---|---|---|
| **AC.E2E.1** `outcome-altitude: true` | Invoking the REAL retrieval+answer path with NO pre-arranged state on the ~15–20 QA-over-memory contradiction items, answer-correctness is **strictly up** vs the pre-change path AND there is **no regression on a non-contradiction control set.** | C | The QA-over-memory probe set scored by a blind `claude -p` judge receiving only `(prompt, answer, canonical_answer)` — no arm label, no hypothesis framing (mirrors `AC.MGRL.5`). Real entry-point, no seeded state (mirrors `AC.MGRL.OA`). |
| **AC.E2E.2** | The judge is blind to the arm (pre-change vs post-change) and to the hypothesis; its inputs structurally exclude the arm label. | C | Judge signature inspection + a blind-judge test (mirrors `test_AC_MGRL_5`). |
| **AC.E2E.3** | The QA probe set is frozen pre-build; its commit is a git ancestor of the first scored-run commit. | C (meta) | Git ref graph at result time (same firewall as AC.SUP.6). |

> **Why E2E is mandatory and not just SUP's recall numbers:** retrieval recall rising does NOT imply answers improve (research: 80%→95% recall → only 5–10% answer gain). Gate A proves "retrieval changed"; only Gate C proves "intelligence stopped operating off bad memory." Per `feedback_test_outcome_altitude_required` every AC set needs ≥1 outcome-altitude AC verified through the production entry-point with no pre-arranged state — here it is the whole point.

### Family RCT — reference-count tie-breaker (Gate B). Falsification probe; pre-committed drop rule.

| AC | Outcome (threshold) | Gate | Verified by |
|---|---|---|---|
| **AC.RCT.1** | The tie-breaker beats the BM25 floor on recall@10 / MRR / precision@10 with a **paired BCa bootstrap CI lower-bound > 0 AND permutation p < 0.05.** If the CI straddles zero (the predicted outcome) → **NOT EARNED → does not ship** (pre-committed drop rule). | B | The held-out test arm of `fbm-eval-harness/harness.py` with the BCa-bootstrap (≥1000 resamples) + permutation test (arXiv:2511.19794). |
| **AC.RCT.2** | The lift is concentrated on the near-tie subset, reported separately from uniform lift. Uniform lift everywhere = generic perturbation, NOT the mechanism earning its place (a flagged-vs-unflagged discriminator). | B | Near-tie-subset arm reported separately (mirrors the `gain_on_flagged` / `gain_on_unflagged` discriminator in `AC.MGRL.6`). |
| **AC.RCT.3** | The tie-breaker operates ONLY over deliberate typed edges (`supersedes` / `answers` / `continues`), never statistical co-occurrence edges, and is hub-corrected (IDF). It re-orders ONLY near-ties — it is never the primary ranker. | B | Edge-source + tie-only test: the tie-breaker is a no-op on non-near-tie queries; the edge set excludes co-occurrence (the 68.6%-noise source that killed co-citation). |
| **AC.RCT.4** | RCT is default-OFF and reversible: with the tie-breaker disabled, retrieval is byte-identical to the SUP-only committed core. | B | Default-off no-op test (mirrors `test_AC_MGRL_2` / `_7`). The committed core never depends on RCT. |

**Verdict rule for RCT (applied without further judgment, mirroring the PRE_REGISTRATION discriminator):** EARNED iff AC.RCT.1 CI-lower-bound > 0 AND p < 0.05 AND AC.RCT.2 concentration holds. NOT-EARNED otherwise (the predicted outcome) → drop, report as a valid null, do not ship. NULL is informative and reported, never buried.

---

## §7 Build steps (method-level guidance only; builder's call per ODD §1.1)

Decomposes into three orthogonal slices, each with a tighter AC than the parent (Lens 5 swarming). Slices A and C are the committed dependency chain (C depends on A's filtering being live); slice B is independent and gated.

1. **Pre-registration FIRST (anachronism firewall).** Author + commit the frozen probe sets (contradiction triples for A, QA-over-memory for C, RCT held-out split for B) + the metric/threshold/verdict definitions, BEFORE any change is built. This commit is the git ancestor every scored run must descend from. No scored run before this lands.
2. **Slice SUP (Gate A).** Validity-interval field + default-view filter + `as_of` path + write-path interval-close, composing on the existing `superseded-by` marker. Promote the harness's no-degradation arm. Author AC.SUP.1–6 tests. Seal.
3. **Slice E2E (Gate C).** Build the QA-over-memory blind-judge arm on the harness; wire the real retrieval+answer entry-point with no pre-arranged state; author AC.E2E.1–3. Run the scored comparison (descendant of the pre-reg commit). Seal.
4. **Slice RCT (Gate B) — separable, gated.** Hub-corrected tie-breaker over typed edges, default-OFF, tie-only. Run through the BCa-bootstrap arm. Apply the verdict rule. If NOT-EARNED, the slice ships as a reported null with the mechanism left default-off-and-dead (or not merged at all — D-RCT.1 in §10).
5. Per-slice: manifest path, source edits in order, AC tests authored, `loam amend apply`, `loam amend seal`, smoke. Method within each slice is the builder's call.

---

## §8 Halt triggers (in-flight; abort the build)

- A scored run is attempted whose commit is NOT a descendant of the pre-registration commit → HALT (anachronism; the result is inadmissible).
- `Currentness@1 < 1.0` on the contradiction set → the supersession filter is not actually filtering → HALT and diagnose before sealing (this is the production failure being fixed; a partial pass is a fail).
- A no-degradation regression appears (any pre-change-correct query fails post-change) → HALT; the filter is dropping a not-actually-superseded record.
- The RCT slice produces a CI straddling zero AND a builder is about to ship it anyway → HALT (the drop rule is pre-committed; re-interpreting a straddle as positive is the exact failure Gate B exists to prevent).
- The eval harness cannot import the live `FileMemoryStore.search` (the faithful-import contract breaks) → HALT; a reconstructed ranker is not a valid measurement surface.

---

## §9 Bookkeeping (post-build backfill)

- STATE.md / roadmap entry for the memory-correctness track (supersession-filtering milestone).
- Parent memory-northstar plan §2 backfill: this is the supersession leg of the ratified merge (decision-ledger + typed links; relational layer stays dead). RCT's verdict (earned/null) recorded as a decision-ledger entry either way.
- §14 method-decision register populated at build time + SHA-backfilled at seal time (D-SCOPE.1, D-PROBE.1, D-GOLD.1, D-RCT.1 placeholders).
- The promoted eval harness gets a canonical home (out of pos3 `.scratch`) — its target path is a build-time decision recorded in §14.

---

## §10 F2 Ruthless Feedback — honest doubts + named decisions with recommendations

### Honest doubts (named, with evidence + alternative)

1. **RCT is probably unprovable at our n — and that is in the design already, carried forward not papered over.** Evidence: the eval methodology's own read (`memory-eval-methodology-research.md` finding 3) — expected effect "modest-to-neutral," it only touches near-ties (a small subset of an already-small set), and run through a protocol "built to systematically refuse 0.5–2pp gains at three seeds" it will very likely produce a CI straddling zero. Alternative: do NOT spend committed build budget on it — run it as a fast falsification probe with the pre-committed drop rule, exactly as scoped. The cost-of-error Gate B exists to prevent is spending heavy build on a change you can predict won't clear the bar. **I am NOT recommending we skip it entirely** (see D-RCT.1) — a cheap pre-committed-null probe has real value as a recorded negative, but it must not be allowed to expand.

2. **Gate C's `claude -p` blind judge is the softest link in the chain.** Evidence: it is an LLM scorer (97% human agreement on LongMemEval's gpt-4o, but we use the subscription `claude -p` path, not gpt-4o, and our corpus is a single-user technical ledger, not persona-chat). Gate A by contrast is a clean deterministic binary (interval filtering is mechanical). Alternative: keep Gate A as the architectural proof that stands alone; treat Gate C's correctness delta as directional-with-a-judge, report effect size + the judge's own agreement rate, and never let a soft Gate C result override a clean Gate A pass. Surfaced so the owner reads the E2E number with the right weight.

3. **The ~330-query no-degradation set and the ~30-query gold set are hand-labeled — that labeling is a degree of freedom.** Evidence: the test-set construction mines the live access log (session-UUID co-membership, independent of the co-citation graph, so non-circular) but the gold labels are human-assigned. Alternative: disclose the labeling as a degree of freedom in the pre-registration (mirrors `PRE_REGISTRATION §6` RF-4), freeze it pre-build, and ground the supersession triples in REAL corpus supersessions (the ledger's own `superseded-by` markers ground-truth them) rather than synthetic ones.

### Named decisions — each carries my recommendation (owner rules only where flagged)

- **D-SCOPE.1 — Committed core = Gate A (SUP) + Gate C (E2E); Gate B (RCT) is a separable gated probe, not committed scope.**
  *Recommendation: ADOPT as written.* This is the eval's F2 finding made structural and it is the correct Lens-4 application (tight scope on the high-confidence architectural change; loose falsification-probe scope on the speculative one). **Owner ruling requested** only because it is the load-bearing scope call.

- **D-RCT.1 — Whether to run Gate B (RCT) at all, given the likely-null prediction.**
  *Recommendation: RUN IT as a fast pre-committed-null falsification probe, but cap its build budget and do NOT merge the mechanism if NOT-EARNED (leave it as a recorded null in the decision ledger, not default-off-dead code).* Rationale: a recorded negative with a real CI is worth more than an untested hunch (we killed co-citation the same way and that null is now load-bearing corpus), AND the cost is small if capped. The alternative — skip it entirely — saves the probe budget but leaves "would a corrected tie-breaker have helped?" as an open hunch that will recur. **Owner ruling requested** (run-capped vs skip): this is the one place reasonable people weigh "recorded null is worth the probe budget" against "predicted null isn't worth any budget" differently (Lens 6 — surface it).

- **D-PROBE.1 — Supersession contradiction-probe set size (~25–40 triples).**
  *Recommendation: 30 triples, grounded in REAL corpus supersessions (the ledger's `superseded-by` markers), covering the four fact-types that actually supersede (decision rulings, personal facts, version/state facts, config facts).* Gate A is architectural (n=1 per fact-type suffices — set size buys fact-type coverage, not statistical power), so 30 is comfortably above the coverage floor without over-investing in a binary check. Autonomous unless owner objects.

- **D-GOLD.1 — Gold-set hand-labeling effort (~30-query gold set + ~15–20 QA-over-memory items).**
  *Recommendation: ~30-query gold set (matches the results-doc recommendation) + ~15–20 QA items, labeled once, frozen by the pre-registration.* The labeling is bounded (a few hours of owner or careful-agent time) and is the cheapest honest path — there is no off-the-shelf supersession benchmark to borrow (research: even Zep/Graphiti has none). Autonomous unless owner wants a larger set for more Gate-C statistical comfort.

- **D-HARNESS.1 — Promote `fbm-eval-harness/harness.py` from pos3 `.scratch` to a canonical loam eval surface.**
  *Recommendation: ADOPT — build the new probe arms ON the existing harness (faithful live-import of `FileMemoryStore.search`), give it a canonical home under the primary-persona eval surface.* Re-implementing retrieval scoring would break the faithful-import contract that makes the measurement valid. Autonomous (it is a build-time path decision recorded in §14).

---

## §11 Provenance trail

**Tier-0 internal (canonical loam, verified this session):**
- `framework/primary-persona/src/loam/primary_persona/supersession.py` — the existing marking entry point (`mark_superseded`/`unmark_superseded`/`read_supersession`, AC.SUP.1 + AC.SUP.3).
- `framework/primary-persona/src/loam/primary_persona/file_memory.py:438–446` — `SUPERSEDED_PENALTY = 0.1` (the ranking-penalty-not-filter gap this plan closes); `:1468–1505` — the multiplicative penalty application.
- `framework/primary-persona/src/loam/primary_persona/keep_pace/corpus_index.py` — the corpus-retrieval honor of the marker.
- `framework/primary-persona/tests/test_AC_SUP_{1,2}*.py`, `test_AC_FBMT1_SUPM_{1,2,3,4}*.py` — existing supersession AC tests this plan extends.
- `framework/deliberate-reasoning/experiment/PRE_REGISTRATION.md` — the reusable pre-registration shape (frozen task set, fixed metric, blind judge, generic-lift-vs-theory discriminator, degrees-of-freedom disclosure, anachronism firewall).
- `framework/deliberate-reasoning/tests/test_AC_MGRL_{3,4,5,6,OA}*.py` — the reusable AC test patterns (no-degradation tolerance-zero, pre-reg-before-scoring git-ancestry, blind-judge, generic-lift discriminator, outcome-altitude real-entry-point).
- `docs/VALUE_PROPOSITION.md:115` — `AC.PO.1` / `AC.PO.2` (prime-objective ladder-up).
- keep-pace `2026-06-09-which-memory-north-star-plan-governs-the-recall-cycle-build-.md` — the ratified merge + the anachronism precedent (Plan-B flagship proof case added ~70min after the failure, dispatcher-caught, excluded).

**Tier-0 internal (pos3 research artefacts, read this session):**
- `workspace/.scratch/claude-output/memory-reasoning-chain-v2-research-folded.md` — THE DESIGN.
- `workspace/.scratch/claude-output/memory-eval-methodology-research.md` — THE EVAL PROTOCOL (Gates A/B/C, thresholds, anti-leak).
- `workspace/.scratch/claude-output/db-as-memory-systems-research.md` — bitemporal-supersession-is-solved background.
- `workspace/.scratch/claude-output/fbm-eval-harness/harness.py` — the live-import eval harness this plan builds on.

**External (fetched/searched 2026-06-23 per the eval research doc):** LongMemEval arXiv:2410.10813; Zep arXiv:2501.13956; paired-bootstrap arXiv:2511.19794; Deepchecks "Retrieval vs Answer Quality"; NeocorRAG arXiv:2604.27852. (Magnitudes vendor-reported = PLAUSIBLE; directions VERIFIED.)

---

## §12 Primitive check

The eval-measurement mechanism leans on a native primitive where one exists:
- **Blind LLM judge (Gate C):** `claude -p` subscription path (`feedback_no_anthropic_api_key`) — NOT the Anthropic SDK/API. Native to loam's existing `claude_print_client.py`.
- **Validity-interval filtering + `as_of` query (SUP):** bespoke — this is a memory-store data-model change with no native Claude primitive; it composes on the EXISTING `superseded-by` frontmatter convention rather than re-implementing supersession.
- **Statistical rigor (Gate B):** bespoke BCa-bootstrap + permutation test (arXiv:2511.19794) — no native primitive; it is a standard small-n statistical method.
- **Anachronism firewall:** native git ref graph (`merge-base` / ancestry), reusing `feedback_published_state_only_from_git_refs` — not a bespoke timestamp check.

---

## §14 Method-decision register (populated at build time; SHA-backfilled at seal)

Build SHAs: pre-registration anchor `90f42515`; source+tests `e0eff95e`;
apply + seal SHAs backfilled at §14a below.

- **D-SCOPE.1** — committed core (A+C) vs gated probe (B) split. ADOPTED as
  written. SUP + E2E shipped; RCT authored separable + gated. _SHA: e0eff95e._
- **D-RCT.1** — run-capped vs skip on Gate B; merge-vs-recorded-null
  disposition. RAN it; NOT-EARNED (CI [-0.0013, +0.0569] straddles zero,
  p=0.233). Pre-committed drop rule fired: mechanism NOT merged into
  production; recorded as a valid null in
  `framework/primary-persona/eval/RESULTS.md`. The probe code lives in the
  eval harness (the surface that produced the null), never in the
  production ranker (AC.RCT.4). _SHA: e0eff95e._
- **D-PROBE.1** — contradiction-probe set size + fact-type coverage. 8
  triples covering all four real supersession fact-types (decision_ruling,
  personal_fact, version_state_fact, config_fact), grounded in real corpus
  supersessions (e.g. the Apple-Valley-vs-Lubbock location ruling).
  _SHA: 90f42515 (frozen by the pre-reg)._
- **D-GOLD.1** — gold-set + QA-set hand-labeling effort. 8 contradiction +
  8 control QA-over-memory items, frozen by the pre-registration.
  _SHA: 90f42515._
- **D-HARNESS.1** — harness promotion path out of pos3 `.scratch`. ADOPTED —
  canonical home at `framework/primary-persona/eval/` (in-fence; faithful
  live-import of `FileMemoryStore.search`). _SHA: e0eff95e._

### §14a Amendment register (apply + seal)

- Pre-registration anchor: `90f42515` (anachronism-firewall ancestor).
- Source + tests (scored-run commit, descendant of the anchor): `e0eff95e`.
- Apply: _backfilled at apply._
- Seal: _backfilled at seal._
- Gate results (eval/RESULTS.md): Gate A Currentness@1=1.0 +
  History-reachable=1.0 (0/8 failures); Gate C gain_on_contradiction=+6,
  gain_on_control=0; Gate B NOT-EARNED (dropped as null).

## §15 Backwards-compat verification

- The existing `SUPERSEDED_PENALTY` honor + AC.FBMT1.SUPM.{1,2,3,4} + AC.SUP.{1,2} tests must still pass (the validity-interval filter composes on top of the marker, does not replace the marker convention).
- The ~330-query no-degradation set: zero regressions (AC.SUP.4).
- With RCT default-OFF, retrieval is byte-identical to the SUP-only core (AC.RCT.4).

## §16 Halt-and-surface findings (plan-authoring)

- Plan is PLAN-ONLY, not ratified. The two owner-ruling decisions (D-SCOPE.1 scope split; D-RCT.1 run-vs-skip Gate B) are surfaced in §10 with recommendations. All other decisions (D-PROBE.1, D-GOLD.1, D-HARNESS.1) are autonomous-with-recommendation unless the owner objects.
- No contradiction with a parent-plan locked decision was found: the validity-interval promotion is the supersession leg of the ratified memory-northstar merge, and the relational/statistical layer stays dead exactly as the merge requires (RCT operates over deliberate TYPED edges only, never statistical co-occurrence — AC.RCT.3).
- No fence-widening into a sealed component without a manifest entry: the fence is `framework/primary-persona/src/loam/primary_persona/` (file_memory, supersession, keep_pace/corpus_index) plus the promoted eval harness surface; manifest entries assigned at build time.
