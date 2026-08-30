# Pending delta — claude-code-changelog

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-30T16:56:01Z

- **new-claim** — adds a capability claim not previously upstream
  - now: ## 2.1.251

- Added `PreModelSwitch` and `PostModelSwitch` hook events (block, confirm, or annotate a model switch); `SessionStart` resume hooks now receive session staleness and the estimated re-cache cost
- Added live streaming of a foreground subagent's tool calls and results to Remote Control clients (background subagents, the default, still show status only)
- Added a Spend limit bar to `/usage` and a `rate_limits.spend_limit` status line field for developers behind a Claude apps gateway with spend limits
- Added a per-session prompt-cache line to `/cost` (hit ratio, misses, tokens re-cached, warm/cold) and a matching `prompt_cache` object for status line scripts
- Added `attach`, `logs`, `stop`, `respawn`, and `rm` to `claude --help`; the `--resume` message for a running background session now names the exact `claude attach <id>` command
- Fixed file tools (Read, Write, Edit) following a symlink swapped inside the working directory after the permission check, which could read or write outside the approved location
- Fixed plugin commands declared in a marketplace entry being able to point outside the plugin directory; such paths are now rejected with a path-traversal error
- Fixed project settings being able to enable detailed beta tracing or raw API body logging, and a lower-scope beta tracing endpoint bypassing an OTLP collector pinned by managed settings or a host app
- Fixed the Workflow tool reading (and quoting in errors) a `scriptPath` outside what the session may read before the permission check ran
- Fixed Grep and Glob not applying `Read(...)` deny rules to files reached through a symlinked search path
- Fixed conversations getting stuck on "text content blocks must be non-empty" errors after a turn where the model produced only thinking
- Fixed the first launch on a fresh install starting in default mode instead of auto mode for accounts whose startup default is auto mode
- Fixed Opus 5 requests failing with "effort … is not supported when thinking is disabled" when effort was xhigh/max and thinking was turned off; effort is now sent as `high` in that case
- Fixed replying to a message Claude Desktop delivered from another session: `SendMessage` to that session id now delivers through Claude Desktop instead of failing with "not reachable"
- Fixed TUI lag with many parallel subagents: per-second progress ticks now replace their predecessor instead of piling up in the transcript
- Fixed agent teams: a teammate's final answer not reaching the team lead — it now arrives in the idle notification instead of a content-free "available" notice
- Fixed background subagents being unable to reply to a message from an unnamed sibling or parent agent (`from` was the agent type, which is not an address)
- Fixed managed-settings `disableAutoMode` arriving mid-session not moving an already-running auto-mode session back to default mode
- Fixed a "switch to Opus 1M for 5x more context" tip that appeared even when the current Opus model already has a 1M context window
- Fixed Claude apps gateway sessions treating a stored Anthropic profile (e.g. a Console sign-in) as active: listing it in `/status` and retrying gateway 401s with it, though requests never use it
- Fixed cloud sessions telling Claude the model had changed when the host was only setting the session's initial model
- Fixed Remote Control reporting a failure when an organization's policy disables it; it now shows a single quiet notice instead
- Fixed `/mcp reconnect` on Remote Control showing a generic withheld-detail error instead of the real remedy when a server was disabled in another session
- Fixed `--input-format stream-json`: client-injected assistant tool calls sent without a message id were merged into the first one and their results lost, including when resuming older sessions
- Fixed session transcripts being silently overwritten when a directory change relocated a session onto an existing same-ID transcript
- Fixed background sessions and their subagents being unable to edit files inside a git worktree they created with `git worktree add`
- Fixed background sessions occasionally starting without any plugin skills (and staying that way) when another Claude Code process was refreshing the plugin marketplace at the same moment
- Fixed selecting text in an opened background session inside tmux over SSH: it now copies to the tmux buffer like a foreground session instead of falling back to OSC 52
- Fixed SDK and cloud sessions hanging indefinitely when an SDK MCP server's handshake acknowledgment was lost; the wait now times out after 70 seconds and marks only that server failed
- Fixed self-hosted runner leaving a stuck session's Bash tool processes running after the session was force-stopped
- Fixed `/usage-credits` for Team and Enterprise members whose admin set the org's usage-credit limit to $0: it now offers to ask the admin instead of saying a cap was reached
- Fixed `--worktree --tmux` with a merge-request number on a gitlab.com origin trying a doomed GitHub-style fetch first instead of fetching the GitLab ref directly
- Fixed Ctrl+G failing with "Emacs quit unexpectedly" in background sessions for editors that open `/dev/tty`, such as `emacs -nw` and `micro`
- Fixed an `additionalDirectories` entry containing a null byte crashing startup, or breaking `/add-dir` and later settings updates when it came from an SDK host, IDE, or hook; it is now skipped
- Fixed the MCP server menu's copy shortcut: it now says how the sign-in URL was copied instead of always claiming success
- Fixed italic text (such as the session recap line) rendering as highlighted blocks in GNU screen and in tmux sessions using a `screen` terminal type
- Fixed `claude mcp add --header` and `claude mcp add-json` help text naming the wrong transports
- Fixed `claude ultrareview` and `/ultrareview` waiting the full 30 minutes when the cloud session fails to start; they now stop early and report the reason
- Fixed Bash permission checks auto-approving commands that assign an arithmetic expression to an integer shell variable (e.g. `OPTIND=1/0`, `RANDOM=2+2`); these now prompt for approval
- Fixed backgrounded sessions (`←`, `/background`, `--bg`) losing a Vertex/Bedrock gateway (`ANTHROPIC_*_BASE_URL` + `CLAUDE_CODE_SKIP_*_AUTH`) exported in the shell, so every request failed
- Fixed `claude --bg --model fable` on Max plans stopping to ask for usage credits while the interactive session on the same account still had Fable allowance
- Fixed the one-time "make auto mode your default" offer appearing in unattended sessions (e.g. agent-team teammate panes), where a stray keypress could accept it unread
- Fixed the managed-settings approval prompt re-appearing after signing in again to the same Claude apps gateway when the settings are unchanged
- Fixed disabled `/bug` and `/share` reporting that `/feedback` was disabled; tips, `/help`, and refusal messages no longer suggest `/feedback` when an org policy or env var turns it off
- Fixed cloud session creation advising GitHub setup after a transient GitHub connection failure — the message now says to retry instead
- Improved CPU usage during turns in interactive sessions by cutting redundant UI re-renders
- Improved install size: the native binary is about 5 MB smaller
- Improved cloud sessions: when the session's network proxy drops a connection during a Bash command, the tool result now names the host and reason instead of only "connection reset"
- Improved `/schedule` to explain that MCP servers configured in Claude Code can't be attached to cloud routines, instead of a bare "No MCP connectors" message
- Improved framing of messages from your own subagents: Claude is told the sender is a worker inside this session, not an unrelated Claude session
- Improved the prompt placeholder to read "Message @name…" while viewing a background subagent or fork transcript opened from the subagent panel or `/tasks`
- Improved sanitization of MCP server names in error messages, menus, and command results
- Improved Amazon Bedrock session start under `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` (e.g. Claude Desktop): a session given a Bedrock model ID or ARN no longer waits for inference-profile discovery
- Improved the managed settings approval dialog to list only the settings that changed since you last approved them
- Improved retry when the model's tool call is malformed: the broken output is now dropped from the retry context, including on Bedrock, Vertex, and Foundry
- Changed `/radio` to be available on Bedrock, Vertex AI, Foundry, and Claude Platform on AWS, and when telemetry is disabled
- Changed Claude in Chrome so browser actions always go through Claude Code's permission checks, including in sessions with telemetry disabled, which previously used the Chrome extension's own prompts
- Changed `CLAUDE_CODE_SUBAGENT_MODEL` to set the default subagent model rather than override everything: an agent definition's `model:` and an explicit per-spawn model now take precedence over it
- Changed the default commit trailer to `Co-Authored-By: Claude Code` when the active model isn't a recognized Claude model (e.g. third-party models behind a custom `ANTHROPIC_BASE_URL`)
- Changed the default model for seat-based Enterprise subscriptions to Opus 5, matching other premium plans
- Changed `/effort` to save your default effort level per model, so each model keeps its own setting when you switch
- Changed analytics to no longer turn off before sign-in solely because managed settings force gateway login (or cannot be read); they stay off once signed in to the gateway or via `DISABLE_TELEMETRY`
- Changed the footer PR badge on Bedrock, Vertex, and Foundry, and when telemetry is off, to call the GitHub API directly (via `gh auth token`, `GH_TOKEN`, or `GITHUB_TOKEN`) instead of `gh pr view`
- Changed how Bash command output files are created and read back when commands run in the sandbox, so a sandboxed command cannot redirect or replace them
- Changed plugin/LSP install suggestions and the auto-mode default offer to wait until you've sent or cleared what you're typing, so the Enter that sends your prompt can't answer them
- Changed server-managed settings that terminate sandbox TLS, route sandbox traffic through your own proxy, inject credentials, or weaken sandbox isolation to require approval before they apply
- Changed `ANTHROPIC_CUSTOM_HEADERS` from managed or project settings to require approval when it sets a credential, org/tenant, routing, or API-behavior header (e.g. `Authorization`, `Host`)
- Changed project-level `.claude/settings.json` `env` to no longer set `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR`, or `TMPDIR`/`TMP`/`TEMP`; set them in your shell, user, or managed settings instead
- Removed syntax highlighting for six rarely used languages (1c, gml, isbl, mathematica, maxima, sqf); the binary is 2.5 MB smaller
- [VSCode] Fixed the sign-in screen's "Bedrock, Foundry, or Vertex" button opening the docs at the top of the page instead of the third-party provider setup section
- [VSCode] Changed the Remote Control banner to a footer pill (shown while Remote Control is on or has failed) that opens the session on claude.ai/code; turn it on or off with `/remote-control`

## 2.1.250

- Bug fixes and reliability improvements

## 2.1.248

- Added `--restricted` (or `CLAUDE_CODE_RESTRICTED=1`): removes the built-in tools that run commands or code and `WebFetch` (unless named in `--tools`), keeps file tools inside the working directory, refuses `bypassPermissions`, and ignores user, project and local settings files
- Added `experimental.cacheTtl` (`"5m"` or `"1h"`) to agent frontmatter: a per-agent prompt cache TTL used when no subagent TTL setting is configured
- Added `claude self-hosted-runner --client-label <label>` (or `SELF_HOSTED_RUNNER_CLIENT_LABEL`) to override the label the runner registers with (default: hostname)
- Added server-managed settings diagnostics: a startup warning when the settings fail to load, and a `/doctor` and `/status` line explaining a load failure or why they weren't fetched (Bedrock/Vertex/third-party provider, custom `ANTHROPIC_BASE_URL`)
- Added a warning in `/web-setup` when the GitHub CLI token lacks the `workflow` scope, since pushes to very large repositories can be rejected without it
- Added `/usage-credits` for Enterprise organizations billed through AWS Marketplace, self-serve Enterprise, and Enterprise trials, so members can request a higher usage limit from their admin
- Added cross-session messaging (`SendMessage` / `ListAgents`) between sessions on the same machine on Bedrock, Vertex, and Foundry, and when telemetry is disabled
- Fixed a prompt-cache miss (and lost extended-thinking context) roughly once an hour in long sessions, caused by tool definitions being re-rendered after an OAuth token refresh
- Fixed the `ScheduleWakeup` tool definition changing between a session and its `--resume` when the account had entered usage overage, causing a full prompt-cache miss on the resumed session's first turn
- Fixed Claude Desktop and Cowork sessions disappearing after 30 days: the transcript cleanup now keeps desktop-written sessions while they are in the app (unless org policy manages retention); the new `desktopSessionCleanupPeriodDays` setting caps the exemption
- Fixed being sent to the login screen when another Claude Code process held the token refresh lock while the session token had expired; the request now fails with a retryable error instead
- Windows: Fixed the `claude agents` list not responding to the keyboard after detaching from a session, or when launched in a terminal tab left in win32-input-mode
- Fixed the recommended Console sign-in in `/login` failing with an OAuth error before showing a sign-in URL on machines where it can't be used (for example when `ANTHROPIC_API_KEY` or an API key helper is set); it now falls back to the API-key sign-in
- Fixed model names in `/model` and fast-mode switch notices to render as code, so suffixes like `[1m]` display literally instead of as a link
- Fixed `claude agents` skipping the workspace trust prompt when the `CI` environment variable is set
- Fixed `claude agents` crashing on launch when the PR-status cache held a malformed entry
- Fixed agent view resurrecting a weeks-old background session after the machine was off: such a session now shows as stopped at its real end, and opening it asks before resuming its saved conversation
- Fixed agent view sometimes opening an older conversation, and dropping the typed prompt, when starting a new session
- Fixed `claude agents`: opening a stopped session that you already resumed in another terminal no longer starts a second process on that conversation; the row now says it is open in a terminal
- Fixed `claude agents` and `claude rm` refusing to delete a session ("has commits that are not pushed anywhere") when its worktree branch was already merged into your checked-out default branch (e.g. local `main`) but not yet pushed
- Fixed background sessions waiting silently when a `PermissionRequest` or `PreToolUse` hook prints an invalid answer: the `claude agents` row now names the hook and the schema error
- Fixed hooks silently treating a stdout `{…}` object that isn't valid JSON as plain text; it's now reported as a hook error with the parse message
- Fixed `/mcp` listing a project `.mcp.json` entry that declares the claude.ai connector type under the trusted "claude.ai" heading; it now appears under its real scope
- Fixed MCP servers whose `headersHelper` supplies the `Authorization` header falling into OAuth discovery on a 401 instead of re-running the helper and retrying the call as documented
- Fixed `/login` to a Claude apps gateway hanging when the managed-settings security approval dialog was required
- Fixed gateway model discovery (`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY`) never running when `apiKeyHelper` is the only credential
- Fixed `claude logs` leaving mouse tracking, bracketed paste and the alternate screen switched on in the terminal it was run from
- Fixed the trust dialog's list of repo permission rules showing a garbled character when a long rule was cut off in the middle of an emoji
- Fixed the permission mode indicator staying hidden behind the "Press Ctrl-C again to exit" hint when you press shift+tab right after ctrl+c
- Fixed `/ultrareview` and locally seeded cloud sessions uploading uncommitted edits to `prod.env`-style and `*.tfvars` files, or to editor swap, temp, and backup copies of credential files (e.g. `key.pem.tmp`, `id_rsa.swo`); they now stay on your machine
- Fixed Remote Control sessions occasionally never showing a permission prompt or the latest messages on the connected device after the CLI silently reconnected
- Fixed cloud sessions occasionally failing at startup when the container's session credentials were not yet readable
- Fixed `claude remote-control` rejecting its own flags (e.g. `--spawn`, `--name`) when a global flag or a wrapper-injected option precedes the subcommand
- Fixed startup warnings (e.g. "N MCP servers need authentication") rendering one column right of the rest of the transcript
- Fixed a backgrounded worktree session losing its checkout: the background session now holds the worktree's lock while it runs, so cleanup and `git worktree remove` leave it alone
- Fixed @-mentions of other sessions not matching names typed with non-Latin characters (for example Korean entered through an IME)
- Fixed an invalid `crossSessionInbound` value being silently ignored: it now warns and holds cross-session messages (user settings) or refuses them (managed settings) until fixed
- Fixed rate-limit, usage, and fast-mode messages telling you to run `/usage-credits` when that command isn't available for your organization (e.g. hidden with `DISABLE_EXTRA_USAGE_COMMAND`)
- [VSCode] Fixed a chat tab getting stuck on "No conversation found" when its session was never saved; it now starts a new conversation instead
- Improved the Workflow tool's prompt footprint: its description is now about 1k tokens instead of 5.7k, with the script-writing reference moved into a bundled `workflow-authoring` skill
- Improved the prompt-footer PR badge to check GitHub less often while the pull request is unchanged; a push or a `gh pr` command still refreshes it right away
- Improved managed settings: client-side timeout, MCP startup-mode, and stream-watchdog env vars no longer trigger the settings-approval prompt
- Improved `/ultrareview <PR#>` to check before launch that the GitHub account connected to your Claude account can access the repository, and to explain how to fix it, instead of failing after the cloud session starts
- Improved cross-session messaging: falls back to a private per-user `/tmp` directory when the default one can't be used, and the notice and `/status` name the directory to fix
- Changed shift+enter in the agent view dispatch input to insert a newline (matching the prompt); ctrl+enter now dispatches and attaches
- Changed `/loop`: self-paced dynamic mode and the no-prompt autonomous default are now always available, including on Bedrock/Vertex/Foundry
- Changed Anthropic telemetry export failures to log at debug level as `[Anthropic telemetry]` instead of `[3P telemetry] OTEL diag error`, so they are not mistaken for your OTel collector failing
- Changed cross-session messaging in Linux user namespaces: root-equivalent trust for unmapped owners is limited to canonical system directories
- Changed `SendMessage` from a subagent to another session: the result now notes that any reply is delivered to the parent session's conversation, not to the subagent

## 2.1.247

