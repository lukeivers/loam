# STATE.md + release-roadmap.md narrow rollup — Active-Version flip + v0.12.x series rollup entry

> **Status:** sub-plan-doc (Batch B-NARROW — course-correction of the prior `state-md-release-roadmap-v012x-backfill` plan-author dispatch). Doc-only. Awaits builder dispatch.
> **Author:** loam-plan-author sub-agent, 2026-05-23.
> **Working directory:** `/Users/lukeivers/loam` (canonical loam, branch `pos-v2`).
> **Parent context:** consistency-review Batch B MAJOR finding at `pos3/workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md`. Dispatcher Option-2 ruling (narrow) replaces the prior plan-author's Option-B framing — the original `state-md-release-roadmap-v012x-backfill.md` (still in working tree, uncommitted) is REPLACED by this plan-doc.
> **Predecessors (load-bearing):**
> - Current canonical HEAD `6e0de79` — `docs(plans): record amendment #148 commit SHAs in method-decision register`.
> - Last seal landing in main `8fea4b9` — #148 BAFI-stale-test-retire (sidecar `plugins/loam-skills/tests/SEAL_COMMIT` = `65a8db3`; Tier-0 verified).
> - v0.12.0 SHIPPED PUBLIC 2026-05-18 (annotated tag `0d25d0a`; pushed `main` at `47c2725`).
> - v0.12.1..v0.12.21 = 21 lightweight tags between 2026-05-18 and now (Tier-0 verified via `git for-each-ref refs/tags/v0.12.*` + `git tag -l --format='%(contents:subject)'` for each).
> **BASELINE candidate:** `6e0de79` (current HEAD).
> **Status-file target:** `docs/STATE.md` + `docs/release-roadmap.md`.
> **Quality bar:** every post-fix claim Tier-0 verifiable against canonical git refs + the sealed plan-doc filenames the rollup entry cites; no SHA claim that the builder cannot resolve via `git rev-parse`.

---

## §1 Summary / TL;DR

**What ships (doc-only, two files).**

