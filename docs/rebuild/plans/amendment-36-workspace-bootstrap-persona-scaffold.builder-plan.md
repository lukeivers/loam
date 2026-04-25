# Builder-plan — Amendment #36 (workspace-bootstrap persona-scaffold)

Pre-edit gate verified:
- Amendment #35 sealed at `ce07242`; backfill at `057afdb`.
- `PersonaContract.is_starter` field default `False` confirmed importable.
- `to_agent_md` importable from `primary_persona.agent_md`.
- `STARTER_PENDING_MARKER`, `persist_elicitation_transcript`,
  `build_starter_pending_contributor` importable from
  `primary_persona.onboarding`.
- Baseline workspace-bootstrap suite: 102/102 green at HEAD `057afdb`.

## Files to edit / add

Source (single sealed component — `workspace-bootstrap/`):

- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
  - Add: `resolve_persona_handle(raw_input: str | None) -> str` —
    pure function. Default → `primary`. Sluggifies via existing
    `workspace_slug` (re-used). Rejects `eve` with
    `PersonaHandleRejectedError` (new BootstrapError sub-class,
    `code = ERR_HANDS_OFF_INTERNAL`).
  - Add: `_PERSONA_TEMPLATE_DIR` constant — path to
    `<repo>/primary-persona/templates/persona-template/`. Resolved
    relative to the repo root (sibling to `workspace-bootstrap/`),
    using the same upward walk pattern as `_resolve_workspace_root`.
  - Add: `_install_persona_directory(*, workspace_root, handle)
    -> tuple[bool, Path]` — copies the framework template into
    `<workspace>/personas/<handle>/`, then mutates the YAML to set
    `handle: <resolved>` and `is_starter: true`. Returns
    `(installed, persona_dir)` where `installed=False` means the
    directory pre-existed (idempotent no-op). Raises a structured
    diagnostic (using the existing `PartialScaffoldError`) when the
    directory exists but `contract.yaml` is malformed (zero bytes
    or Pydantic-invalid).
  - Modify: `run_first_run_scaffold(...)` — accept new optional
    `persona_handle: str = "primary"` parameter; after the existing
    plist install, call `_install_persona_directory` so a fresh
    workspace lands a `personas/<handle>/` directory.
  - Modify: `ScaffoldResult` — add `persona_dir: Path | None = None`
    + `persona_installed: bool = False`.

Tests (new files only — one per AC):

- `workspace-bootstrap/tests/test_AC36_1_persona_scaffold_fresh_clone.py`
- `workspace-bootstrap/tests/test_AC36_2_is_starter_true.py`
- `workspace-bootstrap/tests/test_AC36_3_idempotent_re_run.py`
- `workspace-bootstrap/tests/test_AC36_4_handle_resolver.py`
- `workspace-bootstrap/tests/test_AC36_5_partial_recovery_persona_dir.py`
- `workspace-bootstrap/tests/test_AC36_6_framework_not_content.py`
- `workspace-bootstrap/tests/test_AC36_S_seal_diff.py` — covered by
  the existing `test_no_sealed_amendments.py` once BASELINE bumps;
  no new file needed unless the existing sweep is insufficient. The
  manifest's `components` list already names that test as the
  seal_test for workspace-bootstrap. **Decision: rely on existing
  seal-test machinery**; AC36.S is verified via `pos-amend apply
  --dry-run` green + the cross-component seal-diff sweep. No
  separate test file unless the existing one mis-categorises.

Plan + manifest:

- `docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold.manifest.yaml` — author following #35's pattern. BASELINE = HEAD~1 of the amendment commit.
- `docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold.md` — append §14 method-decision record.

## D-build method choices (committed)

- **D-build.1 (handle prompt UX):** the scaffold defaults handle to
  `primary` always. The handle-resolver function is exposed as a
  pure utility (`resolve_persona_handle`) that takes a `str | None`
  and returns the resolved handle. Future callers (amendment #37 +
  the onboarding flow already landed by #35) can invoke it; this
  amendment does not add a new I/O surface to first-run.
  **Rationale:** plan §9 #4 names "cannot integrate without adding a
  new I/O surface" as a halt; (a) would require touching
  hands-off-lifecycle which is amendment #37's fence; (c) is a
  cleaner shape — the AC measures the resolver's outcome on a
  fixture set, which a pure function satisfies cleanly.

- **D-build.2 (template-copy mechanism):** `shutil.copytree` of
  `primary-persona/templates/persona-template/` into a temporary
  staging directory, then YAML round-trip on `contract.yaml` to set
  `handle` and `is_starter: true`, then `os.rename` to
  `<workspace>/personas/<handle>/`. Atomic-on-success;
  partial-failure leaves the staging dir for partial-recovery to
  pick up.

- **D-build.3 (sluggifier shape):** reuse the existing
  `workspace_slug` sluggifier from
  `workspace_bootstrap.adapters.first_run_scaffold`. Already
  parity-tested under amendment #33. Same lowercase + ASCII +
  dashes + collapse-runs shape required by AC36.4.

- **D-build.4 (partial_recovery diagnostic):** extend the existing
  `PartialScaffoldError` payload with `kind: "persona-scaffold-
  malformed"` + `persona_dir: <path>` data fields. The exception
  class stays the same so existing handlers route uniformly; the
  data payload distinguishes sub-cause for callers that want to
  branch.

## Implementation order

1. Write builder-plan (this file). [now]
2. Land `resolve_persona_handle` + `PersonaHandleRejectedError` +
   AC36.4 test. Verify green.
3. Land `_install_persona_directory` + scaffold-call wiring +
   AC36.1, AC36.2 tests. Verify green.
4. Land idempotency + AC36.3 test. Verify green.
5. Land partial-recovery integration + AC36.5 test. Verify green.
6. Land AC36.6 framework-not-content scan test. Verify green.
7. Run full workspace-bootstrap test suite. Expect all green.
8. Author manifest. `pos-amend apply --dry-run` → green.
9. Amendment commit (single amendment commit). BASELINE = HEAD~1.
10. `pos-amend apply` (advances BASELINE in manifest if needed —
    actually applies sidecar updates to working tree).
11. Cross-component seal-diff sweep:
    `pytest <each-component>/tests/test_no_sealed_amendments.py`.
12. Seal commit via `pos-amend seal`.
13. Update plan §14 method-decision record + commit SHAs.
14. Backfill plan-SHA commit recording the SHAs.

## Halt triggers monitored

- Source edit required outside `workspace-bootstrap/` → halt.
- AC36.4 fixture rejected by existing sluggifier → halt or extend.
- `pos-amend apply --dry-run` red after edits → halt.
- 60-minute wall-time exceeded → halt with current state.
