# Proposal — orchestrator-bootstrap-unification amendment (#7)

**Status:** APPROVED — owner signed off in-session 2026-04-22.
**Authored by:** assistant (this session).
**Target components (multi-component amendment):**
`orchestrator` + `hands-off-lifecycle` (scaffold-invariant assertion).
Possibly `workspace-bootstrap` (adapter default confirmation; likely zero edits).
**Precedent:** namespaced-labels-and-bootout amendment (multi-component
seal at `68e0525`), session-start-detachment amendment (multi-component
seal at `d962ffd`).

---

## 1. Objective

The workspace-bootstrap framework is the sole path through which the
orchestrator acquires its workspace contributions: `Orchestrator._startup()`
no longer loads `bootstrap.py` directly, and the existing
`WorkspaceBootstrapPyContribution` adapter is the only caller of
`load_and_register`. Missing `~/.pos/bootstrap.yaml` replaces missing
`~/.pos/bootstrap.py` as the fail-closed trigger; `bootstrap.py` is
optional by default and opt-in-required via per-workspace adapter config.

Three behaviours in one objective — §4 below counts criteria against it.

## 2. Constraints

- **Budget.** Behavioural refactor only. No new runtime deps. No new
  framework phases. No new IPC methods. If implementation would require
  restructuring the framework's phase graph or introducing a new
  adapter, halt and signal — scope creep.
- **Reversibility.** Fully reversible. Removed call sites and the
  deleted `require_bootstrap` config field can be restored from git.
  No on-disk state written outside the amendment docs.
- **Dependency fence.** Amends `orchestrator/` and
  `hands-off-lifecycle/` only. `workspace-bootstrap/` is on the fence:
  verify the `WorkspaceBootstrapPyContribution` default (`required:
  False`) already satisfies AC4/AC5 and touch nothing there if so. No
  other sealed component may be touched — memory-system, safety-layer,
  reversibility-primitive, cost-governance, self-correction,
  graceful-degradation, scope-of-work, objective-tracker,
  primary-persona, observability-aggregator, self-upgrade,
  telegram-interface are all off-limits.
- **Authority bound.** Owner approves acceptance criteria (this doc)
  + the seal-plan SHA bump. Owner has already ruled on the flagged
  inferences in §5 (2026-04-22): #1 remove, #2 remove, #3 keep,
  #6 delete. Builder chooses file layout and diagnostic wording.
- **Fail-closed direction.** Flipped, not removed. The fail-closed
  point moves from orchestrator (missing `bootstrap.py` → exit 2) to
  the framework (missing `bootstrap.yaml` or composition failure →
  whatever the framework already raises). The orchestrator's own
  startup no longer has a fail-closed branch tied to workspace
  Python code.
- **Error codes.** Reuse what exists. `workspace_bootstrap_py` already
  maps adapter failures to `-32086` (framework AdapterRaisedError
  band); `first_run_scaffold` already uses `-32090..-32099`. No new
  codes introduced.
- **Out of scope (other tasks).** telegram-interface adapter wiring,
  primary-persona's persona-loader path, cross-workspace slug
  collision detection, legacy-label cleanup of already-loaded
  `com.pos.orchestrator` plists — all remain owned by other
  amendments or by owner-manual cleanup.

## 3. Acceptance criteria

Each criterion maps 1:1 to a test function in the build.

### AC1 — Orchestrator._startup no longer loads bootstrap.py directly

After the amendment, `orchestrator/src/orchestrator.py` contains zero
references to `load_and_register` and zero imports from
`.bootstrap`. Test: static-grep the orchestrator sources; assert no
hit. Runtime complement: invoke `Orchestrator._startup()` on a config
whose `bootstrap_path` points at a file that raises on import; assert
startup completes without reading that file.

### AC2 — Missing bootstrap.py no longer causes orchestrator exit code 2

Construct an `OrchestratorConfig` whose `root_dir` contains no
`bootstrap.py`. Start the orchestrator directly (bypassing the
framework). Assert `run()` returns exit code 0 after a clean
SIGTERM — no `bootstrap_refused` event is written, no `BootstrapMissing`
is raised from `_startup`. The brief's "fail-closed on missing
`bootstrap.py`" contract is intentionally removed.

