# OSS v0.1.0 publish — Dev/SDLC plugin M6b.0 (Surface B extraction excluding loam amend MOVE)

**Status:** sub-plan for M6b.0; second sub-amendment in the M6 series.
**Predecessor:** M6a sealed at `acd70ff`; §14 SHA-register backfill at `d9eb001`.
**Successor:** M6b.1 (loam amend MOVE alone with shadow-then-flip; separate dispatch).
**Master plan:** `docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md` (Surface B disposition table at §6.5.2; ship-shape at §6.5.4).
**Halt-surface report (context):** `workspace/.scratch/claude-output/m6b-halt-surface.md` (consult only as context for the four rulings; ALL rulings ratified by dispatcher 2026-04-29).

---

## 1. Objective

Execute the Surface B extraction migrations of the master plan §6.5.2 disposition table EXCEPT Item 7 (`loam amend` MOVE), which is deferred to a separate M6b.1 sub-amendment. The plugin BECOMES the dev-mode package post-extraction (Idea 13 two-modes operationalisation). Hard cutover; `git mv` for whole-package moves.

## 2. Owner rulings (M6b plan-time halt-and-surface — ratified)

The M6b dispatch halted at plan-time and surfaced four findings; the dispatcher ruled on all four before this dispatch:

- **F1 RULING.** `agent_file_authoring.py` + `agent_file_runner.py` STAY in canonical `framework/hands-off-lifecycle/hooks/`. Both are runtime infrastructure imported by `first_run_helper.py` for ALL workspaces (not dev-mode-only). The plan §6.5.2 row 6's MOVE list is corrected: drop these two files.
- **F2 RULING.** **Option D hybrid** for A1-A4 settings.json registration. MOVE the gate hook source files into `plugins/dev-sdlc/hooks/`; KEEP the writer logic at `framework/hands-off-lifecycle/hooks/first_run_helper.py`; the writer probes for plugin-side paths first, falling back to canonical-side if not present (probe-and-prefer pattern, mirror of amendment #67 `_resolve_corpus_path`). No contribution-time settings merger.
- **F3 RULING.** loam amend shadow-then-flip mechanic deferred to M6b.1; not in M6b.0 scope.
- **F4 RULING.** SPLIT into M6b.0 + M6b.1. THIS dispatch is M6b.0 — everything except loam amend MOVE. M6b.1 (loam amend MOVE alone) requires separate dispatch.

## 3. M6b.0 scope — explicit in-scope vs deferred

### In-scope (M6b.0)

**MOVE-WHOLE items (master plan §6.5.2 disposition):**
- **Item 1:** Dev CDCs from `docs/rebuild/FUTURE_IDEAS.md` lines 13-197 → `plugins/dev-sdlc/docs/cdcs/<name>.md` (one file per CDC; 10 CDCs).
- **Item 2:** Long-form ODD docs `docs/odd-methodology.md` (794 LOC) + `docs/odd-in-loam.md` (1058 LOC) → `plugins/dev-sdlc/docs/`.
- **Item 5:** `framework/tools/loam-mode/` package → `plugins/dev-sdlc/tools/loam-mode/` (preserve package layout; pyproject paths update; editable install refresh).
- **Item 9:** Duration-estimation rubric `docs/duration-estimation-rubric.md` → `plugins/dev-sdlc/docs/`.
- **Item 17:** `docs/rebuild/dev-mode-manifest.yaml` → `plugins/dev-sdlc/dev-mode-manifest.yaml`.

**PARTITION items (Option D hybrid for A1-A4):**
- **Item 6:** A1-A4 gate hook source files MOVE into `plugins/dev-sdlc/hooks/`. Five files: `objective_binding_gate.py` (A2), `tdd_guard.py` (A3), `agent_guard.py` (A4), `bash_guard.py` (A4), `dispatch_setup_hook.py` (M4). KEEP first-run hooks (`first_run_helper.py`, `first_run_*.py`, `first-run.sh`, `pos_session_start.py`, `statusline.py`, `agent_file_authoring.py`, `agent_file_runner.py`, `_gate_helpers.py`, `active_scope_sentinel.py`, `corpus_*` helpers) at `framework/hands-off-lifecycle/hooks/`. The five `_*_stanza` builders in `first_run_helper.py` gain a probe-and-prefer pattern: the script path resolves to `<loam_root>/plugins/dev-sdlc/hooks/<gate>.py` if that file exists, else the canonical fallback at `<loam_root>/framework/hands-off-lifecycle/hooks/<gate>.py`.

**Item 4 (templates):** dispatch + plan templates at `framework/tools/loam/templates/dispatch/sealed-component-build.md` + `framework/tools/loam/templates/plan/dev-discipline.md` MOVE to `plugins/dev-sdlc/templates/dispatch/` + `plugins/dev-sdlc/templates/plan/`. The unified loam CLI's template-engine resolver currently lives at `framework/tools/loam/src/loam_cli/amend/template_engine.py`; loam amend stays at canonical for M6b.0, so the template-engine resolver gains a probe-and-prefer pattern: read templates from `<workspace>/plugins/dev-sdlc/templates/<class>/<name>.md` first; fall back to `<workspace>/framework/tools/loam/templates/<class>/<name>.md` if plugin-side missing. This is the F2 mechanism applied to template loading.

**Convention codification items (re-author NEW concise docs at the plugin):**
- **Item 3:** Plan-doc / sub-plan / manifest YAML conventions → `plugins/dev-sdlc/docs/conventions/plan-docs.md` (NEW concise codification, 100-300 LOC per D-build.M6.11; the historical plan-doc instances STAY).
- **Item 10:** FIDRAFT pattern → `plugins/dev-sdlc/docs/conventions/fidraft-pattern.md` (NEW concise codification; `FUTURE_IDEAS_DRAFT.md` itself STAYS).
- **Item 11:** HC#4 / per-invariant baselines / ODD §4 retire-and-rebaseline conventions → `plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md` (NEW concise codification; per-component baseline data STAYS in each component).
- **Item 12:** Seal-ritual + commit-ladder conventions → `plugins/dev-sdlc/docs/conventions/commit-ladder.md` (NEW concise codification; per-component seal narratives STAY).
- **Item 13:** Five-gate chain + amendment-cycle conventions → `plugins/dev-sdlc/docs/conventions/five-gate-chain.md` + `plugins/dev-sdlc/docs/conventions/amendment-cycle.md` (NEW concise codifications).
- **Item 16:** Seal-test template → `plugins/dev-sdlc/templates/component/test_no_sealed_amendments.py.template` (NEW; the per-component seal-tests STAY).

**M2 partition manifest reclassification:**
- `plugins/dev-sdlc/**` reclassifies from `dev_and_public` (M6a) to `dev_only` (per master plan D-build.M6.14).
- `dev_only` block CONTRACTS as items 2 + 9 + parts of `framework/tools/loam-mode/` move into the plugin; the corresponding entries are removed from `dev_only` (and not re-added under `plugins/dev-sdlc/**` because `plugins/dev-sdlc/**` now covers them).
- `framework/tools/loam-mode/**` REMOVED from `dev_only` (path no longer exists).

**Cross-component admission edits:** the existing per-component `tests/test_no_sealed_amendments.py` files admit `framework/hands-off-lifecycle/` and `plugins/dev-sdlc/` cross-cutting widening already (per M6a's wide partner-prefix list); this dispatch verifies those admissions are sufficient post-extraction and adds the new `loam-mode` and gate-hook MOVE paths to the dev-sdlc seal-test's `allowed_prefixes` if needed (the M6a allowed_prefixes already include `framework/hands-off-lifecycle/` so no widening needed for the gate-hook MOVE OUT of HOL).

### Out-of-scope (deferred)

- **M6b.1:** Item 7 — `loam amend` MOVE (shadow-then-flip per master plan D-build.M6.15). `framework/tools/loam/` is UNTOUCHED in M6b.0.
- **M6c:** trailing dead-link / cross-reference cleanup.
- **v0.1.1+:** objective-extraction skill.

## 4. Acceptance criteria

AC family **AC.OSS-M6b0.\*** (continues the AC.OSS-M6.\* numbering convention; the loam-amend-related ACs on the master plan-doc explicitly defer to M6b.1).

| AC ID | Outcome | Verification |
|---|---|---|
| AC.OSS-M6b0.1 | Dev CDCs (10 sections, FUTURE_IDEAS.md lines 13-197) migrated to `plugins/dev-sdlc/docs/cdcs/`; FUTURE_IDEAS.md "temporary parking" header replaced with a one-line redirect to the plugin's home. | List-based test: every CDC heading from the original section resolves to a file under `plugins/dev-sdlc/docs/cdcs/`; the FUTURE_IDEAS.md section is shorter than 50 lines (placeholder only). |
| AC.OSS-M6b0.2 | Long-form ODD docs `docs/odd-methodology.md` + `docs/odd-in-loam.md` MOVED to `plugins/dev-sdlc/docs/`; canonical `docs/` no longer contains them; `git log --follow` resolves history. | `git ls-tree HEAD docs/` shows neither file; `plugins/dev-sdlc/docs/odd-methodology.md` + `plugins/dev-sdlc/docs/odd-in-loam.md` exist with non-empty body matching the original LOC counts within tolerance. |
| AC.OSS-M6b0.3 | `framework/tools/loam-mode/` MOVED to `plugins/dev-sdlc/tools/loam-mode/`; package importable as `loam_mode` post-editable-install refresh; `loam-mode` console-script still present + working; `dev-mode-manifest.yaml` reference updated to plugin-relative path. | Subprocess `loam-mode --help` exits 0; `python -c "import loam_mode"` succeeds. |
| AC.OSS-M6b0.4 | Duration-estimation rubric `docs/duration-estimation-rubric.md` MOVED to `plugins/dev-sdlc/docs/duration-estimation-rubric.md`; canonical `docs/` no longer contains it. | `git ls-tree HEAD docs/duration-estimation-rubric.md` empty; `plugins/dev-sdlc/docs/duration-estimation-rubric.md` exists. |
| AC.OSS-M6b0.5 | `docs/rebuild/dev-mode-manifest.yaml` MOVED to `plugins/dev-sdlc/dev-mode-manifest.yaml`; loam-mode's `_DEFAULT_MANIFEST_REL` updated to plugin-relative path. | `git ls-tree HEAD docs/rebuild/dev-mode-manifest.yaml` empty; `plugins/dev-sdlc/dev-mode-manifest.yaml` exists; `loam-mode audit` resolves the manifest at the new path without error. |
| AC.OSS-M6b0.6 | A2/A3/A4/M4 gate hook SOURCE files (`objective_binding_gate.py`, `tdd_guard.py`, `bash_guard.py`, `agent_guard.py`, `dispatch_setup_hook.py`) MOVED from `framework/hands-off-lifecycle/hooks/` to `plugins/dev-sdlc/hooks/`. The five `_*_stanza` builders in `first_run_helper.py` updated to probe for `<loam_root>/plugins/dev-sdlc/hooks/<gate>.py` first; fall back to canonical path if not present. `agent_file_authoring.py` + `agent_file_runner.py` STAY (per F1 ruling). | `plugins/dev-sdlc/hooks/<five_gates>.py` exist; `framework/hands-off-lifecycle/hooks/<five_gates>.py` do NOT exist; `agent_file_authoring.py` + `agent_file_runner.py` DO exist; PreToolUse stanza authored at first-run probes plugin-side path. |
| AC.OSS-M6b0.7 | Dispatch + plan templates MOVED from `framework/tools/loam/templates/` to `plugins/dev-sdlc/templates/`; loam amend's `template_engine.py` resolver gains probe-and-prefer for plugin-side paths. | `template_engine.discover_templates` returns the plugin-side template paths when invoked from canonical-side `loam amend` import. |
| AC.OSS-M6b0.8 | Six convention codification documents authored under `plugins/dev-sdlc/docs/conventions/` (plan-docs, fidraft-pattern, sealed-component-invariants, commit-ladder, five-gate-chain, amendment-cycle); seal-test template authored at `plugins/dev-sdlc/templates/component/test_no_sealed_amendments.py.template`. Each convention doc is 100-300 LOC concise codification (per D-build.M6.11). | Each file exists with 100-300 LOC. |
| AC.OSS-M6b0.9 | M2 partition manifest `plugins/dev-sdlc/**` reclassified from `dev_and_public` to `dev_only`; `dev_only` block contracts (entries for items 2, 9, and `framework/tools/loam-mode/**` removed; the latter no longer exists). | YAML inspection confirms classification reshape; existing partition-manifest tests pass. |
| AC.OSS-M6b0.S(b0) | Seal-diff fence narrowed to M6b.0 surfaces only (`plugins/dev-sdlc/`, `framework/hands-off-lifecycle/`, `framework/tools/loam-mode/` deletion, `framework/tools/loam/` template removal, `framework/tools/pos-publish-framework-only/` partition manifest, `docs/`, `docs/rebuild/`, `docs/rebuild/plans/`). All cross-component widening admissions verified. | `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` passes against new BASELINE. |

All ladder up to AC.OSS.6 → AC.PO.1 + AC.PO.2 (prime objective).

## 5. Sealed-component fence

**Components touched:**

1. `plugins/dev-sdlc/` — receives all MOVE-WHOLE + convention authoring + new hooks/ + new tools/loam-mode/ subtrees + new templates/ + new docs/ subtrees.
2. `framework/hands-off-lifecycle/` — five gate hooks DELETED (file MOVE OUT); first_run_helper.py + first_run_settings.py edited for probe-and-prefer.
3. `framework/tools/loam-mode/` — DELETED (package MOVED to plugin tree). Component effectively retires; its seal-tests + sidecars MOVE with it. (The deletion of the entire framework/tools/loam-mode/ subtree triggers component-level retirement; M6b.0 records this.)
4. `framework/tools/loam/` — `templates/` subdirectory DELETED (templates MOVED to plugin); `template_engine.py` updated for probe-and-prefer.
5. `framework/tools/pos-publish-framework-only/` — partition manifest YAML reshaped per AC.OSS-M6b0.9.
6. `docs/` — `odd-methodology.md`, `odd-in-loam.md`, `duration-estimation-rubric.md` DELETED (MOVED).
7. `docs/rebuild/` — `dev-mode-manifest.yaml` DELETED (MOVED); `FUTURE_IDEAS.md` lines 13-197 reduced to one-line redirect.

**Universal admissions (per amendment #22 ruling #3):**
- `docs/rebuild/plans/` — for this sub-plan + manifest.
- `docs/rebuild/plans/research/` — for any companion research material.

## 6. Halt triggers

- HT-1: F2 hybrid mechanism for `first_run_helper.py` settings.json writer needs more LOC or structural changes than ~120 LOC of probe-and-prefer logic.
- HT-2: A MOVE creates a cycle (component depends on its own future location).
- HT-3: PARTITION line is unclear for a specific item.
- HT-4: M2 partition manifest reclassification introduces classification ambiguity.
- HT-5: Frozen-baseline / byte-content invariant breach beyond ODD §4 in-band.
- HT-6: ODD §2.5 violations.
- HT-7: Wall-clock approaches 480 min — surface for continuation.
- HT-8: Editable installs cascade fails.
- HT-9: Plan disposition for any item turns out to be empirically wrong — surface specific item.

## 7. Ship shape

- Sub-plan + manifest commit (FIRST commit of M6b.0; this file + `oss-v0-1-0-publish-dev-sdlc-plugin-m6b0.manifest.yaml`).
- Feature commit(s) carrying the extraction diff with `git mv` preserving history. Author as a single feature commit if surfaces stay coherent; corrective commits OK if needed.
- `loam amend apply` commit before seal — runs against `framework/tools/loam/`'s installed `loam` (UNTOUCHED in M6b.0).
- Seal commit per repo convention.

## 8. Method-decision register heading FROM AUTHORING

Section 14 "Method-decision register" appears at the bottom of this plan. SHA register populated by `loam amend seal --plan-doc` SHA-backfill at seal time; method-decision narratives populated by builder during build.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M6b0.1 — F2 hybrid mechanism: probe-and-prefer in first_run_helper.py

(Populated at build time. Mechanism: each `_*_stanza()` builder in `first_run_helper.py` resolves the gate script path via `_resolve_gate_script(loam_root, name)` which returns plugin-side `<loam_root>/plugins/dev-sdlc/hooks/<name>.py` if that file exists, else canonical-side `<loam_root>/framework/hands-off-lifecycle/hooks/<name>.py`. Mirror of amendment #67 `_resolve_corpus_path`. ~30 LOC for the helper + 5 stanza builder edits.)

### D-build.M6b0.2 — Convention codification authoring scope

(Populated at build time. Per master plan D-build.M6.11: 100-300 LOC each, concise codification, structured as objective + summary + named conventions/rules + cross-references + applied-immediately footer. The authoritative LONG-FORM content lives in `docs/odd-in-loam.md` which itself MOVES to the plugin in this same amendment.)

### D-build.M6b0.3 — Template-engine probe-and-prefer

(Populated at build time. The unified loam CLI's `template_engine.discover_templates` resolver gains a probe-and-prefer for plugin-side templates at `<workspace>/plugins/dev-sdlc/templates/<class>/<name>.md`, falling back to canonical-side at `<workspace>/framework/tools/loam/templates/<class>/<name>.md`. Mechanism mirrors F2; loam amend stays at canonical in M6b.0.)

### D-build.M6b0.4 — loam-mode package re-installation

(Populated at build time. Post-MOVE the package directory is at `plugins/dev-sdlc/tools/loam-mode/`; the existing editable install at `framework/tools/loam-mode/` is removed via `pip uninstall loam-mode -y` then `pip install -e plugins/dev-sdlc/tools/loam-mode/` re-registers the console-script. The pyproject's `_DEFAULT_MANIFEST_REL` updates to the plugin-relative path.)

### D-build.M6b0.5 — M2 partition manifest reshape

(Populated at build time. Three changes to `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`: (a) `plugins/dev-sdlc/**` MOVED from `dev_and_public:` to `dev_only:`. (b) `framework/tools/loam-mode/**` REMOVED from `dev_only:` (path no longer exists). (c) `docs/odd-methodology.md`, `docs/odd-in-loam.md`, `docs/duration-estimation-rubric.md` REMOVED from `dev_only:` (paths MOVED into the plugin tree, covered by `plugins/dev-sdlc/**` glob).)

### Commit SHAs

- Amendment commit: `d9babcf9b476b32e87ebc6560107617b3d937973` —
  `chore(dev-sdlc-apply): loam amend apply for amendment #88 (M6b.0 Surface B extraction)`
- Seal commit: `3a7c8d7a83c253abbdf5a2c71ccf39890713e629` —
  `chore(seals): M6b.0 Dev/SDLC plugin Surface B extraction (excluding loam amend MOVE — deferred to M6b.1) — second sub-amendment in the M6 series per master plan §6.5.4 D-Q.M6.6 sub-amendment series ruling. Migrations executed via git mv preserving history: dev CDCs (10 sections from FUTURE_IDEAS.md lines 13-197) → plugins/dev-sdlc/docs/cdcs/<name>.md (one file per CDC; FUTURE_IDEAS.md temporary-parking section reduced to one-line redirect) + long-form ODD docs (docs/odd-methodology.md 794 LOC + docs/odd-in-loam.md 1058 LOC) → plugins/dev-sdlc/docs/ + framework/tools/loam-mode/ package (whole tree: pyproject.toml + src/ + tests/ + README.md) → plugins/dev-sdlc/tools/loam-mode/ + docs/duration-estimation-rubric.md → plugins/dev-sdlc/docs/duration-estimation-rubric.md + docs/rebuild/dev-mode-manifest.yaml → plugins/dev-sdlc/dev-mode-manifest.yaml + A2/A3/A4/M4 gate hook SOURCE files (objective_binding_gate.py + tdd_guard.py + bash_guard.py + agent_guard.py + dispatch_setup_hook.py) MOVED from framework/hands-off-lifecycle/hooks/ to plugins/dev-sdlc/hooks/ (PARTITION per F2 Option D hybrid — first_run_helper.py KEEPS writer logic + probes plugin-side path <loam_root>/plugins/dev-sdlc/hooks/<gate>.py first; falls back to <loam_root>/framework/hands-off-lifecycle/hooks/<gate>.py if plugin not present; agent_file_authoring.py + agent_file_runner.py + _gate_helpers.py + active_scope_sentinel.py + corpus_*.py STAY at framework/hands-off-lifecycle/hooks/ per F1 ruling — runtime infrastructure used unconditionally by ALL workspaces) + dispatch + plan templates from framework/tools/loam/templates/{dispatch,plan}/ MOVED to plugins/dev-sdlc/templates/{dispatch,plan}/ (template_engine.discover_templates resolver gains probe-and-prefer for plugin-side templates with canonical fallback; mirrors F2 mechanism). 6 NEW convention codification documents authored at plugins/dev-sdlc/docs/conventions/ (plan-docs.md, fidraft-pattern.md, sealed-component-invariants.md, commit-ladder.md, five-gate-chain.md, amendment-cycle.md — each 100-300 LOC concise codification per D-build.M6.11; the long-form authoritative content lives in docs/odd-in-loam.md which itself MOVES in this same amendment). Seal-test template authored at plugins/dev-sdlc/templates/component/test_no_sealed_amendments.py.template (per D-Q.M6.7's PARTITION line of 'template MOVES; per-component data STAYS'). M2 partition manifest reshape: (a) plugins/dev-sdlc/** RECLASSIFIES from dev_and_public to dev_only per D-build.M6.14; (b) framework/tools/loam-mode/** REMOVED from dev_only (path no longer exists); (c) docs/odd-methodology.md, docs/odd-in-loam.md, docs/duration-estimation-rubric.md REMOVED from dev_only (paths covered by plugins/dev-sdlc/** glob). Sealed-component fence: 6 components — plugins/dev-sdlc/ (receives all MOVE destinations + new convention authoring) + framework/hands-off-lifecycle/ (5 gate-hook source files DELETED; first_run_helper.py edited for probe-and-prefer) + framework/tools/loam-mode/ (DELETED — package MOVED; component effectively retires; its tests + sidecars MOVE with it) + framework/tools/loam/ (templates/ subdirectory DELETED; template_engine.py edited for probe-and-prefer; UNTOUCHED otherwise — Item 7 loam amend MOVE deferred to M6b.1) + framework/tools/pos-publish-framework-only/ (partition-manifest YAML reshape) + docs/rebuild/ (FUTURE_IDEAS.md temporary-parking section reduced to one-line redirect; dev-mode-manifest.yaml DELETED). HC#4 byte-content sample status: NO RETIRE-AND-REBASELINE — file moves are git-rename-tracked; byte-content of moved files unchanged (renames preserve byte-for-byte content; only path changes). loam amend at framework/tools/loam/ remains UNTOUCHED in M6b.0 — its console-script + entry-point + bookkeeping logic intact; M6b.0 uses canonical-side loam amend for its own apply + seal. F1+F2+F3+F4 owner rulings ratified 2026-04-29 (per workspace/.scratch/claude-output/m6b-halt-surface.md): F1 — agent_file_authoring.py + agent_file_runner.py STAY (runtime infrastructure); F2 — Option D hybrid for A1-A4 settings.json registration (gate files MOVE; writer stays + probes); F3 — loam amend shadow-then-flip deferred to M6b.1; F4 — SPLIT into M6b.0 + M6b.1. AC family: AC.OSS-M6b0.1..M6b0.9 + AC.OSS-M6b0.S(b0). Each AC ladders up to AC.OSS.6 → AC.PO.1 + AC.PO.2 (prime objective) per master plan §6.5.5. — dev-sdlc+hands-off-lifecycle at d9babcf`
## 15. Backwards-compat verification (post-build)

- `framework/tools/loam-mode/`'s former tests (now at `plugins/dev-sdlc/tools/loam-mode/tests/`) pass byte-identically against MOVED package.
- `framework/hands-off-lifecycle/tests/` PreToolUse settings-merge tests verify probe-and-prefer (settings.json stanzas point at plugin-side paths when plugin tree exists; canonical-side when it doesn't).
- All other framework tests pass byte-identically (no source change to non-fence components).
- HC#4 byte-content invariant: NO RETIRE-AND-REBASELINE — file moves are git-rename-tracked; byte-content of moved files unchanged.
- New `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` BASELINE advances to M6a's seal commit (`acd70ff`).

## 16. Halt-and-surface findings encountered during plan authoring

None at this dispatch; the four plan-time findings (F1-F4) were already raised + ruled by dispatcher. Plan is authorised to proceed.
