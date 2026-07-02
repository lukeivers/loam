# Pending delta — claude-code-loop

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/commands`
> Projection target: `claude-code/loop.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-02T13:49:59Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , and /review or /security-review give a deeper read-only pass.
  - now: /diff shows what changed, /code-review checks the diff for correctness bugs and cleanups and can apply the findings with --fix , /review runs the same read-only review on a GitHub pull request, and /security-review gives a deeper read-only pass.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: See how compaction handles rules, skills, and memory files /config Open the Settings interface to adjust theme, model, output style , and other preferences.
  - now: See how compaction handles rules, skills, and memory files /config [key=value ...] Open the Settings interface to adjust theme, model, output style , and other preferences.
From v2.1.181, pass one or more key=value pairs to set a setting directly without opening the interface, for example /config thinking=false .
From v2.1.182, named shorthand keys are also accepted, such as /config theme=dark or /config model=sonnet .
The key=value form also works in non-interactive mode ( -p ) and from Remote Control .
Run /config --help to list every settable key with its options.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Fan out web searches on a question, fetch and cross-check sources, and synthesize a cited report /desktop Continue the current session in the Claude Code Desktop app.
  - now: Fan out web searches on a question, fetch and cross-check sources, and synthesize a cited report /design-login Authorize design-system access for /design-sync with your claude.ai account /design-sync [hint] Skill .
Convert your repo’s React design system and upload it to Claude Design , so designs it produces use your real components.
Optionally name the design system, for example /design-sync Acme DS .
A first-time sync verifies every component and can take a few hours on a large repo.
Available on the Anthropic API; on Amazon Bedrock, Google Cloud’s Agent Platform, and Microsoft Foundry the underlying tool can’t reach claude.ai, so the command is unavailable /desktop Continue the current session in the Claude Code Desktop app.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Set CLAUDE_CODE_NEW_INIT=1 for an interactive flow that also walks through skills, hooks, and personal memory files /insights Generate a report analyzing your Claude Code sessions, including project areas, interaction patterns, and friction points /install-github-app Set up the Claude GitHub Actions app for a repository.
  - now: Set CLAUDE_CODE_NEW_INIT=1 for an interactive flow that also walks through skills, hooks, and personal memory files /insights Generate a report analyzing your Claude Code sessions, including project areas, interaction patterns, and friction points /install-github-app Install the Claude GitHub App for a repository, with an optional step to set up GitHub Actions workflows and secrets.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Alias: /continue /review [PR] Review a pull request locally in your current session.
For a deeper cloud-based review, see /code-review ultra /rewind Rewind the conversation and/or code to a previous point, or summarize from a selected message.
  - now: Alias: /continue /review [PR] Review a GitHub pull request by number, using the same review engine as /code-review .
With no arguments, lists open PRs to pick from.
For a cloud-based review, see /code-review ultra /rewind Rewind the conversation and/or code to a previous point, or summarize from a selected message.
