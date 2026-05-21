# Amendment #142 — plan-author SKILL + dev-sdlc methodology hygiene (merged: manifest-target default + BASELINE walk-forward + source-edit-commit-before-apply step)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 by `loam-plan-author` subagent per dispatch from owner (TG 11808/11837/11847).
**Working directory:** `/Users/lukeivers/loam/`.
**Predecessor (load-bearing):** amendment #141 publish-state commit `2686101683264a21f938a1dc1eca21f530ba9a67` (current HEAD post-publish — `docs(readme): bump current-release to v0.12.18 (amendment #141 section-14 backfill decouple)`).
**Parent captures:** three FIDRAFT entries at `docs/FUTURE_IDEAS_DRAFT.md` — line 330 (`F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP`), line 334 (`F-LOAM-AMEND-APPLY-IMPLICIT-COMMITTED-HEAD-DEPENDENCY`), line 336 (`F-BASELINE-SELECTION-VS-POST-SEAL-CORRECTIVE-FIXUPS`). All three were captured 2026-05-21 from amendments #138 / #139 build-agent findings; all three name the plan-author / dev-sdlc methodology surface; all three carry "consolidate with the next plan-author SKILL update" activation gates. Owner TG 11847 ratifies the queue-merge.
**Quality bar:** single-component amendment (`dev-sdlc`). Three AC sub-families (AC.PASH.A / .B / .C) per scope + one outcome-altitude smoke (AC.PASH.S) exercising the full template-fix + walk-forward + methodology-step path end-to-end against a synthetic amendment cycle.

---

## §1. Objective / Summary / TL;DR

Harden the plan-author SKILL set and the dev-sdlc methodology docs so a session-fresh persona (or a dispatched build agent) authoring the next amendment cannot reproduce any of three failure modes empirically observed during amendments #138 and #139:

