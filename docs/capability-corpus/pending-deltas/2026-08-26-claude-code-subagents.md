# Pending delta — claude-code-subagents

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/sub-agents`
> Projection target: `claude-code/background-agents.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-26T13:36:48Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Use the /agents command Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Spawn nested subagents Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
Copy page Subagents are specialized AI assistants that handle specific types of tasks.
  - now: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Cross-session messaging Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Choose the subagent scope Write subagent files Supported frontmatter fields Subagent files Claude Code skips Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background Subagent names API errors in subagents Subagent output scanning Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Let subagents spawn their own subagents Concurrent subagent limit Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from other subagents Turn fork mode on or off Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
Copy page Copy page Subagents are specialized AI assistants that handle specific types of tasks.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: For sessions that communicate with each other, see agent teams .
  - now: For separate sessions that pass messages to each other, see cross-session messaging .
For a coordinated team of sessions Claude spawns and supervises, see agent teams .
- **removal** — removes a previously-present capability claim
  - was: Claude Code includes several built-in subagents like Explore , Plan , and general-purpose .
You can also create custom subagents to handle specific tasks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Each inherits the parent conversation’s permissions with additional tool restrictions.
  - now: Each inherits the parent conversation’s permissions; most run with a restricted tool set.
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
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Agent Model When Claude uses it statusline-setup Sonnet When you run /statusline to configure your status line claude-code-guide Haiku When you ask questions about Claude Code features Built-in subagents are always registered in interactive sessions.
  - now: Agent Model When Claude uses it claude Inherits When a task doesn’t fit a more specialized agent.
A catch-all with every tool available to subagents .
Also the default agent for a dispatched background session ; which permission mode it starts in depends on how the session was started statusline-setup Sonnet When you run /statusline to configure your status line claude-code-guide Haiku When you ask questions about Claude Code features Built-in subagents are registered by default in interactive sessions.
- **new-claim** — adds a capability claim not previously upstream
  - now: To remove only the built-in Explore and Plan subagents, set CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1 .
Claude reads and explores files directly instead of delegating to them.
Requires Claude Code v2.1.198 or later.
- **new-claim** — adds a capability claim not previously upstream
  - now: An Agent tool call that omits subagent_type fails with subagent_type is required when the session has no general-purpose subagent to fall back on.
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
In the transcript, the delegation appears as a tool call row showing the subagent’s name followed by a short task description, such as code-improver (Suggest code improvements) .
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
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Directories added with --add-dir are also scanned: a .claude/agents/ folder inside an added directory loads alongside project subagents.
  - now: When you add a directory with --add-dir or /add-dir , Claude Code also loads its .claude/agents/ folder, alongside your project subagents.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Keep name values unique across the whole tree: if two files within one scope declare the same name, Claude Code loads only one of them.
As of v2.1.196, running /doctor reports same-scope duplicate agent names and shows which definition is active.
  - now: Keep name values unique across the whole tree: if two files under the same .claude/agents/ directory, including its subfolders, declare the same name, Claude Code loads only one of them, chosen by filesystem read order rather than a documented precedence.
Across nested project directories, the definition closest to the working directory wins, as described above.
The /doctor setup checkup reports files in the same directory that share a name and proposes renaming or removing all but one.
Before v2.1.205, /doctor opened a diagnostics screen that listed duplicates and showed which definition was active.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Analyze errors, identify root causes, and provide fixes." } } '@ The --agents flag accepts JSON with the same frontmatter fields as file-based subagents: description , prompt , tools , disallowedTools , model , permissionMode , mcpServers , hooks , maxTurns , skills , initialPrompt , memory , effort , background , isolation , and color .
  - now: Analyze errors, identify root causes, and provide fixes." } } '@ The --agents flag accepts JSON with a prompt field plus these frontmatter fields: description , tools , disallowedTools , model , permissionMode , mcpServers , hooks , maxTurns , skills , initialPrompt , memory , effort , background , and isolation .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: They appear in /agents alongside your custom subagents.
  - now: They load automatically alongside your custom subagents and appear in the @-mention typeahead under their scoped name.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Write subagent files Subagent files use YAML frontmatter for configuration, followed by the system prompt in Markdown: Subagents are loaded at session start.
