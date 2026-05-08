# Builder-plan — Amendment #37 (hands-off-lifecycle Claude-Code default-agent wiring)

Pre-edit gate verified:
- Amendment #35 sealed at `ce07242` (primary-persona renderer + onboarding +
  `is_starter`); amendment #36 sealed at `0031d1e` (workspace-bootstrap
  persona-scaffold).
- `to_agent_md(contract, *, prompt_text=None)` importable from
  `primary_persona.agent_md`.
- `is_starter` field exists on `PersonaContract` (default False).
- Workspace-bootstrap scaffold materialises `personas/<handle>/` on first-run
  (`workspace_bootstrap.adapters.first_run_scaffold._install_persona_directory`).
- Hands-off-lifecycle's tests/SEAL_COMMIT currently reads `b35e0c0` (true-
  first-run seal); the H19 BASELINE remains frozen at `3780603`
  (amendment #23 convention; manifest sets `frozen_baseline: true`).

## Files to edit / add

Source (single sealed component — `hands-off-lifecycle/`):

- `hands-off-lifecycle/hooks/first_run_settings.py`
  - Generalise the settings.json merge to also-merge a top-level
    `"agent"` field. Two methods considered (D-build.1):
    - **(a) Add a parameter to `merge_session_start`** —
      `agent_handle: str | None = None`. When non-None, the merger
      sets `existing["agent"] = agent_handle` (preserving prior
      keys per the existing semantics). Backwards-compatible with
      every existing call site (default None = unchanged).
    - **(b) Refactor into a generic merger.** Larger blast radius;
      not needed by AC37.1.
  - **Decision: (a)** — minimal blast radius, preserves the
    well-tested SessionStart-stanza machinery, AC37.S enforces no
    spillover. Existing call-sites in `first_run_helper.py`
    (Phase 3d + `_self_retire`) pass the resolved handle for
    Phase 3d (when first-run merges) and Phase 6 self-retire (so
    the agent field survives).

- `hands-off-lifecycle/hooks/first_run_helper.py`
  - Add a Phase 3f (post-3e editable installs, before 3d / 4a):
    "agent-file authorship". The phase loads the workspace's
    persona via `PersonaLoader` (subprocess under shared venv,
    same pattern as `first_run_scaffold_runner.py`), renders the
    `.claude/agents/<handle>.md` body via `to_agent_md(contract,
    prompt_text=...)`, and writes the file with
    write-only-if-different policy (D-build.4).
  - Modify Phase 3d (`merge_session_start`) call: pass the
    resolved `agent_handle` so the agent field appears alongside
    the SessionStart stanza on first authorship.
  - Modify `_self_retire` to also pass `agent_handle` so the
    settings.json post-retire keeps the `"agent"` key.
  - Graceful-degradation: any failure in the agent-file authorship
    sub-phase emits a structured diagnostic via `_advance_state`
    (status preserved as `running`; phase named
    `phase-3f-agent-file-authorship`; no `_emit_diag` halt) —
    the next phase proceeds. The settings.json `"agent"` merge
    itself does not raise on first-run write failure either; if
    it does (e.g. unwriteable settings.json), the existing
    settings-merge wraps in atomic-rename, so transient errors
    propagate the existing diagnostic path. AC37.4 negative case
    checks the agent-file write degrades gracefully.

- `hands-off-lifecycle/hooks/agent_file_authoring.py` (NEW)
  - Stdlib-only thin module: `write_agent_file(*, workspace_root,
    handle, body)` — atomic write via `.tmp` + rename, with
    write-only-if-different. Returns a small dataclass
    `AgentFileWriteResult(wrote: bool, reason: str, path: Path)`.
    Errors caught here surface via the dataclass + log-line; the
    helper's `_advance_state` mirrors them.
  - The body is provided by the caller (the helper); the renderer
    invocation lives in a small CLI runner (see next file) that
    runs under the shared venv.

- `hands-off-lifecycle/hooks/agent_file_runner.py` (NEW)
  - Mirror of `first_run_scaffold_runner.py`'s pattern. Stdlib-
    only up to the import of `primary_persona`; the helper spawns
    it as a subprocess under `<root>/.venv/bin/python`. Reads
    `--workspace-root <path>`, `--handle <handle>`, optional
    `--prompt-path` (defaults to
    `<workspace>/personas/<handle>/prompt.md`), prints rendered
    `to_agent_md()` body to stdout. Exit 0 = body on stdout;
    exit 1 = JSON failure payload on stderr; exit 2 = runner
    framework failure.

Tests (one per AC, in `hands-off-lifecycle/tests/`):

- `tests/test_AC37_1_settings_agent_merge.py` — settings.json after first-
  run merge contains `"agent": "<handle>"`; SessionStart stanza preserved;
  prior user keys preserved; pre-existing `"agent"` value overwritten by
  the workspace-bootstrap-resolved handle.
- `tests/test_AC37_2_agent_file_written.py` — `.claude/agents/<handle>.md`
  exists; content equals `to_agent_md(loaded_contract, prompt_text=
  prompt.md)`.
- `tests/test_AC37_3_rerun_no_op.py` — flipping `is_starter` to False;
  re-running first-run leaves `.claude/agents/<handle>.md` mtime
  unchanged when content matches; settings.json `"agent"` field
  preserved across re-run.
- `tests/test_AC37_4_graceful_failure.py` — `.claude/agents/`
  not writable (chmod 000) → first-run completes; structured
  diagnostic emitted; persona scaffold remains in place.
- `tests/test_AC37_5_session_start_names_persona.py` — read agent file
  identity-anchor block from disk; assert handle + given_name appear;
  invoke compose_session_fields + composer.on_session_start;
  assert SessionPayload's additional_context_text contains given_name
  (via the starter-pending contributor when is_starter remains True).
- `tests/test_AC37_6_no_persona_content_in_source.py` — scan
  `hands-off-lifecycle/hooks/` and `hands-off-lifecycle/src/` (the
  latter does not exist as a directory in this component) for
  persona-prose sentinel strings. Assert no constant in source matches
  the contract template's prose. Use a fixture contract with sentinel
  prose to prove the rendered file's contents come from the contract.

Plan + manifest:

- `docs/plans/amendment-37-hands-off-lifecycle-default-agent-wiring.manifest.yaml` — author following #35/#36 pattern. BASELINE = HEAD~1 of the amendment commit. `frozen_baseline: true` for hands-off-lifecycle (amendment #23).
- `docs/plans/amendment-37-hands-off-lifecycle-default-agent-wiring.md` — append §14 method-decision record.

## D-build method choices (committed)

- **D-build.1 (settings.json merge generalisation shape):** (a)
  parameterise `merge_session_start` with optional `agent_handle:
  str | None`. Backwards-compat preserved (default None = no-op).
  Plan §11 D-build.1 recommendation aligns; minimal blast radius.

- **D-build.2 (agent-file write atomicity):** atomic-rename via
  `.tmp` sibling + `os.replace`. Mirrors the existing settings-
  merge atomic write. Interrupted writes never leave Claude Code
  with a partial agent file to parse.

- **D-build.3 (diagnostic surface routing):** structured
  diagnostic via `_advance_state` with phase=
  `phase-3f-agent-file-authorship`, detail names the failure
  class. State stays `running` (the failure is non-fatal); next
  phase proceeds. Matches the existing pattern in the helper's
  observability surface.

- **D-build.4 (write-only-if-different):** compare existing-file
  bytes to rendered body; skip write when equal. Preserves mtime
  stability across re-runs (AC37.3 measures this) and avoids
  file-watch tooling churn. Costs a single `read_bytes()` per
  first-run; trivially cheap.

## Implementation order

1. Write builder-plan (this file). [done]
2. Add `agent_file_authoring.py` (stdlib-only writer + dataclass).
3. Add `agent_file_runner.py` (subprocess CLI under shared venv).
4. Generalise `merge_session_start` with optional `agent_handle`.
5. Wire Phase 3f into `first_run_helper.py`. Update `_self_retire`
   to pass `agent_handle` through.
6. Author tests AC37.1–AC37.6 in dependency order.
7. Run hands-off-lifecycle tests. Expect all green.
8. Cross-component seal-diff sweep on every other sealed
   component's `test_no_sealed_amendments.py`.
9. Author manifest with `frozen_baseline: true` for hands-off-
   lifecycle. `pos-amend apply --dry-run` → green.
10. Amendment commit (single amendment commit). BASELINE = HEAD~1.
11. `pos-amend apply` if needed (mostly a no-op for sidecar bumps;
    seal commit handles that).
12. Seal commit via `pos-amend seal`.
13. Update plan §14 method-decision record + commit SHAs.
14. Backfill plan-SHA commit recording the SHAs.

## Halt triggers monitored

- Source edit required outside `hands-off-lifecycle/` → halt.
- `pos-amend apply --dry-run` red after edits → halt.
- H19 frozen BASELINE accidentally advances → halt.
- AC37 fixture cannot be exercised deterministically → halt.
- 60-minute wall-time exceeded → halt with current state.
