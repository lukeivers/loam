# v0.7.4 PATCH — auto-backfill completeness (defect-closure for v0.7.3's spec gaps)

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: scope ratified Telegram 10680 (option A — full structural elimination of SHIPPED-LOCAL → SHIPPED-PUBLIC manual touchpoints).
**Slug:** `v0-7-4-auto-backfill-completeness`.
**Date authored:** 2026-05-10.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. No new outcome capability — v0.7.3 closed the obvious surface of the recurring-staleness defect; v0.7.3's own publish dogfood at `loam release v0.7.3` (commit `88964cb`) revealed the spec was **incomplete**: the runner applied 3 edits / 2 files but missed 4 residual surfaces that still required manual touch-up (commits `cb71ca5` for source-edit + apply SHA backfill + STATE.md seal SHA backfill, `5c3f7ac` for roadmap §2 seal SHA backfill, `88964cb` for the auto-flip that left the leading title unflipped). v0.7.4 closes those 4 gaps.
**Predecessor:** v0.7.3 (sealed `39170e6`, published `72de0da`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatched 2026-05-10 (Telegram 10680); covers plan-doc authoring + build + seal. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The v0.7.3 publish dogfood is the F2 surface this cycle closes against. v0.7.3 wired `apply_backfill` between tag-push and post-ship review and committed as `docs(release): v0.7.3 post-publish backfill — SHIPPED PUBLIC` (commit `88964cb`, applied 3 edits / 2 files). But the post-publish state at that commit was still incomplete:

1. **Leading row-title not flipped.** `docs/STATE.md:133` started with `**v0.7.3 PATCH SHIPPED LOCAL** — release-CLI ...`. Auto-backfill flipped only the trailing sentence (appended `**v0.7.3 SHIPPED PUBLIC ...**.`). The eye-grabbing title-claim — the bolded leader of the bullet — is the misleading one a reader sees first.
2. **STATE.md `seal TBD-AT-SEAL` not backfilled.** v0.7.3's `_backfill_tbd_placeholders` only ran against the roadmap §2 row. STATE.md row had its own `seal TBD-AT-SEAL` placeholder (post-publish-prep at commit `cb71ca5` manually backfilled it, including the source-edit + apply SHAs as a side effect).
3. **`TBD-AT-COMMIT` placeholder still manual.** The source-edit commit SHA wasn't in the runner's input scope; v0.7.3 left this alone as a documented limitation (D-BACKFL.1.b).
4. **`TBD-AT-APPLY` placeholder still manual.** Apply commit SHA same — wasn't in publish-time runner inputs.

The v0.7.4 outcome shape is **full structural elimination** of the SHIPPED-LOCAL → SHIPPED-PUBLIC manual touchpoints in the standard publish path. After v0.7.4 lands, `loam release vX.Y.Z` against a freshly-sealed version with the canonical pre-publish state (leading title `SHIPPED LOCAL`, trailing sentence `SHIPPED LOCAL — owner gates publish.`, `seal TBD-AT-SEAL`, `apply TBD-AT-APPLY`, `source-edit ... TBD-AT-COMMIT`) needs zero manual follow-on commits to reach a fully-current SHIPPED-PUBLIC state. The publish IS the state-sync, end-to-end.

**Why patch (not minor).** Per `docs/release-versioning-policy.md`, MINORs add outcome capability; PATCHes close defects within an already-shipped outcome. v0.7.3's outcome shape was "post-publish state stays in sync without manual intervention" — the auto-backfill function exists, the runner wires it, the commit lands. v0.7.4 doesn't add a new gate, a new CLI verb, a new state-sync target — it tightens the existing function to cover the full set of mechanically-derivable surfaces the v0.7.3 spec missed.

**Why this needed v0.7.3 to ship first.** The 4 gaps weren't visible from the v0.7.3 plan-doc's design surface — the plan-doc explicitly named TBD-AT-COMMIT / TBD-AT-APPLY as out-of-scope (D-BACKFL.1.b) and didn't anticipate the leading-title issue (the test fixture only covered the trailing-sentence form). Real-execution dogfood at publish time surfaced the gaps via the mismatch between commit `88964cb`'s diff and the manual touch-up commits that followed it.

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised (v1.0 quality-bar
            criterion #1 — closed at v0.7.1; extends to release-CLI
            publish gates' claims being structurally enforced
            post-action, not just at action-time, AND covering the
            full set of mechanically-derivable surfaces)
             └─ release-CLI post-publish auto-backfill covers ALL
                 SHIPPED-LOCAL → SHIPPED-PUBLIC manual touchpoints
                  └─ AC.BACKFL2.1 (title-flip — leading bold claim)
                  └─ AC.BACKFL2.2 (STATE.md seal SHA symmetry)
                  └─ AC.BACKFL2.3 (source-edit + apply SHA discovery
                                   from the seal commit graph)
                  └─ AC.BACKFL2.4 (idempotence preserved across all
                                   v0.7.3 + v0.7.4 surfaces)
                  └─ AC.BACKFL2.5 (test fixtures extend BACKFL suite)
                  └─ AC.BACKFL2.6 (outcome-altitude probe — `loam
                                   release v0.7.4 --dry-run` against
                                   this very plan-doc)
                  └─ AC.BACKFL2.S (seal-diff discipline)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — every AC reduces translation burden by removing the residual "the publish landed but the state still claims SHIPPED LOCAL at the title" / "I still have to chase down the source-edit + apply SHAs by hand" rituals that ate human attention at v0.7.3's own publish. Downstream agents reading STATE.md no longer need to interpret "leading title says LOCAL but trailing sentence says PUBLIC" as a contradiction.
- **Harness test** — every AC sharpens the existing `apply_backfill` primitive. The new helpers (`_leading_title_pattern`, STATE.md `_backfill_state_md_placeholders`, `_discover_source_edit_and_apply_shas`) compose on top of the existing module's per-target helper-function decomposition (D-BACKFL.3.a precedent — orthogonal helpers per edit-target).

## §3 — Component fence

**Single-component PATCH.** Touched component: `framework/tools/loam/` (the release-CLI runner + post-publish-backfill module + their test corpus).

**PRIMARY:** `framework/tools/loam/`
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` — extend with three new helpers:
  - `_leading_title_pattern(version)` + `_backfill_state_md_leading_title(...)` (AC.BACKFL2.1) — flip the bolded leader `**vX.Y.Z <CLASS> SHIPPED LOCAL**` → `**vX.Y.Z <CLASS> SHIPPED PUBLIC**`. Roadmap §2 row's leading title (the third pipe-cell's classification leader, e.g., `Single-cycle PATCH:`) is NOT a SHIPPED-LOCAL/PUBLIC claim itself — the per-row marker append covers the roadmap; only STATE.md row needs the leading-title flip.
  - `_backfill_state_md_placeholders(...)` (AC.BACKFL2.2) — apply TBD-AT-* backfill to the STATE.md row body, mirror of the existing roadmap-row helper. Applies to TBD-AT-SEAL + TBD-AT-TAG (known SHAs) plus, after AC.BACKFL2.3 lands, TBD-AT-COMMIT + TBD-AT-APPLY (discovered SHAs).
  - `_discover_source_edit_and_apply_shas(repo_root, seal_sha)` (AC.BACKFL2.3) — walk back from the seal commit to find the apply commit (`chore(amend): <slug> manifest+apply — ... BASELINE+sidecar bump to <SOURCE_EDIT_SHA>` message form) + parse the source-edit SHA out of the apply commit's message. Returns `(source_edit_sha, apply_sha)` or `(None, None)` when the canonical message form isn't present (defensive — surfaces via hints, never crashes).
- `framework/tools/loam/src/loam_cli/release/runner.py` — pass the seal SHA to `apply_backfill` in BOTH the publish-success branch + the idempotent-noop branch (the existing `seal_sha=seal_sha` keyword already lands in publish-success per the v0.7.3 corrective at `59c3b24`; verify same in idempotent-noop branch). No new wiring — the discovery happens inside `apply_backfill` from the (seal_sha, repo_root) it already receives.
- `framework/tools/loam/tests/test_AC_BACKFL.py` — extend the existing test module with new AC.BACKFL2.* tests:
  - `test_apply_backfill_flips_state_md_leading_title` (AC.BACKFL2.1)
  - `test_apply_backfill_backfills_state_md_seal_placeholder` (AC.BACKFL2.2)
  - `test_apply_backfill_discovers_source_edit_and_apply_from_seal_commit` (AC.BACKFL2.3)
  - `test_apply_backfill_state_md_already_public_title_no_op` (AC.BACKFL2.4 — no double-flip)
  - `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd` (AC.BACKFL2.5 integration — full canonical pre-image → zero TBD-AT-* + zero SHIPPED LOCAL residual)
- `framework/tools/loam/tests/conftest.py` — extend the existing `staged_repo` / fixture-builders if needed; default = inline fixture extension within the new tests per D-BACKFL2.5 (mirror of v0.7.3's D-BACKFL.5 default).

**Universal-admission docs:**
- `docs/plans/v0-7-4-auto-backfill-completeness.md` (this file).
- `docs/plans/v0-7-4-auto-backfill-completeness.manifest.yaml`.
- `docs/STATE.md` — v0.7.4 SHIPPED LOCAL row added at end-of-build.
- `docs/release-roadmap.md` — v0.7.4 §2-shipped row added with seal SHA at end-of-build.
- `docs/experiments/v0-7-4-hard-smoke.md` — HARD smoke writeup for the v0.7.4 publish gate (covers AC.BACKFL2.6 outcome-altitude probe).
- `docs/release-process.md` — runbook update (informative): the post-publish state-sync row's coverage table extends to leading-title flip + STATE.md placeholder symmetry + commit-graph-walk SHA discovery.
- `docs/FUTURE_IDEAS_DRAFT.md` — capture the v0.7.3-spec-incomplete finding → mark RESOLVED at v0.7.4.

**Untouched:** all other components. No new components; no new files outside the universal-admission set above. Specifically NOT touching `plugins/dev-sdlc/tools/loam-amend/` (path-b ruling per D-BACKFL2.3).

## §4 — Acceptance criteria

Six ACs plus seal-diff. AC IDs use the scope-descriptive `BACKFL2` family per `feedback_scope_descriptive_ac_ids` ("BACKFL2" = "post-publish backfill — completeness amendment").

### AC.BACKFL2.1 — Title-flip: leading row-title `**vX.Y.Z <CLASS> SHIPPED LOCAL**` → `**vX.Y.Z <CLASS> SHIPPED PUBLIC**`

**What:** Extend `apply_backfill` to flip the leading bolded title-claim in `docs/STATE.md`'s row for *version*. The canonical form is `**<version> <CLASS> SHIPPED LOCAL**` where `<CLASS>` is `MINOR` / `PATCH` / `minor` / `patch` (case-insensitive — historical rows have used both shapes; v0.7.3 row used `PATCH`, v0.5.0 row used `minor`). Replacement preserves `<CLASS>` casing + form.

**Roadmap §2 row scope-question:** the §2 row's third pipe-cell starts with `Single-cycle PATCH:` / `Single-cycle MINOR:` — this is a class-classification leader, NOT a SHIPPED-LOCAL/PUBLIC claim. The per-row marker append (existing v0.7.3 behavior) IS the SHIPPED-PUBLIC signal for the roadmap row. So AC.BACKFL2.1 ONLY touches STATE.md.

**Acceptance:**
- `apply_backfill(...)` flips `**v0.7.4 PATCH SHIPPED LOCAL**` → `**v0.7.4 PATCH SHIPPED PUBLIC**` in STATE.md (preserve `<CLASS>` casing + spacing).
- Idempotent: re-run on already-flipped title → no-op.
- Already-public detection prevents double-flip when title is `**v0.7.4 PATCH SHIPPED PUBLIC**` already.
- Edits-applied count increments (this is a NEW edit-target distinct from the trailing-sentence flip).
- `state_md_edit` summary names the leading-title edit (or aggregates with the trailing-sentence flip into one combined summary line).

### AC.BACKFL2.2 — STATE.md seal SHA symmetry: `seal TBD-AT-SEAL` backfilled

**What:** Mirror the v0.7.3 roadmap-row TBD-AT-* backfill to the STATE.md row body. The STATE.md row currently has TBD-AT-SEAL in plain prose (e.g., `... apply 527698b; seal TBD-AT-SEAL.`). Replace with `seal `<sha7>`` (backtick-wrapped form, mirror of the roadmap-row replacement form).

The same helper covers TBD-AT-TAG if present in STATE.md (some historical rows carried it; current v0.7.3 row uses `**SHIPPED PUBLIC ... at tag \`v0.7.3\` (annotated \`72de0da\`)**.` form which is the trailing-sentence target, not a TBD placeholder). After AC.BACKFL2.3 lands, the same helper also covers TBD-AT-COMMIT + TBD-AT-APPLY in STATE.md.

