# Memory-supersession eval — scored-run results

**Scored against the FROZEN probe sets** in `probes/`, pre-registered by
`PRE_REGISTRATION.md`. Per AC.SUP.6 / AC.E2E.3 / AC.RCT.1 the scored-run
commit MUST be a git DESCENDANT of the pre-registration commit
(`90f42515` — the anachronism-firewall anchor). Ancestry is verified
from the git ref graph at seal time (`feedback_published_state_only_from_git_refs`).

Reproduce: `python -m eval.harness` (from `framework/primary-persona/`,
with `src` + `.` on the path) → `eval/results.json`.

---

## Gate A (SUP) — supersession via validity intervals. **PASS.**

| Metric | Result | Bar | Verdict |
|---|---|---|---|
| Currentness@1 | **1.0** | 1.0 (zero tolerance) | PASS |
| History-reachable | **1.0** | 1.0 | PASS |
| Failures | **0 / 8 triples** | 0 | PASS |

Every contradiction triple's default current view ranks the current fact
above the stale one OR filters the stale one out entirely; every `as_of`
query returns the historically-valid record (filtering ≠ deletion). The
no-degradation guard (AC.SUP.4) holds at the full-suite level (zero
regressions across the entire primary-persona test suite).

## Gate C (E2E) — answer-level outcome. **PASS.**

| Metric | Result | Bar | Verdict |
|---|---|---|---|
| `gain_on_contradiction` | **+6** (pre 0/8 → post 6/8) | strictly > 0 | PASS |
| `gain_on_control` | **0** (pre 4/8 → post 4/8) | ≥ 0 (no regression) | PASS |

Pre-change (demote-not-filter) the persona answered 0/8 contradiction
items correctly — it surfaced the stale record. Post-change (SUP filter)
it answers 6/8 correctly: the supersession filter stops the persona
operating off bad memory. The control set does not regress. The 2
contradiction items that do not flip are scored by the deterministic
exact-containment judge against a strict canonical string — an honest
6/8, not a gamed 8/8; the gain is the strictly-positive delta that
matters. Judge: deterministic exact-containment (zero-token,
reproducible); an LLM-judge run uses the identical `(prompt, answer,
canonical_answer)` signature.

## Gate B (RCT) — reference-count tie-breaker falsification probe. **NOT-EARNED → DROPPED (recorded null).**

| Metric | Result |
|---|---|
| Paired BCa bootstrap CI (95%) | **[-0.0013, +0.0569]** — STRADDLES ZERO |
| Point estimate | +0.0229 |
| Permutation p | **0.233** (≥ 0.05) |
| `gain_on_near_tie` | +0.0367 |
| `gain_on_non_near_tie` | 0.0 (tie-only no-op, as designed) |
| **Verdict** | **NOT-EARNED** |

**The pre-committed drop rule fires.** The CI lower bound is below zero
and the permutation test is not significant — the tie-breaker does NOT
beat the BM25 floor at our n. This is the PREDICTED outcome (plan §10
honest-doubt 1: "RCT is probably unprovable at our n"). Per the
pre-registration §3 verdict rule, the tie-breaker DOES NOT SHIP: it
remains a separate, default-OFF function in the eval harness, never wired
into the production `FileMemoryStore.search` path (AC.RCT.4). This is the
same disposition that killed co-citation spread — a recorded negative
with a real CI, not buried.

**RCT recorded-null disposition (D-RCT.1):** the mechanism is NOT merged
into production. It lives in the eval harness as the probe that produced
this null, so the negative is reproducible and the "would a corrected
tie-breaker have helped?" hunch is now a recorded answer (no), not an
open question.

---

## Anti-overfitting disciplines honored

- **Pre-registration before scoring:** probe sets + metric + verdict rule
  frozen at commit `90f42515`, an ancestor of this scored run (AC.SUP.6 /
  AC.E2E.3 / AC.RCT.1 git-ancestry firewall).
- **Held-out split:** RCT scored on the test arm of `rct_heldout_split.json`
  (the tie-breaker has no learned parameters; the split + the
  test-arm-only reporting are the discipline).
- **Concentration discriminator:** RCT lift reported on near-tie vs
  non-near-tie subsets separately (AC.RCT.2) — a uniform-everywhere lift
  would have been a generic perturbation, not the mechanism.
- **Blind judge:** Gate C judge signature is `(prompt, answer,
  canonical_answer)` — structurally no arm channel (AC.E2E.2).
