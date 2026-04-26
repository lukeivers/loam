# self-upgrade BB-feat #54 follow-on bugfix — builder-plan

Builder-plan companion to `self-upgrade-bb-feat-bugfix.md`. Captures
D-build.x method choices and the ODD §2.5 reverse-direction trace.

**Status:** builder-plan (pre-build). 2026-04-26.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/

---

## D-build.1 — state.yaml schema and module location

**Choice.** New module `self-upgrade/src/self_upgrade/state.py` carrying:

- `UpgradeStatus` `str, Enum` — values: `success`, `failure`, `partial`.
- `StateRecord(BaseModel)` — fields:
  - `upgrade_tag: str`
  - `timestamp: str` (ISO-8601 UTC; produced via
    `datetime.now(timezone.utc).isoformat()` at write time)
  - `audit_path: str` — absolute path to the workspace-local
    audit YAML (so re-runs can auto-load it without re-deriving).
  - `total_conflicts: int`
  - `resolved_count: int`
  - `deferred_count: int`
  - `cumulative_tokens_used: int`
  - `status: UpgradeStatus`
  - `halt_reason: str | None = None` — populated for
    `failure` / `partial` to carry the resolver/budget surface.
- `state_yaml_path(workspace_root) -> Path` — returns
  `workspace_root / ".pos" / "upgrade" / "state.yaml"`.
- `load_state(workspace_root) -> StateRecord | None` — returns
  None if absent; raises on validation error.
- `save_state(record, workspace_root)` — writes YAML.

**Why a module rather than inline.** Pydantic schema needs round-trip
coverage; mirrors `sync_protected.py` / `merge_resolver.py` /
`conflict_report.py` shape. Reach-for default per
`odd-methodology.md` §5.3.

**Maps to AC.** AC.HFX.2 (state.yaml exists + round-trips +
schema-validated).

---

## D-build.2 — audit-path resolution

**Choice.** New helper `audit_yaml_path(workspace_root, tag) -> Path`
in `state.py` (kept with state because both belong to the same
`<workspace>/.pos/upgrade/` namespace). Returns
`workspace_root / ".pos" / "upgrade" / tag / "audit.yaml"`.

Legacy `--staging-dir` mode in `cli.py:cmd_upgrade` continues to
use `paths.conflicts_yaml(tag)` for its `report.has_pending()`
save site. Branch on `canonical_resolution is not None` to pick
the audit-write path.

**Maps to AC.** AC.HFX.3 (workspace-local audit path on canonical;
legacy unchanged).

---

## D-build.3 — write audit + state from inside `resolve_clause_h_inferred`

**Choice.** Extend the helper's `finally` block to write both the
audit YAML and the state YAML. The helper already takes
`workspace_root` and `report` (which carries `upgrade_tag`); both
writes have everything they need.

The audit-write uses `save_conflict_report` (already imported) but
to the new workspace-local path computed via `audit_yaml_path`.

The state-write uses `save_state` with:
- `status = "success"` if no exception raised + no PENDING entries.
- `status = "failure"` if `BudgetExhausted` or `ResolverFailure` raised.
- `status = "partial"` if no exception but some PENDING remain
  (e.g. binary files the helper deferred).

`halt_reason` carries the exception's str(...) on failure paths.

The writes happen in `finally` so they fire even when the helper
raises. `BudgetExhausted` and `ResolverFailure` exceptions propagate
after the writes complete.

**Why in the helper, not the CLI.** Two reasons:
1. The helper is the canonical "clause-(h) execution" surface.
   Putting both writes inside it means every caller (CLI + future
   composition) gets them automatically.
2. Test
   `test_halt_surface_state_yaml_not_implemented` calls the helper
   directly (not the CLI) — placing the writes in the helper makes
   the test flip naturally.

**Maps to AC.** AC.HFX.1 (audit on every clause-(h) execution,
in-helper); AC.HFX.2 (state.yaml on every clause-(h) execution).

---

## D-build.4 — CLI auto-discovery on re-invocation

**Choice.** In `cmd_upgrade`, after canonical resolution but before
the clause-(h) helper call, check for a prior state.yaml at
`state_yaml_path(live_root)`. If present + matches the current
`tag` + the prior `audit_path` exists, load the prior audit as the
starting `report`. This means:

- A second invocation against unchanged inputs sees PENDING
  conflicts pre-resolved (the helper skips them per the existing
  `if entry.resolution is not Resolution.PENDING: continue`
  branch).
- Resolver call-count stays at zero on the second run for any
  conflict already resolved in the first.

If state.yaml exists but for a different tag, it is left alone
(no cross-tag conflation); the new run starts fresh.

The auto-discovery only fires when `--conflicts-from` is NOT
passed (operator-supplied path takes precedence per existing
behaviour).

**Maps to AC.** AC.HFX.2 (re-run convergence; resolver call-count
= 0 on second run).

---