**Acceptance:**
- `apply_backfill(...)` replaces `seal TBD-AT-SEAL` → `seal \`<sha7>\`` in STATE.md row.
- Mirror of v0.7.3's roadmap-row behavior (consistent replacement form across both files).
- Idempotent: re-run on already-replaced state → no-op.
- Edits-applied count increments per replacement.
- Hint surfaces if the STATE.md row contains an unrecognized TBD-AT-* placeholder (defensive — never crash).

### AC.BACKFL2.3 — Source-edit + apply SHA auto-backfill via commit-graph walk

**Builder ruling: PATH B (publish runner walks the commit graph from seal_sha).** Path A (extend `loam amend seal` to record SHAs into the row at seal-time) requires cross-component changes (`plugins/dev-sdlc/tools/loam-amend/`); changes the seal-step's contract; introduces ordering constraints between source-edit/apply timing and seal authoring. Path B keeps everything in `framework/tools/loam/` (release-CLI component fence preserved) and exploits the deterministic commit message form already verified across 10+ historical apply commits.

**What:** New helper `_discover_source_edit_and_apply_shas(repo_root, seal_sha) → tuple[str | None, str | None]` in `post_publish_backfill.py`:

1. Read the seal commit's message via `git log -1 --pretty=%B <seal_sha>`. Verify it matches `^chore(seals): <slug> — .* at <apply_sha>$` (canonical form across all 10+ historical seals). Extract the apply SHA from the trailing `at <sha>` clause.
2. Read the apply commit's message via `git log -1 --pretty=%B <apply_sha>`. Verify it matches `^chore(amend): <slug> manifest\+apply — .* BASELINE\+sidecar bump to <source_edit_sha>$`. Extract the source-edit SHA.
3. Return `(source_edit_sha, apply_sha)`. Either may be None when the canonical message shape isn't present (e.g., older repos, hand-authored seals); never crash, surface via the result hints.

