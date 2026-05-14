# Release-backfill helpers completeness batch PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: dispatch brief from dispatcher 2026-05-14 explicitly bundles three FIDRAFT-captured gaps (F-FUNC-2 + F-WALKER-1 + F-FUNC-3) — all three captured-only, all three with activation gate "next release-CLI cycle OR pre-v1.0 sweep." This PATCH executes that bundle.
**Slug:** `release-backfill-helpers-completeness-batch` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-14.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Three orthogonal defect closures inside the v0.7.x backfill helper family — interim-sentence removal mode, pipe-row tokenizer robustness, narrative-safe TBD anchoring. No new outcome capability — same outcome shapes (state backfill on publish; row classification; placeholder backfill) extended to handle previously-corrupting inputs without manual touch-up. No public API changes; all three fixes are helper-internal.
**Predecessor:** v0.10.2 PATCH SHIPPED PUBLIC (sealed `ee1f5ac`; published `a66b16a`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.2) = v0.10.3`. Plan-doc slug scope-descriptive (no version pre-baked); AC family scope-descriptive (`AC.RBHCB.*` for `release-backfill-helpers-completeness-batch`).

---

## §1 — Outcome shape (the "why")

Three FIDRAFT-captured gaps in the v0.7.x post-publish backfill helper family at `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` — each one a narrow defect within an already-shipped helper that requires manual touch-up at publish time when triggered. All three have been hit empirically in past cycles (v0.8.0 / v0.8.1 / v0.10.1 manual edits document the operator burden). This PATCH closes the bundle in one cycle.

### F-FUNC-2 — interim-shipped-local removal mode

`apply_backfill` correctly skips the trailing-claim flip when a SHIPPED-PUBLIC marker already exists for the version (idempotence). But when the row also still carries the stale interim `<version> SHIPPED LOCAL — owner gates publish.` sentence (recorded at SHIPPED-LOCAL time, never cleaned up because the public-marker landed manually before v0.7.3's auto-backfill existed), the helper leaves the stale sentence in place — leading to an internally-contradictory row. v0.8.0 manually removed this for v0.5.0 (AC.HONEST.5); the cleanup pattern needs automation.

**Extension shape:** when `_already_public_in_state_md(body, version)` is True AND the SHIPPED-LOCAL trailing sentence is still present in the same body, remove the stale sentence (plus its preceding whitespace) so the row reads coherently. Idempotent: re-run on already-cleaned body is a no-op.

### F-WALKER-1 — pipe-in-description tokenizer robustness

`_classify_row` reads `row.split("|")[3]` as the classification cell. Rows whose description (cell [2]) contains backtick-wrapped pipes (e.g., v0.4.2's `` `Y` → `Union[X, Y]` / `Optional[X]` ``) cause split to over-segment; cell [3] becomes the SECOND segment of the description rather than the actual class cell. v0.8.1 added a version-pattern fallback (X.Y.0 = MINOR; rest = PATCH) which incidentally produced the correct answer for v0.4.2 because v0.4.2 IS a patch. But the explicit-class detection path is still wrong, and any row whose true class disagrees with the version-pattern fallback would misclassify silently.

The same tokenizer bug affects `_extract_objective_sentence` (also uses `row.split("|")` to read cell [2]). The objective-sentence cell would be truncated mid-description if backtick-wrapped pipes appear before the natural end of cell [2].

**Extension shape:** introduce a backtick-parity-aware pipe tokenizer; replace both `row.split("|")` callsites in `_classify_row` and `_extract_objective_sentence`. Per F-WALKER-1 capture: state-machine tokenizer that tracks backtick parity is the cleanest shape. Existing version-pattern fallback in `_classify_row` stays as defense-in-depth.

### F-FUNC-3 — narrative-safety extension for placeholder backfill

`_backfill_tbd_placeholders` uses non-boundary-aware `new_row.replace("TBD-AT-SEAL", f"\`{seal_sha[:7]}\`")` (and the same shape for TAG / COMMIT / APPLY). STATE.md rows whose prose narrative contains literal `TBD-AT-*` strings — e.g., the v0.7.3 row at `docs/STATE.md:133`, whose body describes what the v0.7.3 auto-backfill helper itself does (specifically the prose `` backfills `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders from known SHAs `` and `` (`TBD-AT-COMMIT` / `TBD-AT-APPLY` not discoverable from runner inputs — left alone) ``) — get corrupted. v0.10.1 Path-A halted specifically on this; Path-B shipped manual surgical edits and captured the gap as F-FUNC-3.