If you add or edit a subagent file directly on disk, restart your session to load it.
Subagents created through the /agents interface take effect immediately without a restart.
--- name : code-reviewer description : Reviews code for quality and best practices tools : Read, Glob, Grep model : sonnet --- You are a code reviewer.
  - now: ​ Write subagent files Subagent files use YAML frontmatter for configuration, followed by the system prompt in Markdown: Claude Code watches ~/.claude/agents/ and .claude/agents/ .
When you add or edit a subagent file on disk, or ask Claude to write one for you, Claude Code detects the change within a few seconds and the next delegation uses the updated definition, with no restart needed.
Three cases still need a restart: The watcher covers only directories that existed when the session started, so after creating a scope’s first agent file in a new agents directory, restart to load it.
Claude Code doesn’t watch .claude/agents/ inside directories added with --add-dir or /add-dir , so after adding or editing a subagent there, restart to load the change.
Sessions started with --disable-slash-commands don’t watch these directories at all.
.claude/agents/code-reviewer.md --- name : code-reviewer description : Reviews code for quality and best practices tools : Read, Glob, Grep model : sonnet --- You are a code reviewer.
- **new-claim** — adds a capability claim not previously upstream
  - now: In non-interactive mode , pass --append-subagent-system-prompt to append your text to the end of every subagent’s system prompt, nested subagents included, apart from a forked subagent , which reuses the conversation’s own prompt.
Requires Claude Code v2.1.205 or later.
- **new-claim** — adds a capability claim not previously upstream
  - now: A subagent with isolation: worktree runs its Bash and PowerShell commands inside its worktree.
A command whose working directory resolves to your main checkout instead, for example because the worktree directory was removed while the subagent was running, fails with an error.
Before v2.1.203, such a command could run in the main checkout.
This working-directory check covers the whole repository containing the directory you launched Claude Code from.
When your session runs in a linked worktree of its own, the check also covers the main checkout that worktree is linked from.
Before v2.1.210, the check covered only the launch directory itself.
A command whose working directory resolved elsewhere in the same repository, such as the repository root when you launched Claude Code from a monorepo subdirectory, ran there instead of failing.
For Bash commands, Claude Code also checks the command itself in two ways: It blocks a command that redirects git into the main checkout.
It refuses a command whose shape it can’t verify stays inside the worktree.
This refusal applies even to a command that runs no git.
The redirect vectors and the shape rules are listed under How Claude Code enforces isolation .
PowerShell commands get only the working-directory check.
Monitor commands go through the same working-directory and command-content checks as Bash commands.
When the main conversation itself runs isolated in a worktree, Claude Code applies the same checks to the session and to every subagent it spawns, including subagents without isolation: worktree ; see How Claude Code enforces isolation .
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
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Enables cross-session learning background No Set to true to always run this subagent as a background task .
Default: false effort No Effort level when this subagent is active.
  - now: Enables cross-session learning background No Set to true to keep this subagent in the background even when Claude asks to run it in the foreground.
Where fork mode is on, Claude Code already runs the subagents Claude spawns in the background effort No Effort level when this subagent is active.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Prepended to any user-provided prompt ​ Choose a model The model field controls which AI model the subagent uses: Model alias : use one of the available aliases: sonnet , opus , haiku , or fable Full model ID : use a full model ID such as claude-opus-4-8 or claude-sonnet-5 .
  - now: Prepended to any user-provided prompt ​ Subagent files Claude Code skips Claude Code skips a file in a project, user, or managed agents directory, or in one under a directory you add with --add-dir , without reporting it in the session, when the frontmatter has any of these problems: No name : Claude Code treats the file as documentation kept beside your agents.
A name that starts with - or contains : : Claude Code skips the file and writes an error to the debug log.
See the name row in the table above.
A name but no description : Claude Code skips the file and writes the reason to the debug log.
YAML that doesn’t parse : Claude Code reads no fields from the file, skips it, and writes the parse error to the debug log.
To see the debug log, run Claude Code with --debug .
A plugin subagent whose frontmatter has no name or doesn’t parse still loads, under its filename.
Check an agents directory before a session To find files in an agents directory whose frontmatter doesn’t parse, run claude plugin validate against the directory, for example .claude/agents or ~/.claude/agents .
Claude Code checks only the directory you name , and doesn’t flag a file whose frontmatter parses but has no name .
Requires Claude Code v2.1.233 or later.
​ Choose a model The model field controls which AI model the subagent uses: Model alias : use one of the available aliases: sonnet , opus , haiku , or fable Full model ID : use a full model ID such as claude-opus-5 or claude-sonnet-5 .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The environment variable, per-invocation parameter, and frontmatter values are checked against your organization’s availableModels allowlist.
A value that resolves to an excluded model is not used and the subagent runs on the inherited model instead.
  - now: Claude Code checks the environment variable, per-invocation parameter, and frontmatter values against your organization’s availableModels allowlist.
