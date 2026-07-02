# Pending delta — claude-code-subagents

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/sub-agents`
> Projection target: `claude-code/background-agents.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-02T13:49:59Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Use the /agents command Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
  - now: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Use the /agents command Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Spawn nested subagents Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: This page covers: Built-in subagents How to create your own Full configuration options Patterns for working with subagents Forked subagents Example subagents ​ Built-in subagents Claude Code includes built-in subagents that Claude automatically uses when appropriate.
  - now: ​ Built-in subagents Claude Code includes built-in subagents that Claude automatically uses when appropriate.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Model : Haiku (fast, low-latency) Tools : Read-only tools (denied access to Write and Edit tools) Purpose : File discovery, code search, codebase exploration Claude delegates to Explore when it needs to search or understand a codebase without making changes.
  - now: Model : Haiku, which is fast and low-latency Tools : read-only tools; Write and Edit are denied Purpose : file discovery, code search, codebase exploration Claude delegates to Explore when it needs to search or understand a codebase without making changes.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Model : Inherits from main conversation Tools : Read-only tools (denied access to Write and Edit tools) Purpose : Codebase research for planning When you’re in plan mode and Claude needs to understand your codebase, it delegates research to the Plan subagent.
This prevents infinite nesting (subagents cannot spawn other subagents) while still gathering necessary context.
  - now: Model : inherits from the main conversation Tools : read-only tools; Write and Edit are denied Purpose : codebase research for planning When you’re in plan mode and Claude needs to understand your codebase, it delegates research to the Plan subagent so that exploration output stays in a separate context window while the main conversation remains read-only.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Model : Inherits from main conversation Tools : All tools Purpose : Complex research, multi-step operations, code modifications Claude delegates to general-purpose when the task requires both exploration and modification, complex reasoning to interpret results, or multiple dependent steps.
  - now: Model : inherits from the main conversation Tools : all tools Purpose : complex research, multi-step operations, code modifications Claude delegates to general-purpose when the task requires both exploration and modification, complex reasoning to interpret results, or multiple dependent steps.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: To block a specific built-in type, add it to permissions.deny as shown in Disable specific subagents .
  - now: To restrict them: To block a specific built-in type, add it to permissions.deny as shown in Disable specific subagents .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The Running tab shows live subagents and lets you open or stop them.
  - now: The Running tab lists live and recently finished subagents and lets you open or stop them.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: When multiple subagents share the same name, the higher-priority location wins.
  - now: When multiple subagents share the same name, Claude Code uses the one from the higher-priority location.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Project subagents are discovered by walking up from the current working directory.
Directories added with --add-dir grant file access only and are not scanned for subagents.
To share subagents across projects, use ~/.claude/agents/ or a plugin .
  - now: Project subagents are discovered by walking up from the current working directory, so every .claude/agents/ between there and the repository root is scanned.
As of v2.1.178, when more than one of these nested directories defines the same name , Claude Code uses the definition closest to the working directory.
Directories added with --add-dir are also scanned: a .claude/agents/ folder inside an added directory loads alongside project subagents.
See Additional directories for which other configuration types load from --add-dir .
To share subagents across projects without --add-dir , use ~/.claude/agents/ or a plugin .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The subdirectory path does not affect how a subagent is identified or invoked, because identity comes only from the name frontmatter field.
Keep name values unique across the whole tree: if two files within one scope declare the same name, Claude Code keeps one and discards the other without warning.
  - now: The subdirectory path doesn’t affect how a subagent is identified or invoked, because identity comes only from the name frontmatter field.
Keep name values unique across the whole tree: if two files within one scope declare the same name, Claude Code loads only one of them.
As of v2.1.196, running /doctor reports same-scope duplicate agent names and shows which definition is active.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For security reasons, plugin subagents do not support the hooks , mcpServers , or permissionMode frontmatter fields.
  - now: For security reasons, plugin subagents don’t support the hooks , mcpServers , or permissionMode frontmatter fields.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: You can also add rules to permissions.allow in settings.json or settings.local.json , but these rules apply to the entire session, not just the plugin subagent.
  - now: You can also add rules to permissions.allow in settings.json or settings.local.json , but these rules apply to the entire session, not only the plugin subagent.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Subagents receive only this system prompt (plus basic environment details like working directory), not the full Claude Code system prompt.
  - now: Subagents receive only this system prompt plus basic environment details like the working directory, not the full Claude Code system prompt.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Within a subagent, cd commands do not persist between Bash or PowerShell tool calls and do not affect the main conversation’s working directory.
  - now: Within a subagent, cd commands don’t persist between Bash or PowerShell tool calls and don’t affect the main conversation’s working directory.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The filename does not have to match description Yes When Claude should delegate to this subagent tools No Tools the subagent can use.
  - now: The filename doesn’t have to match description Yes When Claude should delegate to this subagent tools No Tools the subagent can use.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The full skill content is injected, not just the description.
  - now: The full skill content is injected, not only the description.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Prepended to any user-provided prompt ​ Choose a model The model field controls which AI model the subagent uses: Model alias : Use one of the available aliases: sonnet , opus , haiku , or fable Full model ID : Use a full model ID such as claude-opus-4-8 or claude-sonnet-4-6 .
