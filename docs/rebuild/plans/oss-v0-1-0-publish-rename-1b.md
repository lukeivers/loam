# OSS v0.1.0 publish — M1b — env-vars + per-host config dir — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Prior sub-amendment:** M1a — docs/prose-only brand rebrand (sealed `143d465`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1a.md` §12).
**Programme position:** Second sub-amendment of the M1.rename multi-amendment series. Independent of M1a; lands second per series-master ladder convention (cheapest-first).
**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 items 2 + 3 (per-host config dir + env-var prefix).
- `.scratch/claude-output/loam-rename-migration-plan.md` §2.5 (configuration-surface inventory + env-var dedupe recommendations).
- `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` §2 (sub-amendment ladder), §5 (series-wide hard constraints), §7 (series-wide halt triggers).
- `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (M1 row needs replacement with M1a..M1g ladder; **M1b includes that precursor doc-only commit per series-master §11 / M1a's recommendation**).

---

## 1. Summary / TLDR

**M1b lands two coupled rename surfaces:**

1. **Per-host config dir `~/.pos/` → `~/.loam/`.** All path constants in code + scripts + docs that name `~/.pos/` (or `Path.home() / ".pos"` or `expanduser("~/.pos/...")`) update to the new path. A one-shot per-host migration helper relocates an existing `~/.pos/` directory to `~/.loam/` on first invocation; safe to re-run.
2. **Env-var prefix `POS_V2_*` → `LOAM_*`** for the seven unique (post-dedup) environment variables. Two pre-rename names — `POS_V2_ROOT` and `POS_V2_REPO` — name the same concept (repo root) and dedupe to a single `LOAM_REPO`. One — `POS_V2_POS_ROOT` (the doubled "POS" — research §2.5 §A) — renames to `LOAM_DATA_DIR`. The remaining four straight-rename to their `LOAM_*` analogues.

**Hard cutover** per series-master §1 D-RNM.3. No fallback module that reads both names; no `.environ.get("LOAM_X", os.environ.get("POS_V2_X"))` style compat. Pre-public release; zero existing users; the migration helper handles the one machine state Luke owns.

**What does NOT land in M1b** (deferred per series-master §2 ladder):
- The workspace-side sentinel directory `<workspace>/.pos/` (used by HOL hooks: bash-guard.log, tdd-guard.log, active-scope.json, session-state/, first-run.state, etc.) **stays as `.pos/` for now.** It is a separate surface from the per-host config dir — same name (`.pos`) but different containing path (`<workspace>/` vs `~/`). Per `loam-rename-decisions.md` Tier-1 #2 the rename target is **per-host config dir** specifically. Workspace-sentinel-dir rename is not scoped in the decisions catalogue and is deferred to a future amendment (likely cascades cleanly with M1e namespace pivot or its own dedicated sub-amendment if surfaced).
- Internal Python identifiers carrying the `POS_V2_` prefix as variable-name decoration (`_POS_V2_COMMAND_MARKERS`, `_POS_V2_SURFACE_PATTERNS`, `_POS_V2_USER_PROMPT_SUBMIT_COMMAND_MARKERS`, `CANONICAL_POS_V2_PATH`, etc. in `framework/hands-off-lifecycle/hooks/`) and string-literal classifications (`CLASSIFICATION_POS_V2_DEV = "pos-v2-dev"` in workspace-bootstrap) — these are namespace-prefix surfaces, not env-vars. They rename in M1e (namespace pivot).
- `POS_V2_PATH` Python-internal constant in `framework/hands-off-lifecycle/hooks/first_run_settings.py` — internal symbol, not an env var. M1e.
- launchd labels `com.pos-v2.*` — M1c.
- OTel `pos.*` roots — M1d.
- Code imports `from pos_<comp>` — M1e.
- `pos-amend` CLI rename — M1g.
- graceful-degradation → dormancy — M1f.
- `~/.pos/degradation.sqlite` and `~/.pos/degradation-config.yaml` filename portions — M1f's dormancy rename owns the second-segment update; M1b updates only the `~/.pos/` → `~/.loam/` first-segment portion (so post-M1b the file lives at `~/.loam/degradation.sqlite`; post-M1f it becomes `~/.loam/dormancy.sqlite`).
- Path strings of form `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred per `oss-v0-1-0-publish.md` §6.
- `POS_V2_*` references inside historical seal narratives (`framework/<comp>/seals/SEAL_COMMIT.*`) — preserved per `loam-rename-decisions.md` Q2 (history keeps contemporary terminology).
- `POS_V2_*` references inside historical plan-docs at `docs/rebuild/plans/*` — historical method-record; preserved (consistent with M1a's same exclusion).

**Sealed-component fence (post-build):** The per-host `~/.pos/` surface lands across **eleven** sealed components touching either `Path.home() / ".pos"` (or equivalent) in src/scripts/hooks, or the env-vars at runtime: `cost-governance`, `graceful-degradation`, `hands-off-lifecycle`, `memory-system`, `observability-aggregator`, `orchestrator`, `primary-persona`, `self-correction`, `self-upgrade`, `telegram-interface`, `workspace-bootstrap`. Plus one code-path under `framework/tools/upgrade-merge-resolver/` (one docstring reference). Plus `framework/first-run-inventory.yaml` (one path-string reference; admitted by H19's existing entry).

**This eleven-component fence is wider than the series-master §2 estimate of "likely 3–5 components"** — see §11 finding #1 for the disclosed surface-inventory mismatch and the rationale for keeping the fence wide rather than splitting M1b further. The dispatch's authority text ("All code-side path constants and string literals referencing `~/.pos/`") is the binding scope; the series-master estimate is non-binding. A wider fence here matches the size M1e (namespace pivot) will require anyway, so the surface inventory does not reshape the series ladder.

**Estimate:** 60–120 min AI-time per the duration rubric (multi-component mechanical-substitution category; eleven components in fence; medium-volume surface; light test impact since the target paths are all default values overrideable in tests; M1a calibration suggests +10–20% surrounding-debt tax since M1a absorbed the bulk).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1b closes the env-var-prefix and per-host-config-dir portion. Subsequent sub-amendments close the remaining code-side portions (launchd, OTel, namespace, dormancy, CLI).
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — M1b stabilises the per-host path the M2 partition manifest will reference (the `~/.loam/` path becomes the canonical post-rename target for any partition rule referencing per-host state).
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary in env-var names the user reads when configuring (e.g. when overriding for tests or production deploys).
- **AC.PO.2** (VALUE_PROPOSITION harness test) — the `~/.loam/` path becomes the harness's per-host state root; future plugin-ecosystem composition reads this single canonical path.

**Sealed-component fence (preliminary — see §4 ACs + §11 surface-inventory):** eleven sealed components touched in src/scripts/hooks, plus one tool, plus `first-run-inventory.yaml`. The amendment manifest YAML lists the eleven sealed components.

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose changed in M1b's diff traces back to AC.RNM-1b.1 .. AC.RNM-1b.S below. Mechanical rename of env-var literals + path constants only; no behaviour changes; no defensive-`if` admissions; no cross-mode-debt cascade beyond the named surface.

---

## 3. Three-lens analysis (abbreviated; series-master §4 covers cross-cutting)

- **Lens 1.** Pass. Preserves every existing Claude-native composition (PreToolUse hooks, MCP, skills, plugins). The `settings.json.fragment` template referencing `${POS_V2_REPO}` updates to `${LOAM_REPO}`; first-run scaffolding writes the new variable into the user's `.env` / shell-init at first invocation post-rename. No Claude-Code-shape disturbed.
- **Lens 2.** Primary-persona pass. The user reading their own `.env` / shell-config sees `LOAM_REPO`, `LOAM_DATA_DIR`, etc. — single brand-vocabulary surface. Harness pass — the `~/.loam/` path becomes the canonical per-host state root that future plugins read from.
- **Lens 3.** Pure mechanical-substitution work plus a one-shot migration helper. Outcome-shaped ACs (post-rename grep counts in named files; idempotent-helper-runs-twice check; first-run-on-clean-machine-creates-`~/.loam/` check). Method-shape (sed, Edit, helper script implementation) is the builder's call inside the AC outcome bound.

---

## 4. Acceptance criteria — AC.RNM-1b.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.RNM-1b.1 — Env-var dedup + rename completes across all callsites

The seven post-rename env-var names appear at every callsite where the pre-rename names appeared, with the dedupe of `POS_V2_ROOT` + `POS_V2_REPO` collapsed to a single `LOAM_REPO`:

| Pre-rename | Post-rename | Dedup? |
|---|---|---|
| `POS_V2_POS_ROOT` | `LOAM_DATA_DIR` | rename + de-doubling |
| `POS_V2_PYTHON` | `LOAM_PYTHON` | rename only |
| `POS_V2_ROOT` | `LOAM_REPO` | dedup with REPO |
| `POS_V2_REPO` | `LOAM_REPO` | dedup with ROOT |
| `POS_V2_WORKSPACE_ROOT` | `LOAM_WORKSPACE_ROOT` | rename only |
| `POS_V2_WORKSPACE_SLUG` | `LOAM_WORKSPACE_SLUG` | rename only |
| `POS_V2_FIRST_RUN_NO_TTY` | `LOAM_FIRST_RUN_NO_TTY` | rename only |
| `POS_V2_FIRST_RUN_PROGRESS_FILE` | `LOAM_FIRST_RUN_PROGRESS_FILE` | rename only |

**Outcome:** `grep -rE 'POS_V2_(POS_ROOT|ROOT|PYTHON|FIRST_RUN_NO_TTY|FIRST_RUN_PROGRESS_FILE|REPO|WORKSPACE_SLUG|WORKSPACE_ROOT)\b' framework/ --include="*.py" --include="*.sh" --include="*.fragment"` returns 0 matches. Historical seal narratives + historical plan-docs are excluded from the count (preserved per `loam-rename-decisions.md` Q2 / M1a precedent).

### AC.RNM-1b.2 — Per-host config dir path-constant rename completes

Every code/script/hook source reference to `~/.pos/` — whether as `Path.home() / ".pos"`, `Path("~/.pos/...")`, `expanduser("~/.pos/...")`, `"~/.pos/..."` (string literal), or `$HOME/.pos` (shell) — becomes the corresponding `~/.loam/` form. Doc-prose references inside `src/`-folder docstrings and component-internal `docs/` folders (e.g. `framework/observability-aggregator/docs/bootstrap-registration-guide.md`, `framework/graceful-degradation/docs/architecture.md`) update concurrently because they're code-adjacent and the rename leaves them stale otherwise.

The workspace-side `<workspace>/.pos/` sentinel directory is a **distinct surface** (per §1 / §6); references like `tmp_path / ".pos"`, `workspace_root / ".pos"`, `POS_SUBDIR = ".pos"` (in `workspace_bootstrap/workspace_paths.py` and `hands-off-lifecycle/hooks/_gate_helpers.py`), `<workspace>/.pos/active-scope.json`, `<workspace>/workspace/.pos/bash-guard.log`, etc. **stay unchanged** in M1b.

**Outcome:** `grep -rE 'Path\.home.*\.pos\b|HOME/\.pos\b|"~/\.pos|expanduser.*\.pos' framework/ --include="*.py" --include="*.sh"` returns 0 matches. Workspace-sentinel-dir references are not in this grep's scope (they don't anchor on `home`, `HOME`, `~/`, or `expanduser`).

### AC.RNM-1b.3 — Per-host migration helper exists and is idempotent

A one-shot migration helper (builder picks path: `framework/tools/loam-migrate-host-config/` OR a workspace-bootstrap first-run sub-step OR a top-level `framework/tools/<name>` script — builder's call within the helper-purpose bound) does the following on invocation:

1. If `~/.loam/` does NOT exist and `~/.pos/` exists: rename `~/.pos/` to `~/.loam/`. Print summary of what moved.
2. If `~/.loam/` exists and `~/.pos/` does not exist: report "already migrated"; exit 0.
3. If neither exists: report "no per-host state present; nothing to migrate"; exit 0.
4. If BOTH `~/.loam/` and `~/.pos/` exist: HALT with non-zero exit. Print clear message naming both directories' presence and explicitly refusing to merge or clobber. The user resolves manually (review / back up / delete one) before re-running.

The helper is safe to re-run after any of cases 1–3 succeed. Re-run after success hits case 2 (already migrated). Re-run after case 4 surfaces the same conflict until the user resolves it.

**Outcome:** the helper script exists, is executable, and demonstrably:
- on a synthesised fresh `~/.loam/`-absent + `~/.pos/`-present test setup, performs the rename and prints a non-empty summary;
- on a re-run, prints "already migrated" and exits 0;
- on a synthesised `~/.loam/`-AND-`~/.pos/`-present test setup, prints the conflict message and exits non-zero;
- on a fresh-machine simulation (neither dir), prints "nothing to migrate" and exits 0.

The helper is documented in its own file (README or top-of-file docstring) covering invocation and the four cases.

### AC.RNM-1b.4 — Programme master plan §5 reflects M1a..M1g ladder

`docs/rebuild/plans/oss-v0-1-0-publish.md` §5's `M1.rename` row is replaced with seven rows (M1a..M1g) that mirror the series-master §2 ladder. Each row carries its own description, AC reference, AI-time range, and midpoint. The programme total at the end of §5 updates to reflect the post-split sum.

This is the precursor doc-only commit M1a's agent recommended (§12 "Dependents cleared to dispatch" of `oss-v0-1-0-publish-rename-1a.md`). It lands as a doc-only commit BEFORE the M1b sub-plan commit so the programme plan reflects the post-split ladder when M1b's manifest references it.

**Outcome:** §5's table contains rows for M1a (sealed), M1b (this amendment), M1c, M1d, M1e, M1f, M1g — each with description + ACs + AI-time + midpoint. The programme-total prose updates from "30–60 min midpoint 45 min" to roughly the post-split sum (~4–8 h per series-master §2.5).

### AC.RNM-1b.5 — Migration-helper documentation surfaces the rename for the operator

The migration helper's documentation (whether top-of-file docstring or accompanying README) names: (a) what changes (`~/.pos/` → `~/.loam/`); (b) the four idempotency cases; (c) what the user does in the conflict case (case 4). This satisfies clause (e) of self-upgrade's breaking-change-with-migration-path category at the brand-rename layer (per migration research §3.3).

**Outcome:** the helper's docs cover the four cases in named-case form. The documentation lives at the helper's path (no separate global rename-runbook required).

### AC.RNM-1b.S — Sealed-component fence narrows to env-var + path-constant surfaces only

Eleven-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; this is many sub-amendments before M1g's CLI rename). The amendment manifest YAML lists eleven sealed components. The `seal_diff` `allowed_prefixes` admit `framework/<comp>/` for each touched component plus the universal paths plus `framework/tools/<helper-path>/` for the migration helper plus `framework/first-run-inventory.yaml` (one-line YAML edit for the `socket_path: "~/.pos/orchestrator.sock"` value) plus `framework/tools/upgrade-merge-resolver/src/upgrade_merge_resolver/__init__.py` (one-docstring edit; admitted by `framework/tools/` allowed-prefix per H19).

**Per-component touched-test scope:** narrow to touched files. Per `feedback_amendment_dispatch_speedups`, M1b skips pre-seal full-suite rerun. Each sealed component's `tests/test_no_sealed_amendments.py` runs as part of `pos-amend apply` verification. The seal-diff fence test for AC.RNM-1b.S is the primary check (verifies the fence isn't reaching beyond env-var + path-constant surfaces).

**Outcome:** `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention; eleven per-component sidecars all advance; `pytest framework/<comp>/tests/test_no_sealed_amendments.py` per touched component PASSES.

### AC.RNM-1b.6 — No work outside the named surfaces (negative AC)

Negative AC. The amendment's git-diff includes ZERO touches outside:

- The eleven named sealed components' src/scripts/hooks/tests/docs paths.
- The migration helper's path.
- `framework/first-run-inventory.yaml` (one-line YAML edit).
- `framework/tools/upgrade-merge-resolver/src/upgrade_merge_resolver/__init__.py` (one docstring edit).
- The plan-doc + manifest YAML under `docs/rebuild/plans/`.
- The programme master plan §5 update at `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- Any necessary admission-extension to `framework/hands-off-lifecycle/tests/test_cross_cutting.py` (only if M1b's surface introduces a top-level dir not already in H19's allowed set — expected: NO new top-level dirs introduced because the migration helper lives under existing `framework/tools/` admission).

**Permitted ZERO surfaces (no edits expected):**

- No internal Python identifiers carrying `POS_V2_` decoration (`_POS_V2_*`, `CANONICAL_POS_V2_PATH`, `CLASSIFICATION_POS_V2_DEV`) — namespace work; M1e.
- No string-literal `"pos-v2"` or `"pOS v2"` — brand-prose; M1a closed those.
- No launchd `com.pos-v2.*` labels — M1c.
- No OTel `pos.*` roots — M1d.
- No `from pos_<comp>` imports — M1e.
- No `pos-amend` CLI references in code — M1g.
- No filename changes (e.g. `degradation.sqlite` → `dormancy.sqlite` is M1f).
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites — M9.
- No `framework/<comp>/seals/SEAL_COMMIT.*` historical-narrative edits.
- No `docs/rebuild/plans/*.md` historical method-record edits.
- No workspace-side `<workspace>/.pos/` sentinel-dir constant changes (`POS_SUBDIR`, `tmp_path / ".pos"`, etc.).

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Six outcome-named behaviours (env-var dedup+rename, per-host path-constant rename, migration helper idempotency, programme master plan §5 update, migration-helper docs, fence-narrowing seal) → six ACs (AC.RNM-1b.1 .. AC.RNM-1b.5 + AC.RNM-1b.S). Plus one negative AC (AC.RNM-1b.6) enforcing the env-var + path-constant fence. Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §8.5.

---

## 5. Hard constraints (M1b-specific; series-wide constraints from master §5 inherit)

- **Two-target diff with hard cutover.** AC.RNM-1b.6 is the structural fence — env-var + per-host-path-constant + migration helper + programme-plan §5 update only. No other surfaces.
- **Hard cutover.** Per series-master §1 D-RNM.3: no fallback module reading both old and new env-var names, no symlink-compat in the migration helper, no `os.environ.get("LOAM_X", os.environ.get("POS_V2_X"))` style fallback.
- **Workspace-side `<workspace>/.pos/` stays.** Out of scope per `loam-rename-decisions.md` Tier-1 #2's "per-host config dir" specificity. M1b explicitly does NOT touch `POS_SUBDIR`, `tmp_path / ".pos"`, `workspace_root / ".pos"`, or any workspace-sentinel-dir reference.
- **Workspace-bootstrap-first-run integration**: if the migration helper is implemented as a workspace-bootstrap first-run sub-step (vs a standalone tool), the helper's invocation point in first-run scaffolding is the single load-bearing call site — no implicit migration on every run, no migration during ordinary command execution. Builder's call between standalone-tool vs first-run-step.
- **Path strings under `/Users/lukeivers/ivers-corp-pos-v2/...` stay** — directory rename is M9-deferred per `oss-v0-1-0-publish.md` §6.
- **Filenames stay.** `degradation.sqlite`, `degradation-config.yaml`, `degradation.yaml` filenames don't change in M1b — second-segment is M1f's dormancy rename. M1b updates only the `~/.pos/` → `~/.loam/` first-segment portion of the path.
- **Historical seal narratives stay.** `framework/<comp>/seals/SEAL_COMMIT.*` files containing `POS_V2_*` or `~/.pos/` references are preserved per `loam-rename-decisions.md` Q2.
- **Historical plan-docs stay.** `docs/rebuild/plans/*.md` files not authored by this amendment are preserved (consistent with M1a).
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`). Corrective commits are NEW commits.
- **`pos-amend apply` runs BEFORE the seal commit.**
- **H19 retirement does NOT happen in M1b.** M1b does not touch any path in HC#4's byte-content sample (verified pre-build per finding #2 in §11). H19's `allowed` set contains every top-level dir M1b touches; no new top-level surface is introduced.

---

## 6. Out of scope (named explicitly per ODD §2.5)

- All work deferred to M1c..M1g (launchd, OTel, namespace pivot, dormancy, CLI rename).
- All work deferred to M9 (path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rename, repo directory rename).
- **Workspace-side `<workspace>/.pos/` sentinel directory** — distinct surface from per-host config dir; not in `loam-rename-decisions.md` Tier-1 list; deferred to a future amendment if surfaced (likely cascades cleanly with M1e namespace pivot).
- **Internal Python identifiers** carrying `POS_V2_` decoration — `_POS_V2_COMMAND_MARKERS`, `_POS_V2_USER_PROMPT_SUBMIT_COMMAND_MARKERS`, `_POS_V2_STOP_COMMAND_MARKERS`, `_POS_V2_STATUS_LINE_COMMAND_MARKERS`, `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS`, `_POS_V2_SURFACE_PATTERNS`, `CANONICAL_POS_V2_PATH`, `CLASSIFICATION_POS_V2_DEV`, `POS_V2_PATH` — namespace work; M1e.
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` containing `POS_V2_*` or `~/.pos/` literals — preserved.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` (other than this plan-doc + this manifest + the programme master plan §5 update) — preserved.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** — historical-narrative-heavy live docs; not in M1b's surface (M1a deferred them; M1b inherits the same defer).
- **Spec docs** at `docs/rebuild/spec/pos-v2-*.md` (filename + content) — M1e.
- **Per-component README.md** — M1a closed brand-prose; any `~/.pos/` reference inside a README.md is updated by M1b only if the README contains an actual path-constant (most don't; if a README has illustrative path-prose like "stored under ~/.pos/", that updates; if it has only brand-prose, M1a already handled it).
- **Component docs** at `framework/<comp>/docs/*.md` — M1b updates ONLY where the doc contains a `~/.pos/` path-constant the rename surfaces (e.g. `framework/observability-aggregator/docs/bootstrap-registration-guide.md`, `framework/graceful-degradation/docs/architecture.md`); otherwise preserved.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`; `git status` shows working tree clean (only the pre-existing M1a-untracked items remain). Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to M1a's seal commit `143d465` (or the dispatcher-supplied later HEAD).
3. **Programme master plan §5 update commit (precursor doc-only).** Replace the M1.rename single row in `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 with the seven-row M1a..M1g ladder. Include each sub-amendment's wall-clock estimate (taken from series-master §2 commentary; M1a actuals from `oss-v0-1-0-publish-rename-1a.md`). Update §5's programme-total prose. **Doc-only commit. Lands first.**
4. **M1b sub-plan + manifest commit.** This plan-doc + a manifest YAML at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.manifest.yaml` per the established M1a-precedent shape.
5. **Phase A — env-var rename.** Mechanical rename across the env-var-callsite files (limited inventory: `framework/hands-off-lifecycle/hooks/{first-run.sh,first_run_helper.py,first_run_progress.py,first_run_settings.py,settings.json.fragment}`, `framework/hands-off-lifecycle/tests/{test_AC_A4_settings_merge.py,test_AC_AG_*.py,test_detachment.py,test_first_run.py}`, `framework/memory-system/{src/service.py,tests/test_AC29_health_workspace_identity.py,tests/test_AC34_eager_health_after_startup.py}`, `framework/workspace-bootstrap/{src/workspace_bootstrap/adapters/{first_run_scaffold.py,tracker_seed.py},tests/test_AC_E_*.py,tests/test_AC29_scaffold_memory_port.py,tests/test_D5_plist_path_emission.py}`). The dedup of `POS_V2_ROOT` + `POS_V2_REPO` to single `LOAM_REPO` requires touching both call sites at `framework/hands-off-lifecycle/hooks/{first-run.sh,settings.json.fragment}`. Post-edit grep verifies AC.RNM-1b.1 outcome.
6. **Phase B — per-host path-constant rename.** Mechanical rename across the per-host-callsite files (eleven components' src + a few component docs). Verify each touched file uses the expected post-rename path. Verify NO workspace-side `<workspace>/.pos/` reference is touched (cross-check via grep). Post-edit grep verifies AC.RNM-1b.2 outcome.
7. **Phase C — migration helper authoring.** Implement the helper at the chosen path (builder's call: `framework/tools/loam-migrate-host-config/` standalone OR `framework/workspace-bootstrap/src/workspace_bootstrap/migrate_host_config.py` as a first-run sub-step OR a top-level script under `framework/tools/`). Authored idempotency check covering the four cases (move; already-migrated; nothing-to-migrate; conflict-halt). Document the helper at the chosen path per AC.RNM-1b.5.
8. **Phase D — migration-helper test scaffold.** A small test file (in the helper's host component's `tests/` dir, OR a standalone test if the helper is its own tool) that exercises the four cases against `tmp_path` mocks. Each case asserts the post-state + exit code.
9. **Phase E — feature commit.** Single feature commit carrying the env-var + path-constant rename diff + migration helper + helper docs + helper tests. Commit message names the M1b slug, the AC family, and the series-master pointer.
10. **Phase F — pos-amend apply.** Run `pos-amend apply` against the manifest. Verify clean apply. **`pos-amend apply` BEFORE the seal commit per FIDRAFT note from amendment #41.**
11. **Phase G — apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `pos-amend apply` convention.
12. **Phase H — seal-diff fence verification.** AC.RNM-1b.S + AC.RNM-1b.6 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named surfaces. Verify each component's `pytest framework/<comp>/tests/test_no_sealed_amendments.py` passes.
13. **Phase I — touched-test rerun.** Run the explicit test scope: every test file in the env-var + per-host-path callsite list (Phase A + Phase B), plus the migration helper's tests (Phase D), plus each touched sealed component's `test_no_sealed_amendments.py`. Per `feedback_amendment_dispatch_speedups`, the full-suite rerun is skipped pre-seal — the touched-test-only sweep is the methodology-aligned narrow verification.
14. **Phase J — `pos-amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below). The seal commit narrative cites the AC family, the dedup decision, and the migration-helper idempotency contract.

Phases 5–6 are mechanical-substitution. Phase 7 is helper authoring (the only material code-authoring in M1b). Phases 8–13 are commit + seal mechanics.

---

## 8. Halt triggers (M1b-specific; series-wide triggers from master §7 inherit)

The build agent MUST halt and surface when:

1. **An env-var read site crosses an unexpected sealed-component boundary** (per dispatch §Constraints item Halt #1). Inventory pre-build expects env-var callsites in three components only (HOL, memory-system, workspace-bootstrap); any callsite in a fourth+ component surfaces as a fence-creep signal. Halt; surface for re-scope.
2. **A per-host path-constant callsite crosses an unexpected sealed-component boundary.** Inventory pre-build expects eleven components in the per-host fence (named in §1 + §11); any callsite in a twelfth+ component surfaces as a fence-creep signal. Halt; surface.
3. **Frozen-baseline / byte-content-match invariant breach** (HC#4, AC.D.1.5, AC.M.S, etc.). Apply ODD §4 retire-and-re-extend in-band per the methodology heads-up from the dispatch; if retire is non-trivial, surface to dispatcher. **Pre-build verification** (per finding #2): HC#4's byte-content sample is in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`; the fifteen sample files contain ZERO `POS_V2_*` env-var or `~/.pos/` per-host path callsites (verified at plan time). HC#4 should remain green post-M1b without retirement.
4. **ODD §2.5 violations encountered in surrounding code.** Halt; do NOT silently extend. Surface for owner ruling on whether to fix in-band, defer, or reshape M1b's scope.
5. **`pos-amend` automation hits a gap on the env-var/path surface.** Regex narrowness (e.g. fails on `${POS_V2_REPO}` shell-substitution syntax), abs-path requirement, manifest-validation false-positive on the eleven-component fence. Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
6. **The `~/.pos/` → `~/.loam/` migration would clobber existing `~/.loam/` state** (case 4 in AC.RNM-1b.3). Means a prior-attempt artefact exists. Halt for owner ruling on whether to merge or back up. **The migration helper itself enforces this halt** by exiting non-zero in case 4 — so the production-side instance is structural; the dispatcher-time halt is ONLY relevant if the BUILD-time agent's machine has both dirs (which would mean a prior partial-attempt against the canonical tree).
7. **Cross-mode debt** (loam-mode F-register, hands-off-lifecycle allowed_prefixes, dispatch-template path refs) that prevents env-var or per-host-path rename from landing cleanly.
8. **AC.RNM-1b.6 fence is breached.** The diff reaches outside env-var + path-constant + migration-helper + plan-doc + programme-plan-§5 surfaces. Halt; do not "fix" by widening the AC; the over-reach IS the failure signal.
9. **A `loam` identifier or `LOAM_*` env-var name already in use** in any of the named surfaces (e.g. an example fixture, an existing constant). Halt; surface for rename-the-conflicting-use first.
10. **Wall-clock exceeds 2 h** (M1b is rubric-priced 60–120 min midpoint 90 min; 2 h is 1.33×). Halt with current-state report; dispatcher triages continue / split-further / pause.
11. **Pre-existing test fails post-rename.** Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis. (Distinguish from pre-existing flaky tests recorded in FIDRAFT.)
12. **A `POS_V2_*` reference is found in `framework/<comp>/seals/SEAL_COMMIT.*`** during touched-test verification — historical narratives are preserved per `loam-rename-decisions.md` Q2; if a sealed-narrative cross-reference assertion ties a marker phrase to a `POS_V2_*` literal AND the marker is brand-keyed (vs intent-keyed), apply `feedback_loose_AC_text_fix_AC_not_implementation` per M1a's #9 precedent.

---

## 9. Risks (M1b-specific)

1. **Environment variable plumbing through Claude Code `settings.json`.** `settings.json.fragment` references `${POS_V2_REPO}`. Claude Code reads `settings.json` at session-start; if the user's existing `.claude/settings.json` contains the substituted absolute path (not the variable), no env-var change at runtime affects them. But the **fragment** ships as the canonical template; first-run scaffolding writes the substituted path into the user's `settings.json`. M1b's fragment edit changes the variable name; first-run scaffolding's substitution code ALSO updates from `os.environ["POS_V2_REPO"]` to `os.environ["LOAM_REPO"]`. Hard cutover means: a session opened pre-rename works (its already-substituted `settings.json` has the absolute path); a session opened post-rename works (the new fragment substitutes from `LOAM_REPO`). The risk is a partial state where the fragment uses `${LOAM_REPO}` but the substitution code still reads `POS_V2_REPO` (or vice versa) — caught by Phase I's touched-test rerun.
2. **`POS_V2_ROOT` + `POS_V2_REPO` dedup collision.** Two pre-rename names mapping to one post-rename name. The dedup is correct conceptually (both name the repo root) but mechanically requires careful per-callsite review: every `POS_V2_ROOT` callsite gets `LOAM_REPO`; every `POS_V2_REPO` callsite ALSO gets `LOAM_REPO`. A naive `s/POS_V2_ROOT/LOAM_REPO/g; s/POS_V2_REPO/LOAM_REPO/g` works because the two names are textually distinct. Mitigation: targeted Edit per callsite (not global sed); post-edit grep for both pre-rename names returning 0.
3. **Wide eleven-component fence amplifies the per-component test surface.** The narrow-test-scope speedup (per `feedback_amendment_dispatch_speedups`) excludes the full-suite rerun pre-seal; relies on each touched component's `test_no_sealed_amendments.py` plus the touched test files. Risk: a non-touched-test-file integration test depends on `POS_V2_X` and breaks silently. Mitigation: Phase I runs the touched tests; if a flaky-or-broken non-touched test surfaces post-seal in a follow-on amendment's pre-flight, it goes through the standard FIDRAFT recovery flow.
4. **HC#4 byte-content sample drift.** The fifteen sample files in `test_d1_byte_content_match.py` are pinned by SHA-256. Verified pre-build: none contain a per-host `~/.pos/` or `POS_V2_*` env-var callsite. Risk: a sample file contains an indirect dependency (e.g. imports a module that has the rename-affected constant) — but byte-content is on the FILE bytes, not the imported behaviour; an import-target rename doesn't change the importer's bytes. Mitigation: pre-build verification confirmed clean.
5. **The migration helper running at the wrong time.** If implemented as a first-run sub-step that runs on every workspace-bootstrap invocation (not just first-run), it could be called repeatedly and either (a) fire idempotently (case 2 = noop) or (b) fire on a partial-prior-attempt (case 4 = halt). Case (b) is a halt-trigger, not a safety violation, but a confused user might run it inside a workspace where they just deleted `~/.loam/` for testing. Mitigation: the helper's docs (AC.RNM-1b.5) name the four cases; the helper invocation point is the single load-bearing site (not a recurring hook).
6. **Workspace-side `<workspace>/.pos/` confusion.** A reader of M1b's diff might assume the workspace-sentinel-dir rename is also in scope and grep for residual `.pos` in tests. Mitigation: §1 + §6 + AC.RNM-1b.2's outcome statement explicitly name the workspace-side surface as out of scope; the post-rename grep is anchored on `home`, `HOME`, `~/`, `expanduser` to avoid false positives on workspace paths.
7. **`POS_V2_DEV` and `CLASSIFICATION_POS_V2_DEV` confusion.** `POS_V2_DEV` is sometimes misread as an env-var (the spelling matches the `POS_V2_*` env-var pattern). It is NOT — it is part of the Python identifier `CLASSIFICATION_POS_V2_DEV` whose string value is `"pos-v2-dev"`. Both are namespace work, not env-var work. M1b explicitly excludes them (§6). Mitigation: AC.RNM-1b.1's grep regex names the seven targeted env-var basenames explicitly; `DEV` is not in the list.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per series master §1, all three D-RNM rulings (split, namespace shape, no compat window) closed at owner-ruling time. The dispatch's authority text + the locked rulings cover M1b's scope cleanly.

**Builder's calls within ACs (NOT requiring owner ruling):**

- D-build.M1b.1 — Migration helper path. Three options:
  1. Standalone tool at `framework/tools/loam-migrate-host-config/` (pattern follows existing `framework/tools/<name>/` layout).
  2. Workspace-bootstrap first-run sub-step at `framework/workspace-bootstrap/src/workspace_bootstrap/migrate_host_config.py` (composes with first-run scaffolding).
  3. A simple top-level shell script under `framework/tools/<short-name>` (no Python module).
  Recommendation: option 1 (standalone tool) for clean separation, ease of re-running outside first-run, and simplest test scaffold. Builder's call within AC.RNM-1b.3.
- D-build.M1b.2 — Migration helper invocation timing. Two options:
  1. Run unconditionally as the first step of workspace-bootstrap first-run scaffolding (auto-migrate on first-run for any clone).
  2. Run only on explicit invocation; first-run prints a one-line instruction if `~/.pos/` exists and `~/.loam/` does not.
  Recommendation: option 2 (explicit invocation; first-run advisory) — aligns with the structural-over-advisory principle BUT the migration is per-host (not per-workspace) so auto-running it from per-workspace first-run is the wrong layer. Builder's call within AC.RNM-1b.3.
- D-build.M1b.3 — Component-internal docs sweep boundary. AC.RNM-1b.2's outcome lets the builder choose how broadly to update component-internal `docs/*.md` files. Recommendation: update only where the doc contains a load-bearing path-constant (the five files identified in surface inventory: `framework/observability-aggregator/docs/bootstrap-registration-guide.md`, `framework/graceful-degradation/docs/architecture.md`, plus three more if surfaced during build). Skip docs that mention `~/.pos/` only as historical/incidental prose. Builder's call within AC.RNM-1b.2.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(Scope-mis-estimate disclosure — non-blocking; documented in §1.) The series-master §2 ladder's M1b row prices the fence at "likely 3–5: workspace-bootstrap, hands-off-lifecycle, memory-system, primary-persona".** Empirical surface inventory at plan time:
   - **Env-var callsites** stay narrow: three sealed components (HOL, memory-system, workspace-bootstrap) host all `os.environ.get(POS_V2_*)`-class read sites, the seven-key dedup-rename map, and the `${POS_V2_REPO}` substitution pattern.
   - **Per-host `~/.pos/` path-constant callsites** are wide: **eleven sealed components** in src/scripts/hooks: `cost-governance` (2 src files), `graceful-degradation` (1), `hands-off-lifecycle` (4), `memory-system` (3 — adds tests + scripts), `observability-aggregator` (1 + 1 doc), `orchestrator` (4 src + 2 scripts), `primary-persona` (1), `self-correction` (1), `self-upgrade` (2 src + 1 doc + 1 script), `telegram-interface` (2), `workspace-bootstrap` (2). Plus `framework/tools/upgrade-merge-resolver/` (1 docstring) and `framework/first-run-inventory.yaml` (1 path-string).
   The dispatch's authority text ("All code-side path constants and string literals referencing `~/.pos/`") binds the scope to **all** path constants, not "likely 3–5 components". The series-master estimate was non-binding. Resolution: author the plan with the wide eleven-component fence; the wider fence matches the size M1e (namespace pivot) will require anyway, so the surface inventory does not reshape the series ladder.
2. **(Verification result — non-blocking.) HC#4 byte-content sample is clean.** The fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (5 each from primary-persona, workspace-bootstrap, scope-of-work) contain ZERO `POS_V2_*` env-var callsites and ZERO per-host `~/.pos/` path callsites (the one match found in `framework/primary-persona/src/cli.py` is a `<workspace>/.pos/...` workspace-sentinel reference, NOT per-host, and is out of scope per §6). HC#4 should remain green post-M1b without retirement; H19 retire-and-rebaseline does NOT happen here.
3. **(Pre-emptive scope guard — non-blocking.) Workspace-side `<workspace>/.pos/` is a distinct surface from per-host `~/.pos/`.** The two share the dirname `.pos` but are containing-path-distinct (`~/` vs `<workspace>/`). Per `loam-rename-decisions.md` Tier-1 #2 the rename target is **per-host config dir** specifically; the workspace-side sentinel dir is not in the decisions catalogue. M1b explicitly excludes it (§6); AC.RNM-1b.2's grep regex anchors on `home`, `HOME`, `~/`, `expanduser` to ensure the workspace-side surface isn't false-positive-hit.
4. **(Pre-emptive scope guard — non-blocking.) `POS_V2_DEV` / `CLASSIFICATION_POS_V2_DEV` are NOT env-vars.** They are namespace-prefix decorations on Python identifiers (`CLASSIFICATION_POS_V2_DEV = "pos-v2-dev"` in `framework/workspace-bootstrap/src/workspace_bootstrap/adapters/tracker_seed.py`). Same for `_POS_V2_COMMAND_MARKERS`, `_POS_V2_USER_PROMPT_SUBMIT_COMMAND_MARKERS`, `_POS_V2_STOP_COMMAND_MARKERS`, `_POS_V2_STATUS_LINE_COMMAND_MARKERS`, `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS`, `_POS_V2_SURFACE_PATTERNS`, `CANONICAL_POS_V2_PATH`, `POS_V2_PATH` (a Python-module-level constant). All are namespace work; M1e. M1b explicitly excludes them (§6); AC.RNM-1b.1's grep regex names the seven specific env-var basenames to avoid false-positive sweeps.
5. **(FUTURE_IDEAS_DRAFT — pre-emptive.)** Plan-time observation: a recurring pattern across the M1.rename series is "selective grep-rename — change path constants, keep namespace-decorated identifiers, keep workspace-side dirnames". A future improvement would be a `loam-rename-helper` script in `framework/tools/` that takes a rename map (path-constant pattern; namespace-prefix pattern; workspace-side allowlist) and applies the rename only where the pattern matches the surface class. Captured here for the build agent to surface to FIDRAFT post-build (do NOT extend M1b scope to add it).
6. **(No ODD §2.5 violation found in surrounding code/docs at plan-authoring time.)** The mechanical rename is the rename plus a one-shot helper; no defensive `if`s without backing AC; no behaviour changes beyond the rename + helper. The eleven-component fence is wider than the series-master estimate (finding #1) but each component's rename-touched lines all trace back to AC.RNM-1b.1 / .2 / .3.
7. **(No methodology breach in plan structure.)** ACs are outcome-shape, deterministic, behaviour-count-checked. AC.RNM-1b.6 (negative AC enforcing the env-var + path-constant + migration-helper + plan-doc fence) is the explicit ODD §2.5 reverse-direction protection. The wider fence is disclosed (finding #1) so the dispatcher sees the surface in the plan-doc commit before the feature commit.

---

## 12. Method-decision register (placeholder)

The method-decision content for M1b lives in §14 below per the
`pos-amend seal --plan-doc` convention (which expects §14 as the
SHA-backfill anchor). Content moved to §14 to avoid duplication.

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the migration helper's own tests.
- AC.RNM-1b.1: HOL `test_first_run.py`, `test_detachment.py`; memory-system `test_AC29_health_workspace_identity.py`, `test_AC34_eager_health_after_startup.py`; workspace-bootstrap `test_AC29_scaffold_memory_port.py`, `test_D5_plist_path_emission.py`, `test_AC_E_*.py`.
- AC.RNM-1b.2: each component's per-host-touched test files (e.g. graceful-degradation `test_d8_state.py`, `test_d10_garbage_false_positive.py`, `test_d7_resume.py`; workspace-sync `test_sync_config.py`).
- AC.RNM-1b.3 + AC.RNM-1b.5: migration helper `test_migrate.py` + `test_cli.py` (11 tests, all pass).
- AC.RNM-1b.S: each sealed component's `test_no_sealed_amendments.py` + HOL `test_cross_cutting.py` (HC#4 sample remains green; H19 retirement NOT triggered).

### Backwards-compat verification

N/A — hard cutover per series-master D-RNM.3.

### HC#4 byte-content sample status

GREEN. The fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` were not touched by M1b's rename (verified pre-build per §11 finding #2; verified post-build by 16 passing tests in HOL's full suite). HC#4 retains its frozen-baseline; H19 retirement does NOT happen at M1b.

### Dependents cleared to dispatch

- **M1c** (launchd labels `com.pos-v2.<slug>.*` → `com.loam.<slug>.*`) cleared to dispatch. Dispatcher should author `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c.md`. Pre-build verification: confirm whether HOL's H19 byte-content sample includes any plist file (expected: yes — M1c may trigger H19 retire-and-rebaseline per series-master §1).
- M1c..M1g remain serial in the shared tree per `feedback_serialize_amendment_builds`.

---

## 14. Method-decision register (post-build)

### D-build.M1b.1 — Migration helper path

**Standalone tool** at `framework/tools/loam-migrate-host-config/` (option 1 from §10). Pattern follows the existing `framework/tools/<name>/` layout (orphan-plist-cleanup precedent). Reasoning: clean separation from workspace-bootstrap first-run; ease of re-running outside first-run; simplest test scaffold (own pytest config, own conftest, no fixture dependency on workspace-bootstrap's heavy fixtures).

### D-build.M1b.2 — Migration helper invocation timing

**Explicit invocation; no auto-run** (option 2 from §10). The migration is per-host, not per-workspace. Auto-running it from per-workspace first-run would fire it multiple times across multiple workspaces on the same machine, with the second-onwards firings hitting case 2 (no-op) or case 4 (halt). The structural-over-advisory principle says: name the surface the user uses; don't hide the migration inside an unrelated lifecycle event. The helper's README names invocation explicitly; framework code reading `~/.loam/` finds the dir absent on a fresh-clone post-rename and (per existing fail-closed behaviour for missing config dirs) raises a clear "config dir not present" error that names the helper as the remediation.

### D-build.M1b.3 — Component-internal docs sweep boundary

Updated **only where component-internal docs carry load-bearing path-constants** (per §10 recommendation). Five components touched at the docs surface:
- `framework/graceful-degradation/docs/architecture.md` (config + sqlite path examples).
- `framework/observability-aggregator/docs/{api-reference,architecture,bootstrap-registration-guide,cli-reference,data-flow,prose-explanation,relationship-map}.md` (base_dir + db_path examples; bootstrap.py wiring docs).
- `framework/orchestrator/docs/{api-reference,architecture,operations,relationships}.md` (sqlite + sock paths; logs dir; bootstrap.py path; observability sql examples).
- `framework/self-upgrade/docs/{architecture,cli-reference,conflict-report-reference,notification-flow}.md` (paths.py-derived locations; conflict report example paths).
- `framework/workspace-bootstrap/README.md` (manifest default path; canonical-cache path; legacy-user-config docstring).

Skipped: docs that mention `~/.pos/` only as historical/incidental prose (none surfaced in the sweep). The graceful-degradation README + the per-component READMEs M1a touched were either already brand-shaped or did not contain per-host path-constants.

### D-build.M1b.4 — POS_V2_ROOT + POS_V2_REPO dedup mechanics

The dedup collapsed two pre-rename names (`POS_V2_ROOT`: HOL shell-script env-read at `first-run.sh:117`, `first-run.sh:73`'s sibling test in `test_detachment.py:578,598`; `POS_V2_REPO`: `settings.json.fragment` `${POS_V2_REPO}` substitutions × 4 callsites) to a single `LOAM_REPO` post-rename. No per-callsite ambiguity surfaced — the two names were textually distinct so global Edit-with-`replace_all` per file landed cleanly. Verified by grep-count returning 0 for both pre-rename names post-build.

Note: the **internal shell variable** `POS_V2_ROOT` in `first-run.sh` (set at lines 54, 62; referenced at 68, 69, 167) is NOT the env-var read site — it's a script-internal identifier holding the workspace root (set by `CLAUDE_PROJECT_DIR` or script-relative resolution, then passed via `--pos-v2-root` flag). It stays unchanged in M1b per AC.RNM-1b.6's exclusion of internal-prefix decorations; it renames in M1e.

### Commit SHAs

(populated by `pos-amend seal --plan-doc` SHA-backfill below)

---

## 15. References

- **Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Prior sub-amendment:** `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.md` (sealed `143d465`).
- **Authority documents (inherited from series master):**
  - `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 items 2 + 3.
  - `.scratch/claude-output/loam-rename-migration-plan.md` §2.5 + §3.3.
- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (M1b includes §5 ladder-replacement precursor commit).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply`.
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
  - `feedback_critical_thinking_on_deviations`.
  - `feedback_strict_autonomy_no_pause_for_authorized_work`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.manifest.yaml` (M1a sibling — establishes the sub-amendment manifest shape under the rename series).
  - `docs/rebuild/plans/single-framework-restructure.manifest.yaml` (multi-component fence; universal-paths pattern).
  - `docs/rebuild/plans/a1-substrate-timestamp-format-normalization.manifest.yaml` (three-component fence with H19-frozen on hands-off-lifecycle).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1b is built using this CLI; rename to `loam amend` is M1g).
