# Amendment #143 — Tier 1 retroactive sweep follow-up: tighten heuristic + widen downstream globs + live sweep (closes #134 §16 finding #6)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 by `loam-plan-author` subagent per dispatch from owner (TG 11808 / 11837 / 11854).
**Working directory:** `/Users/lukeivers/loam/`.
**Predecessor (load-bearing):** amendment #142 publish-state commit `b278cc6a08b5c7ff127036d009b8d7ae22a3c2c6` (current HEAD post-publish — `docs(readme): bump current-release to v0.12.19 (amendment #142 plan-author SKILL hygiene)`). Per Scope B of amendment #142's own walk-forward discipline (`D-PASH.BASELINE-WALK`): walked forward from #142's seal `f99827d`; found NO `chore(amend-fixup):` commits between `f99827d` and `b278cc6`; defaulted BASELINE to the publish-state commit `b278cc6`. **Verified by direct `git rev-parse HEAD` + `git log --oneline f99827d..b278cc6 --grep='^chore(amend-fixup)'`.**
**Parent capture:** amendment #134 §16 finding #6 (`docs/plans/sealed/amendment-134-fbm-tier1-foundations.md:357-363`) — the retroactive sweep was deferred until (a) the heuristic is refined to handle older slug-naming conventions, AND (b) downstream consumers are updated to walk both `docs/plans/` and `docs/plans/sealed/`. This amendment closes both gates plus the live-tree sweep itself.
**Quality bar:** multi-component amendment (`dev-sdlc` for sweep mechanism + `loam` CLI for release-gate consumer + `heavy-b-migrate` for amendment-AC consumer + `primary-persona` for session-start consumer). Three AC sub-families (AC.T1RS.HEURISTIC / .GLOB / .SWEEP) per scope + one outcome-altitude smoke (AC.T1RS.S) exercising the full tightened-heuristic → widened-glob → live-sweep path end-to-end against the canonical tree (or a fixture mirror of it).

---

## §1. Objective / Summary / TL;DR

Close amendment #134's §16 finding #6 — the retroactive sweep deferred at #134's seal because (a) the seal-commit attribution heuristic produced a 35% false-negative classification rate against the live corpus, AND (b) downstream production code globs `docs/plans/<slug>*.md` without traversing into `docs/plans/sealed/`. Three merged scopes:

1. **Scope A — tighten the seal-commit attribution heuristic in `plan_archive.py`.** The current narrow heuristic (`git log --grep=^chore(seals): --grep=<slug> --all-match`) misses sealed amendments whose seal-commit subject names a different slug than the plan-doc filename — e.g., `amendment-22-pos-amend-cli.md` whose seal commit `60dc0c6` is subject `chore(seals): pos-amend-cli-and-universal-paths seal — ...`. **Fix:** add a second-pass strategy that, when the narrow grep returns zero matches AND the plan-doc filename matches `amendment-<NN>-<body>`, retries with `--grep=<body>` (the slug tail after `amendment-NN-`); accept the match iff exactly one seal commit results. Plus a third-pass strategy keyed on `amendment #<NN>` (with space) in any commit message, filtered to `chore(seals):` subjects. Ambiguous (multi-match) plan-docs stay in place per the §134 halt-trigger #5 contract.

