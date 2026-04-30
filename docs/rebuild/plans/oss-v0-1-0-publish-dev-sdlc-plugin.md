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

**M6 ships the Dev/SDLC plugin at `plugins/dev-sdlc/` — a NEW component-shaped artefact at a NEW top-level tree, establishing the plugin-tree pattern v0.2+ plugins inherit.** The plugin composes against workspace-bootstrap's existing contribution-protocol (entry-point group `loam.bootstrap.contributions`) — zero bootstrap-side source change. It defaults new projects to ODD-shaped research/spec/plan/build/review/verify stages with structural gate enforcement; provides an opt-out (`--methodology=tdd|bdd|adhoc`) that preserves an internal ODD mirror; surfaces five operator verbs (`loam project new|status|advance|list|gate`) registered as subcommands of the unified `loam` CLI.

**Per master plan §5 M6 row predicted 90-180 min (midpoint 135) for the full new-component build cycle — this dispatch is the research + plan slice (predicted 20-40 min); next dispatch builds the plugin to seal.**

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

**Nine ACs in family AC.OSS-M6.\* + sealed-component fence AC.OSS-M6.S.** All ladder up to AC.OSS.6 (programme-level) → AC.PO.1 + AC.PO.2 (prime objective). See §4 for AC text + verification path; §6 for ladder-up table.

### Owner-gate items (numbered)

Four owner-gate items (per `feedback_summarize_and_surface_decisions`):

- **D-Q.M6.1** — Plugin tree placement: `plugins/dev-sdlc/` (RECOMMEND) vs `framework/dev-sdlc/`.
- **D-Q.M6.2** — Objective-extraction skill at v0.1.0: defer entirely (RECOMMEND) vs ship a skill stub vs ship complete.
- **D-Q.M6.3** — Per-project CLI verb naming: `loam project ...` (RECOMMEND) vs `loam dev ...` vs `loam new ...`.
- **D-Q.M6.4** — `/start-project` skill ship-at-v0.1.0: ship (RECOMMEND) vs defer.

Plus one method-shape decision the plan resolves but documents for transparency:

- **D-Q.M6.5** — `loam project` subcommand discovery mechanism: entry-point group `loam.cli.subcommands` (RECOMMEND; plan-doc §10 D-build.M6.5) vs hardcoded subcommand list patched via host registry vs separate `loam-project` console-script binary.

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

### AC.OSS-M6.8 — M2 partition manifest classifies `plugins/dev-sdlc/` as `dev_and_public`

`framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` extends:
  - `audit_roots:` adds `plugins/`.
  - `dev_and_public:` adds `- glob: "plugins/dev-sdlc/**"`.

The synthesis tool's classification check (post-M2 contract) classifies every file under `plugins/dev-sdlc/` as `dev_and_public`; synthesis includes the plugin in the public artefact.

**Verification:** a unit test invokes the partition manifest's `partition_complete(...)` against a synthetic workspace state including `plugins/dev-sdlc/` files; asserts (a) every file classifies, (b) every file lands in `dev_and_public`. Plus an integration test running `synth.py` against canonical HEAD; asserts the synthetic tree contains `plugins/dev-sdlc/`.

**Test:** `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` (new).

### AC.OSS-M6.9 — `/start-project` Claude skill discoverable + invocable (D-Q.M6.4 ship path)

If owner rules SHIP at D-Q.M6.4: `plugins/dev-sdlc/skills/start-project.md` exists with frontmatter (`description: "Start a new project under loam's Dev/SDLC plugin..."` + `name: start-project`) and a body that names the user-facing intent + the underlying `api.start_project` invocation. The skill is discoverable via the workspace's skill loader (per Idea 26's reader-fall-through composition — plugin-shipped skills resolve through `_resolve_corpus_path`).

**If owner rules DEFER at D-Q.M6.4:** AC.OSS-M6.9 is dropped; the AC count drops to 8.

**Verification:** a unit test asserts the skill file exists + parses frontmatter + the persona's skill-discovery code (per `_resolve_corpus_path`) finds it.

