# Pending delta — claude-code-loop

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/commands`
> Projection target: `claude-code/loop.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-21T13:04:59Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Reference Commands Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Commands across a typical workflow All commands MCP prompts See also Reference Commands Copy page Complete reference for commands available in Claude Code, including built-in commands and bundled skills.
Copy page Commands control Claude Code from inside a session.
  - now: Navigation Reference Commands Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Commands across a typical workflow All commands MCP prompts See also Reference Commands Copy page Copy page Complete reference for commands available in Claude Code, including built-in commands and bundled skills.
Copy page Copy page Commands control Claude Code from inside a session.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Text that follows the command name is passed to it as arguments.
  - now: Text that follows the command name becomes its arguments.
As of v2.1.199, skills are the exception: a skill invocation followed by more skills, such as /skill-a /skill-b do XYZ , loads every skill named at the start and passes the trailing text to each as arguments.
Up to six skills can be chained.
If you send a command while Claude is responding, it queues and runs after the current turn finishes.
Some commands, such as /status , /tasks , and /usage , run immediately without interrupting the response.
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
Use /btw for a quick aside that shouldn’t add to the conversation history.
Run work in parallel.
Claude delegates side tasks to subagents , and /tasks lists the current session’s background work, including subagents that have finished.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , /review runs the same read-only review on a GitHub pull request, and /security-review gives a deeper read-only pass.
  - now: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , /review gives a fast single-pass, read-only review of a GitHub pull request, /code-review <level> <pr#> runs a multi-agent review of one, and /security-review checks the diff for security vulnerabilities.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /resume and /branch let you return to or fork an earlier conversation.
  - now: /resume returns to an earlier conversation, /branch branches the current one to try a different direction, and /fork copies it into a new background session .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: /doctor and /debug diagnose install and runtime issues, and /feedback reports a bug with session context attached.
  - now: /doctor runs a setup checkup that diagnoses installation and configuration issues and can fix them, /debug diagnoses runtime issues, and /feedback reports a bug with session context attached.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For example, /desktop only shows on macOS and Windows when signed in with a Claude subscription, and /upgrade only shows on Pro and Max plans.
  - now: For example, /desktop only shows on macOS and Windows when signed in with a Claude subscription, and /upgrade doesn’t show on Enterprise plans.
- **new-claim** — adds a capability claim not previously upstream
  - now: Typing a partial path shows matching directory suggestions; press Tab to accept one.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Accepts opus , sonnet , fable ( v2.1.170+), or a full model ID.
Without an argument, opens a picker.
Requires Claude Code v2.1.98 or later /agents Manage agent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
  - now: Accepts opus , sonnet , or a full model ID.
Claude Code doesn’t offer Fable 5 as the advisor and rejects /advisor fable .
Without an argument, opens a picker /agents As of v2.1.198, running /agents prints a reminder to ask Claude to create or manage subagents , or to edit .claude/agents/ or ~/.claude/agents/ directly.
On v2.1.197 and earlier, opens an interactive interface for creating and managing subagent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
- **new-claim** — adds a capability claim not previously upstream
  - now: To copy the conversation into a new background session while this one keeps running, use /fork .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: To hand a side task to a background subagent instead of switching into a copy yourself, use /fork /btw <question> Ask a quick side question without adding to the conversation /cd <path> Move this session to a new working directory.
  - now: To run a copy as a separate background session instead of switching into it, use /fork ; to hand a side task to a subagent that reports back into this conversation, use /subtask /btw [question] Ask a quick side question without adding to the conversation.
Without a question, reopens the overlay on your most recent side question from this session so you can browse earlier answers; with no side questions yet, it asks for one.
Before v2.1.212, /btw required a question /bug [report] Report a bug or share your conversation.
You choose how much session history to include and confirm on a consent screen before anything is sent.
When you’re signed in to Anthropic on a first-party connection, the report goes to Anthropic; on a third-party provider, or without Anthropic credentials, Claude Code writes the report to a local archive under ~/.claude/feedback-bundles/ that you forward yourself.
Alias: /share .
Before v2.1.212, /bug and /share were aliases of /feedback /cd <path> Move this session to a new working directory.
- **new-claim** — adds a capability claim not previously upstream
  - now: Typing a partial path shows matching directory suggestions; press Tab to accept one.
The suggestions require Claude Code v2.1.206 or later.
- **removal** — removes a previously-present capability claim
  - was: The previous conversation stays available in /resume .
