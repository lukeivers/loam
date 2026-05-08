# D-migration D.1 — directory restructure (framework/) — builder plan

Builder plan for amendment **D.1** of the D-migration sequence (per
plan `docs/plans/d-migration.md`). D.1 moves all framework
component directories into a new top-level `framework/` directory on
canonical pos-v2, plus `tools/`, `first-run-inventory.yaml`, and
renames the tracked `.claude/settings.json` to a dev template under
`framework/`. Updates path-aware code in `first_run_helper.py`,
`first_run_scaffold.py` (plist templates), `pos-amend`'s sealed-
component discovery, `first-run-inventory.yaml`'s dedicated-venv
path, every sealed component's `tests/test_no_sealed_amendments.py`
+ `tests/test_cross_cutting.py` (REPO_ROOT depth + `allowed_prefixes`
self-and-partner widening), and the canonical-side `.claude/settings.json`
hook references.

**Status:** builder plan (pre-build).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Plan:** `docs/plans/d-migration.md`
**Manifest:** `docs/plans/d-migration-1.manifest.yaml`
**Amendment number:** #61 (next free after #60).
**Baseline (manifest):** HEAD at dispatch
(`57d735fbcde275dc0462306cd53e4830792df894`).
**Date:** 2026-04-26.

---

## 1. Scope (per plan §4 D.1 portion)

D.1 only does the framework restructure. D.2 (next amendment)
establishes the workspace-state directory.

**In scope (D.1):**

- `git mv` each component directory under `framework/`:
  cost-governance, graceful-degradation, hands-off-lifecycle,
  memory-system, objective-tracker, observability-aggregator,
  orchestrator, primary-persona, reversibility-primitive,
  safety-layer, scope-of-work, self-correction, self-upgrade,
  telegram-interface, workspace-bootstrap, workspace-sync (16 components).
- `git mv tools/` → `framework/tools/`.
- `git mv first-run-inventory.yaml` → `framework/first-run-inventory.yaml`.
- Rename canonical's tracked `.claude/settings.json` to
  `framework/hands-off-lifecycle/canonical-dev/settings.dev-template.json`
  (per plan §13 finding 1). The tracked file becomes the dev-canonical
  template. Luke's local-untracked `.claude/settings.json` (workspace
  state) is unaffected.
