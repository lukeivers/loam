# Amendment #140 — loam-amend seal-tool hygiene pair (plugins-tests-skipped + dirty-tree-check-after-archive)

**Status:** plan-doc, plan-before-code. Originally authored 2026-05-21 as amendment #138 by `loam-plan-author` subagent; build halted on the dev-sdlc-tests-not-green pre-existing gate (per `feedback_serialize_amendment_builds`). Resumed 2026-05-21 by `loam-builder` subagent post-#139 unblock; renumbered #138 → #140 because slot #138 is now occupied by the sealed `dev-sdlc-test-directory-cleanup` amendment (the #139 prerequisite) and slot #139 by the manifest-runtime-flag-schema amendment that unblocked this work.
**Working directory:** `/Users/lukeivers/loam/`.
**Predecessor (load-bearing):** amendment #139 publish-state commit `cd3daae` (current HEAD post-publish).
**Parent capture:** two sibling future-ideas-draft entries — F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE — both captured 2026-05-21 from amendment #136 build agent's §16 findings. Merged per owner queue-merge directive TG 11847.
**Quality bar:** single-component, two-scope merged amendment. Two AC families partitioned by mechanism (AC.STSP.\* + AC.DTCO.\*) plus a shared outcome-altitude smoke (AC.HYG.S) that exercises BOTH fixes in one synthetic seal cycle.

---

## §1. Objective / Summary / TL;DR

Two sibling hygiene fixes to `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py`, merged into one amendment per owner queue-merge directive (TG 11847):

1. **Scope A (F-SEAL-PLUGINS-TESTS-SKIPPED)** — `_finalize` step (d) currently hardcodes `framework/<comp>/tests/` for the per-component pytest run. The manifest schema carries a mandatory `seal_test:` field on every `ComponentEntry` (manifest.py line 58 — already consumed by `apply.py` and `dry_run.py`). Switch step (d) to read `seal_test:` from the manifest and pytest against `Path(seal_test).parent`. Net effect: every plugins/-tree component's tests run automatically during seal (today they silently skip; tests still pass because the build agent runs them manually pre-seal, but the automation is broken).

