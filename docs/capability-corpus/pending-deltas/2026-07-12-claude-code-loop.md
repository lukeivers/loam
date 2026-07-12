# Pending delta — claude-code-loop

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/commands`
> Projection target: `claude-code/loop.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-12T12:59:06Z

- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Text that follows the command name is passed to it as arguments.
  - now: Text that follows the command name becomes its arguments.
As of v2.1.199, skills are the exception: a skill invocation followed by more skills, such as /skill-a /skill-b do XYZ , loads every skill named at the start and passes the trailing text to each as arguments.
Up to six skills can be chained.
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
Claude delegates side tasks to subagents , and /tasks lists what’s running in the background of the current session.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , /review runs the same read-only review on a GitHub pull request, and /security-review gives a deeper read-only pass.
  - now: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , /review gives a fast single-pass, read-only review of a GitHub pull request, /code-review <level> <pr#> runs a multi-agent review of one, and /security-review checks the diff for security vulnerabilities.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: /doctor and /debug diagnose install and runtime issues, and /feedback reports a bug with session context attached.
  - now: /doctor runs a setup checkup that diagnoses installation and configuration issues and can fix them, /debug diagnoses runtime issues, and /feedback reports a bug with session context attached.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Requires Claude Code v2.1.98 or later /agents Manage agent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
  - now: Requires Claude Code v2.1.98 or later /agents As of v2.1.198, running /agents prints a reminder to ask Claude to create or manage subagents , or to edit .claude/agents/ or ~/.claude/agents/ directly.
On v2.1.197 and earlier, opens an interactive interface for creating and managing subagent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: When Remote Control is connected, the color syncs to claude.ai/code /compact [instructions] Free up context by summarizing the conversation so far.
  - now: When Remote Control is connected, the color syncs to claude.ai/code.
Also available in non-interactive mode ( -p ); requires Claude Code v2.1.205 or later /compact [instructions] Free up context by summarizing the conversation so far.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /debug [description] Skill .
  - now: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /dataviz [request] Skill .
Design guidance for charts, graphs, and dashboards.
Claude picks the chart form for the data, assigns color by role, validates the palette for colorblind safety and contrast with a bundled script, and applies mark, interaction, and accessibility rules.
Uses a brand-neutral placeholder palette that you replace with your own.
Requires Claude Code v2.1.198 or later /debug [description] Skill .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files /doctor Diagnose and verify your Claude Code installation and settings.
Results show with status icons.
Press f to have Claude fix any reported issues /effort [level|auto] Set the model effort level .
  - now: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files.
As of v2.1.198, the open viewer also refreshes automatically when the repository’s git state changes outside the session, such as a branch switch or commit in another terminal /doctor Skill .
Run a setup checkup that diagnoses issues and can fix them.
Checks installation health, including duplicate or leftover installs, PATH problems, and unparseable settings files.
Finds unused skills, MCP servers, and plugins versus their context cost, deduplicates local CLAUDE.md files against checked-in ones, migrates always-loaded guidance into skills and nested CLAUDE.md files that load on demand, flags slow hooks , and checks for a newer version.
Also offers to make auto mode your default and to pre-approve frequently denied read-only commands.
Reports findings first and asks for confirmation before changing anything.
From the terminal, claude doctor prints read-only installation diagnostics without starting a session.
Alias: /checkup .
Before v2.1.205, /doctor opened a read-only diagnostics screen and pressing f sent the report to Claude /effort [level|auto] Set the model effort level .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Takes effect immediately without waiting for the current response to finish /exit Exit the CLI.
  - now: Takes effect immediately without waiting for the current response to finish.
Also available in non-interactive mode ( -p ) with a level argument, where it applies to the current session only and isn’t saved as your default; requires Claude Code v2.1.205 or later.
On Fable 5, Opus 4.8, and Opus 4.7, a non-interactive /effort reports Not applied while the model-default effort hold is in force, so pass --effort at launch instead /exit Exit the CLI.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Without, opens a dialog to copy to clipboard or save to a file /fast [on|off] Toggle fast mode on or off /feedback [report] Submit feedback, report a bug, or share your conversation.
  - now: Without, opens a dialog to copy to clipboard or save to a file /fast [on|off] Toggle fast mode on or off.
In non-interactive mode ( -p ), /fast works only in a session launched with fast mode in its --settings value, for example claude -p --settings '{"fastMode": true}' ; the toggle then applies to the current session only and isn’t saved as your default, and in any other non-interactive session the command reports that fast mode isn’t available.
Requires Claude Code v2.1.205 or later /feedback [report] Submit feedback, report a bug, or share your conversation.
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.198, the tool-call summary also counts the subagents launched in the turn and collapses completed background-task notifications into a single count.
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
  - now: Not available on Amazon Bedrock, Google Cloud’s Agent Platform, or Microsoft Foundry /recap Generate a one-line summary of the current session on demand.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Without a name, auto-generates one from conversation history /resume [session] Resume a conversation by ID or name, or open the session picker.
  - now: Without a name, auto-generates one from conversation history.
Also available in non-interactive mode ( -p ); requires Claude Code v2.1.205 or later /resume [session] Resume a conversation by ID or name, or open the session picker.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Alias: /continue /review [PR] Review a GitHub pull request by number, using the same review engine as /code-review .
With no arguments, lists open PRs to pick from.
For a cloud-based review, see /code-review ultra /rewind Rewind the conversation and/or code to a previous point, or summarize from a selected message.
  - now: Alias: /continue /review [PR] Run a fast single-pass, read-only review of a GitHub pull request by number.
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
- **new-claim** — adds a capability claim not previously upstream
  - now: Opens the usage-credits billing page in your browser.
When no browser can open, for example over SSH, the command prints the URL to visit instead; this requires Claude Code v2.1.205 or later, and earlier versions showed nothing in that case.