## D-build.5 — CLI legacy save sites

**Choice.** The three existing `save_conflict_report(report,
conflicts_yaml)` sites in `cmd_upgrade`:

1. `BudgetExhausted` handler (line 209) — clause-(h) error;
   helper's `finally` already wrote audit + state. CLI's save
   becomes redundant (helper covers it). Replace with a
   reference to the new audit path in stderr output.
2. `ResolverFailure` handler (line 224) — same as above.
3. `report.has_pending()` block (line 238) — fires for both
   legacy `--staging-dir` flow (pending detected by
   `detect_conflicts`, no clause-(h) ran) AND for canonical
   flow when clause-(h) deferred entries (binary files etc.).
   - Legacy: write to `paths.conflicts_yaml(tag)` (unchanged).
   - Canonical: write to workspace-local audit path; helper
     already wrote partial-status state.yaml.

For (1) and (2): the helper's finally writes audit. The CLI then
prints the audit path to stderr for the operator. No double-write.

For (3): branch on `canonical_resolution is not None` — pick the
right audit path.

**Maps to AC.** AC.HFX.3 (path resolution); AC.HFX.1 (write on
every path).

---

## D-build.6 — test edits

**Choice.** Edit `self-upgrade/tests/test_bb_feat_synthetic_validation.py`:

1. **`test_halt_surface_audit_not_written_on_clean_clause_h_pass`
   (line 725)** — flip from "asserts the bug" to "asserts spec'd
   behaviour". The test calls `resolve_clause_h_inferred` directly
   on a `tmp_path / "workspace"`. After the helper runs, assert:
   - `(workspace / ".pos" / "upgrade" / tag / "audit.yaml").exists()`
   - The audit round-trips and the resolved entry is intact.

2. **`test_halt_surface_state_yaml_not_implemented` (line 801)** —
   flip the negative assertion. After the helper runs, assert:
   - `state_path.exists()` (was `assert not state_path.exists()`)
   - `StateRecord.model_validate(yaml.safe_load(state_path.read_text()))`
     loads cleanly and reports `status: success`.

3. **`test_cli_canonical_pending_writes_audit_yaml` (line 206)** —
   currently uses `audit_path = paths.conflicts_yaml(tag)`. Change
   to:
   - `audit_path = prior / ".pos" / "upgrade" / tag / "audit.yaml"`
     (where `prior` is `live_root` for this test fixture's setup).

4. **`test_cli_canonical_without_merge_resolver_module_skips_clause_h`
   (line 681)** — same change: `audit_path = prior / ".pos" /
   "upgrade" / "pos-v2-v0.2.0" / "audit.yaml"`.

The other 7 CC tests are unchanged. The legacy
`test_cli_staging_dir_only_no_clause_h_path` (line 553) keeps
asserting `paths.conflicts_yaml(tag)` (legacy path unchanged).

Add `tests/test_state.py` with state-yaml round-trip coverage:

- `test_state_record_round_trip` — write + load, schema-validated
- `test_state_yaml_path_workspace_relative` — path resolution
- `test_load_state_returns_none_when_absent`

**Maps to AC.** AC.HFX.1 (test 725 + 206 + 681); AC.HFX.2 (test
801 + new state tests); AC.HFX.3 (tests 206 + 681).

---

## ODD §2.5 reverse trace (one row per code path → AC)

| Module | Function / branch | AC |
|---|---|---|
| `state.py` | `UpgradeStatus` enum + `StateRecord` model + validator | AC.HFX.2 |
| `state.py` | `state_yaml_path(workspace_root)` | AC.HFX.2 |
| `state.py` | `audit_yaml_path(workspace_root, tag)` | AC.HFX.3 |
| `state.py` | `load_state` / `save_state` | AC.HFX.2 |
| `clause_checks.py` | `resolve_clause_h_inferred` finally → audit-write | AC.HFX.1 + AC.HFX.3 |
| `clause_checks.py` | `resolve_clause_h_inferred` finally → state-write | AC.HFX.2 |
| `clause_checks.py` | `_status_from_outcome` helper | AC.HFX.2 |
| `cli.py` | `cmd_upgrade` auto-discovery prior-state branch | AC.HFX.2 |
| `cli.py` | `cmd_upgrade` audit-path resolution (canonical vs legacy) | AC.HFX.3 |
| `cli.py` | BudgetExhausted handler stderr path-print | AC.HFX.1 + AC.HFX.3 |
| `cli.py` | ResolverFailure handler stderr path-print | AC.HFX.1 + AC.HFX.3 |
| `cli.py` | has_pending handler audit-write (canonical branch) | AC.HFX.3 |

Every new code path lands under an AC.HFX.* trace.

---

## Test breakdown (post-build)

(populated post-build)

---

## Backward-compat verification

(populated post-build)

---

## Commit SHAs

(populated by `pos-amend seal --plan-doc <this-file> ...`)
