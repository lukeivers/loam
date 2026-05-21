# FBE.1 sub-plan — `loam init` as a registered subcommand (NEW component `loam-init`)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` §4 FBE.1.
**Programme master:** `docs/plans/oss-v0-1-0-publish.md`.
**BASELINE:** `f0c4aa9` — current canonical HEAD pre-FBE.1.

---

## 1. Summary / TLDR

Land a NEW component `framework/loam-init/` that exposes `loam init <path> --from <canonical-source>` as a `loam.cli.subcommands` entry-point. The builder constructs an argparse parser whose action calls the existing
`loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace(...)` function. Additive only: zero edits to `loam_cli/cli.py` (entry-point discovery is the contract) and zero edits to `bootstrap_new_workspace`'s signature or behaviour. Closes BLOCKER 1 of the v0.1.0 reviewer foldback.

The amendment seals as a single new sealed component (`loam-init`) — the seal-test invariant lives at `framework/loam-init/tests/test_no_sealed_amendments.py` (new), pinned via the standard sidecar pattern.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (admit; explained)
**The new component requires partition admission.** Adding `framework/loam-init/` under canonical `framework/` audit_root means the partition manifest at `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` MUST gain a `dev_and_public` glob entry for `framework/loam-init/**`, otherwise the audit-completeness test (`framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py`) fails for canonical `pos-v2` HEAD as soon as the new files are committed.

Parent plan §4 FBE.1.S allowed a fence extension if a shim was needed, by analogy. Per the multi-signal conflict-resolution principle:
- **Reversibility:** high (single glob line; trivial revert).
- **Blast radius:** tiny (zero behaviour change to publish pipeline; just classifies the new path).
- **Information asymmetry:** parent plan author covered partition reclassification at FBE.2 (existing components moving class) but did not enumerate this admission for FBE.1's new component; the omission appears unintentional.
- **Alternative considered:** defer admission to FBE.2 — rejected because (a) the audit-completeness test fails immediately on FBE.1 commit, (b) FBE.2 might be parallel-built and would race, (c) FBE.1 is physically un-sealable without it.

**Resolution autonomous-call (per "asymmetric problem solving" + tight-scope-at-build-time):** include the partition-manifest single-line admission in FBE.1's structural diff via `universal_paths.prefixes: framework/tools/pos-publish-framework-only/` in the manifest YAML — the SAME pattern used by `oss-v0-1-0-publish-public-docs-partition-fix.manifest.yaml` (M7-partition-fix amendment #98). The fence stays at `framework/loam-init/` (sealed component anchor); the partition-manifest edit rides via universal_paths admission, exactly like M7-partition-fix.

### Surface #2 (no halt; recorded)
The `loam_cli` dispatcher's discovery loop carries four `# pragma: no cover — defensive` exception branches (cli.py:74, 84, 92, 128) that emit `_LOGGER.warning(...)`. Per parent plan §6 Risk 4, these are graceful-fallthrough-with-detection (M6c CDC-honoured) — NOT ODD §2.5 violations. They will not affect FBE.1; documented for the record so a downstream agent doesn't re-surface.

### Surface #3 (no halt; recorded)
The `bootstrap_new_workspace` public API (verified at `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:420-586`) is sufficient for the wrapper without any reach into private internals. Keyword-only signature; supports `new_ws_path: Path`, `canonical_source: str`, `init_existing: bool`, `persona_handle: str`. The exit-code mapping convention from `cli_main` (1=target-not-empty, 2=invalid-source, 3=clone-fail, 4=scaffold-fail, 5=other) is the authoritative shape FBE.1 mirrors.

### Surface #4 (no halt; recorded)
**Tight-scope decision on the auto-source-detection AC.** Parent plan AC.FBE.1.3 reads "with the user-supplied path argument and `--from <canonical>` either resolved from the cloned `framework/` checkout's git remote OR explicit `--from URL`". This is genuinely loose — auto-resolving canonical from a cloned framework/'s git remote is a NEW capability not present in `bootstrap_new_workspace` today. Building it inside FBE.1's wrapper would (a) blow scope, (b) duplicate logic that belongs inside `bootstrap_new_workspace` (which fails ODD §2.5 — duplication of a substrate primitive). Per `feedback_loose_AC_text_fix_AC_not_implementation`, **tighten the AC to explicit `--from` only for FBE.1**; the auto-detect variant defers to a future amendment if/when needed. Recorded in §4 below.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — making the documented `loam init` verb actually exist is a prerequisite for the harness's "primary persona translates intent → execution" promise.
- **Reviewer foldback BLOCKER 1** — `loam init` is the documented verb; FBE.1 closes it.
- **AC.OSS-M6.5** (parent plan §1) — the `loam.cli.subcommands` entry-point group exists today (registered by dev-sdlc); FBE.1 adds the second registrant under that pattern.

