# Pending delta — claude-code-schedule

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/routines`
> Projection target: `claude-code/schedule.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-19T13:27:26Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Claude Code on the web Automate work with routines Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Getting started Overview Quickstart Changelog Core concepts How Claude Code works Extend Claude Code Explore the .claude directory Explore the context window Prompt caching Use Claude Code Store instructions and memories Permission modes Manage sessions Common workflows Prompt library Best practices Platforms and integrations Overview Remote Control Claude Code on the web Get started Reference Routines Plan in the cloud Ultrareview Claude Code on desktop Chrome extension (beta) Computer use (preview) Visual Studio Code JetBrains IDEs Code review & CI/CD Claude Code in Slack On this page Example use cases Create a routine Create from the web Create from the CLI Configure triggers Add a schedule trigger Schedule a one-off run Add an API trigger Trigger a routine API reference Add a GitHub trigger Supported events Filter pull requests How sessions map to events Manage routines View and interact with runs Edit and control routines Repositories and branch permissions Connectors Environments and network access Usage and limits Troubleshooting /schedule shows “No commands match” or “Unknown command” ”Routines are disabled by your organization’s policy” Related resources Claude Code on the web Automate work with routines Copy page Put Claude Code on autopilot.
Define routines that run on a schedule, trigger on API calls, or react to GitHub events from Anthropic-managed cloud infrastructure.
Copy page Routines are in research preview.
  - now: Navigation Claude Code on the web Automate work with routines Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Getting started Overview Quickstart Changelog Core concepts How Claude Code works Extend Claude Code Explore the .claude directory Explore the context window Prompt caching Use Claude Code Store instructions and memories Permission modes Manage sessions Common workflows Prompt library Best practices Platforms and integrations Overview Remote Control Claude Code on the web Get started Reference Routines Ultrareview Claude Code on desktop Mobile Chrome extension Computer use (preview) Visual Studio Code JetBrains IDEs Code review & CI/CD Claude Code in Slack Claude Tag On this page Example use cases Create a routine Create from the web Create from the CLI Configure triggers Add a schedule trigger Schedule a one-off run Add an API trigger Trigger a routine API reference Add a GitHub trigger Supported events Filter pull requests Manage routines View and interact with runs Edit and control routines Manage routines from the CLI Repositories and branch permissions Connectors Environments and network access Usage and limits Troubleshooting /schedule returns “Unknown command” /schedule asks you to authenticate “Routines are disabled by your organization’s policy” Related resources Claude Code on the web Automate work with routines Copy page Copy page Put Claude Code on autopilot.
Define routines that run on a schedule, trigger on API calls, or react to GitHub events from cloud infrastructure.
Copy page Copy page Routines are in research preview.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Routines execute on Anthropic-managed cloud infrastructure, so they keep working when your laptop is closed.
  - now: Routines execute on Anthropic-managed cloud infrastructure, or on your organization’s self-hosted environment when routed there, so they keep working when your laptop is closed.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The routine pulls the stack trace, correlates it with recent commits in the repository, and opens a draft pull request with a proposed fix and a link back to the alert.
  - now: The routine’s prompt tells Claude to investigate the alert in the fire payload, so it pulls the stack trace, correlates it with recent commits in the repository, and opens a draft pull request with a proposed fix and a link back to the alert.
- **removal** — removes a previously-present capability claim
  - was: The sections below walk through creating a routine and configuring each of these trigger types.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: In the Desktop app, click Routines in the sidebar, then New routine , and choose Remote ; choosing Local instead creates a Desktop scheduled task , which runs on your machine rather than in the cloud.
  - now: In the Desktop app, click Routines in the sidebar, then New routine , and choose Cloud ; choosing Local instead creates a Desktop scheduled task , which runs on your machine rather than in the cloud.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: What a routine can reach is determined by the repositories you select and their branch-push setting, the environment’s network access and variables, and the connectors you include.
  - now: What a routine can reach is determined by the repositories you select, the environment’s network access and variables, and the connectors you include.
- **new-claim** — adds a capability claim not previously upstream
  - now: When a trigger fires, the session receives the routine’s saved prompt as its assigned task and carries it out, rather than treating it as untrusted content that arrived mid-conversation.
