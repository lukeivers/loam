# Amendment #141 — loam-amend seal: decouple §14 SHA backfill from post-seal dry-run gate

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 by `loam-plan-author` subagent per dispatch from owner (TG 11808/11837/11854).
**Working directory:** `/Users/lukeivers/loam/`.
**Predecessor (load-bearing):** amendment #140 publish-state commit `b46162f` (current HEAD post-publish — `docs: bump current-release to v0.12.17 (amendment #140 seal-tool hygiene pair) + F-DISPATCH-BRIEF-FULL-SHA-VERIFICATION capture`).
**Parent capture:** FIDRAFT entry `F-SEAL-TOOL-§14-BACKFILL-COUPLED-TO-DRY-RUN` (`docs/FUTURE_IDEAS_DRAFT.md` line 332). Captured 2026-05-21 from amendment #138 builder F2 (finding #2 in §16). **REGRESSION** of amendment #136's auto-backfill expectation: the orphan-file dry-run failure in #138 blocked the §14 auto-backfill even though the §14 register itself was unaffected by the orphan.
**Quality bar:** single-component amendment. One AC family (AC.SCT.\*) with one outcome-altitude smoke (AC.SCT.S) exercising the decoupled backfill against a synthetic seal cycle whose post-seal dry-run intentionally fails.

---

## §1. Objective / Summary / TL;DR

Decouple the seal-tool's `--plan-doc` §14 SHA-backfill step from the post-seal `loam amend apply --dry-run` verification gate. Pre-fix (current canonical at `b46162f`): step (g) at `seal.py:947-969` runs the dry-run; on non-zero exit it `return dry_rc` — early exit BEFORE step (h) (`seal.py:971-1086`) has a chance to fire the §14 backfill. Post-fix: the §14 backfill runs unconditionally after the seal commit lands, independent of dry-run outcome. The dry-run check still runs, still emits its own diagnostic on failure, and the seal command's return code still reflects the dry-run outcome (operator-visible signal preserved).

**Shape decision: (a) always-run backfill.** Rejected alternative (b) auto-retry-after-fixup. Per §10 F2 + §14 D-SCT.SHAPE: shape (a) is simpler (no new runtime state), preserves the dry-run failure signal (it still surfaces + still drives exit code), and the backfill IS independently useful for audit even when dry-run halts. Shape (b) would require a "deferred-backfill" marker file or sidecar state to detect "we owe a backfill from a previous halt"; that's runtime state for no clear win.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T16:14:01Z | Build-strategy delegation (seal-tool hygiene IS build-strategy territory). |
| TG 11837 | 2026-05-21T~19:00Z | Durable-autonomy directive — proceed without per-step ratification on in-scope authorized work. |
| TG 11854 | 2026-05-21T~20:45Z | Re-evaluation directive — this is the persona-class top-of-queue item; the FIDRAFT activation gate ("consolidate with the next seal-tool hygiene amendment") IS met. |

**Pre-flight verification (Tier-0 at canonical HEAD `b46162f`, 2026-05-21):**

