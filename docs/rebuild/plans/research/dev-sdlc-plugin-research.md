# Dev/SDLC Plugin — research findings

**Status:** research findings (inputs to the M6 plan-doc). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (master plan §5 M6 row, R2 ruling, AC.OSS.6).
**Plan-doc consumer:** `docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md`.

**Authority documents synthesised here:**
- Idea 3 — Initial plugin suite (must-have at launch — Dev/SDLC plugin):
  `docs/rebuild/FUTURE_IDEAS.md` lines 278-305.
- Idea 12 — Open-source launch of loam (R2: Dev/SDLC only at v1):
  `docs/rebuild/FUTURE_IDEAS.md` lines 510-557.
- Idea 6 — ODD as the default framing inside pos-v2 conversations:
  `docs/rebuild/FUTURE_IDEAS.md` lines 355-381.
- Idea 26 — Workspace-specific corpus overrides via reader fall-through:
  `docs/rebuild/FUTURE_IDEAS.md` lines 820-833.
- Idea 22 — Memory-doc skeleton template (third member of the template family):
  `docs/rebuild/FUTURE_IDEAS.md` lines 750-763.
- Idea 23 — Research dispatches pre-filter through scope-fence constraint:
  `docs/rebuild/FUTURE_IDEAS.md` lines 766-779.
- Master plan §5 M6 row + §6 sequencing rule #4 + §3 AC.OSS.6:
  `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- VALUE_PROPOSITION (prime objective hook):
  `docs/rebuild/VALUE_PROPOSITION.md`.
- workspace-bootstrap contribution / discovery contract:
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py`,
  `manifest.py`, `discovery.py`.
- Existing component shape reference:
  `framework/dormancy/`, `framework/objective-tracker/`,
  `framework/scope-of-work/`.
