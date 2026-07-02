# Pending delta — claude-code-changelog

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-02T13:49:59Z

- **new-claim** — adds a capability claim not previously upstream
  - now: ## 2.1.198

- Claude in Chrome is now generally available
- Added background agent notifications in `claude agents` — sessions that need input or finish now fire the `Notification` hook (`agent_needs_input` / `agent_completed`)
- Added `/dataviz` skill for chart and dashboard design guidance with a runnable color-palette validator
- Gateway: added Claude Platform on AWS (anthropicAws) as an upstream provider; model-not-found responses now advance the failover chain
- Background agents launched from `claude agents` now commit, push, and open a draft PR when they finish code work in a worktree, instead of stopping to ask
- The built-in Explore agent now inherits the main session's model (capped at opus) instead of running on haiku
- Subagents and context compaction now inherit the session's extended thinking configuration, improving output quality on delegated tasks
- Fixed brief network drops mid-response aborting the turn — transient errors like ECONNRESET now retry with backoff instead of failing
- Fixed excessive background classifier requests when sandboxed processes repeatedly accessed the same network host
- Fixed background tasks in web, desktop, and VS Code task panels getting stuck on "Running" after they finish or after resuming a session
- Fixed agent teams: a teammate that dies on an API error now reports "failed" to the lead, and messaging a stuck teammate wakes it to retry immediately
- Fixed the `/diff` panel not refreshing when you switch branches or commit outside the session
- Fixed markdown tables overflowing and wrapping their right border when rendered in fullscreen mode
- Fixed Claude Platform on AWS and Mantle sessions dead-ending with "Please run /login" when the STS token expires — `awsAuthRefresh` now runs automatically
- Fixed "no route to host" for local-network hosts in macOS background agent sessions by declaring Local Network entitlements
- Fixed `/desktop` failing with "Cannot determine working directory" after entering and exiting a worktree
- Fixed background agents repeatedly showing "Reconnecting…" every ~52 seconds on macOS while the agents view was open
- Fixed pressing `←` inside `claude attach <id>` exiting to the shell instead of opening the agent view
- Fixed `claude --bg` silently creating an unattachable session when combined with `--print`/`-p`; the conflicting flags are now rejected up front
- Fixed the workflow progress view dropping the earliest agents from the list while the phase counter stayed correct in SDK and desktop-app sessions
- Fixed `.claude/rules/` conditional rules not loading when the target file is reached via a symlinked path
- Fixed Cmd+click not opening URLs in fullscreen mode in Warp on macOS
- Fixed double-click word selection in fullscreen mode to select the entire URL including the scheme
- Fixed plan mode not auto-allowing read-only tool calls when a session starts in plan mode
- Fixed `/branch` deriving its default fork name from the compaction summary instead of the first real prompt
- Improved focus mode: subagents launched in a turn now appear in its activity summary, and completed background notifications fold into a single count
- Improved syntax highlighting accuracy in code blocks, diffs, and file previews by upgrading to highlight.js 11
- Keyboard shortcut hints now show opt/cmd instead of alt/super when connected from a Mac over SSH
- Improved API retry UX: the error reason is now shown after the second attempt, and a status page link replaces the spinner tip when the API is overloaded
- `/login` now opens the sign-in dialog from the `claude agents` view instead of saying it isn't available
- Subagents now treat messages from the agent that launched them as normal task direction; an agent's message is still never treated as the user's approval
- Removed the `/agents` wizard; ask Claude to create or manage subagents, or edit `.claude/agents/` directly

## 2.1.197

- Introducing Claude Sonnet 5: now the default model in Claude Code, with a native 1M-token context window and promotional pricing of $2/$10 per Mtok through August 31. Update to version 2.1.197 for access. https://www.anthropic.com/news/claude-sonnet-5

## 2.1.196

