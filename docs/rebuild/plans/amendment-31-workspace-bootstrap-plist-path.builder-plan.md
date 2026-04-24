# Builder plan — Amendment #31 (workspace-bootstrap plist PATH)

Amendment number resolved: **#31** (next sequential after #30).
BASELINE: `795768cd87e7e923e976c9e2c28cce1b48c4c3d4` (amendment #30 seal tip).
Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`.

Authoring plan = the 1:1 mapping from every new source line and every
new test to a named D5.x acceptance criterion. Method decisions named
below are builder-call per ODD §1.1; every such choice maps to at
least one AC.

## 1. Criterion → code map (1:1)

### D5.1 (memory-graphiti /health reaches 200 end-to-end under scaffold plist)

Source lines satisfying D5.1:

- `_launchd_path()` helper in `first_run_scaffold.py` — returns the
  canonical PATH string per research §7.1 flagged-default
  (`~/.local/bin` expanded against `Path.home()` + the other fixed
  segments). Single source of truth for the PATH the scaffold trusts.
- Widening of `_LAUNCHD_TEMPLATES["memory-graphiti"]` — its
  `EnvironmentVariables` dict gains a `<key>PATH</key><string>{path}
  </string>` entry; `.format(..., path=_launchd_path())` supplies
  the value at emit time.

Test satisfying D5.1:

- `test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200`
  (new file `workspace-bootstrap/tests/test_D5_plist_path_emission.py`).
  Drives: scaffold a sandbox workspace → read the memory-graphiti
  plist → rewrite its `<key>Label</key>` to a UUID-unique sandbox
  label `com.pos-v2.d5-sandbox-<uuid>.memory-graphiti` (the
  label-uniqueness method avoids collision with currently-loaded
  services on the dispatch host) → `launchctl bootstrap gui/<uid>
  <plist>` → poll `http://<host>:<port>/health` (host/port read back
  from the memory.yaml the scaffold wrote) → assert HTTP 200 within
  the memory.yaml `startup_timeout_s` → bootout in teardown regardless
  of outcome. Method: plistlib parse/mutate (Label-only) + real
  launchctl + urllib polling. Outcome: `/health` = 200.
- Skip condition: `pytest.skip` if `claude` binary not on host PATH
  (CI hosts without claude installed) or memory-system venv absent —
  stays honest about the test's platform prereqs without making it
  marker-gated (§8 halt-trigger 3 only fires if determinism cannot
  be achieved; a clean skip when prereqs are absent is not a halt).

### D5.2 (orchestrator plist carries same PATH; parse-back equivalence)

Source lines satisfying D5.2:

- Widening of `_LAUNCHD_TEMPLATES["orchestrator"]` — its
  `EnvironmentVariables` dict gains a `<key>PATH</key><string>{path}
  </string>` entry; same `.format(path=_launchd_path())` seam so the
  two plists emit identical PATH by construction.

Test satisfying D5.2:

- `test_D5_2_orchestrator_plist_carries_same_path_as_memory_graphiti`
  (same file). Drives: scaffold one workspace → parse back both plists
  via plistlib → assert
  `plist_mg["EnvironmentVariables"]["PATH"] ==
   plist_orch["EnvironmentVariables"]["PATH"]` and that the string is
  non-empty. Outcome: parse-back equivalence of PATH string across both
  plists (research §7.3 ruling).

### D5.3 (per-plist exact-set env surface guard)

No additional source lines — same _LAUNCHD_TEMPLATES widenings from
D5.1+D5.2 cover emission.

Test satisfying D5.3:

- `test_D5_3_scaffold_plists_emit_exact_env_key_sets` (same file).
  Drives: scaffold one workspace → parse back both plists via plistlib
  → extract `set(plist["EnvironmentVariables"].keys())`. Assert:
    - memory-graphiti keys == `{"PYTHONUNBUFFERED",
      "GRAPHITI_SERVICE_HOST", "GRAPHITI_SERVICE_PORT",
      "POS_V2_WORKSPACE_ROOT", "PATH"}` (5 keys, matches amendment
      plan §D5.3 declaration).
    - orchestrator keys == `{"PYTHONUNBUFFERED", "PATH"}` (2 keys,
      matches amendment plan §D5.3 declaration).
  Outcome: structural anti-creep guard. Any unauthored key added in
  the future will fail this test.

### D5:S (seal-diff discipline)

Enforced by `workspace-bootstrap/tests/test_no_sealed_amendments.py`
BASELINE advance to `795768cd87e7e923e976c9e2c28cce1b48c4c3d4`.
The existing allowed_prefixes tuple already contains
`workspace-bootstrap/` and `docs/rebuild/plans/`, plus universal
files. No widening needed.

## 2. Hands-off-lifecycle: not joining the manifest