1. **STATE.md leading-title status sentence (line 3)** — flips the stale `currently #140 — loam-amend seal-tool hygiene pair` clause to a current claim naming the latest sealed amendment (#148 BAFI-stale-test-retire, seal `8fea4b9`) AND naming the currently-published version (v0.12.21). The two surrounding claims about earlier amendments stay; only the stale-141..148 + stale-version-position is corrected.
2. **release-roadmap.md §3 Active version (lines 100-102 + the v0.12.0 entry at line 162)** — adds a new v0.12.21 active-version entry naming v0.12.21 as the currently-published version. The v0.12.0 entry stays as historical anchor.
3. **STATE.md change-log gains ONE new rollup entry** prepended above the existing 2026-05-18 v0.12.0 entry (chronological-newest-first preserved). The rollup acknowledges the v0.12.1..v0.12.21 series as 21 README-current-release-bumps + amendment-cycle audit-trail tags — single rollup, NOT 21 individual entries. The rollup names the 4 in-arc amendment plan-docs (Batch A = `loam-doc-consistency-batch-a`, A-FIX = `loam-skills-ac-lsk1-root-cause`, A-PROMOTE = `loam-skills-start-project-discoverable`, BAFI-stale-test-retire = `loam-bafi-stale-test-retire`) by their sealed plan-doc filenames + cites those filenames + relevant tag-subject lines as the per-cycle audit surface. The rollup is honest about being a rollup: it says explicitly that per-cycle SHA-level provenance lives in the sealed plan-docs, not in this entry.

**AC families.** `AC.SRMNR.{1,2,3,4,S}` — five ACs scope-descriptive per `feedback_scope_descriptive_ac_ids` (SRMNR = State + Roadmap, Narrow Rollup). AC.SRMNR.4 outcome-altitude (per `feedback_test_outcome_altitude_required`).

**Key decisions baked.**

- **Option-2 (narrow) chosen by dispatcher** over the prior plan-author's Option-B. Doc-only fence; no CLI verb; no helper change; no per-tag entries.
- **Class PATCH** per `docs/release-versioning-policy.md` + `feedback_version_numbers_at_release_time` (doc-only state-record correction; no user-observable behaviour boundary; version itself derives at release time, not pre-assigned here).
- **No new test file authored** — the outcome-altitude AC is verified by a re-grep of the post-fix STATE.md + release-roadmap.md against ground truth (canonical git refs + sealed plan-doc filenames) rather than a new test file. Doc-only scope per dispatcher.
- **Rollup-not-per-tag entry shape** ratified per `feedback_asymmetric_problem_solving` — the v0.12.1..v0.12.21 series is overwhelmingly (17 of 21) README-current-release-bumps tracking amendment cycles, not independent semantic releases. A rollup is the high-leverage shape.

**F2 RF on scope realism.** Four named disagreements with dispatcher framing surfaced inline in §10 below:

- **F2-1.** The dispatcher's "STATE.md summary line that counts components / amendments" conflates two things — STATE.md's line 3 counts components ("All thirteen sealed components built") + cites the current amendment number; there is NO STATE.md count line for shipped versions. The version count lives in `release-roadmap.md:94`. Plan distinguishes the two.
- **F2-2.** STATE.md line 3 already cites amendment #140 — but #141, #142, #143, #144, #145, #146, #147, #148 have all sealed since. The "current amendment" claim is 8 amendments stale, not just "v0.12.21 stale". The flip needs to name the current amendment, not just the current version.
- **F2-3.** Of the 21 v0.12.x tags after v0.12.0, **17 are README-bump-tracking amendment cycles** (per Tier-0 `git tag -l --format='%(contents:subject)'` walk). The remaining 4 (v0.12.5/6 = api_version + BootstrapHostProtocol feat; v0.12.7 = persona-prompt translate-inbound discipline; v0.12.8 = end-of-turn trait-reflection feat; v0.12.9 = workspace-sync just-behind-canonical fast-path) ARE feature/fix work that arguably warrants individual entries. Plan-author recommendation: a single rollup entry that names those 4 distinguishably (one bullet each) within the rollup, vs. the other 17 acknowledged in aggregate — high leverage, honest provenance. If dispatcher disagrees, halt + revise.
- **F2-4.** Batch A (#145) and A-FIX (#146) sealed plan-docs exist in `docs/plans/sealed/` but their `chore(seals):` commits do not appear individually in the recent main-branch log (only A-PROMOTE = `389dac7` and BAFI-stale-test-retire = `8fea4b9` are visible). The `SEAL_COMMIT` sidecars HAVE advanced past those amendments (`loam-skills/tests/SEAL_COMMIT` = `65a8db3`), confirming the seals occurred; the seal commits were likely collapsed into A-PROMOTE/A-FIX successor commits or live on a non-main ref. The rollup entry MUST reference these by their sealed plan-doc filenames rather than seal SHAs (which the builder must NOT fabricate); if the builder finds a different load-bearing answer at Tier-0, halt + surface.

---

## §2 Placement decisions

Per the partition-rule decisions:

- **STATE.md leading-title status sentence** — placement: `docs/STATE.md` line 3 (the existing leading `**Status:**` paragraph). Rationale: this is the sentence read by every session-start corpus load + every fresh-install user; the stale-claim surface that the consistency review identified. Edit shape: surgical mutation of the existing sentence's stale clauses ONLY — do not rewrite the whole paragraph.
- **STATE.md change-log rollup entry** — placement: `docs/STATE.md`, prepended above the existing `2026-05-18` v0.12.0 entry at line 115 (chronological-newest-first preserved per the existing change-log convention). Dated `2026-05-23`. Rationale: this is the canonical placement for shipped-version-state records; the rollup is itself a shipped-state-summary entry.
- **release-roadmap.md §3 Active version v0.12.21 entry** — placement: `docs/release-roadmap.md`, appended after the existing v0.12.0 entry at line 162. Rationale: §3 is the per-MINOR-published bold-entry surface; v0.12.21 is the currently-published version and needs an Active-Version entry. v0.12.0 stays as historical anchor (matches the existing §3 pattern where v0.4.x / v0.5.x / v0.6.x / v0.7.x / v0.10.x all retain their entries as anchors).
- **release-roadmap.md §2 Shipped table** — placement: NOT TOUCHED in this amendment. The §2 table ends at v0.10.8; v0.10.9, v0.11.0, v0.12.0 are all missing as §2 rows. **This is a real gap but it is OUT OF SCOPE for the narrow Option-2 ruling** — adding §2 rows requires either the broken `apply_backfill` helper or from-scratch authoring, which the dispatcher explicitly deferred. Captured at §7 + FIDRAFT.
- **release-roadmap.md `Total shipped` summary line (line 94)** — placement: NOT TOUCHED in this amendment per the same out-of-scope ruling. The walker that maintains this line is part of `apply_backfill`, and Option-2 forbids touching that.
- **Sealed plan-doc references in the rollup entry** — placement: the change-log rollup entry cites the 4 in-arc sealed plan-docs by their `docs/plans/sealed/<slug>.md` paths. Rationale: these are the per-cycle audit-trail surface; the rollup is honest about being a rollup by pointing readers at them.

---

## §3 Halt-and-surface BEFORE build

Five decisions recorded autonomously at plan-authoring time (per `feedback_test_against_operational_objective_before_escalating` — the operational objective is "STATE.md + release-roadmap reflect current state" and implies a clear answer for each):

1. **Option-2 (narrow) chosen.** Dispatcher ruled explicitly; plan-author honours. No CLI verb; no helper change; doc-only fence. **Decision: Option-2.**
2. **Class PATCH.** Doc-only state-record correction; no user-observable behaviour boundary; version itself derives at release time. **Decision: PATCH.**
3. **Rollup entry shape ratified.** A single dated change-log entry summarising the v0.12.1..v0.12.21 series, with one bullet per "real feature/fix" tag (v0.12.5/6, v0.12.7, v0.12.8, v0.12.9 — see F2-3) and one aggregated bullet for the 17 README-bump-tracking tags, plus 4 sealed-plan-doc references for the in-arc amendment audit trail. **Decision: rollup-with-honest-distinguishing.** If dispatcher prefers a fully-aggregated rollup (zero per-tag bullets) OR a fully-individual-entry shape, halt + revise.
4. **`SEAL_COMMIT` sidecar walk used as Tier-0 evidence** that #145 and #146 sealed despite missing visible `chore(seals)` commits in the recent main log (F2-4). Rollup entry cites the sealed plan-doc filenames, NOT fabricated seal SHAs. **Decision: cite plan-doc paths.** If builder cannot resolve a plan-doc path to a real file, halt + surface.
5. **§2 Shipped table + Total-shipped count line OUT OF SCOPE** per dispatcher's explicit "doc-only" ruling — both surfaces are downstream of the `apply_backfill` helper's machinery. **Decision: defer to F-STATE-FROMSCRATCH-AUTHOR.** Captured in §7 + FIDRAFT capture is a separate dispatcher-side step per dispatcher's note.

**The following conditions during build trigger HALT + dispatcher escalation:**

- **HALT-A.** The STATE.md line-3 sentence has changed structurally since plan-authoring (e.g., the leading `**Status:**` block was reformatted by a passing amendment). Surface; do not silently restructure.
- **HALT-B.** The release-roadmap.md §3 v0.12.0 entry has been touched since plan-authoring (entry text differs from the verified line-162 content). Surface; do not silently overwrite.
- **HALT-C.** A sealed plan-doc the rollup entry references does NOT exist at the expected `docs/plans/sealed/<slug>.md` path. Verify Tier-0 via `ls`; surface the missing path; do not invent.
- **HALT-D.** Any of the 21 v0.12.x tags' underlying commits are not resolvable via `git rev-parse v0.12.<N>` (one of the lightweight tags has been deleted or rewritten). Surface the resolution failure; do not invent SHAs.
- **HALT-E.** The dispatcher's "the current STATE.md summary line is already accurate (no recount needed)" halt-trigger fires — i.e., upon Tier-0 read the STATE.md sentence is already current and no flip is needed. Plan-author verified at plan-authoring that line 3 explicitly cites `currently #140`, so this halt should NOT fire; if it does, the plan-author's verification was wrong and the dispatcher needs to know.
- **HALT-F.** A subset of the 21 tags turns out (on closer reading) to represent independent semantic releases that DO warrant individual change-log entries beyond the 4 the plan-author identified (F2-3). Surface; do not silently expand.
- **HALT-G.** The rollup entry's intended shape conflicts with another established convention the builder discovers (e.g., a rule in `docs/conventions/` saying every published tag must have its own change-log entry). Surface; do not silently override.

---

## §4 Spec-objective placement

This work binds to **AC.PO.1** (translation-burden reduction: a session-start corpus load + a fresh-install user reading STATE.md sees current state, not 8-amendments-stale + 21-tags-stale state). The bind is direct: the leading status sentence + release-roadmap §3 are the first surfaces a new session reads, and stale claims at those surfaces propagate misinformation into every dispatch. AC.PO.2 (toolkit extension) is NOT in scope for this narrow amendment — toolkit extension lives in the deferred F-LOAM-RELEASE-BACKFILL-TAG-CLI-VERB work.

The bind ladders up to the prime objective in `docs/VALUE_PROPOSITION.md` per `feedback_value_proposition_as_prime_objective`.

---

## §5 Acceptance criteria

Five ACs, scope-descriptive (AC family `SRMNR` for State + Roadmap, Narrow Rollup):

| ID | Outcome | Verification | Outcome-altitude |
|---|---|---|---|
| **AC.SRMNR.1** | `docs/STATE.md` line 3's leading-title `**Status:**` sentence cites the currently-sealed-and-recorded amendment (#148 BAFI-stale-test-retire) AND the currently-published version (v0.12.21). The stale `currently #140 — loam-amend seal-tool hygiene pair` clause is updated to name #148. Other clauses in the paragraph (component count "All thirteen sealed components built", earlier amendment cycle history, OSS publish history, v0.1.6 SHIPPED claim) stay byte-identical — surgical edit only. | Deterministic check: `grep -E 'currently #148\|v0\.12\.21' docs/STATE.md` returns line 3 match; pre-existing line-3 substrings (`All thirteen sealed components built`, `OSS publish (loam v0.1.0)`, `v0.1.6 SHIPPED`) are preserved unchanged (grep for each). | No |
| **AC.SRMNR.2** | `docs/release-roadmap.md` §3 Active version section gains exactly one new bold entry naming v0.12.21 as the currently-published version (date, tag, underlying commit SHA, brief one-sentence framing). The v0.12.0 entry at line 162 is retained byte-identically as historical anchor. No other §3 entries are added or removed. | Deterministic check: §3 contains a new `**v0.12.21 ... SHIPPED PUBLIC 2026-05-2X**` bold entry; the existing `**v0.12.0 MINOR ... SHIPPED PUBLIC 2026-05-18**` entry text is preserved verbatim; no entries for v0.12.1..v0.12.20 added. | No |
| **AC.SRMNR.3** | `docs/STATE.md` change-log section gains exactly one new dated entry (`**2026-05-2X**`) prepended above the existing `**2026-05-18** — **v0.12.0 SHIPPED PUBLIC**` entry at line 115. The entry: (a) acknowledges the v0.12.1..v0.12.21 series as 21 tags (17 README-current-release-bumps tracking amendment cycles + 4 distinguishable feature/fix tags); (b) names the 4 distinguishable tags individually with one-line each (v0.12.5/6 = workspace-bootstrap api_version + BootstrapHostProtocol; v0.12.7 = persona-prompt translate-inbound + explicit-slash-invocation discipline; v0.12.8 = primary-persona end-of-turn trait-reflection Stop-hook; v0.12.9 = workspace-sync just-behind-canonical fast-path); (c) cites the 4 in-arc sealed plan-docs by their `docs/plans/sealed/<slug>.md` paths (`loam-doc-consistency-batch-a.md`, `loam-skills-ac-lsk1-root-cause.md`, `loam-skills-start-project-discoverable.md`, `loam-bafi-stale-test-retire.md`); (d) states explicitly that per-cycle SHA-level provenance lives in the cited sealed plan-docs; (e) names the currently-published version as v0.12.21 with its underlying commit SHA. | Deterministic check: STATE.md change-log contains a new `**2026-05-2X**` entry that grep-matches each of the 4 sealed plan-doc filenames; entry includes the substring `21 tags` AND `rollup` (or equivalent honesty marker); entry cites v0.12.21 + the underlying commit SHA-7 for tag v0.12.21 (resolvable via `git rev-parse v0.12.21`). | No |
| **AC.SRMNR.4** | **OUTCOME-ALTITUDE.** A fresh shell with no pre-arranged state reads the post-fix `docs/STATE.md` + `docs/release-roadmap.md` at sealed-tip and the following claims hold against canonical git refs as ground truth: (a) every v0.12.x tag named in the rollup resolves to a real commit (`git rev-parse v0.12.<N>`); (b) every sealed-plan-doc path cited in the rollup exists at the expected path on disk; (c) the STATE.md line-3 amendment claim matches the actual latest sealed amendment per the SEAL_COMMIT sidecar walk (`cat plugins/loam-skills/tests/SEAL_COMMIT` resolves to a commit whose subject names the same amendment-N# OR plan-slug as line 3); (d) the release-roadmap §3 v0.12.21 entry's tag-SHA cite matches `git rev-parse v0.12.21`. The verification runs against canonical loam at the sealed-tip state — no fixture, no mock, no pre-arranged file. Failure of any of (a)-(d) is a RED outcome-altitude verdict. | Verification documented at `docs/experiments/state-md-release-roadmap-narrow-rollup-smoke.md` — a markdown file the builder authors at build-time recording the four checks + their pass/fail verdict + the canonical commands used. Each check is a one-liner shell command; the doc records the output. Per `feedback_test_outcome_altitude_required`, this is outcome-altitude verification by an audit-doc-against-canonical pattern rather than a pytest file, because the AC is a doc-content-vs-canonical-git claim, not a code claim. | **YES** |
| **AC.SRMNR.S** | Seal-diff allow-list. The amendment's seal-diff window touches ONLY: `docs/STATE.md`, `docs/release-roadmap.md`, `docs/plans/state-md-release-roadmap-narrow-rollup.md` (this plan-doc), `docs/plans/state-md-release-roadmap-narrow-rollup.manifest.yaml` (manifest), `docs/experiments/state-md-release-roadmap-narrow-rollup-smoke.md` (the AC.SRMNR.4 verification record). NO other files. NO source code touched. NO sealed plan-doc touched. The fence is enforced by the dev-sdlc seal-test against the BASELINE..SEAL window. | Seal-test GREEN post-seal. The fence is structurally tight: a `git diff BASELINE..SEAL --name-only` returns exactly the five files named above (plus the `loam amend` machinery's own commit artefacts, which are tool-emitted, not seal-diff-counted). | No |

**Method-in-AC test passed.** Each AC's outcome can be satisfied by a method other than the one the plan-author has in mind:

- AC.SRMNR.1's leading-title flip can be done via `sed`, manual edit, or any text tool;
- AC.SRMNR.2's §3 entry insertion can use any text-edit method;
- AC.SRMNR.3's rollup entry text can be composed in any prose shape so long as the deterministic-check fields are present;
- AC.SRMNR.4's verification can use any commands so long as the four ground-truth checks are recorded;
- AC.SRMNR.S's fence is enforced structurally.

None of the ACs lock the implementation to a specific code shape. **Per `feedback_odd_no_non_objective_code`.**

---

## §6 Build steps

Per-cycle method-level guidance (builder's call per ODD §1.1 — no file-level prescription):

### A. Pre-build verification (≤5 min)

1. Tier-0 re-verify the plan-author's claims:
   - `git rev-parse HEAD` returns `6e0de79` (BASELINE).
   - `git log --oneline -1 plugins/loam-skills/tests/SEAL_COMMIT` resolves to the latest sidecar-bumping commit (confirms the latest sealed amendment).
   - `grep -n 'currently #' docs/STATE.md` line 3 returns the stale `currently #140` clause.
   - `grep -n 'v0.12.0' docs/release-roadmap.md | head -3` confirms the v0.12.0 entry at line 162.
   - `git for-each-ref 'refs/tags/v0.12.*' --format='%(refname:short) %(objecttype)' | sort -V` returns 22 tags (v0.12.0 = `tag` annotated; v0.12.1..v0.12.21 = `commit` lightweight).
   - `git tag -l --format='%(contents:subject)' v0.12.<N>` for each N in {5,6,7,8,9} returns the feature/fix subjects the plan-author classified as distinguishable.
2. If any Tier-0 re-verification fails, HALT and surface to dispatcher.

### B. Author the three doc edits

1. **B1.** Edit `docs/STATE.md` line 3: surgically update the stale clauses naming amendment #140 + the omitted v0.12.21. Preserve all other prose in the paragraph byte-identically. Suggested shape (builder's call on exact wording):
   - Replace `currently #140 — loam-amend seal-tool hygiene pair, sealed 2026-05-21 at \`8a41e7b\` with §14 backfill \`381645b\`` (or its current form) with `currently #148 — loam-bafi-stale-test-retire, sealed at \`8fea4b9\` with apply \`65a8db3\` (closes the stale `start-project`-absence assertion left over from Batch A by A-PROMOTE's restoration)`.
   - Add (or insert near the version-state clauses) a clause naming `v0.12.21 currently published` with date + tag cite.
2. **B2.** Edit `docs/release-roadmap.md` §3 (after line 162): append a new bold entry for v0.12.21. Suggested shape (builder's call): `**v0.12.21 PATCH (current-release line bumped via README; rollup of the v0.12.1..v0.12.21 series tracking the amendment-#141..#148 cycle audit trail) SHIPPED PUBLIC 2026-05-<date-from-tag>** (tag \`v0.12.21\`, underlying commit \`1d40311\` from \`git rev-parse v0.12.21\`; per-cycle provenance lives in the cited sealed plan-docs in the STATE.md rollup entry).`
3. **B3.** Edit `docs/STATE.md` change-log: prepend a new dated entry above line 115. Suggested shape (builder's call):
   ```
   - **2026-05-2X** — **v0.12.1 → v0.12.21 series ROLLUP — 21 tags spanning the post-v0.12.0 amendment cycle audit trail.** This entry summarises the v0.12.1..v0.12.21 git tags (lightweight) as a single rollup; per-tag SHA-level provenance lives in the per-amendment sealed plan-docs cited below, not in this entry. The series breaks into 17 README-current-release-bumps tracking amendment cycles + 4 distinguishable feature/fix tags:
       - **v0.12.5 / v0.12.6** — workspace-bootstrap F7-PLUGIN-VERSION: `api_version` field + `BootstrapHostProtocol` (tag annotations: see `git tag -l --format='%(contents:subject)' v0.12.5 v0.12.6`).
       - **v0.12.7** — persona-prompt: translate-inbound + explicit-slash-invocation discipline stanza.
       - **v0.12.8** — primary-persona: end-of-turn trait-reflection Stop-hook contributor (AC.EOTTR.1-5).
       - **v0.12.9** — workspace-sync: A.1 just-behind-canonical fast-path (AC.JBC.1-4).
     Remaining 17 tags (v0.12.1, v0.12.2, v0.12.3, v0.12.4, v0.12.10, v0.12.11, v0.12.12, v0.12.13, v0.12.14, v0.12.15, v0.12.16, v0.12.17, v0.12.18, v0.12.19, v0.12.20, v0.12.21) are docs/README-bump commits tracking amendment cycles #137 through #148; their tag-subject lines (`git tag -l --format='%(contents:subject)' v0.12.<N>`) are the audit surface. **Sealed plan-docs for the in-arc amendments tracked by this series:** `docs/plans/sealed/loam-doc-consistency-batch-a.md` (amendment #145, Batch A), `docs/plans/sealed/loam-skills-ac-lsk1-root-cause.md` (amendment #146, A-FIX), `docs/plans/sealed/loam-skills-start-project-discoverable.md` (amendment #147, A-PROMOTE-START-PROJECT, seal `389dac7`), `docs/plans/sealed/loam-bafi-stale-test-retire.md` (amendment #148, BAFI-stale-test-retire, seal `8fea4b9`). Currently-published version: **v0.12.21** (underlying commit `1d40311`). **Out-of-scope deferred** (captured as FIDRAFT entries F-STATE-FROMSCRATCH-AUTHOR + F-LOAM-RELEASE-BACKFILL-TAG-CLI-VERB by the dispatcher post-seal): release-roadmap.md §2 Shipped table v0.10.9 / v0.11.0 / v0.12.0..v0.12.21 row authoring; `Total shipped` summary line recount; new `loam release backfill-tag` CLI verb composing an extended `apply_backfill` from-scratch row-authoring helper. Honest framing: §2 + count-line remain stale at v0.10.8 after this amendment; the rollup closes the STATE.md change-log + §3 Active Version surfaces only.
   ```
   The exact prose is the builder's call; the deterministic-check substrings in AC.SRMNR.3's verification column must all be present.
4. **B4.** Author `docs/experiments/state-md-release-roadmap-narrow-rollup-smoke.md` as a four-check verification record (AC.SRMNR.4):
   - Check 1: every v0.12.x tag resolves — `for tag in v0.12.{0..21}; do git rev-parse $tag; done` — record output.
   - Check 2: every sealed-plan-doc path exists — `ls docs/plans/sealed/loam-doc-consistency-batch-a.md docs/plans/sealed/loam-skills-ac-lsk1-root-cause.md docs/plans/sealed/loam-skills-start-project-discoverable.md docs/plans/sealed/loam-bafi-stale-test-retire.md` — record output.
   - Check 3: STATE.md line 3 amendment claim matches SEAL_COMMIT sidecar walk — verbatim commands + outputs.
   - Check 4: release-roadmap §3 v0.12.21 entry tag-SHA matches `git rev-parse v0.12.21` — verbatim commands + outputs.

### C. Apply + seal

1. **C1.** `loam amend apply docs/plans/state-md-release-roadmap-narrow-rollup.manifest.yaml`.
2. **C2.** `loam amend seal --plan-doc docs/plans/state-md-release-roadmap-narrow-rollup.md --allow-untracked-globs 'docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md' docs/plans/state-md-release-roadmap-narrow-rollup.manifest.yaml` per `feedback_dispatch_explicit_loam_amend_apply` (the `--allow-untracked-globs` covers the pre-existing untracked plan-doc per the dispatcher's note). The dispatcher MAY also need to admit the previously-uncommitted `state-md-release-roadmap-v012x-backfill.md`/`.yaml` (the superseded plan-doc + manifest) at seal-time — surface for dispatcher ruling on whether to delete those (recommended — they are superseded by this plan-doc) before seal, OR include them in `--allow-untracked-globs`.
3. **C3.** Post-seal smoke: re-run the four AC.SRMNR.4 checks against the sealed-tip state — all four must pass.

---

## §7 Out of scope

Explicitly deferred (NOT in this amendment):

1. **`release-roadmap.md` §2 Shipped table backfill** — the table ends at v0.10.8; v0.10.9, v0.11.0, v0.12.0, v0.12.1..v0.12.21 are all missing as §2 rows. This is a real gap. Deferred to the **F-STATE-FROMSCRATCH-AUTHOR** future amendment (which would extend the `apply_backfill` helper to author rows from scratch + then run the helper against each pushed tag).
2. **`release-roadmap.md` `Total shipped` summary line (line 94) recount.** Same deferral — the walker that maintains this line is part of `apply_backfill`'s machinery.
3. **STATE.md change-log per-cycle entries for amendments #141, #142, #143, #144, #145, #146, #147, #148.** The rollup entry references the sealed plan-docs for the in-arc amendments (#145-148); the v0.12.1..v0.12.4 + v0.12.10..v0.12.20 README-bump tags are acknowledged in aggregate. If per-cycle entries are wanted later, they would land in a future amendment (likely the same F-STATE-FROMSCRATCH-AUTHOR cycle, or a separate per-amendment-backfill cycle).
4. **`loam release backfill-tag <version>` CLI verb.** Deferred to **F-LOAM-RELEASE-BACKFILL-TAG-CLI-VERB** future amendment. The CLI verb is the reusable recovery surface for any future pushed-but-not-backfilled tag; it depends on F-STATE-FROMSCRATCH-AUTHOR landing first (the verb needs the helper to be able to author from scratch).
5. **`apply_backfill` helper extension to author rows from scratch.** Same as F-STATE-FROMSCRATCH-AUTHOR; the present narrow amendment does not touch helper code per dispatcher's explicit ruling.
6. **Sealed plan-doc updates.** No sealed plan-doc is touched by this amendment. If the builder discovers a sealed plan-doc references stale STATE.md state in a load-bearing way, HALT.
7. **The previous superseded plan-doc + manifest at `docs/plans/state-md-release-roadmap-v012x-backfill.{md,manifest.yaml}`.** Plan-author recommends the dispatcher delete those before seal (they're superseded by this plan-doc and live uncommitted in working tree). If the dispatcher prefers to keep them as a historical artefact, surface for ruling — they would need `--allow-untracked-globs` admission OR a separate commit deleting them.

**FIDRAFT capture (dispatcher-side, post-seal).** Plan-author recommends the dispatcher captures these two future-work concerns to `docs/FUTURE_IDEAS_DRAFT.md` as a separate dispatch-side step (this plan-doc does not write to FIDRAFT to keep the seal-diff clean):

- **F-STATE-FROMSCRATCH-AUTHOR** — the `apply_backfill` helper needs a from-scratch row-authoring extension. Currently `apply_backfill` only FLIPS pre-existing SHIPPED-LOCAL rows; v0.10.9 / v0.11.0 / v0.12.x are missing rows entirely. The helper extension would synthesise a §2 row from (version, tag, commit, objective-sentence) inputs derivable from the tag's annotation + sealed plan-doc lookup. This is a real defect blocking the §2 table from ever auto-converging. Future amendment.
- **F-LOAM-RELEASE-BACKFILL-TAG-CLI-VERB** — once F-STATE-FROMSCRATCH-AUTHOR lands, a `loam release backfill-tag <version>` CLI verb composes the extended `apply_backfill` against an already-pushed tag's resolved SHA. The verb is the recovery surface for any pushed-but-not-backfilled tag (regardless of whether it was created by the runner or by `git tag` directly). Useful for the present v0.12.x situation + any future analogous staleness. Future amendment.

---

## §8 Halt triggers (in-flight)

See §3 HALT-A through HALT-G. The builder halts and surfaces on any of those + on:

- **HALT-H.** The seal-test fails post-seal because some file outside the AC.SRMNR.S allow-list shows up in the seal-diff. Diagnose; surface; do not silently widen the fence.
- **HALT-I.** `loam amend apply` rejects the manifest's universal-paths shape (e.g., the tool requires per-component fences). Surface; fall back to the dispatcher-suggested fence shape (the `loam-bafi-stale-test-retire.manifest.yaml` precedent uses single-component fence + universal-paths admission).
- **HALT-J.** The dispatcher's previous superseded plan-doc (`state-md-release-roadmap-v012x-backfill.{md,manifest.yaml}`) cannot be cleanly deleted-or-admitted (e.g., git index lock contention). Surface; do not silently re-include in the seal.

---

## §9 Bookkeeping

Per the standard amendment-cycle bookkeeping:

1. **STATE.md** — this amendment's seal entry lands in STATE.md change-log via the rollup entry itself (AC.SRMNR.3 is both the user-facing fix AND the self-bookkeeping entry; this is a self-referential amendment by design — the closing line of the rollup entry should note "this entry itself records the seal of the present amendment").
2. **release-roadmap.md** — this amendment is a PATCH; no §2 row is authored here (per the out-of-scope ruling). The amendment will surface in §2 once F-STATE-FROMSCRATCH-AUTHOR lands and a backfill pass runs over the v0.12.x series.
3. **§14 method-decision register** — backfilled at seal time by `loam amend seal --plan-doc`. The D-SRMNR.* IDs are declared in this plan-doc; the build-time SHA fields populate post-seal.
4. **§16 halt-and-surface findings** — populated as the build proceeds; HALT-A..HALT-J from §3+§8 are the templates.
5. **FIDRAFT capture (F-STATE-FROMSCRATCH-AUTHOR + F-LOAM-RELEASE-BACKFILL-TAG-CLI-VERB)** — dispatcher-side post-seal capture per §7; this plan-doc does not write to FIDRAFT to preserve seal-diff narrowness.

---

## §10 F2 Ruthless Feedback (honest doubts; design risks named explicitly)

Per `feedback_ruthless_feedback` — four named disagreements with dispatcher framing + evidence + alternative:

### F2-1. The dispatcher's "STATE.md summary line that counts components / amendments" conflates two distinct surfaces.

- **Claim:** dispatcher framed item 2 as "STATE.md's summary line at the top (the line that counts components / amendments / etc.) needs the current accurate count".
- **Evidence:** Tier-0 read of STATE.md line 3 returns a `**Status:**` paragraph that (a) counts components (`All thirteen sealed components built`), (b) cites the current amendment (`currently #140 — loam-amend seal-tool hygiene pair`), (c) references historical published versions in passing (`v0.1.6 SHIPPED 2026-05-04`). There is NO "Total shipped" count line in STATE.md. The `Total shipped` line lives in `docs/release-roadmap.md:94` and is downstream of the `_count_published_versions` walker in `post_publish_backfill.py`.
- **Alternative:** the narrow flip scope is **STATE.md line 3's amendment claim** (citing #140 → #148) and **release-roadmap.md §3 Active Version** (v0.12.0 → v0.12.21). The `Total shipped` line at `release-roadmap.md:94` is OUT OF SCOPE per dispatcher Option-2 because updating it requires either touching the walker or doing manual arithmetic against an incomplete §2 table that itself needs F-STATE-FROMSCRATCH-AUTHOR. Plan reflects this scope split.

### F2-2. STATE.md line 3's current-amendment claim is 8 amendments stale, not just version-stale.

- **Claim:** dispatcher said "Flip the Active-Version line. Update STATE.md's leading-title-date-version and release-roadmap.md's §3 Active-Version to reflect v0.12.21".
- **Evidence:** STATE.md line 3 explicitly says `currently #140 — loam-amend seal-tool hygiene pair, sealed 2026-05-21 at \`8a41e7b\``. The latest sealed amendment per the SEAL_COMMIT sidecar walk (`cat plugins/loam-skills/tests/SEAL_COMMIT` = `65a8db3`, which is amendment #148 BAFI-stale-test-retire's apply commit) is #148. So the "current amendment" claim is 8 amendments stale (#141, #142, #143, #144, #145, #146, #147, #148). Just flipping the version cite leaves the amendment cite stale.
- **Alternative:** AC.SRMNR.1 names both the amendment flip AND the version flip; the plan's STATE.md edit corrects both. If the dispatcher prefers to leave the amendment cite for a separate flip, halt + revise.

### F2-3. The 21 v0.12.x tags split 17/4: README-bumps vs distinguishable feature work.

- **Claim:** dispatcher said "**17 of the 21 v0.12.x tags are `docs(readme): bump current-release line to v0.12.<N>`** — single-line README-version-bumps tracking amendment-#X cycles, not independent semantic releases. Treating each as a full §2 entry with full provenance is overweight."
- **Evidence:** Tier-0 `git tag -l --format='%(contents:subject)' v0.12.<N>` for N in {0..21} returned: v0.12.0 = MINOR (session-/clear safety + sealed measurement/loop FBM bundle); v0.12.1 = install-from-source fix; v0.12.2/3/4 = SKILL description quoting / revert / broaden; v0.12.5/6 = workspace-bootstrap F7-PLUGIN-VERSION feat; v0.12.7 = persona-prompt translate-inbound discipline; v0.12.8 = primary-persona end-of-turn trait-reflection Stop-hook feat; v0.12.9 = workspace-sync just-behind-canonical fast-path feat; v0.12.10 = odd-extractor-tests skip; v0.12.11..v0.12.21 = `docs/README` bumps tracking amendment cycles (11 of the 17 the dispatcher counted). Plan-author confirms the 17/4 split, with the 4 distinguishable being v0.12.5/6 (counted together as one feat), v0.12.7, v0.12.8, v0.12.9 — and adds v0.12.1, v0.12.2, v0.12.3, v0.12.4, v0.12.10 to the "small-fix" aggregated group rather than the distinguishable group (per their narrow scope).
- **Alternative:** the rollup entry distinguishes the 4 feat-class tags with one bullet each (AC.SRMNR.3), names the 17 (or 17+small-fixes = 17) other tags in aggregate. This is the rollup-not-individual shape per `feedback_asymmetric_problem_solving` — high-leverage rollup with honest distinguishing of the work that actually matters.

### F2-4. Batch A (#145) and A-FIX (#146) seal SHAs are not visible in recent main-log; cite by plan-doc path not by fabricated SHA.

- **Claim:** the rollup entry should cite each in-arc amendment by its sealed plan-doc path AND optionally its seal SHA.
- **Evidence:** Tier-0 `git log --oneline -300 | grep -iE 'amendment #14[5-6]'` returns ZERO matches on the main branch. `git log --all --oneline --grep='amendment #145'` returns ZERO matches across all refs. The sealed plan-docs DO exist at `docs/plans/sealed/loam-doc-consistency-batch-a.md` (#145) and `docs/plans/sealed/loam-skills-ac-lsk1-root-cause.md` (#146); references inside those plan-docs name commits like `2e3cfbf` (Batch A apply) but no `chore(seals)` commit for them is visible. The SEAL_COMMIT sidecars HAVE advanced past these amendments, confirming seals occurred — but the seal commits were likely collapsed into or rebased through the A-PROMOTE/#147 history. Fabricating SHAs into the rollup entry would violate `feedback_claim_or_cite_no_fake_sources` + `feedback_specific_claims_verified_or_marked_guess`.
- **Alternative:** AC.SRMNR.3 requires the rollup entry to cite the 4 sealed plan-docs by their `docs/plans/sealed/<slug>.md` paths (Tier-0 verifiable via `ls`). Seal SHAs are cited ONLY for A-PROMOTE (`389dac7`) and BAFI-stale-test-retire (`8fea4b9`) where they are Tier-0-verifiable in `git log`. For Batch A and A-FIX, the cite is plan-doc-path-only; the rollup entry is honest about this asymmetry (or omits SHA fields uniformly across all 4 if asymmetry would confuse readers — builder's call). If the builder finds the Batch A / A-FIX seal SHAs at Tier-0 via a deeper search, they may be included; if not, plan-doc-path-only.

---

## §11 Provenance trail

Every load-bearing source cited:

- **Parent context:** `pos3/workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md` (the Batch B MAJOR finding originating the dispatch).
- **Dispatcher Option-2 ruling:** the dispatch brief itself (course-correction over the prior `state-md-release-roadmap-v012x-backfill.md` plan-author's Option-B framing).
- **Tag landscape:** `git for-each-ref 'refs/tags/v0.12.*' --format='%(refname:short) %(objecttype)' | sort -V` executed 2026-05-23 at canonical HEAD `6e0de79` (22 tags total: v0.12.0 = annotated; v0.12.1..v0.12.21 = lightweight).
- **Per-tag subject lines:** `git tag -l --format='%(contents:subject)' v0.12.<N>` for each N in {0..21} executed 2026-05-23.
- **Current canonical state:** `docs/STATE.md` HEAD (190 lines; leading-title `**Status:**` paragraph at line 3 cites stale `currently #140`; change-log last entry `2026-05-18` v0.12.0 SHIPPED PUBLIC at line 115). `docs/release-roadmap.md` HEAD (505 lines; §2 table ends at v0.10.8; `Total shipped` line at line 94; §3 Active Version ends with v0.12.0 entry at line 162).
- **SEAL_COMMIT sidecars:** `cat plugins/loam-skills/tests/SEAL_COMMIT` = `65a8db3` (#148 apply); `cat plugins/dev-sdlc/tests/SEAL_COMMIT` = `25308cf` — Tier-0 verified.
- **Sealed plan-docs for in-arc amendments:** all 4 verified present at `docs/plans/sealed/` (`loam-doc-consistency-batch-a.md` + `loam-skills-ac-lsk1-root-cause.md` + `loam-skills-start-project-discoverable.md` + `loam-bafi-stale-test-retire.md`).
- **Convention authority:** `plugins/dev-sdlc/docs/conventions/plan-docs.md` (plan-doc shape) + `feedback_scope_descriptive_ac_ids` (AC IDs) + `feedback_test_outcome_altitude_required` (outcome-altitude AC) + `feedback_version_numbers_at_release_time` (class PATCH derives at release) + `feedback_asymmetric_problem_solving` (rollup-not-individual) + `feedback_claim_or_cite_no_fake_sources` + `feedback_specific_claims_verified_or_marked_guess` (F2-4 honesty discipline) + `feedback_dispatch_explicit_loam_amend_apply` (seal command shape).
- **Precedent manifests:** `docs/plans/sealed/loam-bafi-stale-test-retire.manifest.yaml` (recent single-component fence + universal-paths admission shape; this amendment follows the same pattern with dev-sdlc as anchor since loam-skills is not touched).
- **Predecessor superseded plan-doc:** `docs/plans/state-md-release-roadmap-v012x-backfill.md` + manifest (uncommitted in working tree; superseded by this plan-doc; dispatcher-recommended deletion before seal per §7 item 7).

---

## §14 Method-decision register (populated at build-time)

Placeholder structure for the D-SRMNR.* + D-build.* IDs:

- **D-SRMNR.1** — Option-2 (narrow) chosen over the prior plan-author's Option-B. Rationale: dispatcher explicit ruling. Owner-ratified.
- **D-SRMNR.2** — Class PATCH (D-STBF.1's analogue). Rationale: doc-only state-record correction; no user-observable behaviour boundary; version derives at release time. Plan-author-autonomous per `feedback_strict_autonomy_no_pause_for_authorized_work`.
- **D-SRMNR.3** — Rollup shape: single dated entry + 4 per-feat-tag bullets + aggregated-17 bullet + 4 sealed-plan-doc citations. Plan-author-autonomous per `feedback_asymmetric_problem_solving`. Halt-and-revise if dispatcher prefers different shape.
- **D-SRMNR.4** — SEAL_COMMIT sidecar walk used as Tier-0 evidence for latest-sealed-amendment claim (per F2-4). Plan-author-autonomous per `feedback_information_trust_ordering`.
- **D-SRMNR.5** — Plan-doc-path-only citations for Batch A (#145) + A-FIX (#146) in the rollup entry (no fabricated seal SHAs). Per `feedback_claim_or_cite_no_fake_sources`. Builder may upgrade to SHA citations if Tier-0 lookup succeeds; otherwise honest plan-doc-path.
- **D-SRMNR.6** — Out-of-scope deferrals named explicitly in the rollup entry's closing paragraph + captured at FIDRAFT post-seal (dispatcher-side step). Per `feedback_durable_capture_for_planned_work`.
- **D-build.SHA** — BASELINE / source-edit / apply / seal SHAs backfilled by `loam amend seal --plan-doc`.

---

## §15 Backwards-compat verification

Tests that MUST still pass post-seal:

- Full dev-sdlc seal-test (the component anchor for the fence) — GREEN post-seal proves the structural fence held.
- No other tests touched; the amendment is doc-only.
- The four AC.SRMNR.4 outcome-altitude checks (re-run at sealed-tip state) — all GREEN.

---

## §16 Halt-and-surface findings (populated at build-time)

Empty at plan-authoring. HALT-A..HALT-J from §3+§8 are the templates; populated as actually triggered.