For a blocked value, it substitutes another model: When the blocked value is a family alias such as opus , Claude Code runs the subagent on the newest version of that family the allowlist permits, following the same substitution rules and provider scope as /model .
Before v2.1.222, Claude Code ran the subagent on the inherited model for a blocked family alias as well.
For any other blocked value, on providers where that substitution doesn’t operate, or when the allowlist permits no version of the family, Claude Code runs the subagent on the inherited model instead.
In interactive sessions, Claude Code shows a warning naming the requested model and the model the subagent runs on, for either substitution.
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
ListAgents follows these filters like any built-in tool: a foreground subagent inherits it in sessions where cross-session messaging is enabled, and a background subagent doesn’t keep it.
Teammates in agent teams additionally keep the task tools and cron tools: TaskCreate , TaskGet , TaskList , TaskUpdate , CronCreate , CronDelete , and CronList .
In a session without the Task tools , Claude Code doesn’t provide the task tools to subagents either, even when the subagent runs a different model.
An in-process teammate follows your session the same way, while a teammate in its own split pane runs as a separate Claude Code process, so its own model decides.
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
  - was: Inline servers defined here are connected when the subagent starts and disconnected when it finishes.
  - now: Inline servers defined here are connected when the subagent starts, subject to the trust rule for the agent file’s folder , and disconnected when it finishes.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The mcpServers field applies in both contexts where an agent file can run: As a subagent, spawned through the Agent tool or an @-mention As the main session, launched with --agent or the agent setting When the agent is the main session, inline server definitions connect at startup alongside servers from .mcp.json and settings files.
  - now: The mcpServers field applies in both contexts where an agent file can run: As a subagent, spawned through the Agent tool or an @-mention As the main session, launched with --agent or the agent setting When the agent is the main session, inline server definitions connect at startup alongside servers from .mcp.json and settings files, under the same trust rule for the agent file’s folder .
In /mcp , a remote (HTTP or SSE) server you’ve used before can show the cached status instead; Claude Code connects it when Claude first calls one of its tools.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Inline definitions use the same schema as .mcp.json server entries ( stdio , http , sse , ws ), keyed by the server name.
  - now: Inline definitions use the same schema as .mcp.json server entries, keyed by the server name, and support the stdio , http , sse , and ws types.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: As of v2.1.153, the MCP restrictions that apply to the main session also cover servers declared in subagent frontmatter: --strict-mcp-config and --bare Enterprise managed MCP configuration allowedMcpServers and deniedMcpServers policies When one of these blocks a server, Claude Code skips it and shows a warning naming the blocked servers.
  - now: Claude Code loads an inline server from an agent file in your project’s .claude/agents/ directory, or in an --add-dir directory’s .claude/agents/ , only after you trust the folder the agent file came from .
Before v2.1.238, Claude Code loaded these servers without checking trust.
Trust that doesn’t count : a parent folder’s trust, and the automatic trust a -p or SDK session gets for hooks in settings files Until then : Claude Code skips every inline server in that agent file and writes the exact projects["<path>"].hasTrustDialogAccepted key for ~/.claude.json to the debug log --add-dir directories : a directory outside your trusted workspace’s repository needs its own trust entry, since its .claude/agents/ files don’t inherit your workspace’s trust Claude Code loads two kinds of server without checking trust for the folder the agent file came from: A name that references a server you already configured An inline server in an agent file from ~/.claude/agents/ , in one you pass with --agents or the SDK agents option, or in one that managed settings supplies As of v2.1.153, the MCP restrictions that apply to the main session also cover servers declared in subagent frontmatter: --strict-mcp-config and --bare Enterprise managed MCP configuration allowedMcpServers and deniedMcpServers policies When one of these blocks a server, Claude Code skips it and shows a warning naming the blocked servers.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Permission modes The permissionMode field controls how the subagent handles permission prompts.
Subagents inherit the permission context from the main conversation and can override the mode, except when the parent mode takes precedence as described below.
Mode Behavior default Standard permission checking with prompts acceptEdits Auto-accept file edits and common filesystem commands for paths in the working directory or additionalDirectories auto Auto mode : a background classifier reviews commands and protected-directory writes dontAsk Auto-deny permission prompts (explicitly allowed tools still work) bypassPermissions Skip permission prompts plan Plan mode (read-only exploration) Use bypassPermissions with caution.
  - now: ​ Permission modes Set permissionMode to choose the permission mode a subagent runs in.
