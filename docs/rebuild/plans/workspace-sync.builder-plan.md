# workspace-sync — builder-plan

**Authored:** 2026-04-26 by build-agent (workspace-sync sealed-component
amendment dispatch).
**Companion plan:** `docs/rebuild/plans/workspace-sync.md`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline:** HEAD `caafdf0` (the `chore(self-upgrade,
tools): release manifest pos-v2-v0.2.0 + upgrade-merge-resolver
factory` commit; the SHA-record commit immediately preceding this
amendment's first touch). Highest amendment number = 55; next free =
**56**.

This builder-plan captures (a) the **method choices** (D-build.x)
within the AC outcome bounds, (b) the **§2.5 reverse-direction
trace** (one row per code path / branch → AC), and (c) the **build
sequence** the agent will execute.

Per ODD §2.5: AC text is WHAT; this section is HOW. The plan-doc's
ACs are not method-coupled, so the choices below are reversible
within their AC's outcome bound.

---

## Section A — Method choices (D-build.x)

### D-build.0 — CLI console-script form (cross-cutting)

**Choice.** Ship `workspace-sync` as a NEW console_script
`pos-sync = workspace_sync.cli:main` (hyphenated) declared in
`workspace-sync/pyproject.toml`. The plan/dispatch say "`pos sync`";
existing convention across pos-v2 (per `pos-amend`, `pos-bootstrap`,
`pos-obs`, `heavy-b-migrate`) is hyphenated component-prefixed
console_scripts. The single dispatch alias `pos workspace-sync`
becomes `pos-workspace-sync` mapped to the same `main()` entry.

**Why.** Hard Constraint #1 forbids edits to `self-upgrade/`. The
existing `pos = self_upgrade.cli:main` console_script lives in
`self-upgrade/pyproject.toml`; adding a `pos sync` subcommand would
mean editing self-upgrade — a halt-trigger #4 condition. The
hyphenated form is shell-equivalent: `pos-sync --canonical X`
satisfies "operator types `pos<delim>sync ...`" while keeping the
fence intact. Hard Constraint #5 ("`pos sync` CLI is a NEW entry
point") is satisfied by a new `pos-sync` console_script.

The dispatch's textual `pos sync` is interpreted as the operator-
visible verb shape, with the understanding that `pos-sync` is the
shell-spelling under pos-v2's component-binary convention. The
plan-doc §11 D-1 LOCKED ruling stands semantically: `pos-sync` is
the short verb; `pos-workspace-sync` is the alias for unambiguity.

**ODD reverse trace target:** `cli.py::main` and the pyproject
`[project.scripts]` block both → AC.WS.1.

### D-build.1 — Salvage-as-is lifts (file-copy)

**Choice.** Copy these files verbatim from `self-upgrade/src/
self_upgrade/` to `workspace-sync/src/workspace_sync/`:

1. `merge_resolver.py` → `workspace-sync/src/workspace_sync/
   merge_resolver.py` (zero edits; ~190 LOC). Resolver Protocol +
   ResolverBudget + BudgetExhausted + ResolverFailure +
   MergeVerdict + build_prompt + MergeResolver.
2. `sync_protected.py` → `workspace-sync/src/workspace_sync/
   sync_protected.py` (zero edits; ~170 LOC). FileClass +
   SyncProtectedRule + SyncProtected + FRAMEWORK_FLOOR + classify +
   load/save/write_default helpers.
3. `templates/sync-protected.default.yaml` →
   `workspace-sync/templates/sync-protected.default.yaml` (zero
   edits; 30 LOC).
4. `observability.py` → `workspace-sync/src/workspace_sync/
   observability.py` with TWO targeted renames: `_TRACER_NAME =
   "pos.self_upgrade"` → `"pos.workspace_sync"`; module docstring's
   span-name list updated to reference `pos.sync.*` semantics. ~55
   LOC. (This is a salvage-with-edits but the edit is mechanical.)

**Why.** GG verdict per §9.1: "salvage-as-is" — these files are
architecture-neutral (merge_resolver, sync_protected) or workspace-
shaped from day one. The clause-(h) primitives sit cleanly above
the A-vs-B execution-path split. Vendoring (per Hard Constraint
#11) means workspace-sync owns its own copy with no
`import self_upgrade` dependency.

### D-build.2 — `tools/upgrade-merge-resolver` re-vendor

**Choice.** Re-vendor the resolver client at
`workspace-sync/src/workspace_sync/_resolver_client.py` instead of
keeping it under `tools/upgrade-merge-resolver/`. The lifted file
is `tools/upgrade-merge-resolver/src/upgrade_merge_resolver/
__init__.py` rebranded to import from `workspace_sync.merge_resolver`
(internal import) instead of `self_upgrade.merge_resolver`.

**Why.** Hard Constraint #11 (salvage-by-COPY-not-import). Keeping
the tool reachable from workspace-sync would create a runtime
dependency on `self_upgrade.merge_resolver` (since
`upgrade_merge_resolver` imports from it) — which is the exact
A↔B coupling the architecture relock forbids. Re-vendoring is
~270 LOC duplicated; the cost is acceptable per the plan's
explicit guidance ("both components carry their own copy of the
merge-resolver primitives").

`tools/upgrade-merge-resolver/` remains untouched (per Hard
Constraint #1). The factory function exposed by
workspace-sync is named `build_merge_resolver()` (same name) so
external `--merge-resolver-module` wiring stays consistent.

### D-build.3 — `conflict_report.py` lift (whole module)

**Choice.** Lift `self-upgrade/src/self_upgrade/conflict_report.py`
WHOLE (~273 LOC) to `workspace-sync/src/workspace_sync/
conflict_report.py`. Keep the existing schema (Resolution enum
including INFERRED_*, ConflictEntry with rationale/confidence/
user_override/override_rationale, ConflictChangeKind, ConflictReport
with sorted_low_confidence_first/inferred_entries/has_pending +
load/save). The schema's `upgrade_tag` field on ConflictReport is
RENAMED to `sync_ref` for accuracy under B's commit-SHA-or-ref
semantic. The `prior_tag` field is RENAMED to `prior_ref` (still
optional, still nullable).

**Why.** GG plan §9.1 row says builder's call between WHOLE and
SUBSET; recommendation is WHOLE. The Resolution enum + ConflictEntry
shape is exactly what AC.WS.4 + AC.WS.5 + AC.WS.9 + AC.WS.12 demand
(no value authorising overwrite of Class-A — the enum itself
structurally enforces this since the Class-A KEEP_LOCAL branch is
the only resolution applied to a Class-A entry, never a
INFERRED_ACCEPT_CANONICAL or ACCEPT_UPSTREAM). `_reject_skipped`
validator carries forward (clause-g enforcement preserved).

The rename `upgrade_tag` → `sync_ref` is needed to stop
audit-yaml-on-disk readers having to translate. Workspace-sync's
audit ships under `<workspace>/.pos/sync/<ref>/audit.yaml` per
AC.WS.5; the YAML's top-level `sync_ref:` field is more honest than
`upgrade_tag:` for that path.

### D-build.4 — `state.py` lift with field rename + path migration

**Choice.** Lift `self-upgrade/src/self_upgrade/state.py` (~148 LOC)
to `workspace-sync/src/workspace_sync/state.py`. Edits:

1. Rename `UpgradeStatus` → `SyncStatus` (class name + docstring).
2. Rename `StateRecord.upgrade_tag` field → `sync_ref`.
3. `state_yaml_path(workspace_root)` returns
   `<workspace_root>/.pos/sync/state.yaml` (was
   `<workspace_root>/.pos/upgrade/state.yaml`).
4. `audit_yaml_path(workspace_root, ref)` returns
   `<workspace_root>/.pos/sync/<ref>/audit.yaml` (was
   `<workspace_root>/.pos/upgrade/<tag>/audit.yaml`).
5. `make_state_record` parameter `upgrade_tag` → `sync_ref`.

**Why.** AC.WS.5 mandates the new audit path
(`<workspace>/.pos/sync/<ref>/audit.yaml`). AC.WS.8 mandates
state.yaml under the same `.pos/sync/` namespace. The rename
follows naturally. Self-upgrade's `state.py` keeps the old
`upgrade_tag` / `.pos/upgrade/` shape (Hard Constraint #1).

### D-build.5 — `canonical.py` lift with manifest scrub

**Choice.** Lift `self-upgrade/src/self_upgrade/canonical.py`
(~104 LOC) to `workspace-sync/src/workspace_sync/canonical.py`.
Edits:

1. Drop the `from .manifest import Manifest, load_manifest` import
   (manifest module is not lifted).
2. Drop the `Manifest` field on `StagingResolution`; rename to
   `CanonicalResolution(canonical_path: Path, ref: str)`. The
   "staging" framing collapses because under B the canonical tree
   IS the at-rest comparison source — not a pre-unpacked staging
   directory.
3. Drop `default_manifest_path` (no manifest under B).
4. Drop the `if manifest.release_tag != tag:` validator (manifest
   gone).
5. Rename function `resolve_canonical_to_staging` →
   `resolve_canonical(canonical_path: Path, *, ref: str = "HEAD") ->
   CanonicalResolution`.
6. Add the `git rev-parse <ref>` resolution step: if
   `ref == "HEAD"` (default), shell out to `git -C <canonical_path>
   rev-parse HEAD` to get the actual SHA so the audit/state records
   carry a stable identifier rather than the symbolic `HEAD`.
7. Keep the `canonical_path.exists()` + `canonical_path.is_dir()` +
   `canonical_path / ".git"` existence checks. Raise
   `CanonicalPullError` on each failure.

**Why.** Per plan §9.1 row "Drop manifest validator; drop
default_manifest_path; rename tag → ref". The `git rev-parse`
addition (D-build.5.6) is the minimum-stamping shape so AC.WS.8's
state.yaml has a stable `sync_ref` value to key idempotency
against; otherwise re-running with `--ref HEAD` after canonical
advances would not detect the advance.

### D-build.6 — `merge_helper.py` (lift `resolve_clause_h_inferred` + helpers)

**Choice.** Lift the four functions from
`self-upgrade/src/self_upgrade/clause_checks.py` —
`_read_text_or_none`, `_verdict_to_resolution`,
`resolve_clause_h_inferred`, `check_clause_h` — to a new module
`workspace-sync/src/workspace_sync/merge_helper.py`.

Edits during lift:

1. Rename `resolve_clause_h_inferred` → `resolve_inferred_conflicts`
   (drops the clause-h naming since workspace-sync doesn't carry
   the seven-clause acceptance contract).
2. Rename `check_clause_h` → `check_inferred_resolution_invariants`.
3. The function's `report.upgrade_tag` reference becomes
   `report.sync_ref` (per D-build.3 rename).
4. The `audit_yaml_path(workspace_root, report.upgrade_tag)` call
   becomes `audit_yaml_path(workspace_root, report.sync_ref)`.
5. The merged-content drop path
   `workspace_root / ".pos" / "upgrade" / report.upgrade_tag /
   "merged"` becomes `workspace_root / ".pos" / "sync" /
   report.sync_ref / "merged"`.
6. The `OTel span` names migrate from `pos.upgrade.merge_gate.*`
   to `pos.sync.merge_gate.*` (per AC.WS.11).
7. The OTel attributes' key namespace migrates from
   `pos.upgrade.merge_gate.*` to `pos.sync.merge_gate.*`.
8. Drop the `INFERRED_RESOLUTIONS` import path adjustment
   (it lives in the lifted `conflict_report.py`).
9. Drop the `from .aggregator_probes import ...` and
   `from .manifest import ...` and `from .paths import Paths`
   imports — those modules are not lifted.

**Hidden-coupling verification (plan §10 trigger 6):** the lifted
helper functions do NOT reference `paths.current_link`, `paths.history`,
`Paths`, or any `live_root` derivation. Verified by reading
clause_checks.py lines 355–634 — the only Paths usage in the
file is `check_clause_f`'s `paths.history_dir_pre(tag)` call
(NOT lifted — that's a self-upgrade-only clause). Confirmed clean.

**Why.** The lifted functions implement AC.WS.2 (Class-A
preservation), AC.WS.3 (Class-B operator preference), AC.WS.4
(Class-C inference), AC.WS.6 (budget halt), AC.WS.11 (OTel
spans), and AC.WS.12 (fail-closed) all in one ~200-LOC helper.
Per GG verdict + plan §9.1, the helper is architecture-neutral;
caller-side rebadging is sufficient.

### D-build.7 — Authored-fresh `cli.py`

**Choice.** Author `workspace-sync/src/workspace_sync/cli.py`
fresh. Argparse:

- `pos-sync` (or via `pos-workspace-sync` alias) is the prog.
- Positional verb is implicit (top-level entry, no subcommand —
  the binary IS the verb).
- `--canonical <path>` (required).
- `--ref <commit-or-tag>` (optional, default `"HEAD"`).
- `--workspace <path>` (optional, default `Path.cwd()`).
- `--dry-run` (optional; render planned operations + exit).
- `--merge-resolver-module <pkg.mod[:factory]>` (optional;
  default `"workspace_sync._resolver_client"` factory
  `build_merge_resolver`).
- `--budget-tokens <N>` (optional cumulative ceiling override).
- `--auto-accept` (optional; opt-in fast-path past human
  confirmation when all confidences ≥ floor).
- `--confidence-floor <0.0-1.0>` (optional; default 0.90 per
  BB D-2 ruling).

Workspace-root derivation per Hard Constraint #12:
1. If `--workspace` supplied AND directory exists, use it.
2. Else if `Path.cwd()` contains `.pos/sync-protected.yaml`
   (existing workspace), use it.
3. Else if `Path.cwd()` contains `.git/` (fresh first-run), use
   it.
4. Else halt with structured argparse error naming both
   fall-through conditions.

NO `paths.current_link`, NO `refuse_if_invoked_from_live_path`,
NO symlink resolution.

The `main(argv)` flow:
1. Parse args → `(canonical_path, ref, workspace_root,
   dry_run, resolver_module, budget, auto_accept, confidence_floor)`.
2. Validate workspace-root structurally; halt-with-error if
   invalid.
3. `resolve_canonical(canonical_path, ref=ref)` → resolved_ref.
4. Seed default `sync-protected.yaml` if absent (per AC.WS.10).
5. Load `sync-protected.yaml` (validates framework floor; halt
   on missing-floor per AC.WS.10).
6. Read state.yaml; if it covers `(workspace_root, resolved_ref)`
   already-applied AND no workspace perturbation, no-op return
   (per AC.WS.8 idempotency).
7. Run conflict-detection (D-build.8).
8. Build resolver from `--merge-resolver-module`.
9. Stage canonical-clean writes to
   `<workspace>/.pos/sync/staging/<ref>/` (per D-build.9).
10. Invoke `resolve_inferred_conflicts(...)` to run A/B/C
    resolution + write audit + state.
11. If dry_run → print plan, no apply.
12. Else if auto_accept and all confidences ≥ floor → apply.
13. Else surface audit summary + prompt; on confirm, apply; on
    reject, discard staging.
14. On any halt (BudgetExhausted / ResolverFailure / unknown
    failure), drop staging atomically; audit + state already
    persisted by the helper's finally-block.

**Why.** This is the substrate AC.WS.1, AC.WS.7, AC.WS.10,
AC.WS.12 each pin a corner of. The workspace-root derivation
per Hard Constraint #12 is structurally enforced; the dry-run /
auto-accept axes give operator discretion without weakening
fail-closed semantics.

### D-build.8 — Authored-fresh `conflict_detection.py` (B-shape)

**Choice.** Author `workspace-sync/src/workspace_sync/
conflict_detection.py` fresh. Mechanism:
**git diff via subprocess shellout** (NOT `git merge-file`, NOT
`dulwich`). The function `detect_b_shape_conflicts(canonical_path,
ref, workspace_root, sync_protected) -> ConflictReport`.

Mechanism detail:
1. `git -C <canonical_path> ls-tree -r --name-only <ref>` → set
   of canonical paths at the resolved ref.
2. For each canonical path, compute three SHAs:
   - canonical SHA = `git -C <canonical> hash-object <ref>:<path>`
     (or via `git cat-file blob <ref>:<path>` + sha256 — note:
     git uses sha1 for tree objects, but we want sha256 for
     audit consistency. Approach: `git -C <canonical> show <ref>:<path>`
     piped through sha256_of_text helper.)
   - workspace SHA = sha256_of_file(workspace_root/path) if exists,
     None otherwise.
   - prior SHA = workspace_state.yaml's last-recorded canonical SHA
     for the path, if any (idempotency anchor; None on first sync).
3. Classify each:
   - canonical_sha == workspace_sha → unchanged (no entry).
   - workspace_sha is None (workspace lacks file) AND
     canonical_sha new vs prior → clean addition (no conflict
     entry — falls into staging-clean writes).
   - canonical_sha == prior_sha (canonical unchanged) AND
     workspace_sha differs → workspace-only modification (no
     conflict entry).
   - canonical_sha != prior_sha AND workspace_sha == prior_sha →
     clean upstream update (no conflict entry; staging applies).
   - canonical_sha != prior_sha AND workspace_sha != prior_sha →
     CONFLICT (both-sides changed). Build ConflictEntry with
     `change_kind=UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED`.
4. Class-A paths (per `sync_protected.classify(path) ==
   FileClass.A`) generate ConflictEntries with
   `resolution=KEEP_LOCAL` directly — never enter the resolver.
5. Class-B paths generate ConflictEntries with PENDING resolution;
   the helper's Class-B branch resolves at execution time.
6. Class-C paths generate ConflictEntries with PENDING resolution;
   the helper's Class-C branch invokes the resolver.

The function returns the populated `ConflictReport` with
`sync_ref=<resolved_ref>`, `prior_ref=<state.last_ref or None>`,
`detected_at=<iso>`, `conflicts=<entries>`.

**Why git-shellout vs alternatives.** Per plan Hard Constraint #2
(no new third-party dep), `dulwich` is forbidden. `git merge-file`
would give us 3-way merge text, but B's resolver wants the
canonical/workspace text pair (D-build.6 reads them via
`_read_text_or_none(canonical_root/path)` directly). Shellout to
`git ls-tree` + `git show` gives clean canonical-text reads
without staging copies. Mechanism is stdlib + git binary
(already required to be present for any pos-v2 development env).

### D-build.9 — Authored-fresh `staging.py`

**Choice.** Author `workspace-sync/src/workspace_sync/staging.py`
fresh. Three primitives:

1. `stage_canonical_clean_writes(canonical_path, ref,
   workspace_root, ref_stamp, paths_to_apply) -> Path` — copies
   each canonical-side file (`git show <ref>:<path>` text) to
   `<workspace>/.pos/sync/staging/<ref_stamp>/<path>`. Returns
   the staging root.
2. `stage_resolved_content(staging_root, path, content) -> None` —
   writes resolver-merged content to the staging tree under the
   same path.
3. `apply_staging_atomically(staging_root, workspace_root) ->
   None` — copies every file in the staging tree to the workspace,
   preserving directory structure. Single-pass apply: each file
   write is an atomic rename within the same filesystem
   (`tempfile.mkstemp` + `os.replace`). Class-A paths are NEVER
   present in the staging tree (they were filtered at conflict-
   detection time), so apply cannot overwrite them.
4. `discard_staging(staging_root) -> None` — `shutil.rmtree`.

**Why.** AC.WS.7 demands stage-then-atomic-accept; the staging
root sits OUTSIDE the workspace's framework tree (`.pos/sync/
staging/` is itself Class-A, so workspace data loss via staging
contamination is structurally impossible). Atomic-accept is
"every write is a rename within the same FS" — partial-apply
visibility to a concurrent reader is bounded by individual file
writes, which is the same atomicity guarantee `git checkout`
provides; for stronger guarantees a future amendment can wrap in
a flock or a single-tx fsync barrier.

### D-build.10 — Authored-fresh `_audit.py` helper (audit-shape)

**Choice.** Author small helper module
`workspace-sync/src/workspace_sync/_audit.py` exposing:
- `summarize_audit_for_operator(report) -> str` — renders a
  short one-line-per-conflict summary with low-confidence first,
  for the CLI's pre-confirm prompt.
- `confirmed_by_operator(...) -> bool` — TTY interactive
  confirmation step; non-TTY returns False (per Hard Constraint
  #8 auto-accept opt-in).

**Why.** Keeps cli.py focused on argparse + flow; audit-rendering
is reusable by future `/sync` slash-command (Lens 1 future
composition).

### D-build.11 — `pyproject.toml` + package scaffold

**Choice.** Create `workspace-sync/pyproject.toml`:
- `name = "pos_workspace_sync"`
- `version = "0.1.0"`
- `requires-python = ">=3.13"`
- `dependencies = [pydantic>=2.5, PyYAML>=6.0,
  opentelemetry-api>=1.22, opentelemetry-sdk>=1.22]` (no new
  deps; git is a system binary, not a Python dep).
- `[project.scripts] pos-sync = "workspace_sync.cli:main"`,
  `pos-workspace-sync = "workspace_sync.cli:main"`.
- Setuptools find packages under `src/`.
- Standard pytest test config.

Plus skeleton: `src/workspace_sync/__init__.py`, `tests/`,
`templates/`, `seals/.gitkeep`, `README.md`.

### D-build.12 — Tests authored

**Choice.** Test files + ACs they cover:

| Test file | ACs covered | Approx test count |
|---|---|---|
| `test_conflict_report_b_shape.py` | AC.WS.4, AC.WS.5, AC.WS.9 | 6 (enum-extends, sync_ref-rename, low-confidence-first, override-shape, round-trip, reject-skipped) |
| `test_sync_protected.py` | AC.WS.2, AC.WS.10 | 5 (classify-A/B/C, floor-refuse, default-write, idempotent) |
| `test_merge_resolver.py` | AC.WS.4, AC.WS.6, AC.WS.12 | 6 (verdict-shape, per-conflict-budget, cumulative, exhausted, failure, merged-requires-content) |
| `test_canonical.py` | AC.WS.1 | 4 (resolve, missing-canonical, ref-rev-parse, no-git-dir) |
| `test_state.py` | AC.WS.8 | 3 (path-resolution, save/load round-trip, sync_ref-rename) |
| `test_conflict_detection_b_shape.py` | AC.WS.1, AC.WS.2, AC.WS.4 | 5 (canonical-only, workspace-only, both-sides, class-A-passthrough, identical-no-entry) |
| `test_staging.py` | AC.WS.7, AC.WS.12 | 4 (stage-clean, stage-resolved, atomic-apply, discard) |
| `test_merge_helper.py` | AC.WS.2, AC.WS.3, AC.WS.4, AC.WS.6, AC.WS.11, AC.WS.12 | 6 (Class-A→KEEP_LOCAL, Class-B-modified→KEEP_LOCAL, Class-C resolver call, budget-halt, OTel span emission, resolver-failure persists state) |
| `test_cli_b_shape.py` | AC.WS.1, AC.WS.7, AC.WS.10 | 5 (halt-on-missing-workspace, fresh-first-run-seeds-envelope, stage-then-accept, stage-then-reject, dry-run) |
| `test_no_sealed_amendments.py` | AC.WS.S | 2 (B23 SEAL_COMMIT-pinning + B20 only-workspace-sync-changed) |

**Total**: ~46 tests in workspace-sync.

For OTel span tests (AC.WS.11), use the in-process span exporter
fixture pattern from `self-upgrade/tests/conftest.py` (copy the
exporter setup into workspace-sync's conftest; do not import from
self-upgrade).

For resolver tests, use a `StubLLMClient` analogue (lifted from
`self-upgrade/tests/conftest.py`) for deterministic verdicts. The
real-adapter integration test is gated `skip_if_no_claude_cli`
per the existing convention in self-upgrade tests.

### D-build.13 — seal-bookkeeping infra (first-seal)

**Choice.** Create at first-seal time alongside source:
- `workspace-sync/tests/test_no_sealed_amendments.py` — B23 +
  B20 pattern. `BASELINE = "caafdf0..."` (the `chore` SHA-record
  commit immediately before this amendment's first touch).
  `SEAL_COMMIT_PATH` reads sidecar; falls back to HEAD.
- `workspace-sync/tests/SEAL_COMMIT` — placeholder line `HEAD`
  before first seal; `pos-amend seal` writes the real SHA.
- `workspace-sync/seals/.gitkeep` — empty file so the directory
  is git-tracked.

Allowed-prefixes for the sweep:
- `workspace-sync/`
- `docs/rebuild/plans/`

Allowed-files (universal admissions):
- `CLAUDE.md`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`,
  `docs/rebuild/FUTURE_IDEAS.md`.

**Why.** Standard #53-pattern. First-seal bundles the test +
sidecar + seals/ creation alongside the source so the very same
amendment commit produces all the bookkeeping infrastructure.

---

## Section B — §2.5 reverse-direction trace

Every code path / branch / dependency added by this amendment maps
to a named AC.

| Code path | AC |
|---|---|
| `cli.py::main` argparse + `[project.scripts] pos-sync` | AC.WS.1 |
| `cli.py::derive_workspace_root` (cwd / --workspace / .pos / .git fall-through) | AC.WS.1 |
| `canonical.py::resolve_canonical` + `git rev-parse <ref>` | AC.WS.1 |
| `sync_protected.py::SyncProtected._floor_intact` validator | AC.WS.10 |
| `sync_protected.py::FRAMEWORK_FLOOR` | AC.WS.10 |
| `sync_protected.py::classify` (Class A branch) | AC.WS.2 |
| `sync_protected.py::classify` (Class B branch) | AC.WS.3 |
| `sync_protected.py::classify` (Class C branch) | AC.WS.4 |
| `sync_protected.py::write_default_if_absent` | AC.WS.10 |
| `templates/sync-protected.default.yaml` | AC.WS.10 |
| `conflict_detection.py::detect_b_shape_conflicts` (canonical / workspace / both-sides matrix) | AC.WS.1, AC.WS.2 |
| `conflict_detection.py` Class-A bypass branch (KEEP_LOCAL preset) | AC.WS.2 |
| `conflict_report.py::Resolution.INFERRED_*` | AC.WS.4 |
| `conflict_report.py::Resolution._reject_skipped` validator | AC.WS.5 |
| `conflict_report.py::ConflictEntry.rationale` field + validator | AC.WS.4, AC.WS.5 |
| `conflict_report.py::ConflictEntry.confidence` field + range validator | AC.WS.4, AC.WS.5 |
| `conflict_report.py::ConflictEntry.user_override` + `override_rationale` | AC.WS.9 |
| `conflict_report.py::ConflictReport.sorted_low_confidence_first` | AC.WS.5 |
| `conflict_report.py::ConflictReport.sync_ref` (rename) | AC.WS.5 |
| `merge_resolver.py::MergeVerdict._merged_requires_content` validator | AC.WS.4 |
| `merge_resolver.py::MergeResolver.resolve` budget pre-flight | AC.WS.6 |
| `merge_resolver.py::ResolverBudget` defaults (5k/100k) | AC.WS.6 |
| `merge_resolver.py::BudgetExhausted` raise path | AC.WS.6, AC.WS.12 |
| `merge_resolver.py::ResolverFailure` translation block | AC.WS.12 |
| `merge_helper.py::resolve_inferred_conflicts` Class-A branch | AC.WS.2 |
| `merge_helper.py::resolve_inferred_conflicts` Class-B branch | AC.WS.3 |
| `merge_helper.py::resolve_inferred_conflicts` Class-C branch | AC.WS.4 |
| `merge_helper.py::resolve_inferred_conflicts` finally block (audit + state persist) | AC.WS.5, AC.WS.8, AC.WS.12 |
| `merge_helper.py` OTel `pos.sync.merge_gate.resolution` per-call span | AC.WS.11 |
| `merge_helper.py` OTel `pos.sync.merge_gate.summary` per-run span | AC.WS.11 |
| `merge_helper.py::check_inferred_resolution_invariants` post-pass verifier | AC.WS.5, AC.WS.12 |
| `state.py::audit_yaml_path` (new path `.pos/sync/<ref>/audit.yaml`) | AC.WS.5 |
| `state.py::state_yaml_path` (new path `.pos/sync/state.yaml`) | AC.WS.8 |
| `state.py::save_state` / `load_state` round-trip | AC.WS.8 |
| `cli.py` state.yaml fast-path (idempotency check) | AC.WS.8 |
| `cli.py` operator-override skip-resolver branch | AC.WS.9 |
| `staging.py::stage_canonical_clean_writes` | AC.WS.7 |
| `staging.py::apply_staging_atomically` | AC.WS.7 |
| `staging.py::discard_staging` | AC.WS.7, AC.WS.12 |
| `cli.py` `--auto-accept` + confidence-floor branch | AC.WS.7 |
| `cli.py` confirm-or-discard branch | AC.WS.7 |
| `cli.py` halt-on-budget / halt-on-failure → `discard_staging` | AC.WS.12 |
| `_resolver_client.py::_ClaudePrintResolverClient.invoke` (subprocess wrap) | AC.WS.4 |
| `_resolver_client.py::build_merge_resolver` factory | AC.WS.4, AC.WS.6 |
| `observability.py` (renamed tracer) | AC.WS.11 |
| `tests/test_no_sealed_amendments.py` BASELINE + B20 + B23 | AC.WS.S |

No row without an AC. Reverse trace closed.

---

## Section C — Test breakdown

(See D-build.12 above for the per-file AC mapping.)

**Total new tests target**: ~46 tests in workspace-sync. No
existing tests in any other component should change behaviour.
Cross-component sweep at seal-time confirms the workspace-sync/
fence (per AC.WS.S).

---

## Section D — Build sequence

1. **Pre-amendment narrow-scope test run** — confirm
   `pytest self-upgrade/` and `pytest tools/upgrade-merge-resolver/`
   pass at HEAD `caafdf0` (sanity baseline). Skipped per dispatch
   speedup (a) — narrow seal-test rerun applies to workspace-sync
   only at seal time. We sanity-spot-check self-upgrade only if
   doubt arises.
2. **Verify salvage map per plan §10 trigger 6.** Re-read the
   four salvage-as-is files (merge_resolver.py, sync_protected.py,
   state.py, conflict_report.py) at HEAD `caafdf0` and confirm no
   `paths.current_link` / `paths.history` / `live_root` references
   exist anywhere. Re-read `clause_checks.py::resolve_clause_h_inferred`
   to confirm the helper still has zero such references. Halt-and-
   surface if any verdict was wrong.
3. **Scaffold `workspace-sync/`** — `pyproject.toml`,
   `src/workspace_sync/__init__.py`, `tests/__init__.py`,
   `tests/conftest.py`, `templates/`, `seals/.gitkeep`,
   `README.md`. No source files yet.
4. **Lift salvage-as-is files** — copy `merge_resolver.py`,
   `sync_protected.py` verbatim. Copy `templates/
   sync-protected.default.yaml` verbatim. Copy `observability.py`
   with the tracer-name + docstring rename.
5. **Lift `conflict_report.py`** with `upgrade_tag`→`sync_ref`,
   `prior_tag`→`prior_ref` field renames. Update class docstring
   to drop self-upgrade references where it confuses — preserve
   the structural-clause-g rationale verbatim.
6. **Lift `state.py`** with `UpgradeStatus`→`SyncStatus`,
   `upgrade_tag`→`sync_ref`, `.pos/upgrade/`→`.pos/sync/` path
   migration.
7. **Lift `canonical.py`** with manifest scrub + `tag`→`ref`
   rename + `git rev-parse HEAD` resolution step.
8. **Re-vendor `_resolver_client.py`** by copying
   `tools/upgrade-merge-resolver/.../__init__.py`, replacing
   `from self_upgrade.merge_resolver import ...` with
   `from .merge_resolver import ...`.
9. **Lift `merge_helper.py`** — copy the four functions from
   `clause_checks.py` (drop the (a)-(g) + run_all_clauses paths;
   they belong in self-upgrade only). Apply renames per
   D-build.6: `resolve_clause_h_inferred` → `resolve_inferred_
   conflicts`, `check_clause_h` → `check_inferred_resolution_
   invariants`, `report.upgrade_tag` → `report.sync_ref`,
   `.pos/upgrade/<tag>/merged` → `.pos/sync/<ref>/merged`,
   OTel `pos.upgrade.merge_gate.*` → `pos.sync.merge_gate.*`.
10. **Author `conflict_detection.py`** (B-shape git-tree-vs-
    workspace classifier).
11. **Author `staging.py`** (stage / atomic-accept / discard).
12. **Author `_audit.py`** (operator-summary helper).
13. **Author `cli.py`** (pos-sync / pos-workspace-sync entry).
14. **Author all 9 unit-test files + conftest** (D-build.12).
15. **Author seal-test + sidecar** (D-build.13). `SEAL_COMMIT`
    sidecar contains `HEAD` placeholder (auto-bumped at seal).
16. **Run touched-component suite** — `pytest workspace-sync/`;
    expect ~46 tests green.
17. **Author manifest** at `docs/rebuild/plans/
    workspace-sync.manifest.yaml` per §9.2 sketch with
    BASELINE = `caafdf0`, amendment number 56.
18. **`pos-amend apply --dry-run`** (skip per dispatch speedup
    (b) if smoke tests on workspace-sync subset pass; rely on
    `pos-amend apply` to catch anything off).
19. **Amendment commit** (single commit; no `--amend`). Commit
    message: `feat(workspace-sync): canonical-to-workspace git-
    shaped sync with LLM-mediated semantic merge (amendment #56,
    AC.WS.1–AC.WS.12 + AC.WS.S)`.
20. **Run `pytest workspace-sync/`** post-commit — expected
    same green count.
21. **`pos-amend seal --plan-doc <ABS>`** — writes the real
    SHA to sidecar; commits seal narrative; backfills §14
    + §15 with commit SHAs.
22. **Post-seal cross-component sweep** — `pos-amend apply
    --dry-run` against all sealed components.

---

## Section E — Backwards-compat verification plan

Per Hard Constraint #5: `pos upgrade <tag> --staging-dir <path>`
and `pos upgrade <tag> --canonical <path>` invocations must
remain byte-identical.

Verification:
1. workspace-sync's pyproject.toml does NOT declare a `pos`
   console_script (only `pos-sync` and `pos-workspace-sync`).
   self-upgrade's `pos = self_upgrade.cli:main` is untouched.
2. No edits to any file under `self-upgrade/`. Verified by
   AC.WS.S seal-diff sweep.
3. The `tools/upgrade-merge-resolver/` package is untouched.
   Verified by AC.WS.S seal-diff sweep.
4. workspace-sync neither imports from `self_upgrade.*` nor
   from `upgrade_merge_resolver` at runtime. Verified by
   `grep -r "from self_upgrade\|import self_upgrade\|from
   upgrade_merge_resolver\|import upgrade_merge_resolver"`
   over `workspace-sync/src/`.
5. Self-upgrade test suite continues green at HEAD post-amendment
   (spot check post-build).

---

## Section F — Halt-trigger watchlist

Per plan §10:

- **#1 (new top-level objective):** Plan §2 argues composition
  under v1.0 self-upgrade objective + Gap-3 line 114. No watch
  needed; halt if a structural property emerges that the
  existing objective cannot frame.
- **#2 (ODD violation in surrounding code):** if the salvage-
  source files reveal AC-untraced code paths during lift, halt
  before extending. Specifically: `clause_checks.py` lines 355-
  579 are the lifted block; we will read them in full and
  confirm no untraced branches.
- **#4 (source edits outside `workspace-sync/`):** strictly
  forbidden. ALL new code under `workspace-sync/`. Universal
  admissions (CLAUDE.md, docs/rebuild/plans/, docs/odd-*.md,
  docs/rebuild/FUTURE_IDEAS.md) are exempt.
- **#5 (no resolver dep):** verified — `_resolver_client.py`
  is a stdlib subprocess wrap of `claude -p`. No new third-
  party deps required for the diff machinery either (git
  shellout is stdlib `subprocess`).
- **#6 (GG salvage map wrong):** D-build step 2 above is the
  verification gate. Halt-and-surface if any "salvage-as-is"
  has a hidden A-coupling.
- **#7 (workspace data loss reproducible):** AC.WS.2 +
  AC.WS.10 + AC.WS.12 pin this. Tests for each.
- **#10 (wall-time exceeds 6-8h):** halt-and-state-report
  if exceeded.

---

## Section G — Speedup application (per dispatch + amendment-dispatch-speedups directive)

(a) **Narrow seal-test rerun.** First test run = `pytest
    workspace-sync/` only. Cross-component sweep deferred to
    seal-time only. Saves ~5–8 min vs full-suite rerun.
(b) **Skip pre-seal full-suite.** If smoke tests
    (workspace-sync subset) green, skip the full pre-seal
    rerun. `pos-amend apply --dry-run` exercises the seal
    boundary without re-running every component's tests.
(c) **Inline methodology snippets in commit prose.** Where
    the commit-message references ODD §2.5 reverse-trace or
    Hard Constraint #1 (no edits to self-upgrade), inline the
    one-line rationale rather than citing the section by
    number.

---

## Section H — Commit SHAs

(populated post-build by `pos-amend seal --plan-doc`)

---

## Section I — Halt findings

(populated as halts occur)