Accepts the same values as the --model flag inherit : Use the same model as the main conversation Omitted : If not specified, defaults to inherit (uses the same model as the main conversation) When Claude invokes a subagent, it can also pass a model parameter for that specific invocation.
Claude Code resolves the subagent’s model in this order: The CLAUDE_CODE_SUBAGENT_MODEL environment variable, if set The per-invocation model parameter The subagent definition’s model frontmatter The main conversation’s model ​ Control subagent capabilities You can control what subagents can do through tool access, permission modes, and conditional rules.
  - now: Prepended to any user-provided prompt ​ Choose a model The model field controls which AI model the subagent uses: Model alias : use one of the available aliases: sonnet , opus , haiku , or fable Full model ID : use a full model ID such as claude-opus-4-8 or claude-sonnet-5 .
Accepts the same values as the --model flag inherit : use the same model as the main conversation Omitted : defaults to inherit and uses the same model as the main conversation When Claude invokes a subagent, it can also pass a model parameter for that specific invocation.
Claude Code resolves the subagent’s model in this order: The CLAUDE_CODE_SUBAGENT_MODEL environment variable, when set to a model alias or model ID The per-invocation model parameter The subagent definition’s model frontmatter The main conversation’s model As of v2.1.196, setting CLAUDE_CODE_SUBAGENT_MODEL to inherit is the same as leaving it unset: resolution continues with the per-invocation model parameter, then the frontmatter.
In earlier versions, inherit forced subagents onto the main conversation’s model and ignored both of those sources.
The environment variable, per-invocation parameter, and frontmatter values are checked against your organization’s availableModels allowlist.
A value that resolves to an excluded model is not used and the subagent runs on the inherited model instead.
​ Control subagent capabilities You can control what subagents can do through tool access, permission modes, and conditional rules.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The following tools depend on the main conversation’s UI or session state and are not available to subagents, even when listed in the tools field: Agent AskUserQuestion EnterPlanMode ExitPlanMode , unless the subagent’s permissionMode is plan ScheduleWakeup WaitForMcpServers To restrict tools, use either the tools field (allowlist) or the disallowedTools field (denylist).
  - now: The following tools depend on the main conversation’s UI or session state and are not available to subagents, even when listed in the tools field: AskUserQuestion EnterPlanMode ExitPlanMode , unless the subagent’s permissionMode is plan ScheduleWakeup WaitForMcpServers To restrict tools, use either the tools field (allowlist) or the disallowedTools field (denylist).
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Restrict which subagents can be spawned When an agent runs as the main thread with claude --agent , it can spawn subagents using the Agent tool.
  - now: Both fields accept MCP server-level patterns in addition to exact tool names: mcp__<server> or mcp__<server>__* grants or removes every tool from the named server.
In disallowedTools , mcp__* also removes every MCP tool from any server.
This example removes every tool from the github MCP server while keeping tools from other servers and every built-in tool: --- name : local-only description : Inherits every tool except those from the github MCP server disallowedTools : mcp__github --- ​ Restrict which subagents can be spawned When an agent runs as the main thread with claude --agent , it can spawn subagents using the Agent tool.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: To allow spawning any subagent without restrictions, use Agent without parentheses: tools : Agent, Read, Bash If Agent is omitted from the tools list entirely, the agent cannot spawn any subagents.
This restriction only applies to agents running as the main thread with claude --agent .
Subagents cannot spawn other subagents, so Agent(agent_type) has no effect in subagent definitions.
  - now: To allow spawning any subagent without restrictions, use Agent without parentheses: tools : Agent, Read, Bash If Agent is omitted from the tools list entirely, the agent can’t spawn any subagents.
