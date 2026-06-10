# conventional-install / PyPI publish — `pip install loam-harness` → working `loam`

**Status:** sub-plan-doc (PLAN ONLY — no build, no publish). Authored by `loam-plan-author`.
**Working directory:** `/Users/lukeivers/loam` (canonical loam tree).
**Parent task:** #21 — *DRIVE: loam structure flatten (Q1) + PyPI publish / conventional install (Q2)* (Luke 12978). This plan IS the Q2 surface.
**Parent plan:** `docs/plans/foundation-polish-cluster.md` — SUB-ITEM 1b (the owner-gated public PyPI flip, F-PUBLISH).
**Predecessors (load-bearing prior seals + artefacts):**
- SUB-ITEM 1a (packaging readiness, AUTONOMOUS, sealed) — `docs/plans/sealed/foundation-polish-cluster-install.md`. Built the meta-package + the `AC.PYPKG.1/2/3` + `AC.INST.S` family, PROVEN against a LOCAL wheelhouse with zero public push. This plan is the deferred public flip it parked.
- Research artefact — `docs/design/loam-structure-and-install-cost-2026-05-29.md` (Q2: conventional install blocked solely by no-PyPI-publish; ~9 h AI-time band; dominated by publish mechanics + version pinning).
- Existing meta-distribution on disk — `framework/loam-init/meta/pyproject.toml` (currently dist-name `loam`, version `1.1.0` — both must change; see §10 F2).
**BASELINE candidate:** `32f362915e4712d6567310f9a1a4e20dbac30162` (HEAD of main at plan-authoring; confirm at apply time).
**Status-file target:** `docs/STATE.md` (release register) + `docs/release-roadmap.md` (§8 register) + parent plan §2 backfill.
**Quality bar:** META-FRAMEWORK minor (packaging/distribution; no end-user runtime capability added). HARD-smoke-per-minor applies (`feedback_hard_smoke_per_minor_before_publish`): the outcome-altitude AC IS the hard smoke.
**Owner-decided parameters (Luke 2026-06-04 — LOCKED, do not re-open):** dist name = `loam-harness`; installed command = `loam` (reuse `loam-cli`'s existing `[project.scripts] loam = "loam_cli.cli:main"`); version lockstep at 1.2.0; final `twine upload` run by Luke with his credential (agent never enters a token).

---

## §1 Summary / TL;DR

**What ships:** one published distribution `loam-harness` on PyPI such that `pip install loam-harness` (and `pipx install loam-harness`) yields a working `loam` command — `loam --version` reports `1.2.0`, `loam --help` lists the real subcommands — with no source checkout. The existing meta-distribution is renamed `loam` → `loam-harness`, re-lockstepped to 1.2.0, and its dependency closure reconciled to the set actually published. Publish tooling is a documented owner-run `build`+`twine` runbook; Luke runs the final upload with his credential.

**AC families:**
- `AC.PKGPUB.*` — the renamed meta-distribution resolves the runtime closure into one install command, builds cleanly, dist-name/import-name/command-name confirmed non-colliding.
- `AC.PUBTOOL.*` — the owner-run publish runbook (build → check → owner-upload), agent never handles a token.
- `AC.INSTPUB.S` ★ outcome-altitude — a cold environment installs the built artefact and gets a working `loam --version` → `1.2.0` with no source checkout.

**Key decisions baked (recommendations in §3, full register §10):**
- **D-PKG.1 ★ARCHITECTURE → meta-package** (`loam-harness` depends on the component distributions; ships zero code). Composes with task #21's flatten (Q1) instead of fighting it; reuses the already-built meta on disk.
- **D-PKG.2 → runtime closure = the `loam` CLI graph** (CLI + verb packages + their transitive runtime deps); dev/test-only packages excluded.
- **D-PKG.3 → manual `build`+`twine` runbook, owner-run upload** (no new CI this cycle; Lens-1 reuse of `loam release` gate chain as pre-flight).
- **D-PKG.4 → no namespace clash**: import-name `loam.*` (PEP 420 namespace), dist-name `loam-harness`, command-name `loam` are three independent identifiers; the unrelated PyPI `loam` is avoided by the dist-name change and never imported.

**F2 scope realism:** the prior cycle already built + locally-proved the meta. This cycle is a rename + version reconcile + closure-truth-up + publish-runbook + the public flip — a TRUE meta-framework minor, not a from-scratch packaging build. The real risk is not mechanics; it is the **stale/aspirational meta closure** (§10 F2-A) — the on-disk meta lists 11 deps, of which the build agent must verify each actually builds + the set is the minimal runtime closure, not the wishlist. Band: ~3–6 h AI-time (midpoint ~4.5 h) for the AUTONOMOUS portion, then an owner-run upload step (wall-clock, owner availability).

---

## §2 Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| The umbrella distribution | KEEP at `framework/loam-init/meta/` (existing meta), renamed `loam` → `loam-harness` | Prior cycle's home; reusing it is Lens-1 (don't reinvent). The dir name need not match the dist name. |
| Version source of truth | Each component's own `pyproject` `version`; meta lockstepped to 1.2.0 by the release process | `feedback_version_numbers_at_release_time` — do not fork the version scheme; the release bump owns it. |
| Publish runbook | NEW doc `docs/publish-to-pypi.md` (operator-facing) | Distribution doc, not component code; lives beside `install-from-source.md`. |
| Install-headline docs | `README.md` + `docs/install-from-source.md` (flip the published-set headline to `pip install loam-harness`) | Doc-only; the source path stays as the contributor path. |
| `AC.INST.S` (prior, local-wheelhouse) | UNCHANGED — sealed; this plan adds `AC.INSTPUB.S` for the published artefact | Prior AC proved local resolution; the new one proves the public flip. No retroactive edit. |
| The structure flatten (Q1, task #21) | OUT OF SCOPE — separable (per sealed plan §10.1 SEPARABILITY VERDICT) | Bundling it is the explicit scope error the prior plan named; D-PKG.1's meta-shape is flatten-neutral (see §3 D-PKG.1). |

---

## §3 Halt-and-surface BEFORE build — named decisions (autonomous + recorded)

All four named decisions are resolved here with recommendations. They are **autonomous (recorded)** except the F-PUBLISH public action and any credential step, which are **owner-gated** (§8). The dispatcher rules only if it disagrees with a recommendation.

### D-PKG.1 ★ARCHITECTURE — how the umbrella ships → **RECOMMEND: meta-package**

Three candidates:

1. **Meta-package** (`loam-harness` = dependencies-only distribution that depends on the component distributions; ships zero code). ← **RECOMMENDED.**
2. **Flattened single package** that vendors all component source under one distribution.
3. **Publish-the-components-plus-an-umbrella** — same as (1) mechanically; the umbrella IS the meta, the "plus components" is just that the deps are independently published. (1) and (3) are the same artefact; (3) is (1) stated with its precondition made explicit.

**Recommendation: meta-package (1).** Reasons:
- **Already built + locally proven.** The prior sealed cycle authored exactly this shape (`framework/loam-init/meta/pyproject.toml`, dependencies-only, `packages = []`). Choosing (1) is reuse, not new work (Lens-1).
- **Does not fight the flatten (task #21 / Q1).** Q1 flattens the *workspace's* `framework/framework` doubling — a `loam init` clone-depth concern, runtime-orthogonal to packaging (research doc §Q1: "Dev/run split… orthogonal to depth"). The meta-package depends on dist NAMES, not on source paths, so re-homing component source during a later flatten changes no dependency edge in the meta. A **flattened single package (2) WOULD fight the flatten**: it hard-codes the current source layout into one distribution's `packages.find`, so any later move forces a packaging rewrite. (1) is the only option that is flatten-stable.
- **Preserves the `loam.*` namespace.** Every component ships `loam.<sub>` as a PEP 420 implicit-namespace package; a flattened (2) that shipped a top-level `loam/` package would shadow the namespace and break imports (the existing meta's own header documents this hazard). (1) ships no code, so no shadow.
- **Independent component versioning + partial installs survive.** Users who want a subset still `pip install loam-cli loam-init …`; the meta is the convenience surface over the same closure.

**Trade-off named (F2):** a meta-package means N distributions on PyPI, not 1 — more upload surface + more name-claims. Accepted: the components are already separately packaged; the alternative (vendor-into-one) trades that for a permanent fight with Q1 and a namespace-shadow hazard. Net: (1) wins decisively.

### D-PKG.2 — runtime dependency closure (what ships on PyPI) → **RECOMMEND: the `loam` CLI runtime graph; dev/test-only excluded**

The closure is **what `loam <verb>` needs at runtime**, derived from `loam-cli`'s entry-point discovery, NOT every package in the tree.

**Verified closure roots (from the actual pyprojects, not assumption):**
- `loam-cli` (`framework/tools/loam/pyproject.toml`) — the `loam` console-script + `release`/`audit`/`flow` verbs; direct dep `PyYAML>=6`; imports `loam_amend`.
- The verb packages that register `loam.cli.subcommands` entry-points: `loam-init` (→ `loam-workspace-bootstrap`), `loam-amend` (`plugins/dev-sdlc/tools/loam-amend/`), and the dev-sdlc verb surfaces (`loam-mode`, `loam-pr-safety`, `loam-odd-extractor`, `loam-plugin-dev-sdlc`), `loam-per-project-pm`, `loam-plugin-loam-skills`, `loam-workspace-sync`, `loam-self-upgrade`.
- Their transitive runtime deps (each component's own `dependencies` block carries the inter-component bounds — `AC.PYPKG.2`, already declared).

**The build agent MUST verify the closure at EXAMINE** (not trust this list): start from `loam-cli`, walk `loam.cli.subcommands` + each verb's runtime imports, and admit only packages reachable as RUNTIME deps. The on-disk meta lists 11 deps; the agent confirms each (a) exists as a buildable distribution and (b) is runtime-reachable — dropping any that are dev/test-only and adding any reachable dep the wishlist missed. **WMS surface (per dispatch):** the work-management packages (`loam-objective-tracker`, `loam-scope-of-work`, `loam-per-project-pm`) ship ONLY IF the keep-pace/primary-persona runtime path imports them; the agent verifies reachability rather than assuming.

**Excluded (dev-only, do NOT ship in the user closure):** `programbench-revival*`, `loam-heavy-b-migrate`, `loam-acceptance-smoke`, `subloam-driver`, and any package reachable only from tests/CI. These are contributor tooling, not the `loam` command's runtime.

**Recommendation:** publish the runtime closure as the meta's dependency set; the agent's EXAMINE-verified reachable set is authoritative over both this list and the on-disk meta's current list. This is outcome-shape: the AC pins "the closure resolves + `loam` works," not the exact membership (method = the agent's reachability walk).

### D-PKG.3 — publish tooling → **RECOMMEND: manual `build`+`twine` runbook, owner-run upload (no new CI this cycle)**

Two candidates: (a) manual `python -m build` + `twine upload` runbook; (b) a GitHub Actions trusted-publisher (OIDC) workflow.

**Recommendation: (a) manual runbook this cycle**, with (b) named as the deferred follow-on. Reasons:
- **No `.github/workflows` exists today** (verified) and twine isn't installed — (b) is a net-new CI build, larger scope than the publish itself, and it requires repo-level PyPI trusted-publisher configuration that is itself an owner/public action.
- **Lens-1 reuse:** the `loam release` gate chain already exists as the pre-flight; the runbook composes on it (`loam release` gates green → `python -m build` per dist → `twine check` → owner runs `twine upload`).
- **No-secret-handling (LOCKED):** the runbook's upload step is explicitly **owner-run** — the agent authors the runbook + builds the artefacts + runs `twine check`, and STOPS. The agent never enters a token, never runs `twine upload`, never configures a credential. The runbook documents the exact command for Luke to run.

**Deferred (named, not this cycle):** the trusted-publisher CI workflow (b) is the right long-term shape (no token on anyone's laptop) — captured as a follow-on for when CI lands; it is the only fully-owner-controlled path and Luke may authorize it instead, in which case the agent authors the workflow file but Luke completes the PyPI-side trusted-publisher binding (still owner-gated).

### D-PKG.4 — namespace / name coexistence → **RECOMMEND: confirm three-identifier separation; no clash**

Three independent identifiers, verified against the tree:
- **Import name** = `loam.*` (PEP 420 implicit namespace; every component ships `loam.<sub>`, no top-level `loam/__init__.py`). Unchanged.
- **Distribution name** = `loam-harness` (the PyPI project; was `loam`, now changed because `loam` is taken by an unrelated config-manager).
- **Command name** = `loam` (the console entry-point in `loam-cli`; independent of dist name).

**No clash, confirmed:**
- The unrelated PyPI `loam` is a *distribution* name only; we neither claim it nor import from it. Our dist is `loam-harness`; our import namespace `loam.*` is local to our installed packages and never resolves to the PyPI `loam` distribution's modules (pip installs OUR `loam.*` packages from OUR dists).
- **Hazard to verify at build (AC.PKGPUB.3):** if a user has BOTH the unrelated PyPI `loam` AND `loam-harness` installed, do the import namespaces collide? The agent verifies in a cold env that installing `loam-harness` yields working `loam.*` imports and that the unrelated `loam` (if co-installed) does not shadow them — the AC pins "imports resolve to loam's modules," the method (namespace-package precedence test) is the agent's call.

---

## §4 Spec-objective placement

Binds to **AC.PYPKG.1** (one documented command resolves the graph) from the prior sealed cycle, extending it to the PUBLISHED surface, and to **AC.PO.1 + AC.PO.2** (VALUE_PROPOSITION prime objective — `feedback_value_proposition_as_prime_objective`): a non-technical user types ONE conventional install command and gets a working `loam` with zero dev-tree knowledge. Ladders up to the prime directive (per-user-tuned translation): the install surface is the first translation a user meets — `pip install loam-harness` is natural-language-adjacent; a 20-line editable-tier-order checkout is not.

---

## §5 Acceptance criteria (outcome-shape; method = builder's call)

| AC ID | Outcome | Verification (method is the builder's call) | Method-in-AC test |
|---|---|---|---|
| `AC.PKGPUB.1` | The `loam-harness` distribution resolves the runtime closure into ONE install command — installing it pulls the whole `loam` CLI dependency graph. | Install `loam-harness` from a local artefact index into a clean venv; assert the closure resolves with no missing-dependency error. | PASS — pins "one command resolves the graph"; the closure membership + index mechanism are the builder's call. |
| `AC.PKGPUB.2` | The renamed distribution carries dist-name `loam-harness` AND version `1.2.0` (lockstep with the tree), and every dist in the closure builds from its pyproject. | Build all closure dists; assert `loam-harness` metadata name == `loam-harness`, version == `1.2.0`; assert each wheel builds. | PASS — pins name + version + buildability outcomes, not the bump mechanism. |
| `AC.PKGPUB.3` | Dist-name `loam-harness`, import-name `loam.*`, command-name `loam` coexist with no collision against the unrelated PyPI `loam`; imports resolve to loam's own modules. | In a cold env, install `loam-harness`; assert `loam.*` imports resolve to loam's installed modules and the `loam` console-script is on PATH. | PASS — pins "no collision / imports resolve," not the namespace-precedence test method. |
| `AC.PUBTOOL.1` | A documented publish runbook exists that takes green pre-flight gates → built+checked artefacts → an OWNER-run upload step, with NO agent token-handling. | Runbook doc present at `docs/publish-to-pypi.md`; it names `loam release` pre-flight + `python -m build` + `twine check` as agent steps and `twine upload` as the owner step; grep confirms no token/credential entry by the agent. | PASS — pins the runbook's outcome shape + the owner-run boundary, not the exact command transcript. |
| `AC.PUBTOOL.2` | The artefacts the runbook produces pass `twine check` (PyPI-metadata-valid) BEFORE any upload. | Run `twine check` on every built dist; assert PASS for all. | PASS — pins metadata-validity, not the build backend. |
| `AC.INSTPUB.S` ★ **outcome-altitude** | A genuinely COLD environment (throwaway venv / fresh container, no source clone on PATH, no pre-arranged loam state) installs the built `loam-harness` artefact from the artefact index, then `loam --version` reports `1.2.0` and `loam --help` lists the real subcommands — with NO framework-tree clone or edit. | Spin a clean env; `pip install` (or `pipx install`) `loam-harness` from the local index; run the REAL `loam --version` + `loam --help` production entry-points; assert `1.2.0` + the subcommand list. | PASS — drives the production install + the real `loam` entry-point with zero pre-arranged state (`feedback_test_outcome_altitude_required`); method = the builder's cold-env mechanism. |

**Outcome-altitude AC present:** `AC.INSTPUB.S` (marked `outcome_altitude`), invoking the production `loam` entry-point in a cold env with no pre-arranged state. This IS the HARD-smoke-per-minor gate (`feedback_hard_smoke_per_minor_before_publish`) for this meta-framework minor.

**Note on the public-flip boundary:** every AC above is satisfiable against a LOCAL artefact index (`--find-links` wheelhouse) — the AUTONOMOUS portion proves the whole chain with ZERO public push, exactly as the prior cycle did. The PUBLIC `twine upload` (F-PUBLISH) is owner-gated (§8) and is NOT an AC the agent satisfies.

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

This is guidance, not prescription. The builder owns method.

1. **Manifest:** `docs/plans/conventional-install-pypi-publish.manifest.yaml` (paired with this plan).
2. **EXAMINE (closure truth-up, D-PKG.2):** walk the runtime closure from `loam-cli` + `loam.cli.subcommands` entry-points; produce the authoritative reachable runtime set; reconcile the on-disk meta's 11-dep list against it (drop dev-only, add missed runtime deps). Halt-and-surface if the reachable set contradicts the dispatch's named WMS expectation.
3. **Rename + lockstep:** dist-name `loam` → `loam-harness` in `framework/loam-init/meta/pyproject.toml`; version `1.1.0` → `1.2.0`; update the meta README + the explicit-install line to `loam-harness`.
4. **Tests authored FIRST (TDD):** one test per AC; `AC.INSTPUB.S` marked `outcome_altitude` + `slow` (cold-env, builds wheels).
5. **Build + local-index proof:** `python -m build` per closure dist into a local wheelhouse; install `loam-harness` from `--find-links` into a clean venv; run the AC suite incl. the cold-env outcome-altitude smoke.
6. **Publish runbook:** author `docs/publish-to-pypi.md` (D-PKG.3) — agent steps end at `twine check`; the `twine upload` step is documented for the OWNER.
7. **Docs headline flip:** README + `docs/install-from-source.md` published-set line → `pip install loam-harness`.
8. **`loam amend apply` + `loam amend seal`** against the manifest (`feedback_dispatch_explicit_loam_amend_apply`); smoke per the manifest's seal_test.
9. **HALT before any public action** — do not `twine upload`, do not claim the PyPI name, do not configure credentials (§8).

---

## §7 Out of scope (deferred + when)

- **The public PyPI upload + name-claim of `loam-harness`** (F-PUBLISH) — OWNER action; the runbook hands Luke the exact command. *When:* after this cycle seals green, on Luke's go.
- **The structure flatten (Q1, task #21)** — separable; bundling it is the prior plan's named scope error. *When:* rides alongside a future `workspace-bootstrap` cycle (research doc recommendation). D-PKG.1's meta-shape is flatten-neutral by design.
- **The trusted-publisher CI workflow (D-PKG.3 option b)** — net-new CI; deferred follow-on. *When:* when CI lands / if Luke authorizes the OIDC binding instead of a token upload.
- **Any component runtime-behavior change** — FENCED OUT; this cycle is packaging/distribution metadata + docs only.
- **`requires-python` reconciliation** (`install-from-source.md` says 3.13; `loam-cli` pyproject says ≥3.11 — §10 F2-B) — surfaced, not fixed here unless it blocks resolution.

---

## §8 Halt triggers (in-flight abort conditions)

The builder STOPS and surfaces if:
1. The runtime-closure walk (D-PKG.2) reveals a dependency that does NOT build from its pyproject, or a runtime dep that is NOT a published/publishable distribution — resolution may require a component change, which is OUT OF FENCE.
2. The dist-name/import-name test (`AC.PKGPUB.3`) shows the unrelated PyPI `loam` DOES shadow `loam.*` imports — a real namespace clash needs an owner ruling, not a silent workaround.
3. Any step would require entering a PyPI token, claiming the `loam-harness` name publicly, running `twine upload`, or configuring a credential — these are OWNER actions; the agent halts at `twine check` (no-secret-handling, LOCKED).
4. Satisfying an AC would require touching a sealed component's RUNTIME behavior (not just its pyproject metadata) without a manifest entry — halt rather than widen the fence.
5. The version lockstep would fork the scheme (e.g., the release tooling expects a different in-scope bump) — halt; do not hand-edit versions in a way the release process will overwrite.

---

## §9 Bookkeeping (post-build backfill items)

- `docs/STATE.md` — release register: add the meta-framework minor; record `loam-harness` as the published dist-name (was `loam`).
- `docs/release-roadmap.md` §8 register — the conventional-install/publish line.
- Parent plan `docs/plans/foundation-polish-cluster.md` §2 — backfill SUB-ITEM 1b status (autonomous portion sealed; public flip owner-gated).
- §14 method-decision register (this plan) — populated at build time with the D-PKG.* resolutions + seal SHAs.
- Task #21 — update Q2 status to "packaging sealed; public flip owner-gated."

---

## §10 / §14 F2 Ruthless Feedback + method-decision register

### §10 F2 — honest doubts (name the disagreement / evidence / alternative)

- **F2-A (load-bearing) — the on-disk meta closure is part-aspirational.** The existing `framework/loam-init/meta/pyproject.toml` lists 11 deps. *Evidence:* of those, `loam-amend`, `loam-pr-safety`, `loam-mode`, `loam-plugin-dev-sdlc`, `loam-odd-extractor` resolve only under `plugins/` (not `framework/`), and the meta was authored at version 1.1.0 against a planned layout. The list is a wishlist, not a verified runtime closure. *Alternative:* D-PKG.2 makes the agent's EXAMINE reachability walk authoritative over the on-disk list — the AC pins the resolved-closure outcome, so a wrong wishlist entry fails the build rather than shipping silently. This is why `AC.PKGPUB.1` proves *resolution*, not list-membership.
- **F2-B (minor) — `requires-python` divergence.** *Evidence:* `docs/install-from-source.md` states Python 3.13; `framework/tools/loam/pyproject.toml` states `>=3.11`. *Alternative:* surfaced in §7 as out-of-scope-unless-blocking; the cold-env smoke (`AC.INSTPUB.S`) will expose any real interpreter-floor mismatch empirically.
- **F2-C — version-fork already on disk.** *Evidence:* meta at `1.1.0`, tree at `1.2.0` — the meta missed the last lockstep bump. *Alternative:* `AC.PKGPUB.2` pins meta version == `1.2.0`; the release-process bump (not a hand-edit) is the correct mechanism (§8 trigger 5).
- **F2-D — N-distribution upload surface.** *Evidence:* meta-package (D-PKG.1) means every closure dist is its own PyPI project + name-claim, not one upload. *Alternative:* accepted trade (D-PKG.1 trade-off); the runbook enumerates the full upload set so Luke's owner-run step is one documented sequence, not a surprise.

### §14 method-decision register (populated at build time)
- D-PKG.1 — meta-package architecture — [SHA at seal]
- D-PKG.2 — runtime-closure membership (EXAMINE-verified) — [SHA at seal]
- D-PKG.3 — manual build+twine runbook, owner-run upload — [SHA at seal]
- D-PKG.4 — three-identifier non-collision — [SHA at seal]

---

## §11 Provenance trail (load-bearing sources, with refs)

- Owner-decided parameters — Luke 2026-06-04 (dispatch): dist `loam-harness`, command `loam`, lockstep 1.2.0, owner-run upload.
- Prior sealed packaging cycle — `docs/plans/sealed/foundation-polish-cluster-install.md:7-51` (`AC.PYPKG.1/2/3`, `AC.INST.S`, F-PUBLISH owner-gate, SEPARABILITY VERDICT).
- Existing meta-distribution — `framework/loam-init/meta/pyproject.toml` (dependencies-only, `packages = []`, dist-name `loam`, version `1.1.0`, the 11-dep list + the namespace-shadow header).
- `loam` console entry-point — `framework/tools/loam/pyproject.toml:[project.scripts] loam = "loam_cli.cli:main"` + `requires-python = ">=3.11"` + direct dep `PyYAML>=6`.
- Verb-package entry-points — `loam-init` (`framework/loam-init/pyproject.toml` `loam.cli.subcommands`), `loam-amend` (`plugins/dev-sdlc/tools/loam-amend/pyproject.toml`), dev-sdlc surfaces (`plugins/dev-sdlc/{pyproject.toml,pr-safety,odd-extractor,tools/loam-mode}`).
- Closure roots (verified imports) — `loam_cli` imports `loam_amend` + `yaml`; the 38-pyproject tree (31 under `framework/`, 6 under `plugins/`, 1 realpb).
- Research artefact — `docs/design/loam-structure-and-install-cost-2026-05-29.md` (Q2 blocked solely by no-PyPI-publish; `loam-cli` 404 on PyPI verified 2026-05-29; ~9 h band; flatten orthogonal to packaging).
- Versioning policy — `docs/release-versioning-policy.md` (SemVer; META-FRAMEWORK minor quality gate; version-at-release).
- Plan-doc conventions — `plugins/dev-sdlc/docs/conventions/plan-docs.md` (AC IDs scope-descriptive; manifest shape).
- BASELINE — `git rev-parse HEAD` == `32f362915e4712d6567310f9a1a4e20dbac30162` (2026-06-04).
