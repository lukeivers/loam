# BB-cycle Architecture-B Retarget — adversarial code review

**Date:** 2026-04-26
**Reviewer:** dispatched code-review agent (Opus 4.7, 1M context).
**Scope:** every file added or extended by BB-feat (#55), DD bugfix (#56),
CC validation (90246dc), and EE prep (caafdf0). Read-only review.
**Lens:** Architecture-A (global `~/.pos/framework/current/` symlink swap,
release-tagged manifests, install/edit dichotomy) versus locked
Architecture-B (per-workspace embedded framework, sync canonical's HEAD
into pos3's working tree, commit-SHA-or-ref identification, no global
symlink swap).
**Calibration:** assume agent reports lied about cleanliness; cite specific
lines as evidence; name hidden coupling.

---

## TL;DR

- **Salvageable LOC fraction:** ~70 % of the touched LOC survives the
  re-target with edits ranging from "literally none" to "rewrite the
  caller, not the callee." The mechanical-A coupling is concentrated
  in two files: `cli.py` (six `paths.current_link` / `paths.history`
  references including the `live_root` derivation that backs every
  workspace-local path) and `_build_manifest.py` (the manifest
  generator's whole reason for existing).
- **Architecture B does not need the manifest.** The 198-entry
  `pos-v2-v0.2.0.yaml` is a tag-keyed file-list with prior-vs-post
  shas — exactly what gets discarded when we swap to "sync canonical
  HEAD into the workspace tree" because git-tree-vs-working-tree
  diffing replaces sha-bookkeeping. **EE manifest = discard.**
- **The merge-resolver factory (EE) is architecture-neutral.**
  `upgrade_merge_resolver/__init__.py` carries zero `~/.pos/` /
  `current/` / release-tag references; the only A-flavoured import
  is the literal `MergeResolver` symbol it returns. Salvage as-is.
- **Clause-(h) helper is the high-leverage win.** `merge_resolver.py`,
  `sync_protected.py`, `clause_checks.py::resolve_clause_h_inferred`
  + `check_clause_h`, `conflict_report.py`'s INFERRED_* extensions,
  and `state.py` are all architecture-neutral by accident. They take
  `canonical_root: Path` and `workspace_root: Path` as injection
  points; they don't care whether those came from a symlink swap or
  a sync command. **Salvage as-is or with cosmetic edits.**
- **High-risk surface-vs-real gap:** the synthetic validation tests
  pass entirely against tmp_path fixtures with hand-rolled
  `ConflictReport` instances. They never run `detect_conflicts`
  against a real-shaped tree under B; they never invoke the live
  CLI with the **post-B** code path; the two CLI-driven tests
  (`test_cli_canonical_pending_writes_audit_yaml*`,
  `test_cli_auto_discovers_prior_state_yaml_on_canonical_rerun`)
  bake A-shaped fixtures (synthetic `paths.release_dir(prior)` +
  `os.symlink(prior, current_link)`) that wouldn't exist under B.

---

## Per-file verdict table

| file | A-coupling | rebadge verdict | concrete rebadge work | A-assumption hooks identified |
| --- | --- | --- | --- | --- |
| `self-upgrade/src/self_upgrade/canonical.py` | A-weak | salvage-with-edits | rename `tag` → `ref` (or `commit_sha`); drop the `manifest.release_tag != tag` validator; default-manifest-path lookup either disappears or moves to a sentinel. The git-working-tree existence check (`canonical_path / ".git"`) survives unchanged. | L42-44 `default_manifest_path()` is tag-shaped; L92-96 `release_tag != tag` validator is only a problem because the manifest is. `staging_dir == canonical_path` (L98-103) is **fine for B**: pointing at canonical HEAD is exactly what B needs. |
| `self-upgrade/src/self_upgrade/sync_protected.py` | neutral | salvage-as-is | none — except possibly extending FRAMEWORK_FLOOR with B-specific paths (e.g. `.git/**` if sync runs inside a git tree). | Zero `~/.pos/` / `current/` / `release_tag` references. The envelope is workspace-shaped from day one. The only A-flavoured implication is that the file lives at `<workspace>/.pos/sync-protected.yaml` — which is also exactly where B wants it. |
| `self-upgrade/src/self_upgrade/merge_resolver.py` | neutral | salvage-as-is | none. | Zero couplings. Resolver takes `path`/`canonical_text`/`workspace_text` as injection params. `LLMClient` Protocol is architecture-blind. |
| `self-upgrade/src/self_upgrade/conflict_report.py` | neutral | salvage-as-is | none — except possibly broadening `upgrade_tag` to `upgrade_ref` (cosmetic). | Schema fields use `upgrade_tag`/`prior_tag` strings but enforce no semantics on them. Set `upgrade_tag = canonical_HEAD_sha[:12]` and the schema doesn't notice. INFERRED_* enum extensions, `sorted_low_confidence_first`, `inferred_entries`, the `_reject_skipped` validator are all architecture-blind. |
| `self-upgrade/src/self_upgrade/clause_checks.py` (BB-feat additions, L26-50, L352-634) | A-weak | salvage-with-edits | swap `report.upgrade_tag` callers to whatever B uses (commit-SHA or sync-id); audit-write line `audit_yaml_path(workspace_root, report.upgrade_tag)` (L549) keeps working under B because `audit_yaml_path` is workspace-rooted not global; finally-block writes `state.yaml` to workspace, not global. | The whole `resolve_clause_h_inferred` function takes `canonical_root` + `workspace_root` as Path injections; classify is via `sync_protected.classify(entry.path)`; resolver invocation is per-file string content. **No reference to `paths.current_link` / `paths.history`.** L549 audit_yaml_path is workspace-relative. L569 save_state is workspace-relative. The pre-existing clauses (a)-(g) ARE A-coupled (clause-f checks `paths.history_dir_pre(tag)` for snapshot existence; clause-g sha-verifies against `live_root` derived from `paths.current_link`); but those are NOT in the BB-cycle scope and are out of bounds for this review. |
| `self-upgrade/src/self_upgrade/cli.py` (BB-feat additions: L29-66 imports; L135-320 cmd_upgrade; L371-397 helper loaders; L463-477 new flags) | **A-strong** | salvage-with-edits to redesign | this is the biggest rebadge. `cmd_upgrade` orchestrates `--canonical` + `--merge-resolver-module` for the upgrade-flow, NOT a sync flow. Architecture B needs a different command (`pos sync`?) with a different argument shape (no `--prior-tag`, no manifest validation, no `paths.current_link.resolve()` derivation of `live_root`). The CLAUSE-H GLUE INSIDE `cmd_upgrade` (L218-256) is salvageable: extract it into a callable that B's new sync-flow invokes. The flag-parsing and argparse construction can be wholesale replaced. | L184 `live_root = paths.current_link.resolve() if paths.current_link.exists() else paths.framework` — under B this is wrong. Live root IS the workspace cwd, not a global symlink. L196 `audit_yaml_path(live_root, ...)` then derives the audit path from the *resolved-symlink* root, which under B never exists. L210 `load_state(live_root)` same bug. L72-91 `refuse_if_invoked_from_live_path` — entire function is A-shaped (refuses execution from inside the symlinked release tree); under B "live tree" is the workspace cwd which is *exactly where you'd run from*. L262-274 pending-block writes to `paths.history` — global. L194-198 even though `audit_yaml_path` itself is workspace-shaped, `live_root` is fed from `current_link`. **Hidden coupling the agent reports glossed over: live_root is not the workspace, it's the resolved symlink target.** |
| `self-upgrade/templates/sync-protected.default.yaml` | neutral | salvage-as-is | none — patterns may want extending (e.g. `.git/**`, `objective_tracker.sqlite` is currently scoped under `.pos/`, fine). | Zero couplings. Pattern set is workspace-shaped. |
| `self-upgrade/src/self_upgrade/state.py` (DD #56) | neutral | salvage-as-is | optional: rename `upgrade_tag` → `sync_ref` for accuracy; not required for the schema to keep working. | Schema and helpers are 100 % workspace-rooted. `state_yaml_path(workspace_root)` and `audit_yaml_path(workspace_root, tag)` both take workspace_root as a parameter. Zero `~/.pos/`/`current_link` references. UpgradeStatus enum (success/failure/partial) carries semantic that fits B unchanged. |
| `self-upgrade/tests/test_bb_feat_synthetic_validation.py` (CC + DD flips) | mixed | salvage half / redesign half | direct-helper tests (every `resolve_clause_h_inferred` invocation that doesn't go through `main()`) survive the re-target with zero edits. CLI-driven tests (4 of 12: the three `test_cli_canonical_*` tests + `test_cli_staging_dir_only_no_clause_h_path` + `test_cli_auto_discovers_prior_state_yaml_on_canonical_rerun`) bake A-architecture fixtures that don't exist under B and need redesign. | L267-276, L593-601, L668-675, L930-938 — all of them stand up `paths.release_dir(prior_tag)` + `os.symlink(prior, paths.current_link)`. That symlink-swap world is gone under B. The tests pass *now* because they synthetically reproduce A; they would all fail end-to-end under B without rewriting the fixture-builders. Mocks at this level mask A-vs-B-mismatch. **The `--staging-dir` byte-identical backward-compat test (L558-625) is a valid invariant under A but doesn't apply under B at all** (B has no `--staging-dir` mode). |
| `tools/upgrade-merge-resolver/src/upgrade_merge_resolver/__init__.py` | neutral | salvage-as-is | none. | Zero `~/.pos/`/`current_link`/`release_tag` references. Subprocess wrap of `claude -p`, env-allowlist, JSON-envelope parsing, token-cost extraction, `build_merge_resolver()` factory — all architecture-blind. |
| `tools/upgrade-merge-resolver/pyproject.toml` | neutral | salvage-as-is | none. | Pure packaging; only dependency is `pydantic>=2`. |
| `self-upgrade/manifests/pos-v2-v0.2.0.yaml` (198 entries, 799 lines) | **A-strong** | **discard** | B uses commit-SHA-or-ref identification + git-tree diff. There is no point at which B reads "list of files-with-shas keyed by release tag." | Whole purpose is to enumerate framework files for tag-keyed sha-verification (clause-(g) `verify_file_against`). Under B, `git diff <ref>` against the workspace tree replaces this. Keeping the manifest is dead weight. |
| `self-upgrade/manifests/_build_manifest.py` | A-strong | discard or repurpose | the SEALED_COMPONENTS enumeration (L46-62) might be reusable as "the list of trees the sync-engine should consider in-scope" — but that list is essentially "everything in canonical's working tree", which `git ls-tree HEAD` answers natively. | Whole script generates the manifest. With manifest discarded, script is dead. |

---

## Synthesis

### What survives cleanly (salvage-as-is)

- **`merge_resolver.py`** — Resolver Protocol + ResolverBudget + BudgetExhausted + ResolverFailure + MergeResolver class. ~190 LOC.
- **`sync_protected.py`** — A/B/C envelope, FileClass enum, FRAMEWORK_FLOOR, classify, default_sync_protected, write_default_if_absent. ~170 LOC.
- **`conflict_report.py`** INFERRED_* extensions + ConflictEntry rationale/confidence/user_override fields + `sorted_low_confidence_first` + `inferred_entries` + `_reject_skipped` validator. ~120 LOC of additions.
- **`state.py`** — StateRecord, UpgradeStatus, audit_yaml_path, state_yaml_path, load_state, save_state, make_state_record. ~130 LOC.
- **`templates/sync-protected.default.yaml`** — 30-line YAML.
- **`tools/upgrade-merge-resolver/**`** — entire package, ~270 LOC. Zero edits.

**Subtotal salvage-as-is:** ~910 LOC out of ~3500 touched.

### What survives with cosmetic / minor edits (salvage-with-edits)

- **`canonical.py`** — drop the manifest validator, rename `tag` → `ref`, drop `default_manifest_path`. ~80 LOC remain.
- **`clause_checks.py::resolve_clause_h_inferred`** + `check_clause_h` + helpers `_read_text_or_none`, `_verdict_to_resolution`. ~280 LOC. Edits: caller-side rebadging of `report.upgrade_tag` semantic; otherwise unchanged.
- **Direct-helper tests in `test_bb_feat_synthetic_validation.py`**: `test_class_b_workspace_modified_keeps_local`, `test_class_b_workspace_unmodified_accepts_canonical`, `test_cli_canonical_pending_writes_audit_yaml_with_class_a_passthrough` (despite name, this one does NOT go through CLI), `test_cli_canonical_idempotent_rerun_no_resolver_calls`, `test_cli_user_override_idempotent_across_runs` (despite name, also direct-helper), `test_cli_canonical_seeds_default_sync_protected_on_first_run`, `test_halt_surface_audit_not_written_on_clean_clause_h_pass`, `test_halt_surface_state_yaml_not_implemented`. ~7 of 12 tests, ~500 LOC. **These survive because they invoke `resolve_clause_h_inferred` directly with `canonical_root` + `workspace_root` Path arguments.**

**Subtotal salvage-with-edits:** ~860 LOC.

### What needs redesign (substantial)

- **`cli.py` cmd_upgrade glue (L135-320)** — the `--canonical` + `--merge-resolver-module` argparse + flow orchestration. The clause-(h) hook block (L218-256) and audit-write block (L262-274) and live_root derivation (L184) are all entangled with the upgrade-symlink-swap mental model. Under B the entry point is a different command (`pos sync`) that doesn't carry `--prior-tag`, doesn't need `paths.current_link`, doesn't refuse-if-invoked-from-live-path. **Redesign the entry point; salvage the inner clause-(h) call as a callable.** ~200 LOC of cli.py changes.
- **CLI-driven tests (4)**: `test_cli_canonical_pending_writes_audit_yaml`, `test_cli_canonical_without_merge_resolver_module_skips_clause_h`, `test_cli_staging_dir_only_no_clause_h_path`, `test_cli_auto_discovers_prior_state_yaml_on_canonical_rerun`. Their fixtures (`paths.release_dir(prior)` + `os.symlink`) reproduce A. Under B these tests need rewriting against the new entry-point. **Functionally redundant** with the direct-helper tests for clause-(h) coverage; useful only as integration-of-CLI-glue once that glue is rewritten. ~400 LOC.

### What gets discarded

- **`pos-v2-v0.2.0.yaml`** (799 LOC) — manifest is fundamentally an A-shape artefact.
- **`_build_manifest.py`** (~100 LOC) — only reason to exist is to generate the manifest.

**Subtotal discard:** ~900 LOC.

### High-risk items (looks-fine-on-surface-but-fails-under-B)

1. **`cli.py:184` — `live_root = paths.current_link.resolve()`.** Reads as a benign safety fall-back; actually the entire workspace-local audit + state lookup hangs off it. Under B `paths.current_link` doesn't exist (no global symlink) so `live_root` falls through to `paths.framework` (= `~/.pos/framework`) — and then `audit_yaml_path(live_root, tag)` writes the audit at `~/.pos/framework/.pos/upgrade/<tag>/audit.yaml` instead of in the actual workspace. **The `--canonical` audit-path branch is functionally broken under B even though the code looks workspace-shaped.** This is the single most important hidden coupling the BB/DD agent reports glossed.
2. **Auto-discovery branch (`cli.py:209-216`).** `prior = load_state(live_root)`. Same `live_root` bug. The auto-discovery would silently fail to find a prior state.yaml under B because it's looking under the wrong root.
3. **`refuse_if_invoked_from_live_path` (`cli.py:72-91`).** Actively *refuses* execution under B's normal mode (running from the workspace = "the live framework path" under B). This is a structural blocker, not a soft warning.
4. **Synthetic-validation tests pass under A and prove nothing about B.** All four CLI-driven tests reproduce the A-symlink world in fixtures. Test green ≠ B-correctness. Real verification needs an integration test that invokes against an actual workspace clone with no `paths.current_link`.
5. **`canonical.py:92-96` `manifest.release_tag != tag` validator.** Under B the manifest goes away; the validator is dead. But it would also raise on a partial migration where the manifest is kept but `tag` becomes a SHA. Quiet trap during incremental migration.
6. **Manifest generator's hard-coded SEALED_COMPONENTS list.** If anyone leaves `_build_manifest.py` around as "doc," it lies — it pins a 15-component world that may drift from canonical's actual layout. Discard or delete.

### Specific lines/functions to spot-verify

The reviewer hand-picks five specific lines for the dispatcher to spot-check (verify the verdict against the actual code without trusting the table):

- **`cli.py:184`** — confirm `live_root` derivation; under B this is the structural bug.
- **`clause_checks.py:549`** — confirm `audit_yaml_path(workspace_root, report.upgrade_tag)` uses the function-scoped `workspace_root` parameter and not a module-level path; this is what makes the helper salvageable.
- **`merge_resolver.py:107-153`** — confirm `build_prompt` is purely-functional with no global-state reads; this is what makes the resolver salvageable.
- **`upgrade_merge_resolver/__init__.py:101-200`** — confirm the subprocess `invoke` doesn't read from `~/.pos/` (it doesn't); this is what makes the EE merge-resolver factory salvage-as-is.
- **`test_bb_feat_synthetic_validation.py:289-307`** (the first `main()` invocation) — confirm the test path goes `os.symlink(prior, paths.current_link)`; this is the A-architecture fixture that won't exist under B.

### Concrete next-step recommendation for the workspace-sync plan-author dispatch

The workspace-sync plan-author dispatch should **inherit** (use as-is or with cosmetic edits):

1. The whole `merge_resolver.py` module (Protocol + Budget + Resolver class).
2. The whole `sync_protected.py` module (A/B/C envelope + classify).
3. The `conflict_report.py` INFERRED_* schema extensions + `sorted_low_confidence_first` + `inferred_entries`.
4. The `state.py` module (StateRecord + UpgradeStatus + audit_yaml_path + state_yaml_path).
5. The `templates/sync-protected.default.yaml` template.
6. The `tools/upgrade-merge-resolver/` factory package.
7. The `resolve_clause_h_inferred` helper from `clause_checks.py`, lifted to a `workspace-sync`-resident module (it doesn't actually depend on clause-(a)-(g) — it just lives in the same file). Same for `check_clause_h`. ~280 LOC of helper survives.
8. Direct-helper tests from the validation suite (~7 tests / ~500 LOC).

The plan-author dispatch should **author fresh**:

1. A new entry point (`pos sync` CLI / slash-command surface). Not the upgrade entry. No `--prior-tag`, no manifest, no `paths.current_link`, no `refuse_if_invoked_from_live_path`.
2. A workspace-cwd-rooted "live root" derivation (e.g. `live_root = Path.cwd()` or `--workspace <dir>`).
3. A canonical-pull surface — git-clone-or-fetch a fresh canonical tree to a tmp location, OR accept a path to an existing canonical clone. Re-uses `canonical.py::resolve_canonical_to_staging` minus the manifest validator.
4. A B-shaped conflict-detection surface to **replace** `detect_conflicts` (which sha-verifies against the manifest). B uses `git diff` (or `git merge-file` three-way) to find conflicts. **This is net-new code.**
5. Integration tests against a workspace tree that lacks any `paths.current_link` symlink, exercising the actual flow.

The plan-author dispatch should **discard**:

1. `pos-v2-v0.2.0.yaml` and `_build_manifest.py`.
2. The four CLI-driven validation tests in their current shape (they pin A-fixtures).
3. The `--prior-tag` argparse arg and any code that consumes it.
4. The `--staging-dir` argparse mode (entirely an A concept).
5. The `refuse_if_invoked_from_live_path` safety check.

### One-sentence bottom line

The BB-cycle's clause-(h) primitives (resolver, envelope, audit schema, state) are architecture-neutral by accident and survive a re-target wholesale; the cli.py glue and the manifest infrastructure are A-shaped and need replacement, not refactor.