- Added support for organization default models — admins set it in the org console; it shows as "Org default" (or "Role default") in `/model` when you haven't picked one yourself
- Added readable default names for sessions at start, making them easier to identify and message
- Added clickable file attachments in chat — Cmd/Ctrl-click reveals the file in Finder/Explorer
- Security: `claude mcp list`/`get` no longer spawn `.mcp.json` servers that a repo self-approved via a committed `.claude/settings.json`; untrusted workspaces show `⏸ Pending approval`
- Fixed waking a background job permanently deleting its conversation and re-running the original prompt when the transcript probe misread a real transcript; the file is now set aside, never deleted
- Fixed the rate-limit warning flickering off and rate-limit telemetry being over-counted when multiple parallel requests were in flight at the moment a usage limit was hit
- Fixed duplicate recap lines after a background session's turn: a schema-rejected StructuredOutput attempt no longer renders alongside its retry
- Fixed PowerShell `git diff`/`git grep`, `egrep`/`fgrep`, and quoted search patterns containing `|` being reported as failures when they exit 1, matching Bash behavior
- Fixed multiple `claude agents` side panel issues: keyboard focus getting stuck when opening an agent, background jobs losing their subagent types on every open, and sessions showing incorrect status while actively running
- Fixed `claude agents --dangerously-skip-permissions` silently falling back to auto mode instead of showing the bypass disclaimer and applying bypass mode to spawned agents
- Fixed mid-turn crash recovery for Remote sessions — sessions interrupted by a server restart now auto-resume on the next worker
- Fixed sessions moved with `/cd` reappearing in the old directory's resume list after a non-graceful exit when the old path contained special characters
- Fixed `claude plugin validate` skipping local plugins whose source is "." and stopping after the first error class
- Fixed Esc Esc at an idle prompt not opening the rewind menu (regression); use Ctrl+C or Ctrl+X Ctrl+K to stop background agents
- Fixed MCP OAuth requesting the authorization server's full `scopes_supported` catalog when no scope is specified, causing `invalid_scope` failures on GitLab self-hosted and other enterprise IdPs
- Fixed `/context` showing 0 tokens for all tool groups on Bedrock
- Fixed `/deep-research` misreporting verifier failures as "all claims refuted" instead of `unverified`
- Fixed plugin dependency version pins not being honored when the marketplace was added as a local folder path backed by a git repo
- Fixed `claude agents` session status: completed rows no longer flip between "Done" and "Needs your input", stalled agents are now labeled "Needs attention", and results that mention a PR show a clickable link
- Fixed voice dictation swallowing spaces and spuriously starting a recording during very fast typing when voice mode is enabled
- Improved background session reliability: long-running commands and workflows now survive the session's process being stopped, restarted, or updated — including on Windows, where background shells are handed off instead of being killed
- Improved background agents: workers killed by a daemon restart are now automatically resumed from where they left off the next time the agents view opens
- Improved `/code-review` workflow: merged five cleanup finders into one, cutting token usage by roughly 25%
- Reduced per-frame rendering work in the terminal UI by skipping no-op subtree walks during streaming
- The streaming idle watchdog is now on by default for all providers — it aborts and retries when a response stream produces no events for 5 minutes. Set `CLAUDE_ENABLE_STREAM_WATCHDOG=0` to disable.
- Remote Control is now disabled when `ANTHROPIC_BASE_URL` points at a non-Anthropic host, matching the existing behavior under `CLAUDE_CODE_USE_BEDROCK`/`_VERTEX`/`_FOUNDRY`
- Changed opening the agents view from a foreground session to require a single `←` press instead of two, matching the behavior in background sessions

## 2.1.195

- Added `CLAUDE_CODE_DISABLE_MOUSE_CLICKS` to disable mouse click/drag/hover in fullscreen mode while keeping wheel scroll
- Fixed hook matchers with hyphenated identifiers (e.g. `code-reviewer`, `mcp__brave-search`) accidentally substring-matching — they now exact-match. Use `mcp__brave-search__.*` to match all tools from a hyphenated MCP server.
- Fixed voice dictation on macOS capturing silence in long-running sessions after the default input device changes
- Fixed voice dictation auto-submit never firing for languages written without spaces (Japanese, Chinese, Thai)
- Fixed external plugins enabled only by project `.claude/settings.json` not requiring explicit install consent on every loader path
- Fixed `/plugin` Enable/Disable not working when a plugin's `plugin.json` `name` differs from its marketplace entry name
- Fixed background jobs disappearing from `claude agents` or losing data when written by a newer Claude Code version
- Fixed reopening a crashed background task showing a blank screen for up to 5 seconds instead of its restart
- Fixed background agent daemons running unreachable when the control socket fails to start, blocking restarts
- Improved voice mode on Linux: now distinguishes "no microphone" from "SoX not installed" when SoX is present but no audio capture device exists
- Improved `claude agents` completed list to fill available vertical space; on short terminals the header compacts so live sessions stay visible
- Improved Remote session startup with a provisioning checklist while the container starts