2. **Scope B (F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE)** — `_finalize`'s dirty-tree validation gate (step (b), line 700-721) runs AFTER the T1.4 plan-doc archive (step at line 656-676). When the gate halts, `git mv` has already moved the plan-doc + manifest into `docs/plans/sealed/` and the operator must manually move them back. Reorder so the gate fires BEFORE any file moves: dirty-tree check → THEN plan-doc archive → THEN seal commit. The current code adds the rename pair to `expected_writes` (lines 689-697) so the rename doesn't appear as "unrelated dirt"; that filtering becomes unnecessary after the reorder, since the rename has not yet happened when the check runs.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T16:14:01Z | Build-strategy delegation (seal-tool hygiene IS build-strategy territory). |
| TG 11837 | 2026-05-21T~19:00Z | Durable-autonomy directive. |
| TG 11840 | 2026-05-21T~19:30Z | Ratification of autonomous queue pickup. |
| TG 11847 | 2026-05-21T~19:45Z | Queue-merge-check-before-pickup directive — this amendment is a merged amendment under that policy. |
| TG 11852 | 2026-05-21T~20:30Z | Option B narrowing (during the original #138 attempt) — keep scope merged; halt-and-surface dev-sdlc-tests-not-green. |
| TG 11858 | 2026-05-21T~21:30Z | Owner ruling on the dev-sdlc-tests-not-green resolution — fix the tests first, then resume this hygiene pair. |
| TG 11861 | 2026-05-21T~22:00Z | Persona surfaced unblock + dispatched resume (this build). |

**Pre-flight verification (per `feedback_verify_fidraft_against_canonical_before_dispatch`, re-confirmed at canonical HEAD `cd3daae`):**

- `ls /Users/lukeivers/loam/plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` — exists (1131 lines).
- Hardcoded path in step (d): line 796 — `comp_tests = repo_root / "framework" / comp.name / "tests"`. Single match-site (verified `grep -n` 2026-05-21).
- Dirty-tree check at line 703 — runs AFTER `_stage_plan_doc_archive` call at line 666 (verified `grep -n` 2026-05-21). Single ordering site.
- `seal_test:` is **mandatory** on every `ComponentEntry` (manifest.py line 58 + line 423 `_require_str`). Already consumed by `apply.py` + `dry_run.py`.
- `plugins/dev-sdlc/tests/` runs green at canonical HEAD `cd3daae` — `pytest plugins/dev-sdlc/tests/` returns `252 passed, 7 skipped` (verified 2026-05-21 by `loam-builder`). This is the post-#139 state that unblocks Scope A's dogfood at seal time.
- No prior implementation of either fix landed on main: `git log --oneline cd3daae` since the previous attempt branched does not contain seal.py changes.

---

## §2. Predecessors / context

- **Amendment #134** (FBM Tier 1) — introduced T1.4 (plan-doc archive on seal). The archive-before-dirty-tree-check ordering was a deliberate design choice at T1.4-authoring time ("part of the expected-writes set rather than dirty unrelated dirt" — per `_finalize` docstring line 656-658). Scope B revises that decision based on empirical recovery cost.
- **Amendment #136** (seal §14 backfill regex widening) — both findings surfaced during its build. F2 §16 finding #2 (dirty-tree-after-archive) + finding #4 (plugins-tests-skipped, captured at 2026-05-21 update).
- **Amendment #137** (legacy pos-amend name sweep).
- **Amendment #138** (dev-sdlc test-directory SKILL-frontmatter cleanup — narrowed scope, sealed at `7d893b0`). The dispatch's "dev-sdlc tests green" precondition for the hygiene pair's dogfood.
- **Amendment #139** (dev-sdlc manifest runtime-flag schema — sealed at `cd3daae`, current HEAD). Unblocked this work by completing the dev-sdlc test corpus admission needed for the plugins-tree pytest invocation to land green.
- **Previous #138 attempt at this work** — branch `plan/amendment-138-seal-tool-hygiene-pair` (commits `2cea328` plan + `3a8ed06` source-edits + `067e3de` apply) — halted at seal time on the 11 pre-existing dev-sdlc test failures that #138-narrowed and #139 jointly resolved. This amendment renumbers + replays that work onto post-`cd3daae` main.

---

## §3. Scope

**In-scope:**

- Modify `_finalize` step (d) in `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` to read `seal_test:` from the manifest and pytest against `Path(seal_test).parent` (Scope A).
- Reorder `_finalize` so the dirty-tree validation gate runs BEFORE `_stage_plan_doc_archive` (Scope B).
- Adjust the `expected_writes` computation to no longer include the rename pair (the rename hasn't happened when the gate runs — the filter is unnecessary post-reorder).
- Tests for AC.STSP.\* + AC.DTCO.\* + AC.HYG.S.

**Out-of-scope:**

- Any other path-resolution logic in seal.py (the cross-component sweep at step (e) uses `_seal_diff_test_path` which has its own framework/-hardcoded convention; not in scope here — separate FIDRAFT entry if it surfaces).
- The oversized YAML field cleanup queued as `ws-loam-amend-oversized-manifest-field-cleanup` (separate queue item — pre-existing failure on `session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml` `smoke_outcome` >200 chars).
- Any change to the manifest schema (no new fields; consumes the existing mandatory `seal_test:`).
- The cocitation-extractor heuristic (separate FIDRAFT entry; different component).

---

## §4. Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.STSP.1** | When a manifest names `seal_test: plugins/<plugin>/<comp>/tests/<test>.py`, the seal-step's pytest invocation runs against `plugins/<plugin>/<comp>/tests/` (the parent of `seal_test`). | Unit test asserts the `_run_pytest` call argument resolves to the plugins-tree directory for a manifest with that shape. |
| **AC.STSP.2** | When a manifest names a framework-layout `seal_test: framework/<comp>/tests/<test>.py`, the seal-step's pytest invocation runs against `framework/<comp>/tests/` (unchanged behaviour). | Unit test asserts the `_run_pytest` call argument resolves to the framework-tree directory for a manifest with that shape. |
| **AC.STSP.3** | The seal step's per-component test run derives its target purely from the manifest's `seal_test:` field — no hardcoded `framework/` prefix in step (d). | Source-level: `grep -n "framework.*tests" seal.py` in `_finalize` step (d) returns no match within the lines covering step (d). |
| **AC.STSP.S** | Outcome-altitude: synthetic seal cycle on a plugins-tree component (e.g., dev-sdlc) with `seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py` named in the manifest produces a seal commit only AFTER that pytest passes. (No pre-arrangement: the test invokes the production `_finalize` entry-point against a fresh fixture manifest.) | `outcome-altitude: true` — test calls the production seal entry-point with a manifest naming a plugins-tree `seal_test:`; asserts the pytest log records the plugins-tree test execution. |
| **AC.DTCO.1** | The dirty-tree validation gate fires BEFORE any plan-doc / manifest file move. | Unit test: invoke `_finalize` against a workspace with intentionally-dirty unrelated paths + a plan-doc still at `docs/plans/<slug>.md`. Assert (a) `_finalize` returns exit 3, (b) the plan-doc still resides at `docs/plans/<slug>.md` post-halt (NOT in `docs/plans/sealed/`). |
| **AC.DTCO.2** | The plan-doc archive (`_stage_plan_doc_archive`) runs only after the dirty-tree gate passes. | Source-level: in `_finalize`, the `_stage_plan_doc_archive` call site appears AFTER the `_working_tree_dirty` check in the function body (line-order verifiable by grep). |
| **AC.DTCO.3** | The `expected_writes` set computed before the dirty-tree gate no longer includes the plan-doc/manifest rename pair (those paths haven't moved when the gate runs). | Source-level: the `for old_path, new_path in archive_renames` loop that populates rename paths into `expected_writes` is gone (or relocated post-gate where it's only used by downstream `git add`/commit steps that don't dirty-check). |
| **AC.DTCO.S** | Outcome-altitude: synthetic seal cycle with an intentionally-dirty working tree halts cleanly; post-halt working-tree state has the plan-doc still at `docs/plans/<slug>.md` (NOT at `docs/plans/sealed/<slug>.md`). | `outcome-altitude: true` — test invokes the production seal entry-point against a workspace with an unrelated dirty file. Asserts exit 3 AND filesystem state shows the plan-doc at its pre-seal location. |
| **AC.HYG.S** | Outcome-altitude shared smoke: ONE synthetic seal cycle exercising BOTH fixes together — a plugins-tree component with a clean working tree → seal succeeds, the plugins-tree pytest runs and passes, plan-doc archives to `docs/plans/sealed/`, seal commit lands. | `outcome-altitude: true` — single end-to-end test invokes the production seal entry-point against a fixture combining the plugins-tree manifest AC.STSP.S uses with the clean-tree AC.DTCO.S inverse. Asserts seal commit exists, pytest ran on plugins-tree path, plan-doc at sealed location. |

**AC ladder-up:** AC.STSP.\* + AC.DTCO.\* + AC.HYG.S → seal-tool reliability (zero silent test-skips + recoverable halts) → AC.PO.2 (harness reduces translation burden by ensuring the seal step does what the agent assumes it does without surprises).

---

## §5. Sealed-component fence (single-component)

**Component touched:** `plugins/dev-sdlc/tools/loam-amend/` ONLY (which lives inside the `dev-sdlc` sealed component).

Files in scope:

- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` (the two edits).
- `plugins/dev-sdlc/tools/loam-amend/tests/` (new AC tests).

**Universal admissions:**

- `docs/plans/` (this plan-doc + manifest; archives to `docs/plans/sealed/` on seal per T1.4).
- `docs/FUTURE_IDEAS_DRAFT.md` (FIDRAFT cleanup-surface; admitted via the `allow_untracked_globs` mechanism per AC.LAE.2 — this is the existing convention, not a new admission).
- `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` — pre-existing untracked plan-only file (PENDING owner ratification, separate workstream). Admitted via `--allow-untracked-globs` at seal time; not part of this amendment's scope.

**Out of fence (halt-and-surface trigger):**

- Any other component under `framework/` or `plugins/`.
- Any other tool under `plugins/dev-sdlc/tools/`.
- The manifest schema definition in `manifest.py` (Scope A composes against the existing schema; no schema change needed).

---

## §6. Halt triggers (in-flight)

1. **Source edits leak outside `plugins/dev-sdlc/tools/loam-amend/`.** Halt and surface.
2. **Either scope's tests reveal that the existing implementation IS already correct.** Would mean drift between FIDRAFT capture and current canonical (e.g., a stealth fix landed between capture and dispatch). Halt + verify via re-grep of canonical seal.py.
3. **The dirty-tree-check reorder breaks an existing test that wasn't anticipated** (e.g., a test in `test_seal.py` family mocks the dirty-tree gate's call site or asserts on the rename-in-expected-writes filtering). Halt — likely indicates a test-fixture that needs updating alongside the reorder.
4. **New regressions in the dev-sdlc test directory** (would mean #139's fix doesn't hold). Halt + re-check `pytest plugins/dev-sdlc/tests/`.
5. **Manual section-14 backfill needed** (F-SEAL-TOOL-SECTION-14-BACKFILL-COUPLING regression). Halt — capture in §16.
6. **The seal-time dogfood at build step 6 fails** — would indicate either fix doesn't actually work in the production code path. Halt and surface (this is the build-time analogue of amendment #136's regex-widening dogfood).

---

## §7. Ship shape

Single cycle, single component, two-scope merged amendment. Commit ladder:

1. Plan-doc + manifest commit (this file + paired manifest YAML).
2. Source-edits + tests commit — `fix(loam-amend): seal-tool hygiene pair — read seal_test from manifest + dirty-tree check before archive` (the previous attempt's `3a8ed06` cherry-picked, message-updated to amendment #140).
3. `loam amend apply` auto-commit.
4. `loam amend seal --plan-doc` deterministic seal commit. **Dogfood:** THIS seal uses the newly-fixed code paths — Scope A's plugins-tree pytest invocation runs against `plugins/dev-sdlc/tests/` (the dev-sdlc component's `seal_test`); Scope B's dirty-tree-check fires before the plan-doc/manifest archive.
5. §14 SHA-register backfill (auto-embedded by amendment #136's widened regex if heading matches; separate follow-up commit otherwise — but expected to be auto-handled).

If both fixes are correct, the seal at step #4 demonstrates them: the dev-sdlc component's `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` runs (rather than silently skipping per Scope A), and the dirty-tree check runs against a pristine working tree before the rename pair lands (per Scope B). That's the proof-of-fix.

---

## §10. F2 Ruthless Feedback (honest doubts)

1. **The archive-before-dirty-check ordering was a deliberate design choice at amendment #134 T1.4 authoring time.** The docstring at line 656-658 explicitly justifies it: "archive plan-doc + manifest BEFORE the dirty-tree check, so the moved files are part of the expected-writes set (staged) rather than dirty unrelated dirt." Scope B revises this decision. The new ordering is simpler (no rename-pair filtering needed in `expected_writes`) and recovery-friendlier (halt leaves plan-doc at original location), BUT the new code must verify that `git status --porcelain` against a clean working tree (no rename staged yet) still reports zero dirt — which is the trivial case. Risk: low; the prior justification's "rename appears as dirt" concern is moot when the rename hasn't happened yet. Per `locked-design-not-license-for-bad-outcomes`: the prior decision is revisitable because its outcome (manual recovery cost on every dirty-tree halt) is bad enough to justify revisit.

2. **Scope A removes the fallback the dispatch brief proposed (D-STSP.FALLBACK).** The dispatch brief recommended a fallback to the legacy `framework/<comp>/tests/` lookup if `seal_test:` is absent. Tier-0 verification shows `seal_test:` is a **mandatory** field on every `ComponentEntry` (manifest.py line 58 + `_require_str` at line 423). Every existing canonical manifest carries `seal_test:`. The fallback would only fire on a malformed manifest that `load_manifest` would have already rejected. Recommendation: drop the fallback (the §14 D-STSP.PATH-RESOLUTION decision below records this); the manifest-schema-driven path is the canonical answer. If a future schema-version-bump made `seal_test:` optional, the fallback can be reintroduced then.

3. **The plugins-tree pytest invocation may surface latent test failures — at amendment #138's original build attempt, this fired (11 failures in plugins/dev-sdlc/tests/).** Amendments #138-narrowed (SKILL-frontmatter cleanup) + #139 (manifest runtime-flag schema admission) jointly resolved those failures. As of canonical HEAD `cd3daae`, `pytest plugins/dev-sdlc/tests/` returns 252 passed + 7 expected skips. The dogfood at seal time SHOULD now pass. If it does not, halt trigger #4 fires.

4. **Existing loam-amend tests have 4 pre-existing failures on canonical HEAD `cd3daae`** — `test_AC_DPS1_13`, `test_AC_DPS2_10`, `test_AC_D_1_5_4`, `test_AC_D_sa_6` all fail because `docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml`'s `smoke_outcome` field is 575 chars (schema enforces ≤200). This is the `ws-loam-amend-oversized-manifest-field-cleanup` queue item, OUT OF SCOPE here. Risk to this amendment: these 4 failures will surface in the seal-step pytest invocation (it runs `plugins/dev-sdlc/tools/loam-amend/tests/`). Mitigated by carrying the same observation forward — the failures are pre-existing and unrelated to this amendment's edits; the seal step's pytest gate will report them; halt-trigger #6 distinguishes "new regression from this amendment's edits" (halt) from "pre-existing canonical-state failure unrelated to this amendment" (capture + dispatcher ruling).

5. **Merging the two scopes is the queue-merge-check directive's first test.** Per TG 11847, the policy is to merge siblings touching the same file. Both scopes touch `_finalize` in `seal.py`. Risk of merge: the two edits could touch nearby lines and create a merge-conflict-like situation IF authored by separate agents on separate branches. Mitigated: single build agent, single edit pass, both scopes' edits land in one source-edits commit. The AC families are partitioned cleanly so each AC verifies one mechanism.

6. **No method-in-AC.** Each AC is outcome-shaped. The method-in-AC test: AC.STSP.1 could be satisfied by reading `seal_test:` and invoking pytest, OR by maintaining an explicit per-component mapping, OR by an external config — the AC pins the outcome (correct directory invoked) without pinning the mechanism. AC.DTCO.1 could be satisfied by reordering the existing checks, OR by adding a separate pre-flight gate, OR by deferring the archive — the AC pins the outcome (no file move on halt) without pinning the mechanism. Builder's call per ODD §1.1.

7. **F4 scope-confidence calibration.** Outcome shape is well-pinned (precise, observable, single-mechanism-each-scope). Scope is moderate-tight: objective + AC + constraints fix the contract; method (which line to read `seal_test:` from, whether to reorder vs. defer, what pytest invocation signature to use) stays the builder's call. Composes with prompt-scope-confidence — high confidence in outcome, moderate confidence in code-shape, tight enough to forbid out-of-scope edits, loose enough to not prescribe HOW.

---

## §14. Method-decision register

**Ratification table (recorded at plan-doc commit time, populated post-build by §14 backfill or by hand):**

| Decision | Recommendation | Ratified by | Authority |
|----------|----------------|-------------|-----------|
| D-STSP.PATH-RESOLUTION | Read the manifest's `seal_test:` field; `Path(seal_test).parent` is the pytest target directory. No fallback — `seal_test:` is mandatory per manifest schema (manifest.py line 58 + `_require_str` at line 423). | `loam-plan-author` subagent (original #138 author); preserved by `loam-builder` on #140 resume | Owner build-strategy delegation TG 11808 + queue-merge directive TG 11847 |
| D-DTCO.SEQUENCE | Strict sequence in `_finalize`: (i) compute `expected_writes` (without rename pair) → (ii) dirty-tree check → (iii) `_stage_plan_doc_archive` → (iv) seal commit. Halt at (ii) leaves working tree pristine. | `loam-plan-author` subagent (original #138 author); preserved by `loam-builder` on #140 resume | Owner build-strategy delegation TG 11808 + queue-merge directive TG 11847 |
| D-MERGE.AC-LADDER | Separate AC families per scope (AC.STSP.\* for plugins-tests; AC.DTCO.\* for dirty-tree-order) plus a shared outcome-altitude smoke AC.HYG.S that exercises both fixes in one synthetic seal cycle. | `loam-plan-author` subagent (original #138 author); preserved by `loam-builder` on #140 resume | Owner queue-merge directive TG 11847 |
| D-RESUME.RENUMBER | Renumber #138 → #140 because the original #138 slot was reassigned to the narrowed dev-sdlc SKILL-frontmatter cleanup (sealed at `7d893b0`) and #139 to the manifest runtime-flag schema (sealed at `cd3daae`). Fresh branch off `cd3daae`; cherry-pick the previous attempt's source-edits commit (`3a8ed06`) with message-update to amendment #140; re-author plan-doc + manifest at amendment #140 numbering. | `loam-builder` subagent on resume | Owner unblock ruling TG 11858 + dispatch TG 11861 |

**Rationale (Tier-0 verified at plan-authoring + at resume):**

- **D-STSP.PATH-RESOLUTION** — the `seal_test:` field is already mandatory and consumed by `apply.py` (line 166: `seal_test_path = repo_root / comp.seal_test`) and `dry_run.py` (line 143). Step (d) in `_finalize` is the lone hardcoded-path holdout. Switching it to `seal_test:` aligns step (d) with the existing schema-driven convention. The dispatch brief's proposed fallback (D-STSP.FALLBACK) is dropped because `load_manifest` rejects any manifest lacking the mandatory field — the fallback is unreachable.

- **D-DTCO.SEQUENCE** — the current code's "rename in expected_writes" filter (lines 689-697) is necessary ONLY because the rename happens before the dirty-tree check. Reordering moots the filter. The recovery cost on every dirty-tree halt (operator must `git mv` plan-doc + manifest back from `sealed/`) was the empirical trigger; the prior decision is revisitable per `locked-design-not-license-for-bad-outcomes`.

- **D-MERGE.AC-LADDER** — partitioned AC families let each scope's ACs be evaluated independently (the F3 / EVAL_DIMENSIONS pattern — named-axis judging). The shared AC.HYG.S smoke catches interaction risk between the two fixes. Three outcome-altitude ACs total for this amendment, all marked `outcome-altitude: true`.

- **D-RESUME.RENUMBER** — slot #138 went to the narrowed dev-sdlc SKILL-frontmatter cleanup that landed during the queue triage after the original hygiene-pair build halted. Slot #139 went to the manifest runtime-flag schema admission that unblocked the dev-sdlc test corpus. Cherry-picking + renumbering #138 → #140 preserves the previous source-edits commit (high-quality, ODD-clean) while restoring monotonic amendment numbering against the current main HEAD.

---

### Commit SHAs

- Amendment commit: `7eaf8d01afe899069572f4ae4978a345a2035964` —
  `chore(amend): loam-amend seal-tool hygiene pair (Scope A + Scope B merged per TG 11847 queue-merge directive). Two sibling fixes to the seal step's _finalize routine:`
- Seal commit: `8a41e7ba50a0f5b3e31d2843d3b0938b8b8feee3` —
  `chore(seals): loam-amend seal-tool hygiene pair (Scope A + Scope B merged per TG 11847 queue-merge directive). Two sibling fixes to the seal step's _finalize routine:`
## §16. Halt-and-surface findings (raised + ruled at plan-authoring + resume)

1. **The dispatch brief proposed a `D-STSP.FALLBACK` fallback to legacy `framework/<comp>/tests/` lookup.** Tier-0 verification revealed `seal_test:` is mandatory on every `ComponentEntry` (manifest.py line 58 + `_require_str` at line 423; consumed by `apply.py` + `dry_run.py`). The fallback is unreachable. **Ruling:** drop D-STSP.FALLBACK; record the dispatch-brief proposal in this §16 + the §10 F2 honest-doubt; D-STSP.PATH-RESOLUTION carries the no-fallback decision.

2. **The dispatch brief's framing of Scope B was empirically correct but missed a detail.** Brief said "the dirty-tree validation gate runs AFTER the T1.4 plan-doc archive step". Tier-0 verification confirms this (line 666 archive call precedes line 703 dirty-tree check). The brief's framing missed that the rename's `git mv` actually STAGES the rename, and the current code adds those staged paths to `expected_writes` (lines 689-697) so the porcelain output doesn't flag them as dirt. The reorder makes that filter unnecessary. **Ruling:** D-DTCO.SEQUENCE includes a note that `expected_writes` no longer needs the rename-pair filter post-reorder; AC.DTCO.3 verifies the filter is removed.

3. **Amendment #134's T1.4 docstring at line 656-658 explicitly justifies the archive-before-check ordering as a deliberate design choice.** This is a locked-design situation per `locked-design-not-license-for-bad-outcomes`. **Ruling:** the empirical recovery cost (every dirty-tree halt requires manual `git mv` recovery) is bad enough to revisit. Recorded in §10 F2 #1.

4. **The plugins-tree pytest invocation surfaced 11 pre-existing failures at the original #138 build attempt.** Resolved by #138-narrowed (SKILL-frontmatter cleanup) + #139 (manifest runtime-flag schema admission). At canonical HEAD `cd3daae`, `pytest plugins/dev-sdlc/tests/` returns 252 passed + 7 expected skips. **Ruling:** halt-trigger #4 (this plan-doc §6) fires if the failures return; capture-and-proceed otherwise. Verified green by `loam-builder` at resume time.

5. **Section-14 heading shape.** This plan-doc uses `## §14. Method-decision register` (canonical post-amendment-#136 shape with §-prefix + em-dash). Amendment #136's widened regex matches this shape; the seal-time §14 backfill should succeed automatically. **Ruling:** rely on the widened regex; halt-trigger #6 surfaces if the dogfood breaks.

6. **4 pre-existing loam-amend test failures on canonical HEAD `cd3daae`** — `test_AC_DPS1_13_existing_manifests_validate_clean`, `test_AC_DPS2_10_existing_manifests_validate_clean`, `test_AC_D_1_5_4_existing_loam_amend_test_suite_still_green`, `test_AC_D_sa_6_existing_test_suite_still_green`. Root cause: `docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml`'s `smoke_outcome` field is 575 chars (schema enforces ≤200). Tracked as `ws-loam-amend-oversized-manifest-field-cleanup` (separate queue item; amendment #137 §16 finding #4 referenced this). **Ruling:** OUT OF SCOPE for this amendment. The seal-step pytest invocation will surface these — they predate this amendment's edits (verified by checking out canonical HEAD before any edits). If the seal halts on them, the halt is on the pre-existing canonical-state, NOT on this amendment's edits — surface in §16 + dispatcher ruling. Resolution path: a follow-up amendment shortens the oversized field; not blocked by anything in this work.

7. **Renumber from #138 to #140 on resume.** Amendment slot #138 was reassigned to the narrowed dev-sdlc SKILL-frontmatter cleanup that landed during queue triage after the original hygiene-pair build halted. Slot #139 went to the manifest runtime-flag schema admission that unblocked the dev-sdlc test corpus. **Ruling:** D-RESUME.RENUMBER in §14 captures the renumber decision. Original branch + commits are preserved at `plan/amendment-138-seal-tool-hygiene-pair` for audit; the fresh #140 branch carries cherry-picked source-edits + re-authored plan-doc/manifest.

8. **Pre-existing untracked plan-doc in working tree** — `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` (unrelated workstream, PENDING owner ratification, plan-only / no code). Admitted via `--allow-untracked-globs` at seal time per §5 universal admissions. **Ruling:** NOT this amendment's concern; admission is dirty-check-only and does not stage or commit the file.

---

### Build-agent findings (appended post-seal, 2026-05-21 by `loam-builder`)

9. **Dispatch brief carried a typo'd full BASELINE SHA.** The dispatch instructed the builder to use `cd3daae` as the BASELINE; the brief's full-SHA form `cd3daaef07d92d28aa4cb55b50fe0a89dcf24ed7` was incorrect (the actual full SHA is `cd3daae6fe220b9cb7d8cd05e1bbeb34c8d88fe2`; verified via `git rev-parse cd3daae`). `loam amend apply` failed at the `is_rename_only` check with `fatal: Invalid revision range`. Recovery: new corrective commit `e0604af` updated the manifest BASELINE to the correct full SHA (per `feedback_no_amend_in_agent_dispatches` — no `git commit --amend`). **Pattern:** dispatcher-side Tier-0 verification of full SHAs is a NEW capture candidate for FIDRAFT — when the dispatch carries both a short SHA (`cd3daae`) and a full SHA, the dispatcher should `git rev-parse <short>` to verify the full form matches before the brief lands.

10. **Scope A's seal-step pytest target is the component's primary `seal_test:` directory, NOT every test directory under the component's source tree.** Empirical: the `dev-sdlc` component carries `seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py`, so the per-component pytest run targets `plugins/dev-sdlc/tests/` (252 passed + 7 skipped). The loam-amend tool subtree at `plugins/dev-sdlc/tools/loam-amend/tests/` carries 4 pre-existing failures (per §16 finding #6) but those failures DO NOT block the seal because they're in a sub-tree not pointed at by the manifest's `seal_test:`. **Implication:** Scope A's fix is exactly as targeted as the schema-driven design intended — one test directory per component, the one named in the manifest. **Ruling:** capture-only; no scope change. The 4 pre-existing failures stay tracked as `ws-loam-amend-oversized-manifest-field-cleanup`. The fact that the seal-step's pytest gate runs in `plugins/dev-sdlc/tests/` (post-#139 green) confirms Scope A's fix works — the dogfood succeeded as designed.

11. **Scope B's reorder dogfooded cleanly at seal time.** The dirty-tree check fired against the working tree (which carried only the untracked unrelated plan-doc admitted via `--allow-untracked-globs`); the plan-doc + manifest archive happened AFTER the gate cleared. Verified post-seal: plan-doc + manifest are in `docs/plans/sealed/` (not `docs/plans/`). The reorder works as designed — if the gate had halted, the plan-doc would still be at `docs/plans/amendment-140-…md` (the recovery-friendly outcome).

12. **§14 SHA auto-backfill succeeded via amendment #136's widened regex** — landed at commit `381645b` with both Amendment + Seal commit SHAs embedded under `### Commit SHAs`. No manual fallback needed (in contrast to #139, where the regex-widening was incomplete + the post-seal dry-run halt blocked auto-backfill). **Ruling:** the regex-widening + sealed-shape composition holds; capture-only.

13. **Cherry-pick from previous #138 attempt was clean** — `git cherry-pick 3a8ed06 --no-commit` produced no merge conflicts onto post-#139 main HEAD `cd3daae6`. The 11 new test files + the seal.py edits were preserved unchanged. Verified by running all 11 tests against the post-#139 baseline (7 unit + 4 smoke, all PASS). **Ruling:** the original #138 build agent's work was high-quality and survived the renumber cleanly; D-RESUME.RENUMBER mechanism (cherry-pick + message-update) is the right shape for future post-halt resumes.

14. **Cross-component sweep result.** Seal commit body records "16 components green (1 skipped — no seal-diff test recognised: scope-of-work)". The 1 skip is unrelated to this amendment (a known gap in the cross-component sweep's `_seal_diff_test_path` lookup, captured in §3 out-of-scope). No regression introduced.

---

## §17. Composition (M5 derivation line)

- **Composes with** amendment #134 (FBM Tier 1) — Scope B revises T1.4's ordering decision; the archive mechanism itself is preserved.
- **Composes with** amendment #136 (seal §14 backfill regex widening) — this plan-doc's §14 heading uses the canonical shape that #136 enabled; the seal-time §14 backfill is expected to succeed automatically.
- **Composes with** amendment #138 (sealed at `7d893b0` — dev-sdlc SKILL-frontmatter cleanup) — joint precondition for Scope A's dogfood.
- **Composes with** amendment #139 (sealed at `cd3daae` — manifest runtime-flag schema admission) — completes the dev-sdlc test corpus baseline that this amendment's Scope A dogfoods against.
- **Composes with** `feedback_workaround_masks_rootcause_urgency` — Scope A's "build agent runs tests manually pre-seal" workaround masks the seal-step's silent skip; this amendment IS the root-cause fix.
- **Composes with** `feedback_locked_design_not_license_for_bad_outcomes` — Scope B revisits amendment #134's T1.4 ordering decision because the operational cost (manual recovery on every halt) is bad enough to justify revisit.
- **Composes with** `feedback_serialize_amendment_builds` — the original #138 attempt halted correctly when the dev-sdlc-tests-not-green gate fired; this resume happens AFTER the gate cleared via #139.
- **Composes with** TG 11847 queue-merge directive — the AC-ladder partition + shared outcome-altitude smoke pattern sets the precedent for merged amendments under that policy.
- **Composes with** F3 / Lens 5 swarming (EVAL_DIMENSIONS named-axis judging) — the AC families are partitioned by mechanism so each scope is verified on its own axis.
- **Closes** F-SEAL-PLUGINS-TESTS-SKIPPED (Scope A) on seal.
- **Closes** F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE (Scope B) on seal.
- **Independent of** F4 — outcome shape is well-pinned regardless of scope-confidence framing.

loam-amend seal-tool hygiene pair (Scope A + Scope B merged
per TG 11847 queue-merge directive). Resume of the original
#138 attempt; renumbered #138 → #140 because slot #138 was
reassigned during queue triage (to the narrowed dev-sdlc
SKILL-frontmatter cleanup, sealed at 7d893b0) and #139 to the
manifest runtime-flag schema (sealed at cd3daae). See plan-doc
§14 D-RESUME.RENUMBER for the renumber rationale.

Scope A (F-SEAL-PLUGINS-TESTS-SKIPPED) — _finalize step (d)
previously hardcoded framework/<comp>/tests/ for the per-
component pytest run, silently skipping plugins-tree components
(e.g., dev-sdlc). Switch to Path(comp.seal_test).parent — the
manifest's mandatory seal_test: field's parent directory. Both
framework- and plugins-located components now run.

Scope B (F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE) — Pre-fix,
the T1.4 plan-doc archive step ran BEFORE the dirty-tree
validation gate. Halt at the gate left the plan-doc + manifest
already moved into docs/plans/sealed/, requiring manual git mv
recovery. Reorder so the gate fires FIRST against a pristine
working tree — halt now leaves nothing to undo.

Composes with amendment #134 (T1.4 ordering revision per
feedback_locked_design_not_license_for_bad_outcomes), amendment
#136 (auto-backfill of §14 SHAs at this seal), amendment
#138-narrowed + amendment #139 (joint precondition for Scope A's
dogfood — dev-sdlc test corpus baseline green at cd3daae).

Closes F-SEAL-PLUGINS-TESTS-SKIPPED (Scope A) + F-SEAL-DIRTY-
TREE-CHECK-AFTER-PLAN-ARCHIVE (Scope B) on seal.
