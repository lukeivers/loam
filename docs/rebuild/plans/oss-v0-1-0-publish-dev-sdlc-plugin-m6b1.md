# OSS v0.1.0 publish — Dev/SDLC plugin M6b.1 (loam amend MOVE alone with shadow-then-flip)

**Status:** sub-plan for M6b.1; third sub-amendment in the M6 series.
**Predecessors:** M6a sealed at `acd70ff` (Surface A baseline); M6b.0 sealed at `3a7c8d7` (Surface B extraction excluding `loam amend` MOVE).
**Successor:** M6c (trailing cleanups; final M6 sub-amendment).
**Master plan:** `docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md` (AC.OSS-M6.15 + §10 D-build.M6.15 — shadow-then-flip migration shape; §6.5.4 ship-shape).
**M6b plan-time halt-and-surface (context for F3):** `workspace/.scratch/claude-output/m6b-halt-surface.md` (F3 cascading-effects analysis specific to loam amend).

---

## 1. Objective

Execute Item 7 of master plan §6.5.2 — `loam amend` package MOVE from `framework/tools/loam/src/loam_cli/amend/` into the Dev/SDLC plugin via shadow-then-flip phasing per master plan D-build.M6.15 + halt-surface F3 phasing recommendation. The unified `loam` CLI dispatcher at `framework/tools/loam/src/loam_cli/cli.py` STAYS in canonical (it remains the public binary entry point for the harness); only the `amend` subcommand-package moves. After M6b.1, the dispatcher discovers `loam amend` via the M6a-authored `loam.cli.subcommands` entry-point group rather than direct import.

This is the FIRST amendment whose own bookkeeping (`loam amend apply` + `loam amend seal`) runs under the plugin-side binary.

## 2. Owner rulings (carried forward)

The four M6b plan-time findings (F1-F4) were ratified by the dispatcher 2026-04-29 (per M6b.0 sub-plan §2). M6b.1 inherits:

- **F3 RULING.** Endorsed the shadow-then-flip Phase α / β / γ / δ phasing recommended by the halt-surface report (canonical-side `loam_cli.amend` source UNTOUCHED in M6b.0 specifically so the canonical binary remains usable for M6b.0's own apply + seal). M6b.1 EXECUTES F3.
- **F4 RULING.** SPLIT was already applied: this dispatch is M6b.1.

## 3. M6b.1 scope — explicit in-scope vs deferred

### In-scope (M6b.1)

**MOVE-WHOLE (Item 7 from master plan §6.5.2 disposition):**
- `framework/tools/loam/src/loam_cli/amend/` (the entire amend submodule: `__init__.py`, `cli.py`, `baseline.py`, `dry_run.py`, `manifest.py`, `narrative.py`, `paths.py`, `rename_detection.py`, `seal_diff.py`, `sidecar.py`, `template_engine.py`, `tracker_registration.py`, plus `commands/` subdir with `__init__.py`, `apply.py`, `new_plan.py`, `seal.py`, `template.py`, `validate.py`) → `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/`.
- `framework/tools/loam/tests/` (~22 files: every `test_*.py` covering the amend surface; `conftest.py`; `fixtures/`) → `plugins/dev-sdlc/tools/loam-amend/tests/`. Test imports rewritten `loam_cli.amend.X` → `loam_amend.X`.
- `framework/tools/loam/src/loam_cli/__main__.py` (delegates to the `amend` package's `__main__`-equivalent via `python -m loam_cli.amend`) — STAYS at canonical (still routes to dispatcher's `main()`); see §3 deferred.

**EDIT (canonical-side dispatcher composition):**
- `framework/tools/loam/src/loam_cli/cli.py`: REMOVE the hardcoded `from loam_cli.amend import cli as amend_cli` import + the hardcoded `amend` subparser registration in `_build_parser()` + the `if args.subcommand == "amend"` branch in `main()`. The `amend` subcommand resolves entirely through the M6a-authored `_discover_subcommand_builders()` entry-point loop. Plugin-side `loam_amend.cli:build_amend_subcommand` becomes the registered builder.

**NEW (plugin-side package scaffold):**
- `plugins/dev-sdlc/tools/loam-amend/pyproject.toml`: declares `name = "loam-amend"`, `version = "0.1.0"`, `dependencies = ["PyYAML>=6"]`, `[project.entry-points."loam.cli.subcommands"] amend = "loam_amend.cli:build_amend_subcommand"`. NO console-script (the unified `loam` binary stays the only entry).
- `plugins/dev-sdlc/tools/loam-amend/README.md`: minimal one-paragraph description + cross-link to the plugin README.
- A small adapter symbol `loam_amend.cli.build_amend_subcommand(sub: argparse._SubParsersAction) -> None` registered as the entry-point builder; internally it adds the `"amend"` subparser, calls the existing `attach_subparsers()` helper, and `set_defaults(func=_dispatch)` so the dispatcher's `args.func` path routes to `loam_amend.cli.dispatch(args)`.

**EDIT (cross-tree consumer):**
- `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/verify.py:76,81` — late imports `from loam_cli.amend.manifest import ...` + `from loam_cli.amend.tracker_registration import ...` → `from loam_amend.manifest import ...` + `from loam_amend.tracker_registration import ...`. (Per F3 analysis + plan §11 finding #11; sole non-test cross-tree consumer, verified by repeat grep at build start.)

**EDIT (path-resolution constant in moved package):**
- `loam_amend/commands/template.py`: `_PKG_ROOT` + `_WORKSPACE_ROOT` parents-depth recomputation. New file path: `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/template.py`. Parents: `[0]=commands/`, `[1]=loam_amend/`, `[2]=src/`, `[3]=loam-amend/`, `[4]=tools/`, `[5]=dev-sdlc/`, `[6]=plugins/`, `[7]=<workspace>`. So `_PKG_ROOT = parents[3]` (the `loam-amend/` package root) and `_WORKSPACE_ROOT = parents[7]` (unchanged from canonical). The probe-and-prefer logic from M6b.0 stays — plugin-side templates continue to resolve at `<workspace>/plugins/dev-sdlc/templates/`. The canonical fallback `_PKG_ROOT / "templates"` is now stale (post-MOVE there are no templates inside the loam-amend package itself; the plugin-side path always exists). Resolver logic intact for safety.

**EDIT (canonical-side dispatcher imports):**
- `framework/tools/loam/src/loam_cli/__main__.py`: if it imports `loam_cli.amend`, retarget to `from loam_cli.cli import main` (no amend reference). Verify at build time.

### Out-of-scope (deferred)

- **M6c:** Trailing cleanups — final dead-link sweep, last cross-reference pruning, any documentation polish surfaced during M6b.1.
- The `loam` console-script entry (`framework/tools/loam/pyproject.toml:[project.scripts] loam = "loam_cli.cli:main"`) STAYS unchanged — `loam` is still the public binary; only `loam amend`'s implementation moves.
- The unified `loam` CLI dispatcher (`framework/tools/loam/src/loam_cli/cli.py` + `__init__.py` + `__main__.py`) STAYS at canonical (per F3 halt-trigger #5 — the dispatcher is the harness's binary entry point and must remain a public-tree resident).

## 4. Acceptance criteria

AC family **AC.OSS-M6b1.\*** (continues the AC.OSS-M6\* numbering convention; ladders to master plan AC.OSS-M6.15).

| AC ID | Outcome | Verification |
|---|---|---|
| AC.OSS-M6b1.1 | The `loam amend` subcommand-package source MOVES from `framework/tools/loam/src/loam_cli/amend/` to `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/`. `git mv` preserves history. Old path GONE post-MOVE. | `git ls-tree HEAD framework/tools/loam/src/loam_cli/amend/` empty; `git ls-tree HEAD plugins/dev-sdlc/tools/loam-amend/src/loam_amend/` non-empty; `git log --follow plugins/dev-sdlc/tools/loam-amend/src/loam_amend/cli.py` resolves into pre-MOVE history. |
| AC.OSS-M6b1.2 | The amend tests (~22 files) MOVE alongside the package; import paths rewrite `loam_cli.amend.*` → `loam_amend.*`. Tests pass byte-equivalent post-MOVE. | `pytest plugins/dev-sdlc/tools/loam-amend/tests/` exits 0; pre-MOVE test file count matches post-MOVE count. |
| AC.OSS-M6b1.3 | `plugins/dev-sdlc/tools/loam-amend/pyproject.toml` declares the `[project.entry-points."loam.cli.subcommands"] amend = "loam_amend.cli:build_amend_subcommand"` entry-point. Editable install registers it. | `python -c "import importlib.metadata as m; eps = m.entry_points(group='loam.cli.subcommands'); print({ep.name: ep.value for ep in eps})"` shows `'amend': 'loam_amend.cli:build_amend_subcommand'`. |
| AC.OSS-M6b1.4 | Canonical `framework/tools/loam/src/loam_cli/cli.py` removes its hardcoded `from loam_cli.amend import cli as amend_cli` import + the `add_parser("amend", ...)` call + the `if args.subcommand == "amend"` dispatch branch. The `amend` subcommand resolves entirely through `_discover_subcommand_builders()`. | Source-grep: zero references to `loam_cli.amend` in `framework/tools/loam/src/loam_cli/cli.py`; `loam amend --help` exits 0 + outputs the original help text post-flip. |
| AC.OSS-M6b1.5 | Cross-tree consumer `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/verify.py` updated: late imports rewrite `loam_cli.amend.manifest` → `loam_amend.manifest` and `loam_cli.amend.tracker_registration` → `loam_amend.tracker_registration`. heavy-b-migrate's own tests still pass. | `grep -rn "loam_cli.amend" framework/tools/heavy-b-migrate/` returns empty; `pytest framework/tools/heavy-b-migrate/tests/` exits 0. |
| AC.OSS-M6b1.6 | Editable install cascade: `pip uninstall loam-cli -y` for the canonical-side amend-pieces (NOT the `loam-cli` package itself, which retains the dispatcher); `pip install -e plugins/dev-sdlc/tools/loam-amend/` registers the new package + its entry-point; `pip install -e framework/tools/loam` re-registers the dispatcher post-edit. Both packages co-exist post-flip; `loam amend ...` dispatches to plugin-side. | `pip show loam-amend` succeeds; `pip show loam-cli` succeeds; `python -c "from loam_amend.cli import build_amend_subcommand"` succeeds; `python -c "from loam_cli.amend import cli"` raises `ModuleNotFoundError` (canonical-side amend GONE). |
| AC.OSS-M6b1.7 | This amendment's own bookkeeping (`loam amend apply` + `loam amend seal`) runs under the **plugin-side** `loam-amend` package. The apply commit lands BEFORE the seal commit. | Both commits show file-level edits to `seals/SEAL_COMMIT.oss-v0-1-0-publish-dev-sdlc-plugin-m6b1` + `tests/SEAL_COMMIT` sidecars; the seal-test passes against the post-flip state. |
| AC.OSS-M6b1.S(b1) | Seal-diff fence narrowed to M6b.1 surfaces only: `plugins/dev-sdlc/` (new `tools/loam-amend/` subtree), `framework/tools/loam/` (`amend/` + `tests/` subtrees DELETED + `cli.py` edited + `__main__.py` adjusted), `framework/tools/heavy-b-migrate/` (verify.py import rewrite), plus universal admissions. | `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` passes against new BASELINE; `framework/hands-off-lifecycle/tests/test_cross_cutting.py` passes (HOL is in-scope as a partner — gate hooks reference `loam amend` strings via bash_guard which already resolves correctly). |

All ACs ladder up to master plan AC.OSS-M6.15 → AC.OSS.6 → AC.PO.1 + AC.PO.2 (prime objective per `docs/rebuild/VALUE_PROPOSITION.md` per `feedback_value_proposition_as_prime_objective`).

## 5. Sealed-component fence

**Components touched:**

1. `plugins/dev-sdlc/` — receives the new `tools/loam-amend/` subtree (NEW package source + tests + pyproject.toml + README.md). Plus the seal-test allowed-prefixes admission already covers this from M6a.
2. `framework/tools/loam/` — `src/loam_cli/amend/` subtree DELETED (MOVED); `tests/` subtree DELETED (MOVED); `src/loam_cli/cli.py` edited (remove hardcoded amend reg + branch); `src/loam_cli/__main__.py` possibly edited.
3. `framework/tools/heavy-b-migrate/` — `src/loam/heavy_b_migrate/verify.py` 2-line import rewrite.

**Universal admissions (per amendment #22 ruling #3):**
- `docs/rebuild/plans/` — for this sub-plan + manifest.
- `docs/rebuild/plans/research/` — for any companion research material.

**Cross-component widening:** the dev-sdlc seal-test's `allowed_prefixes` already includes `framework/tools/loam/` (M6a baseline) — no further widening needed for M6b.1's diff. No new cross-component widening edits expected (verify pre-build).

## 6. Halt triggers (echoed from dispatch + reframed)

- HT-1 (Phase α shadow can't establish): cannot author a working `loam-amend` package side-by-side with canonical without breaking either tree.
- HT-2 (M6a `_discover_subcommand_builders` doesn't compose cleanly): the dispatcher's discovery loop fails to register the plugin's `amend` builder cleanly — surface design concern.
- HT-3 (cross-tree consumer surprise): a `loam_cli.amend.*` consumer surfaces beyond `heavy-b-migrate/verify.py:76,81` — surface specific case (per F3 analysis only this one was named).
- HT-4 (editable install cascade fails): post-flip `pip install -e ...` fails (egg-info collision, dependency resolution, etc.) — surface specific failure.
- HT-5 (dispatcher itself needs to MOVE): structurally the unified loam CLI dispatcher cannot stay canonical — surface for re-scope.
- HT-6 (HC#4 byte-content invariant breach): file MOVEs (`git mv`) preserve content but if any non-rename edit changes byte-content of a sample-path file, surface.
- HT-7 (ODD §2.5 violations): non-AC-mapped behaviour change surfaces — apply ODD §4 retire-and-rebaseline.
- HT-8 (wall-clock approaches 240 min): surface for continuation rather than stalling silently.
- HT-9 (plan disposition empirically wrong): mid-build any item turns out to need different shape — surface specific item.

## 7. Ship shape (commit ladder)

1. **Sub-plan + manifest commit.** This file + the manifest YAML.
2. **Phase α — Shadow commit.** New `plugins/dev-sdlc/tools/loam-amend/` package authored as a copy of the canonical-side `framework/tools/loam/src/loam_cli/amend/`. Inner package directory named `loam_amend/` (NOT `loam_cli/amend/`). pyproject.toml authored with the `loam.cli.subcommands` entry-point. NEW adapter `loam_amend.cli.build_amend_subcommand`. Path-resolution constants in `loam_amend/commands/template.py` recomputed. **Both** packages exist; canonical-side `loam_cli.amend` still importable; canonical `cli.py`'s hardcoded amend registration still drives `loam amend`. Editable install of the new package: `pip install -e plugins/dev-sdlc/tools/loam-amend/`. Verification: `loam amend --help` still works (canonical-side path); `python -c "from loam_amend.cli import build_amend_subcommand"` works.
3. **Phase β — Flip commit.** Edit `framework/tools/loam/src/loam_cli/cli.py` to remove hardcoded amend reg + `import` + `if args.subcommand == "amend"` branch; rely on `_discover_subcommand_builders()` for the amend builder. Edit `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/verify.py` lines 76, 81 imports. Re-run `pip install -e framework/tools/loam`. Verification: `loam amend --help` works (now resolves via plugin entry-point).
4. **Phase γ — Delete-old commit.** `git mv` (or `git rm` if move-as-delete) removes `framework/tools/loam/src/loam_cli/amend/` + `framework/tools/loam/tests/` (the latter MOVES to `plugins/dev-sdlc/tools/loam-amend/tests/` with import rewrites — done in this commit, ideally combined with Phase β to keep history clean; in practice `git mv -k` for the source files lands here and the import rewrites land alongside). The `git mv` mechanic groups the move and the delete into one rename-tracked operation; combining Phase α + γ into a single `git mv` is preferable for history (`git log --follow` works) — Phase α's "shadow" is actually authored as the GIT-MV destination, with the canonical-side files going through `git mv` directly. The "shadow" window in F3 phasing is conceptual (both packages bootable simultaneously between the START of the build and the FLIP commit landing); execution-wise the sequence is: (a) `git mv` source + tests in one commit; (b) edit pyproject.toml + author cli adapter + path-resolution recomputation in same commit OR a follow-up commit; (c) edit canonical `cli.py` + heavy-b-migrate in the FLIP commit (separate or combined). The shadow PROPERTY is preserved by editable-install + the dispatcher's discovery loop being lenient — both can exist if both are installed. **Builder's call** on whether to issue 2 commits (shadow+flip combined; delete-old combined) or 3 commits (separate shadow / flip / delete) — D-build.M6b1.1 records the actual.
5. **Apply commit (Phase δ part 1).** `loam amend apply` for M6b.1 — runs against the plugin-side `loam-amend` package. FIRST RUN under plugin-side binary. Updates objective-tracker + applies any apply-step renames declared in the manifest (none expected for M6b.1).
6. **Seal commit (Phase δ part 2).** `loam amend seal --plan-doc <abs-path>` for M6b.1 — runs against the plugin-side binary. Records SHA in §14 register; seal-test passes against new BASELINE.

The manifest's BASELINE points at `3a7c8d7` (M6b.0 seal). The seal-test computes `BASELINE..HEAD` diff window per the convention.

## 8. Method-decision register heading FROM AUTHORING

Section 14 "Method-decision register" appears at the bottom of this plan. SHA register populated by `loam amend seal --plan-doc` SHA-backfill at seal time; method-decision narratives populated by builder during build.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M6b1.1 — Shadow-then-flip phasing actuals

(Populated at build time. Records: how many commits the builder used (shadow / flip / delete-old combined or split), why, any correctives. Per F3 phasing recommendation, expected: 2-3 commits between sub-plan commit and apply commit.)

### D-build.M6b1.2 — Cross-tree consumer update inventory

(Populated at build time. Per F3 + plan §11 finding #11, expected SOLE update: `framework/tools/heavy-b-migrate/src/loam/heavy_b_migrate/verify.py:76,81`. Record any additional consumers surfaced during build-time grep.)

### D-build.M6b1.3 — Editable-install refresh confirmation

(Populated at build time. Records: which packages were `pip uninstall`'d, which were `pip install -e ...`'d, the final `pip list | grep -i loam` state, and verification that `python -c "from loam_amend.cli import ..."` succeeds while `python -c "from loam_cli.amend import cli"` raises `ModuleNotFoundError`.)

### D-build.M6b1.4 — Plugin-side dispatcher composition shape

(Populated at build time. Records: the precise shape of `loam_amend.cli.build_amend_subcommand`. Expected: ~10 LOC adapter that calls `attach_subparsers(parser)` on the new subparser + sets `args.func = dispatch` so the unified CLI's `args.func` path routes correctly. Verifies M6a's `_discover_subcommand_builders` composes cleanly without dispatcher edit.)

### D-build.M6b1.5 — Path-resolution constant recomputation

(Populated at build time. Records: the recomputed `parents[N]` indices for `_PKG_ROOT` + `_WORKSPACE_ROOT` in `loam_amend/commands/template.py` post-MOVE. Expected: `_PKG_ROOT = parents[3]`; `_WORKSPACE_ROOT = parents[7]`. The plugin-side templates path is resolved correctly + canonical fallback retained for safety.)

### Commit SHAs

(Populated at seal time by `loam amend seal --plan-doc` SHA-backfill.)

## 15. Backwards-compat verification (post-build)

- The moved test suite at `plugins/dev-sdlc/tools/loam-amend/tests/` passes byte-equivalent against the moved package (only import-path rewrites; no behaviour change).
- `loam amend apply` + `loam amend seal` invocations are functionally identical (same surface; same flag set; same exit codes).
- heavy-b-migrate's own tests pass against the rewritten import.
- HC#4 byte-content invariant: NO RETIRE-AND-REBASELINE — the file MOVEs are git-rename-tracked; the `cli.py` edit in canonical removes ~10 LOC of hardcoded amend reg + the `if args.subcommand == "amend"` branch (additive-deletion only); test imports rewrite is a textual substitution per file (`loam_cli.amend` → `loam_amend`); none of these are sample paths in HC#4's seal-fence config.

## 16. Halt-and-surface findings encountered during plan authoring

None new at this dispatch. F3's phasing analysis was authored at plan-time of M6b (parent dispatch) + ratified by dispatcher 2026-04-29; no further plan-authoring findings surfaced during M6b.1's plan-doc authoring. Plan is authorised to proceed.