- **new-claim** — adds a capability claim not previously upstream
  - now: Resume the previous conversation with /resume , or, in the same Claude Code process, restore it from the rewind menu’s previous-session entry .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: When Remote Control is connected, the color syncs to claude.ai/code /compact [instructions] Free up context by summarizing the conversation so far.
  - now: When Remote Control is connected, the color syncs to claude.ai/code.
Also available in non-interactive mode ( -p ); requires Claude Code v2.1.205 or later /compact [instructions] Free up context by summarizing the conversation so far.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The key=value form also works in non-interactive mode ( -p ) and from Remote Control .
  - now: The key=value form also works in non-interactive mode ( -p ) and from the Claude mobile app via Remote Control .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /debug [description] Skill .
  - now: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /dataviz [request] Skill .
Design guidance for charts, graphs, and dashboards.
Claude picks the chart form for the data, assigns color by role, validates the palette for colorblind safety and contrast with a bundled script, and applies mark, interaction, and accessibility rules.
Uses a brand-neutral placeholder palette that you replace with your own.
Requires Claude Code v2.1.198 or later /debug [description] Skill .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Available on the Anthropic API; on Amazon Bedrock, Google Cloud’s Agent Platform, and Microsoft Foundry the underlying tool can’t reach claude.ai, so the command is unavailable /desktop Continue the current session in the Claude Code Desktop app.
  - now: Available on the Anthropic API; on Amazon Bedrock, Google Cloud’s Agent Platform, Microsoft Foundry, and Claude Platform on AWS the underlying tool can’t reach claude.ai, so the command is unavailable /desktop Continue the current session in the Claude Code Desktop app.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files /doctor Diagnose and verify your Claude Code installation and settings.
Results show with status icons.
Press f to have Claude fix any reported issues /effort [level|auto] Set the model effort level .
  - now: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files.
Press Enter to open the selected file’s diff, scroll it with up/down or PageUp/PageDown, and press Esc to return to the file list.
As of v2.1.198, the open viewer also refreshes automatically when the repository’s git state changes outside the session, such as a branch switch or commit in another terminal /doctor Skill .
Run a setup checkup that diagnoses issues and can fix them.
Checks installation health, including duplicate or leftover installs, PATH problems, and unparseable settings files.
Finds unused skills, MCP servers, and plugins versus their context cost, flags slow hooks , and checks for a newer version on your release channel.
Deduplicates local CLAUDE.md files against checked-in ones, trims checked-in CLAUDE.md files by cutting content Claude could derive from the codebase, and migrates the always-loaded guidance that remains into skills and nested CLAUDE.md files that load on demand.
The trim cuts sections such as directory layouts, dependency lists, and architecture overviews, and keeps pitfalls, rationale, and conventions that differ from tool defaults.
Also offers to make auto mode your default and to pre-approve frequently denied read-only commands.
Reports findings first and asks for confirmation before changing anything.
From the terminal, claude doctor prints read-only installation diagnostics without starting a session.
Alias: /checkup .
The CLAUDE.md trim check requires Claude Code v2.1.206 or later.
Before v2.1.206, the version check compared Homebrew installs against the autoUpdatesChannel setting rather than the installed cask’s channel .
Before v2.1.205, /doctor opened a read-only diagnostics screen and pressing f sent the report to Claude /effort [level|auto] Set the model effort level .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Takes effect immediately without waiting for the current response to finish /exit Exit the CLI.
  - now: Takes effect immediately without waiting for the current response to finish.
Also available in non-interactive mode ( -p ) with a level argument, where it applies to the current session only and isn’t saved as your default; requires Claude Code v2.1.205 or later.
On Fable 5, Opus 4.8, and Opus 4.7, a non-interactive /effort reports Not applied while the model-default effort hold is in force, so pass --effort at launch instead /exit Exit the CLI.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Without, opens a dialog to copy to clipboard or save to a file /fast [on|off] Toggle fast mode on or off /feedback [report] Submit feedback, report a bug, or share your conversation.
Aliases: /bug , /share /fewer-permission-prompts Skill .
  - now: Without, opens a dialog to copy to clipboard or save to a file /fast [on|off] Toggle fast mode on or off.