Use the modes’ config values, so Manual mode is default .
If you leave it unset, the subagent inherits the main conversation’s mode, which starts as auto mode on Pro, Max, and Team plans unless your settings or your organization change it.
Setting it overrides that mode, except in the cases described below.
Mode Behavior default Manual mode: prompts for permission acceptEdits Auto-accept file edits and common filesystem commands for paths in the working directory or additionalDirectories auto Auto mode : a background classifier reviews commands and protected-directory writes dontAsk Auto-deny permission prompts.
Explicitly allowed tools still work; AskUserQuestion , connector tools your organization set to ask , and MCP tools marked requiresUserInteraction are denied even if you’ve allowed them bypassPermissions Skip permission prompts plan Plan mode (read-only exploration) Use bypassPermissions with caution.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Explicit ask rules and root and home directory removals such as rm -rf / still prompt.
  - now: Even in this mode, the actions no mode auto-approves still apply.
- **new-claim** — adds a capability claim not previously upstream
  - now: If bypass mode is disabled by permissions.disableBypassPermissionsMode , Claude Code ignores permissionMode: bypassPermissions in the frontmatter and the subagent runs with the parent session’s mode.
Before v2.1.223, Claude Code applied the frontmatter mode even with bypass disabled.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: If a listed skill is missing or disabled, Claude Code skips it and logs a warning to the debug log.
  - now: This includes the bundled /verify skill: only you can run it, so it can’t be preloaded either.
If a listed skill is missing or disabled, for example by your organization’s policy, Claude Code skips it and logs a warning to the debug log.
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
This is a stricter rule than the one for hooks in settings files: trusting a parent folder isn’t enough, and a -p session doesn’t count as trusted.
What runs before you trust a folder compares the two.
Before v2.1.218, frontmatter hooks could run from folders you hadn’t trusted, including in non-interactive sessions.
- **new-claim** — adds a capability claim not previously upstream
  - now: While you type this form the typeahead shows file matches rather than agents.
The agent mention still resolves when you submit.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: This works with built-in and custom subagents, and the choice persists when you resume the session.
  - now: This works with built-in and custom subagents, and the choice persists when you resume the session: Claude Code restores the agent’s system prompt, tool restrictions, and model along with the conversation.
If the agent no longer exists when you resume, the session continues with the default tools and system prompt and shows a warning naming the agent .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: As of v2.1.186, when a background subagent reaches a tool call that needs permission, the prompt surfaces in your main session and names the subagent that is asking.
  - now: When a background subagent reaches a tool call that needs permission, Claude Code surfaces the prompt in your main session and names the subagent that is asking.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude decides whether to run subagents in the foreground or background based on the task.
You can also: Ask Claude to “run this in the background” Press Ctrl+B to background a running task To disable all background task functionality, set the CLAUDE_CODE_DISABLE_BACKGROUND_TASKS environment variable to 1 .
See Environment variables .
When CLAUDE_CODE_FORK_SUBAGENT is set to 1 , every subagent spawn runs in the background regardless of the background field.
Permission prompts from these background subagents surface in your main session as described above.
  - now: For each subagent Claude spawns with the Agent tool, Claude Code picks foreground or background from the first of these cases that applies: If an in-process agent team teammate spawned the subagent, Claude Code runs it in the foreground.
