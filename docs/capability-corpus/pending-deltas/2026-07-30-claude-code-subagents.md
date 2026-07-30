# Pending delta — claude-code-subagents

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/sub-agents`
> Projection target: `claude-code/background-agents.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-30T13:10:25Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Use the /agents command Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Spawn nested subagents Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
Copy page Subagents are specialized AI assistants that handle specific types of tasks.
  - now: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background API errors in subagents Subagent output scanning Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Let subagents spawn their own subagents Session subagent limit Concurrent subagent limit Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
Copy page Copy page Subagents are specialized AI assistants that handle specific types of tasks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Claude Code includes several built-in subagents like Explore , Plan , and general-purpose .
  - now: Claude Code includes several built-in subagents such as Explore, Plan, and general-purpose.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Model : Haiku, which is fast and low-latency Tools : read-only tools; Write and Edit are denied Purpose : file discovery, code search, codebase exploration Claude delegates to Explore when it needs to search or understand a codebase without making changes.
  - now: Model : inherits from the main conversation, capped at Opus on the Claude API, so Explore never runs on a more expensive model than the one you already chose for the session Tools : read-only tools; Write and Edit are denied Purpose : file discovery, code search, codebase exploration As of v2.1.198, Explore inherits the main conversation’s model instead of always running on Haiku.
On the Claude API, the inherited model is capped at Opus: a main conversation on a higher tier runs Explore on Opus, and a main conversation on Sonnet or Haiku runs Explore on that same model.
On any other provider, such as Amazon Bedrock, Google Cloud’s Agent Platform, Microsoft Foundry, or Claude Platform on AWS , Explore inherits the main conversation’s model directly.
A user or project subagent named Explore overrides the built-in and keeps its own model field, so define one with model: haiku to keep exploration on a lower-cost model.
Claude delegates to Explore when it needs to search or understand a codebase without making changes.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Model : inherits from the main conversation Tools : all tools Purpose : complex research, multi-step operations, code modifications Claude delegates to general-purpose when the task requires both exploration and modification, complex reasoning to interpret results, or multiple dependent steps.
  - now: Model : inherits from the main conversation Tools : every tool available to subagents Purpose : complex research, multi-step operations, code modifications Claude delegates to general-purpose when the task requires both exploration and modification, complex reasoning to interpret results, or multiple dependent steps.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Agent Model When Claude uses it statusline-setup Sonnet When you run /statusline to configure your status line claude-code-guide Haiku When you ask questions about Claude Code features Built-in subagents are always registered in interactive sessions.
  - now: Agent Model When Claude uses it statusline-setup Sonnet When you run /statusline to configure your status line claude-code-guide Haiku When you ask questions about Claude Code features Built-in subagents are registered by default in interactive sessions.
- **new-claim** — adds a capability claim not previously upstream
  - now: To remove only the built-in Explore and Plan subagents, set CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1 .
Claude reads and explores files directly instead of delegating to them.
Requires Claude Code v2.1.198 or later.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Quickstart: create your first subagent Subagents are defined in Markdown files with YAML frontmatter.
You can create them manually or use the /agents command.
This walkthrough guides you through creating a user-level subagent with the /agents command.
The subagent reviews code and suggests improvements for the codebase.
1 Open the subagents interface In Claude Code, run: /agents 2 Choose a location Switch to the Library tab, select Create new agent , then choose Personal .
This saves the subagent to ~/.claude/agents/ so it’s available in all your projects.
3 Generate with Claude Select Generate with Claude .
When prompted, describe the subagent: A code improvement agent that scans files and suggests improvements for readability, performance, and best practices.
  - now: ​ Quickstart: create your first subagent Subagents are Markdown files with YAML frontmatter.
To create one, ask Claude to write it for you, or write the file yourself .
As of v2.1.198, the /agents command no longer opens the interactive creation wizard; running it prints a reminder to ask Claude or edit .claude/agents/ directly.
Subagent files, frontmatter fields, and the .claude/agents/ and ~/.claude/agents/ locations are unchanged; only the terminal wizard is removed.
This walkthrough creates a user-level subagent that reviews code and suggests improvements.
1 Ask Claude to create the subagent In Claude Code, describe the subagent you want and where to save it: Create a personal code-improver subagent in ~/.claude/agents/ that scans files and suggests improvements for readability, performance, and best practices.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude generates the identifier, description, and system prompt for you.
4 Select tools For a read-only reviewer, deselect everything except Read-only tools .
If you keep all tools selected, the subagent inherits all tools available to the main conversation.
5 Select model Choose which model the subagent uses.
For this example agent, select Sonnet , which balances capability and speed for analyzing code patterns.
6 Choose a color Pick a background color for the subagent.
This helps you identify which subagent is running in the UI.
7 Configure memory Select User scope to give the subagent a persistent memory directory at ~/.claude/agent-memory/ .
The subagent uses this to accumulate insights across conversations, such as codebase patterns and recurring issues.
Select None if you don’t want the subagent to persist learnings.
8 Save and try it out Review the configuration summary.
Press s or Enter to save, or press e to save and edit the file in your editor.
The subagent is available immediately.
Try it: Use the code-improver agent to suggest improvements in this project Claude delegates to your new subagent, which scans the codebase and returns improvement suggestions.
  - now: Make it read-only and have it use Sonnet.