The trigger attests only that the prompt was stored ahead of time by an authorized session on your account, so the fired prompt is not live user input and can’t act as approval or consent for actions during the run.
Content the session fetches during the run keeps its normal handling.
Before v2.1.213, the session received the same prompt framed as an untrusted background notification and could refuse to act on it.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Environments control what the cloud session has access to: Network access : set the level of internet access available during each run Environment variables : provide API keys, tokens, or other secrets Claude can use Setup script : install dependencies and tools the routine needs.
The result is cached , so the script doesn’t re-run on every session A Default environment is provided with Trusted network access, which allows the default set of package registries, cloud provider APIs, container registries, and common development domains, but blocks everything else.
If your routine needs to reach your own services or a domain outside that list, edit the environment’s network access before running.
  - now: Environments control what the cloud session has access to: Network access : set the level of internet access available during each run Environment variables : provide values Claude can use during each run.
They’re visible to anyone who uses the environment , so add credentials with that in mind Setup script : install dependencies and tools the routine needs.
The result is cached , so the script doesn’t re-run on every session A Default environment is provided with Trusted network access, which allows only the default allowlist of package registries, cloud provider APIs, container registries, and common development domains through the session’s network.
Connectors you add to the routine reach their services through Anthropic’s servers, so they don’t need allowlist changes.
If your routine needs to reach your own services directly, or a domain outside that list, edit the environment’s network access before running.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: 6 Review connectors and permissions The Connectors and Permissions tabs at the bottom of the form control what the routine can reach.
Under Connectors, all of your connected MCP connectors are included by default.
Remove any the routine doesn’t need.
Claude can use every tool from an included connector, including writes, without asking for permission during a run.
Under Permissions, enable Allow unrestricted branch pushes for any repository where Claude should be able to push to existing branches instead of only claude/ -prefixed ones.
  - now: 6 Review connectors Under Connectors at the bottom of the form, all of your connected MCP connectors are included by default.
Remove any the routine doesn’t need: Claude can use every tool from an included connector, including writes, without asking for permission during a run.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: /schedule in the CLI creates scheduled routines only.
To add an API or GitHub trigger, edit the routine on the web at claude.ai/code/routines .
The CLI also supports managing existing routines.
Run /schedule list to see all routines, /schedule update to change one, or /schedule run to trigger it immediately.
  - now: The command is also available under the alias /routines .
A successful start looks like a conversation: Claude asks follow-up questions about the schedule, repositories, and prompt before saving.
If Claude instead replies that you need to authenticate or that it can’t connect to your remote claude.ai account, no routine was created; see Troubleshooting .
/schedule in the CLI creates scheduled routines.
To add an API trigger, edit the routine on the web at claude.ai/code/routines .
You can add a GitHub trigger from the web or from the CLI.
The CLI path requires Claude Code v2.1.225 or later.
A routine with no schedule trigger, such as one started only by API calls or GitHub events, has no next run time, and the CLI shows none when Claude saves or updates it.
Before v2.1.211, the CLI reported a next run time in the year 1 for these routines.
- **new-claim** — adds a capability claim not previously upstream
  - now: One-off scheduling from the CLI is rolling out gradually and may not be available on your account yet.
If /schedule only offers recurring schedules, create the one-off run from the web at claude.ai/code/routines instead.
- **removal** — removes a previously-present capability claim
  - was: They consume your plan’s regular subscription usage like any other session.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The example below triggers a routine from a shell: curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \ -H "Authorization: Bearer sk-ant-oat01-xxxxx" \ -H "anthropic-beta: experimental-cc-routine-2026-04-01" \ -H "anthropic-version: 2023-06-01" \ -H "Content-Type: application/json" \ -d '{"text": "Sentry alert SEN-4521 fired in prod.
  - now: The text value doesn’t reach the routine as a bare message.
It arrives wrapped in a <routine-fire-payload> block that labels it as untrusted data and tells Claude not to follow instructions inside it unless the routine’s own prompt says to.
The same wrapping applies to text supplied with Run now in the web UI.
This means a routine’s saved prompt must opt in to acting on fire text: write the prompt to reference the payload explicitly, for example “Investigate the alert described in the routine-fire-payload block”, or the routine treats the text as inert context.
Anyone holding the bearer token can send text , so the wrapper makes fire text from a leaked token arrive labeled as untrusted data rather than as direct instructions to your routine.
The example below triggers a routine from a shell.
The routine ID and token shown are placeholders: replace them with the URL and token you copied when adding the API trigger , or the request fails with a 401 authentication error: curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \ -H "Authorization: Bearer sk-ant-oat01-xxxxx" \ -H "anthropic-beta: experimental-cc-routine-2026-04-01" \ -H "anthropic-version: 2023-06-01" \ -H "Content-Type: application/json" \ -d '{"text": "Sentry alert SEN-4521 fired in prod.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Each matching event starts its own session.
  - now: Claude Code doesn’t reuse sessions across events, so two PR updates produce two independent sessions.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: GitHub triggers are configured from the web UI only.
  - now: The Claude GitHub App must be installed on the repository you want to subscribe to, whichever surface you configure the trigger from.
