# v0.7.3 PATCH — release-CLI post-publish auto-backfill (defect-closure)

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner pre-ratified scope via Telegram 10675 ("find a way to make this be updated structurally so we don't keep running into staleness").
**Slug:** `v0-7-3-release-cli-auto-backfill`.
**Date authored:** 2026-05-10.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. No new outcome capability — closes a recurring defect in v0.6.0's shipped release-process: post-publish, the version's STATE.md + release-roadmap.md rows currently require a manual SHIPPED-LOCAL → SHIPPED-PUBLIC promotion (commit `f0ae00c` for v0.7.2, `af73a69` for v0.7.1, similar pattern at every prior publish). The v0.6.0 release-process documented "STATE.md updated" as a publish gate but did not enforce post-publish state-update; the recurring miss at v0.6.0 / v0.7.0 / v0.7.1 / v0.7.2 (with downstream agents F2-surfacing the staleness each time) is the defect this closes.
**Predecessor:** v0.7.2 (sealed `91ee1fe`, published `0e67135`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatched 2026-05-10; covers plan-doc authoring + build + seal. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

After `git push origin main + tag` lands, `docs/STATE.md` and `docs/release-roadmap.md` continue to claim the just-published version is "SHIPPED LOCAL — owner gates publish" until a human runs a manual backfill commit. Every minor + patch since v0.6.0 has hit the same defect; every downstream agent that reads STATE.md surfaces the staleness as F2 RUTHLESS FEEDBACK.

The structural fix is a **post-publish auto-backfill step in the release CLI**. After `git push origin main + tag` succeeds, the runner reads the just-published tag SHA + name, scans STATE.md + release-roadmap.md for the version's row(s), and rewrites:

- `SHIPPED LOCAL — owner gates publish` (or equivalent stale-claim phrasing) → `SHIPPED PUBLIC YYYY-MM-DD at tag <name> (annotated <SHA7>)` (the trailing-line stale-claim flip in the STATE.md bullet body).
- For the release-roadmap.md §2 row, append `; **SHIPPED PUBLIC YYYY-MM-DD at tag \`<name>\` (annotated \`<SHA7>\`)**` to the row's third pipe-cell (Anchor column).
- The `**Total shipped:** N minor + M patches. v0.X.Y published.` aggregate-count summary line in §2 is updated: `M` increments (or `N` if minor-class) + the trailing `v<prev_version> published` flips to `v<this_version> published`.
- §3 Active version in release-roadmap.md gets a new bold entry naming this version: `**v0.X.Y <class> (<objective sentence>) SHIPPED PUBLIC YYYY-MM-DD** (tag \`<name>\`, annotated \`<SHA7>\`; seal \`<seal_SHA7>\`).`

The backfill commits as a single follow-on chore commit (`docs(release): v0.X.Y post-publish backfill — SHIPPED PUBLIC`) and pushes that commit immediately as part of the same publish action (the publish has already pushed `main + tag`; the backfill commit pushes to advance `main` one further commit). Idempotence: re-running `loam release v0.X.Y` post-failure-recovery detects already-current state + no-ops (no duplicate rows; no double-PUBLIC marker).

**Aggregate effect:** the v0.6.0 release-process gates table claim "STATE.md updated" — currently true at publish-time only because the BUILDER updates STATE.md to "SHIPPED LOCAL"; after publish-time STATE.md is structurally stale until a human-run backfill commit. Post-v0.7.3 the gate's claim becomes structurally correct: the post-publish step closes the loop, STATE.md + release-roadmap.md stay in sync without manual intervention.

**Why patch (not minor).** Per `docs/release-versioning-policy.md`, MINORs add outcome capability; PATCHes close defects within an already-shipped outcome. The release-CLI's tag + push action already exists (shipped at v0.6.0); v0.7.3 extends it with a post-tag-push state-sync step that closes the documented-gate ↔ enforced-gate gap. No new gate, no new CLI verb, no new user-facing capability — just the missing post-action that the v0.6.0 design assumed but never structurally implemented.

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised (v1.0 quality-bar
            criterion #1 — closed at v0.7.1 across docs/install/CLI;
            extends to release-CLI publish gates' claims being
            structurally enforced post-action, not just at action-time)
             └─ release-CLI post-publish step keeps STATE.md +
                 release-roadmap.md in sync with actual publish state
                  └─ AC.BACKFL.1 (auto-backfill function: SHIPPED LOCAL → PUBLIC)
                  └─ AC.BACKFL.2 (aggregate-count summary update)
                  └─ AC.BACKFL.3 (§3 Active Version entry)
                  └─ AC.BACKFL.4 (idempotence on re-run)
                  └─ AC.BACKFL.5 (test fixture: positive + negative + idempotence)
                  └─ AC.BACKFL.6 (outcome-altitude probe — `loam release v0.7.3 --dry-run` against this plan-doc)
```

The two VALUE_PROPOSITION tests:
- **Primary-persona test** — every AC reduces translation burden by removing the recurring "STATE.md says LOCAL but the version is PUBLIC; let me reconcile manually" ritual that has eaten human attention at every loam publish since v0.6.0. Downstream agents reading STATE.md no longer F2-surface stale-claims; they see ground truth.
- **Harness test** — every AC sharpens an existing primitive (the `loam release` runner gains a post-tag-push state-sync step; the existing `_extract_seal_sha` regex pattern in `gates.py` is the model for the new row-finding regex; the `notes.py` doc-rewrite shape composes with `runner.py` orchestration cleanly).

## §3 — Component fence

**Single-component PATCH.** Touched component: `framework/tools/loam/` (the release-CLI runner + post-ship surface + their test corpus).

**PRIMARY:** `framework/tools/loam/`
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` — new module containing the auto-backfill function set (per AC.BACKFL.1, .2, .3). Exports `apply_backfill(repo_root, version, tag, tag_sha, *, dry_run=False)` returning a `BackfillResult` (count of edits, list of files touched, idempotent-noop flag).
- `framework/tools/loam/src/loam_cli/release/runner.py` — wire the backfill call between step 4 (push) and step 6 (post-ship review). Add a step 4.5 `apply_backfill(...)` + commit + push. Dry-run mode shows the diff without committing.
- `framework/tools/loam/tests/test_AC_BACKFL.py` — new test module covering AC.BACKFL.{1,2,3,4,5}. Three test classes: positive (TBD/SHIPPED-LOCAL → backfilled); negative (already-current → no-op); idempotence (re-run no-op).
- `framework/tools/loam/tests/conftest.py` — extend `staged_repo` fixture if needed to expose the SHIPPED LOCAL line shape; default = inline fixture extension within the new test module to preserve existing tests' semantics (per D-BACKFL.5).

**Universal-admission docs:**
- `docs/plans/v0-7-3-release-cli-auto-backfill.md` (this file).
- `docs/plans/v0-7-3-release-cli-auto-backfill.manifest.yaml`.
- `docs/STATE.md` — v0.7.3 SHIPPED LOCAL row added at end-of-build.
- `docs/release-roadmap.md` — v0.7.3 §2-shipped row added with seal SHA at end-of-build.
- `docs/experiments/v0-7-3-hard-smoke.md` — HARD smoke writeup for the v0.7.3 publish gate (covers AC.BACKFL.6 outcome-altitude probe).
- `docs/release-process.md` — runbook §1 pre-publish gates table gets a new row `**post-publish state-sync** — auto-backfill applies after tag push; commits + pushes as `docs(release): vX.Y.Z post-publish backfill — SHIPPED PUBLIC`. No-op when state is already current.` (informative; the gate is structurally enforced at the runner-side, not user-side).
- `docs/FUTURE_IDEAS_DRAFT.md` — capture the recurring-staleness defect → mark RESOLVED at v0.7.3 with the AC ladder reference.

**Untouched:** all other components. No new components; no new files outside the universal-admission set above.

## §4 — Acceptance criteria

Six ACs plus seal-diff. AC IDs use the scope-descriptive `BACKFL` family per `feedback_scope_descriptive_ac_ids` ("BACKFL" = "post-publish backfill").

### AC.BACKFL.1 — Auto-backfill function (SHIPPED LOCAL → PUBLIC + TBD-AT-* placeholders)

**What:** New module `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` exports a function `apply_backfill(repo_root, version, tag, tag_sha, *, today=None, dry_run=False)` that:

- Reads `docs/STATE.md`. Locates the `**<version> ... SHIPPED LOCAL**` bullet line (the bullet body's trailing-line claim — concretely the `vX.Y.Z SHIPPED LOCAL — owner gates publish.` sentence at the end of the bullet body, OR any equivalent stale-claim shape matching `<version> SHIPPED LOCAL — [^.]+\.`). Replaces that trailing sentence with `**<version> SHIPPED PUBLIC YYYY-MM-DD at tag \`<tag>\` (annotated \`<sha7>\`)**.` (sha7 = first 7 chars of tag_sha).
- Reads `docs/release-roadmap.md`. Locates the §2 row whose first pipe-cell starts with `<version>`. Backfills any `TBD-AT-COMMIT` / `TBD-AT-APPLY` / `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders in the row to known SHAs (seal SHA available from `gates._extract_seal_sha(roadmap_body, version)`; tag SHA passed in; apply SHA NOT discoverable from caller — leave `TBD-AT-APPLY` placeholders alone if encountered, surface to operator). Then appends `; **SHIPPED PUBLIC YYYY-MM-DD at tag \`<tag>\` (annotated \`<sha7>\`)**` to the row's third pipe-cell content (the "Anchor" column) iff the marker is not already present.
- Returns a `BackfillResult` dataclass with fields: `edits_applied: int`, `files_touched: list[Path]`, `idempotent_noop: bool` (True when no edits were needed because state was already current), `state_md_edit: str | None` (the literal sentence before/after for the operator's diff view), `roadmap_edit: str | None` (same).

**Acceptance:**
- `apply_backfill` is callable from `runner.run` between the push and post-ship review steps.
- When the inputs match the canonical SHIPPED-LOCAL state (post-seal-pre-publish), the function returns `BackfillResult(edits_applied=2, idempotent_noop=False, ...)` with both files touched.
- When the inputs match an already-PUBLIC state (the rows already carry `SHIPPED PUBLIC at tag ...` text for this version), the function returns `BackfillResult(edits_applied=0, idempotent_noop=True, ...)` and writes nothing.
- `dry_run=True` returns the result + the proposed edits as strings on `state_md_edit` / `roadmap_edit` but does NOT mutate any file on disk.
- `today` parameter (default `None` → `datetime.date.today()`) lets tests pin the date deterministically.

### AC.BACKFL.2 — Aggregate-count summary update

**What:** When `apply_backfill` runs against `release-roadmap.md`, it also locates the `**Total shipped:** N minor + M patches. v<prev> published. ...` summary line that immediately follows the §2 table (separated by a blank line) and updates it to reflect the just-published version. Concretely:

- Counts published versions by walking the §2 table rows + counting how many carry a `SHIPPED PUBLIC at tag` marker (after applying this cycle's edit). Distinguishes minor (`vX.Y.0`) vs patch (`vX.Y.Z` with Z>0). For backwards-compat with the historical SemVer footnote (Q3 2026-05-09), a row that explicitly says `MINOR` in its third cell counts as minor regardless of version-number form; a row that says `PATCH` counts as patch.
- Replaces `N minor + M patches` with the recomputed counts. Replaces `v<prev> published` with `v<this> published` (the single-version trailing claim).
- Leaves the rest of the summary line (the post-`v<prev> published. ` prose summary of major outcomes) unchanged. The trailing prose is editorial; auto-backfill does NOT generate descriptive prose for the new version.

**Acceptance:**
- Summary line counts increment correctly when a new version's row is being promoted to PUBLIC.
- `v<prev> published` flips to `v<this> published` (just the trailing single-version claim, NOT the per-version summary prose that follows it).
- When the summary line is already current (idempotence case — re-run on already-published version), the line is unchanged.
- When the §2 table has zero `SHIPPED PUBLIC at tag` markers (test-fixture early-state edge case), the summary line is left untouched + the operator gets a hint in the result that the summary-update was skipped.

### AC.BACKFL.3 — §3 Active Version section new bold entry

**What:** When `apply_backfill` runs against `release-roadmap.md`, it locates the `## §3 Active version` section heading + scans its body for the LAST bold-form `**vX.Y.Z ... SHIPPED PUBLIC YYYY-MM-DD**` entry. If a bold entry for the just-published version is NOT already present, appends a new sentence to the §3 body (immediately before the next `## §<n>` heading boundary OR end-of-section paragraph break, whichever is sooner). Sentence form:

```
**v<X.Y.Z> <CLASS> (<objective sentence>) SHIPPED PUBLIC YYYY-MM-DD** (tag `<tag>`, annotated `<sha7>`; seal `<seal_sha7>`).
```

The CLASS comes from the §2 row's third-cell text (`PATCH` / `MINOR` keyword scan; default `PATCH` if not found). The objective sentence comes from the §2 row's second-cell text, truncated to first sentence (split on `.` outside backticks; first 200 chars max as safety bound).

**Acceptance:**
- New bold entry appears in §3 body when not already present, sandwiched cleanly between the existing §3 prose and the next-section boundary (does NOT stomp surrounding text).
- Idempotence: re-running on a state where a bold entry for `<version>` is already present → no edit.
- The CLASS keyword is correctly extracted from the §2 row when the row says `Single-cycle PATCH` / `Single-cycle MINOR` / similar (covers the canonical row shapes from v0.7.0 / v0.7.1 / v0.7.2 / v0.7.3).
- The objective-sentence truncation never breaks markdown (no orphan opening backtick; no orphan asterisk).

### AC.BACKFL.4 — Idempotence: re-running `loam release v0.X.Y` is a clean no-op

**What:** The full publish flow (`runner.run`) re-invoked on an already-published version (tag exists on remote — current idempotency-check at `runner.py:207`) flows through `apply_backfill` with `idempotent_noop=True` for both files. No duplicate rows; no duplicate SHIPPED-PUBLIC markers; no duplicate §3 entries; no duplicate aggregate-count increments. The follow-on commit step is skipped when `idempotent_noop=True` (no commit means no extra push of an empty change).

**Acceptance:**
- `runner.run(repo_root, "v0.X.Y", dry_run=False)` re-invoked on a state where (a) the tag is on remote AND (b) STATE.md + roadmap rows already carry the SHIPPED-PUBLIC marker → returns `PublishOutcome(rc=0, idempotent_noop=True, ...)` AND `apply_backfill` reports `edits_applied=0, idempotent_noop=True`.
- No `git commit` invocation (verified by checking `git log -1 --pretty=%H` matches pre-call HEAD).
- No new push (verified by checking remote ref count unchanged).

### AC.BACKFL.5 — Test fixture: positive + negative + idempotence

**What:** New test module `framework/tools/loam/tests/test_AC_BACKFL.py` covering the three cases plus AC.BACKFL.{1,2,3} structural verifications. At minimum:

- `test_apply_backfill_promotes_state_md_shipped_local_to_public` — fixture `staged_repo` with a STATE.md containing the canonical `vX.Y.Z SHIPPED LOCAL — owner gates publish.` trailing sentence; assert the function rewrites it to `**vX.Y.Z SHIPPED PUBLIC <date> at tag \`vX.Y.Z\` (annotated \`<sha7>\`)**.` form.
- `test_apply_backfill_appends_roadmap_row_marker` — fixture roadmap §2 row without the SHIPPED-PUBLIC marker; assert the marker is appended to the third pipe-cell.
- `test_apply_backfill_updates_aggregate_count_summary` — fixture summary line `**Total shipped:** N minor + M patches. v<prev> published.`; assert M increments (or N for minor); assert v<this> replaces v<prev>.
- `test_apply_backfill_appends_section_3_active_version_entry` — fixture roadmap with §3 body not containing this version; assert a new bold entry is appended.
- `test_apply_backfill_is_noop_when_state_already_public` — fixture with rows already carrying the SHIPPED-PUBLIC marker; assert `BackfillResult(edits_applied=0, idempotent_noop=True)`.
- `test_apply_backfill_is_noop_on_re_run` — apply once; capture state; apply again; assert second call is no-op + state unchanged.
- `test_apply_backfill_dry_run_mutates_nothing_on_disk` — call with `dry_run=True`; assert files are unchanged on disk; assert result carries the proposed edits as strings.
- `test_runner_invokes_backfill_after_tag_push` — use the existing `repo_with_local_remote` fixture from `test_AC_V060_3_*.py`; assert the post-publish commit lands on the local remote with the canonical commit message.

**Acceptance:**
- All test functions land at `test_AC_BACKFL.py`.
- Test module passes (`pytest framework/tools/loam/tests/test_AC_BACKFL.py -v` → all GREEN).
- Existing `test_AC_V060_*` modules continue to pass (`pytest framework/tools/loam/tests/ -v` → no regressions).

`outcome-altitude: false` — implementation-altitude AC (test against function signature + canonical-fixture; not a real-execution probe against the production binary).

### AC.BACKFL.6 — Outcome-altitude probe (`loam release v0.7.3 --dry-run` against this plan-doc + state)

**What:** Real-execution probe against the production CLI binary. After AC.BACKFL.{1-5} land and the v0.7.3 plan-doc is in place + STATE.md row + roadmap row both carry the SHIPPED-LOCAL state, run `loam release v0.7.3 --dry-run` from the repo root. The pre-publish gates report GREEN; the dry-run output includes a `DRY-RUN: would apply post-publish backfill — would rewrite STATE.md line <N> + roadmap row <M> + summary line <K> + §3 entry; <X> total edits` summary block showing what the post-publish step would do without actually running it.

**Acceptance:**
- `loam release v0.7.3 --dry-run` runs to completion without crashing.
- Pre-publish gates all GREEN (HARD smoke + acs-verified + state-shipped + clean-tree + branch-main + seal-reachable, plus any v0.7.1+ additions).
- Output contains a `DRY-RUN: would apply post-publish backfill` line naming the file edits in human-readable form (count of edits + filenames + the literal old/new sentences for the STATE.md flip).
- Probe is documented in `docs/experiments/v0-7-3-hard-smoke.md` with the literal CLI invocation + the gate report excerpt + the dry-run backfill preview.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` — invokes production entry-point against realistic input (this very plan-doc + the live STATE.md + the live roadmap). Risk band: **production-facing release-CLI** — this defect-closure determines whether downstream agents get truthful state from STATE.md post-publish; HARD per-cycle REQUIRED.

### AC.BACKFL.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (AC.BACKFL.{1,2,3} — new module)
- `framework/tools/loam/src/loam_cli/release/runner.py` (AC.BACKFL.1 — wire the call into the publish flow)
- `framework/tools/loam/tests/test_AC_BACKFL.py` (AC.BACKFL.5 — new test module)
- `framework/tools/loam/tests/conftest.py` — only if AC.BACKFL.5 needs a fixture extension; otherwise untouched
- `docs/plans/v0-7-3-release-cli-auto-backfill.md` (this file — universal-admission)
- `docs/plans/v0-7-3-release-cli-auto-backfill.manifest.yaml` (universal-admission)
- `docs/STATE.md` (universal-admission; v0.7.3 SHIPPED LOCAL rollup)
- `docs/release-roadmap.md` (universal-admission; v0.7.3 §2-shipped row)
- `docs/experiments/v0-7-3-hard-smoke.md` (universal-admission; AC.BACKFL.6 writeup)
- `docs/release-process.md` (universal-admission; pre-publish gates table extension naming the new post-publish step — informative)
- `docs/FUTURE_IDEAS_DRAFT.md` (universal-admission; mark recurring-staleness capture RESOLVED at v0.7.3, OR add a fresh capture-and-resolve entry if no prior capture exists)
- Component sidecar + narrative file (managed by `loam amend apply` / `loam amend seal`)

Sidecar advances per sealed-component-cycle ritual via `loam amend apply` then `loam amend seal`.

## §5 — Decisions builder rules at build time

- **D-BACKFL.1.a (state.md trailing-sentence pattern):** the SHIPPED-LOCAL trailing claim takes the canonical form `<version> SHIPPED LOCAL — owner gates publish.` (verified at f0ae00c diff for v0.7.2). Builder uses regex `re.compile(r"\b" + re.escape(version) + r"\s+SHIPPED LOCAL\s*[—\-]\s*[^.\n]+\.")` to locate and replace. If the regex fails to match (the bullet body uses a different stale-claim shape), `apply_backfill` returns a hint naming the missing pattern + leaves the file unchanged + does NOT crash. Operator surface: the dry-run summary names the missing pattern so a manual fix is one-line.
- **D-BACKFL.1.b (TBD-AT-* placeholder backfill scope):** the TBD-AT-* family includes `TBD-AT-COMMIT` / `TBD-AT-APPLY` / `TBD-AT-SEAL` / `TBD-AT-TAG`. Of these, the CLI knows: `TAG` (tag_sha argument) + `SEAL` (extractable from roadmap row via existing `gates._extract_seal_sha`). `COMMIT` and `APPLY` are NOT discoverable from the runner's inputs (they're from earlier in the build cycle); leave those placeholders alone + surface to operator. Builder rules whether to attempt SHA-discovery via git-log heuristic or not — recommended NO heuristic (false-positive risk too high; manual backfill of COMMIT/APPLY at build-time per existing v0.7.2 publish-prep precedent).
- **D-BACKFL.2.a (aggregate-count summary parser):** the summary line shape is `**Total shipped:** N minor + M patches. v<prev> published. <prose>`. Builder uses regex `re.compile(r"^\*\*Total shipped:\*\*\s+(\d+)\s+minor\s+\+\s+(\d+)\s+patches?\.\s+v[\d.]+\s+published\.", re.MULTILINE)` to locate. Counts derived by walking §2 rows + counting `SHIPPED PUBLIC at tag` markers post-edit (after this cycle's edit lands). MINOR/PATCH classification: scan third-cell text for `MINOR` keyword first, fall back to `PATCH`.
- **D-BACKFL.3.a (§3 entry-insertion location):** insert the new bold entry at the END of the §3 body (just before the next `## §<n>` boundary OR EOF for last section). Recommended insertion-point: scan the §3 body for the last `*` character followed by space (the closing-asterisk of the last bold entry) + insert the new sentence after the next `\n\n` boundary OR just before the next `##` heading, whichever is sooner. If §3 is empty or only carries free-form prose without prior bold entries, append the new entry as a new paragraph at the end of §3.
- **D-BACKFL.4 (commit + push mechanics):** post-backfill commit uses `git commit -m "docs(release): vX.Y.Z post-publish backfill — SHIPPED PUBLIC"` (no `--amend` per HARD HALT #4). Push is `git push origin main` (no tag — the tag is already on remote from step 4). `dry_run=True` skips both commit + push.
- **D-BACKFL.5 (fixture choice):** new test module `test_AC_BACKFL.py` builds its own fixtures inline OR extends the existing `staged_repo` fixture with the SHIPPED-LOCAL line shape. Default = author each test's fixture inline (small, contained) so the existing `staged_repo` semantics for `test_AC_V060_*` tests are preserved. Switch to `conftest.py` extension only if inline-fixture verbosity exceeds ~30 lines per test.
- **D-BACKFL.6 (probe location):** the `loam release v0.7.3 --dry-run` invocation lands in `docs/experiments/v0-7-3-hard-smoke.md` §1 (canonical HARD smoke writeup location). Captures: invocation command, exit code, full gate-report stdout, dry-run backfill preview block.

## §6 — Out of scope (explicit)

- **Retroactive backfill of historical versions** (v0.6.0 / v0.7.0 / v0.7.1 / v0.7.2 — already manually backfilled in commits `5c0d272` / `0f0d4b3` / `f0ae00c` etc). v0.7.3 closes the recurring-defect going forward; historical state stays as-edited.
- **Restructuring the STATE.md row format** (the bullet-list shape is well-established across 18 minor + 8 patch versions; backfill operates on the existing format, does NOT propose a new row layout).
- **Cross-publishing to GitHub Releases** (separate concern; current CLI handles via `gh release create` already at runner.py:295-301).
- **Apply-commit / source-edit-commit SHA discovery** — those SHAs aren't passed to `runner.run` (see D-BACKFL.1.b); the auto-backfill leaves `TBD-AT-COMMIT` / `TBD-AT-APPLY` placeholders alone and surfaces them to the operator. Builder ruling: no heuristic SHA-discovery (false-positive risk).
- **TBD-AT-* backfill across MULTIPLE versions in one run** — `apply_backfill` operates on a single version per call. If multiple versions have TBD-AT-* placeholders, separate calls handle each (or operator runs `loam release vX.Y.Z` for each in turn).
- **Editorial prose generation** — the aggregate-count summary line's trailing prose summary (`v0.3.0 ships META-FRAMEWORK foundation; v0.4.0 ships ...`) is editorial + curated by humans; auto-backfill never touches it. The single-version `v<this> published` claim IS auto-flipped (mechanical, deterministic) per AC.BACKFL.2.
- **Pre-publish state-update enforcement gate** — a separate FIDRAFT capture for v0.8.0+ (the v0.6.0 `state-shipped` gate already verifies STATE.md mentions the version + SHIPPED, but does NOT verify the row is up-to-date with seal SHAs). Out of v0.7.3 scope.
- **Anthropic API key paths** (per architectural constraint, never).
- **Multi-LLM via OpenRouter** (per architectural constraint, backlog only).

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.BACKFL.6 outcome-altitude probe RED. The auto-backfill function fails the dogfood probe against this plan-doc + the live STATE.md + the live release-roadmap.md. Halt; surface as F-DESIGN candidate.
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
5. Wall-clock exceeds upper band (90 min midpoint ~76 min) by >2× → 4 hr (matches dispatch brief's surface threshold). Halt with current state.
6. Discovery that the auto-backfill regex/parser breaks an existing release-CLI path or test (e.g., the `state-shipped` gate starts returning RED because the STATE.md edit changed the literal-form the gate scans for; or `seal-reachable` parser starts misbehaving because the appended-marker shape interferes). Halt; surface; do NOT extend scope to fix downstream.
7. The backfill function tries to push a commit BEFORE the tag has been pushed by step 4 of the runner. Sequence MUST be: (4) push branch + tag → (4.5) backfill + commit + push backfill commit. If the order inverts, the backfill commit advances `main` past the seal SHA the tag points to → tag-vs-main divergence. Halt + surface if any test fixture would put backfill push BEFORE tag push.
8. Discovery that the `**Total shipped:** N minor + M patches` summary line shape varies more than the canonical form named in D-BACKFL.2.a across the release-roadmap.md history (e.g., earlier shapes used `M patch` singular, OR included the major-count differently). Halt; surface variant; let dispatcher rule on summary-line tolerance scope.
9. Discovery that AC.BACKFL.3's §3 entry-insertion would stomp on existing curated §3 prose (the §3 body currently carries multi-paragraph editorial commentary; insert-point heuristic must not corrupt it). Halt; surface; do NOT extend scope to "rewrite §3 cleanly" — that's MINOR-class.
10. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.

## §8 — Dependencies

- **v0.6.0 (concrete release process)** — HARD. v0.7.3 extends v0.6.0's `runner.run` orchestration with a post-tag-push step; v0.7.3 cannot land without v0.6.0's `loam release` substrate existing.
- **v0.7.2 (release-CLI parser fix)** — SOFT. v0.7.3's outcome-altitude probe (AC.BACKFL.6) consumes the fixed `acs-verified` parser to verify this plan-doc's §4 ACs without false-positives on cross-references.
- **v0.7.0 (`## §13 — §status` literal heading parser)** — SOFT. The plan-doc §status backfill at end-of-build uses the literal heading form per the v0.7.0 fix.
- **`docs/release-versioning-policy.md`** — SOFT. PATCH-class declaration grounded in the policy.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `BACKFL` AC ID family choice over `V073.*`.
- **`feedback_build_forward_on_publish_pending`** — SOFT. Justifies dispatching v0.7.3 while v0.7.2 just sealed-and-published (build-forward instance).
- **`feedback_no_amend_in_agent_dispatches`** — HARD. The post-backfill commit is a NEW commit, never `--amend`.
- **No external service dependencies.**
- **No new Python packages** (subscription-only constraint).

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — single-component PATCH; tight per-AC scope; one new module + one runner-edit + one test module + one outcome-altitude probe. Defect-closure (no design exploration); confidence in outcome shape is high (Lens 4 — tight scope appropriate). v0.7.2 actuals (43 min for similar single-component PATCH) inform the lower bound; v0.7.3 has slightly more code (new module + runner wiring + 8 tests vs v0.7.2's parser tighten + 3 tests).

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 15-25 min | 20 min |
| AC.BACKFL.1 — auto-backfill function (new module) | 20-35 min | 27 min |
| AC.BACKFL.2 — aggregate-count summary update | 8-15 min | 12 min |
| AC.BACKFL.3 — §3 Active Version entry append | 8-15 min | 12 min |
| AC.BACKFL.4 — idempotence wiring + verification | 5-10 min | 7 min |
| AC.BACKFL.5 — test module (8 tests) | 15-25 min | 20 min |
| AC.BACKFL.6 — outcome-altitude probe + writeup | 10-15 min | 12 min |
| FUTURE_IDEAS_DRAFT capture-and-resolve | 3-5 min | 4 min |
| docs/release-process.md gates-table extension | 3-5 min | 4 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 15-25 min | 20 min |
| **Total v0.7.3 build** | **102-175 min (~1.7-2.9 hr)** | **~138 min (~2.3 hr)** |

The dispatch brief estimates 60-120 min midpoint ~90 min. Plan-time revision: **102-175 min midpoint ~138 min**. Defensible: the dispatch midpoint sits at the lower edge of the plan band; lean-upward reflects the new-module-vs-tighten-existing distinction (v0.7.2 was a 30-line parser tighten; v0.7.3 is a ~150-line new module covering three orthogonal edit-targets — STATE.md row, roadmap row, summary line, §3 entry). Defect-closure shape with high confidence in scope keeps the band tight; midpoint sits below the 4-hr HARD HALT threshold. If new-module authoring goes faster than the band's midpoint (recent calibration: similar-shape new modules like v0.6.0's `notes.py` came in ~25 min for ~210 lines), lower-band ~100 min is reachable.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- Telegram 10675 (owner directive 2026-05-10) — "find a way to make this be updated structurally so we don't keep running into staleness." The dispatch authority for v0.7.3.
- `f0ae00c` (commit 2026-05-10, v0.7.2 post-publish backfill) — the LAST manual SHIPPED-LOCAL→SHIPPED-PUBLIC cycle; the commit message names v0.7.3 as the structural-fix vehicle.
- `af73a69` (commit 2026-05-10, v0.7.1 publish-prep) — prior pattern instance; the publish-prep edits the v0.7.3 auto-backfill replaces structurally.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground.
- `framework/tools/loam/src/loam_cli/release/runner.py` lines 286-317 — the publish-flow steps v0.7.3 inserts the post-backfill step into.
- `framework/tools/loam/src/loam_cli/release/gates.py` lines 424-449 — `_extract_seal_sha` regex pattern v0.7.3's auto-backfill composes with for SHA discovery.
- `framework/tools/loam/src/loam_cli/release/post_ship.py` — sibling module shape v0.7.3's new `post_publish_backfill.py` mirrors structurally.
- `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` (lines 1-150 — fixture shape) — the fixture-shape v0.7.3's test module composes with via `staged_repo` extension.
- `docs/plans/v0-7-2-release-cli-parser-fix.md` — predecessor PATCH-class plan-doc; structural template for §1-§14 sectioning.
- Memory rules: `feedback_scope_descriptive_ac_ids.md` (AC.BACKFL.* not AC.V073.*), `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_no_anthropic_api_key.md` (HARD HALT #10), `feedback_subagent_odd_violation_halt.md` (HARD HALT #2), `feedback_duration_estimation_rubric.md` (§9), `feedback_build_forward_on_publish_pending.md` (§8 build-forward justification), `feedback_test_outcome_altitude_required.md` (AC.BACKFL.6 risk-band), `feedback_locked_design_not_license_for_bad_outcomes.md` (the v0.6.0 design's "STATE.md updated" gate is currently a documented-but-not-enforced claim — this plan revisits the v0.6.0 design rather than living with the bad outcome).

## §13 — §status

**Build cycle:** plan-only at authoring time. Build dispatched 2026-05-10 (Telegram 10675); §status backfilled at end-of-build with commit SHAs + AC verdicts.

### AC verdict matrix

(Pending — backfilled at end-of-build with GREEN/RED + evidence per AC. Template per v0.7.2's §13 matrix.)

### AI-time actuals

(Pending — backfilled at end-of-build comparing predicted vs actual per stage.)

### Halt-and-surface findings

(Pending — backfilled at end-of-build with any HARD HALTs hit + dispatcher-surfaced findings.)

## §14 — Method decisions

The plan-doc's §5 names the build-time decisions (D-BACKFL.1.a SHIPPED-LOCAL pattern, D-BACKFL.1.b TBD-AT-* scope, D-BACKFL.2.a summary-line parser, D-BACKFL.3.a §3 insertion location, D-BACKFL.4 commit/push mechanics, D-BACKFL.5 fixture choice, D-BACKFL.6 probe location). Build-time deviations from these rulings are surfaced here at end-of-build.

### Commit SHAs

- Plan-doc + manifest authoring: TBD-AT-COMMIT
- Source-edit + admin batch (auto-backfill module + runner wiring + tests + release-process update + FIDRAFT + STATE + roadmap + smoke writeup): TBD-AT-COMMIT
- Apply auto-commit (BASELINE + sidecar bump): TBD-AT-APPLY
- Seal commit (deterministic seal): TBD-AT-SEAL

### Build-time decision deviations

(Pending — backfilled at end-of-build with any deviations from §5 rulings + the surfacing rationale.)
