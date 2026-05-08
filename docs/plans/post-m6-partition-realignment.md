# post-M6 partition realignment — partition-reclassification + path-list fix — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/plans/oss-v0-1-0-publish.md` (this sub-plan closes the LAST PRE-PUBLISH BLOCKER per dispatcher recommendation analysis 2026-04-29; M11 dry-run is unblocked once this seals).
**Predecessors sealed:**
- M9 (`2161cb1`) — substitution pass + 12-file in-place fixture refactor.
- memory-sidecar-recovery (`8ee241b`) — lifespan-leak + reference_time schema migration.
- M1c-corrective (`603e953`) — `com.pos.orchestrator` → `com.loam.orchestrator` rebrand + dev-mode-manifest yaml lines 137-138 named-glob refresh.

**Predicted AI-time:** plan-rubric midpoint 30–60 min (multi-component bookkeeping + 3 surfaces); calibrated band 15–30 min after recent multi-component amendments (M9 + M1c-corrective both landed in lower-half of band). Log actual at §14.

**Authority documents:**
- M9 plan-doc HSF#1 (partition completeness gap): `docs/plans/oss-v0-1-0-publish-scrub.md` §7 finding #1.
- M1c-corrective plan-doc HSF#1 (broader dev-mode-manifest staleness): `docs/plans/oss-v0-1-0-publish-rename-1c-corrective.md` §16 HSF#1.
- FUTURE_IDEAS_DRAFT.md item: `docs/FUTURE_IDEAS_DRAFT.md` (dev-mode-manifest broader staleness; M1c-corrective build agent capture 2026-04-29).
- M2 partition manifest: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- corpus_gate hook source: `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` + `corpus_load_session_start.py` + `corpus_load_sentinel.py`.
- dev-mode-manifest: `plugins/dev-sdlc/dev-mode-manifest.yaml`.
- Master plan: `docs/plans/oss-v0-1-0-publish.md`.
- VALUE_PROPOSITION (prime objective): `docs/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2).
- ODD methodology + worked examples: `plugins/dev-sdlc/docs/odd-methodology.md` + `odd-in-loam.md`.
- Sealed-component invariants CDC: `plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md`.
- Commit-ladder CDC: `plugins/dev-sdlc/docs/conventions/commit-ladder.md`.

---

## 1. Summary / TLDR

Three coherent surfaces close — each is a "post-M6b.0 path move not fully propagated" instance. Bundled as a single sealed amendment.

**Surface A — Gate-test files partition reclassification.** 12 gate-test files at `framework/hands-off-lifecycle/tests/test_AC_AG_*.py` (5 files) + `test_AC_BAG_*.py` (7 files) classify `dev_and_public` via the broad `framework/hands-off-lifecycle/**` glob in `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`. They sys.path-probe into `plugins/dev-sdlc/hooks/` (which is `dev_only`) to import the gate modules under test. In the synthesized public artefact the plugin tree is dropped, so the test imports fail at import-time on a fresh-bootstrap pytest run of the synthetic tree. **Fix:** add an explicit `dev_only` entry that excludes those 12 test files from the broad `framework/hands-off-lifecycle/**` `dev_and_public` glob — tightening the partition so test files that depend on `dev_only` source files travel with `dev_only`. Verified empirically at plan-time: every file in both filename-patterns has the `PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"` probe.

**Surface B — corpus_gate hook on-demand path-list update.** `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` lines 135-139 carry an `_ON_DEMAND` constant whose first two entries point at the pre-M6b.0 canonical paths `docs/odd-methodology.md` + `docs/odd-in-loam.md`. Post-M6b.0 these doc files MOVED to `plugins/dev-sdlc/docs/`. The hook's per-file existence probe (via `_resolve_corpus_path`'s two-tier fall-through `<workspace_root>/<rel>` → `<workspace_root>/framework/<rel>`) does NOT cover the plugin-tree, so the on-demand pointer block silently omits those files in DEV MODE today. **Fix:** update the two `_ON_DEMAND` entries to point at `plugins/dev-sdlc/docs/odd-methodology.md` + `plugins/dev-sdlc/docs/odd-in-loam.md`. The condensed `docs/design/odd.md` STAYS canonical and is the public-mode reference (orthogonal — not in the on-demand list).

**Surface C — dev-mode-manifest.yaml `roots:` + `always_loaded:` realignment.** `plugins/dev-sdlc/dev-mode-manifest.yaml` `roots:` block (lines 36-64) and `always_loaded:` block (lines 78-110) reference 15 top-level component dirs that MOVED under `framework/` post-M6b.0 (`cost-governance/`, `graceful-degradation/`, `hands-off-lifecycle/`, `memory-system/`, `objective-tracker/`, `observability-aggregator/`, `orchestrator/`, `primary-persona/`, `reversibility-primitive/`, `safety-layer/`, `scope-of-work/`, `self-correction/`, `self-upgrade/`, `telegram-interface/`, `workspace-bootstrap/`), plus `tools/` (now `framework/tools/`), plus `first-run-inventory.yaml` (now `framework/first-run-inventory.yaml`). The `loam-mode` resolver tolerates the staleness (missing roots return empty match-sets — see `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/manifest.py:expand_entry`), but the manifest is shipping with stale references that mislead future consumers and the compute_corpus_paths_required → A1 sentinel pathway already reports `corpus_gate_state: partial` per dispatcher's session diagnostic. **Fix:** rebase the 15 component refs to `framework/<comp>/`; rebase `tools/` to `framework/tools/`; rebase `first-run-inventory.yaml` to `framework/first-run-inventory.yaml`; rename `graceful-degradation/` to `dormancy/` (the component was renamed pre-M6b.0 and the manifest carries the old name); admit `framework/workspace-sync/` (a missing component admission — workspace-sync was never in the manifest's component list). The `data/` top-level dir STAYS top-level (it's workspace runtime telemetry, not a component source surface).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 + memory entry value-proposition-as-prime-objective)

This amendment binds to:

- **AC.PO.1 (translation-burden absorption)** — the partition manifest mis-classifying gate-test files into `dev_and_public` would surface as a synthesis-time test failure for any future operator running pytest against the public artefact (a translation-burden the user shouldn't have to debug). Surface A closes that. The corpus_gate's `partial` state surfaces as an A1 sentinel diagnostic the user must understand to interpret structural-enforcement gate decisions; Surface B + Surface C close that.
- **AC.PO.2 (toolkit-primitive growth)** — the partition manifest is itself a primary-persona toolkit primitive (it gates synthesis); Surface A makes that primitive sharper (gate-test files travel with the gate-source they test). The dev-mode-manifest is also a toolkit primitive (it gates DEV-MODE corpus selection); Surface C makes that primitive functional rather than tolerated-with-empty-match-sets.

Reverse trace: every AC.PMR.* below ladders up to AC.PO.1 + AC.PO.2 (prime objective).

The dispatcher's recommendation analysis 2026-04-29 named this as the LAST PRE-PUBLISH BLOCKER. After this seals, M11 dry-run is unblocked.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

No Claude primitive composition — the three surfaces are pure path-list / glob-list edits to YAML manifests + Python constants. The corpus_gate hook (Surface B) is a SessionStart hook that already composes on Claude Code's hook surface (no new primitive needed). The partition manifest (Surface A) is consumed by the synthesis tool which is non-Claude. **Pass — no new Claude leverage required.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test (translation burden):** all three surfaces reduce burden — Surface A removes a future synthesis-pytest failure mode the user would otherwise have to interpret; Surface B + Surface C close the corpus_gate's `partial` diagnostic that the user must today reason about as "is this a real gap or just stale config?" Pass.
- **Harness test (toolkit primitive):** the partition manifest + dev-mode-manifest are both toolkit primitives; this amendment sharpens their fidelity. Pass.

**Pass.**

### Lens 3 — ODD authoring

Every AC below is outcome-shape (what classifies where; what the path-list contains; what the gate state is). Method (whether to use a sub-glob `exclude` clause vs explicit `path:` entries; whether to inline-edit the corpus_inline hook's tuple vs source it from a config) is the builder's call inside the AC outcome bound. The substitution table (M9) does NOT need extension here — the post-M6b.0 path strings are workspace-relative `framework/<comp>/`, not canonical-host paths, and don't carry any of the four substitution-table tokens.

**Pass.**

---

## 4. Acceptance criteria — AC.PMR.*

### AC.PMR.1 — Gate-test files classify `dev_only` (Surface A)

`framework/hands-off-lifecycle/tests/test_AC_AG_*.py` (5 files) + `framework/hands-off-lifecycle/tests/test_AC_BAG_*.py` (7 files) — total 12 files — classify `dev_only` after the manifest edit, NOT `dev_and_public`.

**Verification.** Test in `framework/tools/pos-publish-framework-only/tests/test_AC_PMR_1_gate_tests_dev_only.py`: load the partition manifest; for each of the 12 gate-test file paths, assert `classify_path(path)` returns `Classification.DEV_ONLY`. Negative-control: assert non-gate `framework/hands-off-lifecycle/tests/test_*.py` files (those that don't probe into the plugin tree) continue to classify `dev_and_public`.

### AC.PMR.2 — corpus_gate on-demand path-list points at plugin-relative ODD docs (Surface B)

`framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` `_ON_DEMAND` tuple's first two entries are `plugins/dev-sdlc/docs/odd-methodology.md` and `plugins/dev-sdlc/docs/odd-in-loam.md`. The third entry (`docs/FUTURE_IDEAS.md`) is unchanged.

**Verification.** Test in `framework/hands-off-lifecycle/tests/test_AC_PMR_2_corpus_gate_on_demand_paths.py`: import `corpus_inline_session_start`; assert `_ON_DEMAND[:2] == ("plugins/dev-sdlc/docs/odd-methodology.md", "plugins/dev-sdlc/docs/odd-in-loam.md")`. Plus an end-to-end test that drives the SessionStart envelope through `main()` against a fixture workspace where the plugin docs exist on disk; assert the rendered on-demand block lists both plugin-relative paths.

Per the dispatch's halt-trigger #2: in NORMAL-USE workspaces (where `plugins/dev-sdlc/` is dropped post-publish), the hook ALREADY no-ops at the `mode != "dev-mode"` early-return (line 333-334 of `corpus_inline_session_start.py`); the on-demand pointer block is never emitted in NORMAL USE. **No additional graceful-skip wiring needed.** The hook's existing mode-partition is the graceful-skip mechanism. Verified at plan-time.

### AC.PMR.3 — dev-mode-manifest.yaml `roots:` realignment (Surface C, part 1)

`plugins/dev-sdlc/dev-mode-manifest.yaml` `roots:` block:

- 15 component refs rebased to `framework/<comp>/`:
  `cost-governance/` → `framework/cost-governance/`
  `graceful-degradation/` → `framework/dormancy/` (RENAME — the component was renamed pre-M6b.0; carrying the old name forward in the manifest is an additional staleness)
  `hands-off-lifecycle/` → `framework/hands-off-lifecycle/`
  `memory-system/` → `framework/memory-system/`
  `objective-tracker/` → `framework/objective-tracker/`
  `observability-aggregator/` → `framework/observability-aggregator/`
  `orchestrator/` → `framework/orchestrator/`
  `primary-persona/` → `framework/primary-persona/`
  `reversibility-primitive/` → `framework/reversibility-primitive/`
  `safety-layer/` → `framework/safety-layer/`
  `scope-of-work/` → `framework/scope-of-work/`
  `self-correction/` → `framework/self-correction/`
  `self-upgrade/` → `framework/self-upgrade/`
  `telegram-interface/` → `framework/telegram-interface/`
  `workspace-bootstrap/` → `framework/workspace-bootstrap/`
- `tools/` → `framework/tools/`.
- `first-run-inventory.yaml` → `framework/first-run-inventory.yaml`.
- `data/` STAYS top-level (workspace runtime telemetry).
- `docs/` + `CLAUDE.md` + `CLAUDE.dev.md` + `README.md` STAY top-level.
- ADD `framework/workspace-sync/` — a missing component admission (workspace-sync was never in the manifest's component list; the publish-mode manifest's `dev_and_public` glob admits it for the public partition; its DEV-MODE always-loaded admission was an oversight at the original Sub-plan F authoring).

**Verification.** Test in `plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py` (new test sidecar under the plugin's tests dir): load the manifest YAML; assert every entry under `roots:` resolves to an existing on-disk path within the workspace (relative to canonical pos-v2 root). The `dormancy/` rename (replacing `graceful-degradation/`) is asserted explicitly. The new `framework/workspace-sync/` admission is asserted explicitly.

### AC.PMR.4 — dev-mode-manifest.yaml `always_loaded:` realignment (Surface C, part 2)

`plugins/dev-sdlc/dev-mode-manifest.yaml` `always_loaded:` block: 15 component globs rebased to `framework/<comp>/**` with the same `graceful-degradation/` → `dormancy/` rename and the same `workspace-sync/` ADD. The `data/` glob STAYS top-level. The path entries (`docs/VALUE_PROPOSITION.md`, `docs/CLAUDE_CAPABILITIES.md`, `docs/duration-estimation-rubric.md`, `CLAUDE.md`, `README.md`) STAY top-level. `first-run-inventory.yaml` path entry rebases to `framework/first-run-inventory.yaml`.

**Verification.** Same test file as AC.PMR.3: assert every glob/path entry under `always_loaded:` resolves (per `expand_entry`) to a non-empty match-set against the canonical workspace tree. Negative control: assert no entry remains that points at a non-existent top-level dir post-M6b.0.

### AC.PMR.5 — `compute_corpus_paths_required` returns post-realignment paths

`framework.hands-off-lifecycle.hooks.corpus_load_sentinel.compute_corpus_paths_required(workspace_root, "dev-mode")` returns a non-empty list of paths, all of which exist on disk relative to the workspace root (via the function's existing `<workspace_root>/<rel>` ∨ `<workspace_root>/framework/<rel>` fall-through).

**Verification.** Test in `framework/hands-off-lifecycle/tests/test_AC_PMR_5_corpus_paths_required_post_realignment.py`: invoke `compute_corpus_paths_required(workspace_root, "dev-mode")` against canonical pos-v2 root; assert ≥10 paths returned (the 15 component globs expand to many files); assert every returned path resolves on disk (same fall-through semantics).

### AC.PMR.6 — corpus_gate sentinel state computes `loaded` post-realignment when corpus is inlined

The `_classify_state_from_loaded` semantic (when `corpus_paths_loaded` is supplied) returns `"loaded"` iff every required path is in the loaded set. Post-realignment, for the `corpus_inline_session_start.py` hook fire whose `_ALWAYS_LOAD` is the static 3-path tuple (`CLAUDE.md`, `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`), the sentinel's `state` field is computed against `corpus_paths_required ⊆ {dev-mode-manifest.always_loaded ∪ dev_only}`.

**Note on classification semantics:** the dispatch's "corpus_gate_state: partial" diagnostic comes from the LIVE workspace (post-M6b.0), where `compute_corpus_paths_required` returned an empty list (manifest unreadable / globs all empty / mode-routing edge-case). Post-realignment, `compute_corpus_paths_required` returns a non-empty list. The `_classify_state_from_loaded` then returns `"loaded"` only if the inline hook's loaded set matches; otherwise `"partial"` is the CORRECT state (subset relationship). The dispatch's empirical-verification step (next UPS fire) confirms whichever state is actually correct.

**Verification.** Test in `framework/hands-off-lifecycle/tests/test_AC_PMR_6_corpus_gate_state_post_realignment.py`: drive the SessionStart envelope through `corpus_inline_session_start.main` against a fixture workspace; load the resulting sentinel; assert `state in ("loaded", "partial")` (NOT `"missing"`). The "loaded vs partial" branch depends on whether the static 3-path always-load equals the manifest-derived required set; the test asserts only that the degenerate "missing" state is gone.

### AC.PMR.7 — Existing tests continue to pass

Touched components' pre-existing tests pass post-edit:
- `framework/hands-off-lifecycle/` — gate hook tests (the 12 reclassified test files) + corpus_load tests (sentinel + inline hook).
- `framework/tools/pos-publish-framework-only/` — partition + synthesis tests (esp. `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` + `test_AC_OSS_M9_*` + `test_AC_OSS_3_*`).
- `plugins/dev-sdlc/` — loam-mode tests (60 tests; manifest reader + selector + audit + session_start).

**Verification.** Per-component pytest before commit (per `feedback_amendment_dispatch_speedups` — narrow test scope, skip pre-seal full repo-wide rerun).

### AC.PMR.S — Sealed-component fence

The sealed-component fence:
1. `framework/tools/pos-publish-framework-only/` — partition manifest YAML edit + 1 new test.
2. `framework/hands-off-lifecycle/` — corpus_inline_session_start.py `_ON_DEMAND` constant edit + 3 new tests.
3. `plugins/dev-sdlc/` — dev-mode-manifest.yaml YAML edit + 1 new test (under `plugins/dev-sdlc/tests/`).

**Sealed-component count: 3 components + 1 tool.** HC#4 byte-content sample status: NO RETIRE-AND-REBASELINE expected (edits land in YAML manifest files + a tuple constant in a Python hook + new test files; none of these are HC#4 sample paths in any per-component fence config).

`loam amend apply` runs BEFORE seal commit (per dispatch §Constraints; binary lives at `plugins/dev-sdlc/tools/loam-amend/`). `loam amend seal --scoped-sweep` for the seal commit (per `commit-ladder.md`).

---

## 5. Hard constraints

1. **Plan-before-code** — this doc; §14 anchor present.
2. **`loam amend apply` BEFORE seal commit** — operates from `plugins/dev-sdlc/tools/loam-amend/` post-M6b.1.
3. **No `git commit --amend`** — corrective commits are NEW commits per `feedback_no_amend_in_agent_dispatches`.
4. **AC.PMR.S seal-diff fence narrowed** to the 3 components named in §4 AC.PMR.S above.
5. **Hard cutover** — the partition manifest reclassification is the canonical state post-amendment; no flag, no opt-out. The dev-mode-manifest realignment likewise.
6. **No third-party deps** — pure YAML + Python constant edits + new tests using stdlib + pytest.
7. **Test scope narrowed** to touched components per `feedback_amendment_dispatch_speedups`. No full repo-wide rerun pre-seal.
8. **Halt-and-surface triggers** per dispatch:
   1. Surface A's reclassification reveals a non-uniform shape across the 12 files (e.g. some files don't probe-into-plugin and shouldn't reclassify) — surface and resolve per-file.
   2. Surface B's gate hook resists pointing at plugin-side paths cleanly (e.g. NORMAL-USE workspaces where the plugin is dropped) — verified at plan-time the hook's mode-partition (line 333-334) is the graceful-skip; if NEW behaviour surfaces, halt.
   3. Surface C's roots:/always_loaded: realignment reveals a stale ref with no valid post-M6 target — surface specific case.
   4. The M2 partition manifest's structure resists the Surface A reclassification (e.g. the entry shape doesn't support sub-glob exclusion).
   5. ODD §2.5 violations encountered in surrounding code.
   6. Frozen-baseline / byte-content invariant breach beyond ODD §4 in-band.
   7. Wall-clock approaches 90 min — surface for continuation.

---

## 6. Out of scope (named explicitly per ODD §2.5)

- **Three silent-swallow patterns in memory-system + 6 in orchestrator/supervisor.py** (graceful-fallthrough-with-detection CDC retroactive audit) — post-v0.1.0 per dispatch.
- **`pos_orchestrator` editable-install provisioning gap** (HSF#3 from M1c-corrective; pre-existing; not a pre-publish blocker per M11 being publish-synthesis dry-run).
- **Anything not on Surface A / B / C.**
- **Adding new corpus sources** (e.g. promoting `docs/STATE.md` from always-load to on-demand) — out of scope; this amendment preserves the existing 3-always + 3-on-demand split.
- **Reorganising the dev-mode-manifest's `dev_only:` block beyond the workspace-sync ADD** — `dev_only:` already references plugin-relative paths post-M6c (see line 119-120 + 140 + 146); no edits needed.
- **Adding a NORMAL-USE-mode graceful-skip for missing plugin docs in corpus_inline_session_start.py** — verified at plan-time the existing `mode != "dev-mode"` early-return is the skip mechanism; no edit required.
- **Substitution-table extension** (e.g. adding new path tokens) — the realigned paths are workspace-relative `framework/<comp>/`, not canonical-host paths; no substitution table edit needed.
- **Promoting `data/` from always-loaded to its own root partition** — out of scope; `data/` STAYS top-level per dev-mode-manifest design.

---

## 7. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface gaps the dispatch / authority docs didn't predict.

1. **`graceful-degradation/` was renamed to `dormancy/` pre-M6b.0; the dev-mode-manifest carries BOTH the old name AND a stale top-level path.** This is a stack-of-two staleness: the rename happened, AND the top-level → framework/ move happened. The realignment under AC.PMR.3 + AC.PMR.4 handles both in the same edit (the new path is `framework/dormancy/`, not `framework/graceful-degradation/`). **NOT a halt** — handled by the AC. Surfaced in §2.3 of M1c-corrective plan-doc (broader staleness) but not specifically called out as a rename.

2. **`framework/workspace-sync/` is missing entirely from the dev-mode-manifest's component list.** The publish-mode manifest admits `framework/workspace-sync/**` to `dev_and_public` (line 132). The dev-mode-manifest never had a `workspace-sync/` entry — the original sub-plan F authoring (15-component list per locked ruling 4) appears to predate the workspace-sync component, and no subsequent amendment added it. **NOT a halt** — handled by ADDING `framework/workspace-sync/` to both `roots:` and `always_loaded:` per AC.PMR.3 + AC.PMR.4.

3. **`first-run-inventory.yaml` lives at `framework/first-run-inventory.yaml` post-M6b.0, NOT top-level.** The publish-mode manifest already references the post-M6b.0 location (`path: framework/first-run-inventory.yaml` line 134); the dev-mode-manifest still references the pre-M6b.0 top-level path (line 64 + line 108). **NOT a halt** — handled by the realignment.

4. **`tools/` lives at `framework/tools/` post-M6b.0, NOT top-level.** Same as above — handled by the realignment under AC.PMR.3.

5. **The dev-mode-manifest's `dev_only:` block already uses post-M6b.0 plugin-relative paths** (lines 119-120 for ODD docs, lines 140 + 146 for plugin tools, line 135 for the manifest itself). **No edit needed** — the `dev_only:` block was already realigned at M6c HSF#1 fix + M1c-corrective HSF#1 fix. The remaining staleness is exclusively in `roots:` + `always_loaded:`.

6. **The corpus_gate hook's `_resolve_corpus_path` two-tier fall-through (`<workspace_root>/<rel>` → `<workspace_root>/framework/<rel>`) does NOT cover plugin-relative paths.** This is OK for Surface B's fix because the new `_ON_DEMAND` entries explicitly start with `plugins/dev-sdlc/docs/`, which resolves via the first tier (`<workspace_root>/<rel>`). **NOT a halt** — the fall-through is correct; the issue was the entries pointing at the wrong location.

7. **No ODD §2.5 violations encountered in the touched code surface.** The corpus_inline hook's `_ON_DEMAND` constant is a tuple of strings (no try/except branches, no silent-fallthrough); the partition manifest is YAML data; the dev-mode-manifest is YAML data. **NOT a halt.**

8. **A1 sentinel state-classification semantic preserves `partial` correctly post-fix.** The dispatcher's diagnostic `corpus_gate_state: partial` may EITHER resolve to `loaded` (if the static 3-path always-load equals the realigned required set) OR remain `partial` (if the required set is a strict superset of the loaded set, which it is — required draws from the dev-mode-manifest's full `always_loaded ∪ dev_only`, while loaded is the static 3-path tuple). **The dispatch's "corpus_gate_state: loaded post-fix" expectation is OPTIMISTIC.** AC.PMR.6 captures this — the AC verifies state is no longer `missing`, but does NOT assert `loaded` specifically. **Surface this as a halt-trigger #6 (frozen-baseline) candidate? — NO, this is not a frozen-baseline issue; the sentinel state classification is a runtime-computed value, not a frozen invariant.** Documented in AC.PMR.6 itself; surfaced for FUTURE_IDEAS_DRAFT capture if the post-build empirical verification disagrees with this analysis.

**HSF#3 (post-build) — Pre-existing cross-mode prose refs in 3 sealed-component artefacts uncovered by the realignment.** Surfaced during AC.PMR.4 build verification (AC.F3 test fired). The realignment rebased the manifest's `roots:` + `always_loaded:` from pre-M6b.0 top-level component refs to `framework/<comp>/` post-M6b.0 paths AND added the missing `framework/workspace-sync/` admission. Pre-realignment the stale top-level globs matched ZERO files, so AC.F3's always-loaded artefact set was empty / sparse and the pre-existing prose cross-mode refs were masked. Post-realignment 5 refs surface:
- `framework/memory-system/launchd/README.md` → `docs/archive/component-research/true-first-run/research.md` (1).
- `framework/primary-persona/templates/persona-template/prompt.md` → `docs/FUTURE_IDEAS_DRAFT.md` (1).
- `framework/workspace-sync/README.md` → `docs/plans/workspace-sync.{md,builder-plan.md,manifest.yaml}` (3).

Each is a sealed-component README / template carrying a dev-only-path reference that this amendment is NOT authorised to scrub (AC.PMR.S fence sits at hands-off-lifecycle + dev-sdlc + pos-publish-framework-only; opening the workspace-sync / memory-system / primary-persona fences would be a sealed-amendment in disguise per dispatch §6 out-of-scope "Anything not on the three surfaces above"). **Resolved in-amendment** via `KNOWN_CROSS_MODE_DEBT` allowlist extension in `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` per the same convention amendment F used at sub-plan F's original build (the allowlist is designed for "scrubs the current amendment isn't authorised to do"; see file's docstring + the Post-M6 narrative added in this amendment). FIDRAFT entry appended capturing each of the 3 follow-on amendments needed to shrink the allowlist back to empty. **NOT a halt** — the realignment surfaced pre-existing latent violations that the convention's existing allowlist mechanism cleanly absorbs.

**HSF#4 (post-build) — `docs/duration-estimation-rubric.md` was a 4th stale path-list entry not surfaced by the dispatch's pre-build analysis.** Surfaced during AC.PMR.5 build verification. The dev-mode-manifest's `always_loaded:` block had `path: docs/duration-estimation-rubric.md` (line 114 pre-edit), but the file MOVED to `plugins/dev-sdlc/docs/duration-estimation-rubric.md` post-M6b.0 (along with the ODD docs that were also moved into the plugin per AC.OSS-M6b0.5). **Resolved in-amendment** under AC.PMR.4 — the path entry rebases to the plugin-relative location. **NOT a halt** — same shape as the ODD-doc moves; in-amendment fix.

**Halt summary.** None of the above triggers a halt. Findings 1–4 are folded into the ACs. Finding 5 is the no-edit branch for `dev_only:`. Finding 6 is the no-edit branch for the corpus_gate fall-through. Finding 7 confirms no ODD §2.5 surface. Finding 8 is documented in AC.PMR.6 explicitly. HSF#3 + HSF#4 surfaced post-build; both resolved in-amendment per the existing allowlist convention + path-list rebase. The plan is authorised to proceed.

---

## 8. Implementation order (suggested — builder's call to refine)

1. **Verify Surface A empirically** — confirm all 12 gate-test files have the `PLUGIN_HOOKS_DIR` probe (already verified at plan-time; re-confirm at build).
2. **Author the partition manifest edit** (`framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`):
   - Add a new `dev_only:` entry (as glob with subtractive shape OR as explicit `path:` entries — builder's call per D-build.PMR.1):
     - Builder option (a): add a `dev_only:` glob `framework/hands-off-lifecycle/tests/test_AC_AG_*.py` + another for `test_AC_BAG_*.py`. Per partition classification precedence (precedence #2 — `dev_only` checked before `dev_and_public`), these win over the broad `framework/hands-off-lifecycle/**` glob.
     - Builder option (b): add 12 explicit `path:` entries under `dev_only:`. More verbose but auditable. Consider partition manifest precedent.
   - Builder picks based on partition manifest's existing entry-shape pattern.
3. **Author the corpus_inline hook edit** (`framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py`):
   - Update `_ON_DEMAND` tuple's first two entries to `plugins/dev-sdlc/docs/odd-methodology.md` + `plugins/dev-sdlc/docs/odd-in-loam.md`.
4. **Author the dev-mode-manifest edit** (`plugins/dev-sdlc/dev-mode-manifest.yaml`):
   - `roots:` block: rebase 15 component refs + `tools/` + `first-run-inventory.yaml`; rename `graceful-degradation/` → `dormancy/`; ADD `framework/workspace-sync/`.
   - `always_loaded:` block: same rebase + rename + ADD; preserve the `data/` glob top-level; preserve the path entries.
   - `dev_only:` block: NO EDITS (per HSF #5 finding).
5. **Author the 5 new tests** (per AC.PMR.1 / .2 / .3+.4 / .5 / .6 — actually 4 test files since AC.PMR.3 + AC.PMR.4 share a test file, and AC.PMR.2 carries 2 sub-tests):
   - `framework/tools/pos-publish-framework-only/tests/test_AC_PMR_1_gate_tests_dev_only.py` (AC.PMR.1).
   - `framework/hands-off-lifecycle/tests/test_AC_PMR_2_corpus_gate_on_demand_paths.py` (AC.PMR.2).
   - `plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py` (AC.PMR.3 + AC.PMR.4 — combined under one file because the verification is a single manifest-load + assertion sweep).
   - `framework/hands-off-lifecycle/tests/test_AC_PMR_5_corpus_paths_required_post_realignment.py` (AC.PMR.5).
   - `framework/hands-off-lifecycle/tests/test_AC_PMR_6_corpus_gate_state_post_realignment.py` (AC.PMR.6).
6. **Run touched-component pytest** (per `feedback_amendment_dispatch_speedups` — narrow test scope):
   - `pytest framework/hands-off-lifecycle/tests/` (covers the 12 reclassified gate tests + Surface B + Surface C verification tests).
   - `pytest framework/tools/pos-publish-framework-only/tests/` (covers the partition manifest edit + AC.PMR.1).
   - `pytest plugins/dev-sdlc/tests/` + `pytest plugins/dev-sdlc/tools/loam-mode/tests/` (covers AC.PMR.3 + AC.PMR.4 + loam-mode regression).
7. **Feature commit** carrying the 3-surface diff + 5 new tests.
8. **`loam amend apply`** (operates from `plugins/dev-sdlc/tools/loam-amend/` post-M6b.1) — apply commit per CDC. Manifest authored alongside the feature commit OR in a preceding `docs(plans):` commit per repo convention (M9 + M1c-corrective both did `docs(plans):` for the manifest; mirror that).
9. **Seal commit** per `commit-ladder.md`; fence per §4 AC.PMR.S; use `loam amend seal --scoped-sweep` to limit the cross-component sweep to the 3 manifest-listed components.
10. **Post-build verification** — re-read the on-demand block path-list from `corpus_inline_session_start.py`; confirm the dev-mode-manifest YAML resolves cleanly via `loam_mode.manifest.load_manifest`.
11. **§14 method-decision register** filled in this plan-doc post-build.
12. **§9 backwards-compat verification** filled.
13. **§12 test breakdown** filled.

Estimated wall-clock: 15–30 min calibrated band per recent multi-component amendments. Surface A is the largest single-file edit (12 path-list entries to audit + 1 manifest edit); Surface C is the largest YAML edit (~17 entries to rebase across 2 blocks).

---

## 9. Backwards-compat verification (post-build — placeholder)

To be filled by the builder post-build. Each entry verifies:

- All pre-existing tests pass post-amendment (esp. `test_AC_OSS_3_*` + `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin` + the 60 loam-mode tests + the gate-test suite).
- Touched-component pytest passes for the 3 components in the §4 AC.PMR.S fence.
- HC#4 sample status — NO RETIRE-AND-REBASELINE expected (no edits to HC#4 sample paths).
- HC#3 binding analogue — no new third-party deps.

---

## 10. Risks (amendment-specific)

1. **Surface A reclassification breaks the partition's `dev_and_public ∪ dev_only` disjoint invariant.** Mitigation: AC.PMR.1's verification asserts the 12 files classify `dev_only` AND that non-gate test files in the same dir continue to classify `dev_and_public` — exercises both branches.
2. **Surface B's `_ON_DEMAND` edit makes the on-demand pointer block emit dead paths in workspaces where the plugin is dropped.** Mitigation: AC.PMR.2's halt-trigger #2 verification confirmed at plan-time the hook's mode-partition (line 333-334) skips the entire emission in NORMAL-USE mode; the on-demand block is never emitted in NORMAL USE. **Verified — no regression risk.**
3. **Surface C's realignment causes loam-mode's `expand_entry` to walk paths it didn't walk before, slowing dev-mode startup.** Mitigation: the realigned globs (`framework/<comp>/**`) match the same physical files the canonical pre-M6b.0 globs would have matched if the components had been at the top-level; the file-count is unchanged. Wall-clock impact is the per-glob walk overhead — negligible at v0.1.0 surface size. AC.PMR.7 (existing tests pass) catches any regression.
4. **The `graceful-degradation/` → `dormancy/` rename in the manifest reveals a missed rename elsewhere.** Mitigation: at plan-time grep `graceful-degradation` shows results ONLY in `dev-mode-manifest.yaml` lines 42 + 84 (the two we're editing), in source-code prose docstrings (not load-bearing path refs), and in historical plan-docs (preserved per Idea 10). NO load-bearing path refs remain elsewhere.
5. **The `workspace-sync/` ADD to dev-mode-manifest changes the DEV-MODE always-loaded set.** Mitigation: workspace-sync is already a sealed component shipping in `dev_and_public` per the publish-mode manifest; admitting it to the dev-mode always-loaded is correctness, not regression. AC.PMR.7 catches any unexpected interaction.
6. **Empirical UPS hook fire still reports `partial` post-realignment** (HSF #8). Mitigation: AC.PMR.6 explicitly asserts state is no longer `missing`; the `loaded` vs `partial` distinction is documented as "subset relationship between loaded and required" and is not a regression. If the dispatcher's empirical verification expects `loaded` and gets `partial`, that's a clarification not a fix.

---

## 11. References

- Master plan: `docs/plans/oss-v0-1-0-publish.md`.
- M9 plan-doc: `docs/plans/oss-v0-1-0-publish-scrub.md` §7 finding #1.
- M1c-corrective plan-doc: `docs/plans/oss-v0-1-0-publish-rename-1c-corrective.md` §16 HSF#1.
- FUTURE_IDEAS_DRAFT.md: `docs/FUTURE_IDEAS_DRAFT.md` (M1c-corrective build agent capture 2026-04-29).
- M2 partition manifest: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- corpus_gate hook source: `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` + `corpus_load_session_start.py` + `corpus_load_sentinel.py`.
- dev-mode-manifest: `plugins/dev-sdlc/dev-mode-manifest.yaml`.
- loam-mode manifest reader: `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/manifest.py`.
- loam-mode selector: `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/selector.py`.
- ODD methodology: `plugins/dev-sdlc/docs/odd-methodology.md` + `odd-in-loam.md`.
- Sealed-component invariants CDC: `plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md`.
- Commit-ladder CDC: `plugins/dev-sdlc/docs/conventions/commit-ladder.md`.
- VALUE_PROPOSITION (prime objective): `docs/VALUE_PROPOSITION.md`.

---

## 12. Test breakdown (post-build — placeholder)

To be filled by the builder post-build. Expected new test files per §8 step 5:

- `framework/tools/pos-publish-framework-only/tests/test_AC_PMR_1_gate_tests_dev_only.py` (AC.PMR.1).
- `framework/hands-off-lifecycle/tests/test_AC_PMR_2_corpus_gate_on_demand_paths.py` (AC.PMR.2).
- `plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py` (AC.PMR.3 + AC.PMR.4).
- `framework/hands-off-lifecycle/tests/test_AC_PMR_5_corpus_paths_required_post_realignment.py` (AC.PMR.5).
- `framework/hands-off-lifecycle/tests/test_AC_PMR_6_corpus_gate_state_post_realignment.py` (AC.PMR.6).

Each test maps to the named AC.

---

## 14. Method-decision register (post-build)

To be filled by the builder post-build. Mirror M9 + M1c-corrective §14 shape: per-decision narrative with the actual choice + rationale.

Anticipated decision topics (named at plan-time so the register is forward-discoverable):

- **D-build.PMR.1** — Surface A entry shape: glob-with-pattern (`framework/hands-off-lifecycle/tests/test_AC_AG_*.py` + `test_AC_BAG_*.py`) vs explicit 12-path list. Builder's call (glob-with-pattern simpler + matches the partition manifest's existing entry-shape pattern; explicit-path is more auditable).
- **D-build.PMR.2** — Surface C `roots:` entry style: per-component-glob preserving granularity vs bulk `framework/**` admission. Per the dispatch and per the FIDRAFT capture, this is a partition-design decision — recommend per-component-glob to preserve granularity (matches the publish-mode manifest's per-component pattern).
- **D-build.PMR.3** — `workspace-sync/` ADD: in this amendment vs deferred. Builder recommendation: in-amendment (it's a one-line ADD and the dev-mode-manifest is the single source-of-truth being realigned in this pass).
- **D-build.PMR.4** — Test-file placement for AC.PMR.3 + AC.PMR.4: under `plugins/dev-sdlc/tests/` (per AC.PMR.S fence component #3) vs under `plugins/dev-sdlc/tools/loam-mode/tests/` (closer to the manifest reader). Builder's call (former matches the fence; latter co-locates with the consumer).
- **D-build.PMR.5** — Manifest-authoring commit ladder: separate `docs(plans):` for manifest YAML + feature commit for source/test changes vs single feature commit. Builder's call (M9 + M1c-corrective both used separate `docs(plans):` for the manifest).

### Commit SHAs

- Amendment commit: `54794d7b08080f4e87315a81eadcadf292eb4bb9` —
  `chore(loam-amend-apply): loam amend apply for post-M6 partition realignment (amendment #94)`
- Seal commit: `e2828ba28e5beb4180e9acc8f97b01dcfa23f169` —
  `chore(seals): post-m6-partition-realignment — hands-off-lifecycle+dev-sdlc at 54794d7`