Claude writes the file with a name , a description , a tools list, a model , and a system prompt.
2 Review the file Open ~/.claude/agents/code-improver.md and confirm the frontmatter matches what you asked for.
The result looks like this: --- name : code-improver description : Scans files and suggests improvements for readability, performance, and best practices.
Use after writing or modifying code.
tools : Read, Grep, Glob model : sonnet --- You are a code improvement specialist.
For each issue you find, explain the problem, show the current code, and provide an improved version.
Because the file lives in ~/.claude/agents/ , the subagent is available in every project on your machine.
To scope it to one project instead, move it to that project’s .claude/agents/ directory.
Choose the subagent scope compares the two.
3 Try it out Ask Claude to delegate to the new subagent: Use the code-improver agent to suggest improvements in this project Claude delegates to your new subagent, which scans the codebase and returns improvement suggestions.
If Claude can’t find the new subagent, restart Claude Code and try again.
This happens only when ~/.claude/agents/ didn’t exist before the session started, because a running session doesn’t detect a newly created agents directory.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: You can also create subagents manually as Markdown files, define them via CLI flags, or distribute them through plugins.
  - now: You can also write subagent files by hand, define them via CLI flags, or distribute them through plugins.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Configure subagents ​ Use the /agents command The /agents command opens a tabbed interface for managing subagents.
The Running tab lists live and recently finished subagents and lets you open or stop them.
The Library tab lets you: View all available subagents (built-in, user, project, and plugin) Create new subagents with guided setup or Claude generation Edit existing subagent configuration and tool access Delete custom subagents See which subagents are active when duplicates exist This is the recommended way to create and manage subagents.
For manual creation or automation, you can also add subagent files directly.
​ Choose the subagent scope Subagents are Markdown files with YAML frontmatter.
Store them in different locations depending on scope.
  - now: On Claude Code v2.1.197 and earlier, /agents opens an interactive wizard with a Running tab that lists live subagents and a Library tab for creating, editing, and deleting them.
​ Configure subagents A subagent’s file location determines who it’s available to, and its frontmatter determines what it can do.
This section covers where subagent files live and every field they support.
​ Choose the subagent scope Store subagent files in different locations depending on scope.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Location Scope Priority How to create Managed settings Organization-wide 1 (highest) Deployed via managed settings --agents CLI flag Current session 2 Pass JSON when launching Claude Code .claude/agents/ Current project 3 Interactive or manual ~/.claude/agents/ All your projects 4 Interactive or manual Plugin’s agents/ directory Where plugin is enabled 5 (lowest) Installed with plugins Project subagents ( .claude/agents/ ) are ideal for subagents specific to a codebase.
  - now: Location Scope Priority How to create Managed settings Organization-wide 1 (highest) Deployed via managed settings --agents CLI flag Current session 2 Pass JSON when launching Claude Code .claude/agents/ Current project 3 Ask Claude, or create the file manually ~/.claude/agents/ All your projects 4 Ask Claude, or create the file manually Plugin’s agents/ directory Where plugin is enabled 5 (lowest) Installed with plugins Project subagents ( .claude/agents/ ) are ideal for subagents specific to a codebase.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Keep name values unique across the whole tree: if two files within one scope declare the same name, Claude Code loads only one of them.
As of v2.1.196, running /doctor reports same-scope duplicate agent names and shows which definition is active.
  - now: Keep name values unique across the whole tree: if two files under the same .claude/agents/ directory, including its subfolders, declare the same name, Claude Code loads only one of them, chosen by filesystem read order rather than a documented precedence.
Across nested project directories, the definition closest to the working directory wins, as described above.
The /doctor setup checkup reports files in the same directory that share a name and proposes renaming or removing all but one.
Before v2.1.205, /doctor opened a diagnostics screen that listed duplicates and showed which definition was active.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: They appear in /agents alongside your custom subagents.
  - now: They load automatically alongside your custom subagents and appear in the @-mention typeahead under their scoped name.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Write subagent files Subagent files use YAML frontmatter for configuration, followed by the system prompt in Markdown: Subagents are loaded at session start.
If you add or edit a subagent file directly on disk, restart your session to load it.
Subagents created through the /agents interface take effect immediately without a restart.
  - now: ​ Write subagent files Subagent files use YAML frontmatter for configuration, followed by the system prompt in Markdown: Claude Code watches ~/.claude/agents/ and .claude/agents/ .
When you add or edit a subagent file on disk, or ask Claude to write one for you, Claude Code detects the change within a few seconds and the next delegation uses the updated definition, with no restart needed.
Two cases still need a restart: The watcher covers only directories that existed when the session started, so after creating a scope’s first agent file in a new agents directory, restart to load it.
Sessions started with --disable-slash-commands don’t watch these directories at all.
- **new-claim** — adds a capability claim not previously upstream
  - now: In non-interactive mode , the --append-subagent-system-prompt flag appends the text you provide to the end of every subagent’s system prompt, including nested subagents.
Requires Claude Code v2.1.205 or later.
- **new-claim** — adds a capability claim not previously upstream
  - now: A subagent with isolation: worktree runs its Bash and PowerShell commands inside its worktree.
