# fbmt1-smoke-supersession-hard-exclude

## §1 Objective

Realign the FBM Tier-1 end-to-end smoke's supersession leg
(`test_AC_FBMT1_S_end_to_end_smoke.py` sub-test (b)) to assert the
CURRENT sealed supersession contract — the default current view
(`as_of=None`) HARD-EXCLUDES a `superseded-by`-marked episode (AC.SUP.1)
— instead of the retired pre-redesign "visible-but-ranked-lower"
expectation, which no code path has produced since the
memory-supersession cycle sealed.

## §2 Predecessors / context

Composes against, and corrects a lag introduced by, the
memory-supersession / volatility redesign:

- `docs/plans/sealed/memory-supersession-and-salience-eval.md`
  (commit `e0eff95e`) — promoted the `superseded-by`/`superseded-date`
  marker into a real bitemporal validity interval `[valid_from,
  valid_to)`; the DEFAULT view now FILTERS closed-interval (superseded)
  records out (AC.SUP.1), while an `as_of` query keeps history
  reachable (AC.SUP.2).
- `docs/plans/sealed/memory-volatility-classifier-read-disposition.md`
  (commit `779d306f`) — added the volatility close as an additive
  interval source on the same `_filter_by_interval` machinery.

The FBMT1 smoke was authored at amendment-134
(`097ce8f5`, 2026-06-12) against the ORIGINAL Tier-1 contract
(AC.FBMT1.SUPM.3: a `superseded-by`-marked file is DEMOTED via
`SUPERSEDED_PENALTY=0.1` but stays VISIBLE in the default view). The
redesign (2026-06-28) PROMOTED that demote-not-filter penalty into a
real filter and migrated the primary-persona suite accordingly
(`test_AC_FBMT1_SUPM_3_not_filtered.py` pins the reconciliation: the
annotate-not-delete property now lives on the `as_of` HISTORY view; the
DEFAULT view hard-excludes). The smoke's sub-test (b) was never
migrated — it still asserts the retired default-view-demote behavior and
therefore fails on clean HEAD.

## §3 Scope

**In scope:**
- Sub-test (b) of `test_AC_FBMT1_S_end_to_end_smoke.py`: re-point the
  three supersession assertions + the two describing comments (the file
  docstring line for (b) and the (b) section header) from
  "demoted-but-present" to "hard-excluded from the default current
  view."

**Out of scope:**
- Any production code change (the behavior under test is correct and
  sealed; only the stale test expectation moves).
- Sub-tests (a), (c), (d) of the same file — they pass unchanged.
- The `as_of` history-view demote assertion — already covered by
  `framework/primary-persona/tests/test_AC_FBMT1_SUPM_3_not_filtered.py`;
  duplicating it in the loam-amend smoke would widen the smoke's scope
  beyond the FBM T1 primitive it exercises.

## §4 Acceptance criteria

| AC | Outcome | Verification |
|----|---------|--------------|
| **AC.SMKSUP.1** | The FBMT1 end-to-end smoke's supersession sub-test asserts the current AC.SUP.1 contract: after a `superseded-by:` marker is written and the grep-fallback path fires (`as_of=None` default view), the UNSUPERSEDED episode is present in results AND the SUPERSEDED episode is ABSENT (hard-excluded, not merely ranked-lower). | `./.venv/bin/python -m pytest plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_S_end_to_end_smoke.py` passes; the assertion is `idx_first is not None and idx_second is None`. |