2. **Scope B — widen downstream consumers to walk BOTH `docs/plans/` AND `docs/plans/sealed/`.** Pre-flight identified FOUR production-code consumers (the brief named two; verification surfaced two additional — see §16 finding #1):
   - `framework/tools/loam/src/loam_cli/release/gates.py:189` — `_find_plan_doc()` globs `docs/plans/<slug>*.md` for release-gate AC-verification.
   - `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/amendment_acs.py:88` — `discover_amendment_plans()` iterates `docs/plans/` for Phase γ tracker extraction.
   - `framework/primary-persona/src/loam/primary_persona/session_start_gate.py:163` — `enumerate_amendments_in_flight()` globs `docs/plans/amendment-*.md` for session-start digest.
   - `plugins/dev-sdlc/hooks/bash_guard.py:236` — globs `docs/plans/*.manifest.yaml` for the bash-guard dry-run probe.

   **Fix:** introduce a shared helper `iter_all_plan_docs(repo_root, *, include_sealed=True)` (and a sibling `iter_all_manifests` for the bash-guard case) that walks BOTH directories; route each of the four consumers through it. **Method-decision per D-T1RS.GLOB-UPDATE:** shared helper not inline-duplicate-glob in each consumer (DRY; one source of truth for the traversal semantics).

3. **Scope C — run the (now-tightened) sweep against the live canonical tree as one bookkeeping commit.** After Scopes A + B land, invoke `sweep_sealed_plan_docs(repo_root, dry_run=False)` once on canonical; the output is a single `chore(retroactive-sweep):` commit moving the cleanly-attributable plan-docs (and sibling manifests) into `docs/plans/sealed/`. Ambiguous + still-in-flight plan-docs stay put per the existing contract. **Method-decision per D-T1RS.LIVE-SWEEP-TIMING:** sweep runs at this amendment's seal time as a separate corrective commit AFTER the seal commit, NOT during apply. Reason: keeping the source-edit + apply + seal cycle clean from bookkeeping operations preserves the seal-diff window's clarity; the sweep is a one-shot operator-driven action that this amendment's plan-doc records but the seal's commit ladder doesn't include. The sweep commit is the FINAL commit of this amendment's ladder; the plan-doc + manifest are themselves archived BY that sweep commit (T1.4 dogfood — this very plan-doc moves to `docs/plans/sealed/` as part of Scope C's execution).

**Shape decision: merged single amendment** (per F4 scope-confidence — Scope C cannot land WITHOUT Scopes A + B; splitting them sequences as A→apply→seal→B→apply→seal→C→sweep with three apply+seal cycles, vs the merged form's one apply+seal+sweep). All three scopes are scope-disjoint at the AC family level (.HEURISTIC / .GLOB / .SWEEP). Multi-component fence (`dev-sdlc` + `loam` + `heavy-b-migrate` + `primary-persona`) follows the four downstream consumers identified at pre-flight.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T~16:14Z | Build-strategy delegation (the Tier 1 retroactive-sweep follow-on is build-strategy territory). |
| TG 11837 | 2026-05-21T~19:00Z | Durable-autonomy directive — proceed without per-step ratification on in-scope authorized work. |
| TG 11854 | 2026-05-21T~22:00Z | Re-evaluation directive — re-survey deferred-scope queue + dispatch the next persona-eligible item. |
| Implicit (TG 11873) | 2026-05-21T~22:50Z | Persona dispatched the Tier 1 follow-on as the next persona-eligible item in the queue. |

**Pre-flight verification (Tier-0 at canonical HEAD `b278cc6`, 2026-05-21):**

- **`git rev-parse HEAD` returned `b278cc6a08b5c7ff127036d009b8d7ae22a3c2c6`.** Full SHA verified by direct `git rev-parse` call (no transcription from brief). Recorded as BASELINE in the paired manifest. **Verified by direct shell invocation.**
- **`git log --oneline f99827d..b278cc6 --grep='^chore(amend-fixup)'` returned empty.** No fixup commits between #142 seal `f99827d` and publish-state `b278cc6`; BASELINE walk-forward (per #142's Scope B) lands on the publish-state commit. **Verified.**
- **Existing in-flight plan-doc count (`ls docs/plans/*.md | wc -l`) = 298.** Includes `.builder-plan.md` companions (~40); the sweep skips them via `_AMENDMENT_PLAN_RE` style filter (see method note D-T1RS.HEURISTIC.4).
- **Existing sealed plan-doc count (`ls docs/plans/sealed/*.md | wc -l`) = 9** (post-#134 amendments #134-#142 inclusive).
- **Current `plan_archive.py` heuristic Tier-0 read:** `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/plan_archive.py:43-71` — narrow `--all-match` form on `^chore(seals):` AND `<slug>`. **Verified by direct read.**
- **Empirical heuristic stats at canonical HEAD `b278cc6` (Tier-0 — ran Python harness against the live repo, see §16 finding #2 for the stratification numbers):**
  - 138 plan-docs with narrow clean-match (exactly one seal commit).
  - 16 plan-docs with narrow ambiguous (multiple seal commits matching).
  - 13 plan-docs with NO narrow match BUT recoverable by Scope A's `<body>` second-pass strategy.
  - 88 plan-docs with no signal under either strategy (81 non-amendment-shape + 7 amendment-shape that have no traceable seal commit by any pattern).
  - Total non-companion plan-docs evaluated: 255.
- **Four downstream consumers identified by `grep -rn 'plans_dir\|docs/plans.*\.glob\|docs/plans.*iterdir' framework/ plugins/ --include='*.py'` (filtered to production code):**
  - `framework/tools/loam/src/loam_cli/release/gates.py:186-192` — `plans_dir.glob(f"{slug}-*.md")` + `plans_dir.glob(f"{slug}.md")`. **Verified by direct read.**
  - `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/amendment_acs.py:88-108` — `plans_dir.iterdir()` filtered by `_AMENDMENT_PLAN_RE`. **Verified by direct read.**
  - `framework/primary-persona/src/loam/primary_persona/session_start_gate.py:171-175` — `plans_dir.glob("amendment-*.md")`. **Verified by direct read.**
  - `plugins/dev-sdlc/hooks/bash_guard.py:234-237` — `plans_dir.glob("*.manifest.yaml")` for dry-run manifest enumeration. **Verified by direct read.**
- **No fifth production consumer found.** Verified by exhaustive grep of `framework/` + `plugins/` for `plans_dir`, `PLANS_DIR_REL`, `docs/plans/.*\.md`, and `docs/plans/.*\.manifest`. Test fixtures + module docstrings carry path strings but do not glob at runtime; those are out of scope.
- **Existing test fixtures for the sweep:** `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_APS_3_retroactive_sweep.py` exercises the narrow heuristic against a tmpfs git repo with synthetic seal commits. Scope A adds tests in the same module exercising the second-pass and third-pass strategies; the fixture pattern composes (use `_commit_seal()` plus a new helper that crafts a seal-commit-by-body-slug-only).
- **Pre-existing 4 RED tests** rooted in oversized `smoke_outcome` field at `docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml` (575 chars vs 200 cap) — persist; out of scope per #140 §16 #6 + #141 §16 #5 + #142 §6 halt-trigger #7. Tracked separately as `ws-loam-amend-oversized-manifest-field-cleanup`.
- **One pre-existing untracked plan-only file** in working tree: `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` (unrelated workstream, pending owner ratification). Admitted at apply time via `--allow-untracked-globs` per the #140/#141/#142 admission precedent.

---

## §2. Predecessors / context

- **Amendment #134** (FBM Tier 1 foundations, sealed at `6125003`). Established the T1.4 archive convention (`docs/plans/sealed/<slug>.md`), the `plan_archive.py` sweep module, and the narrow `--all-match` heuristic. Surfaced finding #6: deferred live-sweep until heuristic + downstream consumers caught up. THIS amendment closes that deferral.
- **Amendment #142** (plan-author SKILL hygiene, sealed at `f99827d` + publish-state `b278cc6`). Predecessor seal commit; predecessor publish-state IS the canonical HEAD this amendment baselines against. #142 codified the `docs/plans/sealed/<slug>.md` `narrative.target` form in SKILL prose; this amendment exercises that form at its own seal (dogfood: this plan-doc + manifest archive to `docs/plans/sealed/` as part of Scope C's live sweep).
- **No other amendment between #134 and #143 has touched the sweep heuristic OR downstream plan-doc globs.** Verified by `git log --all --oneline --grep='plan_archive\|sweep\|docs/plans/sealed'` since the #134 seal.

---

## §3. Scope

**In-scope (the three merged sub-scopes):**

**Scope A — tighten the seal-commit attribution heuristic:**
- Patch `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/plan_archive.py`:
  - Extract the seal-commit-search into a helper that runs three strategies in order. **Strategy 1 (existing):** `--grep=^chore(seals):` AND `--grep=<full-slug>` `--all-match`. **Strategy 2 (new):** if Strategy 1 returns zero, AND the slug matches `^amendment-\d+-(.+)$`, retry with `--grep=^chore(seals):` AND `--grep=<body-slug>` `--all-match` (the body-slug being the portion after `amendment-NN-`). **Strategy 3 (new):** if Strategy 2 returns zero, AND the slug matches `^amendment-(\d+)-`, search `--grep=amendment #\d+` filtered for `chore(seals):` subjects + filtered to the matching N. Accept only when EXACTLY ONE seal commit results from the first non-empty strategy.
  - Ambiguous (multi-match within ANY single strategy) plan-docs continue to be left in place per the #134 contract.
  - The helper is exported as `_find_seal_commit_for_slug` (or equivalent) so the tests can exercise it directly.
- Patch `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_APS_3_retroactive_sweep.py` to add the new strategy fixtures. Add new file `test_AC_T1RS_HEURISTIC_*.py` for the tightened-heuristic ACs (keeps the new tests scope-tagged distinctly from #134's APS family).

**Scope B — widen downstream consumers via shared helpers:**
- Introduce shared helpers in a new module `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/plan_locator.py` (or extend `plan_archive.py` if the helper is naturally co-located):
  - `iter_all_plan_docs(repo_root: Path, *, include_sealed: bool = True) -> Iterator[Path]` — walks both `docs/plans/*.md` and `docs/plans/sealed/*.md`; yields each plan-doc path once.
  - `iter_all_manifests(repo_root: Path, *, include_sealed: bool = True) -> Iterator[Path]` — same shape for `*.manifest.yaml`.
  - `find_plan_doc_by_slug_glob(repo_root: Path, slug_prefix: str) -> Optional[Path]` — replicates the gates.py `glob(f"{slug}-*.md") + glob(f"{slug}.md")` semantics across both directories; deterministic ordering (sealed FIRST when ambiguous, since sealed plans are the "canonical" archive; see method note D-T1RS.GLOB-PRIORITY).

  **Method-decision per D-T1RS.GLOB-LOCATION:** new module `plan_locator.py` under `loam_amend`, not `loam_cli`. Reason: `loam_amend` is the canonical home for plan-doc archive semantics (per #134's `plan_archive.py`); putting locator helpers next to archive helpers keeps the plan-doc-traversal surface cohesive. Cross-tree import: heavy-b-migrate already imports from `loam_amend` (per `verify.py:81-89`), so the import is precedented.

- Patch `framework/tools/loam/src/loam_cli/release/gates.py:_find_plan_doc()` — replace the inline `plans_dir.glob(...)` calls with `find_plan_doc_by_slug_glob(repo_root, slug)`. Preserves the existing two-path (explicit + implicit) shape; only the implicit-path glob changes.

- Patch `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/amendment_acs.py:discover_amendment_plans()` — replace the `plans_dir.iterdir()` loop with `iter_all_plan_docs(workspace_root)`, then apply the same `_AMENDMENT_PLAN_RE` filter + `.builder-plan.` exclusion + numeric-sort. Yields the same `AmendmentPlanFile` records but from both directories.

- Patch `framework/primary-persona/src/loam/primary_persona/session_start_gate.py:enumerate_amendments_in_flight()` — the semantics here are subtly different (the function name says "in flight"). **Method-decision per D-T1RS.SESSION-START-SEMANTICS:** the session-start digest enumerates SEALED amendments separately from IN-FLIGHT amendments — sealed plans are historical record, in-flight plans need owner-attention. Keep the existing function as-is (it walks `docs/plans/` only) and add a sibling `enumerate_sealed_amendments()` that walks `docs/plans/sealed/`. Both functions go through `iter_all_plan_docs(include_sealed=False)` and `iter_all_plan_docs(include_sealed=True)` respectively (filtering by the `amendment-*` prefix client-side). The session-start digest's caller is updated to use the appropriate function — but this amendment SHOULD NOT modify the digest behaviour itself, only the enumeration semantics. The digest's downstream behavior stays unchanged.

- Patch `plugins/dev-sdlc/hooks/bash_guard.py` — the `*.manifest.yaml` glob at line 236 enumerates manifests for the `loam amend apply --dry-run` probe. Replace inline glob with `iter_all_manifests(workspace_root)`. Sealed manifests are still valid manifests; the dry-run probe operates correctly on either location.

**Scope C — live sweep against the canonical tree:**
- Once Scopes A + B land (source-edit commit + apply + seal commit), run a separate one-shot `loam amend sweep-archive` invocation (or direct Python: `python -c "from loam_amend.plan_archive import sweep_sealed_plan_docs; sweep_sealed_plan_docs(Path('.'), dry_run=False)"`). The output: a `chore(retroactive-sweep):` commit containing all `git mv` operations of cleanly-attributable plan-docs + sibling manifests.
- **Method-decision per D-T1RS.LIVE-SWEEP-MECHANISM:** add a thin CLI subcommand `loam amend sweep-archive [--dry-run]` to `loam-amend/src/loam_amend/cli.py` (or as a standalone command file) that invokes `sweep_sealed_plan_docs`. Reason: making the sweep a named CLI verb makes Scope C reproducible AND auditable (operators can re-run dry-run + apply against new plan-doc additions; the CLI is the durable surface). Without the CLI, Scope C is a one-shot Python invocation that's hard to re-execute later. **Trade-off:** adds CLI surface area; aligns with the existing `loam amend apply` / `loam amend seal` shape so the surface is precedented.
- The sweep commit's author is the operator; subject `chore(retroactive-sweep): live archive of plan-docs with single-match seal commits — N plans moved, M ambiguous, K in-flight (per amendment #143 Scope C)`. The commit message body lists the moved slugs grouped by attribution strategy (narrow / body / hash) for forward auditability.
- **THIS plan-doc + manifest** are themselves expected targets of the live sweep (the sweep moves `amendment-143-tier1-retroactive-sweep-followup.md` + sibling manifest to `docs/plans/sealed/`). Dogfood: this amendment's own seal commit IS its attributable seal — Strategy 1 matches.

**Out-of-scope:**

- Any change to the EXISTING narrow heuristic's semantics — Strategy 1 remains the first-pass; Scopes A's tightening is ADDITIVE (Strategies 2 + 3 only fire when Strategy 1 returns zero).
- Any change that AUTOMATICALLY moves ambiguous plan-docs (`result.ambiguous` continues to stay in place — the §134 halt-trigger #5 contract is preserved verbatim).
- Any RECURSIVE sweep — the sweep operates on direct children of `docs/plans/` only (per existing `plan_archive.py:99-106`); no traversal into `docs/plans/sealed/` (already archived) or other sub-dirs (`docs/plans/research/` if it existed).
- Modification of the `_AMENDMENT_PLAN_RE` regex shape — it stays unchanged; the new strategies parse the slug client-side without touching the regex.
- A NEW seal-commit subject convention that would tighten the heuristic differently (e.g., requiring all future seals to use `chore(seals): amendment-NN-...`). The post-#134 convention already does this; this amendment retro-fits the heuristic to the pre-#134 corpus rather than re-writing history.
- Pre-existing 4 RED tests rooted in oversized `smoke_outcome` field (per #140 §16 #6 / #141 §16 #5 / #142 §6 halt-trigger #7; tracked separately as `ws-loam-amend-oversized-manifest-field-cleanup`).
- Cross-component touches beyond the four-consumer fence (e.g., test fixtures referencing `docs/plans/` path strings in docstrings — those don't glob at runtime).
- Backfill of `lifted_from.source_commit` for the heavy-b-migrate tracker records that Phase γ wrote with `source_commit=None` (a separate FIDRAFT-class follow-up; the post-archive sweep moves the plan-docs, the tracker's source_doc reference still resolves because the slug is preserved).

---

## §4. Acceptance criteria

**AC.T1RS.HEURISTIC.1** — `sweep_sealed_plan_docs` against a tmpfs fixture with a plan-doc `amendment-22-foo.md` and a seal commit subject `chore(seals): foo seal — ...` (body-slug-only attribution, no `amendment-22-` prefix) classifies the plan-doc as cleanly-sealed and moves it. (Strategy 2 verifier.)

**AC.T1RS.HEURISTIC.2** — `sweep_sealed_plan_docs` against a tmpfs fixture with a plan-doc `amendment-50-bar.md`, a non-seal `feat(...) — amendment #50` commit, AND a `chore(seals): bar` seal commit classifies the plan-doc as cleanly-sealed via Strategy 2 OR 3 and moves it. (Strategy 2/3 verifier.)

**AC.T1RS.HEURISTIC.3** — `sweep_sealed_plan_docs` against a tmpfs fixture with a plan-doc `amendment-99-untracked.md` and NO matching commits leaves the plan-doc in `docs/plans/` (in-flight bucket). (Negative case; preserves §134 halt-trigger #5 contract.)

**AC.T1RS.HEURISTIC.4** — `sweep_sealed_plan_docs` against a tmpfs fixture with a plan-doc whose slug matches MULTIPLE seal commits (any strategy) leaves it in `result.ambiguous` for manual triage. (Ambiguous case; preserves contract.)

**AC.T1RS.GLOB.1** — `find_plan_doc_by_slug_glob` against a tmpfs fixture with a sealed plan-doc at `docs/plans/sealed/amendment-50-bar.md` (no live copy) returns the sealed path. The release-gate `_find_plan_doc` (now routed through the helper) resolves version-slug lookups for sealed plans without changing its public signature.

**AC.T1RS.GLOB.2** — `iter_all_plan_docs(include_sealed=False)` returns ONLY the live-tree plan-docs; `iter_all_plan_docs(include_sealed=True)` returns the union of live + sealed. Both `heavy_b_migrate.amendment_acs.discover_amendment_plans` and `primary_persona.session_start_gate.enumerate_amendments_in_flight` continue to surface in-flight plans (the existing call sites use the appropriate filter).

**AC.T1RS.GLOB.3** — `iter_all_manifests` returns sealed + live manifest YAML files; `bash_guard._candidate_manifests` (now routed through the helper) yields the same union; the dry-run probe operates correctly on either location's manifest.

**AC.T1RS.SWEEP.1** — `loam amend sweep-archive --dry-run` against the canonical tree (or a fixture mirror at canonical's plan-doc count) returns a `SweepResult` with `moved` > 0 (the tightened heuristic recovers at least the 13 empirically-known-recoverable cases listed in §1 pre-flight).

**AC.T1RS.SWEEP.2** — `loam amend sweep-archive` (real run) against a tmpfs fixture mirroring canonical's plan-doc layout produces ONE corrective commit moving the cleanly-attributable plan-docs; ambiguous + still-in-flight plan-docs are NOT moved; the commit subject + body match the D-T1RS.LIVE-SWEEP-MECHANISM convention.

**AC.T1RS.S** — Outcome-altitude smoke (`outcome-altitude: true`): a synthetic amendment cycle exercises all three scopes end-to-end. Setup: tmpfs git repo with (a) a pre-#134-style plan-doc + body-slug-only seal commit, (b) a #134+ style plan-doc + amendment-NN-full-slug seal commit, (c) an in-flight plan-doc (no seal), (d) an ambiguous plan-doc (two matching seals). Run `loam amend sweep-archive --dry-run` then `loam amend sweep-archive` (real). Verify: cases (a) + (b) move to `docs/plans/sealed/`; cases (c) + (d) stay in `docs/plans/`. Then invoke each of the four downstream consumers (release-gate `_find_plan_doc`, heavy-b-migrate `discover_amendment_plans`, session-start `enumerate_amendments_in_flight` + `enumerate_sealed_amendments`, bash-guard `_candidate_manifests`) against the post-sweep tree; verify each consumer finds the appropriate plan-docs in both locations per its semantics. **No pre-arrangement of partial-sweep state**; the smoke runs the production entry-points against the production sweep mechanism on a fresh tmpfs.

---

## §5. Sealed-component fence (multi-component)

Per `plugins/dev-sdlc/docs/conventions/plan-docs.md` §3 placement decisions:

- **`dev-sdlc`** (sweep mechanism + CLI subcommand) — sealed component carries the canonical sweep semantics. Source edits at `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/plan_archive.py`, new module `plan_locator.py`, CLI surface at `commands/sweep_archive.py` (or `cli.py` direct), tests at `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_T1RS_*.py`.
- **`loam`** (release-gate consumer) — sealed component for the `loam_cli.release.gates` consumer. Source edit at `framework/tools/loam/src/loam_cli/release/gates.py:_find_plan_doc`. Existing tests under `framework/tools/loam/tests/test_*.py` may need touch-up if any hard-code the inline-glob shape.
- **`heavy-b-migrate`** (Phase γ tracker consumer) — sealed component for the `loam.heavy_b_migrate.amendment_acs` consumer. Source edit at `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/amendment_acs.py:discover_amendment_plans`. Existing tests may need conftest-fixture adjustment if any plan-doc fixture writes only to `docs/plans/` (the sweep-aware iteration is order-equivalent for single-location inputs).
- **`primary-persona`** (session-start consumer) — sealed component for the `loam.primary_persona.session_start_gate` consumer. Source edit at `framework/primary-persona/src/loam/primary_persona/session_start_gate.py:enumerate_amendments_in_flight` + new sibling `enumerate_sealed_amendments`. Existing tests may need adjustment.

Multi-component fence: per the per-component `seal_test:` convention, each component's seal-diff test wraps the appropriate sub-tree. The four components are scope-disjoint at the file level (no shared edits within source files), so the seal-diff window per component is clean.

`extra_allowed_prefixes` (per component):
- `dev-sdlc`: `["docs/plans/", "docs/plans/sealed/"]` (Scope C's sweep operates on both; admitting them at apply time covers the seal commit's `git mv` operations).
- `loam`, `heavy-b-migrate`, `primary-persona`: empty (only the named source file changes).

`universal_paths` (top-level manifest): `prefixes: ["docs/plans/"]` (matches #142 manifest's shape; covers this plan-doc + manifest + the live sweep's `git mv` targets).

---

## §6. Halt triggers (in-flight)

1. **HALT** if Scope A's empirical recovery against canonical drops to ≤5 plan-docs (the empirical pre-flight measured 13; if the build-time re-measurement is meaningfully lower, the tightening's value-add evaporates and the §16 finding #2 numbers must be re-investigated).
2. **HALT** if a fifth production-code downstream consumer is discovered during Scope B's source edits (would expand the fence beyond what's named here; surface for dispatcher ratification before extending).
3. **HALT** if the live sweep (Scope C) would move >100 plan-docs in a single commit (the pre-flight empirically measured 138 + 13 = 151 cleanly-attributable cases; if the actual count balloons higher, surface for dispatcher review — a >100-file `git mv` commit is a significant tree restructure and deserves explicit pause-and-confirm).
4. **HALT** if any of the four downstream consumers' tests RED after the helper refactor (suggests semantic drift, not the API-compatible re-routing this amendment intends).
5. **HALT** if the §134 halt-trigger #5 contract is observably violated — i.e., if any ambiguous-bucket plan-doc moves automatically. The contract is preserved verbatim by this amendment; a regression here is a halt.
6. **HALT** if `loam amend seal --plan-doc` § 14 SHA backfill fails (pre-existing #141-decoupled path should fire cleanly; #142 dogfooded it on a similar plan-doc shape).
7. **HALT** if any of the four pre-existing RED tests (oversized smoke_outcome) starts producing a NEW failure mode rooted in the heuristic or glob changes (would suggest blast-radius beyond the four named components).

---

## §7. Ship shape

Per `plugins/dev-sdlc/docs/conventions/amendment-cycle.md` commit ladder:

1. **Plan-doc + manifest commit** (`docs(plans): amendment #143 plan-doc + manifest`) — this commit. Authored by `loam-plan-author`.
2. **Source-edit commit** (`feat(dev-sdlc, loam, heavy-b-migrate, primary-persona): tighten retroactive sweep heuristic + widen downstream globs + add live-sweep CLI (amendment #143, AC.T1RS.HEURISTIC.{1..4} + AC.T1RS.GLOB.{1..3} + AC.T1RS.SWEEP.{1,2} + AC.T1RS.S)`) — per #142 Scope C's discipline, this commit lands BEFORE `loam amend apply`. Includes:
   - `plan_archive.py` Strategy 2 + 3 helper additions.
   - New `plan_locator.py` module + helpers.
   - `release/gates.py` re-route to helper.
   - `heavy_b_migrate/amendment_acs.py` re-route to helper.
   - `primary_persona/session_start_gate.py` + new `enumerate_sealed_amendments` helper.
   - `bash_guard.py` re-route to helper.
   - New CLI subcommand `loam amend sweep-archive` registration.
   - New test files `test_AC_T1RS_HEURISTIC_*.py` + `test_AC_T1RS_GLOB_*.py` + `test_AC_T1RS_SWEEP_*.py` + `test_AC_T1RS_S_end_to_end_smoke.py`.
3. **`loam amend apply` auto-commit** (`chore(amend): retroactive sweep follow-on apply (amendment #143)`) — bumps `BASELINE`/`SEAL_COMMIT` literals across the four components.
4. **`loam amend seal --plan-doc docs/plans/amendment-143-...md` deterministic seal commit** (`chore(seals): amendment-143-tier1-retroactive-sweep-followup — dev-sdlc+loam+heavy-b-migrate+primary-persona at <sha>`) — touched-component + cross-component sweep tests; T1.4 archives this plan-doc + manifest to `docs/plans/sealed/` (via the existing post-#134 archive path, not the new live-sweep CLI). §14 backfill auto-fires via #141's decoupled path.
5. **§14 backfill commit** — auto-embedded by `_finalize` step (h) per #141's decoupled path.
6. **Live-sweep corrective commit** (`chore(retroactive-sweep): live archive of plan-docs with single-match seal commits — N moved, M ambiguous, K in-flight (per amendment #143 Scope C)`) — operator-typed `loam amend sweep-archive` invocation. NOT part of the seal commit's diff window (Scope C is bookkeeping-class, not source-class). This is the FINAL commit of the amendment's ladder.

---

## §8. Out of scope (extended notes)

(See §3 "Out-of-scope" — repeated here for completeness with cross-references.)

- The 4 pre-existing RED tests rooted in oversized `smoke_outcome` field. Tracked as `ws-loam-amend-oversized-manifest-field-cleanup`.
- A `MAX_SMOKE_OUTCOME` schema audit that prunes oversized fields from other manifests (separate workstream).
- A NEW seal-commit subject convention (would require historical re-writing, hazardous).
- Phase γ's `lifted_from.source_commit` backfill from git log for the heavy-b-migrate tracker records (separate FIDRAFT-class follow-up).
- Auto-graduation of in-flight plan-docs that have no traceable seal commit but ARE empirically completed (would require a semantic-shape parser, not a git-log search — well outside this amendment's mechanical scope).
- Cross-tree sweep operations (e.g., sweeping plan-docs in a derived workspace's `docs/plans/`) — scope here is canonical-tree-only.

---

## §10. F2 Ruthless Feedback (honest doubts)

1. **Recovery rate uncertainty.** The empirical pre-flight measured 13 plan-docs recovered by Scope A's Strategy 2; this is ~5% of the 255 non-companion plan-docs and ~15% of the 88 still-in-flight bucket. The brief's claim of "146 false-negatives" (from #134's measurement) was significantly higher; the discrepancy is explained by amendments landing between #134's measurement and this amendment's pre-flight (#135-#142 are now legitimately sealed, so they no longer appear as false-negatives — they're true-positives). The 88 remaining no-signal plan-docs (81 non-amendment + 7 amendment-shape) are largely PRE-AMENDMENT-NUMBERING-ERA plan-docs (`telegram-5-fix`, `programbench-revival-real-pb`, etc.) whose seal commits used the slug verbatim — these ARE caught by the narrow heuristic. The 88 truly-no-signal cases are plans that have NO seal commit at all (genuinely in-flight OR abandoned). **The tightened heuristic is correct but doesn't solve the whole problem.** A separate workstream may be needed to triage the 88 plan-docs by hand or by a semantic-shape parser; this amendment surfaces the gap without closing it.

2. **Scope C's blast radius.** A `chore(retroactive-sweep):` commit moving ~150 plan-docs + manifests is a large tree restructure. The post-sweep `docs/plans/` directory will be dramatically smaller (the in-flight bucket shrinks from 298 to ~90); the post-sweep `docs/plans/sealed/` will be dramatically larger (9 → ~150). This IS the intended outcome but it visually changes the repo at scale. Halt-trigger #3 surfaces this; the build agent should pause and surface the dry-run count before the real-run.

3. **Session-start digest semantics drift.** D-T1RS.SESSION-START-SEMANTICS preserves the existing `enumerate_amendments_in_flight` semantics (live-tree only) but adds `enumerate_sealed_amendments`. The session-start digest's CALLER currently uses only `enumerate_amendments_in_flight`; this amendment does NOT modify the caller. If the digest's downstream behavior IS meant to surface sealed amendments too (e.g., "here are the N amendments sealed since last session"), that's a separate amendment. F2 surface: this amendment may leave a gap that a future digest-enhancement amendment closes.

4. **Helper-module location.** D-T1RS.GLOB-LOCATION places the new helpers under `loam_amend/plan_locator.py`. An alternative is `loam/plan_locator.py` (in the unified CLI tree); this would avoid the cross-tree import in `loam_cli.release.gates`. Trade-off: `loam_amend` is the canonical plan-doc home (per `plan_archive.py`) but `loam_cli` is the CLI consumer's natural import root. Recommend `loam_amend` per the cohesion argument; surface this for dispatcher confirmation if Scope B's build agent finds it awkward.

5. **CLI subcommand vs Python-only invocation.** D-T1RS.LIVE-SWEEP-MECHANISM recommends a new `loam amend sweep-archive` subcommand. The alternative is invoking `sweep_sealed_plan_docs` from a Python shell or operator-typed `python -c`. Trade-off: CLI surface is durable + reproducible + auditable; Python invocation is ephemeral. The CLI adds ~50-80 lines of `argparse` + `subparser` registration. Recommended.

6. **No HARD smoke against rd-automation requested at this minor.** The Eric-regression HARD smoke (per `feedback_hard_smoke_per_minor_before_publish`) gates per-minor publish, not per-cycle seal. This amendment seals locally then defers publish gate to owner. If owner approves publish, the HARD smoke runs at the v0.12.20 (or whatever minor) gate; this plan-doc DOES NOT block on it.

---

## §14. Method-decision register

(Per `plugins/dev-sdlc/docs/conventions/plan-docs.md`. Method choices are the builder's call per ODD §1.1; the register documents the rationale a session-fresh persona needs to understand the build.)

- **D-T1RS.MERGE** — three FIDRAFT scopes merged into a single amendment. AC families are scope-disjoint (.HEURISTIC / .GLOB / .SWEEP); the three scopes have a CAUSAL ordering (C depends on A + B), but all three touch the same cohesive surface (the plan-doc archive mechanism + its downstream consumers). Merge saves two apply + seal cycles vs three sequential amendments. SHA backfill: TBD at seal time.

- **D-T1RS.HEURISTIC** — three-strategy fallback chain (current narrow / body-slug second-pass / `amendment #NN` third-pass). Each strategy returns a list of matching seal SHAs; the first non-empty list determines attribution. Single-match within ANY strategy → move; multi-match within any strategy → ambiguous bucket. Empirically recovers 13 plan-docs at canonical HEAD (~5% of corpus). SHA backfill: TBD.

- **D-T1RS.HEURISTIC.4** — `.builder-plan.md` companion plan-docs are excluded from the sweep (they're authoring scratch, not the canonical plan-doc). The existing `plan_archive.py:99-106` direct-children iteration would include them; new filter to be added: skip `*.builder-plan.md` filenames. Sibling-manifest detection (`{slug}.manifest.yaml`) already excludes them implicitly. SHA backfill: TBD.

- **D-T1RS.GLOB-UPDATE** — shared helper `iter_all_plan_docs` + `iter_all_manifests` + `find_plan_doc_by_slug_glob` over inline duplicate-glob in each consumer. DRY; one source of truth for the traversal semantics. Trade-off: introduces a new import-graph edge from each consumer to `loam_amend`; the edge is precedented (heavy-b-migrate already imports `loam_amend`). SHA backfill: TBD.

- **D-T1RS.GLOB-LOCATION** — new helpers under `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/plan_locator.py`. Cohesion with `plan_archive.py` (the existing archive-semantics home) over proximity to consumer (CLI tree). F2 doubt #4 surfaces this. SHA backfill: TBD.

- **D-T1RS.GLOB-PRIORITY** — `find_plan_doc_by_slug_glob` returns sealed-path FIRST when both sealed + live versions exist for the same slug (e.g., during the live-sweep transition window). Reason: sealed is the canonical "shipped" artefact; live-tree duplicate is an authoring intermediate. Consumers expect the latest authoritative version; sealed wins. SHA backfill: TBD.

- **D-T1RS.SESSION-START-SEMANTICS** — `enumerate_amendments_in_flight` keeps live-tree-only semantics; new sibling `enumerate_sealed_amendments` walks `docs/plans/sealed/`. The session-start digest's caller is NOT modified by this amendment; behavior continues to surface only in-flight. F2 doubt #3 surfaces the gap a future digest-enhancement amendment may close. SHA backfill: TBD.

- **D-T1RS.LIVE-SWEEP-TIMING** — Scope C runs AFTER the seal commit, as a separate `chore(retroactive-sweep):` commit. Reason: keeps the seal-diff window clean from bookkeeping operations; the sweep is a one-shot operator-driven action, not part of the apply/seal cycle. F2 doubt #2 surfaces the blast-radius concern; halt-trigger #3 enforces the dry-run-first discipline. SHA backfill: TBD.

- **D-T1RS.LIVE-SWEEP-MECHANISM** — new CLI subcommand `loam amend sweep-archive [--dry-run]`. Surface durability + reproducibility over inline Python invocation. F2 doubt #5 surfaces the trade-off. SHA backfill: TBD.

- **D-T1RS.AC-LADDER** — 9 mechanism-level ACs (.HEURISTIC.{1..4} + .GLOB.{1..3} + .SWEEP.{1,2}) + 1 outcome-altitude smoke (.S). Lens 5 EVAL_DIMENSIONS: three orthogonal axes (.HEURISTIC / .GLOB / .SWEEP) + one aggregator judge (.S). The `outcome-altitude: true` mark on AC.T1RS.S satisfies `feedback_test_outcome_altitude_required`. SHA backfill: TBD.

- **D-T1RS.DOGFOOD** — THIS plan-doc + manifest are themselves expected targets of the live sweep (Scope C). At seal time, the existing post-#134 `plan_archive.py` integration (called from `seal.py`'s `_finalize` step) ALREADY moves this plan-doc to `docs/plans/sealed/` via Strategy 1 (the seal commit subject `chore(seals): amendment-143-tier1-retroactive-sweep-followup — ...` matches the full slug). The live-sweep CLI invocation at Scope C is then a no-op for this plan-doc (already moved by seal); it operates on the OTHER cleanly-attributable plan-docs. Dogfood: this amendment exercises the existing T1.4 archive path AND the new live-sweep CLI on the same canonical run. SHA backfill: TBD.

---

## §16. Halt-and-surface findings (raised + ruled at plan-authoring)

1. **Finding #1 — fence expansion from brief's 2 consumers to 4.** The dispatching brief named `release/gates.py` and `heavy_b_migrate/verify.py` as the two known downstream consumers (with "verify these are still the only consumers" as the pre-flight rider). Pre-flight Tier-0 grep surfaced TWO additional consumers: `primary_persona/session_start_gate.py:163` (`plans_dir.glob("amendment-*.md")`) and `dev-sdlc/hooks/bash_guard.py:236` (`plans_dir.glob("*.manifest.yaml")`). Also, the brief's named `heavy_b_migrate/verify.py` does NOT glob `docs/plans/` at runtime — it carries plan-doc paths in fixture-build strings only; the actual heavy-b-migrate consumer is `amendment_acs.py:88` (`discover_amendment_plans`). **Resolution (autonomous, plan-author):** the operational objective is "every downstream consumer can find plans in both locations." The two additional consumers AND the corrected heavy-b-migrate path are named in §5 (sealed-component fence). The fence widens from the brief's 2 to this amendment's 4. Per the operational-objective test (`feedback_test_against_operational_objective_before_escalating`): the objective implies a clear answer (all four consumers in-fence); autonomous fence widening is the correct call. This is NOT a halt-and-surface back to dispatcher — the fence widening is an in-scope correction of an incomplete brief, surfaced here in the plan-doc for dispatcher visibility.

2. **Finding #2 — empirical recovery rate ≠ brief's claim.** The dispatching brief cited #134's measurement of "146 false-negatives" (35% of ~430 plan-docs); the pre-flight Tier-0 re-measurement at canonical HEAD `b278cc6` found 13 recoverable + 88 still-no-signal across 255 non-companion plan-docs. The discrepancy is explained by post-#134 sealing activity (#135-#142 are now true-positives, not false-negatives) AND by the heuristic differentiation (the 88 no-signal cases are largely genuinely-no-seal-commit plans, not heuristic failures). **Resolution (autonomous, plan-author):** the AC family for Scope A targets the RECOVERABLE bucket (Strategy 2/3 verifiers); the 88 no-signal cases are surfaced as F2 doubt #1 for a future workstream. The amendment's AC contract is satisfied by recovering the 13 cases; F4 scope-confidence: high on the recovery mechanism, low on the no-signal-bucket triage (which needs a separate workstream). This is not a halt-and-surface to dispatcher; the divergence from the brief's claim is a Tier-0 recheck per `feedback_specific_claims_verified_or_marked_guess`, and the corrected numbers feed forward into the build agent's expectations.

3. **Finding #3 — Scope C's blast radius vs. the §134 halt-trigger #5 contract.** The live sweep WILL move ~150 plan-docs (the empirical pre-flight number). This is a large tree restructure but it IS the intended outcome — the §134 plan-doc explicitly described it as "the production-tree invocation that's deferred until the heuristic+consumers are ready." Halt-trigger #3 in §6 gates the dry-run vs real-run discipline: the build agent runs `loam amend sweep-archive --dry-run` first, surfaces the count for visual sanity-check, then proceeds to real-run if the count is ≤150 (well-within expected). The §134 halt-trigger #5 contract (ambiguous = stay in place) is preserved verbatim. **Resolution (autonomous, plan-author):** the dry-run-first discipline is named in halt-trigger #3; the build agent must surface the count before real-running. Not a halt-and-surface to dispatcher at plan-authoring time; the dispatcher sees the count at seal-time via the build agent's report.

4. **Finding #4 — section-14 heading shape continuity.** This plan-doc uses `## §14. Method-decision register` (canonical post-#136 shape with §-prefix + period). #136's widened regex + #141's decoupled backfill + #142's dogfood verify this shape works cleanly for the auto-backfill at seal time. **Resolution:** rely on the widened regex; halt-trigger #6 in §6 surfaces if the dogfood breaks.

5. **Finding #5 — pre-existing untracked plan-only file admission.** The working tree carries one untracked file `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` (unrelated workstream). Per #140 / #141 / #142 precedent, this is admitted at apply time via `--allow-untracked-globs 'docs/plans/promote-multi-channel-*'` or via the manifest's `universal_paths.prefixes: ["docs/plans/"]` (which covers untracked plan-docs by glob). **Resolution:** the manifest's `universal_paths` covers it; no explicit `--allow-untracked-globs` needed.

---

## §17. Composition (M5 derivation line)

- **Composes with** amendment #134 — closes its §16 finding #6 (the deferred retroactive sweep) by tightening the heuristic AND widening the downstream consumers AND running the live sweep.
- **Composes with** amendment #142 — exercises the SKILL-prose conventions for `narrative.target` + BASELINE walk-forward + source-edit-commit-before-apply ordering. This plan-doc's manifest's `narrative.target` IS the canonical `docs/plans/sealed/amendment-143-tier1-retroactive-sweep-followup.md` form.
- **Composes with** `feedback_locked_design_not_license_for_bad_outcomes` — the #134 narrow heuristic is "locked design" (sealed); this amendment revisits it because the outcome (35% false-negative rate vs the corpus) is bad enough to merit re-extension. The fix is ADDITIVE (strategies 2 + 3 augment, not replace, strategy 1).
- **Composes with** `feedback_summarize_and_surface_decisions` — the dispatch report carries summary + named-decisions-with-recommendations (D-T1RS.* register above).
- **Composes with** `feedback_verify_dispatch_before_sending` — pre-flight Tier-0 verification widened the fence from brief's 2 consumers to 4; finding #1 records the correction.
- **Composes with** `feedback_specific_claims_verified_or_marked_guess` — the brief's "146 false-negatives" claim was re-measured at canonical HEAD; finding #2 records the corrected empirical numbers.
- **Composes with** `feedback_n1_architectural_vs_n3_statistical` — the heuristic-tightening is an n=1 architectural verdict (does Strategy 2 recover the body-slug case? yes, empirically demonstrated against 13 known cases). Statistical n=3 not required.
- **Composes with** F4 scope-confidence — high confidence on the three-scope merge (causal dependency makes the merge mechanical, not a judgment call); high confidence on the helper-module shape (Lens 5 EVAL_DIMENSIONS makes the AC ladder orthogonal); medium confidence on the live-sweep CLI surface (could be Python-only; F2 doubt #5 surfaces the trade-off).
- **Independent of** the `prompt-scope ↔ confidence` lens for the heuristic strategies themselves — those are mechanical strategies, not scope choices.
- **Supersedes** the implicit "post-#134 sweep is a future-work item" framing — this amendment IS the future-work item.

---
