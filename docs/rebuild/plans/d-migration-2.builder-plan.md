# D-migration D.2 — workspace-state directory established + reader cutover

**Builder-plan.** Authored 2026-04-27 against canonical pos-v2 HEAD `9221fa0`. Wider-fence ruling locked by primary persona 2026-04-27 per the prior D.2 builder's halt-and-surface (option (a) — extend fence to all readers). Amendment #63.

This builder-plan refines the parent plan `docs/rebuild/plans/d-migration.md` §4 D.2 with the wider-fence ACs. Method shape is the builder's call within the AC outcome bound; this plan records it for review.

---

## §0. Summary + named decisions

**Outcome.** After D.2 seals: a fresh-clone first-run produces every workspace-state file under `<workspace>/workspace/<...>` rather than `<workspace>/<...>`. Every reader of workspace-state paths in framework code reads from `<workspace>/workspace/<...>`. Path computation lives in one new helper module so future moves happen in one place. A Pydantic-validator structural guard refuses workspace-state writes that would land under `framework/`. `<workspace>/.claude/` stays at workspace root per D-Q.A4. pos3's existing flat-tree state is NOT migrated by this amendment (HC#5 — that's a future amendment).

**Named decisions (recommendation pre-attached; primary persona rules from this list):**

1. **D.2-build.A — Path-helper home.** Add a new module `framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py` that exports the canonical workspace-state path constants + helper functions (`workspace_state_dir(workspace_root) -> Path`, `pos_subdir(workspace_root)`, `personas_dir(workspace_root)`, `data_subdir(workspace_root)`, `mcp_json_path(workspace_root)`, `tracker_db_path(workspace_root)`, `scratch_dir(workspace_root)`, `orchestrator_log_paths(workspace_root) -> tuple[Path, Path]`, `memory_worker_log_paths(workspace_root)`). Every reader replaces `workspace_root / ".pos" / X` with `pos_subdir(workspace_root) / X` etc. **Recommendation: accept.** Single point of truth; future moves change one file. Trade-off: adds an import edge from primary-persona / hands-off-lifecycle / workspace-sync / self-upgrade / loam-mode onto workspace-bootstrap. That edge is acceptable because (a) workspace-bootstrap is the framework's bootstrap surface — every component already depends on it for service registration / host fixtures, (b) the helper is pure-Python (no runtime side effects), (c) pyproject editable installs already wire the import path. Alternative (own-component `workspace-paths/`) was considered in the halt-surface report; rejected as adding a sealed-component without clear need.

