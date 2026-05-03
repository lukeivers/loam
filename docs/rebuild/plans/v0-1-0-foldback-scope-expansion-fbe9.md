# FBE.9 sub-plan — close BLOCKER-FBE6b.1 + comprehensive doc-vs-CLI conformance sweep

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.9 row to be backfilled in §8 register at completion).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7,8} all sealed; FBE.6 apply at `364c37d` (seal pending FOLDBACK record); FBE.6b sealed at `08589ce` (FOLDBACK to FBE.9). Parent §8 backfilled for FBE.6b at `50a07e0` (current canonical HEAD).
**BASELINE (pre-build tip):** `50a07e0` — current canonical pos-v2 HEAD (FBE.6b §8 backfill commit).

---

## 1. Summary / TLDR

FBE.9 closes the FBE.6b FOLDBACK and **breaks the doc-vs-CLI ping-pong cycle** by combining the named BLOCKER closure with a single comprehensive doc-vs-CLI sweep so we don't catch the next mismatch in FBE.6c → FBE.10. Two buckets:

1. **Bucket 1 — CLI-side fix for BLOCKER-FBE6b.1.** Make `loam init`'s `--from CANONICAL_SOURCE` argument **optional** in `framework/loam-init/src/loam/loam_init/cli.py:185-197`. When omitted: default to the current working directory if it is a git tree (`.git/` exists); otherwise raise `CanonicalSourceInvalidError` with an actionable message naming `--from`. This is Path B from the FBE.6b sweep report (CLI-side fix; recommended over doc-only Path A). Single-fence amendment at `loam-init`.
2. **Bucket 2 — Comprehensive doc-vs-CLI conformance sweep.** Walk every CLI command mentioned in the public-facing docs (`README.md`, `docs/getting-started.md`, `docs/install-from-source.md`, `framework/loam-init/README.md`); verify the syntax + verify the documented behaviour matches the actual CLI; fix mismatches by adjusting either CLI or doc. Sweep covers the full set of `loam`, `pip`, `python`, `git`, `claude`, `source` invocations a stranger types when following the docs literally. Audit findings table in §6.

The dispatcher's strategic call: break the foldback cycle by auditing ALL commands at once, not just the named one. **HIGH-FBE6b.1** (pervasive `Amendment #N` source-comment references — 339 occurrences across 95 files) is **explicitly out of scope** per dispatcher's brief ("NOT the 339 amendment-number scrubs … HIGH-FBE6b.1, deferred per agent recommendation").

Every edit maps to a named AC. ODD §2.5 negative AC: nothing else.

**Sealed-component fence (verified at sub-plan time, see §6 file-by-file map):**
- `framework/loam-init/` — Bucket 1 (cli.py optional `--from` + smart-default; tests + README adjustments).
- README.md + `docs/getting-started.md` + `docs/install-from-source.md` — Bucket 2 (universal-paths admission; pre-admitted in workspace-bootstrap fence-test's `allowed_files` per FBE.2c precedent + new admission for `docs/install-from-source.md` if not yet admitted, verified at build time).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; CLI-fix shape interpretation)

The dispatcher's brief specifies: "Make `loam init`'s `--from CANONICAL_SOURCE` argument **optional**, defaulting to pwd if pwd is a git tree (otherwise error helpfully). After this fix, `loam init <new-ws>` (run from inside a cloned loam tree) just works."

This is a **Mode-A out-of-tree workspace** fix — the user runs `loam init <some-other-path>` from inside the cloned loam tree, with the cloned tree implicitly serving as the canonical source. This is distinct from **Mode-B in-tree workspace** semantics (`loam init .`) which would require `init_existing=True` semantics + nontrivial reinterpretation of `bootstrap_new_workspace`'s "clone canonical INTO `<target>/framework/`" contract (the cloned tree's `framework/` is already laid out post-FBE.2b; there is no top-level `.git` for the framework subdir). Mode-B is bigger than the dispatcher's "small fix" framing and would require a separate amendment.

