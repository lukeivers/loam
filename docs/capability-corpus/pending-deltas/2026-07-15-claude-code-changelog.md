# Pending delta — claude-code-changelog

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-15T13:00:06Z

- **new-claim** — adds a capability claim not previously upstream
  - now: ## 2.1.210

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
- **reprojection** — same-statement update (similarity >= threshold)
  - was: - Added deprecation notification for npm installations - run `claude install` or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options
  - now: - Added deprecation notification for npm installations - run `claude install` or see https://code.claude.com/docs/en/setup for more options