In non-interactive mode ( -p ), /fast works only in a session launched with fast mode in its --settings value, for example claude -p --settings '{"fastMode": true}' ; the toggle then applies to the current session only and isn’t saved as your default, and in any other non-interactive session the command reports that fast mode isn’t available.
Requires Claude Code v2.1.205 or later /feedback [report] Send product feedback about Claude Code.
Opens the same dialog as /bug with the same consent step and sending rules /fewer-permission-prompts Skill .
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.198, the tool-call summary also counts the subagents launched in the turn and collapses completed background-task notifications into a single count.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Only available in fullscreen rendering /fork <directive> Spawn a forked subagent : a background subagent that inherits the full conversation and works on the directive while you keep going.
Its result returns to your conversation when it finishes.
To switch into a copy of the conversation yourself, use /branch .
Before v2.1.161, /fork is an alias for /branch /goal [condition|clear] Set a goal : Claude keeps working across turns until the condition is met.
  - now: Only available in fullscreen rendering /fork [prompt] Copy the current conversation into a new background session and keep working here.
The copy starts with everything in this conversation up to now and runs as its own row in agent view ; the two sessions are independent from that point on.
Pass a prompt and the copy starts working on it immediately; without one it waits in agent view for its first prompt.
To hand a side task to a subagent whose result comes back into this conversation, use /subtask .
To switch into a copy yourself, use /branch .
Requires Claude Code v2.1.212 or later; on v2.1.161 through v2.1.211 /fork starts a forked subagent instead, and before v2.1.161 it is an alias for /branch unless forked subagents were enabled, by setting CLAUDE_CODE_FORK_SUBAGENT to 1 from v2.1.117 or by a server-side rollout.
When agent view is turned off , /fork keeps the forked-subagent behavior /goal [condition|clear] Set a goal : Claude keeps working across turns until the condition is met.
- **new-claim** — adds a capability claim not previously upstream
  - now: The .heapsnapshot file contains your full conversation and credentials, so don’t share it.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Run with no argument to open the interactive list, pass reconnect <server> to reconnect one disconnected server, or pass enable / disable with a server name or all to change connection state without opening the dialog /memory Edit CLAUDE.md memory files, enable or disable auto-memory , and view auto-memory entries /mobile Show QR code to download the Claude mobile app.
  - now: Run with no argument to open the interactive list, pass reconnect <server> to reconnect one disconnected server, or pass enable / disable with a server name or all to change connection state without opening the dialog.
Also available in non-interactive mode ( -p ), where running it with no argument prints a text summary of server status instead of opening the list; requires Claude Code v2.1.205 or later /memory Edit CLAUDE.md memory files, enable or disable auto-memory , and view auto-memory entries /mobile Show QR code to download the Claude mobile app.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Once confirmed, the change applies without waiting for the current response to finish /passes Share a free week of Claude Code with friends.
  - now: Once confirmed, the change applies without waiting for the current response to finish.
Also available in non-interactive mode ( -p ) with a model argument instead of the picker, where it applies to the current session only and isn’t saved as your default; requires Claude Code v2.1.205 or later /passes Share a free week of Claude Code with friends.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Not available on Bedrock, Vertex, or Foundry /recap Generate a one-line summary of the current session on demand.
  - now: Not available on Amazon Bedrock, Google Cloud’s Agent Platform, Microsoft Foundry, or Claude Platform on AWS /recap Generate a one-line summary of the current session on demand.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Select a specific version to see its release notes, or choose to show all versions /reload-plugins [--force] Reload all active plugins to apply pending changes without restarting.
  - now: Select a specific version to see its release notes, or choose to show all versions.
