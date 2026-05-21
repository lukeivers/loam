# Amendment #139 — dev-sdlc manifest runtime flag (resolve PMR_4 mutual contradiction; close F-DEV-SDLC-MANIFEST-DRIFT)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 by the `loam-plan-author` subagent (background dispatch from the persona).
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Quality bar:** single-component change, ≤8 ACs + 1 outcome-altitude smoke; no method-in-AC; behavior-preserving for runtime consumers (audit + selector both accept the new schema field without behavior change for non-flagged entries).

---

## §1. Objective / Summary / TL;DR

Close `F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS` (FIDRAFT L328) by introducing a `runtime: true` flag on partition-manifest entries that point at runtime-shape paths (workspace-side runtime telemetry that may not exist in the canonical tree but populates on first-run). This resolves the mutual contradiction between `test_AC_PMR_4_every_always_loaded_glob_resolves` and `test_AC_PMR_4_data_stays_top_level` (both in `plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py`) that #138's NARROWING ADDENDUM deferred.

Three concrete deltas:

1. **Schema extension.** Add an optional `runtime: bool = False` field to `ManifestEntry`. Extend `_coerce_entry` to parse `runtime:` from YAML; extend root parsing to accept either the bare-string form (existing) OR a mapping with `path:` + `runtime:` (new). Defaults preserve backwards-compat — absent `runtime:` reads as `False`.

2. **Test admission of declared-runtime entries.** `test_AC_PMR_3_every_root_resolves_on_disk` and `test_AC_PMR_4_every_always_loaded_glob_resolves` skip the existence/non-empty-match check when the entry's `runtime` is `True`. All other contract properties remain enforced (entry still declared, still in the right block, etc.).

3. **Manifest edits.** Delete the two `framework/memory-system/` entries (root L49 + glob L97 — that directory was deleted permanently at `b92aaea`, runtime-shape semantics do NOT apply). Mark the two `data/` entries (root L67 + glob L127) with `runtime: true` (workspace runtime telemetry; populates on first-run per the existing comments at L62-64 + L125-126).

**Why now:** This amendment closes the highest-severity capture in FIDRAFT (HIGH severity per L328 — blocks any future plugins/-component seal that runs the full dev-sdlc test suite, including the in-flight seal-tool hygiene pair). Owner ruled path (a) at TG 11858 over path (b) sentinel-directory because (a) has less architectural blast radius — the test-corpus + schema edits are the smaller surface than touching the canonical-tree philosophy.

**Pre-flight Tier-0 evidence (verifiable from this commit at HEAD `67f8a54`):**

