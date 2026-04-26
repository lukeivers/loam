# Structural enforcement — A1: substrate — Builder plan

**Status:** authored 2026-04-26 by build agent. **Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`. **Plan-doc that governs:** `docs/rebuild/plans/structural-enforcement-a1-substrate.md` (LOCKED). **Research:** `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (LOCKED).

This builder plan records the method choices that satisfy AC.SE.1 – AC.SE.S without deviating from the plan-doc's outcomes or D-decisions.

---

## 1. Pre-flight verification

- `git status` clean (only .mcp.json + personas/ pre-session artefacts; tree is on `pos-v2`).
- Pre-amendment narrow-scope test runs:
  - `objective-tracker/`: 132 passed.
  - `hands-off-lifecycle/`: 163 passed, 1 failed (`test_AC37_6_sentinel_prose_flows_through_renderer`). Pre-existing on HEAD; the test substitutes a string ("Describe, in one sentence, what this persona is the sole contact for.") that does not exist in the current `primary-persona/templates/persona-template/contract.yaml`, so the sentinel never lands. Not introduced by A1, not in A1's fence, not §2.5-shaped (the test backs AC37.6 — a real objective). Surfaced in final report; A1 leaves untouched.
- Halt-trigger sweep:
  - Halt 1 (`<workspace>/.pos/` gitignore): existing root `.gitignore` does NOT name `.pos/`. AC.SE.8 lands a top-level entry; admitted via universal-paths block (see §6 below).
  - Halt 2 (`objective-tracker` schema-evolution): existing `_SCHEMA` already uses `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN` (amendment #38 precedent). New `objective_manifest` table follows the same `CREATE TABLE IF NOT EXISTS` shape. No public-API contract change required.
  - Halt 3 (`merge_session_start` registry): the `extra_inner_hooks` parameter on `build_first_run_stanza` / `build_supervisor_stanza` is the registered surface (#45). New corpus-load inner hook composes through that parameter; no contract change.
  - Halt 4 (`loam-mode` synchronous): `loam_mode.session_start.read_dev_intent_safe` + `compute_session_mode` are pure synchronous Python functions over a YAML file read. No async dependency; sub-100ms. Acceptable.
  - Halt 5 (§2.5 in surrounding code): no §2.5 violation surfaced during read-through of the touched modules.
  - Halt 6 (outcome-shaped AC): all nine ACs are outcome-shaped in the plan-doc. No method prescription required.
  - Halt 7 (A2/A3/A4 substrate change): A1's substrate is sufficient for the four-amendment programme as outlined in the research §6 + plan-doc §7.

---

## 2. Method-level decisions (D-build)

Per ODD §1.1 method is the builder's call. The choices below are recorded for audit; none deviate from the plan-doc's D-decisions.

### D-build.1 — Manifest table inside objective-tracker SQLite store

Add table `objective_manifest` to `objective-tracker/src/store.py::_SCHEMA`:

```sql
CREATE TABLE IF NOT EXISTS objective_manifest (
    component         TEXT NOT NULL,
    ac_id             TEXT NOT NULL,
    source_path_glob  TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    PRIMARY KEY (component, ac_id, source_path_glob)
);
CREATE INDEX IF NOT EXISTS idx_obj_manifest_component ON objective_manifest(component);
CREATE INDEX IF NOT EXISTS idx_obj_manifest_ac        ON objective_manifest(ac_id);
```

`PRIMARY KEY (component, ac_id, source_path_glob)` enforces uniqueness per AC.SE.6 (the implicit unique-on-tuple). Forward-compat per AC.SE.6: future amendments may `ALTER TABLE ... ADD COLUMN` (the established #38 pattern). Per Q-adj.1: the table sits next to existing tables; no schema-version bump (the existing schema is mutable).

### D-build.2 — Manifest API surface on `EventStore`

New methods on `EventStore` (the SQLite-store class in `objective-tracker/src/store.py`):

- `insert_manifest_row(*, component: str, ac_id: str, source_path_glob: str) -> None` — validates non-empty + valid fnmatch pattern; inserts `(component, ac_id, source_path_glob, now_iso)`. Idempotent on duplicate (PRIMARY KEY conflict → INSERT OR IGNORE).
- `list_manifest_rows_for_component(component: str) -> list[dict]`
- `list_manifest_rows_for_ac(component: str, ac_id: str) -> list[dict]`
- `list_manifest_rows_matching_source_path(workspace_relative_path: str) -> list[dict]` — Python-side fnmatch over rows (no SQL GLOB usage; portable).

Refusal shape (AC.SE.7): structured `ManifestRowError` (new exception class in `objective-tracker/src/errors.py` namespace; the same module already exports `ObjectiveTrackerError` and friends).

Each top-level method exposed on `ObjectiveTracker` runtime as a thin wrapper for caller convenience:

- `register_source_binding(*, component, ac_id, source_path_glob) -> None`
- `manifest_rows_for_component(component) -> list[dict]`
- `manifest_rows_for_ac(component, ac_id) -> list[dict]`
- `manifest_rows_matching_source_path(path) -> list[dict]`

### D-build.3 — Active-scope sentinel: pure-library writer/reader, no new CLI

Plan §6 D-A1.2 leaves the home open. Per Q-adj.2 recommendation (extend `pos-amend`), the natural home is a small library module the active-scope sentinel writer can be invoked from. To minimise scope per AC.SE.2 / AC.SE.3 ("documented sentinel-writer surface" — library function or CLI subcommand, builder's call):

- New stdlib-only library module `hands-off-lifecycle/hooks/active_scope_sentinel.py`. Pure functions: `write_active_scope_sentinel(workspace_root, scope_id, plan_path, bindings, session_id) -> ActiveScopeWriteResult`, `read_active_scope_sentinel(workspace_root) -> ActiveScopeSentinel | None`. Atomic write via `.tmp` + `os.replace` mirroring `first_run_state.write_state` exactly.
- No CLI subcommand. The library is the surface. No edit to `tools/pos-amend/` or `tools/loam-mode/`. Future amendments (A2 builds the gate; A4 builds an active-scope writer wired to dispatches) can add a CLI veneer as needed.
- Sentinel JSON shape per AC.SE.2:

  ```json
  {
    "scope_id": "...",
    "plan_path": "docs/rebuild/plans/<slug>.md",
    "bindings": [{"component": "...", "ac_id": "..."}],
    "created_at": "ISO-8601 UTC",
    "session_id": "<id> | null"
  }
  ```

  Reader returns a typed dataclass `ActiveScopeSentinel` mirroring the JSON shape; on absent / malformed / unreadable, returns `None` (AC.SE.3).

This keeps the writer in `hands-off-lifecycle/hooks/` (sealed-component surface — backed by AC.SE.2 / AC.SE.3 in the seal-diff fence). No tools/ edit needed for A1; tools/-side wiring is A2's surface.

### D-build.4 — Corpus-load sentinel: SessionStart inner hook + helper module

- New stdlib-only library module `hands-off-lifecycle/hooks/corpus_load_sentinel.py`. Pure functions: `compute_corpus_paths_required(workspace_root, mode) -> list[str]`, `write_corpus_load_sentinel(workspace_root, session_id) -> CorpusLoadWriteResult`, `read_corpus_load_sentinel(workspace_root, session_id) -> CorpusLoadSentinel | None`. Atomic write via `.tmp` + `os.replace`.
- New CLI entry `hands-off-lifecycle/hooks/corpus_load_session_start.py` (CLI script invoked by Claude Code's SessionStart inner-hook composition). Reads stdin Claude Code SessionStart JSON envelope (pattern from `statusline.py`), extracts `workspace.project_dir` + `session_id`, calls `write_corpus_load_sentinel(workspace_root, session_id)`, prints empty stdout (no `additionalContext` surface change in A1 — Lens 1 noted "OPTIONALLY surface" — A1 stays library-only), exits 0 on every path (fail-soft).
- New stanza-builder + merge function additions in `hands-off-lifecycle/hooks/first_run_settings.py`:
  - Add the corpus-load CLI's command marker to `_POS_V2_COMMAND_MARKERS` so re-merge over a stanza we wrote does not back up the corpus-load inner hook as user-authored.
  - Add a helper `build_corpus_load_inner_hook(pos_v2_root)` returning the `{type, command, async, timeout: 5}` dict (matches loam-mode + persona inner-hook timeouts).
- Compose the corpus-load inner hook into both `build_first_run_stanza` and `build_supervisor_stanza` calls in `hands-off-lifecycle/hooks/first_run_helper.py`. Wire ordering: existing wiring composes loam-mode + persona inner hooks; corpus-load adds AFTER persona (last in chain — its sentinel is consumable but A1 ships no consumer, so ordering is not load-bearing).

### D-build.5 — Workspace-mode bit consumer surface

Per plan §6 D-A1.3: consumer-only via `loam-mode`'s existing surface. The mode-bit query inside the corpus-load sentinel writer is:

```python
from loam_mode.session_start import read_dev_intent_safe, compute_session_mode
intent = read_dev_intent_safe(workspace_root)
mode = compute_session_mode(intent)  # "dev" | "user"
```

This already exists; no edit to `loam-mode` source. Per AC.SE.1: the helper returns `"dev-mode" | "normal-use"`. Map: `"dev"` → `"dev-mode"`, `"user"` → `"normal-use"`. Done by a thin local helper in `corpus_load_sentinel.py::workspace_mode(workspace_root) -> str` to honour AC.SE.1's exact string contract without re-exporting loam-mode terms.

Note: the plan-doc names "dev-mode | normal-use" but loam-mode's existing terms are "dev" / "user". The plan-doc's intent is "the workspace-mode bit is queryable" — exact string contract is method. Builder choice: AC.SE.1 helper returns `"dev-mode" | "normal-use"` (the plan-doc's strings) and `corpus_paths_required` is computed in those terms; loam-mode internals stay as "dev"/"user".

### D-build.6 — Required-corpus computation honours mode

AC.SE.5: when mode = `"normal-use"`, `corpus_paths_required` = `loam_mode.selector.select_corpus(manifest, workspace_root, "user")`. When `"dev-mode"`, = `select_corpus(manifest, workspace_root, "dev")`. The manifest is loaded via `loam_mode.manifest.load_manifest(workspace_root / "docs/rebuild/dev-mode-manifest.yaml")` (A1 consumer path; loam-mode is dev-discipline so the import is fine for the dev-discipline workspace).

Fail-soft: if the manifest is missing or unreadable, `corpus_paths_required = []` and `state = "missing"`. The hook still writes a sentinel (per AC.SE.5 — "still writes a sentinel"); state field surfaces the degradation.

### D-build.7 — `<workspace>/.pos/` gitignore

Per AC.SE.8 + Q-adj.1 recommendation: top-level `.gitignore` entry. The repo's existing `.gitignore` is admitted to A1's seal-diff window via the universal-paths block precedent (amendment #44's sibling `.gitignore` admission per H19's `allowed` set already names `.gitignore`). Single addition:

```
# Workspace-local pos-v2 sentinel directory (first-run state, active-
# scope sentinel, session-state sentinels).
.pos/
```

### D-build.8 — Test layout (1:1 AC → test mapping per ODD §3.3)

Tests under `objective-tracker/tests/` (covers AC.SE.1, AC.SE.6, AC.SE.7) and `hands-off-lifecycle/tests/` (covers AC.SE.1 — workspace-mode helper, AC.SE.2, AC.SE.3, AC.SE.4, AC.SE.5, AC.SE.8, AC.SE.S). One test file per AC:

| AC | Test file |
|---|---|
| AC.SE.1 | `hands-off-lifecycle/tests/test_AC_SE_1_workspace_mode_bit.py` |
| AC.SE.2 | `hands-off-lifecycle/tests/test_AC_SE_2_active_scope_sentinel_write.py` |
| AC.SE.3 | `hands-off-lifecycle/tests/test_AC_SE_3_active_scope_sentinel_read.py` |
| AC.SE.4 | `hands-off-lifecycle/tests/test_AC_SE_4_corpus_load_sentinel_write.py` |
| AC.SE.5 | `hands-off-lifecycle/tests/test_AC_SE_5_corpus_load_mode_partition.py` |
| AC.SE.6 | `objective-tracker/tests/test_AC_SE_6_objective_manifest_table.py` |
| AC.SE.7 | `objective-tracker/tests/test_AC_SE_7_objective_manifest_refusal.py` |
| AC.SE.8 | `hands-off-lifecycle/tests/test_AC_SE_8_pos_directory_gitignored.py` |
| AC.SE.S | `hands-off-lifecycle/tests/test_AC_SE_S_seal_diff_window.py` + `objective-tracker/tests/test_AC_SE_S_seal_diff_window.py` |

### D-build.9 — Seal-diff invariant tests

Two seal-diff tests track the per-component contamination:

- `objective-tracker/tests/test_no_sealed_amendments.py` — existing test; BASELINE advances via `pos-amend apply` to the pre-amendment-tip SHA; seal-diff stays inside `objective-tracker/` + `docs/rebuild/plans/` + universal admissions.
- `hands-off-lifecycle/tests/test_cross_cutting.py::test_H19_diff_scope_covers_only_approved_surfaces` — H19 frozen-BASELINE check; admits new top-level surfaces. A1 introduces no new top-level bucket (objective-tracker, hands-off-lifecycle, tools, docs, .gitignore are all already admitted). No edit required to `allowed` set in this test.
- New per-amendment seal-diff invariant tests (per ODD §10.3 per-invariant BASELINE pattern):
  - `objective-tracker/tests/test_AC_SE_S_seal_diff_window.py` — pinned to the A1 baseline → A1 seal commit window; admitted prefixes = `objective-tracker/` + universal.
  - `hands-off-lifecycle/tests/test_AC_SE_S_seal_diff_window.py` — pinned to the A1 baseline → A1 seal commit window; admitted prefixes = `hands-off-lifecycle/` + `tools/loam-mode/` (none touched by A1, but reserved per the substrate's mode-bit consumption — actually A1 consumes loam-mode at runtime but does not edit it; admission tightened to `hands-off-lifecycle/` + universal only).

### D-build.10 — Sealed-component pyproject changes

`objective-tracker`'s public surface widens (new manifest API on the runtime). No bump to `[project].version` per #38's precedent (additive surface; semver discretion per `pyproject.toml`).

`hands-off-lifecycle` ships no Python package (per its README); new modules live under `hooks/` as siblings of `first_run_state.py`.

---

## 3. Files touched (audit per ODD §2.5 reverse direction)

Every file below maps back to AC.SE.1 – AC.SE.S.

### Inside fence — `objective-tracker/`

- `objective-tracker/src/store.py` — extend `_SCHEMA`; add manifest-table CRUD methods. (AC.SE.6, AC.SE.7)
- `objective-tracker/src/errors.py` — add `ManifestRowError`. (AC.SE.7)
- `objective-tracker/src/runtime.py` — add public wrapper methods on `ObjectiveTracker`. (AC.SE.6)
- `objective-tracker/src/__init__.py` — export `ManifestRowError`. (AC.SE.7)
- `objective-tracker/tests/test_AC_SE_6_objective_manifest_table.py` — new. (AC.SE.6)
- `objective-tracker/tests/test_AC_SE_7_objective_manifest_refusal.py` — new. (AC.SE.7)
- `objective-tracker/tests/test_AC_SE_S_seal_diff_window.py` — new. (AC.SE.S)
- `objective-tracker/tests/test_no_sealed_amendments.py` — BASELINE literal advanced by `pos-amend apply`. (AC.SE.S)
- `objective-tracker/tests/SEAL_COMMIT` — sidecar advanced by `pos-amend apply` then `pos-amend seal`. (AC.SE.S)
- `objective-tracker/seals/SEAL_COMMIT.<slug>` — narrative appended by `pos-amend seal`. (AC.SE.S)

### Inside fence — `hands-off-lifecycle/`

- `hands-off-lifecycle/hooks/active_scope_sentinel.py` — new. (AC.SE.2, AC.SE.3)
- `hands-off-lifecycle/hooks/corpus_load_sentinel.py` — new. (AC.SE.1, AC.SE.4, AC.SE.5)
- `hands-off-lifecycle/hooks/corpus_load_session_start.py` — new (CLI entry). (AC.SE.4)
- `hands-off-lifecycle/hooks/first_run_settings.py` — add corpus-load command marker + `build_corpus_load_inner_hook` helper. (AC.SE.4)
- `hands-off-lifecycle/hooks/first_run_helper.py` — wire corpus-load inner hook into `extra_inner_hooks` calls at both stanza-build sites. (AC.SE.4)
- `hands-off-lifecycle/tests/test_AC_SE_1_workspace_mode_bit.py` — new. (AC.SE.1)
- `hands-off-lifecycle/tests/test_AC_SE_2_active_scope_sentinel_write.py` — new. (AC.SE.2)
- `hands-off-lifecycle/tests/test_AC_SE_3_active_scope_sentinel_read.py` — new. (AC.SE.3)
- `hands-off-lifecycle/tests/test_AC_SE_4_corpus_load_sentinel_write.py` — new. (AC.SE.4)
- `hands-off-lifecycle/tests/test_AC_SE_5_corpus_load_mode_partition.py` — new. (AC.SE.5)
- `hands-off-lifecycle/tests/test_AC_SE_8_pos_directory_gitignored.py` — new. (AC.SE.8)
- `hands-off-lifecycle/tests/test_AC_SE_S_seal_diff_window.py` — new. (AC.SE.S)
- `hands-off-lifecycle/tests/test_cross_cutting.py` — H19 BASELINE is frozen; only edit if a new top-level bucket appears (none does — see §3.D-build.9). No expected edit.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — sidecar advanced by `pos-amend apply` then `pos-amend seal`. (AC.SE.S)
- `hands-off-lifecycle/seals/SEAL_COMMIT.<slug>` — narrative appended by `pos-amend seal`. (AC.SE.S)

### Outside fence — universal-paths admissions

- `.gitignore` — top-level entry for `.pos/` (admitted per H19 + amendment #44 precedent). (AC.SE.8)
- `docs/rebuild/plans/structural-enforcement-a1-substrate.builder-plan.md` — this file. (paper trail per FUTURE_IDEAS plan-before-code CDC)
- `docs/rebuild/plans/structural-enforcement-a1-substrate.manifest.yaml` — pos-amend manifest. (bookkeeping)

### Reverse-direction §2.5 audit

Every file lists the AC(s) it satisfies. No orphan branches. No defensive `try`/`except` for cases ACs don't name. No "might be useful later" code.

---

## 4. Implementation order

1. `objective-tracker` schema + API + tests (AC.SE.6, AC.SE.7) — leaf change; isolated from hands-off-lifecycle.
2. `hands-off-lifecycle` library modules (active-scope, corpus-load) + tests (AC.SE.1, AC.SE.2, AC.SE.3, AC.SE.4, AC.SE.5).
3. SessionStart inner-hook wiring (`first_run_settings.py` + `first_run_helper.py`) + CLI entry — composes the new hook into existing stanzas (AC.SE.4).
4. `.gitignore` + AC.SE.8 test.
5. Per-amendment seal-diff invariant tests (AC.SE.S).
6. New per-component `SEAL_COMMIT` sidecar + narrative — `pos-amend apply` → amendment commit → `pos-amend seal` → seal commit.

---

## 5. Manifest authoring

`docs/rebuild/plans/structural-enforcement-a1-substrate.manifest.yaml`:

- `schema_version: 1` (no objective-tracker registration in A1; the manifest table is ABOUT that registry, but A1 doesn't yet seed rows for itself — that's a self-reference best deferred to A2 when the gate exists).
- `baseline:` set to HEAD~1 of the amendment commit (per established #29-#47 pattern).
- `components:` `objective-tracker` (frozen_baseline: false) + `hands-off-lifecycle` (frozen_baseline: true; H19 is frozen at project-start).
- `universal_paths.prefixes:` `docs/rebuild/plans/`.
- `universal_paths.files:` `CLAUDE.md`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`, `docs/rebuild/FUTURE_IDEAS.md`, `.gitignore`.
- `narrative.target:` `hands-off-lifecycle/seals/SEAL_COMMIT.structural-enforcement-a1-substrate` (new sidecar — first time hands-off-lifecycle hosts an A1-class amendment narrative).
- `narrative.body:` describes A1's substrate.

Per-component manifest extras (extra_allowed_prefixes): none. The seal-diff invariant tests live INSIDE each component; the H19 admission set already covers the cross-component bucket.

---

## 6. Pos-amend bookkeeping flow

1. Author manifest at `docs/rebuild/plans/structural-enforcement-a1-substrate.manifest.yaml`.
2. Author all source edits + tests.
3. Commit as the amendment commit.
4. `pos-amend apply --dry-run` — must exit 0.
5. `pos-amend apply` — advance BASELINE literals (objective-tracker only — H/L is frozen) + widen seal-diff bindings + write SEAL_COMMIT sidecars at the amendment-commit SHA (empty-diff window).
6. Commit the apply edits.
7. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/structural-enforcement-a1-substrate.md <manifest>` — runs scoped sweep + creates seal commit + advances SEAL_COMMIT sidecars to the seal commit SHA + appends builder-plan §SHA backfill via the new-plan §14 mechanism.
8. Verify: `pos-amend apply --dry-run` exits 0 against post-seal HEAD.

Per amendment-dispatch speedups: post-seal seal-diff-only across the other 11 sealed components (no full test rerun).

---

## 7. Halt-and-surface log

- Pre-existing `test_AC37_6_sentinel_prose_flows_through_renderer` failure: NOT introduced by A1, NOT in A1's fence, NOT a §2.5 violation. Stale test against template that no longer contains the substituted placeholder. Surfaced in final report; A1 leaves untouched. Future amendment can repair the test or re-extend the AC.

---

*End of builder plan. Awaiting build execution.*
