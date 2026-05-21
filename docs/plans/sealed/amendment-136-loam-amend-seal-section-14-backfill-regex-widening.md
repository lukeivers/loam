# Amendment #136 — loam-amend seal: section-14 backfill regex widening (root-cause fix)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 (inline by persona, no plan-author agent dispatch — scope is small + outcome is precise).
**Working directory:** `/Users/lukeivers/loam/`.
**Parent capture:** future-ideas-draft entry F-SEAL-§14-HEADING-AUTO-BACKFILL-MISMATCH (2026-05-16, 2nd occurrence at that point); recurred for the 3rd time in amendment #134 (FBM Tier 1 today, expected for the 4th in amendment #135 — that build was halted to land this fix first per owner directive TG 11823).
**Predecessor (load-bearing):** amendment #134 seal at `6125003`.
**Quality bar:** single-component change, 4 ACs + 1 outcome-altitude smoke; no method-in-AC; behavior-preserving widening.

---

## §1. Objective / Summary / TL;DR

Widen the seal-tool's `_backfill_plan_doc_shas` section-header regex so it accepts BOTH the legacy `## 14.` shape (which the tool currently matches) AND the canonical plan-doc-convention `## §14<separator>` shape (which the tool currently fails to match, forcing every cycle to do a manual section-14 follow-up commit).

The fix is a one-line regex change + error-message update + tests. Behavior-preserving for plan-docs using the legacy shape; behavior-additive for plan-docs using the canonical shape.

