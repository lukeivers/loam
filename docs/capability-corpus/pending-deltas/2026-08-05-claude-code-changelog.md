# Pending delta — claude-code-changelog

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-05T13:11:50Z

- **new-claim** — adds a capability claim not previously upstream
  - now: ## 2.1.222

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
