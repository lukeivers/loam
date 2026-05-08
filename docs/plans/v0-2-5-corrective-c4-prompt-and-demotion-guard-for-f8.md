# v0.2.5 Corrective C4 — synthesis prompt-engineering + demotion-guard for F8

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-05 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.5 corrective C3 (sealed at `89f97c6`; `loam amend seal`-blessed; HEAD at `189c6db`). C3 surfaced F8 BLOCKER via the new outcome-altitude AC.V025-C3.3 — the very test designed to catch this class of failure caught it on first live run.

**Authority:** v0.2.5 corrective C4 dispatch brief. Two-layer fix per dispatcher ruling — prompt-engineering as primary + demotion-guard as safety net. Validator stays strict; the layer between LLM output and validator becomes more disciplined.

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

The C3.3 outcome-altitude test caught F8 on its first live API run: synthesis LLM produces VERIFIED-banded objectives that violate the two-source rule (AC.OBJX.5 — VERIFIED requires evidence in tests AND in either readme excerpts OR design doc refs). Pydantic validator at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py:296-307` correctly rejects them; entire synthesis stage raises StageError → exit 2 → empty objectives.yaml → cascade-fail of AC.HARD.{1,2,3,4,5}.

**Validator is correct per design.** The fix lives at the parsing layer (post-LLM-response, pre-validator) and at the prompt-author layer.

The two-layer approach:

1. **Prompt-engineering (primary).** Strengthen the synthesis system prompt to give the LLM an explicit, unambiguous instruction on banding semantics: VERIFIED requires two sources of evidence; lacking that, demote to PLAUSIBLE. The LLM is told NOT to produce VERIFIED bands without both (tests AND readme/design-doc).

2. **Demotion-guard (safety net).** Even with a tight prompt, LLMs are stochastic. Add a pre-validator pass that scans LLM-returned objectives — for any row banded VERIFIED that lacks both `evidence.readme_excerpts` and `evidence.design_doc_refs`, demote to PLAUSIBLE before validation. Log the demotion explicitly with the objective ID and reason. The PLAUSIBLE band still requires single-source evidence (one of readme/design-doc/survey) — if the row lacks even that, the validator still raises (the guard does NOT swallow malformed rows wholesale; it only handles the band-rule overshoot case).

This is a methodology refinement of AC.OBJX.5's "raise on malformed" — band-rule violations are now demote-able rather than always-raise. Structural malformation still raises.

---

## §2 — ACs — `AC.V025-C4.1` through `AC.V025-C4.5` (locked, 5 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC.

- **AC.V025-C4.1 — Prompt-engineering: synthesis system prompt's banding instruction explicitly forbids VERIFIED-without-two-sources.** **outcome-altitude: false** (prompt-shape AC; verified by inspection + LLM probe).
  - Surface: `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/synthesis.py` `_SYSTEM_PROMPT` constant. The BANDING RULE section is strengthened with an explicit "if you cannot supply both tests AND (readme_excerpts OR design_doc_refs) for an objective, band it as PLAUSIBLE — never produce VERIFIED without two sources" instruction.
  - Test: structural — verify the prompt text contains the explicit two-source-rule reminder (specific phrasing assertable). Verification: `grep` against the prompt text confirms presence of the strengthened phrase.
  - Pre-fix verification: pre-fix the prompt has the BANDING RULE section but lacks the explicit "if you cannot supply X, demote Y" instruction; the LLM is told the rule but not what to do when it cannot satisfy it. Post-fix the prompt includes the explicit demotion guidance.

- **AC.V025-C4.2 — Demotion-guard: pre-validator pass downgrades VERIFIED-without-two-sources to PLAUSIBLE.** **outcome-altitude: false** (parsing-layer AC; verified by unit test against real-shape input).
  - Surface: `synthesis.py` `_validate_rows` (or a new helper `_apply_band_demotion_guard` invoked before per-row `Objective.model_validate`). The guard scans objectives_raw rows; for any row with `confidence == "VERIFIED"` that lacks both `evidence.readme_excerpts` and `evidence.design_doc_refs`, the row's `confidence` is rewritten to `"PLAUSIBLE"` AND a log entry is emitted naming the objective_id + the reason ("LLM produced VERIFIED-band without two sources; demoted to PLAUSIBLE per band-rule guard").
  - Test: NEW unit test `test_AC_V025_C4_2_demotion_guard.py` — given a synthesis response payload with a VERIFIED-banded row missing readme_excerpts AND design_doc_refs (but having tests + repo_sha), the guard demotes the row to PLAUSIBLE; the demotion is logged; the validator passes (no StageError raised). The test does NOT mock the validator (the validator is the integration point being preserved); the test feeds the raw payload through `_validate_rows` and verifies the result list contains a PLAUSIBLE-banded objective.
  - Pre-fix verification: pre-fix `_validate_rows` invokes `Objective.model_validate(row)` directly with the LLM payload; a VERIFIED row missing two sources raises StageError. Post-fix the row is demoted to PLAUSIBLE first, validator accepts, no StageError.
  - Edge cases:
    1. VERIFIED + tests-only + no readme_excerpts + no design_doc_refs → demote to PLAUSIBLE. (The PLAUSIBLE row needs single-source from {readme_excerpts, design_doc_refs, survey_line_refs}; if the LLM also failed to populate any of those, the validator still raises — guard does not paper over total absence of evidence.)
    2. VERIFIED + tests + readme_excerpts populated → no demotion (already two-source compliant).
    3. VERIFIED + tests + design_doc_refs populated → no demotion (already two-source compliant).
    4. PLAUSIBLE row → no demotion (only VERIFIED rows are guarded).
    5. HYPOTHESISED row → no demotion (only VERIFIED rows are guarded).

- **AC.V025-C4.3 — Extended outcome-altitude AC test verifies GREEN end-to-end after fix.** **outcome-altitude: true** (CLI surface against real LLM; happy path).
  - Surface: NEW test `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_C4_3_cli_live_outcome_altitude_post_fix.py`. Mirrors C3.3's shape (skip cleanly without API key; no monkeypatch; jsts-playwright-app fixture). Asserts: extraction completes (rc == 0), objectives.yaml contains ≥1 objective, backing-map.yaml exists, no validator errors surface — i.e., the full happy path post-fix.
  - The test does NOT assert that the row is specifically PLAUSIBLE-banded — it asserts that ANY band is acceptable. The fix is "no validator error"; the band can be VERIFIED (LLM cooperates with tightened prompt), PLAUSIBLE (LLM had only single-source evidence; OR the demotion guard demoted it from a malformed VERIFIED), or HYPOTHESISED. ALL three are "the fix worked" outcomes.
  - LLM stochasticity tolerance: dispatch brief allows 3x re-run; ≥2 of 3 must pass cleanly. (The test itself is single-invocation; the human/operator re-runs to verify stochastic stability.) The dispatch brief's "3x re-run" is a verification probe of the AC, not a structural part of the test.
  - Pre-fix verification: pre-fix C3.3 fails on first API run (the F8 condition); post-fix C4.3 (and C3.3) passes on at least 2 of 3 runs.

- **AC.V025-C4.4 — All existing tests still pass; no regressions.** **outcome-altitude: false** (meta-AC).
  - Surface: structural — fix MUST NOT regress any sealed AC.
  - Test: meta-AC honored by running full odd-extractor test suite (`pytest plugins/dev-sdlc/odd-extractor/tests/`) at seal-time and verifying zero new failures vs the post-C3 baseline (815 passed, 2 skipped). Post-C4 expectation: 816 passed, 2 skipped (815 + new C4.2 unit test passes-deterministically; C3.3 + new C4.3 outcome-altitude tests skip-without-key OR pass-with-key).

- **AC.V025-C4.5 — AC.OBJX.5 methodology refinement documented.** **outcome-altitude: false** (audit-trail AC).
  - Surface: This plan-doc §14 records the validator-stays-strict-vs-guard-demotes decision; this plan-doc cross-references the v0.2.3 sub-plan-doc's AC.OBJX.5 entry.
  - Test: structural — `grep` for the cross-reference + the §14 decision entry.
  - **DO NOT** modify `docs/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md` — only record a one-line cross-reference HERE in this corrective's plan-doc.

---

## §3 — Build dispatch brief (folded into this run)

This corrective amendment is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Plan-doc + manifest commit** (this commit).
2. **Source-edit feat commit (BASELINE).** Edit `synthesis.py` (prompt strengthening — handful of lines added to `_SYSTEM_PROMPT`; new helper `_apply_band_demotion_guard` ~20-40 lines + integration into `_validate_rows`); add NEW unit test `test_AC_V025_C4_2_demotion_guard.py` (~80-120 lines); add NEW outcome-altitude test `test_AC_V025_C4_3_cli_live_outcome_altitude_post_fix.py` (~150 lines mirroring C3.3 shape). Single commit subject: `fix(synthesis): prompt-strengthen + demotion-guard for VERIFIED two-source rule (v0.2.5 corrective C4)`.
3. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
4. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.
5. **STATE update commit.** Inline corrective entry in `docs/STATE.md` mirroring C3's pattern.

**No `git --amend`. No push. No tag. Single semantic commit per stage.**

---

## §4 — Halt triggers + bookkeeping

**Halt-and-surface triggers (per dispatch brief):**
- `pwd` ≠ `/Users/lukeivers/ivers-corp-pos-v2` — handled at start.
- Concurrent agent activity in this WD — verified clean at start (single claude process; no concurrent loam/pytest).
- Even after prompt-engineering + demotion-guard, the LLM produces objectives that fail OTHER validators (means F8 is just one symptom of a deeper synthesis-quality problem; halt-and-surface).
- `loam amend apply` or `loam amend seal` errors out — halt-and-surface.
- Any push attempt — n/a; no push.
- Any tag attempt — n/a; no tag.
- A FIFTH BLOCKER beyond F1/F2/F5/F6/F8 surfaces — halt-and-surface.

**ODD §2.5 surrounding-code observations (per principle 2 — halt-and-surface on adjacent ODD violations):**
- F7 (ANTHROPIC_API_KEY keychain lift) explicitly out-of-scope per dispatch brief; pushed to FIDRAFT post-Eric.
- The PLAUSIBLE row's single-source rule (one of readme_excerpts / design_doc_refs / survey_line_refs) remains unchanged. Demotion-guard does not address PLAUSIBLE-rule violations — those still raise StageError per AC.OBJX.5 design.

**Bookkeeping:**
- `loam amend apply` (= `pos-amend apply`). NOT `git --amend`. NOT manual `git commit`.
- Manifest schema v3.
- Single semantic commit on apply.
- Short-form seal commit per AC.DPS2 schema-v3.
- §14 backfill via `loam amend seal --plan-doc` flag (separate post-seal commit per AC.D-sa.7).
- NO push; NO tag; v0.2.5 release-tag remains gated on Luke's ship ruling.

---

## §5 — Smoke (REALISTIC CONDITION — applicable dimensions)

**D1 cold-state.** Fresh tmp workspace via `tmp_path`; fresh extraction via `cli.main([<repo>, "--live", ...])` against canonical jsts-playwright-app fixture with NO monkeypatch and NO pre-arrangement of objectives.yaml/backing-map.yaml; assert clean exit + ≥1 objective + backing-map.yaml exists. Verified by AC.V025-C4.3 (when ANTHROPIC_API_KEY is set; skips cleanly otherwise).

**D2 steady-state.** Re-running on byte-identical inputs produces byte-identical artefacts. Inherited from v0.2.3 idempotence verification (AC.BACKMAP.D2 + AC.OBJX.D2); not re-verified per fix-scope.

**D3 restart.** N/a structurally — `_cmd_extract` is stateless on entry.

**D4 reboot.** N/a — one-shot CLI; D4 collapses to D5 for one-shot CLIs.

**D5 cross-session.** Inherited from v0.2.4 cross-session verification; not re-verified per fix-scope.

**D6 telemetry-floor.** `_cmd_extract` continues to write the same audit-log entries; when synthesis runs, `synthesis_complete` event-kind is emitted as before; the demotion-guard ADDS a per-demotion log entry but does not alter the existing audit-log shape.

**PLUS: full-suite green sweep** — pre-corrective odd-extractor tests at HEAD all pass post-corrective; halt + surface on any regression. Verified by AC.V025-C4.4.

---

## §6 — Risk-band classification (per `odd-test-altitude-discipline` SKILL)

This corrective edits:
1. `synthesis.py` `_SYSTEM_PROMPT` — production-facing prompt; affects every live synthesis call. **HARD per-cycle required.**
2. `synthesis.py` `_validate_rows` — production parser; affects every synthesis call. **HARD per-cycle required.**
3. New unit test (test-only; no production code impact).
4. New outcome-altitude test (test-only; no production code impact).

The first two items are production-code edits. HARD per-cycle is required and is satisfied by AC.V025-C4.3 (the new outcome-altitude test running against the real CLI surface with the real SDK).

Risk-band assessment summary: **HARD per-cycle required** for AC.V025-C4.1 + AC.V025-C4.2 (synthesis-prompt + parsing layer are production-facing); the per-cycle HARD probe is AC.V025-C4.3 (the new outcome-altitude test).

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Corrective amendment scope is moderate (prompt-text edit + ~30-line guard helper + 2 new test files).

**Method decisions:**

- **Two-layer fix vs single-layer.** Picked two-layer (prompt-engineering primary + demotion-guard safety net) per dispatcher ruling. Rationale: (1) prompt-engineering alone leaves residual risk — LLMs are stochastic and the prompt cannot guarantee cooperation. (2) Demotion-guard alone is "papering over the LLM's mistake" without educating it; future model upgrades may regress. (3) Together: the prompt teaches the LLM the right shape, the guard catches stragglers. (4) The two-layer approach mirrors the standard defensive-programming pattern: input validation at the boundary AND clear guidance to the upstream producer.

- **Demotion-guard placement: in `_validate_rows` vs separate `_apply_band_demotion_guard` helper.** Picked separate helper invoked from `_validate_rows`. Rationale: (1) keeps `_validate_rows` readable — the guard is conceptually a separate concern (band-rule normalization) from the per-row Pydantic validation. (2) easier to unit-test in isolation per AC.V025-C4.2. (3) the guard's logic (scan rows; demote VERIFIED-without-two-sources to PLAUSIBLE; log) is a cohesive operation that benefits from naming.

- **Validator-stays-strict vs validator-becomes-lenient.** Picked validator-stays-strict + parsing-layer guard. Rationale: (1) the validator IS the structural-correctness contract — Pydantic models cannot hold malformed band/evidence pairs. Loosening it weakens a load-bearing invariant. (2) the parsing layer is the right place for "soft" recovery (band normalization) — the validator handles "hard" structural malformation (extra fields, type mismatches, missing required). (3) downstream code (`backing_map.py`, `verify.py`) reads from validated `Objective` instances and assumes the band/evidence relationship holds — keeping the validator strict preserves that invariant. (4) this is a small but real **methodology refinement** of AC.OBJX.5's "raise on malformed" — band-rule violations are now demote-able; structural malformation still raises. AC.OBJX.5 is locked at v0.2.3 sub-plan-doc level; this corrective adds a one-line cross-reference to AC.OBJX.5 acknowledging the refinement, but DOES NOT modify the sub-plan-doc text per dispatch brief.

- **AC.V025-C4.3 fixture choice: jsts-playwright-app (same as C3.3).** Rationale: (1) canonical existing fixture used by `test_AC_PERSONA_PULL_4_release_smoke`, `test_AC_V025_C1_C2_*`, and `test_AC_V025_C3_3_*`. (2) Allows direct comparison between the C3.3 (pre-fix) and C4.3 (post-fix) test runs on the same input. (3) v0.2.4 Cycle 3 SOFT smoke evidence shows the fixture has README + tests + code patterns sufficient for ≥1 objective at SOME band.

- **AC.V025-C4.3 vs extending C3.3.** Picked NEW test file (sibling) rather than extending C3.3. Rationale: (1) C3.3 is the worked example of the SKILL's HARD per-cycle classifier path — it documents the F8 surfacing in its docstring. Extending it would muddy the worked example. (2) C4.3 is the post-fix verification — semantically a different probe. (3) Naming clarity: the test name `test_AC_V025_C4_3_*` immediately ties it to the corrective.

- **Logging mechanism for demotion-guard.** Picked Python `logging` module via `logger.warning` (or stdout `print` to stderr if logging infrastructure not already wired in synthesis.py). Rationale: (1) the demotion is not an error condition — it's an LLM-output adjustment that downstream operators may want to surface for triage. WARN level is appropriate (not ERROR; not INFO — the operator should see it). (2) Per AC.OBJX.12 the synthesis pass already emits an audit-log entry (`synthesis_complete`); the demotion-guard does NOT add a new audit-log event-kind in this cycle (would require a manifest-tracked schema change). The log statement is for operator visibility; the formal audit-log fields stay unchanged.
  - Implementation note: `synthesis.py` imports nothing from the standard `logging` module currently; will add `import logging` + `logger = logging.getLogger(__name__)` per Python idiom; the demotion logs at WARN level. If pytest captures logging output by default (it does via `--log-cli-level` configurable), the AC.V025-C4.2 unit test asserts the log content via `caplog` fixture.

- **Cross-reference to AC.OBJX.5.** Picked: this plan-doc §14 (the entry above) is the cross-reference. Rationale: (1) per dispatch brief, do NOT modify `docs/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md`. (2) the cross-reference lives HERE so a reader of THIS plan-doc sees the linkage; a reader of the v0.2.3 sub-plan-doc sees AC.OBJX.5 as locked-as-authored without an inline edit. (3) The methodology-amendment audit-trail is satisfied: a future reader searching for AC.OBJX.5 refinements can `grep` across plan-docs and find this one.

### Commit SHAs

- Plan-doc + manifest commit: `<pending>`
- Source-edit feat commit (BASELINE): `<pending>`
- Manifest baseline-pin commit: `<pending>`
- `loam amend apply` commit: `<pending>`
- `loam amend seal` commit: `<pending>`
- §14 backfill commit (auto via seal --plan-doc): `<pending>`
- STATE update commit: `<pending>`
