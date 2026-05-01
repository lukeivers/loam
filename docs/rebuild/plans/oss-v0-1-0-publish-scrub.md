# OSS v0.1.0 publish — M9 — synth-time path substitution + in-place fixture refactor — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (§5 M9 row + §6 sequencing rule #7 + §13 D-Q.OSS.6 ruling).
**Predecessor:** M6 series sealed (M6a `1d27f9b`; M6b.0 `…`; M6b.1 `…`; M6c `a4c3ec3`). M9 is the gate before M11 dry-run per master §6.
**Predicted AI-time:** plan-rubric midpoint 30 min (master plan §5); calibrated band 10–25 min after M5/M6a/M6b.0/M6b.1/M6c. Log actual at §14.

**Authority documents:**
- Master plan §5 M9 row: single-component sealed amendment + in-place fixture refactor.
- Master plan §13 D-Q.OSS.6 ruling: "Luke Ivers" → "Alice Anderson"; project name "Acme Corp"; path `<workspace>/loam/`. Builder-refines on friction.
- Programme AC: AC.OSS.5 (residuals) — `oss-v0-1-0-publish.md` §3.
- OSS-readiness audit §3 M3 + §4.7: `.scratch/claude-output/oss-readiness-audit.md`.
- Partition manifest (post-M6c): `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- Synthesis tool: `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` + `partition.py`.
- VALUE_PROPOSITION (prime objective): `docs/rebuild/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2).

---

## 1. Summary / TLDR

**M9 lands two surfaces** as a single sealed-component amendment (synthesis tool) plus a small in-place fixture refactor across components hosting personal-info markers in shipping-surface files.

**Surface A — Synth-time path substitution mechanism** in `loam.publish_framework_only.synth`. Today the tool walks the source commit's tree via `git ls-tree -r`, classifies each leaf via the partition manifest, and re-uses the *original blob SHAs* in the synthetic tree. M9 introduces a substitution pass that, for every shipping leaf whose blob content contains a known personal-info token, reads the blob, applies a textual `s/X/Y/g` substitution from a fixed table, hashes the rewritten content via `git hash-object -w`, and uses the new blob SHA in the synthetic tree.

The substitution table is owner-locked at master plan §13 D-Q.OSS.6:

| Source token | Replacement |
|---|---|
| `/Users/lukeivers/ivers-corp-pos-v2/` | `<workspace>/loam/` |
| `/Users/lukeivers/ivers-corp-pos-v2` (no trailing slash) | `<workspace>/loam` |
| `lukeivers/pos-v2` | `lukeivers/loam` |
| `Luke Ivers` (in fixture content; see §6 carve-out for load-bearing detection-pattern uses) | `Alice Anderson` |

Determinism + idempotence preserved per audit §6 risk #3: the rewrite is a fixed-table textual substitution; re-running on a synthesised tree produces an identical tree-SHA (the second pass finds nothing to substitute).

**Surface B — In-place fixture refactor** in components where the partition ships user-facing prose / docs / READMEs / test-scenario fixtures with personal-info markers that are NOT load-bearing. The refactor lands directly on canonical (not synth-time) so the fixtures read correctly to dev-tree readers and the synthesis pass becomes belt-and-braces. Files surveyed in §6 below.

**M9 surface = ~17 shipping-surface files** carrying personal-info markers post-M6c partition. Of those:
- **3** carry load-bearing canonical-path literals in test gate assertions (AG_1, BAG_5, d4_scope_binding) — these are NOT touched in-place; they exercise the dev-only gate hooks' detection of off-tree dispatches against the canonical path. **§7 finding #1** surfaces a partition completeness gap (these test files belong in `dev_only` since they test `dev_only` hooks); resolution proposed below — accept the substitution-pass mechanism handles them at synth time.
- **1** is a plist (`com.loam.memory-graphiti.plist`) — the workspace-bootstrap render path already templates this at install time per audit §AC.M3.3; verify only.
- **~13** are docs/README/runtime-doc files where in-place rename is safe.

**Hard cutover** per master plan §5 M9 row. The substitution pass becomes the canonical synthesis path; no opt-out flag.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

M9 binds to:

- **AC.OSS.5 (Documentary rebrand complete)** — programme AC; M9 closes the residual personal-info markers per master plan §3 AC.OSS.5 verification step ("grep for `pos-v2`, `pOS v2`, `POS_V2_`, `pos.v2`, `~/.pos/`, `pos-amend`, `com.pos-v2.`, `lukeivers/pos-v2`. Allowed residuals: historical commit prose inside the canonical pos-v2 working tree (NOT in synthetic), and dev-only artefacts that are excluded by M2 partition. Public-tree count of disallowed matches: zero.").
- **AC.PO.1 (translation-burden absorption)** — a stranger cloning loam should never see canonical-host paths or owner-name-bearing tokens that imply they are reading someone else's machine state. Substitution at synth time delivers this.
- **AC.PO.2 (toolkit-primitive growth)** — the synthesis tool gains a substitution primitive that future scrub-class amendments can extend (additional tokens, additional file-type carve-outs).

Reverse trace: every M9 AC ladders up to AC.OSS.5 → AC.PO.1 + AC.PO.2.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

The substitution pass is pure git plumbing — `git hash-object -w` writes a new blob; the synth tool's existing `_write_tree_from_entries` consumes the new SHAs. No LLM in the loop (per audit §6 risk #3 — determinism invariant). No new Claude primitive composition is required because the synthesis tool itself is a non-Claude artefact (per audit §7 observation: "pos-publish-framework-only does not currently leverage any Claude primitive — this is correct"). **Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test** (translation burden): public stranger never sees canonical-host paths in docs / READMEs / runtime artefacts. Pass.
- **Harness test** (toolkit primitive): the substitution pass is a new toolkit primitive — a fixed-table textual transform applied to every shipping blob during synthesis. Future scrub-class amendments compose on it (e.g. v0.2 may add owner-name-bearing tokens beyond Luke Ivers as the project gains contributors). Pass.

**Pass.**

### Lens 3 — ODD authoring

Every AC below is outcome-shape (file-system state, blob content patterns, idempotence behaviour). Method (which exact byte offsets, which exact regex for the substitution) is the builder's call inside the AC outcome bound. The substitution table itself is owner-locked at master plan §13 D-Q.OSS.6.

**Pass.**

---

## 4. Acceptance criteria — AC.OSS-M9.*

### AC.OSS-M9.1 — Substitution table is fixed and locked in code

