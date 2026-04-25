# pos-amend tracker integration — builder plan

Companion to `pos-amend-tracker-integration.md` (the dev-discipline plan).
Names files + symbols expected to be touched, the test surface, and the
method-level decisions made within the AC scope.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

## 1. Method choices made (per plan §11 D-build.x)

- **D-build.1** — `objectives` block YAML structure: option (a). Flat list of
  dict entries; each entry carries the `ObjectiveSpec` field set verbatim
  (`goal`, `parent_id` xor `parent_root: true`, `acceptance_criteria` as a
  list of dicts with the `kind` discriminator, `time_bound`, `authored_by`,
  `lifted_from.source_doc` + `lifted_from.source_ac`). Master-research rec
  taken; explicit beats shorthand for v1.
- **D-build.2** — Schema-version bump: option (a). Manifest must declare
  `schema_version: 2` when the `objectives` block is present;
  `schema_version: 1` MUST NOT carry the block. Mismatched cases reject
  with `InvalidField`. Master-research rec taken; surfaces drift loudly.
- **D-build.3** — `source_commit` resolution at seal: option (a). Read
  HEAD at seal-step entry (mirrors the existing `_head_sha(repo_root)`
  pattern in `seal._finalize`). No new manifest field. Master-research
  rec taken; symmetric with the seal step's existing amendment-SHA reading.
- **D-build.4** — Tracker DB path resolution: option (a). Inline the
  `objective_tracker.sqlite` filename convention (matching
  `workspace_bootstrap.adapters.tracker_seed.TRACKER_DB_FILENAME` and
  `primary_persona.tracker_context.TRACKER_DB_FILENAME`). Resolves to
  `<repo_root>/objective_tracker.sqlite` — same convention every existing
  consumer follows. No `--tracker-db` flag introduced.

## 2. Files expected to change

### New

- `tools/pos-amend/src/pos_amend/tracker_registration.py` — the
  registration helper. Public surface: `register_objectives(manifest,
  repo_root)` and `update_source_commits(manifest, repo_root,
  amendment_sha)`. Both wrap the asyncio + tracker-DB plumbing behind
  sync entry points (mirrors `tracker_seed.run_seed_synchronously`).
- `tools/pos-amend/tests/fixtures/valid-with-objectives.yaml` —
  schema_version: 2 fixture with an `objectives` block.
- `tools/pos-amend/tests/test_tracker_integration.py` — AC.D-pa.1 …
  AC.D-pa.5 tests.

### Edited

- `tools/pos-amend/src/pos_amend/manifest.py` —
  - bump `SCHEMA_VERSIONS` to accept both 1 and 2
  - new `ObjectiveEntry` dataclass + `LiftedFromEntry`
  - parse `objectives` list into `tuple[ObjectiveEntry, ...]` on the
    `Manifest` dataclass
  - reject `schema_version: 1` carrying an `objectives` block
  - reject `schema_version: 2` missing an `objectives` block
- `tools/pos-amend/src/pos_amend/commands/apply.py` —
  - call `tracker_registration.register_objectives(manifest, repo_root)`
    at the top of `run` (before BASELINE bump / sidecar / widening) when
    `not dry_run` and manifest has an `objectives` block
  - emit a structured diagnostic + return non-zero exit code (3) on
    tracker-unavailable failure, with no partial state
- `tools/pos-amend/src/pos_amend/commands/seal.py` —
  - call `tracker_registration.update_source_commits(...)` at the
    appropriate point in `_finalize` (after the amendment SHA is
    known, before the seal commit). The legacy `_legacy_seal` path
    (i.e. `--no-finalize`) remains byte-identical and does NOT call
    the registration helper — preserves AC.D-sa.4's contract.
- `tools/pos-amend/README.md` — document the schema v2 surface (see §3).

## 3. Test surface

- `test_tracker_integration.py::test_AC_D_pa_1_apply_registers_records`
  — manifest with N objectives → tracker carries N records keyed on
  `lifted_from.source_doc + .source_ac`.
- `test_tracker_integration.py::test_AC_D_pa_2_apply_idempotent` —
  re-running `apply` produces no new records / events.
- `test_tracker_integration.py::test_AC_D_pa_3_seal_writes_source_commit`
  — after `apply` then commit then `seal`, every registered record's
  `lifted_from.source_commit` equals the amendment SHA.
- `test_tracker_integration.py::test_AC_D_pa_4_v1_manifests_unchanged`
  — every existing fixture (schema_version 1) parses + applies clean;
  no tracker DB created when no `objectives` block.
- `test_tracker_integration.py::test_AC_D_pa_5_tracker_unavailable_halts`
  — corrupt / unreadable DB → exit 3, no partial registration.
- Two manifest-parsing tests:
  `test_T16_schema_v2_with_objectives_block_parses` and
  `test_T16_schema_v1_with_objectives_block_rejected`.

The pre-existing 59-test suite must remain green (AC.D-pa.4's
backward-compat invariant).

## 4. Methodology touchpoints

- §2.5 reverse map: every new branch traces to AC.D-pa.x. Three new
  branches (objectives-block parse path, registration call, source-commit
  update) each named in §2 above.
- ODD §3.3 behaviour count: 5 declared / 5 ACs covered (per plan §5).

## 5. Non-method choices

- The registration helper imports `objective_tracker` at module-top
  (not lazily) — the workspace's shared venv ships it as a transitive
  dep of `workspace-bootstrap`. If `objective_tracker` is missing, the
  import error surfaces as a tracker-unavailable diagnostic at
  `apply` time (AC.D-pa.5 path).
- Async plumbing: `ObjectiveTracker.create` is async; the helper
  wraps invocations in `asyncio.run(...)` (matches
  `tracker_seed.run_seed_synchronously`). `query_projection_view` is
  sync and is called directly.