The Agent(agent_type) allowlist syntax applies only to an agent running as the main thread with claude --agent .
In a subagent definition, listing Agent in tools lets that subagent spawn nested subagents , but any type list inside the parentheses is ignored.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The subagent gets the tools; the parent conversation does not.
  - now: The subagent gets the tools; the parent conversation doesn’t.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: --strict-mcp-config does not filter servers you pass inline via --agents or the SDK agents option, since those are explicit caller input.
  - now: --strict-mcp-config doesn’t filter servers you pass inline via --agents or the SDK agents option, since those are explicit caller input.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: If the parent uses bypassPermissions or acceptEdits , this takes precedence and cannot be overridden.
  - now: If the parent uses bypassPermissions or acceptEdits , this takes precedence and can’t be overridden.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: You cannot preload skills that set disable-model-invocation: true , since preloading draws from the same set of skills Claude can invoke.
  - now: You can’t preload skills that set disable-model-invocation: true , since preloading draws from the same set of skills Claude can invoke.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: There are two ways to configure hooks: In the subagent’s frontmatter : Define hooks that run only while that subagent is active In settings.json : Define hooks that run in the main session when subagents start or stop ​ Hooks in subagent frontmatter Define hooks directly in the subagent’s markdown file.
  - now: There are two ways to configure hooks: In the subagent’s frontmatter : define hooks that run only while that subagent is active In settings.json : define hooks that run in the main session when subagents start or stop ​ Hooks in subagent frontmatter Define hooks directly in the subagent’s markdown file.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: This example runs a setup script only when the db-agent subagent starts, and a cleanup script when any subagent stops: { "hooks" : { "SubagentStart" : [ { "matcher" : "db-agent" , "hooks" : [ { "type" : "command" , "command" : "./scripts/setup-db-connection.sh" } ] } ], "SubagentStop" : [ { "hooks" : [ { "type" : "command" , "command" : "./scripts/cleanup-db-connection.sh" } ] } ] } } See Hooks for the complete hook configuration format.
  - now: The matcher value is the agent’s frontmatter name for project-level and user-level subagents, or the plugin-scoped identifier such as my-plugin:db-agent for plugin subagents .
A scoped name contains a colon, so it is evaluated as an unanchored regular expression ; anchor it with ^ and $ , as in ^my-plugin:db-agent$ , to match only that agent.
This example runs a setup script only when the db-agent subagent starts, and a cleanup script when any subagent stops: { "hooks" : { "SubagentStart" : [ { "matcher" : "db-agent" , "hooks" : [ { "type" : "command" , "command" : "./scripts/setup-db-connection.sh" } ] } ], "SubagentStop" : [ { "hooks" : [ { "type" : "command" , "command" : "./scripts/cleanup-db-connection.sh" } ] } ] } } A hyphenated matcher like db-agent matches exactly on Claude Code v2.1.195 or later.
On earlier versions it is evaluated as an unanchored regular expression and also fires for any agent type that contains it, such as prod-db-agent ; anchor it as ^db-agent$ on those versions.
See Hooks for the complete hook configuration format.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For a plugin-provided subagent, you can pass just the agent name and Claude Code will find it: claude --agent security-reviewer If multiple plugins provide agents with the same name, pass the scoped name to disambiguate: claude --agent my-plugin:security-reviewer If the plugin places the agent in a subfolder of its agents/ directory, include the subfolder in the scoped name, for example claude --agent my-plugin:review:security .
  - now: For a plugin-provided subagent, you can pass only the agent name and Claude Code finds it: claude --agent security-reviewer If multiple plugins provide agents with the same name, pass the scoped name to disambiguate: claude --agent my-plugin:security-reviewer If the plugin places the agent in a subfolder of its agents/ directory, include the subfolder in the scoped name, for example claude --agent my-plugin:review:security .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Run subagents in foreground or background Subagents can run in the foreground (blocking) or background (concurrent): Foreground subagents block the main conversation until complete.
  - now: ​ Run subagents in foreground or background Subagents can run in the foreground or the background: Foreground subagents block the main conversation until complete.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: They run with the permissions already granted in the session and auto-deny any tool call that would otherwise prompt.
If a background subagent needs to ask clarifying questions, that tool call fails but the subagent continues.
If a background subagent fails due to missing permissions, you can start a new foreground subagent with the same task to retry with interactive prompts.
  - now: As of v2.1.186, when a background subagent reaches a tool call that needs permission, the prompt surfaces in your main session and names the subagent that is asking.
Approve to let the subagent continue, or press Esc to deny that one tool call without stopping the subagent.
Before v2.1.186, background subagents auto-denied any tool call that would have prompted.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Forks still surface permission prompts in your terminal as they occur; named subagents auto-deny anything that would prompt, as described above.
  - now: Permission prompts from these background subagents surface in your main session as described above.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use the code-reviewer subagent to find performance issues, then use the optimizer subagent to fix them ​ Choose between subagents and main conversation Use the main conversation when: The task needs frequent back-and-forth or iterative refinement Multiple phases share significant context (planning → implementation → testing) You’re making a quick, targeted change Latency matters.
  - now: Use the code-reviewer subagent to find performance issues, then use the optimizer subagent to fix them ​ Choose between subagents and main conversation Use the main conversation when: The task needs frequent back-and-forth or iterative refinement Multiple phases share significant context, such as planning, implementation, and testing You’re making a quick, targeted change Latency matters.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Subagents cannot spawn other subagents.
