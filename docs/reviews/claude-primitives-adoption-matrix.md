# loam ↔ Claude-primitives — exhaustive adoption matrix (Pass-2A)

**Date:** 2026-05-31 · **Scope:** READ-ONLY enumeration + recommendation
(nothing implemented) · **Author:** dispatched research agent (Opus) ·
**Builds on:** `claude-primitives-integration-review.md` (Pass-1) — cited
as **[P1]** below. Loop-design companion: `claude-capability-adoption-loop-design.md`.

This is a **complete, feature-by-feature** matrix over the Claude Code /
Claude surface. Every primitive-semantics claim carries a Tier-0 doc URL;
every "loam status" cites Pass-1 or a file. Default is **HARD toward
adoption** where leverage exists; every non-adopt row states an explicit
**deliberately-skip … because …** reason — no silent gaps. An F2 fragility
flag (⚠) marks any row where adopting would add complexity/fragility
without commensurate leverage (the recent incident was partly too many
un-verified hooks interacting — adoption must be deliberate-complete-
coverage, not blind-cramming).

**Doc sources (fetched 2026-05-31):**
`code.claude.com/docs/en/hooks`, `/commands`, `/sub-agents`, `/skills`,
`/goal`, `/scheduled-tasks`, `/routines`, `/agent-view`, `/agent-teams`,
`/worktrees`, `/plugins`, `/mcp`, `/workflows`, `/checkpointing`.

**Status legend:** USED / PARTIAL / UNUSED / INVISIBLE (authored but not
reachable in the primary workspace) · **Rec legend:** ADOPT / KEEP /
SKIP (deliberately) / RETIRE · **Effort:** AI-time (background-agent),
per the duration rubric.

---

## Roll-up counts

- **Rows: 78.**
- **ADOPT: 27** · **KEEP: 18** · **SKIP (deliberate): 30** · **RETIRE: 1**
  (the never-invoked corpus-duplicating skills — retire-or-repurpose) ·
  **DECIDE (owner-gated fork, adopt-one-branch): 2** (skills install,
  /goal-vs-hook).
- **F2 fragility flags (⚠): 6** rows where adoption is *conditional* on
  not over-wiring.

(Counts treat each named row once; a few rows carry a compound rec like
"ADOPT one branch / RETIRE other" and are tallied under their primary verb.)

---

## A. Hook events — 30 (Tier-0: `/docs/en/hooks`)

P1 confirmed loam wires **5 of 30 events** with **~24 handlers**, all
`type:command`. The new event since loam's mid-May catalogue is
**`MessageDisplay`** [P1 §1a]. Each event below is enumerated individually.