- Added the `SendFeedback` tool: when something goes wrong in a session, Claude can draft a feedback report for you to review and send from `/feedback` (turn off with the `feedbackDrafts` setting)
- Added `{id, text, cooldownSessions, priority}` entries, `tipsFile`, and `label` to `spinnerTipsOverride`, so organizations can rotate their own tips alongside the built-in ones
- Added a tip on Bash permission prompts pointing to auto mode, with a one-keystroke "Yes, and switch to auto mode" option
- Added `/claude-api cost-optimize` to profile an existing project's Claude API spend and work through cost levers (caching, token hygiene, batch, effort, model choice) one measured change at a time
- Updated the `/claude-api` skill with Admin API coverage (organization members, invites, workspaces, API keys, rate limit reports, workload identity federation, CMEK)
- Fixed fast arrow-key + Enter sequences acting on the row above the one you navigated to in history search, `/config`, `/mcp`, `/skills`, background tasks, and `/model`
- Fixed sub-agents dying on a first-call model 404: they now use the session's fallback model chain, and the error returned to the parent includes the error type, status, request id, and model
- Fixed a hook or background agent that printed megabytes of error output being able to overflow the conversation and wedge the session on "Prompt is too long"
- Fixed Ctrl keyboard shortcuts not firing under non-Latin (e.g. Cyrillic) keyboard layouts in kitty-protocol terminals
- Fixed text like `<35;150;7M` being inserted into the prompt when a mouse report arrived split across reads right after the escape prefix
- Fixed the Bash sandbox's after-command cleanup deleting a dotfile-managed `~/.claude/settings.json` symlink (nix/home-manager, stow) when it is repointed outside the sandbox's writable area
- Fixed `/terminal-setup` overwriting your entire Zed `keymap.json` instead of merging in its keybinding
- Fixed `/rename` silently confirming when the session registry could not be updated; it now says other sessions may still show the old name
- Fixed `/compact` and "Summarize from here" in sessions started with `--agent` summarizing under the default system prompt instead of the conversation's own
- Fixed a background session showing "opening…" forever in `claude agents` after its terminal host process died; the row now fails within seconds with the reason, and Enter restarts it
- Fixed unbounded memory growth when a hook's or background task's output file could not be written; the file now notes where output was lost
- Fixed `/install-github-app` over SSH: the copy shortcut now says how the sign-in URL was copied instead of always claiming success, and the URL appears immediately when no browser can open
- Fixed shell commands carried over from the foreground logging an internal error or showing a misleading `[exited with code -1]` line when they finish in background sessions
- Fixed a version-less marketplace plugin's live cache directory being deleted and recreated on a second-scope install, which could disrupt a running session using it
- Fixed Remote Control sessions started with `/remote-control` not reporting the working-tree diff to connected clients
- Fixed self-hosted runner sessions reporting `running` before Claude Code had started, which could trigger a premature "Claude is waiting for your input" notification from the Claude desktop app
- Fixed first-run setup exiting with "Unable to connect to Anthropic services" when managed settings configure Claude apps gateway sign-in and Anthropic endpoints are unreachable
- Fixed cloud sessions (Claude Code on the web, desktop and mobile apps) sometimes showing the previous permission mode when you switch modes right after sending a message
- Fixed cloud sessions going silent when the session's container restarts between turns while a background agent, shell, or monitor is still running — the resumed session now reports the lost work
- Improved plugin marketplace hardening: names containing control or invisible characters are rejected, and marketplace-supplied text in `/plugin` and `claude plugin` output is escape-safe
- Improved Bedrock, Vertex, and Foundry sessions (and any with telemetry disabled): Claude is now told when a configured MCP server failed to connect, instead of concluding its tools don't exist
- Changed Sonnet 5's default auto-compact window to its full 1M context, so sessions on the 1M window now auto-compact at about 967K tokens instead of about 934K
- Changed cross-session peer messages to collapse by default to a one-line `Message from @<sender>: <first line>` preview; Ctrl+O expands the full body
- Changed terminal hyperlinks in rendered markdown: link targets that point at a network or automounter path, contain a control character, or lead with an invisible character now render as plain text
- Changed the prompt-footer PR badge to skip its GitHub re-check on terminal refocus when the last check is under a minute old
- Changed analytics to stay off from startup, not only after login, when managed settings force gateway login or a custom OAuth deployment is configured
- Changed Claude apps gateway sign-in requests to identify Claude Code (a `surface=claude_code` device-authorization parameter and a `claude-code/<version>` User-Agent)
- Changed organization sign-in enforcement to exit at start when the administrator's managed settings cannot be read, even if host-supplied or per-user Windows registry settings exist

## 2.1.246

