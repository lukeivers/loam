# Components

loam ships eighteen runtime components in v0.1.0. Each has one short
reference page in this directory. The summary below is the
one-paragraph "what does it do" view; the per-component pages cover
how-to-invoke and observable surfaces.

| Component | Role |
|-----------|------|
| [`primary-persona`](primary-persona.md) | The single voice you talk to. Loader, monitor, autonomous-authoring contract; owns memory load/write at session boundaries. |
| [`workspace-bootstrap`](workspace-bootstrap.md) | Composition engine. Reads `loam init`, scaffolds per-host config, composes plugin contributions, writes the workspace's `.claude/settings.json`. |
| [`loam-init`](loam-init.md) | Registers the `loam init` subcommand on the unified `loam` CLI; thin shim over `workspace-bootstrap`'s fresh-workspace primitive. |
| [`hands-off-lifecycle`](hands-off-lifecycle.md) | Owns SessionStart greeting, supervisor for orchestrator and memory primitive, drain-and-recovery when a session is interrupted. |
| [`safety-layer`](safety-layer.md) | Three kill switches + always-ask list + dangerous-op gate. PreToolUse interception of risky tool calls. |
| [`cost-governance`](cost-governance.md) | Token / time / money ceilings per scope; activation-gate wrap; per-scope ledger + drift detection. |
| [`reversibility-primitive`](reversibility-primitive.md) | Classifies tool calls into reversibility classes; binds compensations; surfaces irreversibility before it lands. |
| [`self-correction`](self-correction.md) | Four-part self-correction loop after a refusal or budget cap; consumer of safety + cost + reversibility gates. |
| [`dormancy`](dormancy.md) | Pause / resume / fail-loud policy under upstream outage; per-mode FSMs; notification + resume protocol. |
| [`memory`](memory.md)<sup>†</sup> | File-based session-bridging memory the persona reads at SessionStart and writes at Stop. v0.1.0 default substrate. |
| [`observability-aggregator`](observability-aggregator.md) | Single-user local trace store. Subscribes to every component's OTel emissions; serves structured + NL queries; replay support. |
| [`orchestrator`](orchestrator.md) | Session-resilient asyncio process host; Unix-socket JSON-RPC; bind-scope dispatch layer; survives compaction. |
| [`scope-of-work`](scope-of-work.md) | Event-sourced FSM for named units of work; budget envelope; observers + escalation triggers. |
| [`objective-tracker`](objective-tracker.md) | Forest-of-trees objective tracking with event-sourced persistence; scope-bound contributor; ODD integration. |
| [`per-project-pm`](per-project-pm.md) | Workspace-scoped project-manager runtime; decision queue, state-of-world snapshot, one-question-at-a-time surfacing API. |
| [`telegram-interface`](telegram-interface.md) | Telegram channel adapter — multi-identity allowlist, availability probe, direct Bot API fallback. |
| [`workspace-sync`](workspace-sync.md) | Canonical-to-workspace git-shaped sync; three-class workspace-data envelope; LLM-mediated semantic-merge gate. |
| [`self-upgrade`](self-upgrade.md) | Coordinates per-component upgrade fidelity into a single atomic operation; seven-clause acceptance contract. |

### Dev/SDLC plugin verbs (composable, not core runtime)

The Dev/SDLC plugin (shipped at v0.1.0) contributes additional `loam` CLI verbs via the `loam.cli.subcommands` entry-point group. These ship with the canonical install path but are scoped to dev-mode workflows; they are not "runtime components" of the harness itself.

| Verb | Role |
|------|------|
| `loam amend` | Amendment-dispatch tooling (`validate / apply / seal / template / new-plan / new-memory`). Lives at `plugins/dev-sdlc/tools/loam-amend/`. |
| `loam pr-safety` | Gates PRs against the v0.1.8-authored banded ODD contract; pre-commit + pre-push hook installers; CI templates (GitHub Actions / GitLab CI / CircleCI). Lives at `plugins/dev-sdlc/pr-safety/`. |
| `loam odd-extract` | ODD reverse-engineering — read a target repo and emit a confidence-banded contract draft. Lives at `plugins/dev-sdlc/odd-extractor/`. |
| `loam project` | Dev/SDLC project lifecycle — methodology-shaped 5-stage workflow with structural gate enforcement. Lives at `plugins/dev-sdlc/`. |

<sup>†</sup> The `memory` component's implementation lives inside
`framework/primary-persona/` (`file_memory.py`,
`memory_write_queue.py`, `memory_write_worker.py`,
`stop_emitter.py`, `session_start_emitter.py`); there is no
standalone `framework/memory/` directory. The component is real;
it ships as part of the primary-persona package because session-
boundary memory load/write is the persona's contract.

For internal implementation detail beyond the user-facing surface,
each component additionally carries a contributor-facing
`framework/<name>/README.md`. Those are not promised stable; the
per-component pages here are.
