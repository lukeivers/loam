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

<!-- PLACEHOLDER -->

---

## 5. Plugin system

<!-- PLACEHOLDER -->

---

## 6. Skills

<!-- PLACEHOLDER -->

---

## 7. Agent tool and subagents

<!-- PLACEHOLDER -->

---

## 8. Background-task primitives

<!-- PLACEHOLDER -->

---

## 9. Session persistence

<!-- PLACEHOLDER -->

---

## 10. Cross-capability notes

<!-- PLACEHOLDER -->

---

## Source log

Every non-trivial claim in this file is traceable to an entry below. URLs recorded with fetch date; claude-code-guide subagent dispatch count recorded at end.

- _(populated as sections land)_
