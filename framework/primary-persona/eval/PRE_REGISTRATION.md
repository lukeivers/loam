# Pre-registration — memory supersession (validity intervals) + salience-tie-breaker probe

**Status:** PRE-REGISTERED. This document fixes the probe sets, the metric
definitions, what "better" means, the blind-judge protocol (Gate C), and the
reference-count tie-breaker verdict rule (Gate B) **before any scored run**.
Per plan §7 / AC.SUP.6 / AC.E2E.3 / AC.RCT.1 the commit that lands this file
(and the frozen probe JSONs beside it) MUST be a git ancestor of the first
scored-run commit in the ref graph (`feedback_published_state_only_from_git_refs`
— the ordering is the tamper-evidence, not this prose).

**Plan:** `docs/plans/memory-supersession-and-salience-eval.md` (RATIFIED FOR
BUILD, commit `d5af1303`). This document implements the plan's §4 + §8
anachronism-firewall requirement made structural, mirroring
`framework/deliberate-reasoning/experiment/PRE_REGISTRATION.md` (the AC.MGRL.4
precedent).

**HARD honest-boundary (non-negotiable, mirrors the MGRL pre-reg §0):** a NULL
result on Gate B (RCT) — a paired-bootstrap CI that straddles zero — is a VALID
and reported outcome. The drop rule below is pre-committed; re-interpreting a
straddling CI as "directionally positive, ship it" is the exact failure Gate B
exists to prevent (plan §8 trigger 4 / §10 honest-doubt 1). The same disposition
killed co-citation spread; its null is now load-bearing corpus.

---

## §1 The probe sets (FROZEN)

Three frozen probe sets live beside this file under `probes/` and are FROZEN by
this commit. Adding/removing items after the first scored run invalidates the
pre-registration.

### §1.1 `probes/sup_contradiction_triples.json` (Gate A — SUP)

A set of contradiction triples `(A, A', Q)` where:
- `A` — the STALE record (the fact that was later corrected).
- `A_prime` — the CURRENT record (the correction; supersedes `A`).
- `Q` — a natural-language query whose answer differs depending on whether the
  reader sees `A` (wrong) or `A'` (right).
- `valid_from_A` / `valid_to_A` — `A`'s validity interval (closed at `A'`'s
  creation). `valid_from_A_prime` — `A'`'s open interval start.
- `fact_type` ∈ {`decision_ruling`, `personal_fact`, `version_state_fact`,
  `config_fact`} — Gate A is architectural (n=1 per fact-type suffices; the set
  buys fact-type COVERAGE, not statistical power — plan D-PROBE.1).

The triples are GROUNDED in the four real supersession fact-types the ledger
actually carries (plan D-PROBE.1: decision rulings, personal facts,
version/state facts, config facts). The canonical real-corpus example: the
`owner-location-apple-valley-mn` ruling supersedes any earlier Lubbock-location
inference (a `personal_fact` supersession that actually happened, keep-pace
2026-06-10).

### §1.2 `probes/e2e_qa_over_memory.json` (Gate C — E2E)

A set of QA-over-memory items, each:
- `id` — stable id.
- `prompt` — a question the persona would answer FROM memory.
- `canonical_answer` — the ground-truth answer (string; normalized: trim +
  lowercase + collapse internal whitespace).
- `arm` ∈ {`contradiction`, `control`}. A `contradiction` item's correct answer
  depends on the supersession filter surfacing `A'` not `A`. A `control` item's
  answer does not depend on supersession at all (the no-regression arm).
- `stale_record` / `current_record` — the two records seeded into the store for
  the contradiction items; `control` items seed a single uncontested record.

### §1.3 `probes/rct_heldout_split.json` (Gate B — RCT)

The reference-count tie-breaker held-out evaluation set:
- `train` / `test` — a deterministic seed-split (the tie-breaker has NO learned
  parameters — it is hub-corrected IDF over typed edges — so the split exists
  for the git-ancestry-firewall discipline and to report test-arm-only results,
  never to tune).
- Each item: `q`, `relevant` (same-thread ground-truth set, session-UUID
  co-membership per the harness), and a `near_tie` flag (whether the BM25 floor
  leaves a near-tie this tie-breaker could re-order).

## §2 The metrics — what "better" means (FIXED)

### Gate A (SUP) — deterministic, no judge.
- **Currentness@1** = fraction of contradiction triples where the default
  current view ranks `A'` above `A` OR filters `A` out entirely. **Bar: 1.0,
  ZERO TOLERANCE** (plan §4 / AC.SUP.1). Any single `A`-over-`A'` is a HARD
  fail, not an "improved" pass.
- **History-reachable** = fraction of triples where the `as_of τ`
  (`t1 < τ < t2`) query returns `A`. **Bar: 1.0** (AC.SUP.2 — proves filtering
  ≠ deletion).
