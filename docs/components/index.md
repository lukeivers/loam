# Components

loam ships fifteen runtime components in v0.1.0. Each has one short
reference page in this directory. The summary below is the
one-paragraph "what does it do" view; the per-component pages cover
how-to-invoke and observable surfaces.

| Component | Role |
|-----------|------|
| [`primary-persona`](primary-persona.md) | The single voice you talk to. Loader, monitor, autonomous-authoring contract; owns memory load/write at session boundaries. |
| [`workspace-bootstrap`](workspace-bootstrap.md) | Composition engine. Reads `loam init`, scaffolds per-host config, composes plugin contributions, writes the workspace's `.claude/settings.json`. |
| [`hands-off-lifecycle`](hands-off-lifecycle.md) | Owns SessionStart greeting, supervisor for orchestrator and memory primitive, drain-and-recovery when a session is interrupted. |
| [`safety-layer`](safety-layer.md) | Three kill switches + always-ask list + dangerous-op gate. PreToolUse interception of risky tool calls. |
| [`cost-governance`](cost-governance.md) | Token / time / money ceilings per scope; activation-gate wrap; sidecar ledger + drift detection. |
| [`reversibility-primitive`](reversibility-primitive.md) | Classifies tool calls into reversibility classes; binds compensations; surfaces irreversibility before it lands. |
| [`self-correction`](self-correction.md) | Four-part self-correction loop after a refusal or budget cap; consumer of safety + cost + reversibility gates. |
| [`dormancy`](dormancy.md) | Pause / resume / fail-loud policy under upstream outage; per-mode FSMs; notification + resume protocol. |
| [`memory`](memory.md) | File-based semantic memory the persona reads at SessionStart and writes at Stop. v0.1.0 default substrate. |
| [`observability-aggregator`](observability-aggregator.md) | Single-user local trace store. Subscribes to every component's OTel emissions; serves structured + NL queries; replay support. |
| [`orchestrator`](orchestrator.md) | Session-resilient asyncio process host; Unix-socket JSON-RPC; bind-scope dispatch layer; survives compaction. |
| [`scope-of-work`](scope-of-work.md) | Event-sourced FSM for named units of work; budget envelope; observers + escalation triggers. |
| [`objective-tracker`](objective-tracker.md) | Forest-of-trees objective tracking with event-sourced persistence; sidecar scope binding; ODD integration. |
| [`telegram-interface`](telegram-interface.md) | Telegram channel adapter — multi-identity allowlist, availability probe, direct Bot API fallback. |
| [`workspace-sync`](workspace-sync.md) | Canonical-to-workspace git-shaped sync; three-class workspace-data envelope; LLM-mediated semantic-merge gate. |
| [`self-upgrade`](self-upgrade.md) | Coordinates per-component upgrade fidelity into a single atomic operation; seven-clause acceptance contract. |

For internal implementation detail beyond the user-facing surface,
each component additionally carries a contributor-facing
`framework/<name>/README.md`. Those are not promised stable; the
per-component pages here are.