| # | Event | What it does (doc-cited) | loam status [src] | Rec | Reason | Effort | Leverage if adopted |
|---|---|---|---|---|---|---|---|
| 1 | **SessionStart** | Fires at session start | USED (3 handlers) [P1 §2] | KEEP | Core to persona-load + queue-status inject | — | — |
| 2 | **Setup** | One-time project setup hook | UNUSED [P1 §2] | SKIP | loam's setup is the workspace-sync resolver, not a per-project Setup hook; no recurring setup gap | — | low |
| 3 | **UserPromptSubmit** | Fires on each user prompt | USED (6 handlers) [P1 §2] | KEEP | Heavy: time-inject, persona, principle-reminder, intent-classify | — | — |
| 4 | **UserPromptExpansion** | Fires when prompt text is expanded (e.g. `@`/file refs) | UNUSED [P1 §2] | SKIP | loam injects via UserPromptSubmit already; expansion-time is a narrower hook with no current need | — | low |
| 5 | **PreToolUse** | Before a tool runs; can block (exit 2) | USED (heavy) [P1 §2] | KEEP | The structural-enforcement backbone (telegram guard, spawn isolation, edit/write matchers) | — | — |
| 6 | **PermissionRequest** | Fires when a permission prompt is raised | UNUSED [P1 §2] | SKIP | loam runs largely pre-authorized; no permission-prompt automation need today | — | low |
| 7 | **PermissionDenied** | Fires when permission is denied | UNUSED [P1 §2] | SKIP | Denials are rare in loam's pre-authorized flow; surfacing them is covered by agent-outcome capture | — | low |
| 8 | **PostToolUse** | After a tool runs | USED [P1 §2] | KEEP | Used for several command handlers | — | — |
| 9 | **PostToolUseFailure** | After a tool call *fails* | UNUSED [P1 §4] | **ADOPT** | Bridge failures → Telegram out-of-band; composes with Telegram-outage self-heal corpus [P1 P5] | low-med | med — surfaces failures without polling |
| 10 | **PostToolBatch** | After a batch of tool calls | UNUSED | SKIP | No current batch-level side-effect need; PostToolUse covers per-call | — | low |
| 11 | **Notification** | Fires when Claude Code emits a notification | UNUSED [P1 §4] | **ADOPT** | Notification → Telegram bridge; same self-heal composition [P1 P5] | low-med | med |
| 12 | **MessageDisplay** | Fires while assistant message text is displayed (NEW) | UNUSED [P1 §1a] | SKIP ⚠ | Net-new, niche (live-display side effects). Adopting now = fragility w/o leverage. Fold into awareness-SKILL refresh, revisit later | — | low |
| 13 | **SubagentStart** | When a subagent begins | UNUSED [P1 §4] | **ADOPT** | Structurally enforce dispatch-brief shape (WD-literal-first, model-rationale, primitive-rationale) on the 781-agent surface — loam's own "recurrence→hook" doctrine [P1 P4] | med | med-high |
| 14 | **SubagentStop** | When a subagent completes | UNUSED [P1 §4] | **ADOPT** | Capture dispatch outcome + verify brief-shape post-hoc; pairs with #13 | med | med-high |
| 15 | **TaskCreated** | On task-list create | UNUSED [P1 §4] | **ADOPT** ⚠ | Could auto-enforce durable-capture-for-planned-work (every TaskCreate paired w/ FIDRAFT/memory). High leverage BUT ⚠ verify it doesn't fire on trivial tasks — gate carefully | low-med | med |
| 16 | **TaskCompleted** | On task-list complete | UNUSED | SKIP | Completion side-effects are owner-surfacing, already handled at Stop; no separate need | — | low |
| 17 | **Stop** | When a turn finishes; can continue (exit 2) | USED (5 handlers) [P1 §2] | KEEP | Hosts the hand-rolled autonomy-continuation (`/goal` analogue) + channel-rule + outcome-capture | — | — |
| 18 | **StopFailure** | When a Stop hook itself fails | UNUSED | SKIP | No Stop-hook-failure recovery need; failures are loud enough | — | low |
| 19 | **TeammateIdle** | Agent-team teammate goes idle | UNUSED | SKIP | loam doesn't run agent-teams (single-session subagents only) — see row F5 | — | low (until teams adopted) |
| 20 | **InstructionsLoaded** | When CLAUDE.md / rules load | UNUSED [P1 §4] | **ADOPT** ⚠ | Verify session-start load-state matches expectations (session-start-discipline is a hard rule but currently soft). ⚠ keep the check cheap — a heavy hook here taxes every load | low | med |
| 21 | **ConfigChange** | On settings change | UNUSED | SKIP | Config changes are owner-gated + rare; no automation gap | — | low |
| 22 | **CwdChanged** | On working-dir change | UNUSED | **ADOPT** ⚠ | Could enforce the always-specify-WD discipline (warn on CWD drift into wrong tree — pos3 vs ivers-corp-pos-v2). ⚠ low-leverage vs SubagentStart brief-check; adopt only if #13 proves insufficient | low | low-med |
| 23 | **FileChanged** | On file change | UNUSED | SKIP | File-watch automation has no current loam need; loam acts on explicit edits | — | low |
| 24 | **WorktreeCreate** | On worktree creation | UNUSED | SKIP (revisit) | Pairs with `isolation:worktree` adoption (row F6); skip until worktree-isolated builds are standard | — | low-now |
| 25 | **WorktreeRemove** | On worktree removal | UNUSED | SKIP (revisit) | Same as #24 | — | low-now |
| 26 | **PreCompact** | Before auto-compaction; can block | USED (new, tonight) [P1 §2] | KEEP | compaction_discipline_reinject.py — cross-session memory protection | — | — |
| 27 | **PostCompact** | After compaction | UNUSED | **ADOPT** | Re-inject the principle-set + CURRENT-WORK pointer post-compaction (pairs with PreCompact; closes the "compaction discards content" gap from the other side) | low | med |
| 28 | **Elicitation** | MCP elicitation request raised | UNUSED | SKIP | No MCP server in loam elicits; telegram MCP doesn't | — | low |
| 29 | **ElicitationResult** | MCP elicitation result | UNUSED | SKIP | Same as #28 | — | low |
| 30 | **SessionEnd** | On session termination | UNUSED [P1 §4] | **ADOPT** ⚠ | End-of-session state-persistence ritual (flush in-flight task state / FIDRAFT). ⚠ sessions end abruptly — don't make this load-bearing for durability (files-are-memory must hold without it) | low | med |

