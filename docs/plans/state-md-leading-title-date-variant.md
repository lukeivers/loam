# STATE.md leading-title date-in-title variant PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: F-FUNC-1 capture from v0.8.0 build (AC.HONEST.4 halt-and-surface 2026-05-10) explicitly framed this regex extension as the next-release-CLI-cycle activation gate. This PATCH executes that gate.
**Slug:** `state-md-leading-title-date-variant` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-13.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Defect-closure on the v0.7.4 `_backfill_state_md_leading_title` helper's regex (canonical form only); no new outcome capability — same outcome shape (leading-title SHIPPED-LOCAL → SHIPPED-PUBLIC flip) extended to one additional row variant.
**Predecessor:** v0.10.1 PATCH SHIPPED PUBLIC (sealed `4fb89eb`; published `4520ff9`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.1) = v0.10.2`. Plan-doc slug scope-descriptive (no version pre-baked); AC family scope-descriptive (`AC.SMLTV.*` for STATE.md Leading-Title Variant).

---

## §1 — Outcome shape (the "why")

The v0.7.4 `_backfill_state_md_leading_title` helper at `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py:145-198` recognizes the canonical form `**v<X.Y.Z> (MINOR|PATCH|minor|patch) SHIPPED LOCAL**` — a class-keyword between version and SHIPPED. The v0.4.2 STATE.md row carries a non-canonical variant: `**v0.4.2 SHIPPED LOCAL 2026-05-09**` (date in the bolded title; no class keyword between version and SHIPPED).

When v0.8.0's AC.HONEST.4 retroactively ran `apply_backfill(...)` against v0.4.2's row, the helper correctly surfaced a hint and skipped (graceful degradation per AC.BACKFL2.4) — but the row needed manual touch-up to flip LOCAL → PUBLIC. F-FUNC-1 captured the regex extension proposal at `docs/FUTURE_IDEAS_DRAFT.md:246`; this PATCH makes the variant handling structural.

**The extension shape (per F-FUNC-1 proposal, anchored to dispatch brief AC.SMLTV.1):** recognize `**v<X.Y.Z> SHIPPED LOCAL <YYYY-MM-DD>**` (class-keyword absent; date present after LOCAL) AND flip it to `**v<X.Y.Z> SHIPPED PUBLIC <YYYY-MM-DD>**` (preserving the date verbatim). The flip is a pure LOCAL → PUBLIC token swap with date preserved — NOT an append of the at-tag/annotated suffix. The trailing-sentence flip (`_backfill_state_md`, v0.7.3 AC.BACKFL.1) and §2 row marker append (`_backfill_roadmap_row`) remain the surfaces that emit the at-tag/annotated detail; the leading title carries only the version + status + (optional class OR optional date).

**Why PATCH (not MINOR).** Per `docs/release-versioning-policy.md`, MINORs add outcome capability; PATCHes close defects within an already-shipped outcome. This PATCH extends one regex inside an already-shipped helper to cover one additional row variant. No new gate, CLI verb, helper function, or state-sync target. Same outcome shape (leading-title flip) with widened input domain. Defect closure within already-shipped outcome = PATCH.

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ post-publish auto-backfill correctly handles every
                STATE.md row variant currently in use (no manual
                touch-up required for any historical or in-flight row)
                  └─ AC.SMLTV.1 (date-in-title variant recognized +
                                  flipped LOCAL → PUBLIC with date
                                  preserved)
                  └─ AC.SMLTV.2 (canonical-form behavior preserved;
                                  existing tests pass)
                  └─ AC.SMLTV.3 (already-public no-op for the variant
                                  preserves idempotence)
                  └─ AC.SMLTV.4 (synthetic-fixture dogfood probe
                                  verifies all 4 cases handled)
                  └─ AC.SMLTV.S (seal-diff: helper + new test cases
                                  + universal-admission docs only)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — closes one manual-touch-up surface a contributor would have to know about. After this PATCH, no operator running `apply_backfill(...)` against a date-in-title-variant row needs to know "the v0.7.4 helper's regex doesn't catch this — touch up manually."
- **Harness test** — extends the `_backfill_state_md_leading_title` helper, which is part of the post-publish-backfill toolkit the primary persona invokes via `loam release`. Wider input coverage = more reliable harness primitive.

Composes with: F-FUNC-1 (this PATCH closes the captured-only F-FUNC-1 surface; the FIDRAFT entry gets marked RESOLVED in §status). Composes with: `feedback_loose_AC_text_fix_AC_not_implementation` — the F-FUNC-1 proposed regex shape and the dispatch AC.SMLTV.1 outcome differ in one detail (F-FUNC-1 said "appends the at-tag-annotated suffix"; AC.SMLTV.1 says "preserving the date"). The dispatch is the live contract — D-SMLTV.1 ratifies AC.SMLTV.1's shape: simple LOCAL → PUBLIC token swap with date preserved, no at-tag suffix append (that surface is owned by the trailing-sentence flip).

---

## §3 — Component fence

**Single-component PATCH.** Seal anchor: dev-sdlc (the canonical seal-anchor for release-CLI single-component changes; matches v0.7.3 / v0.7.4 / v0.8.2 / v0.8.3 precedent).

**PRIMARY (3 files):**

- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` — extend the `_leading_title_pattern` regex + `_state_md_title_already_public` regex + `_backfill_state_md_leading_title` replacement logic to handle the date-in-title variant. Minimal scope: just the leading-title helper. Do NOT touch `_backfill_state_md_placeholders` (F-FUNC-3 narrative-safety gap captured separately; F-FUNC-3 sits in its own future cycle).
- `framework/tools/loam/tests/test_AC_BACKFL.py` — append 3 new test cases (AC.SMLTV.1 positive flip, AC.SMLTV.3 already-public variant no-op, AC.SMLTV.2 canonical-form preservation). The AC.SMLTV.4 dogfood probe runs as part of the smoke writeup, not as a test (test fixtures stay inline; dogfood is an experiment artefact per v0.7.3 + v0.7.4 precedent).
- `docs/experiments/v0-10-2-hard-smoke.md` — short doc-only smoke writeup with the synthetic-fixture dogfood probe. Stages: (1) synthetic STATE.md fixture with all 4 cases (canonical-LOCAL, variant-LOCAL, canonical-already-PUBLIC, variant-already-PUBLIC); (2) verification that all 4 cases handled correctly.