**Extension shape:** anchor each TBD-AT-* placeholder match to its canonical surrounding token via regex lookbehind, so unanchored prose-narrative occurrences are left untouched. Per the FIDRAFT capture: `TBD-AT-SEAL` is preceded by `seal ` in canonical emission; `TBD-AT-COMMIT` by `source-edit `; `TBD-AT-APPLY` by `apply `; `TBD-AT-TAG` by `tag ` (the §2-row marker context). Backtick-wrapped occurrences in prose narrative (`` `TBD-AT-SEAL` `` etc.) lack the canonical prefix word and are skipped.

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ post-publish auto-backfill correctly handles every
                STATE.md / roadmap row variant currently in use
                without operator manual touch-up
                  └─ AC.RBHCB.1 (interim-shipped-local sentence removed
                                  when SHIPPED-PUBLIC marker already
                                  exists — closes F-FUNC-2)
                  └─ AC.RBHCB.2 (backtick-aware pipe tokenizer
                                  classifies + extracts cells correctly
                                  even when description carries
                                  backtick-wrapped pipes — closes
                                  F-WALKER-1)
                  └─ AC.RBHCB.3 (TBD-AT-* placeholder backfill anchored
                                  to canonical surrounding token; prose
                                  narrative containing literal TBD-AT-*
                                  strings preserved — closes F-FUNC-3)
                  └─ AC.RBHCB.4 (idempotence preserved across all three
                                  extensions; existing 25 BACKFL tests
                                  pass unmodified)
                  └─ AC.RBHCB.5 (synthetic-fixture dogfood probes
                                  verify each sub-scope at function-
                                  altitude)
                  └─ AC.RBHCB.S (seal-diff: helper extensions + new
                                  test cases + universal-admission
                                  docs only)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — closes three manual-touch-up surfaces a contributor would otherwise have to know about. After this PATCH, no operator running `apply_backfill(...)` against rows hit by any of the three corruption patterns needs to fall back to manual edits.
- **Harness test** — extends three helpers in the post-publish-backfill toolkit the primary persona invokes via `loam release`. Wider input coverage = more reliable harness primitive.

Composes with: F-FUNC-2 / F-WALKER-1 / F-FUNC-3 (this PATCH closes all three captured-only surfaces; FIDRAFT entries get marked RESOLVED in §status). Composes with: `feedback_loose_AC_text_fix_AC_not_implementation` — F-FUNC-2's proposed "optional `--remove-interim-shipped-local-sentence` mode (or equivalent kwarg)" framing differs from AC.RBHCB.1's outcome shape: D-RBHCB.1 ratifies that the cleanup runs unconditionally inside `_backfill_state_md` whenever the trigger condition (already-public AND stale-LOCAL-sentence-present) holds, with no kwarg gate. The kwarg in the FIDRAFT capture was an implementation suggestion, not an outcome requirement; the outcome is "stale interim sentence removed when stale" and that fires automatically.

---

## §3 — Component fence

**Single-component PATCH.** Seal anchor: dev-sdlc (the canonical seal-anchor for release-CLI single-component changes; matches v0.7.3 / v0.7.4 / v0.8.2 / v0.8.3 / v0.10.2 precedent).

**PRIMARY (3 files):**

- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` — three orthogonal extensions:
  1. F-FUNC-2: extend `_backfill_state_md` so when `_already_public_in_state_md` is True AND `_shipped_local_pattern` matches, remove the matched sentence (plus preceding whitespace) and return a non-None edit summary; introduce a small helper if it sharpens readability.
  2. F-WALKER-1: introduce `_split_pipe_row_backtick_aware(row)` helper that respects backtick parity; replace `row.split("|")` in `_classify_row` and `_extract_objective_sentence`. Existing version-pattern fallback stays.
  3. F-FUNC-3: replace `str.replace` calls in `_backfill_tbd_placeholders` with regex matches anchored to canonical surrounding tokens (lookbehind for `seal ` / `source-edit ` / `apply ` / `tag `).

- `framework/tools/loam/tests/test_AC_BACKFL.py` — append new test cases per sub-scope. Minimum per sub-scope: one positive + one regression / idempotence + (for FN-3) one narrative-preservation. Final count: ~7-9 new tests across the three sub-scopes (builder's call on exact decomposition; the dispatch brief floor is "at least one positive + one idempotence + one regression test" per sub-scope).

- `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` — slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`. Doc-only short smoke writeup with one dogfood probe per sub-scope (synthetic fixture per sub-scope; verbatim post-call body excerpts).

**SECONDARY (admin docs — universal-admission):**

- `docs/STATE.md` — append v0.10.3 row to §2.
- `docs/release-roadmap.md` — append v0.10.3 row to §2 + v0.10.3 standalone bold entry to §3 Active version.
- `docs/FUTURE_IDEAS_DRAFT.md` — flip F-FUNC-2 + F-WALKER-1 + F-FUNC-3 entries to RESOLVED (status flips; entries preserved for audit trail).

**TERTIARY (cycle bookkeeping):**

- `docs/plans/release-backfill-helpers-completeness-batch.md` — this file.
- `docs/plans/release-backfill-helpers-completeness-batch.manifest.yaml` — schema-v3 manifest.

**Out of fence:**

- `_backfill_state_md_leading_title` (just shipped in v0.10.2 as F-FUNC-1; do not modify — explicit dispatch HARD HALT).
- Any `__version__` bumps outside the standard release-CLI machinery's publish-flow files (PATCH discipline: no bumps).
- The `acs-verified` gate parser (separate concern; v0.7.2 / v0.8.3 territory).
- pyproject.toml or `__version__` bumps (PATCH rides predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 precedent).
- Edits outside fence = halt.

