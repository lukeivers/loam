# OSS v0.1.0 publish — M6 — Dev/SDLC plugin (first plugin; pattern-establishing) — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (master plan §5 M6 row + §6 sequencing rule #4).
**Programme predecessor:** M5.wire-dormancy (sealed `e32d4d8` 2026-04-29; §14 backfill `2770cc9`). M5 itself composed on M4.wire-dispatch (sealed `1719e14`) + M3.wire-clis (sealed `95f1ab2`) + M2.partition (sealed `4cda805`) + M1.rename series (M1g seal `f6c22fd`).

**Authority documents:**
- Master plan §5 M6 row + §6 sequencing rule #4 (M6 is critical-path successor to M5; parallel-safe with M7 docs lane; serial with other amendment builds).
- Master plan §3 AC.OSS.6 — programme AC the plugin satisfies.
- R2 ruling (master plan §2): "Dev/SDLC plugin only at v1" — locked 2026-04-29.
- Idea 3 — Initial plugin suite (`docs/rebuild/FUTURE_IDEAS.md` lines 278-305) — source for the plugin's enumerated capabilities.
- Idea 12 R2 (`docs/rebuild/FUTURE_IDEAS.md` lines 510-557) — open-source launch context that puts this at v1.
- Idea 6 (`docs/rebuild/FUTURE_IDEAS.md` lines 355-381) — ODD as default framing inside loam conversations.
- D-Q.OSS.5 (master plan §13) — plugin tree placement recommendation: `plugins/dev-sdlc/`.
- VALUE_PROPOSITION (prime objective hook): `docs/rebuild/VALUE_PROPOSITION.md`.
- workspace-bootstrap contribution / discovery contract: `framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py`, `manifest.py`, `discovery.py`.
- M2 partition manifest (must extend): `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- Unified loam CLI surface (must extend): `framework/tools/loam/src/loam_cli/cli.py`.
- Existing component shape reference: `framework/dormancy/`, `framework/objective-tracker/`, `framework/scope-of-work/`.
- Research findings: `docs/rebuild/plans/research/dev-sdlc-plugin-research.md` (companion artefact authored alongside this plan).

---

## 1. Summary / TLDR

**M6 has TWO load-bearing surfaces.** Per owner directive 2026-04-29 (after the initial plan-doc landed at `454bbd4`), the Dev/SDLC plugin is BOTH:

  - **Surface A — user-facing plugin capabilities** (Idea 3 features): the 5-stage workflow + methodology opt-out + `loam project ...` CLI + persona-invocable Python API + `/start-project` skill + scope/tracker integration + workspace-local SQLite. Authored at v0.1.0; ACs AC.OSS-M6.1..M6.9.
  - **Surface B — the home of dev-mode** (per Idea 13 two-modes design): the plugin BECOMES the package that delivers DEV MODE itself. Every dev-machinery artefact currently scattered across canonical loam (dev CDCs, ODD methodology long-form docs, plan-doc/manifest conventions, dispatch templates, loam-mode, hands-off-lifecycle A1-A4 gates, loam amend, pos-publish-framework-only, duration-estimation rubric, FIDRAFT, HC#4 + seal-ritual + five-gate-chain + amendment-cycle conventions) extracts into `plugins/dev-sdlc/` per per-item disposition (MOVE / STAY / PARTITION) in §6.5. ACs AC.OSS-M6.10..M6.16.

**Surface A** establishes that loam's harness extension protocol works for new content. **Surface B** establishes that dev mode is itself a plugin — a user installs Dev/SDLC to get dev mode; a user without it gets NORMAL USE. The two surfaces are inseparable in a v0.1.0 ship: the user-facing capabilities are MEANINGLESS without the dev-machinery they shape (the dev/sdlc plugin's "ODD-by-default" default reduces to vapourware if `docs/odd-methodology.md` doesn't ship with it; its dispatch templates reduce to dead links if `framework/tools/loam/templates/dispatch/` doesn't ship with it).

**Per master plan §5 M6 row predicted 90-180 min (midpoint 135) for the full new-component build cycle.** Per the extraction expansion this dispatch authors, M6's actual ship-shape is **a sub-amendment series M6a → M6b → M6c** (mirror M1.rename's M1a..M1g pattern), totalling **~270-450 min midpoint 360** wall-clock, decomposed in §6.5. **This dispatch is the research + plan + extraction-expansion slice** (predicted 20-40 min for the original Surface A; +30-45 min for the Surface B expansion = 50-85 min total). Next dispatch builds the M6a baseline plugin to seal; subsequent dispatches build M6b (extraction migrations) and M6c (deferred-content cleanups).

### Plugin tree placement (new top-level)

`plugins/dev-sdlc/` lands at v0.1.0 — establishes the plugin-tree pattern v0.2+ plugins inherit (per D-Q.M6.1 recommendation). The plugin composes against workspace-bootstrap's existing contribution-protocol (entry-point group `loam.bootstrap.contributions`) — zero bootstrap-side source change.

### v0.1.0 capability set (numbered list of concrete features)

1. **ODD-shaped 5-stage workflow** (research → spec → plan → build → review/verify) with per-stage artefact templates under `<project>/<stage>/<slug>.md` and structural gate enforcement.
2. **Stage-bound scope-of-work + objective-tracker integration** — each stage advance creates a child scope under the project + a per-stage objective with ACs.
3. **Methodology opt-out with internal ODD mirror** — `--methodology=tdd|bdd|adhoc` lets the user pick a different surface; plugin maintains `<project>/.dev-sdlc-odd-mirror.yaml` for persona's review path.
4. **`loam project ...` CLI subcommand** — five operator verbs (`new`, `status`, `advance`, `list`, `gate`) registered as subcommands of the unified `loam` CLI.
5. **Persona-invocable Python API** — `loam.plugins.dev_sdlc.api` exposes `start_project`, `advance_stage`, `project_status`, `list_projects`, `gate_check` for the persona's tool-call path.
6. **Workspace-bootstrap contribution + manifest opt-in** — plugin ships `DevSdlcContribution` registered under `loam.bootstrap.contributions` entry-point; workspace's `bootstrap.yaml` opts in via the `dev_sdlc` name string; default workspaces created via `pos-new-workspace` enumerate the plugin (per Idea 26 reader-fall-through composition).
7. **`/start-project` Claude skill** at `plugins/dev-sdlc/skills/start-project.md` — convenience surface for first-click users (D-Q.M6.4 owner ruling pending; recommendation SHIP).
8. **Per-project state in workspace-local SQLite** at `<workspace>/.loam/dev-sdlc.sqlite` — single source of truth for project metadata; `<project>/.dev-sdlc.yaml` is a human-readable mirror.

### v0.1.1+ deferrals (with rationale)

- **Objective-extraction skill for existing repos** — Idea 3 sub-feature (reverse-ODD walking up from existing code to candidate objective trees). Defer rationale: the slice/swarm/aggregate engine is itself a multi-week build (per Idea 3's "critical implementation constraints" — large-repo handling, token-budget, background-droppable, swarm aggregation). Bundling it into M6 doubles the wall-clock and pushes the publish gate. Master plan §5 M6 row already names this as "v0.1 or v0.1.1, builder's call" — owner has authorised the deferral. Land at v0.1.1 as its own master-plan cycle.
- **Workflow-state-machine engine reimplementation.** Use scope-of-work's existing FSM; the plugin shapes scopes, doesn't invent a new state machine. (Trivial deferral; not even a v0.2 candidate — the abstraction is already where it needs to be.)
- **Per-project Claude PreToolUse / Stop hooks.** v0.2 candidate when a second plugin needs the pattern. (At v0.1.0 the plugin works without project-scoped hooks; the persona is the integration layer.)
- **External issue-tracker integration** (Linear, Jira, GitHub Issues). v0.2 candidate per Idea 3's "additional plugin candidates" list.
- **Multi-project orchestration** (cross-project workflows, project-of-projects). v0.2 candidate; v0.1.0 supports N independent projects per workspace, no cross-project shape.
- **Contradiction detection** (LLM-as-verifier across stages). v0.2 candidate; heavyweight; needs the LLM-as-classifier+verifier pattern (Idea 20) baked in first.
- **Roadmap tooling** (project portfolio, milestone tracking, dependency graphs across projects). v0.2 candidate.
- **Project archive / completion lifecycle.** v0.2 candidate; at v0.1.0 a "completed" project is just a project with all stages advanced.

### Plan ACs (count + family + ladder-up)

**Sixteen ACs in family AC.OSS-M6.\* + sealed-component fence AC.OSS-M6.S.** AC.OSS-M6.1..M6.9 cover Surface A (user-facing capabilities); AC.OSS-M6.10..M6.16 cover Surface B (dev-machinery extraction). All ladder up to AC.OSS.6 (programme-level) → AC.PO.1 + AC.PO.2 (prime objective). See §4 for AC text + verification path; §6 for ladder-up table; §6.5 for extraction-shape per-inventory-item disposition.

### Owner-gate items (numbered)

**Surface A** (user-facing capabilities — original four; per `feedback_summarize_and_surface_decisions`):

- **D-Q.M6.1** — Plugin tree placement: `plugins/dev-sdlc/` (RECOMMEND) vs `framework/dev-sdlc/`.
- **D-Q.M6.2** — Objective-extraction skill at v0.1.0: defer entirely (RECOMMEND) vs ship a skill stub vs ship complete.
- **D-Q.M6.3** — Per-project CLI verb naming: `loam project ...` (RECOMMEND) vs `loam dev ...` vs `loam new ...`.
- **D-Q.M6.4** — `/start-project` skill ship-at-v0.1.0: ship (RECOMMEND) vs defer.

**Surface B** (extraction shape — added 2026-04-29 owner-directive expansion):

- **D-Q.M6.6** — Ship shape: single multi-component amendment vs sub-amendment series M6a → M6b → M6c (RECOMMEND series; mirror M1.rename precedent).
- **D-Q.M6.7** — Hands-off-lifecycle A1-A4 gates disposition: PARTITION (the four gate hooks + `_gate_helpers.py` MOVE into the plugin under `plugins/dev-sdlc/hooks/`; the `settings.json.fragment` SessionStart stanza for the runtime first-run/statusline STAYS in `framework/hands-off-lifecycle/` because it's runtime-load-bearing) (RECOMMEND PARTITION) vs MOVE-WHOLE vs STAY-WHOLE.
- **D-Q.M6.8** — `framework/tools/loam/` (loam amend) disposition: PARTITION (MOVE the dispatch + plan templates + amend bookkeeping logic into the plugin; STAY the unified-CLI wrapper + the `amend` subcommand surface that publishes-mode users may still need to inspect prior to v0.2's full removal) vs MOVE-WHOLE (RECOMMEND MOVE-WHOLE — `loam amend` is dev-discipline machinery; users without dev-mode have no reason to invoke it; partition risk on M2 cutover acceptable per §11 finding #11) vs STAY-WHOLE.
- **D-Q.M6.9** — Methodology + convention docs (`docs/odd-methodology.md`, `docs/odd-in-loam.md`, `docs/duration-estimation-rubric.md`, dev CDCs from FUTURE_IDEAS.md lines 13-198): MOVE into `plugins/dev-sdlc/docs/` vs symlink-shim (RECOMMEND MOVE; the plugin becomes the canonical home; the public `docs/design/odd.md` short-form stays in `framework/`-relative `docs/design/` per the existing M2 partition `dev_and_public` placement).

Plus method-shape decisions the plan resolves but documents for transparency:

- **D-Q.M6.5** — `loam project` subcommand discovery mechanism: entry-point group `loam.cli.subcommands` (RECOMMEND; plan-doc §10 D-build.M6.5) vs hardcoded subcommand list patched via host registry vs separate `loam-project` console-script binary.

(D-build.M6.10..M6.16 are Surface-B-side method decisions enumerated in §10.)

### Halt-and-surface findings encountered at plan-authoring time

Per the dispatch's halt-and-surface clause: ten findings (R1-R7 from research + three plan-time additions) recorded in §11. **None block dispatch.** Each maps to a §10 design decision or a §9 halt condition.

### Predicted vs (post-build) actuals — duration

- **Research + plan-doc slice (THIS dispatch):** predicted 20-40 min wall-clock per dispatch authority. Logged at §16 + post-dispatch in the duration-rubric.
- **Build slice (NEXT dispatch):** predicted 90-180 min wall-clock midpoint 135 per master plan §5 M6 row.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Prime objective:** VALUE_PROPOSITION's two tests (harness-test + primary-persona-test). Per `feedback_value_proposition_as_prime_objective`, every component / feature / amendment / AC ladders up.

**Programme objective:** AC.OSS.6 — "the Dev/SDLC plugin (Idea 3) ships in v0.1.0 as the first plugin. It composes against workspace-bootstrap's extension protocol; defaults new projects to ODD-shaped research/spec/plan/build/review/verify; provides an opt-out for users who prefer TDD/BDD/ad-hoc."

**M6-specific scope:** the plugin is the FIRST end-to-end consumer of workspace-bootstrap's contribution-protocol from outside the framework tree. Its existence proves the harness extension surface works without amending bootstrap-side surfaces. Its shape demonstrates the plugin-tree pattern v0.2+ plugins inherit.

**Lens 1 — Claude-leverage-first:** **pass.** The plugin composes against Claude-Code-shaped primitives:
  - **Skills** (Claude's user-facing intent-routing surface) — `/start-project` skill at `plugins/dev-sdlc/skills/start-project.md` lets the user invoke the plugin without any plugin-specific persona prompting (D-Q.M6.4 ship recommendation).
  - **Workspace-bootstrap's contribution model** — the entry-point-group + manifest-opt-in pattern is itself a Claude-Code-shaped extension surface (per amendment #65's β.2 absorption + Idea 26's reader-fall-through composition).
  - **Persona's tool-call surface** — the plugin's Python API is invocable via the persona's existing dispatch path; no new MCP server needed at v0.1.0.
  - **NO new Claude primitives required** — the plugin is the first proof that what's already in place is sufficient for plugin extension.

**Lens 2 — Harness + primary-persona test:**

- *Primary-persona test (translation-burden):* **pass.** The user says "let's start work on X"; the persona invokes `loam.plugins.dev_sdlc.api.start_project(slug=X)`; the plugin scaffolds the ODD-shaped project tree; the persona's next turn presents the research stage's natural-language prompt — without the user having to know the words "research stage" or "ODD." The translation burden between user intent ("I want to build X") and execution (a structured ODD-shaped workflow) is fully absorbed by the plugin's templates + the persona's prose layer.
- *Harness test (toolkit-primitive):* **pass.** The plugin ADDS to the toolkit: a project lifecycle the persona can invoke. The harness today has scope-of-work + objective-tracker (the primitives), but no shape that composes them into "project workflow" form. The plugin adds the verb the persona reaches for when the user wants methodology-shaped work; future plugins (project/task overlay, communications, etc.) inherit the same composition pattern.

**Lens 3 — ODD authoring:** ODD §2.5 enforced — every line in the M6 diff maps to a named AC under AC.OSS-M6.1..M6.9 + AC.OSS-M6.S. No "while we're here" edits. Stage gates are themselves ODD-shaped (gate = "objective is named + at least one AC is named").

---

## 3. Three-lens analysis

(Condensed — see §2 for the per-lens answers.)

### Lens 1 — Claude-leverage-first

The plugin's first-click experience leans on Claude's skills surface (`/start-project`) and the persona's existing tool-call path (`loam.plugins.dev_sdlc.api.*`). Workspace-bootstrap's contribution-discovery is the integration seam — itself a Claude-Code-shaped pattern. **No new Claude primitives required.** Skills shipped under `plugins/dev-sdlc/skills/` discover via the existing `_resolve_corpus_path` reader-fall-through (Idea 26), so plugin-shipped skills compose naturally without amending the framework's skill loader.

### Lens 2 — Harness + primary-persona value

Per §2 above: translation burden absorbed by plugin templates + persona prose layer. Toolkit grows by one major verb (project workflow) the persona reaches for when user requests methodology-shaped work. Composes existing primitives (scope-of-work + objective-tracker + memory-system + persona) into a new shape; reinvents none.

### Lens 3 — ODD authoring

Every line in M6's diff maps to one of nine ACs (AC.OSS-M6.1..M6.9). ODD §2.5 enforced. No defensive `if` branches without backing AC. Stage gates are themselves ODD-shaped enforcement points — the plugin practices what it preaches at runtime.

---

## 4. Acceptance criteria — AC.OSS-M6.\*

### AC.OSS-M6.1 — Plugin discovers via workspace-bootstrap's contribution protocol

`plugins/dev-sdlc/pyproject.toml` declares an entry-point under group `loam.bootstrap.contributions`:

```toml
[project.entry-points."loam.bootstrap.contributions"]
dev_sdlc = "loam.plugins.dev_sdlc.contribution:DevSdlcContribution"
```

A test workspace whose `bootstrap.yaml` lists `dev_sdlc` in `contributions:` boots cleanly with the plugin's contribution running; a workspace whose `bootstrap.yaml` does NOT list it boots cleanly without the plugin loading (availability vs enablement per `discovery.py` lines 7-9).

**Verification:** a unit test (a) constructs a `BootstrapHost` against a synthetic workspace whose `bootstrap.yaml` lists `dev_sdlc`, (b) runs the bootstrap discovery + contribution-execution loop, (c) asserts `host.dev_sdlc` is a `DevSdlcRuntime` instance after `contribute()` returns. A second test asserts a workspace without the manifest entry boots without `host.dev_sdlc` being set.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_1_contribution_discovers_via_entry_point.py` (new).

