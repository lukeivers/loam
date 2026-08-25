# Pending delta — claude-code-loop

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/commands`
> Projection target: `claude-code/loop.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-25T13:31:03Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Reference Commands Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Commands across a typical workflow All commands MCP prompts See also Reference Commands Copy page Complete reference for commands available in Claude Code, including built-in commands and bundled skills.
Copy page Commands control Claude Code from inside a session.
  - now: Navigation Reference Commands Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Commands across a typical workflow All commands How the command menu matches what you type MCP prompts See also Reference Commands Copy page Copy page Complete reference for commands available in Claude Code, including built-in commands and bundled skills.
Copy page Copy page Commands control Claude Code from inside a session.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Type / to see every command available to you, or type / followed by letters to filter.
  - now: Type / to see the commands available to you, or type / followed by letters to filter.
How the command menu matches what you type covers highlighting, typos, and the few commands Claude Code hides from the menu until you type their full name.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Text that follows the command name is passed to it as arguments.
  - now: Text that follows the command name becomes its arguments.
As of v2.1.199, skills are the exception: a skill invocation followed by more skills, such as /skill-a /skill-b do XYZ , loads every skill named at the start and passes the trailing text to each as arguments.
Up to six skills can be chained.
If you send a command while Claude is responding, Claude Code queues it and runs it after the current turn finishes.
Claude Code runs some commands immediately without interrupting the response, such as /status , /tasks , and /usage .
In fullscreen rendering , Claude Code also opens dialog commands such as /theme and /help immediately.
Before v2.1.234, Claude Code queued those dialogs until the turn finished.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use /mcp and /agents to set up any servers or subagents the project needs, and /permissions to set the approval rules you want.
  - now: Use /mcp to set up any servers the project needs, ask Claude to create any subagents you want, and run /permissions to set your approval rules.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /model and /effort adjust how much reasoning you’re spending.
When the conversation gets long, /context shows where the window is going and /compact summarizes it down; use /btw for a quick aside that shouldn’t bloat history.
Running work in parallel.
/agents opens the manager for the subagents Claude can delegate side tasks to, and /tasks lists what’s running in the background of the current session.
  - now: /model and /effort adjust which model you’re using and how much reasoning it applies.
When the conversation gets long, /context shows what’s filling the window and /compact summarizes it to free space.
Use /btw for a side question that shouldn’t add to the conversation history.
Run work in parallel.
Claude delegates side tasks to subagents , and /tasks lists the current session’s background work, including subagents that have finished.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , /review runs the same read-only review on a GitHub pull request, and /security-review gives a deeper read-only pass.
  - now: /diff shows what changed.
/code-review checks the current diff for correctness bugs and cleanups and can apply the findings with --fix ; pass a PR number, such as /code-review high 1234 , to review a pull request instead.
/review is an alias.
- **new-claim** — adds a capability claim not previously upstream
  - now: /security-review checks the diff for security vulnerabilities.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /resume and /branch let you return to or fork an earlier conversation.
  - now: /resume returns to an earlier conversation, /branch branches the current one to try a different direction, and /fork copies it into a new background session .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: /doctor and /debug diagnose install and runtime issues, and /feedback reports a bug with session context attached.
  - now: /doctor runs a setup checkup that diagnoses installation and configuration issues and can fix them, /debug diagnoses runtime issues, and /feedback reports a bug with session context attached.
- **new-claim** — adds a capability claim not previously upstream
  - now: /verify runs only when you invoke it.
Before v2.1.215, Claude could also run /verify on its own.
- **new-claim** — adds a capability claim not previously upstream
  - now: /deep-research runs only when you invoke it.
Before v2.1.218, Claude could also start it on its own.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For example, /desktop only shows on macOS and Windows when signed in with a Claude subscription, and /upgrade only shows on Pro and Max plans.
  - now: For example, /desktop only shows on macOS and x64 Windows when signed in with a Claude subscription, and /upgrade doesn’t show on Enterprise plans.
- **new-claim** — adds a capability claim not previously upstream
  - now: Type a partial path to see matching directory suggestions; press Tab to accept one.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: You can later resume the session from the added directory with --continue or --resume /advisor [model|off] Enable or disable the advisor tool , which consults a second model for guidance at key moments during a task.