Configure GitHub triggers from the web UI, which prompts you to install the app when it’s missing.
Follow the steps below to configure one on the web.
From the CLI, install the app from the GitHub App page first, then ask Claude to attach a GitHub trigger to an existing routine, for example /schedule add a GitHub trigger to my nightly review for pull requests opened in acme/webapp .
The CLI path requires Claude Code v2.1.225 or later.
When Claude adds the trigger, it replies with a link to the routine the trigger fires.
- **removal** — removes a previously-present capability claim
  - was: 3 Install the Claude GitHub App The Claude GitHub App must be installed on the repository you want to subscribe to.
The trigger setup prompts you to install it if it isn’t already.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: GitHub triggers require installing the Claude GitHub App, which the trigger setup prompts you to do.
4 Configure the trigger Select the repository, choose an event from the supported events list, and optionally add filters.
  - now: 3 Configure the trigger Select the repository, choose an event from the supported events list, and optionally add filters.
- **removal** — removes a previously-present capability claim
  - was: ​ How sessions map to events Each matching GitHub event starts a new session.
Session reuse across events is not available for GitHub-triggered routines, so two PR updates produce two independent sessions.
- **new-claim** — adds a capability claim not previously upstream
  - now: You can optionally supply run-specific text, which reaches the routine the same way as the API trigger’s text field.
- **new-claim** — adds a capability claim not previously upstream
  - now: ​ Manage routines from the CLI The CLI supports managing existing routines.
Run /schedule list to see all routines, /schedule update to change one, or /schedule run to trigger it immediately.
You can also ask about a routine’s run history, for example /schedule why did my nightly review do nothing this morning?
.
Claude lists the routine’s recent runs with their status and a link to open each run on the web , and reads a run’s log to explain what happened, including tool errors, permission denials, and the final result.
Requires Claude Code v2.1.227 or later.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: By default, Claude can only push to branches prefixed with claude/ .
This prevents routines from accidentally modifying protected or long-lived branches.
To remove this restriction for a specific repository, enable Allow unrestricted branch pushes for that repository when creating or editing the routine.
​ Connectors Routines can use your connected MCP connectors to read from and write to external services during each run.
  - now: Claude pushes its work to branches prefixed with claude/ , which are always accepted.
When your prompt directs Claude to push to another branch, Claude Code checks the push first and rejects it if any of the following is true: The branch is protected on GitHub Someone else has an open pull request from that branch The branch carries commits authored by someone other than you ​ Connectors Routines can use your connected MCP connectors to read from and write to external services during each run.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: To manage or add connectors outside of the routine form, visit Settings > Connectors on claude.ai or use /schedule update in the CLI.
​ Environments and network access Each routine runs in a cloud environment that controls network access, environment variables, and setup scripts.
  - now: To manage or add connectors outside of the routine form, visit claude.ai/customize/connectors or use /schedule update in the CLI.
​ Environments and network access Each routine uses a cloud environment that controls network access, environment variables, and setup scripts.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The Default environment uses Trusted network access: the default allowlist of package registries, cloud provider APIs, container registries, and common development domains is reachable, but arbitrary domains are not.
Outbound requests to other hosts fail with 403 and x-deny-reason: host_not_allowed .
MCP connector traffic is routed through Anthropic’s servers, so the connectors you add to the routine work without adding their hosts to Allowed domains .
  - now: The Default environment uses Trusted network access, which allows only the default allowlist through the session’s network.
Requests on that path to hosts outside the allowlist fail with 403 and x-deny-reason: host_not_allowed .
MCP connector traffic is routed through Anthropic’s servers rather than that path, so the connectors you add to the routine work without adding their hosts to Allowed domains .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Turn on usage credits from Settings > Billing on claude.ai.
  - now: Turn on usage credits at claude.ai/settings/usage .
On Team and Enterprise plans, an admin turns them on for the organization at claude.ai/admin-settings/usage .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They draw down your regular subscription usage like any other session, but they are exempt from the per-account daily routine run allowance.
​ Troubleshooting ​ /schedule shows “No commands match” or “Unknown command” The CLI hides /schedule when one of its requirements isn’t met, so the command menu shows No commands match "/schedule" while you type, and submitting it returns Unknown command: /schedule .
The cause is usually one of the following: You are authenticated with a Console API key or a cloud provider such as Bedrock, Vertex, or Foundry.
  - now: They draw down your regular subscription usage like any other session.