- Added a startup warning for Bash allow rules with a wildcard before the subcommand (e.g. `Bash(git * main)`), since they also match options inserted before the subcommand
- Added an Auto mode tab to `/permissions` for viewing and editing auto mode classifier rules
- Added the turn's completion time to the end-of-turn duration line, e.g. `✻ Sautéed for 23s · done 6:05 PM`
- Fixed fullscreen mode showing a blank transcript after resizing the terminal and jumping to the bottom until the next keypress
- Fixed a severe transcript slowdown when a diff contained a very long single line (e.g. a base64 string); such lines now render truncated with a marker
- Fixed erratic fullscreen scrolling when positioned at an earlier message, including jump-to-bottom getting stuck mid-transcript
- Fixed background sessions failing to open after 45 seconds when Claude Code's starting directory had been deleted, the machine had slept, or the host is slow to start processes
- Fixed background sessions failing to open with "Couldn't start the background service … EACCES" when another Claude Code process was re-installing the npm package at that moment
- Fixed markdown rendering being disabled for a whole message when its first 500 characters contained no markdown, and for `+`/`N)` lists and setext headings
- Fixed MCP tool calls interrupted by an incoming message in headless/remote sessions being reported to the model as "completed with no output" instead of an explicit interrupted error
- Fixed MCP tool arguments being sent as JSON strings when the parameter's schema is empty (`{}`), instead of their real type
- Fixed a command interrupted mid-run showing as "Ran 1 shell command" with no sign it was cut
- Fixed pressing ← or running `/background` during a dynamic workflow restarting its finished subagents; it now asks first and says how many subagents would restart
- Fixed opening a just-started session in `claude agents` while its worker was still booting (common on Windows) stopping it with "was stopped while the respawn was in flight"
- Fixed `claude agents` listing a backgrounded named session twice; backgrounding the same conversation again now numbers the new row (e.g. `my-session (2)`)
- Fixed the background retention sweep removing git worktrees under `.claude/worktrees/` that you created yourself when an old background-session record pointed at them
- Fixed auto mode tool calls being denied as "temporarily unavailable" on very large sessions by scaling the safety-check deadline with prompt size
- Fixed the plugin cache creating duplicate SHA-named directories for the same plugin
- Fixed plugin skills whose frontmatter `name` already includes the `<plugin>:` prefix showing it doubled in the slash menu (e.g. `/plugin:plugin:skill`)
- Fixed `claude plugin update` failing for an installed plugin given its bare name (only the fully-qualified name worked)
- Fixed plugin installation failing when `plugin.json` was saved with a UTF-8 byte-order mark (BOM)
- Fixed `/reload-plugins` reporting 0 skills for plugins that define skills under `skills/*/SKILL.md`
- Fixed hook error messages showing a literal `${CLAUDE_PLUGIN_ROOT}` instead of the resolved plugin path
- Fixed `/rename` replacing the theme's prompt border color (including a custom theme's `promptBorder`) with the default cyan; the border now keeps your theme's color unless you pick one with `/color`
- Fixed custom theme diff colors (`diffAdded`/`diffRemoved` and their dimmed variants) being ignored in diffs and the `/theme` preview
- Fixed a `keybindings.json` binding with an unknown action name silently deadening that key; it is now skipped so the default binding keeps working, and a warning is logged under `--debug`
- Fixed `/stats` activity heatmap showing each day's activity one cell off (Sunday's count under Monday) in timezones east of UTC
- Fixed `/fork` from an already-forked or backgrounded session starting the new session with an empty conversation
- Fixed prompts beginning with `/--` (e.g. Lean doc comments) being rejected as an unknown slash command instead of being sent to Claude
- Fixed the `@` file picker staying open after the typed text stopped matching a real path
- Fixed the status line's cost and duration resetting to zero after navigating to the agents view and back
- Fixed fullscreen mode moving keyboard focus onto the control under the pointer when you clicked the terminal window only to bring it back into focus
- Fixed path completion failing when the completion token or working directory contained a null byte
- Windows/macOS: Fixed headless sessions not cleaning up stale entries in `~/.claude/sessions` left by sessions that exited uncleanly
- Fixed the UI stopping with a render error on the first tool call when a third-party Anthropic-compatible endpoint (`ANTHROPIC_BASE_URL`) streams a `tool_use` block without an `id`
- Fixed the Write tool reporting "Out of memory" or freezing for a long time after overwriting a very large existing file, even though the file had been written
- Fixed `claude plugin install <name>` exiting silently (or hanging in a terminal) instead of reporting an error when `~/.claude/plugins/known_marketplaces.json` is empty or corrupted
- Fixed resumed sessions failing every turn with a 400 when the saved history contains tool blocks the Anthropic API does not accept (typically written by a third-party API proxy)
- Fixed `curl -fsSL https://claude.ai/install.sh | bash` failing with "Raw mode is not supported" for some Team/Enterprise users with server-managed settings
- Fixed sessions that ended in plan mode resuming outside plan mode in the VS Code extension, and in `claude -p --continue`/`--resume` with a permission prompt tool, when no permission mode was set
- Fixed the `Notification` hook not firing while the sandbox "Network request outside of sandbox" permission prompt is waiting
- Fixed Bash permission checks to always require approval for malformed commands with a dangling `&&` or `||` operator
- Fixed `--strict-mcp-config` sessions prompting to approve `.mcp.json` servers they would never load, which left background sessions waiting at startup
- Fixed telemetry and metrics requests to Anthropic carrying the API key configured for a third-party gateway (`ANTHROPIC_BASE_URL`); a credential is now only sent to its own host
- Fixed a visible API error on the first prompt after idle when `apiKeyHelper` returns short-lived JWTs: an expired cached token is now refreshed before sending, and 401/403 auth errors retry quietly
- Fixed memory growing with session length in the fullscreen and Ctrl+O transcript views: each rendered message row no longer retains a full copy of the transcript-wide tool lookups
- Fixed `/ultrareview` runs and cloud sessions launched at the same time from one repository (e.g. from several worktrees) sometimes starting with another launch's uncommitted changes
- Fixed the task progress count (e.g. `3/5`) shown for background cloud sessions such as `/autofix-pr` occasionally missing a task
- Fixed Remote Control sessions keeping their placeholder name in claude.ai and the Claude app until the second prompt; the auto-generated title now appears after the first prompt
- Fixed MCP tools marked `requiresUserInteraction` still offering "Yes, and don't ask again" in their permission prompt; the option wrote an allow rule the tool then ignored
- Fixed the self-hosted runner ending its live sessions or exiting when a work-poll response is malformed (e.g. an intercepting proxy's HTML page); it now retries the poll
- Improved `/cd`: the new directory's project settings, hooks, `.mcp.json` servers (behind the usual approval prompt), skills, and agents now take effect right after the move instead of on `--resume`
- Improved Bash tool latency on bash shells by replaying snapshot functions without a base64 subshell per function
- Improved subagent results: a subagent that stops at its `maxTurns` limit now returns its output marked as partial, with a hint to continue it via `SendMessage`, instead of appearing finished
- Improved non-interactive sessions (`-p`, SDK, cloud sessions) to automatically continue a response cut off mid-stream by a server error, connection loss, or stall instead of ending with an error
- Improved attribution of usage telemetry to your organization for workload identity federation sessions, events sent while `apiKeyHelper` runs at startup, and after a login token expired while idle
- Changed `/code-review` so Claude can also start it on its own on Bedrock, Vertex AI, and Foundry, through the Claude apps gateway, and when telemetry or non-essential traffic is disabled
- `/goal`: Changed idle sessions to start at most three check-ins on long-running background work per goal; your next message allows three more
- Changed `claude install` and `claude update` to defer a pending managed-settings consent prompt to the next interactive session instead of prompting mid-command
- Changed OpenTelemetry plugin events for plugins synced from claude.ai: `plugin_id_hash` now reflects the plugin's real marketplace, and `enabled_via` is `admin-install` for admin-installed plugins
- Fixed the command sandbox's filesystem configuration not respecting `--setting-sources`

## 2.1.245

- Fixed a crash on startup on Linux distributions that ship glibc 2.44 (for example Arch Linux, CachyOS and Fedora Rawhide)

## 2.1.243

- Added a Loops breakdown to `/usage`: per-loop run count, total tokens, tokens per run, and last run, so runaway or chatty `/loop` tasks are easy to spot
- Added `modelPicker` setting: curate the `/model` picker with an ordered, labeled list of models (any id spelling, including Vertex/Bedrock ids), appended to or replacing the built-in lineup
- Added `promptCacheTtl` and `subagentPromptCacheTtl` settings so API-key and cloud-provider users can keep a 1-hour prompt cache on the main conversation while subagents stay at 5 minutes
- Added `modelPricing` managed setting so an organization's contracted per-model rates and discount multiplier are used for `/cost`, the status line, and telemetry cost figures instead of list price
- Added a keyless sign-in under `/login` → Anthropic Console: "Sign in with your Console account" (recommended) alongside creating an API key, so organizations that don't allow API keys can sign in
- Added a `Skipped sources` line to `/status` that lists managed settings sources (for example `managed-settings.json`) present but not applied because a higher-precedence managed source is active
- Added a `managed` marker in `/mcp` and `/plugins` on claude.ai connectors whose authentication is managed by your organization
- Added a tip pointing claude.ai users who haven't connected GitHub for Claude Code on the web to `/web-setup`
- Added a `/status` line showing whether GitHub is connected for Claude Code on the web (Pro/Max), pointing to `/web-setup` when it isn't
- Added the model (and effort level) each subagent ran on to `/tasks` and the agent detail dialogs
- Fixed remote MCP servers in non-interactive (`-p`) and SDK sessions never recovering after a dropped connection; they now reconnect automatically or report as failed
- Fixed MCP server sign-in started from the desktop app failing with "Invalid redirect URI" on servers that support client ID metadata documents (for example Linear)
- Fixed auto mode staying unavailable at startup when a temporary server-side disable was cached and later flag fetches failed
- Fixed auto mode tool calls being denied as "temporarily unavailable" after about a minute of waiting when the API was briefly overloaded and asked the client to retry
- Fixed the `/model` picker silently ignoring an Ultracode selection; picking Ultracode now applies it to the current session
- Fixed `/resume` only listing the 50 most recent sessions; the picker now loads more as you scroll
- Fixed cloud sessions resuming after a mid-turn restart with a pending hook or background-task notification re-sent as the prompt instead of the normal continuation message
- Fixed cross-session messaging silently turning off inside user namespaces and rootless containers after the 2.1.232 socket-directory hardening
- Fixed text that hangs outside its container (for example the sign-in URL in `/login`) losing its leading columns when another part of the screen repaints
- Fixed `spellcheck` not underlining a misspelled word typed directly after an emoji
- Fixed background subagents not waking when their last background Bash task completes
- Fixed sessions going silent for 10+ minutes when the Anthropic API never starts a response: the request now times out after ~3 minutes, retries once, then shows `API Error: No response from API`
- Fixed auth, model-availability, and other client-generated error messages rendering like model output instead of as error lines
- Fixed workload identity federation in CI: processes in one job share the exchanged token instead of re-exchanging the single-use token; a rejected exchange fails fast with the server's message
- Fixed server-managed `companyAnnouncements` not showing at startup in a session that began with signing in (for example the first launch after `/logout`)
- Fixed hook `if` conditions like `Bash(cat *)` firing on unrelated Bash commands when the command contained `$()` or backtick command substitution followed by more arguments
- Fixed plugin dependencies declared with a `marketplace` field never resolving when both plugins are loaded together via `--plugin-dir`
- Fixed `/reload-plugins` keeping the LSP tool after the last LSP plugin is disabled; it now also warns before an LSP plugin change that would re-read the conversation
- Fixed `--agents` silently ignoring invalid JSON or invalid agent definitions; it now exits with a clear error, like `--mcp-config`
- Fixed `/status` showing "Found invalid entries in: ." with no filename when `~/.claude.json` has an invalid MCP server entry
- Fixed `/clear` removing the `/rename` session name from the prompt bar even though the name was kept for the new session
- Fixed Ctrl+R history search and up-arrow history breaking when `~/.claude/history.jsonl` contains a malformed entry
- Fixed Ctrl+[ not leaving vim INSERT mode in terminals that encode modified keys (modifyOtherKeys / kitty protocol)
- Fixed the local IDE connection being routed through `HTTPS_PROXY` (and sometimes failing) when `localhost` was listed in `NO_PROXY` but not lowercase `no_proxy`; both casings are now honored
- Fixed sandbox network-violation details being dropped from the Bash tool result when the blocked command still exited 0 (for example `curl` printing the proxy's 403 page)
- Fixed the status line `rate_limits` fields and `/usage` still showing a rate-limit window's pre-reset usage percentage after the window reset while the session was idle
- Fixed `claude --teleport <session>` exiting on uncommitted changes instead of offering to stash them and continue, as the session picker already does
- Fixed `/web-setup` repeatedly asking you to log in when an older GitHub CLI (without `gh auth token`) was already authenticated
- Fixed Claude in Chrome losing its connection to Claude Code after an auto-update cleaned up the version it was set up with; the native host now launches via the stable `claude` launcher
- [VSCode] Fixed sessions started before feature flags were first fetched (for example right after install) opening in the default permission mode instead of auto mode or your configured default mode
- [VSCode] Fixed Focus view sections you expanded collapsing on their own during subagent tool activity
- Improved startup time: sandbox and MCP bring-up no longer block the first frame, bare launches skip subcommand registration, and workflow discovery, settings, and trust-store work is cheaper
- Improved native install and auto-update download size: the binary is now zstd-compressed (about 75 MB instead of 340 MB on Linux x64)
- Improved attribution of usage telemetry to your organization for sessions that authenticate with `ANTHROPIC_AUTH_TOKEN` directly against the Anthropic API, so its data-handling settings apply
- Improved native binary size: about 2 MB smaller by storing the bundled skill and prompt text more compactly
- Improved memory usage of native builds: code is now loaded on demand instead of keeping the whole bundle resident (roughly 40–70 MB less memory per session)
- Improved peak memory usage in long-running sessions (the runtime now garbage-collects sooner as the heap grows)
- Improved `/login` over SSH: the sign-in URL appears immediately, pressing `c` reports how the URL was copied instead of always claiming success, and a hint explains how to select text in fullscreen
- Improved the error when effort `xhigh`/`max` is used with thinking turned off: it now names the level, the setting that disabled thinking, and `/effort high` as the fix
- Improved `/loop`: consecutive wake-ups where Claude has nothing to do now fold into a single line in the terminal instead of printing each one
- Changed the sandboxed Bash tool prompt to no longer list allowed network hosts, so Claude attempts requests (and you can approve new hosts) instead of assuming unlisted hosts are blocked
- Updated the `/model` picker and the bundled `claude-api` skill to show Sonnet 5's $2/$10 per Mtok pricing as its standard list price rather than a limited-time promo
- Changed computer use on macOS so clicking the desktop, Dock, or a Finder window requires granting Finder via the access dialog, like any other app
- Changed `/model`, `/fast`, and `/effort` to also run immediately instead of queueing until the turn ends on Bedrock, Vertex, and Foundry and when telemetry is disabled
- Fixed `claude remote-control` exiting and stranding attached Remote Control sessions when the server drops its environment mid-session; it now recovers
- Fixed Remote Control sessions served by `claude remote-control` sometimes getting stuck after it was stopped and restarted, for Team and Enterprise members without an admin or owner role
- Changed the cross-session messaging inbox socket to close connections that send no complete line within 30 seconds; scripts posting to it should connect once their data is ready
- Improved the notice when resuming a conversation whose Remote Control is held by another terminal: it now says sessions on other machines can't be seen from, or reach, this one
- [VSCode] Improved history trimming in long sessions: older tool-activity rows are dropped first so your messages and Claude's replies stay visible
- [VSCode] Improved attribution of the extension's own usage telemetry to your organization when you are signed in with a Claude account, so its data-handling settings apply

## 2.1.241

- Bug fixes and reliability improvements

## 2.1.240

- Bug fixes and reliability improvements

## 2.1.239

- Cost estimates (`/cost`, status line, `--max-budget-usd`) now include the 1.1× US-only-inference premium for data-residency workspaces
- Added the one-time fullscreen renderer offer on Bedrock, Vertex, Foundry and other previously excluded setups; new installs there now start in fullscreen
- Added `/claude-api upgrade` to migrate Python projects from `anthropic` 0.x to 1.x, and updated the skill's Python reference for 1.x (timeouts use `anthropic.Timeout`, not `httpx.Timeout`)
- Cloud sessions: plugins synced from claude.ai now show as `name@synced`, work with `claude plugin enable/disable <name>@synced`, and never override a same-named plugin you installed
- Alpine/musl builds: native image paste, clipboard, and audio-capture add-ons now load (musl-built binaries instead of glibc ones refused by the runtime)
- The usage-limit message shown when your monthly spend limit is already used up now also says when your session or weekly limit resets
- Fixed Bedrock streaming behind proxies that strip the response Content-Type header, which silently doubled billed API calls by re-running every turn non-streaming
- Fixed Claude Code hanging at startup behind an HTTPS proxy when using Bedrock with an SSO profile and `awsAuthRefresh` — the credential pre-check now honors `HTTPS_PROXY`
- Fixed a raw crash dump when starting Claude Code from a directory that no longer exists; it now prints a clear message
- Fixed Edit and Write calls pausing for about 5 seconds in JetBrains IDE terminals when the Claude Code plugin is connected
- Fixed a race where pressing Esc with a prompt queued could let the next turn finish early, leaving the session idle while Claude was still working and letting a later resubmit repeat actions
- Fixed WebFetch retaining expired page content in memory for the whole session instead of the intended 15 minutes
- Fixed cloud sessions (Claude Code on the web, desktop and mobile apps) resuming out of plan mode after an idle worker restart
- Fixed MCP elicitation forms taller than the terminal being clipped in fullscreen mode: the form now fits the window, with hidden fields reachable by scrolling and Accept/Decline always visible
- Fixed remote MCP servers staying failed after a transient 5xx on a mid-session reconnect in cloud sessions or via SDK `setMcpServers()`
- Fixed custom session titles disappearing from `/resume` after more than ~64 KB of conversation was written following the rename
- Fixed `claude -c`/resume picking up sessions from a different directory whose path differed only by characters like `_`, `-`, or `.`
- Fixed `/resume` and the agents view showing a session as recently changed (and reordering it) when only its file was touched or it was merely reopened
- Fixed `/resume` in all-projects mode telling you to `cd` into a deleted directory (e.g. a removed worktree); such sessions now resume in the current directory
- Fixed the `dark-ansi` theme rendering expanded tool results in fullscreen mode with text the same color as the background
- Fixed the fullscreen renderer prompt reappearing on every launch when it could never be answered; it now stops after being shown on three launches
- Fixed `.worktreeinclude` patterns starting with `**/` silently matching nothing when the target lived in a gitignored directory
- Fixed agents, skills, and commands whose `.md` file starts with a UTF-8 BOM being silently ignored
- Fixed `/insights` echoing literal `<message>` tags in its response on some models
- Fixed marketplace `metadata.pluginRoot` having no effect: bare plugin source names now resolve under it as the docs describe
- Fixed mouse movement in browser-based terminals inserting text like `"35;150;7M"` into the prompt when a mouse report arrived split across writes
- Fixed custom theme overrides for the effort/ultracode status badge colors being ignored
- Fixed OpenTelemetry trace fragmentation: tool executions deferred by a `PreToolUse` hook now resume in the original turn's trace instead of starting a new trace
- Fixed vim mode in the agent view: Escape now switches to NORMAL mode and keeps your text instead of clearing the prompt
- Fixed the `selection:copy` keybinding silently dropping a text selection that had been extended with Shift+Arrow keys
- Fixed the `/voice` startup tip still appearing after voice dictation was enabled via the `voice.enabled` setting
- Fixed shell-mode (`!`) Tab completion dropping the `./` from a `./script` path, which left a command the shell couldn't run
- Fixed fullscreen mode answering a permission prompt or pressing a button when you clicked the terminal window only to bring it back into focus
- Fixed slash-command panels (e.g. `/config`, `/model`) in fullscreen mode covering the latest messages; the conversation now stays pinned above the panel
- Fixed the `/workflows` detail dialog overflowing the terminal and losing its header off-screen when opened while Claude is still responding
- Fixed the Linux sandbox making a nonexistent `.git/config.worktree` unreadable, which broke every sandboxed git command in repos with `extensions.worktreeConfig` set
- Fixed hooks failing with "posix_spawn ENOENT" after the session's working directory was deleted; they now run from the project root or home directory instead
- Fixed `claudeMdExcludes` not excluding a symlinked `.claude/rules` file when the pattern names the rules directory or the symlink rather than its target
- Fixed runaway session-title syncing to Remote Control when two Claude Code processes shared one background job's state (2.1.232 regression); title updates are now deduplicated and rate-limited
- Fixed sessions whose title starts with `/` being unaddressable by `SendMessage` and shown as "(untitled)" in `ListAgents`
- Fixed Ctrl+W, Ctrl+U, Ctrl+K, Option+Backspace, Option+D and vim `df`/`dt` leaving a broken `[Pasted text #N]` placeholder when the cursor was inside it
- Fixed masked (password-style) inputs such as the login code field letting their text be pasted back with Ctrl+Y elsewhere or saved to prompt history when cleared with double Esc
- Fixed Ctrl+Backspace deleting one character instead of a word in search boxes
- Fixed a request rejected by an organization policy check being re-sent before the rejection was shown
- Improved the reminder shown after compaction so a skill's original arguments are not re-run as a new request
- Long file paths on tool-use rows now truncate in the middle to stay on one line
- Remote sessions keep sending keep-alives while a long `SessionStart` or `Setup` hook runs, so the container is not idle-reaped mid-hook
- `/goal`: repeat check-ins on long-running background work now back off (30 min, then 1 h, then every 2 h) instead of repeating every 30 minutes
- `/goal`: resuming a session from the `claude --resume` picker now restores its active goal
- `ListAgents` now tells a session its own name (the one peers use to message it), and `SendMessage` to your own name says so instead of "no agent named …"
- `ListAgents` and `/list-agents` now list your live teammates (previously only subagents and other sessions appeared, so a reachable teammate looked absent)
- `keybindingFlavor: "readline"` now also matches Bash for word keys: Alt+F and Ctrl/Option+→ stop at the end of the word, Alt+D deletes to it (Ctrl+Y pastes it back), and punctuation separates words
- Persistent retry mode (`CLAUDE_CODE_RETRY_WATCHDOG`) now fails immediately on organization spend-limit and out-of-credits errors instead of waiting indefinitely for a reset
- Claude in Chrome: `/clear` now closes the session's Chrome tab group, and empty groups are closed on `/resume` and when Claude Code exits
- Remote sessions: images uploaded from mobile now include their saved file path, so Claude can copy them into files it creates
- Claude Code on the web: requests from Bash and other tools to non-API anthropic.com hosts (e.g. www, docs) now go through the session's network proxy, so your environment's allowed domains apply
- Remote Control: clearer message and `claude doctor` wording when Remote Control isn't enabled for your account
- Windows: cross-session messaging is now available, so Claude Code sessions across your machines can message each other with `SendMessage` and find each other with `ListAgents`, as on macOS and Linux
- [VSCode] "View usage" in the usage-limit banner now sits inline with the warning text instead of floating mid-banner

## 2.1.238

- Added a `keybindingFlavor` setting: set it to `"readline"` to make Ctrl+W in the prompt delete back to the previous whitespace, as in Bash; the default (`"classic"`) is unchanged
- Plugin marketplaces: `headersHelper` on a url marketplace or a catalog entry runs a command that mints HTTP headers (e.g. a short-lived token) for catalog and same-origin archive fetches
- A catalog entry's `headersHelper` runs only when you install or update that plugin, after its command is shown; `claude plugin install/update` ask `[y/N]` (or pass `-y`)
- Added `claude self-hosted-runner --defer-shutdown-max-min <minutes>`: on SIGTERM, keep serving attached sessions, park what is left after that many minutes, then exit
- Added `claude self-hosted-runner --proxy-authorization-command` / `--proxy-authorization-file` for egress proxies that require a freshly issued `Proxy-Authorization` header on every connection
- Fixed unbounded memory growth in long interactive sessions: subagent tool results are now released once they leave the recent display window
- Fixed custom, project, and plugin output styles drifting back to the default voice mid-session
- Fixed `CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION=true` not keeping prompt suggestions on when your account is near, but not over, its usage limit
- Fixed worktree-isolation Bash refusals telling you to remove a redirect when the command had none
- Fixed self-hosted runners occasionally being removed by the server after a single slow or lost poll request, handing their healthy session to another runner
- Fixed MCP elicitation dialogs showing nothing for URLs longer than 4,096 characters, and permission prompts dropping the "don't ask again" option when the project path didn't fit the terminal width
- Fixed leftover `/tmp/claude-*-cwd` files when a Bash command is killed, times out, or is interrupted
- Fixed held Backspace being ignored on terminals that send Ctrl+H for Backspace when keystrokes arrive in large bursts (slow SSH/mosh links)
- Fixed text-wrapping in permission prompt diffs: lines containing wide multi-code-point characters (such as emoji) or tabs are no longer clipped
- Fixed killing a suspended (Ctrl+Z) session sometimes leaving the terminal in bracketed-paste mode with the cursor hidden
- Fixed stdio MCP servers receiving a `server/discover` request before `initialize`, forcing lazy servers to start their backend on every session open
- Fixed a proxy's refusal of a connection being reported as a generic network error instead of naming the proxy
- Fixed the `/model` and `/effort` cache-miss warning appearing when the prompt cache had already expired
- Fixed per-task Stop from the Remote Control tasks panel doing nothing on CLI-hosted sessions
- Fixed remote sessions exiting when a client delivered a user message without a valid role
- Fixed Remote Control sessions started by `claude remote-control` inheriting session-scoped environment variables from the launching shell
- Fixed a Remote Control session whose process crashed staying unavailable until `claude remote-control` was restarted; it can now be reused when you next message it
- Fixed Remote Control messages sent from the web or Desktop while Claude is mid-turn disappearing from the transcript after the turn finishes
- Fixed Remote Control model picks made on a phone or web not updating the model shown in the terminal
- Fixed Remote Control disconnecting with "login expired" when a brief network hiccup delays renewing your sign-in; it now retries and stays connected
- Fixed Remote Control reporting a failed reconnect on sign-out; signing out now ends the session with a clear message
- Fixed `ListAgents`/`SendMessage` reporting "Remote Control is not connected" in sessions run by `claude remote-control` (server mode) or Desktop/IDE hosts; they now list and reach Remote Control peers
- Fixed `ListAgents` and `SendMessage` exposing the idle worker that the agent view pre-warms for your next background session; it now appears only once a task claims it
- Cross-session messaging: sending to a session on this machine that refuses inbound messages (e.g. `crossSessionInbound: "refuse"`) now reports "refused" to the sender instead of a silent success
- Cross-session messaging: a session whose inbox drops your messages (rate limit or full queue) now tells your session, instead of the messages vanishing silently
- Improved startup: bare `claude` starts sooner on macOS
- Improved Bash tool permission checking for zsh-specific syntax in shell conditionals
- Improved Remote Control connection resilience: brief HTTP 403 refusals from a network edge, VPN, or proxy are now tolerated for up to 3 minutes, with the refusing party named when a block persists
- Improved startup responsiveness: the automatic update check now runs about 10 seconds after launch instead of competing with startup for CPU
- Updated the bundled `claude-api` skill for the Managed Agents Aug 19 release: web search/fetch domain settings and memory stores on self-hosted sandboxes
- Changed Ctrl+L and Cmd+K in fullscreen to always just repaint — the double-press `/clear` shortcut was removed, and 1-row nvim terminals no longer trigger automatic `/clear` loops
- Changed `claude mcp list` and `claude mcp get` to show disabled servers as `⊘ Disabled` instead of connecting to them for a health check
- MCP `headersHelper` in a project `.mcp.json`, and inline MCP servers in project or `--add-dir` agent files, now require that folder's trust dialog to have been accepted (also under `claude -p`)
- MCP `headersHelper` from a project `.mcp.json`, plugin, or agent file runs without inherited credential env vars; user, managed and claude.ai-scope helpers now run from the Claude config dir

## 2.1.237

- Fixed prompt caching for sessions using an LLM gateway or custom base URL
- Added a built-in "Concise" output style: Claude leads with results and skips preamble and narration, while doing the work just as thoroughly. Select it under Output style in /config.

## 2.1.236

- Added `ANTHROPIC_DEFAULT_MODEL` environment variable: sets the model new sessions start on, while a `/model` pick still overrides it and persists across restarts (unlike `ANTHROPIC_MODEL`)
- Added `notify_when_idle` to cross-session `SendMessage`: ask another Claude Code session on this machine to send one notice when it next goes idle — opt-in, one-shot, no polling (macOS and Linux)
- Sandbox: on macOS, wildcard read-deny rules (e.g. `**/.env`) now take precedence inside allowed read regions, cover matched directories' contents, and can't be bypassed by renaming the denied file
- Fixed clipboard copy, background housekeeping, background sessions, and local MCP logs breaking after the directory a session had switched into was removed (since 2.1.229)
- Fixed the fullscreen renderer failing permanently after a single failed start: it now falls back to the classic renderer instead of exiting on every subsequent launch
- Fixed the `/model` picker rendering taller than the terminal: it now shows only as many models as fit the window, with the rest reachable by scrolling
- Fixed `SendMessage` calls being rejected when a malformed closing tag left the message text inside the summary field
- Fixed unhandled promise rejections when a subprocess fails to start, for example `powershell.exe` on WSL with Windows interop disabled (regression in 2.1.234)
- Fixed fullscreen mode sometimes not showing a newly sent message until the next update after the terminal was resized
- Fixed a blank band that could remain above the prompt after clearing a multi-line prompt, and panes not repainting after resizing the terminal away and back, in fullscreen mode
- Fixed the managed-settings approval prompt sometimes not appearing at startup while still capturing the first keypress as approval
- Fixed terminal tab titles jumping in tmux (iTerm tmux integration): the title is now written only when its text changes instead of animating every 960ms
- Fixed an unclear error when the cloud environments list came back empty or malformed
- Fixed the Fable 5 first-time usage-credits prompt auto-selecting the fallback model after 60 seconds with no answer when using Remote Control
- Fixed spinner tips never appearing, with a repeated background error, when the cached guest-pass reward in `~/.claude.json` was malformed
- Fixed skills hot-reload in SDK/VS Code sessions raising an error on every skills change after the session's working directory was deleted (2.1.229+)
- Fixed self-hosted runner sessions released on idle, retire, or startup timeout occasionally resuming on another runner before the post-session hook had finished
- Fixed the Clawd mascot's eyes and feet rendering unevenly in iTerm2 at some font sizes
- Fixed occasional runaway session recaps: recap text (automatic and `/recap`) is now capped at 400 characters, cut at a word boundary
- Improved startup performance: the session counter is now written in the background
- Improved auto mode: `Monitor` allow rules are now set aside while auto mode is active, so Monitor commands are reviewed the same way Bash commands are
- Improved auto mode on Bedrock, Vertex AI, and Foundry, and when telemetry is disabled: the classifier now uses the same defaults as on the Claude API, including severity-scored classification
- Improved auto mode: the git status check can no longer be fooled by a repo's `status.showUntrackedFiles=no` setting into reporting a clean tree
- Changed the `/model` picker to highlight only the newest model's name, so the highlight marks the new release rather than an arbitrary subset of the list
- `/goal`: an idle session whose goal is parked behind long-running background work now checks in automatically after 30 minutes (then 1h, 2h) instead of waiting for you to return
- `/usage` now shows the usage-credits spend row for Team and Enterprise members, and shows a capped row at 0% before anything is spent
- SIGTERM in print/SDK mode no longer records an interrupted turn or synthetic tool denials before exiting; running commands are still terminated and the process still exits with code 143
- Pressing Enter on a slash-command typo or a command unavailable in this session now reports it instead of running the closest fuzzy match; prefixes and aliases still run
- Remote Control now marks a session offline within seconds when the CLI exits or its terminal closes
- `SendMessage` now refuses further messages to a session up front once a rapid burst would exceed what that session's inbox accepts, instead of reporting them sent while they were dropped
- Aligned the session title chip on the prompt border with the footer's right edge
- Right-aligned footer items (goal indicator, session state, background agent status) and truncated notices now share a consistent right margin with the rest of the prompt area
- [VSCode] Added screen reader support for the transcript: live announcements for replies, permission requests, errors, and status changes, plus per-turn heading navigation

## 2.1.235

- Added an optional `spellcheck` setting that underlines misspelled words in the prompt input as you type, using your installed `aspell`, `hunspell`, or `ispell`
- Fixed whole-prompt-cache invalidation when a language server disconnected or reconnected mid-session
- Fixed nested markdown list items misaligning at depth 3+ and added a hanging indent to wrapped list items in the terminal UI
- Fixed prompt input highlights (slash commands, keywords, mentions) appearing shifted by one or more characters in some multi-line prompts
- Fixed Shift+Tab inside the permission prompt's comment field approving the edit and granting session-wide edit permission instead of closing the field
- Fixed the Agent tool advertising a general-purpose default in sessions where that agent is unavailable: an omitted `subagent_type` there now gets a clear error listing the available agents
- Fixed notebook cell delete/replace approval dialogs silently omitting the existing cell content when the notebook or cell could not be read; the dialog now says why
- Fixed slash commands run while Claude is responding showing HTML entities instead of the actual characters
- Fixed the prompt footer not showing the "Update installed" restart notice after a background auto-update
- Fixed the expanded task list (`ctrl+t`) always starting collapsed when resuming or relaunching into a session that still has open tasks
- Improved memory and CPU usage while cloud sessions such as `/ultrareview` or `/autofix-pr` run in the background — their event streams are no longer re-scanned and re-rendered on every update
- Improved permission dialogs: display text and "don't ask again" options now always match what a grant would cover, and "don't ask again" is withheld when contents cannot be fully displayed
- Improved the embedded `grep` in native macOS/Linux builds: pathological patterns now fail fast instead of exhausting memory, and `-m N` with `-A/-C` prints correct context
- Improved the context-limit error to say when auto-compact is off and point to `/config` to re-enable it
- Vim mode: NORMAL mode and cursor position are now preserved when toggling the detailed transcript (ctrl+o) or closing a panel
- Dialogs: arrow keys and Enter pressed in quick succession now select the option you navigated to instead of the previously highlighted one
- `SendMessage` now refuses messages too large for cross-session delivery up front instead of silently dropping them
- Remote Control: `claude rc` now applies the same enterprise-gateway availability check as interactive startup
- [VSCode] Fixed focus jumping between open Claude tabs on its own when a window with several Claude panels is restored or reloaded

## 2.1.234

- Added the optional `CLAUDE_CODE_PROJECT_DIR_NAME` environment variable: hosts that give each session its own config directory can choose a short name for the per-project transcript directory
- Added the `selection:clear` keybinding action, so a key can be bound to clear an in-app text selection; also works in the agents view
- Added a GitLab merge request badge to the footer and statusline: repos with a GitLab remote and an authenticated glab CLI show MR !N with draft/pending/green states
- Claude Code now continues your session automatically when a claude.ai usage limit resets; turn it off in `/config` ("Continue automatically at usage limit")
- Claude is now told to use your account email only to identify you, and not to send it to unrelated services unless you ask
- Security: remote file reads, session restore, CLAUDE.md includes, workflow scripts and file uploads now reject Windows NT-namespace (`\??\`) paths, hardening the remaining pre-approval file accesses against the NTLM credential-leak vector
- Fixed auto mode in very long sessions repeatedly re-checking and denying sandboxed commands' network access after the conversation had been compacted
- Fixed session-scoped permission answers (including denies) being dropped when answering background subagent tool permission prompts
- Fixed a crash when an API response on the non-streaming fallback path (typically via third-party gateways) contained a thinking block missing its thinking field or a text block missing its text field
- Fixed markdown rendering becoming extremely slow for some messages containing unusual Unicode sequences
- Fixed `SendMessage` rejecting a recipient copied from `ListAgents` when the session name is at the 200-character cap or emoji-heavy
- Fixed repository detection mis-reading the host of git remotes with unusual userinfo, producing links and repo-specific behavior for the wrong host
- Fixed MCP diagnostics printing resolved secrets: scope-conflict warnings now show the configured `${VAR}` form, and connection-failure details show only the server origin
- Fixed `strictKnownMarketplaces` allowlists accepting SCP-style git marketplace sources whose host differs from the one git would actually connect to
- Fixed modal text such as the `/login` OAuth URL losing characters when copied in fullscreen
- Fixed a `---` horizontal rule in rendered markdown running into the line after it
- Fixed consecutive shell commands splitting into multiple "Ran 1 shell command" rows when todo/task updates were interleaved between them
- Fixed dialogs like `/permissions` opened while a `!` shell command was running being dismissed when the command finished
- Fixed a queued `!` shell command being sent to the model as plain text after pressing up-arrow to edit the queued input
- Fixed queued messages reappearing in the prompt history while still queued, Esc while selecting a queued message no longer interrupts the turn, and `!` mode no longer sticks after a mid-turn submit
- Fixed accepting the "Try the new fullscreen renderer?" prompt restarting the session without its permission mode (e.g. `--dangerously-skip-permissions`), tool allow/deny rules, model or effort flags
- Fixed `/tui` dropping launch `--allowed-tools`/`--disallowed-tools` rules when it restarts; it now declines to switch, with the reason, when the session has restrictions a restart can't carry over
- Fixed trust prompts omitting the repository-wide scope warning when the directory was first seen before the repository existed there
- Fixed a case where an IDE diff tab closing during a permission re-prompt could answer the new prompt with the previous input
- Fixed: files sent to the user during Remote Control sessions hosted by Claude Code Desktop or VS Code now upload, so they open on phone and web instead of showing an empty card
- Fixed: after `/login` while `CLAUDE_CODE_OAUTH_TOKEN` is set, the stale-token reminder no longer leaks into Claude's automatically resumed turn — it now appears only to you
- Fixed: permission previews now relay only to channel servers admitted by the inbound trust gate, and a server's explicit permission-capability opt-out is honored
- Fixed: credential masking on relayed permission previews can no longer hide commands, paths, or destinations from the approver; oversized private-key blocks now redact under full-strength redaction
- Fixed: provider API tokens that mask on permission previews now mask even when directly followed by shell delimiters
- Fixed Claude Desktop inter-session messages being silently dropped by the recipient session when cross-session messaging read as disabled, which left the sender's query "thinking" for many minutes
- Remote Control: signing this computer in to a different claude.ai account or organization now stops the running session within seconds and says why, instead of a misleading HTTP 404 hours later
- Remote Control sessions started from Claude Code Desktop or VS Code now keep phones and claude.ai/code updated on the session's permission mode (and claude.ai/code on the model) as they change
- Remote Control: effort picks made on a phone or on claude.ai/code now apply to terminal- and Desktop/VS Code-hosted sessions, and the session publishes its effort level to connected clients
- `SendMessage` and `ListAgents` now say when your account's session list was too long to check completely, instead of treating unseen sessions as absent
- Expired Anthropic profile credential now points you at `/login` when a claude.ai login would take precedence
- Improved the transcript: your own prompts now render markdown (highlighted code blocks, inline code, lists) the same way replies do
- Improved the "API returned an empty or malformed response" error to say what came back (content type, body kind, size, request ID) and why the original streaming request failed
- Improved auto-generated session titles to read as short, specific names (e.g. "Login button bug") rather than sentences restating your request (e.g. "Fix the login button on mobile")
- Reduced the context cost of loading the built-in `claude-api` skill from ~200k+ tokens to ~25k by loading reference docs on demand
- `/permissions` can now be opened while Claude is working — rule changes apply to the rest of the current turn
- `/add-dir <path>` can now be used while Claude is working; `/add-dir`, `/autocompact`, `/theme`, `/help`, `/config` and `/advisor` dialogs open mid-turn in the fullscreen TUI
- `/goal` now clears itself with a notice when a turn dies on an unrecoverable error (e.g. revoked auth, an exhausted credit balance, or a context overflow) instead of staying armed
- `/goal`: when background tasks keep a goal waiting for 30+ minutes, Claude now checks in on them instead of waiting indefinitely (set `CLAUDE_CODE_GOAL_CHECKIN_MINUTES=0` to opt out)
- `claude setup-token` now rejects unexpected extra arguments instead of silently ignoring them
- Changed Esc in fullscreen mode to no longer clear a mouse text selection: it interrupts or dismisses as usual and the selection stays highlighted
- Removed the redundant "Allowed by auto mode classifier" line that auto mode showed under every Agent tool call
- Removed the "Default teammate model" setting from `/config`; agent-team teammates now use the leader's model unless the spawn names one
- Dimmed the elapsed-time counter on the running tool header so it no longer competes with the bold counts
- Background task notifications delivered between turns are now sent to the model inside `<system-reminder>` tags, matching mid-turn delivery
- Mantle: skip the admin-pin availability probe at startup when a main-loop model is already picked
- Windows: startup no longer stalls on repeated rename retries when `~/.claude.json` is read-only

## 2.1.233

- Added GitLab merge request URL support to the `--worktree` flag and the `claude agents` view (where MRs display as `!N`)
- Added an opt-in `forward_user_identity` apps gateway setting on Anthropic upstreams that sends the signed-in user's identity as headers, so a proxy behind the gateway can attribute spend per user
- Added opt-in memory cgroup support for Bash tool commands on Linux (`CLAUDE_CODE_TOOL_MEMORY_LIMIT`) so a runaway build can't stall the session
- Added `CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS` environment variable to configure the WebFetch session URL cache TTL (default unchanged: 15 minutes)
- Fixed cloud sessions occasionally being marked as lost when the environment shut down while Claude was waiting on a permission prompt
- Fixed MCP v2 connections endlessly reopening the subscriptions/listen stream against servers that terminate long-held streams on a fixed timeout (e.g. serverless hosts)
- Fixed Notification hooks not firing for permission prompts when running under Claude Desktop or VS Code
- Fixed idle sessions on Linux sometimes keeping one CPU core at 100% when sandboxing is enabled
- Fixed bundled skill aliases like `/checkup` and `/review` reporting "Unknown command" in `-p` mode or with plugins/MCP loaded when a user or project skill shadows the bundled skill
- Fixed skill/command argument substitution to prevent argument values from being re-expanded as template markers
- Fixed Windows paths spelled with the NT `\??\` device prefix bypassing UNC path validation, closing an NTLM credential-leak vector
- Improved `claude self-hosted-runner` session start time: the session branch is now created without rewriting the working tree, and two server round trips no longer block the agent's launch
- Improved apps gateway error forwarding: 400/413 errors from Vertex, Foundry, and Claude Platform on AWS upstreams now carry the upstream's own message; fixes a bug with auto-compact on apps gateway
- Improved `claude plugin validate` to check a bare `.claude/skills` directory, reporting SKILL.md files whose frontmatter fails to parse
- Improved screen reader mode: the `/effort` selector renders as a numbered list with a typed-number prompt, and hint and dialog text is no longer clipped
- Improved print mode diagnostics: a `[claude-code:unrecognized_model]` line is written to stderr when a request goes out for a model ID Claude Code doesn't recognize; map it with `modelOverrides` to silence
- Changed the GitHub app setup tip to no longer appear in repositories whose origin remote is on gitlab.com or bitbucket.org; the enterprise marketplace tip now covers non-GitHub internal git hosts
- Todo/task-tracking tools (TaskCreate/Get/Update/List, TodoWrite) are no longer available on Opus 4.8, Sonnet 5, Fable 5, Mythos 5, and newer models; set `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` to bring them back
- Windows: fixed auto mode repeatedly stopping for manual approval on ordinary `cd <dir> && <command> > file` Bash commands (a 2.1.232 regression)
- Reverted the 2.1.232 Bash permission changes for Cygwin-style symlinks on Windows and for input redirections (`< file`); a narrower version will return in a later release

## 2.1.232

- Subagent forking is now on by default: a `subagent_type: "fork"` subagent inherits the full conversation and prompt cache, and non-teammate agent spawns in interactive sessions now run in the background by default
- Type `@` in the prompt to mention another Claude session by name; Claude then uses `SendMessage` to reach that session directly
- `SendMessage` now delivers to a bare name that exactly matches one live session, instead of asking to confirm with a ref first
- Interactive sessions on one machine now keep unique names: starting or renaming a session to a name another live session already uses gives it a `name-word-word` variant and tells you
- Added `/config` rows for "Dialog expiry" and "Messages from your other sessions" (cross-session inbound accept/hold/refuse)
- Added secret redaction for GitLab token families (`glrt-`, `gloas-`, `glptt-`, `glagent-`, `glimt-`, `glsoat-`, `glcbt-`, `glft-`, `glffct-`) and full redaction of routable `glpat-`/`gldt-` tokens; the `glab` CLI config store gets the same sandbox and credential-path protection as `gh`
- Added GitLab support to plugin marketplaces: bare `gitlab.com` repo URLs (including nested subgroups) now clone like `github.com` URLs, and clone auth-failure hints name your actual git host
- Settings: `additionalMarketplaces` and `allowedMarketplaces` are now accepted as friendlier aliases for `extraKnownMarketplaces` and `strictKnownMarketplaces`
- Enterprise policy: a url-typed `blockedMarketplaces` entry for a bare repo URL keeps blocking that URL when the CLI classifies it as a git clone
- Gateway: the `desktop:` overlay now accepts every released Desktop setting (was 11 hand-listed keys), validated at boot against Desktop's own schema; unknown or invalid keys fail boot
- Gateway: empty `managed.policies[].match.groups`/`admin.admin_groups` entries and malformed `email_domain` values (empty, or containing `@`, whitespace, or commas) now fail at boot instead of silently matching no one or granting admin access
- Fable 5 is offered as an advisor in `/advisor` again for organizations with Fable access, with usage-credits consent set up through `/model fable`
- Fixed a PowerShell permission bypass where variable-writing parameters could silently overwrite `$PSDefaultParameterValues` and redirect later commands' file access
- Fixed a Windows permission bypass where Git Bash followed Cygwin-style symlinks that path validation saw as regular files; writes through them now require permission approval
- Fixed nested git repositories inheriting trust from a parent directory; each repository now requires its own trust confirmation
- Fixed MCP connections hanging for the full 30-second connect timeout when a server fails to answer or sends a malformed reply to the protocol-version probe
- Fixed Remote Control sessions hosted by a bridge inside a cloud session inheriting that session's transcript or credentials
- Fixed Remote Control sessions started from Claude Desktop or an IDE appearing as a new claude.ai session each time the local session was resumed; they now reattach to the existing one
- Fixed Remote Control sessions appearing unreachable to newly attached clients while idle
- Fixed Remote Control bridge sessions not restoring conversation history when the session worker restarts
- Remote Control: resuming a conversation whose session was deleted from claude.ai or the app now starts a replacement instead of failing with a message about your login (regressed in v2.1.227)
- Fixed Cloud gateway `/login` exiting silently or leaving an unresponsive terminal after "Press Enter to continue" when managed settings failed to load; the reason is now shown
- Fixed voice mode on native builds getting stuck on "listening…" when the voice service rejected the connection; the rejection is now shown immediately
- Fixed mTLS client certificate rotation requiring a restart; Claude Code now reloads the rotated cert and key automatically on connection errors
- Fixed malformed AWS or Vertex region values being used to build request URLs; they now fall back to the default region
- Fixed stream idle timeout errors failing the request instead of recovering on Bedrock, Vertex, and gateway deployments
- Fixed content-sized overlays containing truncated text rendering one column too wide, and start-truncated text collapsing to an ellipsis
- Fixed a stray garbled character where a long shell-command or agent-description preview was cut off mid-emoji
- Fixed a startup race that could silently unregister a plugin marketplace due to concurrent writes to `known_marketplaces.json`
- Fixed `/update` and `/tui` refusing to restart while work that survives the relaunch was running
- Fixed usage-limit guidance suggesting unavailable slash commands in SDK and remote sessions
- Fixed the consent message for interactive `--advisor fable` launches, which told you to run `/model fable` in an interactive session that had just exited
- Improved fullscreen streaming: long sessions stay responsive because the whole conversation is no longer re-normalized on every update
- Improved the managed settings approval dialog: shows endpoint URLs, uses clearer wording for telemetry-only changes, skips routine OpenTelemetry options, and requires approval for server-managed sandbox binary overrides (`sandbox.bwrapPath`, `sandbox.socatPath`, `sandbox.ripgrep`)
- `/feedback` and `/bug` now open immediately when invoked while Claude is responding, instead of waiting for the turn to finish
- `/plugin install plugin@marketplace` now refreshes the marketplace first, so newly published plugins install without a manual marketplace update
- `/code-review` at high, xhigh, and max effort now runs in a background agent like the other levels
- Pasted and clipboard images are read without blocking the event loop
- Remote Control now keeps reconnecting for about 30 minutes after a network blip and no longer drops after a few blips spread across an hour
- Remote Control: resuming a conversation no longer silently takes Remote Control away from another Claude Code on the same machine that still has it; run `/remote-control` there to move it
- Updated agent panel: completed subagents hide immediately with a `/tasks` footer hint, and the "↓ N more" overflow indicator moved left for visibility
- Remote Control: the terminal now says whether a session was taken over by another device, ended from another app, or deleted, and stops suggesting a reconnect that would undo it
- Bash input redirections (`< file`) are now permission-checked like their argument spellings on all platforms
- Shortened the message shown when resuming a completed background agent
- Cowork sessions no longer inline external @-imports from user-scope memory files
- Hardened the auto-generated cross-session messaging socket directory on shared `/tmp`: a pre-planted symlink or another user's directory is now refused instead of used
- Hardened the Linux filesystem sandbox against a protected-path bypass
- Changed `sandbox.ripgrep` to be honored only from user, managed, and `--settings` settings; project settings can no longer override the sandbox's ripgrep binary
- Removed the startup tip suggesting you create custom subagents, and the matching nudge in the `/powerup` tour

## 2.1.231

- Fixed MCP OAuth sign-in failing with a redirect URI mismatch for servers that use a pre-registered OAuth client, such as Slack

## 2.1.229

- Documented `claude remote-control --continue` for resuming the most recent Remote Control session
- Added server-supplied Claude Code hook support for self-hosted runner sessions, matching managed-environment behavior
- Added SSE keepalive pings to gateway streaming responses during long thinking pauses, preventing idle-timeout disconnects on Vertex and Bedrock upstreams
- Added plugin marketplace `command` sources: a local command (e.g. an IDE) prints the plugin directory, which is re-resolved each session and applied without a restart; `mode: "link"` uses it in place
- `ListAgents` now marks disconnected Remote Control sessions as `offline` and labels your cloud sessions as `cloud`
- Fixed long responses partly disappearing while streaming and being printed twice in the terminal
- Fixed a crash to the error screen (including on `--resume` of the affected session) when a tool call had a non-string `glob`, `file_path`, or `command` value
- Fixed a RangeError crash when a progress bar or markdown table rendered in a very narrow terminal window (could also crash `claude --continue`/`--resume` at startup)
- Fixed a crash on Windows when a tool call or message referenced a file by an extended-length (`\\?\`) or UNC path
- Fixed auto mode failing on every tool call for users who disable the attribution header via `CLAUDE_CODE_ATTRIBUTION_HEADER` (direct Anthropic API connections)
- Fixed `/model` rejecting Sonnet/Opus 1M for claude.ai subscribers using a custom `ANTHROPIC_BASE_URL` gateway
- Fixed MCP OAuth with strict authorization servers by using `127.0.0.1` instead of `localhost` in the redirect URI
- Fixed Remote Control clients showing a stuck working spinner after a slash command typed in the laptop terminal
- Fixed the Claude Code Review workflow generated by `/install-github-app` completing without posting its review on the pull request
- Fixed multi-second UI stalls after editing a file with thousands of IDE diagnostics while the IDE extension is connected
- Fixed one-shot `claude plugin` commands leaving a stray liveness file that could prevent cleanup of outdated plugin versions
- Fixed dynamic workflows inside CPU-limited containers using the host machine's core count instead of the container's CPU limit
- Fixed a file-watcher handle leak after atomic file replacements, and an uncaught error on Windows when the scheduled-tasks watcher failed on a network or virtual filesystem
- Fixed SDK and `--input-format stream-json` sessions getting a 400 API error when a whitespace-only message was submitted
- Fixed conversations whose messages alone exceed the API's 32 MB request limit retrying compaction when no images or documents can be stripped; they now fail once with a clear message
- Fixed OpenTelemetry export from Claude Desktop sessions being rejected by the Desktop-managed gateway when that gateway is also the telemetry endpoint
- Fixed self-hosted runner and other remote sessions exiting at startup when `managed-mcp.json` is deployed and the server delivers MCP servers; those servers are now skipped with a warning
- Fixed self-hosted runner repository preparation hanging on a Git Credential Manager prompt; git now fails fast when credentials are missing
- Improved workflow fan-outs to stagger same-prefix sibling agents so subsequent agents read the cached prompt prefix instead of re-paying it (`CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS=0` disables)
- Improved "prompt is too long" errors to explain why automatic compaction could not recover instead of only suggesting `/compact`
- Improved sandbox: IPv6 literals in network domain lists are now bracketed (`[::1]:443`), and ambiguous spellings are enforced fail-closed and flagged by `/doctor`
- Updated `/login` to repeat the `CLAUDE_CODE_OAUTH_TOKEN` override warning after a successful login
- Changed `/commit-push-pr` so git/gh commands with dangerous flags (`--force`, `--amend`, `--no-verify`, etc.) are no longer auto-approved
- Changed self-hosted runner Windows startup to require an explicit `--base-dir`; there is no default checkout directory on Windows
- [VSCode] "Report a problem" and `/bug` now open the built-in feedback dialog instead of a retired survey link
- [VSCode] Made the `/btw` side-question panel resizable by dragging its boundary, in both side-docked and stacked layouts
- [VSCode] Added session groups in the sidebar — right-click to create, rename, or delete; Cmd/Ctrl- or Shift-click to move several sessions at once

## 2.1.228

- Fixed interactive sessions that could stop redrawing entirely, while the process kept running, after a rare internal layout error
- Fixed `git` / Git Bash not being found on Windows when Claude Code is launched from a parent folder of the git installation
- Fixed `/tui` reverting the session to an earlier model when `/model` had been changed since the last response
- Fixed cross-session messaging sometimes starting without an inbox in the first session after install or upgrade
- Fixed Remote Control `/resume` while connected leaking the resumed conversation's title or history into the connected session
- Fixed `claude self-hosted-runner` sessions failing on every fresh runner when the `checkout` hook fails for a repository the session doesn't push to; that repository is now skipped with a warning
- Fixed self-hosted runners ending sessions in the gap between a background task finishing and the follow-up turn starting
- Fixed session cleanup deleting contents inside a project's memory folder
- Fixed background plugin-cache cleanup deleting a plugin's cache when its only version is a symlinked development checkout
- Fixed a settings-merge issue where a marketplace entry redefined in a higher-precedence settings tier could inherit another tier's custom headers; marketplace entries now merge as whole entries
- Fixed the deferred-tools reminder occasionally being sent to the model twice after a skill invocation
- Hardened skills synced from claude.ai: they no longer shadow local commands or MCP prompts, their descriptions are sanitized and labeled, and on your machine their bodies don't run `!` commands or expand `@` files
- Improved cross-session messages: the sender and body now display inline instead of a collapsed line, and messages to Remote Control sessions on other machines show your Remote Control session name as the sender
- Improved Vertex AI credential handling: expired or missing Google Cloud credentials now fail within seconds instead of retrying for minutes
- Improved compaction progress: the retry countdown and stall hint now appear during compaction instead of only a progress bar
- Updated terminal title busy-spinner glyphs to reduce tab-bar jitter on some terminals
- Changed the Write tool so newer models can overwrite an existing file they haven't read this session, matching the Edit tool's rules; older models still require the read first
- Removed the outdated note about auto mode sessions costing slightly more from the first-use notice for Pro, Max, and Team plans

## 2.1.227

- Fixed feature flags being evaluated without the user's subscription tier when a session started with an expired login token, which could wrongly prompt Max plan users to enable usage credits for Fable
- Fixed every Bash command failing under `claude-code-action` with `allowed_non_write_users` on GitHub-hosted runners
- Fixed `/tui` bringing back a conversation that had been rewound to before its first message
- Improved slash-command menu: blue now marks only the selected row, matched characters are bolded instead of recolored, and emoji or accented names keep their glyphs
- Improved performance: fewer event-loop stalls on file-not-found suggestions and at-mention size checks

## 2.1.226

- Bug fixes and reliability improvements

## 2.1.225

- Added gateway spend-limit support to Claude Code's usage warning; the limit-reached message now names the cap, its reset time, and the operator's message (requires the gateway on 2.1.225)
- Added a workspace trust prompt to `claude agents` for untrusted directories, matching the behavior of `claude`
- Fixed a transient 401 replacing a long-lived `CLAUDE_CODE_OAUTH_TOKEN` with a stored login's short-lived token, breaking headless sessions until restart
- Fixed MCP OAuth servers on macOS intermittently failing with a burst of 401 errors, as if never authenticated, after a keychain read timed out
- Fixed auto mode counting a safety-filter refusal of its own permission check toward the consecutive-block limit; the action is still denied, but the model is now told to move on rather than retry
- Fixed cross-session messages staying parked without a notice or expiry in headless sessions and during startup
- Fixed conversation history breaking on Remote Control session resume after very large conversations were compacted
- Fixed hovering over a session in another project in the agents list changing the directory the next agent starts in
- Fixed `claude self-hosted-runner` registering and then failing every session when `--base-dir` cannot be created or written; it now exits at startup with a clear error
- Fixed Claude Code on the web sessions being misreported as stuck, re-sending a growing event backlog on every reconnect
- Improved Remote Control: photos attached from the Claude app are now shown to Claude directly instead of being read from disk with a separate tool call
- [VSCode] Fixed Focus view folding away the latest to-do list, a pending question's context, and settled answers; thinking-only folds show "Thought for Ns" and re-collapse when their turn completes
- SendMessage can now start a conversation with your Remote Control sessions on other machines by name (`ListAgents` shows them as `name [ref]`), instead of only replying after they message you first
- SendMessage: a Remote Control recipient you already confirmed is never swapped for a same-named session on this machine when its own list couldn't be checked

## 2.1.224

- Added self-hosted environments: `claude self-hosted-runner` turns your own machines or containers into a place Claude Code web, mobile, and desktop sessions can run, on Team and Enterprise plans
- Added `archive` plugin source: install plugins from a zip over HTTPS without git or npm, with optional SHA-256 pinning
- Added a cancel-and-confirm step when removing an unavailable paste changes a command's text
- Added `ANTHROPIC_BEDROCK_REGION_PREFIX` env var for Bedrock to prefer a specific cross-region inference profile over the `AWS_REGION`-derived one
- Added `crossSessionInbound` and `dialogExpiry` settings: cross-session messages sent to a session running with bypassed permissions are held for your approval, and messages to other sessions auto-deliver
- Added sandbox credential-masking options: `extract` and `onExtractNoMatch` for structured env values, `decode: "jwt"` with `maskClaims` for JWT-aware masking, and `awsPairs`/`sigv4` for AWS SigV4 re-signing; these need `network.tlsTerminate` and are honored only from user, managed, or `--settings` settings
- Added cross-session `SendMessage`: Claude Code sessions can now message each other, on any of your machines, with `ListAgents` to discover them (macOS and Linux)
- Fixed long (>200 char) project paths resolving to another project's session directory under a shared sanitized prefix; session list, rename, fork, delete and `/resume` no longer cross projects
- Fixed `SendMessage` reporting "Message sent" when the write to a teammate's inbox had actually failed; failed deliveries are now reported as errors
- Fixed sandbox filesystem deny entries written with a trailing slash (e.g. `denyRead: "~/.aws/"`) being silently bypassable on Linux and macOS
- Fixed sandbox violation details never appearing in Bash tool results; Claude now sees which file or network access was denied and why
- Fixed MCP tools that connect mid-turn being deferred for tool search without their names announced to the model
- Fixed plugin install records being silently corrupted when the same plugin is installed in multiple projects
- Fixed recalled or restored paste content occasionally attaching wrong data or silently losing text when the paste had aged out or placeholder numbers collided
- Fixed copy-on-select on Wayland sometimes not reaching the clipboard; the two selection writes no longer race
- Fixed the feedback survey's transcript share silently failing on long sessions; a failed share now shows an error instead of a success message
- Fixed Remote Control auto-start intermittently failing with "Remote credentials fetch failed" on a cold start with a stale login token
- Fixed Remote Control and SDK clients showing a blank "(no content)" message after `/clear` and other output-less commands
- Fixed a Remote Control session recreated after its server session expired uploading prior local conversation history into the new session
- Improved fullscreen mode to keep the full pre-compaction history in scrollback across repeated compactions, instead of only the most recent interval
- Improved Remote Control: attached web and mobile clients now see compaction progress and the post-compaction boundary instead of a silent pause; `/clear` resets now propagate to attached clients
- Improved Remote Control: connection failures now show a persistent failure indicator with details and a reconnect shortcut, instead of only an 8-second toast
- Removed the 200-subagent-per-session spawn cap; long-running sessions no longer refuse new agents (concurrency and depth limits still apply)
- Changed managed settings: the approval prompt no longer re-appears after re-login or org switching when the organization's settings are unchanged
- Changed the feedback-survey transcript share: with your consent it now also uploads the last request's model settings — the system prompt (which includes your `CLAUDE.md` instructions), tool definitions, and model parameters. Secrets are redacted as before, and these fields are dropped first if the share is too large
- Changed the Bash tool description to always note that command output is displayed to the model, not reliably to the user
- Changed recalled paste placeholder numbers to renumber when accepted into the input
- Changed Remote Control to archive the stale server session instead of leaving a dead one listed when a fresh session is minted after compaction or `/resume`
- [VSCode] Fixed the extension showing Remote Control as connected after the connection failed
- Fixed a session resume silently reconnecting Remote Control after the user turned it off (`--resume`, SDK hosts, and the VS Code extension)
- [VSCode] Fixed sessions not honoring `remoteControlAtStartup` when explicitly enabled

## 2.1.223

- Added owner wildcard entries (`"owner/*"`) to the `strictKnownMarketplaces` and `blockedMarketplaces` managed settings for allowing or blocking all marketplace repos under a GitHub org
- Added a warning when workflow agents, forked skills, slash commands, or resumed background agents' requested subagent model is restricted and the parent model runs instead
- Added a `/teleport` hint in cloud sessions showing how to continue locally with `claude --teleport <session id>`
- Fixed a Bash permission bypass where a crafted command could hide parts of itself from permission checks
- Fixed permission prompts so commands padded with tabs or invisible Unicode can no longer hide part of the command from the approval dialog
- Fixed workflow scripts being able to use dynamic `import()` to run code outside the workflow sandbox
- Fixed a permission gap where an agent definition's `bypassPermissions` mode ignored the org bypass-permissions disable policy
- Fixed resuming a session after a mid-session `/cd` coming back empty
- Fixed gateway model discovery hiding Claude models registered under provider-prefixed IDs such as `vertex_ai/claude-*` or `bedrock/anthropic.claude-*`
- Fixed `modelOverrides` keys that aren't Anthropic model IDs being treated as the session's canonical model ID; unknown keys are now ignored as documented
- Fixed managed settings: server-delivered settings no longer disable the env block of a machine-local `managed-settings.json` or MDM profile; admin env now merges per key
- Fixed sandboxed commands failing to start on Linux when `sandbox.filesystem.denyWrite` covers the working directory
- Fixed forked background agents getting stuck "already resuming" for the rest of the session when rebuilding the fork's parent prompt failed during resume
- Fixed a resumed session failing every turn, or leaving the interactive app on an unresponsive error screen, when its history held a malformed diagnostics attachment
- Fixed a rare hang when parsing unusual `git push` output
- Changed `CLAUDE_CODE_DISABLE_1M_CONTEXT` to hold every Claude model with a native 1M window to 200K via auto-compaction, not just a fixed list; a startup warning now appears when auto-compaction isn't holding the session to 200K
- Changed auto-compact to keep sessions on unrecognized model IDs within the assumed context window instead of letting them grow past it; set `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1` to restore the previous behavior
- Changed `/review` to be an alias of `/code-review`, which reviews the current diff or a PR (`/code-review <level> <pr#>`); use `/code-review ultra` for a deep cloud review
- Changed `/code-review` with no effort level to reuse the level you typed last; type a level like `/code-review high` to change it

## 2.1.222

- Fixed worktree-isolated sessions and their subagents being able to run destructive git commands against the main checkout; isolation now applies to file edits and Bash in every session type
- Fixed PreToolUse auto-allow hooks bypassing tool restrictions in background agent tasks (summaries, compaction, renames)
- Fixed `/usage-credits` on Team and Enterprise showing "you've already sent a usage credit request" for members whose earlier request was dismissed, blocking them from sending a new one
- Fixed the startup connectivity check hanging and then failing behind an HTTPS proxy; it now uses the same proxy-aware transport as API requests and times out with a clear message
- Fixed "Connection closed mid-response" errors being reported on responses that had actually completed
- Fixed `/usage` overattributing usage to MCP servers: a server's share now reflects only the requests that actually consumed its tool results, instead of every turn after any call to it
- Fixed sessions not linking to pull requests created after the branch was pushed, including through the GitHub REST API
- Fixed org-restricted `model: opus`-style subagent and teammate family aliases dropping to the parent model instead of stepping down to the newest org-allowed model in the family
- Fixed stream idle timeout firing on custom `ANTHROPIC_BASE_URL` gateways despite server keep-alive pings arriving on the wire
- Fixed claude.ai connectors being falsely marked as needing authorization when the session token is invalid — they now show a `/login` hint instead
- Fixed tool errors not being displayed for tools no longer available locally, for example after an MCP server is removed
- Fixed `SendMessage` rejecting a long summary — it now truncates instead, so sends no longer fail on a character limit
- Fixed the spinner's effort label in a subagent's transcript view showing the session's effort level instead of the subagent's own `effort:` setting
- Fixed rare crashes when a file watcher hit a filesystem error or during file-watcher teardown
- Fixed screen readers re-reading the whole input line on every backspace in `--ax-screen-reader` mode — end-of-line deletions now echo just the deleted characters
- Fixed host model-selection keys not taking precedence over a stale on-disk `managed-settings.json` when `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` is set
- Improved auto mode safety: messages sent to other agent sessions via `SendMessage` are now evaluated by the permission classifier before dispatch
- Improved the refusal when Claude tries to invoke a skill with `disable-model-invocation`: Claude is now told to ask you to run the skill instead of replicating its workflow
- Improved the `/diff` view, the Remote Control workspace diff, and file-edit diffs in Claude Code on the web sessions to use raw git blob content, ignoring workspace-configured diff drivers and textconv
- Changed Remote Control auto-start so repo-local settings (`.claude/settings.json` or `.claude/settings.local.json`) can no longer turn it on (they can still turn it off); enable it at user scope via `/config`
- Removed ultraplan feature

## 2.1.221

- [VSCode] Added Focus view: a chat-menu toggle that hides tool activity behind an expandable per-turn summary with a live running-tool indicator, toggled with `Ctrl+Alt+F` or the "Claude Code: Toggle Focus view" command
- Added `mode: "mask"` for sandbox credential files on Linux and WSL — sandboxed commands read a sentinel copy (the whole file, or just the spans captured by an `extract` regex) while the sandbox proxy substitutes the real value on egress; on macOS file masking falls back to `deny`
- Added warnings to `claude plugin validate` when a marketplace or plugin name would be rejected by Claude Desktop's managed marketplace sync
- Added a `prompt-audit` subcommand to the `claude-api` skill for auditing prompts and tool descriptions for patterns written for older models
- Fixed a Bash tool permission-check bypass where zsh could execute hidden commands in `[[ ]]` regex conditionals; affected commands now prompt for permission
- Fixed PowerShell permission checks mishandling paths containing quote characters on Windows; such paths now prompt for approval
- Fixed the thinking toggle having no effect for the rest of a session that started with thinking off; disabling an MCP server mid-connect no longer silently reverts
- Fixed MCP servers from `--mcp-config` not being connected before the first turn in print mode (`-p`), which made the model emit tool calls as literal text
- Fixed @-mentioned files being silently dropped when pressing Esc to retract a prompt and resubmitting it
- Fixed a crash when preparing API requests for SDK MCP tools named after built-in object properties such as `constructor`
- Fixed WebSearch failing with a 400 error at effort `xhigh`/`max` when thinking is disabled
- Fixed sandboxed large uploads failing with TLS errors through the sandbox proxy
- Fixed Team and Enterprise spend-limit message incorrectly blaming the org's monthly limit instead of your individual spend limit
- Fixed Bedrock authentication with AWS SSO named profiles failing in desktop-managed sessions on Windows machines that set a stray `HOME` environment variable
- Fixed `CLAUDE_CODE_RESUME_INTERRUPTED_TURN=0` not disabling interrupted-turn auto-resume; falsy values are now honored
- Fixed a rare wake-from-sleep race where two Claude Code processes could both refresh the same MCP connector or WIF OAuth token at once, forcing re-authentication
- Fixed renaming a session from Claude Code Desktop or claude.ai not updating the CLI's session name; session names from every rename surface are now sanitized
- Fixed plugin- and org-delivered skills named after terminal-only built-ins (e.g. `/help`, `/feedback`) being un-invocable in non-interactive sessions
- Fixed the "Plugins changed" notification lingering after plugins were reloaded instead of clearing
- Fixed Vim mode: the yank register now survives dialogs, history search, and the transcript view instead of being silently emptied
- Fixed Vim mode: undoing back to an empty prompt now arms the "press ← again" confirm before returning to the agent view
- Improved tool search on Google Vertex AI: re-enabled for Claude 4.5-generation and newer models
- Improved auto mode: permission checks for parallel tool calls are now cache-efficient, and switching modes while a check is pending reliably prompts instead of applying the stale result
- Reduced prompt-cache costs for auto-mode permission checks by reusing the cached conversation prefix across decisions
- Improved Stats panel to count cache tokens in its token totals, with a breakdown by input, output, cache read, and cache write
- Improved `/ultrareview` error messages when a repo shares no history with its base: a checkout with no branches is now refused up front with advice to create one, and refusal hints no longer suggest `git fetch --unshallow` on clones that are already complete
- Improved Windows startup: process creation times are now read via a native kernel32 call instead of spawning PowerShell, so endpoint security tools that gate `powershell.exe` no longer prompt
- Changed background sessions to commit and push to preserve work, open a draft PR only when the task calls for one, follow your CLAUDE.md git instructions, and always end by reporting where the work lives
- Changed `/plugin install` to refresh a stale marketplace catalog and retry before reporting a plugin not found
- Changed plugins installed from `/plugin` to activate immediately when safe, instead of always requiring `/reload-plugins`
- Changed plugins to accept `"."` as a `skills` path, and the root-level `SKILL.md` validation error now suggests using the plugin root
- Changed `/status` to show the session kind: `interactive`, or a background job that is `attached` or `unattended`
- Changed emoji autocomplete to accept common alternate shortcodes like `:thumbsup:`, `:thumbsdown:`, and `:love:`
- Changed sessions forked with `/fork` to create a new worktree of their own instead of working in the original session's checkout
- Changed Claude in Chrome to close the browser tabs it opens once it no longer needs them
- Changed fast mode to report on the stream when usage credits run out mid-session, instead of failing silently
- Changed Monitor: a watch that exits without producing any output now says so instead of reporting "stream ended"
- Changed the Gateway `model` field validation: non-string values are rejected with a 400 instead of being forwarded
- Removed the repeated "Permission mode changed while the auto-mode classifier call was queued" notice from approval prompts

## 2.1.220

- Bug fixes and reliability improvements

## 2.1.219

- Added Claude Opus 5 (`claude-opus-5`), now the default Opus model — 1M context, fast mode at $10/$50 per Mtok
- Added `sandbox.network.strictAllowlist` setting to deny non-allowlisted hosts for sandboxed commands without prompting
- Added `DirectoryAdded` hook that fires after `/add-dir` or the SDK `register_repo_root` control request registers a new working directory mid-session
- Added `mcp_server_errors` to the headless stream-json init event, listing `--mcp-config` entries skipped by config validation; terminal runs print a startup warning
- Added the `workflowSizeGuideline` settings key so the advisory Dynamic workflow size guideline can be set from any settings file; the `/config` row is hidden while one does
- Added nested subagent forwarding in stream-json: subagents spawned at depth-2+ now appear when `--forward-subagent-text` is set, keyed by their spawning Agent `tool_use` id
- Fixed `claude -p` text output dropping the answer already produced when a turn dies on a mid-stream API error
- Added HTTP status and error text to `claude mcp list` and `/mcp` when a server fails to connect, and a warning for MCP config values with hidden leading or trailing whitespace
- Fixed the Fable model row showing "Requires usage credits" for plans that include it, when a stale cache had baked the label in
- Fixed the `/model` picker showing the merged Opus row as plain "Opus" instead of "Opus (1M context)"
- Fixed copy-on-select inside GNU screen printing base64 into the terminal instead of copying the selection
- Fixed Remote Control clients keeping a stale fast-mode status after a model switch, reconnect, or failed org check
- Fixed `CLAUDE_CODE_GIT_BASH_PATH` on Windows exiting or being used as bash when the path isn't a bash/sh binary; it's now ignored with a warning
- Fixed Vim mode: pressing ← on an empty prompt now returns to the agent view from NORMAL mode, not just INSERT
- Fixed screen-reader mode rewriting the entire input line on every keystroke instead of echoing only the typed character
- Improved the "Remote Control is only available via api.anthropic.com" error to name the specific setting that caused it
- Improved `claude --teleport` to show which repo your current checkout points at when it doesn't match the session's repo
- Changed dynamic workflows to default to a medium size guideline (aim for fewer than 15 agents); pick another size or unrestricted with Dynamic workflow size in `/config`
- Changed managed MCP allowlist/denylist `${VAR}` entries to resolve from the startup environment and managed-settings env instead of settings-file env
- Changed the `/model` picker to highlight only the newest model's name, so the highlight marks the new release rather than an arbitrary subset of the list
- Added the current default workflow size to the running-workflow status line, with a pointer to `/config` for changing it
- Removed Opus 4.7 from fast mode; `/fast` now applies to Opus 5 and Opus 4.8
- Updated the claude-api skill to default to Claude Opus 5, with a migration path from Opus 4.8
- Subagents can now spawn nested subagents up to depth 3 by default (was 1); set CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1 to disable nesting

## 2.1.218

- Changed `/code-review` to run as a background subagent, so review work no longer fills your conversation and keeps stacked slash commands as its review target
- Added screen-reader announcements of deleted text for word and line deletions (`Option+Delete`, `Ctrl+W`, `Cmd+Backspace`, `Ctrl+U`, `Ctrl+K`) in `--ax-screen-reader` mode
- Fixed Windows paths with `\u`-prefixed segments (like `C:\Users\unicorn`) being corrupted into CJK characters in tool inputs, which made those files inaccessible
- Fixed the left arrow key discarding the conversation with no undo: presses right after editing now ask to confirm, and Esc in the agent view returns to the conversation it backgrounded
- Fixed multi-line paste collapsing into one line with `j` in place of newlines in terminals that encode pasted newlines as Ctrl+J
- Fixed `/context` reporting stale pre-compact token usage after compacting from the message picker
- Fixed `/ultrareview` failing on descriptive arguments like "review my auth changes" — they now run a review of your current branch with the text applied as a note to the findings
- Fixed `/code-review ultra` silently running a local review in non-interactive sessions — it now launches the cloud review
- Fixed gateway spend metering to price Bedrock application-inference-profile ARNs and other config-mapped upstream model IDs at the configured model's rates
- Fixed mojibake when a long IDE selection was truncated mid-emoji, and a case where a tool executor error could be silently dropped
- Fixed an engine teardown race that could start and abandon a phantom turn, and made input pushed after close consistently rejected
- Fixed spurious "[Request interrupted by user]" messages after interrupted tool calls, and an unpaired `tool_use` block left in the transcript when a tool aborted mid-response
- Fixed VoiceOver reading "new line" instead of echoing the typed space at the end of the input in `--ax-screen-reader` mode
- Fixed plugin and settings panels not moving the terminal cursor to the focused row, so screen readers and magnifiers can follow arrow-key navigation
- Fixed crashes (maximum call stack exceeded) when a deeply nested watched directory tree was deleted or moved, and when rendering deeply nested UI trees
- Fixed pull request events occasionally being lost when a session exited immediately after creating or linking a PR
- Fixed the Bedrock setup wizard failing profile verification for assume-role profiles in partitioned AWS regions and on proxy-only networks
- Fixed rare negative or incorrect turn duration measurements after a system clock adjustment by timing turns with a monotonic clock
- Fixed the "N MCP servers need authentication" startup notice over-counting claude.ai connectors that aren't connected in claude.ai
- Fixed prompt history entries being dropped or duplicated when history writes raced or failed
- Fixed a retry loop that re-sent identical doomed requests after a context-overflow error with a large thinking budget; `Ctrl+B` backgrounding now applies the same background-shell caps as other paths
- Fixed agent frontmatter hooks running from untrusted folders: hooks now require the agent file's own folder to have accepted workspace trust
- Fixed fork-session lineage being lost after compaction in headless and SDK sessions
- Fixed a resumed session failing every turn, or crashing on resume, when its history held a malformed delta attachment
- Improved `/ultrareview` error feedback so Claude can correct an invalid argument instead of retrying it unchanged
- Improved auto mode: the dangerous-rm, background-`&`, and suspicious-Windows-path checks no longer open permission dialogs; the auto-mode classifier adjudicates them instead
- Improved sandbox command restrictions for IDE interactions
- Improved trust dialogs to name the repository root the grant covers
- Changed `/deep-research` to start only when invoked manually; Claude no longer launches it on its own
- Changed plan mode with auto to no longer prompt for Bash commands the static analyzer can't prove read-only; the auto-mode classifier judges them instead
- Added an announcement when fast mode changes as a result of switching models via `/config model=<x>` or Remote Control
- Changed server-managed settings so benign feature and cost toggles no longer trigger the settings-approval prompt
- Changed agent markdown files to reject agent names containing `:`, which is reserved for plugin namespacing
- Changed skills with `context: fork` to run in the background by default; opt out per skill with `background: false`
- Added `yes`/`no`/`on`/`off`/`1`/`0` (case-insensitive) as accepted values for skill and plugin frontmatter booleans, alongside `true`/`false`
- Fixed remote sessions continuing to send heartbeats after their worker was replaced, which left long-lived desktop and IDE processes retrying a rejected request every few seconds forever

## 2.1.217

- Added emoji shortcode autocomplete in the prompt input: type `:heart:` to insert ❤️, or `:hea` for suggestions — disable with the `emojiCompletionEnabled` setting
- Added warnings when transcript writes are failing (e.g. disk full) or when session saving is off due to an inherited environment variable, instead of losing transcripts silently
- Fixed a memory leak where truncated MCP tool outputs kept the full untruncated result in memory for the rest of the session
- Fixed Windows auto-update failures that could leave `claude.exe` missing; failed updates now restore the preserved executable automatically
- Fixed background session isolation not canonicalizing symlinked working directories, which could let sessions escape their workspace folder
- Fixed auto-compact never triggering for Claude Opus 4.8 on Bedrock and `/compact` failing once over the limit
- Fixed corporate mTLS, TLS-verify, OAuth scope, and proxy settings being ignored in Claude Desktop sessions
- Fixed screen reader mode's startup announcement being cut off by the first prompt render, and the thinking status row re-rendering every few seconds to update elapsed time and token counts
- Fixed managed settings that set `OTEL_EXPORTER_OTLP_ENDPOINT` not governing all signals — lower-scope signal-specific overrides no longer redirect telemetry away from the managed endpoint
- Fixed `--resume`/`--continue` and `/resume` failing with a TypeError when a transcript has a malformed attachment entry
- Fixed Remote Control sessions not showing a pending permission prompt or dialog to viewers that connected after it appeared
- Fixed background shells sometimes becoming impossible to stop after a session is sent to the background (`/background` or `←`) or when the session exits on a heavily loaded machine, most visible on Windows
- Fixed a `CLAUDE.md` or `SKILL.md` paths frontmatter value with many brace groups OOM-killing or stalling the CLI at startup — brace expansion is now budget-bounded
- Fixed the transcript preview sitting flush against the input area when attaching to a starting background session; it now leaves the same one-line gap as the live layout, so the transcript no longer shifts when the session takes over
- Improved footer PR badge links to be clickable hyperlinks even when terminal support can't be detected (e.g. over ssh/tmux); set `FORCE_HYPERLINK=0` to opt out
- Changed the login-expiry warning to appear 3 days before expiry instead of 5
- Capped the frontend-design plugin suggestion tip at 3 lifetime impressions instead of repeating indefinitely
- Added a cap on concurrently-running subagents (default 20, override with `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) so one message can't fan out unbounded background agents
- Changed subagents to no longer spawn nested subagents by default; set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to allow deeper nesting
- Fixed `--max-budget-usd` not stopping background subagents: once the cap is reached, new spawns are denied and running background agents are halted

## 2.1.216

- Added `sandbox.filesystem.disabled` setting to skip filesystem isolation while keeping network egress control
- Fixed a slowdown in long sessions where message normalization cost grew quadratically with the number of turns, causing multi-second stalls and slow resumes
- Fixed auto mode denying commands with "HTTP 401" classifier errors after the OAuth token expired or rotated mid-session
- Fixed AskUserQuestion telling Claude to continue even when your answer asked it to wait or explain first — free-text answers now get neutral wording
- Fixed Claude Code on the web re-asking the same question and dropping your answer after the session sat idle for a few minutes
- Fixed @-mentions silently attaching nothing after file-modifying hooks, vim dot-repeat of `c`-operators and paste, statusline running twice on resume, and resume-picker hangs on failure
- Fixed resumed background agent sessions reverting to the default agent: the agent's prompt and tool restrictions are now restored
- Fixed worktree-isolated subagents redirecting git into the shared checkout via `git -C`, `--git-dir`, or `GIT_DIR`/`GIT_WORK_TREE`
- Fixed worktree sessions landing in another project's leftover worktree when the working directory did not match the selected project
- Fixed background sessions whose worktree has no git repository being undeletable
- Fixed `claude daemon stop --any` potentially terminating an unrelated process via a stale legacy daemon lockfile
- Fixed Esc-Esc at an idle prompt not opening the rewind picker in long-running sessions with background tasks
- Fixed Bash command permission checking for compound statements with redirects inside `&&` lists or negations
- Fixed pressing Ctrl+X twice in the agent list failing to delete a session, and deleted sessions reappearing when their background worker had died
- Fixed background subagents getting cancelled when a high-priority message arrives during their startup window
- Fixed mouse and focus garbage in the terminal while a GUI editor from `/memory`, `/plan`, `/keybindings`, or Ctrl+G is open; `/memory` no longer waits for the editor to close
- Fixed Claude-in-Chrome 403-looping on reconnect when the session's OAuth token lacks a required scope
- Fixed workflow saves and scheduled-task writes following a symlink at `.claude`, which could redirect writes outside the project
- Fixed MCP re-authenticate revoking working credentials before the new sign-in succeeds, and the reconnect needs-auth message in background sessions pointing at an unusable command
- Fixed read-only commands on Windows accessing network paths without a permission prompt
- Fixed Bash command parsing of non-ASCII characters to match real shell word boundaries
- Fixed PowerShell tool permission validation of commands containing invisible Unicode characters
- Fixed dialogs in fullscreen mode stretching past the right-hand edge of their panel
- Fixed the `/config` settings list in fullscreen mode clipping its keyboard-hint footer
- Fixed the transcript-mode (Ctrl+O) footer hint wrapping on terminals narrower than 104 columns
- Fixed the Prometheus metrics endpoint (`OTEL_METRICS_EXPORTER=prometheus`) emitting invalid `# UNIT` lines
- Fixed skills and commands changed during a session not appearing in the slash menu until restart
- Fixed plugin skills with a `name` frontmatter field losing their plugin prefix in slash-command autocomplete
- Fixed telemetry misreporting permission denials: failed permission-prompt requests no longer count as user rejections, and user interrupts are now reported as user aborts instead of rejections
- Improved the `/fork` confirmation to one line with the new session's name, `claude attach` id, and a note when the copy shares your checkout
- Improved validation of `git` and `gh` command arguments in the PowerShell tool
- Improved the `/ultrareview` diff-too-large error to show configured limits, measured diff size, and largest contributing files
- Improved `/code-review ultra` empty-diff message to name the exact base ref and suggest passing an explicit base
- Improved the spend limit adjustment prompt to show the server's reason when a spend limit change is rejected
- `/context` now shows an explicit warning when the conversation exceeds the context window, and a failed `/compact` displays as an error
- `/rewind` no longer restores or deletes files through symlinks or hard links at tracked paths and reports how many paths it skipped
- Background sessions: `/mcp` and `/install-github-app` now park a "needs input" request in the agent view when no client is attached
- Updated the bundled dataviz skill: reordered the default chart palette and fixed guidance that suggested direct labels for four-series charts
- [VSCode] Fixed right-to-left text (Arabic, Hebrew, Persian) rendering in the wrong order when mixed with English or code
- Fixed cloud sessions dropping the in-flight message when the session's container restarts mid-turn — the interrupted turn now re-runs on resume instead of leaving the session unresponsive

## 2.1.215

- Claude no longer runs the `/verify` and `/code-review` skills on its own; invoke them with `/verify` or `/code-review` when you want them

## 2.1.214

- Fixed single-segment `dir/**` allow rules like `Edit(src/**)` auto-approving writes to nested `dir/` directories anywhere in the tree instead of only `<cwd>/dir`
- Fixed a permission-check bypass affecting commands run in Windows PowerShell 5.1 sessions
- Fixed Bash permission checks to fail closed on file-descriptor redirect forms that bash parses differently than the permission analyzer
- Fixed Bash permission checks misjudging very long commands — commands over 10,000 characters now always prompt instead of running automatically
- Fixed Bash permission checks treating zsh variable subscripts and modifiers in `[[ ]]` comparisons as inert text — these commands now prompt for approval
- Fixed Bash permission checks to no longer auto-approve certain `help` and `man` commands that could run unsafe options, command substitutions, or backslash paths
- Fixed permission prompts on remote sessions that could proceed before the local confirmation dialog
- Added the EndConversation tool: Claude can end sessions with highly abusive users or jailbreak attempts, as on claude.ai since 2025 — see https://www.anthropic.com/research/end-subset-conversations
- Added a periodic progress heartbeat for long-running tool calls that previously went silent
- Added an ISO `modified` timestamp to memory file frontmatter
- Added `message.uuid`, `client_request_id`, and `tool_source` attributes to OpenTelemetry log events for message-level correlation and tool provenance
- Added `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` to configure the 60 KB truncation limit on OpenTelemetry content attributes
- Added reasoning effort to the `subagentStatusLine` payload, so custom agent rows can render model and effort
- Added permission prompts for `docker` commands (including the Podman `docker` shim) carrying daemon-redirect flags (`--url`, `--connection`, `--identity`, and Podman's remote mode) that previously ran without one
- Fixed a crash when a GrowthBook feature evaluates to null, and a bug where a malformed flag payload could wipe the cached feature flags
- Fixed Bash tool killing the Claude session when a `pkill -f` pattern accidentally matched the CLI's own process (Linux)
- Fixed unbounded memory growth when `--settings` points at a device file or multi-GB file; oversized (>2 MiB) settings files now fail at startup with a clear error
- Fixed streaming turns failing with "Socket is closed" behind corporate proxies on Windows
- Fixed stream-json output truncation at exit for slow-reading SDK/pipeline consumers; the exit drain now scales with queued bytes instead of a flat 2s cap
- Fixed scheduled tasks refusing their own configured prompt as untrusted input — the fired prompt is now delivered as the session's assigned task
- Fixed PowerShell tool commands hanging until timeout when a child process waited on standard input (Windows)
- Fixed Python scripts under the PowerShell tool crashing with UnicodeDecodeError when reading non-UTF-8 data from standard input (Windows)
- Fixed Python scripts run via the PowerShell tool crashing with UnicodeEncodeError on non-ASCII output, and PowerShell 7 error messages containing raw ANSI escape sequences (Windows)
- Fixed the PowerShell tool reporting `where.exe`, `fc.exe`, and `diff.exe` as errors when they return a valid negative answer (Windows)
- Fixed `>` and `>>` under the PowerShell tool on Windows PowerShell 5.1 writing UTF-16LE files that other tools couldn't read as UTF-8
- Fixed a displaced background daemon deleting its successor's control socket on shutdown, which made the next client kill the healthy replacement daemon
- Fixed background sessions parked with `←` or `/background` and left idle keeping the background daemon and a worker process alive indefinitely
- Fixed completed background sessions being impossible to remove via `claude rm` or the agent view once the background service had gone idle
- Fixed background sessions dispatched from a non-git folder being impossible to delete from the agents view
- Fixed reopening a stopped background session failing to restore its saved conversation when an unreadable folder exists in the session store
- Fixed the Remote Control "session ready" push notification firing for sessions where Remote Control was not explicitly enabled
- Fixed `/install-github-app` and the `/mcp` settings menu being blocked in agent-view sessions — they're now refused only in background sessions with no terminal attached
- Fixed plugins enabled via the `--settings` CLI flag not loading (regression since v2.1.181)
- Fixed feature flags going stale in long-running sessions after the OAuth token rotates
- Fixed `/ultrareview` refusing to run in repos with no merge base — it now offers to review all tracked files
- Fixed `claude update` and `claude doctor` hanging silently, and the `/status` System diagnostics section going blank, when a shell-config path is a directory
- Fixed memory frontmatter values being silently truncated at an inline `#` when memory files are saved
- Fixed session cost and token telemetry double-counting on streams that emit multiple cumulative `message_delta` frames
- Fixed a spurious "check your network" warning that appeared while the advisor was thinking
- Fixed hooks with exit code 2 not blocking as documented when the hook's stdout JSON fails schema validation
- Fixed OTel log events emitted outside the turn's async context missing the interaction span's trace context
- Fixed MCP transient errors during prompts/resources refresh clearing the server's slash commands and resources
- Improved the `claude rc` workspace-trust error in the home directory to say trust there is never saved and to suggest running from a project directory
- Changed single-segment `dir/**` hook `if:` conditions to match only `<cwd>/dir`; write `**/dir/**` for any-depth matching. `deny`/`ask` permission rules keep their any-depth match.
- Changed `file` commands using `-m`/`--magic-file` or `-f`/`--files-from` to require permission instead of being auto-allowed as read-only
- Changed keep-alive connection pooling to disable after a stale-connection error, so retries open a fresh socket
- Changed SessionStart hooks to report source `"fork"` when a session begins as a fork instead of `"resume"`

## 2.1.212

- `/fork` now copies your conversation into a new background session (its own row in `claude agents`) while you keep working; the in-session subagent it used to launch is now `/subtask`
- Added `claude auto-mode reset` to restore the default auto-mode configuration, with a confirmation prompt (pass `--yes` to skip)
- Added a session-wide limit on WebSearch tool calls (default 200, tunable via `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`) to stop runaway search loops
- Added a per-session cap on subagent spawns (default 200, override with `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`) to stop runaway delegation loops; `/clear` resets the budget
- MCP tool calls running longer than 2 minutes now move to the background automatically so the session stays usable; configure the threshold or disable with `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`
- Typing `/resume` in the agent view now opens a picker of past sessions — including sessions deleted from the list — and resumes your pick as a background session
- Fixed plan mode auto-running file-modifying Bash commands (e.g. `touch`, `rm`) without a permission prompt or SDK `canUseTool` callback
- Fixed worktree creation following a repository-committed symlink at `.claude/worktrees`, which could create files outside the repository
- Fixed a `continue:false` hook's halt being dropped when the tool fails or completes mid-stream, and hook infrastructure errors being misreported as user rejections
- Fixed SIGTERM during a running Bash tool orphaning the command's process tree in print/SDK mode; the CLI now aborts the turn, kills the tree, and exits 143
- Fixed `/background` and `claude --bg` failing with "EUNKNOWN: unknown error, uv_spawn" on Windows when Group Policy blocks PowerShell 5.1; the daemon now prefers PowerShell 7
- Fixed shell mode (`!`) not executing commands containing file paths while the path autocomplete popup was open
- Fixed auto-mode denial notifications rendering broken characters when a long denial reason was truncated mid-emoji
- Fixed Ctrl+J not inserting a newline in the agent view dispatch input on terminals with extended key reporting, and surfaced the newline shortcut in the `?` help overlay
- Fixed `/ultrareview` rejecting PR references like `#123`, `PR 123`, and pasted PR URLs; error hints now name the command you actually typed
- Fixed `/ultrareview <branch>` not fetching the branch from origin when it exists remotely; it now suggests the closest branch name on typos
- Fixed `/ultrareview` skipping the billing confirmation in a new conversation after `/clear`
- Fixed `/ultrareview`'s "not a git repository" error on Claude Desktop now suggesting the project's repository folder instead of terminal commands
- Fixed hosted (host-managed) sessions failing at startup when repository settings configured mTLS certs, extra CA bundles, or OAuth scopes; these transport settings are now ignored with a warning
- Fixed a spurious "File has not been read yet" error when editing a file that had been read with offset/limit before resuming a session
- Fixed `ExitWorktree` failing with "no active EnterWorktree session" after resuming a session with `--continue`/`--resume` in print/SDK mode
- Fixed the workflow agent grid staying empty for Remote Control clients that join a session mid-run
- Fixed streaming-mode control requests being marked complete before their handler finished, which could lose the request on session restart
- Fixed background sessions created with `/fork` losing their live-parent protection after a state write failure
- Fixed reopening a stopped background session from the agent view failing silently — it now resumes the session, or shows why it can't and lets you force a restart
- Fixed agent teams: a stopping teammate could send the leader duplicate idle notifications when team initialization re-ran within a session
- Fixed the plan-approval dialog footer splitting "ctrl+g to edit in <editor>" apart when the file path is long
- Fixed the welcome banner keeping its old panel widths after a combined width+height terminal resize in fullscreen mode
- Fixed diff previews losing their line numbers and +/- markers in narrow layouts
- Fixed @-mentions attaching nothing after a partial file read, plugin uninstall targeting the wrong marketplace, and false "Command timed out" on exit code 143
- Fixed OpenTelemetry HTTP exports being rejected with 411/400 by Azure Monitor and other endpoints that don't accept chunked transfer encoding
- Fixed OTLP event log records missing `trace_id`/`span_id` when `TRACEPARENT` is set in SDK/headless mode
- Fixed conversations with many images incorrectly failing with "Request too large" errors, and improved the error message to explain the actual cause
- Fixed web search and web fetch returning "API Error" text as search results or page content when the API was overloaded
- Improved web search and web fetch reliability by retrying 529 errors and rate-limited requests with bounded backoff
- Improved prompt caching: the mid-conversation system block now works behind LLM gateways and custom base URLs (Bedrock, Vertex, 1P)
- Improved background agent attach: cold-attaching now instantly shows the formatted transcript while the session boots, instead of a blank wait
- Reduced token usage in inter-agent messaging: `SendMessage` bodies are no longer duplicated into replayed history and tool results
- Changed `/fork` to name the copy after your prompt when the session has no title, so the row is recognizable in the agent view
- Changed bare `/btw` to reopen the side-question panel on your most recent exchange so you can browse earlier answers
- Changed the `←` footer hint to pulse `N done` for a moment when a background agent finishes while nothing needs your input
- Deprecated the Task tool's `mode` parameter (now ignored); subagents inherit the parent session's permission mode by default
- Changed Enterprise `forceLoginMethod` to be enforced for VS Code extension, SDK, `setup-token`, and `install-github-app` logins, not just the terminal
- Changed session transcripts to record the reasoning effort level on each assistant message
- Changed headless/SDK sessions to apply a `set_model` control request mid-turn; the next model round-trip uses the new model instead of waiting for the next turn
- Changed agent view / `claude agents --json`: sessions waiting on a sandbox, MCP-input, or managed-settings prompt now show as "Needs input" instead of "Working"
- Updated the auth status panel title from "Cloud authentication" to "Authentication"
- Corrected an earlier release note (2.1.200): tmux through the 3.6 series lacks synchronized output; newer tmux with support is detected automatically

## 2.1.211

- Added `--forward-subagent-text` flag and `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT` environment variable to include subagent text and thinking in stream-json output
- Fixed permission previews relayed to chat channels not neutralizing bidirectional-override, zero-width, and look-alike quote characters, so tool inputs cannot visually alter the approval message
- Fixed auto mode overriding a PreToolUse hook's `ask` decision for unsandboxed Bash — a hook `ask` now floors the decision at a prompt
- Fixed parallel Claude Code sessions all logging out simultaneously after wake-from-sleep when many sessions share one credential store
- Fixed plugin MCP servers not reconnecting after an idle web session woke, leaving MCP calls failing until the next message
- Fixed Claude Code on Vertex and Bedrock attempting the default Opus model at startup and printing a spurious fallback notice when a model is explicitly configured
- Fixed subagents spawned with an explicit model override reverting to the parent's model when resumed or sent a follow-up message
- Fixed nested `.claude/rules/*.md` files loading even when setting sources exclude project settings
- Fixed file upload validation: filenames ending in a DOS device suffix (`.prn`) or trailing dot are now accepted, and files with multiple hard links are refused
- Fixed file uploads to Claude in Chrome from remote and CLI sessions
- Fixed edits that leave the input as "?" being silently swallowed and toggling the shortcuts panel
- Fixed a startup hang when the Claude in Chrome extension is enabled but Chrome is not running
- Fixed a 300ms delay revealing async content (Settings tabs, Stats, diff views, and other loading states)
- Fixed reopening a just-stopped background session from the agents view starting a blank conversation under the same session id
- Fixed `/loop` hiding the session from `/resume` after a single use
- Fixed screen reader users losing the audible terminal bell after `/terminal-setup` or onboarding terminal setup
- Fixed background jobs on LLM gateway auth (`ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`) coming back "Not logged in" after the daemon respawns them
- Fixed `claude agents` jobs becoming permanently undeletable when git no longer recognizes their worktree — the row now shows why the delete was refused instead of silently reappearing
- Fixed `/clear` not resetting the session cost counter — the statusline's cost now starts at $0 after `/clear`
- Fixed Claude in Chrome setup pages failing to open in the browser on Windows
- Fixed headless print-mode sessions on Windows crashing or silently exiting when stdin is unreadable
- Fixed background session titles in the agents view showing the naming model's refusal text when the prompt contains a link
- Fixed background agents killed by the user auto-respawning, and revived agents re-running stale prompts from old sessions
- Fixed routines with no schedule reporting a next run time in the year 1
- Hardened synced skill/plugin directory naming on Windows and kept CCR web fetch/search proxies working after `/clear`
- Improved terminal layout and rendering performance
- Improved background agent result reporting — Claude now reports the status of still-running agents and waits for the real completion instead of fabricating results
- Improved the memory index over-limit warning to measure only loaded content, excluding frontmatter and HTML comments
- Updated integer environment variables (timeouts, token budgets, retry counts) to accept scientific notation and digit-separator spellings like `1e6` and `64_000`
- Updated documentation links to the current docs sites
- Changed "always allow" permission rules to save at the repository root, so approvals granted in a git worktree persist across sessions and worktrees
- Changed `/usage-credits` to ask for confirmation before sending a request to organization admins
- Changed Vim mode `s` and `S` (substitute char/line) to work in NORMAL mode, matching vim behavior
- [VSCode] Updated the Remote Control banner to describe what it does
- Claude in Chrome: hardened file-upload path validation
- Claude in Chrome: `save_to_disk` on screenshot actions now writes the image to disk and returns the path; previously it did nothing
- Fixed a prompt-caching regression on Bedrock, Vertex, Mantle, and Foundry that billed the trailing system context block as fresh input tokens on every request.

## 2.1.210

- Added a live elapsed-time counter to the collapsed tool summary line so long-running tool calls visibly tick instead of looking stuck
- Added a startup warning for `Write(path)`, `NotebookEdit(path)`, and `Glob(path)` permission rules — use `Edit(path)` or `Read(path)` instead
- Fixed `isolation: 'worktree'` subagents being able to run git-mutating commands against the main repo checkout instead of their own isolated worktree
- Fixed the `ultracode` keyword opt-in firing on non-human-originated input such as webhook payloads and relayed PR comments
- Fixed a rendered text fragment leaking into crash telemetry when a UI component returned content outside a styled text element
- Fixed paste markers leaking into external editors opened from Claude Code, which could appear as stray È/É characters around pasted text
- Fixed `claude attach` sometimes failing with "job not found" or "agent is still starting" errors during session transitions — attach now waits for the daemon to settle, and terminal resizes during a slow attach are applied once it completes
- Fixed a session crash when a tool's result renderer returned a numeric bigint value or plain text instead of a UI element
- Fixed a hook callback timeout being misreported to the model as a user rejection, which made unattended sessions stop and wait
- Fixed Claude assuming a `cd` took effect after its command was moved to the background; the tool result now states the working directory is unchanged
- Fixed plugin-provided MCP servers being torn down when MCP servers are re-synced mid-session
- Fixed plan approvals without edits being labeled "(edited by user)" and overwriting the plan file with a stale snapshot
- Fixed `/doctor` skipping its auto-mode-default proposal on Bedrock, Vertex, and Foundry, where auto mode no longer needs an opt-in
- Fixed Grep content mode claiming "No matches found" when paginating past the end of results
- Fixed unmatched `$1`/`$2` positional placeholders in skills and commands being silently stripped; they are now preserved verbatim
- Fixed plugin cache writes leaving temp files behind on failure and failing on locked-file renames on Windows and network filesystems
- Fixed background workers crash-looping when a client resets its connection to the background service
- Fixed `claude agents --effort ultracode` not reaching dispatched sessions; the value was silently dropped
- Fixed pressing ← to open the agents view dropping the task tracker when returning to the session
- Fixed the agents dashboard retaining pasted images from abandoned reply drafts after their session was deleted
- Fixed killed background sessions leaving a permanent `git worktree lock` behind; the periodic sweep now releases locks whose owning process is gone
- Fixed SDK MCP servers registered via an `initialize` control request waiting until the next turn to start connecting
- Fixed returning to the agents view from a session leaving overlapping ghost frames with `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1`
- Fixed late-appearing `.claude/*` symlinks not being reconciled into the sandbox deny-write list
- Hardened the Agent tool against indirect prompt injection via content a subagent read
- Improved the Bash/PowerShell tool message when a command hits its timeout and is auto-backgrounded, so the model can distinguish a hang from an explicit background request
- Improved auto mode: the permission classifier now defaults to Sonnet 5 for external sessions, validated on the session's first request and pinned for the session
- Improved the bundled dataviz skill's chart color validation with perceptual OKLab color difference and recalibrated color-blindness thresholds
- Memory writes that leave a MEMORY.md index over its read limit now produce an explicit error instead of silent truncation
- Screen reader mode now announces permission mode changes aloud when cycling modes with Shift+Tab
- The agents footer hint now shows how many background agents are waiting on your input, with a brief color emphasis when the count changes
- Agent view: the session you pressed ← from stays visibly marked even after mouse hover or arrow keys move the selection
- Fable temporarily shows as unavailable in the advisor picker while a server-side issue causing Fable advisor failures is fixed

## 2.1.209

- Fixed /model and other dialogs being blocked in `claude agents` background sessions (reverts an overly broad guard)

## 2.1.208

- Added screen reader mode: opt-in plain-text rendering for screen reader users. Run `claude --ax-screen-reader`, set CLAUDE_AX_SCREEN_READER=1, or add "axScreenReader": true to settings.
- Added `vimInsertModeRemaps` setting: map two-key insert-mode sequences like `jj` to Escape in vim mode
- Added `CLAUDE_CODE_PROCESS_WRAPPER`: agent view and the background service now honor a corporate launcher by running every Claude Code self-spawn through a required wrapper executable
- Added mouse-click support for multi-select menus and "Other" input rows in fullscreen mode
- Changed the Fable 5 usage-credits consent prompt to start with the decline option focused
- Fixed fast mode staying off after switching back to a model that supports it — it now restores automatically when enabled in settings
- Fixed replies typed to a background agent being lost when delivery fails — the text is now saved and delivered when the session restarts
- Fixed background-session attach failing permanently ("Couldn't start the background daemon") after an update replaced the binary a running `claude agents` process was launched from
- Fixed the context window (and auto-compact indicator) briefly resetting to 200k after the CLI auto-updates, causing a false "100% context used" when resuming long-context sessions
- Fixed supervised and background sessions crashing when a server closed an HTTP/2 connection with a GOAWAY while requests were in flight
- Fixed truncated stream-json/JSON output and missing result message when piping large responses from `claude -p`
- Fixed `CLAUDE_CODE_MAX_OUTPUT_TOKENS` and similar env vars silently using the mantissa of scientific-notation values (`1e6` became `1`)
- Fixed very large markdown tables stalling rendering or using excessive memory; tables over 200 rows show the first 200 with a "… N more rows" notice
- Fixed the Edit tool failing on files modified after reading when the target text still matches uniquely
- Fixed Read reporting empty files as "shorter than offset", Grep silently returning "No files found" for invalid regex patterns, Grep count mode under-reporting totals when paginated, and Glob crashing with an unclear error when the pattern, path, or working directory contained a null byte
- Fixed `apiKeyHelper` script failures being hidden behind a generic 401 after ~10 silent retries; the script's own error is now shown within 3 attempts
- Fixed Bedrock streaming requests failing with a misleading "Truncated event message received" when a gateway transforms the response — the error now names the content-type and points at the proxy
- Fixed `/upgrade` showing a login flow instead of the upgrade URL when the browser fails to open
- Fixed stream-json input killing the session on blank CRLF or whitespace-only lines from Windows-style SDK hosts
- Fixed headless stream-json sessions hanging permanently when a `control_request` carried a non-string `set_model` payload; the CLI now answers with an error response
- Fixed repeated "No completion record was found" notices on session resume — orphaned background tasks now collapse into a single summary
- Fixed Remote Control clients attaching to a terminal-hosted session not seeing background agents and workflow progress until a task started or stopped
- Fixed the Agent tool launching with no tools when a subagent's `tools` list resolves to nothing — it now returns a clear error naming the unrecognized entries
- Fixed `/usage` showing stale cached bars over fresher data, and `/mcp` not reclassifying placeholder servers after config edits
- Fixed "Change directory" in SDK hosts (e.g. Claude Desktop) failing with "A turn is in progress" on idle sessions that have a running background task
- Fixed the workflow save dialog showing `~/.claude/workflows/` instead of the `CLAUDE_CONFIG_DIR` location for user-scope saves
- Fixed `/release-notes` adding the viewed notes to the model's context — "Show all" previously injected the entire changelog into every subsequent request
- Fixed a memory leak in the agent view where pasted images were retained for the screen's lifetime after sending peek replies
- Fixed SDK sessions losing agents defined via the initialize request when a plugin refresh ran before the client attached
- Fixed several memory leaks in long sessions: MCP stdio server stderr accumulating up to 64 MB per server, LSP documents staying open indefinitely (now LRU with 50-doc cap), async hook output retained after backgrounding, and unbounded growth in headless/SDK sessions from large tool-result payloads
- Fixed a memory blowup when reading files with extremely long single lines using offset/limit — the read now returns a clean error instead of loading the whole line
- Fixed multi-second per-turn slowdowns in sessions with many permission deny/ask rules — rule matchers are now compiled once and cached
- Improved input responsiveness while agent task lists update — task updates no longer re-render the entire UI
- Reduced per-tool-call CPU overhead in print/SDK sessions with many MCP tools by caching tool-pool assembly (up to 7x faster tool rounds at high tool counts)
- Reduced memory usage by bounding the file edit read cache to 16 MB instead of pinning up to 1,000 full files
- Reduced session transcript size (up to 79x in edit-heavy sessions) and bounded checkpoint disk usage by pruning superseded file-history backups
- Reduced memory usage when resuming sessions with background agents or forks spawned from large conversations
- Completed background agents now stay listed in `/tasks` until cleanup instead of vanishing the moment they finish
- Attaching to a stopped background agent now shows its transcript immediately while the session warms up, instead of a blank "Session is starting" screen
- Background sessions: an older daemon no longer silently restarts workers spawned by a newer version onto the older binary
- Agent view: Ctrl+X now deletes renamed-branch worktrees, never destroys unpushed commits, keeps the session row when a worktree is kept, and reused worktree names reset to the current base
- Catastrophic removals (e.g. `rm -rf ~`) in commands containing `$(…)`/backticks/`<(…)` now prompt in `--dangerously-skip-permissions` and auto mode, matching the plain form
- `/install-github-app` and the `/mcp` settings menu no longer open in background sessions
- MCP servers configured with an empty URL now show as "not configured" in `/mcp` instead of a config error
- `/usage` now shows your last-known usage bars with an "as of" note when the usage endpoint is rate-limited, instead of an error screen
- Fixed Bedrock auth failing with "Session token not found or invalid" for AWS SSO profiles whose sso_region differs from the Bedrock region (2.1.207 regression)

## 2.1.207

- Auto mode is now available without `CLAUDE_CODE_ENABLE_AUTO_MODE` opt-in on Bedrock, Vertex AI, and Foundry; disable via `disableAutoMode` in settings
- Fixed the terminal freezing and keystrokes lagging while streaming responses containing very long lists, tables, paragraphs, or code blocks
- Fixed remote managed settings from a non-interactive run (`claude -p`, the SDK) being permanently recorded as consented without ever showing the security consent dialog
- Fixed spurious prompt-injection warnings triggered by benign system-generated conversation updates
- Fixed the auto-updater overwriting a custom launcher script or symlink at `~/.local/bin/claude` on every release; `/doctor` now reports an externally managed launcher
- Fixed compound commands with `cd` prompting for permission when the only output redirect was to `/dev/null`
- Fixed the transcript jumping above the start of the answer when a response finishes streaming
- Fixed `extensions.worktreeConfig` being left in the repo's `.git/config` (breaking go-git tools like `tea`) after the last `worktree.sparsePaths` worktree was removed
- Fixed malformed bracket patterns in rules globs, skill paths, `.ignore`, and `.worktreeinclude` breaking file reads, file suggestions, and worktree creation
- Fixed a crash loop in agent teams where a malformed teammate mailbox message caused repeated errors every second until the mailbox file was manually deleted
- Fixed background sessions auto-named by accepting a plan not showing that name on their agent-view row
- Fixed background sessions that entered a git worktree resuming blank after a cold reopen from the agent list
- Fixed Remote Control task status updates being lost when the connection recovered from a network interruption or credential refresh
- Fixed Remote Control sessions hosted by the desktop app not showing background agent and workflow progress on mobile and web
- Fixed Deep research runs labeling every Fetch-phase agent "unknown" — chips now show the source hostname
- Fixed Bedrock repeatedly requesting fresh AWS SSO credentials from IAM Identity Center on every API request
- Improved agent view: pasting the same text again now expands the collapsed `[Pasted text #N]` placeholder instead of adding a second one
- Improved agent view: blocked session peeks now lead with the question and show a worded staleness clock (`waiting 3m`) instead of the same timestamp twice
- Changed Bedrock, Vertex, and Claude Platform on AWS to default to Claude Opus 4.8
- Changed auto mode to no longer read `autoMode` from `.claude/settings.local.json` (repo-resident); use `~/.claude/settings.json` instead
- Fixed an indefinite hang on Windows when AWS credential resolution stalls (e.g. a stuck `credential_process`): the 60-second stall guard now fires instead of waiting forever.
- Plugin hooks/monitors/MCP headersHelper: `${user_config.*}` in shell-form commands is now rejected (shell-injection fix). Hooks: use exec form (`args` array) or `$CLAUDE_PLUGIN_OPTION_<KEY>`; monitors and headersHelper: read the value inside the script (config file or the server's `env` block).
- Plugin option values (`pluginConfigs`) are no longer read from project-level `.claude/settings.json`; only user, `--settings`, and managed settings are honored
- Fixed `/usage-credits` amount inputs silently stripping malformed values (e.g. a pasted timestamp) to digits; malformed amounts are now rejected with an error, and amounts over $1,000 require a typed confirmation

## 2.1.206

- Added directory path suggestions to `/cd`, matching `/add-dir` behavior
- Added a `/doctor` check that proposes trimming checked-in `CLAUDE.md` files by cutting content Claude could derive from the codebase
- `/commit-push-pr` now auto-allows `git push` to the repo's configured push remote (`remote.pushDefault`, or the sole remote when only one is configured) in addition to `origin`
- Gateway: `/login` now supports Anthropic-operated public gateway endpoints
- `EnterWorktree` now asks for confirmation before entering a git worktree outside the project's `.claude/worktrees/` directory
- Background agents now upgrade to a new version in the background right after a Claude Code update, instead of paying a slow stale-session upgrade when you attach
- Fixed an expired login failing every model with a misleading "There's an issue with the selected model" error instead of prompting to run `/login`
- Fixed `claude --resume` and `--continue` not responding to keyboard input on startup
- Fixed MCP servers configured via `--mcp-config` or `.mcp.json` ignoring a per-server `request_timeout_ms`, which caused long-running MCP tool calls to time out at the 60s default in fresh sessions
- Fixed `CLAUDE_CODE_EXTRA_BODY` being silently ignored by `claude agents` / `--bg` background workers; the shell-exported override now follows the dispatching session
- Fixed OAuth MCP servers requiring manual re-authentication after a single failed token refresh
- Fixed `--permission-prompt-tool` pointing at an MCP server crashing with "MCP tool not found" on cold start before the server finishes connecting
- Fixed `/model` picker rows printing a price for a different model than the row named, and stopped quoting first-party list prices on providers that don't bill them
- Fixed server-provided model rows being misplaced in the `/model` picker when an entitlement or allowlist restriction drops the row they were positioned against
- Fixed desktop sessions getting stuck showing "running" after a slash command was sent mid-turn
- Fixed keyboard input being ignored in the agents view when a setup prompt appeared before a bare `claude --resume` on Windows
- Fixed `claude rm` leaving the removed job in the daemon roster, causing the row to reappear in `claude agents`
- Fixed `/remote-control` showing "Unknown command" when logged out — it now explains how to sign in
- Fixed left arrow not stepping back out of a phase or agent in the workflow detail view
- Fixed `/status` listing the same broken-install warning twice
- Fixed false "disused plugin" tips and skewed disuse telemetry for LSP plugins
- Fixed `/doctor`'s update check to compare Homebrew installs against their cask's channel instead of the settings channel
- Fixed the fullscreen jump-to-bottom pill suggesting Ctrl+End on macOS, not showing rebound chords, and wrapping over the transcript
- Bedrock: fixed a multi-minute startup hang when using an `awsCredentialExport` helper on networks with restricted egress
- Improved `/code-review` findings quality on claude-opus-4-8 across all effort levels
- Improved agents view: status column now uses full terminal width instead of truncating at 64 characters
- Changed agents view: Ctrl+X now permanently removes a completed session, and sessions no longer render twice; deleted background jobs stay deleted

## 2.1.205

- Added an auto mode rule that blocks tampering with session transcript files
- Fixed `--json-schema` silently producing unstructured output when the schema was invalid, and schemas using the `format` keyword being rejected
- Fixed a message sent while Claude was working being silently lost when the turn ended at the `--max-turns` limit
- Fixed Windows worktree removal deleting files outside the worktree when an NTFS junction or directory symlink existed inside it
- Fixed background agents staying shown as "failed" or "completed" in the agent list after being resumed with `SendMessage`
- Fixed background jobs flipping from "needs input" back to "working" in the agent list when the agent's turn contained no readable text
- Fixed `claude attach` erroring when a background agent was mid-upgrade restart instead of waiting for it to come back
- Fixed session-to-PR linking missing a PR created in a Bash call whose output exceeded the 30K inline limit
- Fixed `claude mcp add-from-claude-desktop` getting stuck when a server name contains unsupported characters; invalid names are now reported and remaining servers still import
- Fixed a plugin LSP server that fails to initialize preventing a valid LSP server from another plugin handling the same file extension
- Fixed a Windows crash when the directory Claude was launched from is deleted, locked, or unmounted while a command is running
- Fixed a crash when a file watcher was closed while a directory scan was still in flight
- Fixed project verify skills being rewritten on every session instead of only when a documented command changed
- Fixed the agent view rendering one line too high and clipping its header when the job list slightly overflowed the screen
- Fixed background tasks in the web and mobile Remote Control panels showing stale "Running" status by forwarding full task state on every membership change
- Improved auto mode to ask before running `rm -rf` on a variable it can't resolve from context
- Auto-update binary downloads now stream to disk instead of buffering in memory, cutting the updater's peak memory usage by roughly 400 MB
- Background task notifications now explicitly state that no human input has occurred, preventing fabricated in-transcript approvals from being acted on
- Improved agent view: sessions that edit, merge, comment on, or push to an existing PR now link it in `claude agents`
- Improved agent view: rows now show a colored state word and a classifier-written headline instead of raw tool call text, and the peek opens with full status including the exact ask for blocked sessions
- `/doctor` is now a full setup checkup that can diagnose and fix issues; `/checkup` is its alias
- Reserved the "Claude Browser" MCP server name (alongside "Claude Preview") ahead of the Claude Desktop pane rename; user-configured MCP servers can no longer register under either name
- Fixed Cowork VM-mode local-agent sessions failing to start with "Not logged in · Please run /login" on CLI 2.1.203+

## 2.1.204

- Fixed hook events not streaming during SessionStart hooks in headless sessions, which could cause remote workers to be idle-reaped mid-hook

## 2.1.203

- Added a warning when your login is about to expire, so you can re-authenticate before background sessions are interrupted
- Added a grey ⏸ badge to the footer when in manual permission mode, making the active mode always visible
- Added the session's additional working directories to MCP `roots/list`, with `notifications/roots/list_changed` sent when the set changes
- Fixed opening or switching background agent sessions on macOS stalling for 15–20 seconds due to a false low-memory detection (regression in 2.1.196)
- Fixed background sessions becoming permanently unresponsive to attach, replies, and stop when the daemon's session token went stale — the session now recovers automatically
- Fixed returning to `claude agents` silently stopping running subagents and re-running the prompt from scratch — their work now carries over
- Fixed a memory and per-turn CPU regression in interactive sessions: the context-usage indicator no longer re-analyzes the entire transcript after every turn
- Fixed background agents inheriting a stale `PATH` from the daemon instead of the dispatching shell, causing missing tools on Windows
- Fixed background and agent-view sessions dropping a shell-exported `ANTHROPIC_BASE_URL`, which sent API keys to the default endpoint and failed with 401
- Fixed Bash failing with "argument list too long" in repos with many git worktrees
- Fixed worktree-isolated subagents sometimes running shell commands in the parent checkout instead of their own worktree
- Fixed worktree creation rejecting nested repositories in multi-repo workspaces, leaving background sessions unable to isolate and edit
- Fixed background agents crash-looping when their working directory was deleted, replaced by a file, or became an invalid path — they now fail once with a clear error
- Fixed a background daemon auto-upgrade failure silently killing all running background sessions
- Fixed `TaskStop` and `TaskOutput` failing to find background agents spawned by another agent — errors now list running agents by id and description
- Fixed the `claude agents` composer discarding your typed message when a slash command isn't available there
- Fixed the agent list crashing when opening a stopped session whose conversation was already open in another session
- Fixed background sessions showing "Needs input" in the agent list after the question was already answered
- Fixed background agent startup failures showing only "exit_with_message" instead of the actual error
- Fixed background sessions ignoring `effortLevel` changes in settings.json when forked through the daemon
- Fixed attached background sessions ignoring `CLAUDE_CODE_DISABLE_MOUSE` and `CLAUDE_CODE_DISABLE_MOUSE_CLICKS` opt-outs
- Fixed `/exit` incorrectly warning about running background agents after all named agents had completed
- Fixed background sessions started from a non-git directory unable to edit files when a `WorktreeCreate` hook was configured
- Fixed the `@` directory picker in `claude agents` not showing registered git worktrees
- Fixed background task output on Windows being permanently replaced by an empty file after `/clear`
- Fixed content jumping when scrolling up through long transcript history
- Fixed the terminal flickering and jumping while typing in bash mode when a shell-history suggestion was shown
- Fixed literal `^[[I` / `^[[O` escape codes being printed when reattaching to a background session
- Fixed LSP-only plugins being incorrectly flagged for disuse when their language servers deliver diagnostics or answer navigation requests
- Improved responsiveness while long responses stream: live-preview updates no longer re-render the whole screen
- Improved subagent behavior: agents are now less likely to re-delegate their entire task to another subagent
- Reduced binary size by ~7 MB and startup memory by ~7 MB by loading a large bundled dependency lazily instead of inlining it
- Changed left arrow to no longer close the background tasks, diff, and workflow detail views — press Esc instead
- Changed the empty `claude agents` view to always show the organized sections (Needs input / Working / Completed) with descriptions
- Removed the startup "claude command missing or broken" warnings — they now appear in `/doctor` and `/status` instead
- Removed a redundant navigation hint from the `claude agents` footer
- [VSCode] Added a Settings toggle for "Enable Remote Control for all sessions"

## 2.1.202

- Added a "Dynamic workflow size" setting in `/config` for controlling how large Claude generally makes dynamic workflows (small/medium/large agent counts) — an advisory guideline, not an enforced cap
- Added `workflow.run_id` and `workflow.name` OpenTelemetry attributes to telemetry emitted by workflow-spawned agents, so a workflow run's activity can be reconstructed from OTel data
- Fixed a crash in the inline Ctrl+R history search when accepting or cancelling while the search was still scanning the history file
- Fixed `/rename` on background sessions being reverted when the job restarts, which broke addressing the session by its new name
- Fixed transient mTLS handshake failures when settings were re-applied during an in-place client certificate rotation
- Fixed commands sent from Remote Control (mobile/web) into an interactive session failing with "Unknown command"
- Fixed images and files sent from the Remote Control mobile or web app without a caption being silently dropped
- Fixed the sign-in URL printed by `claude auth login` and `claude mcp login --no-browser` not being reliably clickable when it wraps over SSH — it is now emitted as a single hyperlink
- Fixed opening a chat from `claude agents` sometimes failing with "currently running as a background agent" followed by a worker crash/respawn loop
- Fixed workflow scripts with unicode quote escapes in strings being corrupted before parsing; workflow parse errors now show the offending line instead of always blaming TypeScript
- Fixed voice dictation retrying in an unbounded loop when the microphone or audio recorder fails — repeated capture failures now pause voice input
- Fixed `/remote-control` sessions showing the wrong permission mode in the mobile and web apps
- Fixed resuming a session by name, or opening the resume picker, taking minutes and using a large amount of memory in repositories with many git worktrees
- Fixed installer and updater downloads failing immediately with "aborted" when a proxy or network drops the connection mid-download — transient connection drops now retry
- Fixed re-invoking an already-loaded skill appending a duplicate copy of its instructions to context
- Improved `/workflows` agent list layout: wider titles, a dedicated time column, shorter model names, and no per-row tool-call counts
- Improved MCP error messages: clearer error when a server config has `url` but no `type`, suggesting `"type": "http"` instead of the misleading "command: expected string"
- Changed `/review <pr>` back to a fast single-pass review; use `/code-review <level> <pr#>` for the multi-agent review at a chosen effort level

## 2.1.201

- Claude Sonnet 5 sessions no longer use the mid-conversation system role for harness reminders

## 2.1.200

- Changed `AskUserQuestion` dialogs to no longer auto-continue by default; opt into an idle timeout via `/config`
- Changed the "default" permission mode to "Manual" across the CLI, `--help`, VS Code, and JetBrains; `--permission-mode manual` and `"defaultMode": "manual"` are accepted alongside `default`
- Fixed a crash at startup when `disabledMcpServers` or `enabledMcpServers` in `.claude.json` is set to a non-array value
- Fixed background sessions silently stopping mid-turn after sleep/wake or when reopening a stalled session
- Fixed background sessions re-running a turn cancelled with Esc after a stall respawn
- Fixed background agents never starting again after a crash left a stale `daemon.lock` whose PID the OS reused
- Fixed background-agent daemon handover so a reinstalled older build can no longer take over the daemon; build recency is now judged by the version's embedded build timestamp
- Fixed background-agent roster issues: transient corruption permanently disabling orphan cleanup, older binaries not preserving fields written by newer versions, and socket auth tokens being stripped during daemon restarts
- Fixed subagents cut off by a rate limit before producing any text output returning an empty result instead of failing cleanly
- Fixed control bytes from background-agent output reaching the terminal in the agent view
- Fixed `claude agents --plugin-dir <dir>` not showing the plugin's agents and skills in the agent view when the flag is placed after `agents`
- Fixed project-scoped plugins not loading correctly from git worktrees of the same repository
- Fixed `/mcp` server list not tracking focus for screen readers and magnifiers
- Fixed voice dictation showing a misleading "Voice connection failed" message when a recording captures no audio
- Fixed rendering flicker under tmux 3.4+ by enabling synchronized terminal output
- Improved screen-reader output: decorative glyphs are now hidden, transcript symbols read as short labels, and nested tables read as `Header: value.` lines
- Improved the install script to explain when installation is killed by the system running out of memory

## 2.1.199

- Stacked slash-skill invocations like `/skill-a /skill-b do XYZ` now load all leading skills (up to 5), not just the first
- Fixed SSL certificate errors (TLS-inspecting proxies, missing `NODE_EXTRA_CA_CERTS`, expired certs) burning retries before showing actionable guidance — they now fail immediately with the fix hint
- Fixed streaming responses being discarded when the API emits a mid-stream overloaded/server error after partial output — the partial is now kept with an incomplete-response notice
- Fixed subagents cut off by a rate limit or server error silently failing instead of returning their partial work to the parent
- Fixed subagents reporting API errors (e.g. usage limit reached) as successful results — the error is now reported to the parent agent
- Fixed the background-agent daemon on Linux killing itself and every running agent every ~50 seconds after an unclean shutdown left a corrupted worker record
- Fixed background agents failing to cold-start over SSH on macOS with "Could not switch to audit session" (regression in 2.1.196)
- Fixed `claude stop` being silently undone when it raced a background-agent respawn — the respawn now honors the stop
- Fixed background job progress indicators stalling for minutes while the job ran long commands
- Fixed background sessions on memory-starved machines showing a generic error — they now indicate low memory and suggest freeing resources
- Fixed remote sessions briefly flapping between Working and Idle in the agent view when a background agent completes
- Fixed idle subagents vanishing from the agent panel while other subagents were still working; surplus idle agents now collapse into an expandable summary row
- Fixed typing `/model` or `/fast` while viewing a subagent silently opening the lead's model picker — a notice now explains the command applies to the lead
- Fixed `SessionStart`, `Setup`, and `SubagentStart` hooks silently hiding stderr when exiting with code 2 — the error is now shown in the transcript
- Fixed `claude --dangerously-skip-permissions daemon <subcommand>` being treated as a chat prompt instead of running the subcommand
- Fixed `SendMessage` silently misrouting when a re-spawned agent reuses a previous agent's name — the tool now detects the mismatch and asks the caller to retarget
- Fixed opening or resuming a session with no new messages needlessly growing the transcript file
- Fixed backgrounding a session with `←` or `/background` dropping its `/color` from the agent view row
- Fixed resetting a corrupted config file from the startup recovery dialog destroying it unrecoverably — it now backs up the file first
- Fixed Claude in Chrome repeatedly opening the reconnect page when sessions run from different builds or config directories
- Fixed plan mode not prompting for state-changing browser tool calls; read-only `browser_batch` calls are now correctly auto-allowed
- Transient server rate-limit errors (429s unrelated to your usage limit) are now retried automatically with backoff for subscribers instead of failing the turn
- `CLAUDE_CODE_RETRY_WATCHDOG` now raises the default retry count for non-capacity transient errors to 300 and lifts the cap of 15 on `CLAUDE_CODE_MAX_RETRIES`
- `claude agents` session rows now show pull-request links as bare `#N` without the redundant "PR" label
- **new-claim** — adds a capability claim not previously upstream
  - now: - Subagents now run in the background by default, so Claude keeps working while they run and is notified when they finish (previously a gradual rollout)
- **removal** — removes a previously-present capability claim
  - was: - Self-hosted runner: added a `post-session` lifecycle hook that runs after the session ends and before the workspace is deleted, so you can snapshot uncommitted work or export logs; also made the child-process SIGTERM→SIGKILL window configurable (default unchanged at 5s)
- **reprojection** — same-statement update (similarity >= threshold)
  - was: - Added deprecation notification for npm installations - run `claude install` or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options
  - now: - Added deprecation notification for npm installations - run `claude install` or see https://code.claude.com/docs/en/setup for more options