---

## §4 — Acceptance criteria (`AC.RBHCB.*`)

Each AC maps to a verifiable acceptance signal. Method stays builder's call.

### AC.RBHCB.1 — Interim SHIPPED-LOCAL sentence removed when SHIPPED-PUBLIC marker exists

When `apply_backfill` is invoked against a STATE.md body where (a) the SHIPPED-PUBLIC marker for *version* is already present (so the trailing-claim flip path normally idempotently no-ops) AND (b) the stale interim `<version> SHIPPED LOCAL — owner gates publish.` sentence (or em-dash variant) is still present in the same body, the helper removes the stale sentence (plus its preceding whitespace) and returns a non-None edit summary naming the removal. Idempotent: re-run on already-cleaned body is a no-op (helper returns None for the trailing-sentence path). Closes F-FUNC-2.

**Verdict GREEN if:** new positive test case asserts post-call STATE.md body no longer contains the stale `<version> SHIPPED LOCAL — owner gates publish.` sentence AND the SHIPPED-PUBLIC marker is preserved verbatim AND the helper returned a non-None summary mentioning "removed" / "stale" / "interim". Idempotence test asserts second invocation against the cleaned body is a no-op (no further edits).

**Verdict YELLOW if:** removal happens but mangles surrounding whitespace (e.g., leaves a doubled space or a leading-blank line) — precision fault.

**Verdict RED if:** stale sentence not removed OR SHIPPED-PUBLIC marker corrupted OR canonical (no-public-marker-yet) trailing-claim flip regresses.

`outcome-altitude: false` (function-altitude test; verification is the assertion).

### AC.RBHCB.2 — Backtick-aware pipe tokenizer

`_classify_row` and `_extract_objective_sentence` use a backtick-parity-aware pipe tokenizer that does NOT split on `|` characters appearing inside paired backticks. For a §2 row whose description (cell [2]) contains backtick-wrapped pipes (e.g., `` | v0.4.2 | desc with `Y` → `Union[X, Y]` / `Optional[X]` | Single-cycle PATCH: ... | ``), the tokenizer returns the same cell-count as a row without backtick-pipes; cell [3] is the actual class cell; cell [2] is the full unaltered description string. Existing version-pattern fallback in `_classify_row` is retained as defense-in-depth. Closes F-WALKER-1.

**Verdict GREEN if:** new positive test case constructs a §2 row with backtick-wrapped pipes in the description; `_classify_row(row)` returns the explicit-class value (e.g., "PATCH") via the FIRST detection path (third pipe-cell) — NOT via the version-pattern fallback. Verified by constructing the row with an explicit class keyword in the third cell that *contradicts* what the fallback would derive (e.g., `v0.4.0` would fallback-classify as MINOR; row with backtick-pipes in description AND third cell containing "PATCH" should classify as PATCH via the backtick-aware tokenizer). Companion test asserts `_extract_objective_sentence(row)` returns the full description text (not the truncation that naive split would yield).

**Verdict YELLOW if:** tokenizer correctly returns matching cell counts but the class-classification still relies on the fallback (i.e., the explicit-class path didn't engage but the answer happens to be right) — partial-fix fault detectable by the contradiction-shape positive test.

**Verdict RED if:** existing tokenizer tests regress (rows without backtick-pipes still split correctly) OR backtick-wrapped pipes still trigger over-segmentation OR fallback path stops firing for legitimate fallback cases.

`outcome-altitude: false` (function-altitude test).

### AC.RBHCB.3 — TBD-AT-* placeholder backfill anchored to canonical surrounding context

`_backfill_tbd_placeholders` matches each TBD-AT-* placeholder only when preceded by its canonical surrounding token (`seal ` for TBD-AT-SEAL; `source-edit ` for TBD-AT-COMMIT; `apply ` for TBD-AT-APPLY; `tag ` for TBD-AT-TAG). Occurrences inside backtick-wrapped prose narrative (e.g., `` `TBD-AT-SEAL` `` in a row body describing what the helper does) are NOT replaced because they lack the canonical preceding token. Closes F-FUNC-3.

**Verdict GREEN if:** new positive test case constructs a row with both the canonical placeholder context (e.g., "seal TBD-AT-SEAL") AND a prose-narrative reference (e.g., `` backfills `TBD-AT-SEAL` and `TBD-AT-TAG` placeholders ``). Post-`_backfill_tbd_placeholders` call: the canonical-context occurrence is replaced with the SHA; the prose-narrative occurrences remain literal. Negative test verifies a row with ONLY prose-narrative TBD-AT-* references is unchanged. Existing `test_apply_backfill_backfills_state_md_seal_placeholder` and `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd` continue to pass unmodified.

**Verdict YELLOW if:** anchoring works for some but not all four placeholders (e.g., TBD-AT-SEAL anchored but TBD-AT-TAG still uses str.replace) — incomplete-fix fault.

**Verdict RED if:** prose-narrative occurrences still corrupted OR canonical-context occurrences no longer matched OR existing TBD backfill tests regress.

`outcome-altitude: false` (function-altitude test).

### AC.RBHCB.4 — Idempotence + regression preserved

All 25 existing BACKFL tests pass unmodified post-source-edit. Each sub-scope's helper extension preserves the existing idempotent-noop contract: re-running `apply_backfill` against already-current state still returns `BackfillResult(idempotent_noop=True, edits_applied=0)` and writes nothing. The integration test `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd` (which exercises all three helpers in one invocation) continues GREEN.

**Verdict GREEN if:** `pytest framework/tools/loam/tests/test_AC_BACKFL.py` post-source-edit reports 25 existing tests pass + new tests added; no existing test was modified to accommodate. Total test count rises from 25 to N (new test count visible in the diff).

**Verdict RED if:** any existing test breaks OR any existing test required modification to keep passing OR the integration test's idempotence re-run no longer returns `idempotent_noop=True`.

`outcome-altitude: false` (regression check; verification is the test run).

### AC.RBHCB.5 — Outcome-altitude dogfood probe

Synthetic-fixture dogfood probe per sub-scope (three probes total) documented at `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`). Each probe: (a) constructs a synthetic input that hits the historical corruption pattern; (b) invokes the relevant helper(s) directly via `.venv/bin/python -c`; (c) reports verbatim before/after body excerpts confirming the fix. The combined probes serve as the function-altitude evidence the helper extensions land their target outcome shapes against realistic inputs.