**Decision (autonomous, builder's call per ODD §1.1):** implement Mode-A only per dispatcher's brief. The README + getting-started.md `loam init .` invocation gets fixed in Bucket 2 to use a fresh out-of-tree path (e.g. `loam init ~/my-loam-workspace`) — this is the natural shape and matches every existing test fixture. Mode-B (re-init the cloned tree as workspace) is a FUTURE_IDEAS_DRAFT candidate; not in FBE.9 scope.

### Surface #2 (no halt — recorded; doc rewrite scope)

Bucket 2 fixes `loam init .` → `loam init <out-of-tree-path>` in README + getting-started.md. The "in this directory" framing in README step 4 (`# 4. Open Claude Code in this directory.`) needs to follow the workspace location, not the cwd. Doc-prose change is small but spans a few prose lines. Per dispatcher's halt trigger: "**NOT bigger doc rewrites; NOT new features; NOT the 339 amendment-number scrubs**." The fix stays surgical to the install-flow + adjacent prose lines per FBE.8 Bucket 1 precedent.

### Surface #3 (no halt — recorded; framework/loam-init/README.md is in-fence)

`framework/loam-init/README.md` documents the `--from` argument as not-optional ("`--from <canonical-source>` — absolute POSIX path …"). After Bucket 1, this needs a doc edit to mark `--from` as optional (default-to-pwd-if-git-tree). Lives inside the loam-init fence component; rides via the same fence as Bucket 1 source/test edits.

### Surface #4 (no halt — recorded; existing test asserts `--from` is required)

`framework/loam-init/tests/test_AC_FBE_1_3_builder_wires_bootstrap.py::test_AC_FBE_1_3_canonical_source_required` (line 90) currently asserts `pytest.raises(SystemExit)` when `--from` is omitted. After Bucket 1 this test must invert — omitting `--from` no longer raises (when cwd is a git tree, parser returns `canonical_source=None`; the `_cmd_init` action resolves it). The test inversion is part of Bucket 1's AC.FBE.9.1.

### Surface #5 (no halt — recorded; partner-prefix gap precedent — single component, canonical shape, low risk)

Per FBE.4/FBE.5/FBE.5b/FBE.6/FBE.6b precedent: `loam amend apply` derives `partner_prefixes` assuming `framework/<name>/` for each fence component. `loam-init` lives at `framework/loam-init/` (canonical shape) — apply tool should derive cleanly with no corrective needed. Mirror FBE.5/FBE.6 outcome. If a corrective is needed at apply, mirror FBE.4's recipe (`0c4d9a0`).

### Surface #6 (no halt — recorded; clean-tree workaround for `loam amend seal`)

Per every prior FBE.x: pre-existing untracked paths (`.claude/`, plan-research drafts, `memory-write-worker.{err,out}.log`, `tools/`, `workspace-sync/`) + dirty `docs/rebuild/FUTURE_IDEAS_DRAFT.md` will need `git stash push --include-untracked` to unblock the seal command. Stash popped clean post-seal. Same workaround as FBE.{2,3,4,5,5b,6,7,8,6b}.

### Surface #7 (no halt — recorded; --force-with-lease deferred to FBE.6c)

This amendment does NOT push synth to staging (that's FBE.6c's job). No `--force-with-lease` interaction.

### Surface #8 (no halt — recorded; HIGH-FBE6b.1 explicitly out of scope)

The 339 `Amendment #N` source-comment references surfaced by FBE.6b's reviewer probe are explicitly deferred per dispatcher's brief ("NOT the 339 amendment-number scrubs (HIGH-FBE6b.1, deferred per agent recommendation)"). This stays a v0.1.x dedicated source-comment scrub amendment candidate; documented as known limitation in v0.1.0 release notes.

### Surface #9 (no halt — recorded; reviewer probe deferred to FBE.6c)

This amendment does NOT run a stranger-perspective reviewer probe. AC.FBE.9.5 below covers the in-band end-to-end smoke (every documented command runs cleanly against the post-FBE.9 canonical clone); the full reviewer-probe re-run is FBE.6c's job per dispatcher's brief ("After it seals → FBE.6c re-runs sweep + smoke + reviewer").

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — the documented install flow must produce a working stranger experience: clone, install, init, claude. The README's literal commands must work end-to-end. FBE.6b's reviewer surfaced the literal-command failure at step 3.
- **BLOCKER-FBE6b.1** (per FBE.6b sweep report §4) — README + getting-started.md `loam init .` does not match CLI's required `--from` flag. Bucket 1 closes the CLI side; Bucket 2 closes the doc side.
- **AC.FBE.9.* (this plan §4)** — every AC ladders to the same parent.

**Ladders to:** AC.FBE.9.* → FBE.6c (re-runs sweep + smoke + reviewer post-FBE.9) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.9.*)