Claude Code refuses with an error to spawn a teammate’s subagent whose definition sets background: true .
Where fork mode is off and you haven’t turned background tasks off , Claude Code also refuses with an error when a teammate sets run_in_background: true .
If you set CLAUDE_CODE_DISABLE_BACKGROUND_TASKS to 1 , Claude Code runs the subagent in the foreground, in every kind of session and whether or not fork mode is on.
Where fork mode is on, as it is by default in an interactive session, Claude Code runs the subagent in the background, forks and non-fork subagents alike, and Claude can’t ask for the foreground.
Where fork mode is off, Claude runs the subagent in the background by default and in the foreground when it needs the result before continuing.
Fork mode is off in non-interactive mode with -p and in the Agent SDK unless you turn it on.
To keep a particular subagent in the background even when Claude wants the result, set its frontmatter background field to true .
For a skill with context: fork , Claude Code follows the rules in Run skills in a subagent instead, whether or not fork mode is on.
Background subagents run with a smaller built-in tool set than foreground subagents, except for conversation forks, and they surface every permission prompt in your main session.
When you answer one of those prompts with a choice that lasts beyond that one tool call, such as a grant that lasts for the rest of the session, Claude Code applies your answer to the whole session, including your main conversation.
A background subagent’s results reach Claude as a completion notification in a later turn.
Claude waits for that notification before reporting the subagent’s results, and if you ask about progress first, it reports that the subagent is still running.
Before v2.1.211, Claude sometimes reported results for a background subagent that hadn’t finished.
You can also steer this yourself: Where fork mode is off, ask Claude to run a task in the background or in the foreground Press Ctrl+B to background a running task Claude Code clears a background subagent’s row from the subagent panel below the prompt input in one of two ways, depending on how the subagent ended: When a subagent finishes successfully, Claude Code removes its row immediately and, except in screen reader mode , shows /tasks to see subagents in the footer for 30 seconds.
During those 30 seconds, run /tasks and press Enter on the subagent to open its transcript.
Before v2.1.232, Claude Code kept the row for 30 seconds after the subagent finished, the same as a failed one, and showed no footer hint.
When a subagent fails or you stop it, Claude Code keeps its row for 30 seconds.
To clear the row sooner, select it and press x .
A background subagent that completes stays listed in /tasks , marked done and sorted below running work, for the same window as the footer hint above.
Its detail view stays open when the subagent finishes.
Subagents that fail or that you stop leave the list.
Before v2.1.208, a completed subagent left the list the moment it finished and its detail view closed.
​ Subagent names Claude can give a subagent a name by passing a name parameter on the Agent tool call, and may do so on its own, without asking you first.
The name makes the subagent addressable: Claude can message or resume it by name after it finishes.
In an interactive session with agent teams enabled, a subagent that Claude spawns from the main conversation with a name launches as a teammate instead, unless the call is a fork or passes isolation on the call itself.
An isolation value in the subagent’s frontmatter doesn’t prevent it, and the teammate then runs in the main session’s working directory.
See How Claude starts agent teams .
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
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Subagents start fresh and may need time to gather context Use subagents when: The task produces verbose output you don’t need in your main context You want to enforce specific tool restrictions or permissions The work is self-contained and can return a summary Consider Skills instead when you want reusable prompts or workflows that run in the main conversation context rather than isolated subagent context.
For a quick question about something already in your conversation, use /btw instead of a subagent.
It sees your full context but has no tool access, and the answer is discarded rather than added to history.
​ Spawn nested subagents As of Claude Code v2.1.172, a subagent can spawn its own subagents.
Use this when a delegated task itself splits into parallel subtasks, such as a reviewer subagent that dispatches a verifier per finding, so the intermediate output never reaches your main conversation.
  - now: A subagent that isn’t a fork starts fresh and may need time to gather context Use subagents when: The task produces verbose output you don’t need in your main context You want to enforce specific tool restrictions or permissions The work is self-contained and can return a summary Consider Skills instead when you want reusable prompts or workflows that run in the main conversation context rather than isolated subagent context.
For a question about something already in your conversation, use /btw instead of a subagent.
It sees your full context but has no tool access, and the answer isn’t added to history.
​ Let subagents spawn their own subagents By default, a subagent can spawn subagents of its own, up to three layers below the main conversation.
At the depth limit, Claude Code withholds the Agent tool from every subagent except a fork , so a subagent at the limit does its delegated work itself and returns one summary.
A fork at the limit keeps Agent in its inherited tool list, but the tool returns an error instead of spawning.
Nested subagents suit a delegated task that itself splits into parallel subtasks, such as a reviewer subagent that dispatches a verifier per finding, so the intermediate output never reaches your main conversation.
- **new-claim** — adds a capability claim not previously upstream
  - now: To change the limit, set CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH to the number of subagent layers you want below your main conversation.
