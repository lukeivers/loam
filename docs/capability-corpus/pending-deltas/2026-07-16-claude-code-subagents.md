# Pending delta — claude-code-subagents

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/sub-agents`
> Projection target: `claude-code/background-agents.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-16T13:05:50Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Use the /agents command Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Spawn nested subagents Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
  - now: Navigation Agents and parallel work Create custom subagents Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Agents and parallel work Overview Create custom subagents Agent view Run agent teams Dynamic workflows Isolate sessions with worktrees MCP Quickstart Reference Skills Extend Claude with skills Plugins Discover and install prebuilt plugins Create plugins Artifacts Share session output as artifacts Automation Automate with hooks Push external events to Claude Run prompts on a schedule Goals Programmatic usage Launch sessions from links Guides Monorepos and large repos Troubleshooting Troubleshoot installation and login Troubleshoot performance and stability Debug configuration Error reference On this page Built-in subagents Quickstart: create your first subagent Configure subagents Choose the subagent scope Write subagent files Supported frontmatter fields Choose a model Control subagent capabilities Available tools Restrict which subagents can be spawned Scope MCP servers to a subagent Permission modes Preload skills into subagents Enable persistent memory Conditional rules with hooks Disable specific subagents Define hooks for subagents Hooks in subagent frontmatter Project-level hooks for subagent events Work with subagents Understand automatic delegation Invoke subagents explicitly Run subagents in foreground or background API errors in subagents Common patterns Isolate high-volume operations Run parallel research Chain subagents Choose between subagents and main conversation Spawn nested subagents Manage subagent context What loads at startup Resume subagents Auto-compaction Fork the current conversation Observe and steer running forks How forks differ from named subagents Limitations Example subagents Code reviewer Debugger Data scientist Database query validator Next steps Agents and parallel work Create custom subagents Copy page Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
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
  - now: They load alongside your custom subagents and appear in the @-mention typeahead under their scoped name.
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
- **new-claim** — adds a capability claim not previously upstream
  - now: If no entry in the list resolves to a tool, the subagent fails to launch with an error naming the entries.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Defaults to inherit permissionMode No Permission mode : default , acceptEdits , auto , dontAsk , bypassPermissions , or plan .
  - now: Defaults to inherit permissionMode No Permission mode : default , acceptEdits , auto , dontAsk , bypassPermissions , plan , or manual as an alias for default .
The manual alias requires Claude Code v2.1.200 or later.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Enables cross-session learning background No Set to true to always run this subagent as a background task .
Default: false effort No Effort level when this subagent is active.
  - now: Enables cross-session learning background No Set to true to always run this subagent as a background task , even when Claude needs its result right away.
When unset, Claude chooses, and as of v2.1.198 it runs subagents in the background by default effort No Effort level when this subagent is active.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The environment variable, per-invocation parameter, and frontmatter values are checked against your organization’s availableModels allowlist.
A value that resolves to an excluded model is not used and the subagent runs on the inherited model instead.
  - now: Claude Code checks the environment variable, per-invocation parameter, and frontmatter values against your organization’s availableModels allowlist.
It skips a value that resolves to an excluded model and runs the subagent on the inherited model instead.
As of v2.1.198, subagents also inherit the main conversation’s extended thinking configuration: if thinking is on in your session, it’s on for the subagent, and if it’s off, it stays off.
There is no per-subagent thinking setting.
Before v2.1.198, subagents ran with extended thinking disabled regardless of the main conversation’s setting.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The following tools depend on the main conversation’s UI or session state and are not available to subagents, even when listed in the tools field: AskUserQuestion EnterPlanMode ExitPlanMode , unless the subagent’s permissionMode is plan ScheduleWakeup WaitForMcpServers To restrict tools, use either the tools field (allowlist) or the disallowedTools field (denylist).
This example uses tools to exclusively allow Read, Grep, Glob, and Bash.
  - now: The following tools depend on the main conversation’s UI or session state and aren’t available to subagents, even when listed in the tools field: AskUserQuestion EnterPlanMode ExitPlanMode , unless the subagent’s permissionMode is plan ScheduleWakeup WaitForMcpServers To restrict tools, use the tools field as an allowlist or the disallowedTools field as a denylist.
This example uses tools to allow only Read, Grep, Glob, and Bash.
- **new-claim** — adds a capability claim not previously upstream
  - now: When nothing in the tools list resolves to a tool, for example because every entry is misspelled or names a tool that isn’t available to subagents, Claude Code refuses to launch the subagent and the Agent tool returns an error naming the unresolved entries.
Before v2.1.208, that subagent launched with no tools and could return an empty or confusing result.
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
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Choose a scope based on how broadly the memory should apply: Scope Location Use when user ~/.claude/agent-memory/<name-of-agent>/ the subagent should remember learnings across all projects project .claude/agent-memory/<name-of-agent>/ the subagent’s knowledge is project-specific and shareable via version control local .claude/agent-memory-local/<name-of-agent>/ the subagent’s knowledge is project-specific but should not be checked into version control When memory is enabled: The subagent’s system prompt includes instructions for reading and writing to the memory directory.
  - now: Choose a scope based on how broadly the memory should apply: Scope Location Use when user ~/.claude/agent-memory/<name-of-agent>/ the subagent should remember learnings across all projects project .claude/agent-memory/<name-of-agent>/ the subagent’s knowledge is project-specific and shareable via version control local .claude/agent-memory-local/<name-of-agent>/ the subagent’s knowledge is project-specific but shouldn’t be checked into version control When memory is enabled: The subagent’s system prompt includes instructions for reading and writing to the memory directory.
