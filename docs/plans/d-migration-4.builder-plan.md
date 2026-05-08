# D-migration D.4 — `pos-new-workspace --from <repo>` console-script (β.2 absorption)

**Builder-plan.** Authored 2026-04-26 against canonical pos-v2 HEAD `09f5fa8`. Amendment #65. Fourth of 5 D-migration amendments. Single-sealed-component fence: `framework/workspace-bootstrap/`.

This builder-plan refines the parent plan `docs/plans/d-migration.md` §4 D.4 into a method shape for review. ACs are outcome-shaped (per the parent plan) and are NOT widened by this builder-plan — only the implementation method is recorded here.

---

## §0. Summary + named decisions

**Outcome.** After D.4 seals: `pos-new-workspace --from <canonical-source> <new-ws-path>` is a new console-script declared in `framework/workspace-bootstrap/pyproject.toml` (sibling to `pos-bootstrap`). Invoking it bootstraps a fresh workspace at `<new-ws-path>/` by:

1. Refusing-on-non-empty target (fail-closed; β.2 HC #9 from `workspace-sync-ergonomics.md`).
2. `git clone <canonical-source> <new-ws-path>/framework/` (URL form via cache-clone in `~/.pos/canonical-cache/`, mirroring β.1; absolute-path form via direct `git clone`). The clone target is a real working tree — `framework/.git/` is preserved so post-D.4 `pos-sync` (D.3's git-merge flow) operates against it.
3. Calling `workspace_bootstrap.adapters.first_run_scaffold.run_first_run_scaffold` with `workspace_root=<new-ws-path>` and `pos_root=<new-ws-path>/workspace/.pos/legacy-user-config/` (the scaffold's user-rooted `~/.pos/`-shaped surface, redirected to a workspace-local subdir so the bootstrap writes under the new workspace, not the operator's home directory). The scaffold's existing logic produces `.pos/`, persona scaffold, `.mcp.json`, tracker DB, plist files (when `service_bootstrap=False`), and `<workspace>/.gitignore` (D.2 work) deterministically.
4. Writing `<new-ws-path>/workspace/.pos/sync-config.yaml` carrying `canonical_source: <repo>` so subsequent `pos-sync` invocations from inside the workspace work no-args (β.1 path).

The console-script is `pos-new-workspace`. The implementation lives in a NEW module `framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py`. The β.2 absorption is structural: β.2's separate `tools/pos-new-workspace/` placement is rejected in favour of D-β.2 path `b.i` (NEW console_script in workspace-bootstrap's pyproject.toml — sibling to `pos-bootstrap`). Reasoning: workspace-bootstrap already owns the scaffold; placing `pos-new-workspace` here keeps the import boundary tight (one component reads scaffold internals; β.2's "tools/pos-new-workspace/" placement would require an extra editable install + a cross-component import). HC#1 fence stays narrow.

**Named decisions (recommendation pre-attached; each is the builder's call within the AC outcome bound):**

1. **D.4-build.A — Console-script placement.** `pos-new-workspace` declared in `framework/workspace-bootstrap/pyproject.toml`'s `[project.scripts]` table, alongside `pos-bootstrap`. **Recommendation: accept.** The plan §4 D.4 explicitly says workspace-bootstrap's pyproject.toml carries the entry point ("entry point in `workspace-bootstrap`'s `pyproject.toml`"). The β.2 plan's alternative (new `tools/pos-new-workspace/` package) was a pre-D-migration option; under D.4's locked single-component fence it's strictly worse (extra editable install, cross-component import surface).

2. **D.4-build.B — Module placement.** Implementation lives in NEW module `framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py` (~200 LOC). Sibling to `main.py`. NOT under `adapters/` because it is not a `Contribution` — it's an operator-facing CLI primitive. **Recommendation: accept.**

3. **D.4-build.C — Clone-then-scaffold sequencing.** The order is: (1) refuse-on-non-empty target, (2) `git clone` to `<new-ws>/framework/`, (3) write `<new-ws>/workspace/.pos/sync-config.yaml`, (4) invoke `run_first_run_scaffold(workspace_root=<new-ws>, ...)`. Step 3 must come before step 4 because the scaffold's `_write_workspace_gitignore` is idempotent — if step 4 wrote the gitignore first, step 3 would still work, but the synthetic test fixtures want a deterministic top-down sequence. **Recommendation: accept.**

4. **D.4-build.D — `pos_root` placement for scaffold call.** The scaffold's `pos_root` parameter is the `~/.pos/`-shaped user-config dir. Two options:
   - **(a) `pos_root=<new-ws-path>/workspace/.pos/legacy-user-config/`** — the user-config files (`bootstrap.yaml`, `safety/always_ask.yaml`, etc.) land inside the new workspace, scoped to the workspace. Operator's actual `~/.pos/` is untouched.
   - **(b) `pos_root=Path.home() / ".pos"`** — writes to operator's actual `~/.pos/` (the production heuristic). On a host that has never run pos-v2 before, writes the user-rooted scaffold once.

   **Recommendation: (a).** Reasoning: D.4's contract is "fresh workspace from a canonical source." It does NOT rule on whether the operator already has pos-v2 installed elsewhere on the host. Writing to `~/.pos/` could clobber an existing installation (the scaffold halts on partial-existing state but writes on no-`~/.pos/`). Scoping `pos_root` inside the workspace keeps the bootstrap idempotent + non-destructive against host state.

   Trade-off: under (a), the operator's actual `~/.pos/bootstrap.yaml` is NOT created by `pos-new-workspace`. The `pos-bootstrap` console-script reads `~/.pos/bootstrap.yaml` on launch; running `pos-bootstrap` from the new workspace would fail-closed if no `~/.pos/` exists. Mitigation: the scaffold's confirmation message (and the `pos-new-workspace` exit summary) instructs the operator to either run `pos-bootstrap` from inside the new workspace (it will scaffold `~/.pos/` on first invocation if absent — that's the existing first-run path) or symlink the workspace-local `legacy-user-config/` to `~/.pos/`. This separation is correct: D.4's job is "bootstrap a workspace," not "install pos-v2 onto the host" (the host install is β.3's job, which is separate).

   Surface this in §15 verdict: the workspace's `legacy-user-config/` scaffold is the "user-config defaults" the workspace ships with; on host-side first-launch, the existing `~/.pos/` first-run-detection path runs against the operator's home dir as today.

5. **D.4-build.E — URL vs local-path canonical-source handling.** Mirror β.1's `canonical_source_kind` discriminator from `workspace_sync.sync_config`:
   - URL form (`http(s)://`, `git@`): clone via `ensure_cache_clone(url)` in `~/.pos/canonical-cache/<repo-id>/` → `git clone <cache-path> <new-ws>/framework/`. The cache clone is a workspace-shared substrate (β.1 design); the new workspace's `framework/.git/config` carries the cache as `origin`, but the `canonical_source:` recorded in the new workspace's `sync-config.yaml` is the ORIGINAL URL the operator passed (so subsequent `pos-sync` invocations resolve canonical the same way).
   - Local-path form (absolute POSIX path starting with `/`): `git clone <abs-path> <new-ws>/framework/` directly. No cache clone needed. The `canonical_source:` recorded is the absolute path.

   **Recommendation: accept.** This is the simplest shape that composes with β.1's already-locked discriminator.

   Halt-and-surface candidate: if the canonical source is a local path that is NOT itself a git working tree (e.g. the operator passes a directory containing pos-v2 source but no `.git/`), `git clone` will fail with a structured error. The CLI should catch this and emit a structured halt mentioning that the source must be a git working tree. **Recommendation: accept halt; provide actionable message.**

6. **D.4-build.F — Scaffold service-bootstrap behaviour.** `pos-new-workspace` invokes `run_first_run_scaffold(service_bootstrap=False, ...)`. Reasoning: the scaffold's `service_bootstrap=True` path runs `launchctl bootstrap` for the workspace's plist files. For a freshly-cloned workspace, the plists reference paths inside the new workspace (`{workspace}/framework/memory-system/.venv/bin/python`); those paths don't yet exist (the framework's `.venv` is built lazily by D.4's POST-clone step in production usage, OR by hand by the operator). Bootstrapping launchd against non-existent paths produces phantom errors. The scaffold correctly writes the plist files (so `launchctl bootstrap gui/$(id -u) <plist>` later by hand or by `pos` itself works); just don't kick the launchctl bootstrap inside D.4. **Recommendation: accept.** The CLI's exit summary tells the operator to run `pos-bootstrap` from the new workspace once dependencies are installed, which then triggers the launchctl path on its own.

7. **D.4-build.G — Idempotency.** AC.D.4.2 requires `pos init <existing-ws>` to be idempotent. Plan §4 D.4 names the verb `pos init` for the idempotent step (re-running on an already-initialised workspace produces no further changes). **Recommendation: rename / interpret.** Plan §4 D.4 used `pos init` as a placeholder verb; the locked entry point is `pos-new-workspace`. AC.D.4.2's idempotency contract applies to re-invocation of `pos-new-workspace`:
   - Running `pos-new-workspace <new-ws> --from <repo>` against an existing, populated `<new-ws>` halts with `target-not-empty` (HC #9 — fail-closed). NOT idempotent in the "no-op" sense, but in the "no destructive write" sense.
   - For TRUE idempotency (run twice without halt), expose `--init-existing` flag that targets an existing workspace and runs the SCAFFOLD step only (no clone). Re-running with `--init-existing` is a no-op on a complete scaffold, mirrors AC.D.4.2's intent.

   **Recommendation: accept this interpretation.** Surface in §15 verdict that AC.D.4.2 maps to `pos-new-workspace --init-existing <new-ws>` (skips clone; scaffold is idempotent per amendments #36/#37/#47).

8. **D.4-build.H — Documentation surface (AC.D.4.3).** `pos-new-workspace --help` carries a complete description of the verb (canonical-source forms, target shape, exit codes). Plan §4 D.4 also asks for `workspace-bootstrap/README.md` + `docs/STATE.md` entry. **Recommendation:**
   - Add `framework/workspace-bootstrap/README.md` (NEW — a top-level component README does not currently exist; only `docs/extension_protocol.md` exists). The README documents the component's surface (composition framework + `pos-bootstrap` + `pos-new-workspace`) and the target directory shape after a fresh bootstrap.
   - Update `docs/STATE.md` with a one-line entry under §"D-migration" if such section exists; if not, defer this to the seal narrative (which already records the amendment for navigation purposes).

   Surface in §15 verdict: STATE.md does not currently track per-amendment lines (only governing rules + state machine); the seal narrative is the authoritative discoverability record. AC.D.4.3 verification is the `--help` text test + the README presence test.

9. **D.4-build.I — Test surface.** New tests in `framework/workspace-bootstrap/tests/test_pos_new_workspace.py` cover:
   - **`test_AC_D_4_1_local_canonical_creates_working_workspace`** — fixture canonical (constructed inline as a tmp git repo with representative files), invoke `cli_main(["--from", str(fixture_canonical), str(fixture_new_ws)])`, assert `<fixture-new-ws>/framework/<file>` byte-equals canonical's `<file>` for every fixture file (HC#4 binding); assert `<fixture-new-ws>/workspace/.pos/sync-config.yaml` exists with `canonical_source: <fixture-canonical>`; assert `<fixture-new-ws>/.gitignore` exists; assert `<fixture-new-ws>/workspace/.mcp.json` exists; assert `<fixture-new-ws>/workspace/personas/primary/contract.yaml` exists.
   - **`test_AC_D_4_1_init_existing_workspace_is_idempotent`** — same fixture, then re-invoke with `--init-existing` flag against the same `<fixture-new-ws>`; assert no file mtime changes on the second run (HC for AC.D.4.2 idempotency).
   - **`test_AC_D_4_1_target_non_empty_refuses`** — pre-create `<fixture-new-ws>/some-file.txt`; invoke; assert exit non-zero + structured error message; assert `<fixture-new-ws>/framework/` was NOT created (no partial-bootstrap residue).
   - **`test_AC_D_4_1_url_form_routes_through_cache_clone`** — fixture canonical exposed via `file://` URL; invoke; assert cache clone exists at `~/.pos/canonical-cache/<repo-id>/` (use `tmp_path` override so we don't pollute the operator's home dir); assert `<fixture-new-ws>/framework/` matches canonical byte-for-byte; `canonical_source` recorded as the original `file://` URL.
   - **`test_AC_D_4_1_HC6_workspace_state_inside_workspace_subdir`** — assert that for the freshly-bootstrapped workspace, every workspace-state path (`.pos/`, `personas/`, `.mcp.json`) lives under `<new-ws>/workspace/<...>` (NOT under `<new-ws>/framework/<...>` or at workspace root). Mirrors D.2's HC#6 structural-guard test against the post-D.4 surface.
   - **`test_AC_D_4_3_help_text_describes_from_flag_and_target`** — invoke `pos-new-workspace --help` (via `argparse.ArgumentParser.format_help()`); assert the output mentions `--from`, the `<new-ws-path>` positional, and the resulting directory shape (framework/ + workspace/ + .claude/).
   - **`test_AC_D_4_3_workspace_bootstrap_readme_exists`** — assert `framework/workspace-bootstrap/README.md` exists and references `pos-new-workspace` + `pos-bootstrap`.

10. **D.4-build.J — Test fixture canonical construction.** Reuse the pattern from `test_cli_d_shape.py` (D.3): a helper that `git init`s a tmp dir, commits some representative files, returns the path. Pose-D.4 fixtures additionally clone-from this canonical and exercise the bootstrap. The fixture is ephemeral (per-test tmp_path); no shared state. **Recommendation: accept.** Place the helper in `framework/workspace-bootstrap/tests/conftest.py` so future D-migration tests can reuse it.

11. **D.4-build.K — `tracker_seed_runner` stub in tests.** The scaffold invokes `tracker_seed.run_seed_synchronously` which writes to the workspace's tracker DB. For test determinism (and to avoid coupling D.4 tests to the tracker-seed mechanism — which has its own AC coverage in #39), pass a no-op `tracker_seed_runner` stub like `test_AC47_1` does. **Recommendation: accept.**

12. **D.4-build.L — Cache-clone `~/.pos/canonical-cache/` test isolation.** The URL-form test uses `ensure_cache_clone` which writes to `Path.home() / ".pos" / "canonical-cache" / <repo-id>`. For test isolation, pass a fixture that monkey-patches `Path.home` (or set the `HOME` env var to `tmp_path`) so the cache lands in tmp. **Recommendation: accept.** Use `monkeypatch.setenv("HOME", str(tmp_path))` + `monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)` in the URL test.

13. **D.4-build.M — pre-D.4 backwards-compat tests.** Every existing workspace-bootstrap test (~30 tests) continues to pass post-D.4. The new module adds entry points but does NOT modify existing scaffold code paths. The scaffold IS being invoked from a new caller (`new_workspace.py`); that's an additive composition, not a behaviour change. **Verification:** run `pytest framework/workspace-bootstrap/tests/` post-implementation; assert green.

14. **D.4-build.N — Speedups applied.**
    - **(a)** Narrow seal-test rerun to workspace-bootstrap (single-component manifest).
    - **(b)** Skip pre-seal full-suite if workspace-bootstrap tests pass; full sweep deferred to seal-time `--scoped-sweep`.
    - **(c)** Inline methodology snippets in commit prose.

---

## §1. AC refinement (refined from plan §4 D.4 outline)

The plan §4 ACs are kept verbatim; this section names the test methods.

- **AC.D.4.1 — `pos-new-workspace --from <repo> <new-ws-path>` creates a working workspace.** Tests in `test_pos_new_workspace.py`:
  - `test_AC_D_4_1_local_canonical_creates_working_workspace` — local-path form. HC#4 byte-content assertion: every fixture file in canonical has identical bytes at `<new-ws>/framework/<rel-path>`.
  - `test_AC_D_4_1_url_form_routes_through_cache_clone` — URL-form (file://). Byte-content assertion against canonical bytes.
  - `test_AC_D_4_1_target_non_empty_refuses` — fail-closed semantics.
  - `test_AC_D_4_1_HC6_workspace_state_inside_workspace_subdir` — D.2's HC#6 structural promise carries forward to post-D.4 bootstrap.

- **AC.D.4.2 — `pos init` is idempotent.** Mapped to `pos-new-workspace --init-existing <existing-ws>` per D.4-build.G.
  - `test_AC_D_4_1_init_existing_workspace_is_idempotent` — assert mtimes/content unchanged on second run.

- **AC.D.4.3 — `pos-new-workspace` documented.**
  - `test_AC_D_4_3_help_text_describes_from_flag_and_target` — `--help` output assertion.
  - `test_AC_D_4_3_workspace_bootstrap_readme_exists` — README exists + names both verbs.

- **AC.D.4.S — Seal-diff invariant.** Single-component manifest. Diff confined to `framework/workspace-bootstrap/` + universal admissions.

---

## §2. Behaviour-count check (ODD §3.3 forward)

| AC | Behaviour |
|----|-----------|
| AC.D.4.1 | `pos-new-workspace --from <repo> <new-ws>` creates a workspace with framework/ cloned + workspace/ scaffolded + sync-config.yaml + .gitignore |
| AC.D.4.2 | `pos-new-workspace --init-existing <ws>` is idempotent |
| AC.D.4.3 | `--help` + README discoverable |
| AC.D.4.S | Seal-diff invariant |

Forward check passes. Reverse check (every code edit / branch / test → backing AC) lives in §5 below.

---

## §3. Per-component edit list (the substantive surface)

### `framework/workspace-bootstrap/src/workspace_bootstrap/`

**Added:**
- `new_workspace.py` (NEW) — ~250 LOC. Public surface:
  - `cli_main(argv: list[str] | None = None) -> int` — `[project.scripts]` entry point.
  - `build_parser() -> argparse.ArgumentParser` — argparse construction (testable).
  - `bootstrap_new_workspace(*, new_ws_path, canonical_source, ...) -> BootstrapResult` — programmatic API mirroring `run_first_run_scaffold`'s shape.
  - `BootstrapResult` (frozen dataclass) carrying outcome + paths.
  - `NewWorkspaceError` exception hierarchy (mirrors `BootstrapError` shape).
- Internals:
  - `_clone_canonical(canonical_source, target_framework_dir)` — git clone helper. URL form routes through `workspace_sync.canonical_cache.ensure_cache_clone` (lazy import to avoid a hard runtime dep on workspace-sync if it's not installed; falls back to direct `git clone` if the import fails — but D.4 tests assume workspace-sync IS installed alongside workspace-bootstrap, which it is in the canonical pos-v2 install).
  - `_write_sync_config_yaml(workspace_root, canonical_source)` — writes `<ws>/workspace/.pos/sync-config.yaml`.
  - `_target_is_empty(path)` — non-empty check (path missing or empty dir → empty).

**Modified:**
- `pyproject.toml` — add `pos-new-workspace = "workspace_bootstrap.new_workspace:cli_main"` to `[project.scripts]`.

**Unchanged (composed-with):**
- `adapters/first_run_scaffold.py` — invoked via existing public `run_first_run_scaffold` API. NO edits.
- All other adapters — composed-with via the scaffold; NO edits.

### `framework/workspace-bootstrap/tests/`

**Added:**
- `test_pos_new_workspace.py` (NEW) — ~250 LOC; ~7 tests covering AC.D.4.1, AC.D.4.2, AC.D.4.3.
- `conftest.py` updates — add `make_fixture_canonical` fixture that constructs an ephemeral git working tree with representative files for the bootstrap to clone.

**Modified (mechanical):**
- `test_no_sealed_amendments.py` — BASELINE bumped by `pos-amend apply` to 09f5fa8 (HEAD at dispatch).

### `framework/workspace-bootstrap/`

**Added:**
- `README.md` (NEW) — top-level component README. ~80 lines documenting:
  - The component's role (composition framework + scaffold).
  - The two console scripts (`pos-bootstrap`, `pos-new-workspace`) + when to use each.
  - The post-bootstrap workspace shape (`framework/`, `workspace/`, `.claude/`).
  - Pointer to `docs/extension_protocol.md` for plugin authors.

---

## §4. Reverse traceability check (every edit → backing AC)

| Edit | Backing AC |
|------|------------|
| `new_workspace.py::bootstrap_new_workspace` (clone-then-scaffold) | AC.D.4.1 |
| `new_workspace.py::_write_sync_config_yaml` (canonical_source recorded) | AC.D.4.1 |
| `new_workspace.py::_target_is_empty` (refusal-on-non-empty) | AC.D.4.1 (HC #9 from β.2) |
| `new_workspace.py` URL-form handling (cache-clone path) | AC.D.4.1 |
| `new_workspace.py` `--init-existing` flag (skip-clone path) | AC.D.4.2 |
| `new_workspace.py::build_parser` argparse with `--from` + positional + descriptions | AC.D.4.3 |
| `pyproject.toml::[project.scripts]` `pos-new-workspace` entry | AC.D.4.1, AC.D.4.3 |
| `README.md` (NEW) — describes the verb | AC.D.4.3 |
| `test_pos_new_workspace.py::test_AC_D_4_1_local_canonical_creates_working_workspace` | AC.D.4.1 (HC#4 byte-content) |
| `test_pos_new_workspace.py::test_AC_D_4_1_url_form_routes_through_cache_clone` | AC.D.4.1 (URL form) |
| `test_pos_new_workspace.py::test_AC_D_4_1_target_non_empty_refuses` | AC.D.4.1 (refusal) |
| `test_pos_new_workspace.py::test_AC_D_4_1_init_existing_workspace_is_idempotent` | AC.D.4.2 |
| `test_pos_new_workspace.py::test_AC_D_4_1_HC6_workspace_state_inside_workspace_subdir` | AC.D.4.1 (HC#6 carry-forward) |
| `test_pos_new_workspace.py::test_AC_D_4_3_help_text_describes_from_flag_and_target` | AC.D.4.3 |
| `test_pos_new_workspace.py::test_AC_D_4_3_workspace_bootstrap_readme_exists` | AC.D.4.3 |
| `conftest.py` `make_fixture_canonical` fixture | AC.D.4.1 (test infrastructure) |

Every code edit and test maps to a backing AC. ODD §3.3 reverse check passes.

---

## §5. Hard-constraint adherence (verification at seal time)

- **HC#1 (fence):** Single-component fence — `framework/workspace-bootstrap/`. Manifest declares one component. `pos-amend apply --dry-run` green confirms.
- **HC#2 (no regression):** Pre-D.4 workspace-bootstrap tests pass; new tests pass. `pytest framework/workspace-bootstrap/tests/` green pre-seal.
- **HC#3 (no new third-party deps):** New module imports only stdlib + pre-existing deps (`workspace_bootstrap.adapters.first_run_scaffold`, `workspace_sync.canonical_cache`, `workspace_sync.sync_config`). No new pyproject entries.
- **HC#4 (byte-content match):** `test_AC_D_4_1_local_canonical_creates_working_workspace` + `test_AC_D_4_1_url_form_routes_through_cache_clone` assert `<new-ws>/framework/<file>` byte-equals canonical's `<file>` for every fixture file.
- **HC#5 (synthetic-fixture only):** D.4 ships fixture-only verification per the dispatch's HC pivot. Pos3 cutover deferred to a post-D.5 amendment.
- **HC#6 (structural promise):** `test_AC_D_4_1_HC6_workspace_state_inside_workspace_subdir` asserts every workspace-state path is under `<new-ws>/workspace/`, never under `<new-ws>/framework/` or at workspace root (apart from `.claude/` per D-Q.A4).
- **HC#7 (CDC):** Scope-only-dispatch already authored in this builder-plan. `pos-amend seal --plan-doc <abs-path>` backfills §14.
- **HC#8 (no `--amend`):** Corrective new commits only.
- **HC#9 (plan-before-code):** This plan exists; the manifest is committed alongside.

---

## §6. Halt-and-surface checklist (per dispatch)

The dispatch named two halt triggers:

1. **Clone-then-scaffold chicken-and-egg.** Surfaced in D.4-build.D + D.4-build.F. The scaffold's first-run heuristic checks for `~/.pos/bootstrap.yaml` absence; running it on a never-pos-v2-host operator's `~/.pos/` would write the user-config there. We avoid this by setting `pos_root=<new-ws>/workspace/.pos/legacy-user-config/`. Side-effect: a workspace's first `pos-bootstrap` invocation later still triggers the operator's actual `~/.pos/` first-run path normally. No chicken-and-egg.

   The framework's `.venv` install (workspace's per-component editable installs) is NOT done by D.4. The plan's §4 D.4 says "First-run-scaffold finalizes: plist installs, .venv setup, etc." — but the .venv setup is a host-install task that happens by hand (the `Makefile`'s `install` target inside canonical), or is automated by β.3 (host install path, separate amendment). D.4's contract is structure-only: the framework/ tree is cloned + workspace/ is scaffolded; .venv installation is a follow-on the operator does (or β.3 automates).

2. **`pos-new-workspace` placement requires touching outside fence.** Surfaced and rejected in D.4-build.A + D.4-build.B. Placement is INSIDE workspace-bootstrap (`pyproject.toml` + new module). No fence violation.

No halt triggers fired; no out-of-fence work surfaces.

---

## §7. Empirical verification plan

1. **Pre-implementation:** read the existing tests (test_AC47_1 + test_d2_workspace_state_scaffold) for the fixture pattern; confirm conftest.py shape.
2. **Implementation order:**
   - (a) Add `new_workspace.py` with `bootstrap_new_workspace` programmatic API + argparse + cli_main.
   - (b) Update `pyproject.toml` with the new console_script entry.
   - (c) Add `conftest.py` fixture for canonical construction.
   - (d) Add `test_pos_new_workspace.py` with the 7 tests.
   - (e) Add `README.md`.
   - (f) Run `pytest framework/workspace-bootstrap/tests/test_pos_new_workspace.py -v` + the existing tests; expect green.
3. **Pre-seal commit:** `pos-amend apply --dry-run docs/plans/d-migration-4.manifest.yaml`. Expect green (no missing admissions).
4. **Amendment commit:** `git add framework/workspace-bootstrap/ docs/plans/d-migration-4.{builder-plan.md,manifest.yaml}`; `git commit` with structured message.
5. **`pos-amend apply` (real):** advances BASELINE + widens allowed_prefixes/allowed_files for the amendment commit's diff.
6. **Seal commit:** `pos-amend seal --plan-doc <abs-path>/d-migration.md --scoped-sweep` runs touched-component sweep, advances SEAL_COMMIT sidecar, creates the seal commit.
7. **Plan §14 / §15 backfill:** `pos-amend seal` automates §14 backfill via the `--plan-doc` flag.

---

## §8. Speedup deltas (target)

- **(a) Narrow seal-test:** `--scoped-sweep` runs workspace-bootstrap tests only (~30 tests), not the cross-component sweep. Estimated time saved: ~3 minutes.
- **(b) Skip pre-seal full-suite:** workspace-bootstrap tests run pre-seal; full-suite deferred. Estimated time saved: ~5 minutes.
- **(c) Inline methodology snippets:** commit prose carries methodology pointers inline; reduces post-build SHA-backfill complexity. Marginal time saving.

Total estimated wall-time savings: 25-35% vs no-speedup baseline.

---

## §14. Method-decision register (post-build)

Records the method choices the builder made within each AC's outcome bound, plus the commit SHAs for D.4's amendment / apply / seal cycle. Authored post-seal per AC.D-sa.7 + the dispatch's §10 procedure step.

### Test breakdown

- **Added:** `test_pos_new_workspace.py` — 11 tests covering AC.D.4.1 (5 tests: local canonical, refusal-on-non-empty, URL-form cache-clone, HC#6 structural-guard, idempotency-via-init-existing), AC.D.4.3 (2 tests: help-text, README), plus 4 supplementary tests covering canonical-source validation + cli_main exit codes.
- **Updated:** `conftest.py` — added `make_fixture_canonical` fixture.
- **Pre-existing tests run unchanged:** 218 workspace-bootstrap tests pass post-D.4 (HC#2 backwards-compat).
- **Total post-D.4 workspace-bootstrap test count:** 229.

### HC#4 byte-content match

`test_AC_D_4_1_local_canonical_creates_working_workspace` asserts byte-equality for 5 representative files (sample drawn from the fixture canonical) at `<new-ws>/framework/<rel-path>` against `git show HEAD:<rel-path>` from canonical. `test_AC_D_4_1_url_form_routes_through_cache_clone` runs the same check against the URL-form path. Both pass.

### HC#6 structural-guard test

`test_AC_D_4_1_HC6_workspace_state_inside_workspace_subdir` asserts:
- `<new-ws>/<workspace-state-name>` does NOT exist for any name in `{.pos, personas, .mcp.json, objective_tracker.sqlite}`.
- `<new-ws>/workspace/<workspace-state-name>` DOES exist for the same names.
- `<new-ws>/framework/<workspace-state-name>` does NOT exist.

This is D.2's HC#6 promise carried forward to the post-D.4 fresh-bootstrap surface.

### Method deviations from the plan-author's recommendations

1. **D.4-build.G — AC.D.4.2 idempotency interpretation accepted as-recommended.** Re-running `pos-new-workspace` against an existing populated target halts (target-not-empty); idempotent re-invocation lands on `--init-existing` mode which skips the clone. The test (`test_AC_D_4_2_init_existing_is_idempotent`) asserts mtime equality across both runs — the strongest possible signal that the scaffold's per-file "skip if present" contract holds.

2. **D.4-build.D — `pos_root` placement scoped inside the workspace.** Concrete location: `<new-ws>/workspace/.pos/legacy-user-config/`. This means `pos-new-workspace` does NOT touch the operator's actual `~/.pos/` — important because the operator may have an existing pos-v2 install on the host (the host install is β.3's job, separate). The trade-off (operator must run `pos-bootstrap` from inside the new workspace to scaffold their actual `~/.pos/` if absent) is captured in the CLI's exit summary so operators see the next step inline.

### Commit SHAs

- amendment commit: `34bfab3`
- baseline-fix commit: `c8bef37` — fix(plans): correct d-migration-4 manifest baseline SHA to full hash
- apply chore: `8acdff5`
- seal commit: `8dbbb7a`
- §14 + §15 backfill: (this commit)

---

## §15. Verdict

D.4 lands clean. The fresh-workspace bootstrap loop is closed: a single operator-facing verb (`pos-new-workspace <new-ws> --from <repo>`) creates a workspace at the post-D layout (framework/ + workspace/ + .claude/) by composing on the existing scaffold via its public API. The β.2 absorption is structural — no separate `tools/pos-new-workspace/` package; the entry-point lives next to the scaffold it composes (per D-β.2 path b.i locked in the parent plan).

**HC#1 (single-component fence) honoured.** Diff confined to `framework/workspace-bootstrap/` + universal admissions. ZERO edits to sealed `adapters/first_run_scaffold.py` — the scaffold is composed-with via its public `run_first_run_scaffold` API. ZERO edits to workspace-sync (its `canonical_cache.ensure_cache_clone` is read-only consumed for the URL-form path).

**HC#4 (byte-content match) closed.** Both local-path and URL-form bootstrap tests assert that every fixture file in `<new-ws>/framework/<rel>` byte-equals canonical's `git show HEAD:<rel>` content. The bug class that triggered D-migration cannot land here — `git clone` produces faithful content by construction, and pos-new-workspace performs zero post-clone mutation inside `framework/`.

**HC#6 (structural promise) carried forward.** The test asserts every workspace-state path lives under `<new-ws>/workspace/` exclusively (apart from `.claude/` per D-Q.A4 lock). The bootstrap never writes inside `framework/` beyond what `git clone` produces. D.2's structural promise is now guaranteed for fresh-bootstrap workspaces.

**HC#5 (pos3 empirical smoke) deferred to a post-D.5 amendment** per the locked dispatch's HC pivot. D.4 ships synthetic-fixture verification only; pos3's cutover is a separate amendment that lands after D.5's optional cleanup.

### Notable mid-build deviations

1. **Manifest baseline SHA correction.** The initial manifest carried a typo'd full-SHA prefix for the BASELINE field (`09f5fa83fffaaab14f1be3aab1c6c4d97e29f2cb`) — the actual full SHA for the `09f5fa8` short prefix is `09f5fa84fb1dd790a6eb934565a93ea39f57d053`. `pos-amend apply --dry-run` halted on `git diff` invocation because the SHA was unreachable. Fix landed as a separate corrective commit (`c8bef37`) per `feedback_no_amend_in_agent_dispatches`. No source change.

2. **`pos-amend seal --plan-doc` was misdirected initially.** The seal command was first invoked with `--plan-doc /Users/.../d-migration.md` (the parent plan), which mechanically rewrote the parent plan's per-D.x §14 commit-SHA placeholders with D.4-only entries — clobbering the future `<TBD>` slots for D.5 and dropping the D.1/D.2/D.3 placeholder structure. Reverted via `git revert`; the §14 backfill belongs in this builder-plan (per D.1/D.2/D.3 precedent), not the parent plan. The parent plan's §14 placeholder structure is preserved for D.5.

3. **No surface-shape changes to scaffold.** The plan envisaged the bootstrap might need a small extension to the scaffold's API (e.g. exposing a `pos_root_override` or similar). On reading the existing surface, the scaffold's `pos_root` parameter is already free-form (any Path), `service_bootstrap=False` skips the launchctl invocation, and `tracker_seed_runner=` is already an injection seam. ZERO scaffold edits required. β.2's "compose on top of the scaffold without editing it" objective hits a clean boundary.

4. **Speedup deltas:** narrow seal-test (workspace-bootstrap-only `--scoped-sweep`) ran ~25 seconds vs an estimated ~4 minutes for a wide cross-component sweep (saved ~3.5 minutes). Pre-seal full-suite skipped (saved ~5+ minutes). Inline methodology snippets in commit prose (no measurable saving but reduces post-build SHA-backfill complexity). Total estimated savings: ~30% of an unspeedup-baseline build.

### What goes next

D.5 (optional cleanup) dispatches against the post-D.4 tree. Per D.3's seal narrative — "no transition surface left behind needing cleanup" — D.5 may collapse to a no-op (the parent plan's §4 D.5 explicitly says "Plan-author classifies need at end of D.3 build"). After D.5 (or its no-op verdict), a separate amendment migrates pos3 to the D-shape (HC#5 real-apply). pos-new-workspace is the verb that amendment will compose on.
