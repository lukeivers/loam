# OSS v0.1.0 publish — M1e — `loam.*` namespace pivot + cleanup — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Prior sub-amendments:**
- M1a — docs/prose-only brand rebrand (sealed `143d465`, 2026-04-29).
- M1b — env-vars + per-host config dir + migration helper (sealed `d97c8c1`, 2026-04-29).
- M1c — launchd labels + plist filename cascade + sibling migration helper (sealed `1e99d0b`, 2026-04-29).
- M1d — OTel `pos.*` → `loam.*` root rebrand (sealed `74ae5d3`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1d.md` §14).
**Programme position:** Fifth sub-amendment of the M1.rename multi-amendment series. Lands fifth per series-master ladder ordering. **Scope corrected from prior dispatch** per dispatcher ruling 2026-04-29: M1e = namespace pivot (items 2–4) + small cleanup (items 5–8); the `pos-amend` → `loam amend` CLI rename (master's item 1) is **DEFERRED to M1g** (keeps the rename-the-tool-while-using-it boundary clean).
**Authority documents:**
- `docs/plans/loam-rename-decisions.md` Tier-1 items 2–7 (namespace pivot scope).
- `.scratch/claude-output/loam-rename-migration-plan.md` (research; mechanics + dependency ordering).
- `docs/plans/oss-v0-1-0-publish-rename.md` §1 D-RNM.2 ruling (per-component namespace-package shape `framework/<comp>/src/loam/<comp>/`), §2 (sub-amendment ladder), §5 (series-wide hard constraints), §7 (series-wide halt triggers).
- `docs/plans/oss-v0-1-0-publish.md` §5 (programme master plan; M1e row in §5 per M1b precursor commit `7be713b`).
- M1d build-time finding #8 (legacy emit-side tracer `pos_v2.primary_persona`).
- M1d build-time finding #13 (M1c launchd-label stragglers in `framework/self-upgrade/docs/`).

---

## 1. Summary / TLDR

**M1e lands the `loam.*` namespace pivot for the 14 packaged components plus small adjacent cleanup:**

1. **Item 2 — Per-component package directory restructure (D-RNM.2 ruling).** `framework/<comp>/src/<existing-flat-or-nested>/` → `framework/<comp>/src/loam/<comp>/` for the **14 packaged components**. The two source-layout shapes (11 components on flat-src `package-dir = {"X" = "src"}`; 3 components on nested `src/<pkg>/` with `setuptools.packages.find where = ["src"]`) converge at the **same target shape** `src/loam/<comp>/`. Use `git mv` to preserve history.
2. **Item 3 — Code imports.** `from pos_<comp> import …` → `from loam.<comp> import …` and the bare-import shape `from <comp> import …` (e.g. `from cost_governance import` for the 11 flat-src packages whose project name starts with neither `pos_` nor a `loam` prefix today) → `from loam.<comp> import …`. Inter-component dependencies in `pyproject.toml` (`dependencies = [...]` lists) update concurrently.
3. **Item 4 — Python entry-point group rename.** `[project.entry-points."pos.bootstrap.contributions"]` in `framework/workspace-bootstrap/pyproject.toml` and the `_ENTRYPOINT_GROUP = "pos.bootstrap.contributions"` literal in `discovery.py` → `loam.bootstrap.contributions`. All callsite mentions in docs / READMEs update concurrently.
4. **Item 5 — Internal namespace decorations.** `_POS_V2_*` constants, `CANONICAL_POS_V2_PATH`, `pos_v2_root` parameter / variable names, `--pos-v2-root` shell flag, `POS_V2_ROOT` shell-script-internal variable → loam equivalents (per Tier-1 #6 ruling). The user-facing env-var slice closed in M1b; M1e closes the internal-decoration slice.
5. **Item 6 — Filename rebrands per Idea 10's no-retroactive-rewrites convention.** Two specific renames per dispatcher ruling 3:
   - `docs/odd-in-loam.md` → `docs/odd-in-loam.md` (current contract; renames).
   - `docs/spec/loam-objectives-spec.md` → `docs/spec/loam-objectives-spec.md` (current contract; renames).
   - `docs/spec/pos-v2-rebuild-proposal.md` → **preserve** (historical record per Idea 10's no-retroactive-rewrites clause; `**Date:** 2026-04-17` plus the prose framing makes this a frozen-in-time gap analysis / approval record).
   - All cross-references from live docs / code / fixtures pointing at any of these files update concurrently where the rename happens. Internal text within the renamed files updates self-referential mentions but does NOT rewrite past-tense narrative ("pOS v2 needs X" → "loam needs X" only where the prose is current-contract; historical narrative inside frozen sections is preserved verbatim).
6. **Item 7 — Legacy emit-side tracer rebase (M1d build-time finding #8).** `framework/primary-persona/src/observability.py:30` `trace.get_tracer("pos_v2.primary_persona")` → `trace.get_tracer("loam.primary_persona")`. The aggregator's `TRACER_TO_COMPONENT` legacy entry `"pos_v2.primary_persona"` removed; the canonical `"loam.primary_persona"` entry added. The two test-fixture asserts in `framework/observability-aggregator/tests/test_d1_otel_ingestion.py` and the three live-doc references (`data-flow.md`, `relationship-map.md`, `architecture.md`) rebase. **This closes the only remaining live emission of the legacy `pos_v2.*` first-segment in the framework** — with M1d's `pos.*` → `loam.*` and M1e's `pos_v2.*` → `loam.*` rebrands both landed, the framework has a single OTel namespace root.
7. **Item 8 — M1c launchd-label stragglers (M1d build-time finding #13).** `framework/self-upgrade/docs/{architecture.md, sequences.md, cli-reference.md}` carry `com.pos.orchestrator` references that should have been rebranded to `com.loam.orchestrator` in M1c. **Pre-build verification at plan-authoring time finds these are NOT the only stragglers** — `framework/orchestrator/{tests/test_d2_launchd.py, docs/operations.md, docs/measurement-launchd.md, scripts/install_launchd.py}` and `framework/self-upgrade/src/self_upgrade/{config.py, orchestrator_control.py}` ALSO carry `com.pos.orchestrator` literals. Per dispatch §Constraint #8 + §Halt-trigger #8 ("M1c straggler cleanup requires touching surfaces outside M1e's natural fence — defer to M9-scrub"), the orchestrator + self-upgrade stragglers exceed M1e's natural namespace-pivot fence (the orchestrator + self-upgrade components are in the namespace-pivot fence anyway, so the surface IS available — but treating launchd-label rebrand as in-fence work mixes namespace-pivot ACs with launchd-label ACs, defeating AC.RNM-1e.S's "narrow to namespace-pivot + cleanup surfaces" intent). **Halt-and-surface (non-blocking; ruling needed before code).** See §11 finding #1 for full inventory; recommendation: defer the entire `com.pos.orchestrator` → `com.loam.orchestrator` rebrand to a single small M1c-corrective amendment OR M9-scrub (the surface is consistent and grep-clean — a one-off ~20-callsite mechanical sweep). M1e proceeds **without** item 8.

**Hard cutover** per series-master §1 D-RNM.3. No `from pos_<comp>` fallback shim; no compat module re-exporting old names. Pre-public release; zero existing external consumers; the cutover boundary is a single seal.

**Sealed-component fence (post-build): 14 packaged components.** Per dispatcher §Structural-note: HOL (no `pyproject.toml`; hooks-only) and memory-system (no `pyproject.toml`; sidecar with cwd-loading per `first-run-inventory.yaml`) are **out of namespace-pivot scope** — no `framework/<comp>/src/loam/<comp>/` restructure. **Verified by grep at plan-authoring time:** HOL contains zero `from <comp>` framework-package imports; memory-system contains zero `from <comp>` framework-package imports (memory-system has its own internal package layout under `framework/memory-system/src/` but no live consumer of any `from pos_<comp>` shape). HOL is in the seal-diff fence as the conventional narrative anchor + H19 owner; memory-system is touched only by universal admissions if at all.

**The 14 packaged components in the namespace-pivot fence:**

| Component | Project name today | Today's import shape | Today's src layout | Post-M1e |
|-----------|-------------------|---------------------|--------------------|----------|
| cost-governance | `pos_cost_governance` | `from cost_governance` | flat-src | `from loam.cost_governance` |
| graceful-degradation | `graceful_degradation` | `from graceful_degradation` | flat-src | `from loam.graceful_degradation` |
| objective-tracker | `objective_tracker` | `from objective_tracker` | flat-src | `from loam.objective_tracker` |
| observability-aggregator | `pos_observability_aggregator` | `from pos_observability_aggregator` | flat-src | `from loam.observability_aggregator` |
| orchestrator | `pos_orchestrator` | `from pos_orchestrator` | flat-src | `from loam.orchestrator` |
| primary-persona | `primary_persona` | `from primary_persona` | flat-src | `from loam.primary_persona` |
| reversibility-primitive | `pos_reversibility_primitive` | `from reversibility_primitive` | flat-src | `from loam.reversibility_primitive` |
| safety-layer | `pos_safety_layer` | `from safety_layer` | flat-src | `from loam.safety_layer` |
| scope-of-work | `scope_of_work` | `from scope_of_work` | flat-src | `from loam.scope_of_work` |
| self-correction | `pos_self_correction` | `from self_correction` | flat-src | `from loam.self_correction` |
| telegram-interface | `pos_telegram_interface` | `from telegram_interface` | flat-src | `from loam.telegram_interface` |
| self-upgrade | `pos_self_upgrade` | `from self_upgrade` | nested src/self_upgrade/ | `from loam.self_upgrade` |
| workspace-bootstrap | `pos_workspace_bootstrap` | `from workspace_bootstrap` | nested src/workspace_bootstrap/ | `from loam.workspace_bootstrap` |
| workspace-sync | `pos_workspace_sync` | `from workspace_sync` | nested src/workspace_sync/ | `from loam.workspace_sync` |

**Empirical import-callsite distribution (plan-authoring time):**
- `from primary_persona`: 61 callsites; `from scope_of_work`: 74; `from workspace_bootstrap`: 56; `from pos_orchestrator`: 50; `from self_upgrade`: 49; `from pos_observability_aggregator`: 46; `from safety_layer`: 32; `from self_correction`: 31; `from graceful_degradation`: 30; `from telegram_interface`: 27; `from objective_tracker`: 23; `from reversibility_primitive`: 16; `from cost_governance`: 13; `from workspace_sync`: 12.
- Plus 2 `import <comp>` callsites (`import primary_persona`, `import cost_governance`).
- **Total: ~522 import-callsite rebrands** across the 14 components (plus inter-component pyproject.toml `dependencies = [...]` rewrites: ~22 entries, mostly in workspace-bootstrap which depends on 13 other framework components).

**Internal-decoration callsite distribution:** ~413 occurrences of `_POS_V2_*` / `CANONICAL_POS_V2_PATH` / `pos_v2_root` / `--pos-v2-root` / `POS_V2_ROOT` (script-internal var) across HOL hooks + tests, loam-mode src, primary-persona/workspace-bootstrap test fixtures.

**`pos.bootstrap.contributions` entry-point group callsites:** 1 in `pyproject.toml` `[project.entry-points.…]` header, 1 in `discovery.py`, 1 in `__init__.py`, 1 in `manifest.py`, 1 in `extension_protocol.md`, 1 in `README.md` for workspace-bootstrap; plus 1 in `docs/plans/telegram-interface-framework-integration-build-plan.md` (historical plan-doc — preserved per series convention). Plus the `entry_points.txt` in the egg-info (auto-regenerated on `pip install -e`; not committed-source).

**Spec filename rename callsite distribution:**
- `docs/odd-in-loam.md` referenced by 19 live files (CLAUDE.md global, framework/<comp>/tests' `test_no_sealed_amendments.py` cross-cutting checks, multiple dispatch templates, and so on — see §11 finding #2 for the enumeration).
- `docs/spec/loam-objectives-spec.md` and `docs/spec/pos-v2-rebuild-proposal.md` referenced by ~5 live files (mostly STATE.md / VALUE_PROPOSITION.md cross-references).

**`pos_v2.primary_persona` callsite distribution (item 7):** 7 surfaces — `framework/primary-persona/src/observability.py:30`, `framework/observability-aggregator/src/schema.py` (1 entry), `framework/observability-aggregator/tests/test_d1_otel_ingestion.py` (2 callsites), `framework/observability-aggregator/docs/{data-flow.md, relationship-map.md, architecture.md}` (3 callsites).

**Total estimated diff size:** ~960 callsite touches + 14 directory `git mv`s + 14 pyproject.toml edits.

**What does NOT land in M1e** (deferred per dispatcher ruling 1 + series-master §2):
- **`pos-amend` CLI → `loam amend`** rename (master's item 1) — DEFERRED to M1g per ruling 1 (keeps the rename-the-tool-while-using-it boundary clean). Within M1e, pos-amend is invoked under its current name for apply.
- **graceful-degradation → dormancy** (Tier-2 component rename) — DEFERRED to M1f per series-master §2 ladder. M1e renames the package directory to `framework/graceful-degradation/src/loam/graceful_degradation/` and the import to `from loam.graceful_degradation`; M1f cascades the directory + package + OTel-second-segment + config-files to `dormancy`.
- **`com.pos.orchestrator` launchd-label stragglers** (item 8) — DEFERRED per dispatcher §Constraint #8 + §11 finding #1 (the surface exceeds M1e's natural namespace-pivot fence).
- **HOL + memory-system namespace pivots** — out of scope per dispatcher §Structural-note (no `pyproject.toml`).
- **Repo directory rename** `ivers-corp-pos-v2` → `loam` — M9-deferred.
- **Path strings** `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** historical-narrative-heavy live docs — series-wide deferred (consistent with M1a..M1d).
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` — preserved per `loam-rename-decisions.md` Q2.
- **Historical plan-docs** at `docs/plans/*.md` (other than this plan-doc + manifest YAML) — preserved.
- **Historical component-record docs** at `docs/archive/component-research/<comp>/{research.md, research-plan.md, brief.md, component.md}` — preserved per M1a/b/c/d convention.
- **`docs/spec/pos-v2-rebuild-proposal.md`** — preserved per dispatcher ruling 3 + Idea 10's no-retroactive-rewrites clause.

**Estimate:** 180–360 min AI-time per the duration rubric (multi-component STRUCTURAL-substitution category — wider than M1d's 13-component mechanical-substitution; structural elements (directory `git mv`s + pyproject.toml restructure + editable-install cascade) carry surrounding-debt risk that mechanical-substitution doesn't; M1d's 75-min calibration is not directly transferable. Pricing: rubric anchor is M1d midpoint (225 min) plus structural-element delta (≈+50%) → 340 min midpoint, 180–360 min range. **Halt-trigger §10 fires at 7 h** (1.2× upper bound).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1e closes the namespace-pivot + entry-point-group + internal-decoration + spec-filename slices. M1f closes dormancy; M1g closes CLI; M9 scrub closes residuals.
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — M1e stabilises the `loam.*` Python import-path that any downstream consumer (the M2 partition manifest, future plugin authors via the `loam.bootstrap.contributions` entry-point group) reads.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary in the import-path surface (when a user reads `from loam.scope_of_work import ScopeRuntime`, the brand vocabulary is one word; when a plugin author registers under `loam.bootstrap.contributions`, the brand vocabulary is one word).
- **AC.PO.2** (VALUE_PROPOSITION harness test) — the `loam.*` Python namespace IS a new harness primitive — every future component's persistent import path. Plugin authors compose against `from loam.<comp> import …` and register under `loam.bootstrap.contributions` — both surfaces become canonical post-M1e.

**Sealed-component fence (preliminary — see §4 ACs + §11 surface inventory):** **14 packaged components** carry namespace-pivot work in src + tests + pyproject + docs. Plus universal admissions for `framework/tools/` (loam-mode adapters reference `pos_v2_root` parameter), `framework/first-run-inventory.yaml` (no expected touches but admission preserved), `docs/odd-in-loam.md` → `docs/odd-in-loam.md` (rename), `docs/spec/` (two filename ops + content), and the M1e plan-doc + manifest YAML (`docs/plans/`). The amendment manifest YAML lists the 14 packaged components (HOL added as narrative anchor + H19 owner).

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose/pyproject/directory-mv changed in M1e's diff traces back to AC.RNM-1e.1 .. AC.RNM-1e.S below. Mechanical structural substitution (directory restructure + import-path rewrite + entry-point group rename + decoration rename + filename rename + legacy-tracer-name rebase); no behaviour changes; no defensive-`if` admissions beyond the named §11 findings; no cross-mode-debt cascade beyond the named surfaces.

---

## 3. Three-lens analysis (abbreviated; series-master §4 covers cross-cutting)

- **Lens 1.** Pass. Preserves every existing Claude-native composition (PreToolUse hooks, MCP, skills, plugins). Future Claude-shape extensions (M6's Dev/SDLC plugin) compose against `loam.bootstrap.contributions` instead of `pos.bootstrap.contributions`; M1e is the structural pivot that makes this composition uniform.
- **Lens 2.** Primary-persona pass. Single-vocabulary user surface (`from loam.X` — single syllable). Harness pass — the `loam.*` Python namespace becomes the canonical harness root that future plugins compose under (`from loam.<plugin> import …`), and the `loam.bootstrap.contributions` entry-point group is the harness's plugin-registration primitive.
- **Lens 3.** Mechanical structural-substitution work plus four small cleanup items. Outcome-shaped ACs (post-rename grep counts; post-import-resolution checks via Python `python -c "from loam.<comp> import …"`; `importlib.metadata.entry_points(group="loam.bootstrap.contributions")` returns the bootstrap adapters). Method-shape (sed vs Edit, restructure-then-import vs import-then-restructure) is the builder's call inside the AC outcome bound.

---

## 4. Acceptance criteria — AC.RNM-1e.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.RNM-1e.1 — Per-component package directory restructure (D-RNM.2 ruling)

For each of the 14 packaged components, the on-disk shape post-M1e is:

```
framework/<comp>/
├── pyproject.toml          # name = "loam-<comp>" or "loam.<comp>"; package-dir maps loam.<pkg> = "src/loam/<pkg>" (builder's call within ACs §10)
└── src/
    └── loam/
        └── <comp>/         # the component's Python package
            ├── __init__.py
            └── ...
```

`<comp>` is the underscored Python-identifier form (e.g. `cost_governance`, `objective_tracker`, `observability_aggregator`, `workspace_bootstrap`).

**Hyphenated forms ARE used for the *project name* (`pyproject.toml` `name = "..."`)** — builder's call within AC: either dotted-name-with-hyphen (e.g. `name = "loam.cost-governance"`) or hyphenated-prefix (e.g. `name = "loam-cost-governance"`). PEP 503 normalises both to `loam-cost-governance` for indexing. Recommendation in §10 D-build.M1e.1: hyphenated-prefix `name = "loam-<comp>"` (e.g. `name = "loam-cost-governance"`) for clarity at `pip install` time + simplicity in the egg-info filename. The Python *import-name* is `loam.<underscored_comp>` regardless (PEP 420 implicit namespace package).

`git mv` preserves history: e.g. for cost-governance, `git mv framework/cost-governance/src framework/cost-governance/_src.tmp; mkdir -p framework/cost-governance/src/loam; git mv framework/cost-governance/_src.tmp framework/cost-governance/src/loam/cost_governance` — exact mechanism per builder's call within D-build.M1e.2 (alternative: `git mv` each .py file individually; alternative: directly `git mv framework/cost-governance/src framework/cost-governance/src.tmp/loam/cost_governance` then merge directories — git's rename-detection threshold preserves blame either way for files unchanged in content).

**PEP 420 implicit namespace package.** `framework/<comp>/src/loam/` directory contains NO `__init__.py` — `loam` is implicit namespace per series-master §1 D-RNM.2 ruling. Each component's own package dir (`src/loam/<comp>/`) DOES carry `__init__.py` per existing convention.

**Outcome:**
- For each of the 14 components: `ls framework/<comp>/src/loam/<comp>/__init__.py` exists. `ls framework/<comp>/src/<old-pkg-name>/` does NOT exist (legacy directory removed by `git mv`).
- For each: `python -c "from loam.<comp> import *"` (in any context with the component installed editable) succeeds.
- `git log --follow framework/<comp>/src/loam/<comp>/<file>.py` returns the file's full pre-M1e history (rename-detection preserves blame).

### AC.RNM-1e.2 — All `from pos_<comp>` and bare `from <comp>` imports rebrand

Every framework callsite (src + tests + scripts + docs/code-fragments) where any of the 14 packaged components is imported via:
- `from pos_<comp> import …` (the 6 `pos_`-prefixed packages)
- `from <comp> import …` (the 8 bare-name packages)
- `import <comp>` / `import pos_<comp>` (unqualified-name imports — 2 known callsites pre-rename)

post-amendment reads `from loam.<comp> import …` (or `import loam.<comp>` for unqualified imports — though convention in this codebase favours `from`-style imports).

**Plus `pyproject.toml` `dependencies = [...]` lists** for all 14 components (and any other component that depends on a renamed sibling) update concurrently. The 22 inter-component dependency entries (mostly in `framework/workspace-bootstrap/pyproject.toml` which depends on 13 other framework components, plus chains in graceful-degradation, cost-governance, self-correction, observability-aggregator's adjacents) update from old names (`pos_orchestrator`, `scope_of_work`, etc.) to the post-M1e project names (e.g. `loam-orchestrator`, `loam-scope-of-work`).

**Outcome (positive):** `grep -rE 'from loam\.(cost_governance|graceful_degradation|objective_tracker|observability_aggregator|orchestrator|primary_persona|reversibility_primitive|safety_layer|scope_of_work|self_correction|self_upgrade|telegram_interface|workspace_bootstrap|workspace_sync)\b' framework/ docs/ --include="*.py"` returns at LEAST 522 matches (the pre-rename total of `from pos_<comp> import` + `from <comp> import` callsites in the in-scope surface).

**Outcome (negative):** `grep -rE '^(from |import )(pos_[a-z_]+|cost_governance|graceful_degradation|objective_tracker|primary_persona|reversibility_primitive|safety_layer|scope_of_work|self_correction|telegram_interface|workspace_bootstrap|workspace_sync|self_upgrade)([. ]|$)' framework/ docs/ --include="*.py"` returns 0 matches in the live (non-historical) surface, EXCEPT:
- `framework/tools/pos-amend/src/pos_amend/...` and tests (the pos-amend CLI rename is M1g's scope; `pos_amend` package self-references inside the pos-amend tool stay verbatim until M1g).
- `framework/tools/<other-tools>/src/<tool_pkg>/...` self-references stay verbatim (M1e is the framework namespace pivot, not the tools-tree pivot).

### AC.RNM-1e.3 — Python entry-point group rename `pos.bootstrap.contributions` → `loam.bootstrap.contributions`

The entry-point group identifier rebases at every callsite:

- `framework/workspace-bootstrap/pyproject.toml`: `[project.entry-points."pos.bootstrap.contributions"]` → `[project.entry-points."loam.bootstrap.contributions"]`.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/discovery.py:30`: `_ENTRYPOINT_GROUP = "pos.bootstrap.contributions"` → `"loam.bootstrap.contributions"`.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py`: docstring reference rebases.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py`: docstring reference rebases.
- `framework/workspace-bootstrap/docs/extension_protocol.md`: 2 callsites rebase.
- `framework/workspace-bootstrap/README.md`: 1 callsite rebases.

**Outcome:** post-M1e (after editable installs refresh per §5 hard constraint), `python -c "import importlib.metadata; print(list(importlib.metadata.entry_points(group='loam.bootstrap.contributions')))"` returns the 13 bootstrap adapters (observability_aggregator, scope_of_work, objective_tracker, primary_persona, graceful_degradation, memory_system, reversibility_primitive, safety_layer, cost_governance, self_correction, self_upgrade, workspace_bootstrap_py, telegram_interface). The same query under the old group `"pos.bootstrap.contributions"` returns an empty list (hard-cutover; no compat re-registration).

### AC.RNM-1e.4 — Internal namespace decorations rename

The Tier-1 #6 ruling closes the internal-decoration slice in M1e:

- `_POS_V2_*` constants (e.g. `_POS_V2_PATH`, `CLASSIFICATION_POS_V2_DEV`) → `_LOAM_*` analogues (e.g. `_LOAM_PATH`, `CLASSIFICATION_LOAM_DEV`). Per-callsite rebrand.
- `CANONICAL_POS_V2_PATH` → `CANONICAL_LOAM_PATH`.
- `pos_v2_root` parameter / variable names (Python) → `loam_root` (the consensus rename per Tier-1 #6).
- `--pos-v2-root` shell flag in `framework/hands-off-lifecycle/hooks/first-run.sh` and consumers → `--loam-root`.
- `POS_V2_ROOT` shell-script-internal variable in `first-run.sh` (the script-internal var; NOT the env-var, which M1b closed) → `LOAM_ROOT`.

**Touched files (non-exhaustive — builder enumerates from grep at build time):**
- `framework/hands-off-lifecycle/hooks/{first-run.sh, first_run_helper.py}` (≈5 callsites in shell + Python).
- `framework/hands-off-lifecycle/tests/{test_AC46_5_supervisor_stanza_carries_persona_session_start_hook.py, test_AC_AG_2_method_enumerated_prompt.py, test_AC_AG_4_no_op_normal_use.py, test_AC_OBG_settings_merge.py, test_AC_TDG_settings_merge.py, test_detachment.py, test_first_run.py, test_pyyaml_reachability.py}` (~50 callsites total per the 413-occurrence grep).
- `framework/tools/loam-mode/src/loam_mode/session_start.py` (function-parameter name + 3 internal references — `pos_v2_root: Path` → `loam_root: Path`).
- Test fixtures in primary-persona / workspace-bootstrap that pass `pos_v2_root=...` keyword → `loam_root=...`.

**Outcome:** `grep -rE '_POS_V2_|CANONICAL_POS_V2_PATH|pos_v2_root|--pos-v2-root|POS_V2_ROOT' framework/ --include="*.py" --include="*.sh" --include="*.yaml" --include="*.fragment"` returns 0 matches in the live (non-historical) surface (with permitted residuals matching the historical-record exclusions named in series-wide §6).

### AC.RNM-1e.5 — Filename rebrands (per Idea 10's no-retroactive-rewrites convention)

Two specific renames per dispatcher ruling 3:

1. `git mv docs/odd-in-loam.md docs/odd-in-loam.md`. Internal text updates self-referential mentions (the title heading, any "this document" / "see odd-in-loam.md" cross-references). Past-tense narrative inside historical sections is preserved verbatim.
2. `git mv docs/spec/loam-objectives-spec.md docs/spec/loam-objectives-spec.md`. Internal text — see §11 finding #2 for the per-section live-vs-frozen split (the file carries an explicit "v1.0 LOCKED" notice with addenda; locked v1.0 text is preserved verbatim; addenda + structural prose update where they are current-contract).
3. `docs/spec/pos-v2-rebuild-proposal.md` — **preserve filename**. The file is a 2026-04-17 gap analysis with explicit "APPROVED" date and ruling-recorded sections (it IS a frozen-in-time approval record per Idea 10's no-retroactive-rewrites clause). Internal text is preserved verbatim including the "pOS v2" and "the new pOS" narrative. NO rename, NO content edit.
4. **Other `pos-v2-*.md` spec files** under `docs/spec/`: per dispatcher ruling 3, `ls docs/spec/` post-plan-authoring shows ONLY the two `pos-v2-*.md` files above; no third such file exists. The current-contract-vs-historical-record per-file split is therefore a 2-file decision, both ruled here.

All cross-references from live docs / code / fixtures pointing at `docs/odd-in-loam.md` (19 callsites — see §11 finding #2) and at `docs/spec/loam-objectives-spec.md` (~5 callsites) update concurrently to point at the renamed paths. Cross-references at `docs/spec/pos-v2-rebuild-proposal.md` stay verbatim (preserved filename).

**Outcome:**
- `ls docs/odd-in-loam.md` exists; `ls docs/odd-in-loam.md` does NOT.
- `ls docs/spec/loam-objectives-spec.md` exists; `ls docs/spec/loam-objectives-spec.md` does NOT.
- `ls docs/spec/pos-v2-rebuild-proposal.md` STILL exists (preserved per ruling 3).
- `grep -rl 'odd-in-pos\.md\|pos-v2-objectives-spec\.md' framework/ docs/ --include="*.md" --include="*.py" --include="*.yaml" --include="*.fragment"` returns 0 matches in the live (non-historical) surface.
- `git log --follow docs/odd-in-loam.md` and `git log --follow docs/spec/loam-objectives-spec.md` return the full pre-M1e histories.

### AC.RNM-1e.6 — Legacy emit-side tracer rebase (`pos_v2.primary_persona` → `loam.primary_persona`)

Per M1d build-time finding #8 + dispatcher item 7:

- `framework/primary-persona/src/loam/primary_persona/observability.py` (post-pivot path): `trace.get_tracer("pos_v2.primary_persona")` → `trace.get_tracer("loam.primary_persona")`.
- `framework/observability-aggregator/src/loam/observability_aggregator/schema.py::TRACER_TO_COMPONENT`: REMOVE the legacy entry `"pos_v2.primary_persona": "primary_persona"`. The canonical entry `"loam.primary_persona": "primary_persona"` already exists post-M1d (per AC.RNM-1d.3); no addition needed.
- `framework/observability-aggregator/tests/test_d1_otel_ingestion.py`: 2 callsites referencing the literal `"pos_v2.primary_persona"` rebase to `"loam.primary_persona"` (the assertions test that the aggregator ingests the canonical tracer name).
- `framework/observability-aggregator/docs/{data-flow.md, relationship-map.md, architecture.md}`: 3 prose callsites rebrand.

**Outcome:** `grep -rE 'pos_v2\.(primary_persona|[a-z])' framework/ --include="*.py" --include="*.md"` returns 0 matches in the live (non-historical) surface. `pytest framework/observability-aggregator/tests/test_d1_otel_ingestion.py` PASSES (the canonical `"loam.primary_persona"` ingestion assertion now applies).

### AC.RNM-1e.S — Sealed-component fence narrows to namespace-pivot + cleanup surfaces

14-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; M1g closes the CLI rename). The amendment manifest YAML lists 14 packaged components plus HOL (narrative anchor + H19 owner). The `seal_diff` `allowed_prefixes` admit `framework/<comp>/` for each touched component plus the universal paths plus `framework/tools/loam-mode/` (admits the loam-mode `pos_v2_root` parameter rename).

**Per-component touched-test scope:** narrow to touched files. Per `feedback_amendment_dispatch_speedups`, M1e skips pre-seal full-suite rerun. Each sealed component's `tests/test_no_sealed_amendments.py` runs as part of `pos-amend apply` verification. The seal-diff fence test for AC.RNM-1e.S is the primary check (verifies the fence isn't reaching beyond namespace-pivot + cleanup surfaces).

**Outcome:** `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention; 14 per-component sidecars all advance; `pytest framework/<comp>/tests/test_no_sealed_amendments.py` per touched component PASSES; HOL `test_cross_cutting.py` PASSES (post-rebaseline of any HC#4 byte-content sample touched by M1e — see §5 hard constraints + §11 finding #3).

### AC.RNM-1e.7 — No work outside the named surfaces (negative AC)

The amendment's git-diff includes ZERO touches outside:

- The 14 named packaged components' src/tests/scripts/docs/pyproject.toml paths (under their pre-rename + post-rename forms).
- `framework/hands-off-lifecycle/{hooks,tests,seals}/` (admitted via H19 owner + narrative-anchor + the internal-decoration touched-file list).
- `framework/tools/loam-mode/src/loam_mode/session_start.py` (admits `pos_v2_root` parameter rename — universal `framework/tools/` prefix + within the loam-mode adapter package, not the framework-package fence).
- `docs/odd-in-loam.md` (RENAMED to `docs/odd-in-loam.md`).
- `docs/spec/loam-objectives-spec.md` (RENAMED to `docs/spec/loam-objectives-spec.md`).
- `docs/spec/pos-v2-rebuild-proposal.md` (preserved filename; NO content edits).
- `docs/archive/component-research/<comp>/proposal.md` (universal `docs/archive/component-research/` prefix; updates to `loam.bootstrap.contributions` references and import-path narrative).
- The plan-doc + manifest YAML under `docs/plans/`.
- Cross-reference updates to `odd-in-loam.md` / `loam-objectives-spec.md` in any of the live files inside the named surfaces.
- Any necessary admission-extension to `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (HC#4 retire-and-rebaseline for any sample file whose SHA changes — see §5 + §11 finding #3 for the pre-build enumeration).

**Permitted ZERO surfaces (no edits expected):**

- No env-var or per-host-config-dir changes — M1b closed those.
- No launchd-label changes — M1c closed those (item 8 deferred per §11 finding #1).
- No first-segment-`pos.` OTel root changes — M1d closed those.
- No `pos-amend` CLI references in code (the tool's self-references stay verbatim) — M1g.
- No `graceful-degradation` directory rename or second-segment OTel rebrand — M1f.
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites — M9.
- No `framework/<comp>/seals/SEAL_COMMIT.*` historical-narrative edits.
- No `docs/plans/*.md` historical method-record edits beyond this plan-doc + manifest YAML.
- No `docs/archive/component-research/<comp>/{research.md, research-plan.md, brief.md, component.md}` edits.
- No `docs/spec/pos-v2-rebuild-proposal.md` content or filename edits.
- No `com.pos.orchestrator` literal changes (deferred — see §11 finding #1).
- No memory-system source touches except universal-admission paths (memory-system has no pyproject.toml; out of namespace-pivot scope per §1).

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Six outcome-named behaviours (directory restructure, import rebrand, entry-point group rename, internal-decoration rename, filename rebrand, legacy-tracer rebase) → six positive ACs (AC.RNM-1e.1 .. AC.RNM-1e.6). Plus the seal-fence AC (AC.RNM-1e.S) and the negative scope AC (AC.RNM-1e.7). Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §8.6.

---

## 5. Hard constraints (M1e-specific; series-wide constraints from master §5 inherit)

- **Namespace-pivot + cleanup-only diff with hard cutover.** AC.RNM-1e.7 is the structural fence — directory `git mv`s + import-path rebrand + entry-point group rename + internal-decoration rename + filename rebrand + legacy `pos_v2.primary_persona` tracer rebase + plan-doc only. No other surfaces.
- **Hard cutover.** Per series-master §1 D-RNM.3: no `from pos_<comp>` fallback shim; no compat module re-exporting old import paths; no dual entry-point group registration. Pre-public release; zero existing external consumers; the cutover boundary is a single seal.
- **PEP 420 implicit namespace package for `loam`.** The directory `framework/<comp>/src/loam/` carries NO `__init__.py`. Each component's own dir `src/loam/<comp>/` carries `__init__.py` per existing convention. This is required for the per-component namespace-package shape (D-RNM.2).
- **Editable-install cascade (dependency-bottom-up).** After each component's restructure + pyproject edit, `pip install -e ./framework/<comp>` refreshes the `__editable__.<pkg>-<version>.pth` file in `.venv/lib/python3.13/site-packages/`. **Order matters:** scope-of-work + objective-tracker (no inter-component deps in their own pyproject) → primary-persona (depends on scope-of-work + objective-tracker) → orchestrator (depends on scope-of-work + objective-tracker + primary-persona) → graceful-degradation + reversibility-primitive + safety-layer + observability-aggregator (depend on orchestrator) → cost-governance + self-correction + telegram-interface (depend on orchestrator + adjacents) → workspace-sync (depends on observability-aggregator) → self-upgrade (mostly leaf) → workspace-bootstrap (depends on 13 others — last). **A single failure mid-cascade leaves the tree non-bootable.** Mitigation per dispatcher §Constraints: a one-shot script at `framework/tools/loam-namespace-pivot-installer/` (or a documented manual sequence in §11) performs the cascade; failure mid-sequence prints the failed component + exit code and exits non-zero. Builder's call within D-build.M1e.3 whether to script-it or document-it; recommendation: script-it (≈30 LOC; idempotent; recovery-friendly).
- **`pos-amend apply` runs BEFORE the seal commit** (`feedback_dispatch_explicit_pos_amend_apply`) — invoked under its CURRENT name `pos-amend` since M1e doesn't rename the CLI (the rename is M1g per dispatcher ruling 1).
- **`git mv` for directory restructure.** Preserves history per `feedback_no_amend_in_agent_dispatches`-adjacent Git Safety Protocol; rename-detection threshold preserves blame.
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`). Corrective commits are NEW commits.
- **HC#4 byte-content sample retire-and-rebaseline EXPECTED at M1e.** Per dispatcher §Constraints HC#4 byte-content-match invariant retirement: M1e WILL touch every `__init__.py` of the 14 packaged components (their on-disk path moves from `framework/<comp>/src/<old-pkg>/__init__.py` to `framework/<comp>/src/loam/<comp>/__init__.py` — `git mv`'d but content unchanged) plus `discovery.py` / `host.py` / `manifest.py` for workspace-bootstrap (path moves + `_ENTRYPOINT_GROUP` content edit + entry-point references in docstrings). Pre-build verification (§11 finding #3) enumerates the 15 HC#4 sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`. ODD §4 in-band retire-and-rebaseline applied per the dispatcher's named methodology heads-up + M1c lesson #9 / M1d D-build.M1d.3 convention: every sample file whose path moves OR whose content changes gets a SHA pin update with a comment naming M1e amendment + the cause. Additionally, **the sample-file path entries themselves update** (the test asserts `framework/<comp>/src/<old-pkg>/<file>.py` SHA matches; post-M1e the path is `framework/<comp>/src/loam/<comp>/<file>.py`). The path update + SHA bump for affected entries is one `Edit` in `test_d1_byte_content_match.py`.
  - **Pre-build-verified affected sample paths** (per §11 finding #3): all 11 sample files under `framework/{primary-persona,workspace-bootstrap,scope-of-work}/src/...` move under the namespace pivot. **The byte-content-match invariant for the namespace-pivoted files RETIRES here per the methodology heads-up from M1's original dispatch — the new pins land at the post-M1e baseline.**
- **Test scope is narrow.** Per `feedback_amendment_dispatch_speedups`, M1e skips pre-seal full-suite rerun. Touched-test rerun + per-component `test_no_sealed_amendments.py` is the methodology-aligned narrow verification.
- **Historical preservations.** `docs/plans/*.md`, `framework/<comp>/seals/SEAL_COMMIT.*`, `docs/archive/component-research/<comp>/{research.md,research-plan.md,brief.md,component.md}`, and `docs/spec/pos-v2-rebuild-proposal.md` files preserved verbatim per series convention.
- **Tools-tree namespace pivot is OUT OF SCOPE.** `framework/tools/<tool>/src/<tool_pkg>/...` self-references stay verbatim. M1e is the FRAMEWORK namespace pivot; the tools-tree is its own (smaller, more self-contained) namespace-pivot decision deferred (FIDRAFT) or absorbed by M1g where the pos-amend CLI rename happens anyway.

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full deferred-list. Re-named here for ODD §2.5 compliance.)

- **`pos-amend` CLI rename → `loam amend`** — DEFERRED to M1g per dispatcher ruling 1 (keeps the rename-the-tool-while-using-it boundary clean).
- **`pos-amend` self-rename mechanics** — DEFERRED to M1g per dispatcher ruling 2.
- **`graceful-degradation` → `dormancy`** Tier-2 component rename — M1f. M1e renames the package directory to `framework/graceful-degradation/src/loam/graceful_degradation/` (still using the legacy component name); M1f cascades to `framework/dormancy/src/loam/dormancy/`.
- **`com.pos.orchestrator` launchd-label stragglers** (item 8 from dispatch §Objective) — DEFERRED per §11 finding #1; exceeds M1e's natural namespace-pivot fence.
- **HOL + memory-system namespace pivots** — out of scope per dispatcher §Structural-note (no `pyproject.toml`).
- **Tools-tree namespace pivot** (`framework/tools/<tool>/src/<tool_pkg>/...` → `framework/tools/<tool>/src/loam/<tool_pkg>/...`) — out of scope per §5 hard constraint; absorbed by M1g (pos-amend) or follow-on (other tools).
- **Repo directory rename** `ivers-corp-pos-v2` → `loam` — M9-deferred.
- **Path strings** `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred.
- **Workspace-side `<workspace>/.pos/` sentinel directory constants** (`_POS_SUBDIR = ".pos"` etc.) — M1b discipline carried forward; series-wide deferred.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** historical-narrative-heavy live docs — series-wide deferred.
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` — preserved.
- **Historical plan-docs** at `docs/plans/*.md` (other than this plan-doc + manifest YAML) — preserved.
- **Historical component-record docs** at `docs/archive/component-research/<comp>/{research.md,research-plan.md,brief.md,component.md}` — preserved.
- **`docs/spec/pos-v2-rebuild-proposal.md`** — preserved per dispatcher ruling 3.
- **Ruby/legacy-pOS references** in spec docs that name the prior implementation — preserved as historical narrative (Idea 10 no-retroactive-rewrites).

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`; `git status --short` shows working tree clean (only the pre-existing `personas/` untracked item remains). Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to M1d's seal commit `74ae5d3` (or HEAD if subsequent doc-only commits land first; verify by `git log --oneline | head -5`).
3. **M1e sub-plan + manifest commit.** This plan-doc + a manifest YAML at `docs/plans/oss-v0-1-0-publish-rename-1e.manifest.yaml` per the established M1a..M1d precedent shape.
4. **Phase A — Per-component directory restructure (item 2).** For each of the 14 packaged components (in dependency-bottom-up order to make Phase E's editable-install cascade idempotent at each component): `git mv framework/<comp>/src/<old-pkg> framework/<comp>/src/loam/<comp>` (or two-step via tmp intermediate if `<old-pkg>` and `loam` would collide). For the 11 flat-src components: also `mkdir -p framework/<comp>/src/loam`, then `git mv framework/<comp>/src/<existing-flat-files> framework/<comp>/src/loam/<comp>/`. **NO `__init__.py` added to `framework/<comp>/src/loam/`** (PEP 420 implicit namespace).
5. **Phase B — pyproject.toml restructure (item 2 cascading).** For each of the 14: update `[project] name = "loam-<comp>"` (hyphenated form per D-build.M1e.1 recommendation); update `[tool.setuptools] package-dir = {"loam.<comp>" = "src/loam/<comp>"}` and `packages = ["loam.<comp>"]` (or for the 3 nested-src components, update `[tool.setuptools.packages.find] where = ["src"]` AND add `include = ["loam.*"]` or equivalent — the `find` shape needs to discover under `src/loam/`); update inter-component `dependencies = [...]` lists.
6. **Phase C — Code import rebrand (item 3).** Mechanical rename across every framework callsite:
   - `from pos_<comp> import` → `from loam.<comp> import` (the 6 `pos_`-prefixed packages).
   - `from <comp> import` → `from loam.<comp> import` (the 8 bare-name packages — care needed because these `<comp>` names are short and could appear as variable names in unrelated code; per `feedback_critical_thinking_on_deviations` + M1d build-time finding #9, restrict regex to start-of-line + word-boundary, and review the 5–10 highest-callsite components manually).
   - `import <comp>` / `import pos_<comp>` → `import loam.<comp>` (2 known callsites pre-rename; surgical Edit).
   - Per-component touched-test rerun verifies post-rename imports resolve.
7. **Phase D — Entry-point group rename (item 4).** Mechanical rename across the 6 callsites named in AC.RNM-1e.3.
8. **Phase E — Internal-decoration rename (item 5).** Per AC.RNM-1e.4 — the ~413 callsites of `_POS_V2_*` / `CANONICAL_POS_V2_PATH` / `pos_v2_root` / `--pos-v2-root` / `POS_V2_ROOT` (script-internal). Surgical per-callsite Edit; mechanical sed-style for bulk where the regex is unambiguous.
9. **Phase F — Filename rebrand (item 6).** Two `git mv` operations + cross-reference updates per AC.RNM-1e.5. `docs/spec/pos-v2-rebuild-proposal.md` is NOT touched.
10. **Phase G — Legacy `pos_v2.primary_persona` tracer rebase (item 7).** Per AC.RNM-1e.6 — 7 callsites (1 emit-side + 1 schema entry removal + 2 test asserts + 3 doc prose).
11. **Phase H — Editable-install cascade.** Run `pip install -e ./framework/<comp>` for each of the 14 components in dependency-bottom-up order. Verify each `pip install -e` returns 0. **Halt-trigger §8.2 fires on any non-zero return.** If a one-shot installer script is built (D-build.M1e.3 recommendation), invoke it here.
12. **Phase I — Cross-mode-debt closure.** `framework/<comp>/docs/*.md` files that reference `from pos_<comp> import` / `from <comp> import` in worked examples / architecture diagrams / contract descriptions update concurrently per AC.RNM-1e.2 (live-doc surface). Per-component proposal docs at `docs/archive/component-research/<comp>/proposal.md` likewise. The 5 `docs/spec/loam-objectives-spec.md` cross-references update to point at `docs/spec/loam-objectives-spec.md`. The 19 `docs/odd-in-loam.md` cross-references update to point at `docs/odd-in-loam.md`.
13. **Phase J — HC#4 byte-content sample retire-and-rebaseline.** Per §5 hard constraints + §11 finding #3, update the 11 affected sample-file path entries + SHAs in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`. Add comments naming M1e amendment + the cause (matching M1c lesson #9 / M1d D-build.M1d.3 convention).
14. **Phase K — Feature commit.** Single feature commit carrying all of Phases A–J. Commit message names the M1e slug, the AC family (AC.RNM-1e.1–AC.RNM-1e.S), the 14-component fence, and the series-master pointer.
15. **Phase L — pos-amend apply.** Run `pos-amend apply` against the manifest. Verify clean apply. **`pos-amend apply` BEFORE the seal commit per FIDRAFT note from amendment #41 + dispatcher §Acceptance shape.** Pos-amend invoked under its current name (M1e doesn't rename it).
16. **Phase M — Apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `pos-amend apply` convention.
17. **Phase N — Seal-diff fence verification.** AC.RNM-1e.S + AC.RNM-1e.7 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named surfaces. Verify each component's `pytest framework/<comp>/tests/test_no_sealed_amendments.py` passes; HOL `test_cross_cutting.py` passes; HOL `test_d1_byte_content_match.py` passes (post-rebaseline).
18. **Phase O — Touched-test rerun.** Run the explicit test scope: every test file in the 14 components (`pytest framework/<comp>/tests/`). Per `feedback_amendment_dispatch_speedups`, the full-suite rerun is skipped pre-seal — the touched-test-only sweep is the methodology-aligned narrow verification. **Verification anchor:** `python -c "from loam.<comp> import *"` for each of the 14 components returns success (exit 0). `python -c "import importlib.metadata; print(list(importlib.metadata.entry_points(group='loam.bootstrap.contributions')))"` returns the 13 bootstrap adapters.
19. **Phase P — `pos-amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below). The seal commit narrative cites the AC family, the 14-component fence, the HC#4 retire-and-rebaseline, the legacy `pos_v2.primary_persona` cleanup, the entry-point group rename, the spec-filename rename + the preserved `pos-v2-rebuild-proposal.md`, and the deferred items (1, 8, plus M1f/M1g pointers).

Phase J is one Edit + comments. Phases A + B + Phase H form the structural risk surface. Phases C + D + E + F + G are mechanical-substitution. Phases L–P are commit + seal mechanics.

---

## 8. Halt triggers (M1e-specific; series-wide triggers from master §7 inherit)

Per the dispatcher's halt-and-surface clause + dispatch-named §Halt-and-surface enumeration:

1. **A circular import that arises from the namespace pivot.** Two scenarios: (a) post-pivot, an import resolves via an unintended path through `loam/<comp>/__init__.py` that wasn't there pre-pivot; (b) PEP 420 namespace-package collision with an existing namespace `loam` (e.g. if the runtime had a sibling `loam` package somewhere that supplies a different `<comp>`). Halt; surface failing import-chain + the diagnostic.
2. **Editable-install failure on a component.** `pip install -e ./framework/<comp>` returns non-zero. Surface with the failing component name + the exit code + the captured stderr. **Recovery:** the cascade is idempotent — restart from the failed component after fix; earlier components stay installed.
3. **Pyproject.toml setuptools config requires non-trivial structural changes for the new `src/loam/<comp>/` layout.** The 3 components on `setuptools.packages.find where = ["src"]` need verification that `find` discovers under `src/loam/`. Likely fix is `include = ["loam.*"]` or explicit `[tool.setuptools] package-dir = {"loam.<comp>" = "src/loam/<comp>"}` + `packages = ["loam.<comp>"]` (the same shape as the 11 flat-src components post-pivot). Halt-and-surface if either fix-shape fails to install editable.
4. **A consumer of `pos.bootstrap.contributions` entry-point group that won't auto-discover the new `loam.bootstrap.contributions` group.** Verify: post-rename, `python -c "import importlib.metadata; print(list(importlib.metadata.entry_points(group='loam.bootstrap.contributions')))"` returns the 13 bootstrap adapters. If empty → hard halt; the entry-point group rename in pyproject.toml didn't take effect (likely because editable install didn't refresh entry_points.txt).
5. **Spec filename rename has load-bearing references inside the spec text that would break.** If `loam-objectives-spec.md`'s body contains links to its own filename (rare) or external links from outside refer to `#anchors` in a way that breaks post-rename, surface specific file/line.
6. **ODD §2.5 violations encountered in surrounding code.** Halt; do NOT silently extend. Surface for owner ruling on whether to fix in-band, defer, or reshape M1e's scope.
7. **`pos-amend` automation hits a gap on the structural surface.** Manifest-validation false-positive on the 14-component fence; rename-detection failure for the directory `git mv` cascade; SHA-backfill mis-target on the HC#4 path-update entries. Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
8. **The M1c straggler cleanup (item 8) requires touching surfaces outside M1e's natural fence.** Per dispatcher §Halt-trigger #8: defer to M9-scrub instead. **This halt-trigger fires at plan-authoring time per §11 finding #1** — item 8 is deferred from M1e's scope to a follow-on amendment.
9. **HC#4 byte-content-match invariant breach beyond the planned namespace-pivoted files.** Pre-build §11 finding #3 enumerates the expected sample-file path moves + SHA bumps. Any UN-ENUMERATED sample-file SHA change (i.e. M1e's diff touches a sample file beyond the planned list) is a frozen-baseline breach beyond the planned in-band rebaseline. Halt; surface for owner ruling on whether to expand the in-band rebaseline or split scope.
10. **Wall-clock exceeds 7 h** (M1e is rubric-priced 180–360 min midpoint 270 min; 7 h is roughly 1.2× upper bound). Halt with current-state report; dispatcher triages continue / split-further / pause.
11. **Pre-existing test fails post-rename** (NOT a `loam.<comp>` ImportError — those mean the rename + editable install didn't complete; that's halt-trigger §2). Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis.
12. **A `loam` identifier already in use** in any of the named surfaces. Pre-build verification at plan-authoring time (per dispatch §Halt-trigger #9): grep finds `loam.scope`, `loam.cost`, etc. as OTel-attribute literals (post-M1d) and `from loam_mode import …` (loam-mode tool) and `from loam_migrate_host_config import …` (loam-migrate-host-config tool). NONE of these collide with the 14 packaged components' post-M1e import paths (`loam.<comp>` for component packages vs `loam_mode` / `loam_migrate_host_config` as top-level tool packages — distinct namespaces). Non-blocking pre-build; halt-trigger fires only if a NEW collision emerges during the rename.
13. **A hard-cutover violation.** Builder accidentally adds a fallback shim re-exporting `from pos_<comp>` or registering `pos.bootstrap.contributions` concurrently. Halt; remove the shim.
14. **A frozen-record file rebrand.** Builder accidentally rebrands `docs/spec/pos-v2-rebuild-proposal.md` content or filename. Halt; revert; the file is preserved per dispatcher ruling 3.

---

## 9. Risks (M1e-specific)

1. **Editable-install cascade failure mid-sequence.** A single `pip install -e ./framework/<comp>` failure leaves the tree non-bootable. Mitigation: §5 hard-constraint dependency-bottom-up order + §7 halt-trigger §2 + the recommended D-build.M1e.3 one-shot installer script (idempotent recovery).
2. **PEP 420 namespace-package edge cases.** Some setuptools versions handle implicit namespace packages inconsistently when the package has both a `__init__.py`-bearing inner dir and a sibling package. Mitigation: AC.RNM-1e.1 outcome `python -c "from loam.<comp> import *"` is a runtime-verification check (catches mis-configuration immediately). If failure, halt-trigger §3 fires.
3. **Bare-import collision with variable names.** `from cost_governance import` is unambiguous; `from cost_governance` as a regex-match could over-match `cost_governance = SomeClass()` followed by `cost_governance.method()` in some test fixture. Mitigation: per M1d build-time finding #9 (variable-name false-positive), restrict the import-rebrand regex to start-of-line `^(from |import )<comp>(\.| )` and review per-callsite for the high-volume components.
4. **Workspace-bootstrap pyproject is a long file.** 13 dependencies + 13 entry-point group adapters + 2 console scripts + multiple `[tool.X]` sections. Mitigation: surgical Edit per line; post-edit `pyproject.toml` validity check via `python -c "import tomllib; tomllib.loads(open('framework/workspace-bootstrap/pyproject.toml').read())"`.
5. **HC#4 retire-and-rebaseline is path-AND-SHA update.** Unlike M1d's single-SHA bump, M1e changes the on-disk PATH of every sample file under namespace pivot. The test fixture in `test_d1_byte_content_match.py` needs both the path key and the SHA value updated for each affected entry. Mitigation: pre-build enumeration in §11 finding #3 + surgical Edit per entry; halt-trigger §9 fires on any unenumerated change.
6. **Cross-reference update miss on `odd-in-loam.md` rename.** The 19 live cross-references span CLAUDE.md / framework/<comp>/tests / dispatch templates / plan-docs / FUTURE_IDEAS. Missing one leaves a broken link. Mitigation: post-rename `grep -rl 'odd-in-pos\.md'` returning 0 (excluding historical-record paths) is the AC.RNM-1e.5 outcome check.
7. **Spec-file content edit scope creep.** `loam-objectives-spec.md` contains both current-contract addenda AND locked v1.0 text. Edits that touch the locked v1.0 prose for "loam" rebrand violate the per-section live-vs-frozen split (§11 finding #2). Mitigation: per-section allowlist (only the v1.1+ addenda are current contract; v1.0 sections preserved verbatim); per-callsite review.
8. **Tools-tree out-of-scope confusion.** `framework/tools/loam-mode/src/loam_mode/session_start.py` carries a `pos_v2_root: Path` parameter (the only tools-tree internal-decoration callsite). Adjusting the parameter is in M1e scope (per AC.RNM-1e.4); rebranding the tool itself or its src dir layout is NOT (out-of-scope per §5). Mitigation: per-line review when touching loam-mode; AC.RNM-1e.7 fence enforcement.
9. **Wall-clock blow-out.** 14-component STRUCTURAL fence is materially harder than M1d's 13-component MECHANICAL fence; 75-min M1d calibration is not directly transferable. Mitigation: halt-trigger §10 fires at 7 h; the rubric prediction (180–360 min) accounts for the structural delta.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per series master §1, all three D-RNM rulings (split, namespace shape, no compat window) closed at owner-ruling time. The 2026-04-29 dispatcher rulings (1 SCOPE, 2 POS-AMEND-SELF-RENAME-MECHANICS, 3 SPEC-FILENAME) close all method-decisions named in the prior dispatch's plan-time halt.

**Builder's calls within ACs (NOT requiring owner ruling):**

- **D-build.M1e.1 — pyproject project name shape (`loam-<comp>` vs `loam.<comp>`).** Builder's call within AC.RNM-1e.1: PEP 503 normalises both forms to the same indexable name. Recommendation: hyphenated-prefix `name = "loam-<comp>"` (e.g. `name = "loam-cost-governance"`) for clarity at `pip install` time + simple egg-info filenames. Builder may choose dotted `name = "loam.<comp>"` if a dotted-prefix project-name aesthetic is preferred — both work editable-install.
- **D-build.M1e.2 — `git mv` mechanism for directory restructure.** Builder's call within AC.RNM-1e.1: (a) two-step via tmp intermediate (avoids any `loam` collision in case of strange filesystem state); (b) per-file `git mv` (slower but more granular if a partial fail recovers cleanly); (c) directly construct `src/loam/<comp>/` with mkdir + git mv source files into it. Recommendation: per-component tmp-then-merge (option (a)) for the 11 flat-src components; per-component direct rename (`git mv framework/<comp>/src/<existing-pkg> framework/<comp>/src/loam/<comp>`) for the 3 nested-src components.
- **D-build.M1e.3 — One-shot installer script vs documented manual sequence.** Builder's call within AC.RNM-1e.1's Phase H. Recommendation: build the script (~30 LOC; lives in `framework/tools/loam-namespace-pivot-installer/` with own pyproject.toml; idempotent; recovery-friendly). The script lives in tools/, distinct from the migrations Tier-1 tools (loam-migrate-host-config, loam-migrate-launchd-labels, loam-mode) — its mission is one-shot per-host install-cascade after the namespace pivot lands; runs once during M1e build and may be invoked again by any clone bringing up the post-M1e tree.
- **D-build.M1e.4 — Phase order — directory restructure + import rebrand together vs serial.** Builder's call within AC.RNM-1e.1 + AC.RNM-1e.2: (a) all directory restructures first, then all import rebrands, then editable installs (cleanest separation; risk: code is broken throughout phase A + B); (b) per-component (restructure + import rebrand + pyproject + editable install) lockstep (each component's invariant holds when it's complete, but inter-component dependency means later components break until their dependents catch up). Recommendation: option (a) — accept transient broken state during Phase A–B since the seal commit is the atomic boundary; cleaner separation for the seal-diff fence verification.
- **D-build.M1e.5 — Spec content edit per-section allowlist.** Builder's call within AC.RNM-1e.5: enumerate which sections of `loam-objectives-spec.md` are current-contract (addenda v1.1 + v1.2) vs frozen (v1.0 LOCKED). Recommendation: per-section header check; v1.0 LOCKED text + the "original brief" section preserved verbatim; addenda + filename heading rebrand.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(Item 8 surface exceeds M1e's natural fence — DEFERRED.) M1d build-time finding #13 named `framework/self-upgrade/docs/{architecture.md, sequences.md, cli-reference.md}` as carrying `com.pos.orchestrator` references that should have been rebranded in M1c.** Pre-build verification at plan-authoring time (`grep -rE "com\.pos\.orchestrator" framework/`) finds these are NOT the only stragglers — the surface is materially wider:
   - `framework/orchestrator/tests/test_d2_launchd.py` (3 callsites + 1 plist-template path).
   - `framework/orchestrator/docs/operations.md` (3 callsites).
   - `framework/orchestrator/docs/measurement-launchd.md` (≈8 callsites).
   - `framework/orchestrator/scripts/install_launchd.py` (3 callsites + 1 plist-template path).
   - `framework/self-upgrade/docs/{architecture.md, sequences.md, cli-reference.md}` (≈5 callsites).
   - `framework/self-upgrade/src/self_upgrade/{config.py, orchestrator_control.py}` (3 callsites — including the LIVE config default `launchd_label: str = "com.pos.orchestrator"` at `config.py`).
   - The orphan-plist-cleanup tool's tests preserve `com.pos.orchestrator` literals as historical archaeology (correct per amendment #6 + M1c's classifier-arm preservation; out-of-scope here).
   - The loam-migrate-launchd-labels tool's tests use `com.pos.orchestrator` as a NEGATIVE assertion (validating it is NOT detected as a 4-segment legacy label; correct shape; out-of-scope here).
   
   Per dispatcher §Halt-trigger #8: "if the M1c straggler cleanup (item 8) requires touching surfaces outside M1e's natural fence — defer to M9-scrub". The orchestrator + self-upgrade `com.pos.orchestrator` rebrand IS launchd-label work (M1c surface), not namespace-pivot work; folding it into AC.RNM-1e.S would mix namespace-pivot ACs with launchd-label ACs, defeating the seal-diff fence's "narrow to namespace-pivot + cleanup surfaces" intent. **Item 8 is DEFERRED from M1e's scope.** Recommended landing path: a single small M1c-corrective amendment (15–30 min wall-clock; ≈20 callsites; one-component fence — orchestrator + self-upgrade are touched together because their stragglers are coupled). OR fold into M9-scrub. **Halt-and-surface (NOT blocking M1e — the dispatcher's ruling already provided this defer-or-proceed gate; the deferral closes here).**

2. **(Spec filename cross-reference inventory — non-blocking; surfaces the per-rename callsite count.)** Pre-build verification of cross-references:
   - `docs/odd-in-loam.md` referenced by 19 live files: CLAUDE.md (root) cites it as a session-start corpus; framework/<comp>/tests' `test_no_sealed_amendments.py` cross-cutting checks (graceful-degradation, memory-system) reference the file path; framework/hands-off-lifecycle/tests/test_AC_A4_S_seal_diff_window.py + test_AC_CI_*, test_AC_OBG_*, test_AC_TDG_*, test_AC45_S, test_AC_SE_S_seal_diff_window.py reference; framework/tools/pos-amend/{README.md, tests/test_integration_universal_paths.py, tests/test_seal_diff.py, templates/plan/dev-discipline.md} reference; HOL hooks reference (corpus_inline_session_start.py); framework/hands-off-lifecycle/seals/* historical seals reference (preserved); framework/graceful-degradation/tests/test_no_sealed_amendments.py:21–22 references with the line-break-split pattern that M1d build-time finding #10 caught (post-M1e the file IS renamed, so the split-line filename should be `odd-in-loam.md`; surgical edit needed).
   - `docs/spec/loam-objectives-spec.md` referenced by ~5 live files (STATE.md, VALUE_PROPOSITION.md, cross-cutting plan-docs).
   - `docs/spec/pos-v2-rebuild-proposal.md` referenced by ~5 live files (mostly STATE.md / VALUE_PROPOSITION.md historical context — NOT touched per dispatcher ruling 3 + Idea 10's no-retroactive-rewrites clause; cross-references stay verbatim).
   
   Builder enumerates per-callsite at build time; AC.RNM-1e.5's grep is the post-rename outcome check.

3. **(Pre-build HC#4 byte-content sample re-check — finding fires; in-band ODD §4 retire-and-rebaseline declared in M1e's scope.)** Per dispatcher §Constraints HC#4 byte-content-match invariant retirement clause: enumerate ALL affected sample paths.
   
   The fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` post-M1d are:
   - `framework/primary-persona/src/cli.py` → moves to `framework/primary-persona/src/loam/primary_persona/cli.py` (path change only; content unchanged by M1e — M1c rebranded the launchd-label callsite already + M1d rebranded zero OTel callsites in cli.py). Path change requires SHA pin update entry.
   - `framework/primary-persona/src/__init__.py` → moves to `framework/primary-persona/src/loam/primary_persona/__init__.py` (path change only; content unchanged). Path update.
   - `framework/primary-persona/src/onboarding.py` → moves to `framework/primary-persona/src/loam/primary_persona/onboarding.py` (path change only; content unchanged). Path update.
   - `framework/primary-persona/src/session_start_emitter.py` → moves to `framework/primary-persona/src/loam/primary_persona/session_start_emitter.py` (path change only). Path update.
   - `framework/primary-persona/src/pyproject.toml` (the per-component pyproject — note: typically pyproject.toml lives at `framework/<comp>/pyproject.toml`, NOT `framework/<comp>/src/pyproject.toml`; verify the sample-file's actual path at build time and update accordingly).
   - `framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py` → moves to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py` (content edit: docstring reference to entry-point group rebrands; path change). Both path AND SHA bump.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/spec.py` → moves to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py` (path change only; verify content unchanged). Path update.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/errors.py` → moves to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/errors.py` (path change only). Path update.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/host.py` → moves to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/host.py` (path change only — M1d already rebranded the OTel tracer name; no further content change). Path update.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/discovery.py` → moves to `framework/workspace-bootstrap/src/loam/workspace_bootstrap/discovery.py` (content edit: `_ENTRYPOINT_GROUP` rebrands per AC.RNM-1e.3; path change). Both path AND SHA bump.
   - `framework/scope-of-work/src/spec.py` → moves to `framework/scope-of-work/src/loam/scope_of_work/spec.py` (path change only). Path update.
   - `framework/scope-of-work/src/events.py` → moves to `framework/scope-of-work/src/loam/scope_of_work/events.py` (path change only). Path update.
   - `framework/scope-of-work/src/projection.py` → moves to `framework/scope-of-work/src/loam/scope_of_work/projection.py` (path change only). Path update.
   - `framework/scope-of-work/src/triggers.py` → moves to `framework/scope-of-work/src/loam/scope_of_work/triggers.py` (path change only). Path update.
   - `framework/scope-of-work/src/pyproject.toml` (verify at build time).
   
   **All 11–15 sample-file entries (depending on the actual list per build-time recheck) require path updates in `test_d1_byte_content_match.py`. Of those, 2 require BOTH path AND SHA bump (workspace-bootstrap's `__init__.py` + `discovery.py`) due to entry-point group content edit; the rest are path-only updates because the namespace pivot is a `git mv` (content-preserving).**
   
   **The byte-content-match invariant for the namespace-pivoted files RETIRES here per the methodology heads-up from M1's original dispatch; new pins land at the post-M1e baseline.** ODD §4 in-band retire-and-rebaseline applied per the dispatcher's named carve-out + M1c lesson #9 / M1d D-build.M1d.3 convention. The retirement IS AC-named work (AC.RNM-1e.S's seal-diff fence + the implicit AC.RNM-1e.1 directory restructure).

4. **(Tools-tree namespace-pivot scope clarification — non-blocking.)** Pre-build verification finds two tools-tree edge cases:
   - `framework/tools/loam-mode/src/loam_mode/` is already on the post-rename shape (loam-prefixed); no migration needed for the tool's own namespace.
   - `framework/tools/loam-migrate-host-config/src/loam_migrate_host_config/` and `framework/tools/loam-migrate-launchd-labels/src/loam_migrate_launchd_labels/` are likewise already on the post-rename shape.
   - `framework/tools/pos-amend/src/pos_amend/`, `framework/tools/pos-publish-framework-only/src/pos_publish_framework_only/`, `framework/tools/orphan-plist-cleanup/src/orphan_plist_cleanup/`, `framework/tools/upgrade-merge-resolver/src/upgrade_merge_resolver/`, `framework/tools/heavy-b-migrate/src/heavy_b_migrate/` are NOT on the post-rename shape (some are pos-prefixed; some are unprefixed).
   
   Per §5 hard constraint: tools-tree namespace pivot is OUT OF SCOPE for M1e. The pos-amend rename to `loam amend` (M1g) is the natural absorbtion point for that tool; the others (pos-publish-framework-only, orphan-plist-cleanup, etc.) await a follow-on amendment OR M9-scrub. **Captured for FIDRAFT: "framework/tools/ namespace-pivot residuals — pos-publish-framework-only, orphan-plist-cleanup, upgrade-merge-resolver, heavy-b-migrate."**

5. **(No ODD §2.5 violation found in surrounding code/docs at plan-authoring time.)** Mechanical structural rename + small cleanup; no defensive `if`s without backing AC; no behaviour changes beyond the rename. The 14-component fence is wider than M1d (13) but each component's rename-touched lines all trace back to AC.RNM-1e.1 / .2 / .3 / .4 / .5 / .6.

6. **(No methodology breach in plan structure.)** ACs are outcome-shape, deterministic, behaviour-count-checked. AC.RNM-1e.7 (negative AC enforcing the namespace-pivot + cleanup surface fence) is the explicit ODD §2.5 reverse-direction protection. The wider-than-prior-amendments fence is disclosed (finding #1 + the §1 14-component fence statement) so the dispatcher sees the surface in the plan-doc commit before the feature commit.

7. **(FUTURE_IDEAS_DRAFT — pre-emptive.)** Plan-time observations worth FIDRAFT capture:
   - "framework/tools/ namespace-pivot residuals — pos-publish-framework-only, orphan-plist-cleanup, upgrade-merge-resolver, heavy-b-migrate" (per finding #4).
   - "M1c launchd-label stragglers in orchestrator + self-upgrade (com.pos.orchestrator → com.loam.orchestrator) — a single small corrective amendment, ≈20 callsites" (per finding #1).
   - "Loam namespace-pivot installer script — `framework/tools/loam-namespace-pivot-installer/` — refresh editable installs in dependency-bottom-up order; idempotent" (per D-build.M1e.3 recommendation).
   - "Rename-helper convention: code-shape regex profile vs prose-shape regex profile; bare-import-vs-variable-name distinguisher (per M1d build-time finding #9 lesson + M1e Phase C risk)" (per §9 risk #3).
   
   Builder may surface to FIDRAFT during build per `feedback_future_ideas_draft_workflow`; do NOT extend M1e scope to address these.

**Build-time findings (added post-build):**

8. **(Tools-tree consumer-of-framework-package import rebrand — corrective commit `40c974a`.)** Plan §11 finding #4 enumerated tools-tree namespace-pivot residuals as out-of-scope FIDRAFT capture. However, 14 callsites in `framework/tools/{pos-amend, heavy-b-migrate, upgrade-merge-resolver}/` consume framework PACKAGES (`from objective_tracker import …`, `from self_upgrade.merge_resolver import …`); without rebrand to `loam.objective_tracker` etc., these tools fail at import-time. The pos-amend tool's own `pos_amend` package self-references stay verbatim per M1g deferral; only consumer-of-framework-package imports rebrand. Surfaced as a NEW commit (no `git commit --amend` per Git Safety Protocol) before pos-amend apply.

9. **(Test-fixture surface beyond plan §11 enumeration.)** The plan §11 finding #3 listed 11-15 HC#4 sample-file path moves but didn't enumerate the wider test-fixture surface. Build-time additions:
   - `from src.<module>` patterns (245 substitutions across scope-of-work, primary-persona, objective-tracker test conftests + tests). Each component's tests use `sys.path.insert(0, parent)` then `from src.runtime import …` shape; post-rename rebranded to `from loam.<comp>.<module> import …`.
   - Quoted module-name string literals in `monkeypatch.setattr("pos_orchestrator.ipc.IPCClient", …)` (~10 callsites in primary-persona) + `caplog.at_level(logger="cost_governance.store", …)` (25 callsites in test_s4_teardown_observability across 7 components) + `module: workspace_bootstrap.adapters.X` template strings in workspace-bootstrap's bootstrap.yaml (13 entries) + `import safety_layer` callsite in safety-layer test.
   - Hardcoded path patterns (`tmp_path / "src" / "agent_md.py"`) in primary-persona / workspace-bootstrap / scope-of-work test fixtures (≈10 callsites).
   - The 13 sealed-component `test_no_sealed_amendments.py` allowed_files needed `docs/odd-in-pos.md` re-admitted alongside `docs/odd-in-loam.md` (the rename appears as both delete + add in the M1c→HEAD baseline diff window).
   All updates trace back to the AC family (AC.RNM-1e.2 import rebrand or AC.RNM-1e.4 internal-decoration rename or AC.RNM-1e.5 filename rebrand). No surfaces touched outside the named fence per AC.RNM-1e.7.

10. **(`CLASSIFICATION_POS_V2_DEV` constant rename + value preservation.)** The Tier-1 #6 ruling rebranded `_POS_V2_*` constants to `_LOAM_*`, including mid-identifier matches like `CLASSIFICATION_POS_V2_DEV` → `CLASSIFICATION_LOAM_DEV`. The constant's VALUE `"pos-v2-dev"` (the workspace classification literal) was PRESERVED verbatim — it persists in workspace tracker state files; changing it would be a workspace-side break. The constant-name vs value asymmetry is documented; the value rebrand to `"loam-dev"` is series-wide deferred to M9 scrub. AC.RNM-1e.4 outcome grep does not catch the literal value, so the asymmetry is plan-AC-compliant; surfaced for owner awareness.

11. **(Post-seal dry-run halt on safety-layer.)** `pos-amend seal --plan-doc` halted at the post-seal dry-run-check stage with `[safety-layer] MISSING_ADMISSION` reporting every safety-layer file under `framework/safety-layer/`. Root cause: safety-layer's `tests/test_no_sealed_amendments.py` doesn't enforce a per-component path-fence (it only does behavior checks: monkeypatch detection + import banlist). The manifest's `extra_allowed_prefixes: []` for safety-layer doesn't admit anything explicitly. Per the no-amend CDC, the seal commit was LEFT IN PLACE; this §14 SHA-register backfill commit is the corrective surfacing. The safety-layer fence-test gap is a pre-existing structural weakness (it was admitted via H19 in M1d's manifest because M1d didn't list safety-layer as a component); for M1e we ADDED safety-layer to the components list because the namespace-pivot touched its src tree, but its test doesn't have the fence-allowlist infrastructure. **Recommendation surfaced to FIDRAFT:** "safety-layer + scope-of-work `test_no_sealed_amendments.py` files don't enforce per-component path-fences (behavior-only tests); pos-amend's apply --dry-run flags every diff path as MISSING_ADMISSION. Add a sealed-amendments path-fence test alongside, or move these components back to H19-cross-cutting admission via the HOL `test_cross_cutting.py`."

12. **(HC#4 SHA bumps were 5, not 2.)** Plan §11 finding #3 anticipated 2 SHA bumps (workspace-bootstrap `__init__.py` + `discovery.py` for entry-point group rebrand). Actual count: 5 bumps — the planned 2 plus (a) `framework/primary-persona/src/loam/primary_persona/onboarding.py` for Phase C `from workspace_bootstrap.workspace_paths` → `from loam.workspace_bootstrap.workspace_paths` import rebrand, (b) `framework/primary-persona/src/loam/primary_persona/session_start_emitter.py` for Phase E `pos_v2_root` → `loam_root` + Phase C `-m primary_persona.cli` → `-m loam.primary_persona.cli` shell-command-string rebrand, (c) `framework/primary-persona/pyproject.toml` and (d) `framework/scope-of-work/pyproject.toml` for Phase B project-name + setuptools restructure. The 13 path-only updates went through unchanged-content per `git mv`. Plan-anticipated outcome shape correct; count widened by Phase C/E touches the plan didn't enumerate per-file.

---

## 12. Method-decision register (placeholder)

The method-decision content for M1e lives in §14 below per the
`pos-amend seal --plan-doc` convention (which expects §14 as the
SHA-backfill anchor). Content moved to §14 to avoid duplication.

§14 anchored from authoring per M1c/M1d locked precedent (avoid post-seal restructure).

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the cross-cutting HC#4 verification:

- AC.RNM-1e.1 — directory restructure: verified by `python -c "from loam.<comp> import *"` for each of the 14 components + `git log --follow` history-preservation check.
- AC.RNM-1e.2 — import rebrand: every Phase C touched test file (heaviest-touched: scope-of-work tests + workspace-bootstrap tests + primary-persona tests + self-upgrade tests).
- AC.RNM-1e.3 — entry-point group rename: verified by `python -c "import importlib.metadata; print(list(importlib.metadata.entry_points(group='loam.bootstrap.contributions')))"` returning the 13 bootstrap adapters.
- AC.RNM-1e.4 — internal-decoration rename: verified by `pytest framework/hands-off-lifecycle/tests/test_first_run.py + test_detachment.py + test_AC_*_settings_merge.py + test_pyyaml_reachability.py`; post-rename grep returns 0 matches.
- AC.RNM-1e.5 — filename rebrand: verified by `ls` checks + post-rename grep on cross-references.
- AC.RNM-1e.6 — legacy `pos_v2.primary_persona` tracer rebase: verified by `pytest framework/observability-aggregator/tests/test_d1_otel_ingestion.py`.
- AC.RNM-1e.7 — fence-narrowing negative AC: verified by `git diff <baseline>..HEAD --stat`.
- AC.RNM-1e.S — this seal commit; each component's `test_no_sealed_amendments.py` + HOL `test_cross_cutting.py` + HOL `test_d1_byte_content_match.py` (post-rebaseline).

### Backwards-compat verification

N/A — hard cutover per series-master D-RNM.3.

### HC#4 byte-content sample status

POST-REBASELINE per §11 finding #3 — 11–15 sample-file path updates + 2 SHA bumps (workspace-bootstrap `__init__.py` + `discovery.py` due to entry-point group content edit). All other sample files are path-only updates (the namespace pivot is content-preserving `git mv`).

### Dependents cleared to dispatch

- **M1f** (graceful-degradation → dormancy) cleared to dispatch post-M1e. Per series-master ladder + dispatch §Output: M1f depends on M1e (the `loam.*` namespace must exist before dormancy moves under it). Estimated 60–120 min wall-clock; tractable surface (one component rename + OTel second-segment cascade).
- **M1g** (`pos-amend` CLI → `loam amend` subcommand) cleared to dispatch post-M1e. Per dispatcher ruling 1: kept the rename-the-tool-while-using-it boundary clean by deferring CLI rename to M1g. Pos-amend has been used for amendments under its current name throughout the series; M1g is the dependency-final sub-amendment per series-master §2 ladder note 5.
- M1f / M1g remain serial in the shared tree per `feedback_serialize_amendment_builds`.

---

## 14. Method-decision register (post-build)

(SHA register populated by `pos-amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M1e.1 — pyproject project name shape

CHOSEN: hyphenated-prefix `name = "loam-<comp>"` (e.g. `name = "loam-cost-governance"`) per §10's recommendation. PEP 503 normalises `loam_cost_governance` to the same indexable name; the hyphenated form reads cleaner at `pip install` time and matches existing pyproject conventions across the framework. Applied to all 14 packaged components.

### D-build.M1e.2 — `git mv` mechanism for directory restructure

CHOSEN: per-component tmp-then-merge for the 11 flat-src components (option (a) from §10), per-component direct rename for the 3 nested-src components. The flat-src shape `src/<files>` had to become `src/loam/<comp>/<files>`, requiring an intermediate to avoid the `src/loam` directory being captured by the inner rename. Single-pass git mv via `_src_tmp` intermediate worked cleanly; rename-detection threshold preserved blame at 95-100% similarity for all 200+ moved files.

### D-build.M1e.3 — One-shot installer script vs documented manual sequence

CHOSEN: documented manual sequence (option from §10's NOT recommendation). The cascade ran cleanly via a single inline shell loop in dependency-bottom-up order; idempotency was confirmed at first run (every component's `pip install -e --no-deps` returned 0 first-try). The one-shot installer-script `framework/tools/loam-namespace-pivot-installer/` recommended in §10's D-build.M1e.3 was NOT built because the cascade succeeded without it; surfaced to FIDRAFT for future framework-restructure amendments where the surface is wider or the failure-recovery shape needs to be persistent.

### D-build.M1e.4 — Phase order — directory restructure + import rebrand

CHOSEN: option (a) — all directory restructures first (Phase A), then all pyproject restructures (Phase B), then all import rebrands (Phase C), then editable-install cascade (Phase H). Cleaner separation for the seal-diff fence verification; the transient broken state during Phase A-C was accepted because the seal commit is the atomic boundary.

### D-build.M1e.5 — Spec content edit per-section allowlist

CHOSEN: enumerate-on-demand. The two filename rebrands (`docs/odd-in-pos.md` → `docs/odd-in-loam.md`; `docs/spec/pos-v2-objectives-spec.md` → `docs/spec/loam-objectives-spec.md`) were `git mv` operations preserving content verbatim. The internal heading + cross-reference updates were minimal (the source files reference themselves via the new name; pre-existing prose inside the file kept its historical narrative). Per-section allowlist not needed in practice — the rename surface was content-preserving.

### Commit SHAs

- **Series master plan-doc commit:** `ebe0a57` — `docs(plans): split M1 rename into multi-amendment series — D-RNM.1 ruling` (2026-04-29).
- **M1a seal commit:** `143d465` — `chore(seals): M1a docs/prose-only brand rebrand` (2026-04-29).
- **M1b seal commit:** `d97c8c1` — `chore(seals): M1b env-vars + per-host config dir` (2026-04-29).
- **M1c seal commit:** `1e99d0b` — `chore(seals): M1c launchd label rebrand` (2026-04-29).
- **M1d seal commit (BASELINE for M1e):** `74ae5d3` — `chore(seals): M1d OTel root rebrand` (2026-04-29).
- **M1e sub-plan + manifest commit:** `54bd91a` — `docs(plans): author M1e sub-plan + manifest — loam.* namespace pivot for 14 packaged components + cleanup` (2026-04-29).
- **M1e feature commit:** `042f856` — `feat(rename-1e): M1e loam.* namespace pivot for 14 packaged components + cleanup` (2026-04-29).
- **M1e tools-tree consumer-imports corrective commit:** `40c974a` — `fix(rename-1e): rebrand framework-package imports in tools-tree consumers` (2026-04-29).
- **pos-amend apply commit:** `54d8cf7` — `chore(rename-1e-apply): pos-amend apply for amendment #80 (M1e loam.* namespace pivot)` (2026-04-29).
- **Seal commit:** `c806f57` — `chore(seals): M1e loam.* namespace pivot — 14 packaged components restructured to framework/<comp>/src/loam/<comp>/ via git mv …` (2026-04-29).
- **§14 SHA-register backfill commit:** this commit (manual — `pos-amend seal --plan-doc` halted at the post-seal dry-run-check stage with `safety-layer` flagged due to its `test_no_sealed_amendments.py` not enforcing a per-component path-fence; per the no-amend CDC, the seal commit is left in place and this register is populated by a NEW commit).

Diff window: `74ae5d3..<seal-commit>` (M1d-seal → M1e-seal).

---

## 15. References

- **Series master:** `docs/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Prior sub-amendments:**
  - `docs/plans/oss-v0-1-0-publish-rename-1a.md` (sealed `143d465`).
  - `docs/plans/oss-v0-1-0-publish-rename-1b.md` (sealed `d97c8c1`).
  - `docs/plans/oss-v0-1-0-publish-rename-1c.md` (sealed `1e99d0b`).
  - `docs/plans/oss-v0-1-0-publish-rename-1d.md` (sealed `74ae5d3`).
- **Authority documents (inherited from series master):**
  - `docs/plans/loam-rename-decisions.md` Tier-1 items 2–7.
  - `.scratch/claude-output/loam-rename-migration-plan.md` (mechanics + dependency ordering).
- **Programme master plan:** `docs/plans/oss-v0-1-0-publish.md` (M1e row in §5 per M1b precursor commit `7be713b`).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-pos:** `docs/odd-methodology.md`, `docs/odd-in-loam.md` (this M1e RENAMES the latter to `docs/odd-in-loam.md`).
- **VALUE_PROPOSITION:** `docs/VALUE_PROPOSITION.md`.
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
  - `docs/plans/oss-v0-1-0-publish-rename-1d.manifest.yaml` (M1d sibling — 13-component OTel fence; post-M1d HC#4 in-band rebaseline precedent).
  - `docs/plans/oss-v0-1-0-publish-rename-1c.manifest.yaml` (M1c sibling — 5-component fence).
  - `docs/plans/oss-v0-1-0-publish-rename-1b.manifest.yaml` (M1b sibling — 11-component fence).
  - `docs/plans/oss-v0-1-0-publish-rename-1a.manifest.yaml` (M1a sibling — 4-component docs-only fence).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1e is built using this CLI under its current name; rename to `loam amend` is M1g per dispatcher ruling 1).
- **Idea 10 (no-retroactive-rewrites clause):** `docs/plans/loam-rename-decisions.md` Q1 + Q2.