AC family `AC.FBE.9.*` — collision-safe (no prior amendment uses `AC.FBE.9.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.9.1** (Bucket 1 CLI fix) | `framework/loam-init/src/loam/loam_init/cli.py` makes `--from` optional. When omitted, `_cmd_init` resolves the default: if `Path.cwd() / ".git"` exists, set `canonical_source = str(Path.cwd().resolve())`; else raise / exit-2 with an actionable message naming `--from` and the cwd-not-a-git-tree reason. The argparse `help` text updates to describe the default. The 5 existing test files in `framework/loam-init/tests/` that assume `--from` is required update to reflect the new contract. | (a) `pytest framework/loam-init/tests/ -x -q` exits 0; (b) `loam init --help` output shows `--from` as optional with default-to-pwd-if-git-tree behaviour described; (c) running `loam init <fresh-target>` from inside a git tree (no `--from`) succeeds; (d) running `loam init <fresh-target>` from a non-git tree (no `--from`) fails with exit 2 + an error message naming `--from`. |
| **AC.FBE.9.2** (Bucket 1 doc inside fence) | `framework/loam-init/README.md` Usage block updates to show `--from` as optional with default-to-pwd-if-git-tree behaviour described. The Usage line's argument syntax notation changes from `--from <canonical-source>` (required) to `[--from <canonical-source>]` (optional) and the bullet for `--from` describes the smart-default. | `git grep -F 'loam init <new-ws-path> --from' framework/loam-init/README.md` returns 0 hits OR returns the new optional-bracket form `[--from ...]`. The bullet text mentions "default" and "current working directory". |
| **AC.FBE.9.3** (Bucket 2 doc-vs-CLI sweep — README + getting-started.md `loam init` invocation) | `README.md` Quickstart and `docs/getting-started.md` Five-step bootstrap update the `loam init .` invocation to match the working CLI semantic (out-of-tree workspace path). The replacement: `loam init <out-of-tree-path>` (e.g. `loam init ~/loam-workspace` or similar). The `# 4. Open Claude Code in this directory.` line's framing follows the workspace path (e.g. cd'ing to the new workspace before launching `claude`). Edits stay surgical to the affected lines + immediately-adjacent prose (no broader Quickstart restructure). | (a) `git grep -F 'loam init .' README.md docs/getting-started.md` returns 0 hits (no bare `loam init .` invocation); (b) `git grep -E 'loam init [~/$\.A-Za-z]' README.md docs/getting-started.md` returns ≥1 hit per file with the new out-of-tree shape; (c) AC.FBE.9.5 smoke verifies the new commands actually work end-to-end. |
| **AC.FBE.9.4** (Bucket 2 doc-vs-CLI sweep — audit table) | The audit table in §6.4 of this sub-plan documents every public CLI command checked, per documented file, with its outcome (PASS = command works as documented; FIX = command corrected via doc or CLI edit). Total commands audited ≥ the count of unique CLI invocations in `README.md` + `docs/getting-started.md` + `docs/install-from-source.md` + `framework/loam-init/README.md`. | The §6.4 table in this sub-plan is populated and referenced from the FBE.9 status file. The status file's audit summary records the per-file count + the per-fix outcome. |
| **AC.FBE.9.5** (end-to-end smoke verifies documented commands) | Stranger-clone smoke against post-FBE.9 canonical pos-v2 verifies every documented public CLI command runs cleanly. The smoke executes the literal command sequence from README's Quickstart end-to-end against a fresh clone + fresh venv: `git clone … && cd loam && python3.13 -m venv .venv && source .venv/bin/activate && pip install -r install-from-source.txt && loam --version && loam init <ws-path> && (cd <ws-path> && claude --help)`. Plus targeted spot-checks for the per-component-fallback path in `docs/install-from-source.md`. | Shell sequence run against post-FBE.9 canonical HEAD; transcript captured in the FBE.9 status file. Every step exits 0; `loam --version` reports `loam 0.1.0`; `loam init <ws-path>` produces a runnable workspace shape (`framework/`, `workspace/personas/primary/`, `.claude/settings.json={}`); `~/.loam/{dormancy.sqlite, logs/}` scaffolded; `claude --help` returns Claude Code usage output (this is a Claude Code precondition, not a loam-side check; smoke verifies the user's environment is amenable to step 4). |
| **AC.FBE.9.6** (negative AC — scope discipline) | Edits stay strictly within the two-bucket scope. NO behaviour changes outside the named CLI-fix in `loam-init/src/loam/loam_init/cli.py` and the test/README adjustments inside the loam-init fence; NO architecture changes; NO test refactors beyond updating the 5 test files affected by `--from`'s optional shape; NO source-comment scrubs (HIGH-FBE6b.1 explicitly deferred); NO broader README rewrites. | `git diff BASELINE..SEAL_COMMIT --name-only` produces ONLY paths under: (a) `framework/loam-init/` (Bucket 1 + the loam-init component README); (b) `README.md`, `docs/getting-started.md`, `docs/install-from-source.md` (Bucket 2; universal-paths admissions); (c) `docs/rebuild/plans/` (sub-plan + manifest + parent §8 backfill via universal prefix admission); (d) per-amendment seal-narrative anchor in `framework/hands-off-lifecycle/seals/`. |
| **AC.FBE.9.S** (sealed-component fence) | Sealed-component fence: 1 component — `framework/loam-init/` (Bucket 1 source + tests + component README; carries the BASELINE bump + sidecar advance). Plus universal-paths admissions for `README.md` + `docs/getting-started.md` + `docs/install-from-source.md` + `docs/rebuild/plans/`. Hands-off-lifecycle frozen-baseline narrative-only seal anchor lives at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe9` (mirrors FBE.6/FBE.6b/FBE.8 pattern). | `git diff BASELINE..SEAL_COMMIT --name-only` matches the AC.FBE.9.6 path-set; loam-init fence component's `tests/SEAL_COMMIT` advances via `loam amend seal`; loam-init's BASELINE literal in `tests/test_no_sealed_amendments.py` bumps via `loam amend apply` (per non-frozen convention). HOL fence-test passes byte-identically (HOL is universal-only seal-narrative carrier; not in fence). |

**ACs deliberately out of scope (NOT in FBE.9):**
- HIGH-FBE6b.1 source-comment scrub (339 `Amendment #N` references) — explicit dispatcher-deferral.
- Mode-B `loam init .` semantics (re-init the cloned tree as workspace) — bigger than "small fix"; FUTURE_IDEAS_DRAFT candidate.
- M12 publish-flip — gated behind FBE.6c GO; separate dispatch.
- FBE.6c re-runs (synth + sweeps + reviewer) — separate dispatch post-FBE.9 seal per dispatcher's brief.
- FBE.6 pending seal — leave as FOLDBACK record per FBE.6b's path-forward Decision 5.

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The fix shape is a small CLI ergonomic change + doc updates — no Claude-native primitive to lean on, no extension surface. Lens 1 is informational here: FBE.9 doesn't add Claude-leverage; it removes the friction that blocks the v0.1.0 publish that itself enables Claude-leverage primitives downstream. Lens 1 PASS by composition (every prior FBE.x amendment paid the Lens 1 cost; FBE.9 closes their cycle).

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The two buckets together are the difference between "stranger reads README, runs the documented `loam init .`, hits exit-2 within 30s" and "stranger reads README, runs the documented invocation, reaches a working `loam --version` + first-session greeting". Translation burden drops materially.
- **Harness test:** PASS by composition. The toolkit gains nothing new structurally, but the install path that delivers the toolkit becomes truthful — the harness is reachable.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact line to edit, which exact resolver shape to implement) is the builder's call but constrained by the file-by-file map below. Per ODD §2.5: every line of the diff maps to AC.FBE.9.{1,2,3,4,5,6}. No defensive code; no other doc edits; no preemptive Mode-B implementation.