If your workflow requires nested delegation, use Skills or chain subagents from the main conversation.
  - now: ​ Spawn nested subagents As of Claude Code v2.1.172, a subagent can spawn its own subagents.
Use this when a delegated task itself splits into parallel subtasks, such as a reviewer subagent that dispatches a verifier per finding, so the intermediate output never reaches your main conversation.
Only the top-level subagent’s summary returns to you.
A nested subagent is configured the same way as a top-level one and resolves from the same scopes .
The subagent panel below the prompt input shows the full tree: each row displays a (+N) count of descendants, and as of v2.1.193, opening a row shows that subagent’s siblings and direct children with a path back to main .
The Running tab in /agents lists running subagents as a flat list.
Depth is counted as the number of subagent levels below the main conversation, regardless of whether each level runs in the foreground or background .
A subagent at depth five doesn’t receive the Agent tool and can’t spawn further.
The limit is fixed and not configurable.
As of Claude Code v2.1.187, a background subagent’s depth is fixed when it is first spawned, and resuming it later doesn’t change that depth.
For example, if your main conversation spawns subagent A, and A spawns a background subagent B at depth two, B is still at depth two when you resume it directly from the main conversation.
Resuming a subagent from a shallower context doesn’t let it spawn additional levels that the depth limit already prevented.
To prevent a specific subagent from spawning others, omit Agent from its tools list or add it to disallowedTools .
A fork still can’t spawn another fork.
It can spawn other subagent types, and those count toward the depth limit.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: It does not see your conversation history, the skills you’ve already invoked, or the files Claude has already read.
  - now: It doesn’t see your conversation history, the skills you’ve already invoked, or the files Claude has already read.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The SendMessage tool is only available when agent teams are enabled via CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 .
  - now: The SendMessage tool is always available for resuming subagents by agent ID or name.
Structured team-protocol messages such as shutdown_request and plan_approval_response require agent teams to be enabled.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Subagent transcripts persist independently of the main conversation: Main conversation compaction : When the main conversation compacts, subagent transcripts are unaffected.
  - now: Subagent transcripts persist independently of the main conversation: Main conversation compaction : when the main conversation compacts, subagent transcripts are unaffected.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Session persistence : Subagent transcripts persist within their session.
  - now: Session persistence : subagent transcripts persist within their session.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Automatic cleanup : Transcripts are cleaned up based on the cleanupPeriodDays setting (default: 30 days).
  - now: Automatic cleanup : transcripts are cleaned up based on the cleanupPeriodDays setting, which defaults to 30 days.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: By default, auto-compaction triggers at approximately 95% capacity.
To trigger compaction earlier, set CLAUDE_AUTOCOMPACT_PCT_OVERRIDE to a lower percentage (for example, 50 ).
See environment variables for details.
  - now: Compaction triggers under the same conditions, and CLAUDE_AUTOCOMPACT_PCT_OVERRIDE applies to subagents as well.
See environment variables for when the override takes effect.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Making forks the model’s default spawn behavior is experimental and may change in future releases.
This default may also be enabled in interactive sessions as part of a staged rollout.
  - now: Letting Claude itself spawn forks is experimental and may change in future releases.
This capability may also be enabled in interactive sessions as part of a staged rollout.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Enabling fork mode changes Claude Code in two ways: Claude spawns a fork whenever it would otherwise use the general-purpose subagent.
Named subagents such as Explore still spawn as before.
  - now: Enabling fork mode changes Claude Code in two ways: Claude can spawn a fork by requesting the fork subagent type explicitly.
Spawns without a subagent type still use the general-purpose subagent, and named subagents such as Explore still spawn as before.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Fork Named subagent Context Full conversation history Fresh context with the prompt you pass System prompt and tools Same as main session From the subagent’s definition file Model Same as main session From the subagent’s model field Permissions Prompts surface in your terminal Auto-denied when running in the background Prompt cache Shared with main session Separate cache Because a fork’s system prompt and tool definitions are identical to the parent, its first request reuses the parent’s prompt cache .
  - now: Fork Named subagent Context Full conversation history Fresh context with the prompt you pass System prompt and tools Same as main session From the subagent’s definition file Model Same as main session From the subagent’s model field Permissions Prompts surface in your terminal Prompts surface in your main session when running in the background Prompt cache Shared with main session Separate cache Because a fork’s system prompt and tool definitions are identical to the parent, its first request reuses the parent’s prompt cache .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: A fork cannot spawn further forks.
  - now: A fork can’t spawn further forks.