For example, this entry in settings.json caps nesting at two layers: { "env" : { "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH" : "2" } } With this value, your subagents can delegate to a second layer of their own, and that second layer can’t delegate further.
Set 1 to turn nesting off.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The subagent panel below the prompt input shows the full tree: each row displays a (+N) count of descendants, and as of v2.1.193, opening a row shows that subagent’s siblings and direct children with a path back to main .
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
  - now: To keep one subagent from spawning while nesting is on, such as a reviewer that should stay read-only, omit Agent from its tools list or add it to disallowedTools .
Claude Code shows nested subagents as a tree in the subagent panel below the prompt input and marks each row that still has descendants in the panel with a (+N) count of them.
Open a row to see that subagent’s siblings and direct children with a path back to main .
Earlier versions used different defaults: v2.1.172 through v2.1.216 : subagents could nest by default, up to five layers deep, and the limit couldn’t be changed.
v2.1.217 through v2.1.218 : the limit defaulted to one, so a subagent couldn’t spawn its own unless you raised it; v2.1.219 raised the default to three.
​ Concurrent subagent limit Two limits control subagent use, each with its own variable: this one stops Claude from spawning more subagents while too many are running, and the depth limit caps how deeply subagents nest.
There’s no limit on the total number of subagents Claude can spawn over a session.
By default, when 20 subagents are running in a session, spawning another with the Agent tool fails with Concurrent subagent limit reached , and the error tells Claude not to retry.
Spawning succeeds again when the running count drops below the limit.
To change the limit, set CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS to any positive whole number.
Sessions with ultracode active are exempt: the limit isn’t enforced there.
Requires Claude Code v2.1.217 or later.
The limit blocks only subagents Claude spawns with the Agent tool, but other runs occupy the same slots: An in-session fork you start with /subtask takes a slot while it runs and is never blocked by the limit.
Resuming a subagent that already finished takes a fresh slot without checking the limit, so resumes can push the running count past it.
Agents that other features run, such as workflow agents and agent team teammates, follow their own limits instead.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: CLAUDE.md and memory : every level of the memory hierarchy the main conversation loads, including ~/.claude/CLAUDE.md , project rules, CLAUDE.local.md , and managed policy files.
  - now: CLAUDE.md files : every level of the CLAUDE.md hierarchy the main conversation loads, including ~/.claude/CLAUDE.md , project rules, CLAUDE.local.md , and managed policy files.
- **new-claim** — adds a capability claim not previously upstream
  - now: Sibling roster : a system reminder listing main and every other named agent in the session, each a valid to value for SendMessage .
Requires Claude Code v2.1.206 or later.
The roster appears only when the subagent’s tools include SendMessage and at least one other agent has a name, whether Claude named it when spawning it or it runs as an agent team teammate.
It is a snapshot taken when the subagent starts, so agents named later don’t appear.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Resume subagents Each subagent invocation creates a new instance with fresh context.
  - now: Some main-conversation state never reaches a non-fork subagent: Output style : a subagent runs its own system prompt, so your output style doesn’t shape its responses, except in a fork .
Auto memory : the main conversation’s auto memory isn’t loaded.
To give a subagent persistent memory of its own, use the memory field .
Context window size : a subagent’s context window is sized by its own model, not the parent’s.
Delegating to a model with a smaller window gives that subagent the smaller window.
​ Resume subagents Each subagent invocation creates a new instance rather than continuing an earlier one.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude uses the SendMessage tool with the agent’s ID as the to field to resume it.
The SendMessage tool is always available for resuming subagents by agent ID or name.
Structured team-protocol messages such as shutdown_request and plan_approval_response require agent teams to be enabled.
To resume a subagent, ask Claude to continue the previous work: Use the code-reviewer subagent to review the authentication module [Agent completes] Continue that code review and now analyze the authorization logic [Claude resumes the subagent with full context from previous conversation] If a stopped subagent receives a SendMessage , it auto-resumes in the background without requiring a new Agent invocation.
  - now: Claude uses the SendMessage tool with the agent’s ID or name as the to field to resume it.
