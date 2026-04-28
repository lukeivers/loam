# Structural enforcement — A2 objective-binding gate — Builder plan

**Authored:** 2026-04-28 (build-time).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.md` (governs).
**Research:** `docs/rebuild/plans/research/structural-enforcement-a2-objective-binding-gate-research.md`.
**Manifest:** `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.manifest.yaml` (BASELINE = `3582054`).

This builder plan records the method-level decisions taken during A2's
build. The parent plan is contract; method decisions live here.

---

## 1. Files touched (the diff window)

### New files (under `framework/hands-off-lifecycle/`)

- `hooks/objective_binding_gate.py` — the PreToolUse gate script.
- `tests/test_AC_OBG_1_deny_missing_sentinel.py`
- `tests/test_AC_OBG_2_deny_no_manifest_row.py`
- `tests/test_AC_OBG_3_deny_no_glob_match.py`
- `tests/test_AC_OBG_4_allow_glob_matches.py`
- `tests/test_AC_OBG_5_allow_carve_outs.py`
- `tests/test_AC_OBG_6_normal_use_no_op.py`
- `tests/test_AC_OBG_7_audit_log.py`
- `tests/test_AC_OBG_S_seal_diff_window.py`
- `tests/test_AC_OBG_settings_merge.py` — settings-merge surface.

### Modified files

- `hooks/first_run_settings.py` — add `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS`, `_is_pos_v2_owned_pre_tool_use`, `merge_pre_tool_use`. No edits to existing functions.
- `hooks/first_run_helper.py` — add `merge_pre_tool_use` to imports, add `_objective_binding_gate_stanza`, `_maybe_merge_pre_tool_use`. Wire `_maybe_merge_pre_tool_use` into the three existing merge call sites (Phase 3d, Phase 4c, Phase 6).
- `tests/test_first_run.py::test_T4_rewritten_settings_preserves_user_keys_across_self_retire` — update to verify the new contract (user-authored PreToolUse → backup + gate replaces). Per `feedback_loose_AC_text_fix_AC_not_implementation`: the prior assertion reflected the absence of an A2-shaped contributor; A2 is the contributor that closes that assumption.

### Sidecar advances

- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.structural-enforcement-a2-objective-binding-gate` — new narrative file (created by `pos-amend apply` from the manifest narrative block).
- `framework/hands-off-lifecycle/tests/SEAL_COMMIT` — advanced by `pos-amend apply` to A2's amendment commit, then to the seal commit by `pos-amend seal`.

---

## 2. AC-to-test mapping

| AC | Test file | Test functions |
|---|---|---|
| AC.OBG.1 | `test_AC_OBG_1_deny_missing_sentinel.py` | `test_AC_OBG_1_dev_mode_no_sentinel_denies`, `test_AC_OBG_1_write_tool_also_denies`, `test_AC_OBG_1_multiedit_tool_also_denies` |
| AC.OBG.2 | `test_AC_OBG_2_deny_no_manifest_row.py` | `test_AC_OBG_2_sentinel_present_no_manifest_row_denies` |
| AC.OBG.3 | `test_AC_OBG_3_deny_no_glob_match.py` | `test_AC_OBG_3_glob_does_not_match_path_denies` |
| AC.OBG.4 | `test_AC_OBG_4_allow_glob_matches.py` | `test_AC_OBG_4_glob_matches_path_allows` |
| AC.OBG.5 | `test_AC_OBG_5_allow_carve_outs.py` | `test_AC_OBG_5_carve_out_path_allows` (parametrised over 15 carve-out paths) + `test_AC_OBG_5_non_carve_out_in_same_branch_denies` (negative confirmation) |
| AC.OBG.6 | `test_AC_OBG_6_normal_use_no_op.py` | `test_AC_OBG_6_normal_use_returns_no_op_without_consulting_substrate`, `test_AC_OBG_6_normal_use_non_carve_out_path_still_no_op` |
| AC.OBG.7 | `test_AC_OBG_7_audit_log.py` | `test_AC_OBG_7_audit_log_at_workspace_state_path` (path), `test_AC_OBG_7_deny_writes_one_ndjson_line` (byte-content + schema), `test_AC_OBG_7_no_op_writes_audit_line_too`, `test_AC_OBG_7_audit_log_is_append_only`, `test_AC_OBG_7_main_emits_deny_envelope_to_stdout` |
| AC.OBG.S | `test_AC_OBG_S_seal_diff_window.py` | `test_AC_OBG_S_no_path_outside_admitted_prefixes` (frozen-both-endpoints; SEAL_COMMIT filled post-seal) |