### Lens 4 — Prompt scope ↔ confidence
High confidence in Bucket 1 outcome shape: the dispatcher's brief named the precise file + the precise behaviour ("optional, defaults to pwd if pwd is a git tree, error helpfully otherwise"). Tight scope for Bucket 1.

Medium confidence in Bucket 2 outcome shape: the audit's surface area (every command in 4 docs) is wide; the per-mismatch fix is narrow. Per F4: tighten scope per-mismatch (each fix is named in §6.4) but loosen scope at the audit-discovery level (the table populates as the audit progresses; not every cell is pre-determined).

### Lens 5 — Swarming
FBE.9 has natural decomposition: Bucket 1 (CLI fix) and Bucket 2 (doc audit) are independent. Per F3 stopping criterion: stop when split adds only coordination overhead. Both buckets are small enough that a single-agent main-thread sequence completes faster than spawning 2 sub-agents. `max_planner_depth = 0` (single-agent build). Model = Sonnet (default; no rationale needed).

---

## 6. File-by-file map

### 6.1 Bucket 1 — `framework/loam-init/` (sealed-component fence)

**`framework/loam-init/src/loam/loam_init/cli.py`:**
- **Line 185-197 (parser.add_argument for `--from`):**
  - `required=True` → `required=False`; `default=None` (explicit).
  - Update `help=` text to describe the smart-default behaviour: "Canonical loam source: an absolute POSIX path to a local git working tree, or an http(s)/git@ URL. Optional; if omitted, defaults to the current working directory when it is a git tree (the typical pattern when `loam init` runs from inside a cloned loam tree). Errors with exit-2 if omitted AND cwd is not a git tree."
- **`_cmd_init` action callable (lines 55-131):**
  - Add a small resolver block at the top of the success path (after the `import` block, before the `bootstrap_new_workspace(...)` call): if `args.canonical_source is None`, check `Path.cwd() / ".git"`; if exists, resolve `args.canonical_source = str(Path.cwd().resolve())`; else raise `CanonicalSourceInvalidError` with a message like `"--from omitted AND current working directory {cwd!s} is not a git tree (missing .git/). Pass --from with an absolute POSIX path to a local git working tree, or run from inside a cloned loam tree."` and let the existing exception handler return exit 2.
  - The resolver must run AFTER the import block (so `CanonicalSourceInvalidError` is in scope) but BEFORE the `bootstrap_new_workspace(...)` call (so the resolved value is what gets passed).