### AC.OSS-M6.2 — `loam project new <slug>` scaffolds an ODD-shaped project tree

Running `loam project new my-project` from a workspace's root creates:

```
<workspace>/projects/my-project/
  .dev-sdlc.yaml              # methodology=odd, current_stage=research, slug=my-project
  research/                   # empty initially
  spec/
  plan/
  build/
  review/
```

…and writes a row to `<workspace>/.loam/dev-sdlc.sqlite`'s `projects` table. The first stage's template (`research/<slug>.md` per the project's chosen methodology — default ODD) is NOT auto-created at `new` time (the user authors the artefact when they're ready); the plugin's `gate` check on stage advance verifies the artefact exists.

**Verification:** a unit test (a) invokes `api.start_project(slug="my-project", workspace_root=tmp_path)`, (b) asserts the project tree exists with the expected directories, (c) asserts the SQLite row exists with `methodology=odd, current_stage=research`.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_2_new_project_scaffolds_odd_tree.py` (new).

### AC.OSS-M6.3 — `--methodology=tdd|bdd|adhoc` opt-out preserves an internal ODD mirror

Running `loam project new my-project --methodology=tdd` creates the project tree with TDD-shaped templates (no ODD-frontmatter in the user-visible artefacts), AND writes `<project>/.dev-sdlc-odd-mirror.yaml` containing the plugin's internal ODD representation of the project (objective: "<unset until populated>"; stages: same five).

**Verification:** a unit test invokes `api.start_project(slug="my-project", methodology="tdd", workspace_root=tmp_path)`; asserts (a) `<project>/.dev-sdlc.yaml` `methodology` field is `tdd`, (b) `<project>/.dev-sdlc-odd-mirror.yaml` exists with the expected mirror schema.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_3_opt_out_preserves_odd_mirror.py` (new).

### AC.OSS-M6.4 — Stage gate enforces objective + AC presence before advance

`loam project advance <slug>` (or `api.advance_stage(slug)`) runs the gate check on the current stage's artefact (e.g. for stage `research`, checks `<project>/research/<slug>.md`). The gate passes iff the artefact:
  - Exists.
  - Contains a recognisable "objective" field (frontmatter `objective:` for ODD methodology, OR a section heading `## Objective` for ODD-prose; for TDD/BDD/adhoc, a methodology-specific equivalent the plugin's gate-checker recognises per the methodology's template).
  - Contains at least one AC (`acceptance_criteria:` array OR a `## Acceptance Criteria` section with ≥1 bullet).

Gate failure surfaces a structured halt-and-surface signal via the plugin's exception (`StageGateFailedError(reason: str, project: str, stage: str)`); the persona's existing exception-handling path translates the structured signal to natural-language prose for the user.

**Verification:** unit tests (a) construct a project with a stage-1 artefact missing — assert `advance_stage` raises `StageGateFailedError` with reason "artefact_not_found"; (b) construct a project with a stage-1 artefact present but missing objective — assert raises with reason "no_objective"; (c) construct a project with a stage-1 artefact missing ACs — assert raises with reason "no_ac"; (d) construct a project with a complete stage-1 artefact — assert `advance_stage` succeeds + the project's current_stage advances to `spec`.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_4_stage_gate_enforces_objective_and_ac.py` (new).

### AC.OSS-M6.5 — Stage-bound scope + objective-tracker integration

When a project is created (M6.2), the plugin creates a parent scope under scope-of-work (`scope.kind=project, scope.label=<slug>`) and a root objective in the tracker (`objective.text="produce <slug> via <methodology>", parent=None`). When a stage advances (M6.4), the plugin creates a child scope (`scope.kind=stage, scope.label=<stage>, parent_scope=<project_scope_id>`) and a child objective (`objective.text="produce <stage> artefact for <slug>", parent=<project_objective_id>`). Each stage advance emits an OTel span (`loam.dev_sdlc.stage_advance`) with attributes `slug`, `from_stage`, `to_stage`, `methodology`.