1. **Scope A — manifest `narrative.target` default** (per FIDRAFT line 330). The plan-author SKILLs do not currently prescribe the FORM of `narrative.target`. Empirical evidence (#138 manifest, `target: dev-sdlc`) shows agents default to component-name when no prescription exists; seal-tool dutifully writes a 2778-byte orphan file at `<repo>/dev-sdlc`, requiring corrective fixup commit `26f3a9e`. **Fix:** the plan-author SKILL prose + the `plan-docs.md` convention doc + the `seal-narrative-writer` SKILL all converge on `narrative.target: docs/plans/sealed/<slug>.md` as the canonical default, matching the post-#134 T1.4 archive convention.

2. **Scope B — BASELINE walk-forward** (per FIDRAFT line 336). Plan-author SKILLs currently pin BASELINE to "predecessor seal commit." When a corrective `chore(amend-fixup):` commit landed between that seal and HEAD (as #138 had at `26f3a9e`), the BASELINE is one commit stale and the next amendment hits a `MISSING_ADMISSION` halt that requires a corrective re-baseline commit (as #139 needed at `ca16e41`). **Fix:** the plan-author SKILLs prescribe BASELINE selection as "walk forward from the predecessor seal commit; if any `chore(amend-fixup):` commits exist between that seal and current HEAD, pick the latest fixup; else the seal commit itself." This is a *discipline* update — no new tooling, no new code paths.

3. **Scope C — source-edit-commit-before-apply** (per FIDRAFT line 334). `loam amend apply` runs against committed HEAD (verified by Tier-0 read of `apply.py:158`); the canonical commit-ladder docs name "feature commit" implicitly as a step but the operative methodology surface doesn't EXPLICITLY name "commit your source edits first" as a step preceding `loam amend apply`. #138 builder ran apply against uncommitted edits, recovered via `git reset --mixed` + manual recommit. **Fix:** the dev-sdlc methodology docs (`commit-ladder.md` + `amendment-cycle.md`) AND the plan-author SKILL prose explicitly name "source-edit commit BEFORE `loam amend apply`" as a step; the `loam amend apply` CLI emits a soft warning (non-blocking) when tracked-but-unstaged changes exist in the working tree at apply time.

**Shape decision: merged single amendment** (per TG 11847 queue-merge directive). All three scopes touch the same plugin component (`dev-sdlc`), the same SKILL surface, and the same methodology docs. Merging saves one apply + seal cycle vs three sequential amendments; the AC families are scope-disjoint (.A / .B / .C) so the seal-diff is clean and the AC ladder reads naturally. No interaction risk between the three sub-scopes — Scope A is SKILL-prose + convention-doc edits; Scope B is SKILL-prose edits only; Scope C is SKILL-prose + methodology-doc edits + a single soft-warning emission in `apply.py`.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T~16:14Z | Build-strategy delegation (plan-author SKILL + dev-sdlc methodology hygiene IS build-strategy territory). |
| TG 11837 | 2026-05-21T~19:00Z | Durable-autonomy directive — proceed without per-step ratification on in-scope authorized work. |
| TG 11847 | 2026-05-21T~21:30Z | Queue-merge directive — merge the three FIDRAFT-330 / -334 / -336 scopes into a single amendment because all three touch the same SKILL + methodology surface; save apply + seal overhead. |

**Pre-flight verification (Tier-0 at canonical HEAD `2686101`, 2026-05-21T22:56:11Z):**

- **`git rev-parse HEAD` returned `2686101683264a21f938a1dc1eca21f530ba9a67`.** Full SHA verified by direct `git rev-parse HEAD` call — no transcription. Recorded as BASELINE in the paired manifest. **Verified by direct shell invocation.**
- **FIDRAFT entries located:** lines 330 / 334 / 336 of `docs/FUTURE_IDEAS_DRAFT.md`. All three entries name "next plan-author SKILL update" or equivalent as activation gate. **Verified by `grep -n "^- \*\*F-PLAN-AUTHOR-SKILL-MANIFEST\|F-BASELINE-SELECTION\|F-LOAM-AMEND-APPLY-IMPLICIT"`.**
- **`plugins/dev-sdlc/skills/plan-docs-author/SKILL.md`** — 489 lines; contains the §1-§14 plan-doc shape prescription but does NOT prescribe `narrative.target` form. **Verified by direct read.**
- **`plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md`** — 276 lines; contains the same shape, also does NOT prescribe `narrative.target` form. **Verified by direct read.**
- **`plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md`** — 179 lines; line 30 names `narrative.target` as a required manifest field but does NOT prescribe its form. **Verified by direct read.**
- **`plugins/dev-sdlc/skills/seal-narrative-writer/SKILL.md`** — line 8 says the seal narrative "lands in `plugins/<plugin>/seals/SEAL_COMMIT.<slug>`" — the LEGACY shape, pre-T1.4. **Verified by direct read.** This is a stale prescription; Scope A updates it.
- **`plugins/dev-sdlc/docs/conventions/plan-docs.md:48`** — names `narrative: {target, body}` as a required field but does NOT prescribe target form. **Verified by direct read.**
- **`plugins/dev-sdlc/docs/conventions/commit-ladder.md:53`** — says "Per-component seal narrative target: `<component>/seals/SEAL_COMMIT.<slug>`" — also the LEGACY shape; needs Scope A update.
- **`plugins/dev-sdlc/docs/conventions/commit-ladder.md:7-15`** — names the canonical commit ladder (plan-doc → feature → corrective → apply → seal). The "feature commit(s)" rung at line 12 IS the source-edit-commit step; Scope C makes the "this happens BEFORE `loam amend apply`" ordering explicit.
- **`plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/apply.py:158`** — `head_sha = _git_head_sha(repo_root)` — confirms apply runs against committed HEAD. No working-tree freshness check before this line. **Verified by direct read.**
- **`plugins/dev-sdlc/tools/loam-amend/src/loam_amend/dry_run.py:66-96`** — `_diff_with_working_tree` ALREADY detects tracked-but-unstaged changes for the DRY-RUN window. The mechanism exists; Scope C reuses it for a real-apply soft warning.
- **Empirical `narrative.target` shape distribution at canonical HEAD:**
  - Legacy `framework/<comp>/seals/SEAL_COMMIT.<slug>` shape: #134, #135.
  - Canonical post-T1.4 `docs/plans/sealed/<slug>.md` shape: #137, #139, #140, #141.
  - Bug shape (`dev-sdlc` component-name only): #138 — the FIDRAFT-330 empirical trigger.
  - Missing field: #136.
  Verified by `grep -A1 "^narrative:" docs/plans/sealed/amendment-13{4..9}*.manifest.yaml docs/plans/sealed/amendment-14{0,1}*.manifest.yaml`. **The canonical shape is empirically established by #137/#139/#140/#141; the SKILL prose just needs to catch up.**
- **No prior amendment closes any of these three FIDRAFTs.** Verified by `git log --oneline -- docs/FUTURE_IDEAS_DRAFT.md` since the 2026-05-21 capture commits.
- **One pre-existing untracked plan-only file** in working tree: `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` (unrelated workstream, pending owner ratification). Admitted at seal time via `--allow-untracked-globs` per the #140/#141 admission precedent.

---

## §2. Predecessors / context

- **Amendment #138** (dev-sdlc test directory cleanup, sealed at `01e63ac` + corrective fixup `26f3a9e` + manual §14 backfill `7d893b0`). Empirical trigger for Scope A (the `target: dev-sdlc` orphan-file bug) AND Scope C (the apply-against-uncommitted-edits halt). #138 §16 findings #1 + #3 directly proposed these scopes.
- **Amendment #139** (dev-sdlc manifest runtime flag, sealed at `1f3d8d7` + corrective re-baseline commit `ca16e41`). Empirical trigger for Scope B (the stale-BASELINE-vs-fixup pattern). #139 §16 finding #2 proposed Scope B.
- **Amendment #134** (FBM Tier 1 foundations, T1.4 amendment-plan archive-on-seal). Established the `docs/plans/sealed/<slug>.md` convention that Scope A converges on. The `plan_archive.py` module + `AC.FBMT1.APS.{1,2,3,4}` codify it in code; this amendment makes the convention explicit in the SKILL prose where authoring agents read it.
- **Amendment #141** (seal-tool §14 backfill decouple, sealed at `c144c2d` + §14 backfill `ce32dee` + publish-state `2686101`). Predecessor seal commit; predecessor publish-state IS the canonical HEAD this amendment baselines against. #141 also dogfooded the §14 backfill auto-write into a `docs/plans/sealed/<slug>.md` narrative target — the convention this amendment is now codifying in the SKILL prose.
- **Amendment #140** (seal-tool hygiene pair, sealed at `8a41e7b` + publish-state `b46162f`). Established the queue-merge precedent: two scopes touching the same `_finalize` function merged into one amendment per TG 11847's predecessor directive. This amendment mirrors the pattern: three scopes touching the same SKILL + methodology surface, merged into one cycle.
- **No prior amendment has touched the plan-author SKILL set in the form this amendment proposes.** The SKILL files have evolved (trim discipline 2026-05-05 added §3-cycle-decomposition + §4-AC enumeration partition; T1.4 added the `sealed/` archive convention at the code level), but the `narrative.target` form prescription has not been written into any SKILL prose. This is the first SKILL-prose hardening pass.

---

## §3. Scope

**In-scope (the three merged sub-scopes):**

**Scope A — manifest `narrative.target` default = `docs/plans/sealed/<slug>.md`:**
- Patch `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — add a new section (e.g., under "## Composition" or after the §9 Bookkeeping prescription) explicitly prescribing `narrative.target: docs/plans/sealed/<slug>.md` as the canonical form, with a worked example.
- Patch `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` — same prescription, integrated into step 10 (§9 Bookkeeping) or as a new sub-step.
- Patch `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` — update line 30's manifest-field enumeration to prescribe the canonical form for `narrative.target`.
- Patch `plugins/dev-sdlc/skills/seal-narrative-writer/SKILL.md` — update line 8's prescription from the legacy `plugins/<plugin>/seals/SEAL_COMMIT.<slug>` to the canonical `docs/plans/sealed/<slug>.md`.
- Patch `plugins/dev-sdlc/docs/conventions/plan-docs.md` §3 — add the form prescription to the `narrative.target` line.
- Patch `plugins/dev-sdlc/docs/conventions/commit-ladder.md:53` — update the legacy "Per-component seal narrative target" line to the canonical form.

**Scope B — BASELINE walk-forward from predecessor seal:**
- Patch `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — add prescription for "BASELINE selection: walk forward from the predecessor seal commit; if any `chore(amend-fixup):` commits exist between that seal and current HEAD, pick the latest fixup; else the seal commit itself" under a new "BASELINE selection" subsection or as part of step 18.
- Patch `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` — same prescription in the manifest-authoring flow.
- Patch `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` — same prescription in step 4 (BASELINE is the source-edit feat commit) and an explicit note that authoring a NEW amendment requires walking forward from the predecessor seal.

**Scope C — source-edit-commit-before-apply step + soft pre-apply warning:**
- Patch `plugins/dev-sdlc/docs/conventions/commit-ladder.md:7-15` — make explicit that "feature commit(s) MUST land BEFORE `loam amend apply`; apply runs against committed HEAD, not working-tree state."
- Patch `plugins/dev-sdlc/docs/conventions/amendment-cycle.md` — same explicit ordering in the amendment-cycle convention doc.
- Patch `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` step 4-5 — add explicit note "the apply step at step 5 runs against committed HEAD; commit your source edits at step 4 before invoking apply."
- Add a soft pre-apply warning to `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/apply.py` — when `dry_run=False` AND the working tree carries tracked-but-unstaged changes that are NOT in the partition's universal_paths + extra_allowed_prefixes union, emit a warning to stderr ("warning: working tree has unstaged changes that will not land in this apply commit; commit them first if intended") but do NOT block. **Method-decision: warning, not error** (per FIDRAFT line 334 "non-blocking"); the existing `_diff_with_working_tree` at `dry_run.py:66-96` provides the detection mechanism; reuse it.

**Out-of-scope:**

- Any change that would automatically commit source edits before apply (the operator stays in control; apply is one-shot per invocation).
- Any change that would block apply on a dirty working tree (per FIDRAFT line 334: "Possibly enforced via a pre-apply check that warns if working tree has unstaged changes" — warns, not blocks).
- Any change to the apply algorithm itself beyond the pre-flight warning emission (the apply's actual behaviour vs committed HEAD is preserved unchanged; it's already correct, just under-documented).
- Any change to the BASELINE constant inside per-component seal-diff tests (`baseline.py` per-component literal — unrelated to manifest BASELINE).
- Any change to `loam amend new-plan` CLI's vars-file scaffold (it doesn't produce a manifest; out of fence for this amendment).
- A PreToolUse hook that scans dispatch briefs for SHA pairs (FIDRAFT 340 — F-DISPATCH-BRIEF-FULL-SHA-VERIFICATION; separate FIDRAFT, separate amendment).
- Pre-existing 4 loam-amend test failures rooted in oversized `smoke_outcome` field (per #140 §16 #6 and #141 §6 halt-trigger #7; tracked separately as `ws-loam-amend-oversized-manifest-field-cleanup`).
- Cross-component touches (`framework/<comp>/`, other plugins).

---

## §4. Acceptance criteria

| AC ID | Outcome | Verification | outcome-altitude |
|---|---|---|---|
| **AC.PASH.A.1** | A fresh persona/agent following the plan-author SKILLs to author a new manifest emits `narrative.target: docs/plans/sealed/<slug>.md` by default (not a component name, not the legacy `framework/<comp>/seals/SEAL_COMMIT.<slug>` shape). | Static-text test: greps `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md`, `plan-before-code-author/SKILL.md`, `loam-amend-cycle/SKILL.md`, `seal-narrative-writer/SKILL.md` for the canonical `docs/plans/sealed/<slug>.md` prescription string (or equivalent regex matching the template form); asserts each file carries the prescription. Also greps for the LEGACY `plugins/<plugin>/seals/SEAL_COMMIT.<slug>` and asserts it is no longer the prescribed default (still allowed as a back-compat note, but not the default). | false |
| **AC.PASH.A.2** | The `plan-docs.md` + `commit-ladder.md` convention docs prescribe the same canonical `narrative.target` form, and the prescription is consistent across all five surfaces (4 SKILLs + 2 convention docs). | Static-text test: greps both convention doc files for the canonical form; asserts presence; asserts no contradiction with the SKILL-side prescription. | false |
| **AC.PASH.B.1** | A fresh persona/agent following the plan-author SKILLs authoring an amendment that follows a fixup-bearing seal picks the latest `chore(amend-fixup):` commit as BASELINE (not the bare seal commit). | Synthetic-fixture test: temporary git repo with a seed seal commit `S` + a corrective fixup commit `F` (subject prefix `chore(amend-fixup):`) on top; invoke a helper function (extracted from the SKILL prescription — `select_baseline(repo, predecessor_seal_sha)`) that walks forward; assert it returns `F`, not `S`. | false |
| **AC.PASH.B.2** | When NO `chore(amend-fixup):` commits exist between the predecessor seal and current HEAD, BASELINE defaults to the seal commit itself (no regression vs the pre-fix discipline). | Synthetic-fixture test: temporary git repo with a seed seal commit `S` + an unrelated `docs:` commit on top; invoke `select_baseline(repo, S)`; assert it returns `S`, not the unrelated commit. | false |
| **AC.PASH.C.1** | The dev-sdlc methodology docs (`commit-ladder.md` + `amendment-cycle.md`) AND `loam-amend-cycle/SKILL.md` explicitly name "commit source edits BEFORE `loam amend apply`" as a step, in a form a fresh agent reading the doc end-to-end could not miss. | Static-text test: greps each of the three files for a regex matching the explicit ordering prescription (e.g., `before .* loam amend apply` AND `committed HEAD` near each other); asserts the prescription is present + reachable from the canonical doc-traversal path. | false |
| **AC.PASH.C.2** | `loam amend apply` (real-apply, not dry-run) emits a soft stderr warning when the working tree carries tracked-but-unstaged changes that would NOT land in the apply commit (because apply doesn't `git add -A`); the warning does NOT block apply. | Unit test against `apply.py`: synthetic repo with a valid manifest + a tracked file modified-but-unstaged in the working tree; invoke `apply.run(manifest_path, dry_run=False)`; assert (a) the return code is the same as the no-dirt control case (typically 0), (b) captured stderr contains the warning string, (c) the apply commit lands. | false |
| **AC.PASH.S** | Outcome-altitude smoke: a synthetic amendment cycle that exercises all three scopes end-to-end — (a) a plan-author authoring a manifest follows the SKILL prose and emits `narrative.target: docs/plans/sealed/<slug>.md`; (b) the cycle's BASELINE is selected from a synthetic predecessor with a post-seal `chore(amend-fixup):` commit, and BASELINE correctly resolves to the fixup; (c) the source-edit ordering halt is exercised — apply-with-unstaged-changes triggers the stderr warning but does NOT block; seal completes; the post-seal HEAD shows the plan-doc + manifest archived at `docs/plans/sealed/<slug>.md` per the T1.4 convention. | `outcome-altitude: true` — test invokes the production manifest-authoring helper (or the plan-author dispatch + SKILL-read flow if the helper is prose-only), the production `apply.run`, the production `seal.run`, against a synthetic tmpfs git fixture; no pre-arrangement of the orphan-target or stale-baseline conditions; asserts the three outcome conditions land green. | true |

**AC ladder-up:** AC.PASH.{A,B,C,S} → plan-author SKILLs + dev-sdlc methodology docs prescribe the canonical authoring shape such that a session-fresh agent dispatched to author the next amendment cannot reproduce the failure modes observed in #138 + #139 → AC.PO.2 (harness reduces translation burden by codifying the canonical authoring shape into the SKILL surface the agent reads, instead of relying on agents re-deriving it from precedent or recovering after the failure mode lands on disk).

---

## §5. Sealed-component fence (single-component)

**Component touched:** `dev-sdlc` ONLY.

Files in scope:

- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — Scope A + Scope B prose additions.
- `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` — Scope A + Scope B prose additions.
- `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` — Scope A + Scope B + Scope C prose additions.
- `plugins/dev-sdlc/skills/seal-narrative-writer/SKILL.md` — Scope A prose update (line 8 path replacement).
- `plugins/dev-sdlc/docs/conventions/plan-docs.md` — Scope A prescription addition to §3.
- `plugins/dev-sdlc/docs/conventions/commit-ladder.md` — Scope A line-53 update + Scope C explicit ordering addition to §1.
- `plugins/dev-sdlc/docs/conventions/amendment-cycle.md` — Scope C explicit ordering addition.
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/apply.py` — Scope C soft-warning emission (one new helper or inline check + one stderr `print` call).
- `plugins/dev-sdlc/tools/loam-amend/tests/` — new AC tests (`test_AC_PASH_A_1_*.py`, `test_AC_PASH_A_2_*.py`, `test_AC_PASH_B_1_*.py`, `test_AC_PASH_B_2_*.py`, `test_AC_PASH_C_1_*.py`, `test_AC_PASH_C_2_*.py`, `test_AC_PASH_S_*.py`).

**Universal admissions:**

- `docs/plans/` (this plan-doc + manifest; archives to `docs/plans/sealed/` on seal per T1.4 — and this amendment's `narrative.target` dogfoods the Scope A convention).
- `docs/FUTURE_IDEAS_DRAFT.md` (FIDRAFT cleanup-surface; admitted via `allow_untracked_globs` per AC.LAE.2 existing convention; this amendment closes three entries on seal).
- `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` — pre-existing untracked plan-only file (unrelated workstream PENDING owner ratification). Admitted via `--allow-untracked-globs` at seal time (same admission pattern as #140 §5 and #141 §5).

**Out of fence (halt-and-surface trigger):**

- Any other component under `framework/` or `plugins/`.
- Any other tool under `plugins/dev-sdlc/tools/` outside `loam-amend/` (Scope C touches apply.py only).
- Any change to `seal.py` / `manifest.py` / `dry_run.py` beyond the `_diff_with_working_tree` helper reuse (re-import only; no edit of `dry_run.py` itself; the helper is already exported-shaped).
- Any change to other plan-author-adjacent SKILLs not named in §5 above (`dispatch-brief-authoring`, `audit-finding-triage`, `loam-amend-status-quick`, etc.). Those compose with the plan-author SKILLs but their prose doesn't need the canonical-form prescription.
- Any change to FUTURE_IDEAS_DRAFT.md beyond the three FIDRAFT-closure surface (the seal-time FIDRAFT cleanup hook handles the closure automatically per AC.FBMT1.FCH ratified at #134).

---

## §6. Halt triggers (in-flight)

1. **Source edits leak outside `plugins/dev-sdlc/`.** Halt and surface.
2. **The pre-apply soft-warning emission breaks an existing test.** Likely `test_apply.py` family — assert no behaviour change for the clean-tree control case. If the warning fires when the tree IS clean (false positive), halt — likely indicates the `_diff_with_working_tree` detection is over-broad for the real-apply case (the dry-run case is fine because dry-run wants to see the whole window; real-apply only cares about tracked-unstaged changes that won't land). The builder may need to author a narrower detection helper for the real-apply path.
3. **The BASELINE walk-forward helper conflict with an existing helper.** Tier-0 grep confirmed no existing `select_baseline` or similar helper at canonical HEAD; if the builder finds one mid-flight, halt and surface (consolidation discipline — don't duplicate; integrate).
4. **A SKILL-prose edit inadvertently breaks the AC.D-sa.7 lint regex** (the `## 14.` heading regex). This is a tight invariant; the SKILL prose changes are well-bounded but if a re-flow accidentally re-numbers sections such that the §14 heading shape changes in a plan-doc THIS amendment authors, halt.
5. **The `apply.py` soft-warning implementation requires more than ~30 lines of code or introduces a new import beyond what's already in `apply.py` + `dry_run.py`.** F4 scope-confidence calibration: outcome is well-pinned; implementation should be small. If the builder finds the natural implementation crosses ~50 LOC or requires a new dependency, halt — likely indicates the design is more complex than the AC suggests and the AC needs revision (per `feedback_loose_AC_text_fix_AC_not_implementation`).
6. **The dogfood-at-seal-time §14 backfill fails.** The new SKILL prose + the new `narrative.target: docs/plans/sealed/<slug>.md` form (dogfooded by THIS amendment's manifest) should trigger #141's decoupled backfill cleanly. If the seal-time auto-backfill halts on this amendment, halt + surface (a regression in #141's decouple).
7. **The 4 pre-existing loam-amend test failures multiply.** Per #141 §6 halt-trigger #7: pre-existing failures rooted in `session-clear-safety-tracker...manifest.yaml`'s oversized `smoke_outcome` are expected at canonical HEAD. If THIS amendment's edits introduce ADDITIONAL test failures beyond that set, halt.
8. **An AC family's prescription overlaps with an existing SKILL-prose section in a way that makes the edit ambiguous (e.g., duplicate prescription).** Halt — likely indicates the SKILL prose already prescribes the canonical form somewhere and the FIDRAFT was wrong about the gap. Tier-0 verify before authoring the patch.
9. **Pre-flight dirty-tree warning's detection is sensitive to the partition's `universal_paths` admission.** The warning should fire when an unstaged tracked change is OUTSIDE the partition's admitted union (i.e., would not have landed in the apply commit anyway), not when it's inside (where it would have been picked up via the partition's prefix admission). If the builder finds the detection is over-broad in either direction, halt + clarify the AC.

---

## §7. Ship shape

Single cycle, single component, three-AC-sub-family amendment per the queue-merge directive. Commit ladder (expected):

1. **Plan-doc + manifest commit** — this file + paired manifest YAML.
2. **Source-edits + tests commit** — `fix(dev-sdlc): plan-author SKILL + methodology hygiene (manifest-target default + BASELINE walk-forward + source-edit-commit-before-apply step + apply pre-flight warning)`. Touches 9 source files (6 SKILL/convention prose + 1 apply.py edit + ~7 new test files) per §5. **The source-edit commit MUST land before `loam amend apply` per Scope C's own prescription — this is the first dogfood of the new methodology step.**
3. **`loam amend apply`** auto-commit.
4. **`loam amend seal --plan-doc`** deterministic seal commit. **Dogfood:** THIS seal exercises Scope A directly (the manifest's `narrative.target: docs/plans/sealed/amendment-142-plan-author-skill-hygiene-merged.md` IS the canonical post-fix shape) AND Scope B indirectly (the next amendment to follow this one will use the walk-forward discipline introduced here). T1.4 archives this plan-doc + manifest to `docs/plans/sealed/`. §14 auto-backfill via #141's decoupled path.
5. **§14 SHA-register backfill commit** — auto-embedded by `_finalize` step (h) (post-#141 decoupled, so even if the dry-run halts for any unrelated reason, the backfill still fires).

**Builder method guidance (builder's call per ODD §1.1):** the SKILL-prose edits are mechanical (find the right insertion point + add the prescription in the surface's existing voice). The `apply.py` soft-warning is the only non-prose edit; the simplest method is to reuse the existing `_diff_with_working_tree` from `dry_run.py` (import it directly into `apply.py` or extract a narrower helper) and emit a single `print(..., file=sys.stderr)` line in `apply.run` between the manifest-load and the bump-loop (after line 158, where `head_sha` is computed). The pseudocode shape (illustrative — not prescriptive):

```python
# Per AC.PASH.C.2: soft pre-flight warning on tracked-but-unstaged changes
# that would not land in this apply commit (apply does NOT git add -A).
if not dry_run:
    unstaged = _list_unstaged_outside_partition(repo_root, manifest)
    if unstaged:
        print(
            f"warning: working tree has {len(unstaged)} tracked-but-unstaged "
            f"change(s) that will not land in this apply commit; "
            f"commit them first if intended (per amendment-cycle convention).",
            file=sys.stderr,
        )
```

Alternative methods (factor the check into a separate helper module, use `logging.warning` instead of `print`, etc.) are equally valid per ODD §1.1. The AC contract pins the outcome (stderr emission, non-blocking, only fires on tracked-but-unstaged outside-partition state), not the mechanism.

---

## §8. Out of scope (extended notes)

See §3 for the in-scope/out-of-scope list. Additional notes:

- **The soft-warning's exact threshold logic is method-decision territory.** The detection might fire on ALL tracked-but-unstaged changes (simple) or ONLY tracked-but-unstaged changes that fall OUTSIDE the partition's admitted union (precise). The AC.PASH.C.2 outcome shape is "warning emits when tracked-but-unstaged exist; does NOT block." Either detection threshold satisfies the outcome; D-PASH.WARN-PRECISION (§14) recommends the precise form to avoid false-positive noise during well-formed cycles where the agent is mid-edit. Builder's call to confirm during implementation if false-positive noise during real-world use is a problem.
- **The SKILL prose additions should be MINIMAL.** Each scope's prescription is a 2-5 sentence addition to the relevant SKILL; avoid re-flowing entire SKILL sections. The mechanical test is "would a session-fresh agent reading the SKILL end-to-end find the prescription?" — yes is the bar; the bar is NOT "rewrite the SKILL's section structure."
- **No new SKILL files.** All edits land in existing SKILL files. Authoring a new SKILL specifically for these prescriptions would dilute the existing plan-author surface; the prescriptions live where the agents already look (the plan-author SKILLs + the dev-sdlc convention docs).
- **No retroactive sweep of historical sealed manifests.** #138's `target: dev-sdlc` shape is already corrected (the orphan was removed by `26f3a9e`); going back and "fixing" the manifest in its sealed location would violate the historical-record discipline. The Scope A discipline applies forward only.

---

## §10. F2 Ruthless Feedback (honest doubts)

1. **The Scope A prescription is "SKILL prose says do X" rather than tooling that enforces X.** A future plan-author may still hand-write `narrative.target: <component-name>` if they don't follow the SKILL prescription. The harder enforcement option would be: extend `loam amend validate` to lint `narrative.target` for the `docs/plans/sealed/<slug>.md` form. **Risk:** F4 scope-confidence on the simpler shape is high (the FIDRAFT 330 directly proposes SKILL-prose patching as the resolution; the prose surface IS where agents look at authoring time). **Mitigation:** if a future amendment shows the SKILL-prose form is insufficient (i.e., another `target: <component>` orphan lands), promote to tooling enforcement via a follow-on FIDRAFT. Captured here so the escalation path is visible.

2. **The Scope B walk-forward prescription is "SKILL prose says do X" rather than a helper function the agent calls.** Could implement `select_baseline(repo, predecessor_seal_sha)` as a Python helper in `loam_amend.baseline` or a new module, and have the SKILL prose say "call this helper." **Counter:** the helper would be ~15 LOC and the agents authoring manifests are typically NOT in a Python REPL — they're reading the SKILL prose and writing YAML. SKILL prose is the right surface. **Mitigation:** if the manual walk-forward proves error-prone (per a future FIDRAFT), the helper can land as a Phase-2 add.

3. **The Scope C warning's false-positive surface.** During an active multi-commit cycle where the agent is mid-edit, the working tree often has tracked-but-unstaged changes; the warning would fire on EVERY apply invocation, become noise, get ignored. **Mitigation:** the precise detection (D-PASH.WARN-PRECISION) fires only on changes OUTSIDE the partition's admitted union — i.e., on changes that would NOT land in the apply commit anyway. False-positive surface for that detection is narrow (genuine mid-edit changes inside the partition are admitted; the warning stays silent). Risk remains for edge cases (multi-component edits where one component is admitted and another isn't); the AC.PASH.C.2 + S smoke exercises the false-positive case explicitly.

4. **The three scopes have different severities in the FIDRAFT.** Scope A: medium (#138 leaked an orphan file). Scope B: medium (#139 needed corrective re-baseline). Scope C: low (recovery is straightforward; methodology gap). Merging three different-severity scopes into one amendment is justified by the same-component-surface argument; the F4 risk is that a halt on one scope blocks the others. **Mitigation:** §6 halt-trigger #2 + #5 are sub-scope-specific; if a halt fires on Scope C's apply.py edit, the SKILL-prose edits in Scope A + Scope B are independently reviewable + landable. The builder's call (per F4 looser-scope-on-lower-confidence) is whether to attempt the merge or split mid-flight; this plan-doc explicitly authorizes the merge at the outset.

5. **The AC.PASH.A test is "grep-the-SKILL-file" which is prose-shape verification, not behaviour verification.** A future SKILL re-write might preserve the literal prescription string but lose the prescriptive force. **Counter:** the test is "the prescription is reachable" — which is the verifiable outcome. The deeper question ("does following the prescription lead to the correct manifest?") is the AC.PASH.S smoke's responsibility, which IS behaviour-shaped. The two-layer AC strategy (prescriptive presence + outcome-altitude smoke) is the right partition.

6. **F4 scope-confidence calibration.** Outcome shapes for all three scopes are well-pinned (precise, observable, single-mechanism each). Scope is tight for each sub-family: objective + AC pin the contract; method (insertion point in the SKILL prose; helper extraction style in apply.py) stays the builder's call. AC.PASH.S smoke is the load-bearing outcome-altitude probe; AC.PASH.{A,B,C}.{1,2} are mechanism-level invariants. Composes with `feedback_prompt_scope_confidence` — high confidence in outcome shape for all three; the merge is the only F4-relevant call and the queue-merge directive (TG 11847) externally validates it.

7. **No method-in-AC.** Each AC is outcome-shaped. The method-in-AC test for AC.PASH.A.1: could the AC be satisfied by a method other than "grep the SKILL file for a literal string"? Yes — could also be satisfied by a fixture that invokes the SKILL via Claude SDK and verifies the rendered manifest, or by a parser that extracts the prescription from the SKILL prose programmatically. The AC pins the outcome (the prescription is reachable for an agent reading the SKILL), not the verification mechanism. Builder's call.

8. **Locked-design revisit (per `feedback_locked_design_not_license_for_bad_outcomes`).** The legacy `framework/<comp>/seals/SEAL_COMMIT.<slug>` narrative-target shape is itself a locked design from pre-T1.4 amendments. The operational outcome (agents default to component-name or framework path when no canonical-form prescription exists; #138's orphan-file empirical trigger) is bad. Per the locked-design-not-license discipline: revisit + replace. T1.4 (#134) already replaced it at the code level (`plan_archive.py` moves plan-docs into `sealed/`); this amendment replaces it at the SKILL-prose level so authoring agents converge on the same form.

9. **Composes with `feedback_workaround_masks_rootcause_urgency`.** #138's manual orphan-removal (commit `26f3a9e`) and #139's manual re-baseline (commit `ca16e41`) and #138's manual re-commit after the apply-against-uncommitted halt — three workarounds that mask the same root cause: the plan-author SKILL set does not prescribe the canonical authoring shape with enough rigor for a session-fresh agent. Two recurrences threshold met (Scope A: #138; Scope B: #139; Scope C: #138 + recovery). This amendment IS the root-cause fix.

10. **A note on swarming (Lens 5) at the AC family level.** The three sub-scopes are a natural EVAL_DIMENSIONS partition: Scope A (manifest target form), Scope B (BASELINE selection algorithm), Scope C (commit ordering + pre-flight warning). Three orthogonal axes; one judge per axis per the swarming reference pattern. The AC ladder (.A / .B / .C / .S) maps directly onto this; the AC.PASH.S smoke is the aggregator judge that verifies all three axes co-satisfied at outcome altitude. The merge is swarming-aware: parallel-shape decomposition with an outcome-altitude aggregator.

---

## §14. Method-decision register

**Ratification table (recorded at plan-doc commit time, populated post-build by §14 backfill commit):**

| Decision | Recommendation | Ratified by | Authority |
|----------|----------------|-------------|-----------|
| D-PASH.MERGE | Merge all three FIDRAFT scopes (330 / 334 / 336) into a single amendment. Touches the same `dev-sdlc` component + same SKILL + methodology surface; AC families are scope-disjoint (.A / .B / .C); save one apply + seal cycle vs three sequential amendments. | `loam-plan-author` subagent | Owner queue-merge directive TG 11847 |
| D-PASH.TARGET-DEFAULT | `narrative.target: docs/plans/sealed/<slug>.md` as the canonical default in all four SKILLs + both convention docs. NOT the legacy `framework/<comp>/seals/SEAL_COMMIT.<slug>` shape (still allowed as back-compat for pre-T1.4 historical manifests). NOT a component name (which is the bug shape `#138` shipped). Empirically established by `#137`/`#139`/`#140`/`#141` manifests. | `loam-plan-author` subagent | FIDRAFT 330 primary proposal; empirical convergence at canonical HEAD |
| D-PASH.BASELINE-WALK | Walk forward from the predecessor seal commit; if any `chore(amend-fixup):` commits exist between that seal and current HEAD, pick the latest fixup as BASELINE; else the seal commit itself. Discipline-only (no new tooling); SKILL-prose prescription. | `loam-plan-author` subagent | FIDRAFT 336 primary proposal; #139 empirical trigger |
| D-PASH.METHOD-DOC | Explicit "commit source edits BEFORE `loam amend apply`; apply runs against committed HEAD" step in `commit-ladder.md` + `amendment-cycle.md` + `loam-amend-cycle/SKILL.md`. Plus a soft (non-blocking) stderr warning emitted by `apply.run` when tracked-but-unstaged changes exist outside the partition's admitted union. | `loam-plan-author` subagent | FIDRAFT 334 primary proposal; #138 empirical trigger |
| D-PASH.WARN-PRECISION | Pre-flight warning fires ONLY when the tracked-but-unstaged change falls OUTSIDE the partition's `universal_paths + extra_allowed_prefixes` admitted union (the precise form). Rejects the simpler-but-noisier "fire on ANY tracked-but-unstaged" form. Reduces false-positive noise during well-formed mid-edit cycles; preserves the warning signal for the genuinely-out-of-partition case that #138 hit. | `loam-plan-author` subagent | F4 scope-confidence (the simpler form would become noise + get ignored; the precise form preserves signal) |
| D-PASH.WARN-NON-BLOCKING | The pre-flight warning emits to stderr but does NOT block apply (return code unchanged). Operator stays in control; the warning is a signal, not a gate. | `loam-plan-author` subagent | FIDRAFT 334 explicit text ("Possibly enforced via a pre-apply check that warns if working tree has unstaged changes") + non-amend CDC (the operator commits source edits themselves; the tool doesn't try to do it for them) |
| D-PASH.AC-LADDER | Six mechanism-level ACs (AC.PASH.A.{1,2}, AC.PASH.B.{1,2}, AC.PASH.C.{1,2}) + one outcome-altitude smoke (AC.PASH.S). Per Lens 5 EVAL_DIMENSIONS: three orthogonal axes (.A target-form / .B BASELINE selection / .C ordering+warning) + one aggregator judge (.S). | `loam-plan-author` subagent | F3 / Lens 5 swarming pattern |
| D-PASH.DOGFOOD | THIS amendment's own manifest carries `narrative.target: docs/plans/sealed/amendment-142-plan-author-skill-hygiene-merged.md` (the canonical Scope A form). THIS amendment's BASELINE is selected per Scope B's walk-forward discipline (the predecessor #141 has no `chore(amend-fixup):` commits between its seal `c144c2d` and publish-state `2686101`, so BASELINE is the publish-state `2686101` — the post-#141 standard convention). THIS amendment's source-edit commit lands BEFORE its apply (Scope C). The plan-doc dogfoods all three scopes at authoring time. | `loam-plan-author` subagent | Eat your own dog food — the new SKILL prescriptions get exercised by the build that introduces them |

**Rationale (Tier-0 verified at plan-authoring time, canonical HEAD `2686101683264a21f938a1dc1eca21f530ba9a67`):**

- **D-PASH.MERGE** — TG 11847 directly directs the queue-merge; the three FIDRAFT entries explicitly compose-with each other (FIDRAFT 336 names FIDRAFT 330 as a "sibling plan-author template gap; consolidate into one plan-author hardening amendment"). AC families are scope-disjoint; the dogfood discipline (D-PASH.DOGFOOD) exercises all three scopes at the same authoring-time, surfacing any merge-conflict risk at plan-time rather than build-time.

- **D-PASH.TARGET-DEFAULT** — empirically established by the convergence at canonical HEAD (4 of the 5 most recent sealed manifests use the canonical form; the 5th is the bug case #138). FIDRAFT 330's primary proposal ("patch the plan-author SKILL's manifest template to emit `narrative.target: docs/plans/sealed/<slug>.md` by default, matching the post-#134 T1.4 archive convention") is adopted verbatim.

- **D-PASH.BASELINE-WALK** — FIDRAFT 336's primary proposal adopted verbatim. The walk-forward is a *discipline* update (no code path change); the SKILL prose carries the prescription in the manifest-authoring step. Builder's call whether to extract a helper function (low priority; FIDRAFT 336 doesn't require it).

- **D-PASH.METHOD-DOC** — FIDRAFT 334's primary proposal adopted with the explicit "warning, not block" constraint preserved. The warning's reuse of `_diff_with_working_tree` (from `dry_run.py`) keeps the implementation small (~15-30 LOC including detection narrowing per D-PASH.WARN-PRECISION).

- **D-PASH.WARN-PRECISION** — F4 calibration: a fire-on-any-unstaged warning would become noise during routine mid-cycle edits where the operator HAS staged changes pending and IS about to apply intentionally. The precise form fires only on the failure mode FIDRAFT 334 actually names: "tracked-but-unstaged changes that should have been committed before apply." Outside-partition is the load-bearing predicate.

- **D-PASH.WARN-NON-BLOCKING** — the non-amend CDC (`feedback_no_amend_in_agent_dispatches`) keeps the operator in control of commits; the warning's role is to surface the discipline gap, not to enforce it. Per FIDRAFT 334's "possibly enforced via a pre-apply check that warns if working tree has unstaged changes" — the verb is "warns," not "blocks."

- **D-PASH.AC-LADDER** — Lens 5 EVAL_DIMENSIONS: three orthogonal mechanism axes + one outcome-altitude aggregator smoke. Mechanism-level ACs are grep-style for SKILL-prose presence (deterministic, fast, low-cost) + unit-tests for the helper + apply.py warning emission. Smoke is the end-to-end aggregator that verifies the three axes co-satisfied.

- **D-PASH.DOGFOOD** — eats own dog food at three levels: (a) manifest's `narrative.target` uses the canonical Scope A form; (b) BASELINE selection follows Scope B's walk-forward discipline; (c) the source-edit commit ladder follows Scope C's explicit ordering. Surfaces any prescriptive bug at the AMENDMENT THAT INTRODUCES THE FIX, not the next-amendment-that-tries-to-follow.

---

### Commit SHAs

- Amendment commit: TBD (populated by §14 backfill at seal time).
- Seal commit: TBD (populated by §14 backfill at seal time).

---

## §16. Halt-and-surface findings (raised + ruled at plan-authoring)

1. **The dispatch brief framed the three scopes as a single merged amendment per the queue-merge directive (TG 11847).** Tier-0 verification (FIDRAFT line 336 explicitly says "consolidate with F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP into a plan-author hardening pass"; the three entries name the same component surface; the AC families are scope-disjoint). **Ruling:** merge proceed; recorded as D-PASH.MERGE.

2. **The Scope A "manifest template" framing in the dispatch brief was slightly misleading — there is no machine-rendered manifest template in loam-amend.** Tier-0 verification: `loam amend new-plan` produces a plan-doc vars-file (not a manifest); manifests are hand-authored per the SKILL prose. **Ruling:** the patches land in the SKILL prose + convention docs (the surface agents actually read at authoring time), not in a non-existent template-render path. Recorded as the Scope A actual fence per §5.

3. **The dispatch brief mentioned "possibly add a pre-apply check that warns on unstaged changes" with low confidence.** Tier-0 read of `apply.py:158` confirms apply runs against committed HEAD; Tier-0 read of `dry_run.py:66-96` confirms the detection mechanism already exists in dry-run form. **Ruling:** the warning is in-scope per Scope C; reuse `_diff_with_working_tree` (or a narrower helper extracted from it) per D-PASH.WARN-PRECISION; warning emits to stderr, non-blocking per D-PASH.WARN-NON-BLOCKING. Recorded in §3 + §14.

4. **The Scope B "walk-forward" prescription could be implemented as a helper function OR as SKILL prose.** Tier-0 verification: no `select_baseline` helper exists at canonical HEAD; the `baseline.py` module is the per-component sidecar literal editor, unrelated. **Ruling:** SKILL-prose prescription is sufficient for the discipline; helper extraction is a Phase-2 optimization not required by FIDRAFT 336. Recorded as D-PASH.BASELINE-WALK rationale. Halt-trigger #3 in §6 covers the edge case where the builder finds an existing helper mid-flight.

5. **Pre-existing untracked plan-doc in working tree** — `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` (unrelated workstream, PENDING owner ratification). Admitted via `--allow-untracked-globs` at seal time per §5 universal admissions. Same admission as #140 §5 / #141 §5. **Ruling:** not this amendment's concern; admission is dirty-check-only.

6. **4 pre-existing loam-amend test failures on canonical HEAD `2686101`** (per #140 §16 #6 and #141 §16 #5) — `test_AC_DPS1_13`, `test_AC_DPS2_10`, `test_AC_D_1_5_4`, `test_AC_D_sa_6`, rooted in the oversized `smoke_outcome` field of `docs/plans/session-clear-safety-tracker-...manifest.yaml`. Tracked separately as `ws-loam-amend-oversized-manifest-field-cleanup`. **Ruling:** OUT OF SCOPE for this amendment; halt-trigger #7 in §6 distinguishes "new regression from this amendment's edits" (halt) from "pre-existing canonical-state failures unrelated" (capture + dispatcher ruling).

7. **Section-14 heading shape.** This plan-doc uses `## §14. Method-decision register` (canonical post-#136 shape with §-prefix + em-dash). #136's widened regex + #141's decoupled backfill make the auto-backfill work cleanly on this shape. **Ruling:** rely on the widened regex; halt-trigger #6 in §6 surfaces if the dogfood breaks.

8. **The dogfood discipline (D-PASH.DOGFOOD) requires THIS amendment's own manifest to use the Scope A canonical form BEFORE the Scope A fix lands on disk.** This is the eating-own-dog-food pattern: the plan-author SKILL prose patch ALSO lands the canonical form at the same time, so a fresh agent reading the post-seal SKILL set would converge on the same form. **Ruling:** the manifest authored alongside this plan-doc uses `narrative.target: docs/plans/sealed/amendment-142-plan-author-skill-hygiene-merged.md` (canonical Scope A form); the SKILL prose patches follow.

9. **Scope C's commit-ordering prescription dogfoods at THIS amendment's own build.** The source-edit commit (the actual `fix(dev-sdlc):` carrying the SKILL prose + apply.py edit) MUST land before `loam amend apply` per the prescription it introduces. This is enforced naturally by the commit-ladder discipline; halt-trigger #6 in §6 would fire if the builder forgets and the new soft-warning fires on this amendment's own apply invocation (which it shouldn't — the source-edit commit lands all the changes; nothing should be tracked-but-unstaged at apply time).

10. **FIDRAFT entry uses § token mixed with plain-text scope names.** Initial reading of the three FIDRAFTs (lines 330 / 334 / 336) confirms scope names are stable (F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP / F-LOAM-AMEND-APPLY-IMPLICIT-COMMITTED-HEAD-DEPENDENCY / F-BASELINE-SELECTION-VS-POST-SEAL-CORRECTIVE-FIXUPS). **Ruling:** plan-doc cites all three by canonical name in §2 + §17.

---

## §17. Composition (M5 derivation line)

- **Composes with** amendment #134 (FBM Tier 1, T1.4 archive-on-seal at `plan_archive.py`) — Scope A's canonical-form prescription matches the convention #134 established at the code level; this amendment closes the SKILL-prose gap.
- **Composes with** amendment #138 (dev-sdlc test directory cleanup, sealed at `01e63ac` + fixup `26f3a9e`) — the empirical trigger for Scope A AND Scope C. §138 §16 findings #1 + #3 directly proposed these scopes.
- **Composes with** amendment #139 (dev-sdlc manifest runtime flag, sealed at `1f3d8d7` + re-baseline `ca16e41`) — the empirical trigger for Scope B. §139 §16 finding #2 proposed Scope B.
- **Composes with** amendment #140 (seal-tool hygiene pair) — same queue-merge pattern (two scopes touching the same `_finalize` function merged into one cycle); this amendment mirrors the pattern with three scopes touching the same SKILL + methodology surface.
- **Composes with** amendment #141 (seal-tool §14 backfill decouple) — the post-#141 decoupled backfill is load-bearing for THIS amendment's own seal-time auto-backfill (per halt-trigger #6); if #141's decouple regresses, this amendment's seal would surface the regression.
- **Composes with** `feedback_locked_design_not_license_for_bad_outcomes` — the legacy `framework/<comp>/seals/SEAL_COMMIT.<slug>` shape is a locked design from pre-T1.4; operational outcome (orphan files when authoring agents converge on component-name shape) is bad enough to revisit + replace.
- **Composes with** `feedback_workaround_masks_rootcause_urgency` — three workarounds (`26f3a9e` orphan removal, `ca16e41` re-baseline, #138's manual re-commit after apply-halt) mask the same root cause: insufficient SKILL-prose prescription. Two-recurrence threshold met; this amendment IS the root-cause fix.
- **Composes with** `feedback_information_trust_ordering` — Tier-0 source-reads (apply.py:158 + dry_run.py:66-96 + all four SKILL files + both convention docs + manifest survey) are the basis for the D-PASH-* rationales; not Tier-2 inference from FIDRAFT text alone.
- **Composes with** F2 Ruthless Feedback — §10 surfaces every honest doubt (tooling-vs-prose tension, false-positive warning surface, three-scope merge risk, AC outcome-altitude vs grep-shape) rather than silently shipping.
- **Composes with** F3 / Lens 5 swarming — EVAL_DIMENSIONS named-axis judging applied at the AC family level (three orthogonal axes + one aggregator). The merge itself is swarming-aware decomposition.
- **Composes with** `feedback_record_owner_ratification_before_dispatch` — §1 owner-ratification record captures the three TG msg-IDs durably; plan-doc commits with the ratification table populated BEFORE the build dispatch.
- **Closes** `F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP` (FIDRAFT line 330), `F-LOAM-AMEND-APPLY-IMPLICIT-COMMITTED-HEAD-DEPENDENCY` (FIDRAFT line 334), and `F-BASELINE-SELECTION-VS-POST-SEAL-CORRECTIVE-FIXUPS` (FIDRAFT line 336) on seal.
- **Independent of** F4 — outcome shapes are well-pinned regardless of scope-confidence framing; F4 informed the merge call (high-confidence on outcome → tight scope authorising the merge) but doesn't derive the prescriptions themselves.

---

dev-sdlc: plan-author SKILL + dev-sdlc methodology hygiene
(merged three-scope amendment per TG 11847 queue-merge
directive). Closes F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP
(FIDRAFT line 330), F-LOAM-AMEND-APPLY-IMPLICIT-COMMITTED-HEAD-
DEPENDENCY (line 334), and F-BASELINE-SELECTION-VS-POST-SEAL-
CORRECTIVE-FIXUPS (line 336) on seal.

Scope A — `narrative.target` canonical form. Plan-author SKILLs
(plan-docs-author / plan-before-code-author / loam-amend-cycle /
seal-narrative-writer) + convention docs (plan-docs.md /
commit-ladder.md) prescribe `docs/plans/sealed/<slug>.md` as the
canonical default, matching the post-#134 T1.4 archive convention
and the empirical convergence at #137/#139/#140/#141. Replaces
the legacy `framework/<comp>/seals/SEAL_COMMIT.<slug>` shape and
prevents the component-name-only bug shape (#138's orphan file
`<repo>/dev-sdlc`, recovered via `26f3a9e`).

Scope B — BASELINE walk-forward from predecessor seal. SKILLs
prescribe: walk forward from predecessor seal commit; if any
`chore(amend-fixup):` commits exist between seal and HEAD, pick
the latest fixup as BASELINE; else the seal commit itself.
Discipline-only (no new tooling). Prevents the stale-BASELINE
pattern that forced #139's corrective re-baseline `ca16e41`.

Scope C — source-edit-commit-before-apply step. Convention docs
(commit-ladder.md / amendment-cycle.md) + loam-amend-cycle SKILL
explicitly name "commit source edits BEFORE `loam amend apply`"
as a step (apply runs against committed HEAD, verified at
apply.py:158). Plus a soft (non-blocking) stderr warning emitted
by `apply.run` when tracked-but-unstaged changes exist OUTSIDE the
partition's admitted union (the precise form per D-PASH.WARN-
PRECISION; reuses `_diff_with_working_tree` from dry_run.py).
Prevents the apply-against-uncommitted-edits halt #138's first
build attempt hit.

Shape (merged) chosen per D-PASH.MERGE: three scopes touch the
same `dev-sdlc` component + same SKILL + methodology surface;
AC families are scope-disjoint (.A / .B / .C); the dogfood
discipline (D-PASH.DOGFOOD) exercises all three scopes at the
amendment's own authoring + build time. Saves one apply + seal
cycle vs three sequential amendments.

Composes with amendment #134 (T1.4 archive convention; this
amendment closes the SKILL-prose gap), #138 (empirical trigger
for A + C — retires the manual `26f3a9e` orphan-removal and
manual re-commit workarounds per `feedback_workaround_masks_-
rootcause_urgency`), #139 (empirical trigger for B — retires
the manual `ca16e41` re-baseline workaround), #140 (queue-merge
precedent — same merge-multi-scope-into-one-cycle pattern),
#141 (post-#141 decoupled §14 backfill is load-bearing for this
amendment's own seal-time auto-backfill).

Closes F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP,
F-LOAM-AMEND-APPLY-IMPLICIT-COMMITTED-HEAD-DEPENDENCY, and
F-BASELINE-SELECTION-VS-POST-SEAL-CORRECTIVE-FIXUPS on seal.