Accepts opus , sonnet , fable ( v2.1.170+), or a full model ID.
Without an argument, opens a picker.
Requires Claude Code v2.1.98 or later /agents Manage agent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
  - now: A successful add runs your DirectoryAdded hooks .
When you run it while Claude is responding, Claude Code asks you to confirm the directory right away, and once you confirm, Claude’s next tool call in the same turn can access it.
Before v2.1.234, Claude Code queued the command until the turn finished /advisor [model|off] Enable or disable the advisor tool , which consults a second model for guidance at key moments during a task.
Accepts fable , opus , sonnet , or a full model ID.
fable requires Fable 5 access .
Without an argument, opens a picker /agents As of v2.1.198, running /agents prints a reminder to ask Claude to create or manage subagents , or to edit .claude/agents/ or ~/.claude/agents/ directly.
On v2.1.197 and earlier, opens an interactive interface for creating and managing subagent configurations /artifacts List the artifacts you own or that are shared with you, then attach one to the session, open it in your browser, or copy its link.
Available where artifacts are.
Requires Claude Code v2.1.208 or later; attaching with Enter requires v2.1.216 /auto-mode-setup Draft autoMode.environment entries from your project and recent sessions, then review the draft and save it to your user settings.
Requires a Pro, Max, or Team plan and Claude Code v2.1.228 or later.
On native Windows, requires v2.1.233 or later /autocompact [auto|<tokens>] Set the auto-compact window: how full the context window gets before Claude Code compacts automatically.
Pass a size such as 500k , or auto to return to the window tuned for your model.
Claude Code saves the value to user settings and applies it to the current session.
See Set the auto-compact window for accepted values and what overrides it.
Without an argument, opens a dialog that shows the current window.
Requires Claude Code v2.1.221 or later /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
- **new-claim** — adds a capability claim not previously upstream
  - now: To copy the conversation into a new background session while this one keeps running, use /fork .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: To hand a side task to a background subagent instead of switching into a copy yourself, use /fork /btw <question> Ask a quick side question without adding to the conversation /cd <path> Move this session to a new working directory.
The conversation’s prompt cache is preserved: the new directory’s CLAUDE.md is appended as a message instead of rebuilding the system prompt.
The session is relocated to the new directory’s project storage, so --resume and --continue find it from there.
Prompts you to trust the directory if you haven’t worked in it before.
  - now: To run a copy as a separate background session instead of switching into it, use /fork ; to hand a side task to a subagent that reports back into this conversation, use /subtask /btw [question] Ask a side question about the current session without adding to the conversation.