**Verdict GREEN if:** smoke writeup at the slug-named path exists; contains three labeled probes (one per sub-scope); each probe reports verbatim before/after excerpts AND a one-sentence verdict line.

**Verdict RED if:** smoke writeup missing OR any of the three probes handled incorrectly OR writeup omits verbatim evidence OR file is at version-prefixed path instead of slug-named (would re-trigger the F-CYCLE-ARTEFACT-SLUG-NAMING discipline failure).

`outcome-altitude: true` (dogfood probe at function-altitude against realistic synthetic inputs).

### AC.RBHCB.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (three helper extensions)
- `framework/tools/loam/tests/test_AC_BACKFL.py` (new test cases per sub-scope)
- `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (slug-named smoke writeup)
- `docs/STATE.md` (v0.10.3 §2 row admin)
- `docs/release-roadmap.md` (v0.10.3 §2 row + v0.10.3 §3 entry admin)
- `docs/FUTURE_IDEAS_DRAFT.md` (F-FUNC-2 + F-WALKER-1 + F-FUNC-3 status flips to RESOLVED)
- `docs/plans/release-backfill-helpers-completeness-batch.md` (this plan-doc)
- `docs/plans/release-backfill-helpers-completeness-batch.manifest.yaml` (manifest)
- `plugins/dev-sdlc/seals/SEAL_COMMIT.release-backfill-helpers-completeness-batch` (seal narrative)
- `plugins/dev-sdlc/tests/SEAL_COMMIT` (sidecar bump)
- `framework/per-project-pm/state/SEAL_COMMIT.dev-sdlc` (per-project-pm sidecar, if applicable)

NO entries elsewhere in `framework/tools/loam/`, no other helper modifications (specifically NOT `_backfill_state_md_leading_title` per dispatch HARD HALT), no pyproject.toml or `__version__` bumps.

**Verdict GREEN if:** diff matches the allow-list above.
**Verdict RED if:** any out-of-fence file appears in the diff.

`outcome-altitude: false` (structural).

---

## §5 — Decisions builder rules at build time

- **D-RBHCB.1 (F-FUNC-2 trigger).** AC.RBHCB.1's outcome shape is "stale interim sentence removed when both conditions hold (already-public AND stale-LOCAL-sentence-present)" — fires unconditionally when triggered, no kwarg gate. F-FUNC-2 capture proposed an `--remove-interim-shipped-local-sentence` mode kwarg; that's an implementation suggestion, not an outcome requirement. Per `feedback_loose_AC_text_fix_AC_not_implementation`, the dispatch AC tightens the F-FUNC-2 framing: removal is automatic. The cleanup runs inside `_backfill_state_md` after the existing `_already_public_in_state_md` short-circuit; if SHIPPED-LOCAL trailing sentence still matches, remove it. Builder may extract a small helper (`_remove_stale_interim_sentence` or similar) if it sharpens readability OR keep the logic inline in `_backfill_state_md` — method stays builder's call.
- **D-RBHCB.2 (F-WALKER-1 tokenizer strategy).** Use a state-machine tokenizer that walks the row character-by-character tracking backtick parity (toggle a boolean on each backtick; emit a cell on each `|` only when parity is 0). Single-pass, no regex backtracking surprises. Edge cases: nested backticks (the tokenizer treats each backtick as a parity toggle, so `` ``code`` `` opens-and-closes on the first pair; nested backticks are rare in real STATE.md prose). Empty cells are preserved as empty strings (matches `str.split("|")` semantics for cell counting). Single helper `_split_pipe_row_backtick_aware(row) -> list[str]` lives next to `_classify_row` for visibility. Builder may inline the state machine as a single function OR split into a generator + list-builder — method stays builder's call.
- **D-RBHCB.3 (F-FUNC-3 anchor strategy).** Each TBD-AT-* placeholder gets a regex matcher with a positive lookbehind for its canonical preceding token. The four canonical tokens, verified from the existing fixture string in `_state_md_with_shipped_local(with_v074_gap_surfaces=True)` and `_roadmap_with_shipped_local_row(with_v074_gap_surfaces=True)`:
  - `TBD-AT-SEAL` ← preceded by `seal ` (e.g., `seal TBD-AT-SEAL`)
  - `TBD-AT-COMMIT` ← preceded by `source-edit ` (e.g., `source-edit TBD-AT-COMMIT`)
  - `TBD-AT-APPLY` ← preceded by `apply ` (e.g., `apply TBD-AT-APPLY`)
  - `TBD-AT-TAG` ← preceded by `tag ` (the §2 row marker context — historical roadmap shape; `tag \`<version>\`` form). Note: TBD-AT-TAG is rarely encountered in current fixtures because `_format_row_marker_suffix` emits the resolved tag directly; the placeholder appears mainly in legacy hand-authored rows. The lookbehind anchors to `tag ` permissively; backtick-wrapped prose-narrative occurrences (`` `TBD-AT-TAG` ``) lack the prefix and are skipped.
  Pattern shape: `(?<=seal )TBD-AT-SEAL\b` (and analogously for the other three). The trailing `\b` is a word boundary so accidental partial matches are blocked. Per AC.RBHCB.3 the canonical `_state_md_with_shipped_local(with_v074_gap_surfaces=True)` fixture continues to backfill correctly (canonical context preserved); prose-narrative TBD-AT-* references in the same row body would NOT match (no `seal ` / `source-edit ` / `apply ` / `tag ` prefix in their backtick-wrapped form).