---

## 3. D-build choices (method-level, builder's call)

### D-build.1 — Decision-tree shape

Linear short-circuit chain in `evaluate(...)`:

1. mode == "normal-use" → no-op (AC.OBG.6).
2. tool not in {Edit, Write, MultiEdit} → no-op (defense-in-depth; matcher should already gate this but the function is callable directly from tests).
3. tool_input has no string `file_path` → no-op (malformed envelope; fail-soft).
4. path canonicalises outside workspace_root → allow (foreign-path; not in gate scope).
5. path is dev-discipline carve-out → allow (AC.OBG.5).
6. sentinel absent → deny (AC.OBG.1).
7. tracker unreachable → allow (fail-closed-to-permissive at substrate-import boundary; per locked plan §10 R7 mitigation).
8. all bindings have zero rows → deny (AC.OBG.2).
9. some bound row's glob fnmatchcase-matches path → allow (AC.OBG.4).
10. otherwise → deny (AC.OBG.3).

Carve-out check fires BEFORE sentinel read so dev-discipline edits admit even when no sentinel exists.

### D-build.2 — Helper-module placement

Inline in `objective_binding_gate.py`, NOT a separate `_gate_helpers.py`. Per locked plan §9 architecture-creep watch: A3/A4 may extract a shared library when the second gate ships; A2 ships only one gate, premature extraction is method-creep.

### D-build.3 — Carve-out match algorithm

Prefix-match for tree carve-outs (`docs/`, `tools/`, etc.) + exact-match for file admissions (`CLAUDE.md`, `.gitignore`, etc.). Lists at module top. Method per ODD §7.4. Order does not affect correctness because the predicate is OR over prefixes + OR over files.

### D-build.4 — Path canonicalisation

`Path(file_path).resolve().relative_to(workspace_root.resolve())`. Returns POSIX-style string via `as_posix()`. Foreign paths (outside workspace_root) → `None` → fall through to allow (out-of-workspace paths are not gated by A2 — no manifest row can match them).

### D-build.5 — Tracker open

Lazy-import inside `_open_tracker(workspace_root)` with venv-site path-fix mirroring the existing `_persona_user_prompt_submit_stanza` / `_persona_inner_hooks` pattern. Returns `None` on any failure (substrate unreachable). Per §1 step 7, substrate-unreachable falls through to allow (fail-closed-to-permissive at the import boundary).

### D-build.6 — Audit-log shape

NDJSON one row per fire. Fields: `ts`, `tool`, `path` (raw), `rel_path` (canonical or None), `mode`, `sentinel_state` ("present" / "absent"), `bound_acs` (list of `{component, ac_id}` dicts), `decision`, `failure_class` (nullable), `reason` (nullable on allow / no-op). Atomic append via `os.open(..., O_APPEND | O_CREAT | O_WRONLY)` + `os.write` of one line — POSIX guarantees per-write atomicity for payloads < `PIPE_BUF` (typically 4 KB; one row is well under).

Path: `<workspace>/workspace/.pos/objective-binding-gate.log` per locked plan §15 (`WORKSPACE_STATE_SUBDIR` = `"workspace"` post-D.2). Rotation deferred per §7.

### D-build.7 — Settings-merge function shape

`merge_pre_tool_use(*, settings_path, new_entry, now_iso=None) -> SettingsMergeResult` — byte-for-byte mirror of `merge_user_prompt_submit`. Single-contributor for now; multi-contributor generalisation is a future amendment when A3/A4 land.

### D-build.8 — Settings-merge marker substring

