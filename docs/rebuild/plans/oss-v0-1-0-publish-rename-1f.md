# OSS v0.1.0 publish — M1f — graceful-degradation → dormancy (Tier-2 component rename) — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Prior sub-amendments:**
- M1a — docs/prose-only brand rebrand (sealed `143d465`, 2026-04-29).
- M1b — env-vars + per-host config dir + migration helper (sealed `d97c8c1`, 2026-04-29).
- M1c — launchd labels + plist filename cascade + sibling migration helper (sealed `1e99d0b`, 2026-04-29).
- M1d — OTel `pos.*` → `loam.*` root rebrand (sealed `74ae5d3`, 2026-04-29; SHA-register `oss-v0-1-0-publish-rename-1d.md` §14).
- M1e — `loam.*` namespace pivot for 14 packaged components + cleanup (sealed `c806f57`, 2026-04-29; SHA-register backfill `820fd84`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1e.md` §14).
**Programme position:** Sixth sub-amendment of the M1.rename multi-amendment series. The single Tier-2 thematic rename per `loam-rename-decisions.md`. Lands sixth per series-master ladder note 4 ("M1f depends on M1e — the `loam.*` namespace must exist before dormancy moves under it").
**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` Tier-2 (the M1f target).
- `.scratch/claude-output/loam-rename-migration-plan.md` §4.1 (research mechanics).
- `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` §2 ladder (M1f row), §5 series-wide hard constraints, §7 series-wide halt triggers.
- `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (programme master plan; M1f row per series-master ladder).
- M1d's locked second-segment OTel narrative (`oss-v0-1-0-publish-rename-1d.md`): M1d rebased first segment `pos.*` → `loam.*` and held the `pos.degradation.*` second-segment surface as `loam.degradation.*` (interim shape), explicitly deferring the `degradation` → `dormancy` second-segment cascade to M1f.

---

## 1. Summary / TLDR

**M1f lands the Tier-2 thematic rename — graceful-degradation → dormancy — across one sealed component plus three small cross-component touchpoints:**

1. **Item 1 — Directory rename.** `framework/graceful-degradation/` → `framework/dormancy/` via `git mv` (preserving history).
2. **Item 2 — Package rename inside the namespace.** Post-M1e, the package lives at `framework/graceful-degradation/src/loam/graceful_degradation/`. M1f cascades:
   - `framework/dormancy/src/loam/graceful_degradation/` → `framework/dormancy/src/loam/dormancy/` via `git mv`. (Step 1's `git mv` rebases the directory; step 2 rebases the inner package name.)
3. **Item 3 — Import-callsite rebrand.** Every `from loam.graceful_degradation import …` (61 callsites at plan-authoring time) and `from loam.graceful_degradation.<sub> import …` callsite rebrands to `from loam.dormancy[.<sub>] import …`. Bulk-mechanical with surgical review for high-volume files (the 11 dormancy-internal test files carry the bulk).
4. **Item 4 — pyproject.toml restructure.** `framework/dormancy/pyproject.toml` updates `name = "loam-graceful-degradation"` → `name = "loam-dormancy"` + setuptools `package-dir = {"loam.graceful_degradation" = ...}` and `packages = ["loam.graceful_degradation"]` → `loam.dormancy` equivalents + the `description` line rebrand if currently mentioning "graceful-degradation". Inter-component dependents update the `loam-graceful-degradation` dependency name to `loam-dormancy` (workspace-bootstrap pyproject is the only known dependent — see §11 finding #1).
5. **Item 5 — OTel second-segment cascade.** `loam.degradation.*` span / event / attribute names → `loam.dormancy.*` (89 callsites at plan-authoring time, mostly in dormancy's own observability.py + tests + architecture.md). Per `loam-rename-decisions.md` Tier-2 + the M1d sub-plan's deferred-second-segment statement, this is the cascade the Tier-2 rename owns.
6. **Item 6 — Config-file path cascade.** `~/.loam/degradation.sqlite` → `~/.loam/dormancy.sqlite` (36 callsites); `~/.loam/degradation-config.yaml` → `~/.loam/dormancy-config.yaml` (24 callsites). Both at the config-default path, in default `__init__.py` strings, in workspace-bootstrap's `first_run_scaffold.py` template, in self-upgrade's `paths.py` + `snapshot.py` documentation tables, in dormancy's own architecture.md / config.py / state.py default paths.
7. **Item 7 — Per-host config-file migration helper.** A new `framework/tools/loam-migrate-dormancy-config/` migration helper (mirroring the M1b `loam-migrate-host-config` shape — the directory was M1b's surface; this helper owns the file-rename within `~/.loam/`). Idempotent four-case logic (case 1: `degradation.sqlite|.yaml` exists, `dormancy.*` doesn't → rename; case 2: `dormancy.*` exists, `degradation.*` doesn't → no-op; case 3: neither → no-op; case 4: both → halt). The SQLite WAL file (`degradation.sqlite-wal`) and the SHM file (`degradation.sqlite-shm`) cascade with the main file when present (single rename moves the WAL and SHM siblings as well).
8. **Item 8 — Component docs subdir rename per series-master M1f row.** `docs/rebuild/components/graceful-degradation/` → `docs/rebuild/components/dormancy/` via `git mv`. **This rename DEVIATES from the series-wide convention that `docs/rebuild/components/<comp>/{research.md,research-plan.md,brief.md,component.md}` are preserved historical records** — the series-master M1f row explicitly names this rename as in-scope for M1f, overriding the general preservation default for THIS component (and only this component). See §10 D-build.M1f.5 for the method-decision.
9. **Item 9 — Workspace-bootstrap adapter rename.** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/graceful_degradation.py` → `adapters/dormancy.py` via `git mv`. The contribution-name string `name="graceful_degradation"` inside the file rebases to `name="dormancy"`. The `pyproject.toml` `[project.entry-points."loam.bootstrap.contributions"]` row `graceful_degradation = "loam.workspace_bootstrap.adapters.graceful_degradation:GracefulDegradationContribution"` rebrands to `dormancy = "loam.workspace_bootstrap.adapters.dormancy:DormancyContribution"`. The `host.py` `self.graceful_degradation: Any = None` field renames to `self.dormancy: Any`. The `first_run_scaffold.py` template strings (`name: graceful_degradation`, `module: loam.workspace_bootstrap.adapters.graceful_degradation`) rebase. Test fixtures (`test_first_run_scaffold.py`, `test_integration_foundational.py`, `test_extension_protocol.py`, `test_bootstrap_unification.py`) update the `"graceful_degradation"` string-literal references.
10. **Item 10 — Self-upgrade probes + manifest-builder component-name rebrand.** `framework/self-upgrade/src/loam/self_upgrade/probes.py` (3 callsites: docstring + section comment + `from loam.graceful_degradation.state` import) + `framework/self-upgrade/manifests/_build_manifest.py` (1 callsite: `"graceful-degradation"` in the component-name list — this is a LIVE re-generator script, distinct from the FROZEN release manifest `pos-v2-v0.2.0.yaml`). The probe-target `degradation.state.DegradationStore` reference in the probes.py `from loam.graceful_degradation.state import DegradationStore` rebases to `from loam.dormancy.state import DormancyStore` IF the `DegradationStore` class also rebrands; see §10 D-build.M1f.6 for the symbol-rename ruling.
11. **Item 11 — `framework/first-run-inventory.yaml` component-name list.** `"graceful-degradation"` → `"dormancy"` (1 callsite). The YAML lists sealed components by their hyphenated framework-directory names; the entry needs to follow the directory rename.
12. **Item 12 — H19 / HC#4 byte-content sample status.** Plan-time pre-verification: M1e's `test_d1_byte_content_match.py` rebaseline (per M1e §11 finding #3) updated 11–15 entries to point at `framework/<comp>/src/loam/<comp>/<file>.py`. **Pre-build verification at plan-authoring time finds NONE of those paths reside under `framework/graceful-degradation/`** — the M1e rebaseline picked sample files from primary-persona / workspace-bootstrap / scope-of-work, not from graceful-degradation. **M1f's directory + package rename therefore does NOT touch any HC#4 sample file.** No HC#4 retire-and-rebaseline is expected; halt-trigger §8.4 fires only if an unexpected sample-file SHA change emerges.

**Hard cutover** per series-master §1 D-RNM.3. No `from loam.graceful_degradation` fallback shim; no compat module re-exporting old names; no dual-namespace OTel emission. Pre-public release; zero existing external consumers.

**Sealed-component fence (post-build): 1 packaged component (dormancy, formerly graceful-degradation) plus the workspace-bootstrap consumer (adapter rename + pyproject entry-point row + host.py field + test-fixture string rebrand) plus the self-upgrade consumer (probes.py + _build_manifest.py refs).** Per `feedback_serialize_amendment_builds`, M1f remains serial in the shared tree against M1e's seal commit `c806f57` + the §14 backfill `820fd84` as BASELINE.

**The 1 + 2 components in the M1f fence:**

| Component | Today's framework path | Post-M1f path | Today's import shape | Post-M1f import shape |
|-----------|------------------------|---------------|---------------------|------------------------|
| dormancy (was graceful-degradation) | `framework/graceful-degradation/src/loam/graceful_degradation/` | `framework/dormancy/src/loam/dormancy/` | `from loam.graceful_degradation` | `from loam.dormancy` |
| workspace-bootstrap | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/graceful_degradation.py` | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/dormancy.py` | `loam.workspace_bootstrap.adapters.graceful_degradation` | `loam.workspace_bootstrap.adapters.dormancy` |
| self-upgrade | n/a (consumer only — `probes.py` import + `_build_manifest.py` component list) | n/a (consumer only) | `from loam.graceful_degradation.state` (probes.py); `"graceful-degradation"` string (_build_manifest.py) | `from loam.dormancy.state`; `"dormancy"` |

**Empirical surface inventory (plan-authoring time):**

| Surface | Count | Where (high-traffic) |
|---------|-------|----------------------|
| `from loam.graceful_degradation`-shape imports | 61 | dormancy/tests/* (45+ across test_d1..d10), dormancy/tests/fakes.py, self-upgrade/tests/test_probes.py, self-upgrade/src/loam/self_upgrade/probes.py |
| `loam.degradation` OTel callsites | 89 | dormancy/src/loam/.../observability.py (~30), dormancy/tests/test_d9_observability.py (~15), test_amendment_20_silent_excepts.py (~10), test_d10_one_hour_outage.py (~3), dormancy/docs/architecture.md (~10), self-upgrade/src/.../probes.py (1) |
| `degradation.sqlite` callsites | 36 | dormancy/{src/loam/.../config.py, src/.../state.py, tests/test_d8_state.py, docs/architecture.md, src/.../component.py docstring}, self-upgrade/src/.../paths.py, self-upgrade/src/.../snapshot.py, hands-off-lifecycle/research.md (historical), foundation-audit/research.md (historical), self-upgrade-framework/research.md (historical) |
| `degradation-config.yaml` / `degradation-config` | 24 | dormancy/src/loam/.../config.py, dormancy/tests/test_d10_garbage_false_positive.py, dormancy/docs/architecture.md, workspace-bootstrap/src/loam/.../adapters/{first_run_scaffold.py, telegram_interface.py}, workspace-bootstrap/tests/test_first_run_scaffold.py, two-modes-and-multi-workspace/{MASTER.md, C-state-file-migration.md} (historical plan-doc — preserved), hands-off-lifecycle/research.md (historical) |
| `graceful-degradation` (hyphenated, framework-tree) | ~476 raw matches; ~80 LIVE in framework/ + workspace-bootstrap deps | mostly path-references; many in historical plan-docs / proposals which are preserved per series convention |
| `graceful_degradation` (underscored, framework-tree) | ~101 raw matches; ~80 LIVE | mostly inside dormancy's own src + test files; rebrands wholesale via item 3 |

**Total estimated diff size:** ~250 callsite touches + 1 directory `git mv` + 1 inner-package `git mv` + 1 adapter file `git mv` + 1 component-docs subdir `git mv` + 4 pyproject.toml edits (dormancy + workspace-bootstrap + first-run-inventory.yaml + the new tools/loam-migrate-dormancy-config/pyproject.toml) + new 4-file migration helper (~150 LOC mirror of loam-migrate-host-config).

**What does NOT land in M1f** (deferred per series-master §2 + plan §6):

- **`pos-amend` CLI rename** → M1g per dispatcher ruling 1 (kept the rename-the-tool-while-using-it boundary clean).
- **`com.pos.orchestrator` launchd-label stragglers** — DEFERRED per M1e finding #1 + M1d finding #13 + dispatch-named §11 finding (recommended landing path: small follow-on M1c-corrective amendment OR M9-scrub).
- **The `DegradationStore` / `DegradationConfig` / `DegradationMode` / `DegradationSignal` / `DegradationChannel` / `DegradationComponent` Python class names.** These are the public-API symbols of the dormancy component; renaming them to `Dormancy*` is a separate semantic rename. Per `loam-rename-decisions.md` Tier-2 silence on internal-symbol renames + ODD §2.5 conservatism, **the symbol rename is OUT OF M1f's scope** (no AC names it; the AC family is module-path-shape-only). See §10 D-build.M1f.6 for the explicit method-decision.
- **`docs/rebuild/spec/pos-v2-rebuild-proposal.md`** and other `docs/rebuild/spec/*.md` historical narrative — preserved per Idea 10 / dispatcher M1e ruling 3.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** historical-narrative-heavy live docs — series-wide deferred.
- **Historical seal narratives** at `framework/graceful-degradation/seals/SEAL_COMMIT.*` (which moves to `framework/dormancy/seals/SEAL_COMMIT.*` under the directory rename via `git mv`). Content preserved verbatim per series convention; the file moves with the directory but its content (which describes pre-M1f sealed events) stays.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` — preserved per series convention. Plan-docs that mention `graceful-degradation` retain that wording (they describe pre-M1f events).
- **`docs/rebuild/plans/two-modes-and-multi-workspace/*.md`** historical plan-docs — preserved.
- **`docs/rebuild/components/{hands-off-lifecycle,foundation-audit,self-upgrade-framework}/research.md` etc. historical research-records** — preserved (per series convention; their references to `graceful-degradation` describe pre-M1f events).
- **The frozen self-upgrade release manifest `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml`** — preserved (release tag `pos-v2-v0.2.0`; this is a frozen pre-namespace-pivot snapshot pinned to a specific commit `dde03a7`; the LIVE `_build_manifest.py` re-generator IS in scope, but its frozen output for that release tag is not).
- **Repo directory rename** `ivers-corp-pos-v2` → `loam` — M9-deferred.
- **Path strings** `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred.

**Estimate:** 30–60 min AI-time per the duration rubric (single-component STRUCTURAL-rename category — narrower than M1e's 14-component STRUCTURAL pivot; M1e-calibrated single-component slice maps to the 15–30 min band). Pricing: rubric anchor is M1e's 75-min-per-component implicit (M1e was ~10–15 minutes per component on average across the structural diff). M1f involves more semantic touches per component (OTel cascade + config-file rename + migration helper) but only one component plus two consumer-side touchpoints. **Halt-trigger §10 fires at 90 min** (1.5× upper bound; the dispatcher's 15–30 min M1e-calibrated estimate doubled to allow for the migration-helper authoring + cross-component consumer touches).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1f closes the Tier-2 thematic rename slice. M1g closes CLI; M9 scrub closes residuals.
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — M1f stabilises the `loam.dormancy` Python import-path that any downstream consumer (the M2 partition manifest, future plugin authors) reads.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — `dormancy` is a substantively richer translation-vocabulary lift than `graceful-degradation`; the user reads `from loam.dormancy import …` and gets the exact botanical word for the system's behaviour (the system goes quiet when upstream is unavailable, resumes without damage when it returns) — single-syllable single-meaning. The translation-burden between user intent ("the system pauses when X breaks") and the import-path surface narrows.
- **AC.PO.2** (VALUE_PROPOSITION harness test) — `loam.dormancy` is a renamed harness primitive that future component authors compose against; the workspace-bootstrap adapter rename means future plugin authors register a contribution under `dormancy = …` instead of `graceful_degradation = …`. The harness toolkit picks up the cleaner name.

**Sealed-component fence (preliminary — see §4 ACs + §11 surface inventory):** **1 packaged component (dormancy, formerly graceful-degradation) plus 2 cross-component consumers (workspace-bootstrap, self-upgrade).** Plus universal admissions for `framework/tools/loam-migrate-dormancy-config/` (the new migration helper), `framework/first-run-inventory.yaml` (1 entry rename), `docs/rebuild/components/graceful-degradation/` → `docs/rebuild/components/dormancy/` (the docs subdir rename per series-master M1f row).

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose/pyproject/directory-mv changed in M1f's diff traces back to AC.RNM-1f.1 .. AC.RNM-1f.S below. Mechanical structural substitution (directory + package rename + import-path rewrite + OTel-second-segment cascade + config-file path cascade + migration helper authoring + adapter rename); no behaviour changes; no defensive-`if` admissions beyond the named §11 findings; no cross-mode-debt cascade beyond the named surfaces.

---

## 3. Three-lens analysis (abbreviated; series-master §4 covers cross-cutting)

- **Lens 1.** Pass. Preserves every existing Claude-native composition (PreToolUse hooks, MCP, skills, plugins). The `loam.bootstrap.contributions` entry-point group (renamed in M1e) gains the `dormancy` entry; future Claude-shape extensions compose against `loam.dormancy` instead of `loam.graceful_degradation`.
- **Lens 2.** Primary-persona pass. Single-vocabulary user surface (`dormancy` is the botanical word for the behaviour; one syllable). Harness pass — the `loam.dormancy` Python namespace becomes the canonical name future plugins reference for pause-when-upstream-unavailable composition.
- **Lens 3.** Mechanical structural-substitution work plus a small migration helper. Outcome-shaped ACs (post-rename grep counts; post-import-resolution checks via Python `python -c "from loam.dormancy import …"`; OTel `loam.dormancy.*` emission verification; per-host migration-helper four-case test). Method-shape (sed vs Edit, restructure-then-import vs import-then-restructure) is the builder's call inside the AC outcome bound.

---

## 4. Acceptance criteria — AC.RNM-1f.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.RNM-1f.1 — Directory + package rename

The on-disk shape post-M1f is:

```
framework/
└── dormancy/
    ├── pyproject.toml          # name = "loam-dormancy"; package-dir maps loam.dormancy = "src/loam/dormancy"
    ├── docs/
    │   └── architecture.md
    ├── tests/
    │   └── test_*.py           # 13 test files; SEAL_COMMIT sidecar
    └── src/
        └── loam/
            └── dormancy/        # the component's Python package
                ├── __init__.py
                ├── adapter.py
                ├── component.py
                ├── config.py
                ├── detection.py
                ├── errors.py
                ├── fsm.py
                ├── notification.py
                ├── observability.py
                ├── policy.py
                └── state.py
```

`framework/graceful-degradation/` does NOT exist post-M1f. `framework/dormancy/src/loam/graceful_degradation/` does NOT exist post-M1f.

`git mv` preserves history: `git mv framework/graceful-degradation framework/dormancy` then `git mv framework/dormancy/src/loam/graceful_degradation framework/dormancy/src/loam/dormancy`. Two `git mv` operations; rename-detection threshold preserves blame per the M1e D-build.M1e.2 precedent.

**Outcome:**
- `ls framework/dormancy/src/loam/dormancy/__init__.py` exists.
- `ls framework/graceful-degradation/` returns "No such file or directory".
- `python -c "from loam.dormancy import *"` (in the editable-install-refreshed venv) succeeds.
- `python -c "from loam.graceful_degradation import *"` raises `ImportError`.
- `git log --follow framework/dormancy/src/loam/dormancy/observability.py` returns the file's full pre-M1f history (rename-detection preserves blame across both `git mv` ops).

### AC.RNM-1f.2 — All `from loam.graceful_degradation` imports rebrand to `from loam.dormancy`

Every framework callsite (src + tests + scripts + docs/code-fragments) where `loam.graceful_degradation` is imported via:
- `from loam.graceful_degradation import …` (whole-package imports — most common shape)
- `from loam.graceful_degradation.<sub> import …` (submodule imports — adapter, errors, fsm, state, observability, etc.)
- `import loam.graceful_degradation` / `import loam.graceful_degradation.<sub>` (unqualified imports — none known at plan-authoring time, but defensively covered)

post-amendment reads `from loam.dormancy …` / `from loam.dormancy.<sub> …` / `import loam.dormancy[.<sub>]`.

**Plus `pyproject.toml` `dependencies = [...]` lists** for any component depending on `loam-graceful-degradation` rebrand to `loam-dormancy`. Plan-time inventory: only `framework/workspace-bootstrap/pyproject.toml` carries the dependency (`"loam-graceful-degradation"` → `"loam-dormancy"`).

**Outcome (positive):** `grep -rE 'from loam\.dormancy([. ]|$)|import loam\.dormancy([. ]|$)' framework/ docs/ --include="*.py" --include="*.md"` returns at LEAST 61 matches (the pre-rename total of `from loam.graceful_degradation` callsites in the in-scope surface).

**Outcome (negative):** `grep -rE 'from loam\.graceful_degradation([. ]|$)|import loam\.graceful_degradation([. ]|$)' framework/ --include="*.py"` returns 0 matches in the live (non-historical) surface.

### AC.RNM-1f.3 — OTel second-segment cascade `loam.degradation.*` → `loam.dormancy.*`

Per `loam-rename-decisions.md` Tier-2 + the M1d sub-plan's deferred-second-segment statement:

- All span names, event names, and span-attribute keys with second segment `degradation` rebase to `dormancy`. The 89 callsites at plan-authoring time include:
  - `loam.degradation.claude_call` (span name)
  - `loam.degradation.detection_event` (event name)
  - `loam.degradation.fsm_transition` (span name)
  - `loam.degradation.episode_started` / `.episode_resolved` (event names)
  - `loam.degradation.policy_decision`, `.probe_call`, `.notification_dispatched`, `.scope_lookup_failed`, `.reconcile_restore_failed` (event/span names)
  - Attribute keys: `loam.degradation.episode_id`, `.scope_id`, `.exception_class`, `.signal`, `.mode`, `.from_state`, `.to_state`, `.trigger`, `.mode_value`, `.paused_scope_ids`, etc.
  - Tracer name: `_TRACER = trace.get_tracer("loam.degradation", "0.1.0")` → `"loam.dormancy"` in dormancy's observability.py + the test fixtures that monkeypatch `_TRACER`.
- Schema entries in `framework/observability-aggregator/src/loam/observability_aggregator/schema.py`: any `TRACER_TO_COMPONENT` entry keyed `"loam.degradation"` rebases to `"loam.dormancy"`. (Plan-time grep finds the schema's component-name reference is in a comment string `"objective-tracker, orchestrator, graceful-degradation, plus test"` — that comment also rebrands.)

**Outcome:** `grep -rE 'loam\.degradation([. ]|$)' framework/ docs/ --include="*.py" --include="*.md"` returns 0 matches in the live (non-historical) surface. `pytest framework/dormancy/tests/test_d9_observability.py` PASSES (the canonical `loam.dormancy.*` span-name + attribute-key assertions now apply).

### AC.RNM-1f.4 — Config-file path cascade

`degradation.sqlite` → `dormancy.sqlite` (36 callsites) + `degradation-config.yaml` → `dormancy-config.yaml` (24 callsites) cascade in:

- `framework/dormancy/src/loam/dormancy/config.py` — default sqlite_path string + yaml-config-path docstring.
- `framework/dormancy/src/loam/dormancy/state.py` — module docstring.
- `framework/dormancy/tests/test_d8_state.py` — assertion `cfg.sqlite_path().name == "degradation.sqlite"` rebases.
- `framework/dormancy/tests/test_d10_garbage_false_positive.py` — narrative path string.
- `framework/dormancy/docs/architecture.md` — diagram + worked-example YAML sample + sqlite_path doc.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — file-template entry `"degradation-config.yaml": _DEGRADATION_YAML` → `"dormancy-config.yaml": _DORMANCY_YAML` (the YAML template constant `_DEGRADATION_YAML` rebrands to `_DORMANCY_YAML` for naming consistency); file-content string.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/telegram_interface.py` — comment `# degradation-config default` rebases.
- `framework/workspace-bootstrap/tests/test_first_run_scaffold.py` — string-list literal containing `"degradation-config.yaml"` rebases.
- `framework/self-upgrade/src/loam/self_upgrade/paths.py` — docstring + `degradation.sqlite` returned-path constant (live runtime reference; rename matters).
- `framework/self-upgrade/src/loam/self_upgrade/snapshot.py` — table-row docstring entry.

**Outcome:** `grep -rE 'degradation\.sqlite|degradation-config' framework/ --include="*.py" --include="*.md" --include="*.yaml"` returns 0 matches in the live (non-historical) surface. The `~/.loam/dormancy.sqlite` and `~/.loam/dormancy-config.yaml` defaults are the new canonical paths.

### AC.RNM-1f.5 — Per-host migration helper for the config-file rename

A new tool at `framework/tools/loam-migrate-dormancy-config/` mirrors the `framework/tools/loam-migrate-host-config/` shape (the M1b precedent — directory rename `~/.pos/` → `~/.loam/`). The new helper performs the file-rename within `~/.loam/`:

- `~/.loam/degradation.sqlite` → `~/.loam/dormancy.sqlite` (with WAL + SHM siblings).
- `~/.loam/degradation-config.yaml` → `~/.loam/dormancy-config.yaml`.

Four-case logic per the M1b precedent (`loam-migrate-host-config/migrate.py`):

1. `OLD_EXISTS_NEW_ABSENT`: rename. Single `os.rename()` per file pair (sqlite + yaml independently — both checked).
2. `NEW_EXISTS_OLD_ABSENT`: already migrated; no-op.
3. `NEITHER`: nothing to migrate; no-op (fresh machine).
4. `BOTH`: conflict; halt without modification; surface guidance.

Idempotent: case-1 followed by re-run hits case 2.

**SQLite WAL/SHM cascade.** SQLite-WAL-mode databases carry sibling files `<db>.sqlite-wal` and `<db>.sqlite-shm`. The migration helper renames the WAL + SHM siblings concurrently with the main file when present; missing sibling files are tolerated (they're regenerated on next sqlite open).

**Outcome:**
- `framework/tools/loam-migrate-dormancy-config/{pyproject.toml, src/loam_migrate_dormancy_config/{__init__.py, __main__.py, cli.py, migrate.py}, tests/test_migrate.py, README.md}` exist post-build.
- `pip install -e ./framework/tools/loam-migrate-dormancy-config` succeeds editable.
- `python -m loam_migrate_dormancy_config --help` returns usage; `python -m loam_migrate_dormancy_config` exits 0 on a fresh tree (case 3); reports MIGRATED on a tree with `~/.loam/degradation.sqlite` only (case 1); reports ALREADY_MIGRATED on a tree with `~/.loam/dormancy.sqlite` only (case 2); reports CONFLICT and exits non-zero on a tree with both (case 4).
- `pytest framework/tools/loam-migrate-dormancy-config/tests/test_migrate.py` passes (test cases for all four states).

### AC.RNM-1f.6 — Workspace-bootstrap adapter rename + entry-point row update

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/graceful_degradation.py` → `adapters/dormancy.py` via `git mv`.
- Inside the file: class `GracefulDegradationContribution` rebrands to `DormancyContribution` (this IS in M1f's scope — it's the workspace-bootstrap adapter, not the dormancy component's public API; the adapter is workspace-bootstrap's own surface). The `name="graceful_degradation"` contribution-name string rebrands to `name="dormancy"`.
- `framework/workspace-bootstrap/pyproject.toml` `[project.entry-points."loam.bootstrap.contributions"]`: `graceful_degradation = "loam.workspace_bootstrap.adapters.graceful_degradation:GracefulDegradationContribution"` → `dormancy = "loam.workspace_bootstrap.adapters.dormancy:DormancyContribution"`. Also the dependency `"loam-graceful-degradation"` → `"loam-dormancy"`.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/host.py`: docstring + `self.graceful_degradation: Any = None` → `self.dormancy: Any = None`.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`: bootstrap.yaml template entries (`name: graceful_degradation`, `module: loam.workspace_bootstrap.adapters.graceful_degradation`) rebrand.
- `framework/workspace-bootstrap/tests/{test_first_run_scaffold.py, test_integration_foundational.py, test_extension_protocol.py, test_bootstrap_unification.py}`: `"graceful_degradation"` string-literal references rebase to `"dormancy"`.

**Outcome:**
- `python -c "import importlib.metadata; print([ep.name for ep in importlib.metadata.entry_points(group='loam.bootstrap.contributions')])"` returns a list containing `"dormancy"` (NOT `"graceful_degradation"`).
- `pytest framework/workspace-bootstrap/tests/` passes (post-editable-install refresh).

### AC.RNM-1f.7 — Self-upgrade probes + manifest-builder cascade

- `framework/self-upgrade/src/loam/self_upgrade/probes.py`: docstring `graceful-degradation: degradation.state.DegradationStore.snapshot_probe()` rebrand + section comment `# ---- graceful-degradation ----` rebrand + `from loam.graceful_degradation.state import DegradationStore` import rebrand to `from loam.dormancy.state import DegradationStore` (note: class name `DegradationStore` PRESERVED per §10 D-build.M1f.6 ruling — symbol rename out of M1f scope).
- `framework/self-upgrade/manifests/_build_manifest.py`: `"graceful-degradation"` in the component-name list → `"dormancy"`.
- `framework/self-upgrade/tests/test_probes.py`: `from loam.graceful_degradation.state` → `from loam.dormancy.state`.
- **Out of scope:** the frozen `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml` release manifest (preserves pre-namespace-pivot path strings; pinned to `commit_sha: dde03a7427037e53e5eb2d2d02e597c3b000f752` — frozen historical artefact).

**Outcome:** `pytest framework/self-upgrade/tests/test_probes.py` passes (the dormancy import resolves post-rename); `python framework/self-upgrade/manifests/_build_manifest.py --help` succeeds (or runs against the post-M1f tree — the `_build_manifest.py` regenerator is a one-shot script, may or may not be exercised in M1f; halt-trigger §8.5 fires only if it errors).

### AC.RNM-1f.8 — Component docs subdir rename (per series-master M1f row)

`docs/rebuild/components/graceful-degradation/` → `docs/rebuild/components/dormancy/` via `git mv`. Files moved as part of the directory rename: `component.md`, `proposal.md`, `research-plan.md`, `research.md`. The 13-allowlist test `framework/graceful-degradation/tests/test_no_sealed_amendments.py` (which becomes `framework/dormancy/tests/test_no_sealed_amendments.py` under the directory rename) carries the literal allowed-prefix `docs/rebuild/components/graceful-degradation/` — that allowlist entry rebases to `docs/rebuild/components/dormancy/` as part of the test-fixture content edit.

**Method-decision (D-build.M1f.5 in §10):** content INSIDE the renamed component-record docs is preserved verbatim under the rename — the prose describes pre-M1f research / proposal events using `graceful-degradation` vocabulary, which IS the historical record. The `git mv` operates on the directory shell, not the inner prose. This matches the series convention (`docs/rebuild/components/<comp>/{research.md,research-plan.md,brief.md,component.md}` historical preservation) for the inner content while honouring the series-master M1f-row directive that the directory shell (the path, not the prose) follow the rename.

**Outcome:**
- `ls docs/rebuild/components/dormancy/component.md` exists.
- `ls docs/rebuild/components/graceful-degradation/` returns "No such file or directory".
- `git log --follow docs/rebuild/components/dormancy/component.md` returns the full pre-M1f history.
- The four files' contents are byte-identical pre-vs-post (`git diff <baseline>..HEAD -- docs/rebuild/components/dormancy/` shows ONLY the directory move, no content edits).

### AC.RNM-1f.9 — `framework/first-run-inventory.yaml` component-name rebrand

The single entry `- "graceful-degradation"` in `framework/first-run-inventory.yaml`'s components list rebases to `- "dormancy"`. This is a 1-line edit in a live workspace-bootstrap-consumed YAML.

**Outcome:** `grep -nE 'graceful-degradation' framework/first-run-inventory.yaml` returns 0 matches.

### AC.RNM-1f.S — Sealed-component fence narrows to dormancy + 2 cross-component consumers

3-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; M1g closes the CLI rename). The amendment manifest YAML lists 3 components: dormancy (renamed), workspace-bootstrap, self-upgrade. Plus universal admissions for `framework/tools/loam-migrate-dormancy-config/` (the new migration helper), `docs/rebuild/components/dormancy/` (the renamed docs subdir), `framework/first-run-inventory.yaml`, and the plan-doc + manifest YAML.

The `seal_diff` `allowed_prefixes` admit `framework/dormancy/`, `framework/graceful-degradation/` (admits the pre-rename source paths in the rename diff window), `framework/workspace-bootstrap/`, `framework/self-upgrade/`, and the universal paths.

**Per-component touched-test scope:** narrow to touched files. Per `feedback_amendment_dispatch_speedups`, M1f skips pre-seal full-suite rerun. Each sealed component's `tests/test_no_sealed_amendments.py` runs as part of `pos-amend apply` verification. The seal-diff fence test for AC.RNM-1f.S is the primary check (verifies the fence isn't reaching beyond dormancy + 2 consumers + universals).

**Outcome:** `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention; 3 per-component sidecars all advance; `pytest framework/{dormancy,workspace-bootstrap,self-upgrade}/tests/test_no_sealed_amendments.py` PASSES; HOL `test_cross_cutting.py` PASSES.

### AC.RNM-1f.10 — No work outside the named surfaces (negative AC)

The amendment's git-diff includes ZERO touches outside:

- `framework/graceful-degradation/...` (admits the pre-rename source paths in the rename diff window).
- `framework/dormancy/...` (the post-rename target).
- `framework/workspace-bootstrap/{pyproject.toml, src/loam/workspace_bootstrap/{host.py, adapters/{graceful_degradation.py → dormancy.py, first_run_scaffold.py, telegram_interface.py}}, tests/{test_first_run_scaffold.py, test_integration_foundational.py, test_extension_protocol.py, test_bootstrap_unification.py}}`.
- `framework/self-upgrade/{src/loam/self_upgrade/probes.py, manifests/_build_manifest.py, tests/test_probes.py}`.
- `framework/observability-aggregator/src/loam/observability_aggregator/{__init__.py, schema.py}` (1 comment-line rebrand each, naming `graceful-degradation` in a component-list comment).
- `framework/tools/loam-migrate-dormancy-config/...` (the new migration helper).
- `framework/first-run-inventory.yaml` (1 entry rename).
- `docs/rebuild/components/graceful-degradation/...` → `docs/rebuild/components/dormancy/...` (the directory rename per AC.RNM-1f.8).
- The plan-doc + manifest YAML under `docs/rebuild/plans/`.

**Permitted ZERO surfaces (no edits expected):**

- No env-var or per-host-config-dir changes — M1b closed those.
- No launchd-label changes — M1c closed those (item 8 deferred).
- No first-segment-`pos.` OTel root changes — M1d closed those.
- No `pos.bootstrap.contributions` entry-point group references — M1e closed those.
- No `pos-amend` CLI references in code — M1g.
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites — M9.
- No `framework/<comp>/seals/SEAL_COMMIT.*` historical-narrative edits (the file MOVES under the directory rename via `git mv` but its content stays verbatim).
- No `docs/rebuild/plans/*.md` historical method-record edits beyond this plan-doc + manifest YAML.
- No `docs/rebuild/components/{hands-off-lifecycle,foundation-audit,self-upgrade-framework}/research.md` etc. historical-research edits (they reference pre-M1f events using the `graceful-degradation` vocabulary, which is the historical record).
- No `docs/rebuild/spec/*.md` content or filename edits.
- No `docs/rebuild/plans/two-modes-and-multi-workspace/*.md` historical plan-doc edits.
- No `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml` content edits (frozen release manifest).
- No `Degradation*` Python class symbol renames (out of M1f scope per §10 D-build.M1f.6).
- No HC#4 byte-content sample SHA changes (plan-time pre-verification — see §11 finding #2).

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Nine outcome-named behaviours (directory + package rename, import rebrand, OTel cascade, config-file cascade, migration helper, workspace-bootstrap adapter rename, self-upgrade consumer rebrand, docs subdir rename, first-run-inventory entry rename) → nine positive ACs (AC.RNM-1f.1 .. AC.RNM-1f.9). Plus the seal-fence AC (AC.RNM-1f.S) and the negative scope AC (AC.RNM-1f.10). Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §8.6.

---

## 5. Hard constraints (M1f-specific; series-wide constraints from master §5 inherit)

- **Single-component-rename + cascade-only diff with hard cutover.** AC.RNM-1f.10 is the structural fence — `git mv` directory + inner-package + adapter file + docs subdir + import-path rebrand + OTel-second-segment cascade + config-file cascade + new migration helper + 3-component manifest. No other surfaces.
- **Hard cutover.** Per series-master §1 D-RNM.3: no `from loam.graceful_degradation` fallback shim; no compat module re-exporting; no dual-namespace OTel emission; no dual entry-point group registration. Pre-public release; zero existing external consumers.
- **Editable install refresh.** After the directory + package rename, run `pip install -e ./framework/dormancy` to refresh the `__editable__.loam_dormancy-0.1.0.pth` file in the venv. Workspace-bootstrap also needs `pip install -e ./framework/workspace-bootstrap` to refresh the entry-point group registration (the `entry_points.txt` in workspace-bootstrap's egg-info regenerates). Order: `pip install -e ./framework/dormancy` (no inter-component dep updates); `pip install -e ./framework/workspace-bootstrap` (depends on `loam-dormancy`); `pip install -e ./framework/tools/loam-migrate-dormancy-config` (new helper). Halt-trigger §8.1 fires on any non-zero return.
- **`pos-amend apply` runs BEFORE the seal commit** (`feedback_dispatch_explicit_pos_amend_apply`) — invoked under its CURRENT name `pos-amend` since M1f doesn't rename the CLI (the rename is M1g per series-master ladder note 5).
- **`git mv` for directory + package + adapter + docs-subdir renames.** Preserves history per Git Safety Protocol; rename-detection threshold preserves blame.
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`). Corrective commits are NEW commits.
- **HC#4 byte-content sample retire-and-rebaseline NOT EXPECTED at M1f.** Per §11 finding #2 + M1e §11 finding #3 enumeration: NONE of the M1e-rebaselined sample files reside under `framework/graceful-degradation/`. M1f's directory + package rename should NOT touch any HC#4 sample file. Halt-trigger §8.4 fires only if an unexpected sample-file SHA change emerges.
- **Test scope is narrow.** Per `feedback_amendment_dispatch_speedups`, M1f skips pre-seal full-suite rerun. Touched-test rerun + per-component `test_no_sealed_amendments.py` is the methodology-aligned narrow verification.
- **Historical preservations.** `docs/rebuild/plans/*.md` (other than this plan-doc + manifest YAML), `framework/dormancy/seals/SEAL_COMMIT.*` (content preserved; file moves with directory), `docs/rebuild/components/{hands-off-lifecycle, foundation-audit, self-upgrade-framework}/research.md` etc., `docs/rebuild/components/dormancy/{research.md,research-plan.md,component.md,proposal.md}` content (path moves; content preserved), `docs/rebuild/plans/two-modes-and-multi-workspace/*.md`, `docs/rebuild/spec/*.md`, and `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml` files preserved verbatim per series convention.
- **Tools-tree pyproject for the new migration helper.** `framework/tools/loam-migrate-dormancy-config/pyproject.toml` follows the M1b helper precedent (loam-migrate-host-config) — package layout `src/loam_migrate_dormancy_config/` (the helper itself is a tool, not a framework component; tools-tree namespace pivot is M1g/FIDRAFT-deferred per M1e §6).

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full deferred-list. Re-named here for ODD §2.5 compliance.)

- **`pos-amend` CLI rename → `loam amend`** — DEFERRED to M1g per series-master ladder note 5.
- **Tools-tree namespace pivot** (`framework/tools/<tool>/src/<tool_pkg>/...` for non-loam-prefixed tools) — out of scope per M1e §6; absorbed by M1g (pos-amend) or follow-on per FIDRAFT.
- **`com.pos.orchestrator` launchd-label stragglers** — DEFERRED per M1e finding #1.
- **`Degradation*` Python class symbol renames** (`DegradationStore`, `DegradationConfig`, `DegradationMode`, `DegradationSignal`, `DegradationChannel`, `DegradationComponent`, `GracefulDegradationContribution` is RENAMED in AC.RNM-1f.6 because it's the workspace-bootstrap adapter, not the dormancy component's public API) — out of M1f scope per §10 D-build.M1f.6 (the `loam-rename-decisions.md` Tier-2 ruling is silent on internal symbol renames; ODD §2.5 conservatism keeps the AC family narrow to module-path-shape; symbol rename is a separate semantic decision deferred to a follow-on amendment OR FIDRAFT capture).
- **Dependent-component pyproject `dependencies = [...]` updates beyond workspace-bootstrap.** Plan-time grep finds workspace-bootstrap is the SOLE inter-component dependent on `loam-graceful-degradation`. Other components do not depend on it.
- **Repo directory rename** `ivers-corp-pos-v2` → `loam` — M9-deferred.
- **Path strings** `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred.
- **Workspace-side `<workspace>/.pos/` sentinel directory constants** — series-wide deferred.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** historical-narrative-heavy live docs — series-wide deferred.
- **Historical seal narratives** at `framework/dormancy/seals/SEAL_COMMIT.*` (content) — preserved.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` (other than this plan-doc + manifest YAML) — preserved.
- **Historical component-record docs** at `docs/rebuild/components/{hands-off-lifecycle,foundation-audit,self-upgrade-framework,...}/{research.md,research-plan.md,brief.md,component.md}` — preserved (their references to `graceful-degradation` describe pre-M1f events).
- **Historical component-record docs INSIDE the renamed `docs/rebuild/components/dormancy/` directory** — content preserved verbatim under the rename per AC.RNM-1f.8 (the `git mv` operates on the directory shell, not the inner prose).
- **`docs/rebuild/spec/*.md` (including `pos-v2-rebuild-proposal.md`)** — preserved.
- **`docs/rebuild/plans/two-modes-and-multi-workspace/*.md`** historical plan-docs — preserved.
- **Frozen self-upgrade release manifest `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml`** — preserved.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`; `git status --short` shows working tree clean (only the pre-existing `personas/` untracked item remains). Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to M1e's §14 backfill commit `820fd84` (or HEAD if subsequent doc-only commits land first; verify by `git log --oneline | head -5`).
3. **M1f sub-plan + manifest commit.** This plan-doc + a manifest YAML at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1f.manifest.yaml` per the established M1a..M1e precedent shape.
4. **Phase A — Directory rename.** `git mv framework/graceful-degradation framework/dormancy`. Then `git mv framework/dormancy/src/loam/graceful_degradation framework/dormancy/src/loam/dormancy`.
5. **Phase B — Component docs subdir rename.** `git mv docs/rebuild/components/graceful-degradation docs/rebuild/components/dormancy`. Content preserved verbatim under the rename per AC.RNM-1f.8.
6. **Phase C — Workspace-bootstrap adapter file rename.** `git mv framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/graceful_degradation.py framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/dormancy.py`. Then surgical Edit on the adapter file content (class name `GracefulDegradationContribution` → `DormancyContribution`; contribution `name="graceful_degradation"` → `name="dormancy"`).
7. **Phase D — pyproject.toml restructure.**
   - `framework/dormancy/pyproject.toml`: `name = "loam-graceful-degradation"` → `name = "loam-dormancy"`; setuptools `package-dir` + `packages` rebrand from `loam.graceful_degradation` to `loam.dormancy`; description string rebrand if currently mentioning "Graceful-degradation policy layer".
   - `framework/workspace-bootstrap/pyproject.toml`: dependency `"loam-graceful-degradation"` → `"loam-dormancy"`; entry-point row `graceful_degradation = "loam.workspace_bootstrap.adapters.graceful_degradation:GracefulDegradationContribution"` → `dormancy = "loam.workspace_bootstrap.adapters.dormancy:DormancyContribution"`.
8. **Phase E — Code import rebrand.** Mechanical rename across every framework callsite:
   - `from loam.graceful_degradation` → `from loam.dormancy` (61 callsites).
   - `from loam.graceful_degradation.<sub>` → `from loam.dormancy.<sub>`.
   - `import loam.graceful_degradation` → `import loam.dormancy` if any (none known at plan-authoring time).
9. **Phase F — OTel second-segment cascade.** `loam.degradation` → `loam.dormancy` across all 89 callsites (mostly in dormancy's own observability.py + tests + architecture.md; plus 1 schema-comment in observability-aggregator). Mechanical sed-style for bulk where the regex is unambiguous; surgical Edit for high-volume files.
10. **Phase G — Config-file path cascade.** `degradation.sqlite` → `dormancy.sqlite` (36 callsites); `degradation-config.yaml` → `dormancy-config.yaml` (24 callsites). Mechanical bulk substitution.
11. **Phase H — Workspace-bootstrap host.py + adapter consumers.** `host.py` `self.graceful_degradation: Any` → `self.dormancy: Any` + docstring entry. `first_run_scaffold.py` template-string entries (`name: graceful_degradation`, `module: loam.workspace_bootstrap.adapters.graceful_degradation`, `_DEGRADATION_YAML` constant) rebrand; `telegram_interface.py` comment line rebrand. Test fixtures (`test_first_run_scaffold.py`, `test_integration_foundational.py`, `test_extension_protocol.py`, `test_bootstrap_unification.py`) string-literal references rebrand.
12. **Phase I — Self-upgrade consumer rebrand.** `probes.py` (3 callsites: docstring + section comment + import); `_build_manifest.py` (1 callsite: component-name list); `test_probes.py` (1 callsite: import).
13. **Phase J — Observability-aggregator schema-comment rebrand.** `framework/observability-aggregator/src/loam/observability_aggregator/__init__.py` and `schema.py` carry comment-line references to `graceful-degradation` in component-name lists; rebrand to `dormancy`.
14. **Phase K — `framework/first-run-inventory.yaml` component-name rebrand.** Single 1-line edit.
15. **Phase L — Migration helper authoring (item 7).** Author `framework/tools/loam-migrate-dormancy-config/` — pyproject.toml + `src/loam_migrate_dormancy_config/{__init__.py, __main__.py, cli.py, migrate.py}` + `tests/test_migrate.py` + README.md. Mirror the M1b `loam-migrate-host-config` shape; substitute the rename target (file rename within `~/.loam/` instead of dir rename `~/.pos/` → `~/.loam/`). The four-case logic is identical pattern; the file-rename includes WAL/SHM siblings for the SQLite case.
16. **Phase M — Editable-install refresh.** `pip install -e ./framework/dormancy` → 0; `pip install -e ./framework/workspace-bootstrap` → 0; `pip install -e ./framework/tools/loam-migrate-dormancy-config` → 0. Verify `python -c "from loam.dormancy import *"` succeeds; `python -c "from loam.graceful_degradation import *"` raises ImportError; `python -c "import importlib.metadata; print([ep.name for ep in importlib.metadata.entry_points(group='loam.bootstrap.contributions')])"` returns a list containing `dormancy` and NOT `graceful_degradation`.
17. **Phase N — Test sweep (touched files).** `pytest framework/dormancy/tests/`; `pytest framework/workspace-bootstrap/tests/`; `pytest framework/self-upgrade/tests/test_probes.py`; `pytest framework/tools/loam-migrate-dormancy-config/tests/`. Halt-trigger §8.7 on non-zero.
18. **Phase O — Feature commit.** Single feature commit carrying all of Phases A–N. Commit message names the M1f slug, the AC family (AC.RNM-1f.1–AC.RNM-1f.S), the 3-component fence, the new migration helper, and the series-master pointer.
19. **Phase P — pos-amend apply.** Run `pos-amend apply` against the manifest. Verify clean apply. **`pos-amend apply` BEFORE the seal commit per FIDRAFT note from amendment #41 + dispatch §Acceptance shape.** Pos-amend invoked under its current name (M1f doesn't rename it).
20. **Phase Q — Apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `pos-amend apply` convention.
21. **Phase R — Seal-diff fence verification.** AC.RNM-1f.S + AC.RNM-1f.10 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named surfaces. Verify each component's `pytest framework/<comp>/tests/test_no_sealed_amendments.py` passes; HOL `test_cross_cutting.py` passes.
22. **Phase S — `pos-amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below). The seal commit narrative cites the AC family, the 3-component fence (dormancy + workspace-bootstrap + self-upgrade), the new migration helper, the OTel second-segment cascade, the config-file path cascade, and the deferred items (M1g, launchd-label stragglers, symbol rename).

Phases A–C are the structural-rename phases. Phases D + L form the configuration / authoring delta. Phases E–K are mechanical-substitution. Phases O–S are commit + seal mechanics.

---

## 8. Halt triggers (M1f-specific; series-wide triggers from master §7 inherit)

Per the dispatch's halt-and-surface clause + dispatch-named §Halt-and-surface enumeration:

1. **Editable-install failure post-restructure.** `pip install -e ./framework/dormancy` returns non-zero. Surface with the failing component name + the exit code + the captured stderr. Recovery: rollback the `git mv` ops, fix pyproject, retry.
2. **A consumer of `loam.graceful_degradation` that didn't get rebranded** (cross-component import). Halt; surface specific file/line; the M1e namespace pivot is the package whose pre-M1f shape was `loam.graceful_degradation`; M1f's import-rebrand AC is exhaustive over framework callsites; any miss is a cross-component-debt cascade.
3. **HOL `test_d1_byte_content_match.py` SHA regression.** Per §11 finding #2: NONE of the M1e-rebaselined samples reside under `framework/graceful-degradation/`. If any sample-file SHA changes during M1f's directory rename, that's a frozen-baseline breach beyond what this AC family handles. Halt; surface the unenumerated sample.
4. **ODD §2.5 violations encountered in surrounding code.** Halt; do NOT silently extend. Surface for owner ruling on whether to fix in-band, defer, or reshape M1f's scope.
5. **`pos-amend` automation hits a gap on the structural surface.** Manifest-validation false-positive on the 3-component fence; rename-detection failure for the directory `git mv` cascade; SHA-backfill mis-target. Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
6. **The migration helper for config-file rename has edge cases.** Specifically: WAL + SHM sibling-file handling under partial-state (case where `degradation.sqlite` exists but `degradation.sqlite-wal` is missing — the helper tolerates this); permission errors during `os.rename`; case where `~/.loam/` doesn't exist (case 3 NOTHING_TO_MIGRATE handles this). Halt-and-surface if a fifth case emerges that the M1b precedent's four-case logic doesn't cover.
7. **AC prefix P or any sealed AC of graceful-degradation needs renaming despite the "P stays" ruling.** Per `loam-rename-decisions.md` Tier-2: AC prefix `P` (Policy) STAYS. If M1f's surface uncovers a sealed AC of graceful-degradation that needs P-prefix rename despite the ruling, halt and surface specific AC (e.g. P3.X tests in dormancy/tests/test_d4_policy.py, etc. — these stay verbatim per the ruling).
8. **The orchestrator's pause/resume hooks that bind into graceful-degradation.** Per the dispatcher's halt-and-surface item 8: the wire-graceful-degradation task #10 in the dispatcher's task list may not be in place yet; if so, M1f just renames the unbound surface. Pre-build verification at plan-authoring time (`grep -rE "pause_activation|resume_activation" framework/orchestrator/`): the pause/resume hooks ARE present in `framework/orchestrator/src/loam/orchestrator/` (M1e pivoted them under the loam.* namespace) and dormancy's `component.py` calls them; **the binding IS in place**. M1f renames the dormancy side; orchestrator's pause/resume API stays verbatim (no second-segment rename required for orchestrator's hooks).
9. **Wall-clock exceeds 90 min** (M1f is rubric-priced 30–60 min midpoint 45 min; M1e-calibrated 15–30 min; halt-trigger fires at 1.5× upper bound of the rubric range to allow for migration-helper authoring + cross-component touches). Halt with current-state report; dispatcher triages continue / split-further / pause.
10. **Pre-existing test fails post-rename** (NOT a `loam.dormancy` ImportError — those mean the rename + editable install didn't complete; that's halt-trigger §1). Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis.
11. **A `dormancy` identifier already in use.** Pre-build verification at plan-authoring time: `grep -rE "dormancy" framework/ docs/` returns 0 hits in framework/ live surface and only hits in `docs/rebuild/plans/loam-rename-decisions.md` + master plan + sub-plans (which name the rename target). NO collision. Halt-trigger fires only if a NEW collision emerges during the rename.
12. **A hard-cutover violation.** Builder accidentally adds a fallback shim re-exporting `from loam.graceful_degradation` or registering a dual entry-point group. Halt; remove the shim.
13. **A frozen-record file rebrand.** Builder accidentally rebrands `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml` content or path-strings. Halt; revert; the file is preserved per §6.
14. **Symbol-rename scope creep.** Builder accidentally rebrands `DegradationStore` / `DegradationConfig` / `DegradationMode` / `DegradationSignal` / `DegradationChannel` / `DegradationComponent` Python class names (NOT the workspace-bootstrap adapter `GracefulDegradationContribution`, which IS in scope per AC.RNM-1f.6). Per §10 D-build.M1f.6, symbol renames are out of M1f scope. Halt; revert; the symbol rename is a separate amendment.

---

## 9. Risks (M1f-specific)

1. **Editable-install cascade failure.** `pip install -e ./framework/dormancy` failure (e.g. setuptools doesn't discover under the new pyproject) leaves dormancy non-importable until fixed. Mitigation: §5 hard-constraint editable-install order + §8 halt-trigger §1 + manual recovery (rollback `git mv`, fix pyproject, retry).
2. **Bare-import collision.** `from loam.graceful_degradation` is unambiguous (the M1e namespace pivot landed `loam.*` as the framework's single import-prefix). No bare-name collision risk like M1e Phase C had. Mitigation: not applicable; M1f's import-rebrand regex `from loam\.graceful_degradation` is unambiguous.
3. **OTel cascade misses a literal.** 89 plan-time callsites; if a literal `loam.degradation` appears in a path that grep didn't match (e.g. a test fixture with a string-concatenation), the OTel cascade misses it. Mitigation: post-cascade `grep -rE "loam\.degradation" framework/ --include="*.py" --include="*.md"` returning 0 is the AC.RNM-1f.3 outcome check; fail-fast.
4. **Migration helper edge case.** SQLite WAL/SHM sibling-file handling on partial states; permission errors; non-default `~/.loam/` location. Mitigation: §8 halt-trigger §6 + four-case test coverage in `tests/test_migrate.py` (mirror of M1b's test_migrate.py — also covers WAL/SHM presence/absence).
5. **Cross-component consumer miss.** workspace-bootstrap + self-upgrade are the only known cross-component consumers at plan-authoring time. Mitigation: post-rename `grep -rE "graceful_degradation|graceful-degradation" framework/ --include="*.py" --include="*.toml" --include="*.yaml"` excluding the historical-record paths returns 0; fail-fast on AC.RNM-1f.10 fence verification.
6. **Component docs subdir rename DEVIATES from series convention.** Per series convention, `docs/rebuild/components/<comp>/` historical records are preserved. Per series-master M1f row, `docs/rebuild/components/graceful-degradation/` → `docs/rebuild/components/dormancy/` IS in scope. Per §10 D-build.M1f.5 ruling: directory-shell move only (content preserved verbatim). Risk: builder accidentally edits inner prose during the rename, breaking the historical record. Mitigation: the `git mv` operates on the directory shell; content edits are explicitly out of scope for the docs subdir rename per AC.RNM-1f.8.
7. **`Degradation*` symbol rename scope creep.** `DegradationStore`, `DegradationConfig`, `DegradationMode`, `DegradationSignal`, `DegradationChannel`, `DegradationComponent` are Python class symbols in `loam.dormancy`. Renaming them to `Dormancy*` is OUT OF M1f's scope per §10 D-build.M1f.6. Risk: builder decides "while we're here..." and renames symbols. Mitigation: §8 halt-trigger §14; AC family is explicitly module-path-shape-only.
8. **Wall-clock blow-out.** Plan-priced 30–60 min midpoint 45 min (M1e-calibrated 15–30 min); migration-helper authoring is the principal source of variance (~20 min if mirror-from-M1b goes cleanly; 60+ min if WAL/SHM edge cases need new-shape thought). Mitigation: §8 halt-trigger §9 fires at 90 min.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per series master §1, all three D-RNM rulings (split, namespace shape, no compat window) closed at owner-ruling time. Series-master M1f row already records the directory + package + OTel + config-files + docs-subdir + workspace-bootstrap-adapter cascade scope. The migration-helper requirement is dispatch-named (§Objective bullet 7).

**Builder's calls within ACs (NOT requiring owner ruling):**

- **D-build.M1f.1 — `git mv` mechanism for directory rename.** Builder's call within AC.RNM-1f.1: (a) two-step (outer dir rename → inner package rename); (b) single `git mv` chain. Recommendation: option (a) — `git mv framework/graceful-degradation framework/dormancy` followed by `git mv framework/dormancy/src/loam/graceful_degradation framework/dormancy/src/loam/dormancy`. Two-step is cleaner because rename-detection runs over both moves independently; blame is preserved at 95–100% similarity for all files unchanged in content.
- **D-build.M1f.2 — pyproject project name shape.** Builder's call within AC.RNM-1f.1: `name = "loam-dormancy"` per the M1e D-build.M1e.1 hyphenated-prefix convention. PEP 503 normalises both forms; the hyphenated form reads cleaner at `pip install` time and matches existing pyproject conventions.
- **D-build.M1f.3 — Migration helper four-case logic vs five-case.** Builder's call within AC.RNM-1f.5. The M1b precedent uses four cases (OLD_EXISTS_NEW_ABSENT, NEW_EXISTS_OLD_ABSENT, NEITHER, BOTH). For M1f's two-file rename (sqlite + yaml), each file is checked independently → 4 cases per file. Recommendation: per-file four-case logic with combined reporting. The MigrationResult dataclass carries per-file status (sqlite_status, yaml_status) + an overall is_clean property.
- **D-build.M1f.4 — Migration helper SQLite WAL/SHM sibling handling.** Builder's call within AC.RNM-1f.5. Recommendation: when `degradation.sqlite` is renamed to `dormancy.sqlite`, ALSO rename `degradation.sqlite-wal` → `dormancy.sqlite-wal` and `degradation.sqlite-shm` → `dormancy.sqlite-shm` if the sibling files exist. Missing siblings are tolerated (they're regenerated on next sqlite open). Implementation: three `os.rename()` calls with try/except FileNotFoundError on the WAL/SHM siblings.
- **D-build.M1f.5 — Component docs subdir rename method.** Builder's call within AC.RNM-1f.8. Series convention preserves `docs/rebuild/components/<comp>/{research,research-plan,brief,component}.md` as historical records. Series-master M1f row OVERRIDES the convention for THIS component only. Recommendation: directory-shell `git mv` only; inner content preserved verbatim under the rename. The `git mv` operates on the directory shell; content edits are explicitly out of scope for the docs subdir rename. The `git log --follow` per file returns full pre-M1f history.
- **D-build.M1f.6 — `Degradation*` Python class symbol rename scope.** Builder's call within AC.RNM-1f.2. Per `loam-rename-decisions.md` Tier-2: directory + package + OTel + config-files cascade. The ruling is silent on internal class-symbol renames. Per ODD §2.5 conservatism, the AC family is module-path-shape-only; symbol renames are NOT named in any AC. Recommendation: `Degradation*` Python class symbols (DegradationStore, DegradationConfig, DegradationMode, DegradationSignal, DegradationChannel, DegradationComponent) are PRESERVED verbatim in M1f. The workspace-bootstrap adapter class `GracefulDegradationContribution` IS rebranded to `DormancyContribution` per AC.RNM-1f.6 because it's the workspace-bootstrap adapter (workspace-bootstrap's own surface), not the dormancy component's public API. The symbol rename of `Degradation*` → `Dormancy*` is a separate semantic decision deferred to a follow-on amendment OR FIDRAFT capture (record at build-time in §11 finding).

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(workspace-bootstrap is the SOLE inter-component pyproject dependent of `loam-graceful-degradation`.)** Pre-build verification at plan-authoring time (`grep -nE 'loam-graceful-degradation' framework/*/pyproject.toml`): only `framework/workspace-bootstrap/pyproject.toml` carries the dependency. No other component depends on it. AC.RNM-1f.2's pyproject-dependency rebrand surface is therefore single-file.

2. **(NONE of the M1e-rebaselined HC#4 sample files reside under `framework/graceful-degradation/`.)** Per M1e §11 finding #3 + M1e §14 D-build.M1e.5: the 11–15 path updates + 2 SHA bumps in M1e's HC#4 retire-and-rebaseline picked sample files from `framework/{primary-persona,workspace-bootstrap,scope-of-work}/src/...`. Pre-build verification at plan-authoring time confirms M1f's directory + package rename does NOT touch any HC#4 sample-file path. Halt-trigger §8.3 fires only if an unexpected sample-file SHA change emerges during M1f's build. The HC#4 invariant is expected to remain GREEN through M1f without any retire-and-rebaseline.

3. **(`docs/rebuild/components/graceful-degradation/` rename DEVIATES from series convention.)** Per series convention (M1a..M1e): `docs/rebuild/components/<comp>/{research.md,research-plan.md,brief.md,component.md}` are preserved historical records. Per series-master M1f row: this directory IS renamed in M1f. Per §10 D-build.M1f.5: directory-shell `git mv` only; inner content preserved verbatim. The deviation is an explicit override of the convention for this single component (the only Tier-2 component-rename in the catalogue).

4. **(`Degradation*` Python class symbols are OUT OF M1f scope per §10 D-build.M1f.6.)** The `loam-rename-decisions.md` Tier-2 ruling names directory + package + OTel + config-files cascade; it is SILENT on internal class-symbol renames. Per ODD §2.5 conservatism, the AC family is module-path-shape-only. The workspace-bootstrap adapter class `GracefulDegradationContribution` IS rebranded (it's workspace-bootstrap's surface, not dormancy's). Surfaced for FIDRAFT capture: "`Degradation*` → `Dormancy*` Python class symbol rename — separate semantic amendment; ~20 callsites; mostly in dormancy's own src + tests + the public-API exports in `__init__.py`."

5. **(Probes.py import path stays valid post-rename only because `DegradationStore` is preserved.)** Per §10 D-build.M1f.6: `framework/self-upgrade/src/loam/self_upgrade/probes.py` line 230 currently reads `from loam.graceful_degradation.state import DegradationStore`. Post-M1f: `from loam.dormancy.state import DegradationStore`. The class name `DegradationStore` is preserved (not renamed to `DormancyStore`); the module path is the only thing rebranded. Verified by reading dormancy's `state.py` exports.

6. **(The `framework/self-upgrade/manifests/pos-v2-v0.2.0.yaml` is a frozen release manifest.)** Pre-build verification: file header carries `release_tag: pos-v2-v0.2.0` and `commit_sha: dde03a7427037e53e5eb2d2d02e597c3b000f752`; this is a frozen pre-namespace-pivot snapshot pinned to a specific commit. Per §6 + §10 hard constraint: NO content edits in M1f. The LIVE `_build_manifest.py` re-generator IS in scope per AC.RNM-1f.7; its frozen output for that release tag is not.

7. **(The `framework/dormancy/tests/test_no_sealed_amendments.py` allowlist needs the path-self-reference rebrand.)** The allowlist literal `"framework/graceful-degradation/"` and `"docs/rebuild/components/graceful-degradation/"` inside the test file rebases to `"framework/dormancy/"` and `"docs/rebuild/components/dormancy/"` as part of the test's own content edit. Plus the module docstring at the top references `"graceful-degradation"` extensively (it's the seal-enforcement-retrofit narrative for that component) — recommendation: preserve the historical narrative inside the docstring (it describes pre-M1f events using the historical vocabulary) BUT update the module-top BASELINE constant to point at `820fd84` (M1f's BASELINE) rather than `74ae5d3` (M1e's). The allowlist rebases; the historical narrative stays. Builder's call at build time per §10 D-build.M1f.5's general principle (path edits, not prose edits, for historical-record files).

8. **(Pre-emptive FIDRAFT capture — dispatch-time observations.)** Plan-time observations worth FIDRAFT capture (per `feedback_future_ideas_draft_workflow`):
   - "`Degradation*` Python class symbol rename — separate semantic amendment; ~20 callsites; out of M1f scope per Tier-2 silence + ODD §2.5 conservatism" (per §10 D-build.M1f.6 + §11 finding #4).
   - "Migration-helper convention: per-file vs per-directory four-case logic; SQLite WAL/SHM sibling-file handling pattern reusable for future component-data renames" (per §10 D-build.M1f.4).
   - "M1c launchd-label stragglers in orchestrator + self-upgrade (com.pos.orchestrator → com.loam.orchestrator) — small corrective amendment, ≈20 callsites" (carried from M1e §11 finding #1).
   - "Tools-tree namespace pivot (`framework/tools/<tool>/src/<tool_pkg>/...` for non-loam-prefixed tools) — out of M1f scope; absorbed by M1g (pos-amend) or follow-on" (carried from M1e §11 finding #4).

   Builder may surface to FIDRAFT during build per `feedback_future_ideas_draft_workflow`; do NOT extend M1f scope to address these.

---

## 12. Method-decision register (placeholder)

The method-decision content for M1f lives in §14 below per the
`pos-amend seal --plan-doc` convention (which expects §14 as the
SHA-backfill anchor). Content moved to §14 to avoid duplication.

§14 anchored from authoring per M1c/M1d/M1e locked precedent (avoid post-seal restructure).

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the cross-cutting verification:

- AC.RNM-1f.1 — directory + package rename: verified by `python -c "from loam.dormancy import *"` + `git log --follow framework/dormancy/src/loam/dormancy/observability.py` history-preservation check.
- AC.RNM-1f.2 — import rebrand: every Phase E touched test file (heaviest-touched: dormancy/tests/* (13 files) + self-upgrade/tests/test_probes.py).
- AC.RNM-1f.3 — OTel second-segment cascade: verified by `pytest framework/dormancy/tests/test_d9_observability.py` + post-rename grep returning 0.
- AC.RNM-1f.4 — config-file path cascade: verified by `pytest framework/dormancy/tests/test_d8_state.py` + post-rename grep returning 0.
- AC.RNM-1f.5 — migration helper: verified by `pytest framework/tools/loam-migrate-dormancy-config/tests/test_migrate.py` (four-case coverage including WAL/SHM siblings).
- AC.RNM-1f.6 — workspace-bootstrap adapter rename: verified by `python -c "import importlib.metadata; print([ep.name for ep in importlib.metadata.entry_points(group='loam.bootstrap.contributions')])"` returning a list containing `dormancy` + `pytest framework/workspace-bootstrap/tests/`.
- AC.RNM-1f.7 — self-upgrade consumer rebrand: verified by `pytest framework/self-upgrade/tests/test_probes.py`.
- AC.RNM-1f.8 — component docs subdir rename: verified by `ls docs/rebuild/components/dormancy/` + `git log --follow` history preservation.
- AC.RNM-1f.9 — first-run-inventory rebrand: verified by `grep` returning 0.
- AC.RNM-1f.10 — fence-narrowing negative AC: verified by `git diff <baseline>..HEAD --stat`.
- AC.RNM-1f.S — this seal commit; each component's `test_no_sealed_amendments.py` + HOL `test_cross_cutting.py` + HOL `test_d1_byte_content_match.py` (NO retire-and-rebaseline expected — see §11 finding #2).

### Backwards-compat verification

N/A — hard cutover per series-master D-RNM.3.

### HC#4 byte-content sample status

**No retire-and-rebaseline expected.** Per §11 finding #2: NONE of the M1e-rebaselined samples reside under `framework/graceful-degradation/`. M1f's directory + package rename does NOT touch any HC#4 sample file. The HC#4 invariant is expected to remain GREEN through M1f.

### Dependents cleared to dispatch

- **M1g** (`pos-amend` CLI → `loam amend` subcommand) cleared to dispatch post-M1f. Per series-master ladder note 5: M1g is the dependency-final sub-amendment.
- **M1c-corrective** (com.pos.orchestrator launchd-label stragglers, ≈20 callsites in orchestrator + self-upgrade) cleared to dispatch post-M1f at any point — independent of M1g; small corrective amendment per M1e §11 finding #1.
- **`Degradation*` Python class symbol rename** (~20 callsites) cleared to FIDRAFT-tracking; out of M1f scope per §10 D-build.M1f.6.

---

## 14. Method-decision register (post-build)

(SHA register populated by `pos-amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M1f.1 — `git mv` mechanism for directory rename

(Populated at build time. Recommendation per §10: two-step `git mv` — outer directory rename followed by inner package rename. Two-step is cleaner because rename-detection runs over both moves independently; blame is preserved at 95–100% similarity for all files unchanged in content.)

### D-build.M1f.2 — pyproject project name shape

(Populated at build time. Recommendation per §10: `name = "loam-dormancy"` — matches M1e's hyphenated-prefix convention.)

### D-build.M1f.3 — Migration helper four-case logic vs five-case

(Populated at build time. Recommendation per §10: per-file four-case logic with combined reporting; MigrationResult dataclass carries per-file status + overall is_clean property.)

### D-build.M1f.4 — Migration helper SQLite WAL/SHM sibling handling

(Populated at build time. Recommendation per §10: rename WAL + SHM siblings concurrently with the main file when present; missing siblings tolerated.)

### D-build.M1f.5 — Component docs subdir rename method

(Populated at build time. Recommendation per §10: directory-shell `git mv` only; inner content preserved verbatim. `git log --follow` per file returns full pre-M1f history.)

### D-build.M1f.6 — `Degradation*` Python class symbol rename scope

(Populated at build time. Recommendation per §10: `Degradation*` Python class symbols (DegradationStore, DegradationConfig, DegradationMode, DegradationSignal, DegradationChannel, DegradationComponent) are PRESERVED verbatim in M1f. The workspace-bootstrap adapter class `GracefulDegradationContribution` IS rebranded to `DormancyContribution` per AC.RNM-1f.6 because it's the workspace-bootstrap adapter, not the dormancy component's public API. The symbol rename is FIDRAFT-tracked.)

### Commit SHAs

- **Series master plan-doc commit:** `ebe0a57` — `docs(plans): split M1 rename into multi-amendment series — D-RNM.1 ruling` (2026-04-29).
- **M1a seal commit:** `143d465` — `chore(seals): M1a docs/prose-only brand rebrand` (2026-04-29).
- **M1b seal commit:** `d97c8c1` — `chore(seals): M1b env-vars + per-host config dir` (2026-04-29).
- **M1c seal commit:** `1e99d0b` — `chore(seals): M1c launchd label rebrand` (2026-04-29).
- **M1d seal commit:** `74ae5d3` — `chore(seals): M1d OTel root rebrand` (2026-04-29).
- **M1e seal commit:** `c806f57` — `chore(seals): M1e loam.* namespace pivot` (2026-04-29).
- **M1e §14 SHA-register backfill commit (BASELINE for M1f):** `820fd84` — `docs(plans): record amendment #80 commit SHAs in M1e §14 method-decision register` (2026-04-29).
- **M1f sub-plan + manifest commit:** _populated post-commit_.
- **M1f feature commit:** _populated post-commit_.
- **M1f apply commit:** _populated post-commit_.
- **M1f seal commit:** _populated post-commit_.
- **§14 SHA-register backfill commit (if any):** _populated post-commit_.

Diff window: `820fd84..<seal-commit>` (M1e-§14-backfill → M1f-seal).

---

## 15. References

- **Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Prior sub-amendments:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.md` (sealed `143d465`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.md` (sealed `d97c8c1`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c.md` (sealed `1e99d0b`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1d.md` (sealed `74ae5d3`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1e.md` (sealed `c806f57`; §14 backfill `820fd84`).
- **Authority documents (inherited from series master):**
  - `docs/rebuild/plans/loam-rename-decisions.md` Tier-2 (the M1f target).
  - `.scratch/claude-output/loam-rename-migration-plan.md` §4.1 (mechanics).
- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (M1f row in §5 per series-master ladder).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-loam.md` (the M1e-renamed file).
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
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1e.manifest.yaml` (M1e sibling — 14-component namespace pivot; precedent for `seal_diff` allowed_prefixes shape).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1d.manifest.yaml` (M1d sibling — 13-component OTel fence).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.manifest.yaml` (M1b sibling — 11-component fence; precedent for migration-helper authoring inside an amendment).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1f is built using this CLI under its current name; rename to `loam amend` is M1g per series-master ladder note 5).
- **Migration-helper precedents (M1f's helper mirrors these shapes):**
  - `framework/tools/loam-migrate-host-config/` (M1b — `~/.pos/` → `~/.loam/` directory rename; four-case logic).
  - `framework/tools/loam-migrate-launchd-labels/` (M1c — launchd-label rebrand; per-label idempotent migration).
