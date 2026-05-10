# v0.8.1 PATCH — honesty-cleanup follow-on (axis-12 NF1 + NF2 closure per pass-2 external review)

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: scope ratified Telegram 10706 (close 2 NEW axis-12 defects surfaced by external-reviewer pass-2 at `<workspace>/.scratch/claude-output/loam-external-review-v0.8.0-2026-05-10.md`).
**Slug:** `v0-8-1-honesty-cleanup-followon`.
**Date authored:** 2026-05-10.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. No new outcome capability — v0.8.0 established the per-component-version discipline outcome shape; v0.8.1 closes 2 defects within that already-shipped outcome (NF1 historical-row title contradictions; NF2 walker count drift). Same defect class the v0.8.0 cleanup just resolved (drift between documented state and actual state).
**Predecessor:** v0.8.0 (sealed `e44b09d`, published `22f4178`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatched 2026-05-10 (Telegram 10706); covers plan-doc authoring + build + seal. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The 2026-05-10 external-reviewer pass-2 (`<workspace>/.scratch/claude-output/loam-external-review-v0.8.0-2026-05-10.md`) verified v0.8.0 closed 6 of 8 axis-12 findings (F1-F6) and reasonably deferred 2 (F7 + F8). Honesty axis moved LOW (FAIL) → MEDIUM (PASS); all four MUST-PASS axes (4 / 7 / 8 / 12) now satisfied. But the cleanup introduced **2 NEW axis-12 defects of the same drift class it was meant to close**:

1. **NF1 — three v0.7.X STATE.md leading-title contradictions.** `docs/STATE.md` lines 132 (v0.7.2), 133 (v0.7.3), 135 (v0.7.1) all carry leading-title `**v0.7.X PATCH SHIPPED LOCAL**` while their bodies say `**v0.7.X SHIPPED PUBLIC 2026-05-10 at tag \`v0.7.X\`**`. This is the IDENTICAL defect class to F5 (the v0.5.0 internal-contradiction case the v0.8.0 cleanup just resolved). Root cause: v0.8.0's per-row manual fix for v0.5.0 didn't generalize to a sweep across all rows; the v0.7.4 `_backfill_state_md_leading_title` helper was never applied retroactively to v0.7.1/v0.7.2/v0.7.3 because the auto-backfill only fires at the version being published. Cost: a stranger reading STATE.md sees 3 rows that contradict themselves; the v1.0 framing is undermined.

2. **NF2 — `_update_total_shipped_line` walker bug: line is mathematically wrong.** `docs/release-roadmap.md` line 73 (also `docs/STATE.md` line 137 v0.8.0 row) reads `**Total shipped:** 19 minor + 8 patches. v0.1.0 → v0.7.4 published.` Actual §2 row count: 8 minor (X.Y.0 form: v0.1.0 / v0.2.0 / v0.3.0 / v0.4.0 / v0.5.0 / v0.6.0 / v0.7.0 / v0.8.0) + 18 patches (X.Y.Z non-X.Y.0 form: v0.1.6/v0.1.7/v0.1.8/v0.1.9 / v0.2.1/v0.2.2/v0.2.3/v0.2.4/v0.2.5/v0.2.5.1 / v0.4.1/v0.4.2/v0.4.3 / v0.5.1 / v0.7.1/v0.7.2/v0.7.3/v0.7.4) = **8 + 18 = 26 rows**. The line says 19 + 8 = 27 — numbers are reversed AND the total is off-by-one. Root cause investigation (function-altitude verification at plan-time):
    - **Cause A:** the `_SUMMARY_LINE` regex `r"^\*\*Total shipped:\*\*\s+(\d+)\s+minor\s+\+\s+(\d+)\s+patch(?:es)?\.\s+v[\d.]+\s+published\."` requires a single `vX.Y.Z published.` form, but the live line carries `v0.1.0 → v0.7.4 published.` (arrow + range form). Regex never matches → `_backfill_summary_line` returns body unchanged → the line stays stale.
    - **Cause B:** even if the regex matched, `_count_published_versions` only counts §2 rows that carry the SHIPPED-PUBLIC marker (`r"^\|\s*v[\d.]+\s*\|.*\*\*SHIPPED PUBLIC[^*]*at tag\s+\`v[\d.]+\`.*$"`). Only 8 of 26 rows currently have markers (all rows shipped before v0.7.3 lack auto-backfill markers because the marker convention only existed from v0.7.3 onward). So the walker would undercount if it ever did fire.

The v0.8.1 outcome shape is **2 NEW axis-12 defect closures within the v0.8.0 honesty-cleanup outcome shape**, plus a structural fix to the `_count_published_versions` walker so future publishes track ground truth correctly.

**Why patch (not minor).** Per `docs/release-versioning-policy.md`, MINORs add outcome capability; PATCHes close defects within an already-shipped outcome. v0.8.0's outcome shape was "documented-state matches actual-state across the user-facing surface" + "per-component-version discipline established." v0.8.1 doesn't add a new gate, a new CLI verb, a new state-sync target — it tightens the existing surface so the documented-state-matches-actual-state outcome holds for the v0.7.X historical rows + the Total-shipped count line. Defect-closure within already-shipped outcome = PATCH.

**Why this needed v0.8.0 pass-2 review to surface.** NF1 is the recurrence of the patch-the-instance-miss-the-class pattern that pass-1 review surfaced; pass-2 (verifying pass-1's closures) caught it. NF2 was invisible until the auto-backfill helper was wired in v0.7.3 + the live count diverged from reality — pass-2's per-row counting verified the miscount. Both defects required the v0.8.0 pass-1 closures to land before they could be observed.

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1 — closed
           at v0.7.1; extended at v0.8.0; v0.8.1 closes the 2 NEW
           axis-12 drift instances surfaced by pass-2 review)
             └─ STATE.md historical-row title contradictions resolved
                 + Total-shipped count line tracks ground truth
                  └─ AC.NFCLEAN.1 (sweep STATE.md for SHIPPED-LOCAL
                                    leading titles whose bodies say
                                    SHIPPED PUBLIC; apply v0.7.4
                                    _backfill_state_md_leading_title
                                    helper retroactively to v0.7.1 /
                                    v0.7.2 / v0.7.3 rows)
                  └─ AC.NFCLEAN.2 (fix _update_total_shipped_line
                                    walker — count ALL §2 version rows
                                    not just marker-bearing rows;
                                    update _SUMMARY_LINE regex to
                                    accept arrow + range form;
                                    correct the live line manually
                                    once + add walker test)
                  └─ AC.NFCLEAN.3 (outcome-altitude probe — cold-clone
                                    of post-v0.8.1 origin tag + verify
                                    NF1 + NF2 are closed at the tag,
                                    not just at maintainer's local)
                  └─ AC.NFCLEAN.S (seal-diff discipline)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — every AC reduces translation burden by removing one drift surface a user / contributor / external reviewer would have to mentally reconcile. NF1 closes 3 internal-contradiction rows; NF2 closes a count line that was the prime example a stranger could find of the maintainer's count discipline failing.
- **Harness test** — AC.NFCLEAN.2's walker fix sharpens the existing v0.7.3 `_count_published_versions` + `_backfill_summary_line` primitives. After v0.8.1 lands, the auto-backfill function correctly handles the actual live shape (arrow + range form) + counts the actual published version count, not just the marker-bearing subset.

## §3 — Component fence

**Single-component PATCH.** Touched component: `framework/tools/loam/` (the release-CLI runner + post-publish-backfill module + their test corpus) for AC.NFCLEAN.2; admin doc edits for AC.NFCLEAN.1 + AC.NFCLEAN.3.

**PRIMARY (single-file edits):**
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (AC.NFCLEAN.2):
  - Tighten `_SUMMARY_LINE` regex to accept arrow + range form: `v[\d.]+(?:\s*→\s*v[\d.]+)?\s+published\.` (matches both `vX.Y.Z published.` and `v0.1.0 → v0.7.4 published.`).
  - Tighten `_count_published_versions` to count ALL §2 version rows (`r"^\|\s*v[\d.]+\s*\|"`), not just marker-bearing ones. The §2 section's semantic is "shipped versions" — every row in §2 is a shipped version regardless of whether it carries the auto-backfill marker.
  - Preserve existing classification logic (`_classify_row` checks the third pipe-cell for `MINOR` keyword).
- `framework/tools/loam/tests/test_AC_BACKFL.py` (AC.NFCLEAN.2):
  - New test `test_count_published_versions_includes_marker_less_historical_rows` — verifies the walker counts §2 rows that lack the SHIPPED-PUBLIC marker (mirror of historical-rows-pre-v0.7.3 case).
  - New test `test_summary_line_regex_accepts_arrow_range_form` — verifies `_SUMMARY_LINE` matches `v0.1.0 → v0.7.4 published.` shape.
  - Update existing `test_apply_backfill_updates_aggregate_count_summary` if expected count shifts (it shouldn't — the test fixture has 2 marker-bearing rows + 0 marker-less rows; with the new "count all rows" logic, count should still be 2 if the test fixture only has 2 §2 rows).

**PRIMARY (admin docs):**
- `docs/STATE.md` (AC.NFCLEAN.1) — flip leading titles for v0.7.1 / v0.7.2 / v0.7.3 rows from `**v0.7.X PATCH SHIPPED LOCAL**` → `**v0.7.X PATCH SHIPPED PUBLIC**` via direct `apply_backfill` invocation per version.
- `docs/release-roadmap.md` (AC.NFCLEAN.2 manual touch-up) — correct the `**Total shipped:** 19 minor + 8 patches. v0.1.0 → v0.7.4 published.` line to reflect actual count `**Total shipped:** 8 minor + 18 patches. v0.1.0 → v0.8.0 published.` Cumulative-prose body (the `v0.3.0 ships META-FRAMEWORK foundation; ...` tail) preserved.
- `docs/STATE.md` (AC.NFCLEAN.2) — same correction in the v0.8.0 row's narrative pointer (if present); verify post-edit.

**Universal-admission docs:**
- `docs/plans/v0-8-1-honesty-cleanup-followon.md` (this file).
- `docs/plans/v0-8-1-honesty-cleanup-followon.manifest.yaml`.
- `docs/STATE.md` — v0.8.1 SHIPPED LOCAL row added at end-of-build (separate from AC.NFCLEAN.1 historical edits).
- `docs/release-roadmap.md` — v0.8.1 §2-shipped row added at end-of-build (separate from AC.NFCLEAN.2 walker + count-line edits).
- `docs/experiments/v0-8-1-hard-smoke.md` — HARD smoke writeup for the v0.8.1 publish gate (covers AC.NFCLEAN.3 outcome-altitude probe).

**Untouched:** all other source code; all other tests beyond the 2 new walker tests; runner.py (the function-internal walker fix is sufficient — no runner-side changes); README.md; dormancy; pyproject.toml versions (the v0.8.0 bump is in effect; v0.8.1 is a PATCH so versions stay at 0.8.0 OR bump to 0.8.1 per the per-component-version discipline established in v0.8.0; build-time decision D-NFCLEAN.4 in §5).

## §4 — Acceptance criteria

Three ACs plus seal-diff. AC IDs use the scope-descriptive `NFCLEAN` family per `feedback_scope_descriptive_ac_ids` ("NFCLEAN" = "NF-class drift cleanup" — closes the NF1 + NF2 surfaces from the v0.8.0 pass-2 review).

### AC.NFCLEAN.1 — Historical SHIPPED-LOCAL title sweep: v0.7.1 / v0.7.2 / v0.7.3

**What:** `docs/STATE.md` lines 132 (v0.7.2), 133 (v0.7.3), 135 (v0.7.1) carry leading-title `**v0.7.X PATCH SHIPPED LOCAL**` while their bodies say `**v0.7.X SHIPPED PUBLIC 2026-05-10 at tag \`v0.7.X\` (annotated \`<sha7>\`)**`. Apply the existing v0.7.4 `_backfill_state_md_leading_title` helper retroactively to all 3 rows.

**Build-time decision (D-NFCLEAN.1.a):** invoke `apply_backfill(repo_root, version, tag, tag_sha, seal_sha=...)` once per historical version (v0.7.1, v0.7.2, v0.7.3), with each version's known tag + seal SHAs. Reuses the v0.7.4 helper exactly as it would have fired had the auto-backfill existed when those versions published. Resulting commit lands as a single commit `docs(state): v0.7.1/v0.7.2/v0.7.3 historical leading-title sweep — SHIPPED PUBLIC` (NOT three separate commits — single atomic cleanup, mirror of v0.8.0's D-HONEST.4.b precedent for the historical TBD-AT-* backfill).

**Discovered SHAs (verified via grep against live STATE.md at plan-time):**
- v0.7.1: tag `v0.7.1` (annotated `1d08a40`); seal `cdae8ed`.
- v0.7.2: tag `v0.7.2` (annotated `0e67135`); seal `91ee1fe`.
- v0.7.3: tag `v0.7.3` (annotated `72de0da`); seal `39170e6`.

**Acceptance:**
- `grep -c "PATCH SHIPPED LOCAL" docs/STATE.md` returns at most 1 match (the in-flight v0.8.1 row's pre-publish state, if added before this AC closes).
- v0.7.1 / v0.7.2 / v0.7.3 STATE.md row leading titles read `**v0.7.X PATCH SHIPPED PUBLIC**`.
- Bodies still carry `**v0.7.X SHIPPED PUBLIC 2026-05-10 at tag \`v0.7.X\`**` markers (the trailing-claim flip already happened in v0.7.3/v0.7.4 cycles).
- `apply_backfill(...)` invocation idempotent on re-run (per AC.BACKFL2.4 already-public title no-op).

`outcome-altitude: false` — implementation-altitude AC (mechanical helper invocation verified via grep + read).

### AC.NFCLEAN.2 — `_update_total_shipped_line` walker fix + count-line correction

**What:** Two compound fixes:

(a) **Walker robustness fix (structural):** Tighten `_SUMMARY_LINE` regex in `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` to accept the actual live shape `vX.Y.Z published.` OR `vA.B.C → vX.Y.Z published.` (arrow + range form). Tighten `_count_published_versions` to count ALL §2 version rows (`r"^\|\s*v[\d.]+\s*\|"`), not just marker-bearing rows — every row in §2 is by definition a shipped version (the section's semantic is "shipped versions"; the SHIPPED-PUBLIC marker is the auto-backfill provenance signal, not the published-state signal).

(b) **Live count-line correction (one-time):** Manually correct the `**Total shipped:** 19 minor + 8 patches. v0.1.0 → v0.7.4 published.` line in `docs/release-roadmap.md` to `**Total shipped:** 8 minor + 18 patches. v0.1.0 → v0.8.0 published.` reflecting the actual §2 row count (verified empirically: 8 MINORs + 18 PATCHes = 26 rows). The cumulative-prose tail (`v0.3.0 ships META-FRAMEWORK ...`) extends from `... ; v0.7.4 closes auto-backfill spec gaps surfaced at v0.7.3's own publish dogfood; v0.8.0 ships honesty cleanup ...` to `... ; v0.8.1 closes the 2 NEW axis-12 defects surfaced by external-reviewer pass-2 (NF1 historical-row title sweep + NF2 walker count-drift fix)` — appended at end-of-build along with the v0.8.1 §2 row.

**Build-time decision (D-NFCLEAN.2.a — walker fix shape):** keep classification logic intact (`_classify_row` reads third pipe-cell for `MINOR` keyword). The only changes are the row-pattern regex (drop the marker requirement) and the summary-line regex (accept arrow + range form). The classification IS robust against pipe-embedded descriptions because `_classify_row` reads `third_cell_split[3]` which is the 4th split element — when descriptions contain pipes, this misclassifies (v0.4.2's row would resolve to 4 cells before the actual class cell). Cross-checked at plan-time: v0.4.2's actual class cell is index [4] not [3]. **Build-time decision (D-NFCLEAN.2.b — pipe-in-description robustness):** out of scope for v0.8.1. v0.4.2 is correctly counted as PATCH (the misclassification incidentally resolves correctly because cell [3] of v0.4.2's split is `Y\` → \`Union[X, Y]\` ...` which contains no MINOR keyword, defaulting to PATCH which matches v0.4.2's true class). FIDRAFT entry F-WALKER-1 captures the deeper robustness fix (split on a pipe-row-aware tokenizer that respects backtick-bounded pipes) for v0.8.x or v0.9.0.

**Build-time decision (D-NFCLEAN.2.c — manual correction first OR walker fix first):** walker fix first; then run the corrected walker against the live state to produce the correct count line; then commit the corrected count + the new walker tests in a single source-edit batch. If the walker still produces the wrong count after the fix, halt-and-surface (per HARD HALT #5 — bigger than v0.8.1's scope).

**Build-time decision (D-NFCLEAN.2.d — tests):** 2 new tests at `framework/tools/loam/tests/test_AC_BACKFL.py`:
- `test_count_published_versions_includes_marker_less_historical_rows` — fixture has 2 marker-bearing + 2 marker-less §2 rows; assertion: count returns (1 minor + 3 patches) or similar reflecting all 4 rows, NOT (1 + 1) reflecting only marker-bearing.
- `test_summary_line_regex_accepts_arrow_range_form` — fixture has summary line `**Total shipped:** 5 minor + 10 patches. v0.1.0 → v0.5.0 published.`; assertion: regex matches; backfill flips the count to walker output + preserves the arrow + range form.

Existing test `test_apply_backfill_updates_aggregate_count_summary` should still pass without modification — its fixture has 2 §2 rows (v0.8.9 marker-bearing + v0.9.0 just-published), both PATCH per their third-cell `Single-cycle PATCH` text. With the new "count all rows" logic, count is still (0 minor + 2 patches), matching the existing assertion.

**Acceptance:**
- `_SUMMARY_LINE` regex matches both `vX.Y.Z published.` and `vA.B.C → vX.Y.Z published.` shapes (2 new test cases).
- `_count_published_versions` counts all §2 version rows (not just marker-bearing).
- Live `docs/release-roadmap.md` line 73 reads `**Total shipped:** 8 minor + 18 patches. v0.1.0 → v0.8.0 published.` (cumulative-prose tail preserved + extended with v0.8.1 entry at end-of-build).
- 2 new tests at `test_AC_BACKFL.py` GREEN; all existing BACKFL tests continue to pass.
- All release-CLI tests remain GREEN (no regression).

`outcome-altitude: false` — implementation-altitude AC (regex tightening + walker logic + manual correction verified via test + grep).

### AC.NFCLEAN.3 — Outcome-altitude cold-clone probe

**What:** Cold-clone the v0.8.1 tag (after publish; or simulate via `git clone` of the local branch state for the pre-publish probe) to a tmp directory; verify NF1 + NF2 are closed AT THE TAG (not just at maintainer's local working tree). Probe pattern same as v0.7.1 / v0.7.4 cold-clone probes.

**Build-time decision (D-NFCLEAN.3.a — pre-publish vs post-publish probe):** v0.8.1 is sealed-locally awaiting owner publish gate. The probe at build-time runs against the maintainer's local working-tree state at the post-seal commit (the would-be tag's content). The full cold-clone-from-origin probe runs after publish per AC.HONEST.7 precedent (post-publish dogfood). At seal-time: `git diff <seal_commit> -- docs/STATE.md docs/release-roadmap.md` shows the corrections + grep against the would-be tag's content verifies closure. Documented at `docs/experiments/v0-8-1-hard-smoke.md`.

**Acceptance:**
- `grep -c "PATCH SHIPPED LOCAL" docs/STATE.md` at the v0.8.1 seal commit returns at most 1 (in-flight v0.8.1 row only, if present pre-publish; 0 post-publish after auto-backfill fires on v0.8.1's own row).
- `grep "Total shipped:" docs/release-roadmap.md` at the v0.8.1 seal commit returns the corrected count line.
- Probe writeup at `docs/experiments/v0-8-1-hard-smoke.md` documents the closure evidence + the post-publish full-cold-clone follow-up (deferred to dispatcher publish action).

`outcome-altitude: true` — outcome-altitude AC (verifies the v0.8.1 fix lands at the tag-content level, the user-observable surface).

### AC.NFCLEAN.S — Seal-diff discipline

**What:** `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under the AC.NFCLEAN.{1,2,3}-allowed paths.

**Acceptance:**
- All paths in the diff are members of the `framework/tools/loam/` PRIMARY scope OR the universal-admission docs list.
- No source code changes outside the `post_publish_backfill.py` walker fix + `test_AC_BACKFL.py` 2 new tests.
- No pyproject.toml version bumps (v0.8.0 bumps stay at 0.8.0; D-NFCLEAN.4 ruling — see §5).

## §5 — Decisions builder rules at build time

- **D-NFCLEAN.1.a (historical sweep mechanism):** invoke `apply_backfill(...)` per version; reuse v0.7.4 helper exactly. Single atomic commit covering all 3 versions (mirror of v0.8.0 D-HONEST.4.b precedent).
- **D-NFCLEAN.2.a (walker fix shape):** drop marker requirement from `_count_published_versions`; tighten `_SUMMARY_LINE` regex to accept arrow + range form. Classification logic unchanged.
- **D-NFCLEAN.2.b (pipe-in-description robustness):** out of scope; FIDRAFT F-WALKER-1.
- **D-NFCLEAN.2.c (sequence):** walker fix first; then run against live state; then commit corrected count + new tests in single batch.
- **D-NFCLEAN.2.d (tests):** 2 new tests covering marker-less rows + arrow-range regex; existing tests preserved.
- **D-NFCLEAN.3.a (probe shape):** pre-publish probe at seal-time against working-tree; post-publish full cold-clone deferred to dispatcher action.
- **D-NFCLEAN.4 (pyproject.toml versions):** stay at `0.8.0` for v0.8.1. The per-component-version discipline (v0.8.0 AC.HONEST.1) advances component versions with shipped MINORs; PATCHes ride within the predecessor MINOR's version. This matches SemVer convention (a v0.8.1 patch is part of the v0.8 MINOR series). FIDRAFT F-PCV-1 captures the question of whether PATCHes should bump component patch-numbers (`0.8.0 → 0.8.1`) for the v0.9.0 cycle's review.

## §6 — Out of scope (explicit)

- **F-WALKER-1 (pipe-in-description robustness)** — see D-NFCLEAN.2.b. Out of scope; FIDRAFT entry.
- **F-PCV-1 (component pyproject patch-number discipline)** — see D-NFCLEAN.4. Out of scope; FIDRAFT entry.
- **v0.7.4 auto-backfill prose-greedy regex bug** — separate scope; v0.7.5+ candidate per dispatch brief.
- **v0.7.4 auto-backfill double-parens objective extraction** — same.
- **F7 plugin contract version surface** — FIDRAFT-deferred per v0.8.0.
- **F8 third-party recruitment** — NOT maintainer-controllable.
- **`Pre-publish state-update enforcement gate`** — the gate that would catch NF1 at pre-publish time (verify no row carries leading-title SHIPPED LOCAL with body SHIPPED PUBLIC) is v0.8.x or v0.9.0 work; FIDRAFT entry.
- **README narrative further cleanup** — the 3 v0.1.0 references in README are correct per v0.8.0 design (1 historical-fact + 2 authorship-attribution).
- **STATE.md / roadmap structural surgery (per-version files)** — axis-6 LOW band evidence per pass-2 review; v0.9.0+ work.
- **Anthropic API key paths** (per architectural constraint, never).

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.NFCLEAN.3 outcome-altitude probe RED. The fix doesn't land at the seal commit's would-be tag content. Halt; surface as F-DESIGN candidate.
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
5. Wall-clock exceeds upper band (60-120 min midpoint ~90 min) by >2× → 4 hr (matches dispatch brief's surface threshold). Halt with current state.
6. **AC.NFCLEAN.2 walker investigation reveals systemic auto-backfill rewrite needed (not just a counting bug).** If the walker fix turns out to require restructuring the auto-backfill pipeline (e.g., the count-walker needs to track historical-vs-auto-backfilled rows separately + change the marker semantics), halt + surface — that's bigger than v0.8.1's scope.
7. AC.NFCLEAN.1 helper invocation against any of v0.7.1 / v0.7.2 / v0.7.3 produces unexpected edits (e.g., the helper flips MORE than the leading title, or fails to find the SHIPPED-LOCAL pattern). Halt + surface.
8. Discovery that the walker fix breaks any of the 19 existing BACKFL tests (regression). Halt + surface.
9. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.

## §8 — Dependencies

- **v0.8.0 (honesty cleanup)** — HARD. v0.8.1 closes 2 NEW defects surfaced by v0.8.0's pass-2 review; v0.8.1 cannot land without v0.8.0 sealed.
- **v0.7.4 (auto-backfill completeness)** — HARD. AC.NFCLEAN.1 reuses the `_backfill_state_md_leading_title` helper from v0.7.4.
- **v0.7.3 (release-CLI auto-backfill)** — HARD. AC.NFCLEAN.2 fixes the v0.7.3 walker.
- **v0.7.2 (release-CLI parser fix)** — SOFT. AC.NFCLEAN.3 outcome-altitude probe consumes the fixed `acs-verified` parser.
- **v0.7.0 (`## §13 — §status` literal heading parser)** — SOFT. The plan-doc §status backfill at end-of-build uses the literal heading form per the v0.7.0 fix.
- **`docs/release-versioning-policy.md`** — SOFT. PATCH-class declaration grounded in the policy.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `NFCLEAN` AC ID family choice over `V081.*`.
- **`feedback_build_forward_on_publish_pending`** — SOFT. v0.8.0 just sealed; v0.8.1 dispatched in flight.
- **`feedback_no_amend_in_agent_dispatches`** — HARD. Post-fix commits are NEW commits, never `--amend`.
- **No external service dependencies.**
- **No new Python packages** (subscription-only constraint).

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — single-component PATCH; tight per-AC scope; extending an existing helper (v0.7.4) + fixing a 2-line walker bug + 2 new tests + outcome-altitude probe. Defect-closure (no design exploration); confidence in outcome shape is high (Lens 4 — tight scope appropriate). v0.7.4 actuals (~51 min for new helpers + 8 tests) calibrates the upper bound; v0.8.1 has less code (3 helper invocations + 2 walker-line edits + 2 tests + count-line correction).

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 12-20 min | 16 min |
| AC.NFCLEAN.1 — historical sweep (3 helper invocations + verify) | 8-12 min | 10 min |
| AC.NFCLEAN.2 — walker fix (regex + count-all-rows) | 6-10 min | 8 min |
| AC.NFCLEAN.2 — manual count-line correction | 2-4 min | 3 min |
| AC.NFCLEAN.2 — 2 new walker tests | 8-12 min | 10 min |
| AC.NFCLEAN.3 — outcome-altitude probe + writeup | 6-10 min | 8 min |
| FIDRAFT capture (F-WALKER-1, F-PCV-1) | 3-5 min | 4 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 12-20 min | 16 min |
| **Total v0.8.1 build** | **57-93 min (~1.0-1.5 hr)** | **~75 min (~1.25 hr)** |

The dispatch brief estimates 60-120 min midpoint ~90 min. Plan-time revision: **57-93 min midpoint ~75 min**. Defensible: 3 helper invocations (no new helper code) + 2 walker-line edits + 2 tests is much smaller than v0.7.4's 3 new helpers + 8 tests. Defect-closure shape with high confidence in scope keeps the band tight; midpoint sits well below the 4-hr HARD HALT threshold.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- Telegram 10706 (owner directive 2026-05-10) — scope ratification ("close 2 NEW axis-12 defects surfaced by external-reviewer pass-2"). The dispatch authority for v0.8.1.
- `<workspace>/.scratch/claude-output/loam-external-review-v0.8.0-2026-05-10.md` — the F2 surface this cycle closes against. Pass-2 review verified v0.8.0's 6/8 closures + identified NF1 + NF2 as new gaps.
- `e44b09d` (commit 2026-05-10, v0.8.0 seal) — the predecessor seal whose pass-2 review surfaced NF1 + NF2.
- `22f4178` (commit 2026-05-10, v0.8.0 publish tag) — the published-state baseline.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground.
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (existing module from v0.7.3 + v0.7.4) — the surface AC.NFCLEAN.2 fixes.
- `framework/tools/loam/tests/test_AC_BACKFL.py` (existing 19-test module) — the test corpus AC.NFCLEAN.2 extends with 2 new tests.
- `docs/plans/v0-8-0-honesty-cleanup.md` — predecessor MINOR-class plan-doc; v0.8.1 closes the residual gaps surfaced by v0.8.0's pass-2 review.
- `docs/plans/v0-7-4-auto-backfill-completeness.md` — provides the `_backfill_state_md_leading_title` helper AC.NFCLEAN.1 reuses.
- Memory rules: `feedback_scope_descriptive_ac_ids.md` (AC.NFCLEAN.* not AC.V081.*), `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_no_anthropic_api_key.md` (HARD HALT #9), `feedback_subagent_odd_violation_halt.md` (HARD HALT #2), `feedback_duration_estimation_rubric.md` (§9), `feedback_build_forward_on_publish_pending.md` (§8 build-forward justification), `feedback_test_outcome_altitude_required.md` (AC.NFCLEAN.3 risk-band), `feedback_locked_design_not_license_for_bad_outcomes.md` (the v0.8.0 cleanup landed but introduced 2 new gaps — this plan revisits the cleanup rather than living with the bad outcome).

## §13 — §status

**Build cycle:** TBD — populated post-seal.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.NFCLEAN.1 — Historical SHIPPED-LOCAL title sweep | TBD | TBD |
| AC.NFCLEAN.2 — `_update_total_shipped_line` walker fix + count-line correction | TBD | TBD |
| AC.NFCLEAN.3 — Outcome-altitude cold-clone probe | TBD | TBD |
| AC.NFCLEAN.S — Seal-diff discipline | TBD | TBD |

### AI-time actuals

TBD — populated post-seal.

### Halt-and-surface findings

TBD.

## §14 — Method decisions

The plan-doc's §5 names the build-time decisions (D-NFCLEAN.1.a sweep mechanism, D-NFCLEAN.2.a walker fix shape, D-NFCLEAN.2.b pipe robustness scope, D-NFCLEAN.2.c sequence, D-NFCLEAN.2.d tests, D-NFCLEAN.3.a probe shape, D-NFCLEAN.4 pyproject versions). Builder rulings to be recorded post-seal.

### Commit SHAs

TBD — populated post-seal.

### Build-time decision deviations

TBD.
