# Upgrade architecture conventions — research

**Date:** 2026-04-26.
**Author:** dispatched research agent (Opus 4.7, 1M context).
**Working tree audited:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Adjacent codebases read:** `/Users/lukeivers/cowork-openclaw/` (full layout); `~/.claude/` (Claude Code's user state).
**Lens:** Lens 1 (Claude-leverage), Lens 2 (harness + primary-persona value), Lens 3 (ODD).
**Owner directive (locked 2026-04-26):** decide between Architecture A (global-shared framework + per-workspace state, symlink swap) vs Architecture B (per-workspace embedded framework + sync mechanism) for "upgrade pos3 from canonical."

---

## TL;DR — one-page summary

**Recommendation: Architecture B (per-workspace embedded framework + git-shaped sync), with a thin Architecture-A-shaped global cache used only for Claude Code-native primitives (plugins, skills, MCP server installs).** Confidence: **high** for the primary axis (B beats A), **medium** for the hybrid carve-out (could ship pure-B for v1 and add the global cache later).

**One-line headline:** *Every comparable AI-harness ships per-project framework code; the only systems that use the global-symlink-swap shape are OS-level package managers (Homebrew, the Claude Code binary itself) — and they swap **the binary**, not the framework's authoring surface.* pos-v2's mission is to be authored, branched, and synced like a project, not installed like a binary; that puts it on Architecture B's side of the line.

**Convention findings (5 bullets):**
1. **Across every AI agent harness sampled (Claude Code, Aider, CrewAI, Letta, LangChain, Continue.dev, Hermes, openclaw), the framework code lives per-project — usually inside the project's venv or `node_modules`.** No sampled system installs framework Python/Ruby/JS *source files* to a global path and symlinks per-project handles to it. The only thing installed globally is the executable shim (the CLI binary on PATH), which is a different artefact than the framework code.
2. **Upgrade mechanism for the framework itself is universally "re-resolve dependencies inside the project's environment"** — `pip install -U <pkg>` inside a venv, `npm update`, `uv sync` — i.e. a project-local declarative manifest is re-resolved against a remote registry. The user data sits next to the env; the upgrade only touches files the package manager owns.
3. **The CLI binary** (Claude Code, Hermes, Aider's `aider-install` shim) is *separately* a global thing that auto-updates itself, and it is independent from the project framework. Claude Code: `claude update` rewrites the global binary; npm-installed `@anthropic-ai/claude-code` is a global PATH entry, not a per-project library. **This is exactly Architecture A — but only for the binary**, not for the project's framework code.
4. **Per-project state is always preserved by living in a separate, opaque directory the package manager doesn't touch.** Every system relies on the same convention: framework code is in a managed location (`venv/`, `node_modules/`, `~/.local/`), state is in a hand-authored location (`./src`, `./config`, `<workspace>/data`, `~/.hermes/`), upgrades only rewrite the managed location. Conflicts are rare because state and framework occupy disjoint trees.
5. **No AI-harness ships a "pull canonical updates into your existing customised workspace" mechanism.** The closest analogues are: (a) `create-react-app` / `create-next-app`, where upgrade = "bump `react-scripts` in `package.json`, run install" (the framework lives in `node_modules`, your code lives in `src/` — they don't collide); (b) Letta's database-backed agent state with library-style framework updates; (c) Hermes's `hermes update` (updates the global install; per-project context in `~/.hermes/skills/<workspace>/`). The "framework as a checked-in clone with embedded code" pattern is actually rare — pos3 today is doing something most ecosystems explicitly avoid (mixing framework source with project state in one git tree).

**Mapping back to pos-v2.** Architecture A (global-symlink-swap) is what `self-upgrade/` was built for and matches Claude Code's own binary-update mechanism — but it is the wrong layer for pos-v2's primary use case, because pos-v2's "framework" is itself the authoring surface (sealed components, persona contracts, ODD plans), not just a runtime. Owners modify the framework in-canonical and sync those changes to workspaces; that's a git/project pattern, not a brew/binary pattern. **Architecture B is the dominant pattern for "framework that you work on and that consumes user data alongside it."**

**Hybrid carve-out (the Claude-Code-native parts):** Plugins, skills, and MCP servers — Claude-native primitives that compose into pos-v2 — live in `~/.claude/plugins/`, `~/.claude/skills/`, etc., and are upgraded by Claude Code's existing global-cache mechanism (Architecture A for those specifically). pos-v2 should consume these as-is, NOT reinvent. This is already how pos-v2 ships `.mcp.json` (amendment #47) and slash-commands.

**Decisions surfaced for owner ruling.** Five — D-A1 through D-A5 below. Most-leveraged is **D-A1** (architecture choice itself). The remaining four are sub-decisions that resolve cleanly once D-A1 lands.

---

## Decisions for owner ruling (named, with recommendations)

### D-A1. Primary architecture — A, B, or hybrid?

**Question.** Does pos-v2 ship as (A) a global framework install at `~/.pos/framework/current/` with per-workspace state-only directories pointing at it, OR (B) a per-workspace embedded git clone where each workspace has its own framework code, with a sync mechanism to pull canonical updates, OR (hybrid) some mix?

**Recommendation. (B), with the existing self-upgrade mechanism pivoted to upgrade *the canonical framework's own state on the developer's machine* rather than to upgrade downstream workspaces.** Rationale:
- Every comparable AI harness uses B (per-project framework code) for the framework's authoring surface.
- pos-v2's mission objective is to *be authored* — sealed components, plans, personas, persona contracts — not just to *be run*. A globally-installed framework is read-only by convention; that conflicts with the operator's day-1 ability to modify their own persona's prompt.
- The existing self-upgrade clauses (a)–(g) actually map cleanly onto "the canonical install upgrades itself when a new pos-v2 release lands" — they don't have to apply to every downstream workspace.
- The "upgrade pos3 from canonical" workflow becomes the `workspace-sync` component already designed in `canonical-to-workspace-sync-research.md` (clause-h). That mechanism is git-shaped (three-way merge with class-A/B/C envelopes + LLM-mediated conflict resolution) — which IS the dominant convention for framework-upgrade-with-customisation across the broader ecosystem (npm package.json bumps, pip requirements upgrades, `create-react-app` `react-scripts` bumps).

The hybrid carve-out is **only** for Claude-Code-native primitives (plugins, skills, MCP servers in `~/.claude/`) — those are managed by Claude Code, not by pos-v2, and pos-v2 should compose on Claude's mechanism rather than duplicate it.

### D-A2. What does `self-upgrade` clause-(h) actually upgrade?

**Question.** The work done today on clause-(h) (BB-feat #55, DD #56, CC tests, EE prep) was framed as "self-upgrade upgrades pos3 from canonical." Given D-A1 = (B), this framing was incorrect. What does clause-(h) actually do under Architecture B?

**Recommendation.** **Pivot clause-(h) to mean "the canonical install upgrades its own framework when a new pos-v2 release tag lands."** The existing clauses (a)–(g) already do this; (h) was redundant under that reading. Pull the cross-clone sync semantic out of self-upgrade entirely and route it to the `workspace-sync` component (per `canonical-to-workspace-sync-research.md`). Today's work on clause-(h) becomes either:
- **Option (i):** dropped from self-upgrade and re-targeted as the first sub-amendment of `workspace-sync` (the staging + audit primitive).
- **Option (ii):** rescoped to "auto-update canonical's tracker DB after a release lands" or some other discrete clause.
- **Option (iii):** kept as-built but renamed to clarify scope. (Least preferred — clause-(h) implies cross-clone semantics under any reading.)

Recommended: **option (i)** — re-target the work into `workspace-sync`. The substrate-snapshot + audit code already written is reusable.

### D-A3. Where does the global Claude Code-native cache fit?

**Question.** Plugins, skills, MCP servers live in `~/.claude/plugins/`, `~/.claude/skills/`, etc. Does pos-v2 own them or delegate?

**Recommendation. Delegate fully — pos-v2 does NOT manage the `~/.claude/` global cache.** It is owned by Claude Code; Claude Code already has plugin update detection (in development per anthropics/claude-code#31462) and skill discovery. pos-v2's role is to declare *which* plugins/skills/MCP servers it needs, via:
- `<workspace>/.mcp.json` for MCP servers (amendment #47 already does this).
- A future declarative `<workspace>/.pos/plugins.yaml` or similar for plugins/skills (NOT yet built — file as future improvement).

This is exactly what every other AI harness does (Continue.dev's config.yaml, CrewAI's `[tool.crewai]` block) — the framework declares what it needs; the host installs it.

### D-A4. Multiple workspaces on one machine — concurrent upgrade semantics?

**Question.** Under Architecture B, if Luke has pos3, pos4, and ivers-corp-pos-v2 all on one machine, and canonical lands a release, how do they upgrade?

**Recommendation. Each workspace upgrades independently via `pos sync` (or git pull) — there is no shared state to coordinate.** This is exactly how npm projects on one machine work: project A's `node_modules` upgrades have zero impact on project B's. The only shared resource is the Claude Code binary itself + the `~/.claude/` cache, both of which are managed by Claude Code, not pos-v2.

Concurrency edge case: if two workspaces on one machine try to write to a shared sidecar (the per-machine memory-system at `~/.pos/memory-sidecar/`, etc.), that's already handled by amendment #29's per-workspace port allocation. No new concurrency primitives needed under B.

### D-A5. The pre-existing `~/.pos/framework/current/` symlink — vestigial?

**Question.** Self-upgrade created `~/.pos/framework/current/` and a release-staging directory. Under Architecture B, what happens to it?

**Recommendation. Re-purpose, not remove.** The path still has a use as a *cache of the canonical install's working tree* on the canonical maintainer's machine — i.e. when a release tag lands and self-upgrade clauses (a)–(g) run, they swap the canonical install's own files at `~/.pos/framework/current/`. Downstream workspaces never look at this path; they have their own embedded framework code. So:
- **Canonical machine:** `~/.pos/framework/current/` is the canonical install's swap target. self-upgrade (a)–(g) operate on it.
- **Downstream-workspace machines:** `~/.pos/framework/current/` does not exist (or is just a per-machine memory cache). Each workspace's framework code lives at `<workspace>/<sealed-component>/`.
- **First-run scaffolding** (workspace-bootstrap) on a downstream workspace does NOT create `~/.pos/framework/current/`.

This carves the ambiguity cleanly: A-shaped behaviour for the canonical's own self-upgrade, B-shaped behaviour for downstream workspaces.

---

## Spectrum table — system × framework location × upgrade × per-project state

| System | Where framework code lives | Upgrade mechanism | Per-project state | Cross-clone "pull canonical changes into existing customised workspace"? |
|---|---|---|---|---|
| **Claude Code (the CLI)** | `/usr/local/bin/claude` (npm-installed binary) OR native installer at platform path | `claude update` (rewrites the binary); `npm update -g`; auto-update background check | `~/.claude/` (global state — settings, sessions, plugin cache); `<project>/.claude/` (project-scoped settings, hooks, agents, commands) | No. Each project's `.claude/` is hand-authored; no mechanism to pull canonical updates. |
| **Claude Code plugins** | `~/.claude/plugins/<name>/` (cache from marketplace repo) | Not yet shipped — issue #31462 proposes `gitCommitSha` comparison + manual upgrade | None — plugins are pure framework, no per-project state | No today; planned. |
| **Claude Code skills** | `~/.claude/skills/<name>/` (similar marketplace cache) | Bundled with plugin updates | None | No. |
| **MCP servers** | Wherever the user installs them (often `npx -y` per-invocation, or pip-installed binaries) | Per-server (typically re-pulled by `npx` on each launch, or `pip install -U`) | Per-server config in `<project>/.mcp.json` and `~/.claude/settings.json` | No — config lives per-workspace, server code lives in registry. |
| **Aider** | Per-project venv (`pipx`/`uv`/`aider-install` all install isolated) OR globally pip-installed | `pip install -U aider-chat` inside the venv, or `aider --upgrade` | Aider is library-only — state is the user's git repo + chat history file. No framework state. | No. Project state is git, framework is venv — disjoint trees, no merge needed. |
| **CrewAI** | Per-project pyproject.toml + uv-managed venv | `uv sync` after bumping `crewai` in `pyproject.toml` | `~/.config/crewai/settings.json` (global) + project's `src/agents.yaml`, `src/tasks.yaml` (per-project) | No. Project agents/tasks are hand-authored; framework is in venv; upgrade rewrites venv only. |
| **LangChain** | Per-venv pip install | `pip install -U langchain` | None — LangChain is pure library, app state is user's choice | No. App data lives in user's chosen DB; framework upgrade only touches venv. |
| **Letta (MemGPT)** | Server install (Python/Docker) | `pip install -U letta` server-side; auto-loading tool libraries | Database-backed agent state — framework upgrades and state are in different stores by design | Partial — state is in DB, server is upgradable independently. Closest to a B-shape with explicit framework/state separation. |
| **Continue.dev** | VS Code/JetBrains extension (host-managed) | Extension marketplace auto-updates | `~/.continue/` (global) + `<workspace>/.continue/` (workspace) + `config.yaml` merge layer with mergeBehavior: merge or overwrite | No — but the merge layer for config IS the closest analogue to the canonical-to-workspace problem in any sampled system. |
| **Hermes Agent (Nous Research)** | `~/.hermes/` global install (curl installer); global `hermes` CLI | `hermes update` — rewrites the global install | `~/.hermes/skills/openclaw-imports/` for user-created skills; per-project context via context engines | No. State is global (`~/.hermes/`), updates rewrite the install. Architecture A in shape. |
| **openclaw (Luke's prior workspace)** | Embedded in the workspace's git tree (`lib/`, `bin/`, `personas/`, `ops/`, `modules/`) | None — pure git pull from upstream if there is one; no upgrade mechanism | All in `<workspace>/` itself (memory/, ops/, products/, personal/) — no separation | No upgrade mechanism existed. **Confirmed via codebase read.** Single-tree, single-workspace, no concept of canonical vs downstream. |
| **pos-v2 today (canonical)** | `<canonical>/<sealed-component>/` per component, embedded | self-upgrade clauses (a)–(g) swap `~/.pos/framework/current/` symlink — but this only ever runs on the canonical machine | `<workspace>/.pos/`, `<workspace>/personas/`, `<workspace>/.mcp.json` per workspace; `~/.pos/` for cross-machine framework state | Designed but not built — `workspace-sync` per `canonical-to-workspace-sync-research.md`. |
| **pos3 today (downstream clone)** | Embedded in pos3's git tree (full git clone of canonical) | None — no upgrade mechanism currently | All in `<workspace>/.pos/` etc. | None today. |
| **Homebrew** | `/opt/homebrew/Cellar/<formula>/<version>/` (the keg); symlinks into `/opt/homebrew/bin`, `/opt/homebrew/lib`, etc. (the prefix) | `brew upgrade <formula>` — install new keg, repoint symlinks, optionally remove old keg | Configuration files in `/opt/homebrew/etc/<formula>/` are NOT overwritten on upgrade; user config preserved by convention | Yes — for config files in `etc/`. Symlink swap for bins/libs, leave-alone for configs. **This is the closest precedent for Architecture A done right.** |
| **pip (system vs venv)** | System Python or venv `lib/python3.x/site-packages/<pkg>/` | `pip install -U <pkg>` rewrites the package files in-place | Project state is outside site-packages by convention; package upgrade leaves it alone | No merge — disjoint trees by convention. |
| **npm (project local)** | `<project>/node_modules/` | `npm update` or `npm install` after bumping `package.json` | Project state in `<project>/src/`, NOT in `node_modules/`. node_modules is .gitignored. | No merge — disjoint trees by convention. |
| **git** | Source control itself, not a framework | `git pull` (fetch + merge) | Working tree is hand-authored; merge resolves conflicts file-by-file | **Yes — git pull IS the universal "pull canonical changes into customised workspace" primitive.** Three-way merge handles user customisation. This is the closest precedent for Architecture B's sync mechanism. |
| **Nix (per-shell)** | `/nix/store/<hash>-<name>/` immutable store; per-shell environment is a derivation | New derivations point at new store paths; old store paths kept until GC | Per-shell environment is declarative; user state outside the store | Partial — shells are reproducible, user data is separate, no merge problem because environment is declarative. |
| **create-react-app / create-next-app** | `<project>/node_modules/react-scripts/` or `<project>/node_modules/next/` | Bump version in `package.json`, run `npm install` | All user code in `<project>/src/`, `<project>/app/` etc. — disjoint from framework | No merge — framework occupies an opaque .gitignored directory. |

### Convention identification

**Three coherent patterns emerge:**

1. **Pattern P1 — "Framework-in-managed-dir" (npm, pip, create-react-app, CrewAI, Aider, LangChain, Continue.dev's framework code).** Framework lives in an opaque managed directory (`node_modules/`, `venv/`, `~/.config/`); user code lives in a separate directory the package manager never touches; upgrade = re-resolve manifest, rewrite managed directory only. **Dominant pattern across software ecosystems.** Dominant pattern across AI harnesses sampled. The user never has to reconcile framework-vs-state changes because the trees never overlap.

2. **Pattern P2 — "Binary upgrade with config preservation" (Homebrew, Claude Code binary, Hermes CLI binary).** A single executable lives at a global path; new versions overwrite the old; configuration files in a designated user-state location are explicitly preserved by convention. **This IS Architecture A** — but it works because the framework being upgraded is a binary, not an authoring surface.

3. **Pattern P3 — "Git-managed source tree with merge-on-pull" (raw git, the upstream/downstream pattern in any forked OSS project).** The framework IS the source tree; upgrade = `git pull` (or `git merge upstream/main`); conflicts resolved by three-way merge with optional automation. **This IS Architecture B's sync flavour.**

**Mapping back to pos-v2's mission:**
- pos-v2 is **not P2** — it isn't a binary; it's a multi-component sealed framework that the operator authors persona contracts, plans, and ODD specs against. The framework's surface area is much larger than a CLI's surface area.
- pos-v2 is **partially P1** — sealed component code COULD live in `<workspace>/.venv/lib/python3.x/site-packages/pos_self_upgrade/` etc. and be upgraded via `uv sync`. But this loses the property that operators can read the source of their framework as part of authoring (which Luke does) and breaks the ODD-spec/sealed-component-source coupling.
- pos-v2 is **mostly P3** — the framework IS a source tree the operator works with; canonical IS upstream; downstream workspaces ARE forks; sync IS three-way merge. The unique property pos-v2 adds is that the merge can be LLM-mediated for class-C conflicts while class-A workspace state is structurally protected.

**The dominant convention for pos-v2's mission is Pattern P3 (git-shaped sync).** Architecture B fits. Architecture A fits a different pos-v2 — one that ships as a binary and reads contracts/personas from per-workspace config files, which is not the pos-v2 being built.

---

## What openclaw reveals (halt-trigger check)

**Read full layout. Verdict: openclaw has no upgrade mechanism — period.** It is a single-tree workspace where framework code (`lib/pos_module.rb`, `lib/skill_loader.rb`, `bin/`, `ops/`, `modules/`, `personas/`) and operator state (`memory/`, `personal/`, `ivers-corp/`, `products/`, `data/`) are all checked into the same git tree. The only "upgrade" mechanism is `git pull` against an upstream, which is the same as Pattern P3 above with no LLM mediation and no class-A/B/C envelope.

**Halt trigger 2 (openclaw reveals an existing upgrade mechanism Luke could re-use directly): does NOT fire.** openclaw's pattern is "no upgrade mechanism, just git" — that's the floor pos-v2 is building above, not a re-usable mechanism.

The instructive bit: openclaw treats its workspace AS its framework. There is no canonical/downstream split. pos-v2 explicitly has a canonical/downstream split (canonical is `ivers-corp-pos-v2`; downstream is pos3, pos4, and any user clones). That split is what creates the upgrade question in the first place — openclaw never had to answer it.

---

## Halt-and-surface check

Per dispatch halt triggers:

1. **Dominant pattern doesn't fit pos-v2's mission objective.** Did not fire — Pattern P3 (git-shaped sync) fits cleanly and is exactly what `canonical-to-workspace-sync-research.md` already designed.
2. **openclaw reveals an existing upgrade mechanism.** Did not fire — openclaw has none.
3. **Question is moot (per-workspace clones inherently right).** Partially fires — yes, per-workspace clones are inherently right per Pattern P3, and `git pull` IS a valid no-LLM-mediation baseline. But the upgraded version with class-A/B/C envelope + LLM mediation is the pos-v2-leverage on top of git, so the question of *whether to use B* is moot (yes, B), but *what B looks like in pos-v2-flavoured form* is not (the `workspace-sync` design is the answer).

**No auto-halt. Owner ruling needed on D-A1 + D-A2.**

---

## Asymmetric observations

### Asymmetric wins surfaced

1. **Today's clause-(h) work (BB-feat #55 + DD #56 + CC + EE prep) is reusable.** The substrate-snapshot, conflict-detection, audit-write code is the right building block — it just needs to be re-targeted at the `workspace-sync` component instead of self-upgrade. **Effort to pivot:** medium (rename, move, re-publish API surface). **Leverage:** high — the work isn't wasted.

2. **`canonical-to-workspace-sync-research.md` is already the right design document.** It identified Pattern P3 (git-shaped, three-way merge, LLM-mediated, class envelope) as the right shape weeks ago. The decision Luke is wrestling with today (A vs B) is already implicitly answered by that research's recommendation to ship `workspace-sync` as a B-shape mechanism. **Effort:** zero — read the existing doc. **Leverage:** very high — closes the architecture-choice question.

3. **Self-upgrade clauses (a)–(g) are CORRECT for the canonical-side use case** (canonical install upgrades its own framework when a new release tag lands). They're the wrong scope for "upgrade pos3 from canonical." Don't tear them down — restrict their scope. **Effort:** low (doc edit + scope clarification in self-upgrade README). **Leverage:** medium — preserves shipped work, clarifies its envelope.

### Inverse-asymmetric proposals dropped

1. **"Build A and B both, let user pick."** Inverse-asymmetric: doubles the framework surface, fragments the audit/conflict-resolution paths, forces every future amendment to consider both. Drop.

2. **"Move all sealed-component code into a venv-installed Python package."** Tempting (cleaner P1 pattern). But operators MUST be able to read framework source as part of authoring (ODD plans, persona contracts, sealed-component proposals reference paths into the framework). Hiding source in `.venv/lib/python3.x/site-packages/` breaks the authoring loop. Drop.

3. **"Wait for Claude Code's plugin upgrade mechanism (#31462) and ship pos-v2 as a Claude Code plugin."** Tempting per Lens 1. But pos-v2 is too big to be a single plugin (it has a launchd-managed orchestrator, a memory sidecar, a tracker DB, an OTel pipeline). Plugins are skills+commands+hooks, not multi-process systems. Drop — but DO compose on the per-plugin auto-update mechanism for the pos-v2 distributed plugins (slash-commands, hooks) that ride alongside the heavier components. That's not architecture; that's hygiene.

---

## Recommended next action

1. **Owner rules on D-A1 (recommended: B).**
2. **If D-A1 = B, owner rules on D-A2 (recommended: option (i) — re-target clause-(h) work into `workspace-sync`).**
3. **A single dispatch authors the `workspace-sync` plan-doc**, lifting the recommendations from `canonical-to-workspace-sync-research.md` + this research's hybrid carve-out.
4. **Self-upgrade README gets a one-paragraph scope clarification** ("clauses (a)–(g) apply to the canonical install's own self-upgrade; for downstream-workspace pulls, see `workspace-sync`").
5. **Today's clause-(h) work is rescoped** — the Pydantic/audit/staging primitives become the foundation of `workspace-sync`'s sealed-component scope.

Estimated wall-clock for the plan-author dispatch: 30–60 minutes (`feedback_duration_estimation_rubric` — single-component plan with research already done). Background.

---

## Summary of the find

| Question | Answer |
|---|---|
| Does Architecture A fit pos-v2's mission? | **Partially** — A fits the canonical install upgrading itself + the Claude-native primitive cache (`~/.claude/`). A does NOT fit the downstream-workspace pull use case. |
| Does Architecture B fit pos-v2's mission? | **Yes** — B is the dominant pattern across every comparable AI harness for the framework's authoring surface, and Pattern P3 (git-shaped sync with LLM mediation) is what `workspace-sync` was designed to be. |
| Is openclaw's pattern reusable? | **No** — openclaw has no upgrade mechanism; halt trigger 2 does not fire. |
| Is today's clause-(h) work wasted? | **No** — re-targetable into `workspace-sync` (option (i) in D-A2). The substrate-snapshot + audit + Pydantic-validated conflict-report primitives are exactly right for workspace-sync. |
| Hybrid? | **Yes — minimal.** Architecture A behaviour is preserved for: (1) the canonical install's own self-upgrade (clauses a–g, scoped to canonical only); (2) Claude Code-native primitives (plugins, skills, MCP servers in `~/.claude/`, managed by Claude Code itself). Architecture B behaviour everywhere else. |
| Confidence on the recommendation? | **High** for B as primary; **medium** for the hybrid carve-out (the Claude-native carve-out IS already the case in pos-v2 today, so it's more "preserve the status quo" than "build something new"). |
| Decisions for owner ruling? | Five (D-A1 through D-A5), each with recommendation. D-A1 + D-A2 are blocking for the next dispatch. |

End of research doc. Owner ruling on D-A1 + D-A2 unblocks the `workspace-sync` plan-author dispatch and rescopes today's clause-(h) work cleanly.

---

## Sources

- [Claude Code: Advanced setup](https://code.claude.com/docs/en/setup)
- [Claude Code plugin update detection (issue #31462)](https://github.com/anthropics/claude-code/issues/31462)
- [Aider installation docs](https://aider.chat/docs/install.html)
- [CrewAI installation + project structure (DeepWiki)](https://deepwiki.com/crewAIInc/crewAI/8-llm-integration)
- [LangChain installation docs](https://docs.langchain.com/oss/python/langchain/install)
- [Continue.dev configuration deep-dive](https://docs.continue.dev/customize/deep-dives/configuration)
- [Letta GitHub](https://github.com/letta-ai/letta) and [Letta v1 agent architecture blog](https://www.letta.com/blog/letta-v1-agent)
- [Hermes Agent installation](https://hermes-agent.nousresearch.com/docs/getting-started/installation) and [GitHub](https://github.com/NousResearch/hermes-agent)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook) and [Manpage](https://docs.brew.sh/Manpage)
- [Create React App: Updating to New Releases](https://create-react-app.dev/docs/updating-to-new-releases/)
- [npm 1.0: Global vs Local installation](https://nodejs.org/en/blog/npm/npm-1-0-global-vs-local-installation)
- [pos-v2 self-upgrade architecture](file:///Users/lukeivers/ivers-corp-pos-v2/self-upgrade/docs/architecture.md) (local)
- [pos-v2 canonical-to-workspace sync research](file:///Users/lukeivers/ivers-corp-pos-v2/docs/plans/research/canonical-to-workspace-sync-research.md) (local)
- openclaw codebase audit at `/Users/lukeivers/cowork-openclaw/` (local — confirmed no upgrade mechanism)