### AC3 — Missing bootstrap.yaml is the new fail-closed condition

Invoke the workspace-bootstrap framework on a `~/.pos/` directory
containing no `bootstrap.yaml` and no other scaffold artefacts. Assert
the framework raises a typed error (reuse
`BootstrapError`/`ManifestMissing`/whatever the framework already
defines — see flagged inference #4) before any contribution runs, with
a diagnostic carrying `-32086` or the framework's existing
manifest-missing code. No orchestrator process is constructed.

### AC4 — Adapter loads bootstrap.py when present (regression)

With `~/.pos/bootstrap.yaml` listing `workspace_bootstrap_py` and a
`~/.pos/bootstrap.py` exposing `def register(orch): orch.marker = 42`,
run the framework end-to-end. Assert `host.orchestrator.marker == 42`
after composition. Confirms the adapter continues to honour the
orchestrator's `load_and_register` contract.

### AC5 — Adapter succeeds with missing bootstrap.py at default (regression)

With `~/.pos/bootstrap.yaml` listing `workspace_bootstrap_py` and no
`~/.pos/bootstrap.py` and no `workspace_bootstrap_py.yaml` (adapter
config absent — `required` defaults to False), run the framework
end-to-end. Assert composition succeeds and `host.orchestrator` is
populated. No exception reaches the user.

### AC6 — Adapter fails closed when required=True and bootstrap.py missing

Same fixtures as AC5 plus a `~/.pos/workspace_bootstrap_py.yaml`
containing `required: True`. Assert the framework raises
`AdapterRaisedError` (wrapping `BootstrapMissing`) with `-32086`.
Confirms the opt-in fail-closed path for production workspaces.

### AC7 — --no-bootstrap flag is removed

Per owner ruling on flagged inference #1 (remove). After the amendment,
invoking `python -m pos_orchestrator --no-bootstrap` exits with
`argparse` error code 2, and `python -m pos_orchestrator --help` does
not mention the flag. Tests that previously passed `--no-bootstrap`
either drop it (if the underlying behaviour is now default-OK) or
are removed (if they were validating the now-dead flag itself).

### AC8 — First-run scaffold does not create bootstrap.py

After `run_first_run_scaffold(pos_root=tmp_path, ...)` on a fresh
tmp_path, assert `(tmp_path / "bootstrap.py").exists() is False`. The
scaffold writes `bootstrap.yaml` and eight sibling YAMLs; it must
not write a Python stub. (Today it does not; this test pins the
invariant.)

### AC9 — Seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` after the amendment
shows only paths under `orchestrator/`, `hands-off-lifecycle/`
(if the AC8 test lands there), optionally `workspace-bootstrap/`
(if the adapter was touched),
`docs/rebuild/components/orchestrator-bootstrap-unification/`, and
`data/`. Any path outside this set is a halt condition for the
seal commit.

## 4. Behaviour-count check

| Behaviour | Criteria |
|-----------|----------|
| Framework is the sole loader | AC1 (direct call removed), AC4 (adapter still works), AC5 (default-lenient), AC6 (opt-in-strict) |
| Fail-closed trigger moves to missing bootstrap.yaml | AC2 (old trigger gone), AC3 (new trigger present) |
| No new on-disk surface for Python-stub scaffolding | AC7 (CLI surface disposition), AC8 (scaffold invariant) |
| Seal discipline | AC9 |

Four distinct behaviours → nine criteria → every behaviour covered.

## 5. Flagged inferences (owner rulings, 2026-04-22)

1. **`--no-bootstrap` disposition.** RULING: **remove**. Rationale:
   with `required: False` default, missing `bootstrap.py` is already
   a silent no-op — the flag has no remaining job. Builder grep the
   first-run harness + primary-persona tests before committing the
   removal to catch any caller depending on the skip semantics.
2. **`OrchestratorConfig.require_bootstrap` field.** RULING:
   **remove**. It exists solely to control the now-dead branch in
   `_startup`. `PrimaryPersonaContribution` currently passes
   `require_bootstrap=False` when constructing the config; that line
   goes away with the field. Builder greps the repo first for any
   docs/YAML references.
3. **`BootstrapMissing` / `BootstrapError` exception classes.**
   RULING: **keep**. They are the types
   `WorkspaceBootstrapPyContribution` catches; `load_and_register`
   itself still raises them. Moving the catch site from orchestrator
   to the adapter does not make the types obsolete.
4. **Framework fail-closed code for missing bootstrap.yaml.** Builder
   call: inspect what the framework raises today for a missing
   manifest and reuse that error code in AC3. If nothing exists,
   raise a named framework error in the `-32086`/AdapterRaisedError
   band; do **not** introduce a new top-level code.
5. **`workspace-bootstrap/` touched at all?** Builder call:
   **probably not**. Confirm by reading AC4 + AC5 + AC6 tests against
   the current adapter source; only amend the adapter if a test
   cannot pass without a change.
6. **`test_missing_bootstrap_fails_closed` +
   `test_erroring_bootstrap_fails_closed` disposition.** RULING:
   **delete outright**. They pin a contract this amendment
   intentionally removes. A doc comment at the test site pointing
   at this proposal suffices for the audit trail; AC2 is the
   positive-space inverse.

## 6. Seal plan

1. Create a new `orchestrator/tests/test_no_sealed_amendments.py`
   (orchestrator currently ships a `SEAL_COMMIT` sidecar but no
   seal-diff test). Mirrors
   `workspace-bootstrap/tests/test_no_sealed_amendments.py`
   structure: `BASELINE`/`_seal_commit()`/diff filter against an
   `allowed_prefixes` tuple. `BASELINE` starts at `a5dbf8f` (the
   current tip — pre-amendment).
2. Advance `BASELINE` in
   `hands-off-lifecycle/tests/test_cross_cutting.py` from `9f35979`
   → `a5dbf8f` (current tip).
3. If (and only if) `workspace-bootstrap/` is touched: advance
   `BASELINE` in `workspace-bootstrap/tests/test_no_sealed_amendments.py`
   from `9f35979` → `a5dbf8f`.
4. Amendment commit: `fix(orchestrator, hands-off-lifecycle):
   orchestrator-bootstrap-unification amendment (#7)`.
5. Tests committed together with the fix.
6. Seal commit (separate): `chore(seals):
   orchestrator-bootstrap-unification seal — orchestrator +
   hands-off-lifecycle at <sha>`. Advances
   `orchestrator/tests/SEAL_COMMIT` from `1dbe81b` → the amendment
   code-commit SHA, and appends an amendment-cycle note to the
   hands-off-lifecycle `SEAL_COMMIT.true-first-run` sidecar.
7. Allowed-prefix additions for the seal tests:
   - `orchestrator/` test:
     `("orchestrator/", "hands-off-lifecycle/", "workspace-bootstrap/", "docs/rebuild/components/orchestrator-bootstrap-unification/", "data/")`.
   - `hands-off-lifecycle/` test gains
     `"docs/rebuild/components/orchestrator-bootstrap-unification/"`
     to the existing `docs` prefix permission.
   - `workspace-bootstrap/` test (if touched) gains `"orchestrator/"`
     and `"docs/rebuild/components/orchestrator-bootstrap-unification/"`.

## 7. Halt triggers

- Removing the direct `load_and_register` call in `_startup` breaks a
  test outside `test_d1_process_skeleton.py` (suggests a dependency
  not mapped in §5).
- The framework has no existing fail-closed path for missing
  `bootstrap.yaml` and adding one requires a new top-level error
  code (out of budget).
- `PrimaryPersonaContribution._startup()` invocation exhibits
  ordering problems once `_startup` no longer self-loads the
  workspace file (unlikely — ordering is preserved, but verify in
  AC4).
- Removing `require_bootstrap` breaks a YAML config file shipped in
  docs, examples, or a persona on the owner's machine that grep does
  not surface.
- Any AC test cannot be written deterministically (would require
  model inference or human judgment).
- The `hands-off-lifecycle` first-run state machine currently probes
  for `bootstrap.py` presence as part of its partial-scaffold
  detection — if so, this amendment scope expands non-trivially and
  re-scoping is required.

Any of the above: halt, signal to owner, re-scope before continuing.