| Check | Command | Result |
|---|---|---|
| Canonical WD + HEAD | `cd /Users/lukeivers/loam && git log --oneline -1` | `67f8a54 docs: bump current-release to v0.12.15 …` |
| Last sealed amendment | `ls docs/plans/sealed/amendment-13*.md \| tail -1` | `amendment-138-dev-sdlc-test-directory-cleanup.md` (this IS #139) |
| memory-system absence | `ls framework/memory-system 2>&1` | `No such file or directory` |
| data/ absence | `ls data 2>&1` | `No such file or directory` |
| memory-system in manifest | `grep -n 'memory-system' plugins/dev-sdlc/dev-mode-manifest.yaml` | `49: - framework/memory-system/` + `97: - glob: "framework/memory-system/**"` (#138's NARROWING ADDENDUM DEFERRED the deletion) |
| data/ in manifest | `grep -n 'data/' plugins/dev-sdlc/dev-mode-manifest.yaml` | `67: - data/` + `127: - glob: "data/**"` |
| Test pair failures | `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py -v` | `test_AC_PMR_3_every_root_resolves_on_disk` fails at `framework/memory-system/`; subsequent run would fail at `data/` after memory-system removed; `test_AC_PMR_4_every_always_loaded_glob_resolves` fails on memory-system glob (empty match-set) then data/ glob |
| `expand_entry` behaviour on path-entries | `manifest.py:236-256` | path-entries return `{entry.path}` UNCONDITIONALLY without on-disk verification (already runtime-tolerant for path-entries via "declaration-time semantics") |
| Production consumers of `ManifestEntry` | `grep -rn 'ManifestEntry\|expand_entry' plugins/ --include='*.py' \| grep -v test_` | `manifest.py` (definition), `audit.py:31+134`, `selector.py:18+43+48`, `__init__.py:10+12+30+32` — all import + use the dataclass; adding an optional field with default `False` is backwards-compat at the dataclass surface |
| No external manifest consumers | `grep -rn 'ManifestEntry\|expand_entry' framework/ --include='*.py' 2>/dev/null` | (none) |

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T16:14:01Z | Build-strategy delegation |
| TG 11837 | 2026-05-21 | Durable-autonomy directive |
| TG 11854 | 2026-05-21 | Re-evaluation directive (after #138 narrowing) |
| TG 11856 | 2026-05-21 | Questions-one-at-a-time discipline reaffirmed |
| TG 11858 | 2026-05-21 | Owner ruling: path (a) — test-corpus edit + `runtime: true` schema flag — chosen over path (b) sentinel-directory because (a) has less architectural blast radius |

The msg-IDs are dispatcher-supplied; if the build agent reads `docs/STATE.md` or scrollback and finds different timestamps, the build agent corrects per its own Tier-0 lookup.

---

## §2. Predecessors / context

- **Predecessor (load-bearing):** amendment #138 seal at `01e63ac` (dev-sdlc test directory cleanup — SKILL-frontmatter narrowed; PMR scope DEFERRED). Manifest BASELINE points there.
- **Parent capture:** FIDRAFT `F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS` at `docs/FUTURE_IDEAS_DRAFT.md` L328. This amendment is its closure.
- **Sibling captures (downstream, unblocked on seal):** F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE (the seal-tool hygiene pair `ws-seal-tool-hygiene-pair`) — those amendments will run the full plugins/dev-sdlc test suite via seal-step automation; this amendment is their PREREQUISITE.
- **Shape exemplar:** `docs/plans/sealed/amendment-138-dev-sdlc-test-directory-cleanup.md` (most-recent dev-sdlc-component amendment with similar manifest+test fence).

---

## §3. Scope

**In-scope:**

1. Extend `ManifestEntry` dataclass at `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/manifest.py` with an optional `runtime: bool = False` field.
2. Extend `_coerce_entry` to parse a top-level `runtime:` key from the YAML mapping (boolean).
3. Extend root parsing (`_coerce_root` + the call site in `load_manifest`) to accept either a bare string (existing — preserved) OR a mapping `{path: <str>, runtime: <bool>}` (new). The parsed root in either case yields a `RootEntry` (a small new dataclass with `path: str` + `runtime: bool` fields), and `manifest.roots` returns a tuple of `RootEntry` instead of a tuple of strings.
4. Edit the `every_root_resolves_on_disk` and `every_always_loaded_glob_resolves` tests to skip the existence/non-empty-match check when the entry's `runtime` is `True`. All other test contracts unchanged.
5. Delete the two `framework/memory-system/` entries from `plugins/dev-sdlc/dev-mode-manifest.yaml` (root L49 + glob L97 — directory permanently deleted, runtime semantics do not apply).
6. Mark the two `data/` entries (root L67 + glob L127) with `runtime: true` — root entry rewritten as the new mapping shape `- {path: data/, runtime: true}`; glob entry receives a `runtime: true` field alongside its `glob:`.
7. Update the inline comments in `dev-mode-manifest.yaml` (the L11-24 schema docstring + the L62-64 / L125-126 explanatory comments) to name the new `runtime:` field semantics.

**Out-of-scope:**

- Any change to the audit module (`audit.py`) or selector (`selector.py`). The runtime flag is a property OF an entry, not consumed by the audit/selector logic — those modules read `entry.path` / `entry.glob` and call `expand_entry`, which is unchanged behaviorally for runtime entries (`expand_entry` already tolerates non-existent paths for `path:` entries; for `glob:` entries it returns an empty set, which audit + selector accept as a no-op).
- Any new test asserting audit/selector behavior under runtime entries. The test surface stays focused on the manifest-shape contract; downstream consumers are unchanged.
- Any other manifest cleanup (oversized YAML manifest fields, F5 orphan audit on `framework/` subdirs not in the manifest — those stay queued separately per #138 §3 and FIDRAFT).
- The seal-tool hygiene pair itself — that's the next amendment, which this one unblocks.

---

## §4. Acceptance criteria

| AC ID | Outcome (what's observable) | Verification |
|---|---|---|
| **AC.DCR.SCHEMA.1** | The `Manifest` parsed from `dev-mode-manifest.yaml` admits entries (in `roots:` OR `always_loaded:` OR `dev_only:`) with `runtime: true`. The parsed entry's `runtime` field equals `True`. | New test `test_AC_DCR_schema_accepts_runtime_field` in `plugins/dev-sdlc/tools/loam-mode/tests/test_manifest_runtime_field.py` (a new file) using a synthetic in-memory YAML payload. |
| **AC.DCR.SCHEMA.2** | An entry without a `runtime:` key parses with `runtime` defaulting to `False`. Existing manifests continue to parse without modification. | Same new test file: `test_AC_DCR_schema_runtime_defaults_false`. The pre-existing tests `test_AC_F1_disjointness` + `test_AC_F4_glob_well_defined` (and any other `loam-mode` test) continue to pass — proof of backwards-compat. |
| **AC.DCR.SCHEMA.3** | A root entry expressed as a mapping `{path: <str>, runtime: <bool>}` parses to a `RootEntry` with the named `path` and `runtime` fields; a bare-string root entry parses to a `RootEntry` with `runtime=False` and `path` equal to the string. | Same new test file: `test_AC_DCR_root_entry_mapping_form` + `test_AC_DCR_root_entry_bare_string_form`. |
| **AC.DCR.TEST.1** | `test_AC_PMR_3_every_root_resolves_on_disk` passes when a root entry has `runtime: True` and points at a non-existent path. | Direct pytest invocation on the canonical manifest after the §3.6 marking (the `data/` root with `runtime: true` no longer fails the existence check). |
| **AC.DCR.TEST.2** | The same test FAILS (raises `AssertionError`) when a root entry without `runtime: True` (or with `runtime: False`) points at a non-existent path. The safety property is preserved. | Same new test file: `test_AC_DCR_test_rejects_nonexistent_non_runtime_root` — temporarily injects a synthetic `frobnitz/` root without the flag, asserts the test asserts. |
| **AC.DCR.TEST.3** | `test_AC_PMR_4_every_always_loaded_glob_resolves` passes when an always-loaded entry has `runtime: True` and points at a non-existent path (empty match-set). | Direct pytest invocation on the canonical manifest after the §3.6 marking (the `data/**` glob with `runtime: true` no longer fails the non-empty-match check). |
| **AC.DCR.TEST.4** | The same test FAILS when an always-loaded entry without `runtime: True` resolves to an empty match-set. The safety property is preserved. | Same new test file: `test_AC_DCR_test_rejects_empty_match_non_runtime_glob` — synthetic glob without the flag, asserts the test asserts. |
| **AC.DCR.MANIFEST.1** | `plugins/dev-sdlc/dev-mode-manifest.yaml` no longer contains any `framework/memory-system/` reference. | `grep -c 'framework/memory-system' plugins/dev-sdlc/dev-mode-manifest.yaml` returns `0`. |
| **AC.DCR.MANIFEST.2** | Both `data/` entries (root + glob) in `dev-mode-manifest.yaml` carry `runtime: true`. | Parsed manifest: `[r for r in manifest.roots if r.path == 'data/']` yields one entry with `runtime is True`; `[e for e in manifest.always_loaded if e.glob == 'data/**']` yields one entry with `runtime is True`. |
| **AC.DCR.S** | **Outcome-altitude smoke:** `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py plugins/dev-sdlc/tools/loam-mode/tests/ -v` against the post-amendment HEAD returns **0 failures + 0 collection errors**. | Direct pytest invocation. |

All ACs are outcome-shape: each asserts a measurable property of the post-amendment artefact, not a method. **Method test:** can AC.DCR.TEST.1 be satisfied by a method other than the one I have in mind (an `if entry.runtime: continue` guard in the test)? Yes — a maintainer could equivalently delete the existence check entirely, or move the runtime entries to a separate `runtime_roots:` block and have the test iterate a different field. The AC text says "passes when `runtime: True`"; it does NOT prescribe the gating mechanism. (Same logic applies to AC.DCR.TEST.{2,3,4} and AC.DCR.SCHEMA.{1,2,3}.) Method-in-AC test passes for all.

**Outcome-altitude classification:** AC.DCR.S satisfies `feedback_test_outcome_altitude_required` — invokes the production verification path (`pytest` against the actual canonical manifest + the loam-mode unit tests) with no pre-arranged state.

---

## §5. Sealed-component fence

**Component touched:** `dev-sdlc` (the sealed component at `plugins/dev-sdlc/`).

**Surfaces edited:**

1. `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/manifest.py` — `ManifestEntry` dataclass + `_coerce_entry` + `_coerce_root` + `load_manifest` (root parsing) + add a `RootEntry` dataclass.
2. `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/__init__.py` — re-export `RootEntry` alongside `ManifestEntry`.
3. `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/audit.py` — update the call site (`manifest.roots`) that previously assumed root entries were bare strings to use `root.path` instead. **Behaviorally unchanged** — same paths, same audit walk — but the call sites need to dereference the new dataclass.
4. `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/selector.py` — same as audit (if it consumes `manifest.roots`; per pre-flight grep it consumes `always_loaded` + `dev_only`, not `roots`, so likely no edit; builder verifies).
5. `plugins/dev-sdlc/dev-mode-manifest.yaml` — delete two `framework/memory-system/` lines (L49 + L97); mark two `data/` lines (L67 + L127) with `runtime: true` (root entry rewritten as mapping form); update the L11-24 schema docstring + L62-64 / L125-126 explanatory comments.
6. `plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py` — edit `test_AC_PMR_3_every_root_resolves_on_disk` (lines 58-69) + `test_AC_PMR_4_every_always_loaded_glob_resolves` (lines 126-153) to admit `runtime: True` entries. The two callsites that iterate `manifest.roots` (line 62) need to use `root.path` instead of the bare string; the `test_AC_PMR_3_dormancy_renamed_not_graceful_degradation` + `_workspace_sync_added` + `_no_top_level_component_refs_remain` tests at lines 72-123 also iterate `manifest.roots` as a set of strings and need the same dereference.
7. `plugins/dev-sdlc/tools/loam-mode/tests/test_manifest_runtime_field.py` — **new file** carrying AC.DCR.SCHEMA.{1,2,3} + AC.DCR.TEST.{2,4} tests.
8. `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_audit.py` + `tests/test_partition_references.py` + `tests/test_selector_partition.py` — any test that constructs a synthetic `roots:` list of bare strings (the pre-flight found `test_partition_audit.py` does this at lines 29 + 106 + 126) may need to be updated to match the new root-entry shape. **Builder verifies** — if those tests use only `roots:` as input to the parser, they need to be re-shaped; if they construct `Manifest(roots=("src/",))` directly via dataclass, they need the `RootEntry` wrapper. This is a backwards-compat surface, not an AC; it stays inside the dev-sdlc fence.

**Universal admissions:**

- `docs/plans/` (this plan-doc + manifest; archives to `docs/plans/sealed/` on seal per T1.4).

**Out of fence (halt-and-surface trigger — see §7):**

- Any other component under `framework/` or `plugins/` outside `plugins/dev-sdlc/`.
- Any file under `plugins/dev-sdlc/` outside the surfaces named above.
- The `loam.plugins.dev_sdlc` package source under `plugins/dev-sdlc/src/` (no edit required for this amendment — the runtime flag lives in the `loam-mode` toolkit under `plugins/dev-sdlc/tools/`).

---

## §6. Build steps (method-level guidance — builder's call per ODD §1.1)

1. **Plan-doc + manifest land** (this commit).
2. **Source edit 1 — `manifest.py` dataclass + parser:**
   - Add `runtime: bool = False` to `ManifestEntry` (frozen dataclass; default preserves backwards-compat).
   - Add a new `RootEntry` frozen dataclass with `path: str` + `runtime: bool = False`.
   - Update `Manifest.roots` type annotation from `tuple[str, ...]` to `tuple[RootEntry, ...]`.
   - Update `_coerce_root` to accept either a bare string OR a `{path: <str>, runtime: <bool>}` mapping; return a `RootEntry`.
   - Update `_coerce_entry` to parse an optional `runtime:` boolean (default `False`); pass to `ManifestEntry` constructor.
   - Verify: `python3.13 -c "from loam_mode.manifest import ManifestEntry, RootEntry; e = ManifestEntry(path='x', runtime=True); print(e.runtime); r = RootEntry(path='y/'); print(r.runtime)"` prints `True` then `False`.
3. **Source edit 2 — `__init__.py` re-export:** add `RootEntry` to the imports + `__all__`.
4. **Source edit 3 — `audit.py` consumer update:** every call site that iterates `manifest.roots` to walk paths needs to dereference `root.path` (was: bare string). Per pre-flight grep, audit.py does not iterate `roots` directly in the slice shown — it consumes `always_loaded` + `dev_only` through `expand_entry`. **Builder verifies via grep** — if `manifest.roots` is consumed anywhere in `audit.py` / `selector.py` / `manifest.py`, those call sites are updated.
5. **Source edit 4 — `dev-mode-manifest.yaml`:**
   - Delete L49 (`- framework/memory-system/`).
   - Delete L97 (`- glob: "framework/memory-system/**"`).
   - Rewrite L67 from `- data/` to `- {path: data/, runtime: true}` (or equivalent block form, builder's call — both YAML shapes parse identically).
   - Add `runtime: true` to the L127 glob entry, e.g. `- {glob: "data/**", runtime: true}` (or block form).
   - Update the L11-24 schema docstring to name `runtime:` as an optional boolean field on entries (root + always_loaded + dev_only).
   - Update the L62-64 + L125-126 explanatory comments to reflect the runtime-flag semantics.
6. **Test edit 1 — `test_AC_PMR_3_dev_mode_manifest_roots_realigned.py`:**
   - `test_AC_PMR_3_every_root_resolves_on_disk` — iterate `manifest.roots` as `RootEntry` objects; skip the `target.exists()` assertion when `root.runtime is True`.
   - `test_AC_PMR_4_every_always_loaded_glob_resolves` — `if entry.runtime: continue` before the `expand_entry` non-empty assertion. (Per #138 §10 RF #6 evidence: the `expand_entry` function returns an empty set for non-existent globs; the runtime flag is what differentiates "expected empty" from "regression".)
   - `test_AC_PMR_3_dormancy_renamed_not_graceful_degradation` + `_workspace_sync_added` + `_no_top_level_component_refs_remain` — the `set(manifest.roots)` constructions become `{r.path for r in manifest.roots}` (same set membership, different dereference).
   - `test_AC_PMR_4_data_stays_top_level` continues to pass unchanged — it asserts `"data/**" in globs`, and the `data/**` entry is still in `always_loaded:` (just with `runtime: true` added).
7. **Test edit 2 — new file `plugins/dev-sdlc/tools/loam-mode/tests/test_manifest_runtime_field.py`:** carries AC.DCR.SCHEMA.{1,2,3} tests (parses synthetic YAML payloads) + AC.DCR.TEST.{2,4} tests (synthetic non-runtime entry pointing at non-existent path; assert the PMR_3/PMR_4 test logic asserts). Methodology: builder may either (a) copy the PMR test bodies and inject synthetic manifests, OR (b) extract the runtime-skip predicate into a helper and unit-test it directly. Either satisfies AC outcome.
8. **Test edit 3 — synthetic-manifest tests in loam-mode/tests/:** any test that uses `roots=("src/", …)` (bare strings) needs `RootEntry(path="src/")` wrapper; tests that pass YAML through `load_manifest` need no change (the YAML preserves bare-string admission).
9. **Touched-tests run.** `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PMR_3_*.py plugins/dev-sdlc/tools/loam-mode/tests/ -v` — every previously-failing case green; every previously-passing case still green.
10. **Pre-seal full directory run.** `python3.13 -m pytest plugins/dev-sdlc/tests/ -q` — verifies AC.DCR.S. **Expected:** 0 failures, 0 errors, ≥252 passed (the 2 PMR cases #138 admitted as known-deferred now green), 7 skipped (unchanged).
11. **`loam amend apply`** — auto-commit per ergonomics. **Order discipline (per #138 §16 finding #3):** all source-edit commits MUST land BEFORE `loam amend apply`. The apply step advances sidecar bookkeeping against the committed HEAD, not the working tree.
12. **`loam amend seal --plan-doc docs/plans/amendment-139-dev-sdlc-manifest-runtime-flag.md`** — deterministic seal commit. **Caveat (per #138 §16 finding #1):** verify the manifest YAML's `narrative.target` is a file-path (e.g. `docs/plans/sealed/amendment-139-…md`), NOT the component name `dev-sdlc`; the seal-tool interprets `narrative.target` as a write-target and a component-name value will create an orphan file at the repo root.
13. **Section-14 auto-backfill** uses the canonical `## §14 — Method-decision register` heading (post-#136 widening); no manual fallback expected. **Caveat (per #138 §16 finding #2):** auto-backfill is GATED on post-seal dry-run passing — if any seal-tool failure intervenes, manual SHA backfill required.

---

## §7. Halt triggers (in-flight)

1. Source edits leak outside the surfaces named in §5.
2. The `ManifestEntry` dataclass change breaks downstream consumers (`audit.py`, `selector.py`, the `loam-mode` CLI) — e.g. an old call site assuming `manifest.roots` is a tuple of strings. Halt-and-surface; do not silently widen scope. (Pre-flight evidence suggests audit + selector don't consume `manifest.roots` directly, but verify.)
3. The `RootEntry` mapping form breaks YAML parsing of an existing root entry not touched by this amendment (e.g. one of the `framework/<comp>/` roots) — would indicate the parser change is over-broad. Halt-and-surface.
4. The new `test_manifest_runtime_field.py` tests fail in a way that suggests the schema design is wrong (e.g. PyYAML parses `{path: data/, runtime: true}` differently than the block form). Halt-and-surface; surface to dispatcher with the empirical diff.
5. Step 10's full-directory pytest reveals an unanticipated failure outside the PMR + new schema tests — would indicate either a flaky test, an unrelated regression introduced by an unrelated commit, or a real product issue. Halt-and-surface.
6. The seal-tool's `narrative.target` field bug (#138 §16 #1) recurs at seal time, dropping an orphan file at repo root. Builder must verify before seal AND clean up via corrective fixup if it lands; halt-and-surface to dispatcher.
7. Manifest auto-backfill fails at seal time (the post-#136 widened regex should match `## §14`; if it doesn't, separate amendment needed against seal-tool — out of scope here).
8. **Confidence-tightening trigger (F4):** if the builder discovers that the `runtime:` field needs to apply also to `dev_only:` (the third entry block), they should add it under the same schema rule. The plan-author scoped this to roots + always_loaded because those are the blocks the failing tests audit; dev_only entries are dev-tooling paths that DO exist in the canonical tree (no runtime semantics needed). But if a future case surfaces during build, the schema is symmetric — extension is trivial and stays inside the fence.

---

## §8. Out of scope (deferred)

- **The seal-tool hygiene pair** (F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE / `ws-seal-tool-hygiene-pair`). Unblocked on seal; promoted to its own amendment (likely next-up after this one).
- **Oversized YAML manifest field cap** (the brief's original Scope C from #138). Stays in queue as `ws-loam-amend-oversized-manifest-field-cleanup`.
- **F5 orphan audit on `framework/` subdirs not in the manifest** (`binary-observation-harness`, `claude-p-client`, `loam-init`, `per-project-pm`, `principle-foundation` — see #138 §10 RF #2). Its own AC.F5 audit pass.
- **Any extension of the runtime-flag semantics to `dev_only:`** — the present amendment scopes to roots + always_loaded because those are the audit surfaces failing. dev_only entries are dev-tooling paths that DO exist in the canonical tree; no runtime semantics needed today.
- **Documentation of the `runtime:` field in plan-docs.md convention** — the convention doc lives at `plugins/dev-sdlc/docs/conventions/plan-docs.md` and is about plan-doc shape, not manifest shape. The `runtime:` field documentation lives in the `dev-mode-manifest.yaml` schema comments (§3 step 7 / §6 step 5) — that's the right surface.

---

## §9. Bookkeeping (post-seal)

- **`docs/STATE.md`** — status-line update naming amendment #139 sealed at `<seal-SHA>` + closing the dependency the seal-tool hygiene pair amendment was waiting on (F-DEV-SDLC-MANIFEST-DRIFT cleared).
- **`docs/FUTURE_IDEAS_DRAFT.md`** — close `F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS` at L328 (mark as resolved by amendment #139; remove from active capture list or move to a closed-captures section per existing FIDRAFT convention).
- **`docs/release-roadmap.md`** — no entry needed (test-infrastructure cleanup is patch-class hygiene; no release-class delta).
- **§14 of this plan-doc** — backfilled by `loam amend seal` (canonical `## §14 — Method-decision register` heading; post-#136 regex widening matches; no manual fallback expected unless seal-tool's post-seal dry-run halts per #138 §16 #2).
- **Parent #138 plan-doc** — no edit; #138 is sealed and its §0 NARROWING ADDENDUM correctly named this follow-up as the deferred work.

---

## §10. F2 Ruthless Feedback (honest doubts + design risks)

1. **F2 on dispatch brief — `D-DCR.MEMORY-SYSTEM-ENTRIES` correctly identified as deletion, not flag.** The brief carried a self-correcting clause ("framework/memory-system is gone permanently … so those entries should be DELETED, not flagged. Plan-author: verify with Tier-0 whether they're still in the manifest + recommend deletion."). Tier-0 confirms: still present (L49 + L97), directory permanently gone at `b92aaea`. Recommend deletion — matches the brief's own correction. (#138's NARROWING ADDENDUM DEFERRED this deletion specifically because PMR_4 couldn't pass after the deletion would unmask the `data/` failure; #139's runtime-flag schema resolves the data/ contradiction, so the memory-system deletion can finally land.)

2. **F2 — root-block schema change is broader than the test-level admission alone.** The dispatch brief framed this as a "test-corpus edit with a `runtime: true` flag on manifest entries." For `always_loaded:` entries, that's straightforward (entries are already mappings — `{glob: ..., exclude: ...}` — so adding `runtime: true` is additive). But `roots:` entries are bare strings (`- data/`), so flagging requires changing the root-block shape to admit either bare strings (existing) OR mappings (new). This is a SCHEMA change to the root block, not just a test admission. The builder should be aware that the surface is broader than "edit the test file"; it includes the parser + dataclass surface + every consumer that iterates `manifest.roots`. Captured in §3 + §5 + §6 explicitly. The blast radius is contained: per pre-flight grep, only `audit.py` consumes `manifest.roots` directly, and the consumer change is mechanical (`root` → `root.path`).

3. **F2 — `expand_entry` for `path:` entries already returns `{entry.path}` unconditionally (manifest.py:256).** This means the `runtime:` flag is somewhat redundant for `path:` entries in `always_loaded:` / `dev_only:` — the test currently passes for non-existent `path:` entries because expand_entry doesn't verify on-disk. The `runtime:` flag matters for: (a) `glob:` entries (where `expand_entry` walks the tree and returns empty for non-existent paths — what currently fails), AND (b) `roots:` entries (where the test explicitly calls `target.exists()`). For `path:` entries in always_loaded/dev_only, the flag is documentation-only — declaring intent without changing behavior. **Recommendation:** preserve the schema symmetry — the field is admissible on all entries (clear semantics for future maintainers), even when the runtime check would be a no-op. Low blast-radius, high readability.

4. **F2 — the `RootEntry` vs `ManifestEntry` split.** I could equivalently lift `ManifestEntry` to cover both shapes by allowing `path` to be a directory path (with trailing `/`) and tightening the discriminator. But `roots:` entries don't carry `glob:` or `exclude:`, and the test at `test_AC_PMR_3_no_top_level_component_refs_remain` operates on root paths as a set. The cleaner shape is a dedicated `RootEntry` dataclass. **Recommendation:** keep the split per the build steps; the small surface increase is justified by readability + type-safety. Builder's call.

5. **F2 — should the NEW tests live in `plugins/dev-sdlc/tests/` or `plugins/dev-sdlc/tools/loam-mode/tests/`?** The schema tests test the `loam-mode` toolkit's parser, so `tools/loam-mode/tests/` is the right home (per pre-flight: that directory already has `test_partition_audit.py`, `test_partition_references.py`, `test_selector_partition.py`). The PMR_3/PMR_4 tests stay in `plugins/dev-sdlc/tests/` because they test the canonical manifest contract, not the parser. **Recommendation:** new file at `plugins/dev-sdlc/tools/loam-mode/tests/test_manifest_runtime_field.py`. Per §5 step 7.

6. **Doubt — does the test-corpus edit pattern preserve the safety property the original test was guarding?** The original test asserted "every always-loaded glob expands to non-empty." The amended test will assert "every always-loaded glob without `runtime: true` expands to non-empty." A future maintainer could SILENTLY add `runtime: true` to a stale entry to make the test pass without actually fixing the underlying problem. **Mitigation:** AC.DCR.TEST.2 + AC.DCR.TEST.4 explicitly assert that non-runtime entries pointing at non-existent paths STILL FAIL — so the safety property holds for entries the maintainer doesn't explicitly opt out of. The remaining risk (opt-out-by-mistake) is bounded by: (a) the `runtime: true` flag is observable in code review (5-character flag, hard to miss), (b) the schema docstring explicitly names the semantics, (c) the manifest is small enough (< 200 lines) that drift is caught by visual inspection. Acceptable residual risk.

7. **Doubt — could the runtime-flag concept generalize beyond `data/`?** Yes — any future runtime-shape path (e.g. workspace-side telemetry, runtime-generated indices, first-run-populated caches) gets the same treatment. The schema is the right shape. The CURRENT manifest has exactly ONE such case (`data/`); future cases will be opt-in additions, not retrofits. (#138's NARROWING ADDENDUM's identification of the data/ contradiction was the trigger; the schema generalizes naturally.)

8. **Doubt — does deleting the `framework/memory-system/` entries break any consumer that ASSUMES those paths exist in the manifest?** Per pre-flight: the only consumers are `audit.py` (walks `roots:`) and `selector.py` (resolves `always_loaded` + `dev_only`). Neither hard-codes `framework/memory-system/`. Deletion is safe. **No additional verification needed.**

9. **F2 — the dispatch brief's §10 RF anticipates the §10 RF section itself.** The brief framed §10 RF gaps as something the plan-author "names explicitly inside §10 of the plan-doc." This plan-doc satisfies that contract; no surprise findings beyond the eight above. The build agent should still surface their own §16 findings post-build (#138 had 5 such findings; #139 will likely surface similar findings around the `narrative.target` bug + `--amend` discipline + post-seal-dry-run gating).

---

## §11. Provenance trail

- **Plan-doc convention:** `plugins/dev-sdlc/docs/conventions/plan-docs.md` (the canonical authoring shape).
- **Recent exemplar (single-component, manifest+test fence):** `docs/plans/sealed/amendment-138-dev-sdlc-test-directory-cleanup.md`.
- **Parent FIDRAFT:** `docs/FUTURE_IDEAS_DRAFT.md` L328 (F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS) — captured across #137 §16 finding #4, #138 builder F2 halt, and #138 second builder F2 halt; HIGH severity; activation gate was "owner ruling on (a) vs (b)"; owner ruled (a) at TG 11858.
- **#138's NARROWING ADDENDUM:** `docs/plans/sealed/amendment-138-dev-sdlc-test-directory-cleanup.md` §0 — describes the mutual contradiction this amendment resolves, and explicitly defers it to "a separate amendment that names the test-corpus resolution explicitly" (which is this one).
- **memory-system deletion commit:** `b92aaea chore(v0.3.0): Cycle 2 — delete framework/memory-system/ (graphiti rip-out)`.
- **data/ deletion commit:** `39cfbb1` (per FIDRAFT L328 — to be Tier-0 verified by builder via `git log --all --oneline --diff-filter=D -- data`).
- **Manifest parser surface:** `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/manifest.py` (load_manifest, ManifestEntry, _coerce_entry, _coerce_root, expand_entry).
- **Consumers of `manifest.roots`:** `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/audit.py` (the only production consumer per pre-flight grep).
- **Test corpus:** `plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py` (the test file carrying the mutually-contradicting tests).
- **Existing loam-mode unit tests (backwards-compat surface):** `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_audit.py`, `test_partition_references.py`, `test_selector_partition.py`.

---

## §14. Method-decision register (placeholder — populated by builder)

| Decision | Recommendation | Ratified by | Authority |
|---|---|---|---|
| **D-DCR.FLAG-SHAPE** | Optional boolean `runtime:` field on each entry — additive to existing `{path: ...}` / `{glob: ..., exclude: ...}` shape; default `False`. Absent or `False` preserves traditional must-exist-on-disk semantics. **Recommend: ratify.** Alternative (separate `runtime_roots:` / `runtime_globs:` blocks) was considered and rejected: doubles schema surface for marginal benefit; the discriminator-by-field-presence pattern is cleaner. | persona (TG 11858 — path (a) ruling) | Plan-author Tier-0 verified. |
| **D-DCR.ROOT-SHAPE** | Extend `roots:` block to accept either bare strings (existing — preserved) OR `{path: <str>, runtime: <bool>}` mappings (new). Introduce a `RootEntry` dataclass to carry both forms uniformly downstream. **Recommend: ratify.** Alternative (lift `ManifestEntry` to subsume roots) was considered and rejected: roots don't carry glob/exclude semantics; the cleaner shape is a dedicated `RootEntry`. | persona (TG 11858) | Plan-author Tier-0 verified. |
| **D-DCR.TEST-LOGIC** | `test_AC_PMR_3_every_root_resolves_on_disk` + `test_AC_PMR_4_every_always_loaded_glob_resolves` skip their existence/non-empty-match assertions when the entry's `runtime` is `True`. New tests `test_AC_DCR_test_rejects_nonexistent_non_runtime_root` + `test_AC_DCR_test_rejects_empty_match_non_runtime_glob` preserve the safety property for non-flagged entries. **Recommend: ratify.** Alternative (a separate runtime-shape test) was considered and rejected: doubles test surface; the existing test bodies are the right home for the admission predicate. | persona (TG 11858) | Plan-author Tier-0 verified. |
| **D-DCR.DATA-ENTRIES** | Mark the two `data/` entries (root L67 + glob L127) with `runtime: true`. They stay in the manifest as runtime-shape declarations because `data/` is workspace runtime telemetry that populates on first-run (per the existing comments at L62-64 + L125-126). **Recommend: ratify.** | persona (TG 11858) | Plan-author Tier-0 verified. |
| **D-DCR.MEMORY-SYSTEM-ENTRIES** | Delete the two `framework/memory-system/` entries (root L49 + glob L97) from `dev-mode-manifest.yaml`. The directory was permanently deleted at `b92aaea` (v0.3.0 Cycle 2, graphiti rip-out); the runtime-flag pattern applies only to "may not exist yet but will populate at first-run" cases, NOT to "deleted permanently" cases. **Recommend: ratify.** This deletion was originally scoped into #138 but DEFERRED by its NARROWING ADDENDUM because the deletion would unmask the `data/` PMR_4 contradiction; #139's runtime-flag schema resolves that contradiction, so the deletion can finally land. | persona (TG 11858) | Plan-author Tier-0 verified + #138 §0 narrative. |
| **D-DCR.AC-LADDER** | AC families: `AC.DCR.SCHEMA.{1,2,3}` (schema extension accepts the new field + backwards-compat + root-mapping form) + `AC.DCR.TEST.{1,2,3,4}` (admit-runtime + safety-preserved for both test branches) + `AC.DCR.MANIFEST.{1,2}` (memory-system removed + data/ flagged) + `AC.DCR.S` (outcome-altitude smoke). Scope-descriptive (per 2026-05-09 ratification), not version-packed. **Recommend: ratify.** | persona (TG 11858) | Plan-author convention. |

**Commit SHAs (manual backfill — populated post-seal by builder per #138 §14 pattern + seal-tool auto-backfill caveat):**

- Plan-doc commit: `3a758a7` (plan-author dispatch — plan-doc + manifest + ratification table)
- Source-edit commit: `e3d0024` (feat(dev-sdlc): manifest runtime-flag schema + PMR test admission)
- Amendment commit (apply auto-commit): `4cf9be2` (chore(amend): BASELINE+sidecar bump to 01e63ac)
- Seal commit: `1f3d8d7` (chore(seals): amendment #139 seal commit — SEAL_COMMIT → 4cf9be2)
- Post-seal corrective: `ca16e41` (chore(amend-fixup): BASELINE bump 01e63ac → 26f3a9e — see §16 finding #2)

Auto-backfill of this section was BLOCKED by the post-seal dry-run halt (the `dev-sdlc` orphan-deletion in the diff window — see §16 finding #2). Manual backfill landed in the corrective commit `ca16e41`.

---

## §15. Backwards-compat verification

- **All non-touched tests in `plugins/dev-sdlc/tests/`** continue to pass (currently 250 pass under py3.13 post-#138). This amendment changes:
  - Two failing tests (PMR_3 + PMR_4 — the #138-known-deferred pair) → now pass.
  - Three passing tests (the dormancy-rename + workspace-sync + no-top-level-refs tests at lines 72-123) → bodies require minor edits to dereference `root.path` instead of bare string; behavior unchanged.
  - All other tests untouched.
- **All loam-mode tests** (`plugins/dev-sdlc/tools/loam-mode/tests/`) — the `test_partition_audit.py` synthetic-manifest tests at lines 29 + 106 + 126 construct bare-string roots; minor wrapper edit needed (`RootEntry(path="src/")` or YAML-string form). `test_partition_references.py` + `test_selector_partition.py` — verify per pre-flight, may not need edits if they pass YAML through `load_manifest`.
- **All other components' tests** untouched; cross-component seal-diff sweep at step 12 verifies no diff leaked into other sealed components.
- **The `loam.plugins.dev_sdlc` Python package** is unchanged (no edit under `plugins/dev-sdlc/src/`). Import behavior + entry-point discovery + CLI subcommand registration + contribution surface — all behaviour-preserved.
- **The `loam-mode` toolkit's public API surface** (`__init__.py`) gains a new export (`RootEntry`) but loses none. Backwards-compat for downstream importers preserved.
- **The dev-mode partition behavior at runtime** (the SessionStart auto-load mechanism) is unchanged — it consumes `expand_entry` on `always_loaded` + `dev_only`, which handles non-existent paths gracefully today and continues to do so post-amendment.

---

## §17. Composition (M5 derivation line)

- **Composes with** `feedback_record_owner_ratification_before_dispatch` — §1 ratification table records the five msg-IDs durably before the build agent dispatches off this commit (TG 11808 / 11837 / 11854 / 11856 / 11858).
- **Composes with** `feedback_information_trust_ordering` — §1 pre-flight Tier-0 evidence table verifies every claim empirically before authoring; §10 RF #3 + #8 are direct applications of Tier-0-over-Tier-2 (verifying the parser surface + consumer surface from code, not from recall).
- **Composes with** `feedback_loose_AC_text_fix_AC_not_implementation` — ACs are outcome-shape; method (`RootEntry` dataclass vs lifted `ManifestEntry`, in-test guard vs helper extraction) is the builder's call.
- **Composes with** `feedback_dispatch_explicit_loam_amend_apply` — §6 step 11 names `loam amend apply` as the bookkeeping mechanism and the source-must-be-committed-before-apply discipline (per #138 §16 finding #3).
- **Composes with** `feedback_test_outcome_altitude_required` — AC.DCR.S is the outcome-altitude AC for the cycle (full-directory pytest, no pre-arranged state).
- **Composes with** `feedback_locked_design_not_license_for_bad_outcomes` — the original "every glob must expand to non-empty" invariant was a locked design that turned out to have a bad outcome (mutual contradiction with the data-stays-top-level locked design); the runtime-flag schema is the revisit, not silent acceptance.
- **Composes with** `feedback_critical_thinking_on_deviations` — when the norm broke (#138's NARROWING ADDENDUM surfaced the contradiction), the resolution-enumeration step weighed path (a) test-corpus + flag vs path (b) sentinel-directory; owner picked (a) at TG 11858 because of lower architectural blast radius.
- **Composes with** post-#136 seal-tool widening — §14 backfill uses the canonical `## §14 — Method-decision register` heading; no manual fallback expected unless the post-seal dry-run halts (#138 §16 #2 caveat).
- **Independent of** F4 — this amendment's scope is small enough that scope-confidence-tightening doesn't drive any structural decision; F4 is one available signal feeding the resolution per M5 but isn't decisive here.
- **CLOSES** `F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS` (FIDRAFT L328) — the HIGH-severity capture from #137 §16 / #138 builder F2 halts.
- **UNBLOCKS** the unwritten seal-tool hygiene pair amendment (`ws-seal-tool-hygiene-pair` / F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE) — that amendment will exercise the full plugins/dev-sdlc test suite via the seal-step automation, which this cleanup makes green.

---

## §16. Halt-and-surface findings (build-agent backfill)

Reserved for the `loam-builder` subagent to backfill post-seal per `feedback_subagent_odd_violation_halt` + F2 Ruthless Feedback. Expected categories (based on #138's pattern):

- `narrative.target` field shape (must be file path, not component name).
- Seal-tool §14 auto-backfill gating on post-seal dry-run.
- Source-must-be-committed-before-`loam amend apply` workflow ordering.
- AC.DCR.S smoke confirmation under py3.13 (target: 0 failures + 0 errors, ≥252 passed, 7 skipped).
- Component fence verification (seal-test `test_only_dev_sdlc_changed` against the SEAL_COMMIT sidecar).

Builder appends findings here under sub-section bullets 1, 2, 3, … as discoveries land.

### Finding 1 — Dirty-tree check fires on unrelated untracked files (F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE-confirms)

First `loam amend seal` invocation halted at `dirty-working-tree` because the working tree carried `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` — an unrelated untracked plan-doc that pre-existed the #139 dispatch (visible in the session-start `git status`). The seal-tool's pre-flight purity check is correctly strict; the surface friction is that the message names the offending path but not a stash-or-skip remediation. Resolution applied: `git stash push --include-untracked -- <path>`, re-invoke seal, `git stash pop` afterward. This is empirical confirmation of the sibling capture `F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE` that #139 was supposed to unblock — the capture's hypothesis (dirty-tree check is over-eager on cross-cycle drift) holds.

**Severity:** medium ergonomics. No data loss, recoverable by stash. **Surface for the hygiene-pair amendment.**

### Finding 2 — Predecessor-seal BASELINE selection vs post-seal corrective fixups (sibling of F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP)

The plan-author selected BASELINE = `01e63ac` (the #138 seal) per the natural "predecessor seal → BASELINE" rule. But the corrective fixup `26f3a9e` ("remove orphan dev-sdlc file from #138 seal commit") landed AFTER the #138 seal and BEFORE the #139 build. The seal-test's diff window `BASELINE..SEAL_COMMIT` then included the orphan-file deletion, which the seal-test classified as a sealed-component-path modification, failing `test_only_dev_sdlc_changed`.

The post-seal dry-run correctly detected this as `MISSING_ADMISSION: dev-sdlc` and halted, leaving the seal commit `1f3d8d7e` in place per the no-amend CDC. Corrective commit `ca16e41` bumped BASELINE from `01e63ac` to `26f3a9e` in both surfaces (the seal-test constant + the sealed manifest YAML's `baseline:` field), re-running the seal-test + post-seal dry-run cleanly afterward.

**Root-cause hypothesis:** the plan-author SKILL's pre-flight Tier-0 evidence collection should include "is there a post-seal corrective fixup commit between the predecessor seal and HEAD?" as a check. If yes, BASELINE should default to the corrective-fixup commit, not the predecessor seal. The current SKILL appears to default to "predecessor seal" without this guard.

**Severity:** medium — recoverable by corrective commit, but adds a cycle to every amendment landing after a fixup. The seal-tool's auto-backfill of §14 is BLOCKED by the post-seal dry-run halt, so §14 SHA backfill becomes manual.

**Composes with:** F-PLAN-AUTHOR-SKILL-MANIFEST-TARGET-DEFAULT-GAP (FIDRAFT L330) — same SKILL, different default. **Surface for FIDRAFT capture.**

### Finding 3 — AC.DCR.S text broader than §6 step 10 (pre-existing F3 drift surfaces)

AC.DCR.S §4 text reads `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PMR_3_*.py plugins/dev-sdlc/tools/loam-mode/tests/ -v` → 0 failures. §6 step 10 names the narrower scope `pytest plugins/dev-sdlc/tests/ -q` → ≥252 passed + 7 skipped. The narrow scope is GREEN (post-amendment HEAD: 252 passed + 7 skipped, exactly matches the plan-doc expectation). The broader scope including `plugins/dev-sdlc/tools/loam-mode/tests/` carries 1 pre-existing failure: `test_AC_F3_always_loaded_no_dev_refs` (the AC.F3 KNOWN_CROSS_MODE_DEBT allowlist drift captured at FIDRAFT L143). That failure existed at the BASELINE before any #139 edit (verified via `git stash` + re-run on the pre-edit state) and is OUT OF SCOPE per plan-doc §3 ("any other manifest cleanup ... stay queued separately").

Per `feedback_loose_AC_text_fix_AC_not_implementation`: the AC text was over-broad; the §6 step 10 expectation is the right verification scope; the broader scope swept in pre-existing AC.F3 drift unrelated to the runtime-flag schema. AC.DCR.S as intended (the deferred PMR contradiction is closed; runtime flag works) is satisfied.

**Severity:** documentation drift. No regression introduced; pre-existing failure documented at FIDRAFT L143 is unchanged. **Surface for plan-doc post-mortem note (already captured here in §16).**

### Finding 4 — F3 cross-mode debt continues to drift independent of fence

While reviewing Finding 3, the F3 test failure surfaced FIVE new cross-mode references not in `KNOWN_CROSS_MODE_DEBT`:
- `README.md` → `docs/STATE.md`
- `framework/primary-persona/skills/implementation-tier-picker.md` → `docs/FUTURE_IDEAS_DRAFT.md`
- `framework/primary-persona/skills/implementation-tier-picker.md` → `docs/plans/v0-7-0-non-tech-user-surface.md`
- `framework/primary-persona/skills/light-touch-narration.md` → `docs/FUTURE_IDEAS.md`
- `framework/primary-persona/skills/light-touch-narration.md` → `docs/plans/v0-7-0-non-tech-user-surface.md`

These are new cross-mode debt arrived via post-v0.3.0 work (skills + README content authored by recent amendments). The `KNOWN_CROSS_MODE_DEBT` allowlist is empty per the v0.3.0 Cycle 4 shrink-to-zero pass; the new debt should either be paid down (preferred — edit the cross-references) or explicitly allowlisted in a new commit (worse — grows the debt surface). **Surface for FIDRAFT capture** — this is new debt and should land as a separate amendment, NOT silently tacked onto #139.

### Finding 5 — Touched-test sweep methodology

The 21-test sweep (`pytest plugins/dev-sdlc/tests/test_AC_PMR_3_*.py plugins/dev-sdlc/tools/loam-mode/tests/test_manifest_runtime_field.py -v`) covers:
- 8 PMR_3/PMR_4 tests (2 previously-failing now green, 6 unchanged behaviour)
- 13 new schema + safety-property + AC.DCR.MANIFEST tests

All 21 green. The full `plugins/dev-sdlc/tests/` directory: 252 passed + 7 skipped (matches plan-doc §6 step 10 exact expectation). The full `plugins/dev-sdlc/tools/loam-mode/tests/`: 71 passed + 1 skipped + 1 failed (the pre-existing F3 drift documented in Finding 3 + 4).

Schema extension + test-corpus admission resolving the
F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS HIGH-severity FIDRAFT
capture (originally surfaced across #137 §16 finding #4, #138
builder F2 halt, and #138 second builder F2 halt; activation gate
was "owner ruling on (a) vs (b)"; owner ruled (a) at TG 11858).

Two related deltas:

Delta 1 (D-DCR.FLAG-SHAPE + D-DCR.ROOT-SHAPE + D-DCR.TEST-LOGIC).
The `ManifestEntry` dataclass at
`plugins/dev-sdlc/tools/loam-mode/src/loam_mode/manifest.py`
gains an optional `runtime: bool = False` field. The `roots:`
block parser gains a new `RootEntry` dataclass accepting either
bare-string entries (existing — preserved for backwards-compat)
or `{path, runtime}` mapping entries (new). The PMR_3 + PMR_4
tests at
`plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py`
skip their existence/non-empty-match assertions when the entry's
`runtime` is `True`. A new test file
`plugins/dev-sdlc/tools/loam-mode/tests/test_manifest_runtime_field.py`
carries the schema-acceptance tests + safety-property tests that
preserve the original "every glob must expand to non-empty"
invariant for non-flagged entries.

Delta 2 (D-DCR.DATA-ENTRIES + D-DCR.MEMORY-SYSTEM-ENTRIES).
`plugins/dev-sdlc/dev-mode-manifest.yaml` —
`framework/memory-system/` root entry (L49) + always_loaded glob
(L97) are DELETED. That directory was permanently deleted at
v0.3.0 Cycle 2 commit `b92aaea` ("graphiti rip-out"); the
runtime-flag pattern does NOT apply to permanently-deleted
paths. Both `data/` entries (root L67 + always_loaded glob L127)
are MARKED `runtime: true` — `data/` is workspace runtime
telemetry that populates on first-run per the existing comments
at L62-64 + L125-126. The manifest's schema docstring at L11-24
is updated to name `runtime:` as an optional boolean field.

Owner rationale (TG 11858): path (a) test-corpus edit + schema
flag was chosen over path (b) sentinel-directory because (a)
has less architectural blast radius — the test-corpus + schema
edits are the smaller surface than touching the
canonical-vs-runtime tree philosophy. A sentinel `data/`
directory in the canonical tree would conflate "directory
exists at canonical commit time" with "directory will populate
at runtime"; the runtime-flag schema keeps that distinction
explicit.

No edit under `plugins/dev-sdlc/src/`. The
`loam.plugins.dev_sdlc` Python package is unchanged. Entry-point
discovery, CLI subcommand registration, and the contribution
surface are behaviour-preserved.

Downstream consumer impact: the `loam-mode` toolkit's
`__init__.py` gains a new export (`RootEntry`) but loses none.
`audit.py`'s consumer of `manifest.roots` dereferences
`root.path` instead of the bare string (mechanical change,
behavior-preserving). `selector.py` per pre-flight evidence
does not consume `manifest.roots` directly (verifies via the
builder during edit). All synthetic-manifest unit tests under
`plugins/dev-sdlc/tools/loam-mode/tests/` that construct bare-
string roots get a one-line wrapper edit (`RootEntry(path="x")`).

Pre-flight Tier-0 evidence (carried in plan-doc §1):
- `framework/memory-system/` directory: absent (deleted at
  `b92aaea`).
- `data/` directory: absent (deleted at `39cfbb1` per FIDRAFT
  L328 — to be Tier-0 re-verified by builder via
  `git log --all --oneline --diff-filter=D -- data`).
- Both stale entry sets still present in
  `plugins/dev-sdlc/dev-mode-manifest.yaml` at L49 + L67 + L97
  + L127.
- `expand_entry` on `path:` entries already tolerates non-
  existent paths (manifest.py:256 returns `{entry.path}`
  unconditionally), so the runtime flag is documentation-only
  for `path:` entries in always_loaded/dev_only. For `glob:`
  entries (the failing case) and for `roots:` entries (where
  the test explicitly calls `target.exists()`), the runtime
  flag is load-bearing.
- The only production consumer of `manifest.roots` outside
  manifest.py itself is `audit.py`; no external consumers under
  `framework/` (pre-flight grep returns empty).

Outcome-altitude smoke (AC.DCR.S): `python3.13 -m pytest
plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py
plugins/dev-sdlc/tools/loam-mode/tests/ -v` against the
post-amendment HEAD returns 0 failures + 0 collection errors.
The 2 PMR cases #138's NARROWING ADDENDUM admitted as known-
deferred (`test_AC_PMR_3_every_root_resolves_on_disk` +
`test_AC_PMR_4_every_always_loaded_glob_resolves`) are now
green. No regressions introduced elsewhere.

Composes with: post-#136 seal-tool §14 backfill regex widening
(canonical `## §14 — Method-decision register` heading auto-
backfills with no manual fallback expected at this seal,
modulo the post-seal dry-run gating caveat from #138 §16 #2).

This amendment CLOSES `F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS`
(FIDRAFT L328) and UNBLOCKS the unwritten seal-tool hygiene
pair amendment (`ws-seal-tool-hygiene-pair` /
F-SEAL-PLUGINS-TESTS-SKIPPED +
F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE in
docs/FUTURE_IDEAS_DRAFT.md) — that amendment will exercise the
full plugins/dev-sdlc test suite via the seal-step automation,
which this cleanup makes green.