## 2.1.193

- Added `autoMode.classifyAllShell` setting to route all Bash/PowerShell commands through the auto-mode classifier instead of only arbitrary-code-execution patterns
- Added auto-mode denial reasons to the transcript, the denial toast, and `/permissions` recent denials
- Added `claude_code.assistant_response` OpenTelemetry log event containing the model's response text. Redacted unless `OTEL_LOG_ASSISTANT_RESPONSES=1`; when that var is unset it follows `OTEL_LOG_USER_PROMPTS`, so deployments that already log prompt content will start receiving response content on upgrade — set `OTEL_LOG_ASSISTANT_RESPONSES=0` to keep prompts-only.
- Added live file path autocomplete to bash mode (`!`)
- Added a startup notice when MCP servers need authentication, pointing at `/mcp`
- Added automatic memory-pressure reaping for idle background shell commands (disable with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`)
- Fixed `/model` and other client-data-gated UI showing stale/empty state immediately after `/login`
- Fixed backgrounding (←←) spuriously cancelling with "N background tasks would be abandoned" when all running tasks carry over to the new session
- Fixed pinned background agents being re-prompted to "Continue from where you left off" after every auto-update
- Fixed backgrounding the main turn spawning a phantom "general-purpose (resumed)" subagent that re-ran the main conversation
- Fixed agent panel hiding sibling agents when viewing a subagent
- Improved background agents: the launch result no longer instructs Claude to "end your response" — it keeps working on other tasks while the agent runs
- Improved MCP `headersHelper` auth: the helper now re-runs and reconnects automatically when a tool call returns 401/403
- Improved plugin auto-rename: marketplace `renames` maps are now followed automatically, updating your settings to the new name
- Improved `/add-dir` message when the directory is already a working directory

## 2.1.191

- Added `/rewind` support for resuming a conversation from before `/clear` was run
- Fixed scroll position jumping to the bottom while reading earlier output during a streaming response
- Fixed background agents resurrecting after being stopped — stopping an agent from the tasks panel is now permanent
- Fixed `/voice` showing a generic "not available" message when disabled by an organization's policy — it now explains the restriction
- Fixed `/login` URL opening truncated in Windows Terminal when it wraps across lines
- Fixed Cmd+click on links in fullscreen mode for Ghostty over ssh/tmux
- Fixed `claude agents` sending builtin slash commands like `/usage` to background sessions as prompt text instead of showing a hint
- Fixed `claude agents` job rows showing full filesystem paths for pasted images instead of the `[Image #N]` placeholder
- Fixed hooks with comma-separated matchers (e.g. `"Bash,PowerShell"`) silently never firing
- Fixed `/permissions` Recently-denied tab: approving a denial now persists on close instead of being silently discarded
- Fixed the agent panel jumping by one row when scrolling the roster past the overflow cap
- Fixed the welcome splash art overflowing the default 80×24 macOS Terminal window
- Fixed managed settings: `forceRemoteSettingsRefresh` now takes effect when set via MDM or file policy, and the fetch sends `Cache-Control: no-cache` to prevent proxies from serving stale responses
- Improved sandbox network permission dialog: hosts you allow with "Yes" are now remembered for the rest of the session instead of re-prompting on every connection
- Improved MCP server reliability: capability discovery (`tools/list`, `prompts/list`, `resources/list`) now retries transient network errors with short backoff
- Improved MCP OAuth: discovery and token requests now retry once after transient network errors, and headless environments skip the browser popup and go straight to the paste-the-URL prompt
- Improved MCP error messages: HTTP 404 errors now show the URL and point to your MCP config
- Improved vim mode prompt-history search (NORMAL `/`) to hint how to reach slash commands
- Reduced CPU usage during streaming responses by ~37% by coalescing text updates to 100ms
- Reduced long-session memory growth from terminal output cache

## 2.1.190

- Bug fixes and reliability improvements

## 2.1.187

- Added `sandbox.credentials` setting to block sandboxed commands from reading credential files and secret environment variables
- Added org-configured model restrictions to the model picker, `--model`, `/model`, and `ANTHROPIC_MODEL`, with a "restricted by your organization's settings" message when a restricted model is selected
- Added mouse click support to select menus (permission prompts, `/model`, `/config`, etc.) in fullscreen mode
- Fixed `--resume` failing with "No conversation found" when the original `-p` run produced no model turns
- Fixed `--json-schema` and workflow `agent({schema})` structured output: the model can no longer re-call `StructuredOutput` indefinitely after a successful call, and follow-up turns now reliably return structured output
- Fixed remote MCP tool calls that hang with no response for 5 minutes — they now abort with an error instead of blocking indefinitely (override with `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`)
- Fixed Claude Code Remote sessions taking ~2.7s longer to start after the agent proxy CA system-trust install was added
- Fixed pasted Korean/CJK text turning into mojibake in terminals that deliver paste as per-byte extended-key events
- Fixed `/update` over Remote Control hanging when a startup trust dialog would have shown
- Fixed background jobs in the agents view getting stuck in "working" indefinitely when the agent ended a turn without producing structured output
- Fixed channel connections dropping after navigating to the agents view and back, and after `/bg`, `/tui`, or `/update`
- Fixed agent stop notifications not correctly attributing who stopped the agent, and improved wording ("finished"/"stopped" instead of "came to rest")
- Fixed subagent depth tracking: resumed subagents now restore their original spawn depth, and forked subagents now count toward the depth cap
- Fixed leaked agent worktree registrations: locked `.git/worktrees/` entries from killed agents are now cleaned up automatically
- Fixed Cmd+click not opening URLs in fullscreen mode in Ghostty on macOS
- Fixed `claude --help` not listing the `--bg`/`--background` flag
- Fixed Esc, Ctrl-C, and Ctrl-D not working while `/share` is uploading
- Improved `/install-github-app`: GitHub Actions workflow setup is now optional — you can install just the GitHub App and skip the workflow/secret steps
- Improved `/btw` with ←/→ arrow navigation to step through earlier answers
- Improved `/plugin` to surface plugins you haven't used recently so you can clean them up
- [VSCode] Fixed extension becoming unresponsive when resuming a large session

## 2.1.186

- Added `claude mcp login <name>` and `claude mcp logout <name>` to authenticate MCP servers from the CLI without opening the interactive `/mcp` menu, with `--no-browser` stdin redirect support for completing over SSH
- Added status filtering (press `f`) to the `/workflows` agent detail view
- Added a "Skills" section to the `/plugin` Installed tab
- Added `teammateMode: "iterm2"` setting with a warning when auto mode cannot find the `it2` CLI
- Added "Claude Platform on AWS - refresh credentials" option to `/login` when `awsAuthRefresh` is configured
- `!` bash commands now trigger Claude to respond to the output automatically; set `"respondToBashCommands": false` in settings.json to keep the previous context-only behavior
- Fixed streaming requests failing with "Content block not found" or JSON parse errors after the machine wakes from sleep
- Fixed subagent transcript scroll position bleeding into the main transcript on exit
- Fixed background task previews flashing raw tool names before the agent's plan loaded
- Fixed Chrome tab-group isolation not applying when the in-product permissions gate is off for concurrent CLI sessions
- Fixed background session recaps being duplicated; the agent's own end-of-turn summary now shows as the recap line
- Fixed opening a background session from `claude agents` leaving the previous screen painted behind it
- Fixed `Agent(type)` deny rules and `Agent(x,y)` allowed-types restrictions not being enforced for named subagent spawns
- Fixed Esc and Ctrl+C not responding while background agents are still running after the main turn ends
- Fixed misaligned option numbers in permission prompts when the option text overflows
- Fixed pressing `x` on a finished subagent in the agent panel not dismissing it
- Fixed a misleading "MCP server disconnected" notice for intentionally retired tools when resuming older sessions
- Fixed `/plugin` Installed showing a "more above" indicator when already scrolled to the top
- Fixed `~~strikethrough~~` showing literal tildes in assistant messages instead of rendering as strikethrough
- Fixed `--tools` allowing feature-gated tools to slip through before flags loaded on a cold first launch
- Fixed background job status in `claude agents` showing a stale "needs input" message after replying
- Fixed a dark-theme flash when opening a background session from `claude agents` on a light terminal
- Fixed mouse-selected text staying highlighted after deleting it in `claude agents`
- Fixed session cost not showing for usage-based Enterprise and Team subscribers
- Fixed agent teams: teammates spawned via tmux/pane backends now inherit the leader's `--effort` level
- Fixed Workflow `agent({schema})` subagents looping forever on repeated schema validation failures instead of aborting after 5 attempts
- Improved `claude mcp get` and `claude mcp remove` to suggest the closest configured server name on a typo and truncate long server lists
- Improved memory: the agent is now reminded to compact its `MEMORY.md` index when nearing the size limit
- Improved skill frontmatter: `display-name`, `default-enabled`, `fallback`, and `metadata.*` keys now accept kebab-case, snake_case, and camelCase
- Improved malformed `SKILL.md` YAML frontmatter handling: loads the skill body with empty metadata instead of failing silently
- Changed `CLAUDE_CODE_MAX_RETRIES` to cap at 15; for unattended sessions, use `CLAUDE_CODE_RETRY_WATCHDOG` instead
- Changed background subagents to surface permission prompts in the main session instead of auto-denying; the dialog shows which agent is asking, and Esc denies just that tool
- Changed `/review <pr>` to use the same review engine as `/code-review medium`

## 2.1.185

- The stream-stall hint now reads "Waiting for API response · will retry in …" instead of "No response from API · Retrying in …", and triggers after 20s of silence instead of 10s

## 2.1.183

- Improved auto mode safety: destructive git commands (`git reset --hard`, `git checkout -- .`, `git clean -fd`, `git stash drop`) are now blocked when you didn't ask to discard local work, `git commit --amend` is blocked when the commit wasn't made by the agent this session, and `terraform destroy`/`pulumi destroy`/`cdk destroy` are blocked unless you asked for the specific stack
- Added a warning when the requested model is deprecated or automatically updated to a newer model, shown on stderr in print mode (`-p`) and now also covering models set in agent frontmatter
- Added `attribution.sessionUrl` setting to omit the claude.ai session link from commits and PRs in web and Remote Control sessions
- Added `/config --help` to list all available shorthand keys for `/config key=value`
- Changed `/config` toggle behavior: Enter and Space both change the selected setting, and Esc now saves and closes instead of reverting
- Removed the startup "setup issues" line under the logo — run `/doctor` to see configuration issues or use `--debug`
- Fixed `thinking.disabled.display: Extra inputs are not permitted` 400 errors on subagent spawns and session-title generation for affected configurations
- Fixed WebSearch returning empty results in subagents
- Fixed the terminal cursor being stranded above the prompt after navigating history in vim mode with the native cursor enabled
- Fixed fullscreen TUI corruption (statusline mid-screen, duplicated spinner rows, merged text) in Windows Terminal under heavy nested-subagent load
- Fixed turns silently completing with no visible output when the model returned only a thinking block; Claude now re-prompts once
- Fixed user-level skills appearing multiple times in slash-command autocomplete when multiple plugins are enabled
- Fixed MCP servers requiring authentication exposing auth-stub tools to the model in headless/SDK mode
- Fixed tmux teammate panes failing to launch when the shell has slow rc-file initialization, and keystrokes typed during agent spawn leaking into the new tmux pane instead of the leader prompt
- Fixed background tasks started by a teammate being killed when the teammate finishes a turn
- Fixed scheduled task and webhook trigger deliveries being treated as keyboard input; they now classify as task notifications and can no longer approve a pending action or set the session title in auto mode
- Fixed focus mode showing "Ran N PostToolUse hooks" timing lines under each response

## 2.1.181

- Added `/config key=value` syntax to set any setting from the prompt (e.g. `/config thinking=false`) — works in interactive, `-p`, and Remote Control
- Added `sandbox.allowAppleEvents` opt-in setting that lets sandboxed commands send Apple Events on macOS
- Added `CLAUDE_CLIENT_PRESENCE_FILE` environment variable: point it at a marker file to suppress mobile push notifications while you're at the machine
- Upgraded the bundled Bun runtime to 1.4
- Improved streaming of long paragraphs: text now appears line-by-line instead of waiting for the first line break
- Improved auto-retry: API connection drops mid-thinking now automatically retry instead of showing "Connection closed while thinking"
- Improved the subagent panel: idle subagents auto-hide after 30s, the list caps at 5 rows with scroll hints, and keyboard hints now show in the footer
- Improved the MCP OAuth browser page to match Claude Code's visual style and auto-close on success
- Changed fullscreen mode URL opening to require Cmd+click (macOS) / Ctrl+click, matching native terminal behavior
- Changed the `Improved N memories` line to no longer list individual files outside verbose mode
- Fixed prompt caching not reading on custom `ANTHROPIC_BASE_URL` and on Foundry due to a per-request attestation token changing every turn
- Fixed Write/Edit producing 0-byte or truncated files on network drives and cloud-synced folders
- Fixed `open`, `osascript`, and browser-based auth flows failing with error -600 on macOS by adding the Apple Events entitlement
- Fixed a startup regression (~120ms per launch in fresh environments, introduced in 2.1.169): the first prompt no longer waits for the managed-settings fetch when no MCP servers are configured
- Fixed startup blocking with a blank terminal for up to 15 seconds when the account settings fetch is slow on a degraded network
- Fixed startup crash (`TypeError: Cannot read properties of null`) when `.claude.json` contains corrupted null project entries
- Fixed macOS TUI freezing at session start (Ctrl+C unresponsive) when Spotlight is busy reindexing
- Fixed long-running idle sessions losing their history when another Claude Code process ran the 30-day transcript cleanup
- Fixed foreground subagents spawning unbounded nested chains; they now respect the same 5-level depth limit as background subagents
- Fixed `/recap` and conversation forks using the previous model immediately after a model switch
- Fixed subagent "Thinking" duration showing the parent agent's elapsed time instead of the subagent's own
- Fixed subagents blocked on a nested agent showing a ticking elapsed time instead of "waiting" in the agent panel
- Fixed the API retry indicator ("Retrying in 0s · attempt N/10") staying on screen after the retry succeeded
- Fixed AWS `awsCredentialExport` credentials with a short remaining lifetime causing credential refreshes every minute, and now accepts the JSON shape from `aws configure export-credentials`
- Fixed `claude mcp get`/`list` showing `✓ Connected` when tools/list fails; they now show `! Connected · tools fetch failed` with the error detail
- Fixed `/remote-control` leaving a stale "connecting…" line; it now confirms in the transcript once connected
- Fixed ExitWorktree refusing to remove a clean worktree with "Could not verify worktree state" when bare `git` cannot be resolved on Windows
- Fixed settings changes (such as `/effort` or `/model`) failing with ENOENT when `~/.claude/settings.json` is a relative symlink under a symlinked `~/.claude`
- Fixed IDE selection line numbers in context reminders being off by one (IntelliJ and VS Code)
- Fixed Ctrl+C in fullscreen after a native terminal selection (modifier+drag) overwriting the clipboard with the app's prior selection
- Fixed Ctrl+V showing "No image found in clipboard" instead of pasting when the clipboard contains text
- Fixed agent creation failing with "EEXIST: file already exists" when the agents directory already exists (Windows/OneDrive)
- Fixed AskUserQuestion preview content being cut off at the dialog edge instead of word-wrapping
- Fixed AskUserQuestion multi-select questions silently dropping a typed "Other" free-text answer when submitting
- Fixed `/stats` "Most active day" and daily token chart dates showing one day early in UTC-negative timezones
- Fixed `/copy` and copy-on-select on Linux not detecting a clipboard utility installed after Claude Code started
- Fixed tab-indented code rendering with incorrect indentation in the Write (create-file) preview
- Fixed user prompts queued mid-turn not showing a full-width background highlight in the transcript
- Fixed the activity spinner's pulse dwelling on the wrong glyph size in Ghostty

## 2.1.179

- Fixed mid-stream connection drops: partial responses are now preserved instead of showing a raw error, and the spinner no longer gets stuck at "running tool"
- Fixed mouse-wheel scrolling in WSL2 under Windows Terminal and VS Code (regression in 2.1.172)
- Fixed a sandbox `denyRead`/`allowRead` glob over a large directory tree making the Bash tool description enormous and the session unusable on Linux
- Fixed the feedback survey capturing a single-digit reply as a session rating immediately after a turn completes
- Fixed the welcome screen stacking multiple promotional banners — at most one promo now shows per session
- Fixed Ctrl+O not showing the subagent's transcript when viewing a subagent
- Fixed clicking the prompt input not returning focus from the subagent/footer panel
- Fixed remote session background tasks appearing stuck as "still running" between turns
- Improved plugin loading performance in remote sessions

## 2.1.178

- Agent teams: removed the `TeamCreate` and `TeamDelete` tools. With `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set, every session now has one implicit team — spawn teammates directly with the Agent tool's `name` parameter, no setup step needed. The `team_name` parameter on the Agent tool is still accepted but ignored.
- Added `Tool(param:value)` syntax for permission rules to match a tool's input parameters (with `*` wildcard), e.g. `Agent(model:opus)` to block Opus subagents
- Skills in nested `.claude/skills` directories now load when working on files there; on a name clash, the nested skill appears as `<dir>:<name>` so both stay available
- Nested `.claude/` directories: the agent, workflow, and output-style closest to the working directory now wins when names collide; project-scope workflow saves now target the closest existing `.claude/workflows/`
- Improved auto mode: subagent spawns are now evaluated by the classifier before launch, closing a gap where a subagent could request a blocked action without review
- Improved `/doctor` with consistent flat tree layout across all sections, clearer section status icons, and highlighted command names
- Improved the skill listing truncation warning to show how many skill descriptions are affected
- Changed the workflow prompt keyword to use a purple shimmer highlight and trigger only on explicit phrases like "run a workflow" or "workflow:", not on any mention of the word
- Improved Remote Control error messages: connection failures now show a persistent red "/rc failed" indicator in the footer, and the "not yet enabled" error now explains whether it's a gate, a check failure, stale entitlement, or org policy
- `/bug` now requires a description before submitting, and no longer uses model-refusal text as the GitHub issue title
- Fixed a crash (out-of-memory) when the CLI inherits a stale websocket/OAuth file-descriptor environment variable from a parent process
- Fixed Claude in Chrome silently failing to connect when the OAuth token belongs to a different account than the Claude Code login
- Fixed nested `.claude/skills` skills with directory-qualified names being blocked by permission prompts in non-interactive runs
- Fixed several subagent issues: viewing a subagent's transcript now shows tool results and live progress, messages sent while it finishes its turn are no longer dropped, and backgrounding a running subagent (ctrl+b) no longer restarts it from scratch
- Fixed `claude agents` workers failing with `401 Invalid bearer token` when the daemon was started from a shell with a custom API gateway via `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`
- Fixed compaction not honoring `--fallback-model`: compaction now falls back to the configured fallback model chain on overload or model-availability errors
- Fixed model requests continuing to fail with auth errors after credentials were refreshed outside the session, due to a stale cached request configuration
- Fixed background sessions created with `/bg` or `←←` after a turn finished showing "Working" forever in the agents list
- Fixed Linux sandbox failing to start when `.claude/skills` or `.claude/hooks` is a symlink
- Fixed `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` preventing fresh marketplace installs from cloning
- Fixed MCP server-level specs (`mcp__server`, `mcp__server__*`, `mcp__*`) in subagent `disallowedTools` being silently ignored
- Fixed vim mode undo: `u` now steps through NORMAL/VISUAL-mode commands one at a time instead of merging commands in quick succession into a single undo step
- Fixed statusline links with custom URI schemes (e.g. `vscode://`) not opening when clicked in `claude agents`
- [VSCode] Fixed pressing Esc to dismiss a CJK IME candidate window canceling the running Claude task

## 2.1.176

- Session titles are now generated in the language of your conversation (set the `language` setting to pin a specific language)
- Added `footerLinksRegexes` setting for regex-matched link badges in the footer row, configurable via user or managed settings
- Improved Bedrock credential caching: credentials from `awsCredentialExport` are now cached until their `Expiration` instead of a fixed 1 hour
- Fixed `availableModels` enforcement: alias model picks can no longer be redirected to a blocked model via `ANTHROPIC_DEFAULT_*_MODEL` environment variables, and `/fast` now refuses to toggle when it would switch to a model outside the allowlist
- Fixed auto mode failing on Fable 5 for organizations without Opus 4.8 enabled — the classifier now falls back to the best available Opus model
- Fixed hook `if` conditions for Read/Edit/Write tool paths: documented patterns like `Edit(src/**)`, `Read(~/.ssh/**)`, and `Read(.env)` now match correctly
- Fixed Linux sandbox failing to start when `.claude/settings.json` is a symlink with an absolute target
- Fixed `/copy` and mouse-selection copy not reaching the system clipboard inside tmux over SSH, and tmux paste buffer not loading on versions older than 3.2
- Fixed Remote Control connecting from web/mobile silently switching the session's model
- Fixed Remote Control disconnect notifications showing a bare numeric code instead of a human-readable reason, and connection failures adding a duplicate line to the conversation transcript
- Fixed Remote Control sessions not disconnecting when you sign in to a different account
- Fixed `/cd` and worktree moves leaving the session reporting the previous directory's git branch
- Fixed `claude agents`: pressing back in one window no longer detaches other windows attached to the same session
- Fixed backgrounded sessions showing "Working" forever when `/bg` mid-turn had nothing left to continue
- Fixed background agent search by PR URL: PRs opened during scheduled wakeups or while a job was blocked now appear in `claude agents` search
- Fixed the agents view input showing no text cursor on Windows
- Fixed `claude --bg -cn <name>` not seeding the session name
- Fixed background sessions to neutralize Windows network paths in persisted state before respawn
- Fixed background-session respawn rejecting malformed resume IDs from corrupted state files
- Fixed the Windows background-service daemon not starting when `~/.claude/daemon` has the ReadOnly attribute set
- Fixed cloud sessions failing with "Could not resolve authentication method" when idle for too long before being claimed
- Background sessions now show clearer guidance when a window left open across an auto-update can't submit a reply, and `claude daemon status` explains version-skew behavior

## 2.1.175

- Added `enforceAvailableModels` managed setting — when enabled, the `availableModels` allowlist also constrains the Default model (a Default that would resolve to a disallowed model now falls back to the first allowed model), and user or project settings can no longer widen a managed `availableModels` list

## 2.1.174

- Added `wheelScrollAccelerationEnabled` setting to disable mouse-wheel scroll acceleration in fullscreen mode
- Fixed the `/model` picker hiding the model family that Default resolves to — Opus now appears as its own row on Max/Team Premium/Enterprise plans, Sonnet on Pro/Team plans, and Opus on pay-as-you-go API accounts
- Fixed `/model` picker showing a hardcoded Sonnet version label when `ANTHROPIC_DEFAULT_SONNET_MODEL` pins a different Sonnet
- Fixed the "Fable 5 is now consuming usage credits" banner incorrectly showing for enterprise accounts with usage-based billing
- Fixed Bedrock GovCloud regions (`us-gov-*`) deriving the wrong inference profile prefix (`global` instead of `us-gov`), causing 400 errors on derived model IDs
- Fixed background sessions inheriting another session's `ANTHROPIC_*` provider env (gateway URL, custom headers, `/model` aliases) from the shell that started the background daemon
- Fixed a 1-2 second pause when exiting Claude Code shortly after a shell command was interrupted or killed on macOS and Linux
- Fixed git commit co-author attribution showing an incorrect model name for some models
- Fixed the `/advisor` dialog pre-selecting a saved advisor model that is blocked by the `availableModels` allowlist
- Fixed skill hot-reload re-sending the entire skill listing when a single skill changed; only changed skills are now re-announced
- Fixed Workflow tool `agent()` subagents missing per-agent attribution headers
- [VSCode] Added usage attribution to the Account & usage dialog (`/usage`) showing cache misses, long context, subagents, and per-skill/agent/plugin/MCP breakdowns over the last 24h or 7d
- Fixed pre-warmed background workers failing with "Could not resolve authentication method" when claimed after sitting idle