- M2 partition manifest:
  `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.

---

## 1. TLDR — three findings

1. **The plugin's v0.1.0 capability set is the *workflow stages* + *artefact authoring templates* + *stage gating*, NOT an objective-extraction skill.** Idea 3's enumerated capabilities list the stage workflow first and the existing-repo objective-extraction skill last with explicit "v0.1 or v0.1.1, builder's call" deferability per master plan §5 M6. The stage workflow is the pattern-demonstrating piece (it's why v0.1.0 ships a plugin at all per Idea 12 R2); the extraction skill is high-leverage but heavy enough that splitting buys timeline insurance.
2. **The plugin composes ON TOP of existing harness primitives — it doesn't introduce new ones.** Scope-of-work hosts the project lifecycle. Objective-tracker hosts the per-stage AC ladder. Memory-system carries decision history. Primary-persona translates user intent into stage-shaped work. Workspace-bootstrap discovers the plugin's contributions via the existing `loam.bootstrap.contributions` entry-point group + manifest opt-in. **Zero new framework primitives.** The plugin is the first proof that the harness's extension protocol works end-to-end without amending bootstrap-side surfaces.
3. **Plugin lives at `plugins/dev-sdlc/` (separate plugin tree).** Master plan D-Q.OSS.5's recommendation establishes the plugin-tree pattern at v0.1.0 — but verification against the M2 partition manifest shows `plugins/` is NOT yet in `audit_roots`. M6 must extend the partition manifest at the same time as the plugin lands. The alternative (`framework/dev-sdlc/`) requires no partition update but conflates "core harness" with "plugin extension" and forfeits the "first plugin establishes the pattern" lever.

---

## 2. What does the plugin DO at v0.1.0?

### Three concrete capabilities

**Capability A — ODD-shaped stage workflow for new projects.** When a user says "I want to start a new project" inside a loam workspace, the persona invokes the plugin's `start_project` flow. The flow runs five stages in order — research → spec → plan → build → review/verify — each backed by a concrete artefact path under the project's working tree, each gated on the prior stage's artefact existing + ODD-conformance check (objective + acceptance criteria present, no aspirational behaviour). Default discipline is ODD; opt-out preserves an internal ODD representation for the persona's review.

  - **Artefacts authored per stage** (concrete file paths the plugin creates):
    - `<project>/research/<slug>.md` — research findings.
    - `<project>/spec/<slug>.md` — spec / objectives + ACs.
    - `<project>/plan/<slug>.md` — work plan.
    - `<project>/build/` — code (the build itself).
    - `<project>/review/<slug>.md` — review/verify artefact.
  - **Stage gates** (each stage's "ready to advance" check):
    - Stage advance is allowed iff the prior stage's artefact exists and contains a named objective + at least one AC.
    - Gate failure surfaces as a structured halt-and-surface signal to the persona; no silent advance.
  - **Persona translation surface:** the user says "let's start work on X" — the persona translates that to `start_project(slug=X)`; subsequent natural-language requests at each stage map to the stage's artefact-authoring action without the user naming the stage.

**Capability B — Stage-bound scope-of-work + objective-tracker integration.** Each stage advance creates a scope-of-work scope (parent: the project; child: the stage) and a per-stage objective in the tracker (objective: "produce <stage> artefact for <project>"; ACs: "stage gate passes"). Scope events emit through observability-aggregator; the persona sees stage-level work in the same `list(filter)` surface that surfaces every other scope-shaped activity. **No new state surface** — the plugin is a SHAPE-LAYER over scope-of-work + objective-tracker.

**Capability C — `loam project` CLI subcommand surface.** Operator-callable verbs:
  - `loam project new <slug> [--methodology=odd|tdd|bdd|adhoc]` — bootstraps the project tree + first scope.
  - `loam project status [<slug>]` — current stage + next gate condition (or all projects if no slug).
  - `loam project advance [<slug>]` — runs the gate check + advances the stage if passing.
  - `loam project list` — all projects + their current stage.
  - All four delegate to the plugin's Python API; the persona's natural-language flow uses the same API path (no shell-out from the persona).

### What ODD-by-default looks like in practice

Per Idea 6 + Idea 3's "ODD is the default for new projects": when the user creates a project without naming a methodology, the plugin's `new` command writes a `<project>/.dev-sdlc.yaml` containing `methodology: odd`. The first artefact (research) is authored with the ODD frontmatter (objective + constraints + ACs); each subsequent stage gate verifies the objective ladder is intact. **Translation burden absorption (per VALUE_PROPOSITION):** the user never has to know the words "objective" or "acceptance criterion" — the plugin's templates carry the ODD frontmatter; the persona's prose translates between user natural-language and the structured fields.

The opt-out path (`--methodology=tdd|bdd|adhoc`) preserves an internal ODD representation per Idea 3 — a private `<project>/.dev-sdlc-odd-mirror.yaml` that the plugin maintains alongside the user's chosen surface. The persona's review-mode reads the mirror; the user sees only their chosen representation.

### What the plugin does NOT do at v0.1.0

- **Objective-extraction skill for existing repos** (Idea 3 sub-feature: reverse-ODD walking up from existing code to candidate objectives). Defer rationale: the slice/swarm/aggregate shape is itself a multi-month research-and-build cycle; bundling it into M6 doubles M6's scope and pushes the publish gate. Land at v0.1.1 or v0.2 as its own master-plan cycle. (Idea 3's text already flags it as "v0.1 or v0.1.1, builder's call" — the deferral is owner-authorised.)
- **Per-project Claude skill / hook installation.** The plugin doesn't install workspace-level skills or PreToolUse hooks at v0.1.0; that's a v0.2 candidate when a second plugin needs the pattern.
- **Multi-project orchestration.** The user can have N projects in a workspace (each its own `<project>/` directory); the plugin tracks them independently. **No cross-project workflows** (e.g. "merge project A's artefacts into project B's plan") at v0.1.0.
- **External issue-tracker integration** (Linear, Jira, GitHub Issues). v0.2 candidate per Idea 3's "additional plugin candidates" list.
- **Workflow-state-machine engine reimplementation.** v0.1.0 uses scope-of-work's existing FSM; the plugin shapes scopes, doesn't invent a new state machine.

### Target user

- **Primary:** the loam owner / first-pass adopters who clone `lukeivers/loam` post-v0.1.0 launch. Per Idea 12 research: the "developer audience" landing on HN / GitHub for "AI harness with methodology built in." The plugin is the proof that "methodology built in" is real, not aspirational.
- **Secondary:** non-technical users who arrive via Idea 12's "show, don't tell" path — the persona surfaces the plugin's stages naturally during conversation; the user experiences ODD-shaped work without knowing the methodology's name.

### First-click experience

A stranger who clones loam + runs `claude` lands in the workspace with the persona greeting them. After the persona's onboarding question (per amendment #35), the persona surfaces the workspace's primary capabilities. **One of those capabilities is "starting a new project."** The user types something like "I want to start a project to write a CLI for parsing Markdown." The persona invokes `loam project new markdown-parser` under the hood; the plugin scaffolds the project tree; the persona's next turn presents the research stage's prompt ("what's the objective, what would success look like, what constraints matter") — natural-language framed; ODD-shape underneath.

---

## 3. Plugin's relationship to existing harness primitives

| Primitive | Plugin's relationship | Direction (consume/expose) |
|---|---|---|
| **scope-of-work** | Plugin creates scopes per project + per stage. Scope events fire on stage advance. | CONSUMES the scope API (`scope_runtime.create_scope`, `scope.advance`, `scope_runtime.subscribe_all`). |
| **objective-tracker** | Plugin registers a per-stage objective (objective text + ACs derived from the stage gate). Tracker's forest-of-trees holds the project as the root; stages as children. | CONSUMES the tracker API (`runtime.register_objective`, `runtime.record_ac`). |
| **memory-system** | Plugin's per-stage decisions emit episode events into memory; future stages query memory for prior decisions. | CONSUMES `mcp__memory-graphiti__add_episode` + `mcp__memory-graphiti__search`. |
| **primary-persona** | Persona invokes the plugin's Python API; plugin returns structured stage data; persona translates back to natural-language prose. | CONSUMED BY persona (plugin is a tool the persona reaches for). |
| **workspace-bootstrap** | Plugin ships a `Contribution` class registered under `loam.bootstrap.contributions` entry-point group; bootstrap's existing `discovery.py` resolves it; manifest opt-in via `bootstrap.yaml`'s contributions list. | CONSUMES bootstrap's contribution protocol (no bootstrap-side change). |
| **observability-aggregator** | Plugin emits OTel spans on stage advance + gate check pass/fail. | CONSUMES `tracer.start_as_current_span`. |
| **orchestrator** | Plugin's CLI / API runs inside the orchestrator's lifecycle; long-running scaffolding work (e.g. external git clone for opt-out imported repos) goes through scope-of-work + can be paused via dormancy. | CONSUMES orchestrator's pause/resume contract indirectly via scope-of-work. |
| **safety-layer** | Plugin's CLI is a console-script entry; user-issued kill goes through `loam-kill scope <id>` (M3-wired). No new safety-gate. | CONSUMES the existing safety-layer surface (passive — no plugin-specific gate). |
| **cost-governance** | Plugin operations cost-instrument like every other scope; no new cost-class. | CONSUMES cost-governance passively. |
| **reversibility-primitive** | Project bootstrap (file creation under `<project>/`) registers a reversibility checkpoint per scope-of-work's existing pattern; `loam project reset <slug>` is NOT in v0.1.0 scope (use `loam-rollback scope <id>`). | CONSUMES reversibility passively. |
| **self-correction** | Stage-gate failures fire self-correction signals that surface in the persona's correction-handling path. | CONSUMES self-correction passively. |

**Net new framework primitives required:** **zero.** The plugin is the first end-to-end proof of the contribution-based extension protocol — it lights up surfaces already authored.

---

## 4. Structural shape — where the plugin lives

### Directory layout (plugins/dev-sdlc/)

```
plugins/
  dev-sdlc/
    pyproject.toml                  # name = "loam-plugin-dev-sdlc"
    README.md
    src/
      loam/
        plugins/
          dev_sdlc/
            __init__.py             # exports public API (start_project, advance, status, list_projects)
            api.py                  # Python API (called by persona + CLI)
            cli.py                  # `loam project ...` subcommand argparse
            contribution.py         # DevSdlcContribution (workspace-bootstrap entry-point target)
            stages.py               # five-stage shape + per-stage gate logic
            templates/              # stage artefact templates (research/spec/plan/build/review)
              odd-research.md
              odd-spec.md
              odd-plan.md
              odd-review.md
              tdd-research.md       # opt-out variants
              tdd-spec.md
              ...
            store.py                # SQLite store for per-project metadata (stage, methodology, scope/objective IDs)
            errors.py
            observability.py        # OTel emit helpers (loam.dev_sdlc.* namespace)
    tests/
      SEAL_COMMIT
      seals/
      test_AC_OSS_M6_*.py           # one test file per AC
      test_no_sealed_amendments.py  # standard sealed-component fence