SendMessage doesn’t require agent teams to be enabled; only structured team-protocol messages such as shutdown_request and plan_approval_response do.
Beyond subagents and teammates, in sessions where cross-session messaging is enabled, Claude can use the same tool to message your other Claude Code sessions , on this machine or beyond it .
To resume a subagent, ask Claude to continue the previous work: Use the code-reviewer subagent to review the authentication module [Agent completes] Continue that code review and now analyze the authorization logic [Claude resumes the subagent with full context from previous conversation] A completed subagent that receives a SendMessage auto-resumes in the background without a new Agent invocation.
The same applies to a subagent that Claude stopped with the TaskStop tool.
As of v2.1.191, a subagent you stopped yourself, with x in /tasks or an SDK stop_task request, doesn’t auto-resume.
The SendMessage call returns a refusal telling Claude the agent was cancelled.
While that subagent’s row is still in the subagent panel , type into its transcript to resume it yourself, which clears the stop so later SendMessage calls can auto-resume it again.
Resuming starts a new run of the agent under the same ID, so a subagent that had already failed or completed shows as running again in the task list and in the Agent SDK’s task events.
Before v2.1.205, it kept showing its earlier failed or completed status while the resumed run was working.
As of v2.1.199, SendMessage checks that a name still refers to the same agent it reached earlier in the conversation.
If a newer agent has taken the name, such as a re-spawned background agent that reused it, Claude Code refuses the send rather than delivering it to the wrong agent, and the error reports which agent the name now reaches so Claude can retarget.
To reach the earlier agent while it’s still running, Claude addresses it by the agent ID it received when it spawned that agent.
The check is scoped to the current conversation and resets on /clear .
As of v2.1.198, a subagent treats messages from the agent that launched it as normal task direction, including mid-task course corrections, and acts on them within its own permission settings.
Two limits still hold regardless of who sent the message: no message from any agent counts as your approval for a pending permission prompt, and no agent message can change a subagent’s permission settings, CLAUDE.md , or configuration.
Only the permission system or your own messages can grant approval.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Automatic cleanup : transcripts are cleaned up based on the cleanupPeriodDays setting, which defaults to 30 days.
  - now: Automatic cleanup : Claude Code deletes subagent transcripts after the cleanupPeriodDays retention period, 30 days by default, following the retention sweep rules .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Fork the current conversation Forked subagents require Claude Code v2.1.117 or later.
From v2.1.161 the /fork command is enabled by default; on earlier versions it requires setting the CLAUDE_CODE_FORK_SUBAGENT environment variable to 1 .
Letting Claude itself spawn forks is experimental and may change in future releases.
This capability may also be enabled in interactive sessions as part of a staged rollout.
  - now: ​ Fork the current conversation Run a forked subagent with /subtask , which requires Claude Code v2.1.212 or later.
When agent view is turned off , /subtask isn’t available and /fork starts the forked subagent instead; otherwise /fork copies the whole session into a new background session .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Use a fork when a named subagent would need too much background to be useful, or when you want to try several approaches in parallel from the same starting point.
To control fork mode regardless of the staged rollout, set CLAUDE_CODE_FORK_SUBAGENT to 1 to enable it explicitly or to 0 to disable it.
The variable is honored in interactive mode and via the SDK or claude -p .
Enabling fork mode changes Claude Code in two ways: Claude can spawn a fork by requesting the fork subagent type explicitly.
Spawns without a subagent type still use the general-purpose subagent, and named subagents such as Explore still spawn as before.
Every subagent spawn runs in the background , whether it is a fork or a named subagent.
Set CLAUDE_CODE_DISABLE_BACKGROUND_TASKS to 1 to keep spawns synchronous.
You can start a fork yourself with /fork followed by a directive, with or without the variable set.
Claude Code names the fork from the first words of the directive.
The following example forks the conversation to draft test cases while you continue with the implementation in the main session: /fork draft unit tests for the parser changes so far The fork appears in a panel below your prompt and runs in the background while you keep working.
  - now: Use a fork when any other subagent would need too much background to be useful, or when you want to try several approaches in parallel from the same starting point.