- **removal** — removes a previously-present capability claim
  - was: Use user when the subagent’s knowledge is broadly applicable across projects, or local when the knowledge should not be checked into version control.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude decides whether to run subagents in the foreground or background based on the task.
You can also: Ask Claude to “run this in the background” Press Ctrl+B to background a running task To disable all background task functionality, set the CLAUDE_CODE_DISABLE_BACKGROUND_TASKS environment variable to 1 .
  - now: As of v2.1.198, subagents run in the background by default.
Claude runs a subagent in the foreground when it needs the result before continuing.
The default changes where a subagent runs, not what it’s allowed to do: background subagents still surface every permission prompt in your main session.
Before v2.1.198, Claude chose between foreground and background based on the task.
You can also steer this yourself: Ask Claude to run a task in the background or in the foreground Press Ctrl+B to background a running task A background subagent that completes stays listed in /tasks , marked done and sorted below running work, until the session cleans up its task list.
Its detail view stays open when the subagent finishes.
Subagents that fail or that you stop leave the list.
Before v2.1.208, a completed subagent left the list the moment it finished and its detail view closed.
To disable all background task functionality, set the CLAUDE_CODE_DISABLE_BACKGROUND_TASKS environment variable to 1 .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: When CLAUDE_CODE_FORK_SUBAGENT is set to 1 , every subagent spawn runs in the background regardless of the background field.
Permission prompts from these background subagents surface in your main session as described above.
  - now: When CLAUDE_CODE_FORK_SUBAGENT is set to 1 , every subagent spawn runs in the background and the frontmatter background field has no effect, because fork mode removes the run_in_background parameter from the Agent tool.
CLAUDE_CODE_DISABLE_BACKGROUND_TASKS takes precedence over fork mode and keeps subagent spawns in the foreground.
​ API errors in subagents As of v2.1.199, a subagent whose run ends on an API error, such as a usage limit or a repeated server error, reports that failure back to Claude instead of returning the error text as if it were the subagent’s findings.
What Claude receives depends on where the subagent ran: Foreground : if a rate limit, overload, or server error cuts off a subagent that already produced text output, the Agent tool returns that partial output with a note that the subagent was cut off and didn’t finish its task.
A subagent that produced nothing, or whose only output was tool calls, fails with Agent terminated early due to an API error , followed by the error detail.
In v2.1.199, a rate limit, overload, or server error that cut off the tool-calls-only shape returned an empty partial result containing only the cut-off note instead.
Background : the subagent is marked failed, and the message Claude receives when it ends names the API error and includes the subagent’s last output, so partial work isn’t lost.
Once the underlying API error clears, ask Claude to retry the task or resume the subagent .
- **removal** — removes a previously-present capability claim
  - was: The Running tab in /agents lists running subagents as a flat list.
- **new-claim** — adds a capability claim not previously upstream
  - now: Sibling roster : a system reminder listing main and every other named agent in the session, each a valid to value for SendMessage .
Requires Claude Code v2.1.206 or later.
The roster appears only when the subagent’s tools include SendMessage and at least one other agent has a name, whether Claude named it when spawning it or it runs as an agent team teammate.
It is a snapshot taken when the subagent starts, so agents named later don’t appear.
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
To reach the earlier agent while it’s still running, Claude addresses it by the agent ID from its spawn result.
The check is scoped to the current conversation and resets on /clear .
As of v2.1.198, a subagent treats messages from the agent that launched it as normal task direction, including mid-task course corrections, and acts on them within its own permission settings.
Two limits still hold regardless of who sent the message: no message from any agent counts as your approval for a pending permission prompt, and no agent message can change a subagent’s permission settings, CLAUDE.md , or configuration.
Only the permission system or your own messages can grant approval.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use these keys to interact with the panel: Key Action ↑ / ↓ Move between rows Enter Open the selected fork’s transcript and send it follow-up messages x Dismiss a finished fork or stop a running one Esc Return focus to the prompt input ​ How forks differ from named subagents A fork inherits everything the main session has at the moment it spawns.
  - now: Use these keys to interact with the panel: Key Action ↑ / ↓ Move between rows Enter Open the selected fork’s transcript and send it follow-up messages x Dismiss a finished fork or stop a running one Esc Return focus to the prompt input With a fork’s or subagent’s transcript open, follow-up messages and skills go to that agent, but built-in commands still run in your main conversation.
As of v2.1.199, typing /model or /fast in that view shows a notice that it changes the main conversation’s model or fast mode, not the viewed agent’s, instead of running it silently.
​ How forks differ from named subagents A fork inherits everything the main session has at the moment it spawns.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This example shows how to design a focused subagent with limited tool access (no Edit or Write) and a detailed prompt that specifies exactly what to look for and how to format output.
  - now: This example shows how to design a focused subagent with limited tool access that excludes Edit and Write, and a detailed prompt that specifies exactly what to look for and how to format output.
