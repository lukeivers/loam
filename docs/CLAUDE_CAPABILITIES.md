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

<!-- PLACEHOLDER -->

---

## 3. Anthropic API (Messages + adjacent)

<!-- PLACEHOLDER -->

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