If you run /btw without a question, Claude Code shows your most recent side question so you can browse earlier answers; if you haven’t asked one yet, Claude Code prints a usage line.
Before v2.1.212, /btw required a question /bug [report] Report a bug or share your conversation.
You choose how much session history to include and confirm on a consent screen before anything is sent.
When you’re signed in to Anthropic on a first-party connection, the report goes to Anthropic; on a third-party provider, or without Anthropic credentials, Claude Code writes the report to a local archive under ~/.claude/feedback-bundles/ that you forward yourself.
In the VS Code extension , /bug opens the extension’s own feedback dialog instead; requires Claude Code v2.1.229 or later.
When you run it while Claude is responding, Claude Code opens the dialog immediately.
Before v2.1.232, Claude Code queued the command until the turn finished.
Alias: /share .
Before v2.1.212, /bug and /share were aliases of /feedback /cd <path> Move this session to a new working directory, keeping the conversation and its prompt cache.
Type a partial path to see matching directory suggestions; press Tab to accept one.
Claude Code prompts you to trust the workspace if you haven’t worked in it before, and --resume finds the moved session afterward.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Requires Claude Code v2.1.169 or later; earlier versions report Unknown command: /cd /chrome Configure Claude in Chrome settings /claude-api [migrate|managed-agents-onboard] Skill .
Load Claude API reference material for your project’s language (Python, TypeScript, Java, Go, Ruby, C#, PHP, or cURL) and Managed Agents reference.
Covers tool use, streaming, batches, structured outputs, and common pitfalls.
  - now: Requires Claude Code v2.1.169 or later /chrome Configure Claude in Chrome settings /claude-api [migrate|upgrade|managed-agents-onboard|prompt-audit] Skill .
Load Claude API and Managed Agents reference material for your project’s language.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Run /claude-api migrate to upgrade existing Claude API code to a newer model: Claude asks which files to scan and which model to target, then updates model IDs, thinking configuration, and other parameters that changed between versions.
Run /claude-api managed-agents-onboard for an interactive walkthrough that creates a new Managed Agent from scratch /clear [name] Start a new conversation with empty context.
The previous conversation stays available in /resume .
  - now: Run migrate to update existing Claude API code to a newer model; upgrade to move your project’s Anthropic SDK dependency across a major version, currently the Python anthropic package from 0.x to 1.x; managed-agents-onboard for a walkthrough that creates a new Managed Agent; or prompt-audit to flag instructions written for older models in your prompts, skills, and tool descriptions and propose fixes as a diff.
The prompt-audit subcommand requires Claude Code v2.1.221 or later, and upgrade requires v2.1.236 or later /clear [name] Start a new conversation with empty context.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Aliases: /reset , /new /code-review [low|medium|high|xhigh|max|ultra] [--fix] [--comment] [target] Skill .
Review the current diff for correctness bugs and for reuse, simplification, and efficiency cleanups.
Pass --fix to apply findings to your working tree, --comment to post them as inline GitHub PR comments, or ultra to run a deep cloud review .
From v2.1.154, /simplify runs a separate cleanup-only review that applies fixes without hunting for bugs.
See Review a diff locally for effort levels and targeting /color [color|default] Set the prompt bar color for the current session.
  - now: Resume the previous conversation with /resume , or, in the same Claude Code process, restore it from the rewind menu’s previous-session entry .
Aliases: /reset , /new /code-review [low|medium|high|xhigh|max|ultra] [--fix] [--comment] [pr#|branch|path] Skill .
Review the current diff, or a PR number, branch, or path you pass, for correctness bugs and cleanup opportunities.
Pass --fix to apply findings, --comment to post them as inline GitHub PR comments, or ultra to run a deep cloud review .
With ultra on a github.com PR target, --post preselects posting the finished findings to the PR in the launch dialog.
See Review a diff locally for the effort levels, targeting, and how it relates to /simplify .
Alias: /review /color [color|default] Set the prompt bar color for the current session.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: When Remote Control is connected, the color syncs to claude.ai/code /compact [instructions] Free up context by summarizing the conversation so far.
  - now: When Remote Control is connected, the color syncs to claude.ai/code.
Also available in non-interactive mode ( -p ); requires Claude Code v2.1.205 or later /compact [instructions] Free up context by summarizing the conversation so far.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The key=value form also works in non-interactive mode ( -p ) and from Remote Control .
Run /config --help to list every settable key with its options.
  - now: The key=value form also works in non-interactive mode ( -p ) and from the Claude mobile app via Remote Control .
The key=value form can’t turn on a setting that needs your confirmation in the panel, such as autoContinueAtUsageLimit , though it can turn one off.
Run /config --help to list the keys it accepts.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: In fullscreen mode the per-item breakdown is collapsed to keep the grid visible.
  - now: When the conversation exceeds the context window, the output includes a warning showing how far over the limit you are and which command frees space.
In fullscreen mode , /context collapses the per-item breakdown to keep the grid visible.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /debug [description] Skill .
  - now: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /dataviz [request] Skill .
Design guidance for charts, graphs, and dashboards.
Claude picks the chart form for the data, assigns color by role, validates the palette for colorblind safety and contrast with a bundled script, and applies mark, interaction, and accessibility rules.
Uses a brand-neutral placeholder palette that you replace with your own.
Requires Claude Code v2.1.198 or later /debug [description] Skill .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Available on the Anthropic API; on Amazon Bedrock, Google Cloud’s Agent Platform, and Microsoft Foundry the underlying tool can’t reach claude.ai, so the command is unavailable /desktop Continue the current session in the Claude Code Desktop app.
Requires macOS or Windows and a Claude subscription.
  - now: Available on the Anthropic API; on Amazon Bedrock, Google Cloud’s Agent Platform, Microsoft Foundry, and Claude Platform on AWS the underlying tool can’t reach claude.ai, so the command is unavailable /desktop Continue the current session in the Claude Code Desktop app.
Requires macOS or x64 Windows and a Claude subscription.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files /doctor Diagnose and verify your Claude Code installation and settings.
Results show with status icons.
Press f to have Claude fix any reported issues /effort [level|auto] Set the model effort level .
Accepts low , medium , high , xhigh , max , or ultracode ; available levels depend on the model, and max and ultracode are session-only.
ultracode is a Claude Code setting that combines xhigh reasoning with automatic workflow orchestration.
auto resets to the model default.
Without an argument, opens an interactive slider; use left and right arrows to pick a level and Enter to apply.
Takes effect immediately without waiting for the current response to finish /exit Exit the CLI.
  - now: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files.
Press Enter to open the selected file’s diff, scroll it with up/down or PageUp/PageDown, and press Esc to return to the file list.
Claude Code computes these diffs from raw git blob content, so diff drivers and textconv filters configured in .gitattributes or git config don’t apply.
Before v2.1.222, workspace-configured drivers and filters could rewrite the viewer’s output.
The open viewer also refreshes automatically when the repository’s git state changes outside the session, such as a branch switch or commit in another terminal; the auto-refresh requires Claude Code v2.1.198 or later /doctor Skill .
Run a setup checkup that diagnoses issues and can fix them.
Checks installation health, including duplicate or leftover installs, PATH problems, and unparseable settings files.
Finds unused skills, MCP servers, and plugins versus their context cost, flags slow hooks , and checks for a newer version on your release channel .
Deduplicates local CLAUDE.md files against checked-in ones, trims checked-in CLAUDE.md files by cutting content Claude could derive from the codebase, and migrates the always-loaded guidance that remains into skills and nested CLAUDE.md files that load on demand.
Also offers to make auto mode your default and to pre-approve frequently denied read-only commands.
Reports findings first and asks for confirmation before changing anything.
From the terminal, claude doctor prints read-only installation diagnostics without starting a session.
Alias: /checkup .
The CLAUDE.md trim check requires Claude Code v2.1.206 or later.
Before v2.1.205, /doctor opened a read-only diagnostics screen and pressing f sent the report to Claude /effort [level|auto|status] Set the effort level : low to xhigh , max , ultracode , or auto ; status prints it.
max and ultracode are session-only; the ultracode key persists.
Works in -p outside the effort hold /exit Exit the CLI.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Without, opens a dialog to copy to clipboard or save to a file /fast [on|off] Toggle fast mode on or off /feedback [report] Submit feedback, report a bug, or share your conversation.
Aliases: /bug , /share /fewer-permission-prompts Skill .
  - now: Without, opens a dialog to copy to clipboard or save to a file /fast [on|off] Toggle fast mode on or off.
Availability in non-interactive mode with -p is limited; see Toggle fast mode .
Requires Claude Code v2.1.205 or later /feedback [report] Send product feedback about Claude Code.
Opens the same dialog as /bug , with the same consent step, sending rules, and mid-turn behavior /fewer-permission-prompts Skill .
- **new-claim** — adds a capability claim not previously upstream
  - now: The tool-call summary also counts the subagents launched in the turn and collapses completed background-task notifications into a single count.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Only available in fullscreen rendering /fork <directive> Spawn a forked subagent : a background subagent that inherits the full conversation and works on the directive while you keep going.
Its result returns to your conversation when it finishes.
To switch into a copy of the conversation yourself, use /branch .
Before v2.1.161, /fork is an alias for /branch /goal [condition|clear] Set a goal : Claude keeps working across turns until the condition is met.
  - now: Only available in fullscreen rendering .
The VS Code extension offers its own Focus view as a command-menu toggle, stored as an extension setting, independent of viewMode /fork [prompt] Copy the current conversation into a new background session and keep working here.
Pass a prompt and the copy starts working on it immediately; without one it waits in agent view for its first prompt.
Except when the copy edits in place , Claude Code instructs it to create a worktree of its own before making code changes; the isolation instruction requires Claude Code v2.1.221 or later.
To hand a side task to a subagent whose result comes back into this conversation, use /subtask ; to switch into a copy yourself, use /branch .
Requires Claude Code v2.1.212 or later; on v2.1.161 through v2.1.211, and whenever agent view is turned off , /fork starts a forked subagent instead /goal [condition|clear] Set a goal : Claude keeps working across turns until the condition is met or the goal clears for another reason .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: See troubleshooting /help Show help and available commands /hooks View hook configurations for tool events /ide Manage IDE integrations and show status /init Initialize project with a CLAUDE.md guide.
Set CLAUDE_CODE_NEW_INIT=1 for an interactive flow that also walks through skills, hooks, and personal memory files /insights Generate a report analyzing your Claude Code sessions, including project areas, interaction patterns, and friction points /install-github-app Install the Claude GitHub App for a repository, with an optional step to set up GitHub Actions workflows and secrets.
  - now: Attach only the -diagnostics.json file when reporting a memory issue; the .heapsnapshot contains your full conversation and credentials, so don’t share it.
Hidden from the command menu ; type it in full.
See what to do with the output /help Show help and available commands /hooks View hook configurations for tool events /ide Manage IDE integrations and show status /import [codex|gemini] [--dry-run] [--yes] Bring configuration from other coding agents on your machine, currently OpenAI Codex and Google Gemini CLI, into Claude Code, including instruction files, MCP servers, commands, subagents, and skills.
In non-interactive mode with -p , /import lists what it found and gives you the command that confirms the import.
Add --dry-run to preview without writing anything, or --yes to skip the interactive picker.
Not available on Amazon Bedrock, Google Cloud’s Agent Platform, Microsoft Foundry, or Claude Platform on AWS.
Also unavailable when you turn off feature-flag fetching .
Requires Claude Code v2.1.213 or later /init Initialize project with a CLAUDE.md guide.
Set CLAUDE_CODE_NEW_INIT=1 for an interactive flow that also walks through skills, hooks, and personal memory files.
If /init finds configuration from a coding agent that /import supports, it offers to carry it over with /import /insights Generate an HTML report analyzing your recent sessions on this machine: which projects you work in, how you use Claude Code, where things go wrong, and features to try.
Not available in cloud sessions .
See Analyze your usage patterns for the report location, retention, and cost /install-github-app Install the Claude GitHub App for a repository, with an optional step to set up GitHub Actions workflows and secrets.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Opens a browser to complete the OAuth flow /keybindings Open your keyboard shortcuts file /login Sign in to your Anthropic account /logout Sign out from your Anthropic account /loop [interval] [prompt] Skill .
  - now: Opens a browser to complete the OAuth flow /keybindings Open your keyboard shortcuts file /list-agents List the subagents, agent team teammates, and other Claude Code sessions Claude can message, with the name to use for each.
See cross-session messaging .
Also available as /peers .
Requires Claude Code v2.1.224 or later; earlier versions report Unknown command: /list-agents .
Teammate rows and the first line showing this session’s own name require v2.1.239 or later.
Available only in sessions where cross-session messaging is enabled /login Sign in to your Anthropic account /logout Sign out from your Anthropic account /loop [interval] [prompt] Skill .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Omit the interval and Claude self-paces between iterations.
  - now: Omit the interval and, where available , Claude self-paces between iterations.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Run with no argument to open the interactive list, pass reconnect <server> to reconnect one disconnected server, or pass enable / disable with a server name or all to change connection state without opening the dialog /memory Edit CLAUDE.md memory files, enable or disable auto-memory , and view auto-memory entries /mobile Show QR code to download the Claude mobile app.
  - now: Run with no argument to open the interactive list, pass reconnect <server> to reconnect one disconnected server, or pass enable / disable with a server name or all to change connection state without opening the dialog.
Also available in non-interactive mode ( -p ), where running it with no argument prints a text summary of server status instead of opening the list; requires Claude Code v2.1.205 or later /memory Edit CLAUDE.md files, enable or disable auto memory , and view auto memory entries /mobile Show QR code to download the Claude mobile app.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The picker asks for confirmation when the conversation has prior output, since the next response re-reads the full history without cached context.
Once confirmed, the change applies without waiting for the current response to finish /passes Share a free week of Claude Code with friends.
  - now: See when Claude Code asks you to confirm the switch .
Once confirmed, the change applies without waiting for the current response to finish.
Also available in non-interactive mode ( -p ) with a model argument instead of the picker, where it applies to the current session only and isn’t saved as your default; requires Claude Code v2.1.205 or later /passes Share a free week of Claude Code with friends.
- **new-claim** — adds a capability claim not previously upstream
  - now: When you run it while Claude is responding, Claude Code opens the dialog immediately and applies your changes starting with Claude’s next tool call in the same turn.
Before v2.1.234, Claude Code queued the command until the turn finished.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Run with no argument to open the plugin menu, or pass a subcommand such as list , install , enable , or disable to act directly /powerup Discover Claude Code features through quick interactive lessons with animated demos /pr-comments [PR] Removed in v2.1.91.
  - now: Run with no argument to open the plugin menu, or pass a subcommand such as list , install , enable , or disable to act directly.
Claude Code can activate a plugin during the install; the install summary tells you whether it did or whether to run /reload-plugins /powerup Discover Claude Code features through quick interactive lessons with animated demos /pr-comments [PR] Removed in v2.1.91.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Not available on Bedrock, Vertex, or Foundry /recap Generate a one-line summary of the current session on demand.
  - now: Not available on Amazon Bedrock, Google Cloud’s Agent Platform, Microsoft Foundry, or Claude Platform on AWS /rate-limit-options Show ways to keep working when a claude.ai usage limit blocks a request: wait and continue automatically when the limit resets , add usage credits , or upgrade your plan.
Claude Code can also open this menu on its own when you hit a limit at your own terminal.
See Turn automatic continue off .
Requires a claude.ai subscription.
Doesn’t appear in the command menu; type it in full.
The wait-and-continue rows require Claude Code v2.1.234 or later /recap Generate a one-line summary of the current session on demand.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Select a specific version to see its release notes, or choose to show all versions /reload-plugins [--force] Reload all active plugins to apply pending changes without restarting.
  - now: Select a specific version to see its release notes, or choose to show all versions.
The notes appear in your transcript without entering the conversation Claude sees /reload-plugins [--force] Reload all active plugins to apply pending changes without restarting.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Added in v2.1.152 /remote-control Make this session available for remote control from claude.ai.
  - now: Added in v2.1.152 /remote-control Make this session available for Remote Control from claude.ai.
Running it while signed out prints that Remote Control requires a claude.ai subscription and tells you how to sign in; before v2.1.206 it reported Unknown command: /remote-control .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Without a name, auto-generates one from conversation history /resume [session] Resume a conversation by ID or name, or open the session picker.
As of v2.1.144, background sessions appear in the picker marked with bg .
Alias: /continue /review [PR] Review a GitHub pull request by number, using the same review engine as /code-review .
With no arguments, lists open PRs to pick from.
For a cloud-based review, see /code-review ultra /rewind Rewind the conversation and/or code to a previous point, or summarize from a selected message.
  - now: Without a name, auto-generates one from conversation history.
Also available in non-interactive mode ( -p ); requires Claude Code v2.1.205 or later.
From every rename surface, including claude.ai and the desktop app, Claude Code replaces control and invisible characters in the new name with spaces and caps the name at 200 characters.
If the name is empty once invisible characters are removed, Claude Code rejects it and shows That name is empty once invisible characters are removed.
Usage: /rename <name> .
The character replacement and length cap require Claude Code v2.1.221 or later.
If another live session on this machine already uses a name you pass, Claude Code applies a variant of it instead /resume [session] Resume a conversation by ID or name, or open the session picker.
Background sessions appear in the picker marked with bg ; one that is still running can’t be resumed here, so attach to it from claude agents or stop it there first.
Alias: /continue /review [low|medium|high|xhigh|max|ultra] [--fix] [--comment] [pr#|branch|path] Alias of /code-review : reviews the current diff, or a PR number, branch, or path you pass, such as /review 1234 , and takes the same effort levels and flags.
With no level given, the review reuses the last low through max level you typed; see Review a diff locally for the exact rules.
For a deep cloud review, use /code-review ultra .
Before v2.1.223, /review was a separate command that ran a single-pass, read-only review of a GitHub pull request by number, listing open PRs to pick from when run with no argument; from v2.1.186 through v2.1.201, it ran the same multi-agent engine as /code-review medium /rewind Rewind the conversation and/or code to a previous point, or summarize from a selected message.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Launch and drive your project’s app to see a change working in the running app, not just in tests.
See Run and verify your app .
Requires Claude Code v2.1.145 or later /run-skill-generator Skill .
Teach /run and /verify how to build, launch, and drive your project’s app from a clean environment by writing a per-project skill .
Requires Claude Code v2.1.145 or later /sandbox Toggle sandbox mode .
Available on supported platforms only /schedule [description] Create, update, list, or run routines , which execute on Anthropic-managed cloud infrastructure.
  - now: Launch and drive your project’s app to see a change working, not only passing tests.
See Run and verify your app /run-skill-generator Skill .
Teach /run and /verify how to build, launch, and drive your project’s app from a clean environment by writing a per-project skill /sandbox Toggle sandbox mode .
Available on supported platforms only /schedule [description] Create, update, list, or run routines , which execute in the cloud.
- **new-claim** — adds a capability claim not previously upstream
  - now: You can also ask about a routine’s recent runs .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Available in fullscreen rendering only and not in the JetBrains IDE terminal /security-review Analyze pending changes on the current branch for security vulnerabilities.
Reviews the git diff and identifies risks like injection, auth issues, and data exposure /setup-bedrock Configure Amazon Bedrock authentication, region, and model pins through an interactive wizard.
Only visible when CLAUDE_CODE_USE_BEDROCK=1 is set.
First-time Bedrock users can also access this wizard from the login screen /setup-vertex Configure Google Vertex AI authentication, project, region, and model pins through an interactive wizard.
Only visible when CLAUDE_CODE_USE_VERTEX=1 is set.
First-time Vertex AI users can also access this wizard from the login screen /simplify [target] Skill .
  - now: Available in fullscreen rendering only and not in the JetBrains IDE terminal /security-review Analyze the changes on your current branch for security vulnerabilities.
Reviews the diff between your branch and origin’s default branch, identifying risks like injection, auth issues, and data exposure.
Needs an origin remote; if the review fails with an ambiguous argument error, see the error reference /setup-bedrock Configure Amazon Bedrock authentication, region, and model pins through an interactive wizard.
Hidden from the command menu until CLAUDE_CODE_USE_BEDROCK=1 is set; type it in full.
First-time Amazon Bedrock users can also access this wizard from the login screen /setup-vertex Configure Google Cloud’s Agent Platform authentication, project, region, and model pins through an interactive wizard.
Hidden from the command menu until CLAUDE_CODE_USE_VERTEX=1 is set; type it in full.
First-time Google Cloud’s Agent Platform users can also access this wizard from the login screen /simplify [target] Skill .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Four review agents run in parallel, covering reuse of existing helpers, simplification, efficiency, and whether the change sits at the right level of abstraction.
From v2.1.154, the review does not look for correctness bugs.
  - now: Four review agents run in parallel, covering reuse of existing helpers, simplification, efficiency, and whether the change is at the right level of abstraction.
From v2.1.154, the review doesn’t look for correctness bugs.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: On earlier versions /simplify is equivalent to /code-review --fix .
  - now: On earlier versions, /simplify is equivalent to /code-review --fix .
- **new-claim** — adds a capability claim not previously upstream
  - now: Type to filter the list by name.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Press Space to hide a skill from Claude or the / menu , then Enter to save /stats Alias for /usage .
Opens on the Stats tab /status Open the Settings interface (Status tab) showing version, model, account, and connectivity.
Works while Claude is responding, without waiting for the current response to finish /statusline Configure Claude Code’s status line .
  - now: Press Space to cycle a skill’s visibility to Claude and the / menu , then Enter to save /stats Alias for /usage .
Opens on the Stats tab /status Open the Settings interface on the Status tab, showing version, model, account, and connectivity.
A Session kind row reads background job · attached or background job · unattended in a background session , depending on whether a terminal is attached, and interactive in any other session.
Before v2.1.221, /status didn’t show this row.
Works while Claude is responding /statusline Configure Claude Code’s status line .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: To detach without stopping, use /exit or press ← /tasks View and manage everything running in the background.
  - now: To detach without stopping, use /exit or press ← /subtask <task> Spawn a forked subagent : a background subagent that inherits the full conversation and works on the task while you keep working.
Its result returns to this conversation when it finishes.
To copy the conversation into a separate background session instead, use /fork .
Requires Claude Code v2.1.212 or later; on v2.1.161 through v2.1.211 this command is /fork .
When agent view is turned off , /subtask isn’t available and /fork keeps the forked-subagent behavior /tasks View and manage background work in the current session, including subagents that have finished.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For claude.ai subscribers on Pro, Max, Team, and Enterprise plans, also returns a share link teammates can open directly in Claude Code /teleport Pull a Claude Code on the web session into this terminal: opens a picker, then fetches the branch and conversation.
  - now: For claude.ai subscribers on Pro, Max, Team, and Enterprise plans, also returns a share link teammates can open directly in Claude Code /teleport Pull a Claude Code on the web session into this terminal.
Opens a picker, then fetches the branch and conversation.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: With no argument, prints the active renderer /ultraplan <prompt> Draft a plan in an ultraplan session, review it in your browser, then execute remotely or send it back to your terminal /ultrareview [PR] Run a deep, multi-agent code review in a cloud sandbox with ultrareview .
  - now: With no argument, prints the active renderer /ultraplan <prompt> Removed.
Use plan mode instead.
Previously sent a planning task to a Claude Code on the web session for review in your browser /ultrareview [PR or branch] Run a deep, multi-agent code review in a cloud sandbox with ultrareview .
Pass a PR reference to review that pull request, or a branch name to change the comparison base.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Includes 3 free runs on Pro and Max, then requires usage credits /upgrade Open the upgrade page to switch to a higher plan tier /usage Show session cost, plan usage limits, and activity stats.
On a Pro, Max, Team, or Enterprise plan, includes a breakdown of usage by skill, subagent, plugin, and MCP server.
See the cost tracking guide for details.
/cost and /stats are aliases /usage-credits Configure usage credits to keep working when you hit a limit.
  - now: Includes 3 free runs on Pro and Max, then requires usage credits /upgrade Open the upgrade page in your browser to switch to a higher plan tier.
When the browser fails to open, the command shows a sign-in prompt without printing the URL /usage Show session cost, plan usage limits, and activity stats.
On a Pro, Max, Team, or Enterprise plan, includes a breakdown of what counts against your plan limits .
/cost and /stats are aliases /usage-credits Configure usage credits, or request them from your admin, when you hit a limit.
Opens your usage-credits billing settings in the browser, except that Team and Enterprise members without billing access instead send a usage-credits request to their admin from the CLI, after confirming in a dialog that the request notifies their admins.
When no browser can open the billing page, for example over SSH, the command prints the URL to visit instead; this requires Claude Code v2.1.205 or later, and earlier versions showed nothing in that case.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: See Run and verify your app .
Requires Claude Code v2.1.145 or later /vim Removed in v2.1.92.
  - now: See Run and verify your app /vim Removed in v2.1.92.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /schedule prompts for this automatically if GitHub isn’t connected /workflows Open the workflow progress view to watch, pause, resume, or save running and completed workflows ​ MCP prompts MCP servers can expose prompts that appear as commands.
  - now: /schedule prompts for this automatically if GitHub isn’t connected /workflows Open the workflow progress view to watch, pause, resume, or save running and completed workflows ​ How the command menu matches what you type Claude Code filters the / menu as you type.
Each bullet below covers one thing you might notice while filtering: Highlighting : Claude Code highlights the top suggestion only when the letters after the / match a command’s name or alias, from the start of the name or from a word within it, ignoring the : , _ , and - separators.
Typing /adddir highlights /add-dir , and typing /new highlights /clear through its alias.
Press Enter to run the highlighted suggestion.
After a typo : Claude Code highlights nothing.
The close matches stay listed, and you can pick one with Tab or the arrow keys, but Enter submits your text as typed and reports Unknown command .
Commands that aren’t available to you : Claude Code leaves them out of the menu.
When nothing matches, Claude Code shows No commands match "/name" .
Most unavailable commands return Unknown command when you submit them; a few, such as /schedule on a Console API key , answer with their own availability message instead.
Hidden commands : Claude Code keeps a few available commands, such as /heapdump , out of the menu by design.
A partial name never brings a hidden command into the menu: if the partial matches nothing visible, Claude Code shows the same no-match message.
Claude Code lists the command only once you’ve typed its full name, and submitting the full name runs it.
​ MCP prompts MCP servers can expose prompts that appear as commands.