D5.1's launchctl-integration method lives entirely in the test file
via `subprocess.run(["launchctl", ...])`. No hands-off-lifecycle hooks
are touched; no fixture helpers imported from hands-off-lifecycle.
Manifest is single-component (`workspace-bootstrap` only).

## 3. Implementation order

1. Create `docs/rebuild/plans/amendment-31-workspace-bootstrap-plist-path.manifest.yaml`.
2. `pos-amend validate` on the manifest.
3. Pre-amendment captures: run `workspace-bootstrap` full test suite
   (all currently-passing), note pass count.
4. Edit `first_run_scaffold.py`:
   - Add `_launchd_path()` helper.
   - Widen both templates' `EnvironmentVariables` with `PATH`.
   - Wire `_launchd_path()` into the `.format(...)` call in
     `_install_service_manager_files`.
5. Create `workspace-bootstrap/tests/test_D5_plist_path_emission.py`
   with three `test_D5_*` functions.
6. Run `workspace-bootstrap` suite again — delta = pre-count + 3 new
   D5 tests, all green (D5.1 may skip on CI hosts without claude; on
   dispatch host should run).
7. Rename amendment plan doc to
   `amendment-31-workspace-bootstrap-plist-path.md` (from the
   unnumbered name) so the filename matches the manifest number.
8. `pos-amend apply --dry-run <manifest>` → exit 0.
9. Stage + commit: `fix(workspace-bootstrap): plist PATH emission —
   amendment #31`.
10. `pos-amend seal <manifest>` → advances SEAL_COMMIT sidecar to
    amendment SHA, writes narrative stanza.
11. Seal commit: `chore(seals): workspace-bootstrap-plist-path seal
    — workspace-bootstrap at <sha>`.
12. Post-seal: `pos-amend apply --dry-run` exit 0 verification.
13. Post-seal: seal-diff-only checks on other sealed components
    (just confirm BASELINE..SEAL_COMMIT diff for each is empty for
    anything outside the amendment surface — touched via running
    each component's `test_no_sealed_amendments.py` / equivalent).

## 4. Halt-trigger pre-check

- §8.1 cross-component scope: none — single-component amendment.
- §8.2 hands-off-lifecycle extension: none — no fixture imports.
- §8.3 seal-test non-determinism: D5.1's real-launchctl path is
  bounded by unique UUID labels + bootout-in-teardown + memory.yaml
  startup_timeout_s polling ceiling. Skip-when-claude-absent avoids
  forcing marker-gated status on hosts lacking prereqs. Determinism
  argued by inspection; if empirically flaky at run time, halt.
- §8.4 ODD break: every line maps to a D5 criterion; AC prose is
  outcome-shaped ("/health = 200", "PATH == PATH", "keys == {…}").
- §8.5 pos-amend apply --dry-run: to be verified before commit.
- §8.6 PATH-helper shape: defaulting to the canonical-list option
  from research §7.1 flagged-default. Not contentious.
- §8.7 launchd injection differs from research: host is the same
  macOS 26.3 Tahoe the research probed; D5.3's exact-set test is
  our empirical guard against host-drift.

## 5. PATH-helper shape (method decision)

```python
def _launchd_path() -> str:
    """Canonical PATH emitted into launchd plist EnvironmentVariables.

    Research §Q1 ruling: launchd's default `/usr/bin:/bin:/usr/sbin:
    /sbin` does not resolve user-installed binaries (notably `claude`
    under `~/.local/bin`). The scaffold emits the canonical ordered
    list from research §7.1 flagged-default; operator-overridable
    via a future memory.yaml field (not this amendment's scope).

    The user-home segment resolves against Path.home() at emit time
    so sandbox-rooted tests see their own home.
    """
    return ":".join([
        str(Path.home() / ".local" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ])
```

Outcome: single source of truth; both plists emit identical PATH;
parse-back equivalence (D5.2) is structural.

## 6. Commit boundary

- Amendment commit touches:
  - `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
  - `workspace-bootstrap/tests/test_D5_plist_path_emission.py` (new)
  - `workspace-bootstrap/tests/test_no_sealed_amendments.py` (BASELINE bump)
  - `docs/rebuild/plans/amendment-31-workspace-bootstrap-plist-path.manifest.yaml` (new)
  - `docs/rebuild/plans/amendment-31-workspace-bootstrap-plist-path.md` (rename from unnumbered file)
  - `docs/rebuild/plans/amendment-31-workspace-bootstrap-plist-path.builder-plan.md` (this file)
  - Research docs are already untracked; include under
    `docs/rebuild/plans/research/` in the same commit.

- Seal commit touches:
  - `workspace-bootstrap/tests/SEAL_COMMIT` (advance to amendment SHA)
  - `workspace-bootstrap/seals/SEAL_COMMIT.plist-path-emission` (narrative, new)

## 7. ODD §2.5 audit promise

Before seal, re-read the amendment diff and confirm for every new
source line: "which D5.x AC would fail if this line were deleted?"
If any line has no answer, halt and revisit.