**Verification:** an integration test runs `api.start_project` + `api.advance_stage`; asserts (a) scope-of-work's `runtime.list(filter)` returns the expected parent + child scopes, (b) objective-tracker's `runtime.get_objective(id)` returns the expected forest shape, (c) the `loam.dev_sdlc.stage_advance` span was emitted (via captured tracer fixture).

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_5_scope_and_tracker_integration.py` (new).

### AC.OSS-M6.6 — `loam project ...` registered as subcommand of unified `loam` CLI

`loam project --help` lists subcommands `new`, `status`, `advance`, `list`, `gate`. Each subcommand dispatches to the plugin's CLI module (`loam.plugins.dev_sdlc.cli`). Discovery mechanism: the unified `loam_cli` resolves `project` via the entry-point group `loam.cli.subcommands` (NEW group authored at M6 — minimal mechanism; symmetric to bootstrap's contribution discovery; see §10 D-build.M6.5).

**Verification:** a unit test (a) invokes `loam_cli.cli.main(["project", "--help"])`; asserts exit-0 + the help output names the five subcommands; (b) invokes `loam_cli.cli.main(["project", "new", "test", "--workspace-root", tmp_path])`; asserts a project was created.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_6_loam_project_subcommand_registered.py` (new) + `framework/tools/loam/tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py` (new — covers `loam_cli`'s side of the entry-point-discovery mechanism).

### AC.OSS-M6.7 — Persona-invocable Python API surface stable

Public API at `loam.plugins.dev_sdlc.api`:

```python
def start_project(slug: str, *, methodology: str = "odd", workspace_root: Path | None = None) -> ProjectHandle: ...
def advance_stage(slug: str, *, workspace_root: Path | None = None) -> StageAdvanceResult: ...
def project_status(slug: str | None = None, *, workspace_root: Path | None = None) -> list[ProjectStatus]: ...
def list_projects(*, workspace_root: Path | None = None) -> list[ProjectStatus]: ...
def gate_check(slug: str, *, workspace_root: Path | None = None) -> GateResult: ...
```

Each function is import-stable (no `_internal_*` shapes). Pydantic models for `ProjectHandle`, `StageAdvanceResult`, `ProjectStatus`, `GateResult` exported via `loam.plugins.dev_sdlc` package-init.

**Verification:** an import-stability test (`from loam.plugins.dev_sdlc.api import start_project, advance_stage, project_status, list_projects, gate_check`) + a contract test asserting the function signatures (via `inspect.signature`).

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_7_python_api_surface_stable.py` (new).

### AC.OSS-M6.8 — M2 partition manifest classifies `plugins/dev-sdlc/` (M6a baseline shape: `dev_and_public`; reclassified at M6b per AC.OSS-M6.13 + D-build.M6.14)

`framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` extends at M6a:
  - `audit_roots:` adds `plugins/`.
  - `dev_and_public:` adds `- glob: "plugins/dev-sdlc/**"`.

The synthesis tool's classification check (post-M2 contract) classifies every file under `plugins/dev-sdlc/` as `dev_and_public`; synthesis includes the plugin in the public artefact AT M6a (Surface A baseline — the plugin contains only user-facing capabilities at this point).

**Surface B reclassification at M6b** (per AC.OSS-M6.13 + D-build.M6.14): once the dev-machinery extraction completes, `plugins/dev-sdlc/**` reclassifies from `dev_and_public` to `dev_only` — the plugin THEN contains dev-discipline machinery extracted from the M2 manifest's pre-M6b `dev_only` block. The reclassification is one of M6b's load-bearing diff actions.

**Verification:** a unit test invokes the partition manifest's `partition_complete(...)` against a synthetic workspace state including `plugins/dev-sdlc/` files; asserts (a) every file classifies, (b) every file lands in `dev_and_public`. Plus an integration test running `synth.py` against canonical HEAD; asserts the synthetic tree contains `plugins/dev-sdlc/`.

**Test:** `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` (new).

### AC.OSS-M6.9 — `/start-project` Claude skill discoverable + invocable (D-Q.M6.4 ship path)

If owner rules SHIP at D-Q.M6.4: `plugins/dev-sdlc/skills/start-project.md` exists with frontmatter (`description: "Start a new project under loam's Dev/SDLC plugin..."` + `name: start-project`) and a body that names the user-facing intent + the underlying `api.start_project` invocation. The skill is discoverable via the workspace's skill loader (per Idea 26's reader-fall-through composition — plugin-shipped skills resolve through `_resolve_corpus_path`).

**If owner rules DEFER at D-Q.M6.4:** AC.OSS-M6.9 is dropped; the AC count drops to 8.

**Verification:** a unit test asserts the skill file exists + parses frontmatter + the persona's skill-discovery code (per `_resolve_corpus_path`) finds it.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_9_start_project_skill_shipped.py` (new — conditional on D-Q.M6.4).

### AC.OSS-M6.10 — Dev CDCs MOVE from FUTURE_IDEAS.md into plugin docs (Surface B)

The 10 dev CDCs currently parked at `docs/rebuild/FUTURE_IDEAS.md` lines 13-198 (step-by-step-when-system-cannot-act, plan-before-code, run-all-execution-through-background-agents, scope-only-dispatch, setup-scripts-self-retire, research-before-plan, shutdown-broad-catch, audit-finding-triage, amendment-dispatch-test-scope, 529-overload-recovery) MOVE to `plugins/dev-sdlc/docs/cdcs/<name>.md` (one file per CDC). FUTURE_IDEAS.md retains a redirect placeholder ("These CDCs lived here until the Dev/SDLC plugin landed; they now live at `plugins/dev-sdlc/docs/cdcs/`").

**Verification:** unit test asserts (a) every CDC's body text is preserved byte-identically in the new location (HC#4 byte-content invariant on the moved content), (b) FUTURE_IDEAS.md no longer carries the CDC bodies, (c) FUTURE_IDEAS.md carries a redirect placeholder. **Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_10_cdcs_moved_to_plugin.py` (new — M6b).

### AC.OSS-M6.11 — Long-form ODD methodology MOVE to plugin docs (Surface B)

`docs/odd-methodology.md` (794 LOC) and `docs/odd-in-loam.md` (1058 LOC) MOVE to `plugins/dev-sdlc/docs/odd-methodology.md` and `plugins/dev-sdlc/docs/odd-in-loam.md`. The condensed `docs/design/odd.md` (259 LOC public surface) STAYS.

**Verification:** unit test asserts (a) the moved files exist at the new location with byte-identical content, (b) the original locations no longer carry the long-form content, (c) `docs/design/odd.md` is unchanged byte-identically (HC#4 invariant on the public-facing condensed form). **Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_11_odd_methodology_moved.py` (new — M6b).

### AC.OSS-M6.12 — `loam-mode` MOVE to plugin; dev-mode delivered via plugin (Surface B)

`framework/tools/loam-mode/` MOVES whole-package to `plugins/dev-sdlc/loam-mode/`. The package's entry-point + console-script registrations update to reflect the new location. `docs/rebuild/dev-mode-manifest.yaml` MOVES to `plugins/dev-sdlc/dev-mode-manifest.yaml`. The selector's path-resolution updates to read the manifest from the plugin-relative path (with workspace-relative fall-through per Idea 26 to support pre-extraction state during M6b's commit window).

**Verification:** integration test asserts (a) `loam-mode audit` runs from the new location, (b) `loam-mode select_corpus(mode=dev)` returns the dev-mode corpus paths correctly, (c) a workspace whose `bootstrap.yaml` does NOT enable `dev_sdlc` does NOT auto-load any dev-mode artefacts at SessionStart (NORMAL USE behaviour preserved). **Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_12_loam_mode_moved_to_plugin.py` (new — M6b).

### AC.OSS-M6.13 — M2 partition manifest `dev_only` block retires (Surface B)

Post-M6b, `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`'s `dev_only:` list is empty (or removed entirely; the schema admits both shapes). What previously lived in `dev_only` either:
  - Lives inside `plugins/dev-sdlc/**` (which classifies via the `plugins/dev-sdlc/**` glob added in AC.OSS-M6.8 — but per the extraction, the plugin itself contains DEV-DISCIPLINE machinery, so the glob's classification at M6b shifts from `dev_and_public` to either `dev_only` (the plugin doesn't ship publicly at all) or to a NEW partition class `plugin_publishable` reflecting "the plugin's BASE ships publicly, but its dev-discipline subtree at `plugins/dev-sdlc/docs/cdcs/`, `plugins/dev-sdlc/docs/odd-methodology.md`, `plugins/dev-sdlc/loam-amend/` STAYS dev-only" — the partition shape decision is D-build.M6.13 below in §10).
  - Has STAYed under one of the inventory items 8, 14, 15, or under the audit-tools category (e.g. `framework/tools/heavy-b-migrate/**`) which retains its `dev_only` classification — in which case `dev_only` does NOT fully retire and AC.OSS-M6.13's verification is "the `dev_only` list contains ONLY items 8, 14, 15 + migration tools per the recorded post-extraction shape" rather than "is empty." The plan recommends the second form (D-build.M6.13: keep `dev_only` for migration tools + audit tools; retire it only for content that moved to the plugin).

**Verification:** unit test asserts the post-M6b `dev_only` list matches the recorded post-extraction shape (per D-build.M6.13). The synthesis-tool's classification check passes against canonical HEAD post-M6b. **Test:** `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_13_dev_only_block_post_extraction.py` (new — M6b).

### AC.OSS-M6.14 — Hands-off-lifecycle A1-A4 gate hooks PARTITION + MOVE to plugin (Surface B)

The A1-A4 gate hooks (per Item 6 disposition: `objective_binding_gate.py`, `tdd_guard.py`, `agent_guard.py`, `bash_guard.py`, `dispatch_setup_hook.py`, `_gate_helpers.py`, `active_scope_sentinel.py`, `agent_file_authoring.py`, `agent_file_runner.py`, `corpus_inline_session_start.py`, `corpus_load_sentinel.py`, `corpus_load_session_start.py`) MOVE from `framework/hands-off-lifecycle/hooks/` to `plugins/dev-sdlc/hooks/`. Their `settings.json.fragment` PreToolUse stanza MOVES with them. The plugin's contribution registers these hooks via Claude Code's `settings.json` extension surface at `contribute(host)` time — only when the plugin is enabled (i.e. only in DEV MODE workspaces). Hands-off-lifecycle's runtime hooks (`first-run.sh`, `first_run_*.py`, `statusline.py`, `pos_session_start.py`) STAY at `framework/hands-off-lifecycle/hooks/`.

**Verification:** unit tests assert (a) the A1-A4 gate hooks exist at the new location with byte-identical content, (b) the existing A1-A4 tests at `framework/hands-off-lifecycle/tests/test_AC_AG_*.py` MOVE alongside the source (the seal-test fence moves with the hooks), (c) a NORMAL USE workspace's session loads without the gates active, (d) a DEV MODE workspace's session loads with the gates active per the original A1-A4 contract. **Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_14_a1_a4_gates_partition_to_plugin.py` (new — M6b) + the moved A1-A4 tests.

### AC.OSS-M6.15 — `loam amend` MOVE to plugin; unified-CLI wrapper STAYS (Surface B)

`framework/tools/loam/src/loam_cli/amend/` (the entire `amend` submodule + its `commands/`, `template_engine.py`, `seal_diff.py`, `narrative.py`, `manifest.py`, `baseline.py`, `dry_run.py`, `paths.py`, `rename_detection.py`, `sidecar.py`, `tracker_registration.py`) MOVES to `plugins/dev-sdlc/loam-amend/src/loam_amend/`. A NEW console-script entry-point `loam-amend` is registered IN THE MIGRATED PACKAGE. The unified `loam` CLI at `framework/tools/loam/` STAYS as a thin dispatcher: `loam amend ...` invocations resolve via the unified `loam.cli.subcommands` entry-point group introduced at M6a (per AC.OSS-M6.6); the plugin's `pyproject.toml` ships `[project.entry-points."loam.cli.subcommands"]` with `amend = "loam_amend.cli:build_amend_subcommand"` AND `project = "loam.plugins.dev_sdlc.cli:build_project_subcommand"`. **CRITICAL DEPENDENCY** (per §11 finding #11 + §9 halt-trigger #11): the M6b extraction must stage the migration so the canonical tree retains an INSTALLED `loam amend` console-script throughout the M6b commit window — the build process itself uses `loam amend` for amendment seal.

**Verification:** unit tests assert (a) `loam amend` subcommand resolves via the plugin's entry-point post-extraction, (b) the existing `framework/tools/loam/tests/test_*.py` tests MOVE alongside the source (the seal-test fence moves with the package), (c) `loam amend --help` exits 0 in a workspace where the plugin is enabled, (d) `loam amend --help` returns an "amend subcommand not available — install plugins/dev-sdlc/" message in a workspace where the plugin is NOT enabled. **Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_15_loam_amend_moved_to_plugin.py` (new — M6b) + the moved `loam_cli.amend.*` tests.

### AC.OSS-M6.16 — Dev-discipline convention docs authored under plugin (Surface B)

NEW convention codification documents authored at `plugins/dev-sdlc/docs/conventions/`:
  - `plan-docs.md` — plan-doc / sub-plan / manifest YAML conventions (per Item 3 + Item 16 disposition).
  - `fidraft-pattern.md` — FIDRAFT no-overhead capture pattern + DRAFT file lifecycle conventions (per Item 10).
  - `sealed-component-invariants.md` — HC#4 byte-content invariant + per-invariant frozen baselines + ODD §4 retire-and-rebaseline conventions (per Item 11).
  - `commit-ladder.md` — Seal ritual + commit-ladder convention (per Item 12).
  - `five-gate-chain.md` — Five-gate chain (research-plan → research → proposal → brief → build → seal) (per Item 13).
  - `amendment-cycle.md` — Amendment-cycle conventions (per Item 13).

Plus a NEW `plugins/dev-sdlc/templates/component/test_no_sealed_amendments.py.template` (per Item 16). Each convention doc is 100-300 LOC (concise codification of currently-precedent-driven shape; not exhaustive prose). Plus updates to `docs/rebuild/STATE.md`, `docs/odd-in-loam.md` (post-MOVE, the in-plugin copy), and the master plan to point at the new convention-doc home.

**Verification:** unit tests assert (a) each convention file exists with at least the recorded section structure (objective + summary + "applied immediately to..." footer), (b) cross-references from canonical-tree docs (post-MOVE) point at the plugin-relative paths. **Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_16_convention_docs_authored.py` (new — M6b).

### AC.OSS-M6.S — Sealed-component fence

**Three sub-amendments — three sealed-component fences** per the M6a/M6b/M6c series (D-Q.M6.6 RECOMMEND series).

**AC.OSS-M6.S(a) — M6a fence (Surface A baseline plugin).** Three components (or four if D-Q.M6.1 lands `framework/dev-sdlc/`) in the M6a fence:

  - **`plugins/dev-sdlc/`** (NEW component) — carries the plugin source + tests + per-component `tests/SEAL_COMMIT` sidecar + per-component `tests/test_no_sealed_amendments.py` seal-test (authored at M6 alongside the source).
  - **`framework/tools/loam/`** — extends `loam_cli.cli.main` to discover `project` subcommand via the new entry-point group (one source-file edit + one new test).
  - **`framework/tools/pos-publish-framework-only/`** — extends the partition manifest YAML + minor classifier test update (one YAML edit + one new test).
  - **(possible 4th)** — if D-Q.M6.5 rules entry-point-group form for subcommand discovery (RECOMMEND), `framework/tools/loam/` source change is the only diff; if it rules host-registry form, `framework/workspace-bootstrap/` MAY enter the fence (additional `host.loam_cli_registry` attribute). Plan recommends entry-point-group form to keep workspace-bootstrap OUT of the fence.

Per-component seal-tests advance their `SEAL_COMMIT` sidecars at seal time. The seal-diff fence is enforced via `tests/test_no_sealed_amendments.py` in each component. **`plugins/dev-sdlc/`'s seal-test is authored AT M6a** (NEW component — first seal). The pattern follows existing components (`framework/dormancy/tests/test_no_sealed_amendments.py` is the template).

**M6a verification:** seal-diff tests pass post-build for all fenced components. The new seal-test in `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` is authored to admit M6a's diff (`plugins/dev-sdlc/`-relative paths) and reject anything outside the plugin's subtree.

**AC.OSS-M6.S(b) — M6b fence (Surface B extraction migrations).** Five-to-seven components in the M6b fence (depending on how loam-mode + plan-tree are classified):

  - **`plugins/dev-sdlc/`** — destination of MOVE-class items (5, 7, 9, 17) + PARTITION-class items (1, 2, 3, 6, 10, 11, 12, 13, 16). Seal-test admits both `plugins/dev-sdlc/`-relative and the per-PARTITION-item canonical-side residue (e.g. updated FUTURE_IDEAS.md placeholder, updated STATE.md cross-references).
  - **`framework/hands-off-lifecycle/`** — source side of Item 6 PARTITION. Seal-test admits the file deletions for the moved hooks + the unchanged runtime hooks.
  - **`framework/tools/loam/`** — source side of Item 7 (loam amend) MOVE. Seal-test admits the file deletions for the moved `amend/` submodule + the unchanged unified-CLI wrapper.
  - **`framework/tools/loam-mode/`** — source side of Item 5 MOVE. Seal-test admits the file deletions for the whole package (or admits empty post-deletion).
  - **`framework/tools/pos-publish-framework-only/`** — partition manifest extension per Item 13. Seal-test admits the YAML edit + new test.
  - **(plan-tree pseudo-component)** — `docs/rebuild/`-relative changes to FUTURE_IDEAS.md, STATE.md, master plan cross-references, and the moved long-form ODD docs (Items 1, 2, 11, 12, 13). The plan-tree is NOT a sealed component today; M6b's diff under `docs/rebuild/` is admitted via the M6b manifest's `universal_paths.prefixes` extension to include `docs/odd-methodology.md` + `docs/odd-in-loam.md` + `docs/duration-estimation-rubric.md` (which are file-level, not subtree).

**M6b verification:** seal-diff tests pass post-build for all fenced components. The MOVE operations are verifiable via `git log --follow` on the moved files; the PARTITION operations are verifiable via paired tests (one asserting destination existence, one asserting source absence).

**HC#4 byte-content invariant** under M6b: every MOVE-class item's content must be byte-identical at the destination (verified by the per-AC tests). The `git mv` mechanic preserves bytes unmodified; the only AC byte-divergence is in the cross-reference UPDATES (e.g. STATE.md's reference to `docs/odd-methodology.md` becomes `plugins/dev-sdlc/docs/odd-methodology.md`) — these are intentional and recorded in the M6b method-decision register.

**AC.OSS-M6.S(c) — M6c fence (cleanups).** One-to-three components in the M6c fence (the actual surface determined by what M6b leaves trailing). Likely candidates: `docs/rebuild/` plan-tree, `framework/tools/pos-publish-framework-only/` (final partition shape), `plugins/dev-sdlc/` (any documentation polish discovered during M6b that wasn't worth widening M6b's fence).

**M6c verification:** seal-diff tests pass post-build. Final assertion: post-M6c, `loam-mode audit --workspace .` exits 0 against the canonical tree (the audit confirms no orphan dev-mode artefacts, no overlap, no cross-mode references — i.e. the extraction is internally consistent).

---

## 5. Out-of-scope (explicit)

Per ODD §2.5 + dispatch authority + Idea 3's deferral text:

- **Objective-extraction skill for existing repos** (Idea 3 sub-feature). Defer to v0.1.1 per master plan §5 M6 + §1 TLDR. The skill's slice/swarm/aggregate engine is itself a multi-week build; bundling doubles M6's scope.
- **Workflow-state-machine engine reimplementation.** Use scope-of-work's existing FSM; the plugin shapes scopes, doesn't invent state machines.
- **External issue-tracker integration** (Linear, Jira, GitHub Issues). v0.2 candidate.
- **Multi-project orchestration** (cross-project workflows, project-of-projects). v0.2 candidate.
- **Contradiction detection** across stage artefacts. v0.2 candidate; needs Idea 20 (LLM-as-classifier+verifier) baked in.
- **Roadmap tooling** (project portfolio, milestone tracking, dependency graphs). v0.2 candidate.
- **Project archive / completion lifecycle.** v0.2 candidate; at v0.1.0 a "completed" project is just one with all stages advanced.
- **Per-project Claude PreToolUse / Stop hooks.** v0.2 candidate when a second plugin needs the pattern.
- **MCP server exposing project state.** v0.2 candidate when remote-access shape becomes valuable.
- **Plugin uninstall / rollback shape.** v0.2 candidate; at v0.1.0 the user removes the `dev_sdlc` line from `bootstrap.yaml` and the plugin no longer loads (manifest opt-in is the inverse of opt-out).
- **Existing-repo retrofit flow** (importing an existing project under the plugin's discipline). v0.2 candidate; composes with the deferred objective-extraction skill.

---

## 6. AC ladder-up to AC.OSS.6

| AC | Master plan AC ladder | Prime objective |
|---|---|---|
| AC.OSS-M6.1 (contribution discovers) | AC.OSS.6 ("composes against workspace-bootstrap's extension protocol") | AC.PO.2 (toolkit-primitive — the harness's extension surface gains a real consumer) |
| AC.OSS-M6.2 (new project scaffolds ODD tree) | AC.OSS.6 ("defaults new projects to ODD-shaped...") | AC.PO.1 (translation-burden — user gets a project from natural-language intent) |
| AC.OSS-M6.3 (opt-out preserves ODD mirror) | AC.OSS.6 ("provides an opt-out for users who prefer TDD/BDD/ad-hoc") | AC.PO.2 (toolkit-primitive — methodology-flexibility extends the harness's reach) |
| AC.OSS-M6.4 (stage gate enforces objective + AC) | AC.OSS.6 (implicit — methodology requires structural enforcement) | AC.PO.1 (translation-burden — gate failure is structural; user doesn't have to remember) |
| AC.OSS-M6.5 (scope + tracker integration) | AC.OSS.6 (implicit — plugin composes existing primitives) | AC.PO.2 (toolkit-primitive — primitives compose into a new shape) |
| AC.OSS-M6.6 (`loam project` subcommand) | AC.OSS.6 (implicit — operator-callable surface) | AC.PO.1 (translation-burden — persona has a callable verb) |
| AC.OSS-M6.7 (Python API surface stable) | AC.OSS.6 (implicit — persona-invocable surface) | AC.PO.1 (translation-burden — persona's tool-call path) |
| AC.OSS-M6.8 (partition manifest includes plugin) | AC.OSS.3 (no dev-discipline machinery in public — inverse: plugin SHIP) | AC.PO.2 (toolkit-primitive ships publicly) |
| AC.OSS-M6.9 (/start-project skill shipped — D-Q.M6.4) | AC.OSS.6 (Claude-leverage surface) | AC.PO.1 (translation-burden — skill is intent-routing for user) |

All ladder up to AC.PO.1 + AC.PO.2 (prime objective ACs in `docs/rebuild/VALUE_PROPOSITION.md`). Per `feedback_value_proposition_as_prime_objective`, this is the required reverse-trace.

(Surface B's AC.OSS-M6.10..M6.16 ladder-up rows are appended in §6.5's per-AC table.)

---

## 6.5 Extraction shape — Surface B (dev-machinery into the plugin)

### 6.5.1 Owner directive (verbatim, 2026-04-29)

> "specifically review all the things in our current pos3, as well as canonical loam, and on top of what is in future ideas already, extract all of the dev-related things into the dev/sdlc plugin."

The plugin is to BECOME the home of the dev-mode content per Idea 13's two-modes design — not just a tool users run on their projects, but the package that delivers DEV MODE itself. A user who installs the Dev/SDLC plugin gets dev mode; a user who doesn't gets NORMAL USE.

### 6.5.2 Per-inventory-item disposition table

Inventory cross-checked against the M2 partition manifest's `dev_only` block (`framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` lines 147-175). The dispatch's preliminary inventory (14 items) is the seed; the table below verifies each + adds three items the agent identified during inventory walk.

| # | Item | Current location | Disposition | Rationale | M6 phase |
|---|---|---|---|---|---|
| 1 | Dev CDCs (10 items at FUTURE_IDEAS.md lines 13-198) | `docs/rebuild/FUTURE_IDEAS.md` lines 13-198 | **PARTITION** — MOVE the CDC bodies to `plugins/dev-sdlc/docs/cdcs/<name>.md` (one file per CDC; mirrors the file-per-feedback pattern in `~/.claude/projects/.../memory/`); STAY the FUTURE_IDEAS.md "temporary parking" placeholder pointing at the new home (one-line redirect). The CDCs are dev-discipline material; FUTURE_IDEAS.md text already says "until the Dev/SDLC plugin (Idea 3 below) exists, this file is their temporary home. When the plugin lands, they migrate there." This MOVE executes that promise. | The CDCs are referenced by every dev-mode dispatch + `docs/odd-in-loam.md`; relocating them under the plugin makes the plugin self-contained as the dev-mode package. | M6b |
| 2 | ODD methodology long-form: `docs/odd-methodology.md` (794 LOC) + `docs/odd-in-loam.md` (1058 LOC) | `docs/odd-methodology.md`, `docs/odd-in-loam.md` | **MOVE** to `plugins/dev-sdlc/docs/odd-methodology.md` + `plugins/dev-sdlc/docs/odd-in-loam.md`. The condensed `docs/design/odd.md` (259 LOC public surface) STAYS in `framework/`-relative location per existing M2 `dev_and_public` placement. | The long-form ODD is dev-mode-only; the M2 partition manifest already classifies them `dev_only`; relocating them under the plugin makes the plugin the canonical dev-mode home. The short-form `docs/design/odd.md` is the public surface; it stays where it is. | M6b |
| 3 | Plan-doc / sub-plan / manifest YAML conventions | Currently expressed by precedent in `docs/rebuild/plans/` + by the dispatch template at `framework/tools/loam/templates/plan/dev-discipline.md` | **STAY** the actual plans (they're the project-level dev artefacts of canonical loam itself); **MOVE** the convention DOCS (the structural template + the schema + the methodology of authoring a plan-doc) into `plugins/dev-sdlc/docs/conventions/plan-docs.md` (NEW authored file, 200-300 LOC, codifying the precedent). | The historical plan-docs ARE canonical loam's dev work-history; they don't belong inside the plugin. The CONVENTIONS for authoring future plan-docs DO belong inside the plugin (it's what the plugin teaches). | M6b |
| 4 | Dispatch templates (`sealed-component-build.md`, `dev-discipline.md`) | `framework/tools/loam/templates/dispatch/` + `templates/plan/` | **MOVE** to `plugins/dev-sdlc/templates/dispatch/` + `plugins/dev-sdlc/templates/plan/`. The unified `loam` CLI's template-engine (`framework/tools/loam/src/loam_cli/amend/template_engine.py`) reads templates by package-relative path; the move requires updating the resolver to read from the plugin's package data. | These are dev-discipline shaped artefacts that drive sealed-component-build dispatches. They don't run in NORMAL USE. | M6b |
| 5 | `loam-mode` (dev-mode auto-load mechanism) | `framework/tools/loam-mode/` | **MOVE** to `plugins/dev-sdlc/loam-mode/` (preserve the package layout: `pyproject.toml`, `src/loam_mode/`, `tests/`, `README.md`). Update entry-point group registrations + console-script registrations. The dev-mode-manifest at `docs/rebuild/dev-mode-manifest.yaml` MOVES to `plugins/dev-sdlc/dev-mode-manifest.yaml`. | `loam-mode` is the package that delivers dev mode itself — its job is "load dev artefacts at SessionStart for DEV MODE workspaces." When dev-mode-as-a-plugin lands, `loam-mode` IS the plugin's mode-routing module. Moving it into the plugin makes the plugin the single deliverable for dev mode. | M6b |
| 6 | Hands-off-lifecycle A1-A4 structural-enforcement gate hooks (`objective_binding_gate`, `tdd_guard`, `agent_guard`, `bash_guard`, `dispatch_setup_hook`, `_gate_helpers`, `active_scope_sentinel`, `corpus_inline_session_start`, `corpus_load_*`) | `framework/hands-off-lifecycle/hooks/` | **PARTITION.** The A1-A4 GATE hooks (`objective_binding_gate.py`, `tdd_guard.py`, `agent_guard.py`, `bash_guard.py`, `dispatch_setup_hook.py`, `_gate_helpers.py`, `active_scope_sentinel.py`, plus the corpus-inline + corpus-load helpers and the `agent_file_authoring.py` / `agent_file_runner.py` + the `__init__.py` / settings fragment they rely on) MOVE to `plugins/dev-sdlc/hooks/`. The runtime SessionStart helper hooks (`first-run.sh`, `first_run_*.py`, `statusline.py`, `pos_session_start.py`, `__init__.py`) STAY in `framework/hands-off-lifecycle/hooks/` — they are runtime first-run-and-statusline machinery, NOT dev-mode-only enforcement; they ship publicly. (Per docstring inspection: `objective_binding_gate.py` "NORMAL USE workspaces no-op the gate at the mode-bit short circuit (D-A2.5 / programme D4 lock — A2 is ODD-discipline, DEV-MODE-only)" — these hooks are purpose-built dev-mode-only enforcement.) | The gates are dev-mode-only by docstring contract; their SessionStart-fragment hook-config registration MOVES with them under the plugin; the plugin's contribution registers the hooks via Claude Code's `settings.json` extension surface (per Lens 1: leverage Claude's PreToolUse hook protocol). The `framework/hands-off-lifecycle/` component proper STAYS; it just becomes thinner (its gate-enforcement substrate moves to the plugin; its first-run-supervisor + statusline + `MemorySupervisor` wiring remain). | M6b |
| 7 | `loam amend` bookkeeping CLI (the renamed pos-amend) | `framework/tools/loam/` | **MOVE** entire package to `plugins/dev-sdlc/loam-amend/`. Rename the console-script entry-point from `loam` to `loam-amend` IN THE MIGRATED PACKAGE; THE UNIFIED `loam` CLI WRAPPER STAYS at `framework/tools/loam/` as a thin dispatcher (no-op when the plugin isn't installed; delegates to the plugin's subcommand-discovery surface when it is). Per §10 D-Q.M6.8 RECOMMEND MOVE-WHOLE; the unified-CLI shim is small enough to author fresh in canonical (no second-pass rename). | `loam amend` IS the dev-discipline bookkeeping mechanism; users without dev-mode have no reason to invoke it. The unified-CLI wrapper STAYS so that `loam project ...` (M6 user-facing surface) remains a stable verb tree even when `amend` is plugin-supplied. CRITICAL DEPENDENCY (per §11 finding #11): the build process itself uses `loam amend` for amendment seal; the M6b extraction must be staged so the canonical tree retains an INSTALLED copy of `loam amend` while the migration is in flight. | M6b |
| 8 | `pos-publish-framework-only` synthesis tool | `framework/tools/pos-publish-framework-only/` | **STAY** at canonical location. The synthesis tool's job is to PRODUCE the public artefact; it operates against canonical's tree. It cannot live inside `plugins/dev-sdlc/` because the plugin is itself one of the artefacts the tool's manifest classifies. **Disposition:** STAY. The tool's `publish-mode-manifest.yaml` is what gets EXTENDED (per AC.OSS-M6.8 already + new AC.OSS-M6.13 — partition manifest's `dev_only` is RETIRED in M6b post-extraction because most `dev_only` content has moved into the plugin's `plugins/dev-sdlc/**` glob; what remains is small enough to inline into `dev_and_public` exclusion subtractive globs). | Synthesis-tool-cannot-live-inside-its-own-output-classification — circular dependency. | STAY |
| 9 | Duration-estimation rubric | Currently in `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md` (host-global per-user) PLUS canonical copy at `docs/duration-estimation-rubric.md` (M2-classified `dev_only`) | **MOVE** the canonical copy to `plugins/dev-sdlc/docs/duration-estimation-rubric.md`. The host-global per-user copy STAYS at `~/.claude/...` (it's the user's own per-project memory; not in the canonical tree's authority). | Same logic as ODD methodology — long-form dev-mode-only convention belongs in the plugin. | M6b |
| 10 | FIDRAFT no-overhead capture pattern + DRAFT file lifecycle | `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (workspace-side draft) + the convention text at top of FUTURE_IDEAS.md + Idea 27 graduation pattern | **PARTITION.** MOVE the FIDRAFT lifecycle CONVENTIONS (the "no-overhead capture, daily rigor reviews, agents-surface-to-chat" rules from FUTURE_IDEAS_DRAFT.md lines 1-15) to `plugins/dev-sdlc/docs/conventions/fidraft-pattern.md` (NEW authored file). STAY the actual `FUTURE_IDEAS_DRAFT.md` file — it's canonical loam's project-level capture surface; analogous to Item 3's "actual plans STAY". | Same partition logic as Item 3: the pattern is what the plugin teaches; the actual FIDRAFT file is canonical loam's working draft. | M6b |
| 11 | HC#4 byte-content invariant + per-invariant frozen baselines + ODD §4 retire-and-rebaseline conventions | Currently expressed in `docs/odd-in-loam.md` §10 + amendment narratives + `framework/tools/loam/`'s seal-diff-test machinery | **PARTITION.** The CONVENTIONS (HC#4 definition, frozen-baseline rules, retire-and-rebaseline mechanics) MOVE to `plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md` (NEW authored file, condensed from `docs/odd-in-loam.md` §10). The IMPLEMENTATION (the `loam_cli.amend.seal_diff` module + per-component `tests/test_no_sealed_amendments.py`) MOVES with `loam amend` per Item 7. The PER-COMPONENT baseline data (`tests/SEAL_COMMIT` sidecars + `seals/SEAL_COMMIT.<slug>` narratives) STAYS in each sealed component (component-local data; not cross-cutting). | Convention-text moves; per-component data stays; engine moves with `loam amend`. | M6b |
| 12 | Seal ritual + commit ladder convention (`chore(seals):`, `docs(plans):`, etc.) | Precedent-driven; partially codified in `framework/tools/loam/templates/dispatch/sealed-component-build.md` | **MOVE** the convention codification to `plugins/dev-sdlc/docs/conventions/commit-ladder.md` (NEW authored file, condensed from precedent + dispatch-template excerpts). Same M2 dev-only character. | Same logic as Item 11. | M6b |
| 13 | Five-gate chain (research-plan → research → proposal → brief → build → seal) + amendment-cycle conventions | Currently expressed in `docs/odd-in-loam.md` + `docs/rebuild/STATE.md` §"Governing rules" rule #1 + master plan §6 sequencing | **MOVE** the convention codification to `plugins/dev-sdlc/docs/conventions/five-gate-chain.md` + `plugins/dev-sdlc/docs/conventions/amendment-cycle.md` (NEW authored files; condensed from the existing locations, which retain their references — `docs/rebuild/STATE.md` already classifies `dev_only`). | Same logic as Items 1, 11, 12. | M6b |
| 14 | `framework/tools/heavy-b-migrate/`, `framework/tools/orphan-plist-cleanup/`, `framework/tools/upgrade-merge-resolver/`, `framework/tools/loam-migrate-host-config/`, `framework/tools/loam-migrate-launchd-labels/`, `framework/tools/loam-migrate-dormancy-config/` | `framework/tools/<each>/` | **STAY** at canonical location. These are MIGRATION tools — one-shot scripts run during canonical-loam architecture migrations (not dev-discipline machinery used by every dev-mode session). The M2 partition manifest already classifies them `dev_only`; that classification stays correct. They MAY land in the plugin at v0.2 if the dev-mode user audience grows to need them; at v0.1.0 they're noise inside the plugin. | Out-of-scope per §5 v0.1.0 deferrals (Item 14 = "anything else dev-related the agent identifies during inventory that isn't already on this list" — agent finding: these are migration tools, not dev-discipline machinery). | STAY |
| 15 | (NEW — agent-identified) `CLAUDE.dev.md` (top-level dev-extension fragment) | `CLAUDE.dev.md` (workspace root) | **STAY** at workspace root. `CLAUDE.dev.md` is the top-level dev-extension fragment that loam-mode loads at SessionStart for DEV MODE workspaces (per `loam-mode B`'s load-time partition; M2 manifest classifies `dev_only`). It's a workspace-root entry point — it cannot live inside `plugins/dev-sdlc/` because Claude Code's loader reads workspace-relative paths at session start, not plugin-relative. | Workspace-root entry-point cannot live inside a plugin subtree. | STAY |
| 16 | (NEW — agent-identified) Sealed-component fence pattern itself + `tests/test_no_sealed_amendments.py` template | Embedded in every sealed component | **STAY** in each component (per-component data); the TEMPLATE for authoring new components' seal-tests MOVES to `plugins/dev-sdlc/templates/component/test_no_sealed_amendments.py.template` (NEW). | Same partition logic: per-component data stays where it is; template/authoring-shape goes into the plugin. | M6b |
| 17 | (NEW — agent-identified) `docs/rebuild/dev-mode-manifest.yaml` (the loam-mode dev-mode partition data) | `docs/rebuild/dev-mode-manifest.yaml` | **MOVE** to `plugins/dev-sdlc/dev-mode-manifest.yaml` (alongside Item 5's `loam-mode` source). The selector reads workspace-relative paths; the move requires updating the selector's path-lookup to either workspace-relative-or-plugin-relative fall-through (Idea 26 reader-fall-through), or to plugin-relative once the plugin owns the dev-mode-manifest. | The dev-mode partition is what `loam-mode` consumes; co-locating it with the package makes the plugin self-contained. | M6b |

### 6.5.3 Overall extraction strategy

**Extraction principle:** the plugin BECOMES the dev-mode package. After M6, a user who installs `plugins/dev-sdlc/` gets dev mode; a user who doesn't gets NORMAL USE. The M2 partition manifest's `dev_only` block (currently lines 147-175 of `publish-mode-manifest.yaml`) RETIRES post-M6 — most of its content has moved INTO `plugins/dev-sdlc/**`; what remains is so small (`framework/tools/<migration-tools>/`, `CLAUDE.dev.md`, `docs/rebuild/**` historical content) that it can be expressed as exclusion subtractive globs inside `dev_and_public` rather than as a separate `dev_only` class. **This is a programme-level dependency** flagged at §9 halt-trigger #11 + §11 finding #11.

**Three migration mechanics** apply across the inventory:

  - **`git mv` for whole-package moves.** Items 5 (`loam-mode`), 7 (`loam amend` package body), 9 (duration-estimation rubric file), 17 (dev-mode-manifest). `git mv` preserves history; the resulting commit is a rename + import-path update.
  - **Re-author for convention codifications.** Items 1, 3, 10, 11, 12, 13, 16. The conventions are CURRENTLY expressed by precedent + scattered prose; M6b authors fresh codification documents inside the plugin. The originating precedent locations are updated to point at the new home.
  - **Surgical PARTITION (file-by-file `git mv`) for shared components.** Item 6 (hands-off-lifecycle hooks). The component splits along the dev-mode-enforcement vs runtime-first-run line; each file moves individually based on its purpose.

**Dispositions summary:** of 17 inventory items, 9 are MOVE/MOVE-WHOLE, 5 are PARTITION, 3 are STAY. The 9 MOVE items are M6b's largest sub-amendment surface; the 5 PARTITION items are M6b's most delicate (require per-file analysis); the 3 STAY items are no-ops with documentation updates.

### 6.5.4 Ship-shape: sub-amendment series M6a → M6b → M6c (D-Q.M6.6 ruling)

**The extraction is too large for one amendment.** Following the M1.rename precedent (M1a..M1g sealed sequentially over 2026-04-29) — the M1 cycle's per-amendment tests verified renames component-by-component, with each amendment touching one mechanical concern at a time. M6's extraction has the same shape: many mechanical concerns, each independently testable, each carrying a fence-isolation risk if bundled with others.

**Recommended ship shape:**

  - **M6a — baseline plugin** (~90-180 min, mirror master plan §5 M6 row's original estimate). Authors `plugins/dev-sdlc/` with the user-facing v0.1.0 capability set ONLY (Surface A: AC.OSS-M6.1..M6.9 per the original plan-doc). Does NOT extract any dev machinery. Lands the plugin as a working v0.1.0-pattern-establishing artefact. **Sealed independently.** ACs: AC.OSS-M6.1..M6.9 + AC.OSS-M6.S(a) (sealed-component fence: 3 components — `plugins/dev-sdlc/`, `framework/tools/loam/`, `framework/tools/pos-publish-framework-only/`).
  - **M6b — extraction migrations** (~150-240 min). Per-inventory-item `git mv` + import-path updates + plugin-doc authoring + the M2 partition-manifest collapse + `loam-mode` location migration + hands-off-lifecycle hook PARTITION. **Sealed independently.** ACs: AC.OSS-M6.10..M6.16 + AC.OSS-M6.S(b) (sealed-component fence: ~5-7 components — `plugins/dev-sdlc/`, `framework/hands-off-lifecycle/`, `framework/tools/loam/`, `framework/tools/pos-publish-framework-only/`, `docs/rebuild/`-as-plan-tree, plus `framework/tools/loam-mode/` if classified as a sealed component, plus the `docs/odd-*.md` move treated as a documentation-tree move).
  - **M6c — cleanups** (~30-60 min). Post-extraction trailing edges: dead-link cleanup in surrounding docs, cross-reference updates in `docs/rebuild/STATE.md` + master plan + remaining FUTURE_IDEAS references, retirement of any `dev_only` block in the partition manifest if M6b didn't complete it. **Sealed independently.** ACs: AC.OSS-M6.S(c) (single sealed-component fence covering whatever components the trailing-edge work touches).

**Total wall-clock: ~270-480 min midpoint 360.** Compared to a single-amendment ship (which would be 270-450 min by the same arithmetic but with much higher fence-collision risk + harder rollback + harder review-pass), the series shape costs effectively zero overhead for substantially better safety.

**Inter-amendment dependencies:**

  - M6b CANNOT start until M6a is sealed (M6b's git-mv operations require the plugin tree to exist as a destination).
  - M6c CANNOT start until M6b is sealed (M6c's cleanups respond to whatever trailing edges M6b leaves).
  - M9.scrub (per master plan §6) is gated on M6's full completion (all three sub-amendments) — scrub captures the final public surface; until M6b retires `dev_only` block content, the partition is in flight.
  - M7.docs-lane remains parallel-safe with all three sub-amendments per master plan §6 sequencing rule #4 — M7's content authoring is `framework/`-relative; M6's extraction is `plugins/`-relative + `dev_only`-block-relative; no overlap.

### 6.5.5 Per-AC ladder-up table (Surface B)

| AC | Master plan AC ladder | Prime objective |
|---|---|---|
| AC.OSS-M6.10 (CDCs MOVE to plugin docs) | AC.OSS.6 (Dev/SDLC plugin ships) + AC.OSS.3 (no dev-discipline machinery in public — by extracting the dev CDCs into the plugin, the main FUTURE_IDEAS.md becomes lighter and dev-machinery is structurally separated) | AC.PO.2 (toolkit-primitive — plugin self-contains the dev-discipline corpus) |
| AC.OSS-M6.11 (long-form ODD methodology MOVE to plugin docs) | AC.OSS.3 + AC.OSS.6 | AC.PO.2 (the methodology IS the toolkit-primitive that the plugin teaches) |
| AC.OSS-M6.12 (loam-mode MOVE to plugin) | AC.OSS.6 (Dev/SDLC plugin DELIVERS dev mode) | AC.PO.2 (dev mode is plugin-supplied; NORMAL USE is the harness baseline) |
| AC.OSS-M6.13 (M2 partition manifest `dev_only` block retires; what remains expressed as `dev_and_public` exclusions) | AC.OSS.3 (no dev-discipline in public) — once dev-discipline lives in the plugin, the partition simplifies | AC.PO.2 (cleaner partition surface) |
| AC.OSS-M6.14 (hands-off-lifecycle A1-A4 gate hooks PARTITION + MOVE to plugin) | AC.OSS.6 (gates are dev-mode-only; they live with the plugin) | AC.PO.2 (gate hooks are plugin-delivered structural enforcement) |
| AC.OSS-M6.15 (loam amend MOVE to plugin; unified-CLI wrapper STAYS) | AC.OSS.6 (loam amend is dev-discipline machinery) | AC.PO.2 (amend is plugin-delivered) |
| AC.OSS-M6.16 (convention docs — five-gate chain, amendment cycle, sealed-component invariants, FIDRAFT pattern, plan-doc/manifest conventions, commit ladder, seal-test template — authored under plugin) | AC.OSS.6 + AC.OSS.3 | AC.PO.2 (the plugin teaches the conventions) |

---

## 7. Test scope (per dispatch constraint)

Test scope is **narrow**: 9 (or 10 with M6.9) new test files exercising the plugin's behaviour at function-boundary level. **No full-suite rerun pre-seal** per `feedback_amendment_dispatch_speedups`.

Per-test ownership:

  - 7 in `plugins/dev-sdlc/tests/` — the new component's own seal-test surface.
  - 1 in `framework/tools/loam/tests/` — for the entry-point-discovery mechanism extension.
  - 1 in `framework/tools/pos-publish-framework-only/tests/` — for partition manifest classification.

Plus one **standard** seal-test per the new-component template:
  - `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — authored to admit `plugins/dev-sdlc/`-relative paths only; rejects diffs outside the subtree (the standard seal-fence test pattern; mirror `framework/dormancy/tests/test_no_sealed_amendments.py`).

**No new tests in scope-of-work, objective-tracker, memory-system, primary-persona, workspace-bootstrap.** Their internal logic remains under existing test coverage; M6 tests cover the plugin's behaviour + its integration seam.

---

## 8. Risks (M6-specific)

1. **First-component-at-`plugins/` partition risk.** The M2 partition manifest doesn't yet classify `plugins/`. M6 extends it; if the extension is incorrect (e.g. glob doesn't match the directory layout), the synthesis tool drops the plugin from the public artefact silently. **Mitigation:** AC.OSS-M6.8's classification test runs against canonical HEAD's actual `plugins/dev-sdlc/` tree post-build; halt if classification incomplete.
2. **Subcommand-discovery mechanism is NEW.** `loam_cli.cli` doesn't yet have an entry-point-group resolution path. The recommendation (`loam.cli.subcommands` group) is symmetric to bootstrap's pattern but adds a new entry-point-group to the framework. **Mitigation:** AC.OSS-M6.6's two-test pair (covers both `loam_cli`'s side of the discovery + the plugin's side); if discovery breaks, both tests fail with clear signals.
3. **Stage-gate parser fragility.** The gate checks for "objective + AC" in artefact files. The parser uses Markdown-frontmatter + heading-based detection (the same pattern existing FUTURE_IDEAS / plans use). If the user's artefact uses non-standard formatting, the gate may false-fail. **Mitigation:** the gate's failure mode is `StageGateFailedError` with a structured `reason` field; the persona's exception-handling translates the reason to natural-language guidance; user can fix the artefact + retry. AC.OSS-M6.4's tests cover the four named failure modes.
4. **Workspace-local SQLite contention.** If two `loam project` invocations run concurrently against the same workspace, SQLite's WAL mode handles serialization but the per-project state may diverge. **Mitigation:** the plugin's CLI is invoked synchronously from the persona's tool-call path; concurrency is not a v0.1.0 concern. Ship with WAL mode + a comment naming the v0.2 concurrency-handling work.
5. **Methodology opt-out mirror diverges from user-visible artefacts.** The internal ODD mirror (`<project>/.dev-sdlc-odd-mirror.yaml`) is plugin-maintained; if the user edits the user-visible artefact (`<project>/spec/<slug>.md`), the mirror falls out of sync. **Mitigation:** the mirror is regenerated lazily on each `gate_check` from the user-visible artefact; the mirror is a derived view, not a source of truth.
6. **Plugin-tree pattern lock-in.** Establishing `plugins/<name>/` at M6 means v0.2+ plugins inherit the pattern. If the pattern turns out wrong (e.g. plugins should live as PyPI packages, not workspace-local subdirectories), v0.2 has to migrate. **Mitigation:** the plugin's pyproject.toml + src/ layout matches PyPI-installable package shape; v0.2 migration to PyPI distribution is mechanical (rename directory, push to registry).
7. **Skill-loader + plugin-skill discovery interaction.** AC.OSS-M6.9 (D-Q.M6.4 ship path) depends on the persona's skill loader (post-#73 corpus-inlining hook) reading from `plugins/<name>/skills/`. The current loader reads `framework/`-relative paths via `_resolve_corpus_path`. **Mitigation:** verify at build time that the loader reads plugin-relative paths via reader-fall-through (Idea 26's surfaced affordance); if not, halt and surface — the skill ships as v0.1.1 not v0.1.0 (D-Q.M6.4 deferral path).
8. **HC#4 byte-content invariant.** The plugin is NEW — no pre-existing HC#4 sample paths. **Mitigation:** AC.OSS-M6.S's seal-test is authored to admit only `plugins/dev-sdlc/`-relative paths; HC#4 invariant remains GREEN trivially. Per plan §11 finding #6.

---

## 9. Halt-and-surface conditions

Per dispatch + `feedback_subagent_odd_violation_halt`:

1. **Idea 3's enumerated capabilities have grown beyond what's reasonable for v0.1.0.** Per dispatch halt-trigger #1. Verified at plan-authoring (research finding R1): post-deferral capability set fits within ~5-7 concrete features matching pre-existing component scope. **No halt; plan proceeds.** If the builder finds during build that the capability set has grown (e.g. an unforeseen integration point), halt and propose split.
2. **Plugin shape contradicts existing workspace-bootstrap plugin-discovery protocol.** Per dispatch halt-trigger #2. Verified at plan-authoring (research finding R2): plugin's `Contribution` class shape matches `BaseContribution` precedent; entry-point group + manifest opt-in pattern is identical to existing adapters. **No halt; plan proceeds.**
3. **ODD §2.5 violations in surrounding code/docs.** Per dispatch halt-trigger #3 + global rule. Verified at plan-authoring (research finding R6): no violations encountered. **No halt.** If builder finds during build, halt and surface — do NOT silently extend.
4. **Authoring research finds Idea 3's premise inconsistent with current corpus state.** Per dispatch halt-trigger #4. Verified at plan-authoring (research finding R7): no inconsistency. **No halt.**
5. **Plugin's host-attribute access requires not-yet-implemented host surfaces.** Verified at plan-authoring: `host.scope_runtime`, `host.objective_tracker`, `host.workspace_root` all exist today. The plugin assigns `host.dev_sdlc = runtime` (per the open-attribute-surface convention; matches dormancy adapter's `host.dev_sdlc` precedent). If builder finds an unmet host surface, halt and surface.
6. **Subcommand-discovery mechanism rejected by `loam_cli`.** D-Q.M6.5 recommends entry-point-group form. If at build time `loam_cli`'s author shows this is wrong (e.g. requires re-architecting `cli.main`), halt and surface — fall back to plan §10 D-build.M6.5 alternative (host-registry form; expands fence to include workspace-bootstrap).
7. **HC#4 byte-content invariant breach.** Per Finding #6. The plugin is NEW; no HC#4 sample paths under it; the HC#4 invariant should remain GREEN through M6. If builder finds an HC#4 retire-and-rebaseline is required (e.g. partition-manifest change impacts a sample path the plan-author didn't see), halt; do NOT silently rebaseline.
8. **ODD §2.5 violations in plugin source.** Per `feedback_subagent_odd_violation_halt` — every code path in M6's diff must ladder up to a named AC under AC.OSS-M6.\*. If builder finds a defensive branch without backing AC, halt.
9. **Frozen-baseline / per-invariant-BASELINE concerns.** If any of the 3 (or 4) fenced components' seal-test BASELINEs are pinned (`frozen_baseline: true`) and M6 requires advancing them, halt and surface; the BASELINE advance must be explicit. **Verified at plan-authoring:** none of the components in M6's fence have frozen baselines today; recommend `frozen_baseline: false` per existing precedent.
10. **Wall-time exceeds projected estimate by >50%.** Per master plan §8 halt-trigger #8. Build slice predicted 90-180 min midpoint 135 for M6a + 150-240 min for M6b + 30-60 min for M6c; halt at ~360 min for M6a, ~360 min for M6b, ~90 min for M6c if not converging. Surface current state; owner triages whether to continue, split, or pause.

11. **Surface B extraction encounters self-bootstrap blocker.** Per Finding #11 + §10 D-Q.M6.8 + §10 D-build.M6.15. If at M6b build-time the shadow-then-flip mechanic encounters an unforeseen blocker (e.g. `loam amend` plugin-side cannot resolve subcommand discovery while canonical-side is still present), halt and surface — owner ruling required.

12. **Surface B extraction reveals an item with ambiguous disposition not anticipated by §6.5.2.** If during M6b an inventory item turns out to require a different MOVE/STAY/PARTITION classification than the table records (e.g. a hidden cross-component dependency surfaces), halt and surface — do NOT silently re-classify.

13. **Two-modes design contradiction.** Per Finding #13: Idea 13 + the extraction directive are compatible. If at build time a contradiction surfaces (e.g. an artefact NORMAL USE depends on that the extraction would move into the plugin), halt and surface specific contradiction.

14. **Programme-level partition manifest dependency**. Per Finding #12: M2's partition manifest is mutated by M6b. If the mutation breaks any M2 invariant (audit-completeness, classification-uniqueness), halt and surface — the M2 contract is plan-doc authority for canonical loam's public-surface synthesis.

---

## 10. Decisions (recommendations locked; recorded for §14 register)

### Owner-rulable (D-Q.M6.\*)

#### D-Q.M6.1 — Plugin tree placement

**Question.** `plugins/dev-sdlc/` (separate plugin tree) vs `framework/dev-sdlc/` (in-tree, sibling of existing components).

**Options + cost/risk:**
- **A. `plugins/dev-sdlc/`** (RECOMMEND per master plan D-Q.OSS.5): establishes the plugin-tree pattern at v0.1.0; v0.2+ plugins inherit cheaper landing. **Cost:** M6 partition manifest update + new top-level tree (one-time). **Risk:** the pattern locks in (mitigation per §8 risk #6).
- **B. `framework/dev-sdlc/`**: no partition manifest update; plugins look like framework components. **Cost:** zero structural cost at M6. **Risk:** plugin #2 has to make the plugin-tree decision under publishing pressure; v0.2 inherits the cost; conflates "core harness" vs "plugin extension."

**Recommendation:** **Option A — `plugins/dev-sdlc/`.** The first plugin pays the structural cost so subsequent plugins don't. Aligns with master plan D-Q.OSS.5. Aligns with the conceptual distinction between "core harness components" (framework/) and "optional plugin extensions" (plugins/).

#### D-Q.M6.2 — Objective-extraction skill scope at v0.1.0

**Question.** Defer entirely vs ship a stub vs ship complete.

**Options + cost/risk:**
- **A. Defer entirely** (RECOMMEND): land at v0.1.1 as its own master-plan cycle. **Cost at v0.1.0:** zero. **Risk:** v0.1.0 ships without the existing-repo on-ramp Idea 3 names as "high leverage for SDLC plugin adoption."
- **B. Ship a stub**: a skill scaffold with placeholder messaging ("coming soon — currently extracts trivial cases"). **Cost at v0.1.0:** ~30-60 min additional build time. **Risk:** users encounter the stub + lose trust; v0.1.0 ships incomplete-feeling.
- **C. Ship complete**: the slice/swarm/aggregate engine + token-budget instrumentation + background-droppable scopes. **Cost at v0.1.0:** 3-5x M6's wall-clock; pushes publish gate by days-to-week. **Risk:** v0.1.0 timeline blows; M6 alone consumes the publish window.

**Recommendation:** **Option A — defer entirely.** Master plan §5 M6 row already names the deferral as builder's call. v0.1.0 ships the methodology-shaped workflow; v0.1.1 adds the existing-repo on-ramp. Honest about scope.

#### D-Q.M6.3 — Per-project CLI verb naming

**Question.** `loam project ...` vs `loam dev ...` vs `loam new ...`.

**Options + cost/risk:**
- **A. `loam project ...`** (RECOMMEND): explicit "project lifecycle" framing; matches `loam amend ...` precedent (verb-objected). **Cost:** zero. **Risk:** "project" is generic — future MAY collide with non-Dev-SDLC project shapes (e.g. a future "project portfolio" plugin).
- **B. `loam dev ...`**: closer to plugin name `dev-sdlc`. **Cost:** zero. **Risk:** "dev" is overloaded with dev-mode (loam-mode); user confuses `loam dev` (Dev/SDLC) with dev-mode invocation.
- **C. `loam new ...`**: verb-first (`loam new project <slug>`, `loam new feature`). **Cost:** zero. **Risk:** `new` is verb-only, doesn't compose with the other operations (`status`, `advance`, `list`).

**Recommendation:** **Option A — `loam project ...`.** Composes cleanly across operations; doesn't overload the dev-mode terminology; future "project portfolio" plugin can land at `loam portfolio ...` (different verb).

#### D-Q.M6.4 — `/start-project` Claude skill ship-at-v0.1.0 vs defer

**Question.** Ship the `/start-project` skill at `plugins/dev-sdlc/skills/start-project.md` at v0.1.0 vs defer to v0.1.1.

**Options + cost/risk:**
- **A. Ship** (RECOMMEND): adds AC.OSS-M6.9; +30-45 min build time; skill is intent-routing for first-click users. **Cost:** modest (one Markdown file with frontmatter; one test). **Risk:** depends on the persona's skill loader handling plugin-relative paths via Idea 26's reader-fall-through (verified at plan-authoring; if unverified at build time, halt per §9 #7).
- **B. Defer**: drops AC.OSS-M6.9; M6 ships 8 ACs; first-click users invoke the plugin via persona conversation rather than skill routing. **Cost at v0.1.0:** smaller M6 fence. **Risk:** first-click experience is less obvious (user has to discover the plugin via persona conversation rather than a `/start-project` slash command).

**Recommendation:** **Option A — ship the skill.** The cost is modest; the leverage (first-click intent routing for the developer audience landing on HN/GitHub) is high. Per Lens 1 (Claude-leverage-first): skills are the right Claude primitive for user-facing intent surfaces.

#### D-Q.M6.6 — Ship shape: single amendment vs sub-amendment series

**Question.** M6 ships as ONE multi-component amendment vs as a sub-amendment series M6a → M6b → M6c (mirror M1.rename's M1a..M1g pattern).

**Options + cost/risk:**
- **A. Sub-amendment series** (RECOMMEND per §6.5.4): three independently-sealable amendments. **Cost:** ~270-480 min midpoint 360 (versus 270-450 for single). **Risk:** lower fence-collision risk, lower review cognitive load, easier rollback per sub-amendment, mirror established M1.rename precedent. CRITICAL ADVANTAGE: M6a delivers the user-facing capability set (Surface A) sealed independently — if M6b's extraction encounters an unexpected blocker, M6a remains shipped + the publish gate is preserved.
- **B. Single multi-component amendment**: one amendment touches all 17 inventory items. **Cost:** smaller seal overhead (one seal commit instead of three). **Risk:** large diff window; high fence-collision; rollback = revert the whole amendment + re-author; reviewer cognitive load. CRITICAL DISADVANTAGE: extraction depends on `loam amend` itself (per §11 finding #11) — a single amendment that moves `loam amend` mid-build is the same "rename-the-tool-while-using-it" complication M1g handled by sub-amendment splitting. Single-amendment shape forces M1g's lesson to be re-learned.

**Recommendation:** **Option A — sub-amendment series.** Mirrors the M1.rename precedent that already proved this shape works for cross-cutting structural change. The marginal extra wall-clock (~30-60 min) is bought as risk reduction.

#### D-Q.M6.7 — Hands-off-lifecycle A1-A4 gates disposition

**Question.** PARTITION (gates MOVE; runtime hooks STAY) vs MOVE-WHOLE (entire `framework/hands-off-lifecycle/` MOVES) vs STAY-WHOLE.

**Options + cost/risk:**
- **A. PARTITION** (RECOMMEND): the A1-A4 gates + corpus helpers MOVE to `plugins/dev-sdlc/hooks/`; the first-run + statusline + memory-supervisor wiring STAYS. **Cost:** per-file `git mv` analysis. **Risk:** mid-component seam; the seal-test fence for `framework/hands-off-lifecycle/` must be widened during M6b to admit the file-deletion side. Per docstring inspection, the dev-mode-vs-runtime split is clean (gates self-identify as DEV-MODE-only via mode-bit short-circuit).
- **B. MOVE-WHOLE**: entire component moves. **Cost:** less per-file analysis. **Risk:** runtime first-run + statusline + memory-supervisor wiring lives only in DEV MODE workspaces post-move. NORMAL USE workspaces lose first-run, statusline, and the memory-supervisor (the M5-wired component). UNACCEPTABLE — these are runtime, not dev-discipline.
- **C. STAY-WHOLE**: gates remain at `framework/hands-off-lifecycle/hooks/`. **Cost:** no movement. **Risk:** the gates' M2 partition classification (`dev_and_public` per the existing manifest line 112) means they ship publicly even though they're dev-mode-only enforcement. Doesn't resolve the original directive. The current state of "dev_and_public" + "no-op in NORMAL USE via mode-bit" is functionally fine but contradicts the directive's "extract all dev-related things into the dev/sdlc plugin."

**Recommendation:** **Option A — PARTITION.** Honest about the dev-mode-vs-runtime distinction within the component; preserves NORMAL USE behaviour intact; honours the directive.

#### D-Q.M6.8 — `loam amend` disposition

**Question.** PARTITION (some logic MOVES, the wrapper STAYS), MOVE-WHOLE (the entire `framework/tools/loam/` package MOVES), or STAY-WHOLE (no change).

**Options + cost/risk:**
- **A. MOVE-WHOLE** (RECOMMEND per §6.5.2 Item 7): `framework/tools/loam/src/loam_cli/amend/` MOVES to `plugins/dev-sdlc/loam-amend/src/loam_amend/`; the unified `loam` CLI wrapper STAYS at `framework/tools/loam/` as a thin dispatcher (it owns the `loam.cli.subcommands` entry-point group resolution introduced at M6a). **Cost:** mid-package surgical extraction + console-script-rename. **Risk:** the build process itself uses `loam amend` for amendment seal — staging is critical (per §11 finding #11). RECOMMENDED MITIGATION: M6b authors the migration in a SHADOW form first (the new package exists at `plugins/dev-sdlc/loam-amend/` with content COPIED, not moved; `loam amend` console-script remains pointed at the canonical-side package); the seal commit FLIPS the entry-point to the plugin's package + DELETES the canonical-side; the seal commit is itself sealed via the SHADOW (plugin-side) `loam amend` invocation, not the canonical-side. This is the same shadow-then-flip pattern M1g used for the `loam amend` rename.
- **B. PARTITION**: separate the bookkeeping logic (templates, seal-diff machinery) into the plugin while keeping a leaner `loam amend` in canonical. **Cost:** higher per-file analysis. **Risk:** unclear what the right partition line is; both halves remain mid-cohesive.
- **C. STAY-WHOLE**: `framework/tools/loam/` stays put. **Cost:** zero movement. **Risk:** doesn't honour the directive — `loam amend` IS dev-discipline machinery; users without dev-mode have no reason to invoke it.

**Recommendation:** **Option A — MOVE-WHOLE.** The shadow-then-flip mitigation per M1g precedent is already a known pattern; the cost is bounded; the post-extraction shape is clean.

#### D-Q.M6.9 — Methodology + convention docs disposition

**Question.** MOVE the long-form ODD methodology + duration-estimation rubric + dev CDCs into `plugins/dev-sdlc/docs/` vs symlink-shim (file STAYS at canonical, plugin contains a symlink).

**Options + cost/risk:**
- **A. MOVE** (RECOMMEND per §6.5.2 Items 1, 2, 9): canonical files MOVE; cross-references (in STATE.md, master plan, etc.) update to point at plugin-relative paths. **Cost:** cross-reference grep + update in M6b. **Risk:** post-extraction, a user without the plugin installed cannot read these docs from a canonical clone (they're inside the plugin's tree). Acceptable per the extraction principle ("dev-mode-only artefacts live in the plugin"); the public `docs/design/odd.md` short-form remains accessible to all readers.
- **B. Symlink-shim**: canonical retains the file; plugin contains a symlink that points back. **Cost:** symlinks across packages don't survive PyPI install (when the plugin is shipped via `pip install loam-plugin-dev-sdlc`, the symlink target outside the plugin tree breaks). **Risk:** unworkable across distribution mechanisms.
- **C. Symlink reverse**: canonical retains a symlink; plugin holds the file. **Cost:** breaks from canonical-only views (a user who clones canonical sees a symlink to a file the canonical tree doesn't contain). **Risk:** confusing, unworkable.

**Recommendation:** **Option A — MOVE.** Symlinks don't survive PyPI distribution; canonical-clone-without-plugin is the same situation as canonical-clone-without-dev-mode (the plugin IS dev mode); user can `pip install` the plugin to read the long-form docs.

### Method-shape decision the plan resolves (recorded for transparency)

#### D-build.M6.5 — `loam project` subcommand discovery mechanism

**Decision:** entry-point group `loam.cli.subcommands` with values pointing at the subcommand's argparse builder + dispatcher.

**Why this shape:** symmetric with workspace-bootstrap's existing `loam.bootstrap.contributions` pattern. Zero new state; the framework (`loam_cli.cli.main`) iterates entry-points at startup to enumerate subcommands. Plugin's `pyproject.toml` ships:

```toml
[project.entry-points."loam.cli.subcommands"]
project = "loam.plugins.dev_sdlc.cli:build_project_subcommand"
```

`loam_cli.cli.main` calls `importlib.metadata.entry_points(group="loam.cli.subcommands")` + invokes each `build_*` callable to register the subcommand parser. Identical pattern to bootstrap's `discovery.py` resolution.

**Alternative considered + rejected:**
- Host-registry form: workspace-bootstrap exposes `host.loam_cli_registry`; plugin registers its subcommand at `contribute()` time; `loam_cli.cli.main` reads `host.loam_cli_registry`. **Rejected:** widens the workspace-bootstrap fence + couples CLI surface to bootstrap lifecycle (CLI works without bootstrap running; e.g. `loam project --help`).
- Separate console-script binary (`loam-project`): ship as its own `[project.scripts]`. **Rejected:** breaks the unified-CLI narrative (per M1g rebrand); user gets multiple binaries instead of one verb tree.

### Surface-B method-shape decisions (recorded for transparency)

#### D-build.M6.10 — `git mv` mechanic vs copy-and-delete for MOVE-class items

**Decision:** `git mv` for whole-file/whole-package moves (Items 5, 7-as-package-body, 9, 17, M6b's hooks PARTITION). `git mv` preserves history; `git log --follow` traces the file's lineage post-move. Copy-and-delete loses history. **Why this shape:** standard Git rename detection. Builder's call to use `git mv` and verify `git log --follow` returns expected history at each PR.

#### D-build.M6.11 — Convention-doc authoring scope at v0.1.0

**Decision:** convention codification documents (per Item 16 / AC.OSS-M6.16) are **concise codifications, NOT exhaustive prose.** Each convention doc is 100-300 LOC, structured as: objective + summary + named conventions/rules + cross-references + applied-immediately footer. **Why this shape:** the conventions are currently expressed by precedent + scattered prose in `docs/odd-in-loam.md`. M6b's job is to name + locate them, not to author exhaustive new content. The exhaustive content lives in `docs/odd-in-loam.md` (which itself MOVES to `plugins/dev-sdlc/docs/odd-in-loam.md` per Item 2). Builder's call on exact section structure per convention.

#### D-build.M6.12 — Plugin-shipped hooks registration mechanism (Surface B integration with Claude Code's `settings.json`)

**Decision:** the plugin's `contribute(host)` body writes a `settings.json` extension fragment to `<workspace>/.claude/settings.json` at startup, registering the A1-A4 PreToolUse hooks. Claude Code's settings-merge mechanism handles it. **Why this shape:** symmetric with `framework/hands-off-lifecycle/hooks/settings.json.fragment`'s existing pattern (the runtime first-run hook is registered the same way). The plugin extends the pattern from "ship-time fragment" to "runtime contribution-time merge." Builder's call on whether the merge is idempotent + reversible (i.e. uninstalling the plugin removes the fragment) — recommendation: idempotent + reversible.

#### D-build.M6.13 — Final shape of `dev_only` block post-extraction

**Decision:** post-M6b, `dev_only:` retains entries for migration tools (`framework/tools/heavy-b-migrate/**`, `orphan-plist-cleanup/**`, `upgrade-merge-resolver/**`, `loam-migrate-*/**`) + `framework/tools/pos-publish-framework-only/**` (the synth tool stays per Item 8) + `CLAUDE.dev.md` (Item 15) + `docs/rebuild/**` historical content. `dev_only` does NOT fully retire; it shrinks to the items that genuinely STAYed in canonical. **Why this shape:** AC.OSS-M6.13's verification framing ("the post-M6b `dev_only` list matches the recorded post-extraction shape") accepts a non-empty `dev_only` — that's the empirical reality. The dispatch's halt-trigger #5 is satisfied: the partition manifest ITSELF doesn't retire, but the `dev_only` block CONTRACTS to a known small surface.

#### D-build.M6.14 — Plugin's own M2 partition classification

**Decision:** `plugins/dev-sdlc/**` classifies as `dev_only` post-M6b (NOT `dev_and_public` as originally stated in AC.OSS-M6.8). **Why this shape:** the plugin contains dev-discipline machinery (extracted from `dev_only` items 1-3, 5-7, 9-13, 16-17 above). It SHOULD NOT ship publicly under the existing partition mechanism. **CRITICAL CONSEQUENCE:** the original AC.OSS-M6.8 (Surface A) said `plugins/dev-sdlc/**` is `dev_and_public` — POST-M6b that classification CHANGES to `dev_only`. The change is captured in AC.OSS-M6.13's "post-extraction shape" verification. **Owner-rulable alternative** if rejected: introduce a NEW partition class `plugin_publishable` for "the plugin's BASE ships publicly when the user installs it via `pip install loam-plugin-dev-sdlc`, but the `pos-publish-framework-only` tool's PUBLIC SYNTHESIS does NOT include the plugin tree" — this is the cleaner separation but adds a new partition class. Recommendation: simpler `dev_only` reclassification at M6b; revisit `plugin_publishable` if a v0.2 plugin needs the distinction.

#### D-build.M6.15 — Shadow-then-flip migration shape for `loam amend`

**Decision:** per D-Q.M6.8 Option A's mitigation. M6b authors the migration in TWO commits inside the M6b sub-amendment: (a) SHADOW commit that creates `plugins/dev-sdlc/loam-amend/` as a COPY of the canonical-side package (no DELETE; both packages exist; the plugin's entry-point points at the canonical-side package via a re-export shim); (b) FLIP commit that updates the entry-point to point at the plugin's package + DELETES the canonical-side `framework/tools/loam/src/loam_cli/amend/` subtree. The seal commit follows (b) and is itself sealed via the plugin's `loam amend` invocation. **Why this shape:** mirrors M1g's pattern; the shadow window allows the build process to seal SHADOW's commits using the canonical-side `loam amend`, then flip atomically.

#### D-build.M6.16 — Post-MOVE cross-reference update mechanic

**Decision:** automated grep+sed under `docs/rebuild/**` + `framework/**` + canonical-side dispatch templates for references to the moved files. Updates land in the same M6b commit as the corresponding MOVE per Item. **Why this shape:** the references are textually grep-able (file path strings); the update is mechanical; bundling the references with the MOVE keeps each commit semantically coherent. Builder authors a small helper at M6b time if the manual count is impractical.

### Method-shape decisions deferred to builder

Per ODD §4 / `feedback_agent_prompts_scope_only`, the plan-doc carries outcome-shape ACs; method-shape (file layout beyond top-level, exact test names beyond AC-mapped, exact LOC deltas, internal helper function shapes) is the builder's call.

What's intentionally not specified:
- Stage-gate parser implementation (Markdown-frontmatter parser library vs hand-rolled regex). Recommendation: stdlib (`yaml.safe_load` for frontmatter; regex for heading detection); zero new third-party dep.
- SQLite store schema details (exact column names beyond the obvious; index decisions). Recommendation: mirror `framework/objective-tracker/`'s store pattern.
- OTel attribute schema. Recommendation: match existing component patterns (`loam.<comp>.<event>` span names; structured attributes).
- Per-stage template content beyond the methodology-discrimination point. Recommendation: ODD templates use loam's existing plan-doc shape; TDD/BDD/adhoc templates are minimal scaffolds.
- Whether `_resolve_corpus_path` reader-fall-through covers `plugins/<name>/skills/` automatically (per Idea 26) or needs an additive change. Recommendation: verify at build time; halt + drop AC.OSS-M6.9 if additive change needed (D-Q.M6.4 deferral path).

---

## 11. Pre-build verification + halt-and-surface findings encountered during plan authoring

### Finding #1 — `plugins/` is NOT in M2 partition manifest's `audit_roots`

**Surface:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`'s `audit_roots:` list contains `framework/`, `docs/`, `CLAUDE.md`, `CLAUDE.dev.md`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `personas/`, `data/`, `workspace/`, `.pos/`, `.scratch/`, `.mcp.json`, `.gitignore` — **NOT `plugins/`.** If the plugin lands at `plugins/dev-sdlc/`, M6 must extend the partition manifest in the same amendment.

**Resolution:** AC.OSS-M6.8 captures the partition manifest extension as an explicit AC; the partition manifest's modification is part of M6's seal-diff fence (under `framework/tools/pos-publish-framework-only/`). The extension is small (1 line in `audit_roots` + 1 glob entry in `dev_and_public`).

### Finding #2 — `loam_cli` does NOT yet have a subcommand-discovery mechanism

**Surface:** `framework/tools/loam/src/loam_cli/cli.py`'s `main()` function currently dispatches to a hardcoded `amend` subcommand. There's no entry-point-group resolution path for plugin-shipped subcommands.

**Resolution:** D-build.M6.5 (recommendation: entry-point-group form) authors the discovery mechanism. AC.OSS-M6.6 covers the test for `loam_cli`'s side of the mechanism + the plugin's side. The mechanism extension is small (~30-50 LOC in `loam_cli.cli`).

### Finding #3 — Skills tree location is NOT yet established at framework level

**Surface:** there's no precedent for `skills/` directory inside any framework component. The persona's skill loader (post-#73 corpus-inlining hook) reads `framework/`-relative paths via `_resolve_corpus_path`. Plugin-shipped skills at `plugins/<name>/skills/` MAY require additive `_resolve_corpus_path` changes.

**Resolution:** D-Q.M6.4 surfaces the decision as owner-rulable. Recommend SHIP per Idea 26's reader-fall-through composition — verify at build time the loader reads plugin-relative paths via fall-through; halt + drop AC.OSS-M6.9 if additive change needed (defer skill to v0.1.1). Per §9 halt-trigger #7.

### Finding #4 — HC#4 byte-content sample paths NOT impacted by M6 diff

**Surface:** the M6 diff is contained in `plugins/dev-sdlc/` (NEW component — no pre-existing samples) + `framework/tools/loam/` (subcommand discovery — additive, no sample paths) + `framework/tools/pos-publish-framework-only/` (partition manifest YAML edit — no sample paths in YAML).

**Resolution:** D-build.M6.6 — NO RETIRE-AND-REBASELINE. HC#4 invariant remains GREEN through M6.

### Finding #5 — Per-component CLI seal-test pattern verified

**Surface:** existing components' `tests/test_no_sealed_amendments.py` follows a consistent pattern (mirror `framework/dormancy/tests/test_no_sealed_amendments.py`). `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` MUST be authored at M6 alongside the source.

**Resolution:** AC.OSS-M6.S explicitly names the seal-test authoring as part of the new-component scope. The pattern: `allowed_prefixes = ("plugins/dev-sdlc/",)` for the diff-admission window.

### Finding #6 — `pos-new-workspace` enumeration of available plugins

**Surface:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` generates fresh workspaces' `bootstrap.yaml`. To make the plugin discoverable for new workspaces, `new_workspace.py` would ideally enumerate the available plugins at `pos-new-workspace` invocation time (rather than hardcoding the contributions list).

**Resolution:** explicit OUT-OF-SCOPE for v0.1.0 (per §5). At v0.1.0, `pos-new-workspace`'s generated `bootstrap.yaml` does NOT list `dev_sdlc` by default; users opt in by editing `bootstrap.yaml`. v0.2 candidate: enumerate available plugins automatically. Mitigation: the public docs scaffold (M7) names how to opt the plugin in.

### Finding #7 — Existing plugin-shape precedent: NONE

**Surface:** verified at plan-authoring — `framework/workspace-bootstrap/pyproject.toml` is the only file currently shipping `loam.bootstrap.contributions` entry-points. The plugin would be the FIRST EXTERNAL contributor to the entry-point group from outside the bootstrap package itself.

**Resolution:** AC.OSS-M6.1's test asserts the entry-point-discovery path works for plugin-tree contributors. Recorded for §14 (this is a structural milestone — first plugin proves the pattern).

### Finding #8 — Idea 3's "review pos v1's full SDLC module set" guidance

**Surface:** Idea 3 names "Review pos v1's full SDLC module set" as a research scope item: enumerate every module/plugin/configuration-set in current pOS, classify each as (a) translates / (b) translates with redesign / (c) obsolete / (d) irrelevant.

**Resolution:** v0.1.0 deliberately ships the WORKFLOW SHAPE (5 stages + gates + opt-out + integration) without literal pos-v1 SDLC module porting. The shape proves the pattern; v0.2+ plugin development can reach back into pos-v1's SDLC for specific surfaces (workflow engine, contradiction detection, roadmap tooling) as separate plugin-cycles or as Dev/SDLC v0.2 sub-features. **Not a halt** — Idea 3's review is itself a deferred research item.

### Finding #9 — Stage gate's "objective + AC presence" parser depends on artefact format

**Surface:** the gate check inspects `<project>/<stage>/<slug>.md` for objective + AC presence. The detection rules differ per methodology (ODD frontmatter vs ODD-prose section headings vs TDD's test-list shape vs BDD's scenario blocks vs adhoc's any-content).

**Resolution:** D-build.M6.5-adjacent — the gate's parser is per-methodology-pluggable. ODD templates carry `objective:` + `acceptance_criteria:` frontmatter; the parser yaml-parses the frontmatter. TDD/BDD/adhoc methodologies use methodology-specific detection (e.g. TDD: presence of test files in the stage's test directory; BDD: scenario blocks in `<stage>/<slug>.feature`). **Builder's call** to keep the parser narrow at v0.1.0 (ODD-only checking; TDD/BDD/adhoc gate on artefact existence + non-empty + a methodology-specific minimal sentinel). Mitigation: AC.OSS-M6.4's tests cover ODD-shape failure modes; opt-out methodologies' gate rules are documented in the plugin's README + verified by spot tests.

### Finding #10 — No surrounding-code ODD violations encountered

**Surface:** code surveyed during plan authoring: workspace-bootstrap discovery, dormancy adapter, scope-of-work runtime, objective-tracker runtime, loam_cli.cli, partition manifest. All have outcome-shape ACs in their proposal/seal artefacts. **No violations found.** Recorded for §14.

### Finding #11 — `loam amend` self-bootstrap during M6b extraction (rename-the-tool-while-using-it)

**Surface:** the build process itself uses `framework/tools/loam/`'s `loam amend` console-script for amendment seal (advancing SEAL_COMMIT sidecars, maintaining the manifest's `BASELINE` literal, validating the manifest's seal-diff `allowed_prefixes`, etc.). M6b's Item 7 disposition MOVES `loam amend` to `plugins/dev-sdlc/loam-amend/`. If M6b's own seal commit is to be sealed via `loam amend`, M6b must stage the migration so an INSTALLED `loam amend` console-script exists at the seal-commit time.

**Resolution:** D-build.M6.15 — shadow-then-flip migration shape (mirror M1g's pattern). M6b's commit ladder: (a) SHADOW commit (plugin-side copy exists, canonical-side intact) → (b) FLIP commit (entry-point points at plugin; canonical-side deleted) → (c) SEAL commit (sealed via plugin-side `loam amend`). The seal-commit-using-shadow approach was M1g's solution. **Halt-and-surface authority:** if at M6b build-time the shadow-then-flip mechanic encounters an unforeseen blocker (e.g. the plugin-side `loam amend` cannot resolve its own subcommand discovery while canonical-side is still present), halt and surface — owner ruling required on whether to (i) extract `loam amend` mid-M6b or (ii) defer Item 7's MOVE to a separate M6b' sub-amendment.

### Finding #12 — Programme-level dependency: M2 partition manifest's `dev_only` block content moves into the plugin

**Surface:** the M2 partition manifest's `dev_only:` list (lines 147-175) currently classifies dev-machinery artefacts that the M6 extraction directive moves INTO the plugin. Pre-M6, `dev_only` is the partition's "dev-discipline machinery, ships only in dev mode" class; post-M6b, most of that content lives at `plugins/dev-sdlc/**` and the partition's classification of `plugins/dev-sdlc/**` itself becomes the load-bearing classifier (per D-build.M6.14 — `plugins/dev-sdlc/**` reclassifies from `dev_and_public` to `dev_only`). The partition's `dev_only` block CONTRACTS but doesn't fully retire (per D-build.M6.13 — migration tools + synth tool + CLAUDE.dev.md + historical `docs/rebuild/**` remain dev_only).

**Resolution:** AC.OSS-M6.13 captures the partition reshape; D-build.M6.13 + D-build.M6.14 record the per-glob classification reshape. **Programme-level dependency** (per dispatch halt-trigger #5): M2's partition manifest is itself MUTATED by M6b. Master plan §6 sequencing rule already names M9.scrub as gated on M6 — M9 captures the FINAL public surface; without M6b's partition contraction, M9 cannot finalise.

### Finding #13 — Idea 13 two-modes design vs extraction directive: COMPATIBLE

**Surface:** Idea 13 (`docs/rebuild/FUTURE_IDEAS.md` lines 560-579) names what auto-loads in DEV MODE: "`pos-amend`, plan docs, manifest YAMLs, BASELINE conventions, SEAL_COMMITs, sealed-component conventions, dispatch-template, spec docs, component proposals + seal narratives, ODD methodology, dev CDCs from FUTURE_IDEAS.md." — and what stays loaded in NORMAL USE: "the runtime harness ... `VALUE_PROPOSITION.md` ... basic settings, plus end-user-facing docs/help."

**Resolution:** the dispatch directive (extract dev-related things into the dev/sdlc plugin) IS the operationalisation of Idea 13's two-modes design — DEV MODE's auto-load list IS the inventory the directive enumerates. M6b's extraction makes the plugin BECOME the package that delivers Idea 13's DEV MODE; `loam-mode`'s selector reads the plugin-relative `dev-mode-manifest.yaml` post-M6b (per AC.OSS-M6.12). **No contradiction; no halt.** Recorded for §14 method-decision register as the design-level confirmation.

### Finding #14 — Hands-off-lifecycle hooks self-identify as dev-mode-only via docstring

**Surface:** `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` line 18-19: "NORMAL USE workspaces no-op the gate at the mode-bit short circuit (D-A2.5 / programme D4 lock — A2 is ODD-discipline, DEV-MODE-only)." Same pattern in `tdd_guard.py`, `agent_guard.py` ("ALL DEV-MODE-only (the rules are pos-v2-dev-specific)"), `bash_guard.py`. The runtime hooks (`first-run.sh`, `pos_session_start.py`, `statusline.py`) do NOT carry this dev-mode-only self-identification — they're runtime first-run + statusline machinery active in NORMAL USE.

**Resolution:** the docstring split confirms the PARTITION line for Item 6 (D-Q.M6.7 Option A). The five gate hooks + their helpers MOVE into the plugin; the runtime hooks STAY. **No halt.** Recorded for §14 — the docstring-driven partition is itself a reverse-extraction signal that the existing components are honestly self-identifying their dev-discipline boundary.

---

## 12. Method-decision register (placeholder)

(See §14 for the post-build narratives + commit SHAs.)

---

## 13. Test breakdown (post-build)

**Nine new test files** (or 10 with M6.9), total ~600-900 LOC across all tests:

1. `plugins/dev-sdlc/tests/test_AC_OSS_M6_1_contribution_discovers_via_entry_point.py` — bootstrap host runs the plugin's contribution; asserts `host.dev_sdlc` is set.
2. `plugins/dev-sdlc/tests/test_AC_OSS_M6_2_new_project_scaffolds_odd_tree.py` — `api.start_project` creates the project tree + SQLite row.
3. `plugins/dev-sdlc/tests/test_AC_OSS_M6_3_opt_out_preserves_odd_mirror.py` — `methodology=tdd` writes mirror YAML.
4. `plugins/dev-sdlc/tests/test_AC_OSS_M6_4_stage_gate_enforces_objective_and_ac.py` — four gate failure modes + one pass mode.
5. `plugins/dev-sdlc/tests/test_AC_OSS_M6_5_scope_and_tracker_integration.py` — scope + tracker forest assertions + OTel span emission.
6. `plugins/dev-sdlc/tests/test_AC_OSS_M6_6_loam_project_subcommand_registered.py` — `loam project --help` + `loam project new`.
7. `framework/tools/loam/tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py` — `loam_cli`'s entry-point-group resolution path.
8. `plugins/dev-sdlc/tests/test_AC_OSS_M6_7_python_api_surface_stable.py` — import-stability + `inspect.signature` contract.
9. `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` — partition classifies all `plugins/dev-sdlc/` files as `dev_and_public`.
10. **(conditional D-Q.M6.4 ship)** `plugins/dev-sdlc/tests/test_AC_OSS_M6_9_start_project_skill_shipped.py` — skill file present + parses + persona's loader finds it.

Plus the standard seal-fence test:
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — admits `plugins/dev-sdlc/`-relative paths only.

**No tests in scope-of-work, objective-tracker, memory-system, primary-persona, workspace-bootstrap.** Their internal logic remains under existing test coverage.

### Cross-tree verification (HC#1 analogue — every public-API consumer that depends on M6's surface)

- The plugin imports from: `loam.scope_of_work.runtime`, `loam.objective_tracker.runtime`, `loam.workspace_bootstrap.spec` (`Phase`, `BaseContribution`, `ContributionMetadata`). All public exports verified at plan-authoring.
- `loam_cli.cli` exposes a new entry-point-group-resolution function (e.g. `_discover_subcommands`) consumed only by `loam_cli.cli.main` itself — no external consumers.
- Partition manifest YAML changes are textual; the `partition.py` classifier already handles arbitrary `audit_roots` entries (no code change needed in the classifier — verified at plan-authoring).

### Backwards-compat verification (HC#2 analogue — pre-existing tests post-M6)

- Existing scope-of-work tests pass byte-identically (no source change).
- Existing objective-tracker tests pass byte-identically (no source change).
- Existing workspace-bootstrap tests pass byte-identically (no source change).
- Existing `loam_cli` tests pass post-edit — the `amend` subcommand path remains intact; the new entry-point-discovery is additive (no `amend` regression).
- Existing partition-manifest tests pass post-YAML-edit — the YAML extension is additive; no existing classification changes.

### HC#4 byte-content sample status

NO RETIRE-AND-REBASELINE per §10 D-build.M6.6 + Finding #4.

### Dependents cleared to dispatch (post-M6)

- M7.docs-lane — parallel-safe with M6 per master plan §6 sequencing rule #4; both can run alongside.
- M8.license-governance — parallel-safe with M6.
- M9.scrub — gated on M6 (scrub captures the final public surface; M6 ships the last new component).
- M10.bus-factor — calendar-parallel; not gated on M6.
- M11.dry-run — gated on M9 (and therefore M6).
- M12.publish — gated on M11.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-Q.M6.1 — Plugin tree placement

(Populated at owner-ruling time. Recommendation per §10: `plugins/dev-sdlc/`.)

### D-Q.M6.2 — Objective-extraction skill at v0.1.0

(Populated at owner-ruling time. Recommendation per §10: defer entirely to v0.1.1.)

### D-Q.M6.3 — Per-project CLI verb naming

(Populated at owner-ruling time. Recommendation per §10: `loam project ...`.)

### D-Q.M6.4 — `/start-project` skill at v0.1.0

(Populated at owner-ruling time. Recommendation per §10: ship.)

### D-build.M6.5 — Subcommand-discovery mechanism

(Populated at build time. Recommendation per §10: entry-point group `loam.cli.subcommands`.)

### D-build.M6.6 — HC#4 retire-and-rebaseline

(Populated at build time. Recommendation per §10: NO.)

### D-build.M6.7 — Stage-gate parser scope at v0.1.0

(Populated at build time. Recommendation per Finding #9: ODD-frontmatter detection only at v0.1.0; TDD/BDD/adhoc gates check artefact-existence + minimal sentinel; per-methodology parser pluggability deferred to v0.2.)

### D-build.M6.8 — Per-project state primary-source-of-truth

(Populated at build time. Recommendation: SQLite at `<workspace>/.loam/dev-sdlc.sqlite`; per-project YAML at `<project>/.dev-sdlc.yaml` is a derived view.)

### D-build.M6.9 — Plugin-shipped skill discovery via reader-fall-through (conditional on D-Q.M6.4)

(Populated at build time + conditional. Recommendation: leverage Idea 26's reader-fall-through; verify at build time; halt + drop AC.OSS-M6.9 if additive `_resolve_corpus_path` change required.)

### Surface B owner-rulable items (added 2026-04-29 owner-directive expansion)

#### D-Q.M6.6 — Ship shape: single amendment vs sub-amendment series

(Populated at owner-ruling time. Recommendation per §10: sub-amendment series M6a → M6b → M6c.)

#### D-Q.M6.7 — Hands-off-lifecycle A1-A4 gates disposition

(Populated at owner-ruling time. Recommendation per §10: PARTITION — gates MOVE; runtime hooks STAY.)

#### D-Q.M6.8 — `loam amend` disposition

(Populated at owner-ruling time. Recommendation per §10: MOVE-WHOLE with shadow-then-flip migration mitigation per D-build.M6.15.)

#### D-Q.M6.9 — Methodology + convention docs disposition

(Populated at owner-ruling time. Recommendation per §10: MOVE the long-form ODD methodology + duration-estimation rubric + dev CDCs to `plugins/dev-sdlc/docs/`.)

### Surface B method-shape decisions (recorded for transparency)

#### D-build.M6.10 — `git mv` mechanic vs copy-and-delete

(Populated at M6b build time. Recommendation per §10: `git mv` for MOVE-class items; `git log --follow` verifies history.)

#### D-build.M6.11 — Convention-doc authoring scope at v0.1.0

(Populated at M6b build time. Recommendation per §10: concise codification — 100-300 LOC per convention; not exhaustive prose.)

#### D-build.M6.12 — Plugin-shipped hooks registration mechanism

(Populated at M6b build time. Recommendation per §10: `contribute(host)` writes a settings.json fragment; idempotent + reversible.)

#### D-build.M6.13 — Final shape of `dev_only` block post-extraction

(Populated at M6b build time. Recommendation per §10: `dev_only` retains migration tools + synth tool + CLAUDE.dev.md + historical `docs/rebuild/**`; contracts but doesn't fully retire.)

#### D-build.M6.14 — Plugin's own M2 partition classification

(Populated at M6b build time. Recommendation per §10: `plugins/dev-sdlc/**` reclassifies to `dev_only` post-M6b.)

#### D-build.M6.15 — Shadow-then-flip migration shape for `loam amend`

(Populated at M6b build time. Recommendation per §10: SHADOW commit + FLIP commit + SEAL commit; mirror M1g's pattern.)

#### D-build.M6.16 — Post-MOVE cross-reference update mechanic

(Populated at M6b build time. Recommendation per §10: automated grep+sed bundled with each MOVE commit.)

### Commit SHAs

- Plan-doc + manifest commit (Surface A original): `454bbd4` (2026-04-29).
- Plan-doc Surface B expansion commit: `<TBD>` (this dispatch — extraction-shape addition + M6a/M6b/M6c series declaration).
- M6a (Surface A baseline plugin):
  - Build feature commit: `<TBD>` (next dispatch).
  - Apply commit: `<TBD>` (next dispatch).
  - Seal commit: `<TBD>` (next dispatch).
- M6b (Surface B extraction migrations) — its own manifest authored at M6b dispatch time:
  - Manifest + plan-update commit: `<TBD>`.
  - Build feature commits (multiple — per inventory item): `<TBD>`.
  - Apply commit: `<TBD>`.
  - Seal commit: `<TBD>`.
- M6c (cleanups) — its own manifest authored at M6c dispatch time:
  - Manifest + plan-update commit: `<TBD>`.
  - Build feature commit(s): `<TBD>`.
  - Apply commit: `<TBD>`.
  - Seal commit: `<TBD>`.

---

## 15. Backwards-compat verification (post-build)

To be filled by builder post-build.

- All pre-existing tests pass post-amendment (touched-component pytest pass; full-repo skipped pre-seal per `feedback_amendment_dispatch_speedups`).
- Per-component seal-diff tests pass for all fenced components (3 or 4 per D-Q.M6.5).
- HC#4 invariant remains GREEN (no rebaseline).
- No new third-party deps (HC#3 analogue) — verify `uv.lock` diff or per-pyproject dependency comparison.
- New `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` seal-fence test passes its first run (admits only `plugins/dev-sdlc/`-relative paths).

---

## 16. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause (extended for Surface B expansion 2026-04-29):

1. **Findings #1–#14 in §11** above. None block dispatch; each maps to a §10 design decision or §9 halt condition. Recorded for builder awareness + §14 method-decision register.
2. **No audit/invariant conflict found.** Idea 3's enumerated capabilities (post-deferral) compose cleanly with sealed-component invariants. The plugin is NEW; no existing seal-diff fence is broken; the partition-manifest extension is additive.
3. **No methodology breach found.** Every AC is outcome-shape; method-shape is the builder's call. The plugin's stage-gate enforcement is itself ODD-shaped — methodology recursion is intentional (the plugin practices what it proposes).
4. **No surrounding-code ODD violations found.** Per Finding #10. Surveyed code areas (workspace-bootstrap, scope-of-work, objective-tracker, loam_cli, partition manifest) all carry outcome-shape ACs.
5. **Idea 3 enumeration vs v0.1.0 reasonable scope.** Per Finding R1: post-deferral capability set fits within ~5-7 concrete features matching pre-existing component scope. No halt.
6. **Plugin shape vs workspace-bootstrap discovery.** Per Finding R2: plugin's `Contribution` shape matches existing precedent. No halt.
7. **`plugins/` partition-manifest gap.** Per Finding #1: closed by AC.OSS-M6.8.
8. **`loam_cli` subcommand-discovery gap.** Per Finding #2: closed by D-build.M6.5 + AC.OSS-M6.6.
9. **Skill-loader plugin-relative-path support.** Per Finding #3 + §8 risk #7: verify at build time; D-Q.M6.4 deferral path catches the failure mode.
10. **`loam amend` self-bootstrap during M6b.** Per Finding #11 + §9 halt-trigger #11. Closed-by-design via D-build.M6.15 shadow-then-flip; halt at build time only if the shadow mechanic encounters an unforeseen blocker.
11. **M2 partition manifest mutation by M6b.** Per Finding #12 + §9 halt-trigger #14. Closed-by-design via D-build.M6.13 + D-build.M6.14; the `dev_only` block contracts but doesn't retire.
12. **Idea 13 two-modes vs extraction directive.** Per Finding #13. COMPATIBLE — extraction operationalises Idea 13.
13. **Hands-off-lifecycle dev-mode-vs-runtime split.** Per Finding #14. Confirmed by docstring inspection; PARTITION line is clean.

**Halt summary.** None. Plan is authorised to proceed pending owner sign-off on D-Q.M6.1..M6.9 + dispatcher review. Surface A (M6a) is buildable on owner approval of D-Q.M6.1..M6.5; Surface B (M6b/M6c) gates additionally on D-Q.M6.6..M6.9.

---

*End of plan.*
