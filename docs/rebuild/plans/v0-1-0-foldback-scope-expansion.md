# OSS v0.1.0 publish — foldback (scope expansion) — plan-doc

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (M11/M12 lanes).
**Programme predecessor:** M11a — sealed GO at `c4f24bf` 2026-05-01 (`oss-v0-1-0-publish-m11a-sweep-report.md` §1).
**Reviewer foldback:** `<workspace>/.scratch/claude-output/loam-user-review-2026-05-03.md` — verdict FOLDBACK; 3 BLOCKERs + 4 HIGH + 3 LOW.
**Owner framing:** v0.1.0 is a flagship publish — "good enough to merit notice on its first publish." Cheap-ship (rewrite docs to match a non-working synth) explicitly rejected; build the product the docs describe.

---

## 1. Summary / TLDR

The reviewer's verdict is **correct**: the public synth tree at `c4f24bf` ships components but **not the CLI, not the dev-sdlc plugin, and the README's `loam init` verb does not exist anywhere in the codebase**. Foldback re-opens M11a; the path back to GO is six new amendments (FBE.1..FBE.6) plus a re-run of M11a-style sweep + reviewer + M12.

**Six amendments. Total AI-time: 165–340 min, midpoint ≈ 250 min (~4 h)**, plus owner gate for re-reviewed staging artifact (~30 min) plus M12 (~20 min). Sequential critical path; two amendments parallelise.

| # | Amendment | Objective (tightest framing) | AI-time band | Depends on |
|---|---|---|---|---|
| FBE.1 | `loam init` subcommand | Author + register `loam.cli.subcommands` builder `init = loam_amend.cli:build_init_subcommand` ... no, **per Decision A**: register from a NEW component package `loam-init` shipping in `framework/workspace-bootstrap/`'s adapter surface. Wraps existing `bootstrap_new_workspace` zero-arg-friendly. | 25–55 min | — |
| FBE.2 | Partition admit `framework/tools/loam/**` (CLI binary) | Reclassify `framework/tools/loam/**` from `dev_only` to `dev_and_public` AND scrub `loam_cli/` of dev-vocabulary. | 15–30 min | — |
| FBE.3 | Partition admit `plugins/dev-sdlc/**` (plugin) | Reclassify `plugins/dev-sdlc/**` from `dev_only` to a NEW partition shape (`plugins/dev-sdlc/{src,pyproject.toml,README.md}` ships; the dev-discipline subtree `{docs,hooks,templates,tools,dev-mode-manifest.yaml,seals,tests}` stays `dev_only`) per Decision B. | 30–60 min | — |
| FBE.4 | Inter-component dep rewrite (path/url specs) | Rewrite `workspace-bootstrap/pyproject.toml`'s 12 inter-component deps + dev-sdlc's 3 inter-component deps + new `loam-init`'s 1 dep as in-tree path specs per Decision C2. | 20–40 min | (independent of FBE.1..3 in source; affects M11a smoke-test fixture) |
| FBE.5 | Description scrub + LOW-fix sweep | Scrub `pOS v2` / `Phase 4` / `amendment #N` from 15 component pyproject `description` fields; fix double-step-5 in getting-started.md; remove "before public flip" framing in README; verify `~/.loam/` scaffolding works end-to-end post-FBE.1. | 15–35 min | FBE.1, FBE.2 |
| FBE.6 | Re-run M11a sweep + extended smoke | New AC.M11a.x extending smoke from `pip install -e ./two-leaf-components` to **`git clone → pip install everything → loam init /tmp/test-ws`**; re-push synth to staging; re-run reviewer agent. | 60–120 min | FBE.1..5 sealed |

**Sequencing diagram:**

```
FBE.1 ─┐
FBE.2 ─┼─→ FBE.5 ─→ FBE.6 ─→ (reviewer agent re-run) ─→ M12 publish-flip
FBE.3 ─┤
FBE.4 ─┘
       (FBE.1..4 can build in parallel via worktree isolation IF
       pos-amend supports it — see Risk #2; otherwise serialise
       per `feedback_serialize_amendment_builds`. Default: serialise.)
```

**Most likely wall-clock if serialised end-to-end:** ~4–6 hours AI + ~30 min owner gate.

**Recommendation: build it.** The docs already describe the right product shape (consistent across README + getting-started + 15 component refs). The synth's gaps are narrow and known. Cheap-ship would land an OSS launch that doesn't actually install — the opposite of the flagship framing.

---

## 2. Verified state of the gaps (re-check from code, not the reviewer's word)

I read each of the reviewer's claims against the canonical tree at `/Users/lukeivers/ivers-corp-pos-v2/` HEAD. The reviewer's diagnosis stands across all 7 BLOCKER + HIGH findings.

### 2.1 BLOCKER 1 — `loam init` does not exist

- **CLI registry:** `framework/tools/loam/src/loam_cli/cli.py` (verified lines 47–135) discovers subcommands only via `importlib.metadata.entry_points(group="loam.cli.subcommands")`. The dispatcher has no hardcoded subcommands.
- **Entry-point declarations:** only two `loam.cli.subcommands` entries exist anywhere in canonical:
  - `plugins/dev-sdlc/pyproject.toml:36-37` → `project = "loam.plugins.dev_sdlc.cli:build_project_subcommand"`
  - `plugins/dev-sdlc/tools/loam-amend/pyproject.toml:17` → `amend = "loam_amend.cli:build_amend_subcommand"`
- **No `init` builder:** `grep -rn "init" framework/tools/loam/src/loam_cli/` returns zero matches. No `build_init_subcommand` exists anywhere in the tree.
- **What does init's job today:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` exposes `bootstrap_new_workspace(...)` + a `cli_main` wired to a `pos-new-workspace` console-script (verified `pyproject.toml:60-61`). `pos-bootstrap` exists too. **Neither is registered as a `loam` subcommand.**

**Diagnosis stands.** `loam init` is a documented surface with no implementation.

### 2.2 BLOCKER 2 — `dev-sdlc` plugin doesn't ship

- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml:280` declares `glob: "plugins/dev-sdlc/**"` under `dev_only:`.
- **Plugin tree exists in canonical:** `plugins/dev-sdlc/{src,pyproject.toml,README.md,docs,hooks,templates,tools,dev-mode-manifest.yaml,seals,tests}` all present.
- **Synth-side absence:** M11a-3 sweep report §3.6 confirms `git ls-tree framework-only` shows zero `plugins/dev-sdlc/...` entries.

**Diagnosis stands.** And the M6b.0 reclassification narrative (lines 264–280 of the manifest) is correct that the *dev-discipline subtree* belongs in `dev_only`. The fix needs to *split* the plugin between user-facing surfaces (ship) and dev-discipline machinery (don't).

### 2.3 BLOCKER 3 — pip deps don't resolve

- **Workspace-bootstrap deps:** `framework/workspace-bootstrap/pyproject.toml:17-29` declares 12 bare PyPI names (`loam-orchestrator`, `loam-observability-aggregator`, `loam-safety-layer`, ...). None published.
- **Dev-sdlc plugin deps (would-ship if FBE.3 lands):** `plugins/dev-sdlc/pyproject.toml:14-16` declares 3 bare PyPI names (`loam-scope-of-work`, `loam-objective-tracker`, `loam-workspace-bootstrap`).
- **M11a smoke test (verified §3.5 of the sweep report):** only exercised `pip install -e ./scope-of-work -e ./primary-persona` — two leaves, no inter-deps. The bootstrap resolution path is genuinely untested.

**Diagnosis stands.** And it's broader than the reviewer noted: dev-sdlc plugin (when admitted by FBE.3) adds 3 more deps in the same shape.

### 2.4 HIGH 1 — `framework/<comp>/` paths in docs vs top-level synth

- **Docs:** consistently use `framework/<comp>/` (verified across 15+ files in `docs/components/`, README.md:35, `getting-started.md:63,77,175`).
- **Synth:** components at top level (verified M11a sweep report §3.5 + reviewer's `git ls-tree`).
- **Canonical canonical is `framework/<comp>/`:** `ls /Users/lukeivers/ivers-corp-pos-v2/framework/` shows the 15 components live under `framework/`.

**Diagnosis stands.** Per Decision D below: the synth-shape mismatch is a synth bug, not a doc bug. Docs describe the canonical layout; the synth pipeline strips the `framework/` prefix. Fix the synth.

### 2.5 HIGH 2 — `~/.loam/` referenced but never created

- **Docs:** README:88 + getting-started.md:88,98,182 + multiple component refs say `loam init` scaffolds `~/.loam/`.
- **Code:** `bootstrap_new_workspace` (the function `pos-new-workspace` calls) writes `~/.loam/canonical-cache/` per `new_workspace.py:638-642` (verified). So the *implementation* exists — it's just unreachable until `loam init` is wired.

**Diagnosis stands but tighter than the reviewer thought.** This is downstream of FBE.1 — fixing BLOCKER 1 fixes this automatically.

### 2.6 HIGH 3 — Hard-coded `lukeivers/loam` URL

- README.md:35 + getting-started.md:63 hard-code `https://github.com/lukeivers/loam`.
- M11a sweep §3.6 confirms staging push is to `lukeivers/loam-staging` (private). M12's role is to flip to `lukeivers/loam`.

