# Linux-removal amendment (amendment #10) — plan

**Status:** plan (written before any source edit, per HARD RULE #1).
**Branch:** `pos-v2` at HEAD `7d462e3`.
**Motivation rule:** `docs/odd-methodology.md` §2.5 — code without a backing
objective is an ODD violation; the structural fix is deletion.
**Owner ruling (2026-04-22):** only removal (option 1) is ODD-compliant.
Promoting Linux to an objective (option 2) or adding a structural-refusal
guard (option 3) both keep non-objective method in the shipped artifact.

No pos-v2 objective in the v1.0/v1.1/v1.2 spec names Linux as a supported
platform. Linux branches exist in the tree because "POSIX-ish shells make
it easy," not because any contract required them. This amendment deletes
them.

---

## 1. Objective

**Remove all code, tests, templates, and documentation in pos-v2 that
supports Linux / systemd / systemctl as a first-class target platform.**
The deliverable after this amendment supports macOS only. Any
non-macOS platform halts with a structural `platform-unsupported:<label>`
diagnostic — the same halt the code already produces for Windows today.

Historical and explanatory references to Linux (e.g. "amendment #6 AC3
was a Linux parity criterion, now superseded") remain in design-doc
prose as record of prior reasoning. Runtime code, tests, inventory
entries, and service-manager templates are removed.

---

## 2. Acceptance criteria

- **AC1** — `detect_platform()` and equivalents return only `"macos"` for
  supported runs; all other platform labels (including `"linux"`) route
  to the structural `PlatformUnsupportedError` halt.
- **AC2** — `_SYSTEMD_TEMPLATES` is removed from
  `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`;
  `_install_service_manager_files` has no `linux` branch;
  `ServiceManagerRunner.bootstrap` has no `linux` branch.
- **AC3** — `systemd_user_restart` and all dead systemd helpers are
  removed from `self-upgrade/src/self_upgrade/orchestrator_control.py`.
  The `/proc/<pid>/status` Linux-zombie-detection path is removed; the
  macOS `ps`-based detection is the sole implementation.
- **AC4** — `orchestrator/ops/systemd/` directory is removed. The sole
  remaining service-manager template directory is `orchestrator/ops/launchd/`.
- **AC5** — `memory-system/systemd/` directory is removed. The memory
  sidecar's service-manager template set is launchd-only.
- **AC6** — `test_H1_linux_writes_systemd_units`,
  `test_AC4_linux_stop_then_reload_then_start`,
  `test_platform_detection_returns_macos_or_linux`,
  `test_systemd_unit_renders_with_restart_always`,
  `test_systemd_throttle_locked_at_30s`, and any other Linux-branded
  tests are deleted. The module `orchestrator/tests/test_d2_launchd_systemd.py`
  is renamed to `test_d2_launchd.py` with systemd-targeted cases stripped.
- **AC7** — `hands-off-lifecycle/hooks/first_run_helper.py` has no
  Linux platform branch; `_detect_platform()` returns `"macos"` or a
  named unsupported label. The platform-unsupported diagnostic text no
  longer mentions WSL2 or Linux as a supported target.
- **AC8** — `hands-off-lifecycle/hooks/first-run.sh` Python-version-gate
  diagnostic lists macOS install instructions only; Ubuntu/Debian/Fedora
  lines are removed.
- **AC9** — `hands-off-lifecycle/hooks/first_run_scaffold_runner.py`
  argparse `help` strings drop systemctl / systemd-user references.
- **AC10** — `first-run-inventory.yaml` schema comment at line 23 names
  "launchd service label" only (no systemd alternate).
- **AC11** — Amendment #6 proposal (`docs/archive/component-research/namespaced-
  labels-and-bootout/proposal.md`) gains a superseded-by note on AC3
  (systemd unit naming) and the Linux portion of AC4; the text itself
  is preserved for historical record. No other design doc is edited in
  this amendment.
- **AC12** — Every amended component's test suite passes (regression-
  free). Counts must meet or exceed pre-amendment minima modulo the
  deleted Linux-branded tests.
- **AC13** — Seal-diff tests (`test_no_sealed_amendments.py` in each
  affected sealed component, `test_cross_cutting.py` in
  hands-off-lifecycle) pass post-amendment and post-seal-commit.
- **AC14** — `grep -rln "\\blinux\\b\\|systemd\\|systemctl"` across runtime
  source (.py, .sh, .tmpl, .yaml) outside the amendment's own plan
  file and explicit historical-marker notes returns zero hits.

ODD guard on the new ACs: each criterion names an outcome (function
returns X / directory absent / grep empty) rather than method. No AC
prescribes *how* the removal is implemented.

---

## 3. Constraints

- No new runtime dependencies.
- No code added except (a) minimal changes to turn two-branch
  dispatches into single-branch dispatches and (b) the superseded-by
  historical note on amendment #6's proposal.
- Net-delete expected.
- Tests updated to drop removed behaviours; no tests added that
  re-verify what the sealed artifact already covered.
- The hands-off-lifecycle open-for-amendment window is honoured —
  BASELINE in `test_cross_cutting.py` advances to `7d462e3` (current
  HEAD, the pre-amendment tip).
- The in-flight Blocker-3 unstaged set is left untouched (see §7).

---

## 4. Files to change

### Sealed-component source

| File | Category | Notes |
|---|---|---|
| `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` | simplify | remove `_SYSTEMD_TEMPLATES`, linux branch in `detect_platform`, `_install_service_manager_files`, `ServiceManagerRunner.bootstrap`; update docstrings + comments to drop systemd-user references |
| `self-upgrade/src/self_upgrade/orchestrator_control.py` | simplify | remove `systemd_user_restart`; remove `/proc` linux branch in `_pid_alive` (fall through to ps); update module docstring |
| `self-upgrade/src/self_upgrade/rollback.py` | simplify | drop "or systemd restart" from docstring |
| `orchestrator/scripts/pos_session_start.py` | simplify | drop linux branch in `detect_platform`, `ask_service_manager_to_start`, `run_session_start` gate; remove `systemd_user_labels` parameter; update module docstring + exit-code comments |
| `orchestrator/src/orchestrator.py` | simplify | drop "/systemd" from comment about auto-restart |

### Sealed-component tests

| File | Category | Notes |
|---|---|---|
| `workspace-bootstrap/tests/test_first_run_scaffold.py` | deletion | remove `test_H1_linux_writes_systemd_units` + `test_AC4_linux_stop_then_reload_then_start` |
| `orchestrator/tests/test_d2_launchd_systemd.py` → `test_d2_launchd.py` | deletion + rename | drop `_SYSTEMD_TMPL`, `_render_systemd`, `test_systemd_unit_renders_with_restart_always`, `test_systemd_throttle_locked_at_30s`; keep launchd tests |
| `orchestrator/tests/test_d7_restart_semantics.py` | simplify | docstring edit — drop `/systemd` |
| `orchestrator/tests/test_pos_session_start.py` | simplify | rename `test_platform_detection_returns_macos_or_linux`; drop linux expectation |

### Sealed-component templates

| File | Category | Notes |
|---|---|---|
| `orchestrator/ops/systemd/pos-orchestrator.service.tmpl` | deletion | file removed |
| `memory-system/systemd/pos-v2-memory-graphiti.service.tmpl` | deletion | file removed; `memory-system/systemd/` directory removed if empty |

### Hands-off-lifecycle

| File | Category | Notes |
|---|---|---|
| `hands-off-lifecycle/hooks/first_run_helper.py` | simplify | `_detect_platform` loses linux branch; Phase-4a platform check only accepts `"macos"`; diagnostic text drops "Windows is out of scope" Linux-fallback wording + systemd status hint |
| `hands-off-lifecycle/hooks/first_run_scaffold_runner.py` | simplify | argparse help strings drop systemctl + systemd-user mentions |
| `hands-off-lifecycle/hooks/first-run.sh` | simplify | diagnostic "Install Python 3.13" block drops Ubuntu/Debian/Fedora lines |
| `hands-off-lifecycle/README.md` | simplify | header table row "Linux systemd unit" → "launchd plist" |
| `hands-off-lifecycle/tests/test_pyyaml_reachability.py` | simplify | docstring at line 115 drops `"macos"` and `"linux"` enumeration |

### Inventory

| File | Category | Notes |
|---|---|---|
| `first-run-inventory.yaml` | simplify | schema comment "launchd/systemd service label" → "launchd service label" |

### Design docs (historical markers only)

| File | Category | Notes |
|---|---|---|
| `docs/archive/component-research/namespaced-labels-and-bootout/proposal.md` | historical marker | Append note to AC3 + AC4 marking the Linux branch superseded by amendment #10 |

Other design docs (`docs/archive/component-research/*/research.md`, `.../brief.md`,
`.../research-plan.md`) are left untouched. They are record of what was
considered during design; per the amendment brief they are not edited in
this amendment. A future docs-sweep amendment can trim them if desired.

### Seal tests (BASELINE advance)

| File | Category | Notes |
|---|---|---|
| `workspace-bootstrap/tests/test_no_sealed_amendments.py` | simplify | BASELINE: `a5dbf8f` → `7d462e3`; allowed prefixes update (add `self-upgrade/`, `memory-system/`, `docs/plans/`) |
| `orchestrator/tests/test_no_sealed_amendments.py` | simplify | BASELINE: `a5dbf8f` → `7d462e3`; allowed prefixes extended to include `self-upgrade/`, `memory-system/`, `docs/plans/`, `first-run-inventory.yaml` |
| `hands-off-lifecycle/tests/test_cross_cutting.py` | simplify | BASELINE: committed value `a5dbf8f` → `7d462e3`; append "self-upgrade" to allowed top-levels; "docs" + "first-run-inventory.yaml" already allowed |

The Blocker-3 unstaged BASELINE update to `9aeabd4` in test_cross_cutting.py
is visible on disk. Staging strategy: use `git add -p` / explicit hunk
selection so only the amendment's BASELINE advance (`a5dbf8f` →
`7d462e3`) lands in this commit, leaving Blocker-3's uncommitted
changes untouched. Blocker-3's later commit will supersede this when it
lands.

### Seal commit (separate commit)

| File | Category | Notes |
|---|---|---|
| `workspace-bootstrap/tests/SEAL_COMMIT` | update | set to amendment's code-commit SHA |
| `orchestrator/tests/SEAL_COMMIT` | update | set to amendment's code-commit SHA |
| `hands-off-lifecycle/tests/SEAL_COMMIT` | update | set to amendment's code-commit SHA |
| `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` | append | amendment-cycle note per precedent |

`self-upgrade` has no seal test or SEAL_COMMIT sidecar in-tree; no ritual.
`memory-system` has a SEAL_COMMIT sidecar but its `test_no_sealed_amendments.py`
is in the Blocker-3 unstaged set, which the amendment must not touch. The
memory-system systemd file is removed but the SEAL_COMMIT bump for
memory-system is deferred — the Blocker-3 amendment will advance the
memory-system baseline to cover both Blocker-3 and this amendment's
memory-system deletion when it commits.

---

## 5. Validation strategy

Per-component, after the code commit but before the seal commit:

1. `workspace-bootstrap`:
   - `cd workspace-bootstrap && .venv/bin/python -m pytest` → all pass
     (expect 2 fewer tests than prior baseline).
2. `orchestrator`:
   - `cd orchestrator && ../.venv/bin/python -m pytest` → all pass
     (expect ~3 fewer tests; `test_d2_launchd.py` still runs launchd
     cases).
3. `self-upgrade`:
   - `cd self-upgrade && ../.venv/bin/python -m pytest` → all pass.
4. `hands-off-lifecycle`:
   - `cd hands-off-lifecycle && ../.venv/bin/python -m pytest` → all
     pass.
5. Seal-diff tests specifically:
   - `pytest workspace-bootstrap/tests/test_no_sealed_amendments.py`
   - `pytest orchestrator/tests/test_no_sealed_amendments.py`
   - `pytest hands-off-lifecycle/tests/test_cross_cutting.py::test_H19_diff_scope_covers_only_approved_surfaces`
6. `grep` sweep (AC14):
   - `grep -rln "\\blinux\\b\\|systemd\\|systemctl" . --include="*.py" --include="*.sh" --include="*.tmpl" --include="*.yaml" | grep -v .venv | grep -v __pycache__ | grep -v docs/rebuild/ | grep -v docs/plans/linux-removal-amendment.md`
   - Expected: empty.

After the seal commit, re-run #5 to confirm SEAL_COMMIT sidecars point
at the amendment's code-commit SHA and seal-diffs pass with the updated
BASELINE.

---

## 6. Halt triggers

Halt and surface to owner (do not force through) if any of these fire:

- **H-load-bearing:** A Linux branch turns out to be routed for macOS
  through shared code (e.g. a helper that pretends to be generic but
  is actually used on macOS under a different name). Do not remove in
  that case.
- **H-coverage-loss:** A deleted Linux-branded test removes assertion
  coverage for a behaviour that is still a macOS AC — i.e. the test
  was the only reverse-direction assertion even though it was named
  after the Linux platform. In that case, the test must be renamed +
  re-pointed at macOS, not deleted.
- **H-sealed-invariant:** The grep surfaces a Linux reference inside a
  sealed component that encodes a sealed-spec invariant (e.g. a
  constant the sealed ACs name). Halt so owner can decide whether to
  extend the amendment scope.
- **H-scope:** Net-deleted LoC exceeds 500 or touched files exceed 20.
  Halt to re-size.

---

## 7. In-flight Blocker-3 handling (DO NOT list)

The following files carry uncommitted Blocker-3 work and must be left
unstaged by this amendment:

- `data/observability/spans.jsonl`
- `hands-off-lifecycle/README.md` (Blocker-3 has its own edit; this
  amendment needs a different edit here — we will stage only this
  amendment's hunk)
- `hands-off-lifecycle/tests/test_cross_cutting.py` (BASELINE advance —
  stage only this amendment's hunk)
- `memory-system/src/factory.py`
- `memory-system/src/process_of_arrival.py`
- `memory-system/tests/SEAL_COMMIT`
- `docs/archive/component-research/memory-system-*/` (untracked directories)
- `docs/archive/component-research/telegram-interface-framework-integration/`
  (untracked directory)
- `memory-system/src/claude_print_client.py` (untracked)
- `memory-system/tests/test_claude_print_client.py` (untracked)
- `memory-system/tests/test_no_sealed_amendments.py` (untracked)

Staging plan: use `git add -p` on the two shared files
(`hands-off-lifecycle/README.md`, `hands-off-lifecycle/tests/test_cross_cutting.py`)
to pick only this amendment's hunks; use explicit file lists (never
`git add -A` / `git add .`) for everything else.

---

## 8. Commit structure

**Code commit (SHA TBD):**
```
fix(workspace-bootstrap, orchestrator, self-upgrade, hands-off-lifecycle): remove non-objective Linux/systemd support (amendment #10)

Application of docs/odd-methodology.md §2.5 (codified in fd8c833).
Linux was never named as a supported-platform objective in the
v1.0/v1.1/v1.2 spec; the code existed incidentally. Per owner
ruling 2026-04-22, only deletion is ODD-compliant — options 2
(promote-to-objective) and 3 (structural-guard retrofit) both keep
non-objective method in the artifact.

Amendment #6's AC3 (systemd unit naming) and AC4 Linux branch are
formally superseded by this removal; the proposal retains the
text as historical record with a superseded-by marker.

(Full change summary: N files modified, net -LoC, seal-ritual for
workspace-bootstrap + orchestrator + hands-off-lifecycle. Tests
in each component still pass.)

Plan: docs/plans/linux-removal-amendment.md
```

**Seal commit (separate):**
```
chore(seals): linux-removal amendment seal — workspace-bootstrap + orchestrator + hands-off-lifecycle at <code-commit-sha>

Advances BASELINE in each affected seal test to the pre-amendment
tip (7d462e3) and updates SEAL_COMMIT sidecars to the amendment
code-commit SHA. Appends amendment-cycle note to
hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run.
```

Both commits plain (no `--amend`, no `--no-verify`). Plan file is
committed as part of the code commit, not separately.

---

## 9. ODD-compliance check (run at completion)

1. Every removed branch was traced back to "no backing objective" per
   §2.5 — documented in §4's table.
2. No new silent-exception branches introduced; `PlatformUnsupportedError`
   halt on non-macOS is the existing structural refusal, unchanged.
3. No method-in-acceptance in the new ACs — AC1..AC14 all name outcomes.
4. Tests assert outcome (macOS plists present, systemd directory absent,
   grep empty), not method.
5. Seal diffs are structural — BASELINE + SEAL_COMMIT sidecars only.
6. The amendment itself has a backing rule (§2.5) and the plan file
   traces every deletion to that rule.