A command whose working directory resolves to your main checkout instead, for example because the worktree directory was removed while the subagent was running, fails with an error.
Before v2.1.203, such a command could run in the main checkout.
This working-directory check covers the whole repository containing the directory you launched Claude Code from.
When your session runs in a linked worktree of its own, the check also covers the main checkout that worktree is linked from.
Before v2.1.210, the check covered only the launch directory itself.
A command whose working directory resolved elsewhere in the same repository, such as the repository root when you launched Claude Code from a monorepo subdirectory, ran there instead of failing.
For Bash commands, Claude Code also checks the command itself: a command that redirects git into the main checkout fails with an error, whether it uses git -C , --git-dir , a GIT_DIR or GIT_WORK_TREE variable, or a cd into the main checkout first.
A command too complex to check also fails, with an error telling Claude to split it into separate plain commands.
This check applies to Bash only; PowerShell commands get only the working-directory check.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The filename doesn’t have to match description Yes When Claude should delegate to this subagent tools No Tools the subagent can use.
Inherits all tools if omitted.
To preload Skills into context, use the skills field rather than listing Skill here disallowedTools No Tools to deny, removed from inherited or specified list model No Model to use: sonnet , opus , haiku , fable , a full model ID (for example, claude-opus-4-8 ), or inherit .
Defaults to inherit permissionMode No Permission mode : default , acceptEdits , auto , dontAsk , bypassPermissions , or plan .
  - now: The filename doesn’t have to match.
Names can’t contain : , which is reserved for plugin-scoped identifiers such as my-plugin:reviewer .
Claude Code doesn’t load a file whose name contains one and logs an error to the debug log.
Before v2.1.218, such names were accepted description Yes When Claude should delegate to this subagent tools No Tools the subagent can use.
Inherits every tool available to subagents if omitted.
If no entry in the list resolves to a tool, the subagent usually fails to launch with an error naming the entries.
To preload Skills into context, use the skills field rather than listing Skill here disallowedTools No Tools to deny, removed from inherited or specified list model No Model to use: sonnet , opus , haiku , fable , a full model ID (for example, claude-opus-5 ), or inherit .
Defaults to inherit permissionMode No Permission mode : default , acceptEdits , auto , dontAsk , bypassPermissions , plan , or manual as an alias for default .
The manual alias requires Claude Code v2.1.200 or later.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Enables cross-session learning background No Set to true to always run this subagent as a background task .
Default: false effort No Effort level when this subagent is active.
  - now: Enables cross-session learning background No Set to true to always run this subagent as a background task , even when Claude needs its result right away.
When unset, Claude chooses, and as of v2.1.198 it runs subagents in the background by default effort No Effort level when this subagent is active.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Prepended to any user-provided prompt ​ Choose a model The model field controls which AI model the subagent uses: Model alias : use one of the available aliases: sonnet , opus , haiku , or fable Full model ID : use a full model ID such as claude-opus-4-8 or claude-sonnet-5 .
  - now: Prepended to any user-provided prompt ​ Choose a model The model field controls which AI model the subagent uses: Model alias : use one of the available aliases: sonnet , opus , haiku , or fable Full model ID : use a full model ID such as claude-opus-5 or claude-sonnet-5 .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The environment variable, per-invocation parameter, and frontmatter values are checked against your organization’s availableModels allowlist.
A value that resolves to an excluded model is not used and the subagent runs on the inherited model instead.
  - now: Claude Code checks the environment variable, per-invocation parameter, and frontmatter values against your organization’s availableModels allowlist.
It skips a value that resolves to an excluded model and runs the subagent on the inherited model instead.
A per-invocation model parameter also applies when the subagent is resumed or sent a follow-up message , so the subagent stays on that model.
Before v2.1.211, resuming dropped the per-invocation value and the subagent reverted to its definition’s model field or, without one, the main conversation’s model.
As of v2.1.198, subagents also inherit the main conversation’s extended thinking configuration: if thinking is on in your session, it’s on for the subagent, and if it’s off, it stays off.
There is no per-subagent thinking setting.
Before v2.1.198, subagents ran with extended thinking disabled regardless of the main conversation’s setting.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Available tools Subagents inherit the internal tools and MCP tools available in the main conversation by default.
The following tools depend on the main conversation’s UI or session state and are not available to subagents, even when listed in the tools field: AskUserQuestion EnterPlanMode ExitPlanMode , unless the subagent’s permissionMode is plan ScheduleWakeup WaitForMcpServers To restrict tools, use either the tools field (allowlist) or the disallowedTools field (denylist).
This example uses tools to exclusively allow Read, Grep, Glob, and Bash.
The subagent can’t edit files, write files, or use any MCP tools: --- name : safe-researcher description : Research agent with restricted capabilities tools : Read, Grep, Glob, Bash --- This example uses disallowedTools to inherit every tool from the main conversation except Write and Edit.
The subagent keeps Bash, MCP tools, and everything else: --- name : no-writes description : Inherits every tool except file writes disallowedTools : Write, Edit --- If both are set, disallowedTools is applied first, then tools is resolved against the remaining pool.
  - now: ​ Available tools Subagents inherit the built-in tools and MCP tools available in the main conversation, narrowed by two filters: the first removes a short list of tools from every subagent, and the second reduces the built-in tool set for subagents that run in the background , which is the default.
