# Pending delta — claude-code-schedule

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/routines`
> Projection target: `claude-code/schedule.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-21T13:04:59Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Claude Code on the web Automate work with routines Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Getting started Overview Quickstart Changelog Core concepts How Claude Code works Extend Claude Code Explore the .claude directory Explore the context window Prompt caching Use Claude Code Store instructions and memories Permission modes Manage sessions Common workflows Prompt library Best practices Platforms and integrations Overview Remote Control Claude Code on the web Get started Reference Routines Plan in the cloud Ultrareview Claude Code on desktop Chrome extension (beta) Computer use (preview) Visual Studio Code JetBrains IDEs Code review & CI/CD Claude Code in Slack On this page Example use cases Create a routine Create from the web Create from the CLI Configure triggers Add a schedule trigger Schedule a one-off run Add an API trigger Trigger a routine API reference Add a GitHub trigger Supported events Filter pull requests How sessions map to events Manage routines View and interact with runs Edit and control routines Repositories and branch permissions Connectors Environments and network access Usage and limits Troubleshooting /schedule shows “No commands match” or “Unknown command” ”Routines are disabled by your organization’s policy” Related resources Claude Code on the web Automate work with routines Copy page Put Claude Code on autopilot.
  - now: Navigation Claude Code on the web Automate work with routines Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Getting started Overview Quickstart Changelog Core concepts How Claude Code works Extend Claude Code Explore the .claude directory Explore the context window Prompt caching Use Claude Code Store instructions and memories Permission modes Manage sessions Common workflows Prompt library Best practices Platforms and integrations Overview Remote Control Claude Code on the web Get started Reference Routines Plan in the cloud Ultrareview Claude Code on desktop Mobile Chrome extension Computer use (preview) Visual Studio Code JetBrains IDEs Code review & CI/CD Claude Code in Slack On this page Example use cases Create a routine Create from the web Create from the CLI Configure triggers Add a schedule trigger Schedule a one-off run Add an API trigger Trigger a routine API reference Add a GitHub trigger Supported events Filter pull requests How sessions map to events Manage routines View and interact with runs Edit and control routines Repositories and branch permissions Connectors Environments and network access Usage and limits Troubleshooting /schedule returns “Unknown command” /schedule asks you to authenticate ”Routines are disabled by your organization’s policy” Related resources Claude Code on the web Automate work with routines Copy page Copy page Put Claude Code on autopilot.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Copy page Routines are in research preview.
  - now: Copy page Copy page Routines are in research preview.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The routine pulls the stack trace, correlates it with recent commits in the repository, and opens a draft pull request with a proposed fix and a link back to the alert.
  - now: The routine’s prompt tells Claude to investigate the alert in the fire payload, so it pulls the stack trace, correlates it with recent commits in the repository, and opens a draft pull request with a proposed fix and a link back to the alert.
- **new-claim** — adds a capability claim not previously upstream
  - now: When a trigger fires, the session receives the routine’s saved prompt as its assigned task and carries it out, rather than treating it as untrusted content that arrived mid-conversation.
The trigger attests only that the prompt was stored ahead of time by an authorized session on your account, so the fired prompt is not live user input and can’t act as approval or consent for actions during the run.
Content the session fetches during the run keeps its normal handling.
Before v2.1.214, the session received the same prompt framed as an untrusted background notification and could refuse to act on it.
- **new-claim** — adds a capability claim not previously upstream
  - now: The command is also available under the alias /routines .
A successful start looks like a conversation: Claude asks follow-up questions about the schedule, repositories, and prompt before saving.
If Claude instead replies that you need to authenticate or that it can’t connect to your remote claude.ai account, no routine was created; see Troubleshooting .
- **new-claim** — adds a capability claim not previously upstream
  - now: A routine with no schedule trigger, such as one started only by API calls or GitHub events, has no next run time, and the CLI shows none when Claude saves or updates it.
Before v2.1.211, the CLI reported a next run time in the year 1 for these routines.
- **new-claim** — adds a capability claim not previously upstream
  - now: One-off scheduling from the CLI is rolling out gradually and may not be available on your account yet.
If /schedule only offers recurring schedules, create the one-off run from the web at claude.ai/code/routines instead.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The example below triggers a routine from a shell: curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \ -H "Authorization: Bearer sk-ant-oat01-xxxxx" \ -H "anthropic-beta: experimental-cc-routine-2026-04-01" \ -H "anthropic-version: 2023-06-01" \ -H "Content-Type: application/json" \ -d '{"text": "Sentry alert SEN-4521 fired in prod.
  - now: The text value doesn’t reach the routine as a bare message.
It arrives wrapped in a <routine-fire-payload> block that labels it as untrusted data and tells Claude not to follow instructions inside it unless the routine’s own prompt says to.
The same wrapping applies to text supplied with Run now in the web UI.
This means a routine’s saved prompt must opt in to acting on fire text: write the prompt to reference the payload explicitly, for example “Investigate the alert described in the routine-fire-payload block”, or the routine treats the text as inert context.
Anyone holding the bearer token can send text , so the wrapper makes fire text from a leaked token arrive labeled as untrusted data rather than as direct instructions to your routine.
The example below triggers a routine from a shell.
The routine ID and token shown are placeholders: replace them with the URL and token you copied when adding the API trigger , or the request fails with a 401 authentication error: curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \ -H "Authorization: Bearer sk-ant-oat01-xxxxx" \ -H "anthropic-beta: experimental-cc-routine-2026-04-01" \ -H "anthropic-version: 2023-06-01" \ -H "Content-Type: application/json" \ -d '{"text": "Sentry alert SEN-4521 fired in prod.
- **new-claim** — adds a capability claim not previously upstream
  - now: You can optionally supply run-specific text, which reaches the routine the same way as the API trigger’s text field.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: To manage or add connectors outside of the routine form, visit Settings > Connectors on claude.ai or use /schedule update in the CLI.
  - now: To manage or add connectors outside of the routine form, visit claude.ai/customize/connectors or use /schedule update in the CLI.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Turn on usage credits from Settings > Billing on claude.ai.
  - now: Turn on usage credits at claude.ai/settings/usage .
On Team and Enterprise plans, an admin turns them on for the organization at claude.ai/admin-settings/usage .
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
