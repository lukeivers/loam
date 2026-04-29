# OSS v0.1.0 publish — M1g — `pos-amend` → `loam amend` CLI rename + tools-tree namespace pivot — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Prior sub-amendments:**
- M1a — docs/prose-only brand rebrand (sealed `143d465`, 2026-04-29).
- M1b — env-vars + per-host config dir + migration helper (sealed `d97c8c1`, 2026-04-29).
- M1c — launchd labels + plist filename cascade + sibling migration helper (sealed `1e99d0b`, 2026-04-29).
- M1d — OTel `pos.*` → `loam.*` root rebrand (sealed `74ae5d3`, 2026-04-29).
- M1e — `loam.*` namespace pivot for 14 packaged components + cleanup (sealed `c806f57`, 2026-04-29; SHA-register backfill `820fd84`).
- M1f — Tier-2 graceful-degradation → dormancy thematic rename (sealed `390e1ca`, 2026-04-29; SHA-register backfill `af2e740`).

**Programme position:** Seventh and final sub-amendment of the M1.rename multi-amendment series. Closes the rename programme. Per series-master ladder note 5: "M1g is the dependency-final sub-amendment — the `pos-amend → loam amend` self-rename only lands once the rest of the rename has stabilised."

**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 #6 (the M1g target — `pos-amend` → `loam amend` subcommand under unified `loam` CLI).
- `.scratch/claude-output/loam-rename-migration-plan.md` §3.6 (research mechanics for CLI rename).
- `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` §2 ladder (M1g row), §5 series-wide hard constraints, §7 series-wide halt triggers.
- `docs/rebuild/plans/oss-v0-1-0-publish-rename-1e.md` §11 finding #4 (tools-tree residuals carried into M1g scope).
- `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (programme master plan; M1g row per series-master ladder).

---

## 1. Summary / TLDR

**M1g lands two coherent surfaces that close the rename programme:**

1. **Surface A — `pos-amend` CLI → unified `loam` top-level CLI with `amend` as the first subcommand.** Per `loam-rename-decisions.md` Tier-1 #6: a unified `loam` daily-driver CLI that acts as a brand concentrator for future subcommands (`loam scope new`, `loam status`, `loam plot create`, etc.). M1g introduces this top-level CLI by migrating `pos-amend`'s subcommand surface (`validate`, `apply`, `seal`, `template`, `new-plan`) under `loam amend <subcmd>`.

2. **Surface B — Tools-tree namespace pivot for the 4 residuals carried from M1e §11 finding #4** (`pos-publish-framework-only`, `orphan-plist-cleanup`, `upgrade-merge-resolver`, `heavy-b-migrate`). M1e was framework-component-scoped — these tools were not pivoted then. M1g closes them by moving their internal Python packages under the `loam.*` namespace (matching M1e's per-component pattern).

**Items in M1g:**

1. **Item 1 — Tool directory rename.** `framework/tools/pos-amend/` → `framework/tools/loam/` via `git mv` (preserving history). Per series-master M1g row: "framework/tools/pos-amend/ → framework/tools/loam/".
2. **Item 2 — Inner package rename.** `framework/tools/loam/src/pos_amend/` → `framework/tools/loam/src/loam_cli/` via `git mv`. Per series-master M1g row: "Package `pos_amend` → `loam_cli`". The `loam_cli` package is the unified-CLI dispatcher container (per Tier-1 #6 — "subcommand under a unified `loam` top-level CLI"); the existing pos-amend subcommand surface migrates one level deeper to `loam_cli/amend/`.
3. **Item 3 — Subcommand restructure.** Restructure the old flat `pos_amend/` package into `loam_cli/` + `loam_cli/amend/` shape:
   - `loam_cli/__init__.py` — top-level package with `__version__`.
   - `loam_cli/__main__.py` — `python -m loam_cli` entrypoint.
   - `loam_cli/cli.py` — top-level dispatcher; argparse subparsers route `loam amend` to the amend subcommand (and reserves namespace for future `loam scope`, `loam status`, etc.).
   - `loam_cli/amend/__init__.py` — amend-subcommand package.
   - `loam_cli/amend/cli.py` — amend subcommand parser (split out from the old `pos_amend/cli.py`); accepts `validate`, `apply`, `seal`, `template`, `new-plan` as deeper subcommands.
   - `loam_cli/amend/commands/{apply.py,seal.py,validate.py,template.py,new_plan.py}` — moved from `pos_amend/commands/` (filenames unchanged).
   - `loam_cli/amend/{manifest.py,baseline.py,paths.py,sidecar.py,seal_diff.py,narrative.py,dry_run.py,template_engine.py,tracker_registration.py,rename_detection.py}` — moved from `pos_amend/` (filenames unchanged).
4. **Item 4 — Console-script entry-point.** `framework/tools/loam/pyproject.toml` `[project.scripts]`: `pos-amend = "pos_amend.cli:main"` → `loam = "loam_cli.cli:main"`. Project `name = "pos-amend"` → `name = "loam-cli"`. Description rebrand.
5. **Item 5 — Internal pos-amend imports rebrand.** Every `from pos_amend.X import Y` in the migrated package's own modules → `from loam_cli.amend.X import Y`. Plus tests: every `from pos_amend.X import Y` in `framework/tools/loam/tests/` (post-rename) → `from loam_cli.amend.X import Y`.
6. **Item 6 — Cross-component consumer of pos-amend internal API: heavy-b-migrate.** `framework/tools/heavy-b-migrate/src/heavy_b_migrate/verify.py` lines 76–84 import `from pos_amend.manifest import ...` and `from pos_amend.tracker_registration import ...`. These rebrand to `from loam_cli.amend.manifest import ...` and `from loam_cli.amend.tracker_registration import ...`. heavy-b-migrate is the SOLE Python-import consumer of pos-amend's internal API (pre-build verification at plan-authoring time confirms; see §11 finding #1).
7. **Item 7 — HOL bash_guard pos-amend invocation rebrand.** `framework/hands-off-lifecycle/hooks/bash_guard.py` line 230 invokes `<workspace>/.venv/bin/pos-amend apply --dry-run <manifest>`. Post-rename: `<workspace>/.venv/bin/loam amend apply --dry-run <manifest>` (binary name + insert `amend` between binary and `apply`). Plus the function name `_pos_amend_dry_run` → `_loam_amend_dry_run`; failure-class string `"pos-amend-dry-run-failure"` → `"loam-amend-dry-run-failure"`. The accompanying test `framework/hands-off-lifecycle/tests/test_AC_BAG_4_pos_amend_dry_run.py` rebrands its monkeypatch targets + assertion strings + filename via `git mv` to `test_AC_BAG_4_loam_amend_dry_run.py`.
8. **Item 8 — HOL agent_guard pos-amend pattern rebrand.** `framework/hands-off-lifecycle/hooks/agent_guard.py` line 123 `re.compile(r"\bpos-amend\b")` → `re.compile(r"\bloam amend\b")`. The associated test `test_AC_AG_1_wrong_wd_dispatch.py` updates its prompt fixture to use `"Run loam amend apply --dry-run on the manifest."`.
9. **Item 9 — Component seal-test allowlist rebrand.** Every `framework/<comp>/tests/test_no_sealed_amendments.py` allowlist entry `"framework/tools/pos-amend/"` → `"framework/tools/loam/"`. Pre-build verification at plan-authoring time identifies 11 components with this entry: cost-governance, dormancy, memory-system, observability-aggregator, reversibility-primitive, self-correction, self-upgrade, telegram-interface, plus the docstring/comment mentions in objective-tracker, primary-persona, workspace-bootstrap, and observability-aggregator that reference `pos-amend apply` in narrative text.
10. **Item 10 — Doc/code prose pos-amend → loam amend rebrand.** All non-historical references to the `pos-amend` CLI binary in:
    - Live framework docstrings + comments (objective-tracker filter.py + runtime.py docstrings; workspace-bootstrap tracker_seed.py comment; self-upgrade _build_manifest.py comment; heavy-b-migrate src + tests; loam-mode README).
    - Live code-comment narrative inside seal-test allowlist comments.
    - **Out of scope — preserved historical record** per Idea 10 / dispatcher M1e ruling 3:
      - Past commit messages.
      - Past seal narratives at `framework/<comp>/seals/SEAL_COMMIT.*`.
      - All `docs/rebuild/plans/*.md` historical plan-docs (M1a..M1f sub-plans, amendment-NN-*.md plans, etc.).
      - `docs/rebuild/spec/pos-v2-rebuild-proposal.md`.
11. **Item 11 — Tools-tree namespace pivot for 4 residuals (Surface B).** Per M1e §11 finding #4 + dispatch §Objective:
    - `framework/tools/pos-publish-framework-only/src/pos_publish_framework_only/` → `src/loam/publish_framework_only/` via `git mv`. pyproject `name = "pos-publish-framework-only"` → `name = "loam-publish-framework-only"`. CLI binary name `pos-publish-framework-only` STAYS unchanged per dispatch conservatism (the script entry-point line updates only the module path: `pos-publish-framework-only = "pos_publish_framework_only.cli:main"` → `pos-publish-framework-only = "loam.publish_framework_only.cli:main"`). Internal imports rebrand. The 2 cross-references in `framework/workspace-bootstrap/tests/{conftest.py, test_AC_SFR_4_pos_sync_composition.py}` update from `from pos_publish_framework_only.synth import ...` → `from loam.publish_framework_only.synth import ...`.
    - `framework/tools/orphan-plist-cleanup/src/orphan_plist_cleanup/` → `src/loam/orphan_plist_cleanup/` via `git mv`. pyproject `name = "orphan-plist-cleanup"` → `name = "loam-orphan-plist-cleanup"`. CLI binary `orphan-plist-cleanup` STAYS. Script: `orphan-plist-cleanup = "orphan_plist_cleanup.cli:main"` → `orphan-plist-cleanup = "loam.orphan_plist_cleanup.cli:main"`. Internal imports rebrand.
    - `framework/tools/upgrade-merge-resolver/src/upgrade_merge_resolver/` → `src/loam/upgrade_merge_resolver/` via `git mv`. pyproject `name = "upgrade-merge-resolver"` → `name = "loam-upgrade-merge-resolver"`. Internal imports rebrand. (No CLI script — library only.)
    - `framework/tools/heavy-b-migrate/src/heavy_b_migrate/` → `src/loam/heavy_b_migrate/` via `git mv`. pyproject `name = "heavy-b-migrate"` → `name = "loam-heavy-b-migrate"`. CLI binary `heavy-b-migrate` STAYS. Script: `heavy-b-migrate = "heavy_b_migrate.cli:main"` → `heavy-b-migrate = "loam.heavy_b_migrate.cli:main"`. Internal imports rebrand (~22 callsites in src + tests). The 1 cross-reference in `framework/tools/loam-mode/src/loam_mode/session_start.py:293` (`from heavy_b_migrate.trigger import run_if_dev_intent`) → `from loam.heavy_b_migrate.trigger import run_if_dev_intent`.
12. **Item 12 — `loam-mode` tool internal consistency check.** Pre-build verification at plan-authoring time finds `framework/tools/loam-mode/` carries:
    - `__init__.py:1` docstring `"loam-mode — pos-v2 dev-mode auto-load partition selector + audit."` — `pos-v2` mention is historical project-name reference; per series convention (M1a closed prose-only `pos-v2 → loam`), this is a STRAGGLER from M1a. **In-scope for M1g** as cleanup (1-line edit).
    - `cli.py:72` argparse description `"pos-v2 dev-mode auto-load partition CLI."` — same kind. **In-scope for M1g** as cleanup (1-line edit).
    - `README.md:18` "Mirrors `tools/pos-amend/`'s install convention." — needs path-rebrand to `tools/loam/`. **In-scope per item 10.**
    - `tests/test_partition_manifest.py:7,66,71-72,78` — fixture path-strings `"tools/pos-amend/..."` used to test glob/exclude logic. These are FIXTURE strings (the partition manifest is text-based path-prefix matching). **In-scope for M1g**: fixture paths update to `"tools/loam/..."` to match the post-rename reality.
    - `tests/test_F_S_seal_diff.py:20` — narrative comment `"Mirrors the dev-discipline pattern from tools/pos-amend/tests/"`. **In-scope** (1-line comment edit).
    - `tests/test_selector_partition.py:100` — fixture path `"tools/pos-amend/cli.py"` → `"tools/loam/cli.py"`. **In-scope.**

**Hard cutover** per series-master §1 D-RNM.3. No `pos-amend` shim binary; no transitional dual-binary registration; no compat re-export from `pos_amend.*`. Pre-public release; zero existing external consumers.

**Sealed-component fence (post-build):** **HOL anchor + 1 Python-import consumer (heavy-b-migrate, in tools-tree) + 11 cross-component allowlist edits (one-line per component test).**

The dispatch's recommended fence shape is "tools-tree-only — pos-amend renamed package + the 4 tools-tree residuals; possibly HOL anchor for the cross-cutting refs". M1g's empirical surface confirms HOL anchor IS needed (bash_guard.py + agent_guard.py + 5 HOL test files). Plus 11 component-allowlist single-line edits live OUTSIDE the tools-tree but are universal-style (allowlist-content updates that follow from the directory rename).

**Self-rename mechanism choice:** The dispatch authorises three options:
- **(a)** Rename pos-amend BEFORE running apply. Run `loam amend apply` and `loam amend seal --plan-doc` for M1g's own bookkeeping.
- **(b)** Rename pos-amend AFTER running apply. Final apply+seal under old name; subsequent amendments use new name.
- **(c)** Transitional shim that registers BOTH names during M1g only.

**Plan recommendation: (a).** Rename atomically, run `pip install -e ./framework/tools/loam`, run `loam amend apply <manifest>` and `loam amend seal --plan-doc <plan>` under the NEW name. The seal commit narrative therefore reflects the post-rename reality.

**Fallback: (b).** If `pip install -e` fails for any reason mid-rename, fall back to (b) — re-install pos-amend under its old name (the editable install from before this amendment is recoverable via `git stash` of the pyproject + a re-`pip install -e`), run `pos-amend apply` + `pos-amend seal --plan-doc`, then complete the rename, re-`pip install -e` under the new name, and verify `loam amend --help` succeeds before the seal commit.

**Empirical surface inventory (plan-authoring time):**

| Surface | Count | Where |
|---------|-------|-------|
| `pos-amend` binary references in framework/ live (excluding pos-amend tool tree itself) | 88 | HOL hooks (~10) + HOL tests (~12) + 11 component seal-test allowlists + ~10 src docstrings/comments + ~22 in heavy-b-migrate (src + tests + README) + 5 in loam-mode |
| `pos-amend` references in framework/tools/pos-amend/ tree | 274 | Internal — moves under the rename |
| `from pos_amend.X import Y` in heavy-b-migrate | 2 | `framework/tools/heavy-b-migrate/src/heavy_b_migrate/verify.py` lines 76, 81 |
| `from pos_publish_framework_only.X import Y` outside its own tree | 2 | `framework/workspace-bootstrap/tests/{conftest.py, test_AC_SFR_4_pos_sync_composition.py}` |
| `from heavy_b_migrate.X import Y` outside its own tree | 1 | `framework/tools/loam-mode/src/loam_mode/session_start.py:293` |
| `from orphan_plist_cleanup.X import Y` outside its own tree | 0 | None (verified at plan-authoring) |
| `from upgrade_merge_resolver.X import Y` outside its own tree | 0 | None (verified at plan-authoring) |
| Internal `from pos_amend.X import Y` in pos-amend's own tree | ~30 | All cli.py + commands/*.py + tests |
| Internal `from heavy_b_migrate.X import Y` in heavy-b-migrate's own tree | ~30 | Across src + tests |
| Internal `from pos_publish_framework_only.X import Y` in own tree | ~5 | cli.py + tests |
| Internal `from orphan_plist_cleanup.X import Y` in own tree | ~5 | cli.py + tests |
| Internal `from upgrade_merge_resolver.X import Y` in own tree | ~3 | __init__.py + (no tests at plan time) |
| Component seal-test `"framework/tools/pos-amend/"` allowlist entries | 11 | cost-governance, dormancy, memory-system, observability-aggregator, reversibility-primitive, self-correction, self-upgrade, telegram-interface (8 hard entries) + comment-only mentions in objective-tracker, primary-persona, workspace-bootstrap (3 narrative comments — preserved verbatim or stripped per item 10) |

**Total estimated diff size:** ~88 callsite touches outside pos-amend tree (binary + import refs + allowlists + comments) + ~274 pos-amend-internal touches (most of which are git mv'd directory + handful of path rewrites in the package restructure) + 4 residual-tools `git mv` ops + ~75 internal-import rebrands across the 4 residual tools + 5 cross-tree consumer rebrands + 4 pyproject.toml restructures (1 for the renamed pos-amend tool + 4 for residual tools) + the new top-level `loam_cli/cli.py` dispatcher (~50 LOC) + the existing pos-amend cli.py becoming `loam_cli/amend/cli.py`.

**What does NOT land in M1g** (deferred per series-master §2 + plan §6):

- **`com.pos.orchestrator` launchd-label stragglers** — DEFERRED per M1e §11 finding #1 + M1f deferred-list. Recommended landing path: small follow-on M1c-corrective amendment OR M9-scrub.
- **`pos-bootstrap` / `pos-new-workspace` console-scripts in workspace-bootstrap/pyproject.toml** — these are TWO additional `pos-` prefixed CLI binaries that are OUT OF M1g's named scope per dispatch (the dispatch names pos-amend and the 4 residual tools; pos-bootstrap/pos-new-workspace are NOT named). Per ODD §2.5 conservatism, leave verbatim. **FIDRAFT-tracked** (see §11 finding #2): "`pos-bootstrap` / `pos-new-workspace` console-scripts in workspace-bootstrap/pyproject.toml — small follow-on amendment, ≈10 callsites for pyproject + invocation surfaces; out of M1g named scope per dispatch's tools-tree-residuals enumeration."
- **`Degradation*` Python class symbol renames** — M1f-deferred FIDRAFT-tracked.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** historical-narrative-heavy live docs — series-wide deferred.
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` — preserved.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` (other than this plan-doc + manifest YAML) — preserved.
- **Historical component-record docs** at `docs/rebuild/components/*/{research,research-plan,brief,component}.md` — preserved.
- **`docs/rebuild/spec/*.md` (including pos-v2-rebuild-proposal.md)** — preserved per Idea 10.
- **`docs/rebuild/plans/two-modes-and-multi-workspace/*.md`** — preserved.
- **Frozen self-upgrade release manifest `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml`** — preserved.
- **Repo directory rename** `ivers-corp-pos-v2` → `loam` — M9-deferred.
- **Path strings** `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred.

**Estimate:** 40–80 min AI-time per the duration rubric (per dispatch's prediction; multi-surface STRUCTURAL rename — narrower than M1e's 14-component pivot but with the unique self-rename mechanic + 4 residual tools). Pricing: rubric anchor M1f's 30–60 min midpoint 45 min; M1g adds the self-rename mechanism (~10 min overhead) + 4 residual-tool pivots (~10 min each, parallelisable bulk substitution) → 40–80 min midpoint 60 min. **Halt-trigger §10 fires at 120 min** (1.5× upper bound).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — M1g closes the CLI rename slice (the user-visible daily-driver brand surface). With M1g sealed, only M9-scrub residuals remain.
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — M1g stabilises the `loam amend` CLI surface that the next amendment reads in invocation. Dev-discipline tooling now reads under the unified `loam` CLI.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable single-CLI identity post-M1g. The persona's user-prose vocabulary loses `pos-amend` and gains the one word `loam` (with `amend` as a subcommand). Translation-burden between user intent ("apply this amendment manifest") and the CLI surface narrows.
- **AC.PO.2** (VALUE_PROPOSITION harness test) — `loam_cli` is a renamed harness primitive. The unified CLI is brand-concentrator infrastructure that future subcommands (`loam scope new`, `loam status`, `loam plot create`, etc.) compose against. The harness toolkit picks up the cleaner unified-CLI surface.

**Sealed-component fence (preliminary — see §4 ACs + §11 surface inventory):** **Tools-tree-only fence** for the structural rename + tools-tree pivot, **plus HOL anchor** for the cross-cutting bash_guard + agent_guard + test refs, **plus 11 cross-component allowlist single-line edits** under universal admissions.

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose/pyproject/directory-mv changed in M1g's diff traces back to AC.RNM-1g.1 .. AC.RNM-1g.S below. Mechanical structural substitution (tool dir + inner package rename + subcommand restructure + console-script entry-point rebrand + import-callsite rewrite + binary-invocation rewrite + tools-tree namespace pivot for 4 residuals); no behaviour changes; no defensive-`if` admissions beyond named §11 findings; no cross-mode-debt cascade beyond the named surfaces.

---

## 3. Three-lens analysis (abbreviated; series-master §4 covers cross-cutting)

- **Lens 1.** Pass. The unified `loam` CLI is exactly the brand-concentrator shape the migration plan §3.6 anticipated. Future Claude-Code-shaped extensions (slash commands, MCP servers, plugins) now compose against the single `loam` CLI binary — the daily surface vocabulary tightens. The `loam amend` subcommand surface preserves every existing pos-amend behaviour (validate, apply, seal, template, new-plan) — no Claude-side composition breaks.
- **Lens 2.** Primary-persona pass — single-CLI vocabulary loss of "pos-amend" / gain of "loam amend" tightens the user's surface. Harness pass — the unified `loam` CLI becomes the canonical entry-point for future subcommands (the harness's daily-driver shell-surface).
- **Lens 3.** Mechanical structural-substitution work plus a small dispatcher-authoring delta (~50 LOC for `loam_cli/cli.py` top-level argparse). Outcome-shaped ACs (post-rename CLI invocation, post-pip-install editable installs, post-rename grep returning 0); method-shape (which exact regex, which exact rename order) is the builder's call inside the AC outcome bound.

---

## 4. Acceptance criteria — AC.RNM-1g.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.RNM-1g.1 — Tool directory + inner package rename + subcommand restructure

The on-disk shape post-M1g is:

```
framework/tools/loam/
├── pyproject.toml       # name = "loam-cli"; script loam = "loam_cli.cli:main"
├── README.md
├── src/
│   └── loam_cli/
│       ├── __init__.py  # __version__
│       ├── __main__.py  # python -m loam_cli
│       ├── cli.py       # top-level dispatcher; argparse subparsers; routes `loam amend` to amend subcommand
│       └── amend/
│           ├── __init__.py
│           ├── cli.py             # amend subcommand parser (validate/apply/seal/template/new-plan)
│           ├── manifest.py
│           ├── baseline.py
│           ├── paths.py
│           ├── sidecar.py
│           ├── seal_diff.py
│           ├── narrative.py
│           ├── dry_run.py
│           ├── template_engine.py
│           ├── tracker_registration.py
│           ├── rename_detection.py
│           └── commands/
│               ├── __init__.py
│               ├── apply.py
│               ├── seal.py
│               ├── validate.py
│               ├── template.py
│               └── new_plan.py
└── tests/  # all tests rebrand from `from pos_amend.X` to `from loam_cli.amend.X`
```

`framework/tools/pos-amend/` does NOT exist post-M1g. `framework/tools/loam/src/pos_amend/` does NOT exist post-M1g.

`git mv` preserves history per M1e D-build.M1e.2 / M1f D-build.M1f.1 precedent. Rename-detection threshold preserves blame at 95%+ similarity for files unchanged in content. Files restructured into `amend/` subdir keep blame via the `git mv` chain.

**Outcome:**
- `ls framework/tools/loam/src/loam_cli/cli.py` exists.
- `ls framework/tools/loam/src/loam_cli/amend/cli.py` exists.
- `ls framework/tools/pos-amend/` returns "No such file or directory".
- `python -c "from loam_cli.amend.manifest import Manifest"` (in the editable-install-refreshed venv) succeeds.
- `python -c "from pos_amend.manifest import Manifest"` raises `ImportError`.
- `git log --follow framework/tools/loam/src/loam_cli/amend/manifest.py` returns the file's full pre-M1g history (tracked under `pos_amend/manifest.py`).

### AC.RNM-1g.2 — Unified `loam` top-level CLI binary

A new console-script entry-point `loam` is registered. The `loam` binary dispatches subcommands via argparse:

- `loam amend [validate|apply|seal|template|new-plan] ...` — preserves pos-amend's full surface.
- `loam --version` prints the loam-cli version.
- `loam --help` lists `amend` (and reserves namespace for future subcommands per Tier-1 #6).

`loam_cli/cli.py` (the top-level dispatcher) builds an argparse parser with one subparser group; the only registered subcommand at M1g time is `amend`. The amend subparser is registered via a delegation to `loam_cli.amend.cli._build_amend_parser()` (the existing pos-amend cli.py's parser-build moved into `amend/cli.py` with the prog string changed from `"pos-amend"` to `"loam amend"`).

**Outcome:**
- `which loam` returns `<workspace>/.venv/bin/loam` (post-`pip install -e ./framework/tools/loam`).
- `loam --version` prints `loam-cli 0.1.0` (or matching pyproject version).
- `loam amend --help` lists `validate / apply / seal / template / new-plan` as subcommands.
- `loam amend validate framework/dormancy/seals/SEAL_COMMIT` (or any sample manifest) behaves identically to pre-rename `pos-amend validate <same path>` would have (functional equivalence is the test).
- `pos-amend --help` raises `command not found` (or returns 127) — the old binary entry-point is unregistered post-rename.

### AC.RNM-1g.3 — Internal pos-amend imports rebrand

Every `from pos_amend.X import Y` callsite (post-restructure: every internal module references its now-deeper-nested counterpart):

- Inside `loam_cli/amend/*.py` — internal cross-module imports rebase from `from pos_amend.X import Y` to `from loam_cli.amend.X import Y` (~30 callsites).
- Inside `loam_cli/cli.py` — the new top-level dispatcher imports `from loam_cli.amend import cli as amend_cli` (or the parser-build helper); zero `pos_amend` references.
- Inside `framework/tools/loam/tests/*.py` — every `from pos_amend.X import Y` rebrands to `from loam_cli.amend.X import Y`. Conftest fixtures referencing `"pos-amend test"` git-config user.name update to `"loam-cli test"`.
- Inside `framework/tools/heavy-b-migrate/src/heavy_b_migrate/verify.py` lines 76–84 — the late imports from `pos_amend.manifest` + `pos_amend.tracker_registration` rebrand to `loam_cli.amend.manifest` + `loam_cli.amend.tracker_registration`. Per item 6.

**Outcome (positive):** `grep -rE 'from loam_cli\.amend([. ]|$)|import loam_cli([. ]|$)' framework/ --include="*.py"` returns matches (~30 internal + 2 cross-tree from heavy-b-migrate).

**Outcome (negative):** `grep -rE 'from pos_amend([. ]|$)|import pos_amend([. ]|$)' framework/ --include="*.py"` returns 0 matches in the live (non-historical) surface.

### AC.RNM-1g.4 — HOL bash_guard pos-amend invocation rebrand

`framework/hands-off-lifecycle/hooks/bash_guard.py` post-M1g:

- Function `_pos_amend_dry_run(...)` renamed to `_loam_amend_dry_run(...)`.
- Inside the function: `pos_amend = workspace_root / ".venv" / "bin" / "pos-amend"` → `loam = workspace_root / ".venv" / "bin" / "loam"`. Variable name `pos_amend` → `loam`. Subprocess args `[str(pos_amend), "apply", "--dry-run", str(manifest)]` → `[str(loam), "amend", "apply", "--dry-run", str(manifest)]`.
- Failure-class string `"pos-amend-dry-run-failure"` → `"loam-amend-dry-run-failure"` everywhere it appears (3 occurrences: function def docstring + return-tuple + the `Decision.failure_class` literal).
- Reason-builder helper `_reason_pos_amend_dry_run(...)` → `_reason_loam_amend_dry_run(...)`.
- All comments + docstrings mentioning `pos-amend` rebrand to `loam amend`.

The accompanying test file `framework/hands-off-lifecycle/tests/test_AC_BAG_4_pos_amend_dry_run.py`:
- Filename: `git mv` to `test_AC_BAG_4_loam_amend_dry_run.py`.
- Inside: monkeypatch targets `_pos_amend_dry_run` → `_loam_amend_dry_run`. Assertion strings `"pos-amend"` → `"loam amend"`. Failure-class assertion `"pos-amend-dry-run-failure"` → `"loam-amend-dry-run-failure"`.

**Outcome:**
- `grep -rE 'pos-amend|pos_amend' framework/hands-off-lifecycle/ --include="*.py"` returns 0 matches in the live (non-historical) surface.
- `pytest framework/hands-off-lifecycle/tests/test_AC_BAG_4_loam_amend_dry_run.py` PASSES.
- The hook's `failure_class` enum-like surface in the type-hint (`Literal["AC.AG.1", "loam-amend-dry-run-failure", "wrong-tree-write", None]`) reflects the new string.

### AC.RNM-1g.5 — HOL agent_guard pos-amend pattern rebrand

`framework/hands-off-lifecycle/hooks/agent_guard.py` post-M1g:

- `re.compile(r"\bpos-amend\b")` → `re.compile(r"\bloam amend\b")` in the `_LOAM_SURFACE_PATTERNS` tuple.
- Comments mentioning `pos-amend` rebrand to `loam amend`.

The accompanying test `test_AC_AG_1_wrong_wd_dispatch.py`:
- Test prompt fixture `"Run pos-amend apply --dry-run on the manifest."` → `"Run loam amend apply --dry-run on the manifest."`.
- Test name `test_AC_AG_1_pos_amend_mention_wrong_cwd_denies` → `test_AC_AG_1_loam_amend_mention_wrong_cwd_denies`.
- Module docstring mentions of `pos-amend` rebrand.

**Outcome:**
- `pytest framework/hands-off-lifecycle/tests/test_AC_AG_1_wrong_wd_dispatch.py` PASSES.
- `grep -E "pos-amend" framework/hands-off-lifecycle/hooks/agent_guard.py` returns 0.

### AC.RNM-1g.6 — Component seal-test allowlist rebrand

Every `framework/<comp>/tests/test_no_sealed_amendments.py` allowlist that contains `"framework/tools/pos-amend/"` rebases to `"framework/tools/loam/"`. Pre-build verification at plan-authoring time identifies 8 components with hard allowlist entries:

- `framework/cost-governance/tests/test_no_sealed_amendments.py:153`
- `framework/dormancy/tests/test_no_sealed_amendments.py:165`
- `framework/memory-system/tests/test_no_sealed_amendments.py:203`
- `framework/observability-aggregator/tests/test_no_sealed_amendments.py:159`
- `framework/reversibility-primitive/tests/test_no_sealed_amendments.py:86`
- `framework/self-correction/tests/test_no_sealed_amendments.py:136`
- `framework/self-upgrade/tests/test_no_sealed_amendments.py:136`
- `framework/telegram-interface/tests/test_no_sealed_amendments.py:135`

Plus narrative comments referring to `pos-amend apply`/`pos-amend seal` in 3 tests where the comment is preserved historical-record but the BASELINE-shape line is preserved verbatim:

- `framework/objective-tracker/tests/test_no_sealed_amendments.py:132` — "by ``pos-amend apply``; kept stable across amendments." → "by ``loam amend apply``; kept stable across amendments."
- `framework/primary-persona/tests/test_no_sealed_amendments.py:38, 40, 53, 151` — narrative comments about how the BASELINE was advanced.
- `framework/observability-aggregator/tests/test_no_sealed_amendments.py:74` — `# shape check: pos-amend apply advances the literal` → `# shape check: loam amend apply advances the literal`.
- `framework/self-correction/tests/test_no_sealed_amendments.py:69` — same shape.
- `framework/memory-system/tests/test_no_sealed_amendments.py:205,210` — Amendment #22 (pos-amend CLI + ...) — these comments are HISTORICAL-RECORD references to the M1c/M1e amendment numbering (the `pos-amend` name was correct at the time of #22). **Decision: preserve verbatim** as historical record (the seal narrative for #22 mentions `pos-amend`; this is consistent with §6 historical-preservation policy). Per §10 D-build.M1g.4: comment-line allowlist narrative that describes pre-M1g amendment events stays verbatim; only the live-fence allowlist entry rebrands.

**Outcome:**
- `grep -nE "framework/tools/pos-amend/" framework/*/tests/test_no_sealed_amendments.py` returns 0 matches.
- `grep -nE "framework/tools/loam/" framework/*/tests/test_no_sealed_amendments.py` returns 8 matches (the 8 hard entries).
- `pytest framework/<comp>/tests/test_no_sealed_amendments.py` PASSES for every component (touched-file rerun under the rename).

### AC.RNM-1g.7 — Doc/code prose pos-amend → loam amend rebrand (live surfaces only)

Every non-historical reference to `pos-amend` in framework/ live source + docs rebrands to `loam amend`:

- `framework/objective-tracker/src/loam/objective_tracker/filter.py:6` — module docstring "pos-amend's `project` subcommand, primary-persona's tracker-context" → "loam amend's `project` subcommand, primary-persona's tracker-context".
- `framework/objective-tracker/src/loam/objective_tracker/runtime.py:608` — function docstring "(pos-amend's `project` subcommand, primary-" → "(loam amend's `project` subcommand, primary-".
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/tracker_seed.py:306` — comment "(#40 contributor, pos-amend project) can" → "(#40 contributor, loam amend project) can".
- `framework/self-upgrade/manifests/_build_manifest.py:21` — comment "are workspace-side; merge-resolver-module + pos-amend live there)." → "are workspace-side; merge-resolver-module + loam amend live there)."
- `framework/tools/heavy-b-migrate/src/heavy_b_migrate/__init__.py:7,12` — module docstring "pos-amend manifest" / "pos-amend tracker-" → "loam amend manifest" / "loam amend tracker-".
- `framework/tools/heavy-b-migrate/src/heavy_b_migrate/cli.py:94` — narrative description string "composes against #38/#39/#40 + pos-amend tracker integration." → "composes against #38/#39/#40 + loam amend tracker integration."
- `framework/tools/heavy-b-migrate/src/heavy_b_migrate/amendment_acs.py:16` — comment "``pos-amend seal`` path which DOES populate source_commit" → "``loam amend seal`` path which DOES populate source_commit".
- `framework/tools/heavy-b-migrate/src/heavy_b_migrate/verify.py:4-20,56,62,69-76` — multiple docstring + comment references to `pos-amend apply`/`pos-amend seal`/`pos-amend's public register_objectives` — rebrand prose to `loam amend ...`. (NOTE: the `pos_amend_repo_root` parameter name on line 56 is a Python identifier — rebrand to `loam_cli_repo_root` or keep as `pos_amend_repo_root` per builder's call. Recommendation per §10 D-build.M1g.5: rebrand to `loam_amend_repo_root` for consistency with the rename — single-symbol rename, easy to grep and verify.)
- `framework/tools/heavy-b-migrate/tests/test_ac_d_mig_4_continuous_registration.py` — module docstring + test names referencing `pos-amend` rebrand to `loam amend`.
- `framework/tools/heavy-b-migrate/README.md:67` — bullet "**#16** — `pos-amend` tracker integration" → "**#16** — `loam amend` tracker integration".
- `framework/tools/loam-mode/README.md:18` — "Mirrors `tools/pos-amend/`'s install convention." → "Mirrors `tools/loam/`'s install convention."
- `framework/tools/loam-mode/tests/test_partition_manifest.py:7,66,71-72,78` — fixture path-strings and narrative comments rebrand `tools/pos-amend/` → `tools/loam/`.
- `framework/tools/loam-mode/tests/test_F_S_seal_diff.py:20` — narrative comment rebrand.
- `framework/tools/loam-mode/tests/test_selector_partition.py:100` — fixture path rebrand.
- `framework/tools/loam-mode/src/loam_mode/__init__.py:1` — docstring "loam-mode — pos-v2 dev-mode auto-load partition selector + audit." → "loam-mode — loam dev-mode auto-load partition selector + audit." (M1a straggler).
- `framework/tools/loam-mode/src/loam_mode/cli.py:72` — argparse description "pos-v2 dev-mode auto-load partition CLI." → "loam dev-mode auto-load partition CLI." (M1a straggler).

**Out of scope (preserved historical record per §6):**
- `docs/rebuild/plans/*.md` historical plan-docs (M1a..M1f sub-plans, amendment-NN-*.md plans, etc.) — preserved per Idea 10 / dispatcher M1e ruling 3.
- `framework/<comp>/seals/SEAL_COMMIT.*` — preserved verbatim.
- Past commit messages — preserved.
- `docs/rebuild/spec/pos-v2-rebuild-proposal.md` — preserved per Idea 10.

**Outcome:** `grep -rE "pos-amend" framework/ --include="*.py" --include="*.md" --include="*.toml"` returns 0 matches in the live (non-historical) surface. (Allowlist comments naming pre-M1g amendment events are scoped per §10 D-build.M1g.4.)

### AC.RNM-1g.8 — Tools-tree namespace pivot for 4 residuals

Per M1e §11 finding #4, the 4 residual tools' internal Python packages pivot under the `loam.*` namespace (matching M1e's per-component pattern):

- `framework/tools/pos-publish-framework-only/src/pos_publish_framework_only/` → `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/` via `git mv`. pyproject `name = "pos-publish-framework-only"` → `name = "loam-publish-framework-only"`. Description rebrand. CLI script: `pos-publish-framework-only = "pos_publish_framework_only.cli:main"` → `pos-publish-framework-only = "loam.publish_framework_only.cli:main"`. Internal `from pos_publish_framework_only.X import Y` → `from loam.publish_framework_only.X import Y`. Cross-tree imports in `framework/workspace-bootstrap/tests/{conftest.py, test_AC_SFR_4_pos_sync_composition.py}` rebrand.
- `framework/tools/orphan-plist-cleanup/src/orphan_plist_cleanup/` → `framework/tools/orphan-plist-cleanup/src/loam/orphan_plist_cleanup/` via `git mv`. pyproject `name = "orphan-plist-cleanup"` → `name = "loam-orphan-plist-cleanup"`. Script: `orphan-plist-cleanup = "orphan_plist_cleanup.cli:main"` → `orphan-plist-cleanup = "loam.orphan_plist_cleanup.cli:main"`. Internal imports rebrand.
- `framework/tools/upgrade-merge-resolver/src/upgrade_merge_resolver/` → `framework/tools/upgrade-merge-resolver/src/loam/upgrade_merge_resolver/` via `git mv`. pyproject `name = "upgrade-merge-resolver"` → `name = "loam-upgrade-merge-resolver"`. (No CLI script.) Internal imports rebrand.
- `framework/tools/heavy-b-migrate/src/heavy_b_migrate/` → `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/` via `git mv`. pyproject `name = "heavy-b-migrate"` → `name = "loam-heavy-b-migrate"`. Script: `heavy-b-migrate = "heavy_b_migrate.cli:main"` → `heavy-b-migrate = "loam.heavy_b_migrate.cli:main"`. Internal imports rebrand (~22 callsites in src + tests). Cross-tree consumer `framework/tools/loam-mode/src/loam_mode/session_start.py:293` rebrands `from heavy_b_migrate.trigger` → `from loam.heavy_b_migrate.trigger`.

**Tool directory names (`framework/tools/<dir>/`) STAY unchanged** per dispatch conservatism. CLI binary names (`pos-publish-framework-only`, `orphan-plist-cleanup`, `heavy-b-migrate`) STAY unchanged per dispatch conservatism (they're tool binaries, not framework component names; renaming them is FIDRAFT-tracked as a separate amendment).

**Outcome:**
- `python -c "from loam.publish_framework_only.synth import generate_framework_only_branch"` (or whatever the live surface is) succeeds.
- `python -c "from loam.heavy_b_migrate.trigger import run_if_dev_intent"` succeeds.
- `python -c "from loam.orphan_plist_cleanup.detector import ..."` succeeds.
- `python -c "from loam.upgrade_merge_resolver import ..."` succeeds.
- `python -c "from pos_publish_framework_only import *"` raises `ImportError`.
- `python -c "from heavy_b_migrate import *"` raises `ImportError`.
- `python -c "from orphan_plist_cleanup import *"` raises `ImportError`.
- `python -c "from upgrade_merge_resolver import *"` raises `ImportError`.
- `pytest framework/tools/heavy-b-migrate/tests/` passes (post-editable-install refresh).
- `pytest framework/tools/orphan-plist-cleanup/tests/` passes.
- `pytest framework/tools/pos-publish-framework-only/tests/` passes.
- `pytest framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py` passes (cross-tree consumer of pos_publish_framework_only).
- `pytest framework/tools/loam-mode/tests/` passes (cross-tree consumer of heavy_b_migrate).

### AC.RNM-1g.9 — Editable installs refreshed

After the directory + package rename + namespace pivot, the editable installs for each renamed tool are refreshed:

- `pip install -e ./framework/tools/loam` — succeeds; registers the `loam` console script.
- `pip install -e ./framework/tools/pos-publish-framework-only` — succeeds; registers `pos-publish-framework-only` console script with new module path.
- `pip install -e ./framework/tools/orphan-plist-cleanup` — succeeds; registers `orphan-plist-cleanup` console script with new module path.
- `pip install -e ./framework/tools/upgrade-merge-resolver` — succeeds (library-only).
- `pip install -e ./framework/tools/heavy-b-migrate` — succeeds; registers `heavy-b-migrate` console script with new module path.

Order: `loam` first (so `loam amend` is available for the apply step), then the 4 residual tools in any order (no inter-tool deps).

**Outcome:**
- `which loam` returns `<workspace>/.venv/bin/loam`.
- `loam --help` returns subcommand help listing `amend`.
- `which pos-amend` returns 1 (binary unregistered).
- `pip install -e ./framework/tools/loam` exit code 0.
- `pip install -e ./framework/tools/{pos-publish-framework-only,orphan-plist-cleanup,upgrade-merge-resolver,heavy-b-migrate}` exit code 0 (each).

### AC.RNM-1g.S — Sealed-component fence: HOL anchor + tools-tree + universal-style allowlist edits

Per the dispatch's recommended fence shape: tools-tree-only for the structural rename + 4 residual-tool pivots, plus HOL anchor for cross-cutting bash_guard + agent_guard refs, plus 11 cross-component allowlist single-line edits as universal-style admissions.

The amendment manifest YAML lists:

- 1 sealed component for the seal-test anchor: hands-off-lifecycle (HOL — narrative anchor + bash_guard + agent_guard owner).
- 11 cross-cutting allowlist-rebrand admissions for the 8 hard `"framework/tools/pos-amend/"` allowlist entries (cost-governance, dormancy, memory-system, observability-aggregator, reversibility-primitive, self-correction, self-upgrade, telegram-interface) plus 3 narrative-comment-only edits (objective-tracker, primary-persona, workspace-bootstrap) — these are universal-style single-line edits that follow from the rename.
- Tools-tree fence: `framework/tools/pos-amend/`, `framework/tools/loam/`, `framework/tools/pos-publish-framework-only/`, `framework/tools/orphan-plist-cleanup/`, `framework/tools/upgrade-merge-resolver/`, `framework/tools/heavy-b-migrate/`, `framework/tools/loam-mode/`.

The `seal_diff` `allowed_prefixes` admit:
- `framework/hands-off-lifecycle/` (HOL anchor).
- `framework/tools/` (the entire tools subtree given M1g touches 7 tools).
- `framework/<comp>/tests/test_no_sealed_amendments.py` per-component allowlist edit (admitted via universal_paths.files list).
- The 5 live-source narrative-prose surfaces named in AC.RNM-1g.7 (objective-tracker filter.py + runtime.py, workspace-bootstrap tracker_seed.py, self-upgrade _build_manifest.py, observability-aggregator schema-comment if any).
- Universal admissions per AC.RNM-1g.S (plan-doc + manifest YAML).

**Per-component touched-test scope:** narrow to touched files. Per `feedback_amendment_dispatch_speedups`, M1g skips pre-seal full-suite rerun. Each sealed component's `test_no_sealed_amendments.py` runs as part of `loam amend apply` verification (post-rename). The seal-diff fence test for AC.RNM-1g.S is the primary check (verifies the fence isn't reaching beyond tools-tree + HOL + universal admissions).

**Outcome:**
- `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention.
- HOL sidecar advances; HOL `test_cross_cutting.py` PASSES.
- `pytest framework/<comp>/tests/test_no_sealed_amendments.py` PASSES for every touched component (narrow rerun under the rename — the seal-diff window for each consumes the post-rename `framework/tools/loam/` allowlist entry).

### AC.RNM-1g.10 — No work outside the named surfaces (negative AC)

The amendment's git-diff includes ZERO touches outside:

- `framework/tools/pos-amend/...` (admits the pre-rename source paths in the rename diff window).
- `framework/tools/loam/...` (the post-rename target).
- `framework/tools/pos-publish-framework-only/...` (namespace pivot in place; CLI binary name + tool dir name unchanged).
- `framework/tools/orphan-plist-cleanup/...` (namespace pivot in place).
- `framework/tools/upgrade-merge-resolver/...` (namespace pivot in place).
- `framework/tools/heavy-b-migrate/...` (namespace pivot in place).
- `framework/tools/loam-mode/...` (M1a-straggler internal cleanup + cross-tree consumer rebrand).
- `framework/hands-off-lifecycle/{hooks/{bash_guard.py, agent_guard.py}, tests/{test_AC_BAG_4_*.py, test_AC_AG_1_wrong_wd_dispatch.py, test_cross_cutting.py if rebrand-impacted}}`.
- `framework/<comp>/tests/test_no_sealed_amendments.py` (per-component allowlist single-line edits — 11 components).
- `framework/objective-tracker/src/loam/objective_tracker/{filter.py, runtime.py}` (live docstring rebrands per AC.RNM-1g.7).
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/tracker_seed.py` (live comment rebrand per AC.RNM-1g.7).
- `framework/workspace-bootstrap/tests/{conftest.py, test_AC_SFR_4_pos_sync_composition.py}` (cross-tree imports of pos_publish_framework_only — namespace-pivot consumer rebrand per AC.RNM-1g.8).
- `framework/self-upgrade/manifests/_build_manifest.py` (live comment rebrand).
- The plan-doc + manifest YAML under `docs/rebuild/plans/`.

**Permitted ZERO surfaces (no edits expected):**

- No env-var or per-host-config-dir changes — M1b closed those.
- No launchd-label changes — M1c closed those (item 8 deferred).
- No first-segment-`pos.` OTel root changes — M1d closed those.
- No `pos.bootstrap.contributions` entry-point group references — M1e closed those.
- No `loam.degradation.*` OTel cascade — M1f closed those.
- No `graceful-degradation` references in live surfaces — M1f closed those.
- No `pos-bootstrap` / `pos-new-workspace` console-script edits in workspace-bootstrap/pyproject.toml — out of M1g scope per §6 (FIDRAFT-tracked).
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites — M9.
- No `framework/<comp>/seals/SEAL_COMMIT.*` historical-narrative edits.
- No `docs/rebuild/plans/*.md` historical plan-doc edits beyond this plan-doc + manifest YAML.
- No `docs/rebuild/spec/*.md` content or filename edits.
- No HC#4 byte-content sample SHA changes (plan-time pre-verification — see §11 finding #3).

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Nine outcome-named behaviours (tool dir + package rename + subcommand restructure, unified `loam` CLI dispatcher, internal pos-amend imports rebrand, HOL bash_guard, HOL agent_guard, component seal-test allowlist, doc/code prose, tools-tree namespace pivot, editable installs refreshed) → nine positive ACs (AC.RNM-1g.1 .. AC.RNM-1g.9). Plus the seal-fence AC (AC.RNM-1g.S) and the negative scope AC (AC.RNM-1g.10). Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §8.6.

---

## 5. Hard constraints (M1g-specific; series-wide constraints from master §5 inherit)

- **Single-amendment self-rename mechanism per §10 D-build.M1g.1.** Mechanism (a) — rename pos-amend → loam amend BEFORE running apply; run `loam amend apply` + `loam amend seal --plan-doc` for M1g's own bookkeeping. Fallback (b) if `pip install -e` fails mid-rename.
- **Hard cutover.** Per series-master §1 D-RNM.3: no `pos-amend` shim binary; no transitional dual-binary registration; no `from pos_amend` re-export module. Pre-public release; zero existing external consumers.
- **Editable install refresh.** After the rename + namespace pivot, run editable installs in this order: (1) `pip install -e ./framework/tools/loam` (so `loam amend` is available for the apply step); (2) `pip install -e ./framework/tools/{pos-publish-framework-only,orphan-plist-cleanup,upgrade-merge-resolver,heavy-b-migrate}` in any order (no inter-tool deps); (3) verify with `loam --help` + `python -c "from loam_cli.amend.manifest import Manifest"` + `python -c "from loam.heavy_b_migrate.trigger import run_if_dev_intent"`. Halt-trigger §8.1 fires on any non-zero return.
- **`loam amend apply` runs BEFORE the seal commit** per `feedback_dispatch_explicit_pos_amend_apply` (the directive applies to the renamed tool — `loam amend apply` IS the new shape).
- **`git mv` for directory + package + subcommand restructure renames.** Preserves history per Git Safety Protocol; rename-detection threshold preserves blame.
- **No `git commit --amend`** per `feedback_no_amend_in_agent_dispatches`. Corrective commits are NEW commits.
- **HC#4 byte-content sample retire-and-rebaseline NOT EXPECTED at M1g.** Per §11 finding #3: NONE of the M1e-rebaselined sample files reside under `framework/tools/`. M1g's tool-tree restructure should NOT touch any HC#4 sample file. Halt-trigger §8.4 fires only if an unexpected sample-file SHA change emerges.
- **Test scope is narrow.** Per `feedback_amendment_dispatch_speedups`, M1g skips pre-seal full-suite rerun. Touched-test rerun + per-component `test_no_sealed_amendments.py` (which exercises the post-rename allowlist) is the methodology-aligned narrow verification.
- **Historical preservations** per §6: past commit messages, past seal narratives, all `docs/rebuild/plans/*.md` historical plan-docs, `docs/rebuild/spec/pos-v2-rebuild-proposal.md`, and inner content of historical component-record docs preserved verbatim.
- **Unified `loam` CLI top-level shape constraint.** Per `loam-rename-decisions.md` Tier-1 #6: argparse subparsers; `amend` is the first registered subcommand. The dispatcher reserves namespace for future `loam scope`, `loam status`, `loam plot`, etc. (Builder's call within AC bound: choose argparse subparsers vs click — argparse matches the existing pos-amend implementation; minimal author cost.)
- **CLI binary names for the 4 residual tools STAY unchanged.** Per dispatch conservatism — they're not framework component names, they're tool-tree binaries. Renaming them to drop `pos-`/`heavy-b-`/etc. prefixes is FIDRAFT-tracked as a separate amendment.

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full deferred-list. Re-named here for ODD §2.5 compliance.)

- **`com.pos.orchestrator` launchd-label stragglers** — DEFERRED per M1e §11 finding #1 + M1f deferred-list. Recommended landing path: small follow-on M1c-corrective amendment OR M9-scrub. **The only remaining series-relevant rename surface post-M1g.**
- **`pos-bootstrap` / `pos-new-workspace` console-scripts in `framework/workspace-bootstrap/pyproject.toml`** — these are TWO additional `pos-` prefixed CLI binaries OUT of M1g named scope per dispatch (the dispatch enumerates pos-amend + 4 residual tools; pos-bootstrap/pos-new-workspace are NOT named). **FIDRAFT-tracked** per §11 finding #2.
- **CLI binary renames for the 4 residual tools** (`pos-publish-framework-only` → ?; `orphan-plist-cleanup` → ?; `heavy-b-migrate` → ?). Dispatch conservatism keeps them. **FIDRAFT-tracked.**
- **`Degradation*` Python class symbol renames** — M1f-deferred FIDRAFT-tracked.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** historical-narrative-heavy live docs — series-wide deferred.
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` — preserved.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` (other than this plan-doc + manifest YAML) — preserved.
- **Historical component-record docs** at `docs/rebuild/components/<comp>/{research,research-plan,brief,component}.md` — preserved.
- **`docs/rebuild/spec/*.md` (including `pos-v2-rebuild-proposal.md`)** — preserved per Idea 10.
- **`docs/rebuild/plans/two-modes-and-multi-workspace/*.md`** — preserved.
- **Frozen self-upgrade release manifest `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml`** — preserved.
- **Repo directory rename** `ivers-corp-pos-v2` → `loam` — M9-deferred.
- **Path strings** `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred.
- **Workspace-side `<workspace>/.pos/` sentinel directory constants** — series-wide deferred.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`; `git status --short` shows working tree clean (only the pre-existing `personas/` untracked item remains). Verify pos-amend works under its current name (`pos-amend --version`). Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to M1f's §14 backfill commit `af2e740` (or HEAD if subsequent doc-only commits land first; verify by `git log --oneline | head -5`).
3. **M1g sub-plan + manifest commit.** This plan-doc + a manifest YAML at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1g.manifest.yaml` per the established M1a..M1f precedent shape.
4. **Phase A — Tool directory rename.** `git mv framework/tools/pos-amend framework/tools/loam`.
5. **Phase B — Inner package rename.** `git mv framework/tools/loam/src/pos_amend framework/tools/loam/src/loam_cli`.
6. **Phase C — Subcommand restructure.** Within `loam_cli/`:
   - `mkdir framework/tools/loam/src/loam_cli/amend && mkdir framework/tools/loam/src/loam_cli/amend/commands` (and remove the old `commands/` sibling once moved).
   - `git mv framework/tools/loam/src/loam_cli/{cli.py,manifest.py,baseline.py,paths.py,sidecar.py,seal_diff.py,narrative.py,dry_run.py,template_engine.py,tracker_registration.py,rename_detection.py,__main__.py}` into `loam_cli/amend/`.
   - `git mv framework/tools/loam/src/loam_cli/commands/* framework/tools/loam/src/loam_cli/amend/commands/`. Remove the old `loam_cli/commands/` directory.
   - Add `loam_cli/amend/__init__.py` (empty or with version).
   - Author NEW `loam_cli/cli.py` — top-level argparse dispatcher (50–80 LOC). Build a top-level parser with `prog="loam"`, one subparser group with `amend` as the only registered command at M1g time. The `amend` subparser is built by importing `loam_cli.amend.cli` and calling its `_build_parser()` helper (split out from the existing parser-build); when `loam amend ...` runs, dispatch falls through to `loam_cli.amend.cli.main(remaining_argv)`.
   - Update `loam_cli/__init__.py` (move `__version__` from old `pos_amend/__init__.py` if it lived there; keep the same value).
   - Add NEW `loam_cli/__main__.py` for `python -m loam_cli` (calls `cli:main`).
7. **Phase D — pyproject.toml restructure.** `framework/tools/loam/pyproject.toml`:
   - `name = "pos-amend"` → `name = "loam-cli"`.
   - `description = "Amendment-dispatch tooling for pos-v2 (pos-amend CLI)."` → `description = "Unified loam top-level CLI; amend subcommand for amendment dispatch."` (or similar).
   - `[project.scripts]` `pos-amend = "pos_amend.cli:main"` → `loam = "loam_cli.cli:main"`.
   - `[tool.setuptools.packages.find]` stays `where = ["src"]`.
8. **Phase E — Internal pos-amend imports rebrand inside loam_cli/amend/.** Every `from pos_amend.X import Y` (now in `loam_cli/amend/cli.py`, `commands/*.py`, etc.) → `from loam_cli.amend.X import Y`. Mechanical.
9. **Phase F — pos-amend tests rebrand inside framework/tools/loam/tests/.** Every `from pos_amend.X import Y` → `from loam_cli.amend.X import Y`. Conftest fixtures (`"pos-amend test"` git config) → `"loam-cli test"` or similar. Test docstrings + asserts (`"pos-amend"` literal in CLI help-text assertions) update if hard-coded.
10. **Phase G — Update `loam_cli/amend/cli.py`'s `prog` string.** `prog="pos-amend"` → `prog="loam amend"`. Help text rebrand.
11. **Phase H — Editable install refresh #1.** `pip install -e ./framework/tools/loam` → 0. Verify `loam --help` + `loam amend --help` + `python -c "from loam_cli.amend.manifest import Manifest"` succeeds. (At this point in the build, `pos-amend` is no longer the registered binary; the rest of the build uses `loam amend ...`.)
12. **Phase I — heavy-b-migrate consumer rebrand.** `framework/tools/heavy-b-migrate/src/heavy_b_migrate/verify.py` lines 76–84: `from pos_amend.manifest import ...` → `from loam_cli.amend.manifest import ...`; `from pos_amend.tracker_registration import ...` → `from loam_cli.amend.tracker_registration import ...`. Per item 6.
13. **Phase J — HOL bash_guard rebrand.** `framework/hands-off-lifecycle/hooks/bash_guard.py` per AC.RNM-1g.4. Rename function `_pos_amend_dry_run` → `_loam_amend_dry_run`; rename helper `_reason_pos_amend_dry_run` → `_reason_loam_amend_dry_run`; binary path `.venv/bin/pos-amend` → `.venv/bin/loam`; subprocess args insert `"amend"` between binary and `"apply"`; failure-class string `"pos-amend-dry-run-failure"` → `"loam-amend-dry-run-failure"`.
14. **Phase K — HOL agent_guard rebrand.** `framework/hands-off-lifecycle/hooks/agent_guard.py` per AC.RNM-1g.5. `re.compile(r"\bpos-amend\b")` → `re.compile(r"\bloam amend\b")`.
15. **Phase L — HOL test rebrand.** `git mv framework/hands-off-lifecycle/tests/test_AC_BAG_4_pos_amend_dry_run.py framework/hands-off-lifecycle/tests/test_AC_BAG_4_loam_amend_dry_run.py`. Inside: monkeypatch targets + assert strings rebrand. `test_AC_AG_1_wrong_wd_dispatch.py` test prompt fixture rebrand. Module-docstring + comment rebrands across the 5 HOL tests with pos-amend mentions.
16. **Phase M — Component seal-test allowlist rebrand.** Per AC.RNM-1g.6. The 8 hard `"framework/tools/pos-amend/"` allowlist entries rebase to `"framework/tools/loam/"`. The 3 narrative-comment-only entries (objective-tracker, primary-persona, observability-aggregator's `# shape check: pos-amend apply advances ...`) rebrand to `loam amend`. The memory-system narrative comment about `Amendment #22 (pos-amend CLI ...)` is preserved verbatim per §10 D-build.M1g.4 (historical-record naming convention).
17. **Phase N — Live doc/code prose rebrand.** Per AC.RNM-1g.7. The 5 src docstring/comment edits + heavy-b-migrate's src + tests + README + loam-mode README + loam-mode tests fixture-string rebrands + loam-mode src M1a-straggler cleanup.
18. **Phase O — Tools-tree namespace pivot for 4 residuals (Surface B).** Per AC.RNM-1g.8. For each of the 4 tools:
    - `git mv framework/tools/<dir>/src/<old_pkg> framework/tools/<dir>/src/loam/<old_pkg>` (creates the `src/loam/` namespace dir).
    - Update `framework/tools/<dir>/pyproject.toml` `name`, `[project.scripts]` module path. Description rebrand.
    - Internal `from <old_pkg>.X import Y` → `from loam.<old_pkg>.X import Y`. Mechanical.
    - Test-file imports rebrand.
19. **Phase P — Cross-tree consumer rebrands for residual tools.** `framework/workspace-bootstrap/tests/{conftest.py, test_AC_SFR_4_pos_sync_composition.py}` — `from pos_publish_framework_only.synth import ...` → `from loam.publish_framework_only.synth import ...`. `framework/tools/loam-mode/src/loam_mode/session_start.py:293` — `from heavy_b_migrate.trigger import ...` → `from loam.heavy_b_migrate.trigger import ...`.
20. **Phase Q — Editable install refresh #2.** `pip install -e ./framework/tools/{pos-publish-framework-only,orphan-plist-cleanup,upgrade-merge-resolver,heavy-b-migrate}` (each → 0). Verify `python -c "from loam.publish_framework_only.synth import ..."` + `python -c "from loam.heavy_b_migrate.trigger import ..."` succeed.
21. **Phase R — Test sweep (touched files).** Run pytest on:
    - `framework/tools/loam/tests/` (the renamed pos-amend test suite — verifies post-rename CLI surface).
    - `framework/tools/heavy-b-migrate/tests/` (verifies cross-tree pos_amend → loam_cli.amend rebrand + namespace pivot).
    - `framework/tools/pos-publish-framework-only/tests/` (namespace pivot verification).
    - `framework/tools/orphan-plist-cleanup/tests/` (namespace pivot).
    - `framework/tools/loam-mode/tests/` (cross-tree consumer of heavy_b_migrate + fixture path rebrands).
    - `framework/hands-off-lifecycle/tests/test_AC_BAG_4_loam_amend_dry_run.py` (HOL bash_guard rebrand).
    - `framework/hands-off-lifecycle/tests/test_AC_AG_1_wrong_wd_dispatch.py` (HOL agent_guard rebrand).
    - `framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py` (cross-tree pos_publish_framework_only consumer).
    - Plus per-component `test_no_sealed_amendments.py` for each of the 11 components with allowlist edits.
    Halt-trigger §8.7 on non-zero.
22. **Phase S — Feature commit.** Single feature commit carrying all of Phases A–R. Commit message names the M1g slug, the AC family (AC.RNM-1g.1–AC.RNM-1g.S), the tools-tree fence + HOL anchor + 11 component allowlist edits, and the series-master pointer.
23. **Phase T — `loam amend apply`.** Run `loam amend apply <abs-path-to-manifest>` against the manifest. Verify clean apply. **`loam amend apply` BEFORE the seal commit** per FIDRAFT note from amendment #41 + dispatch §Acceptance shape. **Pos-amend invoked under its NEW name** per §10 D-build.M1g.1 mechanism (a).
24. **Phase U — Apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `loam amend apply` convention.
25. **Phase V — Seal-diff fence verification.** AC.RNM-1g.S + AC.RNM-1g.10 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named surfaces. Verify each touched component's `pytest test_no_sealed_amendments.py` passes; HOL `test_cross_cutting.py` passes.
26. **Phase W — `loam amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below). The seal commit narrative cites the AC family, the tools-tree + HOL fence, the 4 residual-tool namespace pivots, the unified `loam` CLI shape, the deferred items (M1c-corrective for launchd-label stragglers, pos-bootstrap/pos-new-workspace as FIDRAFT, residual-tool CLI-binary renames as FIDRAFT).

Phases A–G are the structural-rename phases for pos-amend. Phase H is the first editable-install gate. Phases I–N are mechanical-substitution work for pos-amend's consumers. Phases O–Q are the 4-residual-tools namespace pivot. Phases R–W are commit + seal mechanics.

**Mechanism (a) → (b) fallback procedure.** If Phase H's `pip install -e ./framework/tools/loam` fails for any reason: (1) `git stash` the rename ops; (2) verify `pos-amend --help` works under the old name (the editable install from before this amendment is recoverable); (3) run `pos-amend apply <manifest>` + `pos-amend seal --plan-doc <plan>` UNDER THE OLD NAME to bookkeep M1g's amendment; (4) `git stash pop` the rename ops; (5) re-`pip install -e ./framework/tools/loam`; (6) verify `loam amend --help` succeeds; (7) commit the corrective `pip install -e` re-attempt as a follow-up commit. Surface mechanism choice in §14 D-build.M1g.1.

---

## 8. Halt triggers (M1g-specific; series-wide triggers from master §7 inherit)

Per the dispatch's halt-and-surface clause + dispatch-named §Halt-and-surface enumeration:

1. **Editable-install failure post-restructure.** `pip install -e ./framework/tools/loam` returns non-zero. Surface with the failing tool name + the exit code + the captured stderr. Recovery: invoke mechanism (b) fallback per §7 Phase H fallback procedure.
2. **Unified `loam` top-level CLI design needs structural decisions beyond what the docs specify.** The plan picks argparse-subparsers + `loam_cli/cli.py` dispatcher; if implementation surfaces a structural question (e.g. how to register future subcommands lazily, whether to use entry-point group `loam.subcommands` for plugin extensibility) — surface specific question. Recommendation: defer extensibility-via-entry-points to a follow-on amendment; M1g hard-codes `amend` as the single subparser to keep scope tight.
3. **Tool-tree residual has a structural shape M1e didn't address.** E.g. heavy-b-migrate's data layout (the tool ships data fixtures under `data/` or `fixtures/` that are referenced by absolute paths — if the namespace pivot breaks fixture-resolution, halt and surface the specific fixture path). Pre-build verification at plan-authoring: heavy-b-migrate has no `data/` or `fixtures/` subdir under src; tests use tmpdir fixtures only. NO known structural issue.
4. **HOL cross-cutting / seal-test allowlist contains literal `pos-amend` references that the M1g rename will break.** Per the dispatch §Constraint #4: pre-build verification at plan-authoring confirms 8 hard `"framework/tools/pos-amend/"` allowlist entries + 3 narrative-comment-only mentions in component seal-tests. Per §11 finding #4: the dispatch-time pre-build grep is exhaustive over the set; M1g's scope rebases ALL of them. Halt-trigger fires only if a 12th-or-later allowlist entry surfaces during build.
5. **Frozen-baseline / byte-content-match invariant breach beyond ODD §4 in-band.** Per §11 finding #3: NONE of the M1e-rebaselined HC#4 sample files reside under `framework/tools/`. M1g's tool-tree restructure should NOT touch any HC#4 sample file. Halt-trigger fires only if an unexpected sample-file SHA change emerges.
6. **ODD §2.5 violations encountered in surrounding code.** Halt; do NOT silently extend. Surface for owner ruling on whether to fix in-band, defer, or reshape M1g's scope.
7. **Pre-existing test fails post-rename** (NOT a `loam_cli.amend` ImportError — those mean the rename + editable install didn't complete; that's halt-trigger §1). Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis.
8. **Pos-amend command behaviour changes vs simple rename.** Per dispatch §Halt-trigger #7: any deviation from "validate/apply/seal/template/new-plan all behave identically post-rename" means scope creep. Halt; revert.
9. **Wall-clock exceeds 120 min** (M1g is rubric-priced 40–80 min midpoint 60 min; halt-trigger fires at 1.5× upper bound). Halt with current-state report; dispatcher triages continue / split-further / pause.
10. **A hard-cutover violation.** Builder accidentally adds a `pos-amend` shim binary or registers a dual `[project.scripts]` entry. Halt; remove the shim.
11. **A frozen-record file rebrand.** Builder accidentally rebrands `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml` content or path-strings. Halt; revert.
12. **Symbol-rename scope creep.** Builder accidentally rebrands Python identifiers beyond the named scope (e.g. accidentally renaming the `Manifest` / `ObjectiveEntry` / `LiftedFromEntry` classes, the `register_objectives` / `update_source_commits` API surface, etc.). Halt; revert. Per AC.RNM-1g.10's negative-AC fence.
13. **A `loam_cli` identifier already in use.** Pre-build verification at plan-authoring time: `grep -rE "loam_cli|loam-cli" framework/ docs/` returns hits ONLY in the master plan + this sub-plan (which name the rename target). NO collision in live code. Halt-trigger fires only if a NEW collision emerges during the rename.
14. **Mechanism (a) → (b) fallback fires.** Per dispatch's expectation: if mechanism (a) fails mid-rename, fall back to (b) and surface the cause in §14 D-build.M1g.1. NOT a halt — a fallback-and-surface. Builder records which mechanism was used.

---

## 9. Risks (M1g-specific)

1. **Editable-install cascade failure.** `pip install -e ./framework/tools/loam` failure (e.g. setuptools doesn't discover under the new pyproject) leaves the renamed tool non-importable until fixed. Mitigation: §5 hard-constraint editable-install order + §8 halt-trigger §1 + mechanism (b) fallback procedure in §7 Phase H.
2. **Subcommand-restructure regression.** The pos-amend cli.py is moved from `pos_amend/cli.py` → `loam_cli/amend/cli.py` and a new top-level dispatcher wraps it. If the wrapping introduces argparse-namespace bugs (e.g. the `--version` flag clashes between top-level and subcommand parsers), the CLI surface breaks. Mitigation: §5 constraint "validate/apply/seal/template/new-plan all behave identically post-rename"; §8 halt-trigger §8 (behaviour change → halt).
3. **HOL bash_guard regression.** The bash_guard's hard-coded `.venv/bin/pos-amend` path + subprocess args + failure-class string change concurrently. If any one diverges (e.g. binary path updates but failure-class doesn't), the AC.BAG.4 test fails. Mitigation: AC.RNM-1g.4 enumerates all 4 surfaces; §8 halt-trigger §7 (test fail → halt).
4. **Cross-component allowlist consumer miss.** 8 hard allowlist entries. If a 9th-or-later component carries the entry that pre-build grep missed, the rename leaves the dangling allowlist entry pointing at a non-existent path. Mitigation: post-rename grep `framework/<comp>/tests/test_no_sealed_amendments.py` returning 0 matches for `pos-amend` is the AC.RNM-1g.6 outcome check.
5. **heavy-b-migrate verify.py late-import regression.** The `from pos_amend.manifest import ...` is INSIDE a function (line 76, "Late imports — keep heavy-b-migrate's install graph clean even if pos-amend isn't on path at import time."). Post-rename: `from loam_cli.amend.manifest import ...` — same late-import shape. The comment mentioning "pos-amend isn't on path" rebrands to "loam amend isn't on path". Mitigation: AC.RNM-1g.3 outcome check.
6. **Tools-tree namespace pivot breaks fixture resolution.** The 4 residual tools' tests reference module paths internally; if any fixture-resolution code path uses `__file__`-based path arithmetic that breaks under the deeper namespace, fixtures fail. Mitigation: AC.RNM-1g.8 outcome checks (`pytest framework/tools/<tool>/tests/` PASSES); §8 halt-trigger §3.
7. **Wall-clock blow-out.** Plan-priced 40–80 min midpoint 60 min; the principal source of variance is the subcommand-restructure of pos-amend (~30 min if mechanical; longer if argparse design needs iteration). Mitigation: §8 halt-trigger §9 fires at 120 min.
8. **Mechanism (a) self-rename pip install fails.** Per dispatch's expectation: this is the named risk. Mechanism (b) fallback handles it. Mitigation: §7 Phase H fallback procedure; §14 D-build.M1g.1 records which mechanism was used.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per series master §1, all three D-RNM rulings (split, namespace shape, no compat window) closed at owner-ruling time. Series-master M1g row already records the directory + package + console-script + dispatch-template scope. The unified `loam` top-level CLI shape is dispatch-named (Tier-1 #6 in `loam-rename-decisions.md`).

**Builder's calls within ACs (NOT requiring owner ruling):**

- **D-build.M1g.1 — Self-rename mechanism (a/b/c).** Builder's call within AC.RNM-1g.1 + AC.RNM-1g.S. Recommendation per dispatch §Special-structural-concern: try (a) — rename pos-amend → loam amend BEFORE running apply; reinstall via `pip install -e`; run `loam amend apply` + `loam amend seal --plan-doc` for M1g's own bookkeeping. Fallback (b) if pip install -e fails mid-rename. Builder records actual mechanism in §14 D-build.M1g.1.
- **D-build.M1g.2 — Top-level `loam` CLI dispatcher framework.** Builder's call within AC.RNM-1g.2: argparse subparsers vs click vs typer. Recommendation per §5 constraint + the existing pos-amend implementation: argparse subparsers — matches the existing pos-amend implementation (no new dependency); minimal author cost. The `loam_cli/cli.py` dispatcher uses `argparse.ArgumentParser` with one subparser group; the `amend` subparser is registered by importing `loam_cli.amend.cli` and calling its `_build_parser()` helper (split out from the existing parser-build).
- **D-build.M1g.3 — Subcommand restructure shape.** Builder's call within AC.RNM-1g.1: (a) keep pos_amend/ flat under loam_cli/ (i.e. `loam_cli/cli.py` IS the amend cli); (b) restructure into `loam_cli/amend/...` subdir. Recommendation: option (b) — `loam_cli/amend/...` keeps namespace clean for future `loam_cli/scope/`, `loam_cli/status/`, `loam_cli/plot/`, etc. subcommand surfaces. The dispatch's "future subcommands like `loam scope new`, `loam status` live under the same umbrella" directly motivates this shape.
- **D-build.M1g.4 — Allowlist narrative-comment scope.** Builder's call within AC.RNM-1g.6: 3 allowlist files have `# Amendment #22 (pos-amend CLI + universal-paths retrofit) brings ...` style comments that describe pre-M1g historical events. Recommendation: PRESERVE verbatim for entries that name a specific historical amendment number (`#22` etc.) — these are historical records of what the comment was at the time of that amendment. Rebrand only entries that are LIVE-FENCE-DESCRIPTIVE (e.g. `# shape check: pos-amend apply advances the literal` — the comment describes the live fence behaviour, which is now `loam amend apply`).
- **D-build.M1g.5 — `pos_amend_repo_root` parameter rename in heavy-b-migrate's verify.py.** Builder's call within AC.RNM-1g.7. The function signature `verify_continuous_registration(..., pos_amend_repo_root: Path | None = None, ...)` — the parameter name carries the old tool-name. Recommendation: rebrand to `loam_amend_repo_root` for consistency. Single-symbol rename, easy to grep + verify. Cross-callsite check: `grep -rE "pos_amend_repo_root" framework/` returns 1 callsite (the function def itself); any caller site that names it as a kwarg must also rebrand. Pre-build grep at plan-authoring: 1 callsite (the def); no kwarg callsites. NO breakage.
- **D-build.M1g.6 — CLI binary names for the 4 residual tools.** Builder's call within AC.RNM-1g.8. Per dispatch conservatism: STAY unchanged (`pos-publish-framework-only`, `orphan-plist-cleanup`, `heavy-b-migrate` — no rename). Internal package paths pivot to `loam.<tool>`. Recommendation: follow the dispatch — preserve binary names; FIDRAFT-track the rename as a follow-on amendment. The pos- prefix on `pos-publish-framework-only` is the most awkward; capture in §11 finding #5.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(heavy-b-migrate is the SOLE Python-import consumer of pos-amend's internal API.)** Pre-build verification at plan-authoring time (`grep -rE 'from pos_amend' framework/ docs/ --include='*.py'`): only `framework/tools/heavy-b-migrate/src/heavy_b_migrate/verify.py:76,81` carries the import (2 callsites). No other component or tool imports `pos_amend.*`. AC.RNM-1g.3's pyproject-import-rebrand surface is therefore narrow.

2. **(`pos-bootstrap` / `pos-new-workspace` console-scripts in workspace-bootstrap/pyproject.toml are OUT of M1g scope per dispatch.)** Pre-build verification at plan-authoring: `framework/workspace-bootstrap/pyproject.toml` lines 55–61 carry TWO additional `pos-` prefixed CLI binaries (`pos-bootstrap = "loam.workspace_bootstrap.main:cli_main"`, `pos-new-workspace = "loam.workspace_bootstrap.new_workspace:cli_main"`). The dispatch's M1g scope enumerates `pos-amend` + the 4 residual tools (publish, orphan-plist, upgrade-merge, heavy-b); pos-bootstrap/pos-new-workspace are NOT named. Per ODD §2.5 conservatism + dispatch's "halt and surface ODD violations OR scope creep", these are OUT of M1g. **FIDRAFT-tracked**: "`pos-bootstrap` / `pos-new-workspace` console-scripts in workspace-bootstrap/pyproject.toml — the workspace-bootstrap CLI surface still carries `pos-` prefixed binaries; small follow-on amendment, ≈10 callsites for pyproject + invocation surfaces (each rename cascades to internal imports + dispatch templates referencing the old name). Out of M1g per dispatch's tools-tree-residuals enumeration."

3. **(NONE of the M1e-rebaselined HC#4 sample files reside under `framework/tools/`.)** Per M1e §11 finding #3 + M1e §14 D-build.M1e.5: the 11–15 path updates + 2 SHA bumps in M1e's HC#4 retire-and-rebaseline picked sample files from `framework/{primary-persona,workspace-bootstrap,scope-of-work}/src/...`. Pre-build verification at plan-authoring time confirms M1g's tool-tree restructure does NOT touch any HC#4 sample-file path. Halt-trigger §8.5 fires only if an unexpected sample-file SHA change emerges during M1g's build. The HC#4 invariant is expected to remain GREEN through M1g without any retire-and-rebaseline.

4. **(11 component seal-test allowlist references are exhaustively enumerated.)** Pre-build verification at plan-authoring time (`grep -nE "framework/tools/pos-amend/" framework/*/tests/test_no_sealed_amendments.py`): 8 hard allowlist entries (cost-governance, dormancy, memory-system, observability-aggregator, reversibility-primitive, self-correction, self-upgrade, telegram-interface) + 3 narrative-comment mentions (objective-tracker, primary-persona, workspace-bootstrap). Plus the 3 "shape check" comment-only mentions (observability-aggregator, self-correction) at the top of the allowlist function. Total enumerated: 14 surfaces. AC.RNM-1g.6 + §10 D-build.M1g.4 split these into 8 hard rebrands + 6 narrative-comment rebrands (live fence descriptions; the 4 historical-amendment-number comments stay verbatim).

5. **(The `pos-publish-framework-only` CLI binary name is the most awkward residual.)** Among the 4 residual tools' CLI binaries (which dispatch conservatism preserves): `pos-publish-framework-only` is the most awkward — it carries the literal `pos-` prefix, which is exactly what the M1 series rebrands across the framework. Per dispatch §Constraint "Conservative: only namespace-pivot, don't rename CLI binaries unless the master plan requires it" + master plan silence on tool-binary renames, we preserve it. **FIDRAFT-tracked**: "`pos-publish-framework-only` CLI binary rename to e.g. `loam-publish-framework-only` — the most awkward of the 4 residual-tool CLI binaries; dispatch conservatism preserves it in M1g; ≈5-callsite cleanup amendment (pyproject script line + workspace-side invocation surfaces). Out of M1g per dispatch's tools-tree-residuals enumeration constraint."

6. **(The `framework/tools/loam-mode/src/loam_mode/__init__.py:1` and `cli.py:72` `pos-v2` mentions are M1a stragglers.)** Pre-build verification at plan-authoring time: `grep -nE "pos-v2" framework/tools/loam-mode/`. M1a closed prose-only `pos-v2 → loam`; these 2 callsites are stragglers in tools-tree (M1a's fence was framework-component-scoped READMEs). **In-scope for M1g** as small cleanup work (2 single-line edits). Surfacing here for awareness; included in AC.RNM-1g.7.

7. **(Narrative-record vs live-fence distinction in component seal-test allowlist comments.)** Per §10 D-build.M1g.4: `framework/memory-system/tests/test_no_sealed_amendments.py:205` "Amendment #22 (pos-amend CLI + universal-paths retrofit) brings ..." is a HISTORICAL-RECORD reference to amendment #22's name (the `pos-amend CLI` was correct at the time of #22). PRESERVE verbatim. Similarly: `framework/primary-persona/tests/test_no_sealed_amendments.py:38,40,53` "advanced to the #32 seal commit per `pos-amend apply`" — these reference HISTORICAL events (#32's apply was via `pos-amend`). PRESERVE verbatim. Live-fence-descriptive comments (e.g. "shape check: pos-amend apply advances the literal" describing the LIVE fence) rebrand to `loam amend`. The distinction: comment names a SPECIFIC AMENDMENT NUMBER → preserve verbatim; comment names the LIVE-FENCE BEHAVIOUR (no amendment number) → rebrand.

8. **(Pre-emptive FIDRAFT capture — dispatch-time observations.)** Plan-time observations worth FIDRAFT capture (per `feedback_future_ideas_draft_workflow`):
   - "`pos-bootstrap` / `pos-new-workspace` console-scripts in workspace-bootstrap/pyproject.toml — small follow-on amendment, ≈10 callsites; out of M1g named scope per dispatch" (per §11 finding #2).
   - "`pos-publish-framework-only` CLI binary rename to `loam-publish-framework-only` — the most awkward of the 4 residual-tool CLI binaries; ≈5-callsite cleanup amendment" (per §11 finding #5).
   - "`heavy-b-migrate` CLI binary rename to `loam-heavy-b-migrate` — ≈3-callsite cleanup; out of M1g per dispatch conservatism" (per §10 D-build.M1g.6).
   - "M1c launchd-label stragglers in orchestrator + self-upgrade (`com.pos.orchestrator → com.loam.orchestrator`) — small corrective amendment, ≈20 callsites" (carried from M1e §11 finding #1 + M1f deferred-list).
   - "`Degradation*` Python class symbol rename — separate semantic amendment; ~20 callsites; out of M1f scope per Tier-2 silence + ODD §2.5 conservatism" (carried from M1f §11 finding #4).

   Builder may surface to FIDRAFT during build per `feedback_future_ideas_draft_workflow`; do NOT extend M1g scope to address these.

---

## 12. Method-decision register (placeholder)

The method-decision content for M1g lives in §14 below per the
`loam amend seal --plan-doc` convention (which expects §14 as the
SHA-backfill anchor). Content moved to §14 to avoid duplication.

§14 anchored from authoring per M1c/M1d/M1e/M1f locked precedent (avoid post-seal restructure).

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the cross-cutting verification:

- AC.RNM-1g.1 — directory + package + subcommand restructure: verified by `python -c "from loam_cli.amend.manifest import Manifest"` + `git log --follow framework/tools/loam/src/loam_cli/amend/cli.py` history-preservation check.
- AC.RNM-1g.2 — unified `loam` CLI binary: verified by `loam --help` returning subcommand list with `amend`; `loam amend --help` returning the migrated pos-amend subcommands.
- AC.RNM-1g.3 — internal pos-amend imports: every Phase E + Phase F touched test file (heaviest-touched: `framework/tools/loam/tests/*` — ~22 test files inherit the rename via the `from loam_cli.amend.X import Y` rebrand).
- AC.RNM-1g.4 — HOL bash_guard: verified by `pytest framework/hands-off-lifecycle/tests/test_AC_BAG_4_loam_amend_dry_run.py`.
- AC.RNM-1g.5 — HOL agent_guard: verified by `pytest framework/hands-off-lifecycle/tests/test_AC_AG_1_wrong_wd_dispatch.py`.
- AC.RNM-1g.6 — component seal-test allowlist rebrand: verified by per-component `pytest test_no_sealed_amendments.py` + post-rename grep returning 0 for `framework/tools/pos-amend/` literal.
- AC.RNM-1g.7 — doc/code prose: verified by post-rename grep returning 0 in live (non-historical) surface.
- AC.RNM-1g.8 — tools-tree namespace pivot: verified by `pytest framework/tools/{heavy-b-migrate,pos-publish-framework-only,orphan-plist-cleanup}/tests/` + cross-tree `pytest framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py` + `pytest framework/tools/loam-mode/tests/`.
- AC.RNM-1g.9 — editable installs: verified by `pip install -e ./framework/tools/{loam,pos-publish-framework-only,orphan-plist-cleanup,upgrade-merge-resolver,heavy-b-migrate}` each → 0; `loam --help` succeeds.
- AC.RNM-1g.10 — fence-narrowing negative AC: verified by `git diff <baseline>..HEAD --stat`.
- AC.RNM-1g.S — this seal commit; HOL `test_cross_cutting.py` + HOL `test_d1_byte_content_match.py` (NO retire-and-rebaseline expected — see §11 finding #3).

### Backwards-compat verification

N/A — hard cutover per series-master D-RNM.3.

### HC#4 byte-content sample status

**No retire-and-rebaseline expected.** Per §11 finding #3: NONE of the M1e-rebaselined samples reside under `framework/tools/`. M1g's tool-tree restructure does NOT touch any HC#4 sample file. The HC#4 invariant is expected to remain GREEN through M1g.

### Dependents cleared to dispatch

- **M1c-corrective** (com.pos.orchestrator launchd-label stragglers, ≈20 callsites in orchestrator + self-upgrade) cleared to dispatch post-M1g — small corrective amendment per M1e §11 finding #1 + M1f deferred-list.
- **`pos-bootstrap` / `pos-new-workspace` rename amendment** (≈10 callsites in workspace-bootstrap/pyproject.toml + invocation surfaces) cleared to FIDRAFT-tracking; out of M1g named scope per §11 finding #2.
- **CLI binary renames for the 4 residual tools** cleared to FIDRAFT-tracking; out of M1g per §10 D-build.M1g.6.
- **`Degradation*` Python class symbol rename** (~20 callsites) cleared to FIDRAFT-tracking; out of M1f scope per M1f §10 D-build.M1f.6.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M1g.1 — Self-rename mechanism (a/b/c)

(Populated at build time. Recommendation per §10 + dispatch §Special-structural-concern: try mechanism (a) — rename pos-amend → loam amend BEFORE running apply; `pip install -e ./framework/tools/loam`; run `loam amend apply <manifest>` + `loam amend seal --plan-doc <plan>` for M1g's own bookkeeping. Fallback (b) if `pip install -e` fails mid-rename. Builder records actual mechanism + any fallback cause.)

### D-build.M1g.2 — Top-level `loam` CLI dispatcher framework

(Populated at build time. Recommendation per §10: argparse subparsers — matches the existing pos-amend implementation; minimal author cost; no new dependency. The `loam_cli/cli.py` dispatcher uses `argparse.ArgumentParser(prog="loam")` with one subparser group; `amend` is the first registered subcommand; namespace reserved for future `loam scope`, `loam status`, etc.)

### D-build.M1g.3 — Subcommand restructure shape

(Populated at build time. Recommendation per §10: `loam_cli/amend/...` subdirectory shape — keeps namespace clean for future `loam_cli/scope/`, `loam_cli/status/`, `loam_cli/plot/`, etc. subcommand surfaces.)

### D-build.M1g.4 — Allowlist narrative-comment scope

(Populated at build time. Recommendation per §10: PRESERVE verbatim for entries that name a specific historical amendment number (`#22` etc.); rebrand only entries that are LIVE-FENCE-DESCRIPTIVE.)

### D-build.M1g.5 — `pos_amend_repo_root` parameter rename in heavy-b-migrate's verify.py

(Populated at build time. Recommendation per §10: rebrand to `loam_amend_repo_root` for consistency. Pre-build grep: 1 callsite (the def); no kwarg callsites; NO breakage.)

### D-build.M1g.6 — CLI binary names for the 4 residual tools

(Populated at build time. Recommendation per §10: STAY unchanged per dispatch conservatism; FIDRAFT-tracked as follow-on.)

### Commit SHAs

- Amendment commit: `52dfdbbffaf2e13a007fc0cc83ece74b130f531e` —
  `chore(rename-1g-apply): loam amend apply for amendment #82 (M1g pos-amend → loam amend rename + tools-tree pivot)`
- Seal commit: `f6c22fd6bb1e7a91925ed89ffb2b267ad7d6e3c4` —
  `chore(seals): M1g Tier-1 #6 pos-amend → loam amend CLI rename + tools-tree namespace pivot — directory framework/tools/pos-amend/ → framework/tools/loam/ via git mv (preserving history) + inner package pos_amend → loam_cli via git mv + subcommand restructure (existing pos-amend subcommand surface migrated to loam_cli/amend/{cli.py, commands/{apply.py, seal.py, validate.py, template.py, new_plan.py}, manifest.py, baseline.py, paths.py, sidecar.py, seal_diff.py, narrative.py, dry_run.py, template_engine.py, tracker_registration.py, rename_detection.py}) + new top-level loam_cli/cli.py argparse-subparser dispatcher (amend first registered; namespace reserved for future loam scope, loam status, loam plot subcommands per loam-rename-decisions.md Tier-1 #6) + pyproject [project] name rebrand (pos-amend → loam-cli) + [project.scripts] pos-amend = pos_amend.cli:main → loam = loam_cli.cli:main + ~30 internal from pos_amend.X import → from loam_cli.amend.X import rebrands across loam_cli/amend/{cli.py, commands/*.py} + framework/tools/loam/tests/*.py + 2 cross-tree heavy-b-migrate verify.py pos_amend imports rebrand to loam_cli.amend (lines 76, 81 — late imports per heavy-b-migrate's clean-graph convention) + HOL bash_guard.py rebrand (function _pos_amend_dry_run → _loam_amend_dry_run + helper _reason_pos_amend_dry_run → _reason_loam_amend_dry_run + binary path .venv/bin/pos-amend → .venv/bin/loam + subprocess args [str(loam), 'amend', 'apply', '--dry-run', str(manifest)] + failure_class string 'pos-amend-dry-run-failure' → 'loam-amend-dry-run-failure' + Decision Literal type rebrand) + HOL agent_guard.py rebrand (re.compile(r'\bpos-amend\b') → re.compile(r'\bloam amend\b') in _LOAM_SURFACE_PATTERNS) + HOL test rebrand (test_AC_BAG_4_pos_amend_dry_run.py → test_AC_BAG_4_loam_amend_dry_run.py via git mv + monkeypatch targets + assert strings + test_AC_AG_1_wrong_wd_dispatch.py prompt fixture rebrand) + 11 cross-component test_no_sealed_amendments.py allowlist edits (8 hard 'framework/tools/pos-amend/' → 'framework/tools/loam/' across cost-governance, dormancy, memory-system, observability-aggregator, reversibility-primitive, self-correction, self-upgrade, telegram-interface + 3 narrative-comment live-fence rebrands across observability-aggregator schema-comment + self-correction shape-check + objective-tracker docstring; historical-record amendment-number-named comments preserved verbatim per plan §10 D-build.M1g.4) + ~10 framework src docstring/comment rebrands (objective-tracker filter.py:6 + runtime.py:608 + workspace-bootstrap tracker_seed.py:306 + self-upgrade _build_manifest.py:21 + heavy-b-migrate __init__.py:7,12 + cli.py:94 + amendment_acs.py:16 + verify.py:4-20,56,62,69-76 [pos_amend_repo_root parameter rename to loam_amend_repo_root per plan §10 D-build.M1g.5] + heavy-b-migrate tests + README + loam-mode README:18 + 5 loam-mode tests + 2 loam-mode src M1a-stragglers __init__.py:1 + cli.py:72) + tools-tree namespace pivot for 4 residuals per M1e §11 finding #4 (pos-publish-framework-only/src/pos_publish_framework_only/ → src/loam/publish_framework_only/ via git mv + pyproject name pos-publish-framework-only → loam-publish-framework-only + script module path rebrand + 2 cross-tree consumer rebrands in workspace-bootstrap/tests/{conftest.py, test_AC_SFR_4_pos_sync_composition.py}; orphan-plist-cleanup/src/orphan_plist_cleanup/ → src/loam/orphan_plist_cleanup/ via git mv + pyproject name orphan-plist-cleanup → loam-orphan-plist-cleanup + script module path rebrand; upgrade-merge-resolver/src/upgrade_merge_resolver/ → src/loam/upgrade_merge_resolver/ via git mv + pyproject name upgrade-merge-resolver → loam-upgrade-merge-resolver [library only, no CLI script]; heavy-b-migrate/src/heavy_b_migrate/ → src/loam/heavy_b_migrate/ via git mv + pyproject name heavy-b-migrate → loam-heavy-b-migrate + script module path rebrand + ~22 internal import rebrands in src + tests + 1 cross-tree consumer rebrand in loam-mode/session_start.py:293 from heavy_b_migrate.trigger → from loam.heavy_b_migrate.trigger). CLI binary names for the 4 residual tools (pos-publish-framework-only, orphan-plist-cleanup, heavy-b-migrate; upgrade-merge-resolver has no CLI) STAY unchanged per dispatch conservatism — FIDRAFT-tracked. Hard cutover per series-master D-RNM.3 — no pos-amend shim binary; no transitional dual-binary registration; no from pos_amend re-export module. M1g closes the M1.rename multi-amendment programme. Self-rename mechanism per plan §10 D-build.M1g.1: try (a) — rename → pip install -e → loam amend apply + loam amend seal; fallback (b) if pip install -e fails. HC#4 byte-content sample status: NO RETIRE-AND-REBASELINE (M1e-rebaselined samples reside in primary-persona / workspace-bootstrap / scope-of-work, not framework/tools/; verified at plan-authoring per plan §11 finding #3). pos-bootstrap / pos-new-workspace console-scripts in workspace-bootstrap/pyproject.toml DEFERRED to FIDRAFT-tracked follow-on (out of M1g named scope per plan §11 finding #2). com.pos.orchestrator launchd-label stragglers DEFERRED to small M1c-corrective amendment per M1e §11 finding #1. — hands-off-lifecycle at 52dfdbb`
## 15. References

- **Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Prior sub-amendments:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.md` (sealed `143d465`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.md` (sealed `d97c8c1`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c.md` (sealed `1e99d0b`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1d.md` (sealed `74ae5d3`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1e.md` (sealed `c806f57`; §14 backfill `820fd84`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1f.md` (sealed `390e1ca`; §14 backfill `af2e740`).
- **Authority documents (inherited from series master):**
  - `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 #6 (the M1g target).
  - `.scratch/claude-output/loam-rename-migration-plan.md` §3.6 (mechanics).
- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (M1g row in §5 per series-master ladder).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-loam.md`.
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
  - `feedback_future_ideas_draft_workflow`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1f.manifest.yaml` (M1f sibling — 3-component dormancy rename).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1e.manifest.yaml` (M1e sibling — 14-component namespace pivot).
- **Tool to rename (target of self-rename mechanism):** `framework/tools/pos-amend/` → `framework/tools/loam/` post-M1g.