**Ladders to:** AC.FBE.1.* → AC.OSS.6 (final scrub; FBE.5) → AC.OSS-M11a (reviewer GO; FBE.6) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.1.*)

AC family **`AC.FBE.1.*`** — collision-safe (verified: `grep -rE "AC\.FBE\.1" docs/` returns only the parent foldback plan-doc + this sub-plan).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.1.1** | NEW directory `framework/loam-init/` exists with `pyproject.toml` (package `loam-init`, version `0.1.0`), `src/loam/loam_init/{__init__.py,cli.py}`, and a tests subtree. | `ls framework/loam-init/{pyproject.toml,src/loam/loam_init/__init__.py,src/loam/loam_init/cli.py,tests/}` |
| **AC.FBE.1.2** | `framework/loam-init/pyproject.toml` declares `[project.entry-points."loam.cli.subcommands"] init = "loam.loam_init.cli:build_init_subcommand"`. | `grep -A2 'loam.cli.subcommands' framework/loam-init/pyproject.toml` |
| **AC.FBE.1.3** | `loam.loam_init.cli.build_init_subcommand(sub)` registers an argparse parser whose default action invokes `loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace` with the user's positional `<path>` + required `--from <canonical-source>` (URL or absolute local path) + optional `--persona-handle` + optional `--init-existing`. **Tightened from parent plan loose text per §2 Surface #4: NO auto-detect-from-framework-remote in FBE.1.** | Unit test `test_AC_FBE_1_3_builder_wires_bootstrap.py` patches `bootstrap_new_workspace`; asserts call shape + kwargs. |
| **AC.FBE.1.4** | After `pip install -e framework/loam-init/` in a venv that already has `loam-cli` + `loam-workspace-bootstrap` installed editable, `importlib.metadata.entry_points(group="loam.cli.subcommands")` returns an entry named `init` whose `.load()` resolves to a callable. | Unit test `test_AC_FBE_1_4_entry_point_registered.py` reads the entry-point group and asserts `init` resolves. |
| **AC.FBE.1.5** | The unified-CLI dispatch path works end-to-end: invoking `loam.loam_init.cli.build_init_subcommand` against a stub `argparse._SubParsersAction` produces a leaf parser carrying `func=<dispatched callable>`; calling that callable with a parsed `argparse.Namespace` (carrying `path`, `canonical_source`, `init_existing`, `persona_handle`) returns the expected exit code (0 on success path; mapped non-zero on the four named error classes 1/2/3/4 mirroring `cli_main`'s convention). | Unit test `test_AC_FBE_1_5_dispatch_exit_codes.py` exercises the success + four mapped-error paths against monkeypatched `bootstrap_new_workspace`. |
| **AC.FBE.1.6** | Negative AC: zero changes to `framework/tools/loam/src/loam_cli/cli.py` (entry-point discovery is the contract) AND zero changes to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` (wrapper composes on the existing public function). | `git diff BASELINE..SEAL_COMMIT -- framework/tools/loam/ framework/workspace-bootstrap/` is empty. |
| **AC.FBE.1.7** | Inter-component dep: `framework/loam-init/pyproject.toml` declares `dependencies = ["loam-workspace-bootstrap"]` as a bare-name dep (FBE.4 will rewrite to a path-spec; bare-name shape is intentional at FBE.1 to keep the ordering hazard explicit per parent plan §4 FBE.4 halt-trigger #3). | `grep loam-workspace-bootstrap framework/loam-init/pyproject.toml` returns the bare-name line. |
| **AC.FBE.1.8** | Partition admission: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`'s `dev_and_public:` block contains `- glob: "framework/loam-init/**"`. The audit-completeness test passes for canonical `pos-v2` HEAD post-seal. | Direct `grep` + run `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py` post-commit. |
| **AC.FBE.1.S** | Sealed-component fence: `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under `framework/loam-init/` + `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` (admitted via `universal_paths.prefixes`) + `docs/plans/v0-1-0-foldback-scope-expansion-fbe1*.{md,yaml}` (admitted via `universal_paths.prefixes`) + the parent plan-doc backfill. | `framework/loam-init/tests/test_no_sealed_amendments.py` invariant + manual `git diff --name-only` check at seal time. |

**ACs deliberately out of scope (NOT in FBE.1):**
- Auto-resolve canonical from `framework/.git/config` — defer (parent plan loose text tightened per §2 Surface #4).
- Cross-platform smoke (Linux) — parent plan §6 Risk 5 deferred to v0.1.x.
- Full end-to-end smoke (`loam init` against real canonical with venv) — parent plan AC.FBE.6.3 owns the full smoke; FBE.1's tests stub the bootstrap call to keep the test fast and isolated.
- Path-spec dep rewrite — FBE.4 owns it; FBE.1 declares the bare-name dep per AC.FBE.1.7.

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Pure Python CLI plumbing; no Claude-native primitive in scope. The unified `loam` CLI itself is the closest thing — FBE.1 extends it via the established M6a entry-point discovery pattern (the SAME pattern dev-sdlc's `loam project` uses). Composes on existing harness shape rather than re-implementing.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The whole point — operators currently can't use the documented onboarding verb; FBE.1 makes the verb work, reducing translation burden between "I want a workspace" and "what command do I type".
- **Harness test:** PASS. Adds a registered subcommand to the toolkit the unified CLI exposes; pattern-establishing for future user-facing verbs (`loam status`, `loam plot`, etc., per `loam-rename-decisions.md`).

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (argparse construction details, exit-code mapping shape, test stub style) is builder's call. No "options to rule on" framed inside this plan-doc — every line of code maps to AC.FBE.1.{1..8,S}.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape (parent plan locked Decision A1; the M6a precedent gives a direct shape template). Tight scope is appropriate. ACs name observable outputs; method is inferable from `dev-sdlc/cli.py:build_project_subcommand` shape and `bootstrap_new_workspace`'s public signature without being prescribed.

### Lens 5 — Swarming
FBE.1 is itself a leaf in the parent plan's swarm (one of six FBE.* amendments each with tighter ACs than the parent foldback objective). Internally, FBE.1's ACs do not partition further — every AC binds to a single observable surface. No sub-decomposition.

---

## 6. File-by-file map

### NEW files under sealed-component fence (`framework/loam-init/`):

```
framework/loam-init/
├── pyproject.toml                                          # AC.FBE.1.1, 1.2, 1.7
├── README.md                                               # one-paragraph capability description
├── src/
│   └── loam/
│       └── loam_init/
│           ├── __init__.py                                 # AC.FBE.1.1; minimal __version__ export
│           └── cli.py                                      # AC.FBE.1.3, 1.5; build_init_subcommand
└── tests/
    ├── __init__.py
    ├── conftest.py                                         # shared fixtures
    ├── SEAL_COMMIT                                         # sidecar; written at apply-time
    ├── test_no_sealed_amendments.py                        # AC.FBE.1.S; standard structural fence
    ├── test_AC_FBE_1_3_builder_wires_bootstrap.py          # AC.FBE.1.3
    ├── test_AC_FBE_1_4_entry_point_registered.py           # AC.FBE.1.4
    └── test_AC_FBE_1_5_dispatch_exit_codes.py              # AC.FBE.1.5
```

### Edits via `universal_paths.prefixes` (NOT in fence; admitted at manifest level):

- `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` — single new line in the `dev_and_public:` block: `- glob: "framework/loam-init/**"` (with a 3-line provenance comment naming FBE.1 + the foldback plan).

### Plan-doc + manifest (universal_paths.prefixes: `docs/plans/`):

- `docs/plans/v0-1-0-foldback-scope-expansion-fbe1.md` (this file).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe1.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/plans/v0-1-0-foldback-scope-expansion.md` — §8 method-decision register entries: apply commit SHA + seal commit SHA for FBE.1.

**TOTAL fence diff:** 8 new files under `framework/loam-init/` + 1-line edit to partition manifest (universal-admitted) + plan-doc + manifest YAML (universal-admitted) + parent plan-doc backfill (universal-admitted).

---

## 7. Hard constraints

- Single sealed-component fence: `framework/loam-init/` (its own anchor — the new component carries its own `tests/test_no_sealed_amendments.py` invariant).
- No new external runtime deps beyond `loam-workspace-bootstrap` (the wrapper composes on the existing function).
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.1.*` (collision-safe; verified via `grep -rE "AC\.FBE\.1" docs/`).
- Auto-memory `MEMORY.md` NOT touched.
- Zero edits to `framework/tools/loam/src/loam_cli/cli.py` (entry-point discovery is the contract — AC.FBE.1.6).
- Zero edits to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` (wrapper composes — AC.FBE.1.6).
- Component-scoped test rerun only per `feedback_amendment_dispatch_speedups`: `framework/loam-init/tests/` + `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py` (the audit-completeness test that the partition admission affects). NOT the full canonical sweep.

---

## 8. Out of scope (per ODD §2.5)

- Auto-detection of `--from` from a cloned `framework/`'s git remote — see §2 Surface #4; deferred to a future amendment if/when the demand surfaces.
- `loam init` invocation against URL-form canonical sources requiring network — the wrapper passes through to `bootstrap_new_workspace` which handles URL forms; FBE.1 doesn't add new URL handling.
- Path-spec rewrite of the `loam-workspace-bootstrap` dep — FBE.4 owns it.
- Description scrub of the new pyproject's `description` field — FBE.5 owns it (FBE.1 authors a clean description; FBE.5 sweep verifies).
- Editing the `loam_cli/cli.py` discovery loop — entry-point discovery is the contract; AC.FBE.1.6 forbids touching it.
- Editing `bootstrap_new_workspace`'s signature or behaviour — AC.FBE.1.6.
- Cross-platform Linux smoke — parent §6 Risk 5; out of v0.1.0 critical path.
- Touching the dev-sdlc plugin's `loam project` registration (orthogonal).

---

## 9. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** `bootstrap_new_workspace`'s public signature requires a parameter the wrapper can't reasonably supply from a `loam init` argparse Namespace (e.g. mandatory `tracker_seed_runner` callable). **Mitigation:** verified at planning that all required-positional/keyword args are coverable from CLI args; the test-only `*_override` parameters default to `None` and don't need CLI surface. Should not trigger.
- **HT-2:** Entry-point loaded via `importlib.metadata` returns a non-callable or fails to import (cli.py:84-89 dispatcher path). Surface the import-time failure; do not paper over with try/except.
- **HT-3:** `pip install -e framework/loam-init/` fails because `loam-workspace-bootstrap` isn't installed in the venv. Surface the install-order requirement; document explicitly in plan §10 (it's already a known FBE.4 concern).
- **HT-4:** Audit-completeness test for `pos-v2` HEAD (`test_AC_OSS_3_default_partition_complete.py`) fails post-commit even with the partition admission. Surface; the admission shape (`glob: "framework/loam-init/**"`) is wrong or precedence ordering interferes.
- **HT-5:** `loam amend apply` against the FBE.1 manifest fails with a fence breach diagnostic. Surface; the manifest's `extra_allowed_files` / `universal_paths` block needs adjustment.
- **HT-6:** Wall-time exceeds 70 min (parent plan band 25–55 min, midpoint 40; 70 is the dispatch-imposed hard cap). Surface partial findings + named what's left.
- **HT-7:** A surrounding-code ODD §2.5 violation discovered during the build (e.g. in `loam_cli/cli.py` or `bootstrap_new_workspace`'s public surface). Surface; do NOT silently extend or fix in-band.
- **HT-8:** `bootstrap_new_workspace`'s `cli_main` exit-code mapping doesn't match the four-class structure described in §4 AC.FBE.1.5 (e.g. `cli_main` carries different exit codes than 1/2/3/4). Re-verify against the actual source; tighten the AC if needed (per `feedback_loose_AC_text_fix_AC_not_implementation`).

---

## 10. Risks

- **Risk: install-order constraint surfaces in stranger smoke.** A stranger doing `pip install -e framework/loam-init/` against a clean checkout WITHOUT first installing `loam-workspace-bootstrap` will fail because `loam-workspace-bootstrap` is a bare-name dep at FBE.1. Mitigation: parent plan AC.FBE.4.7 authors `docs/install-from-source.md` covering the explicit install order; FBE.6's extended smoke exercises the documented path. Until then, the install-order concern is a known limitation FBE.1 doesn't have to fix.
- **Risk: discovery-loop silent-skip.** If the new entry-point fails to load post-install (typo in module path, package install corrupted), `loam_cli/cli.py:84-89` swallows the exception with `_LOGGER.warning(...)`. Mitigation: AC.FBE.1.4 explicitly verifies `entry_points(group="loam.cli.subcommands")` returns the entry post-install; if it doesn't surface, the warning still fires (audit via test or run `loam --version` and check stderr).
- **Risk: tests run before pip install.** The unit tests for AC.FBE.1.3 and 1.5 stub `bootstrap_new_workspace`; AC.FBE.1.4's entry-point test requires `pip install -e framework/loam-init/` to have run. Mitigation: conftest or test fixture invokes `pip install -e .` against the loam-init component if not already installed; or skip-with-clear-message if the install isn't present. Builder's call on test mechanics.
- **Risk: parent plan's `extra_allowed_files` list is wider than needed.** Mitigation: my manifest uses `universal_paths.prefixes` only for the partition manifest path + `docs/plans/` (already universal); the fence stays tight at `framework/loam-init/`.

---

## 11. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Feature commit #1** — author `framework/loam-init/{pyproject.toml,README.md,src/...,tests/...}` (new files; no other path touched). Tests included; the structural seal-test (`test_no_sealed_amendments.py`) included; sidecar SEAL_COMMIT placeholder = `HEAD`. Confirm `pytest framework/loam-init/tests/` passes (modulo `pip install -e .` for the entry-point test).
3. **Feature commit #2** — author the partition-manifest single-line admission + 3-line provenance comment. Confirm `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py` passes.
4. **Manifest commit** — author `docs/plans/v0-1-0-foldback-scope-expansion-fbe1.manifest.yaml`.
5. **`loam amend apply`** — invoke against the manifest. Produces the apply-bookkeeping commit (BASELINE bumps in test files, sidecar bump, narrative append).
6. **`loam amend seal`** — produces the deterministic seal commit; sidecar SEAL_COMMIT advances to the seal SHA; narrative file finalised.
7. **Parent plan-doc backfill** — `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 FBE.1 entries get the apply + seal SHAs (separate NEW commit; admitted via `docs/plans/` universal prefix).
8. **Status file** — write `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe1-status-2026-05-03.md` (outside canonical tree; the dispatcher reads it).

NO `git commit --amend` at any point. NO push to any remote.

---

## 12. References

- **Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` §4 FBE.1.
- **Reviewer foldback dossier:** `<workspace>/.scratch/claude-output/loam-user-review-2026-05-03.md` BLOCKER 1.
- **CLI dispatcher (READ ONLY):** `framework/tools/loam/src/loam_cli/cli.py`.
- **Existing subcommand-builder precedent:** `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/cli.py:166` (`build_project_subcommand`).
- **Bootstrap function being wrapped:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:420` (`bootstrap_new_workspace`).
- **CLI exit-code convention being mirrored:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:666` (`cli_main`).
- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Universal-paths-admission precedent:** `docs/plans/oss-v0-1-0-publish-public-docs-partition-fix.manifest.yaml` (M7-partition-fix, amendment #98).
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (AC.FBE.1.3 tightened; auto-detect dropped).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §11).
  - `feedback_subagent_odd_violation_halt` (HT-7 covers ODD violations in surrounding code).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to touched-only).
  - `feedback_summarize_and_surface_decisions` (surfaces 1–4 explicit in §2).
  - `feedback_principle_conflict_resolution_multi_signal` (§2 Surface #1 applies the four-step process).

---

## 13. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Feature commit #1 (loam-init source + tests): `<TBD>`.
- Feature commit #2 (partition admission): `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.1 sub-plan-doc. Ready to build.*