Forks skip both filters and receive the main conversation’s exact tool pool.
The first filter removes these tools, even when listed in the tools field: Agent , when the subagent is at the depth limit ; in a fork the tool stays listed but returns an error instead of spawning AskUserQuestion EndConversation , which can end only the main conversation; see EndConversation tool behavior EnterPlanMode ExitPlanMode , unless the subagent’s permissionMode is plan ScheduleWakeup TaskOutput WaitForMcpServers Workflow The second filter applies to subagents running in the background.
Apart from Agent and ExitPlanMode , which follow the first filter’s conditions wherever the subagent runs, a background subagent keeps every MCP tool but only these built-in tools: Read , Grep , Glob , Bash , PowerShell , Edit , Write , NotebookEdit , WebFetch , WebSearch , TodoWrite , Skill , ToolSearch , EnterWorktree , ExitWorktree , Monitor , TaskStop , SendMessage , and Artifact .
Claude Code removes every other built-in tool from a background subagent, whether inherited or listed in the tools field, so the same definition can resolve to different tools in the foreground and the background.
The removal reports no error unless it leaves the tools list resolving to nothing .
Teammates in agent teams additionally keep the task tools and cron tools: TaskCreate , TaskGet , TaskList , TaskUpdate , CronCreate , CronDelete , and CronList .
To restrict tools, use the tools field as an allowlist or the disallowedTools field as a denylist.
This example uses tools to allow only Read, Grep, Glob, and Bash.
The subagent can’t edit files, write files, or use any MCP tools: --- name : safe-researcher description : Research agent with restricted capabilities tools : Read, Grep, Glob, Bash --- This example uses disallowedTools to inherit the subagent’s tool pool except Write and Edit.
The subagent keeps Bash, MCP tools, and the rest of its pool: --- name : no-writes description : Inherits the available tools except file writes disallowedTools : Write, Edit --- If both are set, disallowedTools is applied first, then tools is resolved against the remaining pool.
- **new-claim** — adds a capability claim not previously upstream
  - now: When nothing in the tools list resolves to a tool, for example because every entry is misspelled or names a tool that isn’t available to subagents, Claude Code usually refuses to launch the subagent and the Agent tool returns an error naming the unresolved entries; see Agent would be spawned with zero tools for the message and how to fix each entry.
Before v2.1.208, that subagent launched with no tools and could return an empty or confusing result.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This example removes every tool from the github MCP server while keeping tools from other servers and every built-in tool: --- name : local-only description : Inherits every tool except those from the github MCP server disallowedTools : mcp__github --- ​ Restrict which subagents can be spawned When an agent runs as the main thread with claude --agent , it can spawn subagents using the Agent tool.
  - now: This example removes every tool from the github MCP server while keeping tools from other servers and the built-in tools in its pool: --- name : local-only description : Inherits every tool except those from the github MCP server disallowedTools : mcp__github --- ​ Restrict which subagents can be spawned When an agent runs as the main thread with claude --agent , it can spawn subagents using the Agent tool.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: To allow spawning any subagent without restrictions, use Agent without parentheses: tools : Agent, Read, Bash If Agent is omitted from the tools list entirely, the agent can’t spawn any subagents.
  - now: To allow spawning any subagent without restrictions, use Agent without parentheses: tools : Agent, Read, Bash If you omit Agent from the tools list entirely, the agent can’t spawn any subagents with the Agent tool.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: In a subagent definition, listing Agent in tools lets that subagent spawn nested subagents , but any type list inside the parentheses is ignored.
  - now: In a subagent definition, listing Agent in tools lets that subagent spawn subagents of its own while the depth limit allows it, but any type list inside the parentheses is ignored.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Inline definitions use the same schema as .mcp.json server entries ( stdio , http , sse , ws ), keyed by the server name.
  - now: Inline definitions use the same schema as .mcp.json server entries, keyed by the server name, and support the stdio , http , sse , and ws types.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Mode Behavior default Standard permission checking with prompts acceptEdits Auto-accept file edits and common filesystem commands for paths in the working directory or additionalDirectories auto Auto mode : a background classifier reviews commands and protected-directory writes dontAsk Auto-deny permission prompts (explicitly allowed tools still work) bypassPermissions Skip permission prompts plan Plan mode (read-only exploration) Use bypassPermissions with caution.
  - now: Mode Behavior default Standard permission checking with prompts acceptEdits Auto-accept file edits and common filesystem commands for paths in the working directory or additionalDirectories auto Auto mode : a background classifier reviews commands and protected-directory writes dontAsk Auto-deny permission prompts.
Explicitly allowed tools still work; AskUserQuestion , connector tools your organization set to ask , and MCP tools marked requiresUserInteraction are denied even if you’ve allowed them bypassPermissions Skip permission prompts plan Plan mode (read-only exploration) Use bypassPermissions with caution.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Explicit ask rules and root and home directory removals such as rm -rf / still prompt.
  - now: Explicit ask rules , connector tools your organization set to ask , MCP tools marked requiresUserInteraction , and root and home directory removals such as rm -rf / still prompt.
