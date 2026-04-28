# Structural enforcement — A3: TDD-guard — Builder plan

**Status:** authored 2026-04-28 (build-time, post-dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Plan-doc (governs):** `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.md`.
**Research artefact:** `docs/rebuild/plans/research/structural-enforcement-a3-tdd-guard-research.md`.
**Manifest:** `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.manifest.yaml`.

This builder plan records the D-build choices A3's build agent picks per the plan-doc's "method per ODD §7.4 — builder's call" clauses. Structurally analogous to A2's builder plan (`structural-enforcement-a2-objective-binding-gate.builder-plan.md`).

---

## 1. D-build register

### D-build.1 — Decision-tree shape (method per plan §11)

**Choice:** flat sequence of early-returns inside `evaluate(...)`. Each predicate either returns a `Decision` or falls through to the next. No nested branches. Mirrors A2's `objective_binding_gate.evaluate` shape byte-for-byte.

**Rationale:** the decision chain in the plan §1 fence statement is naturally linear (mode → tool → path-canonicalise → carve-out → test-tree → sentinel → tracker-open → bindings → new-AC-detect → test-existence). Each fall-through is named in §4 of the plan; nesting would obscure the AC mapping.

### D-build.2 — Helper-module shape (method per plan Q5)

**Choice:** single module `framework/hands-off-lifecycle/hooks/_gate_helpers.py`. Six top-level helpers extracted from A2's gate. No package nesting.

**Rationale:** locked plan §6 D-A3.7 + research Q5 default. Extracted helper count is small (six functions + two carve-out tuples + two path-constant strings); a package shape would add import indirection without payoff. If A4 grows the helper count, package shape opens.

**Symbols extracted from `objective_binding_gate.py` → `_gate_helpers.py`:**

- `WORKSPACE_STATE_SUBDIR = "workspace"` (constant)
- `POS_SUBDIR = ".pos"` (constant)
- `_CARVE_OUT_PREFIXES: tuple[str, ...]`
- `_CARVE_OUT_FILES: frozenset[str]`
- `is_carve_out_path(workspace_relative_path: str) -> bool`
- `workspace_relative(file_path: str, workspace_root: Path) -> str | None`
- `read_workspace_mode_or_normal_use(workspace_root: Path) -> str`
- `read_active_scope_sentinel_or_none(workspace_root: Path) -> ActiveScopeSentinel | None`
- `open_tracker_or_none(workspace_root: Path) -> Any | None`
- `audit_log_path(workspace_root: Path, log_filename: str) -> Path`
- `append_audit_line(workspace_root: Path, log_filename: str, payload: dict[str, Any]) -> None`

`_gate_helpers.py` keeps the leading-underscore naming on `_CARVE_OUT_PREFIXES` / `_CARVE_OUT_FILES` to mark them as module-private to the helper library; the public functions have unprefixed names.

`objective_binding_gate.py` keeps thin module-level shims for `_workspace_relative`, `_is_carve_out_path`, `_open_tracker`, `_audit_log_path`, `_append_audit_line`, `WORKSPACE_STATE_SUBDIR`, `POS_SUBDIR`, `AUDIT_LOG_FILENAME`, `_CARVE_OUT_PREFIXES`, `_CARVE_OUT_FILES` so existing test imports continue to work without rename. Each shim delegates to `_gate_helpers`. This is a refactor-equivalence preservation — A2's tests reach into module privates; the shim layer keeps them green.

### D-build.3 — AC normalisation rule (D-A3.9 default per plan §6)

**Choice:** `normalise_ac_id(ac_id: str) -> str`:

1. If starts with `AC.` (case-insensitive) → drop the leading `AC.`.
2. Replace every `.` with `_`.
3. Uppercase.

So `AC.TDG.1` → `TDG_1`; `AC.OBG.S` → `OBG_S`; `AC.A8.A` → `A8_A`. Test-file glob: `test_AC_<normalised>_*.py`. Function-name prefix: `test_AC_<normalised>_`.

**Empirical verification at build start:** every `framework/*/tests/test_AC_*.py` filename across the canonical tree follows the dotted-AC-id-with-dots-replaced convention (`test_AC_OBG_1_*`, `test_AC_SE_6_*`, `test_AC_M_11_*`, `test_AC_A8_A_*`, `test_AC_SL_2_*`, `test_AC_SFR_3_*`, `test_AC_E_1_*`). Pre-`AC` legacy names (`test_AC29_*`, `test_AC37_*`, `test_AC38_*`, `test_AC45_*`, `test_AC46_*`) follow a pre-convention shape (no underscore between `AC` and the numeric prefix); these tests were authored before the dotted-AC-id convention crystallised. **A3's normalisation rule is scoped to ACs whose ID matches `AC.<COMPONENT>.<INDEX>` — the dotted form. ACs whose first manifest row's `created_at` is after the sentinel's `created_at` (i.e. the ones A3 actually gates on) are necessarily authored under the dotted convention; legacy IDs are pre-A1 substrate so they cannot be NEW-in-this-diff.** The rule is sound.

### D-build.4 — Matching-function detection — regex vs AST (method per plan §11)

**Choice:** regex over file source text. Pattern `^def\\s+test_AC_<NORM>_\\w*\\s*\\(` (multiline). Read each candidate file as text, scan with `re.search`. No AST parse.

**Rationale:** AST parse pulls compile cost per file (~1ms each); regex is ~50µs. The pattern is narrow enough that false positives (a string literal containing the pattern) are vanishingly rare and harmless — false-positive direction is "allow" (the gate's softer outcome), not "deny." Per locked plan §1.5 / §4 AC.TDG.2, the gate verifies function-name presence, not function-body correctness — exact AST shape doesn't matter.

### D-build.5 — Hook-chain ordering specifics in settings.json (D-A3.8)

**Choice:** the multi-contributor PreToolUse list is `[A2_stanza, A3_stanza]` in that order. `A2_stanza.matcher = "Edit|Write|MultiEdit"`; `A3_stanza.matcher = "Edit|Write|MultiEdit"`. Both stanzas have a single inner-hook command. Claude Code admits multiple matcher entries; sequential evaluation means A2 evaluates first; A2 deny short-circuits A3.

A3's gate is built as a stanza by `_tdd_guard_stanza(pos_v2_root: Path) -> dict[str, Any]` analogous to `_objective_binding_gate_stanza`. The settings-merge call site `_maybe_merge_pre_tool_use` composes `[a2_stanza, a3_stanza]` and calls `merge_pre_tool_use(settings_path=..., new_entries=[a2_stanza, a3_stanza])`.

### D-build.6 — Multi-contributor merge function shape

**Choice:** `merge_pre_tool_use` accepts `new_entries: list[dict[str, Any]] | None = None` AND `new_entry: dict[str, Any] | None = None`; when `new_entries` is provided, the OUTER `hooks.PreToolUse` list is replaced by `new_entries`; when only `new_entry` is provided, behaviour is byte-identical to pre-A3 (the OUTER list becomes `[new_entry]`); raises `ValueError` if both are None.

**Rationale:** preserves A2's existing single-contributor call sites byte-for-byte (the test suite checks `len(data["hooks"]["PreToolUse"]) == 1` for `new_entry=` callers); enables A3's multi-contributor call site cleanly. The `_is_pos_v2_owned_pre_tool_use` predicate's marker tuple grows to include `tdd_guard.py`; a stanza whose every inner-hook command matches one of the markers is pos-v2-owned (single OR multi-contributor), so re-merge over a pos-v2 stanza never backs up.

### D-build.7 — JSON keys for deny reason + audit log

**Choice:** identical to A2's keys for the deny envelope (`hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason: "<text>"`). Audit-log keys mirror A2 with three new fields:

- A2's keys retained: `ts`, `tool`, `path`, `rel_path`, `mode`, `sentinel_state`, `bound_acs`, `decision`, `failure_class`, `reason`.
- A3-new keys: `new_acs_in_scope` (list of `{component, ac_id}` for ACs A3 considers new); `tests_present` (list of `{ac_id, test_path}` for ACs whose test was found); `tests_missing` (list of `{ac_id, expected_test_glob}` for ACs whose test was NOT found — empty on allow).

Audit log filename: `tdd-guard.log`. Path: `<workspace>/workspace/.pos/tdd-guard.log`. Mirrors A2's shape exactly.

### D-build.8 — `created_at` strict-vs-tolerance comparison

**Choice:** strictly-after (`row_created_at > sentinel_created_at`). ISO-8601 string lex-compare gives correct ordering on second-resolution timestamps. No skew tolerance.

**Rationale:** plan §6 D-A3.4 + research §2.5. Same-machine, same-process — drift is essentially zero. A row registered exactly at the sentinel's second is treated as "not new" (the row was registered AT sentinel-author time, not after) — that's the conservative direction (allow rather than deny on a millisecond-edge case). When the build agent registers rows AFTER sentinel-author (the canonical sequence), the row's timestamp is at minimum one millisecond later, lex-comparing correctly.

---

## 2. Files touched

### New files

- `framework/hands-off-lifecycle/hooks/_gate_helpers.py` — shared helper library (D-build.2 symbol list).
- `framework/hands-off-lifecycle/hooks/tdd_guard.py` — A3's PreToolUse hook script.
- `framework/hands-off-lifecycle/tests/test_AC_TDG_1_deny_no_test_file.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_2_deny_no_test_function.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_3_allow_test_path.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_4_allow_existing_ac.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_5_allow_test_present.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_6_normal_use_no_op.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_7_audit_log.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_S_seal_diff_window.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_8_helper_extraction_equivalence.py`
- `framework/hands-off-lifecycle/tests/test_AC_TDG_settings_merge.py`
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.structural-enforcement-a3-tdd-guard` (sidecar; written by `pos-amend apply`).
- `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.builder-plan.md` (this file).
- `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.manifest.yaml` (manifest).

### Modified files

- `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` — refactored to consume `_gate_helpers.py`. Module-level shims preserve existing test imports.
- `framework/hands-off-lifecycle/hooks/first_run_settings.py` — `merge_pre_tool_use` extended to multi-contributor (D-build.6); `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS` adds `tdd_guard.py`.
- `framework/hands-off-lifecycle/hooks/first_run_helper.py` — adds `_tdd_guard_stanza`; `_maybe_merge_pre_tool_use` composes `[a2_stanza, a3_stanza]` and calls `merge_pre_tool_use(new_entries=[...])`.

---

## 3. AC-to-test mapping

| AC | Test file | Behaviour |
|---|---|---|
| AC.TDG.1 | `test_AC_TDG_1_deny_no_test_file.py` | DEV MODE + new AC + no test file → deny with structured reason |
| AC.TDG.2 | `test_AC_TDG_2_deny_no_test_function.py` | DEV MODE + new AC + test file present + no matching function → deny |
| AC.TDG.3 | `test_AC_TDG_3_allow_test_path.py` | Path under `framework/<comp>/tests/**` → allow (chicken-and-egg) |
| AC.TDG.4 | `test_AC_TDG_4_allow_existing_ac.py` | All manifest rows for binding `created_at` BEFORE sentinel's → allow |
| AC.TDG.5 | `test_AC_TDG_5_allow_test_present.py` | New AC + test file + matching function → allow |
| AC.TDG.6 | `test_AC_TDG_6_normal_use_no_op.py` | Mode=normal-use → no-op (no consultation of tracker/sentinel/fs) |
| AC.TDG.7 | `test_AC_TDG_7_audit_log.py` | Per-fire NDJSON line; byte-content read of on-disk file |
| AC.TDG.S | `test_AC_TDG_S_seal_diff_window.py` | Seal-diff confined to fence (frozen-both-endpoints, post-seal) |
| AC.TDG.8 | `test_AC_TDG_8_helper_extraction_equivalence.py` | A2's behaviour byte-equivalent post-extraction |
| AC.TDG.settings_merge | `test_AC_TDG_settings_merge.py` | Multi-contributor merge composes A2+A3 stanzas, single-contrib backwards-compat preserved |

The `settings_merge` test is the regression contract for the multi-contributor merge (parallel to A2's `test_AC_OBG_settings_merge.py`). It is a behaviour-supporting test for AC.TDG.S (the seal-diff invariant) + AC.TDG.8 (the equivalence guarantee covers the merge-helper symbols A2's tests reach into); not a separate AC.

---

## 4. Bootstrap-order trace

1. Author manifest YAML + builder plan + (already-authored) plan-doc + research artefact. (Universal-paths admissions; no manifest rows needed.)
2. `tracker.register_source_binding` for each A3 AC: `(hands-off-lifecycle, AC.TDG.1, framework/hands-off-lifecycle/{hooks,tests}/**)` ... through `AC.TDG.S` and `AC.TDG.8`. Build agent's first programmatic action — but in canonical pos-v2 (NORMAL USE workspace), neither A2 nor A3 fires, so the row registration is bookkeeping for future bootstrapped workspaces; the canonical-tree build does not depend on it for gate-passage. (Recorded here for completeness.)
3. Author A3's tests first — admitted by A3's own test-tree carve-out (AC.TDG.3) when A3 ships in DEV MODE. In canonical (NORMAL USE), all gates no-op; the order is preserved as discipline.
4. Author A3's source files (`_gate_helpers.py`, `tdd_guard.py`, refactor `objective_binding_gate.py`, extend `first_run_settings.py`, extend `first_run_helper.py`).
5. Run targeted test sweep: `framework/hands-off-lifecycle/tests/` + `framework/objective-tracker/tests/` (consumer-only sanity). All AC.OBG.x + AC.TDG.x + cross-cutting GREEN.
6. Commit feature commit on branch `pos-v2`.
7. `pos-amend apply --dry-run docs/rebuild/plans/structural-enforcement-a3-tdd-guard.manifest.yaml` — must exit 0.
8. `pos-amend apply <manifest>` — advances BASELINE / SEAL_COMMIT sidecars.
9. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/structural-enforcement-a3-tdd-guard.builder-plan.md <manifest>` — runs scoped tests, creates seal commit, advances SEAL_COMMIT, appends builder-plan §SHA backfill follow-up commit.
10. Verify `pos-amend apply --dry-run` exits 0 against post-seal HEAD.

---

## 5. ODD §2.5 reverse-direction audit

Every line in A3's diff traces to a named AC:

- `_gate_helpers.py` symbols → AC.TDG.8 (extraction equivalence) + AC.OBG.x preservation (regression contract). Each symbol is consumed by `objective_binding_gate.py` (post-refactor) AND `tdd_guard.py`; its presence supports the named ACs.
- `tdd_guard.py` decision-chain branches → AC.TDG.1 (deny no test file), AC.TDG.2 (deny no test function), AC.TDG.3 (allow test path), AC.TDG.4 (allow existing AC), AC.TDG.5 (allow test present), AC.TDG.6 (no-op normal-use), AC.TDG.7 (audit log).
- `tdd_guard.py` audit-log writer → AC.TDG.7.
- `objective_binding_gate.py` refactor → AC.TDG.8 (equivalence) + AC.OBG.1..AC.OBG.7 (regression).
- `first_run_settings.py` multi-contributor extension → AC.TDG.settings_merge (supports AC.TDG.S surface).
- `first_run_helper.py` `_tdd_guard_stanza` + composed `_maybe_merge_pre_tool_use` → AC.TDG.settings_merge.
- Test files → their named AC.

No silent branches, no defensive `if`s without backing AC.

---

## 6. Halt-trigger checks (from plan §8)

Run at build start; record outcome:

1. A1 substrate gap — VERIFIED CLEAN. `manifest_rows_for_ac` returns dict rows including `created_at`. `ActiveScopeSentinel.created_at` is a top-level field. `workspace_mode` returns `"dev-mode" | "normal-use"` two-string contract.
2. A2 helper incompatibility — VERIFIED CLEAN by completing the extraction. `objective_binding_gate.py`'s helpers do not depend on module-private state; the lazy-import pattern is factor-able. Module-level shim preserves test-import compatibility.
3. A2 manifest API insufficient — VERIFIED CLEAN. `list_manifest_rows_for_ac` returns `list[dict[str, Any]]` with `created_at` directly accessible.
4. MultiEdit semantics — A2's empirical answer (single `file_path` at top-level) holds.
5. PreToolUse hook collision — extended `merge_pre_tool_use` to multi-contributor; A2's existing `test_AC_OBG_settings_merge.py` passes byte-equivalent because single-contributor calls `new_entry=` continue to produce `[new_entry]`.
6. ODD §2.5 surrounding-code violations — none surfaced during the helper-extraction; refactor moved code 1:1 with no new branches.
7. Outcome-resistant AC — none; all 9 ACs are outcome-shaped.
8. Architecture creep — extracted shared library; no single-dispatcher creep.
9. AC normalisation ambiguity — VERIFIED CLEAN. Empirical scan recorded in §1 D-build.3.
10. Substrate-fence breach — none. All edits inside `framework/hands-off-lifecycle/{hooks,tests,seals}/` + universal admissions.
11. Self-bootstrap — canonical pos-v2 is `normal-use`; gate self-targeting risk does not arise.
12. AC.OBG.x regression — pre-seal sweep confirms all AC.OBG.x tests pass.
13. Dispatch staleness — pre-flight clean (no A3 commit before this build).

---

## 7. Pos-amend bookkeeping flow

Per plan §11.

1. Manifest authored at `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.manifest.yaml` with `baseline: 8c20bba...` (HEAD at dispatch).
2. Tracker rows registered for AC.TDG.x (canonical NORMAL USE — bookkeeping; gate doesn't fire).
3. Tests authored before source.
4. Source authored.
5. Commit feature commit on `pos-v2`.
6. `pos-amend apply --dry-run` — exit 0.
7. `pos-amend apply` — advances BASELINE.
8. `pos-amend seal --plan-doc <ABSOLUTE>` — scoped tests + seal commit + plan SHA backfill.
9. Verify `pos-amend apply --dry-run` exits 0 post-seal.

---

## 8. Helper-extraction equivalence verification

A3's regression contract for D-A3.7 is two-fold:

1. A2's existing AC.OBG.1..AC.OBG.7 + AC.OBG.S + AC.OBG.settings_merge tests pass byte-for-byte against the post-refactor `objective_binding_gate.py`. The pre-seal test sweep confirms.
2. AC.TDG.8's explicit equivalence test parametrises a representative set of decision paths through `objective_binding_gate.evaluate` and asserts the post-refactor `Decision` matches the pre-refactor outcome. The pre-refactor outcome is captured by re-running A2's existing test fixtures (the `_FakeTracker` + sentinel stubs from `test_AC_OBG_4_*.py` etc.); the test imports `objective_binding_gate` post-refactor and asserts the same decisions.

The shim layer (module-level re-exports of `_workspace_relative`, `_is_carve_out_path`, `_open_tracker`, `_audit_log_path`, `_append_audit_line`, `_CARVE_OUT_PREFIXES`, `_CARVE_OUT_FILES`, `WORKSPACE_STATE_SUBDIR`, `POS_SUBDIR`, `AUDIT_LOG_FILENAME`) preserves test-import compatibility — A2's tests reach into these privates from `import objective_binding_gate as gate; gate._audit_log_path(...)` etc.

---

## 9. Method-decision register (post-build)

(See plan-doc §14 for SHAs; this builder plan documents the D-build choices above.)

---

*End of builder plan. Manifest at `structural-enforcement-a3-tdd-guard.manifest.yaml`; plan-doc at `structural-enforcement-a3-tdd-guard.md`.*