`AC.SMKSUP.1` ladders up to `AC.SUP.1` (default-view current-over-stale
hard-exclude), which ladders up to the prime objective's protection
floor (`docs/VALUE_PROPOSITION.md`: "a recent, stale operational-status
claim is not served as current in a later recall").

**Named contract asserted:** `AC.SUP.1` (canonical definition:
`docs/plans/sealed/memory-supersession-and-salience-eval.md`;
enforced by
`framework/primary-persona/tests/test_AC_SUP_1_default_view_filters_stale.py`,
passing on HEAD).

## §5 Sealed-component fence

Single component: `plugins/dev-sdlc/` (the smoke test lives at
`plugins/dev-sdlc/tools/loam-amend/tests/`, inside the dev-sdlc sealed
fence). Seal-test `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`;
sidecar `plugins/dev-sdlc/tests/SEAL_COMMIT`. No `extra_allowed_prefixes`
— the edit is confined to one file inside the fence. Universal paths:
`docs/plans/` + `docs/STATE.md`.

**Primitive check:** no new mechanism introduced (a test-expectation
correction; no runtime, hook, or scheduling primitive added).

## §6 Halt triggers

- If reproduction had shown the grep-fallback path excluding the
  superseded record while the FTS5 path KEPT it visible (an asymmetry
  between the two search paths), that would be a real regression, NOT a
  stale test — HALT and surface, do not edit the test. **Evaluated and
  cleared:** both `_fts_search` and `_grep_search` funnel through
  `_compose_score` → `_filter_by_interval`, so the hard-exclude is
  uniform across paths by construction; no asymmetry exists.
- If the seal's guard-sweep floor breaches for a reason unrelated to
  this edit — halt and surface.

## §7 Ship shape

Single amendment, single feature commit + apply + seal + §14 backfill.
Commit ladder: `fix(dev-sdlc): ...` (source), `chore(amend): ...`
(apply), `chore(seals): ...` (seal), `docs(plans): ...` (§14 backfill).

## §14 Method-decision register

- **D-SMKSUP.1 — stale-test-corrected-to-shipped-behavior (NOT
  papered-over regression).** The fork "stale test vs real regression"
  was resolved to STALE via: (1) the `search()` docstring + AC.SUP.1
  comment block in `file_memory.py` state the default view filters
  superseded records out by design; (2) two sealed commits (`e0eff95e`,
  `779d306f`) establish deliberate intent; (3) the canonical
  primary-persona SUP suite (`test_AC_SUP_1_...`, `..._SUP_2_...`,
  `test_AC_FBMT1_SUPM_3_not_filtered.py`) passes on HEAD asserting
  exactly this contract; (4) git timeline — the smoke's last touch
  (2026-06-12) predates the redesign (2026-06-28). Both search paths
  hard-exclude identically, ruling out a grep-vs-FTS regression.
  - Source SHA: `ae461621` (`fix(dev-sdlc): ...`)
  - Plan+manifest SHA: `a1adbef7` (`docs(plans): ...`)
  - Apply SHA: `53c73f16` (`chore(amend): ...`; dev-sdlc BASELINE + sidecar → `53c73f16`)
  - Seal SHA: `69a345ba` (`chore(seals): ...`)
  - BASELINE: `08da4e68`. `main` LOCAL only — sealed-local, NOT pushed.

## §15 Backwards-compat verification

- `test_AC_FBMT1_S_end_to_end_smoke.py` passes in full (all four
  sub-tests a/b/c/d).
- The canonical SUP contract tests remain green (unchanged by this
  amendment):
  `test_AC_SUP_1_default_view_filters_stale.py`,
  `test_AC_SUP_2_as_of_history_reachable.py`,
  `test_AC_FBMT1_SUPM_3_not_filtered.py`.
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` (the dev-sdlc
  seal-test) passes post-apply.

## §16 Halt-and-surface findings

Raised + ruled at plan-authoring:

- **The stale-vs-regression fork.** Ruled STALE (D-SMKSUP.1) on Tier-0
  code + sealed design docs + passing canonical suite + git timeline.
  The regression branch was specifically probed (grep-vs-FTS
  over-exclusion) and cleared by construction — both paths share
  `_compose_score` → `_filter_by_interval`.
- **No separate hidden gap (F2 check).** The demote-not-delete property
  the old SUPM.3 protected is not lost — it migrated to the `as_of`
  history view and is pinned by the primary-persona
  `test_AC_FBMT1_SUPM_3_not_filtered.py`. The smoke correctly does not
  re-test it (scope discipline).