`objective_binding_gate.py` (the script's path substring) — canonical pos-v2-owned marker for the PreToolUse stanza. Mirrors the SessionStart / UserPromptSubmit / statusLine convention exactly.

### D-build.9 — Gate registration in first_run_helper

Inserted at all three existing merge call sites (Phase 3d, Phase 4c, Phase 6) immediately after `_maybe_merge_status_line(...)`. Same fail-soft wrapper pattern. The gate is co-located with hands-off-lifecycle's hooks; no lazy-import probe (mirrors `_maybe_merge_status_line`, not `_maybe_merge_user_prompt_submit`).

### D-build.10 — Updating test_T4

Per `feedback_loose_AC_text_fix_AC_not_implementation`: the prior test assertion that user-authored PreToolUse hooks remain untouched after self-retire reflected a contract that pre-A2 was true (no pos-v2 contributor wrote to PreToolUse) but is no longer correct post-A2. The correct test asserts the new contract: user-authored PreToolUse stanza moved to backup, gate stanza in its place. The test was authored as a baseline preservation test; A2 makes PreToolUse a pos-v2-owned stanza like SessionStart / UserPromptSubmit. Updating the assertions matches the same pattern AC46.5 followed when UserPromptSubmit became pos-v2-owned.

---

## 4. ODD §2.5 reverse-direction audit

Walk the diff backwards: every code path / branch / dependency / test in A2's diff traces back to a named AC.

### `framework/hands-off-lifecycle/hooks/objective_binding_gate.py`

| Surface | AC |
|---|---|
| `_CARVE_OUT_PREFIXES`, `_CARVE_OUT_FILES`, `_is_carve_out_path` | AC.OBG.5 |
| `_workspace_relative` (path canonicalisation) | R8 mitigation supporting AC.OBG.3 + AC.OBG.4 |
| `Decision` container | AC.OBG.{1..7} (carries the outcome surface) |
| `evaluate` — mode-bit short circuit | AC.OBG.6 |
| `evaluate` — tool gate | matcher contract; supports AC.OBG.{1..4, 6} |
| `evaluate` — carve-out check | AC.OBG.5 |
| `evaluate` — sentinel-absent branch | AC.OBG.1 |
| `evaluate` — tracker-unreachable fall-through | R7 mitigation; not its own AC (allow on env-failure is fail-open per locked plan §10) |
| `evaluate` — no-rows-for-any-binding branch | AC.OBG.2 |
| `evaluate` — glob-match scan | AC.OBG.3 + AC.OBG.4 |
| `_reason_missing_sentinel`, `_reason_no_manifest_row`, `_reason_no_glob_matches` | AC.OBG.{1, 2, 3} reason-text contracts |
| `_open_tracker` | AC.OBG.{2, 3, 4} substrate access |
| `_audit_log_path`, `_append_audit_line` | AC.OBG.7 |
| `_emit_allow_response`, `_emit_deny_response` | AC.OBG.{1, 2, 3} response contract |
| `main` — envelope parse | AC.OBG.{1..7} CLI entry; defensive return-0 on parse failure is the documented fail-soft contract per locked plan §5 fail-closed direction (the "fail-closed-to-permissive at the env-failure boundary" mirror) |

No silent exception branches. No code path lacks an AC. No defensive `if` for cases the ACs don't name (the env-failure return-0s ARE named in §5 fail-closed direction).

### `framework/hands-off-lifecycle/hooks/first_run_settings.py`

| Surface | AC |
|---|---|
| `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS` | AC.OBG.7 (settings-merge contract — gate is recognised as pos-v2-owned across re-merges) + R6 mitigation (merge regression) |
| `_is_pos_v2_owned_pre_tool_use` | Same |
| `merge_pre_tool_use` | Same — also satisfies the structural-enforcement A2 settings-merge surface that closes Q3 (existing user-authored PreToolUse hooks preserved via timestamped backup) |

### `framework/hands-off-lifecycle/hooks/first_run_helper.py`

| Surface | AC |
|---|---|
| `merge_pre_tool_use` import | AC.OBG.7 |
| `_objective_binding_gate_stanza` | AC.OBG.{1..7} — registers the gate in settings.json |
| `_maybe_merge_pre_tool_use` | AC.OBG.{1..7} fail-soft wrapper at the three call sites |
| The three call-site insertions (Phase 3d, 4c, 6) | AC.OBG.{1..7} — gate becomes live across the first-run / re-bootstrap / self-retire phases |

### Tests

Eight AC files + the settings-merge file. Every test function names its AC explicitly in the docstring; every AC has at least one test asserting its outcome.

### Reverse-direction conclusion

Every code path, branch, dependency, and test traces back to AC.OBG.1..AC.OBG.S. No method-in-AC drift. No unnamed cases. Clean.

---

## 5. Empirical answers (Q1, Q2, Q3)

### Q1 — MultiEdit partial-deny semantics

**Empirical answer:** MultiEdit is a single-tool-call that operates on a SINGLE `tool_input.file_path` with multiple edits in `edits: [{old_string, new_string, ...}, ...]`. There is no "mixed batch with multiple file_paths" — MultiEdit cannot edit multiple files in one call. The PreToolUse hook fires ONCE per MultiEdit call; the gate decision is per-call, applied to that one file_path. The "partial deny" question dissolves: there is no batch of paths to selectively deny.

The gate's behaviour on MultiEdit is identical to Edit / Write — single-path decision, single deny envelope on failure. Test: `test_AC_OBG_1_multiedit_tool_also_denies`.

### Q2 — PreToolUse merge mechanism

**Empirical answer:** `first_run_settings.py`'s merge architecture admits a parallel `merge_pre_tool_use` function without contract change to `merge_session_start` / `merge_user_prompt_submit` / `merge_stop` / `merge_status_line`. The new function mirrors `merge_user_prompt_submit` byte-for-byte (single-contributor; backup-on-displace; preserved-keys narration). All existing merge tests pass unchanged. No symmetry break; the PreToolUse stanza joins the existing list of pos-v2-owned event keys.

### Q3 — Existing user-authored PreToolUse hook preservation

**Empirical answer:** Existing user-authored PreToolUse hooks are preserved via the timestamped backup convention (mirrors AC46.5 byte-for-byte). On re-merge over a user-authored PreToolUse stanza:

1. The entire prior `settings.json` is written to `<settings>.user-backup-<ts>.json` (recoverable byte-equal).
2. The live `hooks.PreToolUse` is replaced with `[gate_envelope]`.
3. Other top-level keys (`env`, `permissions`, `hooks.SessionStart`, `hooks.UserPromptSubmit`, `hooks.Stop`, `statusLine`, etc.) are preserved on the live settings.json.

Tests: `test_re_merge_over_user_authored_creates_backup` + `test_pre_tool_use_merge_preserves_orthogonal_stanzas` in `test_AC_OBG_settings_merge.py`. Pre-existing `test_T4_rewritten_settings_preserves_user_keys_across_self_retire` updated to verify the new contract (test_T4 was authored when there was NO PreToolUse merge; the prior assertion reflected absence-of-contributor, not invariant — feedback_loose_AC_text_fix_AC_not_implementation applies).

---

## 6. Halt-trigger checks (locked plan §8 walked at build)

| # | Trigger | Fired? | Resolution |
|---|---|---|---|
| 1 | A1 substrate gap | No | A1's `manifest_rows_for_ac`, `read_active_scope_sentinel`, `workspace_mode` cover A2's surface byte-for-byte. |
| 2 | PreToolUse merge mechanism missing | No | `first_run_settings.py` admits `merge_pre_tool_use` without contract change (Q2). |
| 3 | MultiEdit semantics ambiguity | No | Q1: MultiEdit is single-path; per-call deny applies cleanly. |
| 4 | Existing PreToolUse hook collision | No | Q3: user-authored stanzas preserved via backup. |
| 5 | Surrounding-code ODD §2.5 violation | No | The §4 reverse-direction audit walked the diff and the surrounding `first_run_settings.py` / `first_run_helper.py` regions; no unnamed cases surfaced. |
| 6 | Outcome-resistant AC | No | All 8 ACs cleared §4. |
| 7 | Architecture creep | No | Per D-build.2: no shared helper library (premature). |
| 8 | Carve-out path-list incomplete | No | The list covers every path the test suite exercises; future additions are a separate amendment per §10 R1. |
| 9 | Substrate-fence breach | No | All edits live under `framework/hands-off-lifecycle/{hooks,tests}/` + `docs/rebuild/plans/`. |
| 10 | Self-bootstrap fails | N/A | Canonical-pos-v2 doesn't run the gate (no `.claude/settings.json`); workspaces will need manifest rows when they bootstrap with gate active. |

Plus the dispatch-level halt triggers (pre-flight staleness, AC.MS-fix.S regression, self-targeting hook activation, seal-diff fence breach on a non-named sealed component, API overload): none fired.

---

## 7. Pos-amend bookkeeping flow

1. ✅ Manifest authored at `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.manifest.yaml` with BASELINE = `3582054`.
2. ⚠️ Build-time manifest-row registration (locked plan hard constraint 14): the build agent's manifest rows for AC.OBG.1..AC.OBG.S are NOT registered in canonical-pos-v2's tracker — canonical doesn't have the gate active (no `.claude/settings.json` running first_run_helper), so the chicken-and-egg doesn't apply HERE. Workspaces that bootstrap with the gate active will need their build agents to register rows for their amendments' ACs as the gate's first audit-log fire shows. Future amendment dispatches into gate-active workspaces will register their own rows at build start.
3. ✅ Source edits + tests authored on branch `pos-v2`.
4. (Next) Stage + commit as the amendment commit.
5. (Next) `pos-amend apply --dry-run <manifest>` — must exit 0.
6. (Next) `pos-amend apply <manifest>` — advances BASELINE literals + writes SEAL_COMMIT sidecar narrative.
7. (Next) `pos-amend seal --plan-doc <ABS PATH>` — runs scoped test sweep, creates seal commit, advances SEAL_COMMIT to seal SHA, appends §14 SHA backfill commit.
8. (Next) Verify `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.

---

## 8. Test scope for the amendment-dispatch CDC speedups

Per the locked plan §11 + the dispatch's speedup directives:

- **Full hands-off-lifecycle test suite:** RUN (the only sealed component A2 touches). 254/254 passed.
- **Full objective-tracker test suite:** RUN (consumer-only sanity check that A1's substrate API still works). 146/146 passed.
- **Other sealed components — `test_no_sealed_amendments.py` only:** orchestrator (2), cost-governance (1), workspace-sync (2), workspace-bootstrap (2), self-correction (2), self-upgrade (2), memory-system (2), graceful-degradation (2), observability-aggregator (2), primary-persona (2). All passed.
- **AC.MS-fix.S frozen-window regression:** GREEN (frozen-both-endpoints; A2 cannot affect it).
- **Pre-seal full rerun:** SKIPPED per the dispatch's directive (sidecar-only edits between amendment commit and seal commit; the targeted suites cover the surface).

---

## 9. ODD §8.2.14 — byte-content verification

A2's audit log writes NDJSON to disk. `test_AC_OBG_7_audit_log.py::test_AC_OBG_7_deny_writes_one_ndjson_line` reads the on-disk log file via `Path.read_text(encoding="utf-8")` and asserts the schema (timestamp, tool, path, rel_path, mode, sentinel_state, bound_acs, decision, failure_class, reason). The test is the byte-content read AC.OBG.7 names; satisfies §8.2.14.

---

## 10. Synthetic post-amendment verification

The build agent's final verification step (per dispatch §7):

1. Mock out-of-glob edit (DEV MODE, no sentinel, sealed source path) → verify deny + reason text. **Done via test_AC_OBG_1_dev_mode_no_sentinel_denies.**
2. Mock carve-out edit (DEV MODE, no sentinel, `docs/` path) → verify allow. **Done via test_AC_OBG_5_carve_out_path_allows[docs/...].**
3. Both work as designed.

---

## 11. Cosmetic / capture items for FUTURE_IDEAS_DRAFT

None surfaced during this build. The plan / research / build sequence ran cleanly; no new ideas surfaced that would warrant a FIDRAFT entry.

---

## 14. Method-decision register (post-build, builder-backfilled)

The D-build choices recorded above (D-build.1 .. D-build.10) are the method-decision register entries.

### Commit SHAs

- Amendment commit: `ef02e7df325f18e902eee8792e3f979ee6f429ad` —
  `feat(structural-enforcement-a2): objective-binding gate (PreToolUse Edit/Write/MultiEdit refusal-on-binding-miss)`
- Seal commit: `052ad86e28466f8f4dbce0c345b07fa5c8909950` —
  `chore(seals): structural-enforcement A2 objective-binding gate (PreToolUse Edit/Write/MultiEdit deny on binding miss; carve-out admission; NORMAL USE no-op; NDJSON audit log) — hands-off-lifecycle at ef02e7d`