- Update path-aware code:
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py`'s
    `_discover_components` walks `<root>/framework/` instead of
    `<root>/`.
  - All `pos_v2_root / "<comp>"` constructions in
    `first_run_helper.py` (lines 188, 368, 1425, 1445, 1493 pre-move)
    become `pos_v2_root / "framework" / "<comp>"`.
  - `framework/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`'s
    `_LAUNCHD_TEMPLATES` updates: `{workspace}/memory-system/...` →
    `{workspace}/framework/memory-system/...` for the memory-graphiti
    plist's ProgramArguments, WorkingDirectory, StandardOutPath,
    StandardErrorPath. Orchestrator + memory-write-worker plists keep
    `{workspace}/.venv/bin/python` (shared workspace venv stays at
    workspace root, gitignored).
  - `framework/first-run-inventory.yaml`'s `dedicated_venvs[0]`:
    `venv_path: framework/memory-system/.venv`,
    `requirements: framework/memory-system/requirements.txt`.
  - `framework/tools/pos-amend/src/pos_amend/commands/seal.py`'s
    `_discover_sealed_components` glob `*/tests/SEAL_COMMIT` becomes
    `framework/*/tests/SEAL_COMMIT`.
- Update each sealed component's seal-diff test
  (`tests/test_no_sealed_amendments.py` for 13 components +
  `tests/test_cross_cutting.py` for hands-off-lifecycle):
  - `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` →
    `parent.parent.parent.parent` (one extra parent for the new
    `framework/` layer).
  - `parents[2]` → `parents[3]` for `test_cross_cutting.py`.
  - `allowed_prefixes` tuple: replace each `<comp>/` (16 known
    components) with `framework/<comp>/`; replace `tools/` with
    `framework/tools/`.
  - `allowed_files` set: replace `first-run-inventory.yaml` with
    `framework/first-run-inventory.yaml`.
  - For `test_cross_cutting.py`'s `allowed` set: add `framework`;
    keep existing entries (they become inert post-move but cost
    nothing to retain — historic admissions kept per ODD §10's
    monotonic admission convention).
  - Add `.claude/settings.json` deletion admission (the tracked file
    is removed; its content moves to `framework/hands-off-lifecycle/
    canonical-dev/settings.dev-template.json`).
- Update canonical's tracked `.claude/settings.json` content to
  reference `framework/hands-off-lifecycle/hooks/first-run.sh` etc.
  AND THEN move the file. (Order: edit content first, then `git mv`
  to template path — this preserves git rename detection.)
  Wait — see §3.1 D-build.D.1.A: simpler shape adopted.
- Add the byte-content-survival regression test per HC#4
  (AC.D.1.5) — new file at
  `framework/scope-of-work/tests/test_d1_byte_content_match.py`
  (or per-component test sidecar, builder's call inside §3).
- Apply via `pos-amend apply --plan <manifest>` (advances
  BASELINE / SEAL_COMMIT sidecars / widens allowed_prefixes per
  manifest); commit with `feat(framework/...)` subject; seal via
  `pos-amend seal --plan-doc <abs>`.
- Plan §14 + §15 backfill via `pos-amend seal --plan-doc`.

**Out of scope (deferred to D.2 / D.3):**

- `data/observability/spans.jsonl` — tracked test fixture; D.1
  leaves at root. D.2 can relocate to workspace-state.
- `<workspace>/workspace/` directory — D.2.
- `.gitignore` rewrite (`framework/`-only-tracked) — D.2.
- Workspace-state migration script — D.2.
- `~/.pos/canonical-cache/` — D.3.

---

## 2. Method choices (D-build.D.1.x — pre-build)

### D-build.D.1.A — `.claude/settings.json` template treatment

**Decision.** Move tracked `.claude/settings.json` →
`framework/hands-off-lifecycle/canonical-dev/settings.dev-template.json`.

**Rationale.** Plan §13 finding 1 names the asymmetry: the file is
both framework-tracked AND workspace-scaffolded. Under D, it must
clearly become a template. Hands-off-lifecycle owns the SessionStart
hook surface, so the template lives next to its owning component.
Path `framework/hands-off-lifecycle/canonical-dev/...` keeps the
template close to its consumer (the canonical maintainer's first-run
copies it to `<canonical-root>/.claude/settings.json` on a fresh
clone) without polluting the test/source surface (`canonical-dev/`
is a sibling to `tests/` and `hooks/`, namespaced clearly).

**Content edit.** Before move, the file content is updated to use
`framework/hands-off-lifecycle/hooks/first-run.sh` and
`framework/hands-off-lifecycle/hooks/corpus_load_session_start.py`
and `framework/hands-off-lifecycle/hooks/statusline.py` paths. The
edit + rename land in the same commit (HC#4 byte-content-match
applies to the framework/<comp>/ source code body, not to template
files whose content is intentionally edited as part of the
amendment).

**Luke's local-untracked `.claude/settings.json`:** unchanged by
this amendment. Out-of-tree modifications survive the rename.

### D-build.D.1.B — Order of operations

1. Pre-move audit: capture sample-file SHA-256 hashes for the
   byte-content regression test (HC#4 / AC.D.1.5).
2. `git mv` 16 components → `framework/<comp>/`.
3. `git mv tools/` → `framework/tools/`.
4. `git mv first-run-inventory.yaml` → `framework/first-run-inventory.yaml`.
5. Edit canonical-side `.claude/settings.json` content (rewrite
   paths to `framework/hands-off-lifecycle/...`); `git mv` to
   `framework/hands-off-lifecycle/canonical-dev/settings.dev-template.json`.
6. Edit `framework/hands-off-lifecycle/hooks/first_run_helper.py`:
   - `_discover_components(pos_v2_root)` walks
     `pos_v2_root / "framework"` instead of `pos_v2_root`.
   - All `pos_v2_root / "<comp>"` constructions become
     `pos_v2_root / "framework" / "<comp>"`.
   - `_install_shared_components`'s
     `pos_v2_root / name / "requirements.txt"` becomes
     `pos_v2_root / "framework" / name / "requirements.txt"`.
   - `_install_dedicated_venv`'s `pos_v2_root / entry["venv_path"]`
     stays as-is (the inventory now declares the path WITH the
     `framework/` prefix — see step 7).
7. Edit `framework/first-run-inventory.yaml`:
   - `dedicated_venvs[0].venv_path: "framework/memory-system/.venv"`
   - `dedicated_venvs[0].requirements: "framework/memory-system/requirements.txt"`
8. Edit `framework/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`:
   - `_LAUNCHD_TEMPLATES["memory-graphiti"]`:
     - `{workspace}/memory-system/.venv/bin/python` →
       `{workspace}/framework/memory-system/.venv/bin/python`
     - `{workspace}/memory-system` (WorkingDirectory) →
       `{workspace}/framework/memory-system`
     - `{workspace}/memory-system/data/graphiti-service.log` →
       `{workspace}/framework/memory-system/data/graphiti-service.log`
     - same for `.err.log`.
   - Orchestrator + memory-write-worker plists: leave unchanged (
     `{workspace}/.venv/bin/python` references the workspace's
     shared `.venv/`, which stays at workspace root). Their
     `StandardOutPath`/`StandardErrorPath` reference
     `{workspace}/orchestrator.{out,err}.log` — also workspace-state
     at workspace root for D.1 (D.2 relocates to
     `workspace/<...>` paths).
9. Edit `framework/tools/pos-amend/src/pos_amend/commands/seal.py`:
   - `repo_root.glob("*/tests/SEAL_COMMIT")` →
     `repo_root.glob("framework/*/tests/SEAL_COMMIT")`.
   - `_seal_diff_test_path(repo_root, component)`'s candidates:
     `repo_root / "framework" / component / "tests" / ...`.