- **No-degradation** = regressions on the existing ~330-query session-thread
  set: a query correct pre-change that fails post-change. **Tolerance EXACTLY 0**
  (AC.SUP.4 — mirrors AC.MGRL.3).

### Gate C (E2E) — blind LLM judge.
- **Per-arm answer-correctness** = count of items the arm answered correctly,
  as scored by the blind judge (§4).
- **`gain_on_contradiction`** = (post-change correct − pre-change correct) over
  the `contradiction` items. **Bar: strictly > 0** (AC.E2E.1).
- **`gain_on_control`** = (post-change correct − pre-change correct) over the
  `control` items. **Bar: ≥ 0** (no regression on the control set — AC.E2E.1).

### Gate B (RCT) — paired bootstrap.
- **recall@10 / MRR / precision@10** delta (tie-breaker ON vs BM25 floor OFF),
  with a **paired BCa bootstrap CI (≥1000 resamples)** + **permutation test**
  (arXiv:2511.19794).
- **`gain_on_near_tie`** vs **`gain_on_non_near_tie`** — the concentration
  discriminator (AC.RCT.2; mirrors `gain_on_flagged` / `gain_on_unflagged`).

## §3 The RCT verdict rule (FIXED — load-bearing, pre-committed drop rule)

Applied without further judgment (AC.RCT verdict rule, mirroring the MGRL
PRE_REGISTRATION §3 discriminator):

- **EARNED** iff the paired BCa bootstrap **CI lower-bound > 0** AND
  **permutation p < 0.05** AND the lift is CONCENTRATED on the near-tie subset
  (`gain_on_near_tie > 0` while uniform-everywhere lift is absent —
  AC.RCT.2). The tie-breaker earns its place.
- **NOT-EARNED** otherwise (THE PREDICTED OUTCOME — plan §10 honest-doubt 1):
  CI straddles zero, OR p ≥ 0.05, OR the lift is uniform-not-concentrated.
  → **the tie-breaker DOES NOT SHIP.** It remains default-OFF (AC.RCT.4) and
  the result is recorded as a VALID NULL in the decision ledger (D-RCT.1) — a
  recorded negative with a real CI, never buried.

The committed core (SUP + E2E) ships whether or not RCT clears its bar — RCT is
a separable probe, not a promise (plan §3 / D-SCOPE.1).

## §4 The blind-judge protocol (Gate C, FIXED)

The judge scoring each E2E answer is **blind to the arm** (pre-change vs
post-change) **and to the hypothesis**: it receives only
`(prompt, answer, canonical_answer)` and returns `correct ∈ {0,1}`. It does NOT
receive the arm label, the supersession framing, or any hypothesis text — there
is no parameter through which the arm could enter (the blindness is structural,
mirroring AC.MGRL.5). The default reference judge is a deterministic exact-match
checker under the §2 normalizer (zero-token, reproducible); an LLM judge run
uses the `claude -p` subscription path (`feedback_no_anthropic_api_key`, NOT the
Anthropic SDK) with the IDENTICAL `(prompt, answer, canonical_answer)` signature.

## §5 The procedure (FIXED)

1. **Gate A:** for each contradiction triple, seed `A` then `A'` (the write-path
   closes `A`'s interval at `A'`'s creation), run the default current-view
   search → Currentness@1; run the `as_of` query → History-reachable; run the
   ~330-query set before/after → no-degradation.
2. **Gate C:** for each QA item, invoke the REAL retrieval+answer entry-point
   with NO pre-arranged index state (fresh workspace root), score with the blind
   judge, compute `gain_on_contradiction` + `gain_on_control`.
3. **Gate B:** run the held-out test arm with the tie-breaker default-OFF (floor)
   and ON, paired-bootstrap the deltas, apply the §3 verdict rule.

The first scored run's commit MUST be a DESCENDANT of this file's commit
(AC.SUP.6 / AC.E2E.3 / AC.RCT.1 git-ancestry evidence).

## §6 Degrees-of-freedom disclosures (RF-4)

- The probe-set authorship is a degree of freedom (RF-4). Disclosed here, frozen
  by this commit. The SUP triples are grounded in REAL corpus supersession
  fact-types (not synthetic), and the gold/control labels are human-assigned
  (plan §10 honest-doubt 3).
- Gate C's `claude -p` LLM judge is the softest link (plan §10 honest-doubt 2):
  the result reports effect size and treats Gate C's delta as
  directional-with-a-judge; a soft Gate C result never overrides a clean Gate A
  pass. The default reference judge is deterministic to remove that softness from
  the reproducible run.
- RCT has no learned parameters; the train/test split exists for the
  ancestry-firewall discipline and test-arm-only reporting, never to tune.