The TBD-AT-COMMIT / TBD-AT-APPLY backfill then runs against both STATE.md row + roadmap §2 row (using the existing `_backfill_tbd_placeholders` helper, extended to cover COMMIT + APPLY when the discovery succeeded).

**Why path-B is structurally cleaner than path-A:**
- Component fence preserved (single component vs cross-component).
- Existing `loam amend seal` contract unchanged (no new mandatory inputs; no new manifest fields).
- Discovery is deterministic per the verified message-form invariant; the discovery code is colocated with its consumer (the backfill function).
- Path A would need to handle the case where source-edit happens AFTER the loam amend new-plan but BEFORE loam amend apply — an ordering constraint that doesn't exist today and would create coupling.
- Path A would require schema-version bump on manifest (a new field to capture source-edit SHA) — that's MINOR-class adjacent. Out of v0.7.4 patch scope.

**Acceptance:**
- `_discover_source_edit_and_apply_shas(repo_root, "39170e6")` returns `("01e0883...", "527698b...")` when called against the live `/Users/lukeivers/loam/` repo state at v0.7.3's seal SHA. (Real-state probe, not just fixture.)
- Returns `(None, None)` when seal SHA's commit message doesn't match the canonical form; surfaces via hints; never crashes.
- The TBD-AT-COMMIT + TBD-AT-APPLY backfill in STATE.md + roadmap §2 row uses the discovered SHAs.
- The 7-char abbreviation form (mirror of TBD-AT-SEAL replacement) is used.
- When discovery fails for any reason (commit not found, message form mismatch, git-binary-missing), the existing TBD-AT-SEAL + TBD-AT-TAG backfill still runs (graceful degradation per defensive design).