​ Troubleshooting ​ /schedule returns “Unknown command” The CLI hides /schedule when one of its requirements isn’t met: the command menu shows No commands match "/schedule" while you type, and submitting it returns Unknown command: /schedule in every case below except a Console API key or an Anthropic profile with feature-flag fetching enabled.
The cause is usually one of the following: You are authenticated with a Console API key, an Anthropic profile or federation credential , or a cloud provider such as Amazon Bedrock, Google Cloud’s Agent Platform, or Microsoft Foundry.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: If ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is set in your shell, or apiKeyHelper is set in settings.json , remove it first, since these take precedence over a claude.ai login DISABLE_TELEMETRY , DO_NOT_TRACK , CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC , or DISABLE_GROWTHBOOK is set in your shell environment or in the env block of a settings.json file .
  - now: With a Console API key or a profile, submitting /schedule instead shows /schedule is available with Claude for Enterprise — ask your admin about migrating from API-key access .
With a cloud-provider login, you still see Unknown command: /schedule .
If ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is set in your shell, or apiKeyHelper is set in settings.json , remove it first, since these take precedence over a claude.ai login.
A profile or federation credential takes precedence too, so switch that off as well DISABLE_TELEMETRY , DO_NOT_TRACK , CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC , or DISABLE_GROWTHBOOK is set in your shell environment or in the env block of a settings.json file .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Manage routines from the web UI instead Your CLI is older than v2.1.81.
Run claude update You can always create and manage routines at claude.ai/code/routines regardless of how the CLI is configured.
​ ”Routines are disabled by your organization’s policy” An Owner in your Team or Enterprise organization has likely turned off the Routines toggle at claude.ai/admin-settings/claude-code .
  - now: Manage routines from the web UI instead Your organization’s policy disables Claude Code on the web , which routines run on An Owner turned off routines for your Team or Enterprise organization.
Before v2.1.227, the command still appeared in this case, and claude.ai rejected the routine when Claude tried to create or run it Unless your organization’s policy disables routines or Claude Code on the web, you can create and manage routines at claude.ai/code/routines regardless of how the CLI is configured.
​ /schedule asks you to authenticate If /schedule runs but Claude responds that you need to authenticate with a claude.ai account first, the CLI has no stored claude.ai login.
API accounts aren’t supported for routines.
Run /login , sign in with your claude.ai account, then run /schedule again.
​ “Routines are disabled by your organization’s policy” An Owner in your Team or Enterprise organization has likely turned off the Routines toggle at claude.ai/admin-settings/claude-code .
On Claude Code v2.1.227 or later, the same toggle also hides /schedule in the CLI.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Related resources /loop and in-session scheduling : schedule local tasks within an open CLI session Desktop scheduled tasks : local scheduled tasks that run on your machine with access to local files Cloud environment : configure the runtime environment for cloud sessions MCP connectors : connect external services like Slack, Linear, and Google Drive GitHub Actions : run Claude in your CI pipeline on repository events Was this page helpful?
Yes No Reference Plan in the cloud ⌘ I Claude Code Docs home page x linkedin Company Anthropic Careers Economic Futures Research News Trust center Transparency Help and security Availability Status Support center Learn Courses MCP connectors Customer stories Engineering blog Events Powered by Claude Service partners Startups program Terms and policies Privacy choices Privacy policy Disclosure policy Usage policy Commercial terms Consumer terms Assistant Responses are generated using AI and may contain mistakes.
  - now: ​ Related resources /loop and in-session scheduling : schedule local tasks within an open CLI session Desktop scheduled tasks : local scheduled tasks that run on your machine with access to local files Cloud environments : configure network access, environment variables, and setup scripts for cloud sessions MCP connectors : connect external services like Slack, Linear, and Google Drive GitHub Actions : run Claude in your CI pipeline on repository events Was this page helpful?
Yes No Reference Ultrareview ⌘ I Claude Code Docs home page x linkedin Company Anthropic Careers Economic Futures Research News Trust center Transparency Help and security Availability Status Support center Learn Courses MCP connectors Customer stories Engineering blog Events Powered by Claude Service partners Startups program Terms and policies Privacy choices Privacy policy Disclosure policy Usage policy Commercial terms Consumer terms Assistant Responses are generated using AI and may contain mistakes.