- **Epilog block (lines 168-173):** add a third example line `  loam init ~/my-ws       (run from inside a cloned loam tree; --from defaults to cwd)`.
- Module docstring (lines 15-46): minimal touch — update the example at line 18 to reflect optional `--from`. Behaviour preserved verbatim outside the named edits.

**`framework/loam-init/tests/test_AC_FBE_1_3_builder_wires_bootstrap.py`:**
- **`test_AC_FBE_1_3_canonical_source_required`** (line 90-93): RENAME → `test_AC_FBE_1_3_canonical_source_optional` and INVERT the assertion. The new contract: omitting `--from` is no longer a parse error (parser returns `canonical_source=None`); the `_cmd_init` resolver handles the default. Test the parser-side outcome: `ns = _build_loam_init_namespace(["init", "/tmp/x"])`; `assert ns.canonical_source is None`.
- **`test_AC_FBE_1_3_persona_handle_default_is_primary`** (line 81-87): preserved (independent of --from change).
- **`test_AC_FBE_1_3_argparse_surface_accepts_documented_args`** (line 57-78): preserved (still passes a `--from`).
- **`test_AC_FBE_1_3_dispatch_calls_bootstrap_with_parsed_kwargs`** (line 96-145): preserved.

**`framework/loam-init/tests/test_AC_FBE_1_5_dispatch_exit_codes.py`:**
- **`_make_args` defaults** (line 43-52): preserved (defaults still include a non-None `canonical_source`; tests that exercise specific error paths don't depend on the new resolver). Add 1 NEW test: `test_AC_FBE_1_5_canonical_source_omitted_defaults_to_cwd_when_git_tree` — uses `monkeypatch.chdir(tmp_path)` + `(tmp_path / ".git").mkdir()` setup; calls `_cmd_init(_make_args(canonical_source=None))`; asserts it succeeds (exit 0 via the stub bootstrap monkeypatch). Add 1 NEW test: `test_AC_FBE_1_5_canonical_source_omitted_errors_when_cwd_not_git` — `monkeypatch.chdir(tmp_path)` (no `.git/`); calls `_cmd_init(_make_args(canonical_source=None))`; asserts exit 2 (the `CanonicalSourceInvalidError` exit code).

**`framework/loam-init/tests/test_AC_FBE_1_4_entry_point_registered.py`:** likely no changes (entry-point discovery is orthogonal to the --from change). Verify pre-build that the file doesn't reference `--from` defaults.

**`framework/loam-init/README.md`:**
- Usage block (lines 7-9): change `loam init <new-ws-path> --from <canonical-source>` → `loam init <new-ws-path> [--from <canonical-source>]`.
- Bullet for `--from` (line 12): append the smart-default description: "Optional; defaults to the current working directory when it is a git tree."

### 6.2 Bucket 2 — `README.md` (universal admission)

**Quickstart code block (lines 32-47):**
- Drop step `loam init .` and replace with a fresh out-of-tree path. The cleanest invocation that mirrors the post-FBE.2c shape is `loam init ~/loam-workspace` (creates a new workspace at `~/loam-workspace/` cloned from the current tree).
- Step 4 (`# 4. Open Claude Code in this directory.` + `claude`) updates to `# 4. Open Claude Code in the new workspace.` + `cd ~/loam-workspace` + `claude`. Three-line block instead of two-line.
- Comment line for step 3 updates from "Initialise the workspace." to "Bootstrap a fresh workspace from this clone."
- Surrounding prose at lines 49-57 ("The install step walks `install-from-source.txt` …", "Your first run scaffolds `~/.loam/`…") preserved (no architectural change to the prose).

### 6.3 Bucket 2 — `docs/getting-started.md` (universal admission)

**§3 "Initialise the workspace" (lines 85-98):**
- Change `loam init .` → `loam init ~/loam-workspace` (mirrors README's chosen example path).
- Section title preserved.
- Surrounding prose at lines 87-89 + 95-98: minor adjustment to describe the out-of-tree workspace shape ("scaffolds the per-host config under `~/.loam/`, clones the framework into `~/loam-workspace/framework/`, scaffolds the workspace state at `~/loam-workspace/workspace/`, and writes the workspace-level Claude Code settings.").

**§4 "Open Claude Code in the workspace" (lines 100-110):**
- Add a `cd ~/loam-workspace` line before the `claude` invocation (consistent with README).

**Common-first-run-problems (lines 172-192):**
- The `.claude/settings.json` reference at line 180 (`re-run loam init .`) updates to `re-run loam init ~/loam-workspace` (consistent with the new example path).

### 6.4 Bucket 2 — Doc-vs-CLI audit table

This table populates during Bucket 2 execution. Every public CLI command in `README.md`, `docs/getting-started.md`, `docs/install-from-source.md`, `framework/loam-init/README.md` is enumerated and verified against the actual CLI behaviour.

| Doc file | Line | Command | Status | Fix applied |
|---|---|---|---|---|
| README.md | 34 | `git clone https://github.com/lukeivers/loam` | PASS | — (clone target is M12-deferred per FBE.6's HIGH 3 staging-vs-prod URL note) |
| README.md | 35 | `cd loam` | PASS | — |
| README.md | 38 | `python3.13 -m venv .venv` | PASS | — |
| README.md | 39 | `source .venv/bin/activate` | PASS | — |
| README.md | 40 | `pip install -r install-from-source.txt` | PASS | — (verified by FBE.8 + FBE.6b smoke) |
| README.md | 43 | `loam init .` | FIX | Bucket 2 — replaced with `loam init ~/loam-workspace` |
| README.md | 46 | `claude` | PASS (Claude Code precondition) | — (operator's responsibility per docs/getting-started.md §Prerequisites) |
| docs/getting-started.md | 53 | `git clone https://github.com/lukeivers/loam` | PASS | — |
| docs/getting-started.md | 54 | `cd loam` | PASS | — |
| docs/getting-started.md | 72 | `python3.13 -m venv .venv` | PASS | — |
| docs/getting-started.md | 73 | `source .venv/bin/activate` | PASS | — |
| docs/getting-started.md | 74 | `pip install -r install-from-source.txt` | PASS | — |
| docs/getting-started.md | 92 | `loam init .` | FIX | Bucket 2 — replaced with `loam init ~/loam-workspace` |
| docs/getting-started.md | 103 | `claude` | PASS (Claude Code precondition) | — |
| docs/getting-started.md | 180 | `loam init .` (in troubleshooting) | FIX | Bucket 2 — replaced with the new example path |
| docs/install-from-source.md | 33 | `python3.13 -m venv .venv` | PASS | — |
| docs/install-from-source.md | 34 | `source .venv/bin/activate` | PASS | — |
| docs/install-from-source.md | 38 | `pip install --upgrade pip` | PASS | — |
| docs/install-from-source.md | 41 | `pip install -r install-from-source.txt` | PASS | — |
| docs/install-from-source.md | 58 | `loam init .` | FIX | Bucket 2 — replaced with `loam init ~/loam-workspace` |
| docs/install-from-source.md | 72 | `pip install -e ./framework/scope-of-work` | PASS | — (verified at FBE.4 install-from-source.txt smoke) |
| docs/install-from-source.md | 73-106 | per-component-fallback `pip install -e ./framework/<comp>` | PASS | — (mirrors install-from-source.txt's tier ordering byte-for-byte) |
| docs/install-from-source.md | 142 | `.venv/bin/python --version` | PASS | — |
| docs/install-from-source.md | 164 | `pip install loam-cli loam-init …` | DEFERRED (v0.2 PyPI shape) | — (correctly framed as v0.2 future state per the surrounding prose) |
| framework/loam-init/README.md | 8 | `loam init <new-ws-path> --from <canonical-source>` | FIX | Bucket 1 — `--from` now optional; line updates to `[--from <canonical-source>]` |
| framework/loam-init/README.md | 26 | `pip install -e framework/loam-init` | PASS | — (per-component install; verified via install-from-source.txt walk) |

**Audit summary:** ~26 unique CLI commands across 4 docs. **5 FIXES** (4 distinct `loam init .` → `loam init ~/loam-workspace` substitutions across the 3 public docs + 1 docs/install-from-source.md internal cross-ref + 1 loam-init component README's `--from` syntax bracket). All other 21 commands PASS. `claude` invocations verified as Claude Code preconditions (operator-environment, not loam-side).

### 6.5 Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`)

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe9.md` (this file, NEW commit).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe9.manifest.yaml` (NEW commit).

### 6.6 Parent plan-doc backfill (post-seal, separate commit)

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 — ADD a new `### FBE.9 — close BLOCKER-FBE6b.1 + comprehensive doc-vs-CLI conformance sweep` subsection with apply commit SHA + seal commit SHA + AC surface + verification summary; update the closing sequence narrative.

### 6.7 Sidecar bumps within sealed-component fence

- `framework/loam-init/tests/SEAL_COMMIT` advances to FBE.9 seal SHA via `loam amend seal`.
- `framework/loam-init/tests/test_no_sealed_amendments.py` BASELINE literal bumps via `loam amend apply`.
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe9` (NEW narrative anchor file; mirrors FBE.6/FBE.6b/FBE.8 pattern; HOL fence carries `frozen_baseline: true` per amendment #23 + prior FBE precedent — narrative-only).

**TOTAL fence diff:** ~30-40 LOC source/test edits in loam-init + Bucket 2 doc edits across 3 public docs + 1 narrative anchor file + plan-doc + manifest YAML + parent plan §8 backfill.

---

## 7. Smoke verification

**Smoke (AC.FBE.9.5):** runs POST-seal so it exercises the seal-bumped tree.

```bash
# Pre-test cleanup
cd /tmp && rm -rf loam-fbe9-test loam-fbe9-test-ws

# Stranger-clone smoke
git clone --branch pos-v2 --single-branch \
  /Users/lukeivers/ivers-corp-pos-v2 loam-fbe9-test
cd loam-fbe9-test
python3.13 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version

# AC.FBE.9.1 — no --from from inside a git tree
.venv/bin/loam init /tmp/loam-fbe9-test-ws

# AC.FBE.9.5 — verify workspace shape
ls /tmp/loam-fbe9-test-ws/{framework,workspace,.claude}
ls ~/.loam/

# AC.FBE.9.5 — claude --help (precondition check)
which claude && claude --help | head -1 || echo "claude precondition not met (operator-side)"

# Cleanup
rm -rf /tmp/loam-fbe9-test /tmp/loam-fbe9-test-ws
```

**Note:** the smoke runs against the `pos-v2` branch (canonical pos-v2; FBE.9 is in flight). The full `framework-only` branch smoke is deferred to FBE.6c per dispatcher's brief (FBE.6c's job is the synth re-run + sweep + smoke + reviewer).

**Smoke (Bucket 2 audit per-command spot check):** for each FIX command in §6.4, a one-line shell sanity check that the new command parses + dispatches correctly against the post-FBE.9 CLI. Captured in the FBE.9 status file.

**Failure modes:**
- Any step exits non-zero → halt; surface; do not iterate (FBE.6b's smoke worked end-to-end on the dispatcher's flow; FBE.9's CLI-side fix should preserve that).
- `loam init <ws-path>` from inside the cloned tree fails (the new code path) → halt; the resolver implementation has a bug.

---

## 8. Hard constraints

- 1 sealed-component fence (`framework/loam-init/`) + universal-paths admission for `README.md` + `docs/getting-started.md` + `docs/install-from-source.md` + `docs/rebuild/plans/`.
- HOL narrative-only seal anchor (no fence-component edit; HOL frozen-baseline narrative pattern).
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.9.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only the loam-init fence component's tests run post-seal.
- Per FBE.4/FBE.5/FBE.5b/FBE.6/FBE.6b partner-prefix gap precedent: `framework/loam-init/` is canonical `framework/<name>/` shape; partner-prefix derivation should run cleanly. Apply hand-corrective if it recurs.
- Negative AC.FBE.9.6: no scope expansion beyond the 2 buckets; no source-comment scrubs (HIGH-FBE6b.1 deferred); no broader README rewrites; no Mode-B `loam init .` semantics.
- ODD §2.5 — every line of the diff maps to AC.FBE.9.{1..6}. No defensive code for cases ACs don't name.

---

## 9. Out of scope (per ODD §2.5)

- HIGH-FBE6b.1 source-comment scrub (339 `Amendment #N` references) — explicit dispatcher-deferral; FUTURE_IDEAS_DRAFT candidate for v0.1.x source-comment scrub.
- Mode-B `loam init .` semantics (re-init the cloned tree as workspace) — bigger than "small fix"; FUTURE_IDEAS_DRAFT candidate.
- M12 publish-flip — gated behind FBE.6c GO; separate dispatch.
- FBE.6c re-runs (synth + sweeps + reviewer) — separate dispatch post-FBE.9 seal.
- Backfilling FBE.6's pending seal commit — leave as FOLDBACK record per FBE.6b's path-forward Decision 5.
- Edits to other components' source files beyond Bucket 1's loam-init scope.
- Broader Quickstart / getting-started rewrites beyond the named line-replacements.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt`:

- **HT-1:** WD drifts to pos3 → halt immediately.
- **HT-2:** Bucket 2 surfaces a mismatch class bigger than a small fix (e.g., a documented flow that requires a feature that doesn't exist) → halt + surface (per dispatcher's halt-trigger #2).
- **HT-3:** Sealed-component fence breach beyond plan-named (loam-init + universal admissions + HOL narrative) → halt + surface.
- **HT-4:** Partner-prefix bug recurs → apply hand-corrective per FBE.4/FBE.5 precedent (`0c4d9a0` / `e20445f`).
- **HT-5:** Build cycle exceeds 90 min wall-clock → halt with partial findings (per dispatcher's halt-trigger #5).
- **HT-6:** Post-edit smoke (AC.FBE.9.5) regresses (any step exits non-zero) → halt + surface.
- **HT-7:** ODD §2.5 violation discovered in any touched file → halt + surface; do NOT silently extend or fix in-band.
- **HT-8:** Audit (Bucket 2) discovers a CLI-side bug requiring source-side fix in a NON-fence component → halt + surface (the fence is loam-init only; other components' fixes need their own amendment).

---

## 11. Risks

- **Risk: Resolver semantics ambiguous.** The smart-default rule "if cwd is a git tree, use cwd as `--from`" is simple but doesn't capture every reasonable scenario (e.g., user runs from inside the venv subdir which is NOT a git tree itself but is inside a git tree). Mitigation: stick to the literal "is `Path.cwd() / '.git'` a directory" check; document this in the help text. Out-of-scope cases produce clear exit-2 messages.
- **Risk: README example path `~/loam-workspace` is opinionated.** Operators may want a different convention. Mitigation: the example is illustrative; the prose says "e.g." or similar. The CLI accepts any path.
- **Risk: Test inversion in `test_AC_FBE_1_3_canonical_source_required` may break a downstream test that depends on the old contract.** Mitigation: grep + read all `--from` references in `framework/loam-init/tests/` before the inversion; update any cross-test deps.
- **Risk: Bucket 2 audit table misses a documented command.** Mitigation: §6.4 enumerates all known commands; the smoke (AC.FBE.9.5) verifies the END-USER literal flow runs end-to-end. If a command is missed, the smoke catches it.
- **Risk: Partner-prefix gap recurs.** Per FBE.4/FBE.5 precedent. Mitigation: apply with watchful eye; hand-correct if needed; document in seal narrative.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Bucket 1 source + tests + component README commit** — single commit covering `framework/loam-init/src/loam/loam_init/cli.py` + 5 test file updates + `framework/loam-init/README.md`.
3. **Bucket 2 doc edit commit** — single commit covering `README.md` + `docs/getting-started.md` + `docs/install-from-source.md` (the `loam init .` → `loam init ~/loam-workspace` substitutions + adjacent prose).
4. **HOL seal narrative anchor commit** — `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe9` NEW file (mirrors FBE.6/FBE.6b/FBE.8 pattern).
5. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe9.manifest.yaml` (1 fence component: loam-init; HOL narrative-only via universal admission).
6. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bump in loam-init; sidecar advances).
7. **Corrective commit (if partner-prefix gap recurs)** — per FBE.4/FBE.5 precedent.
8. **`loam amend seal`** — produces deterministic seal commit; sidecars advance to seal SHA; narrative appends.
9. **Smoke verification (AC.FBE.9.5)** — POST-seal; verify shipped behaviour against the seal-bumped tree.
10. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 add `### FBE.9` subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/rebuild/plans/` universal prefix).
11. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe9-status-2026-05-03.md` with seal report.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **FBE.6b status (BLOCKER-FBE6b.1 origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6b-status-2026-05-03.md`.
- **FBE.6b sweep report (BLOCKER-FBE6b.1 detailed reproduction):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-0-foldback-fbe6b-sweep-report.md`.
- **FBE.8 status (closures FBE.6b verified):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe8-status-2026-05-03.md`.
- **FBE.6 status (FOLDBACK origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6-status-2026-05-03.md`.
- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 register FBE.6b row + closing sequence.
- **FBE.8 sub-plan + manifest (recent CLI/doc-fix amendment template):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe8.{md,manifest.yaml}`.
- **FBE.1 sub-plan (loam-init origin):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe1.md`.
- **bootstrap_new_workspace contract:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:459-632`.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-8).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to loam-init component only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1-9 explicit).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at" claim has a path/line citation; SHAs computed empirically not guessed).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (AC.FBE.9.{3,4} tightened doc-text scope).
  - `feedback_critical_thinking_on_deviations` (Surface #1 weighed Mode-A vs Mode-B by outcome × cost × risk).
  - `feedback_value_proposition_as_prime_objective` (Buckets 1-2 ladder to AC.PO.1 + AC.PO.2 via FBE.6c → M12).
  - `feedback_principle_conflict_resolution_multi_signal` (Surface #1 Mode-A vs Mode-B resolved via the multi-signal process: tight scope of dispatcher's brief × Mode-B's bigger-than-small-fix scope × FUTURE_IDEAS_DRAFT availability).

---

## 14. AI-time band

- Predicted: **30–60 min, midpoint 45 min**; dispatch hard cap 90 min.
- Justification: 1 small CLI fix + 5 test file updates + 3 public-doc edits (4-5 substitutions across 3 docs) + 1 component-README edit + manifest YAML + apply (1-fence; partner-prefix watchful eye) + seal + smoke + parent §8 backfill + status file. Per rubric: 1-component amendment with surgical CLI + doc edits is closer to 30-45 min midpoint; widen upper bound for the audit table maintenance + potential partner-prefix corrective.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Bucket 1 source + tests + component README commit: `<TBD>`.
- Bucket 2 public-doc edit commit: `<TBD>`.
- HOL narrative anchor commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Corrective commit (if needed): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.9 sub-plan-doc. Ready to build.*
