# Claude capability map for pOS v2

- **Snapshot date:** 2026-04-23
- **Version:** 0.1 (skeleton — being filled incrementally)
- **Stewarded by:** primary persona; future refresh automation per `docs/rebuild/FUTURE_IDEAS.md` Idea 1 Step 4
- **Refresh cadence (target):** daily, budget-permitting, once Step 4 lands
- **Scope:** the Claude-attached capability surface available to pOS v2 feature research — Claude Code CLI, Claude Agent SDK, Anthropic API, MCP, plugins, skills, subagents, background tasks, session persistence

## Purpose

This map is the reference an AI agent (or a human author) consults during feature research for pOS v2 to answer Lens 1 — *"what Claude capability does this lean on or extend?"* — without having to re-discover the surface. The file is not a tutorial and not an API reference; it is a curated map that names each capability, says how it composes with pOS v2's existing sealed components, flags the known pitfalls, and points at the end-user configuration surface.

How to use it: open this file at the start of any feature research. For each capability that might plausibly back the feature, read the four subsections (one-line description, pos-v2 composition, pitfalls, end-user configuration). If none of the capabilities fit, that is itself a finding — write it up in the research plan so the Lens 1 gate (once enforcement lands in Idea 1 Step 3) can record the negative answer.

The map is deliberately a **2026-04-23 snapshot**. Claude's surface drifts weekly. Sections flagged *Volatile* are particularly likely to be stale by the time you read them; the refresh automation in Idea 1 Step 4 will keep the snapshot current once it ships. Until then, cross-check anything load-bearing against the cited source URL before you build on it.

## How entries are structured

Every capability entry has four parts:

1. **What it does** — one line.
2. **How it composes with pos-v2** — which sealed components already use it or could latently compose with it. Citations are to `docs/rebuild/components/<name>/` narratives where relevant.
3. **Pitfalls** — known footguns, version skew risks, rate limits, silent-failure modes.
4. **End-user configuration surface** — where a user turns the capability on, off, or tunes it. Typically a file path, a CLI flag, an env var, or a settings key.

Where sources are thin, the entry ends with `_Unclear from available sources as of 2026-04-23; flagged for Idea 1 Step 4 refresh._`

---

## Table of contents

