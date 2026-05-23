# loam-bafi-stale-test-retire — Retire the stale `start-project`-absence assertion in Batch A's outcome-altitude test

**Status:** plan-doc, plan-before-code. Authored 2026-05-23 by `loam-plan-author` agent (background dispatch).
**Working directory:** `/Users/lukeivers/loam/`.
**Parent capture:** A-PROMOTE-START-PROJECT seal (`389dac7`) — A-PROMOTE's builder honored the "don't touch sealed Batch A test" rule by surfacing the now-stale assertion rather than modifying it. This amendment closes that surfaced finding.
**Predecessor (load-bearing):** A-PROMOTE seal `389dac7` (`chore(seals): PATCH — Promote /start-project SKILL to discoverable subdirectory shape; close the silent v0.1.7 AC.LAYERED.2 divergence regression.`); current main HEAD `120c16d` (`docs(plans): record amendment #147 commit SHAs in method-decision register`) is the BASELINE.
**Quality bar:** PATCH-class, test-only; single-file fence (`plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py`); no behavior change for any production code path; no source-code edits; one targeted test assertion removal.

---

## §1. Objective / Summary / TL;DR

Retire the single stale `assert "start-project" not in body` assertion at lines 71-75 of `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py::test_AC_BAFI_ARCH_skills_section_reflects_current_reality` so the loam-skills component seal-test passes cleanly against the post-A-PROMOTE canonical state. Preserve the function's other 4 assertions which remain load-bearing against current `docs/architecture.md`.

**Pre-flight Tier-0 verification (this turn — every claim re-checked against canonical source):**

| Claim | Tier-0 re-check this turn | Verdict |
|---|---|---|
| Lines 71-75 of the test assert `"start-project" not in body` of `docs/architecture.md` | `Read` of the test file confirms verbatim assertion + AssertionError message naming D-BAFI.START-PROJECT. | **CONFIRMED** |
| The assertion currently fails in canonical | `pytest plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py::test_AC_BAFI_ARCH_... -xvs` → 1 failed, 4 passed; failure is the `start-project` assertion at line 71. | **CONFIRMED — stale-RED** |
| The other 4 assertions in the same function still pass | Same pytest run: 4 passed (the `loam does not ship skills directly` absence + `loam-skills` presence + `dev-sdlc` presence + `_symlink_plugin_skills` presence). | **CONFIRMED — Option A applies, not Option B** |
| `docs/architecture.md` currently DOES contain `start-project` | `grep -n start-project docs/architecture.md` returns lines 104, 257, 286. | **CONFIRMED — A-PROMOTE restored the reference** |
| The other 4 BAFI test functions (INSTALL, PYPROJ, QUICK, DOCS) all pass | Full file pytest: 4 passed, 1 failed; the 4 non-ARCH functions are all green. | **CONFIRMED — no other staleness in the file** |
| A-PROMOTE plan-doc §10 D-SPDISC.BAFI-TEST-COLLISION ratified path (a) — "builder updates the BAFI test as part of this amendment's source-edit commit" | `Read` of `docs/plans/sealed/loam-skills-start-project-discoverable.md:152, 318-320` confirms the autonomous ratification. | **CONFIRMED — this retire amendment is the same semantic correction, just deferred to a follow-on amendment because A-PROMOTE's builder honored a separate "don't touch sealed Batch A test" directive.** |

**Operational-objective test (per `feedback_test_against_operational_objective_before_escalating`):** the operational objective is "restore the loam-skills component seal-test to green by retiring a single stale assertion that asserts a property already-correctly-reversed by A-PROMOTE". No critical-call / public-action / financial decision is in scope. The semantic correctness of the retirement was already ratified at A-PROMOTE plan-author time (D-SPDISC.BAFI-TEST-COLLISION → path (a)). **Autonomous build dispatch** is the right next step after this plan-doc + manifest land.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Ruling |
|---|---|---|
| A-PROMOTE plan-doc §10 D-SPDISC.BAFI-TEST-COLLISION | 2026-05-22 | Autonomous ratification: builder updates the BAFI test in this amendment's source-edit commit (path (a) preferred — single semantic correction). |
| Dispatcher brief (this turn) | 2026-05-23 | Dispatcher confirmed the retire-as-separate-amendment shape after A-PROMOTE's builder surfaced rather than touched the sealed Batch A test. |
| (this plan-doc) | 2026-05-23 | Plan-author records the single-file fence + Option A (surgical assertion removal) over Option B (whole-function deletion) per Tier-0 evidence that the function's other 4 assertions are still load-bearing. |