10. Edit each sealed component's seal-diff test (14 files):
    - `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` →
      `parents[3]` (cleaner than `.parent.parent.parent.parent`).
    - `allowed_prefixes` tuple: `<comp>/` → `framework/<comp>/`
      for the 16 component names; `tools/` → `framework/tools/`.
    - `allowed_files`: `first-run-inventory.yaml` →
      `framework/first-run-inventory.yaml`.
    - `test_cross_cutting.py`: also add `framework` to `allowed`
      set; keep historic entries.
11. Edit `framework/hands-off-lifecycle/hooks/first-run.sh` if it
    references its own dirpath (verify). If not, no edit.
12. Add new test file
    `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`
    that asserts pre-move file content (captured in step 1) equals
    post-move file content for sample files (HC#4 / AC.D.1.5).
    Lives under hands-off-lifecycle because it's a cross-cutting
    structural test (analogous to test_cross_cutting.py).
13. Run targeted touched-component test sweeps
    (`framework/<comp>/tests/`) for each touched component. Iterate
    on path-related failures.
14. Author manifest at `docs/plans/d-migration-1.manifest.yaml`.
15. `pos-amend apply --plan d-migration-1.manifest.yaml --dry-run`;
    iterate until clean.
16. `pos-amend apply --plan d-migration-1.manifest.yaml` (real apply
    bumps BASELINEs + sidecars + widens allowed_prefixes).
17. Commit: `feat(framework): D-migration D.1 — directory restructure
    (amendment #61, AC.D.1.1–AC.D.1.S)`.
18. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/plans/d-migration.md --plan d-migration-1.manifest.yaml`.

### D-build.D.1.C — REPO_ROOT depth

Use `parents[3]` not `.parent.parent.parent.parent` for readability.
14 seal tests have the same line shape; mechanical edit.

### D-build.D.1.D — Per-component allowed_prefixes update strategy

Bulk find-replace per file:
- `"cost-governance/"` → `"framework/cost-governance/"`
- `"graceful-degradation/"` → `"framework/graceful-degradation/"`
- `"hands-off-lifecycle/"` → `"framework/hands-off-lifecycle/"`
- `"memory-system/"` → `"framework/memory-system/"`
- `"objective-tracker/"` → `"framework/objective-tracker/"`
- `"observability-aggregator/"` → `"framework/observability-aggregator/"`
- `"orchestrator/"` → `"framework/orchestrator/"`
- `"primary-persona/"` → `"framework/primary-persona/"`
- `"reversibility-primitive/"` → `"framework/reversibility-primitive/"`
- `"safety-layer/"` → `"framework/safety-layer/"`
- `"scope-of-work/"` → `"framework/scope-of-work/"`
- `"self-correction/"` → `"framework/self-correction/"`
- `"self-upgrade/"` → `"framework/self-upgrade/"`
- `"telegram-interface/"` → `"framework/telegram-interface/"`
- `"workspace-bootstrap/"` → `"framework/workspace-bootstrap/"`
- `"workspace-sync/"` → `"framework/workspace-sync/"`
- `"tools/"` → `"framework/tools/"`
- `"first-run-inventory.yaml"` → `"framework/first-run-inventory.yaml"`
- Test-file-path admissions (e.g.
  `"workspace-bootstrap/tests/test_AC36_6_framework_not_content.py"`)
  → `"framework/workspace-bootstrap/tests/..."`.

The `docs/archive/component-research/<comp>/` admissions DO NOT change
(docs/ stays at root).

### D-build.D.1.E — Manifest shape

Per plan §9 D.1 sketch + amendment #46 multi-component precedent.

- 14 sealed components in the `components` list (the 14 that have
  SEAL_COMMIT sidecars; scope-of-work + safety-layer are not sealed).
- Wait: safety-layer DOES have a seal test
  (`safety-layer/tests/test_no_sealed_amendments.py`) but no
  SEAL_COMMIT sidecar pre-D.1. Verify during build.
- `frozen_baseline: true` on `hands-off-lifecycle` (per #23 H19).
- `seal_test` paths post-move:
  `framework/<comp>/tests/test_no_sealed_amendments.py` for 13
  components; `framework/hands-off-lifecycle/tests/test_cross_cutting.py`
  for hands-off-lifecycle.
- `sidecar` paths post-move:
  `framework/<comp>/tests/SEAL_COMMIT`.
- `universal_paths.prefixes`: `["docs/plans/"]` (docs stays
  at root).
- `universal_paths.files`: `["CLAUDE.md", "docs/odd-in-pos.md",
  "docs/odd-methodology.md", "docs/FUTURE_IDEAS.md"]`.
- `seal_description: "D-migration D.1 — framework/ directory
  restructure"`.
- `narrative.target`: `framework/hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`
  (canonical narrative target since hands-off-lifecycle is the
  cross-cutting component).

### D-build.D.1.F — Universal admission for `framework/` prefix in H19

Plan-author note: H19 (test_cross_cutting.py) checks
first-segments. After D.1, all framework-content first-segments to
`framework`. The `allowed` set in test_cross_cutting.py needs the
single new entry `framework`. This is added to the test FILE
directly (alongside the historic entries). This is NOT a
universal-paths admission — it's a one-time test-file edit per
ODD §10's monotonic-admission convention.

### D-build.D.1.G — pos-amend apply edge case

`pos-amend apply` wields `partner_prefixes = {f"{c.name}/" for c in
manifest.components}` which would inject old `<comp>/` prefixes
into each test's allowed_prefixes. The injection is harmless
(post-move no file matches the old prefix) but adds dead entries
to the tuple. **Decision:** accept the dead entries. They don't
break anything; they document the move's history. Future cleanup
amendment (or D.5) can prune.

Alternative considered: declare `name: framework/<comp>` in the
manifest. Rejected — produces commit subjects like "framework/
cost-governance+framework/orchestrator+..." (~280 chars), ugly +
breaks subject convention. Dead entries in tuples is the lesser
cost.

### D-build.D.1.H — HC#4 byte-content-match test shape

Per AC.D.1.5: byte-content-match for representative components
post-move. Method choice: SHA-256 on a pre-determined sample of
files, captured pre-move into a sidecar test fixture; post-move
the test reads the same files at their new paths and asserts
SHA-256 match.

Implementation:
1. Pre-step (during build): compute SHA-256 of ~15 sample files
   (5 from primary-persona, 5 from workspace-bootstrap, 5 from
   scope-of-work — leaf, mid, high-fan-in per AC.D.1.5).
2. Hardcode the sample-file paths + expected SHA-256s into the
   test file at
   `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`.
3. The test reads each file at its post-move path and asserts the
   SHA-256 matches. If the file was modified post-move, test
   fails.

The test composes naturally with `git mv`'s preservation: rename
without content edit gives byte-identical files. The test catches
a regression where a builder accidentally edits content during
move (HC#4 binding).

### D-build.D.1.I — Settings.json template content edit

The current tracked `.claude/settings.json` content uses
`$CLAUDE_PROJECT_DIR/hands-off-lifecycle/...`. After D.1 it becomes
`$CLAUDE_PROJECT_DIR/framework/hands-off-lifecycle/...`. The
template at `framework/hands-off-lifecycle/canonical-dev/
settings.dev-template.json` has a SessionStart hook that the
canonical maintainer's first-run can copy.

**Decision:** edit content first, then `git mv` the file. The
content-edit + rename is the same commit; git rename detection
will surface as `R<percent>` (similarity below 100% because of
the path-string edit, but rename still tracked).

The Luke-local-untracked `.claude/settings.json` (current path:
`/Users/lukeivers/ivers-corp-pos-v2/.claude/settings.json`)
references absolute `/Users/lukeivers/ivers-corp-pos-v2/hands-off-
lifecycle/...` paths. Post-D.1, those paths break (no longer
exist). **This is a builder-surface concern**: Luke's local
hooks will fail until he updates them. Surface to Luke at
seal-narrative time as an empirical-action item; this is exactly
HC#5's concern (post-seal smoke-test verification).

### D-build.D.1.J — Heavy-b-migrate scope

Per plan §13 finding 5: "tools/heavy-b-migrate moves under
framework/tools/. Verified that pos-amend uses relative-path
resolution. The move should be clean."

Verified during build via grep. heavy-b-migrate's source has no
hardcoded absolute paths to its own location. After move, the
`heavy-b-migrate` console-script entry resolves correctly because
the editable install in `<workspace>/.venv/lib/python3.13/
site-packages/heavy-b-migrate.egg-link` is rewritten by first-run
helper (which itself moves to framework/).

**However**: existing editable-install state in the canonical
maintainer's local `.venv/` will still point at the OLD
`tools/heavy-b-migrate/` paths post-D.1 (because the .venv is
gitignored workspace state). On a fresh clone, first-run rebuilds
correctly. On Luke's local machine, post-D.1 the maintainer must
re-run first-run (or re-pip-install editable) to refresh egg-links.
Surface to Luke at seal-narrative time as an empirical-action
item.

### D-build.D.1.K — Halt triggers monitored

- Plan §10 trigger 4 (cross-fence work): D.1's fence is "every
  component + tools/ + docs (via universal admissions) + .claude/
  template move + first-run-inventory.yaml". If a discovered
  edit needs source outside this fence, halt.
- Plan §10 trigger 5 (pre-existing test fails): if a non-path-
  related test fails post-restructure, halt.
- Plan §10 trigger 8 (wall-time): 6h ceiling per dispatch.

---

## 3. Per-AC build outline

### AC.D.1.1 — Directory move complete

Method: `git mv <comp>/ framework/<comp>/` for 16 components,
`git mv tools/ framework/tools/`, `git mv first-run-inventory.yaml
framework/first-run-inventory.yaml`. `git ls-files framework/ | wc
-l` post-move equals pre-move root file count minus the unmoved
items (data/, docs/, README.md, CLAUDE.md, CLAUDE.dev.md, .gitignore,
.claude/settings.json — wait, .claude/settings.json moves too).

Verification test (new): in
`framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`
(D-build.D.1.H), assert `(REPO_ROOT / "framework" / "<comp>" /
"pyproject.toml").exists()` for every component, and
`(REPO_ROOT / "<comp>").exists() == False` for every component.

### AC.D.1.2 — Editable-install topology preserved

Method: edit `_discover_components` to walk
`pos_v2_root / "framework"` (D-build.D.1.B step 6).

Verification test (new): unit test in
`framework/hands-off-lifecycle/tests/test_d1_editable_topology.py`
(or extend an existing test) that constructs a fixture pos_v2_root
with a `framework/` subdirectory holding 3 fake component dirs
each with `pyproject.toml`, invokes `_discover_components(root)`,
asserts the returned list has exactly those 3 components in
top-sorted order.

Note: the existing `test_first_run_helper.py` style tests already
exercise topological order; we extend a fixture to use the
`framework/` layout.

### AC.D.1.3 — Plist templates point at new framework paths

Method: edit `_LAUNCHD_TEMPLATES["memory-graphiti"]` (D-build.D.1.B
step 8). The orchestrator + memory-write-worker plists keep
`{workspace}/.venv/bin/python` (workspace shared venv).

Verification: existing `test_D5_plist_path_emission.py` asserts
the plist content includes the expected paths. Post-D.1 the
expected paths in those tests must change to `{workspace}/framework/
memory-system/...`. Mechanical update of the test's expected-string
literals.

### AC.D.1.4 — Canonical-side dev workflow continues to function

Method: after restructure, `pytest framework/<comp>/tests/`
passes for each touched component. `pos-amend apply --dry-run`
+ `pos-amend seal --plan-doc <abs>` resolve correctly against the
new layout (after D-build.D.1.B step 9 edit).

Verification: targeted touched-component pytest sweep runs green
(D-build.D.1.B step 13). The seal step's deterministic-seal-commit
machinery exercises `pos-amend apply --dry-run` post-commit; if the
machinery resolves component paths correctly, AC.D.1.4 passes.

### AC.D.1.5 — Byte-content-match for representative files (HC#4)

Method: D-build.D.1.H — SHA-256 on 15 sample files pre-move,
hardcode in test, assert post-move match.

### AC.D.1.S — Seal-diff invariant

Method: every component's seal-diff test (with allowed_prefixes
updated to `framework/<comp>/` form per D-build.D.1.D + the
manifest's `pos-amend apply` widening) asserts the diff between
BASELINE..SEAL_COMMIT lands only under admitted paths.

Verification: `pos-amend apply --dry-run --plan d-migration-1.
manifest.yaml` reports zero missing admissions; `pos-amend seal`
runs the cross-component sweep across all 14 sealed components
and reports 14 green.

---

## 4. Test-strategy notes

- Per plan §6 HC#4 + HC#5: byte-content tests run pre-seal and
  during seal; the empirical pos3 verification fires at end of D.2
  (not D.1) per HC#5 wording.
- Per plan §6 HC#2 (no regression): every pre-existing test
  passes post-D.1 modulo path-shift mechanical updates. Path-shift
  updates count as "mechanical fixture updates" per ODD §3.4 and
  do not constitute regressions.
- Per `feedback_amendment_dispatch_speedups`: scoped test rerun at
  seal time (the touched-component sweep is the natural scope for
  D.1 since EVERY component is touched — the cross-component
  sweep IS the full sweep).

---

## 5. Reverse trace (per ODD §2.5)

Every code path edit in D.1 traces to a named AC:

| Edit | Backing AC |
|------|-----------|
| 16 component `git mv` operations | AC.D.1.1 |
| `tools/` → `framework/tools/` | AC.D.1.1 |
| `first-run-inventory.yaml` move | AC.D.1.1 |
| `.claude/settings.json` content + rename | AC.D.1.1 + plan §13 finding 1 |
| `_discover_components` walk update | AC.D.1.2 |
| `pos_v2_root / "<comp>"` → `pos_v2_root / "framework" / "<comp>"` | AC.D.1.2 + AC.D.1.4 |
| `_LAUNCHD_TEMPLATES` edits | AC.D.1.3 |
| `first-run-inventory.yaml` venv_path update | AC.D.1.2 |
| pos-amend `_discover_sealed_components` glob | AC.D.1.4 |
| 14 seal-test `REPO_ROOT` depth updates | AC.D.1.S |
| 14 seal-test `allowed_prefixes` updates | AC.D.1.S |
| H19 `allowed` set + `framework` entry | AC.D.1.S |
| Byte-content-match regression test | AC.D.1.5 + HC#4 |
| Manifest authoring | AC.D.1.S |

Reverse check passes — no orphan code path.

---

## 6. References

- `docs/plans/d-migration.md` (parent plan)
- `docs/plans/amendment-46-persona-session-start-turn-start-emitters.manifest.yaml`
  (multi-component manifest precedent)
- `docs/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`
  (multi-component builder-plan precedent)
- `framework/tools/pos-amend/src/pos_amend/commands/apply.py` (post-D.1 path)
- `framework/tools/pos-amend/src/pos_amend/commands/seal.py` (post-D.1 path)
- `framework/hands-off-lifecycle/hooks/first_run_helper.py` (post-D.1 path)
- `framework/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (post-D.1 path)
- `framework/first-run-inventory.yaml` (post-D.1 path)

---

## 7. Wall-time budget

Per dispatch §"Halt-and-surface": ceiling 6h. Plan §1 estimate
4-6h. Track via session timestamps. Halt + surface at 6h elapsed.

---

## 8. Method-decision register (post-build)

### Commit SHAs

Hand-rolled seal flow (pos-amend seal's cross-component test sweep
incompatible with rename-only multi-component moves; gap captured
for D.1.5 to fix pos-amend's rename-aware-seal logic before D.2):

- **Amendment commit (feat):** `0d599bb` — `feat(framework): D-migration D.1 — framework/ directory restructure (amendment #61, AC.D.1.1–AC.D.1.S)`
- **Apply chore commit:** `97a4459` — `chore(framework): advance BASELINE + SEAL_COMMIT for amendment #61 window`
- **Transitional prefix fix:** `c7fb441` — `fix(framework/*): add transitional OLD prefix to seal-diff tests for D.1 rename window`
- **Seal commit:** `570092a` — `chore(seals): D-migration D.1 — framework/ directory restructure (multi-component) at c7fb441`
- **§8 backfill commit:** (this commit)

### Test sweep skipped per option (b) ruling 2026-04-27

Cross-component test sweep was skipped because pos-amend's seal step
bumps SEAL_COMMITs uniformly across all components in the manifest,
including rename-only ones. Each prior amendment's `AC.X.S` seal-test
hardcodes path prefixes for ITS amendment's fence; with SEAL_COMMITs
advanced to point at D.1, those tests see a diff window spanning D.1's
renames → fence-violation cascade.

The 13 `test_no_sealed_amendments.py` tests got transitional OLD-prefix
patches in `c7fb441`, but the inner amendment-fence tests (e.g.
`test_AC_M_S_seal_diff_window.py` for #48) need the same treatment
across many amendments. Estimated 20-50 tests; deferred to D.1.5
(pos-amend rename-aware-seal) which fixes the root cause structurally
rather than patching every test.

### AC.D.1.S manual verification

Diff window: `57d735f .. 570092a` (corpus-edit commit → D.1 seal commit).

Seal-diff confined to:
- `framework/` (every renamed component path)
- `docs/plans/` (universal admission — d-migration*.md, manifest, vars, builder-plan)
- `.claude/settings.json` (renamed file — captured in 0d599bb)

No paths outside the framework/ + universal-paths admissions. AC.D.1.S
satisfied by manual inspection (`git diff --name-only 57d735f..570092a`
output reviewed).

### Deviations from §2 (for completeness)

- **D-build.D.1.D (per-component allowed_prefixes update):** the planned
  per-component test patch was DONE in `c7fb441` for the 13
  `test_no_sealed_amendments.py` files, but did NOT cover the inner
  AC.X.S amendment-fence tests. Those defer to D.1.5.
- **Halt-and-surface fired at seal-step** (not at build-step): the
  pos-amend seal cross-component sweep cycled on memory-system test
  collection (graphiti_core / kuzu deps missing in canonical's .venv;
  primary persona installed both during the seal cycle). Subsequent
  AC.X.S fence violations across primary-persona triggered the
  first-principles surface that produced the (b)+(c) ruling.