- **new-claim** — adds a capability claim not previously upstream
  - now: This includes the bundled /verify and /code-review skills: only you can run them, so they can’t be preloaded either.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Choose a scope based on how broadly the memory should apply: Scope Location Use when user ~/.claude/agent-memory/<name-of-agent>/ the subagent should remember learnings across all projects project .claude/agent-memory/<name-of-agent>/ the subagent’s knowledge is project-specific and shareable via version control local .claude/agent-memory-local/<name-of-agent>/ the subagent’s knowledge is project-specific but should not be checked into version control When memory is enabled: The subagent’s system prompt includes instructions for reading and writing to the memory directory.
  - now: Choose a scope based on how broadly the memory should apply: Scope Location Use when user ~/.claude/agent-memory/<name-of-agent>/ the subagent should remember learnings across all projects project .claude/agent-memory/<name-of-agent>/ the subagent’s knowledge is project-specific and shareable via version control local .claude/agent-memory-local/<name-of-agent>/ the subagent’s knowledge is project-specific but shouldn’t be checked into version control Subagent memory is part of auto memory : if you turn auto memory off, with the autoMemoryEnabled setting or CLAUDE_CODE_DISABLE_AUTO_MEMORY , the memory field has no effect and the subagent launches without the memory instructions or the memory tool access described below.
When memory is enabled: The subagent’s system prompt includes instructions for reading and writing to the memory directory.
- **removal** — removes a previously-present capability claim
  - was: Use user when the subagent’s knowledge is broadly applicable across projects, or local when the knowledge should not be checked into version control.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The validation script reads this JSON, extracts the Bash command, and exits with code 2 to block write operations: #!/bin/bash # ./scripts/validate-readonly-query.sh INPUT = $( cat ) COMMAND = $( echo " $INPUT " | jq -r '.tool_input.command // empty' ) # Block SQL write operations (case-insensitive) if echo " $COMMAND " | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b' > /dev/null ; then echo "Blocked: Only SELECT queries are allowed" >&2 exit 2 fi exit 0 See Hook input for the complete input schema and exit codes for how exit codes affect behavior.
  - now: The validation script reads this JSON, extracts the Bash command, and exits with code 2 to block write operations: #!/bin/bash # ./scripts/validate-readonly-query.sh INPUT = $( cat ) COMMAND = $( echo " $INPUT " | jq -r '.tool_input.command // empty' ) # Block SQL write operations (case-insensitive) if echo " $COMMAND " | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b' > /dev/null ; then echo "Blocked: Only SELECT queries are allowed" >&2 exit 2 fi exit 0 On macOS and Linux, make the script executable, or the hook fails instead of blocking anything: chmod +x ./scripts/validate-readonly-query.sh To test the rule, ask the subagent to run an UPDATE statement: the script exits with code 2, Claude Code blocks the command, and the subagent sees the Blocked: Only SELECT queries are allowed message.
See Hook input for the complete input schema and exit codes for how exit codes affect behavior.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: There are two ways to configure hooks: In the subagent’s frontmatter : define hooks that run only while that subagent is active In settings.json : define hooks that run in the main session when subagents start or stop ​ Hooks in subagent frontmatter Define hooks directly in the subagent’s markdown file.
  - now: There are two ways to configure hooks: In the subagent’s frontmatter : define hooks that run only while that subagent is active In settings.json : define session-wide hooks that also fire inside subagents.
Tool events such as PreToolUse and PostToolUse fire for the subagent’s tool calls the same way they do in the main conversation, and SubagentStart and SubagentStop fire when a subagent starts or finishes Hooks from settings files, managed policy settings, and plugins all apply inside subagents, so a PreToolUse hook in settings.json also runs before every tool a subagent uses.
​ Hooks in subagent frontmatter Define hooks directly in the subagent’s markdown file.
- **new-claim** — adds a capability claim not previously upstream
  - now: To let a project-level subagent’s frontmatter hooks run, accept the workspace trust dialog for the folder that contains the agent file.
Hooks from user-level subagents in ~/.claude/agents/ and from definitions you pass with --agents run without this step.
If you added a folder with --add-dir from outside your trusted workspace’s repository, trust that folder separately: its .claude/agents/ hooks don’t inherit the workspace’s grant.
Until you trust the folder, the subagent still runs, but Claude Code skips its frontmatter hooks and logs an error to the debug log explaining how to trust the folder.
The grant is the same workspace trust approval that covers project settings and project-level hooks.
Before v2.1.218, frontmatter hooks could run from folders you hadn’t trusted, including in non-interactive sessions.
- **new-claim** — adds a capability claim not previously upstream
  - now: While you type this form the typeahead shows file matches rather than agents.
The agent mention still resolves when you submit.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: This works with built-in and custom subagents, and the choice persists when you resume the session.
  - now: This works with built-in and custom subagents, and the choice persists when you resume the session: Claude Code restores the agent’s system prompt, tool restrictions, and model along with the conversation.
If the agent no longer exists when you resume, the session continues with the default tools and system prompt and shows a warning naming the agent .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude decides whether to run subagents in the foreground or background based on the task.
You can also: Ask Claude to “run this in the background” Press Ctrl+B to background a running task To disable all background task functionality, set the CLAUDE_CODE_DISABLE_BACKGROUND_TASKS environment variable to 1 .
  - now: As of v2.1.198, subagents run in the background by default.
