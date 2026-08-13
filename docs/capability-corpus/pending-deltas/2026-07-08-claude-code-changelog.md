# Pending delta — claude-code-changelog

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-08T16:21:35Z

- **new-claim** — adds a capability claim not previously upstream
  - now: ## 2.1.204

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
