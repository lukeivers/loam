# FBMT1 end-to-end smoke — supersession leg realigned to AC.SUP.1 hard-exclude

Per `docs/plans/fbmt1-smoke-supersession-hard-exclude.md`. Single-component
amendment on the EXISTING `plugins/dev-sdlc/` component; advances the sidecar.
Composes on the SEALED memory-supersession validity-interval machinery
(`e0eff95e`, AC.SUP.1/2/3) + the volatility read-disposition (`779d306f`).

## The fork, resolved

A pre-existing failure on clean HEAD: `test_AC_FBMT1_S_end_to_end_smoke.py`
sub-test (b) asserts a `superseded-by`-marked episode is present-but-
ranked-lower in grep-fallback results; the current path returns the
unsuperseded episode and EXCLUDES the superseded one (`idx_second is None`).
Resolved to STALE TEST (not a papered-over regression) on four independent
signals:

  1. Tier-0 code intent. `file_memory.py`'s `search()` docstring +
     the AC.SUP.1 comment block state the default view (`as_of=None`)
     FILTERS closed-interval (superseded) records out — "the marked record
     is removed not merely demoted — this is the gap the old
     SUPERSEDED_PENALTY left open." A `superseded-by` marker promotes the
     record into a closed validity interval `[valid_from, valid_to)`;
     `_supersession_interval` closes it (via `superseded-date`, or a
     far-future sentinel when the date is absent — the marker's PRESENCE is
     the close signal); `_filter_by_interval` drops closed intervals on the
     default view.

  2. Deliberate design, two sealed commits. `e0eff95e` (supersession via
     validity intervals) + `779d306f` (volatility read-side hard-exclude)
     establish the hard-exclude as the intended architecture, not a bug.

  3. Passing canonical suite. `test_AC_SUP_1_default_view_filters_stale.py`,
     `test_AC_SUP_2_as_of_history_reachable.py`, and
     `test_AC_FBMT1_SUPM_3_not_filtered.py` all pass on HEAD. The last one
     PINS the reconciliation: amendment-134's SUPM.3 "demote-not-filter on
     the DEFAULT view" was PROMOTED into a real filter; the annotate-not-
     delete property SUPM.3 protects now lives on the `as_of` HISTORY view
     (marked-but-in-window record returned AND demoted by SUPERSEDED_PENALTY).

  4. Git timeline. The smoke's last touch (`299b3a42`, 2026-06-12) predates
     the redesign (`e0eff95e`/`779d306f`, 2026-06-28). The smoke was never
     migrated when the contract moved.

Regression branch specifically probed + cleared: both `_fts_search`
(file_memory.py:1563) and `_grep_search` (file_memory.py:1681) funnel
through `_compose_score`, which applies `_filter_by_interval` FIRST — so the
hard-exclude is UNIFORM across the FTS and grep paths by construction. There
is no grep-vs-FTS over-exclusion asymmetry, which is the only shape that
would have made this a real defect.

## The change

One file: `plugins/dev-sdlc/tools/loam-amend/tests/
test_AC_FBMT1_S_end_to_end_smoke.py` sub-test (b). Three assertions +
two describing comments re-pointed:

  - `assert idx_second is not None` + `assert idx_first < idx_second`
    (present-but-demoted) → `assert idx_second is None` (hard-excluded from
    the default current view), with `assert idx_first is not None`
    retained (the unsuperseded episode stays current).
  - The file docstring line for (b) and the (b) section-header comment
    updated from "demotes the second" / "ranks below the first" to the
    hard-exclude contract.

No production source change. `AC.SMKSUP.1` (new): the FBMT1 smoke's
supersession leg asserts the current AC.SUP.1 default-view hard-exclude
contract. Ladders up to AC.SUP.1 → the prime-objective protection floor
(a stale operational-status claim is not served as current in a later
recall).

## Out of scope

  - Any runtime code (the behavior is correct + sealed).
  - The `as_of` history-view demote assertion — already pinned by the
    primary-persona `test_AC_FBMT1_SUPM_3_not_filtered.py`; re-testing it in
    the loam-amend smoke would widen the smoke beyond the FBM T1 primitive
    it exercises (scope discipline).

BASELINE `08da4e68` (current canonical HEAD). The dev-sdlc SEAL_COMMIT
sidecar lands at the seal SHA via `loam amend seal`.