1. [Claude Code CLI](#1-claude-code-cli)
2. [Claude Agent SDK](#2-claude-agent-sdk)
3. [Anthropic API (Messages + adjacent)](#3-anthropic-api-messages--adjacent)
4. [Model Context Protocol (MCP)](#4-model-context-protocol-mcp)
5. [Plugin system](#5-plugin-system)
6. [Skills](#6-skills)
7. [Agent tool and subagents](#7-agent-tool-and-subagents)
8. [Background-task primitives](#8-background-task-primitives)
9. [Session persistence](#9-session-persistence)
10. [Cross-capability notes](#10-cross-capability-notes)

---

## 1. Claude Code CLI

Claude Code is the terminal-first harness the primary persona runs inside. Every pos-v2 session is ultimately a Claude Code process; the capabilities below define what the harness exposes to the persona and to the workspace configuration.

### 1.1 Slash commands (merged into Skills as of late-2025)

**What it does.** `/name` invokes either a bundled command (e.g. `/help`, `/compact`, `/status`) or a user-authored skill. Custom commands under `.claude/commands/<name>.md` still work but the documented canonical form is a Skill directory at `.claude/skills/<name>/SKILL.md`. Skills can accept positional arguments (`$ARGUMENTS`, `$0`, `$1`, or named `arguments` list in frontmatter) and support string substitution for `${CLAUDE_SESSION_ID}` and `${CLAUDE_SKILL_DIR}`.

**Composes with pos-v2.**
- `telegram-interface` already ships user-facing slash skills (`/telegram:configure`, `/telegram:access`) — the Skill pattern is proven inside pos-v2 already.
- `tools/pos-amend/` is a CLI today; a future Skill wrapper (`.claude/skills/pos-amend/SKILL.md`) would let the primary persona trigger amendment-cycle bookkeeping through the same `/` dispatch surface as everything else. Latent composition.
- `docs/rebuild/FUTURE_IDEAS.md` Idea 8 (structural context-load gate) can likely be authored as a Skill invoked at session-start or a Skill called by a SessionStart hook, depending on where the gate lives.

**Pitfalls.**
- Skills default to being both user-invocable AND auto-loaded by Claude. Workflows with side effects (deploy, commit, amend) need `disable-model-invocation: true` or the persona may run them unprompted.
- Skill descriptions share a dynamic character budget (~1% of context window, fallback 8000 chars, cap 1536/entry). Long or poorly-front-loaded descriptions get truncated — keywords the persona needs to match on must appear in the first ~200 chars.
- Invoked skill content stays resident in the conversation; auto-compaction reattaches at most 5000 tokens per skill and 25000 tokens total, so heavy skill stacks get silently truncated after compaction.
- `context: fork` skills run in a subagent with an isolated context — they do not see the main conversation's history. Skills without an explicit task (reference-style skills) produce no useful output when forked.

**End-user configuration surface.**
- Skills: `.claude/skills/<name>/SKILL.md` (project), `~/.claude/skills/<name>/SKILL.md` (personal), `<plugin>/skills/` (plugin-scoped).
- Legacy commands: `.claude/commands/<name>.md` (project), `~/.claude/commands/<name>.md` (personal).
- Permission gates: `Skill(name)` / `Skill(name *)` in `permissions.allow`/`deny`.
- Budget override: `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var.

### 1.2 Hook events

**What it does.** Deterministic lifecycle callbacks the harness fires on well-defined events. Hooks can modify behaviour (allow / deny / inject context / rewrite tool input), not just observe. The full 2026-04-23 event list:

| Category | Events |
|----------|--------|
| Session | `SessionStart`, `SessionEnd`, `InstructionsLoaded` |
| User input | `UserPromptSubmit`, `UserPromptExpansion` |
| Tool execution | `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch` |
| Subagent | `SubagentStart`, `SubagentStop`, `Stop`, `StopFailure` |
| Tasks | `TaskCreated`, `TaskCompleted` |
| Config / FS | `ConfigChange`, `FileChanged`, `CwdChanged` |
| Compaction | `PreCompact`, `PostCompact` |
| Worktree | `WorktreeCreate`, `WorktreeRemove` |
| Notification | `Notification`, `TeammateIdle` |
| MCP | `Elicitation`, `ElicitationResult` |

Handler types: `command` (shell, default 600s timeout), `http`, `mcp_tool`, `prompt` (model call), `agent` (subagent). Matcher syntax supports exact names, `|`-separated alternatives, regex (any non-alphanumeric char). Exit code 0 = allow; stdout parsed as JSON for structured control. Exit code 2 = block with stderr surfaced. `WorktreeCreate` treats any non-zero exit as failure.

**Composes with pos-v2.**
- `hands-off-lifecycle` owns the SessionStart hook wired in `.claude/settings.json` today — `first-run.sh` is the thin shim, detached worker handles venv/install/scaffold. The pattern (thin shim, detached worker, re-entry on subsequent boots) is the reference implementation for any future pos-v2 SessionStart hook.
- `safety-layer` and `reversibility-primitive` are natural consumers of `PreToolUse` hooks — pos-v2's current approach is AC-shaped refusal, but `PreToolUse` with `permissionDecision: "deny"` is the structural-enforcement equivalent.
- `observability-aggregator` composes with `PostToolUse` / `SessionEnd` / `Stop` for passive event capture without intrusive instrumentation.
- `cost-governance` can attach to `PreToolUse` (check budget before expensive tool), `PostToolUse` (record spend), and `PreCompact` (assess compaction cost).
- `self-correction-loop` composes with `PostToolUseFailure` (capture failure + retry context) and `Stop` with `decision: "block"` (force continuation if correction incomplete).
- The structural-context-load gate (Idea 8) maps cleanly onto `UserPromptSubmit` or `SessionStart` — the hook refuses to advance until design docs are loaded.
- `primary-persona-loader` can assert on `InstructionsLoaded` (fired when `CLAUDE.md` / `.claude/rules/*.md` enter context) that the right set of persona docs was loaded.

**Pitfalls.**
- Default command-hook timeout is 600s, not infinite — long-running worker spawn must detach (as `first-run.sh` does via `first_run_dispatch.py`), not block the hook.
- `async: true` returns immediately but the hook lifetime ends, so async hooks cannot inject `additionalContext` synchronously. pos-v2's current SessionStart uses `async: false` deliberately — see the comment in `.claude/settings.json` line 2.
- Hooks declared in `settings.local.json` are gitignored — they do not ship with the repo. Project-shared hooks must live in `.claude/settings.json`.
- `disableAllHooks: true` in managed settings silently kills every hook in the workspace; debug via `/hooks` to see what's active.
- MCP tool matchers use `mcp__<server>__<tool>` pattern — regex matchers must account for the double-underscore separator.
- `SessionStart` `source` field values (`startup|resume|clear|compact`) change what context is meaningful — a hook that runs setup only on `startup` must filter, or it re-runs on every resume.

**End-user configuration surface.**
- `.claude/settings.json` (project, shared), `.claude/settings.local.json` (project, gitignored), `~/.claude/settings.json` (user), `managed-settings.json` (IT-deployed).
- Hook schema is documented at `hooks.<EventName>[].hooks[]`; each hook declares `type`, `command`/`url`/`server`/`tool`/`prompt`, `timeout`, optional `matcher`, optional `async`.
- Runtime viewer: `/hooks` command shows all active hooks grouped by source (User, Project, Local, Plugin, Session, Built-in).

### 1.3 settings.json schema and precedence

**What it does.** JSON configuration file governing permissions, env, model, hooks, plugins, sandbox, and 50+ other keys. Hierarchical precedence: Managed > CLI flags > `settings.local.json` (project-local) > `settings.json` (project-shared) > `~/.claude/settings.json` (user). **Array-valued settings** (permissions.allow, deny, etc.) concatenate and deduplicate across scopes rather than replacing — managed baselines compose with project additions compose with user additions.

**Composes with pos-v2.**
- Current pos-v2 `.claude/settings.json` only wires the SessionStart hook; everything else (permissions, plugins, sandbox) is unspecified and therefore defaults. Any future `workspace-bootstrap` amendment that wants to ship permission defaults adds them here.
- `cost-governance` could consume `env.CLAUDE_CODE_ENABLE_TELEMETRY` + `OTEL_*` keys to surface metered spend through standard OpenTelemetry exporters without custom plumbing.
- `safety-layer` structural refusals map onto `permissions.deny` rules — any tool/path combination the safety layer refuses can be duplicated as a `deny` rule so Claude never even proposes it.

**Pitfalls.**
- Permission rule evaluation order is `deny → ask → allow` (first match wins). Placing `allow` rules expecting fallback behavior is a common bug.
- The array-merge rule applies to top-level permission arrays but not to every key — check the docs per field before assuming merge semantics.
- `apiKeyHelper`, `awsCredentialExport`, `otelHeadersHelper` shell out on each request; a slow helper bottlenecks every tool call.
- `allowManagedHooksOnly: true` in managed settings silently ignores project and user hooks — debugging "why isn't my hook firing" starts with `/status`.
- `.claude/settings.local.json` is gitignored by default; new contributors to a pos-v2 clone don't get its hooks automatically. The current pos-v2 SessionStart hook is deliberately in the shared `settings.json` so every clone gets it.

**End-user configuration surface.**
- Files: `~/.claude/settings.json`, `<repo>/.claude/settings.json`, `<repo>/.claude/settings.local.json`, platform-specific managed paths.
- Inspection: `/status` shows active sources; `/config` exposes a subset of UI settings.
- Top-level keys (partial): `permissions`, `env`, `model`, `sandbox`, `agent`, `hooks`, `attribution`, `plugins`, `enabledPlugins`, `cleanupPeriodDays`, `language`, `alwaysThinkingEnabled`, `autoMode`, `disableAllHooks`.

### 1.4 CLI flags and `--print` (headless) mode

**What it does.** The `claude` binary accepts both interactive (no `-p`) and headless (`-p` / `--print`) modes. Headless mode runs one turn, streams output per `--output-format` (`text`, `json`, `stream-json`), and exits — it is the primitive the Agent SDK and most scripted harnesses build on. Session IDs (UUIDs) can be passed with `--session-id` to correlate multiple invocations. `--resume <id|name>` or `-c` (continue most recent) resumes stored sessions. `--fork-session` creates a new ID from a resumed session so both diverge.

**Composes with pos-v2.**
- `session-resilient-orchestrator` and `hands-off-lifecycle` both spawn Claude Code processes; they rely on `-p`, `--output-format stream-json`, and explicit session IDs to correlate logs across restarts. `--include-hook-events` is the flag that surfaces hook firings into the output stream — essential for the orchestrator's background-work-awareness contract (STATE.md rule 7).
- `memory-system` uses `ClaudePrintLLMClient` (amendment #8) which is exactly `claude -p` invoked as a subprocess for entity extraction. The fallback routing, error handling, and cost governance all compose with the CLI's behaviour, not a raw API.
- `--max-budget-usd` is a first-class cost ceiling that `cost-governance` could compose with rather than re-implementing wall-clock spend tracking.
- `--bare` mode skips skill/hook/plugin/MCP discovery for faster scripted calls — relevant for `pos-amend` and other CLI tools where a quick model call shouldn't drag in the whole harness.
- `--json-schema` enforces structured output — relevant for any pos-v2 component that needs a validated JSON response from Claude (objective-tracker, foundation-audit, self-correction-loop all have shapes that would benefit).

**Pitfalls.**
- `claude -p` with `--no-session-persistence` means the session is not saved — use carefully; you cannot debug a failed session after the fact.
- `--dangerously-skip-permissions` is equivalent to `--permission-mode bypassPermissions` and skips every user-confirmation prompt. Any pos-v2 script using it must assert its own safety invariants first.
- Flags absent from `claude --help` may still exist (the CLI reference is the ground truth, not `--help`).
- `--max-turns` only applies in print mode and exits with error when exceeded — interactive sessions have no turn cap.
- `--exclude-dynamic-system-prompt-sections` improves prompt-cache reuse across machines/users but only takes effect with the default system prompt; ignored when `--system-prompt` overrides.
- `--fallback-model` is print-mode only — interactive sessions must select model upfront.
- Session IDs must be valid UUIDs when passed with `--session-id`.

**End-user configuration surface.**
- Invocation: `claude [flags] [prompt]` or piped stdin for `-p`.
- Persistent default flags: none — every invocation re-parses. Consider shell aliases or wrapper scripts.
- Auth: `claude auth login [--email|--sso|--console]`, `claude auth status --text`, `claude auth logout`. `claude setup-token` for CI long-lived tokens.
- Version pin: `claude install <version|stable|latest>`.

### 1.5 Session mechanics (interactive vs headless)

**What it does.** Every Claude Code session has a UUID session ID. Interactive sessions auto-persist to disk (honouring `cleanupPeriodDays`, default 30). Sessions can be named (`-n` / `/rename`), resumed (`-r <id|name>`), continued (`-c`), forked (`--fork-session`). Session context is scoped to the working directory plus any directories added via `--add-dir` or `/add-dir`. Transcripts live as `.jsonl` files; hook events receive `transcript_path` for offline analysis.

**Composes with pos-v2.**
- `session-resilient-orchestrator`'s entire premise — that work survives session boundaries — depends on predictable session IDs and resumption semantics. Passing explicit `--session-id` to spawned Claude processes lets the orchestrator correlate logs, outputs, and recovery across orchestrator restarts.
- `observability-aggregator` consumes the transcript `.jsonl` files for after-the-fact session analysis; the transcript_path field exposed in every hook is the reliable way to find them.
- `primary-persona-loader` + `memory-system` together give the persona the illusion of continuity across sessions — session persistence is one leg, memory the other.

**Pitfalls.**
- `--no-session-persistence` (print mode only) skips disk write; there is no way to resume such a session.
- `cleanupPeriodDays` deletes old sessions silently — long-term audit logs need to be harvested to durable storage (observability-aggregator is the right home).
- `--add-dir` grants file access but does not load most `.claude/` configuration from the added dir — skills are an exception (loaded), subagents and commands are not. Latent footgun for pos-v2 plugin authors.
- `--from-pr <N>` auto-links sessions to GitHub PRs when created via `gh pr create`; useful for traceability but also leaks session data into PR tooling — confirm the team's policy.

**End-user configuration surface.**
- `claude resume`, `claude -c`, `claude -r <name>`, `claude -n <name>`, `/rename`, `/add-dir`.
- Storage location: platform-specific (see `claude auth status --text` for active paths).
- `cleanupPeriodDays` in settings.json controls retention.

_Sources (1.x): `https://code.claude.com/docs/en/slash-commands`, `https://code.claude.com/docs/en/hooks`, `https://code.claude.com/docs/en/settings`, `https://code.claude.com/docs/en/cli-reference` — all fetched 2026-04-23._

---

## 2. Claude Agent SDK

**Renamed from Claude Code SDK late-2025.** Available in Python (`claude_agent_sdk`) and TypeScript (`@anthropic-ai/claude-agent-sdk`). The SDK is the programmatic form of the Claude Code harness — the same tool loop, hook surface, subagent dispatch, and skills/commands discovery, but invoked as a library from your own Python or TypeScript process.

### 2.1 Core primitive — `query()`

**What it does.** `query(prompt, options)` returns an async iterator of messages. Claude handles the entire tool-use loop internally — it decides which tools to call, the harness executes them against the configured permission model, results stream back as messages. Unlike the raw Messages API (where you implement the `while stop_reason == "tool_use"` loop yourself), the Agent SDK owns the loop and just yields messages at each step.

```python
async for message in query(
    prompt="Find and fix the bug in auth.py",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
):
    print(message)
```

Message types: `SystemMessage` (session-init with `session_id`), `AssistantMessage`, `UserMessage`, `ToolUseMessage`, `ToolResultMessage`, `ResultMessage` (final, with `.result` on it). Streaming is per-message, not per-token — use `--include-partial-messages` equivalent SDK options for token-level streaming.

**Composes with pos-v2.**
- Every pos-v2 component that needs to call Claude programmatically — `memory-system`'s `ClaudePrintLLMClient`, background workers, orchestrator-dispatched scopes — is a candidate for migrating from subprocess `claude -p` to the Agent SDK. The SDK path is higher-throughput (no process spawn per query), gives first-class hook callbacks instead of stdout parsing, and supports typed message objects instead of JSON parsing.
- `session-resilient-orchestrator` can call `query()` with an explicit `resume=<session_id>` option to reattach to durable sessions across orchestrator restarts. The SystemMessage init payload includes the new session ID which must be captured and persisted to survive crashes.
- `self-correction-loop` maps onto the SDK's hook callback shape naturally — a `PostToolUse` callback in the SDK is a regular Python/TS function, easier to author than a shell-command hook declared in settings.json.

**Pitfalls.**
- The TypeScript SDK bundles a platform-specific Claude Code binary as an optional dep; the Python SDK does not bundle — it shells out to `claude` on PATH. Python deployments must install Claude Code separately.
- Opus 4.7 (`claude-opus-4-7`) requires SDK ≥ v0.2.111; older pinned versions error with `thinking.type.enabled`.
- Third-party providers (Bedrock, Vertex, Azure Foundry) work via env vars (`CLAUDE_CODE_USE_BEDROCK=1`, etc.) and credential files — the SDK does not accept provider SDKs directly. Non-Anthropic hosting means non-Anthropic rate limits and pricing.
- Anthropic does not permit third parties to offer claude.ai-subscription-backed API access to their customers. SDK-built products must use API keys (or Bedrock/Vertex/Azure). This affects pos-v2 only if the eventual open-source launch (Idea 12) ever offers a managed tier.

**End-user configuration surface.**
- Auth: `ANTHROPIC_API_KEY` env var, or provider equivalents.
- Options bag: `ClaudeAgentOptions` in Python / `options` object in TS. Fields include `allowed_tools`, `disallowed_tools`, `permission_mode`, `hooks`, `agents` (subagent definitions), `mcp_servers`, `resume`, `system_prompt` / `append_system_prompt`, `model`, `max_turns`, `setting_sources`.
- Filesystem discovery: by default the SDK loads skills from `.claude/skills/`, commands from `.claude/commands/`, memory from `CLAUDE.md`, plugins from programmatic config. Restrict with `setting_sources=["user"|"project"|"local"]`.

### 2.2 Built-in tools available via SDK

Read, Write, Edit, Bash, **Monitor** (watch a background script and react to each output line as an event — directly relevant to pos-v2 orchestrator patterns), Glob, Grep, WebSearch, WebFetch, AskUserQuestion. Plus MCP tools wired via `mcp_servers` and the `Agent` tool for subagent dispatch.

**Composes with pos-v2.**
- The `Monitor` tool is the first-class primitive for STATE.md rule 7 (background-work awareness). `observability-aggregator` today parses process stdout; `Monitor` converts each stdout line into an in-context event, eliminating the parsing layer and letting the persona react per-line without polling.
- `AskUserQuestion` is the structural way to elicit a ruling from the user with bounded multiple choice — compose with ODD's "any unresolved ambiguity halts" pattern. Beats free-form question-asking, which the persona is empirically bad at bounding.

**Pitfalls.**
- `allowed_tools` gates tool visibility; a tool absent from the list cannot be used. Forgetting to include `Agent` in `allowed_tools` when also defining subagents silently disables delegation.
- Tool parallelism: Claude may batch multiple tool calls in a single turn (`PostToolBatch` hook fires after the whole batch). Hook callbacks must be idempotent per tool call.

### 2.3 SDK hooks

Same hook event types as Claude Code CLI (§1.2) but declared as **callback functions** in-process instead of shell commands. `HookMatcher(matcher="Edit|Write", hooks=[callback])`. Available events documented as `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, and more.

**Composes with pos-v2.** Hooks authored in-process are easier to unit-test than shell hooks, easier to share state with the calling program, and easier to package into a Python/TS library. For future pos-v2 primitives that want to enforce a rule (safety-layer's refusal, cost-governance's spend check), an SDK hook callback may be a better home than a command hook in settings.json — especially inside the Python backend of `session-resilient-orchestrator`.

**Pitfalls.**
- Hook callbacks run in the same process as the SDK caller; an infinite loop or blocking I/O in a hook halts the whole agent turn.
- Hooks declared programmatically via `ClaudeAgentOptions.hooks` compose with settings.json hooks — both fire. Avoid duplicate logic.

### 2.4 Subagents via SDK

`agents={"code-reviewer": AgentDefinition(description=..., prompt=..., tools=[...])}` defines a named subagent the main agent can dispatch. Messages from within a subagent context carry `parent_tool_use_id` for attribution. See §7 for the full subagent capability surface.

### 2.5 MCP servers via SDK

`mcp_servers={"playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}}` — the SDK spawns and manages MCP server lifecycles. See §4 for full MCP surface.

### 2.6 Sessions via SDK

First query emits a SystemMessage with `session_id`; subsequent queries pass `resume=<session_id>` to continue the same session. `--fork-session`-equivalent options available programmatically. pos-v2's `session-resilient-orchestrator` already relies on this pattern at the CLI level; migrating to SDK would let the orchestrator capture the session ID from the SystemMessage object directly instead of parsing init logs.

### 2.7 Agent SDK vs Claude Client SDK (Anthropic SDK) vs Claude Code CLI

| Use case | Best choice | Why |
|----------|-------------|-----|
| Interactive dev | Claude Code CLI | TUI, REPL, `/slash` surface |
| Production automation | Agent SDK | Typed primitives, in-process hooks |
| Pure API (no tool loop) | Client SDK (`anthropic`) | No loop, full control |
| CI/CD | Agent SDK or CLI | Both work; SDK is cleaner error handling |
| One-off scripts | `claude -p` | No setup |

The Client SDK (`anthropic` / `@anthropic-ai/sdk`) is a thinner layer that directly wraps the Messages API — it does not ship the tool loop, the permission model, or skills/commands/hooks. Use it when you want raw model access or are building a different kind of agent (not Claude-Code-shaped). Use the Agent SDK when you want Claude-Code capabilities programmatically.

**Composes with pos-v2.** pos-v2 today uses `claude -p` as subprocess (memory-system's `ClaudePrintLLMClient`). The Agent SDK is a natural migration target for any caller that benefits from typed messages, in-process hook callbacks, or programmatic subagent control. The Client SDK is a better fit when pos-v2 needs model calls without the harness — e.g. small-scope entity extraction where the tool loop is overkill.

_Sources (2.x): `https://code.claude.com/docs/en/agent-sdk/overview` — fetched 2026-04-23._

---

## 3. Anthropic API (Messages + adjacent)

The layer Claude Code and the Agent SDK compose on top of. pos-v2 rarely touches the raw API directly today (memory-system uses Claude-via-Max through `claude -p`), but several pos-v2 primitives are cleaner when authored against the API directly.

### 3.1 Messages API (`POST /v1/messages`)

**What it does.** Stateless request/response to Claude. Required params: `model`, `max_tokens`, `messages[]` (alternating user/assistant). Optional: `system`, `tools`, `tool_choice`, `temperature`, `top_p`, `top_k`, `stream`, `stop_sequences`, `thinking`, `cache_control`, `metadata`.

Message content can be a plain string or an array of blocks. Block types: `text`, `image`, `document`, `tool_use`, `tool_result`, `thinking`. Responses contain a `content` array (same block types plus model-generated `tool_use` / `thinking` / `text`), a `stop_reason` (`end_turn` / `tool_use` / `max_tokens` / `stop_sequence`), and a `usage` object (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`).

Tool loop is caller's responsibility: if `stop_reason == "tool_use"`, execute each tool_use block, append a `tool_result` user message, call `/v1/messages` again. Repeat until `end_turn`.

**Composes with pos-v2.**
- `memory-system`'s extraction path could migrate from `claude -p` subprocess to direct Messages API for lower latency and finer-grained error recovery. Amendment #8's `ClaudePrintLLMClient` abstraction is the composition seam — add a sibling `ClaudeAPIClient` that the subscription-vs-API routing decision feeds.
- `self-correction-loop` benefits from direct API access when the loop needs to inspect `stop_reason` and `usage` for pacing decisions (e.g. back off when output_tokens is spiking).
- `objective-tracker` and `foundation-audit` both benefit from structured-output features — the `output_config` JSON schema param forces validated JSON without the full Claude Code tool loop.

**Pitfalls.**
- Roles must alternate strictly (user, assistant, user, …). A trailing assistant message errors.
- `max_tokens` is not the total turn budget; it's the completion cap. Large max_tokens + streaming can bill heavily even if the response stops early.
- `stop_reason == "max_tokens"` is silent failure from a product standpoint — the model did not finish its thought. Surface it as an error, not a success.
- Model IDs drift: `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5` are current as of 2026-04-23; older model IDs eventually retire.

**End-user configuration surface.**
- Auth: `x-api-key` header, `ANTHROPIC_API_KEY` env var, or provider-specific auth (Bedrock/Vertex/Foundry).
- SDK shortcuts: `anthropic` (Python), `@anthropic-ai/sdk` (TS), `anthropic-sdk` (Go, Java, others).
- Beta headers via `anthropic-beta` for features like interleaved thinking, files, some batch variants.

### 3.2 Tool use

Tool definitions are passed in `tools[]`; each is `{name, description, input_schema (JSON Schema)}`. Model emits `tool_use` blocks; caller runs the tool, returns `tool_result` block; loop until `end_turn`. Tool choice modes: `{"type": "auto"}`, `{"type": "any"}`, `{"type": "none"}`, `{"type": "tool", "name": "..."}` — but `any` and named choice are incompatible with extended thinking.

**Composes with pos-v2.** The Agent SDK wraps this loop, so most pos-v2 code that needs tool use goes through the SDK (§2) rather than touching tool use directly. Raw API tool use is preferable when the toolset is custom or small and the pos-v2 Python process wants full control over the loop — e.g. a scope that needs exactly two tools and no filesystem access.

### 3.3 Extended thinking

**What it does.** `thinking: {type: "enabled", budget_tokens: N, display: "summarized"|"omitted"}` adds a `thinking` content block to the response containing Claude's internal reasoning. Opus 4.7+ requires **adaptive thinking** via the `effort` parameter instead of manual `budget_tokens` (manual mode returns 400 on Opus 4.7+).

| Model | Thinking support |
|-------|------------------|
| Opus 4.7 | Adaptive only; manual → 400 |
| Opus 4.6 | Adaptive recommended; manual deprecated |
| Sonnet 4.6 | Manual + interleaved (deprecated) |
| Sonnet 3.7 | Full manual |

**Composes with pos-v2.**
- `self-correction-loop` and `foundation-audit` are reasoning-heavy scopes that benefit from extended thinking / adaptive thinking. The `effort: "high"` or `"xhigh"` knob on Opus 4.7 replaces the old manual budget without re-tuning.
- `primary-persona-loader` + ODD-authoring interactions benefit from adaptive thinking during plan drafting (the persona needs to consider constraints + acceptance fully).

**Pitfalls.**
- **Tool loops with thinking must pass thinking blocks back** on subsequent calls — dropping them corrupts the reasoning chain. `signature` field is encrypted proof of the block; the API validates it.
- `tool_choice: any` and explicit tool selection are **not compatible** with extended thinking — use `auto` or `none`.
- Thinking parameter changes between turns **invalidate message cache breakpoints** (system cache survives).
- `display: "summarized"` (default on Claude 4) returns a summary but **you still pay for full thinking tokens**. `"omitted"` streams faster but same cost.
- Interleaved thinking (think between tool calls): Mythos Preview automatic, Opus 4.6/4.7 via adaptive thinking, Sonnet 4.6 via beta header `interleaved-thinking-2025-05-14` (deprecated).

**End-user configuration surface.** `thinking.type`, `thinking.budget_tokens` (pre-Opus-4.7), `thinking.display`, `effort` param (Opus 4.7+), beta headers.

### 3.4 Prompt caching

**What it does.** Marking content blocks with `cache_control: {type: "ephemeral"}` lets Anthropic cache the prefix and charge **0.1x base rate** (90% off) on cache hits. Writes cost 1.25x (5m TTL) or 2x (1h TTL). Up to 4 explicit breakpoints; automatic caching (top-level `cache_control`) moves the breakpoint forward for multi-turn conversations.

**Cacheable:** tool definitions, system, messages, images, documents, tool_use/tool_result blocks. **Not cacheable to mark:** thinking blocks, empty text, citation sub-blocks (but thinking blocks do get cached alongside other content).

**Minimum prompt length:** 4096 tokens (Opus 4.5/4.6/4.7, Haiku 4.5), 2048 tokens (Sonnet 4.6, Haiku 3.5), 1024 tokens (older). Below minimum, cache fields return 0 silently.

**Composes with pos-v2.**
- `memory-system`, `self-correction-loop`, and any pos-v2 component running repeated Claude calls with large stable prefixes (system prompts, tool definitions, canonical docs) should mark them `cache_control` — 90% cost reduction on hits.
- `cost-governance` can surface cache hit/miss ratio via the usage fields (`cache_read_input_tokens` / `cache_creation_input_tokens`) as a first-class metric. Amendment-level regressions that silently drop cache hits would show up immediately.
- ODD methodology docs + CLAUDE.md itself become a natural cache breakpoint when the primary persona is invoked — same content every turn.

**Pitfalls.**
- **Timestamps in cached blocks** = cache never hits. Mark breakpoint on the last *stable* block; leave volatile content uncached.
- 20-block lookback limit: in growing conversations, add a second breakpoint when the moving breakpoint drifts past 20 blocks from the last write.
- Invalidation cascades: changing tools → full cache gone. Changing system (web search on/off, citations on/off) → system+messages gone. Changing tool_choice → messages gone. Changing speed setting → system+messages gone. Adding non-tool user text after extended thinking → all prior thinking blocks stripped.
- Longer TTL must come before shorter in the same request.

**End-user configuration surface.** `cache_control: {type: "ephemeral", ttl: "5m"|"1h"}` on blocks; automatic top-level `cache_control`.

### 3.5 Message Batches API

**What it does.** Asynchronous bulk request processing. **50% cost reduction** vs real-time, most batches finish in <1 hour. Poll status, retrieve all results at once. Up to tens of thousands of requests per batch.

**Composes with pos-v2.**
- `memory-system`'s bulk entity extraction over historical transcripts is a natural batch fit — no latency SLA, 50% cheaper.
- `foundation-audit` running against every component's artefact set is another batch candidate when the audit is not interactive.
- Scheduled daily refreshes (Idea 1 Step 4 — this file's refresh job) fit the batch pattern: no user waiting, cheaper.

**Pitfalls.**
- **Not ZDR-eligible** (Zero Data Retention). Batched data is retained per standard policy. Workspaces with ZDR requirements cannot use batches.
- No streaming; no partial results during processing.
- Failed requests inside a batch are returned in the result set, not raised synchronously — consumer must inspect per-request status.

**End-user configuration surface.** `POST /v1/messages/batches` to create, `GET /v1/messages/batches/{id}` to poll, `GET /v1/messages/batches/{id}/results` to retrieve.

### 3.6 Citations

**What it does.** When documents are passed in user content with `citations: {enabled: true}`, Claude returns responses with auto-attributed `citation` sub-blocks pointing at source document spans. Supported document types: PDF (via Files API), plain text, custom JSON chunks.

**Composes with pos-v2.**
- Any future research-shaped plugin (legal, knowledge-management, long-form editorial per Idea 3) benefits — auto-citations turn Claude outputs into verifiable artefacts without post-hoc retrieval.
- `memory-system` interplay: citations source documents from the request, not from memory. For memory-backed citations, the retrieval layer must surface source-citation-ready chunks.

**Pitfalls.** Citations invalidate some cache paths. Not all models support citations; check current model docs before relying on them.

_Volatile — likely to drift within weeks._

### 3.7 Files API

Upload files once, reference by ID across many requests. Supports PDFs, images, large text documents. Composes with citations (upload document → reference by file_id → get citations back). Not all providers (Bedrock/Vertex) mirror the Files API.

_Unclear from available sources as of 2026-04-23 whether pos-v2's current usage patterns need Files API; flagged for Idea 1 Step 4 refresh._

### 3.8 Memory API

Anthropic's server-side memory tool (distinct from `memory-system` the pos-v2 component) — a model-managed key/value store that the API can read and write across conversations. Offered as a client-tool type in some configurations.

**Composes with pos-v2.** Potential shortcut for simple workspace memory needs, but pos-v2's `memory-system` is substantially richer (graphiti-based knowledge graph, entity+relationship extraction, deep personalisation per Idea 4). The Anthropic Memory API is a thin alternative; the pos-v2 memory-system is the durable answer for this workspace.

_Unclear from available sources as of 2026-04-23; flagged for Idea 1 Step 4 refresh._

_Sources (3.x): `https://platform.claude.com/docs/en/api/messages`, `https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching`, `https://platform.claude.com/docs/en/docs/build-with-claude/batch-processing`, `https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking` — all fetched 2026-04-23._

---

## 4. Model Context Protocol (MCP)

MCP is the open-source standard for connecting AI applications (clients like Claude Code, ChatGPT, Cursor, VS Code Copilot) to external systems (servers exposing tools, resources, prompts). From pos-v2's perspective: MCP is the external-integration surface that most plugins will lean on (per FUTURE_IDEAS.md Idea 3 introspection).

### 4.1 What MCP exposes

**Three server primitives:**
- **Tools** — callable actions the model can invoke (e.g. `search_issues`, `create_draft`). Appear in Claude as `mcp__<server>__<tool>` names.
- **Resources** — addressable read-only content the model can reference (e.g. document URIs).
- **Prompts** — parametrised prompt templates the user can invoke (surfaced as slash-command-like suggestions in some clients).

**Three transports:**
- **stdio** — local subprocess over stdin/stdout. Zero network; fastest.
- **HTTP (streamable-http)** — recommended for remote. Supports auth headers, Bearer tokens, OAuth 2.0.
- **SSE (Server-Sent Events)** — deprecated; HTTP preferred. Still supported for older servers.

**Lifecycle features:**
- `list_changed` notifications — server can push tool/prompt/resource list updates; Claude Code auto-refreshes without reconnect.
- Automatic reconnect (HTTP/SSE only) — exponential backoff, 5 attempts, starts at 1s. Stdio servers never auto-reconnect (they're local processes).
- **Channels** — MCP servers can push messages into the session so Claude reacts to external events (Telegram messages, CI results, Discord chats, webhooks). Enable with `--channels plugin:<name>@<marketplace>` at startup. Server declares `claude/channel` capability.

### 4.2 Composes with pos-v2

- **`telegram-interface`** is already wired as an MCP server that ships via the pos-v2 `plugin:telegram:telegram` namespace; its tools (`reply`, `edit_message`, `react`, `download_attachment`) appear to the primary persona as MCP tools. The channel capability is what lets a Telegram message arriving while pos-v2 is idle wake the session. This is the reference MCP composition inside pos-v2.
- **Any of the Idea 3 plugins** (communications, knowledge-management, project-management overlay, finance, creative, health, trading, legal) will almost certainly consume MCP. Gmail and Google Calendar already ship as MCP servers (`claude_ai_Gmail`, `claude_ai_Google_Calendar`) — the communications plugin is a workflow layer over them, not a reimplementation.
- **`memory-system`** could expose itself as an MCP server so non-Claude-Code clients (the eventual open-source distribution per Idea 12) can consume pos-v2 memory.
- **`safety-layer` + `reversibility-primitive`** compose with MCP via `PreToolUse` hook matchers on `mcp__<server>__.*` patterns — the safety gate can rule per-server or per-tool without the server having to cooperate.
- **`cost-governance`** consumes `MAX_MCP_OUTPUT_TOKENS` as a first-class ceiling. Default is 10000 (with a warning); large-context MCP tools (file-search, database queries) may need raising explicitly.

### 4.3 Scopes and configuration

| Scope | Loads in | Shared with team? | Stored in |
|-------|----------|-------------------|-----------|
| **Local** (default) | Current project only | No | `~/.claude.json` |
| **Project** | Current project only | Yes (checked into VCS) | `.mcp.json` in project root |
| **User** | All your projects | No | `~/.claude.json` |
| **Plugin** | When plugin enabled | Yes (ships with plugin) | `plugin/<name>/.mcp.json` or inline in `plugin.json` |

**CLI:**
```bash
claude mcp add --transport http <name> <url>                     # remote http
claude mcp add --transport stdio --env KEY=v <name> -- <cmd>    # local stdio
claude mcp list                                                  # list all
claude mcp get <name>                                            # details
claude mcp remove <name>                                         # remove
claude mcp reset-project-choices                                 # reset auth prompts
/mcp                                                             # status + OAuth
```

**Flag ordering matters:** options (`--transport`, `--env`, `--scope`, `--header`) must come **before** the server name; `--` then separates name from subprocess command. Misordering is a common bug.

### 4.4 Pitfalls

- **Project-scoped servers from `.mcp.json` prompt for approval** on every fresh clone — security-intentional, but surfaces as "why isn't the server loading?" Reset with `claude mcp reset-project-choices`.
- **Stdio servers do not auto-reconnect.** If the subprocess crashes, you must remove and re-add (or just restart Claude Code). Remote servers auto-reconnect up to 5 times.
- **Prompt injection risk** is the largest MCP pitfall: any MCP server that pulls external content (Slack, email, web fetch, issue trackers) is a potential injection vector. The safety warning in the Claude Code MCP docs is explicit — Anthropic has not verified third-party servers. pos-v2's `safety-layer` is the structural mitigation; it must be considered whenever a new MCP server is added.
- **`MAX_MCP_OUTPUT_TOKENS` default is 10000.** MCP tools returning more (e.g. database queries, large file reads) trigger a truncation warning. Set via env var.
- **Windows + npx stdio** requires `cmd /c` wrapper or "Connection closed" errors hit silently.
- **Scope confusion:** "local" MCP scope (in `~/.claude.json`) is different from "local settings" (`.claude/settings.local.json`). Two different files, two different concepts, both called "local."
- **Channel allowlist:** `--channels` only accepts servers on the approved allowlist unless `--dangerously-load-development-channels` is passed.
- **MCP tool matcher in hooks:** matcher strings are literal and regex-capable; use `mcp__<server>__.*` not `<server>/<tool>` style.

### 4.5 Authoring new MCP servers

Server SDKs exist for TypeScript, Python, Go, Rust, Java, C#, Swift, Kotlin (see `modelcontextprotocol.io`). Minimum shape: implement `list_tools`, `call_tool` for each tool; optionally `list_resources`, `read_resource`, `list_prompts`, `get_prompt`. Transport is a CLI choice — the SDK handles protocol framing.

pos-v2-local MCP servers (e.g. a future `pos-memory-mcp` exposing memory-system as a tool) should be stdio-transport + project scope + plugin-bundled — that composition gives zero-config activation for every clone and no network exposure.

### 4.6 End-user configuration surface

- `claude mcp add/list/remove`, `/mcp` inside a session.
- `.mcp.json` at project root (shared), `~/.claude.json` (user + local).
- `MCP_TIMEOUT` env var for server startup (default 30s?).
- `MAX_MCP_OUTPUT_TOKENS` env var for output cap.
- `--channels` flag for opting into push notifications.
- `--dangerously-load-development-channels` for unapproved channel sources.

_Sources (4.x): `https://code.claude.com/docs/en/mcp`, `https://modelcontextprotocol.io/docs` — fetched 2026-04-23._

---

## 5. Plugin system

Plugins are self-contained directories of components (skills, commands, agents, hooks, MCP servers, LSP servers, background monitors, binaries, default settings) that extend Claude Code with namespaced functionality. They are the distribution unit for the pos-v2 Idea 3 plugin suite.

### 5.1 Plugin structure

Every plugin has a manifest at `.claude-plugin/plugin.json`:

```json
{
  "name": "my-plugin",                // required; namespace prefix for skills
  "description": "...",               // required; shown in plugin manager
  "version": "1.0.0",                 // optional; git SHA used if omitted
  "author": { "name": "..." },        // optional
  "homepage": "...",                  // optional
  "repository": "...",                // optional
  "license": "..."                    // optional
}
```

**Directory layout** (all relative to plugin root, NOT inside `.claude-plugin/`):

| Directory / file | Purpose |
|------------------|---------|
| `.claude-plugin/plugin.json` | Manifest (only file that belongs inside `.claude-plugin/`) |
| `skills/<name>/SKILL.md` | Skills — auto-discovered; namespace `/plugin-name:skill-name` |
| `commands/<name>.md` | Legacy commands (same effect, no supporting files) |
| `agents/<name>.md` | Custom subagent definitions |
| `hooks/hooks.json` | Hook event handlers |
| `.mcp.json` | MCP server configurations |
| `.lsp.json` | LSP servers for code intelligence |
| `monitors/monitors.json` | Background monitors — each stdout line becomes a Claude notification |
| `bin/` | Executables added to Bash `PATH` while plugin is enabled |
| `settings.json` | Default settings (currently only `agent` and `subagentStatusLine` honoured) |

### 5.2 Plugin namespacing

Plugin skills / commands / MCP tools are namespaced as `<plugin-name>:<component>` — pos-v2's `telegram-interface` ships tools like `mcp__plugin_telegram_telegram__reply` and skills like `/telegram:configure`, `/telegram:access`. Namespacing prevents conflicts when multiple plugins are installed and is the mechanism by which the plugin marketplace can safely host arbitrary user content.

Plugin skills **cannot conflict** with project/user/enterprise skills because of namespacing. Project-scoped skills (in `.claude/skills/`) are unnamespaced (`/hello`); plugin skills are always namespaced (`/my-plugin:hello`).

### 5.3 Marketplaces

Plugin marketplaces are the distribution layer. A marketplace is a git repo or HTTP-served manifest listing plugins. Claude Code users add marketplaces via `claude plugin marketplace add <source>`; once added, users install individual plugins via `/plugin install <name>@<marketplace>` or `claude plugin install <name>@<marketplace>`.

**Marketplace configuration in settings.json:**
```json
{
  "enabledPlugins": {
    "formatter@acme-tools": true,
    "deployer@acme-tools": false
  },
  "extraKnownMarketplaces": {
    "acme-tools": { "source": { "source": "github", "repo": "acme-corp/claude-plugins" } }
  },
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme-corp/approved-plugins" }
  ]
}
```

The official Anthropic marketplace accepts submissions via `claude.ai/settings/plugins/submit` or `platform.claude.com/plugins/submit`.

### 5.4 Composes with pos-v2

- **`telegram-interface` is already a plugin** (`plugin:telegram:telegram` namespace visible in the MCP tool names). The telegram-interface + telegram-interface-framework-integration work is the reference implementation for how pos-v2 ships a plugin.
- **`workspace-bootstrap`** and **`hands-off-lifecycle`** together form the native foundational layer that every pos-v2 plugin is supposed to compose on. Idea 3 names these plugins as must-have-at-launch candidates, with dev/SDLC plugin as the first.
- **Plugin monitors (`monitors/monitors.json`)** are exactly the shape STATE.md rule 7 background-work-awareness demands — a tail command becomes in-context notifications without pos-v2 reinventing the surface. `observability-aggregator` and `session-resilient-orchestrator` could emit to monitor-shaped outputs that a pos-v2 plugin picks up.
- **Plugin `bin/` directory** is the distribution mechanism for pos-v2 CLI tools — `tools/pos-amend/` currently ships via the repo root; a future "pos-v2 dev/SDLC plugin" (Idea 3) could ship `pos-amend` as `bin/pos-amend` and get automatic PATH inclusion.
- **Plugin `settings.json` with `agent`** is the mechanism for shipping an entire custom primary persona as a plugin — a "code-reviewer persona" or "research-assistant persona" plugin becomes a one-toggle override of the default agent.
- **Workspace-specific pos-v2 compositions** (e.g. a workspace that wants a canned `/pos:context-load` skill for Idea 8's gate) become plugins once they stabilise; before then they live unnamespaced in `.claude/skills/`.

### 5.5 Lifecycle

1. **Install**: `/plugin install <name>@<marketplace>` or programmatic via SDK `plugins` option.
2. **Enable/disable**: `enabledPlugins` in settings.json, or `/plugin` interactive manager.
3. **Reload without restart**: `/reload-plugins` picks up skill, agent, hook, MCP, and LSP updates mid-session.
4. **Update**: re-install pulls latest version per marketplace manifest; explicit `version` field in plugin.json gates updates, otherwise every commit SHA counts as new.
5. **Uninstall**: `/plugin uninstall <name>@<marketplace>` or remove from `enabledPlugins`.

### 5.6 Testing and development

- **`--plugin-dir ./path`** loads a plugin from disk without marketplace install; the flag can be repeated for multiple plugins.
- Local `--plugin-dir` plugin **overrides** an installed marketplace plugin of the same name (except managed-force-enabled plugins).
- `/reload-plugins` picks up file changes.
- `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` are available inside plugin configs — the latter is the persistent data directory that survives updates.

### 5.7 Pitfalls

- **Common mistake:** putting `commands/`, `agents/`, `skills/`, `hooks/` inside `.claude-plugin/` — they must be at the plugin root, only `plugin.json` lives inside `.claude-plugin/`.
- **No version field = every git SHA is a new version.** Users get churny update prompts. Set `version` explicitly for stable plugins.
- **Plugin MCP servers** appear in `/mcp` alongside user-configured servers and inherit the prompt-injection risk (§4.4) — do not ship plugins that pull untrusted external content without documenting the risk.
- **Managed-force-enabled plugins** cannot be overridden by local `--plugin-dir`; contradicts the "local wins" assumption.
- **`strictKnownMarketplaces`** restricts which marketplaces can be added at all — silently blocks user self-installs on locked-down workspaces.
- **Hooks in plugin `hooks/hooks.json`** use the same schema as settings.json hooks; the command receives JSON on stdin and must `jq` out the fields it needs.
- Plugins loaded via `--plugin-dir` during testing do not persist across sessions — add to marketplace or `enabledPlugins` for durable install.

### 5.8 End-user configuration surface

- `/plugin` (interactive manager), `claude plugin install/uninstall/marketplace add`.
- `enabledPlugins`, `extraKnownMarketplaces`, `strictKnownMarketplaces` in settings.json.
- `--plugin-dir <path>` CLI flag (repeatable).
- `/reload-plugins` slash command.

_Sources (5.x): `https://code.claude.com/docs/en/plugins`, `https://code.claude.com/docs/en/plugins-reference` — fetched 2026-04-23._

---

## 6. Skills

Skills are the primary authoring surface for user-facing pos-v2 functionality that feels like a slash command. Since the slash-commands-merged-into-skills change, skills subsume most of what custom commands used to do and add directory-supporting-files, invocation control, subagent-forking, and dynamic context injection. The broad slash-command mechanics are in §1.1; this section collects the Skills-specific design patterns relevant to pos-v2.

### 6.1 Skill invocation modes (from pos-v2's perspective)

| Invocation shape | pos-v2 analogue |
|------------------|------------------|
| User types `/skill-name` explicitly | The deterministic, user-controlled dispatch. Safe default for side-effecting skills. |
| Claude auto-invokes when description matches | Useful for reference-shaped skills (conventions, style guides, internal API docs) and read-only research skills. |
| `disable-model-invocation: true` | Required for any skill with side effects — deploy, commit, amend, send email. Mirrors pos-v2's safety-layer posture. |
| `user-invocable: false` | Background knowledge the persona needs but the user would never invoke directly. E.g. a "how ODD is structured" skill that Claude loads when relevant but the user never types `/`. |

### 6.2 Skill composition patterns

**Reference-style skills.** Static conventions / style guides / domain knowledge. Short, always-loadable. Example: a `pos-v2-odd-conventions` skill that carries the ODD methodology primer — loadable any time Claude sees an ODD-shaped task. Composes naturally with FUTURE_IDEAS.md Idea 6 (ODD as default framing) — the persona pulls the skill when it needs to think about an objective but doesn't have the full methodology in context.

**Task-style skills.** Explicit procedure with side effects. Usually `disable-model-invocation: true`. Example: `/pos-amend:apply` that wraps the `pos-amend` CLI. Runs when the user types it, never auto-loads.

**Forked-context skills (`context: fork`).** Run in an isolated subagent with its own context; receive the skill body as the task prompt. Good for research-shaped work that shouldn't contaminate the main conversation. Example: a `deep-research` skill forked into the `Explore` agent that scans a topic and returns a summary. Maps to the Agent-tool dispatch pattern but with a skill manifest as the entrypoint.

**Dynamic-context skills.** Inline `` !`command` `` blocks run before the prompt is sent to Claude — the command's stdout replaces the placeholder. Not Claude executing; preprocessing. Example: a `pr-summary` skill that runs `gh pr diff` + `gh pr view --comments` + `gh pr diff --name-only` and stuffs the results into Claude's prompt. Replaces the "Claude, fetch the PR then summarise" two-turn pattern with a one-turn pattern.

### 6.3 Skill lifecycle inside a conversation

- Skill content enters the conversation as a single message when invoked.
- Content persists for the rest of the session — Claude Code does not re-read the file on subsequent turns.
- Auto-compaction carries recent skill invocations forward (first 5000 tokens per skill, 25000 tokens combined budget, most-recently-invoked wins).
- **Consequence:** write skill bodies as standing instructions for the whole task, not as one-off steps.
- If a skill seems to "stop working," the content is usually still present — Claude is choosing other approaches. Strengthen description/instructions or move enforcement to hooks.

### 6.4 Composes with pos-v2

- **Bundled skills in Claude Code** (`/simplify`, `/debug`, `/loop`, `/claude-api`, `/batch`, `/review`, `/security-review`, `/init`, `/schedule`, `/keybindings-help`, `/update-config`, `/fewer-permission-prompts`) are immediately available to any pos-v2 session with no authoring cost. FUTURE_IDEAS.md Idea 1 Step 1 noted `/loop` specifically as composing with scope-of-work activation cycles; `/schedule` is the natural composition for the Step 4 refresh job that updates this file.
- **pos-v2's telegram plugin** ships `/telegram:configure` and `/telegram:access` skills — reference pattern for any future pos-v2 plugin's user-facing surface.
- **A `.claude/skills/pos-context-load/SKILL.md`** is a plausible implementation of Idea 8 (structural context-load gate) at the skill layer — the persona invokes it before planning, the skill enumerates the design docs that must be loaded, the skill body fails if any are missing. Mechanical enforcement without inventing new pos-v2 machinery.
- **Reference-style skills for each sealed component** could surface the component's seal notes + amendment history the moment the persona touches that component — latent composition with the "component-scoped work reads that component's artefacts" session-start discipline (CLAUDE.md).
- **`$ARGUMENTS` + `paths` glob trigger** lets a skill auto-activate only for specific file patterns, reducing false-positive auto-loads for skills that only matter inside one component's tree.

### 6.5 Pitfalls specific to skills

- **Description truncation** at 1536 chars per-entry (shared across `description` and `when_to_use`). Front-load the key-use-case phrase.
- **Reference-style skill with no task** behaves like a no-op when `context: fork` is set — the subagent receives the guidelines but no actionable prompt.
- **Live-reload directories** are watched only if they existed at session start. Creating `~/.claude/skills/` during a live session requires restart.
- **Managed `disableSkillShellExecution: true`** disables `` !`command` `` blocks org-wide; dynamic-context skills degrade to "shell command execution disabled by policy."
- **"Ultrathink" in a skill body enables extended thinking** for that skill's turn — subtle feature, easy to forget; can bill unexpectedly.
- **Precedence order is enterprise > personal > project**, so a personal skill can silently override a project one with the same unnamespaced name; namespace plugin skills to avoid.

### 6.6 End-user configuration surface

- Skill files: `.claude/skills/<name>/SKILL.md` (project), `~/.claude/skills/<name>/SKILL.md` (personal), `<plugin>/skills/` (plugin).
- Enterprise managed skills: managed-settings-controlled.
- `disableSkillShellExecution: true` setting to kill `` !`command` `` preprocessing.
- `Skill(name)` / `Skill(name *)` permission rules.
- `/reload-plugins` for plugin skills, live-reload for filesystem skills.

_Sources (6.x): same as §1.1 — `https://code.claude.com/docs/en/slash-commands` (fetched 2026-04-23)._

---

## 7. Agent tool and subagents

The Agent tool (renamed from Task tool in Claude Code 2.1.63; `Task(...)` still works as alias) is Claude Code's dispatch primitive for delegating work to a subagent. A subagent runs in its own context window with a custom system prompt, tool restrictions, permissions, optional MCP servers, optional hooks, optional preloaded skills, optional persistent memory, and optional worktree isolation. This is the mechanism pos-v2 leans on most heavily during the rebuild — every component's build was dispatched through an Agent invocation.

### 7.1 Built-in subagent types

| Agent | Model | Tools | Use case |
|-------|-------|-------|----------|
| `general-purpose` | Inherits main | All tools | Multi-step tasks, exploration + modification, default choice |
| `Explore` | Inherits main | Read-only | Codebase research, fast exploration |
| `Plan` | Inherits main | Read-only | Plan mode research; cannot spawn other subagents |
| `Bash` | Haiku (cheaper) | Bash + Read | Shell-heavy tasks where a small model is fine |
| `statusline-setup` | Sonnet | scoped | Invoked automatically by `/statusline` |
| `Claude Code Guide` | Haiku | scoped | Used when user asks questions about Claude Code features |

### 7.2 Scope precedence for custom subagents

Same precedence pattern as other Claude Code components:

| Location | Scope | Priority |
|----------|-------|---------:|
| Managed settings `.claude/agents/` | Organization | 1 (highest) |
| `--agents` CLI flag (JSON) | Session | 2 |
| `.claude/agents/` | Project | 3 |
| `~/.claude/agents/` | User | 4 |
| Plugin `agents/` | Where plugin enabled | 5 (lowest) |

### 7.3 Subagent frontmatter fields

| Field | Description |
|-------|-------------|
| `name` (req) | lowercase-hyphen identifier |
| `description` (req) | When Claude should delegate |
| `tools` | Allowlist; inherits all if omitted. `Agent(worker, researcher)` restricts which agents can be spawned |
| `disallowedTools` | Denylist; applied before `tools` |
| `model` | `sonnet` / `opus` / `haiku` / full ID / `inherit` (default) |
| `permissionMode` | `default` / `acceptEdits` / `auto` / `dontAsk` / `bypassPermissions` / `plan` |
| `maxTurns` | Turn cap |
| `skills` | Skills preloaded into subagent context at startup (full content, not just description) |
| `mcpServers` | Inline MCP server defs or references to already-configured servers |
| `hooks` | Lifecycle hooks scoped to this subagent |
| `memory` | `user` / `project` / `local` — persistent MEMORY.md dir |
| `background` | `true` = always runs as background task |
| `effort` | `low` / `medium` / `high` / `xhigh` / `max` |
| `isolation` | `worktree` = temporary git worktree copy |
| `color` | Display colour in UI |
| `initialPrompt` | Auto-submitted first user turn (when agent is main thread) |

### 7.4 Isolation modes

- **Default (no isolation).** Subagent starts in main conversation's cwd. `cd` in Bash tool calls inside the subagent does not persist between tool calls and does not affect the main conversation's cwd.
- **`isolation: worktree`.** Subagent gets a temporary git worktree; cleaned up automatically if subagent makes no changes. Enables safe parallel-work patterns.
- **`context: fork` via skill.** Alternative entrypoint — a skill with `context: fork` runs its body as the task in a fresh subagent of the named `agent` type. Inverse of `skills:` preloading (skill → agent vs agent ← skills).

### 7.5 Composes with pos-v2

- **Every component seal in pos-v2 was dispatched through the Agent tool.** The handoff-brief-then-dispatch pattern documented in STATE.md rule 1 is literally Agent(general-purpose) invocations with scoped briefs. Custom subagents would formalise this — e.g. a `.claude/agents/pos-v2-component-builder.md` that ships with the right defaults (permissionMode, skills preload for ODD methodology, persistent memory scoped to the component tree).
- **`Explore` is the right default for research-plan authoring** — read-only scope matches the "read before editing" session-start discipline in CLAUDE.md.
- **`Plan` subagent** is invoked during plan mode; pos-v2's plan-before-code CDC (see MEMORY.md) is the workflow layer above this — Plan handles the research, the output lands at `docs/rebuild/plans/<name>.md`.
- **Persistent `memory: project`** on a pos-v2-specific agent would accumulate architectural insights across component builds, compose with `memory-system` at the workspace layer but scoped per-agent. Candidate for the future Dev/SDLC plugin (Idea 3).
- **`Agent(worker, researcher)` restriction** in an agent with its own `tools` list implements "this orchestrator can dispatch only these two subagents" — structural enforcement matching pos-v2's safety posture.
- **Subagent hooks** (`hooks:` in frontmatter) are the pattern for the "agent dispatches carry scope only" discipline (feedback_agent_prompts_scope_only in MEMORY.md). A future `pos-v2-builder` subagent could have a `PreToolUse` hook that refuses method-prescribing prompts — structural mechanisation of the current social convention.
- **`background: true`** composes with STATE.md rule 7 — long-running research agents run in background, the primary persona remains interactive and polls / monitors.

### 7.6 Agent teams (distinct from subagents)

Agent teams are multiple agents in parallel across separate sessions that can communicate. Subagents are single-session delegation. Agent teams are the right primitive for "I want three researchers investigating three topics simultaneously"; subagents are the right primitive for "run one focused scope and return a summary." Agent teams surface teammate-idle and teammate-display configuration. Beyond scope for most pos-v2 work today; relevant if Idea 3's plugin suite grows parallel-research patterns.

### 7.7 Pitfalls

- **Subagents cannot spawn other subagents.** The `Plan` agent exists because plan mode needs research but must not recurse infinitely. Custom agents inherit this limit.
- **Parent `bypassPermissions` / `acceptEdits` / `auto` take precedence** and cannot be overridden by subagent `permissionMode`.
- **Subagents don't inherit skills from parent conversation.** Must list them explicitly in `skills:`. `disable-model-invocation: true` skills cannot be preloaded (same pool as invocable skills).
- **Subagent gets only the system prompt** (plus cwd + basic env). Not the full Claude Code system prompt. Agent authors who assume the full harness's tool-use guidance is present will be surprised.
- **Plugin subagents do not support `hooks`, `mcpServers`, or `permissionMode`** — those fields are silently ignored in plugin agents. Copy the agent file into `.claude/agents/` or `~/.claude/agents/` to use them.
- **`Agent(agent_type)` restriction has no effect in subagent definitions** (subagents can't spawn anyway); only meaningful on main-thread agents.
- **`--disallowedTools "Agent(Explore)"`** or `permissions.deny: ["Agent(name)"]` is how you block a built-in agent; same syntax for custom.
- **Memory directory `MEMORY.md` is auto-truncated to first 200 lines or 25KB** at subagent system-prompt-time; agent is instructed to curate. Uncurated memory leads to loss.
- **`--agent` makes an agent file the main thread** (with `initialPrompt`, top-level `agent` setting in settings.json possible) — this is how plugins ship custom primary personas.

### 7.8 End-user configuration surface

- `/agents` (TUI), `claude agents` (CLI list), `--agents` JSON flag, `--agent <name>` (main-thread override), `--disallowedTools "Agent(name)"`.
- Files: `.claude/agents/<name>.md`, `~/.claude/agents/<name>.md`, plugin `agents/<name>.md`.
- Settings: `agent` key for main-thread agent override; `permissions.deny: ["Agent(name)"]` for denylist.
- Env: `CLAUDE_CODE_SUBAGENT_MODEL` globally overrides subagent model.

_Sources (7.x): `https://code.claude.com/docs/en/sub-agents` — fetched 2026-04-23._

---

## 8. Background-task primitives

pOS v2 treats "the primary persona never loses track of background work" as a foundational rule (STATE.md rule 7). Claude Code ships several primitives that compose with that rule without pos-v2 re-inventing them.

### 8.1 Bash `run_in_background: true`

**What it does.** The Bash tool accepts `run_in_background: true` for commands the agent does not want to block on. Output is captured; the session remains interactive. `/tasks` (alias `/bashes`) lists and manages active background bashes. Background commands have their own task lifecycle events (`TaskCreated`, `TaskCompleted`).

**Composes with pos-v2.**
- `session-resilient-orchestrator` already spawns long-running Python workers outside Claude Code entirely. Where work is short enough to stay inside Claude Code (e.g. a test suite, a scan, a compile), `run_in_background` is the right primitive — avoids blocking the persona while work completes.
- `hands-off-lifecycle`'s first-run shim detaches to a separate process; `run_in_background` is the in-Claude-Code equivalent when detach-from-Claude isn't required.

**Pitfalls.** Background bash tasks still consume Claude Code memory for buffered output. A very-long-running task with heavy stdout bloats the session. Pair with `Monitor` (see below) for streaming consumption.

### 8.2 Monitor tool

**What it does.** Watch a background script and react to each stdout line as an event. Agent SDK ships `Monitor` as a built-in tool (§2.2). The monitor pattern: start a process (`tail -F`, a websocket reader, a long-poll), each line delivered as a notification Claude can respond to.

**Composes with pos-v2.**
- **This is the primary tool for STATE.md rule 7 (background-work awareness).** Today `observability-aggregator` consumes process stdout via its own polling loop; `Monitor` converts each line into an in-session event with no polling. The primary persona becomes event-driven rather than poll-driven for background work.
- Plugin `monitors/monitors.json` (§5.1) is the plugin-level packaging of the same primitive — a plugin can declare "watch this log" and every plugin user gets it wired automatically.
- `self-correction-loop` consumes failure events from background processes the moment they arrive.

**Pitfalls.** High-volume lines can flood the session. Filter at the command level (`grep`, `tail -n 0`) not inside Claude. Monitors declared in plugin `monitors/monitors.json` start automatically when the plugin is active — no user action required — which can surprise users who don't expect a plugin to spawn processes at session start.

### 8.3 `/loop` bundled skill

**What it does.** `/loop [interval] [prompt]` re-runs a prompt repeatedly inside the current session. With interval: fixed cadence (e.g. `/loop 5m check if deploy finished`). Without interval: Claude self-paces. Without prompt: uses `.claude/loop.md` if present, else an autonomous maintenance check. Alias: `/proactive`.

**Composes with pos-v2.**
- FUTURE_IDEAS.md Idea 1 Step 1 named `/loop` specifically: "composes with scope-of-work activation cycles." A scope that wants periodic check-in (is the memory-system entity-extraction backlog draining? are any background workers stuck?) becomes `/loop <interval> <check>` instead of reimplementing the cadence in pos-v2 Python.
- Persistent daily refresh of `CLAUDE_CAPABILITIES.md` (Idea 1 Step 4) could be authored as `.claude/loop.md` — the primary persona re-checks and amends this file when the loop fires. Alternative to `/schedule` (below) for session-local use.

**Pitfalls.** Loop runs inside a live session — consumes context and bills each iteration. For long-horizon recurring work (daily, cross-session), `/schedule` is the right primitive; `/loop` is for same-session cadence.

### 8.4 `/schedule` bundled skill

**What it does.** `/schedule [description]` creates, updates, lists, or runs **routines** — scheduled Claude Code runs on cron or one-time at a specific time. Routines run as remote agents; web sessions pulled back with `/teleport`. Alias: `/routines`.

**Composes with pos-v2.**
- **Idea 1 Step 4 (capability-map refresh automation) maps directly onto `/schedule`** — a daily routine that re-fetches Claude docs and amends this file. Replaces building cron infra from scratch in pos-v2.
- Any pos-v2 scope with a "check every N hours" cadence (scheduled backlog drains, digest generation, alert summarisation) is a routine candidate.
- Composes with `cost-governance` — routines respect session-level cost ceilings; if a refresh would push spend over the cap, it defers (per Idea 1 Step 4's explicit design).

**Pitfalls.**
- Requires GitHub connection via `/web-setup` if the routine runs via web session.
- One-time routines (`run this once at 3pm`) and recurring routines are both `/schedule` — distinction is in the prompt body.
- Routines run in a separate session, not the current one. Results are viewed via `/schedule` listing or pulled via `/teleport`. If the user wants results in-line, `/loop` is better.

### 8.5 Task events and `TaskStop` tool

**What it does.** `TaskCreated` and `TaskCompleted` hook events fire around background task creation / completion (§1.2). The deferred `TaskStop` tool (surfaced to this doc-authoring session) lets an agent stop an active background task. `PreToolUse` on `TaskCreate` can block creation (exit 2 rolls back); `PostToolUse`-equivalent on `TaskCompleted` with `decision: "block"` can prevent completion.

**Composes with pos-v2.**
- `safety-layer` + `reversibility-primitive` can attach `PreToolUse` matchers on `TaskCreate` — a background task that would violate a safety invariant is refused at creation, not after it has run.
- `cost-governance` attaches on `TaskCompleted` to record the spend of each background task.
- `self-correction-loop` consumes `TaskCompleted` to detect completed-but-failed background scopes and trigger the correction arc.

### 8.6 `/tasks` and observability

`/tasks` (alias `/bashes`) lists active background bashes in-session. `/usage` (alias `/cost`, `/stats`) shows session cost; `/insights` generates an analysis report over recent sessions; `/recap` emits a one-line session summary on demand (automatic recap appears after idle time). These are the primary persona's introspection surface.

### 8.7 Pitfalls

- `/loop` and `/schedule` both require clear descriptions; an underspecified prompt ("check if things are OK") will self-define what "OK" means every iteration. Bind tightly.
- Routines run outside the current session — no cached context, no working-directory assumption unless set via routine config. The routine prompt must be self-contained.
- Plugin-shipped monitors (§5.1) have access to the plugin-declared environment but not necessarily the user's full env — workspace-sensitive monitors need explicit env-passing in `monitors.json`.
- Background bash buffered output can silently OOM in pathological cases; cap with `head`, `tail -F`, or `grep` at the shell layer.

### 8.8 End-user configuration surface

- `/loop`, `/schedule`, `/tasks`, `/bashes`, `/insights`, `/recap`, `/usage` — in-session slash commands.
- `.claude/loop.md` — default loop prompt.
- Plugin `monitors/monitors.json` — packaged watchers.
- `Bash.run_in_background: true` — one-off async exec.
- Agent SDK `Monitor` tool — programmatic per-line event consumption.
- Hooks on `TaskCreated` / `TaskCompleted` / `PreToolUse` for `TaskCreate` — structural gates.

_Sources (8.x): `https://code.claude.com/docs/en/commands`, `https://code.claude.com/docs/en/hooks`, `https://code.claude.com/docs/en/plugins-reference` (monitors section), Agent SDK overview — all fetched 2026-04-23._

---

## 9. Session persistence

Session persistence is the substrate everything else composes on: without it, pOS v2's background-work awareness, session-resilient orchestration, and cross-session memory have nothing to attach to. §1.5 covers the CLI-level mechanics; this section collects the pos-v2-relevant details with additional features (checkpointing, rewinding, recap, remote-control, web-session teleport) that constitute the full persistence surface.

### 9.1 On-disk session artefacts

- Every interactive session has a UUID session ID, stored alongside a JSONL transcript on disk.
- Retention governed by `cleanupPeriodDays` setting (default 30).
- Hook events receive `transcript_path` for offline inspection.
- `--no-session-persistence` (print mode only) skips disk write entirely — useful for scripted calls that shouldn't leave a trail.
- Sessions may be **named** (`-n <name>`, `/rename`, `--remote-control-session-name-prefix`) for human-friendly resumption.

**Composes with pos-v2.**
- `observability-aggregator` harvests the transcript_path artefacts for cross-session analysis.
- Long-term audit retention beyond `cleanupPeriodDays` needs explicit harvesting to a durable store — pos-v2 should capture transcripts that back amendments into the observability store before cleanup fires.
- `session-resilient-orchestrator` correlates orchestrator-spawned sessions with their transcripts via explicit `--session-id` UUIDs.

### 9.2 Resume / continue / fork

- `claude -c` / `--continue` — load most recent conversation in cwd. Includes sessions that added cwd via `/add-dir`.
- `claude -r <id|name>` / `--resume` / `/resume` / `/continue` — resume specific session; shows interactive picker without arg.
- `claude --fork-session --resume <id>` — create new session ID from resumed session; both diverge.
- `claude --from-pr <N>` — resume sessions linked to a GitHub PR (auto-linked at `gh pr create`).

**Composes with pos-v2.** Amendment-cycle bookkeeping (`tools/pos-amend/`) could attach to session IDs so every amendment-commit has a traceable session-of-record; `--from-pr` is the GitHub-integrated version if amendments flow through PRs.

### 9.3 Checkpointing and rewinding

`/rewind` (alias `/checkpoint`, `/undo`) rewinds the conversation and/or code to a previous point, or summarises from a selected message.

**Composes with pos-v2.**
- `reversibility-primitive` composes naturally with `/rewind` — the primitive provides structural undo for actions; `/rewind` provides conversational undo for Claude Code's own state. Together they bracket "the system can go back" across the two relevant layers.
- `self-correction-loop` could trigger a rewind when a scope failed in a way that compromises subsequent turns — clean restart to a known-good state.

**Pitfalls.** `/rewind` affects both conversation and code (git working tree). Does not compose with background bashes that have side-effected outside the working tree (database writes, HTTP calls). `reversibility-primitive` is the broader surface for that.

### 9.4 Context management

- **`/compact [instructions]`** — free up context via summarisation. Optional instructions focus the summary.
- **`/context`** — visualises current context usage as a coloured grid; shows optimisation suggestions.
- **Auto-compaction** — triggers when context fills. Skills carry forward per §6.3.
- **`PreCompact` / `PostCompact` hooks** — structural gates around compaction (§1.2).

**Composes with pos-v2.**
- `cost-governance` can attach to `PreCompact` to record spend-so-far before context is summarised and the usage accounting resets.
- Long-running pos-v2 sessions with heavy context (the component rebuild is this shape) should set explicit compact points via `/compact` with focus instructions to preserve the bits that matter to the current component's build.

### 9.5 Recap and insights

- `/recap` — one-line session summary on demand. Automatic recap appears after idle time.
- `/insights` — report across recent sessions: project areas, interaction patterns, friction points.
- `/team-onboarding` — generate a teammate-onboarding guide from 30-day session history.

**Composes with pos-v2.** These surface ambient session data that pos-v2 primitives (primary-persona, memory-system, observability) can consume without per-session instrumentation. `/insights` is a cheap substitute for bespoke analysis during the early pos-v2 evaluation-workspace phase.

### 9.6 Remote control and web sessions

- `claude remote-control` / `claude -rc` — start a Remote Control server; claude.ai or Claude app can drive the local session.
- `claude --remote <task>` — create a new web session on claude.ai. No local session.
- `claude --teleport` / `/teleport` (alias `/tp`) — pull a web session into the local terminal.
- `claude --from-pr <N>` — resume via PR linkage.

**Composes with pos-v2.**
- Mobile-equivalent interaction for pOS v2 users who don't live in a terminal. Telegram channel (Idea 3's communications-plugin-ish shape) is the other mobile interface; web sessions are complementary.
- **Not a safe surface for autonomous pos-v2 dispatch** — remote-control exposes the session to an external client; the `safety-layer` and `cost-governance` invariants must still hold. Managed settings should gate whether remote control is available in a given workspace.

### 9.7 Pitfalls

- `cleanupPeriodDays` default is 30. Long-term audit or research artefacts need explicit harvesting before cleanup.
- `--no-session-persistence` is silent — no warning in logs that the session is ephemeral.
- `/rewind` can undo work that Claude did in the current session, but not side effects outside the working tree or state held by background bashes.
- Web sessions (`--remote`, `/teleport`) require GitHub connection via `/web-setup`. First-time routine setup prompts automatically.
- Remote Control server runs on localhost by default; expose carefully if routing through tunnels.
- Resume with `-c` loads the most recent session *in the current directory*; a session that was in a sibling directory is invisible until `--resume` by ID.

### 9.8 End-user configuration surface

- CLI: `-c`, `-r`, `--resume`, `--fork-session`, `--session-id`, `--no-session-persistence`, `--from-pr`, `--remote`, `--teleport`, `remote-control`.
- Slash: `/resume`, `/continue`, `/rewind`, `/checkpoint`, `/undo`, `/compact`, `/context`, `/recap`, `/insights`, `/rename`, `/teleport`, `/remote-control`.
- Settings: `cleanupPeriodDays`.
- Hooks: `SessionStart`, `SessionEnd`, `PreCompact`, `PostCompact` — structural gates.

_Sources (9.x): `https://code.claude.com/docs/en/cli-reference`, `https://code.claude.com/docs/en/commands`, `https://code.claude.com/docs/en/hooks` — all fetched 2026-04-23._

---

## 10. Cross-capability notes

<!-- PLACEHOLDER -->

---

## Source log

Every non-trivial claim in this file is traceable to an entry below. URLs recorded with fetch date; claude-code-guide subagent dispatch count recorded at end.

- _(populated as sections land)_