- **D-RBHCB.4 (test-decomposition).** New tests append to `test_AC_BACKFL.py` (not a new file) per the v0.10.2 / v0.8.1 / v0.7.4 precedent. Each sub-scope gets its own marker-comment-block with the AC tag in the header for grep-ability. Builder picks exact test count per sub-scope; floor per dispatch brief is one positive + one idempotence + one regression. Recommended decomposition (final count is builder's call):
  - F-FUNC-2: 2 tests — positive (already-public + stale-LOCAL → cleaned); idempotence (already-cleaned → no-op).
  - F-WALKER-1: 3 tests — positive backtick-pipe classification (explicit-class-via-tokenizer, contradicts-fallback shape); positive backtick-pipe objective extraction; regression non-backtick rows still classify correctly.
  - F-FUNC-3: 3 tests — positive narrative-preserving (canonical context replaced; prose backtick-wrapped references preserved); negative (only prose narrative → no replacement); regression (canonical pre-image unchanged outcome).
- **D-RBHCB.5 (pyproject versions).** Per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 precedent: per-component-version discipline advances pyproject.toml versions with MINORs; PATCHes ride the predecessor MINOR. v0.10.3 = PATCH-after-v0.10.x; pyproject versions stay at 0.10.0.
- **D-RBHCB.6 (smoke shape).** Doc-only short smoke writeup at `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (SLUG-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`; not version-named). Three function-altitude probes (one per sub-scope) verifying real-input-shape handling. NO full cold-clone or runner-altitude probe (function-altitude is sufficient evidence; matches v0.10.2 + v0.10.1 + v0.7.4 Stage 1 precedent for helper-internal PATCHes).

---

## §6 — Out of scope (explicit)

- `_backfill_state_md_leading_title` (just shipped in v0.10.2 as F-FUNC-1 — explicit dispatch HARD HALT; do not touch).
- Any `__version__` bumps outside the standard release-CLI machinery's publish-flow files (PATCH discipline: no bumps).
- The `acs-verified` gate parser (separate concern; v0.7.2 / v0.8.3 territory).
- Pre-baking version numbers anywhere (slug-only naming for all artefacts).
- `git commit --amend` for any reason.
- Any historical row sweep (no retroactive `apply_backfill(...)` invocations against historical rows beyond the new test fixtures). The 3rd F-NFCLEAN-FOLLOWON item (v0.7.3 STATE.md + roadmap §2 row historical placeholder backfills) MAY become unblocked once F-FUNC-3 lands here, but the unblock itself is a separate cycle; v0.10.3 ships the helper extension only.
- Adding any new AC tag family beyond `AC.RBHCB.*`.

---

## §7 — HARD HALTs (build-time)