Claude runs a subagent in the foreground when it needs the result before continuing.
Background subagents run with a smaller built-in tool set than foreground subagents, except for conversation forks, and they surface every permission prompt in your main session.
A background subagent’s results reach Claude as a completion notification in a later turn.
Claude waits for that notification before reporting the subagent’s results, and if you ask about progress first, it reports that the subagent is still running.
Before v2.1.211, Claude sometimes reported results for a background subagent that hadn’t finished.
You can also steer this yourself: Ask Claude to run a task in the background or in the foreground Press Ctrl+B to background a running task A background subagent that completes stays listed in /tasks , marked done and sorted below running work, until the session cleans up its task list.
Its detail view stays open when the subagent finishes.
Subagents that fail or that you stop leave the list.
Before v2.1.208, a completed subagent left the list the moment it finished and its detail view closed.
To disable all background task functionality, set the CLAUDE_CODE_DISABLE_BACKGROUND_TASKS environment variable to 1 .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: When CLAUDE_CODE_FORK_SUBAGENT is set to 1 , every subagent spawn runs in the background regardless of the background field.
Permission prompts from these background subagents surface in your main session as described above.
  - now: When CLAUDE_CODE_FORK_SUBAGENT is set to 1 , every subagent runs in the background and the frontmatter background field has no effect, because fork mode removes the run_in_background parameter from the Agent tool.
