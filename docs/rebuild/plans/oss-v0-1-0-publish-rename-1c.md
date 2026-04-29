# OSS v0.1.0 publish — M1c — launchd label rebrand — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Prior sub-amendments:**
- M1a — docs/prose-only brand rebrand (sealed `143d465`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1a.md` §12).
- M1b — env-vars + per-host config dir + migration helper (sealed `d97c8c1`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1b.md` §14).
**Programme position:** Third sub-amendment of the M1.rename multi-amendment series. Independent of M1a / M1b in scope; lands third per series-master ladder ordering.
**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 item 4 (launchd label rebrand; version suffix dropped concurrently).
- `.scratch/claude-output/loam-rename-migration-plan.md` §3.4 (launchd surface mechanics + breaking-change flag).
- `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` §2 (sub-amendment ladder), §5 (series-wide hard constraints), §7 (series-wide halt triggers).
- `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (programme master plan; M1c row already present per M1b precursor commit `7be713b`).

---

## 1. Summary / TLDR

**M1c lands the launchd label rebrand:**

1. **Label rebase: `com.pos-v2.<slug>.<kind>` → `com.loam.<slug>.<kind>`** across every framework callsite. The version suffix (`-v2`) is dropped concurrently — there is no `v1` to differentiate from any more, per `loam-rename-decisions.md` Tier-1 #4.
2. **Plist filename cascade.** `framework/memory-system/launchd/com.pos-v2.memory-graphiti.plist` is renamed to `com.loam.memory-graphiti.plist` (historical reference plist; not loaded at runtime, but the filename matches the label by convention).
3. **Bootstrap/teardown flow updates.** `service_label()` in `framework/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` returns `com.loam.{slug}.{kind}`; `framework/first-run-inventory.yaml`'s service-label templates carry `com.loam.{slug}.{kind}`; HOL's bootout-before-bootstrap flow (already structurally label-agnostic — it runs whatever the scaffold emits) inherits cleanly.
4. **Per-host one-shot migration helper.** A sibling helper at `framework/tools/loam-migrate-launchd-labels/` performs the per-host one-time bootout-of-old + rename-aside flow for the legacy `com.pos-v2.<slug>.<kind>.plist` files in `~/Library/LaunchAgents/`. Idempotent (re-run is safe). Documented per the M1b helper's pattern.
5. **Orphan-plist-cleanup tool's NAMESPACED arm rebases.** The tool's `NAMESPACED_V2` classification (which says "this is the LIVE shape — leave alone") gets repointed to `com.loam.<slug>.<kind>`. The tool's existing pre-#6 single-segment ORPHAN classifications (`com.pos-v2.<single>` ORPHAN_V2, `com.pos.<single>` ORPHAN_V1) are preserved — those describe genuine pre-#6 historical shapes that are still orphans regardless of M1c. Per halt-trigger #7 of the dispatch.

**Hard cutover** per series-master §1 D-RNM.3. No fallback that loads under both labels concurrently. The migration helper handles the one machine state Luke owns (the canonical pos-v2 working tree on this host plus any sibling clones).

**What does NOT land in M1c** (deferred per series-master §2 ladder):
- Workspace-side `<workspace>/.pos/` sentinel directory — distinct surface from per-host config dir; M1b deferred; M1c also defers (cascades cleanly with M1e namespace pivot).
- Internal Python identifiers carrying the `pos-v2` prefix as variable/constant decoration (`_POS_V2_*`, `CANONICAL_POS_V2_PATH`, `CLASSIFICATION_POS_V2_DEV`, `POS_V2_PATH`) — namespace work; M1e.
- `--pos-v2-root` shell flag in `framework/hands-off-lifecycle/hooks/first-run.sh:167` and `pos_v2_root` Python variable name in `framework/hands-off-lifecycle/hooks/first_run_helper.py` — namespace-shape, M1e per dispatch §Scope.
- OTel `pos.*` span/event roots — M1d.
- `pos-amend` CLI rename → `loam amend` — M1e per dispatch §Scope.
- Code imports `from pos_<comp>` and package directory restructure — M1f per dispatch §Scope.
- `graceful-degradation` → `dormancy` — M1g per dispatch §Scope.
- Path strings of form `/Users/lukeivers/ivers-corp-pos-v2/...` (including the absolute paths inside the historical reference plist file body itself) — M9-deferred per `oss-v0-1-0-publish.md` §6.
- `com.pos-v2.*` references inside historical seal narratives (`framework/<comp>/seals/SEAL_COMMIT.*`) — preserved per `loam-rename-decisions.md` Q2 (history keeps contemporary terminology).
- `com.pos-v2.*` references inside historical plan-docs at `docs/rebuild/plans/*` — historical method-record; preserved (consistent with M1a + M1b's same exclusion).
- `com.pos-v2.*` literal in M1a / M1b sub-plans' "out of scope" lists — those sub-plans are historical record. This M1c sub-plan is the live one.
- `pos_v2_root` parameter name in `_run_bootstrap()` and `pos-v2 root` prose in user-facing diagnostic messages — namespace work; M1e.

**Sealed-component fence (post-build):** **five sealed components** carry launchd label callsites in src / scripts / tests / docs / launchd-dir:
- `hands-off-lifecycle` — tests/test_first_run.py (label-template assertions + sample labels).
- `workspace-bootstrap` — adapters/first_run_scaffold.py (`service_label()` + plist-template docstrings) + tests/test_first_run_scaffold.py (~14 callsites) + tests/test_AC_J_5_memory_write_worker_plist.py + tests/test_D5_plist_path_emission.py + tests/test_no_sealed_amendments.py (one-comment ref) + tests/conftest test fixtures.
- `memory-system` — launchd/README.md (4 prose callsites) + launchd/com.pos-v2.memory-graphiti.plist (Label key + filename rename).
- `primary-persona` — src/cli.py (1 docstring) + src/memory_write_worker.py (1 docstring) + tests/test_AC_M_7_stop_returns_fast_write_async.py (1 docstring).
- `orchestrator` — scripts/pos_session_start.py (default kwargs `memory_label="com.pos-v2.memory-graphiti"` + `orchestrator_label="com.pos.orchestrator"` — see §11 finding #4 for the v1-shape default surfaced for repair in-band).

Plus `framework/tools/orphan-plist-cleanup/` (1 component-tool — classifier + 2 tests + conftest + README + docstrings — NAMESPACED arm repoint per §1 item 5). Plus `framework/tools/loam-migrate-launchd-labels/` (NEW sibling tool — own pyproject, own tests). Plus `framework/first-run-inventory.yaml` (2 service-label entries; admitted by H19's existing top-level entry).

**Estimate:** 60–120 min AI-time per the duration rubric (multi-component mechanical-substitution category; five-component fence narrower than M1b's eleven; medium volume of label callsites; M1b calibration suggests modest surrounding-debt tax — M1a + M1b absorbed the bulk; HC#4 byte-content sample contains zero plist files per M1b §11 finding #2 — H19 retire-and-rebaseline does NOT happen at M1c).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1c closes the launchd-label slice. Subsequent sub-amendments close the OTel + namespace + CLI portions.
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — M1c stabilises the launchd label root that any future plugin / extension would observe via `launchctl list | grep loam`.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary in the launchctl labels they read when debugging service health (`launchctl print gui/$(id -u)/com.loam.<slug>.<kind>`).
- **AC.PO.2** (VALUE_PROPOSITION harness test) — the `com.loam.<slug>.<kind>` label root becomes the harness's launchd-namespaced ID-root that future plugin services (any plugin that wants to install its own launchd-supervised daemon) can reserve sub-namespaces under.

**Sealed-component fence (preliminary — see §4 ACs + §11 surface inventory):** five sealed components touched in src/scripts/tests/docs/launchd, plus one tool repoint, plus one NEW sibling tool, plus `first-run-inventory.yaml`. The amendment manifest YAML lists the five sealed components.

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose changed in M1c's diff traces back to AC.RNM-1c.1 .. AC.RNM-1c.S below. Mechanical rename of label literals + one plist filename + one classifier-arm repoint + one NEW migration helper; no behaviour changes beyond the rename + helper; no defensive-`if` admissions; no cross-mode-debt cascade beyond the named surface.

---

## 3. Three-lens analysis (abbreviated; series-master §4 covers cross-cutting)

- **Lens 1.** Pass. Preserves every existing Claude-native composition (PreToolUse hooks, MCP, skills, plugins). The launchd label namespace is below the Claude Code interaction layer; nothing in Claude's surface area reads launchd labels directly. The user's `launchctl list | grep loam` debug commands change one regex; no Claude-Code-shape disturbed.
- **Lens 2.** Primary-persona pass. The user reading `launchctl list` sees `com.loam.<slug>.*` — single brand-vocabulary surface. Harness pass — the `com.loam.*` reverse-DNS root becomes the canonical launchd ID-root that future harness-extensions claim sub-namespaces under.
- **Lens 3.** Pure mechanical-substitution work plus a sibling one-shot migration helper. Outcome-shaped ACs (post-rename grep counts; idempotent-helper-runs-twice check; on-disk-plist-filename matches label check). Method-shape (sed, Edit, helper script implementation, sibling-helper vs in-place classifier extension) is the builder's call inside the AC outcome bound.

---

## 4. Acceptance criteria — AC.RNM-1c.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.RNM-1c.1 — Label rebrand completes across all framework callsites

Every framework-code/test/doc/launchd-file callsite that names `com.pos-v2.<slug>.<kind>` (or its template form `com.pos-v2.{slug}.{kind}` in YAML, or its component-anchored form like `com.pos-v2.alpha.orchestrator` in tests, or its single-segment legacy form `com.pos-v2.memory-graphiti` in pre-#6 callers) post-amendment reads the corresponding `com.loam.<slug>.<kind>` (or `com.loam.{slug}.{kind}` template, etc.).

**The version suffix `-v2` is dropped concurrently** per `loam-rename-decisions.md` Tier-1 #4. There is no `com.loam-v2.*` shape; the post-rename root is `com.loam.*`.

**Outcome:** `grep -rE 'com\.pos-v2\.' framework/ --include="*.py" --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.md" --include="*.json" --include="*.fragment" --include="*.plist" --include="*.txt"` returns 0 matches in the live (non-historical) surface. Permitted residuals:
- `framework/<comp>/seals/SEAL_COMMIT.*` historical seal narratives (preserved per `loam-rename-decisions.md` Q2 / M1a + M1b precedent).
- `docs/rebuild/plans/*.md` historical method-record (preserved consistent with M1a + M1b).
- The orphan-plist-cleanup tool's ORPHAN_V2 detector arm + tests + docstrings + README explicitly testing/documenting the pre-#6 single-segment shape `com.pos-v2.<single-segment>.plist` as a HISTORICAL ORPHAN class — the tool's NAMESPACED arm repoints, but the orphan-detection arm preserves its archaeological mission (see §11 finding #2 + AC.RNM-1c.5).
- Post-rename: tool's renamed `com.pos-v2.<single-segment>` callsites in `detector.py` + tests + README continue to describe pre-#6 orphan shapes.

### AC.RNM-1c.2 — Plist filename cascade

The historical reference plist file at `framework/memory-system/launchd/com.pos-v2.memory-graphiti.plist` is renamed to `framework/memory-system/launchd/com.loam.memory-graphiti.plist`. The plist's `<key>Label</key><string>com.pos-v2.memory-graphiti</string>` body becomes `<string>com.loam.memory-graphiti</string>`. The README in the same directory's references update concurrently per AC.RNM-1c.1.

**Outcome:** `ls framework/memory-system/launchd/` shows `com.loam.memory-graphiti.plist` (not `com.pos-v2.memory-graphiti.plist`). The plist body's Label key carries `com.loam.memory-graphiti`. The hardcoded absolute paths in the plist body (`/Users/lukeivers/ivers-corp-pos-v2/...`) are NOT changed — those are M9-deferred per `oss-v0-1-0-publish.md` §6 and the file's READIME explicitly notes it is historical-reference-only (not loaded at runtime; the runtime plist is generated by workspace-bootstrap's first_run_scaffold).

### AC.RNM-1c.3 — Per-host one-shot migration helper exists and is idempotent

A sibling migration helper at `framework/tools/loam-migrate-launchd-labels/` (parallel structure to `framework/tools/loam-migrate-host-config/` from M1b — own pyproject, own src, own tests, own README) performs the per-host one-shot bootout + rename-aside flow:

1. Scan `~/Library/LaunchAgents/` for `com.pos-v2.<slug>.<kind>.plist` filenames (4-segment shape; pre-M1c live shape; post-M1c stale).
2. For each match:
   a. Issue `launchctl bootout gui/<uid>/<label>` (benign-stderr-fragments treated as success per amendment #6's `ServiceManagerRunner.bootstrap` policy + the orphan-plist-cleanup tool's apply mode).
   b. Rename the plist file to `<label>.label-rebrand-disabled.bak` (preserves the file for recovery; never deletes).
3. Print one absolute path per file processed.
4. Exit 0 on success (any subset of bootouts may be benign-no-op when the label isn't loaded; that's still success). Exit non-zero on a non-recoverable launchctl error on at least one file (the affected file is left in place; consistent with orphan-plist-cleanup's exit-1 contract).

**Idempotency:** running the helper twice produces no double-action. After the first run, the legacy plists carry the `.label-rebrand-disabled.bak` suffix and no longer match the detection pattern.

**Out of scope for the helper:**
- Single-segment pre-#6 orphans (`com.pos-v2.<single>.plist`, `com.pos.<single>.plist`) — those are the orphan-plist-cleanup tool's mission. The two helpers are orthogonal: orphan-plist-cleanup remediates pre-#6 archaeological orphans; loam-migrate-launchd-labels remediates the M1c label rebrand transition.
- Writing new `com.loam.<slug>.<kind>.plist` files — workspace-bootstrap's first_run_scaffold writes those on the next workspace bootstrap (running the existing bootout-before-bootstrap flow with the new labels).
- Re-running the workspace-bootstrap first-run — the user opens the workspace in Claude Code post-rebrand and the existing first-run flow handles the new-label install.

**Outcome:** the helper script exists, is executable, and demonstrably:
- on a synthesised `~/Library/LaunchAgents/`-with-`com.pos-v2.<slug>.<kind>.plist` test setup, performs the bootout-attempt + rename-aside and prints a non-empty summary;
- on a re-run, prints "no legacy labels detected" and exits 0;
- on an empty / fresh-machine `~/Library/LaunchAgents/`, exits 0 with a "nothing to migrate" message;
- on a synthesised launchctl-error setup (one file fails bootout with non-benign stderr), prints the failure reason and exits non-zero.

The helper is documented in its own README covering the contract above, plus the post-rebrand-recovery path (`mv foo.label-rebrand-disabled.bak foo.plist` then re-run workspace first-run).

### AC.RNM-1c.4 — Bootstrap/teardown flow inherits cleanly

The hands-off-lifecycle bootout-before-bootstrap flow (`framework/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py::ServiceManagerRunner.bootstrap`) is structurally label-agnostic — it bootouts whatever label it's passed and bootstraps whatever plist file it's passed. AC.RNM-1c.4 verifies that post-rename, the flow:

1. Computes labels via `service_label(kind, slug)` returning `com.loam.<slug>.<kind>` (not `com.pos-v2.<slug>.<kind>`).
2. Writes plist files to `~/Library/LaunchAgents/com.loam.<slug>.<kind>.plist` (not the legacy filename).
3. The bootout-before-bootstrap call sequence in `ServiceManagerRunner.bootstrap` issues `launchctl bootout gui/<uid>/com.loam.<slug>.<kind>` followed by `launchctl bootstrap gui/<uid> <plist-path>` (both invocations carry the new label).
4. Distinct workspaces still get distinct labels (multi-workspace AC.6 invariant from amendment #6 still holds: `com.loam.<slug-a>.<kind>` and `com.loam.<slug-b>.<kind>` are non-overlapping).

**Outcome:** `pytest framework/workspace-bootstrap/tests/test_first_run_scaffold.py -k "AC4 or AC5 or AC6"` PASSES post-rename (the tests are updated to assert against `com.loam.*` instead of `com.pos-v2.*`). `pytest framework/workspace-bootstrap/tests/test_AC_J_5_memory_write_worker_plist.py` PASSES. `pytest framework/hands-off-lifecycle/tests/test_first_run.py -k "T14 or AC7"` PASSES.

### AC.RNM-1c.5 — Orphan-plist-cleanup tool's NAMESPACED arm rebases

The orphan-plist-cleanup tool's classifier `framework/tools/orphan-plist-cleanup/src/orphan_plist_cleanup/detector.py`:

- The `Classification.NAMESPACED_V2` enum value is renamed to `Classification.NAMESPACED` (or `Classification.NAMESPACED_LOAM` — builder's call within the AC bound). Its docstring describes the post-M1c live shape `com.loam.<slug>.<kind>.plist`.
- The classifier's segment-prefix check matches `["com", "loam"]` for the NAMESPACED arm (4 segments) instead of `["com", "pos-v2"]`.
- The classifier's `Classification.ORPHAN_V2` arm continues to match `com.pos-v2.<single>` (3 segments) — describes pre-#6 historical orphans; that meaning is unchanged regardless of M1c.
- The classifier's `Classification.ORPHAN_V1` arm continues to match `com.pos.<single>` (3 segments) — pre-pos-v2 v1 shape; unchanged.

The tool's tests (`tests/test_detector.py` + `tests/conftest.py` SAMPLE_FILES + `tests/test_apply.py` + `tests/test_dry_run.py` callsites referencing the live NAMESPACED shape) update to assert against `com.loam.<slug>.<kind>.plist` as the "live; do not touch" shape.

The tool's README and module docstrings update concurrently to describe the post-M1c contract: detect pre-#6 single-segment orphans (`com.pos-v2.<single>`, `com.pos.<single>`); leave 4-segment `com.loam.<slug>.<kind>` plists alone.

**Out of scope:** the tool does NOT detect post-M1c-stale `com.pos-v2.<slug>.<kind>` (4-segment) plists as orphans — that surface is the M1c migration helper's mission per AC.RNM-1c.3. Carving the surface into the orphan tool would add a new ORPHAN classification arm + apply path; the cleaner separation is per-helper-per-mission.

**Outcome:** `pytest framework/tools/orphan-plist-cleanup/tests/` PASSES (every test under the tool's test dir runs green post-rename; assertions reference `com.loam.<slug>.<kind>` for NAMESPACED and `com.pos-v2.<single>`/`com.pos.<single>` for the ORPHAN arms).

### AC.RNM-1c.S — Sealed-component fence narrows to launchd surface only

Five-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; this is one sub-amendment before M1e's CLI rename). The amendment manifest YAML lists five sealed components. The `seal_diff` `allowed_prefixes` admit `framework/<comp>/` for each touched component plus the universal paths plus `framework/tools/` (admits the orphan-plist-cleanup repoint + the NEW loam-migrate-launchd-labels helper) plus `framework/first-run-inventory.yaml` (one-line YAML edit for the two `label:` template values).

**Per-component touched-test scope:** narrow to touched files. Per `feedback_amendment_dispatch_speedups`, M1c skips pre-seal full-suite rerun. Each sealed component's `tests/test_no_sealed_amendments.py` runs as part of `pos-amend apply` verification. The seal-diff fence test for AC.RNM-1c.S is the primary check (verifies the fence isn't reaching beyond launchd surfaces).

**Outcome:** `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention; five per-component sidecars all advance; `pytest framework/<comp>/tests/test_no_sealed_amendments.py` per touched component PASSES.

### AC.RNM-1c.6 — No work outside the named surfaces (negative AC)

Negative AC. The amendment's git-diff includes ZERO touches outside:

- The five named sealed components' src/scripts/tests/docs/launchd paths.
- The orphan-plist-cleanup tool's path.
- The NEW loam-migrate-launchd-labels helper's path.
- `framework/first-run-inventory.yaml` (two service-label template entries).
- The plan-doc + manifest YAML under `docs/rebuild/plans/`.
- Any necessary admission-extension to `framework/hands-off-lifecycle/tests/test_cross_cutting.py` (only if M1c's surface introduces a top-level dir not already in H19's allowed set — expected: NO new top-level dirs introduced because the new helper lives under existing `framework/tools/` admission).

**Permitted ZERO surfaces (no edits expected):**

- No env-var or per-host-config-dir changes — M1b closed those.
- No internal Python identifiers carrying `POS_V2_` decoration — M1e.
- No string-literal `pos-v2` outside launchd context — M1a/M1b/M1e.
- No OTel `pos.*` roots — M1d.
- No `from pos_<comp>` imports — M1f.
- No `pos-amend` CLI references in code — M1e.
- No `--pos-v2-root` CLI flag rename in `first-run.sh` — M1e.
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites — M9.
- No `framework/<comp>/seals/SEAL_COMMIT.*` historical-narrative edits.
- No `docs/rebuild/plans/*.md` historical method-record edits beyond this plan-doc + this manifest YAML.
- No workspace-side `<workspace>/.pos/` sentinel-dir constant changes.
- No `graceful-degradation` / `dormancy` rename — M1g.

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Six outcome-named behaviours (label rebrand + version-suffix-drop, plist filename cascade, migration helper idempotency, bootstrap/teardown flow inheritance, orphan-plist-cleanup NAMESPACED arm rebase, fence-narrowing seal) → six ACs (AC.RNM-1c.1 .. AC.RNM-1c.5 + AC.RNM-1c.S). Plus one negative AC (AC.RNM-1c.6) enforcing the launchd-surface-only fence. Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §8.5.

---

## 5. Hard constraints (M1c-specific; series-wide constraints from master §5 inherit)

- **Launchd-only diff with hard cutover.** AC.RNM-1c.6 is the structural fence — label-callsites + plist filename + migration helper + orphan-tool NAMESPACED-arm + first-run-inventory + plan-doc only. No other surfaces.
- **Hard cutover.** Per series-master §1 D-RNM.3: no `service_label()` that returns either label depending on env-var; no fallback that boots both old and new labels concurrently. The migration helper handles the per-host transition.
- **Workspace-side `<workspace>/.pos/` stays.** Out of scope per M1b's scope discipline; M1c continues that discipline.
- **Orphan-plist-cleanup NAMESPACED arm rebases; ORPHAN arms preserved.** Per halt-trigger #7 of the dispatch — the tool's orphan-detection mission for pre-#6 single-segment shapes is preserved verbatim; only the NAMESPACED ("live, do not touch") arm rebases to `com.loam.<slug>.<kind>`.
- **Plist filename rename uses `git mv`.** The historical-reference plist file at `framework/memory-system/launchd/com.pos-v2.memory-graphiti.plist` is renamed via `git mv` so git rename-detection preserves blame history. The body's Label key value updates as a content edit on the renamed file.
- **Path strings under `/Users/lukeivers/ivers-corp-pos-v2/...` stay** — directory rename is M9-deferred. Specifically applies to the `<string>/Users/.../memory-system/...</string>` paths inside the renamed plist's body.
- **Filenames stay (other than the one named).** `degradation.sqlite`, `degradation-config.yaml`, etc. don't change — those are M1g.
- **Historical seal narratives stay.** `framework/<comp>/seals/SEAL_COMMIT.*` files containing `com.pos-v2.*` references are preserved per `loam-rename-decisions.md` Q2.
- **Historical plan-docs stay.** `docs/rebuild/plans/*.md` files not authored by this amendment (including M1a + M1b sub-plans + their manifest YAMLs + the orphan-plist-cleanup-tool plan-doc) are preserved.
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`). Corrective commits are NEW commits.
- **`pos-amend apply` runs BEFORE the seal commit** (`feedback_dispatch_explicit_pos_amend_apply`).
- **HC#4 byte-content sample is GREEN.** Verified at M1b §11 finding #2: the fifteen sample files contain ZERO plist references. M1c does NOT touch any sample-pinned file. H19 retire-and-rebaseline does NOT happen at M1c (the dispatch's note about "first sub-amendment that may cross H19" was a series-master pre-emptive flag; empirical surface confirms HC#4 stays green).
- **Migration helper is sibling, not extension of M1b helper.** The M1b `loam-migrate-host-config` helper has a clean single-purpose contract (per-host config dir relocation). Adding launchd-label remediation to it would conflate two distinct surfaces. The clearer shape is a sibling tool at `framework/tools/loam-migrate-launchd-labels/`. Builder's call to refine within the AC.RNM-1c.3 bound.

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full list. Re-named here for ODD §2.5 compliance.)

- All work deferred to M1d..M1g + M9 (OTel, namespace pivot, CLI rename, dormancy rename, dir rename).
- **Workspace-side `<workspace>/.pos/` sentinel directory** — distinct surface; M1b discipline carried forward.
- **Internal Python identifiers** carrying `POS_V2_` decoration / `pos_v2` lower-case decoration — namespace work; M1e.
- **`--pos-v2-root` CLI flag** in `framework/hands-off-lifecycle/hooks/first-run.sh` and `pos_v2_root` parameter name in `framework/hands-off-lifecycle/hooks/first_run_helper.py::_run_bootstrap` — namespace shape; M1e per dispatch §Scope.
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` — preserved.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` (other than this plan-doc + this manifest YAML) — preserved.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** — historical-narrative-heavy live docs; M1a + M1b deferred; M1c continues to defer. (FUTURE_IDEAS.md does mention `com.pos-v2.<slug>.*` in one historical-narrative paragraph — preserved as historical record consistent with §6 of M1a.)
- **Spec docs** at `docs/rebuild/spec/pos-v2-*.md` — M1e (filename + content).
- **The orphan-plist-cleanup tool's pre-#6 ORPHAN_V2 / ORPHAN_V1 detection arms** — those describe genuine pre-#6 historical shapes; their `com.pos-v2.<single>` and `com.pos.<single>` literals are archaeological references, not the live shape. **Preserved verbatim.** Only the tool's NAMESPACED ("live, do not touch") arm rebases (AC.RNM-1c.5).
- **Renaming `Classification.NAMESPACED_V2` enum value** — builder's call within AC.RNM-1c.5. Recommendation: rename to `Classification.NAMESPACED` (drops the version suffix, matching the brand-side version-drop). Builder may keep the `_V2` suffix for compatibility with any out-of-tree consumer if surfaced — but the tool has no out-of-tree consumers per its README.
- **The orchestrator's `pos_session_start.py:126` `orchestrator_label="com.pos.orchestrator"` v1-shape default** — this is a pre-#6 v1 shape (single-segment under `com.pos.`, NOT `com.pos-v2.`). Per §11 finding #4, this is a pre-existing tech-debt anomaly that surfaces at M1c. The default rebrands to `com.loam.orchestrator` as part of AC.RNM-1c.1 (single-segment legacy form maps to single-segment new form).

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`; `git status --short` shows working tree clean (only the pre-existing `personas/` untracked item remains). Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to M1b's seal commit `d97c8c1`.
3. **M1c sub-plan + manifest commit.** This plan-doc + a manifest YAML at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c.manifest.yaml` per the established M1a/M1b-precedent shape.
4. **Phase A — label rebrand across framework src/scripts/tests.** Mechanical rename across:
    - `framework/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` — `service_label()` returns `com.loam.{slug}.{kind}`; the surrounding docstring's label-shape prose updates.
    - `framework/workspace-bootstrap/tests/test_first_run_scaffold.py` — every fixture/assertion `com.pos-v2.alpha.*`, `com.pos-v2.beta.*`, `com.pos-v2.pos-v2.*`, `com.pos-v2.pos3.*` callsite renames to `com.loam.*`.
    - `framework/workspace-bootstrap/tests/test_AC_J_5_memory_write_worker_plist.py` — docstring + assertion updates.
    - `framework/workspace-bootstrap/tests/test_D5_plist_path_emission.py` — sandbox-label string update.
    - `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` — single comment-line reference updates.
    - `framework/hands-off-lifecycle/tests/test_first_run.py` — `com.pos-v2.alpha.*` + `com.pos-v2.{slug}.*` + `com.pos-v2.fixture-x.*` callsites rename to `com.loam.*`.
    - `framework/primary-persona/src/cli.py` — single docstring callsite.
    - `framework/primary-persona/src/memory_write_worker.py` — single docstring callsite.
    - `framework/primary-persona/tests/test_AC_M_7_stop_returns_fast_write_async.py` — single docstring callsite.
    - `framework/orchestrator/scripts/pos_session_start.py` — `memory_label="com.pos-v2.memory-graphiti"` → `memory_label="com.loam.memory-graphiti"`; `orchestrator_label="com.pos.orchestrator"` → `orchestrator_label="com.loam.orchestrator"` (see §11 finding #4 for the v1-shape repair note).
    - `framework/memory-system/launchd/README.md` — four prose callsites (label name + bootout/rm command examples).
    - `framework/first-run-inventory.yaml` — two `label:` template values.
   Post-edit grep verifies AC.RNM-1c.1 outcome (0 framework `com.pos-v2.*` matches outside historical seals + historical plan-docs + orphan-plist-cleanup ORPHAN arms).
5. **Phase B — historical-reference plist rename + Label-key edit.** `git mv framework/memory-system/launchd/com.pos-v2.memory-graphiti.plist framework/memory-system/launchd/com.loam.memory-graphiti.plist`. Edit the renamed file's `<key>Label</key><string>com.pos-v2.memory-graphiti</string>` to `<string>com.loam.memory-graphiti</string>`. The hardcoded absolute paths in the plist body are NOT changed (M9-deferred). Verify AC.RNM-1c.2 outcome.
6. **Phase C — orphan-plist-cleanup NAMESPACED-arm rebase.** Update:
    - `framework/tools/orphan-plist-cleanup/src/orphan_plist_cleanup/detector.py` — `Classification.NAMESPACED_V2` → `Classification.NAMESPACED` (recommended rename); the segment-prefix check matches `["com", "loam"]` for the NAMESPACED arm; module docstring + `Classification` enum docstring update to reference post-M1c live shape `com.loam.<slug>.<kind>.plist`.
    - `framework/tools/orphan-plist-cleanup/tests/conftest.py` — `SAMPLE_FILES` dict's `com.pos-v2.alpha.*` namespaced entries rename to `com.loam.alpha.*`; the ORPHAN_V2 entries (`com.pos-v2.memory-graphiti.plist`, `com.pos-v2.orchestrator.plist`) STAY (they're explicit historical orphan fixtures).
    - `framework/tools/orphan-plist-cleanup/tests/test_detector.py` — every parametrize entry citing `com.pos-v2.<slug>.<kind>` for the NAMESPACED arm renames to `com.loam.<slug>.<kind>`; ORPHAN_V2 entries stay.
    - `framework/tools/orphan-plist-cleanup/tests/test_apply.py` — assertions referencing the namespaced-arm shape rename to `com.loam.*`; orphan-arm assertions (which cite `com.pos-v2.memory-graphiti.plist` as a HISTORICAL ORPHAN fixture) stay.
    - `framework/tools/orphan-plist-cleanup/tests/test_dry_run.py` — namespaced-arm fixture rename; orphan-arm fixtures stay.
    - `framework/tools/orphan-plist-cleanup/README.md` — "What counts as an orphan" section: ORPHAN definitions stay (pre-#6 single-segment shapes); the "is NEVER classified as orphan" example rebases to `com.loam.<slug>.<kind>.plist`.
   Post-edit `pytest framework/tools/orphan-plist-cleanup/tests/` PASSES.
7. **Phase D — author the loam-migrate-launchd-labels sibling helper.** Create `framework/tools/loam-migrate-launchd-labels/` with structure mirroring `framework/tools/loam-migrate-host-config/`:
    - `pyproject.toml` (mirrors M1b helper's, with new package name).
    - `src/loam_migrate_launchd_labels/__init__.py`, `__main__.py`, `cli.py`, `migrate.py`.
    - `tests/__init__.py`, `conftest.py`, `test_migrate.py`, `test_cli.py`.
    - `README.md` covering the contract per AC.RNM-1c.3.
   The migrate.py implementation: scan `~/Library/LaunchAgents/` for filenames matching `com.pos-v2.<2segments>.plist` (4-segment shape), invoke `launchctl bootout gui/<uid>/<label>` (benign-stderr-fragments treated as no-op), rename the file to `<base>.label-rebrand-disabled.bak`. Idempotent: re-run after success finds zero matches.
   The cli.py: argparse with optional `--launch-agents-dir` (test override) + optional `--launchctl-bin` (test override). Default exit codes: 0 on clean (any number of files processed including zero); non-zero on any non-recoverable launchctl error. (Specific exit code: `2` for parity with the orphan-plist-cleanup `--apply`'s exit-1 contract — the sibling tool can use exit-1 for "non-recoverable" too; builder's call.)
   Tests cover the four behavioural cases (empty dir, one-orphan-cleanly, multiple-orphans, launchctl-error-on-one). Run `pytest framework/tools/loam-migrate-launchd-labels/tests/` PASSES.
8. **Phase E — feature commit.** Single feature commit carrying the launchd label rename diff + plist filename rename + Label-key edit + orphan-tool NAMESPACED-arm rebase + NEW loam-migrate-launchd-labels helper + helper docs + helper tests + first-run-inventory edits. Commit message names the M1c slug, the AC family, and the series-master pointer.
9. **Phase F — pos-amend apply.** Run `pos-amend apply` against the manifest. Verify clean apply. **`pos-amend apply` BEFORE the seal commit per FIDRAFT note from amendment #41.**
10. **Phase G — apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `pos-amend apply` convention.
11. **Phase H — seal-diff fence verification.** AC.RNM-1c.S + AC.RNM-1c.6 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named surfaces. Verify each component's `pytest framework/<comp>/tests/test_no_sealed_amendments.py` passes.
12. **Phase I — touched-test rerun.** Run the explicit test scope: every test file in the launchd-label callsite list (Phase A), the plist-rename verification (Phase B file's contents read back), the orphan-tool full test suite (Phase C), the new migration helper's tests (Phase D), plus each touched sealed component's `test_no_sealed_amendments.py`. Per `feedback_amendment_dispatch_speedups`, the full-suite rerun is skipped pre-seal — the touched-test-only sweep is the methodology-aligned narrow verification.
13. **Phase J — `pos-amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below). The seal commit narrative cites the AC family, the version-suffix-drop decision, the plist-filename cascade, the orphan-tool NAMESPACED-arm rebase, and the new sibling helper.

Phase A is mechanical-substitution. Phase B is one git mv + one Edit. Phase C is mechanical-substitution + tests. Phase D is helper authoring (the only material code-authoring in M1c). Phases 8–13 are commit + seal mechanics.

---

## 8. Halt triggers (M1c-specific; series-wide triggers from master §7 inherit)

The build agent MUST halt and surface when:

1. **A launchd-label callsite crosses an unexpected sealed-component boundary.** Inventory pre-build expects callsites in five sealed components (HOL, workspace-bootstrap, memory-system, primary-persona, orchestrator) plus orphan-plist-cleanup tool plus first-run-inventory.yaml. Any callsite in a sixth+ sealed component surfaces as a fence-creep signal. Halt; surface for re-scope.
2. **HC#4 byte-content sample breach.** Per M1b §11 finding #2, the fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` contain ZERO plist or launchd-label callsites. **Pre-build verification (mandatory per dispatch §Constraints HOL byte-content-match):** confirm no plist file is in HC#4's sample (expected: zero). If a sample file IS in HC#4's set (unexpected), apply ODD §4 retire-and-rebaseline in-band per the methodology; record reasoning in this plan's §11.
3. **ODD §2.5 violations encountered in surrounding code.** Halt; do NOT silently extend. Surface for owner ruling on whether to fix in-band, defer, or reshape M1c's scope.
4. **`pos-amend` automation hits a gap on the launchd surface.** Regex narrowness (e.g. fails on plist-XML segments, fails on YAML template-string `com.pos-v2.{slug}.*`), abs-path requirement, manifest-validation false-positive on the five-component fence, manifest-validation false-positive on the new loam-migrate-launchd-labels tool path. Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
5. **Pre-existing `~/.loam/` per-host state from M1b's migration that conflicts with M1c's relocation expectations.** M1c's launchd helper does NOT touch `~/.loam/` (it operates on `~/Library/LaunchAgents/`). However, if the build-tree's host has both `~/.pos/` and `~/.loam/` from a partial M1b state, halt for owner ruling per dispatch halt-trigger #5.
6. **Cross-mode debt** (loam-mode F-register, hands-off-lifecycle allowed_prefixes, dispatch-template path refs) that prevents launchd-label rename from landing cleanly. Record + address in scope or surface for follow-on.
7. **Orphan-plist-cleanup tool's behaviour fundamentally changes when the labels rename.** Pre-build verification: the tool's `Classification.NAMESPACED_V2` arm strings literal `["com", "pos-v2"]` for the prefix check; post-rename it becomes `["com", "loam"]`. The tool's pre-#6 ORPHAN_V2 + ORPHAN_V1 arms keep their archaeological mission (those describe genuine pre-#6 historical shapes). Per dispatch halt-trigger #7, the carve-out IS inside M1c's scope per AC.RNM-1c.5. If the build agent finds the tool's contract has additional surfaces beyond the classifier (e.g. the apply mode's behaviour depends on label shape in ways not visible in the classifier alone), halt and surface for AC.RNM-1c.5 expansion.
8. **AC.RNM-1c.6 fence is breached.** The diff reaches outside launchd-surface + plist-filename + migration-helper + plan-doc + orphan-tool-namespaced-arm surfaces. Halt; do not "fix" by widening the AC; the over-reach IS the failure signal.
9. **A `loam` identifier already in use** in any of the named surfaces (e.g. an existing `com.loam.*` label in some pre-rename fixture). Halt; surface for rename-the-conflicting-use first.
10. **Wall-clock exceeds 2 h** (M1c is rubric-priced 60–120 min midpoint 90 min; 2 h is 1.33×). Halt with current-state report; dispatcher triages continue / split-further / pause.
11. **Pre-existing test fails post-rename.** Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis. (Distinguish from pre-existing flaky tests recorded in FIDRAFT — the launchd-related flaky test `test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200` recorded at amendment #67's seal IS launchd-touching; verify whether M1c's rename surfaces it.)
12. **A `com.pos-v2.*` reference is found in `framework/<comp>/seals/SEAL_COMMIT.*`** during touched-test verification — historical narratives are preserved per `loam-rename-decisions.md` Q2; if a sealed-narrative cross-reference assertion ties a marker phrase to a `com.pos-v2.*` literal AND the marker is brand-keyed (vs intent-keyed), apply `feedback_loose_AC_text_fix_AC_not_implementation` per M1a's #9 precedent.

---

## 9. Risks (M1c-specific)

1. **The historical-reference plist file at `framework/memory-system/launchd/com.pos-v2.memory-graphiti.plist`.** It carries hardcoded absolute paths to `/Users/lukeivers/ivers-corp-pos-v2/...`. Per M9-deferral, those stay. The plist is RENAMED (filename + Label key body). The README in the same dir explicitly states the file is reference-only (not loaded at runtime; runtime plist is generated by workspace-bootstrap). M1c's edit is to the filename + Label key only; the absolute path strings are M9-deferred and preserved. **Risk:** an external consumer following the historical README's instructions copies the (now-renamed) plist to `~/Library/LaunchAgents/` and `launchctl load`s it. The README explicitly disclaims this path; the rename does not introduce a new risk.
2. **Migration helper running on Luke's machine.** Luke's host currently has `com.pos-v2.ivers-corp-pos-v2.{kind}.plist` files loaded under launchd (per the migration research §2.5). Post-M1c rebrand on disk + post-restart-of-Claude-Code-on-this-workspace, the next first-run-or-resume hits the bootout-before-bootstrap flow with the new `com.loam.<slug>.<kind>` labels. The OLD `com.pos-v2.<slug>.<kind>` labels remain loaded in launchd until the migration helper bootouts them. **The helper is the surface that closes that gap.** Without it, the user has dual-loaded labels (old `com.pos-v2.*` running its old daemon + new `com.loam.*` running the new daemon) potentially competing on ports — BUT the `com.pos-v2.*` daemon's plist files still point at the same workspace's services, so they probably bind the same port (8765 for memory-graphiti) and one would crash on launch. Mitigation: helper is documented + the user runs it once per host post-upgrade per the M1b helper's pattern.
3. **Orphan-plist-cleanup tool's contract drift.** The tool's NAMESPACED arm rebases. If a downstream consumer of the tool (none currently — the tool has no out-of-tree dependents per its README) imports `Classification.NAMESPACED_V2`, that import breaks post-rename. Mitigation: rename to `Classification.NAMESPACED` matches the version-drop convention. The tool's tests catch any internal drift.
4. **The `orchestrator_label="com.pos.orchestrator"` v1-shape default in `pos_session_start.py:126`.** This is a pre-amendment-#6 default — `com.pos.<single>` (NOT `com.pos-v2.*`). Per finding #4 in §11, no live caller uses this default; all callers either pass explicit per-workspace labels (via the resolve_service_labels flow) or don't reach this path. The default rebrands to `com.loam.orchestrator` (single-segment legacy form maps to single-segment new form). Risk: a future caller reads the post-rename default and assumes single-segment legacy form is the canonical shape. The default still exists (for symmetry with `memory_label`) but is functionally dead. Acceptable: mechanical rename for visual consistency; finding #4 is recorded for §11.
5. **Wide test-fixture surface in workspace-bootstrap and HOL test suites.** ~14 fixture callsites in `test_first_run_scaffold.py` (and a few more in `test_first_run.py`) reference `com.pos-v2.alpha.*` / `com.pos-v2.beta.*` / `com.pos-v2.pos-v2.*` / `com.pos-v2.fixture-x.*`. A naive `s/com.pos-v2/com.loam/g` is correct because every callsite rebrands; the failure mode is missing one (which would cause its assertion to fail post-rename). Mitigation: post-edit grep verifies AC.RNM-1c.1 outcome (0 framework `com.pos-v2.*` matches outside historical seals).
6. **Test fixture name `pos-v2` (used as a workspace basename in `test_H1_fresh_first_run_writes_all_yamls`).** That fixture creates `tmp_path / "pos-v2"` and asserts the resulting label is `com.pos-v2.pos-v2.<kind>`. Post-M1c, the workspace basename `"pos-v2"` STAYS (it's a fixture string, not a brand callsite — namespace work, M1e), but the label format changes to `com.loam.pos-v2.<kind>`. The doubled-prose comment ("the doubled `pos-v2` is an artefact of naming the test fixture after the repo") needs an in-place comment-update to read "the doubled `pos-v2` was an artefact ... post-M1c the prefix is `com.loam.` so the doubled-prose is gone (the fixture basename + the brand prefix differ now)". Recorded as Phase A item.
7. **The orphan-plist-cleanup tool's tests reference both ORPHAN and NAMESPACED shapes side-by-side.** A naive global `s/com.pos-v2/com.loam/g` over the test files would WRONG-rename the ORPHAN_V2 fixtures (e.g. `com.pos-v2.memory-graphiti.plist` is meant to STAY as the orphan-fixture). Mitigation: targeted Edit per fixture line, not global sed.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per series master §1, all three D-RNM rulings (split, namespace shape, no compat window) closed at owner-ruling time. The dispatch's authority text + the locked rulings cover M1c's scope cleanly.

**Builder's calls within ACs (NOT requiring owner ruling):**

- D-build.M1c.1 — Migration helper path. Three options:
  1. Sibling tool at `framework/tools/loam-migrate-launchd-labels/` (parallel to M1b's `loam-migrate-host-config/`).
  2. Extension of M1b's helper to add a `--launchd-labels` mode.
  3. Sub-command under a future `loam migrate <subcommand>` umbrella (anticipates M1g's CLI rename — premature here).
  Recommendation: option 1 (sibling tool) per §5 hard-constraint and the clean-single-purpose principle. Builder's call within AC.RNM-1c.3.
- D-build.M1c.2 — Orphan-plist-cleanup `Classification` enum rename. Two options:
  1. Rename `NAMESPACED_V2` → `NAMESPACED` (drops the version suffix, matching the `-v2` drop in label shape).
  2. Keep `NAMESPACED_V2` for backward-compat with any out-of-tree consumer.
  Recommendation: option 1 (rename to `NAMESPACED`) — the tool has no out-of-tree consumers per its README; the version-drop matches the brand-side decision in `loam-rename-decisions.md` Tier-1 #4. Builder's call within AC.RNM-1c.5.
- D-build.M1c.3 — Migration helper exit-code convention. Two options:
  1. Match orphan-plist-cleanup's apply-mode (exit 1 on any non-recoverable launchctl error).
  2. Match loam-migrate-host-config's case-4 convention (exit 2 on conflict).
  Recommendation: option 1 (exit 1 on launchctl error) — the helper's "conflict" case is functionally different from the host-config helper's case-4 (both dirs present); the launchd helper's failure mode is "launchctl returned an error", which mirrors orphan-plist-cleanup. Builder's call within AC.RNM-1c.3.
- D-build.M1c.4 — `Classification.ORPHAN_V2` / `ORPHAN_V1` enum value strings. The current strings are `"orphan_v2"` / `"orphan_v1"`. Option 1: keep verbatim (they describe historical shapes that are version-keyed by definition; the v1/v2 in the string IS the historical-shape identifier, not a brand version). Option 2: rename to e.g. `"orphan_pre_amendment_6"` / `"orphan_pre_pos_v2"`. Recommendation: option 1 (keep verbatim) — these identify historical shapes by their pre-#6 / pre-pos-v2 vintage, which is intrinsic to what the tool detects. Builder's call within AC.RNM-1c.5.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(Scope-mis-estimate disclosure — non-blocking; documented in §1.) The series-master §2 ladder's M1c row prices the fence at "2: hands-off-lifecycle, workspace-bootstrap".** Empirical surface inventory at plan time: **five sealed components** carry launchd label callsites:
   - **hands-off-lifecycle** (HOL): `tests/test_first_run.py` ~7 callsites in test fixtures + label-template assertions.
   - **workspace-bootstrap**: `src/.../first_run_scaffold.py` (`service_label()` + 2 docstrings) + `tests/test_first_run_scaffold.py` (~14 callsites) + `tests/test_AC_J_5_memory_write_worker_plist.py` (1 docstring) + `tests/test_D5_plist_path_emission.py` (1 sandbox-label) + `tests/test_no_sealed_amendments.py` (1 comment).
   - **memory-system**: `launchd/README.md` (4 prose callsites) + `launchd/com.pos-v2.memory-graphiti.plist` (filename + Label key body).
   - **primary-persona**: `src/cli.py` (1 docstring) + `src/memory_write_worker.py` (1 docstring) + `tests/test_AC_M_7_stop_returns_fast_write_async.py` (1 docstring).
   - **orchestrator**: `scripts/pos_session_start.py` (default kwargs `memory_label` + `orchestrator_label`).
   The dispatch's authority text ("All `com.pos-v2.<slug>.*` launchd labels across plist files, plist filenames, and bootstrap/teardown shell flow that reads/writes them") binds the scope to **all** label callsites. The series-master estimate was non-binding. Resolution: author the plan with the wider five-component fence; M1a + M1b absorbed the brand-keyed test-debt so this fence-breadth lands cleanly.
2. **(Verification result — non-blocking.) HC#4 byte-content sample is clean.** The fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (5 each from primary-persona, workspace-bootstrap, scope-of-work) contain ZERO plist references and ZERO launchd-label callsites (verified at plan time per M1b §11 finding #2 + re-confirmed at M1c plan time by re-reading the sample list). HC#4 should remain green post-M1c without retirement; H19 retire-and-rebaseline does NOT happen at M1c. Note: the dispatch's "first sub-amendment that may cross H19" framing was a series-master pre-emptive hedge; empirical surface confirms the byte-content sample is independent of M1c's scope.
3. **(Pre-emptive scope guard — non-blocking.) Orphan-plist-cleanup tool contract requires careful surgical editing.** The tool's classifier carries TWO arms describing pre-#6 historical shapes (`ORPHAN_V2` for `com.pos-v2.<single>`, `ORPHAN_V1` for `com.pos.<single>`) and ONE arm describing the live shape (`NAMESPACED_V2` for `com.pos-v2.<slug>.<kind>`). Per dispatch halt-trigger #7, the carve-out is inside M1c's scope: only the NAMESPACED arm rebases. The two ORPHAN arms describe genuine pre-#6 shapes whose `pos-v2` / `pos` literals are archaeological identifiers, not brand-keyed prose. Resolution: AC.RNM-1c.5 + Phase C's surgical edit instructions name exactly which lines change and which preserve.
4. **(Pre-existing tech-debt observed; non-blocking; resolved in-band per Phase A.) `framework/orchestrator/scripts/pos_session_start.py:126` has `orchestrator_label: str = "com.pos.orchestrator"` — a pre-amendment-#6 v1-shape single-segment default.** This is NOT `com.pos-v2.orchestrator`; it's `com.pos.orchestrator` (the pre-pos-v2 v1 era shape). Tracing callers: `ask_service_manager_to_start` is invoked from `run_session_start`'s `service_manager_fn` lambda fallback — `smf = service_manager_fn or (lambda: ask_service_manager_to_start(plat=plat))`. No live caller passes `orchestrator_label`; the default is used. Rendered the function's "find the .plist file at <label>.plist" loop dead because `~/Library/LaunchAgents/com.pos.orchestrator.plist` does NOT exist on any post-#6 host (the workspace-bootstrap scaffold writes namespaced labels). The function's Phase 4a behaviour is structurally a no-op for orchestrator (the warning "com.pos.orchestrator.plist not installed at ..." is appended but unconsumed by the `run_session_start` caller path). Resolution: rebrand both defaults — `memory_label="com.pos-v2.memory-graphiti"` → `memory_label="com.loam.memory-graphiti"`; `orchestrator_label="com.pos.orchestrator"` → `orchestrator_label="com.loam.orchestrator"`. The fact that the orchestrator default is functionally dead is a pre-existing tech-debt observation, not a methodology breach; rebranding it to `com.loam.orchestrator` preserves the function's API surface and keeps the symmetry with `memory_label`. **No live behaviour changes.** Recorded for FIDRAFT-or-future-cleanup ("ask_service_manager_to_start's orchestrator path is structurally dead post-amendment-#6; consider removing the per-label loop or making the labels mandatory parameters in a future cleanup amendment").
5. **(FUTURE_IDEAS_DRAFT — pre-emptive.)** Plan-time observation: a recurring pattern across the M1.rename series is "selective grep-rename — change live-shape literals, keep historical/archaeological literals". The `loam-rename-helper` script idea (M1a §11.5 + M1b §11.5) is reinforced by M1c's orphan-plist-cleanup case (`com.pos-v2.<single>` orphan literals must STAY; `com.pos-v2.<slug>.<kind>` namespaced literals must rename). Captured here for the build agent to surface to FIDRAFT post-build (do NOT extend M1c scope to add it).
6. **(No ODD §2.5 violation found in surrounding code/docs at plan-authoring time.)** The mechanical rename is the rename plus a sibling helper; no defensive `if`s without backing AC; no behaviour changes beyond the rename + helper. The five-component fence is wider than the series-master estimate (finding #1) but each component's rename-touched lines all trace back to AC.RNM-1c.1 / .2 / .3 / .4 / .5.
7. **(No methodology breach in plan structure.)** ACs are outcome-shape, deterministic, behaviour-count-checked. AC.RNM-1c.6 (negative AC enforcing the launchd-surface fence) is the explicit ODD §2.5 reverse-direction protection. The wider fence is disclosed (finding #1) so the dispatcher sees the surface in the plan-doc commit before the feature commit.
8. **(Pre-existing flaky test observation — non-blocking.) `framework/workspace-bootstrap/tests/test_D5_plist_path_emission.py::test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200`** is a launchd-touching test recorded as flaky at amendment #67's seal (per M1a §11.11 recovery flow). M1c renames its `sandbox_label = f"com.pos-v2.{sandbox_token}.memory-graphiti"` to `com.loam.<...>`. The flakiness was/is environmental (depends on a real launchd service responding to health probe — a host-quality issue, not a label-shape issue). M1c's rename does not fix the flakiness; it just rebrands the label string. **Build-time observation**: the test PASSED in the post-build touched-test rerun — the flakiness has been silent in the M1c build window. No FIDRAFT update needed.

**Build-time finding 9 (halt-trigger #2 fired; resolved in-band per ODD §4 retire-and-rebaseline).** During the post-Phase-A touched-test sweep, `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py::test_AC_D_1_5_byte_content_match_post_move[framework/primary-persona/src/cli.py-...]` failed: the post-rebrand SHA of `cli.py` no longer matched the pinned hash. Pre-build verification (finding #2) had asserted "ZERO plist references and ZERO launchd-label callsites in the fifteen sample files" by re-reading the sample list, but missed the cross-check: `cli.py`'s docstring at line ~147 contained `com.pos-v2.<slug>.memory-write-worker` (verbatim launchd-label literal in a docstring), which Phase A's mechanical rename touched. The dispatch's authority text named "HOL byte-content-match check" as a halt-and-surface trigger; the M1b §11 finding #2 verification was for `~/.pos/` and `POS_V2_*` callsites only, not for `com.pos-v2.*` launchd-label callsites — finding #2's transitive reuse was incomplete.

**Resolution.** ODD §4 in-band retire-and-rebaseline applied per the dispatch's named methodology heads-up: the SHA pin in `test_d1_byte_content_match.py` for `cli.py` was updated to the post-rebrand hash with a comment naming M1c amendment #78 + the cause. Methodology-aligned: the docstring rebrand is named AC-named work (AC.RNM-1c.1), not a silent content edit. The other fourteen sample files in HC#4 contain ZERO `com.pos-v2.*` callsites (confirmed by post-resolution re-read); HC#4 stays GREEN with the single SHA bump.

**Lesson for future renames in the M1.rename series.** Pre-build HC#4 verification must enumerate ALL renamed surfaces — not just the last sub-amendment's surfaces — and grep each HC#4 sample file for any of them. Forwarded to FIDRAFT-worthy convention update for the rename-helper idea (§11.5).

---

## 12. Method-decision register (placeholder)

The method-decision content for M1c lives in §14 below per the
`pos-amend seal --plan-doc` convention (which expects §14 as the
SHA-backfill anchor). Content moved to §14 to avoid duplication.

§14 anchored from authoring per M1b's recommendation (avoid post-seal
restructure) per M1b §1 + dispatch §Authority documents.

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the new helper's own tests.
- AC.RNM-1c.1: HOL `test_first_run.py` (T14 + AC7); workspace-bootstrap `test_first_run_scaffold.py` (H1 + AC1 + AC4 + AC5 + AC6 + AC8); workspace-bootstrap `test_AC_J_5_memory_write_worker_plist.py`; workspace-bootstrap `test_D5_plist_path_emission.py`; primary-persona `test_AC_M_7_stop_returns_fast_write_async.py`.
- AC.RNM-1c.2: read-back of `framework/memory-system/launchd/com.loam.memory-graphiti.plist` (renamed file's Label key contains `com.loam.memory-graphiti`).
- AC.RNM-1c.3: new helper `framework/tools/loam-migrate-launchd-labels/tests/test_migrate.py` + `test_cli.py` (≥4 tests covering empty-dir, one-orphan, multiple-orphans, launchctl-error).
- AC.RNM-1c.4: workspace-bootstrap `test_first_run_scaffold.py::test_AC4_*` + `test_AC5_*` + `test_AC6_*` (bootout-before-bootstrap call-sequence assertions; multi-workspace label-distinctness).
- AC.RNM-1c.5: orphan-plist-cleanup full test suite (`test_detector.py`, `test_apply.py`, `test_dry_run.py`).
- AC.RNM-1c.S: each sealed component's `test_no_sealed_amendments.py` + HOL `test_cross_cutting.py` (HC#4 sample remains green; H19 retirement NOT triggered).

### Backwards-compat verification

N/A — hard cutover per series-master D-RNM.3.

### HC#4 byte-content sample status

GREEN. The fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` were not touched by M1c's rename (verified pre-build per §11 finding #2). HC#4 retains its frozen-baseline; H19 retirement does NOT happen at M1c.

### Dependents cleared to dispatch

- **M1d** (OTel `pos.*` span/event roots → `loam.*`) cleared to dispatch. Dispatcher should author `docs/rebuild/plans/oss-v0-1-0-publish-rename-1d.md`.
- M1d..M1g remain serial in the shared tree per `feedback_serialize_amendment_builds`.

---

## 14. Method-decision register (post-build)

### D-build.M1c.1 — Migration helper path

**Sibling tool at `framework/tools/loam-migrate-launchd-labels/`** (option 1 from §10). Pattern follows the M1b `loam-migrate-host-config/` precedent: own `pyproject.toml`, own `src/loam_migrate_launchd_labels/` package (`__init__`, `__main__`, `cli`, `migrate`), own `tests/` with conftest + 15 tests, own `README.md`. Reasoning: clean separation from M1b's host-config helper (distinct surface — LaunchAgents/ vs ~/.pos/), easy to invoke independently, simplest test scaffold.

### D-build.M1c.2 — Orphan-plist-cleanup `Classification` enum rename

**Renamed `NAMESPACED_V2` → `NAMESPACED`** (option 1 from §10) — drops the version suffix matching the brand-side decision in `loam-rename-decisions.md` Tier-1 #4. Also renamed `NOT_POS_V2` → `NOT_LOAM` for symmetry (the "not this tool's mission" classification). Enum string values updated in lockstep (`namespaced_v2` → `namespaced`; `not_pos_v2` → `not_loam`). The tool has no out-of-tree consumers per its README; no compat shim needed. ORPHAN_V2 / ORPHAN_V1 enum names + value strings preserved verbatim per D-build.M1c.4.

### D-build.M1c.3 — Migration helper exit-code convention

**Exit 1 on PARTIAL_FAILURE; exit 0 on NOTHING_TO_MIGRATE or MIGRATED** (option 1 from §10). Mirrors orphan-plist-cleanup's `--apply` convention exactly. Failure detail emitted on stderr; processed-files summary on stdout. The CLI splits its formatted summary by line-prefix heuristic (lines starting with "FAILED" or "  " in failure mode → stderr). The MigrationOutcome enum carries three values (`NOTHING_TO_MIGRATE`, `MIGRATED`, `PARTIAL_FAILURE`); the `is_clean` predicate excludes only PARTIAL_FAILURE.

### D-build.M1c.4 — `Classification.ORPHAN_V2` / `ORPHAN_V1` enum value strings

**Kept verbatim** (option 1 from §10). The strings `"orphan_v2"` and `"orphan_v1"` identify pre-#6 historical shapes by their archaeological vintage, intrinsic to what the tool detects. The `pos-v2` literal in `ORPHAN_V2`'s docstring refers to "the pre-M1c shape" and is archaeological, not brand-keyed. ORPHAN_V2 + ORPHAN_V1 enum names + value strings + docstring references preserved verbatim.

### D-build.M1c.5 — Plist filename rename mechanism

**`git mv`** used. Single command: `git mv framework/memory-system/launchd/com.pos-v2.memory-graphiti.plist framework/memory-system/launchd/com.loam.memory-graphiti.plist`. Git's rename-detection threshold (~50% similarity by default) preserves blame for the renamed file because only the Label key body changed (1 line of 45). Verified by `git log --follow framework/memory-system/launchd/com.loam.memory-graphiti.plist` post-seal returning the file's full pre-M1c history.

### D-build.M1c.6 — Pre-existing tech-debt resolution: `pos_session_start.py:126` v1-shape default

**Both defaults rebranded in-band per §11 finding #4.** `memory_label="com.pos-v2.memory-graphiti"` → `memory_label="com.loam.memory-graphiti"`; `orchestrator_label="com.pos.orchestrator"` → `orchestrator_label="com.loam.orchestrator"`. The `orchestrator_label` v1-shape (`com.pos.<single>`, NOT `com.pos-v2.*`) was a pre-amendment-#6 default that no live caller passes; the function's Phase 4a behaviour is structurally a no-op for orchestrator (warning unconsumed by `run_session_start`'s caller path). Rebrand preserves the function's API surface + symmetry with `memory_label` without behaviour change. Recorded as a FIDRAFT-worthy observation: "ask_service_manager_to_start's orchestrator path is structurally dead post-amendment-#6; future cleanup amendment could remove the per-label loop or make labels mandatory parameters."

### D-build.M1c.7 — HC#4 byte-content sample retire-and-rebaseline (in-band per ODD §4)

Build-time finding #9 surfaced an HC#4 byte-content breach: `framework/primary-persona/src/cli.py`'s docstring at line ~147 contained `com.pos-v2.<slug>.memory-write-worker` which Phase A's mechanical rename touched. Pre-build verification (M1b §11 finding #2 transitive reuse) had only checked for `~/.pos/` and `POS_V2_*` callsites, missing `com.pos-v2.*` launchd-label callsites in the HC#4 sample. ODD §4 in-band retire-and-rebaseline applied: the SHA pin in `test_d1_byte_content_match.py` for `cli.py` updated to the post-rebrand hash (`ed2398283ae6259baff172f4eb629f5a38041d8a14e45c8f8f3da3b08efdc5d2`) with a comment naming M1c amendment #78 + the cause. Methodology-aligned: the docstring rebrand is named AC-named work (AC.RNM-1c.1), not a silent content edit. Other fourteen sample files contain ZERO `com.pos-v2.*` callsites (re-verified post-resolution); HC#4 stays GREEN with the single SHA bump.

### Commit SHAs

- **Series master plan-doc commit:** `ebe0a57` — `docs(plans): split M1 rename into multi-amendment series — D-RNM.1 ruling` (2026-04-29).
- **M1a seal commit:** `143d465` — `chore(seals): M1a docs/prose-only brand rebrand` (2026-04-29).
- **M1b seal commit (BASELINE for M1c):** `d97c8c1` — `chore(seals): M1b env-vars + per-host config dir` (2026-04-29).
- **M1c sub-plan + manifest commit:** `9c5deaf` — `docs(plans): author M1c sub-plan + manifest — launchd labels com.pos-v2.<slug>.* → com.loam.<slug>.* + plist filename cascade + sibling migration helper` (2026-04-29).
- **M1c feature commit:** `cd1d837` — `feat(rename-1c): launchd labels com.pos-v2.<slug>.<kind> → com.loam.<slug>.<kind> + plist filename cascade + sibling migration helper (amendment #78, AC.RNM-1c.1–AC.RNM-1c.S)` (2026-04-29).
- **pos-amend apply commit:** `431151d` — `chore(rename-1c-apply): pos-amend apply for amendment #78 (M1c launchd label rebrand)` (2026-04-29).
- **Seal commit:** `1e99d0b` — `chore(seals): M1c launchd label rebrand — com.pos-v2.<slug>.<kind> → com.loam.<slug>.<kind> (version suffix dropped concurrently per loam-rename-decisions Tier-1 #4) + plist filename cascade (memory-system historical-reference plist renamed via git mv) + orphan-plist-cleanup NAMESPACED arm rebases to com.loam.<slug>.<kind> (pre-#6 ORPHAN arms preserved) + sibling per-host migration helper at framework/tools/loam-migrate-launchd-labels/ (one-shot bootout-of-old + rename-aside; idempotent) — hands-off-lifecycle+workspace-bootstrap+memory-system+primary-persona+orchestrator at 431151d` (2026-04-29).
- **§14 SHA-register backfill commit:** `59af565` — `docs(plans): record amendment #78 commit SHAs in method-decision register` (2026-04-29; auto-emitted by `pos-amend seal --plan-doc`).
- **§11 build-time findings + §14 D-build sub-decision details follow-up commit (this commit):** TBD — `docs(plans): record M1c build-time findings (HC#4 retire-and-rebaseline) + D-build.M1c.* method-decision details` (2026-04-29).

Diff window: `d97c8c1..1e99d0b` (M1b-seal → M1c-seal).

---

## 15. References

- **Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Prior sub-amendments:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.md` (sealed `143d465`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.md` (sealed `d97c8c1`).
- **Authority documents (inherited from series master):**
  - `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 item 4.
  - `.scratch/claude-output/loam-rename-migration-plan.md` §3.4.
- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (M1c row already in §5 per M1b precursor commit `7be713b`).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply`.
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
  - `feedback_critical_thinking_on_deviations`.
  - `feedback_strict_autonomy_no_pause_for_authorized_work`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.manifest.yaml` (M1b sibling — establishes the manifest shape under the rename series; eleven-component fence).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.manifest.yaml` (M1a sibling — four-component docs-only fence).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1c is built using this CLI; rename to `loam amend` is M1e per dispatch §Scope).
- **M1b sibling helper precedent:** `framework/tools/loam-migrate-host-config/` (parallel structure for the new `framework/tools/loam-migrate-launchd-labels/` sibling helper).
- **Orphan-plist-cleanup tool:** `framework/tools/orphan-plist-cleanup/` (NAMESPACED-arm-only repoint per AC.RNM-1c.5; pre-#6 ORPHAN arms preserved verbatim).