**Why now (per owner directive TG 11823):** the issue has hit 3+ amendment cycles (May 16 capture + amendment #134 today + expected #135). Continuing to dispatch builds with "manual fallback expected" is the autopilot-past-recurring-issue pattern the new `feedback_pause_and_fix_recurring_issues_before_continuing` memory rule prohibits.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T16:14:01Z | Build-strategy delegation (this is a build-strategy detail — regex widening is method-decision territory). |
| TG 11823 | 2026-05-21T17:48:40Z | Pause-and-fix-recurring-issues directive — this amendment IS the immediate application. |
| TG 11825 | 2026-05-21T17:50:48Z | Owner confirmation of course-correction. |

**Pre-flight verification (per `feedback_verify_fidraft_against_canonical_before_dispatch` + `feedback_verify_component_paths_in_dispatch_briefs`):**

- `ls /Users/lukeivers/loam/plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` — exists.
- The regex at line 338 (`section_header_re = re.compile(r"^## 14[.\s]", re.MULTILINE)`) is the single match-site for the §14 heading lookup.
- No other section-N regex in seal.py needs the same treatment (verified via grep).
- F-PLAN-DOC-TEMPLATE-§13-STATUS-HEADING (the sibling FIDRAFT entry) is a separate code path and out-of-scope for this amendment.

---

## §2. Scope

**In-scope:**
- Widen the regex in `_backfill_plan_doc_shas` to accept `## §?14[.\s—]` (or equivalent that accepts both the legacy and canonical heading shapes).
- Update the failure-message text (currently says "no '## 14.' heading") to reflect the widened acceptance.
- Update or add tests so the regex-widening is verified at the AC.LAS14R.1-4 level.

**Out-of-scope:**
- Any other section-N regex in seal.py (none currently exist that need widening).
- The sibling F-PLAN-DOC-TEMPLATE-§13-STATUS-HEADING issue (different code path; separate amendment if needed).
- Any rename of the plan-doc convention (the FIDRAFT recommended widening the scanner instead).

---

## §3. Sealed-component fence (single-component)

**Component touched:** `plugins/dev-sdlc/tools/loam-amend/` ONLY.

**Universal admissions:**
- `docs/plans/` (this plan-doc + manifest; archives to `docs/plans/sealed/` on seal per T1.4).

**Out of fence (halt-and-surface trigger):**
- Any other component under `framework/` or `plugins/`.
- Any other tool under `plugins/dev-sdlc/tools/`.

---

## §4. Acceptance criteria

- **AC.LAS14R.1** — The widened regex matches `## §14<separator>` heading shapes (canonical plan-doc convention).
- **AC.LAS14R.2** — The widened regex STILL matches `## 14<separator>` heading shapes (backwards-compat with any pre-canonical plan-docs).
- **AC.LAS14R.3** — Synthetic seal-cycle of a plan-doc whose section-14 heading is `## §14 — Method-decision register` succeeds the auto-backfill without manual fallback; the `### Commit SHAs` subsection appears under that heading; no `plan-doc-missing-section-14` checkpoint fires.
- **AC.LAS14R.4** — The failure-message text (when section-14 IS genuinely missing) names BOTH accepted shapes, not just `## 14.`.
- **AC.LAS14R.S** — Outcome-altitude smoke: end-to-end `loam amend seal --plan-doc <p>` against a fixture plan-doc using the canonical `## §14 — ...` heading produces a clean seal commit + a `### Commit SHAs` follow-up commit, both deterministic, with no manual operator intervention.

---

## §5. Build steps

1. **Plan-doc lands** (this file) + manifest YAML.
2. **Source edit:** `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` — change the regex on line 338 to accept both shapes; update the error message at line 345 to reflect.
3. **Tests authored:**
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_LAS14R_1_canonical_section_matches.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_LAS14R_2_legacy_section_still_matches.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_LAS14R_3_synthetic_seal_succeeds.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_LAS14R_4_error_message_names_both_shapes.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_LAS14R_S_smoke.py`
4. **Touched-tests run.** Touched + the existing `test_seal.py` family (which exercises the backfill code path).
5. **`loam amend apply`** — auto-commit per ergonomics.
6. **`loam amend seal --plan-doc <this-doc>`** — eats its own dog food: the seal's own backfill step uses the NEWLY-WIDENED regex against THIS plan-doc's `## §14` heading. If the build is correct, NO manual fallback is needed for this seal itself.
7. **D1 cold-state smoke:** fresh workspace + plan-doc with canonical heading → seal succeeds with auto-backfill.

---

## §6. Ship shape

Single cycle, single component. Commit ladder:

1. Plan-doc + manifest commit (this file).
2. Source-edits commit — `fix(loam-amend): widen seal section-14 backfill regex to accept canonical heading shape`.
3. `loam amend apply` auto-commit.
4. `loam amend seal --plan-doc` deterministic seal commit (which itself uses the new regex on this plan-doc — first dogfood).

If the regex widening is correct, NO §14 backfill follow-up commit is needed for this amendment — the auto-backfill works on the canonical heading. That's the proof-of-fix.

---

## §7. Halt triggers (in-flight)

1. Source edits leak outside `plugins/dev-sdlc/tools/loam-amend/`.
2. The regex change breaks any existing test in `test_seal.py` family that wasn't anticipated (pre-existing fixtures use the legacy shape; widening must remain backwards-compat).
3. The seal-time dogfood at step 6 fails — would indicate the widening doesn't actually fix the production code path; halt and surface.
4. A surprising second regex appears in seal.py that ALSO matches section-14 (would suggest the architecture has more than one match site and we'd need a broader fix).

---

## §10. F2 Ruthless Feedback (honest doubts)

1. **Regex over-matching.** Widening `## 14[.\s]` to `## §?14[.\s—]` could in principle over-match malformed headings like `## §14` followed by trailing text on the same line. Mitigated by the `[.\s—]` separator class — at least one separator must follow.
2. **Multi-byte em-dash handling.** If the convention uses `—` (U+2014) and the regex needs to match it explicitly, the regex needs to handle UTF-8 correctly. Mitigated by Python's default unicode-aware regex compilation.
3. **The fix doesn't address the sibling §13 issue** (F-PLAN-DOC-TEMPLATE-§13-STATUS-HEADING). That's a separate code path; out of scope here. If it recurs, separate amendment.

---

## §14. Method-decision register

**Ratification table (recorded at plan-doc commit time):**

| Decision | Recommendation | Ratified by | Authority |
|----------|----------------|-------------|-----------|
| D-LAS14R.REGEX | `^## §?14[.\s—]` — accept `## 14`, `## §14`, and both with `.` `<whitespace>` or `—` as separator | persona | Owner build-strategy delegation TG 11808 + pause-and-fix-recurring-issues directive TG 11823 |

**Rationale:** the canonical plan-doc convention uses `## §14 — Method-decision register` (em-dash separator). The legacy form `## 14.` was also occasionally used in older plan-docs. The widened regex accepts both shapes by making the `§` optional and the separator class `[.\s—]`. Behavior is backwards-compatible (every previous successful match still matches) and additively accepts the canonical form.

---

## §17. Composition (M5 derivation line)

- **Composes with** `feedback_workaround_masks_rootcause_urgency` — this amendment IS the urgent root-cause fix the rule predicts at 3+ recurrence.
- **Composes with** `feedback_pause_and_fix_recurring_issues_before_continuing` (today's capture) — this amendment IS the operational instance of that discipline.
- **Composes with** amendment #134 (just-sealed FBM Tier 1) — Tier 1's T1.4 plan-archive-on-seal moves this plan-doc to `docs/plans/sealed/` on seal, second user of T1.4 after Tier 1 itself.
- **Composes with** `feedback_critical_thinking_on_deviations` — the workaround was a deviation; this is the evaluate-and-fix response.
- **Closes** the F-SEAL-§14-HEADING-AUTO-BACKFILL-MISMATCH future-ideas-draft entry.
- **Independent of** F4.