2. **D.2-build.B — Hands-off-lifecycle hooks (non-Python-package code) reach the helper how?** Hands-off-lifecycle's `hooks/first_run_state.py` etc. are **NOT** Python packages — they're standalone scripts under `framework/hands-off-lifecycle/hooks/`. They cannot `from workspace_bootstrap.workspace_paths import ...` without dependency churn (the hook scripts run under launchd / from-bash subprocesses; they import only stdlib + their own helper module). **Recommendation: duplicate the constants in `first_run_state.py` (and any other hook that needs them) with a comment pointing at `workspace_paths.py` as the canonical source.** Trade-off: small repetition. Alternative (refactor hooks to import workspace_bootstrap) was considered; rejected because the hooks have an explicit "minimum-import" contract (per amendment #4's first-run-helper architecture — the hook should boot before the workspace's `.venv` is built, so it can only use stdlib).

3. **D.2-build.C — HC#6 structural guard shape.** The dispatch recommends a Pydantic validator on a `WorkspaceLayout` schema. Two viable options:
   - **(c1)** Add a `WorkspaceLayout` Pydantic model in `workspace_paths.py` with a model-level validator that asserts every emitted path's first component (after the workspace root) is `"workspace"` (or `".claude"` for the Claude Code surface) — refuses `"framework"`. Every helper instantiates `WorkspaceLayout(workspace_root=...)` and reads its derived attributes.
   - **(c2)** Add a runtime assertion inside each helper (`assert "framework" not in path.relative_to(workspace_root).parts[:1]`) without a schema layer.
   **Recommendation: (c1).** The Pydantic-schema layer matches the dispatch's recommended pattern + amendment #43's "structural-guard via schema" precedent (workspace-sync's `FRAMEWORK_FLOOR` Pydantic model). The validator runs once at construction; subsequent path reads are cheap attribute access. A test asserts the validator fires when a malformed root or a hypothetical mis-path is constructed.

4. **D.2-build.D — pos-amend's per-amendment manifest path.** pos-amend has its own `objective_tracker.sqlite` constants in `framework/tools/heavy-b-migrate/` and `framework/tools/pos-amend/src/pos_amend/tracker_registration.py`. These reference `<repo_root>/objective_tracker.sqlite` — but `<repo_root>` for pos-amend means the **canonical pos-v2 repo** (where pos-amend operates), NOT a derived workspace. Post-D.2, the canonical pos-v2 repo's `objective_tracker.sqlite` lives at the canonical-repo root, not under `workspace/` (canonical pos-v2 has no `workspace/` — it IS the framework). **Recommendation: leave pos-amend / heavy-b-migrate alone.** Their `<repo_root>` semantics are correct; they don't read workspace-state, they read the canonical repo's own tracker DB. (Verified via grep — the constants are only referenced from canonical-repo-rooted code paths.)

5. **D.2-build.E — `.gitignore` shape.** The existing root `.gitignore` lists `.pos/` (top-level) and `.mcp.json` (per amendments #36, #44, #47). Post-D.2 the workspace-state lives under `workspace/<...>`. Two shapes:
   - **(e1)** Add a `<workspace>/.gitignore` (workspace-root, scaffolded by workspace-bootstrap) that declares `framework/` as the only tracked subtree. The old `.pos/` / `.mcp.json` lines stay in canonical's `.gitignore` (canonical pos-v2 still has them at canonical root for its own dev-state).
   - **(e2)** Move the gitignore lines to workspace-bootstrap's scaffold so derived workspaces get a tailored `.gitignore` at scaffold time.
   **Recommendation: (e1).** Canonical pos-v2's `.gitignore` is unchanged (pos-amend / heavy-b-migrate still use `.pos/` at canonical root for amendment-window state). Derived workspaces get a workspace-bootstrap-scaffolded `<workspace>/.gitignore` declaring `framework/` as the only tracked subtree. Trade-off: derived workspaces' `.gitignore` is a new scaffolded artefact (one more file in `_SCAFFOLD_FILES`).

6. **D.2-build.F — pre-D.2 workspace cleanup.** A fresh-clone first-run scaffold post-D.2 will write to `workspace/.pos/`, `workspace/personas/`, etc. But pos3 (and any workspace already first-run pre-D.2) has its workspace-state at `<workspace>/.pos/` etc. Per HC#5, **D.2 does NOT auto-migrate pos3.** A future amendment ships the migration script. For the AC.D.2.4 outline in plan §4 (originally "migration script in self-upgrade/ or workspace-bootstrap/"), **recommendation: defer migration script to a follow-up D-amendment (e.g. D.2.5).** Drop AC.D.2.4 (migration script) and AC.D.2.5 (pos3 real-apply) from D.2's amendment scope; replace with AC.D.2.4 (HC#6 structural guard) and AC.D.2.5 (workspace-paths helper centralization). The wider-fence ruling already restructured the amendment's shape; the migration script can land cleanly once D.2 establishes the layout.

7. **D.2-build.G — workspace-sync's `<workspace>/.pos/sync/`, `<workspace>/.pos/sync-protected.yaml`, `<workspace>/.pos/sync-config.yaml` paths.** All read by workspace-sync; all move to `workspace/.pos/sync/` etc. **Recommendation: move them.** The dispatch's wider-fence ruling explicitly includes all of workspace-sync. workspace-sync's `state.py`, `staging.py`, `merge_helper.py`, `ancestor_detection.py`, `sync_config.py`, `sync_protected.py` all get the cutover. (D.3 retires the bulk of workspace-sync; D.2 is the lockstep path-correctness window during the transition.)

8. **D.2-build.H — self-upgrade's `<workspace>/.pos/upgrade/...` paths.** self-upgrade's `state.py`, `clause_checks.py`, and its own `sync_protected.py` (which D.1.5 already noted as a duplicate of workspace-sync's) read these. **Recommendation: cut over.** Even though D.3 retires self-upgrade's runtime in favor of git-merge, D.2 still needs path-correctness during the transition (per dispatch).

9. **D.2-build.I — Speedup (b) "skip pre-seal full-suite if smoke tests on the touched components pass."** Touched components = workspace-bootstrap, hands-off-lifecycle, primary-persona, workspace-sync, self-upgrade, tools/loam-mode (6 components). Pre-seal smoke = pytest each component's tests + the new path-helper tests. **Recommendation: apply (b).** Full-repo pytest is the seal-time `--scoped-sweep` job.

---

## §1. AC refinement (replaces plan §4 D.2 outline under the wider fence)

The plan §4 outline is REPLACED for D.2 with the following ACs:

- **AC.D.2.1 — workspace-bootstrap scaffolds workspace state under `<workspace>/workspace/`.** A fresh-clone first-run produces `<workspace>/workspace/.pos/`, `<workspace>/workspace/personas/`, `<workspace>/workspace/.mcp.json`, `<workspace>/workspace/objective_tracker.sqlite`, `<workspace>/workspace/orchestrator.{out,err}.log`, `<workspace>/workspace/memory-write-worker.{out,err}.log`, `<workspace>/workspace/data/<sub>/<sqlite>` for every adapter that uses `host.workspace_root / "data"`. Pre-D.2 paths (`<workspace>/.pos/`, `<workspace>/personas/`, etc.) are NOT created. **Verification.** `framework/workspace-bootstrap/tests/test_d2_workspace_state_scaffold.py` (new) runs the scaffold against a fixture fresh-clone workspace and asserts every workspace-state path lives at `<fixture-ws>/workspace/<...>`. Pre-D.2 pathnames asserted absent. **HC#4 binding — byte-content match for `<fixture-ws>/workspace/.pos/memory-worker.yaml`, `.pos/ollama-prewarm-recommended.txt`, `.pos/sync-protected.yaml`, `.mcp.json`, `personas/primary/contract.yaml` against expected default content (SHA-256 + plain-text byte-for-byte where appropriate).**

- **AC.D.2.2 — `<workspace>/.claude/` location preserved at workspace root (D-Q.A4 lock).** Per Claude Code's expectation, `.claude/settings.json` lives at `<workspace>/.claude/`, NOT under `<workspace>/workspace/.claude/`. workspace-bootstrap scaffolds `.claude/settings.json` and `.claude/agents/` at workspace root. **Verification.** The scaffold test asserts `<fixture-ws>/.claude/settings.json` and `<fixture-ws>/.claude/agents/` (not under `workspace/`).

- **AC.D.2.3 — Plist EnvironmentVariables reference new paths.** Orchestrator + memory-graphiti + memory-write-worker plists' WorkingDirectory / StandardOutPath / StandardErrorPath reference `<workspace>/workspace/orchestrator.out.log` etc. (not `<workspace>/orchestrator.out.log`). The orchestrator's `WorkingDirectory` becomes `<workspace>/workspace/` (so cwd-relative writes land under workspace-state). The memory-graphiti template's `{workspace}/framework/memory-system/...` references stay (framework path, unchanged by D.2). **Verification.** `framework/workspace-bootstrap/tests/test_D5_plist_path_emission.py` extends to assert the new log-path locations + WorkingDirectory.

- **AC.D.2.4 — HC#6 structural guard fires.** A `WorkspaceLayout` Pydantic model in `workspace_paths.py` raises `ValidationError` (or a structured subclass) when constructed with a workspace_root whose computed workspace-state directory would collide with a `framework/` segment. A test asserts the refusal. **Verification.** `framework/workspace-bootstrap/tests/test_d2_workspace_layout_refuses_framework_state.py` (new) asserts a `WorkspaceLayout` constructed with hypothetical bad input (e.g. workspace_state_dir explicitly tampered to `framework/`) raises. The natural construction path produces correct paths.

- **AC.D.2.5 — Path-helper centralisation (every framework reader of workspace-state uses `workspace_paths` constants/functions).** Every `workspace_root / ".pos" / X`, `workspace_root / "personas"`, `host.workspace_root / "data" / X`, etc. occurrence in framework code (excluding test fixtures) imports + invokes the helper. **Verification.** `framework/workspace-bootstrap/tests/test_d2_no_inline_workspace_state_paths.py` (new) greps the framework source tree (excluding tests/, the helper itself, and `workspace_paths.py` consumers' allowed import lines) for inline `workspace_root / ".pos"` etc. patterns and asserts zero matches. Per the dispatch's HC#4 binding, this is the structural enforcement that the cutover landed everywhere.

- **AC.D.2.S — Seal-diff invariant.** Diff between BASELINE and SEAL_COMMIT for the multi-component manifest (workspace-bootstrap, hands-off-lifecycle, primary-persona, workspace-sync, self-upgrade, loam-mode, plus universal admissions) is confined to (a) those components' source/tests (path edits + new files), (b) per-component seal-test BASELINE bumps + SEAL_COMMIT sidecar updates, (c) universal admissions (`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-in-pos.md`, etc.).

---

## §2. Behaviour-count check (ODD §3.3 forward)

| AC | Behaviour |
|----|-----------|
| AC.D.2.1 | Fresh-scaffold writes workspace-state under `workspace/` |
| AC.D.2.2 | `.claude/` at workspace root preserved |
| AC.D.2.3 | Plist paths updated |
| AC.D.2.4 | HC#6 structural guard via WorkspaceLayout schema |
| AC.D.2.5 | Path-helper centralisation enforced structurally |
| AC.D.2.S | Seal-diff invariant |

Forward check passes. Reverse check (every code edit / branch / test → backing AC) lives in §5 below.

---

## §3. Per-component edit list (the substantive surface)

### `framework/workspace-bootstrap/`

**New file:** `src/workspace_bootstrap/workspace_paths.py`
- `WORKSPACE_STATE_SUBDIR = "workspace"` constant.
- `WorkspaceLayout` Pydantic model with `workspace_root: Path` field + computed-properties for every workspace-state path.
- Top-level helper functions (thin wrappers over `WorkspaceLayout`) for ergonomic use: `workspace_state_dir(ws)`, `pos_subdir(ws)`, `personas_dir(ws)`, `data_subdir(ws)`, `mcp_json_path(ws)`, `tracker_db_path(ws)`, `scratch_dir(ws)`, `orchestrator_log_paths(ws)`, `memory_worker_log_paths(ws)`, `claude_dir(ws)` (returns `<ws>/.claude/` — outside workspace_state per D-Q.A4).
- Validator: refuses construction when `workspace_root` is itself inside a path segment named `framework` (defence against accidental framework-rooted construction).

**Edits:**
- `src/workspace_bootstrap/adapters/first_run_scaffold.py`:
  - `WORKSPACE_POS_DIR = ".pos"` → import from `workspace_paths` (or replace with helper invocation).
  - `_write_amendment_j_workspace_files`: `Path(workspace_root) / WORKSPACE_POS_DIR` → `pos_subdir(workspace_root)`.
  - Plist templates' `{workspace}/orchestrator.out.log` → `{workspace}/workspace/orchestrator.out.log` (and similarly for `.err.log`, memory-write-worker log paths). The orchestrator + memory-write-worker plist `WorkingDirectory` → `{workspace}/workspace`.
  - `_install_persona_directory`'s `personas_dir = workspace_root / "personas"` → `personas_dir(workspace_root)`.
  - `_SCAFFOLD_FILES` write loop already targets `pos_root` (= `~/.pos/` host-config); unchanged.
  - **New:** scaffold writes `<workspace>/workspace/.gitignore` (declares the workspace-state directory contents are not tracked) and `<workspace>/.gitignore` if not present (declares `framework/` as the only tracked subtree). Builder's choice on the exact gitignore body; minimal contents per D.2-build.E (e1).
- `src/workspace_bootstrap/adapters/observability_aggregator.py`: `host.workspace_root / "data" / "aggregator" / "spans.jsonl"` → `data_subdir(host.workspace_root) / "aggregator" / "spans.jsonl"`.
- `src/workspace_bootstrap/adapters/cost_governance.py`, `safety_layer.py`, `self_correction.py`, `reversibility_primitive.py`: same pattern (`host.workspace_root / "data"` → `data_subdir(host.workspace_root)`).
- `src/workspace_bootstrap/adapters/primary_persona.py`: `host.workspace_root / ".pos"` → `pos_subdir(host.workspace_root)`.
- `src/workspace_bootstrap/adapters/mcp_json_writer.py`: `workspace_root / MCP_JSON_FILENAME` → `mcp_json_path(workspace_root)`.
- `src/workspace_bootstrap/adapters/tracker_seed.py`: `tracker_db_path_for(workspace_root)` already returns `<ws>/objective_tracker.sqlite`. Update to return `<ws>/workspace/objective_tracker.sqlite` via `workspace_paths.tracker_db_path`. **Note:** `tracker_seed.py` is shared between workspace-bootstrap (this) and `hands-off-lifecycle/hooks/first_run_state.py`'s `tracker_db_path_for` — verify the helpers agree (D.2-build.B: hooks duplicate constants per minimum-import contract).

**Test edits + new:**
- `tests/test_first_run_scaffold.py`, `tests/test_AC36_*`: update fixtures to assert `<ws>/workspace/personas/...` etc.
- `tests/test_AC29_scaffold_memory_port.py`, `tests/test_AC_J_*`: update workspace-state path assertions.
- `tests/test_D5_plist_path_emission.py`: update plist content assertions.
- **New:** `tests/test_d2_workspace_state_scaffold.py` (AC.D.2.1).
- **New:** `tests/test_d2_workspace_layout_refuses_framework_state.py` (AC.D.2.4).
- **New:** `tests/test_d2_no_inline_workspace_state_paths.py` (AC.D.2.5).
- **New:** `tests/test_d2_workspace_paths_helper.py` (helper-unit tests).

### `framework/hands-off-lifecycle/`

**Edits:**
- `hooks/first_run_state.py`: `state_path()` returns `Path(workspace_root) / "workspace" / ".pos" / STATE_FILE`. Constants pinned with comment pointing at canonical `workspace_paths.py`. `tracker_db_path_for` returns `Path(workspace_root) / "workspace" / TRACKER_DB_FILENAME`.
- `hooks/active_scope_sentinel.py`: `SENTINEL_DIR = ".pos"` → either keep as-is + change construction to prefix with `workspace/`, or rename to `SENTINEL_DIR = "workspace/.pos"`. **Recommendation:** introduce `SENTINEL_PARENT = "workspace"` and join. (Method shape — builder's call within outcome.)
- `hooks/corpus_load_sentinel.py`: same pattern.
- `hooks/first_run_dispatch.py`, `hooks/first_run_helper.py`, `hooks/first_run_scaffold_runner.py`, `hooks/statusline.py`: update workspace-state path constructions wherever they read `<workspace>/.pos/...`. Note the `~/.pos/` references (host-global config) are UNCHANGED — those are NOT workspace-state.
- `hooks/agent_file_authoring.py`: `Path(workspace_root) / ".claude" / "agents" / ...` — UNCHANGED (`.claude/` at workspace root per D-Q.A4).

**Test edits:**
- `tests/test_AC_SE_*`, `tests/test_first_run.py`, `tests/test_workspace_identity_routing.py`, `tests/test_AC29_health_workspace_probe.py`, etc. — fixture path updates.
- `tests/test_AC_SE_8_pos_directory_gitignored.py`: assertion changes (pre-D.2 asserts root `.gitignore` lists `.pos/`; post-D.2 the workspace-side `<workspace>/.gitignore` declares `framework/` as only-tracked, and the canonical's root `.gitignore` keeps `.pos/` for canonical-repo dev state). **Note for builder:** the AC.SE.8 test runs against `REPO_ROOT/.gitignore` — for canonical pos-v2 that's still relevant because canonical has `.pos/` for its own per-amendment-window state. The test stays; method shape unchanged. (If AC.SE.8 turns out to be loose under D.2's wider semantics, halt-and-surface — possible loose-AC tightening.)

### `framework/primary-persona/`

**Edits:**
- `src/session_start_gate.py`: `workspace_root / ".pos" / "memory-port"` → `pos_subdir(workspace_root) / "memory-port"`. Same for `orchestrator.sock`, `cost-headroom.json`, `first-run.state`.
- `src/dispatch_wrapper.py`: `workspace_root / ".pos" / "orchestrator.sock"` → `pos_subdir(workspace_root) / "orchestrator.sock"`. Same for `ambient-objective-id`, `dispatch-wrapper.log`.
- `src/loader.py`: `self.workspace_root / "personas"` → `personas_dir(self.workspace_root)`.
- `src/authoring.py`: `self.workspace_root / "personas"` → `personas_dir(self.workspace_root)`.
- `src/onboarding.py`: `workspace_root / ".claude" / "agents"` UNCHANGED. `Path(workspace_root) / "personas"` → `personas_dir(workspace_root)`.
- `src/introduction.py`: `Path(self.workspace_root) / ".pos" / "intro_queue"` → `pos_subdir(...) / "intro_queue"`. `Path(self.workspace_root) / "personas" / handle` → `personas_dir(...) / handle`.
- `src/memory_write_worker.py`: `Path(workspace_root) / ".pos" / "memory-writes.log"` → `pos_subdir(...) / "memory-writes.log"`.
- `src/stop_emitter.py`: `Path(workspace_root) / ".pos" / "last-turn-id"`, `Path(workspace_root) / ".pos" / "memory-writes.log"` → `pos_subdir(...)`.
- `src/tracker_context.py`: tracker DB path → `tracker_db_path(workspace_root)` (the workspace_paths helper).

**Test edits:**
- `tests/test_AC_M_*`, `tests/test_AC_SE_*`, etc. — fixture path updates.

### `framework/workspace-sync/`

**Edits:**
- `src/workspace_sync/sync_protected.py`: `workspace_root / ".pos" / "sync-protected.yaml"` → `pos_subdir(...) / "sync-protected.yaml"`. The `FRAMEWORK_FLOOR` patterns `(".pos/...", FileClass.A)` are workspace-sync's own internal config — they refer to file-class patterns inside the sync window, not absolute workspace-root paths. **Note for builder:** under D.3, the entire workspace-sync pipeline retires; for D.2 we just keep the FRAMEWORK_FLOOR patterns matching whatever pos-sync currently expects. Verify — if α-hotfix-2's resolution depends on these patterns matching workspace-state paths, halt-and-surface.
- `src/workspace_sync/sync_config.py`: `workspace_root / ".pos" / "sync-config.yaml"` → `pos_subdir(...)`.
- `src/workspace_sync/state.py`: `Path(workspace_root) / ".pos" / "sync" / ...` → `pos_subdir(...) / "sync" / ...`.
- `src/workspace_sync/staging.py`: same.
- `src/workspace_sync/merge_helper.py`: same.
- `src/workspace_sync/ancestor_detection.py`: same.
- `src/workspace_sync/cli.py`: docstrings + error-message references to `<workspace>/.pos/sync-config.yaml` etc. update to `<workspace>/workspace/.pos/sync-config.yaml`.

**Test edits:**
- `tests/test_*` — fixture path updates.

### `framework/self-upgrade/`

**Edits:**
- `src/self_upgrade/state.py`: `Path(workspace_root) / ".pos" / "upgrade" / ...` → `pos_subdir(...) / "upgrade" / ...`.
- `src/self_upgrade/sync_protected.py`: same as workspace-sync's sync_protected.py (file is a duplicate — D.1.5 noted this; D.3 retires it).
- `src/clause_checks.py` (if it reads workspace-state paths — verify; it may only read upgrade-config which is `~/.pos/`).

**Test edits:**
- `tests/test_*` — fixture path updates.

### `framework/tools/loam-mode/`

**Edits:**
- `src/loam_mode/session_start.py`: `Path(workspace_root) / "personas"` → `personas_dir(workspace_root)`.

**Test edits:**
- `tests/test_*` — fixture path updates.

---

## §4. New scaffolded artefact: `<workspace>/.gitignore` and `<workspace>/workspace/.gitignore`

Builder writes a minimal `<workspace>/.gitignore` template (scaffolded by workspace-bootstrap):

```
# Auto-scaffolded by pos-v2 workspace-bootstrap (D-migration D.2).
# `framework/` is the only git-tracked subtree; everything else is
# workspace-state and gitignored.
*
!.gitignore
!framework
!framework/**
!.claude
!.claude/**
```

(Method shape — builder's call. The structural promise is that workspace-state never lands under `framework/`. The exact pattern set is the builder's outcome bound.)

---

## §5. Reverse traceability check (every edit → backing AC)

| Edit | Backing AC |
|------|------------|
| `workspace_paths.py` (new module) | AC.D.2.5 (centralisation) + AC.D.2.4 (HC#6 guard via `WorkspaceLayout`) |
| Scaffold writer's plist + WORKSPACE_POS_DIR + persona-dir + scaffold-files-rel-paths edits | AC.D.2.1 (fresh-scaffold lands under `workspace/`) + AC.D.2.3 (plists) |
| `<workspace>/.gitignore` + `<workspace>/workspace/.gitignore` scaffolded | AC.D.2.1 (fresh-scaffold artefacts) + HC#6 (gitignore #2 in plan §6) |
| `.claude/` at workspace root unchanged | AC.D.2.2 (D-Q.A4 lock) |
| 5 adapter `data/`-path edits (observability, cost, safety, reversibility, self_correction) | AC.D.2.1 (data subdir lands under `workspace/`) |
| `primary_persona.py` adapter `.pos`-path edit | AC.D.2.1 (workspace-bootstrap-side reader) |
| `mcp_json_writer.py` `.mcp.json`-path edit | AC.D.2.1 (`.mcp.json` lands under `workspace/`) |
| `tracker_seed.py` tracker-db-path edit | AC.D.2.1 (objective_tracker lands under `workspace/`) |
| Hands-off-lifecycle hooks state-path / sentinel-dir / first-run-state edits | AC.D.2.1 (hook readers) |
| primary-persona session_start_gate / dispatch_wrapper / loader / authoring / onboarding / introduction / memory_write_worker / stop_emitter / tracker_context edits | AC.D.2.1 (every primary-persona reader) |
| workspace-sync state / staging / merge_helper / ancestor_detection / sync_config / sync_protected / cli edits | AC.D.2.1 (every workspace-sync reader; pre-D.3 path-correctness window) |
| self-upgrade state / sync_protected edits | AC.D.2.1 (self-upgrade readers; pre-D.3 path-correctness window) |
| loam-mode session_start.py edit | AC.D.2.1 (loam-mode persona-dir reader) |
| `test_d2_workspace_state_scaffold.py` (new) | Verifies AC.D.2.1 |
| `test_d2_workspace_layout_refuses_framework_state.py` (new) | Verifies AC.D.2.4 |
| `test_d2_no_inline_workspace_state_paths.py` (new) | Verifies AC.D.2.5 |
| `test_d2_workspace_paths_helper.py` (new) | Unit-test for the helper |
| Updated `test_D5_plist_path_emission.py` | Verifies AC.D.2.3 |
| All other test fixture path updates | Mechanical fixture updates per ODD §3.4 (not behaviour edits — they preserve existing AC verification under the new path layout) |
| Per-component seal-test BASELINE + SEAL_COMMIT bumps | AC.D.2.S |

Reverse check passes — every edit traces to an AC.

---

## §6. Halt triggers for the build (per dispatch §8 + plan §10)

1. **A reader the surface report didn't catalog turns up.** Halt + adjust fence + builder-plan.
2. **HC#6's structural guard requires touching code outside the now-widened fence.** Halt.
3. **pos-amend's seal step fails on the wider component list.** Halt.
4. **Wall-time exceeds 6h.** Halt.
5. **Pre-existing test fails post-cutover other than mechanical-path-update fails.** Halt.
6. **AC.SE.8 (root .gitignore) test fails post-cutover.** Halt — possibly loose AC requiring tightening per `feedback_loose_AC_text_fix_AC_not_implementation`.

---

## §7. Pos-amend manifest binding

Per the manifest at `docs/rebuild/plans/d-migration-2.manifest.yaml` — components are: workspace-bootstrap, hands-off-lifecycle (frozen_baseline=true per amendment #23 H19 rule), primary-persona, workspace-sync, self-upgrade, plus the loam-mode tool. Note: `framework/tools/loam-mode/` is not a sealed component (no `tests/SEAL_COMMIT` sidecar pre-D.2); admitted via `framework/tools/` universal-paths prefix per D.1's precedent.

Plan-doc admitted via `docs/rebuild/plans/` prefix.

---

## §8. Build sequence

1. Author this builder-plan + manifest. (DONE on commit of these two files.)
2. Create `workspace_paths.py` helper module + its tests.
3. Update workspace-bootstrap scaffold (writer + adapters + plist).
4. Update primary-persona readers.
5. Update workspace-sync readers.
6. Update self-upgrade readers.
7. Update hands-off-lifecycle hooks.
8. Update loam-mode reader.
9. Update existing tests' fixtures.
10. Add new tests (AC.D.2.1, .4, .5, helper).
11. Run touched-component pytest sweep (speedup (b)).
12. `pos-amend apply --dry-run` against the manifest. Green prerequisite.
13. Amendment commit (single feat commit per `feedback_no_amend_in_agent_dispatches`).
14. `pos-amend apply <plan>` — bumps BASELINE + SEAL_COMMIT for each touched component (D.1.5's rename-aware logic should classify all components as substantively-changed, since path-string edits ARE substantive under strict-R100).
15. `pos-amend seal <manifest> --plan-doc <abs> --scoped-sweep` — full per-component seal-diff sweep on the touched components.
16. Backfill plan §14 (method-decision register) + §15 (verdict).

---

## §9. Speedups applied

- **(a) Narrow seal-test rerun to D.2's manifest components** (~6 components — workspace-bootstrap, hands-off-lifecycle, primary-persona, workspace-sync, self-upgrade, plus loam-mode admitted via universal-paths prefix). `pos-amend seal --scoped-sweep` invokes per-component seal-diff tests; the cross-component sweep at seal-time validates fence integrity.
- **(b) Skip pre-seal full-suite if smoke tests on the touched components pass.** Touched-component pytest is the gate; full pytest is the seal-time `--scoped-sweep` job.
- **(c) Inline methodology snippets in commit prose.** The amendment commit message references the wider-fence ruling + D-Q.A4 lock + D.2-build.A/B/C/D/E inline.

Estimated wall-time: **4-6h** (per the halt-surface report's option (a) projection).