**SECONDARY (admin docs — universal-admission):**

- `docs/STATE.md` — append v0.10.2 row to §2.
- `docs/release-roadmap.md` — append v0.10.2 row to §2 + v0.10.2 standalone bold entry to §3 Active version.
- `docs/FUTURE_IDEAS_DRAFT.md` — mark F-FUNC-1 as RESOLVED (status flip; entry preserved for audit trail).

**TERTIARY (cycle bookkeeping):**

- `docs/plans/state-md-leading-title-date-variant.md` — this file.
- `docs/plans/state-md-leading-title-date-variant.manifest.yaml` — schema-v3 manifest.

**Out of fence:**

- ANY other helper (`_backfill_state_md` trailing-sentence flip; `_backfill_state_md_placeholders`; `_backfill_roadmap_row`; etc.). Deliberately untouched per dispatch brief HARD HALT — F-FUNC-3 narrative-safety gap is a separate cycle.
- ANY non-test framework code outside `post_publish_backfill.py`.
- pyproject.toml or `__version__` bumps (PATCH rides predecessor MINOR per D-NFCLEAN.4 / AC.HONEST.1 / D-SDPD / v0.8.3 precedent).
- Edits outside fence = halt.

---

## §4 — Acceptance criteria (`AC.SMLTV.*`)

Each AC maps to a verifiable acceptance signal. Method stays builder's call.

### AC.SMLTV.1 — Date-in-title variant recognized + flipped