1. **Helper extension breaks existing tests.** If any of the 25 existing BACKFL tests fail post-source-edit, HARD HALT + surface (don't aggressively patch — surface the regression first per dispatch brief HARD HALT criteria).
2. **Empirical-recheck wall.** If any sub-scope's extension hits a "structurally infeasible" wall (e.g., backtick parity tracking conflicts with markdown-pipe-table escape rules in some way), apply the 4-step recheck per `feedback_agent_empirical_recheck_before_halt` (state conclusion + evidence; generate ≥3 alternative hypotheses; empirically test each in the same env; halt only after the alternatives confirm impossibility), THEN HARD HALT + surface if still impossible. Especially relevant for F-WALKER-1 tokenizer-design choice.
3. **Out-of-fence edit.** Any edit to `_backfill_state_md_leading_title`, `_section_2_row_pattern`, `_state_md_row_pattern`, the `_count_published_versions` walker logic, the `_SUMMARY_LINE` regex, OR any non-test framework code outside `post_publish_backfill.py` = HARD HALT.
4. **`--amend` use.** Never `git commit --amend`. New corrective commits only (per `feedback_no_amend_in_agent_dispatches`). If `loam amend validate` fails after manifest baseline, fix via NEW corrective commit.
5. **Loose-AC trap.** If implementation matches intent but plan-doc AC text is loose (e.g., the F-WALKER-1 contradiction-shape test reveals the AC text doesn't actually pin the explicit-class-path requirement), tighten the AC text doc-only BEFORE claiming GREEN. Per `feedback_loose_AC_text_fix_AC_not_implementation`.
6. **Slug-naming drift.** If autopilot reaches for `v0-10-3-hard-smoke.md` as the smoke writeup name, HARD HALT — slug-named only per `F-CYCLE-ARTEFACT-SLUG-NAMING` (the explicit purpose of the previous cycle's FIDRAFT capture).
7. **Telegram-only-channel violation.** Final report flows to the dispatcher; dispatcher routes to Luke.

---

## §8 — Dependencies

- `feedback_build_forward_on_publish_pending` — v0.10.2 SHIPPED PUBLIC 2026-05-14; this PATCH builds against the published predecessor without owner-gate pause.
- `feedback_version_numbers_at_release_time` — version derives at release-time: `next_PATCH(v0.10.2) = v0.10.3`.
- `feedback_scope_descriptive_ac_ids` — AC family `AC.RBHCB.*` (scope-descriptive, not version-packed).
- `feedback_loose_AC_text_fix_AC_not_implementation` — D-RBHCB.1 ruling on F-FUNC-2's "kwarg mode" framing vs AC.RBHCB.1's "automatic when triggered" outcome.
- `feedback_agent_empirical_recheck_before_halt` — HARD HALT #2 guard for tokenizer-design choice.
- `feedback_no_amend_in_agent_dispatches` — HARD HALT #4 guard.
- `feedback_subagent_odd_violation_halt` — HARD HALT #3 guard.
- `F-CYCLE-ARTEFACT-SLUG-NAMING` (FIDRAFT 2026-05-14) — HARD HALT #6 guard; the prior-cycle FIDRAFT capture this PATCH structurally honors via the slug-named smoke writeup path.
- F-FUNC-2 (FIDRAFT, captured 2026-05-10 v0.8.0 AC.HONEST.5) — the originating capture this PATCH closes for the interim-removal sub-scope.
- F-WALKER-1 (FIDRAFT, captured 2026-05-10 v0.8.1 AC.NFCLEAN.2) — the originating capture this PATCH closes for the tokenizer sub-scope.
- F-FUNC-3 (FIDRAFT, captured 2026-05-13 v0.10.1 plan-time empirical recheck) — the originating capture this PATCH closes for the narrative-safety sub-scope.

---

## §9 — Estimated AI-time

| Stage | Estimated | Notes |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | Three sub-scopes; richer than single-scope PATCH. |
| Source-edit (3 helper extensions + ~7-9 new tests + smoke writeup) | 35-55 min | Per dispatch brief AI-time band (90-180 min total midpoint ~135 min, this is the source-edit-batch share). |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` | 5-10 min | Standard sealed-amendment cycle. |
| §13 §status backfill commit | 3-5 min | Single Edit + commit. |
| **Total** | **~58-95 min midpoint ~75 min** | Within dispatch brief 90-180 min band (lower bound of midpoint). |

---

## §11 — Authority chain

- F-FUNC-2 / F-WALKER-1 / F-FUNC-3 FIDRAFT captures — the three originating defect captures this PATCH closes.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground; version derivation at release-time.
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` — the verified location of all three helper-extension targets (lines 117-138 trailing-sentence flip / lines 422-464 TBD placeholder backfill / lines 546-577 walker classification).
- `docs/STATE.md:133` — the verified live-corruption fixture for F-FUNC-3 (v0.7.3 row body containing literal `TBD-AT-SEAL` / `TBD-AT-TAG` strings inside backticked descriptions).
- v0.4.2 row historical shape for F-WALKER-1 (`v0.4.2`'s description containing `` `Y` → `Union[X, Y]` / `Optional[X]` `` backtick-pipe pattern).
- v0.5.0 row historical shape for F-FUNC-2 (interim sentence manually removed at v0.8.0 cycle per AC.HONEST.5).
- `F-CYCLE-ARTEFACT-SLUG-NAMING` FIDRAFT capture (2026-05-14) — the prior-cycle slug-naming discipline this PATCH honors.
- Memory rules: `feedback_scope_descriptive_ac_ids.md`, `feedback_plan_before_code.md`, `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_subagent_odd_violation_halt.md` (HARD HALT #3), `feedback_duration_estimation_rubric.md` (§9), `feedback_build_forward_on_publish_pending.md` (§8), `feedback_version_numbers_at_release_time.md` (version derivation), `feedback_loose_AC_text_fix_AC_not_implementation.md` (D-RBHCB.1), `feedback_agent_empirical_recheck_before_halt.md` (HARD HALT #2).

---

## §13 — §status

**Build cycle:** SHIPPED LOCAL 2026-05-14. Single-cycle PATCH bundling three FIDRAFT closures (F-FUNC-2 + F-WALKER-1 + F-FUNC-3) via three orthogonal helper extensions inside `post_publish_backfill.py`. Sealed local; awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc + manifest `f57d705`; source-edit (three helper extensions + 9 new tests + slug-named smoke writeup + STATE/roadmap admin + F-FUNC-2/F-WALKER-1/F-FUNC-3 RESOLVED) `f3f6cf1`; manifest baseline backfill `8574113`; apply auto-commit (BASELINE + sidecar bump to `f3f6cf1`) `840ff6d`; seal commit (deterministic seal) `44c28e6`.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.RBHCB.1 — Interim SHIPPED-LOCAL sentence removed | GREEN | New tests `test_apply_backfill_removes_stale_interim_sentence_when_marker_present` + `test_apply_backfill_interim_removal_is_idempotent` at `framework/tools/loam/tests/test_AC_BACKFL.py` pass: synthetic STATE.md body with already-public marker AND stale interim sentence → stale sentence removed (plus single preceding whitespace trimmed); SHIPPED-PUBLIC marker preserved verbatim; leading title PUBLIC marker preserved; idempotence re-run on cleaned body returns None edit_summary. Live dogfood probe at §1 of `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` confirms removal with verbatim post-call body excerpt + edit_summary `STATE.md: removed stale interim sentence 'v0.5.0 SHIPPED LOCAL — owner gates publish.' (SHIPPED-PUBLIC marker already present)`. Implementation per D-RBHCB.1: cleanup runs unconditionally inside `_backfill_state_md` when `_already_public_in_state_md` is True AND the trailing sentence still matches; new helper `_remove_stale_interim_sentence(body, version)` extracted for readability. |
| AC.RBHCB.2 — Backtick-aware pipe tokenizer | GREEN | New tests `test_split_pipe_row_backtick_aware_skips_pipes_inside_backticks` + `test_classify_row_uses_explicit_class_path_with_backtick_pipes` + `test_extract_objective_sentence_preserves_backtick_wrapped_pipes` + `test_classify_row_fallback_still_works_for_marker_less_rows` pass. Implementation per D-RBHCB.2: state-machine tokenizer `_split_pipe_row_backtick_aware(row)` walks character-by-character tracking backtick parity; emits cell on `|` only when parity is 0. Replaces `row.split('|')` in BOTH `_classify_row` and `_extract_objective_sentence`. Existing version-pattern fallback in `_classify_row` retained as defense-in-depth. Contradiction-shape test (v0.4.0 + explicit PATCH in third cell; would fallback to MINOR but explicit-class-path correctly returns PATCH via the tokenizer) confirms the explicit-class detection path engages, NOT the fallback. Live dogfood probe at §2 of smoke writeup confirms naive split returns 6 cells / backtick-aware returns 5 / classification PATCH (would be MINOR via fallback alone). |
| AC.RBHCB.3 — TBD-AT-* anchor to canonical context | GREEN | New tests `test_backfill_tbd_placeholders_preserves_prose_narrative` + `test_backfill_tbd_placeholders_skips_prose_only_rows` + `test_backfill_tbd_placeholders_canonical_context_unchanged_outcome` pass. Implementation per D-RBHCB.3: each TBD-AT-* placeholder gets a regex matcher with positive lookbehind for its canonical preceding token: `TBD-AT-SEAL ← seal `, `TBD-AT-COMMIT ← source-edit `, `TBD-AT-APPLY ← apply `, `TBD-AT-TAG ← tag `. Pattern shape `(?<=seal )TBD-AT-SEAL\b` (and analogously for the other three). Backtick-wrapped prose-narrative occurrences (`` `TBD-AT-SEAL` `` etc.) lack the canonical prefix and are skipped — verified by live dogfood probe at §3 of smoke writeup: synthetic row carrying both `seal TBD-AT-SEAL` (canonical) AND `` `TBD-AT-SEAL` / `TBD-AT-TAG` `` (prose narrative) → only the canonical-context occurrence is replaced; prose narrative preserved verbatim. Existing canonical-context tests (`test_apply_backfill_backfills_state_md_seal_placeholder` + `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd`) continue to pass unmodified. |
| AC.RBHCB.4 — Idempotence + regression preserved | GREEN | All 25 existing BACKFL tests pass unmodified post-source-edit (verified mid-build at commit `f3f6cf1`); 9 new RBHCB tests added (3 per sub-scope average); 34/34 BACKFL tests GREEN; 98/98 release-CLI tests GREEN (89 baseline + 9 new). No existing test was modified to accommodate the helper extensions — all three changes are purely additive (interim-removal extends `_backfill_state_md`'s already-public path which was previously a return-None no-op; tokenizer replaces internal cell-extraction with no API change; TBD anchoring replaces `str.replace` with regex `.sub` of equivalent semantics for canonical-context inputs). The `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd` integration test (which exercises all three helpers in one invocation) continues GREEN. |
| AC.RBHCB.5 — Outcome-altitude dogfood probe | GREEN | `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`) documents three function-altitude probes (one per sub-scope) with verbatim before/after body excerpts + verdict lines. Live invocations via `.venv/bin/python` against synthetic fixtures hitting each historical corruption pattern; all three probes confirm correct fix-target outcome. §5 of the writeup pins the slug-naming compliance (file lives at `<slug>-hard-smoke.md`, NOT `v<version>-hard-smoke.md`). |
| AC.RBHCB.S — Seal-diff discipline | GREEN | `git diff --name-only f57d705..44c28e6` shows changes only under: `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (three helper extensions, ~186 line diff = 164 insertions + 22 deletions), `framework/tools/loam/tests/test_AC_BACKFL.py` (9 new tests, 318 insertions), `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (slug-named smoke writeup), `docs/STATE.md` (v0.10.3 §2 row admin), `docs/release-roadmap.md` (v0.10.3 §2 row + §3 entry admin), `docs/FUTURE_IDEAS_DRAFT.md` (F-FUNC-2 + F-WALKER-1 + F-FUNC-3 RESOLVED status flips), `docs/plans/release-backfill-helpers-completeness-batch.{md,manifest.yaml}` (this plan-doc + manifest), `plugins/dev-sdlc/seals/SEAL_COMMIT.release-backfill-helpers-completeness-batch` (seal narrative), `plugins/dev-sdlc/tests/SEAL_COMMIT` (sidecar bump), `framework/per-project-pm/state/SEAL_COMMIT.dev-sdlc` (per-project-pm sidecar). NO entries in `_backfill_state_md_leading_title` (HARD HALT enforcement preserved); NO pyproject.toml bumps; NO `__version__` updates; NO entries in any non-test framework/plugin source beyond the named release-CLI helper. |

### AI-time actuals

| Stage | Estimated (§9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | ~20 min |
| Source-edit (3 helper extensions + 9 new tests + smoke writeup) | 35-55 min | ~30 min |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` | 5-10 min | ~3 min |
| §13 §status backfill commit + roadmap-row seal-SHA backfill | 3-5 min | ~5 min |
| **Total** | **~58-95 min midpoint ~75 min** | **~58 min** |

In-band — three-helper-extension batch landed cleanly without HARD HALTs; the empirical-recheck discipline never fired (each sub-scope's helper-extension shape was directly inferable from the FIDRAFT capture's proposed-shape line). All 25 existing BACKFL tests preserved unmodified.

### Halt-and-surface findings

**No HARD HALTs fired in-cycle.**

**One minor test-fixture iteration:** the F-WALKER-1 cell-count contradiction-shape test initially asserted `len(row.split("|")) == 7` against a fixture that only contained one backtick-wrapped pipe (yielding 6 cells). Corrected by adding a second backtick-wrapped pipe to the fixture string so the pre-fix bug shape is correctly demonstrated (naive split = 7 cells; backtick-aware = 5 cells). Single Edit; no NEW commit needed (test-authoring iteration within the source-edit batch).

**Slug-naming discipline honored:** the smoke writeup landed at `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (slug-named) on first authoring — the prior-cycle `F-CYCLE-ARTEFACT-SLUG-NAMING` FIDRAFT capture was internalized at dispatch-brief read time. No version-prefix slip.

**Live regression evidence preserved:** all 25 existing BACKFL tests pass at both pre-source-edit baseline (verified at commit `f57d705`) and post-source-edit (verified at commit `f3f6cf1`). 9 new RBHCB tests added; 34/34 BACKFL GREEN; 98/98 release-CLI tests GREEN.

**Dogfood probe evidence:** live `.venv/bin/python` invocations of `_backfill_state_md` / `_classify_row` / `_split_pipe_row_backtick_aware` / `_extract_objective_sentence` / `_backfill_tbd_placeholders` against synthetic fixtures produced output byte-equal to the writeup's expected output. All three sub-scope probes verified at the verbatim level.

**Three FIDRAFT entries flipped to RESOLVED:** F-FUNC-2 (line 248), F-WALKER-1 (line 262), F-FUNC-3 (line 250); each entry preserves its original capture text and adds a RESOLVED block citing this PATCH cycle's plan-doc + smoke writeup paths.

---

## §14 — Method decisions

Plan-doc's §5 names the build-time decisions (D-RBHCB.{1,2,3,4,5,6}). Each is a deterministic ruling at plan-time; no in-flight builder rulings expected unless a HARD HALT fires.