```

### Why `plugins/dev-sdlc/` not `framework/dev-sdlc/`

Per master plan D-Q.OSS.5 recommendation: the plugin-tree pattern is the load-bearing structural lever for v0.2+ plugins. The first plugin that establishes the pattern carries the cost; every subsequent plugin gets a cheaper path. Putting Dev/SDLC under `framework/` defers the pattern-establishment cost to plugin #2 — but because R2 caps v1 at one plugin, plugin #2 doesn't land in v0.1.0; the cost compounds.

**Counter-argument considered + rejected:** every existing component lives at `framework/<comp>/`; introducing a new top-level tree increases conceptual surface area. **Rebuttal:** plugins ARE conceptually distinct from framework components — they extend rather than compose; they're optional rather than core; the directory name makes the distinction visible. Same shape as `framework/tools/` vs `framework/<sealed-components>/` — the segregation is semantically right.

### Workspace-bootstrap integration

The plugin's `pyproject.toml` ships:

```toml
[project.entry-points."loam.bootstrap.contributions"]
dev_sdlc = "loam.plugins.dev_sdlc.contribution:DevSdlcContribution"

[project.scripts]
# (no console_scripts here — `loam project` is a SUBCOMMAND of the
# unified `loam` CLI per loam-rename-decisions.md Tier-1 #6; the
# subcommand is registered via loam_cli's plugin-resolution path,
# not as its own [project.scripts].)
```

The workspace's `bootstrap.yaml` opts in by listing `dev_sdlc` in `contributions`. **Availability vs enablement** (per `discovery.py` line 7-9): an installed-but-not-listed plugin is inert. Default workspaces created via `pos-new-workspace` enumerate every available plugin in their generated `bootstrap.yaml`; users who don't want Dev/SDLC remove the line.

The `Contribution` class:
  - `metadata.name = "dev_sdlc"`.
  - `metadata.phase = Phase.after_orchestrator_ready` — plugin is non-load-bearing for orchestrator startup; it registers with the persona's command-surface after orchestrator is ready.
  - `metadata.after = ("primary_persona", "objective_tracker", "scope_of_work")` — the plugin reads these surfaces at construction.
  - `contribute(host)` body: constructs the plugin's `DevSdlcRuntime` from `host.scope_runtime` + `host.objective_tracker` + `host.workspace_root`; registers it on `host.dev_sdlc`; registers the `loam project` subcommand with `loam_cli`'s subcommand registry (via a host attribute or a lightweight pubsub).

### MCP / hook / skill surface

- **MCP:** none new at v0.1.0. The plugin's API is Python; the persona invokes it via tool calls that wrap the Python entry. (A future MCP server exposing project state is a v0.2 candidate when a remote-access shape becomes valuable.)
- **Hooks:** none new at v0.1.0. The plugin doesn't install PreToolUse / Stop / SessionStart hooks. (A v0.2 candidate: a SessionStart hook that surfaces "in-progress projects you might want to advance" — but that surface is the persona's job today.)
- **Skills:** the plugin SHIPS a Claude skill at `plugins/dev-sdlc/skills/start-project.md` that documents the user-facing intent ("start a new project"). The skill loads automatically when the user types `/start-project` or when the persona detects matching intent. (Per Idea 6 — the skill is the user-facing surface of the methodology, not the methodology itself.) **Optional at v0.1.0** — the plugin works without the skill; the skill is a convenience layer. v0.1.0 ships the skill (low marginal cost; high leverage for first-click experience).

### Per-project state location

`<project>/.dev-sdlc.yaml` carries the project metadata (slug, methodology, current stage, scope_id, objective_id). **Workspace-local** (per the per-project subdirectory pattern; not host-global). `loam project list` reads `<workspace>/projects/*/.dev-sdlc.yaml` if a project root convention is followed, OR the plugin's SQLite store at `<workspace>/.loam/dev-sdlc.sqlite` if the project tree is non-conventional. **Recommendation:** ship the SQLite store as the canonical source of truth; the per-project YAML is informational/auditable.

---

## 5. Owner-gate items the methodology cannot rule

The methodology + dispatch rule the plugin's existence + most of its shape. Four items remain genuinely owner-rulable:

1. **D-Q.M6.1 — Plugin tree placement.** `plugins/dev-sdlc/` (recommendation per master plan D-Q.OSS.5) vs `framework/dev-sdlc/` (no partition manifest update needed). Surfaced in plan-doc.
2. **D-Q.M6.2 — Objective-extraction skill scope at v0.1.0.** Defer entirely (recommendation) vs ship a stub (skill scaffold without the slice/swarm engine) vs ship complete (~3-5x M6's wall-clock; pushes publish gate). Surfaced in plan-doc.
3. **D-Q.M6.3 — Per-project CLI verb naming.** `loam project ...` (recommendation; matches `loam amend ...` precedent) vs `loam dev ...` (closer to the plugin's name `dev-sdlc`) vs `loam new ...` (verb-first). Surfaced in plan-doc.
4. **D-Q.M6.4 — Skill ship-at-v0.1.0 vs defer.** Ship the `/start-project` skill (recommendation; low cost, high first-click leverage) vs defer to v0.1.1 (smaller M6 fence). Surfaced in plan-doc.

Other items the dispatch suggested might need owner ruling are actually methodology-resolvable:

- Plugin discovery mechanism: ALREADY DECIDED — workspace-bootstrap's contribution entry-point group (`loam.bootstrap.contributions`). No new mechanism.
- Public API surface naming: methodology-resolvable from existing component patterns (`<comp>.runtime`, `<comp>.api`, etc.).
- Opt-out shape: ALREADY DECIDED by Idea 3's text — `--methodology=tdd|bdd|adhoc` flag + internal ODD mirror. Mechanical authoring, not owner ruling.

---

## 6. AC ladder-up to AC.OSS.6

Master plan AC.OSS.6:
> Per R2: the Dev/SDLC plugin (Idea 3) ships in v0.1.0 as the first plugin. It composes against workspace-bootstrap's extension protocol; defaults new projects to ODD-shaped research/spec/plan/build/review/verify; provides an opt-out for users who prefer TDD/BDD/ad-hoc.

**M6 ACs (per plan-doc) ladder up:**

- AC.OSS-M6.1 — plugin discovers via `loam.bootstrap.contributions` entry-point + manifest opt-in (composition test). Ladders to AC.OSS.6 "composes against workspace-bootstrap's extension protocol."
- AC.OSS-M6.2 — `loam project new` scaffolds a project tree with ODD-shaped artefact templates by default. Ladders to AC.OSS.6 "defaults new projects to ODD-shaped..."
- AC.OSS-M6.3 — `--methodology=tdd|bdd|adhoc` opt-out preserves an internal ODD mirror. Ladders to AC.OSS.6 "provides an opt-out for users who prefer TDD/BDD/ad-hoc."
- AC.OSS-M6.4 — stage gate enforces objective + AC presence before advance. Ladders to AC.OSS.6 (implicit — methodology requires structural enforcement).
- AC.OSS-M6.5 — plugin's per-stage scopes + objectives integrate with scope-of-work + objective-tracker (reuse, not reinvent). Ladders to AC.PO.2 (toolkit-primitive; the plugin ADDS to the toolkit by composing the existing primitives into a new shape).
- AC.OSS-M6.6 — `loam project ...` CLI subcommand registered via the unified `loam` CLI. Ladders to AC.PO.1 (translation-burden — the persona has a callable verb to invoke).
- AC.OSS-M6.7 — persona-invocable Python API surface (`start_project`, `advance`, `status`, `list_projects`). Ladders to AC.PO.1.
- AC.OSS-M6.8 — partition manifest classifies `plugins/dev-sdlc/` as `dev_and_public` so the plugin ships at synthesis. Ladders to AC.OSS.3 (no dev-discipline machinery in public — inverse: the plugin SHOULD ship publicly).
- AC.OSS-M6.S — sealed-component fence covers the new `plugins/dev-sdlc/` component + `framework/tools/loam/` (registers the subcommand) + `framework/tools/pos-publish-framework-only/` (partition manifest update).

---

## 7. Halt-and-surface findings encountered during research

### Finding R1 — Idea 3's enumerated capabilities do NOT exceed v0.1.0 reasonable scope (after deferral)

Idea 3 lists multiple capability classes:
  - SDLC stage workflow (THIS IS the must-ship piece).
  - Workflow engine + stage gates (covered by stages.py — small surface).
  - Artefact registry (covered by store.py — SQLite, ~150-200 LOC).
  - Product lifecycle (project-level; covered by per-project metadata).
  - Roadmap tooling (DEFERRED — v0.2 candidate).
  - Task orchestration (DEFERRED — composes with scope-of-work, not duplicating).
  - Contradiction detection (DEFERRED — heavyweight LLM-as-verifier; v0.2 candidate).
  - Objective-extraction skill for existing repos (DEFERRED to v0.1.1 per master plan §5 M6).

Post-deferral: ~5-7 concrete capabilities (workflow + stages + artefact templates + persona API + CLI + scope/tracker integration + opt-out mirror). Surface size matches pre-existing components (cost-governance, self-correction, reversibility-primitive — all 800-1500 LOC source). **Within reasonable v0.1.0 scope.** No halt.

### Finding R2 — Plugin shape composes cleanly with workspace-bootstrap's discovery contract

Verified at research time (`discovery.py` lines 30, 49-73): entry-point group is `loam.bootstrap.contributions`; resolution accepts entry-point form (bare-string in manifest) OR module/path forms. The plugin's `Contribution` class has identical shape to existing adapters (`metadata: ContributionMetadata`, `contribute(host)`). **No bootstrap-side change required.** No halt.

### Finding R3 — `plugins/` is NOT in M2 partition manifest's `audit_roots`

Verified at research time: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` `audit_roots` lists `framework/`, `docs/`, `CLAUDE.md`, `CLAUDE.dev.md`, `README.md`, `LICENSE`, etc. — but NOT `plugins/`. If the plugin lands at `plugins/dev-sdlc/`, M6 must extend the partition manifest in the same amendment. The extension is small (1 line in `audit_roots` + 1 glob entry in `dev_and_public`) but it's structurally inside M6's fence (touches `framework/tools/pos-publish-framework-only/`). **NOT a halt** — it's a known scope item that the plan-doc's manifest must admit. Surfaced as plan §11 finding.

### Finding R4 — `loam project` subcommand registration mechanism is NOT yet specified

The unified `loam` CLI (per M1g) lives at `framework/tools/loam/src/loam_cli/cli.py` and currently exposes the `amend` subcommand. Adding `project` as a sibling subcommand requires either:
  - (a) `loam_cli.cli.main` discovers subcommands via an entry-point group (e.g. `loam.cli.subcommands`) — symmetric to bootstrap's contribution discovery.
  - (b) `loam_cli.cli.main` hardcodes its subcommand list; the plugin patches it via a workspace-bootstrap-time registration on `host.loam_cli_registry` (or similar host attribute).
  - (c) The plugin ships its own console-script `loam-project` (different binary; no `loam project` form).

**Methodology-rulable** between (a)/(b)/(c): per Idea 1's Claude-leverage lens, the entry-point group (a) is symmetric with bootstrap's existing pattern + zero new state. **Recommend (a).** Surfaced as a plan-doc decision (D-build.M6.X — entry-point-group form for subcommand discovery).

### Finding R5 — Skills tree location is NOT yet established in the framework

There's no precedent for `skills/` directory at any framework level today. Master plan §3 AC.OSS.3 lists what's excluded from public synthesis but doesn't address where skills LIVE. **Recommendation:** plugin ships its skills under `plugins/dev-sdlc/skills/` (plugin-relative); the persona's skill loader (post-#73 corpus-inlining hook) reads from a discoverable manifest the plugin contributes. **Owner-rulable** if the plan-doc author thinks it's load-bearing — but per CDC research-recommendation-fence-filter (Idea 23), the recommendation has to fit the M6 scope-fence; if it crosses into corpus-inlining territory, defer to v0.1.1. **For v0.1.0, the skill is OPTIONAL** (D-Q.M6.4); shipping under `plugins/dev-sdlc/skills/` is the simplest path that doesn't widen fence.

### Finding R6 — No ODD §2.5 violations encountered in surrounding code

Surrounding code surveyed during research (workspace-bootstrap discovery, dormancy adapter, scope-of-work runtime). All have outcome-shape ACs in their proposal/seal artefacts. No violations to surface. No halt.

### Finding R7 — Idea 3's premise IS consistent with current corpus state

Verified: the SDLC-stage-workflow shape is internally consistent with how pos-v2 itself is built (the ODD methodology IS the dev/SDLC discipline already practiced). Idea 6 reinforces "ODD as default framing." Idea 12 R2 locks Dev/SDLC as the v1 plugin. No premise inconsistency. No halt.

---

## 8. Cross-references (for plan-doc author)

- Master plan §5 M6 row: predicted 90-180 min midpoint 135 (full 5-gate cycle). Research+plan slice (this dispatch) is the FIRST 20-40 min of that.
- Master plan §11 (spec-objective placement): AC.OSS.6 → AC.PO.1 + AC.PO.2 (translation-burden + toolkit-primitive). Plan-doc §2 mirrors this.
- Master plan §6 sequencing rule #4: M6 is parallel-safe with M7 (docs lane); serial with other amendment builds.
- D-Q.OSS.5 (master plan §13): plugin tree placement recommendation.

---

*End of research findings.*
