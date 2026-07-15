# Pending delta — claude-code-schedule

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/routines`
> Projection target: `claude-code/schedule.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-15T13:00:06Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Claude Code on the web Automate work with routines Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Getting started Overview Quickstart Changelog Core concepts How Claude Code works Extend Claude Code Explore the .claude directory Explore the context window Prompt caching Use Claude Code Store instructions and memories Permission modes Manage sessions Common workflows Prompt library Best practices Platforms and integrations Overview Remote Control Claude Code on the web Get started Reference Routines Plan in the cloud Ultrareview Claude Code on desktop Chrome extension (beta) Computer use (preview) Visual Studio Code JetBrains IDEs Code review & CI/CD Claude Code in Slack On this page Example use cases Create a routine Create from the web Create from the CLI Configure triggers Add a schedule trigger Schedule a one-off run Add an API trigger Trigger a routine API reference Add a GitHub trigger Supported events Filter pull requests How sessions map to events Manage routines View and interact with runs Edit and control routines Repositories and branch permissions Connectors Environments and network access Usage and limits Troubleshooting /schedule shows “No commands match” or “Unknown command” ”Routines are disabled by your organization’s policy” Related resources Claude Code on the web Automate work with routines Copy page Put Claude Code on autopilot.
  - now: Navigation Claude Code on the web Automate work with routines Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Getting started Overview Quickstart Changelog Core concepts How Claude Code works Extend Claude Code Explore the .claude directory Explore the context window Prompt caching Use Claude Code Store instructions and memories Permission modes Manage sessions Common workflows Prompt library Best practices Platforms and integrations Overview Remote Control Claude Code on the web Get started Reference Routines Plan in the cloud Ultrareview Claude Code on desktop Chrome extension Computer use (preview) Visual Studio Code JetBrains IDEs Code review & CI/CD Claude Code in Slack On this page Example use cases Create a routine Create from the web Create from the CLI Configure triggers Add a schedule trigger Schedule a one-off run Add an API trigger Trigger a routine API reference Add a GitHub trigger Supported events Filter pull requests How sessions map to events Manage routines View and interact with runs Edit and control routines Repositories and branch permissions Connectors Environments and network access Usage and limits Troubleshooting /schedule returns “Unknown command” /schedule asks you to authenticate ”Routines are disabled by your organization’s policy” Related resources Claude Code on the web Automate work with routines Copy page Put Claude Code on autopilot.
- **new-claim** — adds a capability claim not previously upstream
  - now: A successful start looks like a conversation: Claude asks follow-up questions about the schedule, repositories, and prompt before saving.
If Claude instead replies that you need to authenticate or that it can’t connect to your remote claude.ai account, no routine was created; see Troubleshooting .
- **new-claim** — adds a capability claim not previously upstream
  - now: One-off scheduling from the CLI is rolling out gradually and may not be available on your account yet.
If /schedule only offers recurring schedules, create the one-off run from the web at claude.ai/code/routines instead.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The example below triggers a routine from a shell: curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \ -H "Authorization: Bearer sk-ant-oat01-xxxxx" \ -H "anthropic-beta: experimental-cc-routine-2026-04-01" \ -H "anthropic-version: 2023-06-01" \ -H "Content-Type: application/json" \ -d '{"text": "Sentry alert SEN-4521 fired in prod.
  - now: The example below triggers a routine from a shell.
The routine ID and token shown are placeholders: replace them with the URL and token you copied when adding the API trigger , or the request fails with a 401 authentication error: curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \ -H "Authorization: Bearer sk-ant-oat01-xxxxx" \ -H "anthropic-beta: experimental-cc-routine-2026-04-01" \ -H "anthropic-version: 2023-06-01" \ -H "Content-Type: application/json" \ -d '{"text": "Sentry alert SEN-4521 fired in prod.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Troubleshooting ​ /schedule shows “No commands match” or “Unknown command” The CLI hides /schedule when one of its requirements isn’t met, so the command menu shows No commands match "/schedule" while you type, and submitting it returns Unknown command: /schedule .
The cause is usually one of the following: You are authenticated with a Console API key or a cloud provider such as Bedrock, Vertex, or Foundry.
  - now: ​ Troubleshooting ​ /schedule returns “Unknown command” The CLI hides /schedule when one of its requirements isn’t met: the command menu shows No commands match "/schedule" while you type, and submitting it returns Unknown command: /schedule .
The cause is usually one of the following: You are authenticated with a Console API key or a cloud provider such as Amazon Bedrock, Google Cloud’s Agent Platform, or Microsoft Foundry.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Manage routines from the web UI instead Your CLI is older than v2.1.81.
Run claude update You can always create and manage routines at claude.ai/code/routines regardless of how the CLI is configured.
  - now: Manage routines from the web UI instead You can always create and manage routines at claude.ai/code/routines regardless of how the CLI is configured.
​ /schedule asks you to authenticate If /schedule runs but Claude responds that you need to authenticate with a claude.ai account first, the CLI has no stored claude.ai login.
API accounts aren’t supported for routines.
Run /login , sign in with your claude.ai account, then run /schedule again.