The notes appear in your transcript without entering the conversation Claude sees.
Before v2.1.208, the viewed notes entered the conversation, including the entire changelog when showing all versions /reload-plugins [--force] Reload all active plugins to apply pending changes without restarting.
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
Also available in non-interactive mode ( -p ); requires Claude Code v2.1.205 or later /resume [session] Resume a conversation by ID or name, or open the session picker.
As of v2.1.144, background sessions appear in the picker marked with bg ; one that is still running can’t be resumed here, so attach to it from claude agents or stop it there first.
Alias: /continue /review [PR] Run a fast single-pass, read-only review of a GitHub pull request by number.
With no argument, lists open PRs to pick from; text after the PR number becomes additional review instructions.
From v2.1.186 through v2.1.201, /review instead ran the same multi-agent engine as /code-review medium .
For a multi-agent review at a chosen effort level, use /code-review <level> <pr#> ; for a cloud-based review, see /code-review ultra /rewind Rewind the conversation and/or code to a previous point, or summarize from a selected message.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Launch and drive your project’s app to see a change working in the running app, not just in tests.
  - now: Launch and drive your project’s app to see a change working, not only passing tests.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: First-time Bedrock users can also access this wizard from the login screen /setup-vertex Configure Google Vertex AI authentication, project, region, and model pins through an interactive wizard.
  - now: First-time Amazon Bedrock users can also access this wizard from the login screen /setup-vertex Configure Google Cloud’s Agent Platform authentication, project, region, and model pins through an interactive wizard.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: First-time Vertex AI users can also access this wizard from the login screen /simplify [target] Skill .
  - now: First-time Google Cloud’s Agent Platform users can also access this wizard from the login screen /simplify [target] Skill .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Four review agents run in parallel, covering reuse of existing helpers, simplification, efficiency, and whether the change sits at the right level of abstraction.
From v2.1.154, the review does not look for correctness bugs.
  - now: Four review agents run in parallel, covering reuse of existing helpers, simplification, efficiency, and whether the change is at the right level of abstraction.
From v2.1.154, the review doesn’t look for correctness bugs.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: On earlier versions /simplify is equivalent to /code-review --fix .
  - now: On earlier versions, /simplify is equivalent to /code-review --fix .
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.121, type to filter the list by name.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Press Space to hide a skill from Claude or the / menu , then Enter to save /stats Alias for /usage .
Opens on the Stats tab /status Open the Settings interface (Status tab) showing version, model, account, and connectivity.
Works while Claude is responding, without waiting for the current response to finish /statusline Configure Claude Code’s status line .
  - now: Press Space to cycle a skill’s visibility to Claude and the / menu , then Enter to save /stats Alias for /usage .
Opens on the Stats tab /status Open the Settings interface on the Status tab, showing version, model, account, and connectivity.
Works while Claude is responding /statusline Configure Claude Code’s status line .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: To detach without stopping, use /exit or press ← /tasks View and manage everything running in the background.
  - now: To detach without stopping, use /exit or press ← /subtask <task> Spawn a forked subagent : a background subagent that inherits the full conversation and works on the task while you keep working.
Its result returns to this conversation when it finishes.
To copy the conversation into a separate background session instead, use /fork .
Requires Claude Code v2.1.212 or later; on v2.1.161 through v2.1.211 this command is /fork .
When agent view is turned off , /subtask isn’t available and /fork keeps the forked-subagent behavior /tasks View and manage background work in the current session, including subagents that have finished.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: With no argument, prints the active renderer /ultraplan <prompt> Draft a plan in an ultraplan session, review it in your browser, then execute remotely or send it back to your terminal /ultrareview [PR] Run a deep, multi-agent code review in a cloud sandbox with ultrareview .
  - now: With no argument, prints the active renderer /ultraplan <prompt> Draft a plan in an ultraplan session, review it in your browser, then execute remotely or send it back to your terminal /ultrareview [PR or branch] Run a deep, multi-agent code review in a cloud sandbox with ultrareview .
Pass a PR reference to review that pull request, or a branch name to change the comparison base.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Includes 3 free runs on Pro and Max, then requires usage credits /upgrade Open the upgrade page to switch to a higher plan tier /usage Show session cost, plan usage limits, and activity stats.
  - now: Includes 3 free runs on Pro and Max, then requires usage credits /upgrade Open the upgrade page in your browser to switch to a higher plan tier.
When the browser fails to open, the command shows a sign-in prompt without printing the URL /usage Show session cost, plan usage limits, and activity stats.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /cost and /stats are aliases /usage-credits Configure usage credits to keep working when you hit a limit.
  - now: /cost and /stats are aliases /usage-credits Configure usage credits, or request them from your admin, when you hit a limit.
On Pro and Max plans, opens an in-CLI dialog to buy usage credits, set a monthly spend limit, and configure auto-reload; on Claude Code versions before v2.1.207 and on other plans, opens the usage-credits billing page in your browser, except that Team and Enterprise members without billing access instead send a usage-credits request to their admin from the CLI, after confirming in a dialog that the request notifies their admins.
Before v2.1.211, Claude Code sent the request without a confirmation step.
When no browser can open the billing page, for example over SSH, the command prints the URL to visit instead; this requires Claude Code v2.1.205 or later, and earlier versions showed nothing in that case.