**Test:** `plugins/dev-sdlc/tests/test_AC_OSS_M6_9_start_project_skill_shipped.py` (new — conditional on D-Q.M6.4).

### AC.OSS-M6.S — Sealed-component fence

Three components (or four if D-Q.M6.1 lands `framework/dev-sdlc/`) in the M6 fence:

  - **`plugins/dev-sdlc/`** (NEW component) — carries the plugin source + tests + per-component `tests/SEAL_COMMIT` sidecar + per-component `tests/test_no_sealed_amendments.py` seal-test (authored at M6 alongside the source).
  - **`framework/tools/loam/`** — extends `loam_cli.cli.main` to discover `project` subcommand via the new entry-point group (one source-file edit + one new test).
  - **`framework/tools/pos-publish-framework-only/`** — extends the partition manifest YAML + minor classifier test update (one YAML edit + one new test).
  - **(possible 4th)** — if D-Q.M6.5 rules entry-point-group form for subcommand discovery (RECOMMEND), `framework/tools/loam/` source change is the only diff; if it rules host-registry form, `framework/workspace-bootstrap/` MAY enter the fence (additional `host.loam_cli_registry` attribute). Plan recommends entry-point-group form to keep workspace-bootstrap OUT of the fence.

Per-component seal-tests advance their `SEAL_COMMIT` sidecars at seal time. The seal-diff fence is enforced via `tests/test_no_sealed_amendments.py` in each component. **`plugins/dev-sdlc/`'s seal-test is authored AT M6** (NEW component — first seal). The pattern follows existing components (`framework/dormancy/tests/test_no_sealed_amendments.py` is the template).

**Verification:** seal-diff tests pass post-build for all fenced components. The new seal-test in `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` is authored to admit M6's diff (`plugins/dev-sdlc/`-relative paths) and reject anything outside the plugin's subtree.

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
10. **Wall-time exceeds projected estimate by >50%.** Per master plan §8 halt-trigger #8. Build slice predicted 90-180 min midpoint 135; halt at ~270 min if not converging. Surface current state; owner triages whether to continue, split, or pause.

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

### Commit SHAs

- Plan-doc + manifest commit: `<TBD>` (this dispatch).
- Build feature commit: `<TBD>` (next dispatch).
- Apply commit: `<TBD>` (next dispatch).
- Seal commit: `<TBD>` (next dispatch).

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

Per the dispatch's halt-and-surface clause:

1. **Findings #1–#10 in §11** above. None block dispatch; each maps to a §10 design decision or §9 halt condition. Recorded for builder awareness + §14 method-decision register.
2. **No audit/invariant conflict found.** Idea 3's enumerated capabilities (post-deferral) compose cleanly with sealed-component invariants. The plugin is NEW; no existing seal-diff fence is broken; the partition-manifest extension is additive.
3. **No methodology breach found.** Every AC is outcome-shape; method-shape is the builder's call. The plugin's stage-gate enforcement is itself ODD-shaped — methodology recursion is intentional (the plugin practices what it proposes).
4. **No surrounding-code ODD violations found.** Per Finding #10. Surveyed code areas (workspace-bootstrap, scope-of-work, objective-tracker, loam_cli, partition manifest) all carry outcome-shape ACs.
5. **Idea 3 enumeration vs v0.1.0 reasonable scope.** Per Finding R1: post-deferral capability set fits within ~5-7 concrete features matching pre-existing component scope. No halt.
6. **Plugin shape vs workspace-bootstrap discovery.** Per Finding R2: plugin's `Contribution` shape matches existing precedent. No halt.
7. **`plugins/` partition-manifest gap.** Per Finding #1: closed by AC.OSS-M6.8.
8. **`loam_cli` subcommand-discovery gap.** Per Finding #2: closed by D-build.M6.5 + AC.OSS-M6.6.
9. **Skill-loader plugin-relative-path support.** Per Finding #3 + §8 risk #7: verify at build time; D-Q.M6.4 deferral path catches the failure mode.

**Halt summary.** None. Plan is authorised to proceed pending owner sign-off on D-Q.M6.\* + dispatcher review.

---

*End of plan.*