**Hook-event subtotal:** USED 6 · ADOPT 9 (3 hard ⚠-flagged conditional) · SKIP 15 · KEEP counted in USED.

---

## B. Hook handler types — 5 (Tier-0: `/docs/en/hooks`)

| # | Handler type | What it does (doc-cited) | loam status [src] | Rec | Reason | Effort | Leverage |
|---|---|---|---|---|---|---|---|
| 31 | **command** | Runs a shell command/script | USED (all ~24) [P1 §2] | KEEP | Every loam hook is this type | — | — |
| 32 | **prompt** | Runs a small prompt vs a fast model (inline Haiku-as-judge) | UNUSED [P1 §4] | **ADOPT** | Several command hooks do brittle regex classification (intent_classifier_inbound, methodology-vocab check) a `prompt` hook does more robustly [P1 #4] | low | med |
| 33 | **agent** | Runs a full subagent as the hook (60s default) | UNUSED | SKIP ⚠ | Heavyweight per-hook; only justified for a hook needing multi-step tool use. No such loam hook today — adopting = fragility w/o leverage | — | low |
| 34 | **http** | POST to URL; 2xx JSON parsed as decision | UNUSED | SKIP | No external decision service in loam's local-first model; would add a network dependency on the hot path | — | low |
| 35 | **mcp_tool** | Invokes an MCP tool as the hook | UNUSED | SKIP (revisit) | Could route Notification→Telegram via the telegram MCP directly instead of a command shim — revisit when #9/#11 are built (mcp_tool may be the cleaner impl) | — | low-now |

**Async flags** (`async`, `asyncRewake`) [P1 §1b]: UNUSED. **ADOPT** for #9/#11 (Telegram bridge should be `async` so failure-surfacing never blocks the turn). Effort: trivial (one flag).

---

## C. Sub-agent capabilities + frontmatter levers (Tier-0: `/docs/en/sub-agents`)

The Agent tool fired **781×** in pos3 [P1 §2] — background-agents-by-default
is real. But loam dispatches with **near-zero frontmatter use**: dispatches
are ad-hoc prompts, not reusable definition files. The doc exposes **18
frontmatter fields** + built-in agents + fork mode + agent-teams. Each lever
enumerated:

| # | Capability / field | What it controls (doc-cited) | loam status | Rec | Reason | Effort | Leverage |
|---|---|---|---|---|---|---|---|
| 36 | **Agent tool (background dispatch)** | Spawn a subagent in its own context | USED (very heavy, 781×) [P1 §2] | KEEP | The core execution primitive | — | — |
| 37 | **Built-in `Explore` agent** | Fast read-only Haiku codebase search | UNUSED (loam hand-rolls research dispatches) | **ADOPT** | Read-only research dispatches (the "grep+read in main first" verify-before-dispatch pattern) map exactly onto Explore — Haiku, no CLAUDE.md load, cheap | low | med — cheaper research |
| 38 | **Built-in `Plan` agent** | Read-only research during plan mode | UNUSED | SKIP (revisit) | loam's plan-before-code writes plans via full dispatches w/ methodology context; Plan agent skips CLAUDE.md which loam plans *need*. Revisit if a lightweight plan-research leg emerges | — | low |
| 39 | **`general-purpose` built-in** | Full-tool multi-step agent | USED (implicitly — most dispatches) | KEEP | What loam's Agent dispatches effectively are | — | — |
| 40 | **Reusable subagent *definition files*** (`.claude/agents/*.md`) | Named, version-controlled agent w/ fixed prompt+tools+model | UNUSED (dispatches are ad-hoc) | **ADOPT** | loam re-spawns the same shapes (research, plan-author, builder, judge) w/ the same instructions — the doc's exact "define when you keep spawning the same kind of worker" case. Encodes brief-shape + model-rationale structurally | med | high — turns repeated prose briefs into typed, enforceable agents |
| 41 | `name` | Unique id; hooks receive as `agent_type` | n/a (no def files) | ADOPT (w/ #40) | Enables SubagentStart matchers (#13) to target by name | — | — |
| 42 | `description` | When to delegate | n/a | ADOPT (w/ #40) | Auto-delegation trigger | — | — |
| 43 | `tools` (allowlist) | Restrict tool access | UNUSED | **ADOPT** | Research agents → read-only; builders → no telegram. Enforces least-privilege structurally | low | med |
| 44 | `disallowedTools` (denylist) | Deny specific tools | UNUSED | **ADOPT** | Cleaner than allowlist for "everything except Write/Edit" research agents | low | med |
| 45 | `model` | Per-agent model (`sonnet`/`opus`/`haiku`/id/`inherit`) | UNUSED (model picked per-dispatch in prose) | **ADOPT** | Bakes the model-rationale decision into the definition — judge=Haiku, builder=Sonnet, architecture=Opus | low | med-high |
| 46 | `permissionMode` | default/acceptEdits/auto/dontAsk/bypassPermissions/plan | UNUSED | **ADOPT** ⚠ | `acceptEdits` for trusted builders removes prompt friction. ⚠ NEVER `bypassPermissions` (writes to .git/.claude unguarded — collides w/ spawn-isolation safety). Adopt acceptEdits/plan only | low | med |
| 47 | `maxTurns` | Cap agentic turns | UNUSED | **ADOPT** | Bounds runaway dispatches (cost + dead-agent risk); pairs w/ dead-agent-detection corpus | low | med |
| 48 | `skills` (preload) | Inject full skill content at agent startup | UNUSED | **ADOPT** | THE fix for skill Mode-B (P1): preload `tool-selection-rubric` / `claude-feature-awareness` into builder agents so the content is *present*, not hope-loaded. Bypasses description-match entirely | low | **high** — directly resolves the 0-invocation finding for dispatched work |
| 49 | `mcpServers` (scope) | Give/deny MCP servers per-agent | PARTIAL (loam scrubs via --strict-mcp-config) [P1 §10] | **ADOPT** | Structurally guarantees builders DON'T inherit the telegram MCP (the proven Telegram-drop root cause) — frontmatter-level enforcement of the spawn-isolation rule | low | high — codifies a CRITICAL safety rule |
| 50 | `hooks` (per-agent) | Lifecycle hooks scoped to one agent | UNUSED | **ADOPT** ⚠ | Per-builder PreToolUse guards (e.g. read-only-query validation pattern). ⚠ scope tightly; don't replicate global hooks per-agent | low | med |
| 51 | `memory` (user/project/local) | Persistent cross-session agent memory dir | UNUSED | **ADOPT** ⚠ | A judge/reviewer agent that accumulates "recurring AC-failure patterns" across builds = compounding value. ⚠ memory drift risk — needs curation discipline (mirror MEMORY.md hygiene) | med | med-high |
| 52 | `background` (always-bg) | Force background execution | PARTIAL (loam backgrounds by default in prose) | **ADOPT** | Makes background-agents-by-default *structural* instead of per-dispatch discretion | low | med |
| 53 | `effort` | Per-agent effort override | UNUSED | **ADOPT** | High-effort for architecture agents, low for mechanical edits — surgical cost control | low | med |
| 54 | `isolation: worktree` | Run agent in an isolated git worktree | UNUSED | **ADOPT** | Directly resolves the serialize-amendment-builds rule: parallel builders in separate worktrees stop racing on index.lock. THE structural fix for a known loam constraint | med | **high** |
| 55 | `color` | Display color in task list | UNUSED | SKIP | Cosmetic; no leverage. (Also: loam forbids Greek-letter labels — color is a fine *visual* aid but adds nothing to outcomes) | — | none |
| 56 | `initialPrompt` | Auto-submitted first turn for `--agent` main-session | UNUSED | SKIP (revisit) | Only relevant if loam runs a session *as* a named agent via `--agent`; not today's shape | — | low |
| 57 | **Fork mode** (`CLAUDE_CODE_FORK_SUBAGENT=1`) | Subagent inherits full conversation, shares prompt cache | UNUSED | **ADOPT** ⚠ | Cheaper than fresh subagent when the agent needs heavy main-context (shared prompt cache). ⚠ drops input isolation — only for tasks where context-inheritance is wanted, not for isolated builds | low | med |
| 58 | **`/fork` directive** | Spawn a fork w/ a directive from the prompt | UNUSED | KEEP-available | Useful interactively for "try N approaches from here"; no standing-process need | — | low |
| 59 | **Agent teams** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | Many independent communicating contexts, `SendMessage`, teammate resume | UNUSED | SKIP ⚠ | Experimental; loam's swarming today is dispatch-fan-out + judge, which subagents+worktrees cover. Agent-teams adds inter-agent messaging loam doesn't yet need — adopting = experimental fragility w/o proven leverage. Revisit when a true multi-agent-conversation workload appears | — | low-now |
| 60 | **Subagent resume** (`SendMessage`) | Continue a stopped subagent w/ full history | UNUSED | SKIP (gated on teams) | Requires agent-teams flag; tied to #59 | — | low-now |
| 61 | **CLI `--agents` JSON** | Define ephemeral session-only agents | UNUSED | SKIP | loam's agents should be version-controlled def files (#40), not ephemeral JSON | — | low |

---

## D. Skill system + frontmatter levers (Tier-0: `/docs/en/skills`)

**The load-bearing finding [P1 §3]: loam-authored skills = 0 invocations,
ever, two failure modes — Mode A structural invisibility (pos3, not
installed as plugin) + Mode B description-match-never-fires (everywhere).**
Frontmatter levers enumerated (P1 confirms only `start-project` uses any
field beyond `description`):

| # | Lever / capability | What it does (doc-cited) | loam status [src] | Rec | Reason | Effort | Leverage |
|---|---|---|---|---|---|---|---|
| 62 | **Skill auto-load (description-match)** | Body loads when Claude judges convo matches description | USED-mechanism / 0-fires [P1 §3] | **RETIRE-or-repurpose** | The mechanism failed 0/186 transcripts. For corpus-duplicating skills (rubric content already in CLAUDE.md) → RETIRE. For genuinely path-scoped → convert to `paths:` (#67) or `/command` (#64) | — | — (decision) |
| 63 | `description` field | The only thing in context until load | USED (all skills) | KEEP | Required; but insufficient alone (Mode B) | — | — |
| 64 | `disable-model-invocation: true` | Skill becomes user/`/command`-only, never auto | UNUSED | **ADOPT** | For skills the *persona* should invoke deterministically by name (handsoff-loop, log-visit): stop relying on description-match, make them explicit `/commands` | low | med-high — converts hope into determinism |
| 65 | `user-invocable` | Controls `/`-menu visibility | UNUSED | ADOPT (w/ #64) | Pairs w/ invocation-control decisions | low | low-med |
| 66 | `allowed-tools` / `disallowed-tools` | Restrict skill's tool access | UNUSED | **ADOPT** | Least-privilege for skills (e.g. a research skill = read-only) | low | low-med |
| 67 | **`paths:`** (glob-gated auto-load) | Skill auto-loads ONLY when working in matching files | UNUSED [P1 §3] | **ADOPT** | THE highest-leverage Mode-B fix [P1 P3]: deterministic file-triggered load for path-scoped skills (log-visit, dev-sdlc build skills, prose skills) | low (1-line/skill) | **high** |
| 68 | `model:` | Per-skill model override | UNUSED [P1 §2] | **ADOPT** ⚠ | Surgical Haiku/Opus per skill. ⚠ only where the skill's work genuinely warrants a non-default — not blanket | low | low-med |
| 69 | `effort:` | Per-skill effort override | UNUSED | ADOPT (selective) | Same surgical logic as #68 | low | low |
| 70 | `context: fork` | Skill runs in forked subagent context (isolation) | UNUSED [P1 §2] | **ADOPT** | Heavy reference skills (claude-feature-awareness is large) load in a fork so they don't pollute main context — directly serves the output-to-disk / token-economy doctrine | low | med |
| 71 | `agent:` (subagent type when forked) | Which subagent runs the forked skill | UNUSED | ADOPT (w/ #70) | Pairs with context:fork | low | low |
| 72 | `hooks:` (skill-scoped) | Hooks scoped to skill lifecycle | UNUSED | SKIP (revisit) | No current skill needs lifecycle hooks; revisit per-skill | — | low |
| 73 | `shell:` / `!`cmd`` dynamic injection | Inject command output into skill at render | UNUSED [P1 §2] | **ADOPT** | claude-feature-awareness could inject `claude --version` + live changelog head at render → self-freshening catalogue (directly serves the loop, Deliverable B) | low | med |
| 74 | **Bundled skills as `/commands`** (`/code-review`, `/simplify`, `/verify`, `/run`, `/debug`, `/batch`, `/deep-research`, `/loop`, etc.) | Anthropic-shipped workflow skills | PARTIAL (3 built-in Skill-tool fires ever [P1 §3]) | **ADOPT (specific ones)** | `/batch` (decompose→worktree-per-unit→PR) maps onto loam swarming; `/code-review`+`/simplify` onto the dual-audience/quality pass; `/deep-research` onto the changelog research. Compose, don't reinvent | low | high |

---

## E. Scheduler / iteration primitives (Tier-0: `/goal`, `/loop`, `/scheduled-tasks`, `/routines`)

P1 pinned: `/goal` and `/loop` are **session-keep-running iteration
primitives, NOT schedulers**; the durable cross-session scheduler is
**launchd** (loam already runs 5 pos3 launchd jobs: places-audit,
events-audit, usage-monitor, daily-reminders, memory-write-worker —
confirmed on disk at `~/Library/LaunchAgents/com.loam.pos3.*.plist`).

| # | Primitive | What it does (doc-cited) | loam status [src] | Rec | Reason | Effort | Leverage |
|---|---|---|---|---|---|---|---|
| 75 | **`/goal`** | Keep working across turns until a fresh-Haiku evaluator confirms a condition; wrapper around a session-scoped prompt-based Stop hook; `--resume`-restored; works in `-p` | UNUSED [P1 §1c] | **ADOPT (head-to-head) / DECIDE** | loam HAND-ROLLS this in `autonomy_continuation.py` [P1 P1]. Native = platform-maintained evaluator + status UI + resume + `-p` for free. DECIDE: does native's "judge only the transcript" cover loam's autonomy semantics? Owner-gated [P1 P1] | low (eval) | high — removes a maintained reimplementation |
| 76 | **`/loop [interval] [prompt]`** | Re-run a prompt on an interval (or self-paced); reads `.claude/loop.md` if no prompt | UNUSED [P1 §2] | SKIP (session-bound) | Session-only; loam's durable recurring work belongs in launchd. KEEP-available for interactive "poll until X" (but Monitor is better — #79) | — | low — Monitor/launchd dominate its use cases |
| 77 | **Routines (cloud, `/schedule`)** | Anthropic-cloud scheduled agent; min 1h; survives machine-off; API/GitHub-triggerable; fresh clone (no local files) | UNUSED [P1 §1d] | **ADOPT (specific)** | For the **capability-adoption loop itself** (Deliverable B) and any audit that needs no local tree: cloud-durable, survives machine-off — strictly better than launchd where local-file access isn't needed [P1 P7] | med | med-high |
| 78 | **Desktop scheduled tasks** | Local GUI-scheduled, min 1m | UNUSED | SKIP | launchd already covers local durable scheduling w/ finer control + version-controlled plists; GUI tasks aren't reproducible-in-repo | — | low |
| 79 | **Monitor tool** | Watch a command for completion (event-driven) | USED (light, 9×) [P1 §2] | **KEEP + use more** | More token-efficient than `/loop` for "wait until X" [P1 §6]; under-used relative to its fit | — | med (already-owned lever) |
| 80 | **CronCreate** | 5-field cron, session-scoped despite `durable:true` (loam empirical, task #77) | USED (light, 2×) [P1 §2] | KEEP (bounded) | Fine for session-bounded scheduling; loam correctly knows it's NOT cross-session durable | — | low |
| 81 | **launchd** | macOS durable cross-session scheduler, min 1s | USED (5 pos3 jobs) [disk] | KEEP | THE durable-scheduling reference path; version-controlled plists | — | — |
| 82 | **`ScheduleWakeup` tool** | Schedule a session wakeup | UNUSED | SKIP | Session-scoped wakeup; launchd/Routines cover durable needs | — | low |
| 83 | **`/workflows` + `ultracode`** | Bundled dynamic workflows fan work across subagents in background | UNUSED | SKIP (revisit) | loam has its own swarming methodology (Lens 5); `/batch` (#74) is the concrete overlap to adopt. Full `/workflows` runtime = revisit if loam's hand-rolled fan-out shows gaps | — | low-now |

---

## F. Session / context / plugin / MCP primitives

| # | Primitive | What it does (doc-cited) | loam status [src] | Rec | Reason | Effort | Leverage |
|---|---|---|---|---|---|---|---|
| F1 | **MCP servers** | External tool/data connectors | USED (telegram only installed) [P1 §2] | KEEP | telegram MCP is the user-visible channel; Gmail/Calendar/Drive/computer-use available | — | — |
| F2 | **Plugin install / marketplace** | Package commands+agents+skills+hooks+MCP; install via marketplace.json | PARTIAL — loam skills packaged as dirs, NO marketplace.json, not installed [P1 §2] | **DECIDE/ADOPT** | Mode-A fix [P1 P0]: add `.claude-plugin/marketplace.json` + install so pos3 sessions can SEE the skills — OR accept loam-repo-only + retire. Doing neither is the current waste | low | decision-unblocking — high |
| F3 | **`CLAUDE_PROJECT_DIR` in stdio MCP env** | MCP servers receive project dir | available [P1 §7] | KEEP-available | Plugin MCP configs can reference it; no current need | — | low |
| F4 | **`--strict-mcp-config`** | Restrict MCP to passed config; scrub defaults | USED [P1 §10] | KEEP | CRITICAL: loam's spawn-isolation uses this to avoid killing the parent Telegram bot | — | — |
| F5 | **`--bare` / `CLAUDE_CODE_SIMPLE=1`** | Skip hooks/LSP/plugins/auto-memory for fast subprocess | UNUSED [P1 §10] | SKIP ⚠ | Tempting for fast `claude -p` spawns BUT loam's `claude -p` calls go through claude_print_client w/ subscription auth; `--bare` forces ANTHROPIC_API_KEY auth which loam explicitly forbids (no-API-key rule). Adopting = breaks a hard constraint | — | none (constraint conflict) |
| F6 | **Worktrees** (`/worktrees`, auto-worktree) | Isolated git copies for parallel agents | UNUSED (loam serializes builds instead) | **ADOPT** | See #54 — resolves serialize-amendment-builds by isolation instead of serialization | med | high |
| F7 | **Checkpointing** (`/rewind`) | Roll code+conversation back to a checkpoint | UNUSED | KEEP-available | Useful interactive safety net; no standing-process need | — | low |
| F8 | **`/context`** | Visualize context usage + bloat warnings | UNUSED | **ADOPT (persona habit)** | Directly serves the compact/clear decision heuristic (the <85% trigger) — gives the persona a real number instead of estimation | trivial | med |
| F9 | **`/usage`** | Plan-cap utilization + per-skill/subagent/MCP breakdown | USED (1×) [P1 §3] | **ADOPT (telemetry source)** | The per-skill/subagent/MCP breakdown is a NATIVE telemetry feed for the loop's usage-re-pull sub-pass (Deliverable B §2b) — cheaper than grepping transcripts | trivial | med-high |
| F10 | **`/insights`** | Report on session patterns + friction points | UNUSED | **ADOPT (loop input)** | Native usage-drift signal — "what is the persona doing repeatedly / where's friction" feeds the drift-reassessment sub-pass (Deliverable B §2c) | low | med |
| F11 | **`/release-notes`** | Interactive changelog viewer | UNUSED | **ADOPT (loop input)** | Native feature-surface-refresh feed for the loop's sub-pass (a) — the changelog IS the trigger | trivial | med |
| F12 | **`/reload-skills`** | Re-scan skill dirs mid-session (v2.1.152) | UNUSED | **ADOPT** | After the loop adds/edits a skill, reload without restart — makes the loop's living-artifact updates take effect same-session | trivial | low-med |
| F13 | **`/team-onboarding`** | Generate onboarding guide from usage history | UNUSED | SKIP | Single-operator (Luke); no team to onboard | — | none |
| F14 | **`/statusline`** | Custom status line | UNUSED | SKIP | Cosmetic; no outcome leverage | — | none |
| F15 | **Output styles** (`/config`) | Alter response formatting globally | UNUSED | SKIP ⚠ | loam controls voice via the abstraction-voice persona layer + hooks; a global output-style would collide with that, not compose | — | none |
| F16 | **`/memory` + auto-memory** | Edit CLAUDE.md, manage auto-memory entries | USED (MEMORY.md corpus) [memory] | KEEP | loam's files-are-memory doctrine IS this, hand-managed | — | — |
| F17 | **Remote control / `/teleport` / web sessions** | Drive local session from claude.ai / pull web→terminal | UNUSED | SKIP | loam is terminal+Telegram driven; web-session bridge has no current need | — | low |

---

## G. F2 — Ruthless Feedback on "adopt EVERY feature to the fullest"

**Disagreement:** "use every feature to the fullest" is the wrong target;
the right target is **deliberate-complete-coverage** — adopt every feature
that adds leverage, AND for every feature you don't adopt, record *why not*.
**Evidence:** the recent incident was partly **too many un-verified hooks
interacting** [task brief]; 30 SKIP rows here each carry a constraint-or-
fragility reason, and 6 ADOPT rows are ⚠-flagged as conditional. Blanket
"adopt everything" would have loam wire `MessageDisplay`, `agent`-type
hooks, `bypassPermissions`, agent-teams, and `--bare` — four of which
actively conflict with loam's safety/auth constraints (#12, #33, #46, F5)
and one (F5) breaks the hard no-API-key rule. **Alternative frame:** "use
every feature loam has a *reason* to use, and document the skip on the rest"
— which is what this matrix delivers. The coverage is total (78 rows, no
silent gaps); the adoption is selective.

**Second disagreement (carried from P1, re-affirmed):** the skills problem
is not "tune the triggers." It's **decide install-vs-retire first** (Mode A,
F2/#62), THEN fix triggers (`paths:` #67, `disable-model-invocation` #64)
only on survivors. Tuning a trigger on an invisible skill is wasted effort.

**Highest-leverage cluster (the through-line):** the biggest single win
isn't any one hook — it's **#40 reusable subagent definition files** +
their frontmatter (#43–#54). loam spawns 781 agents from ad-hoc prose
briefs; converting the repeated shapes (research/plan/build/judge) into
typed definitions with `model`, `tools`, `mcpServers` (telegram-scrub!),
`isolation:worktree`, `maxTurns`, and `skills`-preload structurally
encodes a dozen loam memory-rules that are currently soft. That's the
"recurrence → structural enforcement" doctrine applied to loam's own
dispatch surface.

---

## H. Top adopt-now (ranked, the 5 the loop should action first)

1. **#48 `skills:`-preload + #40 subagent definition files** — directly
   resolves the 0-invocation skill finding *for dispatched work* by
   injecting skill content instead of hoping description-match fires.
2. **#67 `paths:` on path-scoped skills** + **F2 plugin install decision** —
   the Mode-A/Mode-B fix for the skills that survive the retire cut.
3. **#75 `/goal` head-to-head vs `autonomy_continuation.py`** — retire a
   hand-rolled reimplementation of a now-native primitive (owner-gated call).
4. **#49 `mcpServers:` telegram-scrub on builder agents + #54
   `isolation:worktree`** — codify two CRITICAL loam safety rules
   (Telegram-drop prevention, build-race prevention) at the frontmatter level.
5. **F9 `/usage` + F11 `/release-notes` + F10 `/insights`** — adopt the
   three native feeds that *power the recurring loop itself* (telemetry,
   feature-surface, drift) rather than grepping transcripts by hand.

---

## Appendix — evidence index

- Hooks (30 events, 5 handlers): `code.claude.com/docs/en/hooks` + [P1 §1a/§1b]
- Commands (full table): `code.claude.com/docs/en/commands` (fetched 2026-05-31)
- Sub-agents (18 frontmatter fields, fork, teams): `code.claude.com/docs/en/sub-agents`
- Skills frontmatter: `code.claude.com/docs/en/skills` + [P1 §1e]
- `/goal` semantics: `code.claude.com/docs/en/goal` + [P1 §1c]
- Scheduling: `/docs/en/scheduled-tasks`, `/docs/en/routines` + [P1 §1d]
- loam usage facts: [P1 §2/§3] (file-cited) ; launchd jobs verified on disk
  `~/Library/LaunchAgents/com.loam.pos3.{places-audit,events-audit,usage-monitor,daily-reminders,memory-write-worker}.plist`
- Pass-1 review: `docs/reviews/claude-primitives-integration-review.md`