A constant `SUBSTITUTION_TABLE` (or equivalent) exists in `loam.publish_framework_only.synth` (or a new `substitution.py` sibling — builder's call). The table contains exactly the four entries listed in §1 above (no fewer, no more — additions require a follow-on amendment).

**Verification.** `grep -c "SUBSTITUTION_TABLE\|_substitution_table\|substitutions" framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/` returns ≥1; the table's literal entries match §1 exactly; no host-specific data outside this table.

### AC.OSS-M9.2 — Substitution pass runs AFTER the partition filter

For every leaf whose `classify_path` result is `PUBLIC_ONLY` or `DEV_AND_PUBLIC`, the substitution pass reads the blob, applies the table, writes a new blob via `git hash-object -w` IFF the substitution changed the content, and uses the rewritten SHA. For leaves classified `DEV_ONLY` / `EXCLUDED_FROM_PUBLISH` / audit-excluded, the substitution pass does NOT run (those leaves never reach the synthetic tree).

**Verification.** Test in `tests/test_AC_OSS_M9_substitution_after_partition.py`: synthesise a fixture canonical that contains both a `dev_only` blob with a substitution-token AND a `dev_and_public` blob with the same token; assert (a) the `dev_only` blob is absent from the synthetic tree, (b) the `dev_and_public` blob's tree entry SHA does NOT match the source SHA when the source carried a substitution token.

### AC.OSS-M9.3 — Idempotent on second-pass synthesis

Running the synthesis twice on the same source commit produces identical tree-SHAs. The substitution pass is purely textual; the second pass finds zero tokens to substitute (because the first pass already replaced them).

**Verification.** Test in `tests/test_AC_OSS_M9_substitution_idempotent.py`: synthesise twice on the same source SHA + manifest; assert `result1.framework_only_sha == result2.framework_only_sha` (the second call no-ops at the existing-tree-matches branch in `synthesise_framework_only`).

### AC.OSS-M9.4 — Binary-blob safety: substitution SKIPS blobs that don't UTF-8-decode

Some shipping-surface blobs may be binary (e.g. PNGs in docs/, sealed-component test artefacts). The substitution pass attempts UTF-8 decode; on `UnicodeDecodeError` it preserves the original blob SHA verbatim.

**Verification.** Test in `tests/test_AC_OSS_M9_substitution_binary_safe.py`: synthesise a fixture canonical whose `dev_and_public` set includes a blob whose first 4 bytes are `\x89PNG`; assert the synthetic tree's blob SHA for that path matches the source blob SHA exactly.

### AC.OSS-M9.5 — Fixture-refactor: cosmetic personal-info renames in non-load-bearing shipping-surface files

The following files have their personal-info markers replaced in-place on canonical (not synth-time):

- `framework/dormancy/tests/test_d10_garbage_false_positive.py` — `Luke Ivers` → `Alice Anderson`; `pOS` (in the same fixture's `kind: project` entry) → `Acme Corp` (cosmetic; matches §13 D-Q.OSS.6 ruling).
- `framework/objective-tracker/README.md`, `framework/objective-tracker/docs/overview.md`, `framework/orchestrator/docs/operations.md`, `framework/orchestrator/docs/measurement-launchd.md`, `framework/dormancy/docs/architecture.md`, `framework/memory-system/launchd/README.md`, `framework/workspace-bootstrap/README.md` — `/Users/lukeivers/ivers-corp-pos-v2` (in shell example commands) → `<workspace>/loam` (per master plan §13 D-Q.OSS.6 substitution form). The example commands now read as workspace-templated rather than canonical-host-bound.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:602` — `https://github.com/lukeivers/pos-v2` → `https://github.com/lukeivers/loam` (this is a runtime first-time-bootstrap example URL emitted to the user; the rebrand applies in-place).
- `framework/workspace-sync/src/loam/workspace_sync/canonical_cache.py:35-40` — docstring examples: `github.com/lukeivers/pos-v2` → `github.com/lukeivers/loam` (the path-parsing regex is generic; only the docstring examples carry the brand).
- `framework/workspace-bootstrap/tests/test_pos_new_workspace.py:256` — fixture URL `https://test-host/lukeivers/pos-v2-fixture` → `https://test-host/lukeivers/loam-fixture` (cosmetic; the test asserts URL parsing, not the literal owner-name).

**Verification.** After the in-place edits, `grep -rln "Luke Ivers\|/Users/lukeivers\|lukeivers/pos-v2" framework/` (excluding `dev_only`-classified subtrees + `seals/` directories + `framework/memory-system/data/`) returns ONLY:
- The 3 load-bearing test files (AG_1, BAG_5, d4_scope_binding) — these stay in canonical and are scrubbed at synth time per AC.OSS-M9.2.
- The plist (`com.loam.memory-graphiti.plist`) — its absolute paths are workspace-bootstrap-template-rendered per audit §AC.M3.3; M9 does NOT touch the source plist (§6 below).

### AC.OSS-M9.6 — Smoke-test: substitution pass produces clean synthesis on a sample subset

A smoke test (manual or scripted) synthesises a small subset of the canonical tree, blob-greps the synthetic tree for the four substitution tokens; result is zero matches. (M11 dry-run runs the full synthesis; M9's smoke test exercises the substitution mechanism on a reduced surface.)

**Verification.** Inline in `tests/test_AC_OSS_M9_substitution_smoke.py`: builds a fixture canonical that mirrors a reduced version of the live canonical surface (~5 files chosen to span doc / source / test / README); synthesises; greps the synthetic blobs; asserts zero hits on `Luke Ivers`, `lukeivers/pos-v2`, `/Users/lukeivers/ivers-corp-pos-v2`.

### AC.OSS-M9.7 — Existing partition + synthesis tests continue to pass

The M2-authored test suite (`test_AC_OSS_3_*.py` + `test_AC_SFR_2_synthesis_pipeline.py`) plus the M6a-authored `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` continue to pass post-M9 (the substitution pass is additive; existing partition / promotion / idempotency invariants unaffected).

**Verification.** `pytest framework/tools/pos-publish-framework-only/tests/` exits 0.

### AC.OSS-M9.S — Sealed-component fence

The sealed-component fence is the sum of:
1. `framework/tools/pos-publish-framework-only/` — substitution-pass extension + tests.
2. `framework/dormancy/tests/test_d10_garbage_false_positive.py` — single-line fixture rename.
3. `framework/objective-tracker/` — in-place doc/README rename.
4. `framework/orchestrator/docs/` — in-place doc rename (2 files; no source/test changes).
5. `framework/dormancy/docs/architecture.md` — single-line rename (already in fence component #3? — actually framework/dormancy fence overlap; treat as fence component #3 wrapping all `framework/dormancy/`).
6. `framework/memory-system/launchd/README.md` — single-line README rename.
7. `framework/workspace-bootstrap/` — README.md + new_workspace.py (line 602) + tests/test_pos_new_workspace.py (line 256) — in-place rename.
8. `framework/workspace-sync/` — single-file docstring rename in `canonical_cache.py`.

**Sealed-component count:** ~7 components + 1 tool — verify HC#4 byte-content sample status: NO RETIRE-AND-REBASELINE expected (M9 edits are content-rewrites at known locations, not file moves; the synthesis-tool edits are additive — new module / new tests — not edits to HC#4-sampled paths).

`loam amend apply` runs BEFORE seal commit (per dispatch §Constraints; dispatch reminds: post-M6b.1 the binary lives at `plugins/dev-sdlc/tools/loam-amend/`).

---

## 5. Hard constraints (M9-specific; series-wide constraints from master §5/§7 inherit)

1. **Plan-before-code** — this doc; §14 anchor present.
2. **`loam amend apply` BEFORE seal commit** — operates from `plugins/dev-sdlc/tools/loam-amend/` post-M6b.1.
3. **No `git commit --amend`** — corrective commits are NEW commits per `feedback_no_amend_in_agent_dispatches`.
4. **AC.OSS-M9.S seal-diff fence narrowed** to the components named in §4 AC.OSS-M9.S above.
5. **Hard cutover** — substitution pass is the canonical synthesis path post-M9; no flag to disable.
6. **Determinism + idempotence** preserved (AC.OSS-M9.3 + AC.OSS-M9.4).
7. **No third-party deps** — substitution pass uses stdlib only (`subprocess` for `git hash-object -w` is already available; UTF-8 decoding is stdlib).
8. **No edit to the substitution table beyond the four entries in §1** without halt-and-surface (AC.OSS-M9.1).

---

## 6. Out of scope (named explicitly per ODD §2.5)

- **The plist (`framework/memory-system/launchd/com.loam.memory-graphiti.plist`) is NOT touched in M9.** Per audit §AC.M3.3, the plist is workspace-bootstrap-rendered at install time via template substitution; the source plist's hardcoded paths exist for the canonical install on the build machine. **§7 finding #2** verifies the workspace-bootstrap template path is healthy; if it's not, that's a separate amendment (out of M9 scope).
- **The 3 load-bearing test files (`test_AC_AG_1_wrong_wd_dispatch.py`, `test_AC_BAG_5_wrong_tree_write.py`, `test_d4_scope_binding.py`) are NOT touched in-place.** They assert the gates' canonical-path detection patterns — substituting them in-place breaks the actual semantic. The substitution pass runs at synth time and rewrites them in the public artefact ONLY; canonical tests continue to assert the canonical-path literal so they keep working.
- **Partition manifest reclassification of gate-test files to `dev_only`** (the partition completeness gap surfaced at §7 finding #1) — proposed for a follow-on amendment, not M9. M9's substitution pass handles the synthesis output regardless of where the test files classify.
- **Memory-system launchd label `com.loam.memory-graphiti` remnants** — per master plan §5 task #16 (M1c-corrective programme) — separate amendment.
- **Memory-system code fix** (graceful-fallthrough CDC application; task #18) — separate amendment.
- **Running the M11 synthesis dry-run** — that's M11's job; M9 only verifies the substitution mechanism on a smoke-test sample.
- **Adding owner-name-bearing tokens beyond Luke Ivers** (e.g. owner-personal-life context, telegram handles, Gmail addresses) — none surfaced in shipping-surface files per the audit. If M9's builder finds new tokens during the build, halt and surface (master plan §8 trigger 11).
- **Contribution-attribution rebrand** (Co-Authored-By trailers in seal commits) — handled at M11/M12 publish step (squashed initial commit prose is owner-ruled at G3).

---

## 7. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface gaps the audit / master plan didn't predict.

1. **Partition completeness gap: gate-test files in `dev_and_public` while gate-source files are `dev_only`.** Post-M6b.0 + M6c, gate-hook source files (`agent_guard.py`, `bash_guard.py`, `objective_binding_gate.py`, `tdd_guard.py`, `dispatch_setup_hook.py`) live in `plugins/dev-sdlc/hooks/` (classified `dev_only` via the `plugins/dev-sdlc/**` glob). Their test files live in `framework/hands-off-lifecycle/tests/test_AC_AG_*.py` + `test_AC_BAG_*.py` — these classify `dev_and_public` via the `framework/hands-off-lifecycle/**` glob. Test files import the moved gate modules via a sys.path probe (`PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"`); when the public artefact is synthesised, `plugins/dev-sdlc/` is dropped, so the test imports fail in the synthetic tree's pytest run. **Resolution proposed (NOT in M9):** a follow-on partition-classification amendment (call it M9.1 or fold into M11.dry-run findings) reclassifies the gate-test files to `dev_only` (or extracts `_gate_helpers.py` and the gate-test files to the plugin in a follow-on plugin-extraction amendment). **For M9 specifically:** the substitution pass handles the canonical-path literals in those test files at synth time per AC.OSS-M9.2 + AC.OSS-M9.6, so M9's deliverable is correct even if the partition gap remains. **NOT a halt** — surfaced for the next-amendment register.

2. **Plist source paths are absolute on the build machine.** `framework/memory-system/launchd/com.loam.memory-graphiti.plist` carries 4 hardcoded paths under `/Users/lukeivers/ivers-corp-pos-v2/...`. Per audit §AC.M3.3 the plist is workspace-bootstrap-rendered at install time via template substitution. **Verification needed (NOT a halt for M9):** confirm the current rendering path produces a plist with workspace-relative paths post-install. If the source plist's content ships verbatim in the synthetic tree, the substitution pass under AC.OSS-M9.2 rewrites the absolute paths to `<workspace>/loam/...` — which is the correct synthetic-tree state regardless of whether workspace-bootstrap re-renders post-install on the public artefact. **NOT a halt.**

3. **Existing fixture name collisions: `Acme Corp` and `Alice` are already in use, and they don't collide with M9's new uses.** `framework/workspace-bootstrap/tests/test_AC39_5_non_dev_workspace_user_supplied.py` uses `Acme Corp Workspace Value Proposition` as a non-dev-mode workspace fixture — orthogonal to M9's `Acme Corp` cosmetic name in the dormancy `kind: project` field. `framework/observability-aggregator/` uses `Alice` as a memory-extraction example name — orthogonal to M9's `Alice Anderson` person-fixture in the dormancy test. **NO collision; NOT a halt.** The pre-existing fixtures show the master plan §13 D-Q.OSS.6 ruling is already aligned with codebase precedent.

4. **No new audit-table entries needed beyond the four in §1.** Grep across all shipping-surface files (excluding `dev_only`-classified subtrees + `seals/` + gitignored `data/` + `personas/`) found ZERO additional owner-name-bearing tokens, ZERO additional canonical-host paths beyond those in §1, ZERO additional URL refs. **NOT a halt** — confirms master plan §13 D-Q.OSS.6 audit was complete.

5. **`pOS` literal in dormancy test_d10:37** — a memory-extraction example uses `{"name": "pOS", "kind": "project"}`. This is a fixture-decorative `pOS` reference (not load-bearing). Per master plan §13 D-Q.OSS.6 ruling on project-name fixtures (`Acme Corp` is the recommended replacement), the rename to `Acme Corp` is in-scope at AC.OSS-M9.5 above. **NOT a halt** — handled by the AC.

6. **No ODD §2.5 violations encountered in surrounding code/docs during the M9 audit.** The code surface targeted by M9 (synthesis tool extension + ~17-file in-place fixture refactor) is purely additive / cosmetic; no silent except branches, no fallthrough-without-detection patterns, no test-only-callers. **NOT a halt.**

**Halt summary.** None of the above triggers a halt. Findings 1 + 2 + 5 are surfaced for the next-amendment register and folded into AC.OSS-M9.5 / §6 out-of-scope as appropriate. The plan is authorised to proceed.

---

## 8. Implementation order (suggested — builder's call to refine)

1. **Author + run new substitution-pass tests** (test-first or test-during; builder's call):
   - `tests/test_AC_OSS_M9_substitution_after_partition.py` — fixture-canonical with `dev_only` + `dev_and_public` blobs both carrying tokens; assert only `dev_and_public` blob is rewritten.
   - `tests/test_AC_OSS_M9_substitution_idempotent.py` — two-pass synthesis; assert identical tree-SHAs.
   - `tests/test_AC_OSS_M9_substitution_binary_safe.py` — binary blob in `dev_and_public`; assert SHA preserved.
   - `tests/test_AC_OSS_M9_substitution_smoke.py` — reduced-canonical synthesis; assert zero hits on the four tokens.
2. **Author the substitution module** (`substitution.py` sibling of `synth.py`, or an inline `_apply_substitutions` helper — builder's call). Public surface: `apply_substitutions(blob_content: str | bytes, table: SubstitutionTable) -> tuple[str | bytes, bool]` (returns `(rewritten, changed)`).
3. **Wire substitution into `_build_synthetic_tree`** — between the `is_publishable` check and the `_LeafEntry` construction, call `apply_substitutions` on the leaf's blob content; if changed, write a new blob via `git hash-object -w` and use the new SHA.
4. **Run the existing test suite** to confirm AC.OSS-M9.7 (no regression). Any failure: halt-and-surface.
5. **In-place fixture refactor** — Surface B per AC.OSS-M9.5. Hand-edits across the ~13 files:
   - `framework/dormancy/tests/test_d10_garbage_false_positive.py:37`.
   - `framework/objective-tracker/README.md` + `docs/overview.md`.
   - `framework/orchestrator/docs/operations.md` + `measurement-launchd.md`.
   - `framework/dormancy/docs/architecture.md`.
   - `framework/memory-system/launchd/README.md`.
   - `framework/workspace-bootstrap/README.md` + `src/loam/workspace_bootstrap/new_workspace.py:602` + `tests/test_pos_new_workspace.py:256`.
   - `framework/workspace-sync/src/loam/workspace_sync/canonical_cache.py:35-40` (docstring).
6. **Run touched-component pytest** (per `feedback_amendment_dispatch_speedups` — narrow test scope, skip pre-seal full repo-wide rerun). Touched components per §4 AC.OSS-M9.S: `pos-publish-framework-only`, `dormancy`, `objective-tracker`, `orchestrator`, `memory-system`, `workspace-bootstrap`, `workspace-sync`.
7. **Feature commit** carrying the substitution-pass extension + fixture refactor.
8. **`loam amend apply`** (operates from `plugins/dev-sdlc/tools/loam-amend/` post-M6b.1) — apply commit per CDC.
9. **Seal commit** per repo convention (CDC `commit-ladder.md`); fence per §4 AC.OSS-M9.S.
10. **Post-build verification** (smoke test substitution-pass on ~5-file subset; manual or scripted; AC.OSS-M9.6 + the synth-output blob-grep check).
11. **§14 method-decision register** filled in this plan-doc post-build.

Estimated wall-clock: 10–25 min calibrated band per recent amendments (rubric midpoint 30; M5/M6a/M6b.0/M6b.1/M6c calibration). Extension-style amendments tend to land in the lower half of the band when ACs are already authored.

---

## 9. Backwards-compat verification (per amendment, post-build — placeholder)

To be filled by the builder post-build. Each entry verifies:

- All pre-existing tests pass post-amendment (especially `test_AC_OSS_3_*` + `test_AC_SFR_2_synthesis_pipeline` + `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin`).
- Touched-component pytest passes for the ~7 components in the §4 AC.OSS-M9.S fence.
- HC#4 sample status — NO RETIRE-AND-REBASELINE expected (no file moves, no edits to HC#4-sampled paths).
- HC#3 binding analogue — no new third-party deps (substitution pass is stdlib + `git hash-object -w` subprocess).

---

## 10. Risks (M9-specific)

1. **Substitution pass introduces nondeterminism.** Mitigation: AC.OSS-M9.3 (idempotent on second pass) is a hard constraint; the test asserts identical tree-SHAs across two synthesis runs.
2. **Substitution pass corrupts a binary blob.** Mitigation: AC.OSS-M9.4 (UTF-8 decode try/except — preserve original SHA on `UnicodeDecodeError`).
3. **Substitution table is incomplete and a personal-info marker leaks.** Mitigation: AC.OSS-M9.6 smoke test plus M11.dry-run review-circle audit. Fold-back amendment if M11 surfaces leaks.
4. **In-place fixture refactor breaks an existing test.** Mitigation: per-component pytest before commit (§8 step 6); halt-and-surface if a fixture turns out to be load-bearing where the plan thought it cosmetic.
5. **Plist source paths drift from the workspace-bootstrap template renderer's expectations.** §7 finding #2: M9 does NOT modify the plist; if the renderer's contract is broken, that's a separate amendment.

---

## 11. References

- Master plan: `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 M9 row + §13 D-Q.OSS.6.
- Audit: `.scratch/claude-output/oss-readiness-audit.md` §3 M3 + §4.7.
- Partition manifest: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- Synthesis tool: `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/{synth.py,partition.py,cli.py}`.
- M2 sub-plan (predecessor): `docs/rebuild/plans/oss-v0-1-0-publish-partition.md`.
- M6a/M6b.0/M6b.1/M6c sub-plans: `docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin{,-m6b0,-m6b1,-m6c}.md`.
- ODD methodology: `plugins/dev-sdlc/docs/odd-methodology.md` + `odd-in-loam.md` (post-M6b.0 paths).
- Commit ladder CDC: `plugins/dev-sdlc/docs/conventions/commit-ladder.md`.
- Sealed-component invariants CDC: `plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md`.
- Graceful-fallthrough CDC (M6c): `plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md`.
- VALUE_PROPOSITION (prime objective): `docs/rebuild/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2).

---

## 12. Test breakdown (post-build — placeholder)

To be filled by the builder post-build. Expected new test files per §8 step 1:

- `tests/test_AC_OSS_M9_substitution_after_partition.py`
- `tests/test_AC_OSS_M9_substitution_idempotent.py`
- `tests/test_AC_OSS_M9_substitution_binary_safe.py`
- `tests/test_AC_OSS_M9_substitution_smoke.py`

Each test maps to the named AC (AC.OSS-M9.2 / .3 / .4 / .6 respectively).

---

## 14. Method-decision register (post-build)

To be filled by the builder post-build. Mirror M6c §14 shape: per-decision narrative with the actual choice + rationale.

Anticipated decision topics (named at plan-time so the register is forward-discoverable):

- **D-build.M9.1** — Substitution module placement: new `substitution.py` sibling vs inline helper in `synth.py`. Builder's call.
- **D-build.M9.2** — Substitution table representation: dict-of-strings vs ordered-tuple-of-tuples vs frozen dataclass. Builder's call (frozen-dataclass favoured for forward-strict schema; dict-of-strings simpler).
- **D-build.M9.3** — `git hash-object -w` invocation shape: subprocess per blob vs batched `git update-index --add --cacheinfo` + `git hash-object --stdin -w` pipeline. Builder's call (per-blob simpler; batched faster on larger trees).
- **D-build.M9.4** — Binary detection threshold: try-UTF-8-decode-or-skip vs explicit magic-byte check. Builder's call (try-decode is simpler + more general; magic-byte is defensive).
- **D-build.M9.5** — Smoke-test fixture-canonical scope: how many files mirror live canonical (5? 10?). Builder's call (5 favoured for fast test).
- **D-build.M9.6** — In-place rename mechanic: hand-edits vs scripted `sed -i`. Builder's call (scripted favoured if all 13 files have unambiguous one-line replacements; hand-edit if any file has ambiguous context).

### Commit SHAs

- M9 sub-plan commit: `0364ec9` (this plan-doc).
- M9 feature commit: `3ae817c` (substitution module + 4 tests +
  synth.py extension + 12-file in-place fixture refactor).
- M9 manifest commit: `d43cc28` (amendment #91 manifest authoring).
- M9 apply commit: `3e6ac88` (`loam amend apply` — sidecars bumped to
  BASELINE 14609d8 + allowed_prefixes extended).
- M9 corrective commit: `aa647c4` (workspace-sync test_AC_D_5_5_1
  tightened to reflect post-M1g + M6b.0 + M6b.1 surface — pre-existing
  stale assertion surfaced as HSF#1 in §7 + resolved in-band; doc-
  only test-text update; no behaviour change).
- M9 seal commit: `2161cb1` (`loam amend seal --scoped-sweep`; 7-
  component fence + HOL narrative anchor; touched-component sweep all
  green; cross-component sweep scoped to manifest-listed components
  per `--scoped-sweep`).

### Method-decision register narratives

**D-build.M9.1 — Substitution module placement: new sibling module.**
Authored `loam.publish_framework_only.substitution` as a new sibling
of `synth.py` rather than inlining helpers in `synth.py`. Rationale:
(a) clean public surface — `apply_substitutions` + `SubstitutionResult`
+ `SUBSTITUTION_TABLE` are testable in isolation without spinning up
a fixture canonical; the unit tests in `test_AC_OSS_M9_substitution_binary_safe.py`
exercise the substitution function directly on PNG bytes without git
plumbing. (b) Single-responsibility split — `synth.py` owns git
plumbing + tree assembly; `substitution.py` owns the textual rewrite.
(c) Future-extensibility — additional substitution-rules / additional
table entries land in `substitution.py` without `synth.py` churn.

**D-build.M9.2 — Table representation: tuple-of-tuples.**
`SUBSTITUTION_TABLE: tuple[tuple[str, str], ...]` chosen over
dict-of-strings or frozen dataclass. Rationale: (a) tuple ordering is
stable across Python versions (dict ordering is too in 3.7+, but
frozen tuple is the explicit "ordered + immutable" shape). (b)
ordering matters: the no-trailing-slash `/Users/lukeivers/ivers-corp-pos-v2`
substitution would also match inside paths that DO carry the trailing
slash; tuple iteration order ensures the trailing-slash entry applies
first (defensive — both produce the same result, but explicit
ordering documents intent). (c) Equality semantics for testing — the
unit test asserts `len(SUBSTITUTION_TABLE) == 4` + membership of the
4 source tokens; tuple-of-tuples makes this trivial.

**D-build.M9.3 — `git hash-object` invocation: per-blob subprocess.**
Each rewritten blob calls `subprocess.run(["git", "hash-object", "-w",
"--stdin"], input=content)` — a separate subprocess per shipping blob
that needed substitution. Rationale: (a) simplicity — the existing
`_git` helper in `synth.py` was modeled on per-call subprocess; the
new `_hash_object_w` helper extends that pattern. (b) Most shipping
blobs do NOT need substitution (only ~17 shipping-surface files in
the entire pos-v2 tree carry the four tokens — verified at plan-
time); the per-blob subprocess cost is negligible at v0.1.0 surface
size. (c) Profiling-driven optimisation can land later if M11 dry-run
shows the substitution pass dominates synthesis wall-clock.

**D-build.M9.4 — Binary detection: try-UTF-8-decode.**
`apply_substitutions` attempts `blob_content.decode("utf-8")` and
catches `UnicodeDecodeError` to flag binary blobs (returns
`SubstitutionResult(content=blob_content, changed=False, binary=True)`).
Rationale: (a) more general than magic-byte sniffing — catches binary
PNG / JPG / WAV / unknown-format bytes without enumerating known
binary types. (b) UTF-8 is the dominant text encoding in pos-v2's
tree (Python source, Markdown, YAML); the false-positive rate is
zero for tracked text content. (c) The integration test
(`test_AC_OSS_M9_substitution_binary_safe.py::test_AC_OSS_M9_4_synth_preserves_binary_blob_sha`)
verifies a real PNG blob preserves its source SHA in the synthetic
tree.

**D-build.M9.5 — Smoke-test fixture scope: 5 files spanning 4 surface
shapes.** The smoke test
(`test_AC_OSS_M9_substitution_smoke.py::test_AC_OSS_M9_6_smoke_synthesis_carries_zero_substitution_residuals`)
builds a fixture canonical with 5 token-bearing files (1 Python
source, 1 README with shell-example, 1 test fixture, 1 CLAUDE.md, 1
README) + 1 docs/positioning.md without tokens. Rationale: (a) fast
test runtime — the fixture canonical is small enough that `git init
--initial-branch=pos-v2 + git add + git commit + synthesise + ls-tree
+ cat-file blob × N` runs in <1s. (b) covers the 4 substitution-token
families: absolute path with trailing slash, absolute path without
trailing slash, GitHub URL, person-name. (c) positive sanity — the
test asserts AT LEAST one synthesised blob carries replacement tokens
(catches the failure mode where the substitution pass is wired but
silently no-ops).

**D-build.M9.6 — In-place rename mechanic: targeted Edit calls per
file.** Surface B's 12-file in-place refactor used per-file `Edit`
tool calls with `replace_all=true` on context-stable token forms,
rather than a scripted `sed -i` pass. Rationale: (a) per-file context
inspection — `framework/workspace-bootstrap/README.md` carries 3
distinct path-references (a local-canonical example, a URL example, a
re-scaffold example); each needed independent verification that the
substitution made sense in context. (b) `replace_all=true` was safe
on docs/README files where the source token was unambiguous; case-by-
case decision per file. (c) the substitution pass at synth time is
the belt-and-braces — if any in-place rename was missed at M9, the
synth-time pass catches it in the public artefact.