Claude starts a fork by requesting the fork subagent type through the Agent tool.
You control whether it can with fork mode , which is on by default in interactive sessions.
You can start a fork yourself with /subtask followed by a task, whether or not fork mode is on.
On v2.1.161 through v2.1.211 the command is /fork .
Claude Code names the fork from the first words of the task.
The following example forks the conversation to draft test cases while you continue with the implementation in the main session: /subtask draft unit tests for the parser changes so far The fork appears in a panel below your prompt and runs in the background while you keep working.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Use these keys to interact with the panel: Key Action ↑ / ↓ Move between rows Enter Open the selected fork’s transcript and send it follow-up messages x Dismiss a finished fork or stop a running one Esc Return focus to the prompt input ​ How forks differ from named subagents A fork inherits everything the main session has at the moment it spawns.
A named subagent starts from its own definition.
Fork Named subagent Context Full conversation history Fresh context with the prompt you pass System prompt and tools Same as main session From the subagent’s definition file Model Same as main session From the subagent’s model field Permissions Prompts surface in your terminal Prompts surface in your main session when running in the background Prompt cache Shared with main session Separate cache Because a fork’s system prompt and tool definitions are identical to the parent, its first request reuses the parent’s prompt cache .
  - now: When a fork finishes successfully, Claude Code removes its row.
Claude Code keeps the row of a fork that failed or that you stopped for 30 seconds, the same as for any other background subagent .
Before v2.1.232, Claude Code kept a finished fork’s row for 30 seconds as well.
Use these keys to interact with the panel: Key Action ↑ / ↓ Move between rows Enter Open the selected fork’s transcript and send it follow-up messages x Stop the selected fork if it’s running, or dismiss its row if it’s no longer running.
On the main session row, or on the row of the fork whose transcript you opened with Enter , x types into the prompt instead Esc Return focus to the prompt input With a fork’s or subagent’s transcript open, follow-up messages and skills go to that agent, but built-in commands still run in your main conversation.
As of v2.1.199, typing /model or /fast in that view shows a notice that it changes the main conversation’s model or fast mode, not the viewed agent’s, instead of running it silently.
​ How forks differ from other subagents A fork inherits everything the main session has at the moment it spawns.
Any other subagent starts fresh from its definition.
Fork Non-fork subagent Context Full conversation history Fresh context with the prompt you pass System prompt and tools Same as main session From the subagent’s definition file , filtered for background runs Model Same as main session From the subagent’s model field Permissions Prompts surface in your terminal Prompts surface in your main session when running in the background Prompt cache Shared with main session Separate cache Because a fork’s system prompt and tool definitions are identical to the parent, its first request reuses the parent’s prompt cache .
- **removal** — removes a previously-present capability claim
  - was: ​ Limitations Setting CLAUDE_CODE_FORK_SUBAGENT=1 enables fork mode in interactive sessions, non-interactive mode , and the Agent SDK; setting it to 0 disables fork mode everywhere, including any server-side rollout.
- **new-claim** — adds a capability claim not previously upstream
  - now: ​ Turn fork mode on or off Claude Code turns fork mode on by default in interactive sessions and leaves it off by default in non-interactive mode with -p and in the Agent SDK.
The interactive default requires Claude Code v2.1.232 or later.
On earlier versions, set CLAUDE_CODE_FORK_SUBAGENT to 1 to turn fork mode on.
You can tell fork mode is on from how Claude Code handles the Agent tool: Claude can spawn a fork by requesting the fork subagent type.
When Claude doesn’t request a type, it gets the general-purpose subagent, if the session still has that type.
Subagents spawned from a definition, such as Explore, work as usual.
Claude Code runs the subagents Claude spawns in the background, forks and non-fork subagents alike, apart from the cases that stay in the foreground .
Claude Code also removes the Agent tool’s run_in_background parameter, so Claude can’t ask for the foreground.
Set the CLAUDE_CODE_FORK_SUBAGENT environment variable to override the defaults: 1 turns fork mode on in non-interactive mode and the Agent SDK as well 0 turns fork mode off in every kind of session To keep fork mode on but stop Claude from spawning forks, deny the fork subagent type with an Agent(fork) rule.
Claude Code still runs the subagents Claude spawns in the background, apart from the same cases that stay in the foreground .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This example shows how to design a focused subagent with limited tool access (no Edit or Write) and a detailed prompt that specifies exactly what to look for and how to format output.
  - now: This example shows how to design a focused subagent with limited tool access that excludes Edit and Write, and a detailed prompt that specifies exactly what to look for and how to format output.
- **new-claim** — adds a capability claim not previously upstream
  - now: The system prompt tells the subagent to refuse write requests, so the hook is a backstop: if the subagent attempts a write anyway, Claude Code blocks the command and the subagent sees the Blocked: Write operations not allowed.
Use SELECT queries only.
message.