**Diagnosis stands as M12-mechanics.** Not in foldback scope; rolls into M12.

### 2.7 HIGH 4 — README "before public flip" tense leakage

- README.md (verified) carries the rename-deferral note in the wrong tense.
- This is doc-prose-only. Lands in FBE.5.

**Diagnosis stands.**

### 2.8 LOW findings — surfaced for FBE.5

- LOW 1: getting-started.md double "step 5" — verified (lines 102 + 114).
- LOW 2: `loam memory` CLI absence narrative — fine; out of scope.
- LOW 3: 15 component pyproject `description` fields contain `pOS v2` / `Phase 4` / `amendment #N` / `M-series` leakage — verified across 12 of 15 pyproject.toml files. Bigger than the reviewer noted (it's not just `workspace-bootstrap`); needs a sweep edit at FBE.5.

### 2.9 No new ODD §2.5 violations discovered

I checked the partition manifest, the CLI dispatcher, and the bootstrap module for silent except branches or unbacked code paths while verifying. None found. The graceful-fallthrough-with-detection CDC (per `plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md`, established at M6c) is honoured in the surfaces I touched. **No halt-and-surface to escalate at planning time.**

---

## 3. Decisions A–E (Luke-call vs autonomous)

### Decision A — Where does `loam init` live?

**Recommendation (autonomous, mechanical):** **A1 (wrap)** — author a NEW component `framework/loam-init/` that ships a `loam.cli.subcommands` entry-point `init = loam.loam_init.cli:build_init_subcommand`. The builder constructs an argparse parser whose action calls `loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace(...)` (the existing function). The `pos-bootstrap` and `pos-new-workspace` console-scripts STAY (back-compat for any existing operator) — `loam init` is a NEW user-facing alias.

**Rationale + constraints:**
- A2 (rename) breaks back-compat for in-flight operators using `pos-new-workspace` and would touch every loam-mode/loam-amend reference. Higher blast radius.
- A3 (cheap-ship) explicitly rejected by Luke per the dispatch.
- A1 is additive: new component, new entry-point, no existing surface changes. Composes cleanly with M6a's plugin-discovery pattern (see `plugins/dev-sdlc/pyproject.toml:36-37` precedent).
- The new component keeps the existing `bootstrap_new_workspace` ODD-shape; the init builder is a 50–100 LOC argparse shim. ODD §2.5 clean — every line maps to AC.FBE.1.x.
- **Naming:** `framework/loam-init/` (top-level component dir, matches `framework/<comp>/` shape per Decision D) with package `loam.loam_init`. Console-script-equivalent already exists as `loam init` via the unified CLI dispatcher.

**Mark for ruling?** No. This is mechanical; clearly-correct path is A1 + ship `framework/loam-init/`.

### Decision B — What partition shape for `framework/tools/loam/**` and `plugins/dev-sdlc/**`?

**Recommendation (autonomous):**

- **B.1 — `framework/tools/loam/**` reclassify entirely to `dev_and_public`.** The CLI binary (`loam_cli/cli.py`) carries no internal-vocabulary leakage today (verified — the docstring references "M1g sealing time" but that's in a code comment a stranger can read; per FBE.5 scrub, a 2-line edit cleans the docstring). The CLI is intrinsically user-facing — the M11a partition rationale (line 196 of manifest) was excluding it as "publish tool" lumped together with `pos-publish-framework-only`. That was wrong: `loam_cli` is the user CLI; only `pos-publish-framework-only`, `heavy-b-migrate`, `orphan-plist-cleanup`, `upgrade-merge-resolver`, `loam-migrate-*` (the migration helpers) belong in `dev_only`. Split them out.

- **B.2 — `plugins/dev-sdlc/**` partition split** by sub-tree:
  - `dev_and_public` (ship): `plugins/dev-sdlc/src/**`, `plugins/dev-sdlc/pyproject.toml`, `plugins/dev-sdlc/README.md`.
  - `dev_only` (don't ship): `plugins/dev-sdlc/docs/**`, `plugins/dev-sdlc/hooks/**`, `plugins/dev-sdlc/templates/**`, `plugins/dev-sdlc/tools/**`, `plugins/dev-sdlc/dev-mode-manifest.yaml`, `plugins/dev-sdlc/seals/**` (covered by `**/seals/**` already), `plugins/dev-sdlc/tests/**` (covered by `**/tests/**` already).
  - Pre-existing universal `**/seals/**` and `**/tests/**` globs continue to win for `seals/` + `tests/` precedence (per manifest precedence rule #2 already in place).

**Rationale + constraints:**
- The user-facing surface a stranger needs is the plugin's `src/` (the `loam project ...` builder + the contribution registration). The dev-discipline corpus (CDCs, conventions, gate hooks, loam-amend tooling, dev-mode-manifest) was correctly classified as dev-only at M6b.0 and STAYS that way.
- The plugin's `tools/loam-amend/` ships a `loam amend` console-script. **Open sub-question:** does `loam amend` ship in v0.1.0? The dev-sdlc README and the architecture.md doc describe it as a dev-discipline tool — strangers using loam for non-development purposes don't need it. **Recommendation: NO, `loam amend` does NOT ship in v0.1.0** (it stays in `plugins/dev-sdlc/tools/loam-amend/` which is `dev_only` per the per-subtree split above). The reviewer's Lens 2 framing supports this: `loam amend` is a developer tool for building loam itself, not a primary-persona toolkit verb.
- This means v0.1.0 ships a CLI with **only `loam init` and `loam project`** registered. `loam project` is the dev-sdlc-plugin verb; per the plugin-shipping decision, it ships. If we don't want `loam project` either at v0.1.0, the dev-sdlc-plugin shipping needs to be deferred entirely (see B.alt below).

- **B.alt (escalate for ruling):** **Should the dev-sdlc plugin ship at v0.1.0 at all?** The reviewer's BLOCKER 2 frames it as documented-but-missing. But if loam's primary-persona framing is "general-purpose harness" (per CLAUDE.md Lens 2), and dev-sdlc is dev-specific, then v0.1.0 *could* ship the harness without dev-sdlc and rewrite the public-doc references to position dev-sdlc as a v0.2 plugin. **This is the only Luke-decision in the foldback** — the answer shapes the whole plan.

  **Sub-recommendation if Luke rules ship-dev-sdlc:** FBE.3 lands as planned; `loam project` ships; documentation stays as-is.

  **Sub-recommendation if Luke rules defer-dev-sdlc:** FBE.3 becomes a doc-rewrite amendment (remove dev-sdlc from positioning + architecture + `docs/plugins/dev-sdlc.md`); the plugin source stays in canonical for v0.1.x M-DEV-SDLC-V2 publish; v0.1.0 ships with only `loam init` registered.

  **My read of Luke's framing:** "good enough to merit notice on its first publish" + "attract Anthropic's attention" — **shipping a working plugin alongside the harness is the stronger demo**. The dev-sdlc plugin is the live demonstration of the contribution-protocol — without it, the plugin protocol is text-only. **Recommend: ship dev-sdlc at v0.1.0** (proceed with FBE.3 as planned).

**Mark for ruling?** Yes — B.alt is genuinely Luke's call. **Default if Luke unavailable: ship dev-sdlc** (stronger demo, plan is already shaped that way, foldback hours within band).

### Decision C — Inter-component pip deps

**Recommendation (autonomous):** **C2 (path-specs)** — rewrite the 12 + 3 + 1 = **16 inter-component dep declarations** as in-tree path specs.

**Shape:** PEP 508 + PEP 621 supports the `<name> @ file://...` form; setuptools accepts it. For deps within the same repo, the cleanest shape is:

```toml
dependencies = [
    "pydantic>=2",
    ...
    # In-tree component dependencies — pinned to the sibling directory
    # rather than PyPI (v0.1.0 publishes from-source; v0.2 considers
    # PyPI-publish per future-ideas-draft).
    "loam-orchestrator @ file://${PROJECT_ROOT}/orchestrator",
    ...
]
```

**Halt-and-surface concern:** PEP 508 path-specs in published wheels are an anti-pattern (PyPA discourages them; pip's resolver can balk depending on version). For an in-tree editable install via `pip install -e .`, they work; for a wheel-distributed install, they don't. v0.1.0 ships **source-only** (clone + `pip install -e ./<comp>` per repo per the README path), so file-specs are acceptable for v0.1.0. **Mark in plan: C2 is a v0.1.0-only shape; v0.2 PyPI-publish migration is a future-ideas-draft entry.**

**Rationale vs alternatives:**
- C1 (publish to PyPI) — real release work; account claims, signing, namespace registration; extends v0.1.0 by days. Out of band for "soon."
- C3 (document explicit per-comp install order) — works but pushes the resolver burden onto the user; bad UX. The reviewer flagged this.
- C2 — adds 16 path-spec edits across 3 pyproject.toml files (workspace-bootstrap, dev-sdlc, loam-init); zero infrastructure work; preserves the `pip install -e ./workspace-bootstrap` UX from the README.

**Mark for ruling?** No. Mechanical, reversible, only blocks v0.2 PyPI shape (which is already a separate planning item).

### Decision D — Path layout: `framework/<comp>/` or top-level

**Recommendation (autonomous):** **D.framework** — fix the synth pipeline to preserve the `framework/` prefix. Components live at `framework/<comp>/` in the published tree, matching docs.

**Rationale:**
- 15+ doc files reference `framework/<comp>/` paths. Rewriting all of them would be a 50+ edit sweep.
- The synth strip is a single edit in the partition pipeline (`framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` — verify at FBE.2 build time which transform strips the prefix; could be in `partition.py` or `synth.py`).
- Adding `framework/` to the `audit_roots` already preserves the structure on the *read* side; the issue is whether the synth pipeline rewrites paths on the *write* side. If it does, removing that rewrite is a one-line edit.

**Mark for ruling?** No.

### Decision E — `~/.loam/` scaffolding

**Recommendation (autonomous):** Verified at FBE.5-time that `bootstrap_new_workspace` creates `~/.loam/` (verified at planning: `new_workspace.py:638-642` writes `~/.loam/canonical-cache/`). Once FBE.1 wires `loam init` to call `bootstrap_new_workspace`, the scaffolding works. **No new code needed; AC.FBE.5.x verifies end-to-end.**

**Mark for ruling?** No.

### Decision-summary table

| Decision | Recommendation | Autonomous? | Notes |
|---|---|---|---|
| A — `loam init` shape | A1: new `framework/loam-init/` component + `loam.cli.subcommands` entry | Yes | |
| B — Partition for tools/loam + dev-sdlc | B.1 reclassify CLI; B.2 split-shape plugin | Yes | |
| B.alt — Ship dev-sdlc at v0.1.0? | YES (shipping is stronger demo) | **NO — Luke-call** | Default if no answer: ship |
| C — Inter-component deps | C2: file-specs (v0.1.0); v0.2 PyPI is FUTURE_IDEAS | Yes | |
| D — Path layout | `framework/<comp>/` (fix synth, not docs) | Yes | |
| E — `~/.loam/` | Auto-resolves once FBE.1 lands | Yes | Verify in FBE.5 |

---

## 4. Amendment ladder

Each amendment follows the loam amendment pattern (sealed-component fence + manifest + `loam amend apply` bookkeeping + seal commit). All built in canonical pos-v2 working tree. Per `feedback_serialize_amendment_builds`, build agents serialise unless worktree isolation is verified safe by `pos-amend`.

### FBE.1 — `loam init` as a registered subcommand (NEW component `loam-init`)

**Objective:** Make `loam init <path>` and `loam init .` work end-to-end as a registered `loam.cli.subcommands` entry, wrapping the existing `bootstrap_new_workspace` code path.

**ACs:**
- **AC.FBE.1.1** — NEW directory `framework/loam-init/` exists with `pyproject.toml` (package `loam-init`, version `0.1.0`), `src/loam/loam_init/{__init__.py,cli.py}`, `tests/test_AC_FBE_1_init_registered.py`.
- **AC.FBE.1.2** — `framework/loam-init/pyproject.toml` declares `[project.entry-points."loam.cli.subcommands"] init = "loam.loam_init.cli:build_init_subcommand"`.
- **AC.FBE.1.3** — `loam.loam_init.cli.build_init_subcommand(sub)` registers an argparse parser whose action calls `loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace(...)` with the user-supplied path argument and `--from <canonical>` either resolved from the cloned `framework/` checkout's git remote OR explicit `--from URL`.
- **AC.FBE.1.4** — `importlib.metadata.entry_points(group="loam.cli.subcommands")` after `pip install -e framework/loam-init/` returns an entry named `init` resolving to the builder.
- **AC.FBE.1.5** — `loam init /tmp/test-ws --from /Users/lukeivers/ivers-corp-pos-v2/` invocation (run from a venv with loam-cli + loam-init + workspace-bootstrap installed) succeeds and produces the expected workspace shape (verified by AC.FBE.6.x — full smoke).
- **AC.FBE.1.6** — Negative AC: zero changes to the `loam_cli/cli.py` dispatcher (entry-point discovery is the contract); zero changes to `bootstrap_new_workspace` signature or behaviour.
- **AC.FBE.1.S** — Sealed-component fence: `framework/loam-init/` (NEW) + sidecar bump for any touched component (none expected; if `bootstrap_new_workspace` needs a one-line wrapping shim, then `framework/workspace-bootstrap/` joins the fence — surface and decide at build time).

**Halt triggers:**
1. The init verb requires reaching into `bootstrap_new_workspace`'s internals beyond its public signature → halt; surface what private API is needed; defer to a refactor amendment.
2. `loam init .` (current dir) semantics conflict with `pos-new-workspace`'s `--init-existing` flag in surprising ways → halt; surface.
3. `pip install -e framework/loam-init/` fails because `loam-cli` or `loam-workspace-bootstrap` aren't in the venv → halt; document install order.
4. The CLI dispatcher's discovery loop (cli.py:50-99) silently swallows the new builder → halt; this is an existing graceful-fallthrough-with-detection violation in the dispatcher (it's marked `# pragma: no cover — defensive` but should still surface via WARNING — verify behaviour).

**Dependencies:** None on other FBE.* amendments. Can build in parallel with FBE.2, FBE.3, FBE.4 if worktree-isolation safe (default: serialise).

**AI-time band:** **25–55 min, midpoint 40 min.** Justification: amendment build (single sealed component, source + tests + seal) per rubric = 10–20 min; this is on the upper end because (a) new component requires `pyproject.toml` + package layout, (b) requires editable-install refresh + cross-component import verification, (c) entry-point registration test needs `importlib.metadata` correctness. ~80–120 tool calls. Formula `wall_clock_minutes ≈ 0.1–0.15 × tool_calls` = 8–18 min on the optimistic side; widen to 25–55 min for the new-component overhead.

### FBE.2 — Partition admit `framework/tools/loam/**` (CLI binary ships)

**Objective:** Reclassify the unified `loam` CLI from `dev_only` to `dev_and_public` so the synth tree includes `framework/tools/loam/` (and the `pip install -e framework/tools/loam` command in the README actually finds something).

**ACs:**
- **AC.FBE.2.1** — `publish-mode-manifest.yaml`'s `dev_only:` block REMOVES `glob: "framework/tools/loam/**"`.
- **AC.FBE.2.2** — `dev_and_public:` block ADDS `glob: "framework/tools/loam/**"`.
- **AC.FBE.2.3** — `dev_only:` retains the legitimately-dev tools: `framework/tools/heavy-b-migrate/**`, `framework/tools/orphan-plist-cleanup/**`, `framework/tools/upgrade-merge-resolver/**`, `framework/tools/pos-publish-framework-only/**`, `framework/tools/loam-migrate-host-config/**`, `framework/tools/loam-migrate-launchd-labels/**`, `framework/tools/loam-migrate-dormancy-config/**`, `framework/tools/loam-memory-inspect/**`. (No reclassification beyond `loam/` itself.)
- **AC.FBE.2.4** — Synth re-run from a clean checkout: `framework-only` branch tree includes `framework/tools/loam/{pyproject.toml,src/loam_cli/cli.py,...}` and the `loam` console-script's pyproject entry survives.
- **AC.FBE.2.5** — Existing partition tests (per `framework/tools/pos-publish-framework-only/tests/`) continue to pass post-reclassification; specifically, the audit-completeness test that verifies every leaf path classifies into exactly one bucket.
- **AC.FBE.2.6** — Negative AC: no changes to `loam_cli/cli.py` source itself (FBE.5 handles description scrub).
- **AC.FBE.2.S** — Sealed-component fence: `framework/tools/pos-publish-framework-only/` (manifest owner) + `framework/tools/loam/` (the moved-class component, sidecar bump per the dev_only→dev_and_public reclassification convention).

**Halt triggers:**
1. The synth pipeline's path-rewrite logic strips `framework/tools/` even when admitted → halt; this is the Decision D issue manifesting; needs synth-pipeline edit (out of FBE.2's pyproject-only scope; surface for FBE.2 expansion or new amendment).
2. `loam_cli/` package depends on dev-only modules (e.g. imports from `loam_amend` directly rather than via entry-point discovery) → halt; surface the dep cycle.
3. Audit-completeness test fails → halt; surface what classification is now ambiguous.

**Dependencies:** None on other FBE.* in source. **Couples with FBE.4 + FBE.6 indirectly** — FBE.4 must rewrite loam-cli's deps if any are inter-component (verify at build time: loam-cli's pyproject only depends on `PyYAML>=6` per inspection, no inter-component deps; OK).

**AI-time band:** **15–30 min, midpoint 22 min.** Justification: tiny manifest edit + sweep test refresh + sidecar bump. ~50–80 tool calls.

### FBE.3 — Partition split-admit `plugins/dev-sdlc/**` (plugin source ships, dev-discipline doesn't)

**Objective:** Per Decision B.2, split the `plugins/dev-sdlc/**` admission so the user-facing plugin source ships while the dev-discipline corpus stays `dev_only`.

**ACs:**
- **AC.FBE.3.1** — `publish-mode-manifest.yaml` REMOVES the broad `glob: "plugins/dev-sdlc/**"` from `dev_only:`.
- **AC.FBE.3.2** — ADDS to `dev_and_public:`:
  - `glob: "plugins/dev-sdlc/src/**"`
  - `path: plugins/dev-sdlc/pyproject.toml`
  - `path: plugins/dev-sdlc/README.md`
- **AC.FBE.3.3** — ADDS to `dev_only:` (explicit subtree-globs):
  - `glob: "plugins/dev-sdlc/docs/**"`
  - `glob: "plugins/dev-sdlc/hooks/**"`
  - `glob: "plugins/dev-sdlc/templates/**"`
  - `glob: "plugins/dev-sdlc/tools/**"` (covers `loam-amend` + `loam-mode`)
  - `path: plugins/dev-sdlc/dev-mode-manifest.yaml`
- **AC.FBE.3.4** — Pre-existing universal globs `**/seals/**` + `**/tests/**` continue to wind `seals/` + `tests/` from the plugin tree per partition-precedence rule #2 (verify in test).
- **AC.FBE.3.5** — Synth re-run produces a synthetic tree containing `plugins/dev-sdlc/{src,pyproject.toml,README.md}` and ZERO files under `plugins/dev-sdlc/{docs,hooks,templates,tools,seals,tests,dev-mode-manifest.yaml}`.
- **AC.FBE.3.6** — Audit-completeness test passes; partition-precedence test passes (specifically the `**/seals/**` and `**/tests/**` precedence over the new `plugins/dev-sdlc/src/**` admission).
- **AC.FBE.3.7** — A stranger doing `pip install -e plugins/dev-sdlc/` against the synthetic tree successfully installs the plugin (deps resolve via FBE.4; the `loam project` console-script becomes invokable).
- **AC.FBE.3.8** — Negative AC: zero changes to plugin SOURCE files; this is partition-only.
- **AC.FBE.3.S** — Sealed-component fence: `framework/tools/pos-publish-framework-only/` (manifest owner) + `plugins/dev-sdlc/` (the reclassified component).

**Halt triggers:**
1. The plugin's `src/` imports modules that LIVE under `tools/loam-amend/` or other dev-only paths → halt; surface the cross-subtree import; this is an ODD §2.5 violation (the plugin's user-facing surface has a hidden dep on its dev-discipline subtree).
2. Plugin's `pyproject.toml`'s `package-dir` declaration assumes a layout that breaks when the dev-discipline subtree disappears → halt; verify package discovery at build.
3. **Major halt:** if Luke ruled "defer dev-sdlc to v0.1.x" per Decision B.alt, FBE.3 is rewritten as a doc-rewrite amendment (remove dev-sdlc references from positioning.md + architecture.md + remove `docs/plugins/dev-sdlc.md`); the plugin reclassification doesn't happen.

**Dependencies:** None on FBE.1, FBE.2 in source (independent partition lines). Output gates FBE.6's stranger-clone smoke (the smoke needs the plugin to install).

**AI-time band:** **30–60 min, midpoint 45 min.** Justification: more partition entries than FBE.2 (8 globs vs 1) + stronger smoke verification (pip install + import test) + the partition-precedence verification needs careful test authoring. ~100–150 tool calls.

### FBE.4 — Inter-component pip deps as path-specs

**Objective:** Per Decision C2, rewrite the 16 inter-component bare-name deps as `<name> @ file://...` path-specs that resolve in-tree.

**ACs:**
- **AC.FBE.4.1** — `framework/workspace-bootstrap/pyproject.toml`'s 12 inter-component deps rewritten as path-specs (relative to the workspace root post-clone; the literal value is `<name> @ file://${PROJECT_ROOT}/<comp>` OR PEP 508 path syntax that pip accepts in editable installs).
- **AC.FBE.4.2** — `plugins/dev-sdlc/pyproject.toml`'s 3 inter-component deps rewritten in the same shape.
- **AC.FBE.4.3** — `framework/loam-init/pyproject.toml`'s 1 inter-component dep (`loam-workspace-bootstrap`) declared as a path-spec.
- **AC.FBE.4.4** — `pip install -e ./workspace-bootstrap` from a fresh clone of the synthetic tree succeeds (dependency resolution finds the sibling directories).
- **AC.FBE.4.5** — Path-specs use `${PROJECT_ROOT}` or pip-compatible relative form that works regardless of the user's clone location.
- **AC.FBE.4.6** — No changes to `[project.entry-points.loam.bootstrap.contributions]` block in workspace-bootstrap (preserved per ODD §2.5 fence).
- **AC.FBE.4.7** — A `requirements.txt`-style operator-readable install order document is added at `docs/install-from-source.md` covering the four-step path: (1) clone, (2) `pip install -e ./loam-cli`, (3) `pip install -e ./workspace-bootstrap` (which resolves siblings), (4) `pip install -e ./plugins/dev-sdlc` (if Decision B.alt = ship). The README + getting-started.md retain the simpler `loam init` flow as the headline path.
- **AC.FBE.4.S** — Sealed-component fence: `framework/workspace-bootstrap/` + `plugins/dev-sdlc/` + `framework/loam-init/`. Three components.

**Halt triggers:**
1. Pip's path-spec syntax doesn't accept `${PROJECT_ROOT}` or relative-form variables → halt; surface the actual constraint and rewrite as absolute `file://` paths that get rewritten at install time, OR fall back to documenting the explicit per-component install order (Decision C3 fallback).
2. Build agent discovers a circular dep between two components (e.g. `workspace-bootstrap` ↔ `primary-persona`) → halt; this is a real architectural finding; surface for refactor planning.
3. The `loam-init` component's dep on `loam-workspace-bootstrap` creates an FBE.1 ↔ FBE.4 ordering hazard → resolve by sequencing: FBE.1 lands `loam-init/pyproject.toml` with bare-name dep; FBE.4 rewrites it to path-spec. This is the canonical sequence — surface if any other ordering is required.

**Dependencies:** Touches `loam-init/pyproject.toml` (created at FBE.1) — must seal AFTER FBE.1. Independent of FBE.2, FBE.3 in source but functionally needed before FBE.6's smoke can pass.

**AI-time band:** **20–40 min, midpoint 30 min.** Justification: 3 pyproject.toml edits + 1 new doc file + smoke-verification test. ~70–110 tool calls.

### FBE.5 — Description scrub + LOW-fix sweep + ~/.loam verify

**Objective:** Final cleanup pass — scrub dev-vocabulary leakage from 15 component pyproject `description` fields; fix README's "before public flip" tense; fix getting-started.md double "step 5"; verify `loam init` actually scaffolds `~/.loam/` post-FBE.1.

**ACs:**
- **AC.FBE.5.1** — Scrub `pOS v2`, `Phase 4`, `amendment #N`, `M1`/`M-series`, `M1g`, etc. dev-vocabulary from `description` fields in: `framework/{cost-governance,observability-aggregator,orchestrator,objective-tracker,scope-of-work,safety-layer,primary-persona,reversibility-primitive,workspace-bootstrap,telegram-interface,self-upgrade,self-correction,workspace-sync}/pyproject.toml` (13 components verified leaky at planning) + `framework/{dormancy,hands-off-lifecycle}/pyproject.toml` (verify at build) + `plugins/dev-sdlc/pyproject.toml` if shipping per Decision B.alt + `framework/tools/loam/pyproject.toml` + `framework/loam-init/pyproject.toml`.
- **AC.FBE.5.2** — Verified replacement vocabulary: `pOS v2` → `loam`; `Phase 4+ extension protocol` → `the plugin contribution protocol`; `amendment #65` → drop the parenthetical; `M-series` → drop or describe in user-facing terms.
- **AC.FBE.5.3** — `framework/tools/loam/src/loam_cli/cli.py` docstring scrub: `M1g sealing time`, `loam-rename-decisions.md`, `M6a`, `M6b.1` references either removed or rephrased to user-facing terms (the *behaviour* description stays; the *amendment numbers* go).
- **AC.FBE.5.4** — `README.md` "before public flip" note (HIGH 4) rewritten in present tense or removed entirely.
- **AC.FBE.5.5** — `docs/getting-started.md` double "step 5" (LOW 1) re-numbered.
- **AC.FBE.5.6** — `loam init /tmp/test-fbe5-ws --from /Users/lukeivers/ivers-corp-pos-v2/` smoke verification: post-invocation, `~/.loam/` exists with the expected scaffolding (matches the `bootstrap_new_workspace` contract). HIGH 2 closes by verification, no code edit needed.
- **AC.FBE.5.7** — Negative AC: no behaviour changes; this is a scrub + smoke amendment.
- **AC.FBE.5.S** — Sealed-component fence: every component whose pyproject was edited (likely all 15 + tools/loam + loam-init + dev-sdlc) → fence is wide. Per `feedback_amendment_dispatch_speedups`, scope test rerun to touched-only.

**Halt triggers:**
1. A description-scrub edit changes the substance of what the component does (not just vocabulary) → halt; surface the substantive change candidate; do not silently rewrite product description.
2. `loam init` smoke fails → FBE.1 has a regression; halt and feedback to FBE.1.
3. README rewrite drifts beyond the named "before public flip" sentence → halt; ODD §2.5 violation (out-of-scope edit).

**Dependencies:** Sequenced AFTER FBE.1 (needs `loam init` working) and AFTER FBE.2 (needs `loam_cli/` admitted to ship for the docstring scrub to land in synth). Independent of FBE.3 unless dev-sdlc ships per Decision B.alt.

**AI-time band:** **15–35 min, midpoint 25 min.** Justification: many small edits across many files (15 pyproject.toml description scrubs, 2 doc fixes, 1 docstring scrub, 1 smoke run). Per rubric, this is "tiny docs edit" × scale → upper-bound the band. ~80–130 tool calls.

### FBE.6 — Re-run M11a sweep with extended smoke + reviewer re-run

**Objective:** Close the foldback cycle. Re-synth canonical HEAD; re-push to `lukeivers/loam-staging` (or rotate to a clean `lukeivers/loam-staging-v2` if the dirty staging history is awkward); run the M11a sweep with an EXTENDED smoke that exercises the documented install path end-to-end; re-dispatch the stranger-perspective reviewer agent; close on GO or surface fresh halt.

**ACs:**
- **AC.FBE.6.1** — `pos-publish-framework-only` re-runs from canonical HEAD post-FBE.5; produces a fresh `framework-only` branch SHA. Synth exit code 0.
- **AC.FBE.6.2** — All 8 AC.M11a.* sweeps from the M11a-3 sweep report re-run and PASS (no regression on banned-literal grep, source-side substitution grep, wired-component sweep, MFBM dep sweep, etc.).
- **AC.FBE.6.3** — **EXTENDED smoke (NEW vs M11a-3 §3.5)** — full documented install path:
  ```
  cd /tmp && rm -rf loam-fbe6-test
  git clone --branch framework-only --single-branch \
    /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6-test
  cd loam-fbe6-test
  python3.13 -m venv .venv
  .venv/bin/pip install -e framework/tools/loam
  .venv/bin/pip install -e framework/workspace-bootstrap
  .venv/bin/pip install -e framework/loam-init
  .venv/bin/pip install -e plugins/dev-sdlc       # if FBE.3 shipped
  .venv/bin/loam --version                          # works
  .venv/bin/loam init /tmp/loam-fbe6-test-ws --from /tmp/loam-fbe6-test
  ls /tmp/loam-fbe6-test-ws/{framework,workspace,.claude}
  ls ~/.loam/                                       # scaffolded
  ```
  Every step succeeds; final `loam init` produces a runnable workspace.
- **AC.FBE.6.4** — Push synth to staging (`git push staging framework-only:main`); confirm remote SHA matches.
- **AC.FBE.6.5** — Re-dispatch the stranger-perspective reviewer agent (new instance, no prior context) against the new staging tree. Reviewer's verdict = GO or surfaces a NEW BLOCKER not covered by FBE.1..5.
- **AC.FBE.6.6** — Sweep report authored at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6-sweep-report.md`.
- **AC.FBE.6.7** — Negative AC: zero source/doc edits during FBE.6; if the reviewer surfaces a new BLOCKER, foldback re-opens (do NOT silently fix in FBE.6).
- **AC.FBE.6.S** — Sealed-component fence: NONE — this is a sweep + smoke + review amendment with no source-side delta. Narrative anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6` per M11a precedent.

**Halt triggers:**
1. Reviewer agent surfaces a new BLOCKER → halt; re-open foldback; author FBE.7..N.
2. Extended smoke fails at any step → identify which FBE.x amendment regressed; halt and surface for fix.
3. Synthesis re-run fails → halt; partition manifest is in an invalid state.
4. Staging push fails → halt; surface remote/auth issue.
5. Reviewer agent observes the install path works but raises a new HIGH-severity finding (e.g. install path works but the resulting `claude` session immediately errors) → surface and triage; HIGH-severity findings may or may not block v0.1.0 GO.

**Dependencies:** All of FBE.1..5 sealed.

**AI-time band:** **60–120 min, midpoint 90 min.** Justification: synth (5 min cold) + 8 sweep ACs (20 min batched) + extended smoke (20 min — multi-step pip install + loam init — venv churn is real) + reviewer agent dispatch (10–30 min — Sonnet, 200–400 tool calls per the M11a-3 review precedent) + report authoring (10 min) + staging push (5 min). Wider band because the reviewer agent's wall-clock is hard to bound.

### Sealed-component fence summary across the ladder

| Amendment | Components in fence | Notes |
|---|---|---|
| FBE.1 | `loam-init` (NEW) | + maybe `workspace-bootstrap` if shim needed |
| FBE.2 | `pos-publish-framework-only` + `tools/loam` | partition + reclassified component |
| FBE.3 | `pos-publish-framework-only` + `dev-sdlc` | partition + reclassified plugin |
| FBE.4 | `workspace-bootstrap` + `dev-sdlc` + `loam-init` | three pyprojects |
| FBE.5 | (wide — every component edited) | low-touch per file |
| FBE.6 | none (HOL narrative only) | sweep amendment |

---

## 5. Cycle gates

The foldback closes when:

1. **FBE.1..5 each sealed** with their own `loam amend apply` + seal commit; method-decision register backfilled per `feedback_amendment_dispatch_speedups`.
2. **FBE.6 closes GO** — sweep PASS, extended smoke PASS, reviewer agent verdict GO (or non-blocking HIGH only).
3. **M12 publish-flip dispatches** per master plan §5 M12 row — squashed initial commit on `lukeivers/loam:main`, tag v0.1.0, release notes.
4. **§14 master plan backfill** in `oss-v0-1-0-publish.md` — record FBE.1..6 SHAs against the M11a-foldback narrative.

**Owner gate-time additive to AI-time:**
- Re-review of staging tree by reviewer agent: ~15 min (subagent wall-clock; rolled into FBE.6).
- Owner skim of FBE.6 sweep report: 5–15 min (per `feedback_summarize_and_surface_decisions`).
- Owner gate at M12: 5–15 min.

**Total foldback-to-publish: ~4–6 h AI + ~30–60 min owner gate.**

---

## 6. Risk register

### Risk 1 — Decision B.alt (ship dev-sdlc?) genuinely needs Luke

If Luke unreachable, the autonomous default is "ship" but if he later rules "defer," FBE.3 + FBE.4 + parts of FBE.5 + FBE.6 need to rebuild. Mitigation: **escalate before launching any FBE build**; the question is binary and Luke can answer in two messages.

### Risk 2 — Worktree-isolation parallel builds vs serialised

`feedback_serialize_amendment_builds` says two amendment builds in one git tree race on `index.lock` / `pos-amend` / tests. FBE.1..4 are nominally parallelisable (disjoint ACs), but without verified worktree isolation, default to serial. **Wall-clock cost of serial:** ~25+22+45+30 = 122 min for FBE.1..4 (vs ~45 min critical path if parallel). If Luke wants the parallel path, dispatch FBE.1, 2, 3, 4 to four separate worktrees and verify pos-amend handles cross-worktree apply correctly first. Mitigation: **default serial unless Luke greenlights parallel + verifies pos-amend worktree-safe**.

### Risk 3 — Partition test coverage is shallow

The current audit-completeness test verifies *every leaf classifies* but does NOT verify *the synth output matches expectations file-for-file*. After FBE.2 + FBE.3 reclassification, a regression in synth pipeline path-rewriting could go undetected. Mitigation: AC.FBE.2.4 + AC.FBE.3.5 require concrete `git ls-tree framework-only | grep ...` assertions in the build verification, not just partition-completeness.

### Risk 4 — `loam-cli`'s `_LOGGER.warning(... # pragma: no cover — defensive)` exception swallows

`framework/tools/loam/src/loam_cli/cli.py:74,84,92,128` carries 4 silent-except branches with `# pragma: no cover — defensive` markers. These are graceful-fallthrough-with-detection per the M6c CDC (logger.warning surfaces them) — so they're NOT ODD §2.5 violations technically. But the `# pragma: no cover` annotation means they're never exercised by tests. **Halt-and-surface (low priority):** at FBE.2 build time, the build agent should at minimum verify the WARNING actually emits in the failure case (not silently log to a discarded handler). Defer to FBE.2's halt triggers.

### Risk 5 — PEP 508 path-spec edge cases

If pip's resolver behaves differently on macOS vs Linux for `file://${PROJECT_ROOT}/<comp>`-style specs (particularly older pip versions), strangers on Linux could hit failures the macOS-developed FBE.4 didn't catch. Mitigation: AC.FBE.6.3's smoke runs locally on macOS; consider running the smoke on a Linux container for v0.1.x; for v0.1.0 GO, accept the macOS-verified path and document the Linux caveat.

### Risk 6 — Reviewer agent at FBE.6 surfaces a NEW BLOCKER

A second-pass reviewer reading a working install path will probe deeper than the first pass. They may find: (a) the `claude` session post-`loam init` immediately errors because the persona scaffold needs additional config, (b) the `~/.loam/` scaffold leaks a path or value that wasn't anticipated, (c) the architecture's "primary persona" claim doesn't match what a stranger sees on first session. Mitigation: budget for **one foldback round** (FBE.7..N) within the v0.1.0 lane; if a SECOND foldback round is needed, escalate to "is v0.1.0 too ambitious for Luke's timeline" — surface to Luke for re-shaping (e.g. ship as v0.0.x experimental).

### Risk 7 — Synth pipeline path-rewrite (Decision D)

If the synth pipeline's path-rewrite logic is non-trivially baked in (e.g. iterates partition entries and strips the leading `framework/` segment), fixing Decision D's `framework/<comp>/` shape requires editing `synth.py` itself, not just the manifest. This blows FBE.2 and FBE.3's scope — they'd need a sub-amendment for the synth-pipeline edit. Mitigation: at FBE.2 build start, the build agent reads `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` first to determine whether path-rewrite happens; if yes, FBE.2 halts and surfaces a sub-amendment requirement.

### Risk 8 — `loam amend apply` scope creep across amendments

`loam amend apply` on an amendment whose plan-doc is THIS file (foldback) would need a new manifest. Each FBE.x amendment authors its own manifest YAML alongside the existing pattern; the foldback plan-doc is the *parent* spec, not an amendment manifest itself. **Mitigation:** every FBE.x amendment dispatch carries its own manifest authoring step before `loam amend apply` runs. The dispatcher (the operator running this plan) authors the manifest as part of each FBE.x build dispatch, per the existing convention.

### Risk 9 — Force-replan triggers

The plan should be re-opened if any of these occur:
- Decision B.alt ruled "defer dev-sdlc" → FBE.3 reshapes from partition to docs.
- Synth pipeline edit needed (Risk 7) → FBE.2.5 or new amendment FBE.2b inserted.
- Reviewer agent surfaces a new BLOCKER → FBE.7..N opens, M12 deferred.
- Pip path-spec doesn't work cross-platform → FBE.4 rewrites to Decision C3 (per-component install order doc); UX degrades but install works.

---

## 7. References

- **Reviewer report:** `<workspace>/.scratch/claude-output/loam-user-review-2026-05-03.md` (3 BLOCKER + 4 HIGH + 3 LOW).
- **M11a sweep (precedent + sweep contract):** `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md`.
- **Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Substitution table (M9):** `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py` (12 entries post-#102).
- **CLI dispatcher:** `framework/tools/loam/src/loam_cli/cli.py`.
- **Workspace-bootstrap CLI:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py`.
- **Dev-sdlc plugin:** `plugins/dev-sdlc/{pyproject.toml,src,docs,tools,...}`.
- **Plan-doc template precedent:** `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.md` (M3 — rich AC + halt + risk shape).
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code).
  - `feedback_agent_prompts_scope_only` (FBE.x dispatches will carry objective + scope + halt only).
  - `feedback_summarize_and_surface_decisions` (Decision A–E + recommendations).
  - `feedback_serialize_amendment_builds` (default serial in §1 sequencing).
  - `feedback_subagent_odd_violation_halt` (every FBE.x carries the halt-and-surface clause).
  - `feedback_dispatch_explicit_pos_amend_apply` (every FBE.x dispatch names `pos-amend apply` / `loam amend apply`).
  - `feedback_duration_estimation_rubric` (AI-time bands per category + formula).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (FBE.5 ACs are tight on what gets edited).
  - `feedback_critical_thinking_on_deviations` (Decisions A–E are the resolution-enumeration applied).
  - `feedback_value_proposition_as_prime_objective` (FBE.1..6 ladder up to AC.PO.1+AC.PO.2 via making the docs true).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified" claim in §2 has a path/line citation).
  - `feedback_swarming_recursive_decomposition` (Lens 5 — six amendments each with tighter ACs than the parent foldback objective).

---

## 8. Method-decision register (placeholder for post-build SHAs)

(Populated as each FBE.x amendment seals + the master plan §14 backfill commit.)

### FBE.1 — `loam init` subcommand
- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe1.md` (authored at `b111340` by FBE.1 build agent before code per `feedback_plan_before_code`).
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe1.manifest.yaml` (amendment #103, committed at `2ce6ae2`).
- Source commit (loam-init NEW component + tests): `2c6b488`.
- Partition admission commit (`framework/loam-init/**` → `dev_and_public`): `608ecea`.
- Apply commit: `6d5a3f1`.
- Seal commit: `21b9480`.
- ACs satisfied: AC.FBE.1.{1,2,3,4,5,6,7,8,S} (9/9 — sub-plan tightened AC.FBE.1.3 to drop loose auto-detect language; added AC.FBE.1.7 for bare-name dep + AC.FBE.1.8 for partition admission per §2 Surface #1).
- Verification: 14/14 component tests pass; 3/3 partition tests pass; `loam init --help` works through the unified CLI dispatcher; cross-component seal-diff sweep at seal-time green (16 components).

### FBE.2 — Partition admit `framework/tools/loam/**`
- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.md` (authored at `8f0e778` by FBE.2 build agent before code per `feedback_plan_before_code`).
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.manifest.yaml` (amendment #104, committed at `cb4d61f`).
- Source commit (loam-cli sidecar shape: SEAL_COMMIT + test_no_sealed_amendments.py): `0f75364`.
- Partition admission commit (manifest YAML reclassification + 2 test fixture spot-check edits): `80d52ab`.
- Apply commit: `af47c45`.
- Seal commit: `8d2b770`.
- ACs satisfied: AC.FBE.2.{1,2,3,4,5,6,7,S} (8/8).
- Verification: 70/70 partition tests pass; 1/1 loam-cli fence test passes; AC.FBE.2.4 verified via direct `synthesise_framework_only` invocation against post-FBE.2 HEAD — synth tree-SHA `da4e2b9` carries all 5 expected `tools/loam/` leaves (`pyproject.toml`, `README.md`, `src/loam_cli/{__init__.py, __main__.py, cli.py}`); `tests/` correctly drops via `**/tests/**` precedence.
- Halt-and-surface from build (recorded for the dispatcher): synth pipeline strips `framework/` prefix on shipping paths (lines 302-312 of `synth.py`) — Risk #7 verified BENIGN for FBE.2 (mirrors FBE.1's `loam-init/` synth shape; Decision D out of scope here; documented as expected behaviour in sub-plan §2 Surface #1). Pre-existing dirty `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (unrelated main-session edit) was stash-then-pop'd to unblock `loam amend seal` (it requires a clean tree); no FBE.2 substance affected. Seal command's optional §14 backfill failed because parent plan-doc carries the method-decision register at §8 (not §14); this §8 backfill is the manual replacement.

### FBE.3 — Partition split-admit `plugins/dev-sdlc/**`
- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe3.md` (authored at `4ced26c` by FBE.3 build agent before code per `feedback_plan_before_code`).
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe3.manifest.yaml` (amendment #106, committed at `a2713ff`).
- Partition admission commit (manifest YAML 2-section edit + 2 test fixture spot-check edits): `9cdcc92`.
- Apply commit: `66935e0`.
- Seal commit: `becf183`.
- ACs satisfied: AC.FBE.3.{1,2,3,4,5,6,7,8,9,S} (10/10).
- Verification: 21/21 touched tests pass (2 dev-sdlc fence + 3 default-partition-complete + 3 M6_8 plugin-classification + 13 partition-classifier); pip install --dry-run -e plugins/dev-sdlc resolves cleanly ("Would install loam-plugin-dev-sdlc-0.1.0"); direct synth invocation produces 16 plugin leaves in synth tree (1 pyproject + 1 README + 1 skill + 8 src/.../*.py + 5 src/.../templates/odd-*.md), zero forbidden subtree leakage.
- Halt-and-surface from build (recorded for the dispatcher): **Surface #1 (skills/ admitted dev_and_public at build-time).** Parent plan §3 Decision B.2 enumeration was non-exhaustive — `plugins/dev-sdlc/skills/` was not listed in either `dev_and_public` or `dev_only`. The audit-completeness test failed with `'plugins/dev-sdlc/skills/start-project.md'` unclassified; resolved by admitting `glob: "plugins/dev-sdlc/skills/**"` to `dev_and_public:` (skills/start-project.md is explicitly the user-facing first-click intent-routing surface per its own front-matter — "first-click intent routing for the Dev/SDLC plugin"). Reversible if the dispatcher rules differently. Documented inline in the manifest provenance comment + the partition-admission commit message.

### FBE.4 — In-tree resolution via `install-from-source.{txt,md}` (Path B + fence-three-no-edit)

**Re-shaped post-empirical-halt.** The parent plan's Decision C2
(rewrite 16 inter-component bare-name deps as `<name> @ file://${PROJECT_ROOT}/<comp>`
path-specs) is non-functional on pip 26.0.1 — empirically verified
in the prior FBE.4 dispatch's halt-and-surface
(`<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md`
Probes 1–7: `${PROJECT_ROOT}` substitution narrowed in pip 26.0;
`file:../<rel>` resolves relative to CWD not pyproject; absolute
`file:///abs/...` not portable; `[tool.uv.sources]` ignored by pip).
The dispatcher ruled **Path B + fence-three-no-edit**: bare-name
deps STAY in pyprojects (byte-identical to BASELINE); a NEW top-
level file `install-from-source.txt` carries ordered `-e ./<path>`
lines that pip walks so each editable install registers its name
before later components reach for it; a NEW `docs/install-from-source.md`
covers the install path in prose; three sealed-component sidecars
(workspace-bootstrap + dev-sdlc + loam-init) bump to record the
architectural ratification ("FBE.4 ratified bare-name inter-
component deps as the v0.1.0 shape; in-tree resolution lives in
install-from-source.{txt,md}") without touching pyproject content.

- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe4.md` (authored at `14c9673` by FBE.4 build agent before code per `feedback_plan_before_code`).
- Source-side delta commit (NEW install-from-source.txt + NEW docs/install-from-source.md + 2-line partition-manifest admission edit at `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`): `cfc9ed4`.
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe4.manifest.yaml` (amendment #107, committed at `afb8a6c`).
- Apply commit: `9c51fd1`.
- Corrective commit (admit `plugins/dev-sdlc/` in loam-init's fence-test allowed_prefixes — apply tool's partner-prefix derivation assumes `framework/<name>/` shape and missed dev-sdlc's `plugins/<name>/` path): `0c4d9a0`.
- Seal commit: `99c03a6`.
- ACs satisfied: AC.FBE.4.{1,2,3,4,6,7,8,S} (8/8 — sub-plan tightened AC.FBE.4.{1,2,3} per the empirical Surface #1 anchor; DROPPED AC.FBE.4.5 per same; KEPT/EXPANDED AC.FBE.4.{4,6,7}; ADDED AC.FBE.4.8 for the partition-manifest admission; REVISED AC.FBE.4.S to fence-three-no-edit shape).
- Verification: smoke (AC.FBE.4.4) `pip install --dry-run -r install-from-source.txt` in fresh Python 3.13.12 venv exits 0; reports "Would install" all 17 `loam-*` packages plus PyPI deps (no PyPI 404s on inter-component bare-name deps); partition tests 63/63 pass; loam-init tests 14/14 pass; workspace-bootstrap fence test 2/2 pass; dev-sdlc fence test 2/2 pass; both new files classify DEV_AND_PUBLIC via direct `classify_path` invocation; pyproject byte-identicity for all three fence-three components verified via `git diff d645ed5..99c03a6 -- <pyproject>` empty.
- Halt-and-surface from build (recorded for the dispatcher): **Surface #5 (apply-tool partner-prefix gap).** `loam amend apply` derives partner_prefixes assuming `framework/<name>/` + bare-`<name>/` for every manifest-listed component. For `dev-sdlc` (which lives at `plugins/dev-sdlc/`), the tool admitted `dev-sdlc/` and `framework/dev-sdlc/` (both wrong shapes), and missed `plugins/dev-sdlc/`. The `loam-init` fence test had to be hand-edited to admit `plugins/dev-sdlc/` (corrective commit `0c4d9a0`); the redundant `dev-sdlc/` + `framework/dev-sdlc/` entries are preserved as witness of the apply-tool's derivation gap. Other two fence components already had `plugins/dev-sdlc/` admitted via M6a baseline. Latent issue — surfaces only when a fence-three includes both a `framework/`-located + a `plugins/`-located component; reasonable post-FBE.4 follow-up is a `loam amend apply` enhancement to derive prefix from each component's manifest-stated path (currently the apply tool only knows the component's `name`, not its path-prefix). FUTURE_IDEAS_DRAFT entry candidate.

### FBE.5 — Description scrub + LOW-fix sweep
- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5.md` (authored at `dda7fe4`; updated at `fb7c55d` for Surface #7 + AC.FBE.5.6 contract-tighten).
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5.manifest.yaml` (amendment #108, committed at `d580ed7`).
- Source-side delta commit (15 pyproject `description` field scrubs + `loam_cli/cli.py` docstring + comments scrub + README "before public flip" block removal + `getting-started.md` three-edit coherence fix): `8032348`.
- Apply commit: `ae0e77f`.
- Corrective commit #1 (orchestrator launchd test assertion brought into line with shipped `loam.orchestrator` template): `18e4c13`.
- Seal commit: `bc56f0d`.
- Corrective commit #2 (admit `plugins/dev-sdlc/` in `framework/tools/loam/tests/test_no_sealed_amendments.py` `allowed_prefixes` per FBE.4 partner-prefix gap precedent — required because the fence-test caught dev-sdlc sidecar+test paths during post-seal verification): `e20445f`.
- ACs satisfied: AC.FBE.5.{1,2,3,4,5,6,7,S} (8/8 — AC.FBE.5.6 rewritten at `fb7c55d` to align with verified `bootstrap_new_workspace` contract).
- Verification: `loam init /tmp/test-fbe5-ws --from /Users/lukeivers/ivers-corp-pos-v2/` smoke exits 0 (run pre-source-edit per sub-plan §12 step 2); 14/15 fence-tests pass post-corrective (scope-of-work has no fence test, skipped — this is pre-existing); `git grep -E "pOS v2|Phase 4|amendment #|M[0-9][a-z]|M-series|M-FBM"` returns zero hits in the 15 in-scope `description` lines (verified post-edit); `framework/tools/loam/src/loam_cli/cli.py` has zero amendment-number references (verified post-edit); README + getting-started edits per AC.FBE.5.{4,5}.
- Halt-and-surface from build (recorded for the dispatcher): **Surface #7 (`<workspace>/.claude/` not created despite CLI claim).** Pre-build smoke surfaced that `loam init` prints "  .claude/    ← scaffolded (Claude Code expects this here)" but no code creates `<workspace>/.claude/`. Verified at `framework/loam-init/src/loam/loam_init/cli.py:128` + `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:508` (`claude_dir` declared but never `mkdir`-ed). FBE.7 retired the `mcp_json_writer` invocation which may have been the historical creator. **Out of FBE.5 scope** per ODD §2.5 (AC.FBE.5.6 verification scope is `~/.loam/`, not `<workspace>/.claude/`); FUTURE_IDEAS_DRAFT candidate or FBE.6 reviewer-flag candidate. **Surface #8 (orchestrator launchd test assertion stale since `f0c4aa9`).** Pre-existing test assertion `pos_orchestrator` lagged the production template's `loam.orchestrator` value (rename happened at `f0c4aa9` 2026-05-03 06:55:52, missed updating the test). Surfaced when FBE.5's seal pipeline ran orchestrator's component test suite. Hand-corrective at `18e4c13` (single-line: `pos_orchestrator` → `loam.orchestrator`); test passes post-corrective. **Surface #9 (`safety-layer` dry-run false-positive — no admission list in test file).** `safety-layer/tests/test_no_sealed_amendments.py` is purely integration tests (A15/A17/A18) with no `allowed_prefixes`/`allowed_files`/`allowed` admission list. The `loam amend apply --dry-run` post-seal verification reports MISSING_ADMISSION for safety-layer; this is a false-positive (no fence-diff check exists in safety-layer's seal test, so the pre-amendment claim is vacuously true). The actual fence test passes 5/5; seal validity preserved. Mirrors FBE.4's apply-tool gap pattern. FUTURE_IDEAS_DRAFT candidate: "loam amend apply dry-run treats components-without-admission-list as fence-violation; should treat as 'no fence test, skip'."

### FBE.2b — Synth pipeline preserves `framework/` prefix on shipped paths (Decision D)

Inserted post-FBE.5 per the parent dispatcher's ruling (Decision D from
parent §3 was deferred at FBE.2 + FBE.3 + FBE.4 + FBE.5 builds; FBE.2 +
FBE.5 status files both surfaced the doc-vs-synth divergence as the
remaining HIGH 1 blocker for FBE.6's extended smoke). Single sealed-
component fence (`framework/tools/pos-publish-framework-only/`) — NEW
seal anchor established at FBE.2b mirroring FBE.2's loam-cli pattern.
Closes the doc-vs-synth path-shape divergence (HIGH 1) without rewriting
the 15+ docs that reference `framework/<comp>/` paths.

- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2b.md` (authored at `2ac582f` by FBE.2b build agent before code per `feedback_plan_before_code`).
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2b.manifest.yaml` (amendment #109, committed at `0506074`).
- Source + 3-test + sidecar combined commit (synth.py prefix-strip removal + cli.py description scrub + 3 in-fence test path-shape updates + NEW tests/SEAL_COMMIT + NEW tests/test_no_sealed_amendments.py): `03f261e`.
- Apply commit: `a058ba9`.
- Seal commit: `47ccb3a`.
- ACs satisfied: AC.FBE.2b.{1,2,3,4,5,6,7,8,9,10,S} (11/11).
- Verification: 64/64 pos-publish-framework-only tests pass post-seal (was 63 pre-FBE.2b — the new fence test); cross-component fence-test sample (loam-init + safety-layer + orchestrator + cost-governance + workspace-sync + tools/loam + workspace-bootstrap + primary-persona + dev-sdlc) all green; AC.FBE.2b.4 verified via direct `synthesise_framework_only` invocation against post-seal HEAD — synth tree-SHA `aa38b71` carries 328 `framework/`-prefixed leaves (`framework/loam-init/{pyproject.toml,README.md,src/loam/loam_init/{__init__.py,cli.py}}`, `framework/tools/loam/{pyproject.toml,README.md,src/loam_cli/{__init__.py,__main__.py,cli.py}}`, `framework/workspace-bootstrap/...` etc.), zero bare-comp paths (`tools/loam/...` returns 0), zero doubled-framework leakage (`framework/framework/...` returns 0); fence diff `git diff 03f261e..47ccb3a --name-only` produces only paths under `framework/tools/pos-publish-framework-only/` + `docs/rebuild/plans/`.
- Halt-and-surface from build (recorded for the dispatcher): **No new surfaces.** Surface #7 from sub-plan §2 (FBE.4/FBE.5 partner-prefix gap recurrence risk) did NOT recur — defensive cross-component partner-prefix admissions in the new `test_no_sealed_amendments.py` `allowed_prefixes` were sufficient; no corrective hand-admit needed. The synth re-run produced the documented install-path shape exactly; FBE.6's extended smoke (AC.FBE.6.3) can now reference `pip install -e framework/tools/loam` against a framework-only checkout and find the package.

### FBE.6 — Sweep + extended smoke + reviewer re-run
- Sweep report: `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6-sweep-report.md`.
- HOL narrative: `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6`.
- Seal commit: `<TBD>`.

### FBE.7 — Drop graphiti from v0.1.0 first-run shape (M-FBM is the v0.1.0 floor)

Added post-FBE.2 per Luke's 2026-05-03 16:53 + 16:55 UTC ruling: graphiti
must NOT ship enabled in v0.1.0. M-FBM (file-based memory; built at
`framework/primary-persona/src/loam/primary_persona/file_memory.py`)
becomes the v0.1.0 floor. Closes the workspace-bootstrap-side gap:
fresh stranger-clone v0.1.0 workspaces no longer auto-launch the
graphiti sidecar and no longer register `memory-graphiti` in
`<workspace>/workspace/.mcp.json`. Primary-persona's runtime production
path was already M-FBM-aligned; FBE.7 verified-but-no-source-edits
there. M-GMP plugin (post-v0.1.0) restores graphiti as a `MemoryProvider`-
implementing plugin against the existing surface.

- Plan-doc: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md` (authored at `db17485` by FBE.7 build agent before code per `feedback_plan_before_code`).
- Manifest: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.manifest.yaml` (amendment #105, committed at `89eec03`).
- Source + 10 test edits commit: `a22272c`.
- Apply commit: `99b237e`.
- Seal commit: `a102bde`.
- ACs satisfied: AC.FBE.7.{1,2,3,4,5,6,7,8,9,S} (10/10).
- Verification: workspace-bootstrap 242/253 pass + 11 skipped (10 net new skips relative to baseline 252+1=253 — every skip carries FBE.7 + M-GMP attribution per AC.FBE.7.5); primary-persona 521/521 pass byte-identically (AC.FBE.7.7 + AC.FBE.7.9); partition tests 3/3 pass; sealed-component fence diff clean (only paths under `framework/workspace-bootstrap/` + `docs/rebuild/plans/` per AC.FBE.7.S).
- Halt-and-surface from build (recorded for the dispatcher): **Surface #2 (cli_memory_write preserved).** AC #3's literal reading would have edited `framework/primary-persona/src/loam/primary_persona/stop_emitter.py` line 551 to drop the `build_live_mcp_memory_client` call; the multi-signal conflict-resolution in sub-plan §2 Surface #2 ruled NOT to edit (production runtime path already uses M-FBM via the queue → worker → `FileBackedMemoryClient` chain; editing `cli_memory_write` would break the AC.J.8 + AC.M.10 + AC.J.2 backwards-compat contracts). Dispatcher rules whether AC #3 needs a corrective amendment. **Surface #4 (`_install_service_manager_files` iteration switched).** Iteration switched from `_LAUNCHD_TEMPLATES.items()` to `_SERVICE_KINDS` so removing `memory-graphiti` from `_SERVICE_KINDS` actually prevents the graphiti plist from being written; the alternative (iterate templates but skip bootstrap) leaves the plist on disk + the launchd label registered, defeating the user-visible cleanliness goal.

---

*End of foldback plan-doc. FBE.2b sealed 2026-05-03 at `47ccb3a` (closes Decision D — synth pipeline preserves canonical's `framework/<comp>/` shape verbatim; FBE.6's extended smoke now has the documented install paths reachable in the synth tree). Remaining sequence: FBE.5b (Surface #7 — `<workspace>/.claude/` scaffold gap) if dispatched → FBE.6 sweep + extended smoke + reviewer re-run → M12 publish-flip.*
