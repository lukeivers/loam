# Pending delta — claude-code-loop

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/commands`
> Projection target: `claude-code/loop.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-09T13:36:14Z

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
  - was: Requires Claude Code v2.1.98 or later /agents Manage agent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
  - now: Requires Claude Code v2.1.98 or later /agents As of v2.1.198, running /agents prints a reminder to ask Claude to create or manage subagents , or to edit .claude/agents/ or ~/.claude/agents/ directly.
On v2.1.197 and earlier, opens an interactive interface for creating and managing subagent configurations /autofix-pr [prompt] Spawn a Claude Code on the web session that watches the current branch’s PR and pushes fixes when CI fails or reviewers leave comments.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /debug [description] Skill .
  - now: Press w in the picker to write the selection to a file instead of the clipboard, which is useful over SSH /cost Alias for /usage /dataviz [request] Skill .
Design guidance for charts, graphs, and dashboards.
Claude picks the chart form for the data, assigns color by role, validates the palette for colorblind safety and contrast with a bundled script, and applies mark, interaction, and accessibility rules.
Uses a brand-neutral placeholder palette that you replace with your own.
Requires Claude Code v2.1.198 or later /debug [description] Skill .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files /doctor Diagnose and verify your Claude Code installation and settings.
  - now: Use left/right arrows to switch between the current git diff and individual Claude turns, and up/down to browse files.
As of v2.1.198, the open viewer also refreshes automatically when the repository’s git state changes outside the session, such as a branch switch or commit in another terminal /doctor Diagnose and verify your Claude Code installation and settings.
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.198, the tool-call summary also counts the subagents launched in the turn and collapses completed background-task notifications into a single count.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Not available on Bedrock, Vertex, or Foundry /recap Generate a one-line summary of the current session on demand.
  - now: Not available on Amazon Bedrock, Google Cloud’s Agent Platform, or Microsoft Foundry /recap Generate a one-line summary of the current session on demand.
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