- `seal.py:947-969` — step (g) is the dry-run gate. `dry_rc = _apply_dry_run_post_seal(effective_manifest_path)`; on `dry_rc != 0`, emits `post-seal-dry-run-failed` diagnostic and `return dry_rc`. **Verified by direct read.**
- `seal.py:971-1086` — step (h) is the `--plan-doc` §14 backfill. Gated on reaching that line, which requires step (g) returning 0. **Verified by direct read.**
- `seal.py:411` — `_apply_dry_run_post_seal` wraps `apply_cmd.run(manifest_path, dry_run=True)` (no side effects to the seal commit itself; pure verification call).
- `seal.py:311-406` — `_backfill_plan_doc_shas` is independent of the dry-run. It locates the `## §14` (or legacy `## 14.`) heading, walks the §14 body, idempotently appends/replaces the `### Commit SHAs` subsection. No reference to dry-run state.
- Amendment #138 manual recovery: `7d893b0` ("docs(plans): record amendment #138 commit SHAs in method-decision register") — the manual backfill commit the operator had to author because of this coupling. **Verified by `git log --oneline 7d893b0 -1`.**
- Amendment #136 expectation (the regression baseline): `docs/plans/sealed/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md:99` — "If the regex widening is correct, NO §14 backfill follow-up commit is needed for this amendment — the auto-backfill works on the canonical heading." That expectation holds for the clean-dry-run case only. This amendment makes it hold unconditionally.
- Existing seal-test families that touch this code path: `test_seal.py:633-826` (AC.D-sa.7 family), `test_AC_LAS14R_*` (5 files — #136's widened-regex coverage), `test_AC_FBMT1_APS_2_content_unchanged.py` (cross-references the backfill). **None of these test the post-seal dry-run-failed case + backfill-still-fires combination — that's the new AC.SCT.S smoke this amendment adds.**
- No prior implementation of this decouple landed on main: `git log --oneline b46162f -- plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` since #140 shows zero changes touching steps (g)/(h).

---

## §2. Predecessors / context

- **Amendment #136** (seal §14 backfill regex widening, sealed at `5c73a30`) — established the auto-backfill expectation that this amendment defends. #136 widened the heading-regex to accept the canonical `## §14<sep>` shape, removing the "manual backfill commit is the norm" expectation. The post-#138 regression revealed that the widened regex alone doesn't deliver the "no manual fallback" promise when the dry-run halts for unrelated reasons.
- **Amendment #138** (dev-sdlc test directory cleanup, sealed at `01e63ac` + corrective fixup `26f3a9e` + manual §14 backfill `7d893b0`) — the empirical trigger. The orphan-`dev-sdlc` file (root-cause: a separate `narrative.target` bug in the plan-author SKILL's manifest template) broke the post-seal dry-run; that halt blocked the §14 auto-backfill; the operator authored the manual `7d893b0` backfill. §138 §16 finding #2 explicitly proposed this amendment's two-option shape.
- **Amendment #140** (seal-tool hygiene pair, sealed at `8a41e7b`, publish at `b46162f`) — the most recent seal-tool touch. Established the pattern of single-amendment-touching-seal.py-_finalize for hygiene fixes (Scope A path-resolution + Scope B reorder). This amendment is the third such fix; same pattern (one or two narrow edits in `_finalize`, AC family scoped to the touched mechanism).
- **No prior amendment** has touched the step (g) → step (h) sequencing; the coupling has been present since the §14 backfill was introduced at AC.D-sa.7 authoring time (amendment #66, dev-sdlc seal-automation extension — pre-loam.amend rename).

---

## §3. Scope

**In-scope:**

- Decouple `_finalize`'s step (h) §14 backfill from step (g) post-seal dry-run in `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py`. After the change: backfill runs whenever a `--plan-doc` was supplied AND a seal commit landed, regardless of dry-run outcome.
- Preserve the dry-run diagnostic emission and the dry-run-driven exit code: if dry-run fails AND backfill succeeds, the seal command exits with the dry-run's non-zero code; both surfaces (dry-run failure log + backfill commit) are visible to the operator.
- Add the AC.SCT.\* test family + AC.SCT.S outcome-altitude smoke.

**Out-of-scope:**

- The `--amend` constraint stays. The §14 backfill is a SEPARATE follow-up commit, never an `--amend` of the seal commit (per the no-amend CDC; per `feedback_no_amend_in_agent_dispatches`). Pre-fix this is already true; this amendment doesn't relax it.
- The root cause of #138's dry-run failure (the `narrative.target: dev-sdlc` bug in the plan-author SKILL template). That's a separate FIDRAFT (`F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP`) for a different component.
- Auto-retry of dry-run after corrective fixups. Operator still authors the corrective commit + re-runs `loam amend apply --dry-run` by hand. The seal command is one-shot per invocation.
- Any change to step (g) itself (the dry-run still runs; its diagnostic still emits; its exit code still surfaces).
- Any change to the `--plan-doc` flag's argument-parsing or any other step of `_finalize`.
- Any cross-component touch outside `plugins/dev-sdlc/tools/loam-amend/`.

---

## §4. Acceptance criteria

| AC ID | Outcome | Verification | outcome-altitude |
|---|---|---|---|
| **AC.SCT.1** | When `--plan-doc <path>` is supplied AND the seal commit lands AND `loam amend apply --dry-run` exits non-zero, the §14 SHA-backfill commit STILL lands as a follow-on commit. | Unit test invokes `_finalize` against a fixture where the post-seal dry-run is forced to fail (orphan file outside admitted paths, or equivalent unrelated-dirt). Asserts (a) the seal commit exists at HEAD~1, (b) a §14-backfill commit exists at HEAD, (c) the backfill commit's subject matches the canonical `docs(plans): record <slug> commit SHAs in method-decision register` shape. | false |
| **AC.SCT.2** | When the post-seal dry-run exits non-zero, the dry-run diagnostic STILL emits AND the seal command's return code STILL reflects the dry-run exit code (non-zero). | Same fixture as AC.SCT.1; assert the captured stdout/stderr contains the `post-seal-dry-run-failed` `klass:` diagnostic AND the `_finalize` return value equals the (non-zero) dry-run exit code. | false |
| **AC.SCT.3** | The §14 backfill is idempotent across the new ordering: re-invoking the seal step (or running the backfill alone) against a plan-doc that already carries the `### Commit SHAs` subsection produces NO additional commit (no double-emit, no duplicate subsection). | Unit test invokes the backfill twice (or the seal twice with the same plan-doc state); asserts the second invocation reports `§14 SHAs already current.` and produces zero new commits. | false |
| **AC.SCT.S** | Outcome-altitude smoke: synthetic seal cycle with a plan-doc + manifest + INTENTIONAL orphan file (so the post-seal dry-run fails) → seal commit lands, dry-run diagnostic emits non-zero, §14 backfill commit lands as a separate follow-on commit, the post-seal HEAD's plan-doc carries the `### Commit SHAs` subsection naming both the amendment commit and the seal commit SHAs. No pre-arrangement: the test invokes the production `seal.run` (or `_finalize`) entry-point against a fresh fixture. | `outcome-altitude: true` — test calls the production seal entry-point; asserts seal commit + backfill commit are present at HEAD~1 and HEAD respectively, dry-run diagnostic appears in captured output, plan-doc on disk carries the `### Commit SHAs` subsection. | true |

**AC ladder-up:** AC.SCT.\* → seal-tool's auto-backfill matches its design promise (no manual fallback when the §14 heading exists) → AC.PO.2 (harness reduces translation burden by making the seal step do what the agent assumes it does without surprises; the post-#136 expectation holds unconditionally instead of conditionally).

---

## §5. Sealed-component fence (single-component)

**Component touched:** `dev-sdlc` ONLY (via `plugins/dev-sdlc/tools/loam-amend/`).

Files in scope:

- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` (the edit — decouple steps (g) and (h)).
- `plugins/dev-sdlc/tools/loam-amend/tests/` (new AC tests: `test_AC_SCT_1_*.py`, `test_AC_SCT_2_*.py`, `test_AC_SCT_3_*.py`, `test_AC_SCT_S_*.py`).

**Universal admissions:**

- `docs/plans/` (this plan-doc + manifest; archives to `docs/plans/sealed/` on seal per T1.4).
- `docs/FUTURE_IDEAS_DRAFT.md` (FIDRAFT cleanup-surface; admitted via `allow_untracked_globs` per AC.LAE.2 — existing convention).
- `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` — pre-existing untracked plan-only file (unrelated workstream PENDING owner ratification). Admitted via `--allow-untracked-globs` at seal time (same admission pattern as #140 §5).

**Out of fence (halt-and-surface trigger):**

- Any other component under `framework/` or `plugins/`.
- Any other tool under `plugins/dev-sdlc/tools/` outside `loam-amend/`.
- Any change to `apply.py` / `dry_run.py` / `manifest.py` (the dry-run + manifest schema are consumed unchanged).
- Any change to the no-amend CDC (the §14 backfill remains a separate commit; this amendment does not introduce `git commit --amend` anywhere).

---

## §6. Halt triggers (in-flight)

1. **Source edits leak outside `plugins/dev-sdlc/tools/loam-amend/`.** Halt and surface.
2. **Investigation reveals shape (b) auto-retry is actually required** (the always-run shape has a hidden safety reason — e.g., the §14 backfill commit references state that becomes invalid when the operator authors a corrective fixup). The plan-doc § §10 F2 honest-doubt #2 surfaces this risk; if the builder discovers it's load-bearing, halt + surface.
3. **An existing test in the `test_AC_LAS14R_*` family or `test_seal.py:633-826` (AC.D-sa.7) family breaks unexpectedly.** Likely indicates a test fixture asserting on the old `step (g) blocks step (h)` ordering. Halt — likely indicates a test that needs updating alongside the decouple.
4. **The dogfood-at-seal-time §14 backfill fails** (this plan-doc's own seal at build step 4). Would indicate the decouple itself doesn't work in production. Halt and surface (this is the build-time analogue of #136's regex-widening dogfood).
5. **The seal step's exit code after decouple no longer surfaces the dry-run failure.** Would defeat AC.SCT.2 and lose the operator-visible signal. Halt.
6. **A new ordering bug between the §14 backfill commit and a possible later `(i)` FIDRAFT-cleanup hook surfaces** — `_finalize` step (i) at `seal.py:1088-1098` fires `_emit_fidraft_cleanup_surface` after the §14 backfill; that ordering is preserved by this amendment (the backfill still happens BEFORE step (i)). If the builder finds a hidden interaction, halt + surface.
7. **The existing 4 pre-existing loam-amend test failures** (per #140 §16 #6 — `test_AC_DPS1_13`, `test_AC_DPS2_10`, `test_AC_D_1_5_4`, `test_AC_D_sa_6`, all rooted in the oversized `smoke_outcome` field of an unrelated manifest). These remain pre-existing-and-unrelated; their presence at seal time is expected. If they multiply (i.e., this amendment's edits introduce ADDITIONAL failures), halt.

---

## §7. Ship shape

Single cycle, single component, single-scope amendment. Commit ladder (expected):

1. **Plan-doc + manifest commit** — this file + paired manifest YAML.
2. **Source-edits + tests commit** — `fix(loam-amend): decouple seal-tool §14 backfill from post-seal dry-run gate`. One source edit (the decouple in `_finalize`) + 4 new test files (AC.SCT.{1,2,3,S}).
3. **`loam amend apply`** auto-commit.
4. **`loam amend seal --plan-doc`** deterministic seal commit. **Dogfood:** THIS seal exercises the decoupled code path — assuming a clean working tree, the post-seal dry-run passes AND the §14 backfill fires, looking byte-identical to the pre-fix happy path. The decouple's distinct behaviour is only observable when dry-run fails; that's what AC.SCT.S verifies via synthetic fixture.
5. **§14 SHA-register backfill commit** — auto-embedded by step (h) of the seal (now decoupled from step (g), but step (g) is expected to pass cleanly for this amendment's own seal anyway). The proof-of-fix is the test suite, not this amendment's own seal cycle.

**Builder method guidance (builder's call per ODD §1.1):** the decouple shape is constrained by the AC ladder + the no-amend CDC. The simplest method that satisfies AC.SCT.{1,2,3,S}: extract the dry-run-result-handling so the diagnostic + return-code propagation happen AFTER the §14 backfill (instead of as an early `return dry_rc`). Pseudocode shape (illustrative — not prescriptive):

```
# (g) Post-seal apply --dry-run (capture result, defer return)
dry_rc = _apply_dry_run_post_seal(effective_manifest_path)
if dry_rc != 0:
    _emit_diagnostic(...)  # diagnostic still emits at the failure point
    # (do NOT return yet — fall through to (h))

# (h) §14 backfill (unconditional, when plan_doc supplied)
if effective_plan_doc is not None:
    ...  # existing backfill logic unchanged

# (i) FIDRAFT cleanup surface (unchanged ordering)
if effective_plan_doc is not None and not skip_fidraft_cleanup:
    _emit_fidraft_cleanup_surface(...)

# Final return: dry_rc if non-zero, else 0
return dry_rc
```

Alternative methods (split helpers, separate `_run_post_seal_followups` function, etc.) are equally valid per ODD §1.1. The AC contract pins the outcome (backfill + dry-run + exit code all surface), not the mechanism.

---

## §8. Out of scope (extended notes)

See §3 for the in-scope/out-of-scope list. Additional notes:

- **The post-seal dry-run will still fail noisily.** The decouple does not silence dry-run failures — it just stops them from blocking the §14 backfill. The operator still sees the dry-run diagnostic + still gets a non-zero exit code from the seal command. This amendment defers no responsibility to operator-visible signal; if anything, it strengthens the signal (the operator now also sees the §14 backfill commit landing, which makes the post-halt recovery shape cleaner — only the corrective fixup is needed, not the §14 backfill on top).
- **No retry / no rerun.** If the operator authors a corrective fixup commit + re-runs `loam amend apply --dry-run` by hand and it passes, the §14 backfill is ALREADY done from the original seal invocation — re-running the seal step would invoke AC.SCT.3 idempotence (no double-emit). Operator workflow stays simple.

---

## §10. F2 Ruthless Feedback (honest doubts)

1. **Shape (b) auto-retry was explicitly proposed in the FIDRAFT as an alternative.** Tier-0 read of the FIDRAFT line 332: "Proposed shape: decouple §14 backfill from post-seal verification — the backfill should fire even if the dry-run halts (the dry-run failure surfaces separately). Alternative: auto-retry the backfill after corrective fixup commits land." Shape (a) is the FIDRAFT's primary recommendation; shape (b) is the alternative. The dispatch brief leaned (a); this plan-doc confirms (a) for the reasons in §1 + §14 D-SCT.SHAPE. **Risk of (a):** the §14 backfill commit captures `seal_sha` at the moment of the original seal — if the operator subsequently authors a corrective fixup (`git commit` — never `--amend`), the §14 register's `seal_sha` still points at the ORIGINAL seal commit, not the corrective fixup. Is that the correct address? **Yes** — the §14 register documents the seal commit specifically (per AC.D-sa.7 and the seal.py line 1057 mechanise note); corrective fixups are tracked separately (often in §16 of the plan-doc, as #138 did). The seal commit IS the canonical anchor; subsequent fixups are recovery context.
2. **What if the dry-run is failing because the seal commit itself is malformed in a way the backfill is sensitive to?** E.g., the seal commit's body parsing for `amendment_sha` in `_backfill_plan_doc_shas` depends on the seal-commit message format. Tier-0 read: `_backfill_plan_doc_shas(plan_doc, amendment_sha, amendment_subject, seal_sha, seal_subject)` — the SHAs and subjects are passed in as parameters, computed from `_head_sha(repo_root)` + `_commit_subject(repo_root, seal_sha)` at lines 940-941 (before step (g)). Both are derived from the seal commit itself, not from `apply --dry-run`. **The backfill is NOT sensitive to dry-run state.** Verified.
3. **Could a future dry-run mode return non-zero for a backfill-affecting reason?** Tier-0 read: `apply.py`'s `run(..., dry_run=True)` reports `MISSING_ADMISSION` / unstaged-changes / partition-overlap / dirty-tree-against-baseline class checks. None of these influence whether the §14 heading exists or whether the seal SHAs are addressable. **The two concerns are orthogonal.** Verified.
4. **Idempotence under retry.** If the operator re-runs `loam amend seal` after authoring a corrective fixup, `_backfill_plan_doc_shas` already idempotently no-ops when the `### Commit SHAs` subsection is current (`seal.py:1021-1024`). AC.SCT.3 codifies this. Risk: low — the existing idempotence is verified by `test_AC_LAS14R_*` family already.
5. **Does this amendment compose cleanly with #140 Scope B's dirty-tree-check-before-archive reorder?** Yes — #140 changed steps (b)/(c) ordering (gate-then-archive); this amendment changes steps (g)/(h) coupling (decouple backfill from dry-run). Different scopes entirely. The composition: in the new flow, a dirty tree halts BEFORE seal (per #140 Scope B), so no seal commit lands; therefore no §14 backfill should fire either (which is the current behaviour, preserved by this amendment — the backfill only fires when `effective_plan_doc is not None` AND we've passed all the earlier halts). **Verified by re-reading `_finalize` 700-1100.**
6. **F4 scope-confidence calibration.** Outcome shape is well-pinned (precise, observable, single-mechanism). Scope is tight: objective + AC pin the contract; method (extract a helper, restructure as if/elif/return-late, etc.) stays the builder's call. AC.SCT.S smoke is the load-bearing outcome-altitude probe; AC.SCT.{1,2,3} are mechanism-level invariants. Composes with `feedback_prompt_scope_confidence` — high confidence in outcome, moderate confidence in code-shape, tight enough to forbid out-of-scope edits, loose enough to not prescribe HOW.
7. **No method-in-AC.** Each AC is outcome-shaped. The method-in-AC test for AC.SCT.1: could the AC be satisfied by a method other than "extract the dry-run return into a deferred step"? Yes — could also be satisfied by running the backfill in a `try: ... finally:` block, by splitting `_finalize` into `_finalize_pre_followup` + `_finalize_followup`, by a state-machine refactor. The AC pins the outcome (backfill commit lands when seal lands, regardless of dry-run), not the mechanism. Builder's call.
8. **Locked-design revisit (per `feedback_locked_design_not_license_for_bad_outcomes`).** The current coupling (step (g) early-returns before step (h)) is itself a locked design — established at AC.D-sa.7 authoring time, preserved through #136's widened-regex amendment. The operational outcome (every dry-run failure forces a manual §14 backfill commit, even when the §14 register is unaffected) is bad. Per the locked-design-not-license discipline: the prior decision is revisitable when its outcome is empirically bad enough. #138's manual recovery (commit `7d893b0`) is the empirical trigger. Revisit + replace.

---

## §14. Method-decision register

**Ratification table (recorded at plan-doc commit time, populated post-build by §14 backfill commit or by hand):**

| Decision | Recommendation | Ratified by | Authority |
|----------|----------------|-------------|-----------|
| D-SCT.SHAPE | (a) Always-run backfill, decoupled from dry-run. Reject (b) auto-retry. Simpler (no new runtime state); preserves dry-run signal (still emits + still drives exit code); independent of dry-run outcome (the §14 register documents the seal SHA, not the dry-run SHA). | `loam-plan-author` subagent | Owner build-strategy delegation TG 11808 + re-evaluation directive TG 11854 |
| D-SCT.ERROR-SURFACE | Dry-run failure still emits its existing `post-seal-dry-run-failed` diagnostic at the failure point; the seal command's return code still equals the dry-run's non-zero exit code. The decouple is solely about REACHABILITY of step (h), not about silencing step (g). | `loam-plan-author` subagent | Owner build-strategy delegation TG 11808 |
| D-SCT.AC-LADDER | AC.SCT.{1,2,3} for mechanism invariants + AC.SCT.S for outcome-altitude smoke (synthetic dry-run-fails-but-backfill-still-fires fixture). One AC family for this single-scope amendment. | `loam-plan-author` subagent | F3 / Lens 5 swarming (EVAL_DIMENSIONS named-axis judging) — one axis suffices for a single-mechanism decouple. |
| D-SCT.IDEMPOTENCE | The existing `_backfill_plan_doc_shas` + `git diff --cached --quiet` idempotence path (`seal.py:1015-1024`) is preserved by the decouple; AC.SCT.3 codifies its invariance. No new idempotence mechanism. | `loam-plan-author` subagent | Pre-existing convention (covered by `test_AC_LAS14R_S_smoke.py`). |
| D-SCT.ORDERING | Order in `_finalize` post-decouple: (g') dry-run runs + diagnostic emits on failure (no early return) → (h') §14 backfill runs unconditionally on plan-doc presence → (i') FIDRAFT cleanup surface (unchanged) → final `return dry_rc`. | `loam-plan-author` subagent | ODD §1.1 — method-level guidance; builder's call to refactor (helper vs inline). |

**Rationale (Tier-0 verified at plan-authoring time, canonical HEAD `b46162f`):**

- **D-SCT.SHAPE** — shape (a) is the FIDRAFT's primary recommendation (line 332: "Proposed shape: decouple §14 backfill from post-seal verification — the backfill should fire even if the dry-run halts"). Shape (b) auto-retry was offered as an alternative; rejected here because: (i) (a) is mechanically simpler — no deferred-backfill state to track; (ii) (a) preserves all operator-visible signals (dry-run failure log + non-zero exit code); (iii) (a) makes the §14 register a deterministic post-seal artefact (always present when seal commit lands), which simplifies downstream audits.

- **D-SCT.ERROR-SURFACE** — the operator's signal source is the dry-run diagnostic (`post-seal-dry-run-failed` `klass:` block) + the non-zero exit code. Both are preserved unchanged. The decouple only changes whether step (h) is reachable, not whether step (g) emits.

- **D-SCT.AC-LADDER** — single-mechanism single-AC-family per Lens 5 EVAL_DIMENSIONS. No interaction risk with other code paths needing separate axes.

- **D-SCT.IDEMPOTENCE** — pre-existing idempotence is verified by `test_AC_LAS14R_S_smoke.py:test_idempotence_no_double_emit` (already in the corpus). AC.SCT.3 adds an explicit assertion under the new decoupled ordering — guards against any accidental change to idempotence introduced by the refactor.

- **D-SCT.ORDERING** — preserves step (i) FIDRAFT cleanup surface ordering (after step (h), before final return). The cleanup surface fires only when `effective_plan_doc is not None and not skip_fidraft_cleanup` — same gate as today.

---

### Commit SHAs

- Amendment commit: `d334ad58d2401dcf5987ae1ecebec56a21d044a2` —
  `chore(amend): loam-amend seal: decouple §14 SHA backfill from post-seal dry-run gate. Pre-fix (b46162f canonical), `_finalize` step (g) at seal.py:947-969 early-returns on `loam amend apply --dry-run` non-zero exit, blocking step (h) (the §14 SHA-backfill at seal.py:971-1086) from firing. Empirically: amendment #138's orphan-file dry-run failure forced operator to author a manual §14 backfill commit (7d893b0), defeating amendment #136's no-manual-fallback promise.`
- Seal commit: `c144c2d2098f3fc1b022a873be0d15c6812fcb7f` —
  `chore(seals): loam-amend seal: decouple §14 SHA backfill from post-seal dry-run gate. Pre-fix (b46162f canonical), `_finalize` step (g) at seal.py:947-969 early-returns on `loam amend apply --dry-run` non-zero exit, blocking step (h) (the §14 SHA-backfill at seal.py:971-1086) from firing. Empirically: amendment #138's orphan-file dry-run failure forced operator to author a manual §14 backfill commit (7d893b0), defeating amendment #136's no-manual-fallback promise.`
## §16. Halt-and-surface findings (raised + ruled at plan-authoring)

1. **The dispatch brief framed the decision as "investigate the current code path + recommend (a) or (b)".** Tier-0 verification confirms the code-path inspection: step (g) at `seal.py:947-969` early-returns on dry-run failure; step (h) at `seal.py:971-1086` is only reached when (g) returns 0. The decouple is mechanically straightforward; the question is purely shape-of-fix. **Ruling:** shape (a) recommended per the FIDRAFT's primary proposal + the §10 F2 rationale; recorded as D-SCT.SHAPE.

2. **The dispatch brief noted a possible hidden safety reason for shape (b).** Investigated in §10 F2 #1: the only candidate hidden reason was "the §14 register's seal_sha pointer becomes stale if the operator authors a corrective fixup." Verified that's NOT a load-bearing concern — the §14 register documents the seal commit, not HEAD; corrective fixups are tracked separately. **Ruling:** no hidden safety reason; shape (a) is the right call. Recorded in §10 F2 #1.

3. **The plan-doc's §6 step 4 dogfood at seal time is expected to LOOK byte-identical to the pre-fix happy path.** When the working tree is clean + the plan-doc + manifest are correctly authored, the post-seal dry-run passes + the §14 backfill fires — same behaviour as today. The decouple's distinct behaviour is only observable when dry-run fails. **Ruling:** this is correct + intentional — AC.SCT.S synthetic fixture exercises the dry-run-fails path; the seal-time dogfood does not need to.

4. **Pre-existing untracked plan-doc in working tree** — `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` (unrelated workstream, PENDING owner ratification, plan-only). Admitted via `--allow-untracked-globs` at seal time per §5 universal admissions. Same admission as #140 §5. **Ruling:** not this amendment's concern; admission is dirty-check-only.

5. **4 pre-existing loam-amend test failures on canonical HEAD `b46162f`** (per #140 §16 #6) — `test_AC_DPS1_13`, `test_AC_DPS2_10`, `test_AC_D_1_5_4`, `test_AC_D_sa_6`, rooted in the oversized `smoke_outcome` field of `docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml`. Tracked separately as `ws-loam-amend-oversized-manifest-field-cleanup`. **Ruling:** OUT OF SCOPE for this amendment; halt-trigger #7 in §6 distinguishes "new regression from this amendment's edits" (halt) from "pre-existing canonical-state failures unrelated" (capture + dispatcher ruling).

6. **Section-14 heading shape.** This plan-doc uses `## §14. Method-decision register` (canonical post-#136 shape with §-prefix + em-dash). #136's widened regex matches this shape; #140's seal-time §14 backfill confirmed the auto-backfill works on canonical headings. This amendment's seal-time §14 backfill is expected to fire cleanly via the same path. **Ruling:** rely on the widened regex; halt-trigger #4 surfaces if the dogfood breaks.

7. **FIDRAFT entry uses `§14` token, not `SECTION-14`.** Initial grep search using `SECTION-14` returned no results; the actual FIDRAFT name is `F-SEAL-TOOL-§14-BACKFILL-COUPLED-TO-DRY-RUN`. The dispatch brief used the substituted `SECTION-14` for ASCII compatibility — same target. **Ruling:** plan-doc cites the FIDRAFT by its canonical `§14` name in §2 + §17.

---

## §17. Composition (M5 derivation line)

- **Composes with** amendment #136 (sealed at `5c73a30` — seal §14 backfill regex widening) — this amendment defends #136's no-manual-fallback promise unconditionally (it held only when dry-run cleanly passed; now holds even when dry-run halts).
- **Composes with** amendment #138 (sealed at `01e63ac` + corrective fixup `26f3a9e` + manual §14 backfill `7d893b0`) — the empirical trigger. §138 §16 finding #2 explicitly proposed this amendment's two-option shape.
- **Composes with** amendment #140 (sealed at `8a41e7b` — seal-tool hygiene pair) — same touch site (`_finalize` in `seal.py`); preserves all of #140's reorderings (dirty-tree-check-before-archive in steps (b)/(c)) and only touches steps (g)/(h) coupling. Different scopes; no overlap.
- **Composes with** `feedback_locked_design_not_license_for_bad_outcomes` — the step (g)→(h) coupling is a locked design from AC.D-sa.7 authoring; operational outcome (manual §14 backfill on every dry-run halt) is bad enough to revisit + replace.
- **Composes with** `feedback_workaround_masks_rootcause_urgency` — #138's manual `7d893b0` backfill commit is the workaround that masked this; second-recurrence trigger threshold met; this amendment IS the root-cause fix.
- **Composes with** `feedback_information_trust_ordering` — Tier-0 source-read of `seal.py:947-1086` + `_backfill_plan_doc_shas` is the basis for the §14 D-SCT.SHAPE rationale; not Tier-2 inference from the FIDRAFT text alone.
- **Composes with** F2 Ruthless Feedback — §10 surfaces every honest doubt (shape (b) alternative, sealing-sha staleness, dry-run side-effect risk, ordering composition with #140) rather than silently shipping (a).
- **Composes with** F3 / Lens 5 swarming — EVAL_DIMENSIONS named-axis judging applied (single AC family for a single-mechanism decouple is the right axis count).
- **Closes** `F-SEAL-TOOL-§14-BACKFILL-COUPLED-TO-DRY-RUN` on seal.
- **Independent of** F4 — outcome shape is well-pinned regardless of scope-confidence framing.

---

loam-amend seal: decouple §14 SHA backfill from post-seal
dry-run gate. Pre-fix, `_finalize` step (g) early-returned on
dry-run non-zero exit, blocking step (h) (§14 SHA backfill)
from firing. Empirically: amendment #138's orphan-file dry-run
failure forced operator to author manual backfill commit
`7d893b0`, defeating #136's no-manual-fallback promise.

Post-fix: §14 backfill runs unconditionally when a `--plan-doc`
was supplied AND a seal commit landed, regardless of dry-run
outcome. Dry-run diagnostic still emits at failure point; seal
command return code still equals dry-run exit code. Operator-
visible signals preserved; only step-(h) reachability changes.

Shape (a) "always-run backfill" chosen over shape (b) "auto-
retry-after-fixup" per §14 D-SCT.SHAPE: mechanically simpler,
preserves all signals, §14 register documents seal SHA (not
HEAD — corrective fixups land separately).

Composes with amendment #136 (defends its no-manual-fallback
promise unconditionally), amendment #138 (empirical trigger —
retires the manual `7d893b0` workaround per `feedback_-
workaround_masks_rootcause_urgency`), amendment #140 (same
`_finalize` function, disjoint scope).

Closes F-SEAL-TOOL-§14-BACKFILL-COUPLED-TO-DRY-RUN on seal.