CLAUDE_CODE_DISABLE_BACKGROUND_TASKS takes precedence over fork mode and keeps subagents in the foreground.
​ API errors in subagents As of v2.1.199, a subagent whose run ends on an API error, such as a usage limit or a repeated server error, reports that failure back to Claude instead of returning the error text as if it were the subagent’s findings.
What Claude receives depends on where the subagent ran: Foreground : if a rate limit, overload, or server error cuts off a subagent that already produced text output, the Agent tool returns that partial output with a note that the subagent was cut off and didn’t finish its task.
A subagent that produced nothing, or whose only output was tool calls, fails with Agent terminated early due to an API error , followed by the error detail.
In v2.1.199, a rate limit, overload, or server error that cut off the tool-calls-only shape returned an empty partial result containing only the cut-off note instead.
Background : the subagent is marked failed, and the message Claude receives when it ends names the API error and includes the subagent’s last output, so partial work isn’t lost.
Once the underlying API error clears, ask Claude to retry the task or resume the subagent .
​ Subagent output scanning Claude Code scans each subagent’s final report before Claude reads it.
A subagent may have read files, web pages, or command output you never reviewed, and text from those sources can carry instructions aimed at the main conversation.
The scan never removes or rewords anything; it makes two kinds of change you may notice in a report: Backslash insertion : the scan inserts a backslash into text that imitates Claude Code’s own output, such as a <system-reminder> tag or a line starting with Human: or Assistant: , so the imitation reads as ordinary text instead of being mistaken for part of the conversation.
Marker line : the scan prepends a line starting with [harness: subagent output matched instruction-shaped pattern(s): when the report imitates a tag like <system-reminder> or mentions permission settings such as bypassPermissions or --dangerously-skip-permissions .
Permission-setting mentions get the marker line, but the text itself stays as written.
The scan doesn’t judge whether content is malicious, and it doesn’t change what an instruction in a report can do: a tool call the report leads Claude to make still goes through the session’s permission checks and sandboxing .
It isn’t a substitute for restricting what a subagent can reach .
Subagent output scanning requires Claude Code v2.1.210 or later.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Spawn nested subagents As of Claude Code v2.1.172, a subagent can spawn its own subagents.
Use this when a delegated task itself splits into parallel subtasks, such as a reviewer subagent that dispatches a verifier per finding, so the intermediate output never reaches your main conversation.
  - now: ​ Let subagents spawn their own subagents By default, a subagent can spawn subagents of its own, up to three layers below the main conversation.
At the depth limit, Claude Code withholds the Agent tool from every subagent except a fork , so a subagent at the limit does its delegated work itself and returns one summary.
A fork at the limit keeps Agent in its inherited tool list, but the tool returns an error instead of spawning.
Nested subagents suit a delegated task that itself splits into parallel subtasks, such as a reviewer subagent that dispatches a verifier per finding, so the intermediate output never reaches your main conversation.
- **new-claim** — adds a capability claim not previously upstream
  - now: To change the limit, set CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH to the number of subagent layers you want below your main conversation.
For example, this entry in settings.json caps nesting at two layers: { "env" : { "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH" : "2" } } With this value, your subagents can delegate to a second layer of their own, and that second layer can’t delegate further.
Set 1 to turn nesting off.
- **new-claim** — adds a capability claim not previously upstream
  - now: To keep one subagent from spawning while nesting is on, such as a reviewer that should stay read-only, omit Agent from its tools list or add it to disallowedTools .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The Running tab in /agents lists running subagents as a flat list.
Depth is counted as the number of subagent levels below the main conversation, regardless of whether each level runs in the foreground or background .
A subagent at depth five doesn’t receive the Agent tool and can’t spawn further.
The limit is fixed and not configurable.
As of Claude Code v2.1.187, a background subagent’s depth is fixed when it is first spawned, and resuming it later doesn’t change that depth.
For example, if your main conversation spawns subagent A, and A spawns a background subagent B at depth two, B is still at depth two when you resume it directly from the main conversation.
Resuming a subagent from a shallower context doesn’t let it spawn additional levels that the depth limit already prevented.
To prevent a specific subagent from spawning others, omit Agent from its tools list or add it to disallowedTools .
A fork still can’t spawn another fork.
It can spawn other subagent types, and those count toward the depth limit.
  - now: Earlier versions used different defaults: v2.1.172 through v2.1.216 : subagents could nest by default, up to five layers deep, and the limit couldn’t be changed.
v2.1.217 through v2.1.218 : the limit defaulted to one, so a subagent couldn’t spawn its own unless you raised it; v2.1.219 raised the default to three.
​ Session subagent limit Three separate limits control subagent use, each with its own variable: this one caps the total spawned over a session, the concurrent subagent limit stops Claude from spawning more while too many are running, and the depth limit caps how deeply subagents nest.
By default, Claude can spawn at most 200 subagents per session.
To raise the limit, set CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION to any positive whole number; there is no upper bound, but the limit can’t be turned off.
Requires Claude Code v2.1.212 or later.
Every subagent Claude spawns with the Agent tool counts toward the limit: nested subagents, forks , and background subagents, including subagents that a workflow ’s agents spawn with the Agent tool.
An in-session fork you start yourself with /subtask counts too: it spends the same budget, though the limit blocks only subagents Claude spawns with the Agent tool, so your own /subtask still starts after Claude reaches the limit.
A session you create with /fork doesn’t count; it runs as a separate background session with its own budget.
Before v2.1.212, the in-session fork was named /fork .
Agents a workflow script spawns with agent() don’t count; workflows have their own per-run limit.
A finished subagent still counts.
When Claude reaches the limit, the Agent tool fails with Subagent spawn limit reached , and the error tells Claude to complete the remaining work directly with its own tools.
Run /clear to reset the count and start a new conversation with the full budget.
If work that can still spawn subagents survives the clear, such as a running workflow, the count carries over instead.
​ Concurrent subagent limit By default, when 20 subagents are running in a session, spawning another with the Agent tool fails with Concurrent subagent limit reached , and the error tells Claude not to retry.
Spawning succeeds again when the running count drops below the limit.
To change the limit, set CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS to any positive whole number.
Sessions with ultracode active are exempt: the limit isn’t enforced there.
Requires Claude Code v2.1.217 or later.
The limit blocks only subagents Claude spawns with the Agent tool, but other runs occupy the same slots: An in-session fork you start with /subtask takes a slot while it runs and is never blocked by the limit.
Resuming a subagent that already finished takes a fresh slot without checking the limit, so resumes can push the running count past it.
Agents that other features run, such as workflow agents and agent team teammates, follow their own limits instead.
The session subagent limit separately caps the total Claude spawns over the whole session.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: CLAUDE.md and memory : every level of the memory hierarchy the main conversation loads, including ~/.claude/CLAUDE.md , project rules, CLAUDE.local.md , and managed policy files.
  - now: CLAUDE.md files : every level of the CLAUDE.md hierarchy the main conversation loads, including ~/.claude/CLAUDE.md , project rules, CLAUDE.local.md , and managed policy files.
- **new-claim** — adds a capability claim not previously upstream
  - now: Sibling roster : a system reminder listing main and every other named agent in the session, each a valid to value for SendMessage .
Requires Claude Code v2.1.206 or later.
The roster appears only when the subagent’s tools include SendMessage and at least one other agent has a name, whether Claude named it when spawning it or it runs as an agent team teammate.
It is a snapshot taken when the subagent starts, so agents named later don’t appear.
- **new-claim** — adds a capability claim not previously upstream
  - now: Some main-conversation state never reaches a non-fork subagent: Output style : a subagent runs its own system prompt, so your output style doesn’t shape its responses, except in a fork .
Auto memory : the main conversation’s auto memory isn’t loaded.
To give a subagent persistent memory of its own, use the memory field .
Context window size : a subagent’s context window is sized by its own model, not the parent’s.
Delegating to a model with a smaller window gives that subagent the smaller window.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude uses the SendMessage tool with the agent’s ID as the to field to resume it.
The SendMessage tool is always available for resuming subagents by agent ID or name.
Structured team-protocol messages such as shutdown_request and plan_approval_response require agent teams to be enabled.
To resume a subagent, ask Claude to continue the previous work: Use the code-reviewer subagent to review the authentication module [Agent completes] Continue that code review and now analyze the authorization logic [Claude resumes the subagent with full context from previous conversation] If a stopped subagent receives a SendMessage , it auto-resumes in the background without requiring a new Agent invocation.
  - now: Claude uses the SendMessage tool with the agent’s ID or name as the to field to resume it.
SendMessage doesn’t require agent teams to be enabled; only structured team-protocol messages such as shutdown_request and plan_approval_response do.
To resume a subagent, ask Claude to continue the previous work: Use the code-reviewer subagent to review the authentication module [Agent completes] Continue that code review and now analyze the authorization logic [Claude resumes the subagent with full context from previous conversation] A completed subagent that receives a SendMessage auto-resumes in the background without a new Agent invocation.
The same applies to a subagent that Claude stopped with the TaskStop tool.
As of v2.1.191, a subagent you stopped yourself, with x in /tasks or an SDK stop_task request, doesn’t auto-resume.
The SendMessage call returns a refusal telling Claude the agent was cancelled.
Type into that subagent’s transcript in the subagent panel to resume it yourself, which clears the stop so later SendMessage calls can auto-resume it again.
Resuming starts a new run of the agent under the same ID, so a subagent that had already failed or completed shows as running again in the task list and in the Agent SDK’s task events.
Before v2.1.205, it kept showing its earlier failed or completed status while the resumed run was working.
As of v2.1.199, SendMessage checks that a name still refers to the same agent it reached earlier in the conversation.
If a newer agent has taken the name, such as a re-spawned background agent that reused it, Claude Code refuses the send rather than delivering it to the wrong agent, and the error reports which agent the name now reaches so Claude can retarget.
To reach the earlier agent while it’s still running, Claude addresses it by the agent ID it received when it spawned that agent.
The check is scoped to the current conversation and resets on /clear .
As of v2.1.198, a subagent treats messages from the agent that launched it as normal task direction, including mid-task course corrections, and acts on them within its own permission settings.
Two limits still hold regardless of who sent the message: no message from any agent counts as your approval for a pending permission prompt, and no agent message can change a subagent’s permission settings, CLAUDE.md , or configuration.
Only the permission system or your own messages can grant approval.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Automatic cleanup : transcripts are cleaned up based on the cleanupPeriodDays setting, which defaults to 30 days.
  - now: Automatic cleanup : Claude Code deletes subagent transcripts after the cleanupPeriodDays retention period, 30 days by default.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Fork the current conversation Forked subagents require Claude Code v2.1.117 or later.
From v2.1.161 the /fork command is enabled by default; on earlier versions it requires setting the CLAUDE_CODE_FORK_SUBAGENT environment variable to 1 .
  - now: ​ Fork the current conversation Run a forked subagent with /subtask , which requires Claude Code v2.1.212 or later.
When agent view is turned off , /subtask isn’t available and /fork starts the forked subagent instead; otherwise /fork copies the whole session into a new background session .
Before v2.1.212, the forked-subagent command was /fork .
It was enabled by default on v2.1.161 or later; on v2.1.117 through v2.1.160 it required setting the CLAUDE_CODE_FORK_SUBAGENT environment variable to 1 , unless a server-side rollout enabled it.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Spawns without a subagent type still use the general-purpose subagent, and named subagents such as Explore still spawn as before.
Every subagent spawn runs in the background , whether it is a fork or a named subagent.
Set CLAUDE_CODE_DISABLE_BACKGROUND_TASKS to 1 to keep spawns synchronous.
You can start a fork yourself with /fork followed by a directive, with or without the variable set.
Claude Code names the fork from the first words of the directive.
The following example forks the conversation to draft test cases while you continue with the implementation in the main session: /fork draft unit tests for the parser changes so far The fork appears in a panel below your prompt and runs in the background while you keep working.
  - now: When Claude doesn’t request a type, it still gets the general-purpose subagent, and named subagents such as Explore still spawn as before.
Every subagent runs in the background , whether it is a fork or a named subagent.
Set CLAUDE_CODE_DISABLE_BACKGROUND_TASKS to 1 to keep subagents synchronous.
You can start a fork yourself with /subtask followed by a task, with or without the variable set.
On v2.1.161 through v2.1.211 the command is /fork .
Claude Code names the fork from the first words of the task.
The following example forks the conversation to draft test cases while you continue with the implementation in the main session: /subtask draft unit tests for the parser changes so far The fork appears in a panel below your prompt and runs in the background while you keep working.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use these keys to interact with the panel: Key Action ↑ / ↓ Move between rows Enter Open the selected fork’s transcript and send it follow-up messages x Dismiss a finished fork or stop a running one Esc Return focus to the prompt input ​ How forks differ from named subagents A fork inherits everything the main session has at the moment it spawns.
  - now: Use these keys to interact with the panel: Key Action ↑ / ↓ Move between rows Enter Open the selected fork’s transcript and send it follow-up messages x Dismiss a finished fork or stop a running one Esc Return focus to the prompt input With a fork’s or subagent’s transcript open, follow-up messages and skills go to that agent, but built-in commands still run in your main conversation.
As of v2.1.199, typing /model or /fast in that view shows a notice that it changes the main conversation’s model or fast mode, not the viewed agent’s, instead of running it silently.
​ How forks differ from named subagents A fork inherits everything the main session has at the moment it spawns.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Fork Named subagent Context Full conversation history Fresh context with the prompt you pass System prompt and tools Same as main session From the subagent’s definition file Model Same as main session From the subagent’s model field Permissions Prompts surface in your terminal Prompts surface in your main session when running in the background Prompt cache Shared with main session Separate cache Because a fork’s system prompt and tool definitions are identical to the parent, its first request reuses the parent’s prompt cache .
  - now: Fork Named subagent Context Full conversation history Fresh context with the prompt you pass System prompt and tools Same as main session From the subagent’s definition file , filtered for background runs Model Same as main session From the subagent’s model field Permissions Prompts surface in your terminal Prompts surface in your main session when running in the background Prompt cache Shared with main session Separate cache Because a fork’s system prompt and tool definitions are identical to the parent, its first request reuses the parent’s prompt cache .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This example shows how to design a focused subagent with limited tool access (no Edit or Write) and a detailed prompt that specifies exactly what to look for and how to format output.
  - now: This example shows how to design a focused subagent with limited tool access that excludes Edit and Write, and a detailed prompt that specifies exactly what to look for and how to format output.
- **new-claim** — adds a capability claim not previously upstream
  - now: The system prompt tells the subagent to refuse write requests, so the hook is a backstop: if the subagent attempts a write anyway, Claude Code blocks the command and the subagent sees the Blocked: Write operations not allowed.
Use SELECT queries only.
message.