`_backfill_state_md_leading_title` recognizes the date-in-title variant `**v<X.Y.Z> SHIPPED LOCAL <YYYY-MM-DD>**` AND flips it to `**v<X.Y.Z> SHIPPED PUBLIC <YYYY-MM-DD>**` (preserving the date verbatim). The function returns a non-None edit_summary when the variant is matched. Verified by a new positive test case with the v0.4.2-shape input (`**v0.4.2 SHIPPED LOCAL 2026-05-09**`).

**Verdict GREEN if:** new test case `test_apply_backfill_flips_state_md_date_in_title_variant` passes; post-call STATE.md body contains `**v0.4.2 SHIPPED PUBLIC 2026-05-09**` AND no longer contains `**v0.4.2 SHIPPED LOCAL 2026-05-09**`.

**Verdict YELLOW if:** flip happens but date is altered (e.g., today's date substituted instead of preserved) — precision fault.

**Verdict RED if:** variant unrecognized OR canonical-form regression OR date corrupted.

`outcome-altitude: false` (function-altitude test; verification is the assertion).

### AC.SMLTV.2 — Canonical-form behavior preserved

Existing canonical-form behavior preserved: `**v<X.Y.Z> (MINOR|PATCH|minor|patch) SHIPPED LOCAL**` → `**v<X.Y.Z> (MINOR|PATCH|minor|patch) SHIPPED PUBLIC**` still works (CLASS casing preserved per v0.7.4 AC.BACKFL2.1 ruling). All existing tests pass.

**Verdict GREEN if:** existing tests `test_apply_backfill_flips_state_md_leading_title` + `test_apply_backfill_preserves_class_casing_minor` + 20 other BACKFL tests pass unmodified; total 22+ BACKFL tests GREEN.

**Verdict RED if:** any existing test breaks OR the canonical regex no longer matches the canonical input.

`outcome-altitude: false` (regression check; verification is the test run).

### AC.SMLTV.3 — Already-public variant is a no-op

If row already says `**v<X.Y.Z> SHIPPED PUBLIC <YYYY-MM-DD>**`, no edit applied (idempotence preserved for the variant, mirroring AC.BACKFL2.4 for the canonical form). Verified by a new test case with the already-public variant shape.

**Verdict GREEN if:** new test case `test_apply_backfill_date_in_title_variant_already_public_no_op` passes; STATE.md body byte-equal pre/post call when input is the already-public variant.

**Verdict RED if:** double-flip mutates already-public state OR helper returns non-None edit_summary on already-public input.

`outcome-altitude: false` (function-altitude idempotence test).

### AC.SMLTV.4 — Outcome-altitude dogfood probe

Synthetic STATE.md fixture containing all 4 cases (canonical-LOCAL row + variant-LOCAL row + canonical-already-PUBLIC row + variant-already-PUBLIC row) invoked through `_backfill_state_md_leading_title` produces correct edits: canonical-LOCAL flipped, variant-LOCAL flipped (with date preserved), both already-PUBLIC rows untouched. Documented at `docs/experiments/v0-10-2-hard-smoke.md`.

**Verdict GREEN if:** smoke writeup at `docs/experiments/v0-10-2-hard-smoke.md` exists; contains the synthetic fixture; reports all 4 cases handled correctly with verbatim post-call body excerpts.

**Verdict RED if:** smoke writeup missing OR any of the 4 cases handled incorrectly OR writeup omits verbatim evidence.

`outcome-altitude: true` (dogfood probe at function-altitude against a real synthetic input).

### AC.SMLTV.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (regex extension)
- `framework/tools/loam/tests/test_AC_BACKFL.py` (3 new test cases)
- `docs/experiments/v0-10-2-hard-smoke.md` (smoke writeup)
- `docs/STATE.md` (v0.10.2 §2 row admin)
- `docs/release-roadmap.md` (v0.10.2 §2 row + v0.10.2 §3 entry admin)
- `docs/FUTURE_IDEAS_DRAFT.md` (F-FUNC-1 status flip to RESOLVED)
- `docs/plans/state-md-leading-title-date-variant.md` (this plan-doc)
- `docs/plans/state-md-leading-title-date-variant.manifest.yaml` (manifest)
- `plugins/dev-sdlc/seals/SEAL_COMMIT.state-md-leading-title-date-variant` (seal narrative)
- `plugins/dev-sdlc/tests/SEAL_COMMIT` (sidecar bump)
- `framework/per-project-pm/state/SEAL_COMMIT.dev-sdlc` (per-project-pm sidecar, if applicable)

NO entries elsewhere in `framework/tools/loam/`, no other helper modifications, no pyproject.toml or `__version__` bumps.

**Verdict GREEN if:** diff matches the allow-list above.
**Verdict RED if:** any out-of-fence file appears in the diff.

`outcome-altitude: false` (structural).

---

## §5 — Decisions builder rules at build time

- **D-SMLTV.1 (replacement shape).** AC.SMLTV.1's shape is "preserving the date" — a pure LOCAL → PUBLIC token swap with date verbatim. Differs from F-FUNC-1's "appends the at-tag-annotated suffix" — the at-tag/annotated suffix is the trailing-sentence helper's (`_backfill_state_md`) surface, NOT the leading-title helper's. Per `feedback_loose_AC_text_fix_AC_not_implementation`, the dispatch AC tightens the F-FUNC-1 framing: leading-title helper handles ONLY the LOCAL→PUBLIC + date-preservation; the at-tag/annotated detail lives in a sibling helper that already covers both the trailing-sentence flip and the §2 row marker.
- **D-SMLTV.2 (regex strategy).** Extend `_leading_title_pattern` to accept either (a) class-keyword between version and SHIPPED (canonical) OR (b) date after SHIPPED LOCAL (variant), via alternation. Mirror the extension on `_state_md_title_already_public` for the already-public check. Capture the class-keyword (canonical) OR date (variant) so the replacement preserves it. Builder may use one combined regex with optional groups OR two regexes with alternation — method stays builder's call.
- **D-SMLTV.3 (test scaffolding).** Append 3 new test cases to the existing `test_AC_BACKFL.py` (not a new file) per v0.7.4 / v0.8.1 / v0.8.2 / v0.8.3 precedent. Inline fixture strings rather than reusing `_state_md_with_shipped_local` (the existing helper is parameterized for canonical form; the variant needs its own minimal fixture).
- **D-SMLTV.4 (pyproject versions).** Per `AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 precedent`: per-component-version discipline advances pyproject.toml versions with MINORs; PATCHes ride the predecessor MINOR. v0.10.2 = PATCH-after-v0.10.x; pyproject versions stay at 0.10.0.
- **D-SMLTV.5 (smoke shape).** Doc-only short smoke writeup at `docs/experiments/v0-10-2-hard-smoke.md`. Single stage: synthetic-fixture function-altitude dogfood probe verifying all 4 cases (canonical-LOCAL, variant-LOCAL, canonical-already-PUBLIC, variant-already-PUBLIC). NO full cold-clone or runner-altitude probe (the function-altitude probe is sufficient evidence; matches v0.7.4 Stage 1 precedent).

---

## §6 — Out of scope (explicit)

- F-FUNC-3 (narrative-safety extension to `_backfill_state_md_placeholders`) — captured separately; activation gate is its own future cycle.
- F-FUNC-2 (interim SHIPPED-LOCAL-sentence removal mode) — different shape; not touched.
- The trailing-sentence flip helper (`_backfill_state_md`) — separate helper; not in fence.
- The §2 row marker append helper (`_backfill_roadmap_row`) — separate file's helper; not in fence.
- Any historical row sweep (no retroactive `apply_backfill(...)` invocations against v0.4.2 / v0.5.0 / other historical date-in-title rows beyond the new test fixture). Historical rows already manually-touched-up at v0.8.0 / v0.8.1 / v0.10.1; sweep stays deferred to a future cycle if needed.
- Summary-line `**Total shipped:**` count or any other backfill helper.

---

## §7 — HARD HALTs (build-time)

1. **Regex extension breaks existing tests.** If the regex change causes any of the 22 existing BACKFL tests to fail, HARD HALT + surface (don't aggressively patch — surface the regression first per dispatch brief).
2. **Structural impossibility surface.** If the regex extension hits an empirical-recheck wall (e.g., the date conflicts with the class-keyword position such that one regex can't disambiguate), apply the 4-step recheck per `feedback_agent_empirical_recheck_before_halt` then HARD HALT + surface if still impossible.
3. **Out-of-fence edit.** Any edit to `_backfill_state_md_placeholders` or any other helper = HARD HALT (per dispatch brief).
4. **`--amend` use.** Never `git commit --amend`. New corrective commits only.
5. **Telegram-only-channel violation.** Final report flows to the dispatcher; dispatcher routes to Luke.

---

## §8 — Dependencies

- `feedback_build_forward_on_publish_pending` — v0.10.1 SHIPPED PUBLIC 2026-05-14; this PATCH builds against the published predecessor without owner-gate pause.
- `feedback_version_numbers_at_release_time` — version derives at release-time: `next_PATCH(v0.10.1) = v0.10.2`.
- `feedback_scope_descriptive_ac_ids` — AC family `AC.SMLTV.*` (scope-descriptive, not version-packed).
- `feedback_loose_AC_text_fix_AC_not_implementation` — D-SMLTV.1 ruling on F-FUNC-1's "append at-tag suffix" vs AC.SMLTV.1's "preserving the date."
- `feedback_agent_empirical_recheck_before_halt` — HARD HALT #2 guard.
- F-FUNC-1 (FIDRAFT, captured 2026-05-10 v0.8.0 AC.HONEST.4) — the originating capture this PATCH closes.

---

## §9 — Estimated AI-time

| Stage | Estimated | Notes |
|---|---|---|
| Plan-doc + manifest authoring | 10-15 min | Single-cycle PATCH; scope is one regex extension. |
| Source-edit (regex extension + 3 new tests + smoke writeup) | 20-30 min | Per dispatch brief AI-time band. |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` | 5-8 min | Standard sealed-amendment cycle. |
| §13 §status backfill commit | 2-3 min | Single Edit + commit. |
| **Total** | **~37-56 min midpoint ~45 min** | Matches dispatch brief midpoint ~55 min. |

---

## §11 — Authority chain

- F-FUNC-1 FIDRAFT capture (v0.8.0 AC.HONEST.4 halt-and-surface) — the originating defect capture this PATCH closes.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground; version derivation at release-time.
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py:145-198` — the verified location of the regex helpers to extend.
- v0.4.2 row historical shape (`**v0.4.2 SHIPPED LOCAL 2026-05-09**`) verified at v0.8.0 commit `4f1dcf6` — the input variant the regex extension covers.
- Memory rules: `feedback_scope_descriptive_ac_ids.md`, `feedback_plan_before_code.md`, `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_subagent_odd_violation_halt.md` (HARD HALT #3), `feedback_duration_estimation_rubric.md` (§9), `feedback_build_forward_on_publish_pending.md` (§8), `feedback_version_numbers_at_release_time.md` (version derivation), `feedback_loose_AC_text_fix_AC_not_implementation.md` (D-SMLTV.1), `feedback_agent_empirical_recheck_before_halt.md` (HARD HALT #2).

---

## §13 — §status

**Build cycle:** TBD-AT-STATUS-BACKFILL — appended post-seal.

**Plan-doc commits:** TBD-AT-STATUS-BACKFILL — appended post-seal.

### AC verdict matrix

TBD-AT-STATUS-BACKFILL — appended post-seal.

### AI-time actuals

TBD-AT-STATUS-BACKFILL — appended post-seal.

### Halt-and-surface findings

TBD-AT-STATUS-BACKFILL — appended post-seal.

---

## §14 — Method decisions

Plan-doc's §5 names the build-time decisions (D-SMLTV.{1,2,3,4,5}). Each is a deterministic ruling at plan-time; no in-flight builder rulings expected unless a HARD HALT fires.