---

## §2. Scope

### In-scope

1. **`plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py`** — delete lines 71-75 (the single `assert "start-project" not in body, (...)` block including its 4-line failure message). The surrounding test function `test_AC_BAFI_ARCH_skills_section_reflects_current_reality` retains its 4 other assertions (lines 67-70 stale-framing absence, lines 77-80 loam-skills presence, lines 81-84 dev-sdlc presence, lines 85-88 `_symlink_plugin_skills` presence) byte-equivalent. **AC.BAFISTR.RETIRE.**
2. **An audit-trail comment** above the function docstring naming the retirement reason (A-PROMOTE-START-PROJECT seal `389dac7` reversed D-BAFI.START-PROJECT) so future readers can trace why one assertion is missing from the AC.BAFI.ARCH set. Recommended placement: insert as a final paragraph inside the function's docstring at lines 60-64. **AC.BAFISTR.AUDIT.**
3. **Outcome-altitude verification** — the modified `test_AC_BAFI_ARCH_skills_section_reflects_current_reality` passes against canonical `docs/architecture.md` AND the full `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` file passes 5/5. **AC.BAFISTR.S.**

### Out-of-scope (explicitly NOT in this amendment)

1. **Deletion of the entire `test_AC_BAFI_ARCH_skills_section_reflects_current_reality` function** (Option B from the dispatcher brief). Rejected — Tier-0 evidence shows 4 of the 5 assertions are still load-bearing properties of current `docs/architecture.md` (verified this turn). Whole-function deletion would silently drop 4 valid AC.BAFI.ARCH guards.
2. **Editing the other 4 BAFI test functions** (INSTALL, PYPROJ, QUICK, DOCS) — all pass cleanly against current canonical; no staleness in those functions per the full-file pytest this turn.
3. **Editing the AC text in `docs/plans/sealed/loam-doc-consistency-batch-a.md`** for AC.BAFI.ARCH — the sealed plan-doc's AC text describes the post-Batch-A state; A-PROMOTE's seal narrative already records the semantic re-correction with full audit trail at `docs/plans/sealed/loam-skills-start-project-discoverable.md`. Touching sealed AC text is unnecessary additional surface. (Per `feedback_loose_AC_text_fix_AC_not_implementation`: this is NOT a loose-AC case — the original AC text was correct at Batch A's seal time; the corrective is at the test-assertion level, not the AC text.)
4. **Source-code edits** — none. No production module is touched.
5. **Edits to any other component's tree** — fence is loam-skills-only.
6. **Edits to the `SEAL_COMMIT.notes` file** in loam-skills/tests — not load-bearing for this amendment; left as-is.

---

## §3. Sealed-component fence

Single-component fence on **`loam-skills`** (the test file `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` lives under this component's tree). No universal-paths admissions needed beyond `docs/` for the plan-doc + manifest archival to `docs/plans/sealed/` at T1.4.

**Components in fence:** `loam-skills` (seal_test: `plugins/loam-skills/tests/test_no_sealed_amendments.py`; sidecar: `plugins/loam-skills/tests/SEAL_COMMIT`; current sidecar value `d5b022f` per `cat` this turn).

**Out of fence (halt-and-surface trigger):**

- Any edit outside `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` except the plan-doc + manifest under `docs/plans/`.
- Any production source-code edit.
- Any other plugin's tree (dev-sdlc, etc.).
- Any other test file edit.

---

## §4. Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.BAFISTR.RETIRE** | `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py::test_AC_BAFI_ARCH_skills_section_reflects_current_reality` no longer contains the `assert "start-project" not in body` clause (or any other absence-assertion for the `start-project` substring) in its body. The function's other 4 assertions (stale-framing absence, `loam-skills` presence, `dev-sdlc` presence, `_symlink_plugin_skills` presence) remain present and unmodified in substance. | `Bash grep -c 'start-project' plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` returns 0 (or returns only matches inside a docstring/audit-trail comment, never inside an `assert` clause); `Bash grep -c 'loam does not ship skills directly\|loam-skills\|dev-sdlc\|_symlink_plugin_skills' plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` returns ≥4 (preserved). |
| **AC.BAFISTR.AUDIT** | The function carries an audit-trail comment or docstring paragraph naming the retirement reason — at minimum, the substring `A-PROMOTE` or `389dac7` (the A-PROMOTE seal SHA) AND `D-BAFI.START-PROJECT` appear inside the function's docstring or as an inline comment immediately above/inside the function body. | `Bash grep -E 'A-PROMOTE\|389dac7' plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` returns ≥1 match; `Bash grep 'D-BAFI.START-PROJECT' plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` returns ≥1 match; `Read` confirms placement is inside the function's docstring or as a comment in/above the function body (not in a module-level comment unrelated to the function). |
| **AC.BAFISTR.S** | **Outcome-altitude smoke**: the full `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` file passes 5/5 against canonical `docs/architecture.md` (read via the test's production filesystem-walk, no pre-arranged state). The loam-skills component seal-test (`test_no_sealed_amendments.py`) also passes cleanly. RED-on-mutation proof: re-introducing the deleted `start-project` absence assertion causes `test_AC_BAFI_ARCH_skills_section_reflects_current_reality` to fail. | `Bash .venv/bin/python -m pytest plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py -v` returns `5 passed`; `Bash .venv/bin/python -m pytest plugins/loam-skills/tests/test_no_sealed_amendments.py -v` returns green; mutation proof: builder temporarily restores the deleted assertion + reruns + observes RED, then re-applies the deletion. |

**Outcome-altitude AC mark:** `AC.BAFISTR.S` is `outcome-altitude: true` per `feedback_test_outcome_altitude_required` — the production-altitude verification is the BAFI test's own filesystem-walk read of canonical `docs/architecture.md` with no pre-arranged state. The outcome-altitude property is inherited from the AC.BAFI.S contract; this amendment restores it to green rather than introducing a new outcome-altitude surface.

**Method-in-AC test passed (per ODD §2.5):** can each AC be satisfied by a method other than the one I have in mind?
- **AC.BAFISTR.RETIRE** — satisfied by deleting lines 71-75 verbatim OR by commenting them out OR by changing the assertion to a permissive truism. Method is the builder's call; outcome (no surviving `assert "start-project" not in` clause) is fixed.
- **AC.BAFISTR.AUDIT** — satisfied by docstring extension, inline comment, separate sentinel comment block, or commit-message-style narration inside the function body. Method is the builder's call.
- **AC.BAFISTR.S** — satisfied by any pytest run that reports 5 passed; mutation proof can be done via re-edit or via a separate sentinel assertion file. Method is the builder's call.

---

## §5. Build steps

Method-level guidance only; builder's call per ODD §1.1.

1. **Plan-doc + manifest commit** (this file + its manifest YAML).
2. **Test-edit commit** — delete lines 71-75 of `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` + add the audit-trail comment/docstring paragraph (AC.BAFISTR.RETIRE + AC.BAFISTR.AUDIT in a single commit; per-AC split is unnecessary at this scale).
3. **Pre-apply verification run** — `pytest plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py -v` confirms 5/5 passed; mutation proof (temporarily restore the deleted assertion, observe RED, re-apply deletion).
4. **`loam amend apply <manifest>`** (auto-commit; per `feedback_dispatch_explicit_loam_amend_apply`).
5. **Component test run** — `pytest plugins/loam-skills/tests/ -v` (full loam-skills test suite) confirms no regressions.
6. **`loam amend seal --plan-doc docs/plans/loam-bafi-stale-test-retire.md --allow-untracked-globs 'docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md'`** — deterministic seal commit; the `--allow-untracked-globs` flag admits the pre-existing untracked plan-doc that the dispatcher brief named. T1.4 archives this plan-doc + manifest to `docs/plans/sealed/` via the post-#134 `plan_archive.py` integration (Strategy 1 match on full slug `loam-bafi-stale-test-retire`).
7. **§14 backfill** — auto-embedded by `loam amend seal`'s `_finalize` step per amendment #141's decoupled path.

---

## §6. Halt triggers

The build agent **must halt and surface** on:

1. **Pre-edit grep reveals the stale assertion has already been removed** — `Bash grep -c 'assert "start-project" not in body' plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` returns 0 at apply-time. Indicates someone landed the fix between this plan and apply; halt and surface for re-scope (this amendment becomes a no-op or needs different scope).
2. **The other 4 BAFI test functions (INSTALL, PYPROJ, QUICK, DOCS) start failing** at apply-time — indicates additional staleness drift not anticipated by this plan; halt and surface for scope widening ruling (Option A becomes "wider stale-assertion retirement" rather than the single-assertion shape).
3. **A NEW stale assertion appears in `test_AC_BAFI_ARCH_skills_section_reflects_current_reality`** that this plan did not name — beyond the line 71-75 one (e.g., one of the other 4 assertions becomes stale because `docs/architecture.md` drifted further after A-PROMOTE) — halt and surface.
4. **The loam-skills component seal-test (`test_no_sealed_amendments.py`) is missing or relocated** — D-BAFI.FENCE-SHAPE precedent in Batch A's manifest notes this as a possibility; halt and surface for fence-shape ruling.
5. **The `--allow-untracked-globs` admission for `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` is rejected by the seal tool** — surface for an alternate seal-time admission shape.

---

## §7. Ship shape

Single PATCH-class amendment, two ACs (one retirement + one audit-trail) + one outcome-altitude verification AC, one apply/seal cycle. No sub-amendment split — the scope is already minimal and further decomposition adds only coordination overhead (per Lens 5 stopping criterion).

**Estimated AI-time (per `feedback_duration_estimation_rubric`):** 8-12 min midpoint ~10 min. Drivers: 5-line test deletion + 2-3 line docstring extension + apply + seal cycle. Sub-cycle-time amendment.

---

## §8. (reserved — risks / cross-references)

No additional risks beyond §6 halt triggers + §10 below.

**Cross-references:**

- A-PROMOTE plan-doc §10 D-SPDISC.BAFI-TEST-COLLISION + §16 Finding #4: ratified this exact corrective at A-PROMOTE plan-author time.
- Batch A plan-doc §4 AC.BAFI.ARCH + §10 F2: the sealed AC text remains correct at Batch A's seal time; A-PROMOTE's seal narrative records the post-Batch-A re-correction.
- `feedback_loose_AC_text_fix_AC_not_implementation`: NOT applicable here — this is not an AC-too-loose case; it's an assertion-stale-after-locked-amendment-reversed case.

---

## §9. Bookkeeping

- **STATE.md** update at seal time: amendment `loam-bafi-stale-test-retire` sealed; A-PROMOTE-surfaced stale-assertion finding RESOLVED.
- **No FIDRAFT update needed** — the corrective shape was ratified at A-PROMOTE plan-author time; no novel FIDRAFT-worthy pattern surfaced.
- **No roadmap update needed** — PATCH-class, no version-line impact.

---

## §10. Halt-and-surface findings (raised at plan-authoring time)

### F1. Option A (surgical deletion) wins over Option B (whole-function deletion) — Tier-0 evidence.

- **Claim:** Dispatcher brief named two options: A (delete the single stale assertion), B (delete the entire function). The plan-author should choose based on Tier-0 evidence.
- **Evidence:** Full-file pytest this turn returns `4 passed, 1 failed`. The 4 passing assertions (stale-framing absence at line 67-70, `loam-skills` presence at line 77-80, `dev-sdlc` presence at line 81-84, `_symlink_plugin_skills` presence at line 85-88) are all load-bearing properties of current `docs/architecture.md` (grep confirms all 4 substrings present at expected sites). Only the `start-project` absence assertion (line 71-75) is stale.
- **Alternative:**
  - **Option A (recommended):** Surgical removal of lines 71-75 only. Preserves 4 still-valid AC.BAFI.ARCH guards.
  - **Option B:** Delete the whole function. Would silently drop 4 still-valid guards.
- **Decision (autonomous per operational-objective test):** Option A. The operational objective is "restore green seal-test without dropping load-bearing guards"; Option B violates the second clause.

### F2. AC.BAFISTR.AUDIT (audit-trail comment) is on-shape but not strictly required for ODD §2.5 — recommended retention.

- **Claim:** The audit-trail comment (AC.BAFISTR.AUDIT) is a "why" annotation; the strict retirement (AC.BAFISTR.RETIRE) is the load-bearing AC.
- **Evidence:** ODD §2.5 says every line of code/assertion maps to a named AC. A deletion doesn't add a line; it removes one. The audit-trail comment is meta-information for future readers, not an outcome the test verifies.
- **Alternative:**
  - **Option 1 (recommended):** Keep AC.BAFISTR.AUDIT as a separate AC because the comment IS an outcome the test file's reader benefits from. Cost: one extra AC line in §4.
  - **Option 2:** Collapse the audit comment into AC.BAFISTR.RETIRE's verification clause ("retirement is accompanied by a comment naming why"). Slightly muddles the outcome (deletion + comment-presence are different outcomes).
  - **Option 3:** Drop the audit comment entirely; let the seal narrative + git log carry the audit trail.
- **Decision (autonomous):** Option 1. Future readers of the test file (without the seal narrative loaded) benefit from in-file audit context; the marginal cost of a separate AC is trivial.

### F3. No widening required — only one BAFI test function is affected.

- **Claim:** Dispatcher brief halt-trigger: "Plan-author discovers other stale assertions in the same test file beyond the one A-PROMOTE's builder flagged (widen scope; surface)."
- **Evidence:** Full-file pytest this turn: `4 passed, 1 failed`. Only `test_AC_BAFI_ARCH_skills_section_reflects_current_reality::start-project` is stale. INSTALL, PYPROJ, QUICK, DOCS functions all pass cleanly.
- **Alternative:** None — no widening needed.
- **Decision (autonomous):** Single-assertion scope holds; no widening surfaced.

### F4. The sealed Batch A AC.BAFI.ARCH text is NOT modified.

- **Claim:** Per ODD §4 + `feedback_loose_AC_text_fix_AC_not_implementation`, when a test's verification text becomes stale post-build, the choice is sometimes "tighten the AC" (doc-only) rather than alter the test. Here, the choice is the inverse.
- **Evidence:** The Batch A AC.BAFI.ARCH text says "The `start-project` SKILL claim is removed OR replaced with a flat-shape non-discoverability note" — this text was CORRECT at Batch A's seal time. A-PROMOTE later semantically reversed the design decision (start-project SKILL became discoverable via promotion). The test assertion encoding "start-project absent" was correct against Batch A's outcome, then became stale against A-PROMOTE's outcome. This is NOT a loose-AC case; the AC text was outcome-correct at its seal moment.
- **Alternative:**
  - **Option 1 (recommended):** Retire the test assertion only. The sealed Batch A plan-doc + AC text stays untouched; A-PROMOTE's seal narrative (already sealed at `389dac7`) records the post-Batch-A re-correction with full audit trail.
  - **Option 2:** Retire the assertion AND add a parenthetical to Batch A's sealed AC.BAFI.ARCH text noting the post-A-PROMOTE re-correction. Cost: touches a sealed plan-doc for a benefit already captured at A-PROMOTE's seal narrative.
- **Decision (autonomous):** Option 1. Sealed plan-docs are immutable; A-PROMOTE's seal narrative is the canonical audit surface for the post-Batch-A re-correction.

### F5. Untracked-glob admission at seal-time is dispatcher-named — no scope-widening implied.

- **Claim:** Dispatcher brief said "the builder should also seal with `--allow-untracked-globs 'docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md'` for the pre-existing untracked file."
- **Evidence:** `ls docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` confirms the file exists, untracked. The file is unrelated to this amendment's scope (it's a different promote plan-doc for the multi-channel extractor work).
- **Decision:** Plan §5 step 6 carries the seal-time `--allow-untracked-globs` admission verbatim per dispatcher direction. No scope widening; the admission is a seal-mechanics convenience.

---

## §11. (no §11 needed — single-component fence)

---

## §12. Provenance trail

| Claim | Source | Tier |
|---|---|---|
| Test function at lines 60-88 of `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` carries 5 assertions, only line 71-75 stale | `Read` of the test file this turn + `pytest -v` this turn (4 passed, 1 failed; the 1 failure is line 71) | Tier-0 |
| `docs/architecture.md` currently contains `start-project` at lines 104, 257, 286 | `Bash grep -n start-project docs/architecture.md` this turn | Tier-0 |
| A-PROMOTE seal commit SHA is `389dac7` | `git log --oneline -20` this turn returns `389dac7 chore(seals): PATCH — Promote /start-project SKILL to discoverable subdirectory shape` | Tier-0 |
| A-PROMOTE plan-doc §10 D-SPDISC.BAFI-TEST-COLLISION ratified path (a) | `Read` of `docs/plans/sealed/loam-skills-start-project-discoverable.md:152, 318-320` this turn | Tier-0 |
| Batch A AC.BAFI.ARCH text was correct at Batch A's seal time (D-BAFI.START-PROJECT removed the reference) | `Read` of `docs/plans/sealed/loam-doc-consistency-batch-a.md:88-92` + `docs/plans/sealed/loam-doc-consistency-batch-a.manifest.yaml:13-18, 100-107` this turn | Tier-0 |
| loam-skills component sidecar at `plugins/loam-skills/tests/SEAL_COMMIT` reads `d5b022fd4439bad4afecb3f18e6f57188c4aaddb` | `Bash cat plugins/loam-skills/tests/SEAL_COMMIT` this turn | Tier-0 |
| Current main HEAD is `120c16d` | `Bash git rev-parse HEAD` this turn | Tier-0 |
| Untracked file `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` exists | `Bash git status --short` this turn shows `?? docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` | Tier-0 |
| The plan-doc convention (§1-§16 shape + AC ID scope-descriptive) | `Read` of `plugins/dev-sdlc/docs/conventions/plan-docs.md` this turn | Tier-0 |

---

## §13. F2 Ruthless Feedback (honest doubts)

1. **The sequence Batch A → A-FIX → A-PROMOTE → this retire is a 4-amendment ladder for what could have been folded into A-PROMOTE itself.** A-PROMOTE's plan §10 ratified path (a) "builder updates the BAFI test as part of this amendment's source-edit commit" — but at build-time the builder evidently received a separate dispatcher directive ("don't touch sealed Batch A test") that overrode the plan ratification. Either the plan ratification or the dispatcher directive should have surfaced the conflict at dispatch authoring time. **Not actionable in this amendment** — this retire amendment is the right closing move regardless — but worth a FIDRAFT capture for next-cycle dispatcher discipline.

2. **The audit-trail comment (AC.BAFISTR.AUDIT) duplicates information already in the seal narrative + git log.** Three lines of comment for the same information that exists in two other places. The justification (in-file context for readers who don't load the seal narrative) is real but marginal. Builder may choose to skip AC.BAFISTR.AUDIT if scope-tightness preference wins; that's an acceptable build-time call.

3. **A wider-scope alternative not chosen:** convert the 5 BAFI test functions from substring-assertion shape (brittle to architecture.md edits) to AST-walk / section-anchor assertions (robust to wording changes). Out-of-scope here — Tier-0 evidence shows the substring shape is currently green for 4/5 functions; the brittleness only fires when an architecture.md edit semantically reverses a prior assertion (as A-PROMOTE did). FIDRAFT candidate, not this-amendment work.

---

## §16. Halt-and-surface findings

(See §10. Single section; numbering preserved at §10 to keep finding text + decision co-located per the convention recently established in `loam-doc-consistency-batch-a.md` + `loam-skills-start-project-discoverable.md`.)

---

## §17. Plan-doc convention compliance footer

This plan-doc follows the canonical shape per `plugins/dev-sdlc/docs/conventions/plan-docs.md`:

- AC IDs scope-descriptive (AC.BAFISTR.*), not version-packed. Per the 2026-05-09 ratification (Telegram 10644) + `feedback_scope_descriptive_ac_ids`.
- §14 method-decision register placeholder (builder backfills at apply-time; decisions are F1-F5 in §10 above + this amendment has no novel D-* decisions — all builder choices ratified at plan-author time).
- §15 backwards-compat verification (the 4 retained assertions in the modified function plus the 4 other BAFI test functions are the backwards-compat surface; AC.BAFISTR.S verifies green across all 5).
- §16 halt-and-surface findings (see §10).
- Provenance trail (§12) with Tier-tagged citations.
- F2 Ruthless Feedback (§13) named gaps + honest doubts.
- Halt-and-surface-before-build decisions named WITH recommendations per `feedback_summarize_and_surface_decisions`.

---

## §14. Method-decision register (populated at build time)

Placeholders for builder narration; SHAs backfilled by `loam amend seal --plan-doc`. This amendment carries no novel D-* decisions — all builder choices ratified at plan-author time per §10 F1-F5. §14 entries (if any are added by the builder for build-time discoveries) get appended here.

Retire the single stale `assert "start-project" not in body`
assertion at lines 71-75 of plugins/loam-skills/tests/test_AC_
BAFI_S_post_fix_state.py::test_AC_BAFI_ARCH_skills_section_
reflects_current_reality. The assertion encoded Batch A
(amendment #145) decision D-BAFI.START-PROJECT, which removed
the `start-project` reference from docs/architecture.md.
A-PROMOTE-START-PROJECT (amendment #147, seal `389dac7`)
semantically reversed that decision by promoting the SKILL to
discoverable subdirectory shape AND restoring the architecture.
md reference with refined wording naming the subdirectory shape
+ auto-symlink mechanism. From A-PROMOTE's seal forward, the
assertion was stale-RED in canonical; this amendment closes the
surfaced finding A-PROMOTE's builder raised by Option A —
surgical deletion of the single stale assertion, preserving the
function's 4 other still-load-bearing assertions.

AC.BAFISTR.RETIRE — surgical deletion of lines 71-75 only. The
function's other 4 assertions (stale-framing absence, loam-
skills presence, dev-sdlc presence, _symlink_plugin_skills
presence) remain unmodified in substance; full-file pytest at
plan-author time confirmed they are all load-bearing properties
of current docs/architecture.md. Whole-function deletion
(Option B from the dispatcher brief) was rejected per the
evidence.

AC.BAFISTR.AUDIT — audit-trail comment inside the function names
the retirement reason (A-PROMOTE seal `389dac7` + D-BAFI.START-
PROJECT). In-file context for readers who don't load the seal
narrative.

AC.BAFISTR.S — outcome-altitude smoke: full test_AC_BAFI_S_post_
fix_state.py file passes 5/5 against canonical docs/architecture.
md (production-altitude filesystem-walk read, no pre-arranged
state). RED-on-mutation: temporarily re-introduce the deleted
assertion + observe RED + re-apply deletion.

Five plan-author halt-and-surface findings (plan §10) all
surfaced + autonomous-decision-recorded: F1 (Option A wins per
Tier-0 evidence); F2 (AUDIT comment recommended, builder may
collapse); F3 (no widening — only one function affected); F4
(sealed Batch A AC text NOT modified); F5 (seal-time `--allow-
untracked-globs` admission per dispatcher direction).

Test-only amendment; no behavior change for any production code
path; no source-code edits. Composes with A-PROMOTE (closes
surfaced finding) + Batch A (removes now-stale assertion).
Sub-cycle-time amendment.