### AC.BACKFL2.4 — Idempotence preserved (don't break v0.7.3's idempotence AC)

**What:** All v0.7.3 + v0.7.4 surfaces respect idempotence. Re-running `loam release vX.Y.Z` on a state where:

- STATE.md leading title is already `SHIPPED PUBLIC` (AC.BACKFL2.1)
- STATE.md `seal TBD-AT-SEAL` already backfilled to `seal \`<sha7>\`` (AC.BACKFL2.2)
- STATE.md `TBD-AT-COMMIT` / `TBD-AT-APPLY` already backfilled (AC.BACKFL2.3)
- All v0.7.3 surfaces already current (trailing sentence, roadmap row marker, summary line, §3 entry — preserved)

→ returns `BackfillResult(edits_applied=0, idempotent_noop=True)` and writes nothing.

**Acceptance:**
- Test `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd` covers the integration case: full canonical pre-image (with all 4 v0.7.4 gaps) → first call applies all edits + zero residual TBD-AT-* + zero residual SHIPPED LOCAL; second call (idempotence re-run) → `idempotent_noop=True`, `edits_applied=0`, files unchanged on disk.
- All 11 v0.7.3 BACKFL tests continue to pass without modification (AC.BACKFL2 doesn't break existing AC.BACKFL.4 verification).
- The runner's idempotent-noop-branch backfill (the post-failure-recovery path at `runner.py:279-297`) also reaches `idempotent_noop=True` when state is fully current.

### AC.BACKFL2.5 — Test fixtures extend the v0.7.3 BACKFL test suite

**What:** Five new test functions added to `framework/tools/loam/tests/test_AC_BACKFL.py`. The fixtures extend the existing `_state_md_with_shipped_local` / `_roadmap_with_shipped_local_row` helpers to cover the canonical v0.7.4 pre-image:

- STATE.md row with: leading `**vX.Y.Z PATCH SHIPPED LOCAL**`, trailing `vX.Y.Z SHIPPED LOCAL — owner gates publish.`, body containing `source-edit ... TBD-AT-COMMIT; apply TBD-AT-APPLY; seal TBD-AT-SEAL`.
- Roadmap §2 row with: trailing `; source-edit ... TBD-AT-COMMIT; apply TBD-AT-APPLY; seal TBD-AT-SEAL |`.
- A `_make_seal_apply_commit_chain(repo_root, version, slug)` helper that constructs a real git commit graph in a tmp_path repo with the canonical seal + apply + source-edit message forms, used by AC.BACKFL2.3 tests.

**Acceptance:**
- `test_apply_backfill_flips_state_md_leading_title` — positive: leading title flips.
- `test_apply_backfill_backfills_state_md_seal_placeholder` — positive: STATE.md `seal TBD-AT-SEAL` → `seal \`<sha7>\``.
- `test_apply_backfill_discovers_source_edit_and_apply_from_seal_commit` — positive: real-commit-graph fixture; discovery returns expected SHAs; STATE.md + roadmap row both backfilled.
- `test_apply_backfill_state_md_already_public_title_no_op` — negative: already-flipped title → no edit.
- `test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd` — integration: full canonical pre-image → zero residual TBD-AT-* + zero residual SHIPPED LOCAL post-call; idempotence re-run no-op.
- All new tests pass (`pytest framework/tools/loam/tests/test_AC_BACKFL.py -v` → all GREEN).
- All 11 existing v0.7.3 BACKFL tests continue to pass.
- All 60+ release-CLI tests (existing + new) GREEN; no regressions.

`outcome-altitude: false` — implementation-altitude AC (test against function signature + canonical-fixture; not a real-execution probe against the production binary).

### AC.BACKFL2.6 — Outcome-altitude probe (`loam release v0.7.4 --dry-run` against this plan-doc + state)

**What:** Real-execution probe against the production CLI binary. After AC.BACKFL2.{1-5} land and the v0.7.4 plan-doc is in place + STATE.md row + roadmap row both carry the canonical SHIPPED-LOCAL pre-image (with all 4 gap-surfaces present), run `loam release v0.7.4 --dry-run` from the repo root. The pre-publish gates report GREEN; the dry-run output includes a `DRY-RUN: would apply post-publish backfill` summary block naming all 4 gap-edits in human-readable form (leading-title flip + STATE.md seal SHA backfill + STATE.md COMMIT/APPLY backfill + roadmap COMMIT/APPLY backfill, on top of the v0.7.3 baseline edits).

**Acceptance:**
- `loam release v0.7.4 --dry-run` runs to completion without crashing.
- Pre-publish gates all GREEN (HARD smoke + acs-verified + state-shipped + clean-tree + branch-main + seal-reachable, plus any v0.7.1+ additions).
- Output's `DRY-RUN: would apply post-publish backfill` block names the v0.7.4 gap-edits explicitly (the title-flip + STATE.md placeholder backfill + commit-graph-discovered SHAs).
- Probe is documented in `docs/experiments/v0-7-4-hard-smoke.md` with the literal CLI invocation + the gate report excerpt + the dry-run backfill preview block.
- Probe correctly identifies the discovered (source_edit_sha, apply_sha) for v0.7.4's own seal commit.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` — invokes production entry-point against realistic input (this very plan-doc + the live STATE.md + the live roadmap). Risk band: **production-facing release-CLI** — defect-closure on a publish-time path; HARD per-cycle REQUIRED.

### AC.BACKFL2.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (AC.BACKFL2.{1,2,3} — extend module)
- `framework/tools/loam/src/loam_cli/release/runner.py` (AC.BACKFL2.4 — verify idempotent-noop branch passes seal_sha; touch only if needed)
- `framework/tools/loam/tests/test_AC_BACKFL.py` (AC.BACKFL2.5 — new tests added to existing module)
- `framework/tools/loam/tests/conftest.py` — only if AC.BACKFL2.5 needs a fixture extension; otherwise untouched
- `docs/plans/v0-7-4-auto-backfill-completeness.md` (this file — universal-admission)
- `docs/plans/v0-7-4-auto-backfill-completeness.manifest.yaml` (universal-admission)
- `docs/STATE.md` (universal-admission; v0.7.4 SHIPPED LOCAL rollup)
- `docs/release-roadmap.md` (universal-admission; v0.7.4 §2-shipped row)
- `docs/experiments/v0-7-4-hard-smoke.md` (universal-admission; AC.BACKFL2.6 writeup)
- `docs/release-process.md` (universal-admission; gates table coverage update — informative)
- `docs/FUTURE_IDEAS_DRAFT.md` (universal-admission; capture-and-resolve the v0.7.3-spec-incomplete finding)
- Component sidecar + narrative file (managed by `loam amend apply` / `loam amend seal`)

Sidecar advances per sealed-component-cycle ritual via `loam amend apply` then `loam amend seal`.

## §5 — Decisions builder rules at build time

- **D-BACKFL2.1.a (leading-title pattern):** STATE.md row's leading title is `- **<date>** — **<version> <CLASS> SHIPPED LOCAL**` where `<CLASS>` is `MINOR` / `PATCH` / `minor` / `patch` (case-insensitive). Builder uses regex `re.compile(r"\*\*" + re.escape(version) + r"\s+(MINOR|PATCH|minor|patch)\s+SHIPPED LOCAL\*\*")` to locate; preserves the captured `<CLASS>` casing in the replacement (`SHIPPED LOCAL` → `SHIPPED PUBLIC`). If the regex fails to match, surface a hint, leave the row alone (defensive — same as v0.7.3's STATE.md trailing-sentence pattern). Roadmap §2 row's third pipe-cell `Single-cycle PATCH:` / `Single-cycle MINOR:` is NOT a SHIPPED-LOCAL claim — out of AC.BACKFL2.1 scope.
- **D-BACKFL2.2.a (STATE.md TBD-AT-* helper shape):** mirror v0.7.3's `_backfill_tbd_placeholders(row, tag, tag_sha, seal_sha)` — same replacement form (backtick-wrapped 7-char SHA). Apply against the STATE.md bullet body using a `_state_md_row_pattern(version)` regex that captures the full bullet line (`^-.*\b<version>\b.*$` multiline, picking the most-recent-date row when multiple match — defensive against future amendments adding multiple rows for the same version).
- **D-BACKFL2.3.a (commit-graph walk shape):** use `subprocess.run(["git", "log", "-1", "--pretty=%B", <sha>], cwd=repo_root, ...)` for both seal-message + apply-message reads. Parse the apply SHA from seal message via `re.compile(r"chore\(seals\):\s+\S+\s+—\s+\S+\s+at\s+([0-9a-f]+)")` (the canonical form across 10+ historical seals: `chore(seals): <slug> — <component-list> at <apply-sha>`). Parse source-edit SHA from apply message via `re.compile(r"chore\(amend\):\s+\S+\s+manifest\+apply\s+—\s+.+?BASELINE\+sidecar\s+bump\s+to\s+([0-9a-f]+)")` (canonical form across 10+ historical applies). Defensive: any subprocess failure / regex miss returns (None, None) + hint; never crash.
- **D-BACKFL2.3.b (discovery is opt-in, not mandatory):** when `_discover_source_edit_and_apply_shas` returns (None, None), the existing v0.7.3 TBD-AT-SEAL + TBD-AT-TAG backfill still runs against the row. The TBD-AT-COMMIT + TBD-AT-APPLY placeholders are left alone + a hint surfaces (mirror of v0.7.3's existing graceful-degradation design).
- **D-BACKFL2.4.a (existing-test preservation):** all 11 v0.7.3 BACKFL tests use a hand-authored seal SHA (`abc1234567890def`) that does NOT correspond to a real git commit in the test fixture's tmp_path repo. So the AC.BACKFL2.3 discovery will return (None, None) when called against those fixtures — which means existing tests will continue to pass without modification (graceful-degradation per D-BACKFL2.3.b). The new AC.BACKFL2.3 test (`test_apply_backfill_discovers_source_edit_and_apply_from_seal_commit`) is the only test that constructs a real commit-graph fixture; it sets up a tmp_path git repo with seal + apply + source-edit commits matching the canonical message forms.
- **D-BACKFL2.5 (fixture choice):** mirror v0.7.3's D-BACKFL.5 default — author each new test's fixture inline or via small additive helpers in `test_AC_BACKFL.py`; do not extend `conftest.py`. The existing `_state_md_with_shipped_local` helper gets a `with_v074_gap_surfaces=False` keyword arg (default False preserves existing-test behavior; True extends the body with the leading title + TBD-AT-COMMIT + TBD-AT-APPLY surfaces). Same shape for `_roadmap_with_shipped_local_row`.
- **D-BACKFL2.6 (probe location):** the `loam release v0.7.4 --dry-run` invocation lands in `docs/experiments/v0-7-4-hard-smoke.md` §1 (canonical HARD smoke writeup location). Captures: invocation command, exit code, full gate-report stdout, dry-run backfill preview block.
- **D-BACKFL2.7 (runner idempotent-noop branch verification):** verify `runner.py:279-281` already passes the discovered seal_sha (it doesn't — it passes `dry_run=False` without `seal_sha=...`). The idempotent-noop branch at `runner.py:261-315` runs the backfill but doesn't extract seal_sha first. AC.BACKFL2.4 verification: the idempotent-noop branch should also be able to discover (source_edit, apply) from the tag's underlying commit. Builder rules: extract seal_sha in the idempotent-noop branch the same way as in the publish-success branch (via `gates._extract_seal_sha(roadmap_body, version)`) before calling `apply_backfill`, OR rely on `apply_backfill`'s own internal seal_sha discovery via `gates._extract_seal_sha` when `seal_sha=None`. Either correct; recommend the second (less code duplication; the function already has the fall-back).

## §6 — Out of scope (explicit)

- **Path-A (extend `loam amend seal` to record SHAs at seal-time)** — see AC.BACKFL2.3 ruling. Cross-component, contract-changing; not pursued in v0.7.4.
- **Schema-version bump on manifest** — adding a `source_edit_sha` / `apply_sha` field to the manifest would be path-A-adjacent. Out of scope.
- **Retroactive backfill of historical versions' TBD-AT-COMMIT / TBD-AT-APPLY** (v0.4.2 / v0.4.3 / v0.5.0 still carry these in roadmap §2; v0.7.3 row had them; manually backfilled at `cb71ca5`). Out of scope; auto-backfill operates on the just-published version per call.
- **`Pre-publish state-update enforcement gate`** — the v0.6.0 `state-shipped` gate verifies STATE.md mentions the version + SHIPPED, but doesn't verify the row carries the canonical pre-publish shape (leading `**SHIPPED LOCAL**` title + trailing `SHIPPED LOCAL — owner gates publish.` sentence + TBD-AT-* placeholders). Tightening the gate to enforce the canonical pre-image is v0.8.0+ work (FIDRAFT capture).
- **Walking back from seal commit to find publish-prep / corrective commits** (e.g., v0.7.3's `cb71ca5` + `5c3f7ac` + `59c3b24`). Those are post-source-edit human-authored commits that don't fit the canonical apply-message pattern; out of scope. The discovery covers the (source-edit → apply → seal) chain only.
- **Gh release notes auto-update** — v0.6.0 ships gh release create with auto-generated notes; not touched here.
- **Anthropic API key paths** (per architectural constraint, never).
- **Multi-LLM via OpenRouter** (per architectural constraint, backlog only).

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.BACKFL2.6 outcome-altitude probe RED. The auto-backfill function fails the dogfood probe against this plan-doc + the live STATE.md + the live release-roadmap.md. Halt; surface as F-DESIGN candidate.
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
5. Wall-clock exceeds upper band (60-120 min midpoint ~90 min) by >2× → 4 hr (matches dispatch brief's surface threshold). Halt with current state.
6. AC.BACKFL2.3 path-a vs path-b decision turns out to require cross-component changes you can't keep tight (e.g., the seal commit message form doesn't actually match the canonical regex against historical seals in production data). Halt; surface for owner ruling on path-A pivot.
7. Discovery that the leading-title regex breaks an existing test (e.g., a fixture body has `**vX.Y.Z minor SHIPPED LOCAL**` form and the regex doesn't preserve casing). Halt; surface; tighten the regex.
8. Discovery that the v0.7.3 BACKFL test suite starts failing under v0.7.4 changes (regression). Halt; surface; never silently change v0.7.3's behavior.
9. The backfill function tries to push a commit BEFORE the tag has been pushed (HARD HALT #7 from v0.7.3 — same invariant; sequence MUST be tag-push before backfill commit + push).
10. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.

## §8 — Dependencies

- **v0.7.3 (release-CLI auto-backfill)** — HARD. v0.7.4 extends v0.7.3's `apply_backfill` function + reuses the runner integration; v0.7.4 cannot land without v0.7.3 sealed.
- **v0.6.0 (concrete release process)** — HARD. v0.7.4 extends the v0.6.0 publish-flow's post-tag-push step.
- **v0.7.2 (release-CLI parser fix)** — SOFT. v0.7.4's outcome-altitude probe (AC.BACKFL2.6) consumes the fixed `acs-verified` parser to verify this plan-doc's §4 ACs without false-positives on cross-references.
- **v0.7.0 (`## §13 — §status` literal heading parser)** — SOFT. The plan-doc §status backfill at end-of-build uses the literal heading form per the v0.7.0 fix.
- **`docs/release-versioning-policy.md`** — SOFT. PATCH-class declaration grounded in the policy.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `BACKFL2` AC ID family choice over `V074.*`.
- **`feedback_build_forward_on_publish_pending`** — SOFT. Justifies dispatching v0.7.4 while v0.7.3 just sealed-and-published.
- **`feedback_no_amend_in_agent_dispatches`** — HARD. The post-backfill commit is a NEW commit, never `--amend`.
- **No external service dependencies.**
- **No new Python packages** (subscription-only constraint).

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — single-component PATCH; tight per-AC scope; extending an existing module + adding 5 tests + outcome-altitude probe. Defect-closure (no design exploration); confidence in outcome shape is high (Lens 4 — tight scope appropriate). v0.7.3 actuals (~77 min for the new ~430-line module + 11 tests + runner wiring) calibrates the upper bound; v0.7.4 has less code (extending an existing module + 5 tests + 1 commit-graph helper).

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 12-20 min | 16 min |
| AC.BACKFL2.1 — leading-title flip helper | 8-15 min | 11 min |
| AC.BACKFL2.2 — STATE.md TBD-AT-* helper | 8-15 min | 11 min |
| AC.BACKFL2.3 — commit-graph-walk discovery helper | 12-20 min | 16 min |
| AC.BACKFL2.4 — idempotence verification (mostly free — graceful-degradation path) | 3-8 min | 5 min |
| AC.BACKFL2.5 — 5 new tests + fixture extensions | 12-20 min | 16 min |
| AC.BACKFL2.6 — outcome-altitude probe + writeup | 8-12 min | 10 min |
| FUTURE_IDEAS_DRAFT capture-and-resolve | 2-4 min | 3 min |
| docs/release-process.md update | 2-4 min | 3 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 12-20 min | 16 min |
| **Total v0.7.4 build** | **79-138 min (~1.3-2.3 hr)** | **~107 min (~1.8 hr)** |

The dispatch brief estimates 60-120 min midpoint ~90 min. Plan-time revision: **79-138 min midpoint ~107 min**. Defensible: extend-existing-module + 5 tests is faster than new-module + 11 tests (v0.7.3); the commit-graph-walk helper is the most novel piece (~25 lines + tests). Defect-closure shape with high confidence in scope keeps the band tight; midpoint sits well below the 4-hr HARD HALT threshold.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- Telegram 10680 (owner directive 2026-05-10) — option A ratification ("full structural elimination of SHIPPED-LOCAL → SHIPPED-PUBLIC manual touchpoints"). The dispatch authority for v0.7.4.
- `88964cb` (commit 2026-05-10, v0.7.3 auto-backfill execution) — the dogfood that surfaced the 4 gaps; commit message states `docs(release): v0.7.3 post-publish backfill — SHIPPED PUBLIC` but the diff applied only 3 edits / 2 files; gap-pattern visible by comparison to corrective commits `cb71ca5` + `5c3f7ac` + (the 88964cb itself's missed-leading-title).
- `cb71ca5` (commit 2026-05-10, v0.7.3 publish-prep — backfill source-edit + apply + corrective SHAs) — the manual touch-up that closed gaps 3 + 4 + part of gap 2 for v0.7.3; v0.7.4 makes this manual step structural.
- `5c3f7ac` (commit 2026-05-10, v0.7.3 publish-prep — backfill seal SHA for seal-reachable gate) — the manual touch-up that closed gap 2 (roadmap-side) for v0.7.3.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground.
- `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (existing 581-line module from v0.7.3) — the surface v0.7.4 extends.
- `framework/tools/loam/src/loam_cli/release/runner.py` lines 261-315 (idempotent-noop branch) + 387-417 (publish-success branch) — the runner integration v0.7.4 verifies idempotence across.
- `framework/tools/loam/tests/test_AC_BACKFL.py` (existing 504-line test module from v0.7.3) — the test corpus v0.7.4 extends.
- `docs/plans/v0-7-3-release-cli-auto-backfill.md` — predecessor PATCH-class plan-doc; structural template for §1-§14 sectioning + ground for D-BACKFL.* decisions v0.7.4 mirrors.
- Memory rules: `feedback_scope_descriptive_ac_ids.md` (AC.BACKFL2.* not AC.V074.*), `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_no_anthropic_api_key.md` (HARD HALT #10), `feedback_subagent_odd_violation_halt.md` (HARD HALT #2), `feedback_duration_estimation_rubric.md` (§9), `feedback_build_forward_on_publish_pending.md` (§8 build-forward justification), `feedback_test_outcome_altitude_required.md` (AC.BACKFL2.6 risk-band), `feedback_locked_design_not_license_for_bad_outcomes.md` (the v0.7.3 spec was incomplete — this plan revisits the spec rather than living with the bad outcome).

## §13 — §status

(Pending — backfilled at end-of-build with AC verdict matrix + AI-time actuals + commit SHAs + halt-and-surface findings.)

## §14 — Method decisions

The plan-doc's §5 names the build-time decisions (D-BACKFL2.1.a leading-title pattern, D-BACKFL2.2.a STATE.md TBD-AT-* helper, D-BACKFL2.3.a commit-graph walk regex, D-BACKFL2.3.b graceful-degradation, D-BACKFL2.4.a existing-test preservation, D-BACKFL2.5 fixture choice, D-BACKFL2.6 probe location, D-BACKFL2.7 runner idempotent-noop seal_sha extraction). Build-time deviations from these rulings are surfaced here at end-of-build.

### Commit SHAs

- Plan-doc + manifest authoring: TBD-AT-COMMIT
- Source-edit batch (post_publish_backfill extension + tests + release-process update + FIDRAFT + STATE + roadmap + smoke writeup): TBD-AT-COMMIT
- Apply auto-commit (BASELINE + sidecar bump): TBD-AT-APPLY
- Seal commit (deterministic seal): TBD-AT-SEAL

### Build-time decision deviations

(Pending — backfilled at end-of-build with any deviations from §5 rulings + the surfacing rationale.)
